import os
import re
import json
import base64
import asyncio
import mimetypes
import tempfile
from copy import deepcopy
from pathlib import Path
import cloudinary
import cloudinary.uploader
from parser.pdf_k2_parser import SPM_SYLLABUS_MAPPING
from parser.parser_common import (
    encode_image_to_data_url,
    fix_json_string,
    render_pdf_pages,
    page_in_selected_range,
    get_db_connection,
    insert_paper,
    insert_question,
    insert_marking_scheme,
    insert_question_marking_link,
    upload_cropped_diagram,
    crop_diagram_above_anchor,
)
from parser.metadata_classifier import apply_verified_chapters
K1_QUESTION_SEMAPHORE = None
K1_MARKING_SEMAPHORE = None
WORK_DIR = os.path.join(tempfile.gettempdir(), "mathsy_parsed_output_k1")
QUESTION_IMG_DIR = os.path.join(WORK_DIR, "question_pages")
MARKING_IMG_DIR = os.path.join(WORK_DIR, "marking_pages")
QUESTION_CROP_DIR = os.path.join(WORK_DIR, "question_crops")

cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
    secure=True
)
def attach_k1_question_diagram(
    q: dict,
    pdf_path: str,
    page_no: int,
    page_image_path: str,
    output_prefix: str,
    crop_dir: str
) -> dict:
    if not q.get("has_diagram"):
        q["diagram_path"] = ""
        q["_diagram_image_path"] = ""
        q["_diagram_public_id"] = ""
        return q

    os.makedirs(crop_dir, exist_ok=True)

    qno = str(q.get("question_no", "")).strip() or "unknown"

    cropped_path = os.path.join(
        crop_dir,
        f"{output_prefix}_Q{qno}_diagram.png"
    )

    cropped = crop_diagram_above_anchor(
        pdf_path=pdf_path,
        page_no=page_no,
        image_path=page_image_path,
        out_path=cropped_path,
        dpi=150,
        padding_percent=0.10
    )

    if not cropped:
        print(f"Could not crop diagram for K1 Q{qno}")
        q["diagram_path"] = ""
        q["_diagram_image_path"] = ""
        q["_diagram_public_id"] = ""
        return q

    uploaded = upload_cropped_diagram(
        cropped,
        folder="mathsy/k1_question_diagrams"
    )

    if uploaded:
        q["diagram_path"] = uploaded["url"]
        q["_diagram_image_path"] = uploaded["url"]
        q["_diagram_public_id"] = uploaded["public_id"]
    else:
        q["diagram_path"] = ""
        q["_diagram_image_path"] = ""
        q["_diagram_public_id"] = ""

    return q


K1_EXPECTED_SCHEMA = {
    "question_no": "",
    "question_type": "mcq",

    # LLM extraction
    "topic": "",
    "subtopic": "",
    "form": "",
    "chapter": "",

    # Backend verified classification
    "verified_form": "",
    "verified_chapter": "",
    "classification_status": "unclassified",
    "classification_confidence": 0.0,

    "instructions_en": [],
    "instructions_ms": [],
    "sequence": [],

    "equations": [],
    "expressions": [],
    "variables": [],
    "given_values": {},
    "table_data": {},
    "constraints": {},

    "options": [
        {
            "label": "A",
            "text_en": "",
            "text_ms": "",
            "has_image": False,
            "image_path": "",
            "visual_description": ""
        },
        {
            "label": "B",
            "text_en": "",
            "text_ms": "",
            "has_image": False,
            "image_path": "",
            "visual_description": ""
        },
        {
            "label": "C",
            "text_en": "",
            "text_ms": "",
            "has_image": False,
            "image_path": "",
            "visual_description": ""
        },
        {
            "label": "D",
            "text_en": "",
            "text_ms": "",
            "has_image": False,
            "image_path": "",
            "visual_description": ""
        }
    ],

    "target": "",

    # Question diagram
    "has_diagram": False,
    "diagram_type": "",
    "visual_semantic_summary": "",
    "diagram_path": "",
    "difficulty": "",
    "difficulty_level": 3,
    "marks": 1
}
K1_ANSWER_KEY_PROMPT = """
You are extracting the answer key for SPM Mathematics Paper 1 / Kertas 1.

The page contains a marking scheme table with question numbers and answers.

Return ONLY valid JSON in this exact format:
{
  "answers": [
    {
      "question_no": "",
      "correct_option": ""
    }
  ]
}

Rules:
1. Extract every question number and its correct option.
2. correct_option must be only one uppercase letter: A, B, C, or D.
3. Do not explain.
4. Do not extract marks, notes, or other text.
5. If the table is split into multiple column groups, extract all groups.
6. Sort answers by question_no ascending.
"""

