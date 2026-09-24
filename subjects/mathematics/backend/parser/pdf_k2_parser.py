from copy import deepcopy
import sys
# Force UTF-8 encoding for standard output to prevent print() crashes on Windows
sys.stdout.reconfigure(encoding='utf-8')
import asyncio
import base64
import mimetypes
import tempfile
import os
import re
import json
import cloudinary
import cloudinary.uploader
import cv2
from dotenv import load_dotenv
import fitz  # PyMuPDF
from json_repair import repair_json
import mysql.connector
from mysql.connector import Error
import os
from openai import AsyncOpenAI, OpenAI
import pytesseract
from parser.metadata_classifier import (
    apply_group_difficulty_from_stage_logic,
    apply_group_form_chapter,
    apply_verified_chapters,
    apply_question_grouping,
    apply_marking_grouping,
    assign_exercise_stages_by_page,
    inherit_group_chapter_for_blank_parts,
    sync_display_marks_from_markings
)
from parser.parser_common import (
    upload_cropped_diagram,
    enforce_rate_limit,
    encode_image_to_data_url,
    fix_json_string,
    clean_part_label,
    extract_pdf_page_texts,
    render_pdf_pages,
    page_in_selected_range,
    get_db_connection,
    insert_paper,
    insert_question,
    insert_marking_scheme,
    insert_question_marking_link,
    crop_diagram_above_anchor,
)

load_dotenv()

cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_CLOUD_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_CLOUD_API_SECRET")
)


gemini_api_key = os.getenv("GEMINI_API_KEY", "").strip()

if not gemini_api_key:
    raise RuntimeError("GEMINI_API_KEY is missing from the Mathematics backend .env file")

client = OpenAI(
    api_key=gemini_api_key,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
)

gemini_async_client = AsyncOpenAI(
    api_key=gemini_api_key,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
    max_retries=3,
)

# These older variable names are retained because other project code uses them.
openai_async_client = gemini_async_client
openai_client = client


RATE_LIMIT_LOCK = None
LAST_API_CALL_TIME = 0.0

        

SPM_SYLLABUS_MAPPING = {
    # =========================
    # NUMBERS & ALGEBRA
    # =========================
    "Numbers and Arithmetic": [
        "Rational Numbers",
        "Factors and Multiples",
        "Squares, Square Roots, Cubes",
        "Standard Form",
        "Indices"
    ],

    "Algebra": [
        "Algebraic Expressions",
        "Algebraic Formulae",
        "Expansion and Factorisation",
        "Algebraic Fractions"
    ],

    "Equations and Inequalities": [
        "Linear Equations",
        "Simultaneous Equations",
        "Linear Inequalities",
        "Quadratic Equations"
    ],

    "Functions and Graphs": [
        "Functions",
        "Graphs of Functions",
        "Quadratic Functions",
        "Graphs of Motion",
        "Gradient of Straight Line"
    ],

    "Sequences and Patterns": [
        "Patterns",
        "Sequences"
    ],

    # =========================
    # GEOMETRY
    # =========================
    "Geometry": [
        "Lines and Angles",
        "Polygons",
        "Circles",
        "Angles and Tangents of Circles",
        "Loci in Two Dimensions"
    ],

    "Mensuration": [
        "Perimeter and Area",
        "Surface Area",
        "Volume of Solids"
    ],

    "Trigonometry": [
        "Trigonometric Ratios",
        "Trigonometric Graphs"
    ],

    "Transformations": [
        "Translation",
        "Reflection",
        "Rotation",
        "Enlargement",
        "Combined Transformations",
        "Symmetry"
    ],

    "Coordinate Geometry": [
        "Cartesian Coordinate System",
        "Distance",
        "Midpoint",
        "Straight Lines"
    ],

    "3D Geometry": [
        "Three-Dimensional Shapes",
        "Plans and Elevations",
        "Geometric Properties of 3D Shapes"
    ],

    # =========================
    # STATISTICS & PROBABILITY
    # =========================
    "Statistics": [
        "Data Handling",
        "Measures of Central Tendency",
        "Measures of Dispersion"
    ],

    "Probability": [
        "Simple Probability",
        "Combined Events"
    ],

    # =========================
    # DISCRETE / LOGIC
    # =========================
    "Sets and Logic": [
        "Sets",
        "Logical Reasoning"
    ],

    "Graph Theory": [
        "Network in Graph Theory"
    ],

    # =========================
    # APPLIED / REAL WORLD
    # =========================
    "Financial Mathematics": [
        "Savings and Investments",
        "Credit and Debt",
        "Insurance",
        "Taxation"
    ],

    "Variation": [
        "Direct Variation",
        "Inverse Variation",
        "Combined Variation"
    ],

    "Matrices": [
        "Matrices",
        "Matrix Operations"
    ],

    "Mathematical Modeling": [
        "Mathematical Modeling"
    ],

    "Rates and Motion": [
        "Speed",
        "Acceleration"
    ]
}

LLM_EXPECTED_SCHEMA = {
  "question_no": "",
  "part": "",
  "subpart": "",
  "sub_subpart": "",
  "question_type": "",
  "topic": "",
  "subtopic": "",
  "form": "",
  "chapter": "",
  "introductory_instructions_en": "",
  "introductory_instructions_ms": "",
  "instructions_en": [],
  "instructions_ms": [],
  "sequence": [],
  "equations": [],
  "expressions": [],
  "variables": [],
  "given_values": {},
  "table_data": {},
  "constraints": {},
  "options": [],
  "target": "",
  "requires_next_page": False,
  "has_diagram": False,
  "diagram_type": "",
  "difficulty": "",
  "marks": 0,
  "visual_semantic_summary": ""
}
EXPECTED_SCHEMA = {
  **LLM_EXPECTED_SCHEMA,
  "group_id": "",
  "verified_form": "",
  "verified_chapter": "",
  "classification_status": "unclassified",
  "classification_confidence": 0.0,
  "difficulty_level": 3,
  "group_difficulty_level": 3,
  "group_form": "",
  "group_chapter": "",
  "exercise_stage_id": "",
  "stage_index": 1,
  "unlock_after_stage_id": "",
  "display_marks": 0.0,
  "marks_source": "",
}

EXPECTED_MARKING_SCHEMA = {
    "group_id": "",
    "question_no": "",
    "part": "",
    "subpart": "",
    "sub_subpart": "",
    "subpart_marks": 0.0,           
    "question_total_marks": 0.0,    
    "answer_type": "",            # numeric | text | equation | coordinate | range | table | drawing | graph
    "final_answer": "",           
    "answer_value": "",           # Explicit value (e.g., 36.13 or "[-8, 8]")
    "answer_range": [],           # Array [min, max] for inequalities
    "units": "",                  # e.g., cm, ms^-1, jam
    "method": "",
    "steps": [],
        "rounding_and_tolerance": {
        "numeric_tolerance": 0.0,
        "accepted_decimal_places": 2,
        "accepted_exact_forms": ["e.g., \\pi/2", "sqrt(3)"],
        "accepted_equivalent_forms": ["e.g., 564 2/3", "1694/3"]
    },
    "method_policy": {
        "required_method": "e.g., matrix, substitution, graph",
        "forbidden_methods": ["e.g., trial and error"],
        "working_required": True
    },
    "conditional_marking_rules": [
        {
            "condition": "e.g., correct final answer seen without working",
            "action": "award 0 marks"
        },
        {
            "condition": "e.g., 1 or 2 points plotted incorrectly",
            "action": "award 1 mark instead of 2"
        }
    ],
    "graph_validation": {
        "required_points": [[0, -5], [2, -5]],
        "required_lines_or_curves": ["y = -5", "smooth curve passing through all points"],
        "plot_tolerance": "+/- 0.5 small square",
        "axis_requirements": "e.g., uniform scale 2cm to 1 unit"
    },
    "drawing_validation": {
        "required_shapes": ["rectangle", "dashed line for hidden edge"],
        "required_dimensions": ["4 cm", "3 cm"],
        "required_angles": ["90 degree"],
        "allowed_alternatives": ["accept mirrored drawing"]
    },         
    "notes": [],
    "answer_image_path": ""
}

def get_marks_for_difficulty(question_data: dict) -> float:
    """
    Prefer display_marks from marking scheme.
    Fall back to raw extracted marks.
    """
    if question_data.get("marks_source") == "marking_scheme":
        try:
            return float(question_data.get("display_marks", 0) or 0)
        except (TypeError, ValueError):
            return 0.0

    try:
        return float(question_data.get("marks", 0) or 0)
    except (TypeError, ValueError):
        return 0.0
def difficulty_label_from_score(score: float):
    if score <= 3:
        level = 1
    elif score <= 4:
        level = 2
    elif score <= 6:
        level = 3
    elif score <= 8:
        level = 4
    else:
        level = 5

    if level <= 2:
        label = "Easy"
    elif level == 3:
        label = "Moderate"
    else:
        label = "Hard"

    return level, label

def calculate_spm_difficulty(question_data: dict) -> str:
    marks = get_marks_for_difficulty(question_data)

    text = " ".join(question_data.get("instructions_en", [])).lower()
    text += " " + " ".join(question_data.get("instructions_ms", [])).lower()
    text += " " + str(question_data.get("diagram_type", "")).lower()
    text += " " + str(question_data.get("visual_semantic_summary", "")).lower()

    has_diagram = bool(question_data.get("has_diagram", False))
    has_table = bool(question_data.get("table_data", {}))

    subpart = str(question_data.get("subpart", "")).strip()
    sub_subpart = str(question_data.get("sub_subpart", "")).strip()

    core_score = 0.0

    # 1. Marks score
    if marks <= 2:
        core_score += 1
    elif marks <= 4:
        core_score += 2
    elif marks <= 6:
        core_score += 3
    else:
        core_score += 4

    # 2. Subpart depth
    if subpart:
        core_score += 0.5

    if sub_subpart:
        core_score += 1

    # 3. Hard keywords
    hard_keywords = [
        "justify", "hence", "determine whether",
        "maximum", "minimum", "draw", "shade", "construct",
        "sketch", "conclusion",
        "beri justifikasi", "seterusnya", "tentukan sama ada",
        "maksimum", "minimum", "lukis", "lorek", "kesimpulan"
    ]

    if any(keyword in text for keyword in hard_keywords):
        core_score += 1

    shared_bonus = 0.0

    if has_diagram:
        shared_bonus += 1

    if has_table:
        shared_bonus += 1

    total_score = core_score + shared_bonus
    question_data["difficulty_core_score"] = core_score
    question_data["difficulty_visual_score"] = shared_bonus
    question_data["difficulty_score"] = total_score

    level, label = difficulty_label_from_score(total_score)
    question_data["difficulty_level"] = level

    return label

