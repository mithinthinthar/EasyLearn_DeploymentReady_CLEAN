
import json
from solving.extractor import run_base_extractor, normalize_topic_subtopic
from solving.rag_retriever import get_smart_rag_context, format_rag_context_for_llm, has_explicit_subparts
from solving.grader import normalize_extracted_for_rag
from solving.solvers.router import route_solver_for_subpart, should_use_mixed_subpart_solver, solve_mixed_stage_with_dependencies, get_subpart_rag_contexts_by_label, format_subpart_rag_contexts_by_label


def attach_rag_audit(result: dict, rag_bundle: dict) -> dict:
    if not isinstance(result, dict):
        result = {"raw_result": result}

    result["rag_audit"] = {
        "mode": rag_bundle.get("mode"),
        "strength": rag_bundle.get("strength"),
        "stage_score": rag_bundle.get("stage_score"),
        "subpart_score": rag_bundle.get("subpart_score"),
        "is_exact_match": rag_bundle.get("is_exact_match"),
        "exact_match_type": rag_bundle.get("exact_match_type")
    }

    return result

def is_cartesian_transformation_question(interpreted):
    topic = str(interpreted.get("topic", "")).lower()
    subtopic = str(interpreted.get("subtopic", "")).lower()
    diagram_type = str(interpreted.get("diagram_type", "")).lower()
    visual_summary = str(interpreted.get("visual_semantic_summary", "")).lower()

    if "transformation" in topic or "transformation" in subtopic:
        return (
            "cartesian" in diagram_type
            or "coordinate" in diagram_type
            or "cartesian" in visual_summary
            or "coordinate" in visual_summary
        )

    subparts = interpreted.get("subpart_classification") or {}

    if isinstance(subparts, dict):
        for info in subparts.values():
            if not isinstance(info, dict):
                continue

            sp_topic = str(info.get("topic", "")).lower()
            sp_subtopic = str(info.get("subtopic", "")).lower()
            sp_instruction = (
                str(info.get("instruction_en", "")) + " " +
                str(info.get("instruction_ms", ""))
            ).lower()

            if (
                "transformation" in sp_topic
                or "transformation" in sp_subtopic
                or "transformation" in sp_instruction
                or "penjelmaan" in sp_instruction
            ):
                return True

    return False

def solve_new_question(
    image_base64,
    interpreted=None,
    confirmed_coordinates=None,
    coordinate_input=None,
    language=None
):
    """
    MASTER ROUTER:
    1. Extracts metadata.
    2. Fetches RAG marking schemes.
    3. Routes the image to the correct Specialized Solver based on the topic/subtopic.
    """
    if interpreted is None:
        print("🚀 Step 1: Running Base Extractor to determine topic...")
        interpreted = run_base_extractor(image_base64)
        interpreted = normalize_topic_subtopic(interpreted)
        interpreted = normalize_extracted_for_rag(interpreted)
    else:
        print("🚀 Step 1: Reusing provided extracted metadata to save time/cost...")
    print("📚 Step 2: Fetching RAG Context...")
    rag_bundle = get_smart_rag_context(interpreted, purpose="solve")
    rag_data = format_rag_context_for_llm(rag_bundle, purpose="solve")
    is_mixed = should_use_mixed_subpart_solver(interpreted)
    # For same-topic multi-subpart questions, keep one solver,
    # but still retrieve subpart-specific RAG.
    subpart_rag_by_label = {}
    if has_explicit_subparts(interpreted) and not is_mixed:
        subpart_rag_by_label = get_subpart_rag_contexts_by_label(
            interpreted,
            top_k=2
        )
        if subpart_rag_by_label:
            rag_data += format_subpart_rag_contexts_by_label(subpart_rag_by_label)
    if rag_bundle.get("is_exact_match"):
        rag_data += """
    ==============================
    EXACT MATCH OVERRIDE
    ==============================
    This question is an exact or near-exact match to an official database question.
    The official marking scheme inside RAG is the source of truth.
    The solver MUST follow the official marking scheme structure, final answer, units, and rounding.
    """
    print("RAG MODE:", rag_bundle["mode"])
    print("STAGE SCORE:", rag_bundle.get("stage_score"))
    print("SUBPART SCORE:", rag_bundle.get("subpart_score"))
    print("SUBPART CLASSIFICATION:")
    print(json.dumps(interpreted.get("subpart_classification", {}), indent=2, ensure_ascii=False))

    if is_mixed and not is_cartesian_transformation_question(interpreted):
        print("🧩 Mixed-topic subparts detected. Using dependency-aware subpart orchestrator.")
        result = solve_mixed_stage_with_dependencies(
            image_base64,
            interpreted,
            rag_data,
            language=language
        )
        result = attach_rag_audit(result, rag_bundle)
        return result

    if is_mixed and is_cartesian_transformation_question(interpreted):
        print("🧩 Mixed question contains Cartesian transformation. Routing whole question to transformation solver first.")
        from solving.solvers.transformations import solve_transformations

        result = solve_transformations(
            image_base64,
            interpreted,
            rag_data,
            confirmed_coordinates=confirmed_coordinates,
            coordinate_input=coordinate_input,
            language=language
        )

        result = attach_rag_audit(result, rag_bundle)
        return result
    topic = interpreted.get("topic", "")
    subtopic = interpreted.get("subtopic", "")
    diagram_type = str(interpreted.get("diagram_type", "")).strip().lower()
    
    print(f"🧭 Step 3: Routing -> Topic: {topic} | Subtopic: {subtopic} | Diagram: {diagram_type}")
    
    solver_fn = route_solver_for_subpart(topic, subtopic)
    
    if solver_fn.__name__ == "solve_transformations":
        result = solver_fn(
            image_base64,
            interpreted,
            rag_data,
            confirmed_coordinates=confirmed_coordinates,
            coordinate_input=coordinate_input,
            language = language
        )
    else:
        result = solver_fn(image_base64, interpreted, rag_data, language=language)

    result = attach_rag_audit(result, rag_bundle)
    if subpart_rag_by_label:
        result["subpart_rag_audit"] = {
            label: {
                "score": data.get("score"),
                "strength": data.get("strength"),
                "is_exact": data.get("is_exact")
            }
            for label, data in subpart_rag_by_label.items()
        }

    return result


# def main():
#     # Helper function to keep our code clean
#     def get_base64(image_path):
#         if not os.path.exists(image_path):
#             raise FileNotFoundError(f"Could not find image at {image_path}")
#         with open(image_path, "rb") as image_file:
#             return base64.b64encode(image_file.read()).decode('utf-8')

#     print("="*50)
#     print("🚀 MATHSY AI ENGINE TESTING DASHBOARD")
#     print("="*50)
    
#     # new_question_path = r"C:\Users\YK\Pictures\Screenshots\Screenshot 2026-04-20 104423.png"
#     new_question_path = r"C:\Users\YK\Pictures\Screenshots\Screenshot 2026-04-20 104804.png"
    
#     print("\n[TEST 1] Running RAG Solver...")
#     try:
#         q_b64 = get_base64(new_question_path)
#         solution = solve_new_question(q_b64)
#         print("\n--- AI SOLUTION ---")
#         print(solution)
#     except Exception as e:
#         print(f"Error: {e}")
    