async def parse_k1_answer_key_page_with_vision(
    image_path: str,
    openai_client,
    model: str = "gemini-3.5-flash-lite"
) -> dict:
    """
    Reads one K1 marking scheme page image and returns:
    {
        "1": "B",
        "2": "C",
        ...
    }
    """

    image_data_url = encode_image_to_data_url(image_path)

    response = await openai_client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": "You are a strict Kertas 1 answer key parser. Return JSON only."
            },
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": K1_ANSWER_KEY_PROMPT},
                    {"type": "image_url", "image_url": {"url": image_data_url}}
                ]
            }
        ],
        temperature=0,
        response_format={"type": "json_object"}
    )

    raw_text = response.choices[0].message.content.strip()

    try:
        parsed = json.loads(raw_text)
    except json.JSONDecodeError:
        cleaned_text = fix_json_string(raw_text)
        parsed = json.loads(cleaned_text)

    answers = parsed.get("answers", [])

    answer_key = {}

    for item in answers:
        qno = str(item.get("question_no", "")).strip()
        option = str(item.get("correct_option", "")).strip().upper()

        if qno.isdigit() and option in ["A", "B", "C", "D"]:
            answer_key[str(int(qno))] = option

    return dict(sorted(answer_key.items(), key=lambda x: int(x[0])))

def grade_k1_answer(student_option: str, correct_option: str) -> dict:
    student_option = str(student_option).strip().upper()
    correct_option = str(correct_option).strip().upper()

    is_correct = student_option == correct_option

    return {
        "is_correct": is_correct,
        "score": 1 if is_correct else 0,
        "max_score": 1,
        "student_option": student_option,
        "correct_option": correct_option
    }

def build_k1_marking_scheme(question_no: str, correct_option: str) -> dict:
    correct_option = str(correct_option).strip().upper()

    return {
        "group_id": "",
        "question_no": str(question_no).strip(),

        # K1 has no parts/subparts
        "part": "",
        "subpart": "",
        "sub_subpart": "",

        # For compatibility with your existing marking_schemes structure
        "subpart_marks": 1.0,
        "question_total_marks": 1.0,

        "answer_type": "mcq",
        "final_answer": correct_option,
        "answer_value": correct_option,
        "correct_option": correct_option,

        # K1 does not need official working steps
        "steps": [],

        "answer_range": [],
        "units": "",
        "method": "",

        "rounding_and_tolerance": {},
        "method_policy": {
            "required_method": "",
            "forbidden_methods": [],
            "working_required": False
        },

        "conditional_marking_rules": [],
        "graph_validation": {},
        "drawing_validation": {},
        "notes": [
            "Kertas 1 MCQ marking scheme. Award 1 mark if selected option matches correct_option."
        ],
        "answer_image_path": ""
    }