def normalize_marking_output(data: dict) -> dict:
    result = EXPECTED_MARKING_SCHEMA.copy()

    for key in result:
        if key in data:
            result[key] = data[key]

    try:
        result["subpart_marks"] = float(result.get("subpart_marks", 0))
    except (TypeError, ValueError):
        result["subpart_marks"] = 0.0

    try:
        result["question_total_marks"] = float(result.get("question_total_marks", 0))
    except (TypeError, ValueError):
        result["question_total_marks"] = 0.0

    # Ensure drawing_rules is always a dictionary
    for dict_field in ["rounding_and_tolerance", "method_policy", "graph_validation", "drawing_validation"]:
        if not isinstance(result.get(dict_field), dict):
            result[dict_field] = {}
            
    # Ensure conditional rules is a list
    if not isinstance(result.get("conditional_marking_rules"), list):
        result["conditional_marking_rules"] = []

    # String fields (Allow final_answer to remain a list if it's a table/matrix)
    for field in [
        "group_id",
        "question_no",
        "part",
        "subpart",
        "sub_subpart",
        "method",
        "answer_image_path",
        "answer_type",
        "units"
    ]:
        value = result.get(field)
        result[field] = "" if value is None else str(value).strip()

    if not isinstance(result.get("answer_range"), list):
            result["answer_range"] = []

    val = result.get("answer_value")
    result["answer_value"] = "" if val is None else str(val).strip()

    if isinstance(result["final_answer"], list):
        # Keep tables/matrices as lists
        pass
    else:
        result["final_answer"] = "" if result["final_answer"] is None else str(result["final_answer"]).strip()
    # notes
    if not isinstance(result["notes"], list):
        result["notes"] = [] if result["notes"] in (None, "") else [str(result["notes"]).strip()]
    else:
        result["notes"] = [str(x).strip() for x in result["notes"] if str(x).strip()]

    # steps
    if not isinstance(result["steps"], list):
        result["steps"] = []

    result["part"] = clean_part_label(result.get("part", ""))
    result["subpart"] = clean_part_label(result.get("subpart", ""))
    result["sub_subpart"] = clean_part_label(result.get("sub_subpart", ""))
    normalized_steps = []
    for i, step in enumerate(result["steps"], start=1):
        if not isinstance(step, dict):
            continue

        marks_val = step.get("marks", 0)
        try:
            marks_val = float(marks_val)
        except (TypeError, ValueError):
            marks_val = 0
        answer_val = step.get("answer", "")

        required_val = step.get("required", True)
        if isinstance(required_val, str):
            required_val = required_val.lower() == "true"
        else:
            required_val = bool(required_val)

        if isinstance(answer_val, list):
            answer_val = [str(x).strip() for x in answer_val if str(x).strip()]
        elif answer_val in (None, ""):
            answer_val = ""
        else:
            answer_val = str(answer_val).strip()
        keywords_val = step.get("keywords", [])
        if isinstance(keywords_val, list):
            keywords_val = [str(x).strip() for x in keywords_val if str(x).strip()]
        else:
            keywords_val = []
            
        normalized_steps.append({
            "step_no": int(step.get("step_no", i)) if str(step.get("step_no", i)).isdigit() else i,
            "label": str(step.get("label", "")).strip(),
            "marks": marks_val,
            "required": required_val,
            "answer": answer_val,
            "keywords": keywords_val
        })

    result["steps"] = normalized_steps
    return result

