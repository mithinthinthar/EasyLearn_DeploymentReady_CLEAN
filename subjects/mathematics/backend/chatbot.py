from __future__ import annotations

import re
import os
from typing import Any, Dict, List

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

from pinecone_client import index, CONCEPT_NAMESPACE, QUESTION_NAMESPACE
from embeddings import embed_text

load_dotenv()


def normalize_language(language: str) -> str:
    text = str(language or "").strip().lower()
    if text in ["bm", "bahasa melayu", "malay", "bahasa_melayu"]:
        return "bm"
    return "english"


def get_language_label(language: str) -> str:
    return "Bahasa Melayu" if normalize_language(language) == "bm" else "English"

SPM_CHAPTER_MAP = {
    1: [
        (1, "Rational Numbers", "Nombor Nisbah"),
        (2, "Factors and Multiples", "Faktor dan Gandaan"),
        (3, "Squares, Square Roots, Cubes and Cube Roots", "Kuasa Dua, Punca Kuasa Dua, Kuasa Tiga dan Punca Kuasa Tiga"),
        (4, "Ratios, Rates and Proportions", "Nisbah, Kadar dan Kadaran"),
        (5, "Algebraic Expressions", "Ungkapan Algebra"),
        (6, "Linear Equations", "Persamaan Linear"),
        (7, "Linear Inequalities", "Ketaksamaan Linear"),
        (8, "Lines and Angles", "Garis dan Sudut"),
        (9, "Basic Polygons", "Poligon Asas"),
        (10, "Perimeter and Area", "Perimeter dan Luas"),
        (11, "Introduction of Set", "Pengenalan Set"),
        (12, "Data Handling", "Pengendalian Data"),
        (13, "The Pythagoras Theorem", "Teorem Pythagoras"),
    ],
    2: [
        (1, "Patterns and Sequences", "Pola dan Jujukan"),
        (2, "Factorisation and Algebraic Fractions", "Pemfaktoran dan Pecahan Algebra"),
        (3, "Algebraic Formulae", "Rumus Algebra"),
        (4, "Polygons", "Poligon"),
        (5, "Circles", "Bulatan"),
        (6, "Three-Dimensional Geometrical Shapes", "Bentuk Geometri Tiga Dimensi"),
        (7, "Coordinates", "Koordinat"),
        (8, "Graphs of Functions", "Graf Fungsi"),
        (9, "Speed and Acceleration", "Laju dan Pecutan"),
        (10, "Gradient of a Straight Line", "Kecerunan Garis Lurus"),
        (11, "Isometric Transformations", "Transformasi Isometri"),
        (12, "Measures of Central Tendencies", "Sukatan Kecenderungan Memusat"),
        (13, "Simple Probability", "Kebarangkalian Mudah"),
    ],
    3: [
        (1, "Indices", "Indeks"),
        (2, "Standard Form", "Bentuk Piawai"),
        (3, "Consumer Mathematics: Savings and Investments, Credit and Debt", "Matematik Pengguna: Simpanan dan Pelaburan, Kredit dan Hutang"),
        (4, "Scale Drawings", "Lukisan Berskala"),
        (5, "Trigonometric Ratios", "Nisbah Trigonometri"),
        (6, "Angles and Tangents of Circles", "Sudut dan Tangen bagi Bulatan"),
        (7, "Plans and Elevations", "Pelan dan Dongakan"),
        (8, "Loci in Two Dimensions", "Lokus dalam Dua Dimensi"),
        (9, "Straight Lines", "Garis Lurus"),
    ],
    4: [
        (1, "Quadratic Functions and Equations in One Variable", "Fungsi dan Persamaan Kuadratik dalam Satu Pemboleh Ubah"),
        (2, "Number Bases", "Asas Nombor"),
        (3, "Logical Reasoning", "Penaakulan Logik"),
        (4, "Operations on Sets", "Operasi Set"),
        (5, "Network in Graph Theory", "Rangkaian dalam Teori Graf"),
        (6, "Linear Inequalities in Two Variables", "Ketaksamaan Linear dalam Dua Pemboleh Ubah"),
        (7, "Graphs of Motion", "Graf Gerakan"),
        (8, "Measures of Dispersion for Ungrouped Data", "Sukatan Serakan Data Tak Terkumpul"),
        (9, "Probability of Combined Events", "Kebarangkalian Peristiwa Bergabung"),
        (10, "Consumer Mathematics: Financial Management", "Matematik Pengguna: Pengurusan Kewangan"),
    ],
    5: [
        (1, "Variation", "Ubahan"),
        (2, "Matrices", "Matriks"),
        (3, "Consumer Mathematics: Insurance", "Matematik Pengguna: Insurans"),
        (4, "Consumer Mathematics: Taxation", "Matematik Pengguna: Percukaian"),
        (5, "Congruency, Enlargement and Combined Transformations", "Kekongruenan, Pembesaran dan Gabungan Transformasi"),
        (6, "Ratios and Graphs of Trigonometric Functions", "Nisbah dan Graf Fungsi Trigonometri"),
        (7, "Measures of Dispersion for Grouped Data", "Sukatan Serakan Data Terkumpul"),
        (8, "Mathematical Modeling", "Pemodelan Matematik"),
    ],
}