def normalize_k1_question(data: dict) -> dict:
    result = deepcopy(K1_EXPECTED_SCHEMA)

    for key in result:
        if key in data:
            result[key] = data[key]

    # List fields
    for field in [
        "instructions_en",
        "instructions_ms",
        "sequence",
        "equations",
        "expressions",
        "variables",
    ]:
        value = result.get(field)

        if isinstance(value, list):
            result[field] = [str(x).strip() for x in value if str(x).strip()]
        elif value in (None, ""):
            result[field] = []
        else:
            result[field] = [str(value).strip()]

    # Dict fields
    for field in ["given_values", "table_data", "constraints"]:
        if not isinstance(result.get(field), dict):
            result[field] = {}

    # Options
    options = result.get("options", [])

    if not isinstance(options, list):
        options = []

    normalized_options = []

    for label in ["A", "B", "C", "D"]:
        found = None

        for opt in options:
            if isinstance(opt, dict) and str(opt.get("label", "")).strip().upper() == label:
                found = opt
                break

        if found:
            normalized_options.append({
                "label": label,
                "text_en": str(found.get("text_en", "") or "").strip(),
                "text_ms": str(found.get("text_ms", "") or "").strip(),
                "has_image": bool(found.get("has_image", False)),
                "image_path": str(found.get("image_path", "") or "").strip(),
                "visual_description": str(found.get("visual_description", "") or "").strip(),
            })
        else:
            normalized_options.append({
                "label": label,
                "text_en": "",
                "text_ms": "",
                "has_image": False,
                "image_path": "",
                "visual_description": "",
            })

    result["options"] = normalized_options
    # Strings
    for field in [
        "question_no",
        "question_type",
        "topic",
        "subtopic",
        "form",
        "chapter",
        "target",
        "diagram_type",
        "visual_semantic_summary",
        "difficulty"
    ]:
        result[field] = "" if result.get(field) is None else str(result.get(field)).strip()

    result["question_type"] = "mcq"
    result["marks"] = 1.0
    result["has_diagram"] = bool(result.get("has_diagram", False))

    # Difficulty
    level, label = calculate_k1_difficulty(result)
    result["difficulty_level"] = level
    result["difficulty"] = label

    return result

def calculate_k1_difficulty(q: dict):
    text = " ".join(q.get("instructions_en", [])).lower()
    text += " " + " ".join(q.get("instructions_ms", [])).lower()
    text += " " + str(q.get("target", "")).lower()
    text += " " + str(q.get("diagram_type", "")).lower()
    text += " " + str(q.get("visual_semantic_summary", "")).lower()
    text += " " + str(q.get("topic", "")).lower()
    text += " " + str(q.get("subtopic", "")).lower()

    score = 1

    # Visual/table questions are usually harder
    if q.get("has_diagram") or q.get("table_data"):
        score += 1

    # Multi-step command keywords
    multi_step_keywords = [
        "calculate", "hitung",
        "find", "cari",
        "determine", "tentukan",
        "which of the following", "antara berikut",
        "represents", "mewakili",
        "satisfies", "memuaskan",
        "equivalent", "setara",
        "shortest path", "laluan terpendek",
        "shaded region", "kawasan berlorek",
        "negation", "penafian",
        "antecedent", "antejadian"
    ]

    if any(k in text for k in multi_step_keywords):
        score += 1

    # Known harder SPM K1 topics
    hard_signals = [
        "combined transformation", "gabungan transformasi",
        "transformation", "transformasi",
        "variance", "varians",
        "standard deviation", "sisihan piawai",
        "linear inequalities", "ketaksamaan linear",
        "shaded region", "kawasan berlorek",
        "matrix", "matrices", "matriks",
        "speed-time graph", "graf laju-masa",
        "distance-time graph", "graf jarak-masa",
        "inverse variation", "ubahan songsang",
        "direct variation", "ubahan langsung",
        "venn diagram", "gambar rajah venn",
        "shortest path", "laluan terpendek",
        "quadratic functions", "fungsi kuadratik"
    ]

    if any(k in text for k in hard_signals):
        score += 1

    # Lots of algebra/math expressions means more complex
    expression_count = len(q.get("equations", [])) + len(q.get("expressions", []))

    if expression_count >= 2:
        score += 1

    # Options with long text are often conceptual/harder
    options = q.get("options", [])
    option_text = " ".join(
        str(opt.get("text_en", "")) + " " + str(opt.get("text_ms", ""))
        for opt in options
        if isinstance(opt, dict)
    )

    if len(option_text) > 250:
        score += 1

    score = max(1, min(5, score))

    if score <= 2:
        return score, "Easy"
    elif score == 3:
        return score, "Moderate"
    else:
        return score, "Hard"


