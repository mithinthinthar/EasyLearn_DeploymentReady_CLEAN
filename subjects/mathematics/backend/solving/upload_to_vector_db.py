import json
import os
from openai import OpenAI
from pinecone import Pinecone
from dotenv import load_dotenv

# 1. Load Environment Variables
load_dotenv()

# Initialize API Clients
openai_client = OpenAI(
    api_key=os.getenv("GEMINI_API_KEY"),
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))

# Connect to your specific index
INDEX_NAME = "mathsy-rag"
index = pc.Index(INDEX_NAME)


def group_and_propagate_context(parsed_questions):
    """
    Injects the "Intro" paragraph text into all of its sub-questions
    so the LLM embedding doesn't lose the mathematical context.
    """
    grouped = {}
    for q in parsed_questions:
        qno = str(q.get('question_no', '')).strip()
        if not qno: continue
        
        if qno not in grouped:
            grouped[qno] = []
        grouped[qno].append(q)

    for qno, parts in grouped.items():
        # Find the parent (part, subpart, sub_subpart are all empty)
        parent = next((q for q in parts if not q.get('part') and not q.get('subpart') and not q.get('sub_subpart')), None)
        
        if parent:
            parent_intro = " ".join(parent.get("instructions_en", []))
            parent_equations = " ".join(parent.get("equations", []))
            
            for child in parts:
                if child != parent:
                    # Give the child the parent's context
                    child["_inherited_context"] = f"Context from main question: {parent_intro} {parent_equations}"

    return parsed_questions

def prepare_for_pinecone(parsed_question, paper_prefix, paper_id):
    """
    Formats the metadata for filtering and squishes the math text together.
    """
    q_no = str(parsed_question.get('question_no', '')).strip()
    part = str(parsed_question.get('part', '')).strip()
    sub = str(parsed_question.get('subpart', '')).strip()
    sub_sub = str(parsed_question.get('sub_subpart', '')).strip()
    
    question_id = f"{paper_prefix}_Q{q_no}_{part}_{sub}_{sub_sub}".strip("_")
    
    # ✨ THE FIX: We now explicitly store exactly what MySQL needs to find the rubric!
    metadata = {
        "question_id": question_id,
        "paper_id": int(paper_id),  # The MySQL ID!
        "question_no": q_no,
        "part": part,
        "subpart": sub,
        "sub_subpart": sub_sub,
        "topic": str(parsed_question.get("topic", "")),
        "subtopic": str(parsed_question.get("subtopic", "")),
        "form": str(parsed_question.get("form", "")),
        "chapter": str(parsed_question.get("chapter", "")),
    }

    inherited_context = parsed_question.get("_inherited_context", "")
    instructions = " ".join(parsed_question.get("instructions_en", []))
    equations = " ".join(parsed_question.get("equations", []))
    expressions = " ".join(parsed_question.get("expressions", []))
    target = str(parsed_question.get("target", ""))
    
    # Safely convert the new nested dictionaries to JSON strings
    given_values_str = json.dumps(parsed_question.get("given_values", {}), ensure_ascii=False)
    table_data_str = json.dumps(parsed_question.get("table_data", {}), ensure_ascii=False)
    constraints_str = json.dumps(parsed_question.get("constraints", {}), ensure_ascii=False)
    diagram_type = str(parsed_question.get("diagram_type", "")).strip()
    diagram_data_str = json.dumps(parsed_question.get("diagram_data", {}), ensure_ascii=False)
    visual_analysis = str(parsed_question.get("visual_analysis", "")).strip()

    # Inject everything into the ultimate embedding string
    embedding_string = (
        f"Topic: {metadata['topic']} - {metadata['subtopic']} "
        f"{inherited_context} "
        f"Question: {instructions} "
        f"Math Elements: {equations} {expressions} "
        f"Given Values: {given_values_str} "
        f"Table Data: {table_data_str} "
        f"Diagram Type: {diagram_type} "          
        f"Diagram Data: {diagram_data_str} "      
        f"Visual Context: {visual_analysis} "     
        f"Constraints: {constraints_str} "
        f"Target to find: {target}"
    )
    
    # Clean up excess whitespace
    embedding_string = " ".join(embedding_string.split())

    return question_id, embedding_string, metadata

def upload_questions_to_pinecone(json_file_path,paper_prefix,paper_id, namespace="exam_questions"):
    print("Loading parsed questions from JSON...")
    with open(json_file_path, "r", encoding="utf-8") as f:
        questions = json.load(f)
        
    # Apply the context propagation
    questions = group_and_propagate_context(questions)
    qnos_with_parts = set(
        str(q.get('question_no', '')).strip() 
        for q in questions 
        if q.get('part') or q.get('subpart') or q.get('sub_subpart')
    )

    # 2. Keep the item if it IS a subpart, OR if its question_no doesn't have any subparts at all
    questions = [
        q for q in questions 
        if q.get('part') or q.get('subpart') or q.get('sub_subpart') 
        or str(q.get('question_no', '')).strip() not in qnos_with_parts
    ]
    # ----------------------------
    
    vectors_to_upload = []
    print(f"Generating OpenAI embeddings for {len(questions)} questions...")
    
    for q in questions:
        # Skip garbage fragments
        if not q.get("question_no"):
            continue
            
        q_id, text_to_embed, metadata = prepare_for_pinecone(q, paper_prefix, paper_id)
        
        try:
            # Call OpenAI to turn the text into 1,536 numbers
            response = openai_client.embeddings.create(
                input=text_to_embed,
                model="gemini-embedding-2-preview",
                dimensions=768
            )
            vector_numbers = response.data[0].embedding
            
            # Package it exactly how Pinecone expects it
            vectors_to_upload.append({
                "id": q_id,
                "values": vector_numbers,
                "metadata": metadata
            })
            print(f"  ✅ Generated vector for {q_id}")
            
        except Exception as e:
            print(f"  ❌ Error embedding {q_id}: {e}")

    # Upload to Pinecone in batches to avoid overwhelming the network
    print("\nUploading vectors to Pinecone...")
    batch_size = 50
    for i in range(0, len(vectors_to_upload), batch_size):
        batch = vectors_to_upload[i : i + batch_size]
        index.upsert(vectors=batch, namespace=namespace)
        print(f"  ⬆️ Uploaded batch {i//batch_size + 1} ({len(batch)} vectors)")

    print("\n🎉 Success! All questions are now searchable in your vector database.")

if __name__ == "__main__":
    # Point this to the JSON file your extraction script generated
    filename = "Kedah_2025_parsed_questions.json"
    json_path = os.path.join("parsed_output2", filename)
    mysql_paper_id = 20
    if os.path.exists(json_path):
        paper_prefix = filename.replace("_parsed_questions.json", "")
        upload_questions_to_pinecone(json_path, paper_prefix, mysql_paper_id, namespace="exam_questions")
    else:
        print(f"Error: Could not find {json_path}. Run your PDF extractor first!")