def try_answer_chapter_map_query(user_message: str, language: str = "English") -> str | None:
    text = (user_message or "").lower().strip()
    lang = normalize_language(language)

    # 1. Specific chapter query first
    chapter_lookup = parse_form_chapter_query(user_message)

    if chapter_lookup:
        form_no, chapter_no = chapter_lookup

        chapters = SPM_CHAPTER_MAP.get(form_no)
        if not chapters:
            return None

        chapter = next((item for item in chapters if item[0] == chapter_no), None)
        if not chapter:
            return None

        no, en, ms = chapter

        # If student wants explanation, do not stop here.
        # Let Pinecone retrieve the full chapter notes.
        explain_intent_keywords = [
            "explain",
            "teach",
            "learn",
            "understand",
            "dont understand",
            "don't understand",
            "not understand",
            "terangkan",
            "ajar",
            "belajar",
            "tak faham",
            "tidak faham",
        ]

        if any(keyword in text for keyword in explain_intent_keywords):
            return None

        if lang == "bm":
            return (
                f"Tingkatan {form_no} Bab {chapter_no} ialah **{ms} / {en}**."
            )

        return (
            f"Form {form_no} Chapter {chapter_no} is **{en} / {ms}**."
        )

    # 2. Chapter list query
    list_patterns = [
        r"chapters\s+in\s+form\s*(\d)",
        r"form\s*(\d)\s+chapters\b",
        r"chapters\s+for\s+form\s*(\d)",
        r"what\s+are\s+the\s+chapters\s+in\s+form\s*(\d)",
        r"bab\s+dalam\s+tingkatan\s*(\d)",
        r"senarai\s+bab\s+tingkatan\s*(\d)",
        r"tingkatan\s*(\d)\s+senarai\s+bab",
    ]

    for pattern in list_patterns:
        match = re.search(pattern, text)
        if match:
            form_no = int(match.group(1))

            if form_no not in SPM_CHAPTER_MAP:
                return None

            chapters = SPM_CHAPTER_MAP[form_no]

            if lang == "bm":
                lines = [f"Berikut ialah senarai bab Matematik Tingkatan {form_no}:"]
                for no, en, ms in chapters:
                    lines.append(f"{no}. {ms} / {en}")
            else:
                lines = [f"Here are the Form {form_no} Mathematics chapters:"]
                for no, en, ms in chapters:
                    lines.append(f"{no}. {en} / {ms}")

            return "\n".join(lines)

    return None