async def parse_k1_question_page_with_vision(image_path, openai_client, model="gemini-3.5-flash-lite"):
    page_schema = {"questions": [K1_EXPECTED_SCHEMA]}
    schema_text = json.dumps(page_schema, indent=2, ensure_ascii=False)
    syllabus_mapping_json = json.dumps(SPM_SYLLABUS_MAPPING, indent=2, ensure_ascii=False)

    image_data_url = encode_image_to_data_url(image_path)

    system_prompt = """
You are a strict SPM Mathematics Paper 1 MCQ parser.
Return JSON only.
Do not solve questions.
Do not choose answers.
""".strip()

    user_prompt = f"""
Parse this SPM Mathematics Paper 1 page.

Return ONLY valid JSON using this schema:
{schema_text}

Syllabus mapping:
{syllabus_mapping_json}

{K1_EXTRACTION_PROMPT}
""".strip()

    response = await openai_client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": user_prompt},
                    {"type": "image_url", "image_url": {"url": image_data_url}}
                ]
            }
        ],
        temperature=0,
        response_format={"type": "json_object"}
    )

    raw_text = response.choices[0].message.content.strip()

    try:
        parsed = json.loads(raw_text)
    except json.JSONDecodeError:
        cleaned_text = fix_json_string(raw_text)
        parsed = json.loads(cleaned_text)

    questions = parsed.get("questions", [])

    if not isinstance(questions, list):
        questions = []

    return [
        normalize_k1_question(q)
        for q in questions
        if isinstance(q, dict)
    ]

K1_EXTRACTION_PROMPT = """
You are a STRICT parser for SPM Mathematics Paper 1 multiple-choice questions.

Your task:
Extract all visible Kertas 1 / Paper 1 MCQ questions from the page image.

Return ONLY valid JSON with this structure:
{
  "questions": [
    {
      "question_no": "",
      "question_type": "mcq",
      "topic": "",
      "subtopic": "",
      "form": "",
      "chapter": "",
      "instructions_en": [],
      "instructions_ms": [],
      "sequence": [],
      "equations": [],
      "expressions": [],
      "variables": [],
      "given_values": {},
      "table_data": {},
      "constraints": {},
      "options": [
        {"label": "A", "text_en": "", "text_ms": ""},
        {"label": "B", "text_en": "", "text_ms": ""},
        {"label": "C", "text_en": "", "text_ms": ""},
        {"label": "D", "text_en": "", "text_ms": ""}
      ],
      "target": "",
      "has_diagram": false,
      "diagram_type": "",
      "visual_semantic_summary": "",
      "difficulty": "",
      "difficulty_level": 3,
      "marks": 1
    }
  ]
}

STRICT RULES:
1. Do NOT solve the question.
2. Do NOT choose the answer.
3. Extract every visible MCQ question on the page.
4. Each question must have exactly four options: A, B, C, and D.
5. If a question has Malay and English, separate them:
   - Malay text into instructions_ms / text_ms
   - English text into instructions_en / text_en
6. If a question has only one language visible, place it in the most appropriate field and leave the other empty.
7. Preserve mathematical expressions, fractions, matrices, coordinates, vectors, inequalities, and equations.
8. If options contain diagrams or visual choices, describe each option briefly in text_en/text_ms.
9. If a table is visible and needed to answer the question, extract it into table_data.
10. If a diagram, graph, Venn diagram, shaded region, Cartesian plane, geometry figure, or transformation diagram is visible, set has_diagram = true.
11. For diagrams, write a useful visual_semantic_summary. Include important labels, values, angles, coordinates, regions, and relationships.
12. Do not extract formula pages.
13. Do not extract answer key pages.
14. Do not create group_id, exercise_stage_id, stage_index, or grouped subparts.
15. Every K1 question is independent.
16. Set marks = 1.
17. Leave difficulty blank if unsure. Backend will calculate difficulty.

OPTION DIAGRAM RULE:
If only the answer choices A, B, C, and D are diagrams, do NOT set has_diagram = true for the main question.
Instead:
- keep has_diagram = false
- describe the option diagrams briefly inside each option's visual_description
- do not create image_0 in sequence

Only set has_diagram = true when there is a main question diagram, graph, table, Venn diagram, Cartesian plane, or geometry figure that appears before/above the answer options and is needed to solve the question.

SEQUENCE RULES:
- If question is Text → Options, use:
  "sequence": ["text_0"]
- If question is Text → Diagram → Command/Options, use:
  "sequence": ["text_0", "image_0", "text_1"]
- If question is Text → Table → Command/Options, use:
  "sequence": ["text_0", "table_0", "text_1"]
- If table_data is extracted, sequence MUST contain table_0.
- If has_diagram is true and the diagram is visually needed, sequence MUST contain image_0.
"""