async def parse_marking_page_with_vision(image_path, client, model="gemini-3.5-flash-lite"):
    system_prompt = r"""
You are a STRICT data extraction engine for SPM mathematics marking schemes. 
Your singular goal is to extract precise, programmatic grading constraints.

Strict rules:
1. Do NOT solve the question or summarize the logic.
2. Return a JSON object with a top-level key: "markings".
3. "markings" must be a list of marking scheme objects.
4. Split question parts separately, e.g. 5(a), 5(b), 5(a)(i).
5. NEW RULE FOR NESTED NUMBERING: If a marking entry is labelled 11(b)(i)(a), you MUST split it accurately using the "sub_subpart" field.
   Example: "question_no": "11", "part": "b", "subpart": "i", "sub_subpart": "a". Do NOT merge "i" and "a" into one string.
6. Extract EXACT mathematical strings, symbols, and geometry constraints.
7. Return valid JSON only. No markdown, no explanations.
8. If it is objective answer, skip that page.
9. MATH OCR GUARDRAIL (CRITICAL): You are strictly FORBIDDEN from outputting raw, vertical, disconnected text for equations or matrices. If you see a fraction, matrix, or multi-line equation, you MUST format it as a single, clean horizontal line of LaTeX (e.g., \begin{pmatrix} 2 & 3 \\ 0 & 4 \end{pmatrix}).
""".strip()

    page_schema = {
        "markings": [EXPECTED_MARKING_SCHEMA]
    }

    schema_text = json.dumps(page_schema, indent=2)
    image_data_url = encode_image_to_data_url(image_path)

    user_prompt = f"""
Parse this full SPM mathematics marking scheme page into JSON.

Return ONLY valid JSON using this schema:
{schema_text}

CRITICAL EXTRACTION RULES:
-- U may IGNORE group_id as it will be filled later on by the backend based on question grouping. But ALL other fields must be extracted as accurately as possible.
1. VISUAL ANSWERS (GRAPHS & DRAWINGS) ARE NOT APPENDICES:
- If a page shows a plotted graph (histogram, ogive, shaded region, box plot) or a geometric drawing intended as the final answer, YOU MUST EXTRACT IT. Do NOT skip it.
- If the page has NO explicit marking text (e.g., P1, K1), but clearly shows the visual answer, create a marking object with the correct "question_no" (usually found at the top).
- Set "answer_type" to "graph" or "drawing", and thoroughly describe the visual in "graph_validation" or "drawing_validation".

2. METHOD POLICY (CRITICAL):
- Read the notes for phrases like "Tidak dibenarkan menggunakan selain kaedah matriks" (Do not accept other than matrix method) or "solution without working gets 0m".
- Translate these into the "method_policy" object. Set "required_method" or populate "forbidden_methods" accordingly. Set "working_required" to true if the final answer alone scores 0.

3. CONDITIONAL MARKING RULES:
- Translate conditional text notes (e.g., "accept 1-2 mistakes for 1 mark", "seen award 1 mark", "P1 - 1 kesilapan") into the "conditional_marking_rules" array. 
- Format them strictly as {{"condition": "...", "action": "..."}}.

4. ROUNDING AND EQUIVALENT FORMS:
- Do not leave "answer_range" empty if the scheme explicitly provides equivalent fractions or decimals. 
- Populate "rounding_and_tolerance" with "accepted_equivalent_forms" (e.g., ["1694/3", "564 2/3"]) and "accepted_decimal_places".

4. GRAPH VALIDATION (CARTESIAN & PLOTTING):
- For coordinate-based Graph questions (Ogives, Histograms, Functions), leave "drawing_validation" empty.
- Populate "graph_validation" with explicit structures: "required_points", "required_lines_or_curves", and exact "plot_tolerance" (e.g., "+/- 0.5 small square").

5. DRAWING & CONSTRUCTION VALIDATION (GEOMETRY & PLANS):
- For geometric drawings (Plans, Elevations, Loci, Polygons), leave "graph_validation" empty.
- Populate "drawing_validation" with physical constraints: "required_shapes", "required_dimensions", "required_angles", and "allowed_alternatives".

6. STRUCTURED ANSWERS & UNITS:
- "answer_type": MUST be exactly one of: "numeric", "text", "equation", "coordinate", "range", "table", "drawing", or "graph".
- "answer_value": If the answer is a specific number (36.13) or coordinate ([-8, 8]), extract it here cleanly.
- "answer_range": If the answer is an inequality range (e.g., 3.65 <= x <= 3.75), extract as an array of floats: [3.65, 3.75].
- "numeric_tolerance": If the answer is a decimal/float, provide an acceptable rounding tolerance (e.g., 0.01). If it is an exact integer, use 0.0.
- "units": Extract explicit units separately (e.g., "cm", "cm²", "ms^-1", "batu nautika", "jam", "°", "°T"). Do not leave units in the answer_value field.
- SPECIFIC TYPING RULES:
  * For simultaneous equations (e.g., x=10, y=8), use "numeric" or "equation", NOT "coordinate".
  * For bearings (e.g., 65°T or 065°), use "numeric" and put "°T" or "°U" in the units field.

7. NON-VISUAL QUESTIONS:
- If it is a standard calculation or word problem, leave BOTH "graph_validation" and "drawing_validation" empty {{}}.

8. MARKS SEPARATION (NO MIXING):
- "subpart_marks": The exact marks awarded for THIS specific part/subpart ONLY (usually the sum of the step marks, e.g., 3).
- "question_total_marks": The overall total for the entire question block (usually found floating in the far right margin, e.g., 12 or 15). Do NOT put the overall total into the "subpart_marks".

9. ANTI-SUMMARIZATION (FINAL ANSWER):
- Do NOT write descriptive summaries like "Table of outcomes" or "Graph with line".
- If the final answer is a table, extract the table data as a 2D array of strings and put it directly into "final_answer".
- If the final answer is a matrix or a set of coordinates, extract the exact mathematical text.
- If the answer is purely a drawing, leave "final_answer" empty and use "drawing_validation" or "graph_validation" instead.

9. EXHAUSTIVE NOTES EXTRACTION:
- Scan the page for conditional grading rules and extract them into the "notes" array.
- Look explicitly for: "atau setara" (or equivalent), "terima" (accept), "seen award P1", "jika jadual tidak lengkap" (if table is incomplete). 

10. STEP-BY-STEP MARKING:
- Map each marking symbol (P1, K1, K2, N1) to a step object. 
- Extract the numerical value (e.g., K2 -> 2.0).
- "keywords" must contain the exact acceptable forms or variables.

11. IGNORE BACKGROUND GRIDS (CRITICAL): If the marking scheme contains a plotted graph, coordinate plane, or transformation grid, DO NOT attempt to extract the background grid lines, and DO NOT list out all the numbers on the x/y axes. Only extract the explicitly written text, marking symbols (e.g., P1, K2), and validation notes below or beside the grid.

GENERAL FORMATTING RULES:
- Extract ALL visible marking entries on the page.
- Each object must include question_no, part, and subpart if visible.
- If a page contains multiple marking entries (e.g., 5a and 5b), return separate objects.
- Store part labels separately as "part": "a", "b", etc. without brackets.
- If no real marking entry exists, return {{"markings": []}}.
- Final numerical results should be concise, e.g. "x = 4".

STEP & KEYWORD RULES:
- "steps" should contain the exact marking steps. Each step must use this structure:
{{
    "step_no": 1,
    "label": "Short descriptive label",
    "marks": 1.0,
    "required": true,
    "answer": "Exact math/logic",
    "keywords": ["math string 1", "math string 2"]
  }}
- If a step has multiple lines of working, store "answer" as a list of strings.
- "keywords" MUST contain useful variables, numbers, or expressions for matching student steps later.
- If the marking scheme shows alternative equivalent forms (e.g., "atau", "setara", "or equivalent"):
  - DO NOT include the words "atau/setara" in "keywords".
  - Extract the actual alternative mathematical expressions as separate valid forms.
  - Store them as a list in "answer".
  - Also include them in "keywords" for matching.
""".strip()
    
    await enforce_rate_limit()
    response = await client.chat.completions.create(
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
    text = response.choices[0].message.content.strip()
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        cleaned_text = fix_json_string(text)
        print(cleaned_text)
        parsed = json.loads(cleaned_text)

    if isinstance(parsed, list):
        markings = parsed
    else:
        markings = parsed.get("markings", [])
        if not isinstance(markings, list):
            markings = []

    return [normalize_marking_output(m) for m in markings if isinstance(m, dict)]




def safe_parse_json(raw_text):
    """Safely attempts to parse JSON, falling back to json_repair, 
    and escaping completely if the string is infinitely looping."""
    try:
        # Clean away markdown ```json blocks first
        clean_text = raw_text.replace("```json", "").replace("```", "").strip()
        return json.loads(clean_text)
    except json.JSONDecodeError:
        try:
            # If standard fails, try json_repair. 
            repaired = repair_json(clean_text, return_objects=True)
            if repaired:
                return repaired
            else:
                print("⚠️ JSON Repair failed to salvage the data.")
                return []
        except Exception as e:
            # THIS IS THE MAGIC: It catches the infinite loop freeze!
            print(f"⚠️ FATAL PARSE ERROR: {e}. Skipping this heavily corrupted page.")
            return []
        

def promote_tables_from_given_values(q: dict) -> dict:
    """
    If the LLM accidentally extracts a table into given_values
    while table_data is empty, copy that table into table_data.

    This is useful when:
    - sequence contains table_0
    - question mentions Table/Jadual
    - table_data is {}
    - given_values contains a 2D list table
    """

    if not isinstance(q.get("table_data"), dict):
        q["table_data"] = {}

    if not isinstance(q.get("given_values"), dict):
        q["given_values"] = {}

    # If table_data already exists, do nothing
    if q["table_data"]:
        return q

    promoted_tables = {}

    for key, value in q["given_values"].items():
        key_text = str(key).strip()
        key_lower = key_text.lower()

        looks_like_table_key = (
            "table" in key_lower
            or "jadual" in key_lower
            or key_lower.startswith("table_")
        )

        # Case 1: given_values has {"Table 6": [[...], [...]]}
        if (
            isinstance(value, list)
            and value
            and all(isinstance(row, list) for row in value)
        ):
            table_name = key_text if key_text else f"Table_{len(promoted_tables) + 1}"
            promoted_tables[table_name] = value

        # Case 2: key name clearly says table, but value is a dict
        elif looks_like_table_key and isinstance(value, dict):
            rows = []

            for k, v in value.items():
                if isinstance(v, list):
                    rows.append([str(k)] + [str(x) for x in v])
                else:
                    rows.append([str(k), str(v)])

            if rows:
                table_name = key_text if key_text else f"Table_{len(promoted_tables) + 1}"
                promoted_tables[table_name] = rows

    if promoted_tables:
        q["table_data"] = promoted_tables

        # Make sure sequence has table_0 if table exists
        sequence = q.get("sequence", [])
        if not isinstance(sequence, list):
            sequence = []

        has_table_ref = any(str(item).startswith("table_") for item in sequence)

        if not has_table_ref:
            # If intro exists, final merged order is usually:
            # intro -> table -> command
            if str(q.get("introductory_instructions_en", "")).strip():
                old_text_count = len(q.get("instructions_en", []) or [])
                q["sequence"] = ["text_0", "table_0"]

                for i in range(old_text_count):
                    q["sequence"].append(f"text_{i + 1}")

            else:
                # Safe fallback: table first, then existing text refs
                text_refs = [
                    f"text_{i}"
                    for i in range(len(q.get("instructions_en", []) or []))
                ]
                q["sequence"] = ["table_0"] + text_refs

    return q

def normalize_parser_output(data: dict) -> dict:
    """
    Ensure all expected keys exist and types are consistent.

    Important:
    - This function only cleans LLM extraction output.
    - It should NOT decide verified_form / verified_chapter.
    - Chapter verification is handled later by metadata_classifier.py.
    """

    result = deepcopy(EXPECTED_SCHEMA)

    # Copy model output into full internal schema
    for key in result:
        if key in data:
            result[key] = data[key]

    # -----------------------------
    # List fields
    # -----------------------------
    list_fields = [
        "instructions_en",
        "instructions_ms",
        "sequence",
        "equations",
        "expressions",
        "variables",
        "options",
    ]

    for field in list_fields:
        if field not in result:
            continue

        value = result.get(field)

        if isinstance(value, list):
            result[field] = [str(x).strip() for x in value if str(x).strip()]
        elif value in (None, ""):
            result[field] = []
        else:
            result[field] = [str(value).strip()]

    # -----------------------------
    # Dict fields
    # -----------------------------
    dict_fields = ["given_values", "table_data", "constraints"]

    for field in dict_fields:
        if not isinstance(result.get(field), dict):
            result[field] = {}
    result = promote_tables_from_given_values(result)
    # -----------------------------
    # Numeric fields
    # -----------------------------
    for field in ["marks", "classification_confidence", "display_marks"]:
        try:
            result[field] = float(result.get(field, 0.0) or 0.0)
        except (TypeError, ValueError):
            result[field] = 0.0

    for field in ["difficulty_level", "group_difficulty_level", "stage_index"]:
        try:
            result[field] = int(result.get(field, 3) or 3)
        except (TypeError, ValueError):
            result[field] = 3

    # -----------------------------
    # String fields
    # -----------------------------
    string_fields = [
        "question_no",
        "part",
        "subpart",
        "sub_subpart",
        "question_type",
        "topic",
        "subtopic",
        "target",
        "diagram_type",
        "chapter",
        "form",
        "difficulty",
        "visual_semantic_summary",

        # Internal fields
        "group_id",
        "verified_form",
        "verified_chapter",
        "group_chapter",
        "group_form",
        "exercise_stage_id",
        "unlock_after_stage_id",
        "marks_source"
    ]

    # Optional: keep this only if still in your schema
    if "classification_status" in result:
        string_fields.append("classification_status")

    for field in string_fields:
        if field not in result:
            continue

        value = result.get(field)
        result[field] = "" if value is None else str(value).strip()

    # -----------------------------
    # Clean numbering labels
    # -----------------------------
    result["part"] = clean_part_label(result.get("part", ""))
    result["subpart"] = clean_part_label(result.get("subpart", ""))
    result["sub_subpart"] = clean_part_label(result.get("sub_subpart", ""))

    # -----------------------------
    # Boolean fields
    # -----------------------------
    result["requires_next_page"] = bool(result.get("requires_next_page", False))
    result["has_diagram"] = bool(result.get("has_diagram", False))

    result["difficulty"] = calculate_spm_difficulty(result)

    try:
        result["difficulty_level"] = int(result.get("difficulty_level", 3))
    except (TypeError, ValueError):
        result["difficulty_level"] = 3

    return result

async def parse_question_page_with_vision(image_path, openai_client, next_image_path=None, model="gemini-3.5-flash-lite"):
    system_prompt = """
You are a parser for SPM mathematics question pages from images.

Your task:
Look at the full exam page and extract ALL visible questions and subparts into structured JSON.

Strict rules:
1. Do NOT solve the questions.
2. Do NOT explain the questions.
3. Return a JSON object with a top-level key: "questions".
4. If math appears inside a sentence, extract the math separately into "equations" or "expressions" when relevant.
5. If the image suggests a diagram, graph, table, or geometry figure, set "has_diagram" to true.
6. If a diagram is present, identify its type conservatively in "diagram_type".
7. "questions" must be a list of question objects.
8. Split question parts separately, e.g. 5(a), 5(b), 5(a)(i).
9. NEW RULE FOR NESTED NUMBERING: If a question has 3 levels of nested numbering like 11(b)(i)(a), you MUST use the new field "sub_subpart". 
   Example: "question_no": "11", "part": "b", "subpart": "i", "sub_subpart": "a".
10. Do NOT merge multiple numbered parts into one object.
11. Ignore cover-page content, candidate info, and page instructions,formula page if present.
12. Only extract clearly visible question content.
13. Return valid JSON only.
14. Do NOT include markdown, explanations, or extra text.
15. MISSING DATA FLAG (EXTREMELY STRICT): If the question text refers to a table or diagram, AND that item is visually MISSING, you may set "requires_next_page": true. HOWEVER, you are strictly FORBIDDEN from triggering this flag just because you see the words "Answer space" (Ruang jawapan) or "Turn over" (Lihat sebelah). If you can read the mathematical question itself, set this to FALSE. Only use this if a sentence or table is literally cut in half.
16. TRANSFORMATION SPLIT RULE (CRITICAL): 
In "Combined Transformations" questions, you will often see an instruction followed by a nested list, such as:
   "(i) Describe in full the transformation:
        (a) T
        (b) ST"
You MUST break this into TWO separate objects. Do NOT merge them.
- Object 1: "subpart": "i", "sub_subpart": "a", "instructions_en": ["Describe in full the transformation T"]
- Object 2: "subpart": "i", "sub_subpart": "b", "instructions_en": ["Describe in full the transformation ST"]
17. WIDE MARGIN RULE (CRITICAL): Subpart labels like (a), (b), (c) and roman numerals (i), (ii) are often printed far to the left margin, separated from the question text by a large gap of whitespace. You MUST actively scan the far left edge of the image for these labels. 
18. DO NOT ignore isolated letters in the margin, and DO NOT merge the text next to them into a single block. If you see (a) and (b) in the margin, you MUST create separate JSON objects for each.
""".strip()

    page_schema = {
        "questions": [LLM_EXPECTED_SCHEMA]
    }

    schema_text = json.dumps(page_schema, indent=2)
    syllabus_mapping_json = json.dumps(SPM_SYLLABUS_MAPPING, indent=2)
    image_data_url = encode_image_to_data_url(image_path)
    next_image_data_url = None
    if next_image_path:
        next_image_data_url = encode_image_to_data_url(next_image_path)
    user_prompt = f"""
Parse this full SPM mathematics question page into JSON.

Return ONLY valid JSON using this schema:
{schema_text}

STRICT TOPIC & SUBTOPIC SELECTION:
You MUST select the "topic" strictly from the top-level keys in this JSON mapping:
{syllabus_mapping_json}
Once you select a "topic", you MUST select the "subtopic" strictly from the available list of subtopics under that specific topic. Do NOT invent your own subtopics.

CRITICAL MULTI-PAGE RULE:
- You are initially provided with ONLY the MAIN PAGE.
- You must extract ALL questions that START on the MAIN PAGE.
- DO NOT request the next page just to find an empty "answer space" or "ruang jawapan". In SPM papers, an instruction like "Complete Table 1 in the answer space" simply refers to a blank template for students to draw on. Do NOT set the flag for this.
- ONLY set "requires_next_page": true if a critical piece of mathematical data (like a data table that has NO values on the current page, or an image cut in half) is explicitly missing.
- If you set this flag, the system will re-run your prompt and provide the NEXT PAGE image.
- When you find the missing data on the NEXT PAGE, insert its data directly into the "given_values" of the question you are currently building from the MAIN PAGE. 
- DO NOT extract new questions that start on the NEXT PAGE. Ignore them entirely.
- Once the NEXT PAGE is provided, extract the missing data and set "requires_next_page": false.
INTRODUCTORY CONTEXT POSITION RULE:

The introductory context is usually printed beside or immediately after the main question number, before the subpart labels.

Common layout:
Question number + introductory paragraph
(a) actual command
(b) actual command

Example:
3 Izzah cycled 12 km at a speed of (x - 3) kmh⁻¹ in (x - 2) hours.
(a) Write a quadratic equation in terms of x.
(b) Hence, calculate the value of x.

Correct extraction:
For both 3(a) and 3(b):
"introductory_instructions_en": "Izzah cycled 12 km at a speed of (x - 3) kmh⁻¹ in (x - 2) hours."

For 3(a):
"instructions_en": [
  "Write a quadratic equation in terms of x."
]

For 3(b):
"instructions_en": [
  "Hence, calculate the value of x."
]

The actual command is usually the text after the subpart label such as:
- (a), (b), (c)
- (i), (ii), (iii)
- (a)(i), (b)(ii)

Do not treat the introductory paragraph beside the main question number as the command for only part (a). It applies to all related subparts on the same page unless the layout clearly shows otherwise.

EXCEPTION:
If the question has only one main question and no visible subparts, then the full visible question text may be placed directly into instructions_en / instructions_ms, and introductory_instructions_en / introductory_instructions_ms may be left empty.
SEQUENCE AND VISUAL ORDER RULES (CRITICAL)
The sequence array must represent the FINAL visual order after the backend merges introductory_instructions into instructions.

If intro exists:
- introductory_instructions_en becomes text_0 after backend merging.
- instructions_en[0] becomes text_1.
- instructions_en[1] becomes text_2.

Example:
Intro → Table → Command
"sequence": ["text_0", "table_0", "text_1"]

Example:
Intro → Diagram → Command
"sequence": ["text_0", "image_0", "text_1"]

Example:
Intro → Command
"sequence": ["text_0", "text_1"]

If there is no intro:
- instructions_en[0] remains text_0.

DIFFICULTY & SYLLABUS METADATA (INFERENCE):
- Just leave difficulty as blank "" for now. We will infer it later based on the question number and part.
- Just leave form and chapters as blank "" for now. We will infer them later based on the question number and topic.

LOGIC EXTRACTION RULES (CRITICAL FOR SOLVING):
You must translate visual and implicit data into explicit machine-readable JSON.

1.  "visual_semantic_summary": Write a brief, high-level 1-2 sentence summary of the diagram focusing purely on geometric relationships and semantic concepts. Do NOT list coordinates or dense numbers here.
   - CRITICAL EXCEPTION FOR GRAPHS: If the image is a dense graph on grid paper (like an ogive, histogram, or continuous curve), DO NOT attempt to extract the coordinates of the curve. It will cause a system crash. Instead, simply return an empty dictionary {{}} or only extract explicitly printed text labels.
2. "table_data": Extract tables cleanly into this top-level dictionary. 
   - If there are multiple tables, use their titles as keys (e.g., "Table 1"). If there is no title, use "Table_1".
   - Format each table's data as a 2D array (a list of lists) mapping the exact rows and columns to preserve the visual grid.
   - EMPTY CELLS: Preserve visual gaps by using empty strings "".
   - MULTI-LEVEL/MERGED HEADERS: If a header spans multiple columns, DO NOT skip columns. Put the text in the first cell of the span and use empty strings "" for the remaining spanned cells to maintain matrix alignment.
     Example of 1 header spanning 3 columns: [["Main Category", "", ""], ["Sub 1", "Sub 2", "Sub 3"]]

3. GRIDS & GRAPH PAPER (CRITICAL): 
   - BLANK GRAPH PAPER: If you see a completely empty grid or blank graph paper meant for the student to draw on, DO NOT attempt to extract or map any lines, boxes, or coordinates. Instantly move on.
   - Do NOT transcribe blank Cartesian grids, graph paper, or empty answer lines into "table_data". 
   - For coordinate graphs or Venn Diagrams: DO NOT extract complex JSON arrays of points or regions. Instead, simply write a 1-2 sentence text summary in the "visual_analysis" field (e.g., "A Cartesian graph with point S plotted at (4,2)" or "A Venn diagram showing sets G, N, and S").

4. "constraints": Extract any real-world logical rules required to solve the problem.
   - Examples: {{"max_capacity": value, "pricing_condition": "condition details", "time_limit": "value"}}.
   - If no logical constraints exist, leave empty {{}}.

NUMBERING:
- Use only numbering explicitly visible on the current page.
- If the main question number is missing, leave "question_no" empty.
- Do not infer missing numbering from earlier pages.
- ORPHAN SUBPARTS (CRITICAL): If a page starts directly with a subpart like "(b) or "(c)" or "(d)" and has no main question number, you MUST STILL EXTRACT IT! IF THERE EXIST Diagram with no MAIN QUESTION NUMBER, treat it as a valid standalone question, leave "question_no" empty, and extract the part/subpart normally.
- CRITICAL ANTI-TYPO RULE: Do NOT auto-correct or fix typos in the exam paper's numbering. If the paper accidentally prints "(a)" twice in a row, you MUST extract both as "part": "a". Do not change the second one to "b".
- Always populate "instructions_en" and "instructions_ms" with the full human-readable question text as written,
  including conditions, context sentences, and what is being asked (e.g. "Find the value of x").
  This is required for display — do NOT leave it empty if question text is visible.
- If math appears inside a sentence, keep the full sentence in "instructions_en" and "instructions_ms" AND extract 
  the math separately into "equations" or "expressions".

TEXT GROUPING RULES:
- Group sentences into the same "instructions" entry if they belong to the same visual block.
- If multiple lines appear inside a box, table, or grouped region, combine them into ONE entry using newline "\n".
- Do NOT split short related statements into separate entries if they are visually grouped.
- Only split into multiple entries when the content is clearly separated (e.g. paragraph vs diagram vs another paragraph).

MATH NOTATION PRESERVATION RULES:
- Preserve vectors, matrices, coordinates, inequalities, and symbolic expressions faithfully.
- If a visual mathematical symbol is unclear, normalize it into plain inline notation.
- Example: a translation vector shown vertically should be written as (-6, 2).
- Do not output broken bracket fragments or partial symbols.
- If the exact visual formatting is unclear, prefer mathematically correct inline text.

Diagram detection:
- Detect if the question includes a diagram.
- If diagram exists, set "has_diagram": true and fill "diagram_type" conservatively.
- If unsure, leave fields empty instead of guessing.
- A diagram on a page typically belongs to the main question number it appears under.
- If that question has multiple subparts (e.g. 5(a), 5(b), 5(c)), copy the SAME "diagram_bbox" 
  to ALL subpart objects sharing that question number — they all reference the same diagram.
- "has_diagram" should also be true for ALL subparts that share the diagram.
- If unsure, leave "diagram_type" empty rather than guessing.   
""".strip()
    message_content = [
        {"type": "text", "text": user_prompt},
        {"type": "image_url", "image_url": {"url": image_data_url}}
    ]
    
    # Attach the next page if it exists!
    if next_image_data_url:
        message_content.append({"type": "text", "text": "--- START OF NEXT PAGE (Look here for referenced tables/answer spaces) ---"})
        message_content.append({"type": "image_url", "image_url": {"url": next_image_data_url}})

    
    await enforce_rate_limit()

    response = await openai_client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": message_content
            }
        ],
        temperature=0,
        response_format={"type": "json_object"}
    )

    text = response.choices[0].message.content.strip()
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        cleaned_text = fix_json_string(text)
        print(cleaned_text)
        parsed = json.loads(cleaned_text)

    if isinstance(parsed, list):
        questions = parsed  # model returned a bare array
    else:
        questions = parsed.get("questions", [])
        if not isinstance(questions, list):
            questions = []
    print(parsed)
    return [normalize_parser_output(q) for q in questions if isinstance(q, dict)]