def format_conversation_history(history_messages: List[Dict[str, Any]] | None) -> str:
    if not history_messages:
        return "No previous conversation history."

    lines = []
    for msg in history_messages:
        sender = msg.get("sender", "user")
        text = (msg.get("message_text") or "").strip()
        if not text:
            continue
        role = "Tutor" if sender == "assistant" else "Student"
        lines.append(f"{role}: {text}")

    return "\n".join(lines) if lines else "No previous conversation history."


def is_exam_style_query(user_message: str) -> bool:
    text = (user_message or "").strip().lower()

    if not text:
        return False

    # 1. Strong explicit exam / solution intent
    exam_keywords = [
        "solve",
        "answer",
        "marking",
        "scheme",
        "kertas",
        "paper 1",
        "paper 2",
        "mcq",
        "working",
        "show steps",
        "step by step",
        "worked example",
        "exam",
        "trial",
        "past year",
        "how to answer",
        "check my work",
        "full solution",
    ]
    if any(keyword in text for keyword in exam_keywords):
        return True

    # 2. Common math-question command verbs
    question_starters = [
        "find ",
        "calculate ",
        "determine ",
        "solve ",
        "convert ",
        "simplify ",
        "state ",
        "write down ",
        "sketch ",
        "evaluate ",
        "express ",
        "hence ",
        "show that ",
        "prove that ",
    ]
    if any(text.startswith(starter) for starter in question_starters):
        return True

    # 3. MCQ pattern
    if re.search(r"(^|\n)\s*[a-d]\.", text) or re.search(r"(^|\n)\s*[a-d]\)", text):
        return True

    # 4. Looks like pasted mathematical question
    math_patterns = [
        r"\d+\s*[=+\-*/]",         # e.g. 2x + 5, 12 = ...
        r"[a-z]\s*=\s*\d+",        # e.g. y = 12
        r"\(\s*[0-9a-z+\-*/ ]+\s*\)",  # bracketed expressions
        r"\bvaries directly\b",
        r"\bvaries inversely\b",
        r"\bbase\s*\d+\b",
        r"\bdiagram\b",
        r"\btable\b",
        r"\bgraph\b",
        r"\bfigure\b",
    ]
    if any(re.search(pattern, text) for pattern in math_patterns):
        return True

    # 5. Long multi-line pasted prompt often means actual question text
    if "\n" in text and len(text) > 80:
        return True

    return False


def query_namespace(namespace: str, query_vector: List[float], top_k: int = 4, metadata_filter: Dict[str, Any] | None = None) -> List[Any]:
    if not query_vector:
        return []

    query_kwargs = {
        "namespace": namespace,
        "vector": query_vector,
        "top_k": top_k,
        "include_metadata": True,
        "include_values": False,
    }

    if metadata_filter:
        query_kwargs["filter"] = metadata_filter

    result = index.query(**query_kwargs)
    return list(getattr(result, "matches", []) or [])


def get_match_score(match: Any) -> float:
    if hasattr(match, "score"):
        return float(match.score or 0)
    if isinstance(match, dict):
        return float(match.get("score", 0))
    return 0.0


def get_match_metadata(match: Any) -> Dict[str, Any]:
    if hasattr(match, "metadata"):
        return dict(match.metadata or {})
    if isinstance(match, dict):
        return dict(match.get("metadata", {}) or {})
    return {}

def get_top_concept_topic(concept_matches: List[Any]) -> str | None:
    if not concept_matches:
        return None

    top_metadata = get_match_metadata(concept_matches[0])
    topic = top_metadata.get("topic")
    return str(topic).strip() if topic else None

def merge_results(concept_matches: List[Any], question_matches: List[Any], max_total: int = 6) -> List[Any]:
    combined = list(concept_matches) + list(question_matches)
    combined.sort(key=get_match_score, reverse=True)
    return combined[:max_total]