def prepare_k1_question_for_insert(q: dict) -> dict:
    q["part"] = ""
    q["subpart"] = ""
    q["sub_subpart"] = ""

    q["group_id"] = ""
    q["group_form"] = ""
    q["group_chapter"] = ""

    q["exercise_stage_id"] = ""
    q["stage_index"] = 1
    q["unlock_after_stage_id"] = ""

    q["display_marks"] = 1.0
    q["marks_source"] = "mcq_answer_key"

    q["classification_status"] = q.get("classification_status", "unverified")
    q["classification_confidence"] = q.get("classification_confidence", 0.0)

    q["verified_form"] = q.get("verified_form", q.get("form", ""))
    q["verified_chapter"] = q.get("verified_chapter", q.get("chapter", ""))

    q["difficulty_group_level"] = q.get("difficulty_level", 3)
    q["group_difficulty_level"] = q.get("difficulty_level", 3)

    return q

async def parse_k1_answer_key_page_with_vision(
    image_path: str,
    openai_client,
    model: str = "gemini-3.5-flash-lite"
) -> dict:
    """
    Reads one K1 marking scheme page image and returns:
    {
        "1": "B",
        "2": "C",
        ...
    }
    """

    image_data_url = encode_image_to_data_url(image_path)

    response = await openai_client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": "You are a strict Kertas 1 answer key parser. Return JSON only."
            },
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": K1_ANSWER_KEY_PROMPT},
                    {"type": "image_url", "image_url": {"url": image_data_url}}
                ]
            }
        ],
        temperature=0,
        response_format={"type": "json_object"}
    )

    raw_text = response.choices[0].message.content.strip()

    try:
        parsed = json.loads(raw_text)
    except json.JSONDecodeError:
        cleaned_text = fix_json_string(raw_text)
        parsed = json.loads(cleaned_text)

    answers = parsed.get("answers", [])

    answer_key = {}

    for item in answers:
        qno = str(item.get("question_no", "")).strip()
        option = str(item.get("correct_option", "")).strip().upper()

        if qno.isdigit() and option in ["A", "B", "C", "D"]:
            answer_key[str(int(qno))] = option

    return dict(sorted(answer_key.items(), key=lambda x: int(x[0])))


def insert_k1_answer_for_question(conn, paper_id, question_id, question_no, answer_key, question_data=None):
    correct_option = answer_key.get(str(question_no))

    if not correct_option:
        print(f"No answer found for K1 Q{question_no}")
        return None

    marking = build_k1_marking_scheme(
        question_no=str(question_no),
        correct_option=correct_option
    )

    marking_id = insert_marking_scheme(conn, paper_id, marking)
    insert_question_marking_link(conn, question_id, marking_id, "matched_exact")

    return marking_id