WORK_DIR = os.path.join(tempfile.gettempdir(), "mathsy_parsed_output2")
QUESTION_IMG_DIR = os.path.join(WORK_DIR, "question_pages")
MARKING_IMG_DIR = os.path.join(WORK_DIR, "marking_pages")
QUESTION_CROP_DIR = os.path.join(WORK_DIR, "question_crops")
MARKING_CROP_DIR = os.path.join(WORK_DIR, "marking_crops")

for folder in [WORK_DIR, QUESTION_IMG_DIR, MARKING_IMG_DIR, QUESTION_CROP_DIR, MARKING_CROP_DIR]:
    os.makedirs(folder, exist_ok=True)


# =========================================================
# KEY / FILTER HELPERS
# =========================================================

def make_key(item):
    q = str(item.get("question_no", "")).strip().lower()
    p = str(item.get("part", "")).strip().lower()
    s = str(item.get("subpart", "")).strip().lower()
    ss = str(item.get("sub_subpart", "")).strip().lower() # <--- ADD THIS
    return (q, p, s, ss) # <--- ADD THIS

# def should_skip_question(question_data):
#     instructions = " ".join(question_data.get("instructions_en", [])).lower()
#     question_type = str(question_data.get("question_type", "")).lower()
#     topic = str(question_data.get("topic", "")).lower()
#     subtopic = str(question_data.get("subtopic", "")).lower()

#     combined_text = f"{instructions} {question_type} {topic} {subtopic}"

#     skip_phrases = [
#         "draw the graph",
#         "sketch the graph",
#         "draw a graph",
#         "sketch a graph",
#         "plot the graph",
#         "construct",
#         "geometrical construction",
#         "geometric construction",
#         "using ruler and compass",
#         "draw the locus",
#         "sketch the curve"
#         "draw an ogive",
#         "draw to full scale"
#     ]

#     return any(phrase in combined_text for phrase in skip_phrases)

        
# =========================================================
# NUMBERING EXTRACTION
# =========================================================

QUESTION_ID_REGEX = re.compile(
    r'^\s*(\d+)\s*(?:[\.\)])?\s*(?:\(([a-zA-Z])\))?\s*(?:\(([ivxIVX]+)\))?',
    re.MULTILINE
)

def extract_question_metadata_from_text(text: str) -> dict:
    """
    Examples matched:
    5
    5.
    5)
    5(a)
    5(a)(i)
    """
    if not text:
        return {"question_no": "", "part": "", "subpart": ""}

    m = QUESTION_ID_REGEX.search(text.strip())
    if not m:
        return {"question_no": "", "part": "", "subpart": ""}

    question_no = m.group(1) or ""
    part = (m.group(2) or "").lower()
    subpart = (m.group(3) or "").lower()

    return {
        "question_no": question_no,
        "part": part,
        "subpart": subpart
    }