def format_retrieved_context(matches: List[Any]) -> str:
    if not matches:
        return "No relevant knowledge base context retrieved."

    blocks = []

    for i, match in enumerate(matches, start=1):
        metadata = get_match_metadata(match)

        block = f"""
[Reference {i}]
KB Type: {metadata.get("kb_type", "")}
Topic: {metadata.get("topic", "")}
Form: {metadata.get("form", "")}
Chapter: {metadata.get("chapter_label", "")}
Content Type: {metadata.get("content_type", "")}
Source File: {metadata.get("source_file", "")}
Score: {round(get_match_score(match), 4)}

Content:
{metadata.get("chunk_text", "")}
""".strip()

        blocks.append(block)

    return "\n\n".join(blocks)


def retrieve_context(user_message: str, retrieval_mode: str = "auto") -> str:
    retrieval_mode = str(retrieval_mode or "auto").lower()

    if retrieval_mode == "none":
        return "No knowledge base retrieval needed for this message."

    query_vector = embed_text(user_message)

    if not query_vector:
        return "No relevant knowledge base context retrieved."

    chapter_lookup = parse_form_chapter_query(user_message)

    if chapter_lookup:
        form_no, chapter_no = chapter_lookup

        chapter_map_matches = query_namespace(
            CONCEPT_NAMESPACE,
            query_vector,
            top_k=2,
            metadata_filter={"content_type": {"$eq": "chapter_map"}},
        )

        topic_note_matches = query_namespace(
            CONCEPT_NAMESPACE,
            query_vector,
            top_k=4,
            metadata_filter={
                "form": {"$eq": f"Form {form_no}"},
                "chapter_no": {"$eq": chapter_no},
            },
        )

        combined_matches = chapter_map_matches + topic_note_matches

        return (
            "The student is asking about a specific form and chapter number. "
            "First use the chapter map to identify the correct chapter title. "
            "Do not guess the chapter title. Then explain the chapter using topic notes if available.\n\n"
            + format_retrieved_context(combined_matches)
        )

    # Concept-only retrieval
    if retrieval_mode == "concept_only":
        concept_matches = query_namespace(CONCEPT_NAMESPACE, query_vector, top_k=4)

        print("CONCEPT_NAMESPACE =", CONCEPT_NAMESPACE)
        print("QUESTION_NAMESPACE =", QUESTION_NAMESPACE)

        print("\n=== CONCEPT MATCHES ===")
        for match in concept_matches:
            metadata = get_match_metadata(match)
            print({
                "score": round(get_match_score(match), 4),
                "source_file": metadata.get("source_file"),
                "topic": metadata.get("topic"),
                "content_type": metadata.get("content_type"),
            })

        print("\n=== QUESTION MATCHES ===")
        print("(skipped due to concept_only retrieval mode)")

        return format_retrieved_context(concept_matches)

    # Practice-question retrieval
    # Use concept notes + question-bank examples as SPM format/style references.
    if retrieval_mode == "practice":
        concept_matches = query_namespace(CONCEPT_NAMESPACE, query_vector, top_k=3)
        detected_topic = get_top_concept_topic(concept_matches)

        question_matches = []

        # Try filtered question search first, but only if topic is meaningful
        weak_detected_topics = [
            "Lower Secondary Foundations",
            "Exam Format and Rules",
            "KBAT Strategies",
            "Common Student Mistakes",
            "Formula Sheet Guide",
            "Calculator Techniques",
        ]

        if detected_topic and detected_topic not in weak_detected_topics:
            question_filter = {"topic": {"$eq": detected_topic}}

            question_matches = query_namespace(
                QUESTION_NAMESPACE,
                query_vector,
                top_k=4,
                metadata_filter=question_filter,
            )

        # Fallback: if filtered search fails, search question namespace without topic filter
        if not question_matches:
            question_matches = query_namespace(
                QUESTION_NAMESPACE,
                query_vector,
                top_k=4,
                metadata_filter=None,
            )

        print("CONCEPT_NAMESPACE =", CONCEPT_NAMESPACE)
        print("QUESTION_NAMESPACE =", QUESTION_NAMESPACE)
        print("DETECTED_TOPIC =", detected_topic)
        print("RETRIEVAL_MODE = practice")

        print("\n=== CONCEPT MATCHES ===")
        for match in concept_matches:
            metadata = get_match_metadata(match)
            print({
                "score": round(get_match_score(match), 4),
                "source_file": metadata.get("source_file"),
                "topic": metadata.get("topic"),
                "content_type": metadata.get("content_type"),
            })

        print("\n=== QUESTION MATCHES ===")
        for match in question_matches:
            metadata = get_match_metadata(match)
            print({
                "score": round(get_match_score(match), 4),
                "source_file": metadata.get("source_file"),
                "topic": metadata.get("topic"),
                "content_type": metadata.get("content_type"),
                "paper_type": metadata.get("paper_type"),
                "question_no": metadata.get("question_no"),
            })

        merged_matches = merge_results(concept_matches, question_matches, max_total=6)

        return (
            "Practice-question generation context.\n"
            "Use the concept notes for syllabus accuracy.\n"
            "Use the question-bank examples only as SPM format/style references.\n"
            "Do not copy an existing question exactly if avoidable.\n"
            "Do not reveal answer/solution unless the student asked for it.\n\n"
            + format_retrieved_context(merged_matches)
        )


    # Full retrieval for solving/exam-style questions
    if retrieval_mode == "full":
        concept_matches = query_namespace(CONCEPT_NAMESPACE, query_vector, top_k=2)
        detected_topic = get_top_concept_topic(concept_matches)

        question_filter = {"topic": {"$eq": detected_topic}} if detected_topic else None
        question_matches = query_namespace(
            QUESTION_NAMESPACE,
            query_vector,
            top_k=4,
            metadata_filter=question_filter,
        )

        print("CONCEPT_NAMESPACE =", CONCEPT_NAMESPACE)
        print("QUESTION_NAMESPACE =", QUESTION_NAMESPACE)
        print("DETECTED_TOPIC =", detected_topic)

        print("\n=== CONCEPT MATCHES ===")
        for match in concept_matches:
            metadata = get_match_metadata(match)
            print({
                "score": round(get_match_score(match), 4),
                "source_file": metadata.get("source_file"),
                "topic": metadata.get("topic"),
                "content_type": metadata.get("content_type"),
            })

        print("\n=== QUESTION MATCHES ===")
        for match in question_matches:
            metadata = get_match_metadata(match)
            print({
                "score": round(get_match_score(match), 4),
                "source_file": metadata.get("source_file"),
                "topic": metadata.get("topic"),
                "content_type": metadata.get("content_type"),
            })

        merged_matches = merge_results(concept_matches, question_matches, max_total=6)
        return format_retrieved_context(merged_matches)

    # Auto fallback keeps your old behavior
    if not is_exam_style_query(user_message):
        concept_matches = query_namespace(CONCEPT_NAMESPACE, query_vector, top_k=4)
        return format_retrieved_context(concept_matches)

    concept_matches = query_namespace(CONCEPT_NAMESPACE, query_vector, top_k=2)
    detected_topic = get_top_concept_topic(concept_matches)

    question_filter = {"topic": {"$eq": detected_topic}} if detected_topic else None
    question_matches = query_namespace(
        QUESTION_NAMESPACE,
        query_vector,
        top_k=4,
        metadata_filter=question_filter,
    )

    merged_matches = merge_results(concept_matches, question_matches, max_total=6)
    return format_retrieved_context(merged_matches)