async def parse_k1_answer_key_pdf(
    marking_pdf_path: str,
    openai_client,
    output_prefix: str = "K1_Marking",
    start_page: int = 1,
    end_page: int | None = None,
    model: str = "gemini-3.5-flash-lite",
    out_dir: str = MARKING_IMG_DIR
) -> dict:
    """
    Renders marking scheme PDF pages and extracts K1 answer key.
    """

    page_infos = render_pdf_pages(
        pdf_path=marking_pdf_path,
        out_dir=out_dir,
        dpi=150,
        prefix=f"{output_prefix}_answer_key"
    )

    combined_answer_key = {}

    for page_info in page_infos:
        page_no = int(page_info["page_no"])

        if page_no < start_page:
            continue

        if end_page and page_no > end_page:
            continue

        image_path = page_info["page_image_path"]

        print(f"Reading K1 answer key page {page_no}...")

        page_answer_key = await parse_k1_answer_key_page_with_vision(
            image_path=image_path,
            openai_client=openai_client,
            model=model
        )

        combined_answer_key.update(page_answer_key)

    return dict(sorted(combined_answer_key.items(), key=lambda x: int(x[0])))

def validate_k1_answer_key(answer_key: dict, expected_total: int = 40) -> bool:
    missing = []
    invalid = []

    for i in range(1, expected_total + 1):
        qno = str(i)

        if qno not in answer_key:
            missing.append(qno)
        elif answer_key[qno] not in ["A", "B", "C", "D"]:
            invalid.append(qno)

    if missing:
        print(f"Missing K1 answers: {missing}")

    if invalid:
        print(f"Invalid K1 answers: {invalid}")

    return not missing and not invalid

async def smart_k1_question_wrapper(
    page_info: dict,
    question_pdf_path: str,
    question_client,
    question_model: str,
    output_prefix: str,
    crop_dir: str,
    max_retries: int = 3
):
    """
    Parses one K1 question page safely.
    Uses semaphore so pages can run concurrently without sending too many API calls at once.
    Also crops/uploads main question diagrams after parsing.
    """
    global K1_QUESTION_SEMAPHORE

    if K1_QUESTION_SEMAPHORE is None:
        K1_QUESTION_SEMAPHORE = asyncio.Semaphore(2)

    page_no = int(page_info["page_no"])
    page_image_path = page_info["page_image_path"]

    for attempt in range(max_retries):
        try:
            async with K1_QUESTION_SEMAPHORE:
                await asyncio.sleep(1)

                page_questions = await parse_k1_question_page_with_vision(
                    image_path=page_image_path,
                    openai_client=question_client,
                    model=question_model
                )

            enriched_questions = []

            for q in page_questions:
                q["_page_no"] = page_no
                q["_page_image_path"] = page_image_path

                q = attach_k1_question_diagram(
                    q=q,
                    pdf_path=question_pdf_path,
                    page_no=page_no,
                    page_image_path=page_image_path,
                    output_prefix=output_prefix,
                    crop_dir=crop_dir
                )

                enriched_questions.append(q)

            print(f"✅ Parsed K1 question page {page_no}: {len(enriched_questions)} questions")
            return enriched_questions

        except Exception as e:
            error_msg = str(e).lower()

            if "429" in error_msg:
                print(f"⏳ Rate limit on K1 question page {page_no}. Waiting 60s...")
                await asyncio.sleep(60)
                continue

            if attempt < max_retries - 1 and (
                "500" in error_msg
                or "timeout" in error_msg
                or "timed out" in error_msg
            ):
                wait_time = 5 * (attempt + 1)
                print(f"🔄 Retry K1 question page {page_no} in {wait_time}s...")
                await asyncio.sleep(wait_time)
                continue

            print(f"⚠️ Failed K1 question page {page_no}: {e}")
            return []

    return []