def consolidate_markings(parsed_markings):
    """
    Merges marking objects that share the exact same question/part/subpart IDs.
    Solves the 1-to-many marking scheme issue (e.g., Q6 graph criteria).
    """
    consolidated = {}
    
    for item in parsed_markings:
        key = make_key(item)
        
        if key not in consolidated:
            consolidated[key] = item.copy()
        else:
            existing = consolidated[key]
            
            # Sum the marks
            existing["subpart_marks"] += item.get("subpart_marks", 0.0)
            
            # Ensure the total question marks aren't lost if one of the fragments had it
            if item.get("question_total_marks", 0) > existing.get("question_total_marks", 0):
                existing["question_total_marks"] = item.get("question_total_marks")
            
            # Merge the steps
            if not isinstance(existing.get("steps"), list):
                existing["steps"] = []
            if isinstance(item.get("steps"), list):
                existing["steps"].extend(item.get("steps"))
                
            # Merge notes (removing exact duplicates)
            if isinstance(item.get("notes"), list):
                if not isinstance(existing.get("notes"), list):
                    existing["notes"] = []
                existing["notes"].extend(item["notes"])
                existing["notes"] = list(dict.fromkeys(existing["notes"])) # Remove dupes

            # Merge final answers if they differ (prevents losing text/table fragments)
            curr_ans = str(existing.get("final_answer", "")).strip()
            new_ans = str(item.get("final_answer", "")).strip()
            if new_ans and new_ans != curr_ans:
                existing["final_answer"] = f"{curr_ans} \n {new_ans}".strip(" \n ")

    # Re-number the steps sequentially after merging
    for val in consolidated.values():
        if isinstance(val.get("steps"), list):
            for idx, step in enumerate(val["steps"]):
                step["step_no"] = idx + 1
                
    return list(consolidated.values())

def backfill_question_numbering(items):
    last_q = ""
    last_part = ""
    last_subpart = ""  # <-- We need to track the 3rd level now too
    last_total_marks = 0.0

    for item in items:
        q = str(item.get("question_no", "")).strip().lower()
        p = str(item.get("part", "")).strip().lower()
        s = str(item.get("subpart", "")).strip().lower()
        ss = str(item.get("sub_subpart", "")).strip().lower() # <-- Grab the 4th level

        q = q.replace("(", "").replace(")", "")
        p = p.replace("(", "").replace(")", "")
        s = s.replace("(", "").replace(")", "")
        ss = ss.replace("(", "").replace(")", "")

        # 1. Has Main Question Number
        if q.isdigit():
            last_q = q
            last_part = p
            last_subpart = s
        # 2. Missing Main, but has Part (e.g., "(b)")
        elif not q and p:
            q = last_q
            last_part = p
            last_subpart = s
        # 3. Missing Main & Part, but has Subpart (e.g., "(i)")
        elif not q and not p and s:
            q = last_q
            p = last_part
            last_subpart = s
        # 4. Missing everything except Sub-subpart (e.g., "(a)")
        elif not q and not p and not s and ss:
            q = last_q
            p = last_part
            s = last_subpart
        # 5. Completely blank numbering
        elif not q and not p and not s and not ss:
            q = last_q
            p = last_part
            s = last_subpart

        # --- THE TOTAL MARKS FIX ---
        current_total = float(item.get("question_total_marks", 0.0))
        
        if q == last_q and current_total == 0.0 and last_total_marks > 0.0:
            item["question_total_marks"] = last_total_marks
        elif current_total > 0.0:
            last_total_marks = current_total
        elif q != last_q:
            last_total_marks = current_total 
        # ---------------------------

        item["question_no"] = q
        item["part"] = p
        item["subpart"] = s
        item["sub_subpart"] = ss # <-- Save it back

    return items

def is_meaningful_question_item(item: dict) -> bool:
    qno = str(item.get("question_no", "")).strip()
    en = " ".join(item.get("instructions_en", [])).strip()
    ms = " ".join(item.get("instructions_ms", [])).strip()
    text = f"{en} {ms}".strip().lower()

    junk_phrases = [
        "refer graph", "rujuk graf", "x = ...", "y = ...",
        "x = ................................", "y = ................................"
    ]

    if any(p in text for p in junk_phrases):
        return False

    # Filter out empty answer spaces by removing "answer", "jawapan", standalone letters, and roman numerals
    test_text = text.replace("answer:", "").replace("jawapan:", "")
    test_text = re.sub(r'\b[a-z]\b', '', test_text) # remove isolated single letters like "a", "b"
    test_text = re.sub(r'\b[ivx]+\b', '', test_text) # remove roman numerals like "i", "ii"
    test_text = re.sub(r'[\(\)\.\,\s]', '', test_text) # remove brackets and spaces

    # If nothing is left but formatting, and there is no table data, it's a junk answer space
    if len(test_text) < 3 and not item.get("given_values"):
        return False

    if qno:
        return True

    return len(text) > 40 and any(word in text for word in [
        "calculate", "find", "state", "complete", "write", "determine", "draw", "sketch",
        "hitung", "cari", "nyatakan", "lengkapkan", "tulis", "lukis", "lukiskan"
    ])

def clean_parsed_questions(items):
    cleaned = []
    seen = {}
    
    for item in items:
        raw_diagram_path = item.get("_diagram_image_path")
        raw_page_no = item.get("_page_no")
        raw_public_id = item.get("_diagram_public_id")
        item = normalize_parser_output(item)
        item["_diagram_image_path"] = raw_diagram_path
        item["_page_no"] = raw_page_no
        item["_diagram_public_id"] = raw_public_id
        if not is_meaningful_question_item(item):
            continue
            
        # Create a unique key for this specific question part
        key = (item["question_no"], item["part"], item["subpart"], item["sub_subpart"])
        
        if key not in seen:
            # First time seeing this question part, add it to our lists
            seen[key] = item
            cleaned.append(item)
        else:
            # DUPLICATE DETECTED! Merge the data instead of creating a new object
            existing_item = seen[key]
            
            # Merge given_values (so if the duplicate had the table, we keep it!)
            for k, v in item.get("given_values", {}).items():
                # Only overwrite if the existing item doesn't have it or is empty
                if k not in existing_item["given_values"] or not existing_item["given_values"][k]:
                    existing_item["given_values"][k] = v
                    
            # Ensure diagram flags aren't lost
            if item.get("has_diagram"):
                existing_item["has_diagram"] = True
                if not existing_item.get("diagram_type"):
                    existing_item["diagram_type"] = item.get("diagram_type", "")
                    
            # We skip appending `item` to `cleaned` because we merged it into `existing_item`
            if item.get("_diagram_image_path") and not existing_item.get("_diagram_image_path"):
                existing_item["_diagram_image_path"] = item["_diagram_image_path"]

            if item.get("_diagram_public_id") and not existing_item.get("_diagram_public_id"):
                existing_item["_diagram_public_id"] = item["_diagram_public_id"]

    return cleaned

def normalize_text_for_compare(text: str) -> str:
    return re.sub(r"\s+", " ", str(text or "").strip().lower())

def is_valid_intro_text(intro: str, instructions: list) -> bool:
    intro_norm = normalize_text_for_compare(intro)

    if not intro_norm:
        return False

    # If intro is actually the same as the command, reject it
    instruction_text = normalize_text_for_compare(" ".join(instructions))
    if intro_norm in instruction_text:
        return False

    return True


def get_best_stage_intro(items: list) -> tuple:
    """
    Find the best real introductory paragraph from questions in the same stage.
    Usually part (a) has the correct intro.
    """

    for q in items:
        intro_en = str(q.get("introductory_instructions_en", "")).strip()
        intro_ms = str(q.get("introductory_instructions_ms", "")).strip()

        if is_valid_intro_text(intro_en, q.get("instructions_en", [])):
            return intro_en, intro_ms

    return "", ""


def merge_intro_into_question(q: dict, shared_intro_en: str = "", shared_intro_ms: str = "") -> dict:
    """
    Merge introductory_instructions into instructions_en/ms
    so DB, frontend, RAG, and sequence all work normally.
    """

    own_intro_en = str(q.get("introductory_instructions_en", "")).strip()
    own_intro_ms = str(q.get("introductory_instructions_ms", "")).strip()

    instructions_en = q.get("instructions_en", []) or []
    instructions_ms = q.get("instructions_ms", []) or []
    old_sequence = q.get("sequence", []) or []

    # Prefer valid own intro, otherwise use stage shared intro
    if is_valid_intro_text(own_intro_en, instructions_en):
        intro_en = own_intro_en
        intro_ms = own_intro_ms
    else:
        intro_en = shared_intro_en
        intro_ms = shared_intro_ms

    if not intro_en:
        return q

    # Avoid duplicate intro
    full_instruction_text = normalize_text_for_compare(" ".join(instructions_en))
    if normalize_text_for_compare(intro_en) in full_instruction_text:
        return q

    old_instruction_count = len(instructions_en)

    q["instructions_en"] = [intro_en] + instructions_en
    q["instructions_ms"] = [intro_ms] + instructions_ms if intro_ms else instructions_ms

    visual_items = [
        item for item in old_sequence
        if item.startswith("table_") or item.startswith("image_")
    ]

    has_invalid_text_ref = False

    for item in old_sequence:
        if item.startswith("text_"):
            try:
                old_index = int(item.split("_")[1])
                if old_index >= old_instruction_count:
                    has_invalid_text_ref = True
            except Exception:
                pass

    # Case like Q6:
    # old sequence = text_0, table_0, text_1
    # but old instructions only has text_0
    # means intended order is intro -> table -> command
    if has_invalid_text_ref and visual_items:
        q["sequence"] = ["text_0"] + visual_items
        for i in range(old_instruction_count):
            q["sequence"].append(f"text_{i + 1}")

    else:
        # Normal case:
        # prepend intro before old content and shift old text indexes
        new_sequence = ["text_0"]

        if old_sequence:
            for item in old_sequence:
                if item.startswith("text_"):
                    try:
                        old_index = int(item.split("_")[1])
                        if old_index < old_instruction_count:
                            new_sequence.append(f"text_{old_index + 1}")
                    except Exception:
                        pass

                elif item.startswith("table_") or item.startswith("image_"):
                    new_sequence.append(item)
        else:
            for i in range(old_instruction_count):
                new_sequence.append(f"text_{i + 1}")

        q["sequence"] = new_sequence

    return q
def apply_intro_context_by_stage(questions: list) -> list:
    from collections import defaultdict

    stages = defaultdict(list)

    for q in questions:
        stage_id = str(q.get("exercise_stage_id", "")).strip()
        if stage_id:
            stages[stage_id].append(q)

    for stage_id, items in stages.items():
        items.sort(key=lambda q: (
            str(q.get("part", "")),
            str(q.get("subpart", "")),
            str(q.get("sub_subpart", ""))
        ))

        shared_intro_en, shared_intro_ms = get_best_stage_intro(items)

        for q in items:
            before = list(q.get("instructions_en", []))

            merge_intro_into_question(
                q,
                shared_intro_en=shared_intro_en,
                shared_intro_ms=shared_intro_ms
            )

            after = q.get("instructions_en", [])

            if before != after:
                print(
                    f"  🔗 Merged intro into Q{q.get('question_no')}({q.get('part')}) "
                    f"stage={stage_id}"
                )

    return questions


def is_blank_or_nearly_blank(text: str) -> bool:
    if not text:
        return True

    cleaned = re.sub(r'\s+', ' ', text).strip()
    if len(cleaned) < 60:
        return True

    # very low alphanumeric content
    alnum_count = len(re.findall(r'[A-Za-z0-9]', cleaned))
    return alnum_count < 50
QUESTION_ANCHOR_REGEX = re.compile(
    r'^\s*(\d+)\s*(?:[\.\)])?\s*(?:\(([a-zA-Z])\))?\s*(?:\(([ivxIVX]+)\))?',
    re.MULTILINE
)

def has_question_anchors(text: str) -> bool:
    return bool(QUESTION_ANCHOR_REGEX.search(text or ""))