def parse_form_chapter_query(user_message: str) -> tuple[int, int] | None:
    text = (user_message or "").lower()

    patterns = [
        # form first
        (r"form\s*(\d)\s*chapter\s*(\d+)", "form_first"),
        (r"tingkatan\s*(\d)\s*bab\s*(\d+)", "form_first"),
        (r"f\s*(\d)\s*c\s*(\d+)", "form_first"),

        # chapter first
        (r"chapter\s*(\d+)\s*(?:in|of|for)?\s*form\s*(\d)", "chapter_first"),
        (r"bab\s*(\d+)\s*(?:dalam|untuk)?\s*tingkatan\s*(\d)", "chapter_first"),
        (r"c\s*(\d+)\s*f\s*(\d)", "chapter_first"),
    ]

    for pattern, order in patterns:
        match = re.search(pattern, text)
        if match:
            if order == "form_first":
                form_no = int(match.group(1))
                chapter_no = int(match.group(2))
            else:
                chapter_no = int(match.group(1))
                form_no = int(match.group(2))

            return form_no, chapter_no

    return None

def get_chatbot_response(
    user_message,
    language="English",
    history_messages=None,
    agent_instruction=None,
    retrieval_mode="auto",
    retrieval_query=None,
    return_metadata=False,
):
    direct_chapter_answer = try_answer_chapter_map_query(user_message, language)

    if direct_chapter_answer:
        if return_metadata:
            return {
                "reply": direct_chapter_answer,
                "retrieved_refs_json": {
                    "retrieval_mode": "direct_chapter_map",
                    "retrieval_query": user_message,
                    "language": normalize_language(language),
                    "context_available": True,
                    "retrieved_context_text": "Answered from hardcoded SPM_CHAPTER_MAP.",
                },
            }

        return direct_chapter_answer

    language_label = get_language_label(language)
    conversation_history = format_conversation_history(history_messages or [])
    retrieved_context = retrieve_context(
        retrieval_query or user_message,
        retrieval_mode=retrieval_mode
    )

    llm = ChatOpenAI(
        model=os.getenv("GEMINI_CHAT_MODEL", "gemini-3.5-flash-lite"),
        temperature=0.3,
        api_key=os.getenv("GEMINI_API_KEY"),
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
    )

    system_prompt = f"""
You are EasyLearn, an AI tutor for SPM Mathematics students in Malaysia.

Your task:
- Answer as an SPM Mathematics tutor
- Use the retrieved knowledge base context first
- Use recent conversation history when it is relevant
- Stay focused on SPM Mathematics topics
- Explain clearly and simply
- Show step-by-step working when solving
- Include formulas when relevant
- Give the final answer clearly
- Use the student's requested language

IMPORTANT RULES:
- Prefer the retrieved context when it is relevant
- If the student asks a follow-up question, use the recent conversation history
- For conceptual tutoring questions, answer primarily from the retrieved concept notes
- For exam-style or worked-solution questions, you may use both concept notes and exam-question context
- Only add extra general math knowledge if the retrieved context is clearly insufficient, and keep it aligned with SPM level
- Keep explanations student-friendly
- Avoid overly advanced notation unless needed
- If the student ask to list the chapters in a form, use the chapter map from the knowledge base to ensure accuracy and return the topics name that belongs to the language selected.
- If the student asks about a form and chapter number, such as "Form 4 Chapter 3" or "Tingkatan 4 Bab 3", always verify the chapter title using the KSSM Mathematics Chapter. Never guess the chapter title from memory.
- If the student asks questions about a chapter without specifying the form, please double confirm with the user before proceeding.

Answer language: {language_label}

Learner-aware agent instruction:
{agent_instruction or "No learner-aware strategy provided. Use normal SPM tutoring style."}

Recent conversation history:
{conversation_history}

Retrieved knowledge base context:
{retrieved_context}
""".strip()

    user_prompt = f"Student question:\n{user_message}"

    response = llm.invoke(
        [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
    )

    retrieved_refs_json = {
        "retrieval_mode": retrieval_mode,
        "retrieval_query": retrieval_query or user_message,
        "language": normalize_language(language),
        "context_available": bool(
            retrieved_context
            and "No relevant knowledge base context retrieved" not in retrieved_context
            and "No knowledge base retrieval needed" not in retrieved_context
        ),
        "retrieved_context_text": retrieved_context,
    }

    if return_metadata:
        return {
            "reply": response.content,
            "retrieved_refs_json": retrieved_refs_json,
        }

    return response.content