async def smart_k1_answer_key_wrapper(
    page_info: dict,
    marking_client,
    marking_model: str,
    max_retries: int = 3
):
    """
    Parses one K1 answer key page safely.
    """
    global K1_MARKING_SEMAPHORE

    if K1_MARKING_SEMAPHORE is None:
        K1_MARKING_SEMAPHORE = asyncio.Semaphore(2)

    page_no = int(page_info["page_no"])
    image_path = page_info["page_image_path"]

    for attempt in range(max_retries):
        try:
            async with K1_MARKING_SEMAPHORE:
                await asyncio.sleep(1)

                page_answer_key = await parse_k1_answer_key_page_with_vision(
                    image_path=image_path,
                    openai_client=marking_client,
                    model=marking_model
                )

            print(f"✅ Parsed K1 answer key page {page_no}: {len(page_answer_key)} answers")
            return page_answer_key

        except Exception as e:
            error_msg = str(e).lower()

            if "429" in error_msg:
                print(f"⏳ Rate limit on K1 answer key page {page_no}. Waiting 60s...")
                await asyncio.sleep(60)
                continue

            if attempt < max_retries - 1 and (
                "500" in error_msg
                or "timeout" in error_msg
                or "timed out" in error_msg
            ):
                wait_time = 5 * (attempt + 1)
                print(f"🔄 Retry K1 answer key page {page_no} in {wait_time}s...")
                await asyncio.sleep(wait_time)
                continue

            print(f"⚠️ Failed K1 answer key page {page_no}: {e}")
            return {}

    return {}
async def parse_k1_answer_key_pdf(
    marking_pdf_path: str,
    openai_client,
    output_prefix: str = "K1_Marking",
    start_page: int = 1,
    end_page: int | None = None,
    model: str = "gemini-3.5-flash-lite",
    out_dir: str = MARKING_IMG_DIR
) -> dict:
    """
    Renders marking scheme PDF pages and extracts K1 answer key concurrently.
    """

    page_infos = render_pdf_pages(
        pdf_path=marking_pdf_path,
        out_dir=out_dir,
        dpi=150,
        prefix=f"{output_prefix}_answer_key"
    )

    tasks = []

    for page_info in page_infos:
        page_no = int(page_info["page_no"])

        if page_no < start_page:
            continue

        if end_page and page_no > end_page:
            continue

        print(f"Queueing K1 answer key page {page_no}...")

        tasks.append(
            smart_k1_answer_key_wrapper(
                page_info=page_info,
                marking_client=openai_client,
                marking_model=model
            )
        )

    print(f"Queued {len(tasks)} K1 answer key pages.")

    results = await asyncio.gather(*tasks, return_exceptions=True)

    combined_answer_key = {}

    for result in results:
        if isinstance(result, Exception):
            print(f"⚠️ Answer key task failed: {result}")
            continue

        if isinstance(result, dict):
            combined_answer_key.update(result)

    return dict(sorted(combined_answer_key.items(), key=lambda x: int(x[0])))