def classify_question_page(text: str, is_scanned: bool = False) -> str:
    if is_scanned:
        return "parse"

    clean_text = text.lower()
    
    # ✨ 1. THE NOISE ERASER
    # These phrases do NOT count as "real question content".
    noise_phrases = [
        "scanned with camscanner", "cs camscanner",
        "graf untuk soalan", "graph for question",
        "ruang jawapan", "answer space", 
        "kegunaan pemeriksa", "examiner", "use",
        "halaman kosong", "blank page",
        "lihat sebelah", "turn over",
        "jawapan", "answer"
    ]
    
    # Strip the noise phrases out of our test string
    substance_text = clean_text
    for phrase in noise_phrases:
        substance_text = substance_text.replace(phrase, "")
        
    # ✨ 2. THE GRAPH PAPER & GRID NOISE FILTER
    # Now we count the letters that are actually left over!
    letter_count = sum(c.isalpha() for c in substance_text)
    if letter_count < 20:
        return "skip_graph_or_empty"

    # 3. CHECK IF BLANK (just in case)
    if is_blank_or_nearly_blank(clean_text):
        return "skip_blank"

    # 4. COVER & FORMULA PAGE FILTERS
    cover_keywords = [
        "name", "candidate", "index number", "class",
        "nama", "angka giliran", "tingkatan",
    ]
    formula_keywords = [
        "the following formulae may be helpful",
        "rumus-rumus berikut boleh membantu",
        "shapes and space", "bentuk dan ruang",
        "rumus matematik", "mathematical formulae", 
        "perkaitan", "relations"                    
    ]

    if any(k in clean_text for k in formula_keywords):
        return "skip_formula"

    if any(k in clean_text for k in cover_keywords) and not has_question_anchors(clean_text):
        return "skip_cover"

    return "parse"
def classify_marking_page(text: str, is_scanned: bool = False) -> str:
    """
    Returns: "skip_blank", "skip_header", or "parse"
    """
    if is_scanned:
        return "parse"
    if is_blank_or_nearly_blank(text):
        return "skip_blank"

    lower = text.lower()
    
    # Check for orphan subparts (e.g., "(a)", "(i)")
    has_orphan_subpart = bool(re.search(r'^\s*\([a-zivx]+\)', lower, re.MULTILINE))
    
    # Check for SPM Grading Symbols (P1, K1, N1, J1) OR the word "mark/markah"
    has_grading_symbols = bool(re.search(r'\b[pknj]\d\b', lower)) or bool(re.search(r'\b\d+\s*mark[s|ah]*\b', lower))

    # ✨ GRAPH INDICATORS: If it mentions axes, frequency, or graphs, parse it!
    has_graph_indicators = any(k in lower for k in ["graf", "graph", "kekerapan", "frequency", "paksi", "axis","y","x"])

    if has_orphan_subpart or has_grading_symbols or has_graph_indicators:
        return "parse"

    # 2. COVER PAGE DETECTION
    header_keywords = [
        "scheme of marking", "marking scheme",
        "skema pemarkahan", "peraturan pemarkahan",
        "mathematics", "matematik", "kertas 2"
    ]

    if any(k in lower for k in header_keywords):
        return "skip_header"

    return "skip_header"


# =========================================================
# INSERT ALL
# =========================================================

def insert_all_questions(conn, question_paper_id, parsed_questions):
    question_id_map = {}

    for q in parsed_questions:
        key = make_key(q)
        image_path = q.pop("_diagram_image_path", None)
        q_id = insert_question(conn, question_paper_id, q, image_path=image_path)

        if key not in question_id_map:
            question_id_map[key] = []
        question_id_map[key].append(q_id)

        print(f"Inserted question {key} -> ID {q_id}")

    return question_id_map

def insert_all_marking_schemes(conn, marking_paper_id, parsed_markings):

    marking_id_map = {}

    for m in parsed_markings:
        key = make_key(m)
        m_id = insert_marking_scheme(conn, marking_paper_id, m)

        if key not in marking_id_map:
            marking_id_map[key] = []
        marking_id_map[key].append(m_id)

        print(f"Inserted marking scheme {key} -> ID {m_id}")

    return marking_id_map

def link_questions_and_markings(conn, question_id_map, marking_id_map):
    for key, q_ids in question_id_map.items():
        if key not in marking_id_map:
            print(f"No marking scheme found for question {key}")
            continue

        m_ids = marking_id_map[key]

        pair_count = min(len(q_ids), len(m_ids))
        for i in range(pair_count):
            q_id = q_ids[i]
            m_id = m_ids[i]
            link_id = insert_question_marking_link(conn, q_id, m_id, "matched_exact")
            print(f"Linked {key}: question_id={q_id}, marking_id={m_id}, link_id={link_id}")

        if len(q_ids) != len(m_ids):
            print(f"Warning: count mismatch for {key} | questions={len(q_ids)} markings={len(m_ids)}")

PAGE_SEMAPHORE = None

async def smart_parse_wrapper(image_path, next_image_path, client, model, max_retries=3):
    """
    Executes Pass 1. If the LLM requests the next page, executes Pass 2.
    Includes Auto-Retry and Concurrency Limits to survive Server Errors!
    """
    global PAGE_SEMAPHORE
    if PAGE_SEMAPHORE is None:
        PAGE_SEMAPHORE = asyncio.Semaphore(2)  # Max 5 pages processing at once

    for attempt in range(max_retries):
        async with PAGE_SEMAPHORE:
            try:
                await asyncio.sleep(2)  # Small delay to reduce burstiness
                # PASS 1: Send ONLY the current page
                items = await parse_question_page_with_vision(
                    image_path=image_path, 
                    next_image_path=None,  
                    openai_client=client, 
                    model=model
                )

                # Check if the LLM flagged any of the questions as missing data
                needs_lookahead = any(q.get("requires_next_page", False) for q in items)

                if needs_lookahead and next_image_path:
                    print(f"  🧠 LLM requested missing data for {os.path.basename(image_path)}. Re-running with next page...")
                    
                    # PASS 2: Send BOTH pages
                    items = await parse_question_page_with_vision(
                        image_path=image_path, 
                        next_image_path=next_image_path, 
                        openai_client=client, 
                        model=model
                    )
                print(json.dumps(items, indent=2, ensure_ascii=False))
                return items

            except Exception as e:
                error_msg = str(e).lower()
                
                # 1. Catch 429 Rate Limits and take a coffee break
                if "429" in error_msg:
                    print(f"⏳ Rate Limit hit on {os.path.basename(image_path)}. Pausing for 60s...")
                    await asyncio.sleep(60)
                    continue 
                
                # 2. Catch 500 Server Errors and Timeouts
                elif attempt < (max_retries - 1) and ("500" in error_msg or "timed out" in error_msg):
                    wait_time = 5 * (attempt + 1)
                    print(f"🔄 Google Server hiccup on {os.path.basename(image_path)}. Retrying in {wait_time}s... (Attempt {attempt + 2}/{max_retries})")
                    await asyncio.sleep(wait_time)
                    continue 
                
                # 3. Fail safely if it's a code error or out of retries
                print(f"⚠️ Fatal Error parsing {os.path.basename(image_path)}: {e}")
                return []
    return[]

MARKING_SEMAPHORE = None

async def smart_marking_wrapper(image_path, client, model, max_retries=3):
    """Protects marking scheme parsing with auto-retries and concurrency limits."""
    global MARKING_SEMAPHORE
    if MARKING_SEMAPHORE is None:
        MARKING_SEMAPHORE = asyncio.Semaphore(5)

    for attempt in range(max_retries):
        async with MARKING_SEMAPHORE:
            try:
                items = await parse_marking_page_with_vision(
                    image_path=image_path,
                    client=client,
                    model=model
                )
                return items
            except Exception as e:
                error_msg = str(e).lower()
                if "429" in error_msg:
                    print(f"⏳ Rate Limit hit on marking page. Pausing for 60s...")
                    await asyncio.sleep(60)
                    continue 
                elif attempt < (max_retries - 1) and ("500" in error_msg or "timed out" in error_msg):
                    wait_time = 5 * (attempt + 1)
                    print(f"🔄 Google Server hiccup. Retrying in {wait_time}s...")
                    await asyncio.sleep(wait_time)
                    continue 
                
                print(f"⚠️ Fatal Error parsing marking page: {e}")
                return []
    return []
            
def apply_typo_overrides(parsed_items, overrides):
    """
    Forces manual corrections for known printing errors in the exam papers
    so they align perfectly with the marking schemes.
    """
    for item in parsed_items:
        key = (item["question_no"], item["part"], item["subpart"], item["sub_subpart"])
        
        if key in overrides:
            new_q, new_p, new_s, new_ss = overrides[key]
            item["question_no"] = new_q
            item["part"] = new_p
            item["subpart"] = new_s
            item["sub_subpart"] = new_ss
            print(f"  🔧 Auto-Fixed Exam Typo: Changed {key} to {overrides[key]}")
            
    return parsed_items

def filter_unlinked_data(parsed_questions, parsed_markings):
    """
    Compares the parsed lists and throws away any items that don't have a match,
    while safely protecting "intro" paragraphs at ANY level (e.g., Q5, Q12c) 
    that belong to valid subparts.
    """
    marking_keys = {make_key(m) for m in parsed_markings}
    question_keys = {make_key(q) for q in parsed_questions}

    # Group questions by main question number to check for children later
    questions_by_qno = {}
    for q in parsed_questions:
        qno = str(q.get('question_no', '')).strip()
        if qno:
            if qno not in questions_by_qno:
                questions_by_qno[qno] = []
            questions_by_qno[qno].append(q)

    valid_questions = []
    valid_markings = []

    print("\n--- Cleaning Up Unlinked Data ---")

    # 1. Filter Questions
    for q in parsed_questions:
        k = make_key(q)
        qno, part, sub, sub_sub = k
        
        # Condition A: Exact match in marking scheme
        if k in marking_keys:
            valid_questions.append(q)
            continue
            
        # Condition B: Dynamic "Parent Protection Rule"
        is_parent_of_valid_child = False
        
        # Look at all other questions that share the same main number
        for child in questions_by_qno.get(qno, []):
            child_k = make_key(child)
            c_qno, c_part, c_sub, c_sub_sub = child_k
            
            # To be a child, it must match the parent's existing letters
            if part and c_part != part: continue
            if sub and c_sub != sub: continue
            if sub_sub and c_sub_sub != sub_sub: continue
            
            # The child must actually be deeper than the parent, AND have a marking scheme
            if child_k != k and child_k in marking_keys:
                is_parent_of_valid_child = True
                break # We found at least one valid child, so this parent is saved!
                
        if is_parent_of_valid_child:
            valid_questions.append(q)
        else:
            print(f"  🗑️ Discarding unlinked question: {k}")

    # 2. Filter Marking Schemes
    for m in parsed_markings:
        k = make_key(m)
        if k in question_keys:
            valid_markings.append(m)
        else:
            print(f"  🗑️ Discarding unlinked marking scheme: {k}")

    print("---------------------------------\n")
    return valid_questions, valid_markings

def auto_shift_numbering(items):
    """
    Detects if the LLM accidentally skipped the 'part' field and put an alphabet 
    letter (a, b, c) into the 'subpart' field. If so, it shifts everything left.
    """
    # Standard alphabet letters used for 'parts' in SPM
    valid_parts = ["a", "b", "c", "d", "e", "f"]

    for item in items:
        p = str(item.get("part", "")).strip().lower()
        s = str(item.get("subpart", "")).strip().lower()
        ss = str(item.get("sub_subpart", "")).strip().lower()

        # If 'part' is empty, but 'subpart' has an 'a', 'b', 'c', etc.
        if not p and s in valid_parts:
            # Shift everything left!
            item["part"] = s         # 'a' moves up to part
            item["subpart"] = ss     # whatever was in sub_subpart moves up
            item["sub_subpart"] = "" # sub_subpart is cleared
            
            # Print a log so you know the script fixed it automatically
            q = item.get("question_no", "")
            print(f"  ✨ Auto-Shifted Numbering: Q{q} moved ({s}) from subpart to part.")
            
    return items

def align_orphan_markings(parsed_questions, parsed_markings):
    """
    Fixes marking schemes where the LLM accidentally skipped the 'part' or shifted roman numerals.
    Handles two common cases:
    1. Roman numeral in 'part' -> ('12', 'ii', '', '')
    2. Missing 'part' but valid 'subpart' -> ('12', '', 'ii', '')
    """
    question_keys = {make_key(q) for q in parsed_questions}
    
    for m in parsed_markings:
        k = make_key(m)
        if k not in question_keys:
            qno, part, sub, sub_sub = k
            
            # Case 1: Roman numeral got stuffed into the 'part' field ('12', 'ii', '', '')
            if re.fullmatch(r'[ivx]+', part) and not sub and not sub_sub:
                for qk in question_keys:
                    if qk[0] == qno and qk[2] == part and not qk[3]:
                        m["part"] = qk[1]
                        m["subpart"] = qk[2]
                        print(f"  🤝 Auto-Aligned (Shift): Changed {k} to match Question {qk}")
                        break
                        
            # ✨ Case 2 (YOUR FIX): 'part' is blank, but 'subpart' is a roman numeral ('12', '', 'ii', '')
            elif not part and re.fullmatch(r'[ivx]+', sub) and not sub_sub:
                for qk in question_keys:
                    if qk[0] == qno and qk[2] == sub and not qk[3]:
                        m["part"] = qk[1] # Borrow the missing 'part' (e.g., 'b') from the Question!
                        print(f"  🤝 Auto-Aligned (Fill Missing Part): Changed {k} to match Question {qk}")
                        break
                        
    return parsed_markings

def recalculate_question_difficulty(questions: list) -> list:
    for q in questions:
        q["difficulty"] = calculate_spm_difficulty(q)

    return questions


async def process_question_and_marking_pdfs_full_page(
    question_pdf_path: str = None,
    marking_pdf_path: str = None, # Make this optional
    question_client=None,
    marking_client=None,
    exam_name=None,
    subject=None,
    year=None,
    question_model="gemini-3.5-flash-lite",      # NEW: Model for questions
    marking_model="gemini-3.5-flash-lite",
    question_start_page: int = None,
    question_end_page: int = None,
    question_page_numbers: list = None,  # e.g. [27] or [27, 28],
    marking_start_page: int = None,
    marking_end_page: int = None,
    marking_page_numbers: list = None,  # e.g. [27] or [27, 28],
    output_prefix: str = "paper",
    save_to_db: bool = True
):
    conn = None

    try:
        # 1. Render and Extract Question Pages
        question_pages = render_pdf_pages(question_pdf_path, QUESTION_IMG_DIR)
        question_texts = extract_pdf_page_texts(question_pdf_path)
        tasks = []
        task_metadata = [] # To keep track of which page is which
        parsed_questions = []
        all_raw_questions = []
        # 2. Parse Question Pages (USING LOOKAHEAD STRATEGY)
        for i, page_info in enumerate(question_pages):
            page_no = page_info["page_no"]

            if not page_in_selected_range(
                page_no,
                start_page=question_start_page,
                end_page=question_end_page,
                page_numbers=question_page_numbers
            ):
                continue
            
            text_info = question_texts[i]
            
            # ✨ THE PRE-SCANNER FIX: If PyMuPDF couldn't read the text (scanned page), use Tesseract!
            if text_info.get("is_scanned", False):
                print(f"  🔍 Page {page_no} is a scan. Running quick OCR to check for blank answer spaces...")
                img = cv2.imread(page_info["page_image_path"])
                gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                ocr_text = pytesseract.image_to_string(gray)
                
                # Overwrite the empty fitz text with the actual OCR text!
                text_info["text"] = ocr_text  
                text_info["is_scanned"] = False # Treat it as normal text so the filters apply!

            # Now the classifier has the real text and can confidently skip the page!
            decision = classify_question_page(text_info["text"], text_info.get("is_scanned", False))
            print(f"Question page {page_no}: {decision}")

            if decision != "parse":
                continue

            next_image_path = None
            if i + 1 < len(question_pages):
                next_image_path = question_pages[i + 1]["page_image_path"]
            task = smart_parse_wrapper(
                image_path=page_info["page_image_path"], 
                next_image_path=next_image_path,
                client=question_client, 
                model=question_model
            )
            tasks.append(task)
            task_metadata.append(page_info)

        print(f"Queued {len(tasks)} question pages for async processing...")

        # page_items = parse_question_page_with_vision(
        #     image_path=page_info["page_image_path"], 
        #     next_image_path=next_image_path,
        #     client=client, 
        #     model=model
        # )
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for i, page_items in enumerate(results):
            if isinstance(page_items, Exception):
                print(f"⚠️ Error parsing question page {i}: {page_items}")
                continue
            page_info = task_metadata[i]
            for item in page_items:
                cloud_image_url = None
                if item.get("has_diagram"):
                    fname = f"diagram_q{item.get('question_no', 'X')}_p{page_info['page_no']}.jpg"
                    out_filepath = os.path.join(QUESTION_CROP_DIR, fname)

                    # THIS is the exact crop from crop_diagram_above_anchor
                    cropped_local_path = crop_diagram_above_anchor(
                        pdf_path=question_pdf_path,
                        page_no=page_info["page_no"],
                        image_path=page_info["page_image_path"],
                        out_path=out_filepath
                    )

                    if cropped_local_path and os.path.exists(cropped_local_path):
                        uploaded = upload_cropped_diagram(cropped_local_path)
                        if uploaded:
                            cloud_image_url = uploaded["url"]
                            item["_diagram_public_id"] = uploaded["public_id"]

                item["_diagram_image_path"] = cloud_image_url
                item["_page_no"] = page_info["page_no"]
                all_raw_questions.append(item)
        all_raw_questions = backfill_question_numbering(all_raw_questions)
        all_raw_questions = auto_shift_numbering(all_raw_questions)
        parsed_questions = clean_parsed_questions(all_raw_questions)
        # 2. Add group_id and group_difficulty_level
        parsed_questions = apply_question_grouping(parsed_questions, output_prefix)
        # 5. Split question group into page-based stages
        parsed_questions = assign_exercise_stages_by_page(parsed_questions)
        parsed_questions = apply_intro_context_by_stage(parsed_questions)
        parsed_questions = apply_verified_chapters(parsed_questions)
        # 3. Fill blank subparts from confident group members
        parsed_questions = inherit_group_chapter_for_blank_parts(parsed_questions)
        # 4. Decide one final form/chapter for whole displayed question
        parsed_questions = apply_group_form_chapter(parsed_questions)

        print(f"Parsed questions: {len(parsed_questions)}")

        # ==========================================
        # 3. ONLY PROCESS MARKING IF PATH IS PROVIDED
        # ==========================================
        parsed_markings = []
        if marking_pdf_path:
            marking_pages = render_pdf_pages(marking_pdf_path, MARKING_IMG_DIR)
            marking_texts = extract_pdf_page_texts(marking_pdf_path)
            
            tasks = []
            task_metadata = []
            for page_info, text_info in zip(marking_pages, marking_texts):
                page_no = page_info["page_no"]
                if not page_in_selected_range(
                    page_no,
                    start_page=marking_start_page,
                    end_page=marking_end_page,
                    page_numbers=marking_page_numbers
                ):
                    continue
                decision = classify_marking_page(text_info["text"], text_info.get("is_scanned", False))
                print(f"Marking page {page_info['page_no']}: {decision}")

                if decision != "parse":
                    continue

                # page_items = parse_marking_page_with_vision(
                #     page_info["page_image_path"], client, model=model
                # )
                task = smart_marking_wrapper(
                    image_path=page_info["page_image_path"], 
                    client=marking_client, 
                    model=marking_model
                )
                tasks.append(task)
                task_metadata.append((page_info, text_info))
        print(f"Queued {len(tasks)} marking pages for async processing...")
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for i, page_items in enumerate(results):
            page_info, text_info = task_metadata[i]
            for item in page_items:
                item["_page_no"] = page_info["page_no"]
                item["_page_text"] = text_info["text"]
                item["_source_page_image"] = page_info["page_image_path"]
                parsed_markings.append(item)

        parsed_markings = backfill_question_numbering(parsed_markings)
        parsed_markings = auto_shift_numbering(parsed_markings)
        parsed_markings = consolidate_markings(parsed_markings)
        parsed_markings = apply_marking_grouping(parsed_markings, output_prefix)
        parsed_questions = sync_display_marks_from_markings(parsed_questions, parsed_markings)
        parsed_questions = recalculate_question_difficulty(parsed_questions)
        parsed_questions = apply_group_difficulty_from_stage_logic(parsed_questions)
        q_filename = f"{output_prefix}_parsed_questions.json"
        with open(os.path.join(WORK_DIR, q_filename), "w", encoding="utf-8") as f:
            json.dump(parsed_questions, f, ensure_ascii=False, indent=2)
        print(f"💾 Saved {len(parsed_questions)} questions to {q_filename}")

        print(f"Parsed markings: {len(parsed_markings)}")
        m_filename = f"{output_prefix}_parsed_markings.json"
        with open(os.path.join(WORK_DIR, m_filename), "w", encoding="utf-8") as f:
            json.dump(parsed_markings, f, ensure_ascii=False, indent=2)
        print(f"💾 Saved {len(parsed_markings)} markings to {m_filename}")

        # ==========================================
        # 4. DATABASE INSERTIONS
        # ==========================================
        if marking_pdf_path and parsed_markings:
            parsed_markings = align_orphan_markings(parsed_questions, parsed_markings)
            parsed_questions, parsed_markings = filter_unlinked_data(parsed_questions, parsed_markings)
        # --------------------------------------------------------------------

        if not save_to_db:
            return {
                "questions": parsed_questions,
                "markings": parsed_markings
            }
        
        conn = get_db_connection()

        question_paper_id = insert_paper(
            conn=conn, title=os.path.basename(question_pdf_path),
            paper_type="question_paper", file_path=question_pdf_path,
            exam_name=exam_name, subject=subject, year=year
        )
        question_id_map = insert_all_questions(conn, question_paper_id, parsed_questions)

        # Only insert and link marking schemes if we processed them
        if marking_pdf_path and parsed_markings:
            marking_paper_id = insert_paper(
                conn=conn, title=os.path.basename(marking_pdf_path),
                paper_type="marking_scheme", file_path=marking_pdf_path,
                exam_name=exam_name, subject=subject, year=year
            )
            marking_id_map = insert_all_marking_schemes(conn, marking_paper_id, parsed_markings)
            link_questions_and_markings(conn, question_id_map, marking_id_map)
        print("\n🚀 Pushing extracted questions to Pinecone Vector Database...")
        q_filepath = os.path.join(WORK_DIR, f"{output_prefix}_parsed_questions.json")
        # upload_questions_to_pinecone(q_filepath, output_prefix, question_paper_id,namespace="spm_trial_questions")
        print("Pipeline completed successfully.")

    except Error as db_err:
        print("Database error:", db_err)
    except Exception as e:
        print("Pipeline failed:", e)
    finally:
        if conn is not None and conn.is_connected():
            conn.close()