async def process_k1_pdf(
    question_pdf_path: str,
    marking_pdf_path: str,
    question_client,
    marking_client,
    output_prefix: str = "Johor_2025_K1",
    question_start_page: int = 3,
    question_end_page: int | None = None,
    marking_start_page: int = 1,
    marking_end_page: int | None = None,
    exam_name: str = "SPM Trial",
    subject: str = "Mathematics",
    year: int = 2025,
    question_model: str = "gemini-3.5-flash-lite",
    marking_model: str = "gemini-3.5-flash-lite",
):

    os.makedirs(WORK_DIR, exist_ok=True)
    os.makedirs(QUESTION_IMG_DIR, exist_ok=True)
    os.makedirs(MARKING_IMG_DIR, exist_ok=True)
    os.makedirs(QUESTION_CROP_DIR, exist_ok=True)

    # 1. Read K1 answer key first
    answer_key = await parse_k1_answer_key_pdf(
        marking_pdf_path=marking_pdf_path,
        openai_client=marking_client,
        output_prefix=output_prefix,
        start_page=marking_start_page,
        end_page=marking_end_page,
        model=marking_model,
        out_dir=MARKING_IMG_DIR
    )

    validate_k1_answer_key(answer_key, expected_total=40)

    # 2. Render question pages
    page_infos = render_pdf_pages(
        pdf_path=question_pdf_path,
        out_dir=QUESTION_IMG_DIR,
        dpi=150,
        prefix=output_prefix
    )

    tasks = []

    for page_info in page_infos:
        page_no = int(page_info["page_no"])

        if not page_in_selected_range(
            page_no,
            start_page=question_start_page,
            end_page=question_end_page
        ):
            continue

        print(f"Queueing K1 question page {page_no}...")

        tasks.append(
            smart_k1_question_wrapper(
                page_info=page_info,
                question_pdf_path=question_pdf_path,
                question_client=question_client,
                question_model=question_model,
                output_prefix=output_prefix,
                crop_dir=QUESTION_CROP_DIR
            )
        )

    print(f"Queued {len(tasks)} K1 question pages.")

    results = await asyncio.gather(*tasks, return_exceptions=True)

    all_questions = []

    for result in results:
        if isinstance(result, Exception):
            print(f"⚠️ Question task failed: {result}")
            continue

        if isinstance(result, list):
            all_questions.extend(result)

    # 3. Apply your metadata classifier
    all_questions = apply_verified_chapters(all_questions)

    prepared = []

    for q in all_questions:
        q["form"] = q.get("verified_form") or q.get("form", "")
        q["chapter"] = q.get("verified_chapter") or q.get("chapter", "")

        level, label = calculate_k1_difficulty(q)
        q["difficulty_level"] = level
        q["difficulty"] = label

        q = prepare_k1_question_for_insert(q)
        prepared.append(q)

    # 4. Save backup JSON
    out_json = os.path.join(WORK_DIR, f"{output_prefix}_parsed_k1_questions.json")

    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(prepared, f, ensure_ascii=False, indent=2)

    print(f"Saved K1 parsed questions to {out_json}")

    # 5. Insert into DB
    conn = get_db_connection()

    paper_id = insert_paper(
        conn=conn,
        title=os.path.basename(question_pdf_path),
        paper_type="kertas1",
        file_path=question_pdf_path,
        exam_name=exam_name,
        subject=subject,
        year=year
    )

    for q in prepared:
        image_path = q.get("_diagram_image_path") or q.get("diagram_path") or None

        q_id = insert_question(
            conn,
            paper_id=paper_id,
            question_data=q,
            image_path=image_path
        )

        insert_k1_answer_for_question(
            conn=conn,
            paper_id=paper_id,
            question_id=q_id,
            question_no=q.get("question_no"),
            answer_key=answer_key,
            question_data=q
        )

    conn.close()

    print("K1 parsing complete.")

    

if __name__ == "__main__":
    import asyncio
    from dotenv import load_dotenv
    from openai import AsyncOpenAI

    load_dotenv()

    # ==============================
    # Clients
    # ==============================
    openai_async_client = AsyncOpenAI(
        api_key=os.getenv("GEMINI_API_KEY"),
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
    )

    # If you want to use OpenAI for both question parsing and K1 answer-key parsing
    question_client = openai_async_client
    marking_client = openai_async_client

    # ==============================
    # File paths
    # ==============================
    base_dir = r"C:\Users\YK\Documents\Degree Y3\FYP\Test Paper"

    question_pdf_path = os.path.join(
        base_dir,
        "TRIAL JOHOR K1 2025 - SET 2.pdf"
    )

    marking_pdf_path = os.path.join(
        base_dir,
        "SKEMA KERTAS 1 SET 2.pdf"
    )

    # ==============================
    # Safety check
    # ==============================
    if not os.path.exists(question_pdf_path):
        raise FileNotFoundError(f"Question PDF not found: {question_pdf_path}")

    if not os.path.exists(marking_pdf_path):
        raise FileNotFoundError(f"Marking PDF not found: {marking_pdf_path}")

    # ==============================
    # Run K1 parser
    # ==============================
    asyncio.run(
        process_k1_pdf(
            question_pdf_path=question_pdf_path,
            marking_pdf_path=marking_pdf_path,

            question_client=question_client,
            marking_client=marking_client,

            output_prefix="Johor_2025_K1_Set2",

            # For the Johor K1 paper you uploaded:
            # Pages 1-2 are formula pages.
            # Page 3 onwards are questions.
            question_start_page=3,
            # Change this based on where the K1 answer key starts in your marking PDF.
            marking_start_page=2,
            exam_name="SPM Trial Johor 2025 Set 2",
            subject="Mathematics",
            year=2025,

            question_model="gemini-3.5-flash-lite",
            marking_model="gemini-3.5-flash-lite"
        )
    )