if __name__ == "__main__":
    
    base_dir = r"C:\Users\YK\Documents\Degree Y3\FYP\Test Paper"
    
    # Define all papers to process here
    papers_to_process = [
        # {
        #     "id": "UD3_2025",
        #     "q_path": os.path.join(base_dir, "2025_SOALAN _MATEMATIK_UD3_KERTAS 2.pdf"),
        #     "m_path": os.path.join(base_dir, "2025_PERATURAN_PEMARKAHAN_MATEMATIK_UD3_KERTAS_2.pdf")
        
        # {
        #     "id": "JOHOR_2020",
        #     "q_path": os.path.join(base_dir, "2020 Johor MPSM Matematik K2.pdf"),
        #     "m_path": os.path.join(base_dir, "2020 Johor MPSM Matematik K2 Jawapan.pdf"),
        # },
        # {
        #     "id": "Johor_2025",
        #     "q_path": os.path.join(base_dir, "TRIAL JOHOR KERTAS 2 2025 - SET 2.pdf"),
        #     "m_path": os.path.join(base_dir, "SKEMA TRIAL JOHOR K2-SET 2.pdf")
        # },
        # {
        #     "id": "Perak_2025",
        #     "q_path": os.path.join(base_dir, "K2 MATEMATIK PPC PERAK 2025.pdf"),
        #     "m_path": os.path.join(base_dir, "SKEMA PERAK K2.pdf")
        # },
        # {
        #     "id": "Terengganu_2025",
        #     "q_path": os.path.join(base_dir, "K2 PPC MATH Terengganu 2025.pdf"),
        #     "m_path": os.path.join(base_dir, "SKEMA K1 K2 TGANU 2025.pdf")
        # },
        # {
        #     "id": "Penang_2025",
        #     "q_path": os.path.join(base_dir, "K2 Maths PPC Pulau Pinang 2025.pdf"),
        #     "m_path": os.path.join(base_dir, "Skema Maths K2 PPC Pulau Pinang 2025.pdf")
        # },
        # {
        #     "id": "Selangor_2023",
        #     "q_path": os.path.join(base_dir, "2023 Selangor Matematik K2.pdf"),
        #     "m_path": os.path.join(base_dir, "2023 Selangor Matematik K2 Skema.pdf")
        # },
        # {
        #     "id": "Negeri_Sembilan_2023",
        #     "q_path": os.path.join(base_dir, "2023 Negeri Sembilan MPSM Matematik K2.pdf"),
        #     "m_path": os.path.join(base_dir, "2023 Negeri Sembilan MPSM Matematik K1 K2 Skema.pdf")
        # },
    #     # {
    #     #     "id": "UD3_2025",
    #     #     "q_path": os.path.join(base_dir, "2025_SOALAN _MATEMATIK_UD3_KERTAS 2.pdf"),
    #     #     "m_path": os.path.join(base_dir, "2025_PERATURAN_PEMARKAHAN_MATEMATIK_UD3_KERTAS_2.pdf")
    #     # },
        # {
        #     "id": "Johor_2024",
        #     "q_path": os.path.join(base_dir, "Trial K2 Matematik SPM 2024 - Johor_JB SET 2.pdf"),
        #     "m_path": os.path.join(base_dir, "Trial Skema K2 Matematik SPM 2024 - Johor_JB SET 2.pdf")
        # },
        # {
        #     "id": "Melaka_2023",
        #     "q_path": os.path.join(base_dir, "2023 UD3 Melaka Matematik K2.pdf"),
        #     "m_path": os.path.join(base_dir, "2023 UD3 Melaka Matematik K1 K2 Skema.pdf")
        # },
        # {
        #     "id": "Negeri_Sembilan_2025",
        #     "q_path": os.path.join(base_dir, "2023 Negeri Sembilan MPSM Matematik K2.pdf"),
        #     "m_path": os.path.join(base_dir, "2023 Negeri Sembilan MPSM Matematik K1 K2 Skema.pdf")
        # },
        # {
        #     "id": "Sabah_2025",
        #     "q_path": os.path.join(base_dir, "2023 JPN Sabah Matematik K2.pdf"),
        #     "m_path": os.path.join(base_dir, "2023 JPN Sabah Matematik K2 Skema.pdf")
        # },
        # {
        #     "id": "Semporna_2025",
        #     "q_path": os.path.join(base_dir, "2023 Semporna Matematik K2.pdf"),
        #     "m_path": os.path.join(base_dir, "2023 Semporna Matematik K1 K2 Skema.pdf")
        # },
        #         {
        #     "id": "SPM_2021",
        #     "q_path": os.path.join(base_dir, "2021 SPM Maths K2.pdf"),
        #     "m_path": os.path.join(base_dir, "2021 SPM Maths K2 Jawapan.pdf")
        # },
        {
            "id": "Kedah_2025",
            "q_path": os.path.join(base_dir, "TRIAL MATEMATIK KEDAH 2025.pdf"),
            "m_path": os.path.join(base_dir, "SKEMA KEDAH 2025.pdf")
        },
    ]

    for paper in papers_to_process:
        print(f"\n{'='*50}\nStarting Processing for: {paper['id']}\n{'='*50}")
        
        # Check if the files actually exist before running to avoid sudden crashes
        if not os.path.exists(paper["q_path"]) or not os.path.exists(paper["m_path"]):
            print(f"Skipping {paper['id']} - One or both PDF files not found.")
            continue
        RATE_LIMIT_LOCK = None
        PAGE_SEMAPHORE = None
        MARKING_SEMAPHORE = None

        asyncio.run(process_question_and_marking_pdfs_full_page(
            question_pdf_path=paper["q_path"],
            marking_pdf_path=paper["m_path"],
            question_client=openai_async_client,
            marking_client=gemini_async_client,
            exam_name="SPM Trial",
            subject="Mathematics",
            year="2025",
            question_model="gemini-3.5-flash-lite",
            marking_model="gemini-3.5-flash-lite",
            question_start_page=1,
            marking_start_page=2,
            output_prefix=paper["id"]
        ))

# if __name__ == "__main__":
#     # question_pdf_path = r"C:\Users\YK\Documents\Degree Y3\FYP\Test Paper\2020 Johor MPSM Matematik K2.pdf"
#     # question_pdf_path = r"C:\Users\YK\Documents\Degree Y3\FYP\Implementation\Sample Ques\2021 SPM Maths K2.pdf"
#     # marking_pdf_path = r"C:\Users\YK\Documents\Degree Y3\FYP\Test Paper\2020 Johor MPSM Matematik K2 Jawapan.pdf"
#     # question1_pdf_path = r"C:\Users\YK\Documents\Degree Y3\FYP\Test Paper\2025_SOALAN _MATEMATIK_UD3_KERTAS 2.pdf"
#     # question2_pdf_path = r"C:\Users\YK\Documents\Degree Y3\FYP\Test Paper\K2 Maths PPC Pulau Pinang 2025.pdf"
#     # question3_pdf_path = r"C:\Users\YK\Documents\Degree Y3\FYP\Test Paper\TRIAL JOHOR KERTAS 2 2025 - SET 2.pdf"
#     question4_pdf_path = r"C:\Users\YK\Documents\Degree Y3\FYP\Test Paper\K2 MATEMATIK PPC PERAK 2025.pdf"
#     # # question5_pdf_path = r"C:\Users\YK\Documents\Degree Y3\FYP\Test Paper\K2 PPC MATH Terengganu 2025.pdf"
#     # marking1_pdf_path = r"C:\Users\YK\Documents\Degree Y3\FYP\Test Paper\2025_PERATURAN_PEMARKAHAN_MATEMATIK_UD3_KERTAS_2.pdf"
#     # marking2_pdf_path = r"C:\Users\YK\Documents\Degree Y3\FYP\Test Paper\Skema Maths K2 PPC Pulau Pinang 2025.pdf"
#     # marking3_pdf_path = r"C:\Users\YK\Documents\Degree Y3\FYP\Test Paper\SKEMA TRIAL JOHOR K2-SET 2.pdf"
#     # marking4_pdf_path = r"C:\Users\YK\Documents\Degree Y3\FYP\Test Paper\SKEMA PERAK K2.pdf"
#     # marking5_pdf_path = r"C:\Users\YK\Documents\Degree Y3\FYP\Test Paper\SKEMA K1 K2 TGANU 2025.pdf"

#     # question_pdf_path = r"C:\Users\YK\Documents\Degree Y3\FYP\Implementation\Sample Ques\2023 Selangor Matematik K2.pdf"
#     # marking_pdf_path = r"C:\Users\YK\Documents\Degree Y3\FYP\Implementation\Sample Ques\2023 Selangor Matematik K2 Skema.pdf"
#     # question_pdf_path = r"C:\Users\YK\Documents\Degree Y3\FYP\Implementation\Sample Ques\Trial K2 Matematik SPM 2024 - Johor_JB SET 2.pdf"
#     # marking_pdf_path = r"C:\Users\YK\Documents\Degree Y3\FYP\Implementation\Sample Ques\Trial Skema K2 Matematik SPM 2024 - Johor_JB SET 2.pdf"
#     # doc = fitz.open(question_pdf_path)
#     # page = doc[11]  # 0-indexed, so page 12 = index 11
#     # zoom = 200 / 72
#     # matrix = fitz.Matrix(zoom, zoom)
#     # pix = page.get_pixmap(matrix=matrix, alpha=False)
#     # image_path = "page_12_test.png"
#     # pix.save(image_path)
#     # doc.close()
#     # result = parse_question_page_with_vision(image_path, client)  # pass None for client since we're just testing rendering
#     # result = clean_parsed_questions(result)
#     # print(json.dumps(result, indent=2, ensure_ascii=False)) 
#     asyncio.run(
#         process_question_and_marking_pdfs_full_page(
#         question_pdf_path=question4_pdf_path,
#         marking_pdf_path=None,
#         client=aclient,  # uses your existing OpenAI/Gemini client
#         exam_name="SPM Trial",
#         subject="Mathematics",
#         year="2024",
#         model="gemini-3.5-flash-lite",
#         question_start_page=28,
#         question_end_page=35,
#         question_page_numbers=None,
#         marking_start_page=None,
#         marking_end_page=None,
#         marking_page_numbers=None,
#         # question_page_numbers=[4]  # e.g. [27] to only process page 27
#         )
#     )