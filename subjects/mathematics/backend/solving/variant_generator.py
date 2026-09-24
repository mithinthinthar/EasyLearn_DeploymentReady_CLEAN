from collections import defaultdict
import os
import json
import re
from solving.config import openai_client, get_db_connection, normalize_response_language, get_response_language_rules
from solving.format_json import AgentOutputProcessor
from solving.extractor import format_image_for_llm

K1_MUTATION_TYPES = [
    "text_number_switch",
    "diagram_text_number_switch",
    "diagram_target_switch",
    "representation_switch",
    "reverse_question",
    "complement_switch",
    "condition_switch",
    "property_switch",
    "method_switch",
    "statement_switch",
    "misconception_switch",
]

def parse_db_json(value, fallback):
    if value is None:
        return fallback

    if isinstance(value, (dict, list)):
        return value

    try:
        return json.loads(value)
    except Exception:
        return fallback


def is_form4_only_source(source_question):
    rows = source_question if isinstance(source_question, list) else [source_question]

    for row in rows:
        if not isinstance(row, dict):
            continue

        form_value = (
            row.get("form")
            or row.get("verified_form")
            or row.get("group_form")
            or row.get("form_snapshot")
            or ""
        )

        if str(form_value).strip().lower() not in ["form 4", "f4", "tingkatan 4"]:
            return False

    return True

def extract_single_letter_labels_from_source(source_question):
    labels = set()

    items = source_question if isinstance(source_question, list) else [source_question]

    def scan_value(value):
        if isinstance(value, dict):
            for key, val in value.items():
                # avoid scanning MCQ option labels A-D
                if key == "options":
                    continue
                scan_value(val)
        elif isinstance(value, list):
            for item in value:
                scan_value(item)
        else:
            text = str(value or "")
            for match in re.findall(r"\b[A-Z]\b", text):
                # avoid common option letters if they only appear as choices
                labels.add(match)

    for q in items:
        if not isinstance(q, dict):
            continue

        scan_value(q.get("instructions_en", []))
        scan_value(q.get("instructions_ms", []))
        scan_value(q.get("table_data", {}))
        scan_value(q.get("given_values", {}))

    # Remove common MCQ labels unless they are the only possible labels
    labels = labels - {"A", "B", "C", "D"}

    return sorted(labels)

def classify_logical_reasoning_task(row):
    text = json.dumps({
        "instructions_en": row.get("instructions_en", []),
        "instructions_ms": row.get("instructions_ms", []),
        "table_data": row.get("table_data", {}),
        "diagram_type": row.get("diagram_type", ""),
    }, ensure_ascii=False).lower()

    if any(x in text for x in ["negation", "truth value", "penafian", "nilai kebenaran"]):
        return "negation_truth_value"

    if any(x in text for x in ["valid and sound", "sah dan munasabah"]):
        return "valid_sound_argument"

    if any(x in text for x in ["strong or weak", "cogent", "kuat atau lemah", "meyakinkan"]):
        return "strong_cogent_argument"

    if any(x in text for x in ["converse", "inverse", "contrapositive", "akas", "songsangan", "kontrapositif"]):
        return "converse_inverse_contrapositive"

    if any(x in text for x in ["inductive conclusion", "kesimpulan induktif"]):
        return "inductive_conclusion"

    if any(x in text for x in ["compound statement", "pernyataan majmuk"]):
        return "compound_statement"

    return "general_logical_reasoning"

def is_mixed_task_stage(source_rows):
    if not isinstance(source_rows, list) or len(source_rows) <= 1:
        return False

    task_types = {
        classify_logical_reasoning_task(row)
        for row in source_rows
    }

    return len(task_types) > 1

def force_existing_visual_label_for_k1(variant, source_question):
    labels = extract_single_letter_labels_from_source(source_question)

    if len(labels) != 1:
        return variant

    correct_label = labels[0]
    question = variant.get("question", {})

    for field in ["instructions_en", "instructions_ms"]:
        lines = question.get(field, [])

        if not isinstance(lines, list):
            continue

        fixed_lines = []

        for line in lines:
            line = str(line)

            # English: card labeled N / card labelled N / card marked N
            line = re.sub(
                r"\b(card\s+(?:labeled|labelled|marked)\s+)([A-Z])\b",
                lambda m: m.group(1) + correct_label,
                line,
                flags=re.IGNORECASE
            )

            # Malay: kad bertanda N
            line = re.sub(
                r"\b(kad\s+bertanda\s+)([A-Z])\b",
                lambda m: m.group(1) + correct_label,
                line,
                flags=re.IGNORECASE
            )

            # General fallback: value of N / nilai N
            line = re.sub(
                r"\b(value\s+of\s+)([A-Z])\b",
                lambda m: m.group(1) + correct_label,
                line,
                flags=re.IGNORECASE
            )

            line = re.sub(
                r"\b(nilai\s+)([A-Z])\b",
                lambda m: m.group(1) + correct_label,
                line,
                flags=re.IGNORECASE
            )

            fixed_lines.append(line)

        question[field] = fixed_lines

    variant["question"] = question
    return variant

def enforce_safe_question_image_placement(variant, source_rows):
    """
    Safely place question images for normal stage variants and grouped variants.

    Main rules:
    1. For group variants with question.stages, match images by stage_index.
    2. For normal stage variants with question.questions, match images by part/subpart.
    3. Do not put one subpart/stage image at parent level unless every source row shares the same image.
    4. If a node has no image, remove image_0 from its sequence.
    """

    if not isinstance(variant, dict):
        return variant

    question = variant.get("question") or {}

    if not isinstance(question, dict):
        return variant

    if not isinstance(source_rows, list):
        source_rows = []

    source_rows = [row for row in source_rows if isinstance(row, dict)]

    def normalize_stage_index(value, fallback="1"):
        try:
            return str(int(value))
        except Exception:
            return str(fallback)

    def label_key(item):
        return "|".join([
            str(item.get("part") or "").strip().lower(),
            str(item.get("subpart") or "").strip().lower(),
            str(item.get("sub_subpart") or "").strip().lower(),
        ])

    def stage_label_key(item, fallback_stage="1"):
        return "|".join([
            normalize_stage_index(item.get("stage_index"), fallback_stage),
            str(item.get("part") or "").strip().lower(),
            str(item.get("subpart") or "").strip().lower(),
            str(item.get("sub_subpart") or "").strip().lower(),
        ])

    def get_first_image(item):
        if not isinstance(item, dict):
            return ""

        image_path = str(item.get("image_path") or "").strip()

        if image_path:
            return image_path

        image_urls = item.get("image_urls")

        if isinstance(image_urls, list):
            for url in image_urls:
                url = str(url or "").strip()

                if url:
                    return url

        return ""

    def remove_image_from_node(node):
        if not isinstance(node, dict):
            return node

        node["image_path"] = ""
        node["image_urls"] = []

        sequence = node.get("sequence")

        if isinstance(sequence, list):
            node["sequence"] = [
                item for item in sequence
                if not str(item).startswith("image_")
            ]

        return node

    def set_image_on_node(node, image_url):
        if not isinstance(node, dict):
            return node

        image_url = str(image_url or "").strip()

        if not image_url:
            return remove_image_from_node(node)

        node["image_path"] = image_url
        node["image_urls"] = [image_url]

        sequence = node.get("sequence")

        if not isinstance(sequence, list):
            sequence = []

        if not any(str(item).startswith("image_") for item in sequence):
            sequence.insert(0, "image_0")

        node["sequence"] = sequence
        node["has_diagram"] = 1

        return node

    def all_rows_share_same_image(rows):
        rows = [row for row in rows if isinstance(row, dict)]

        if not rows:
            return ""

        images = [get_first_image(row) for row in rows]

        if not all(images):
            return ""

        unique_images = set(images)

        if len(unique_images) == 1:
            return images[0]

        return ""

    # Build source image lookup
    source_by_stage = {}

    for index, row in enumerate(source_rows):
        stage_key = normalize_stage_index(row.get("stage_index"), index + 1)
        source_by_stage.setdefault(stage_key, []).append(row)

    source_image_by_stage_label = {}

    for index, row in enumerate(source_rows):
        fallback_stage = normalize_stage_index(row.get("stage_index"), index + 1)
        key = stage_label_key(row, fallback_stage)
        source_image_by_stage_label[key] = get_first_image(row)

    source_image_by_label = {}

    for row in source_rows:
        source_image_by_label[label_key(row)] = get_first_image(row)

    # ==================================================
    # CASE 1: Group variant: question.stages
    # ==================================================
    stages = question.get("stages")

    if isinstance(stages, list) and stages:
        # For group questions, do not keep image at parent level.
        # Images should belong to each stage.
        remove_image_from_node(question)

        for stage_index, stage in enumerate(stages):
            if not isinstance(stage, dict):
                continue

            current_stage_key = normalize_stage_index(
                stage.get("stage_index"),
                stage_index + 1
            )

            source_stage_rows = source_by_stage.get(current_stage_key, [])

            # Some generated stages may not preserve stage_index correctly.
            # Fallback to row order.
            if not source_stage_rows and stage_index < len(source_rows):
                source_stage_rows = [source_rows[stage_index]]

            nested_rows = []

            if isinstance(stage.get("questions"), list):
                nested_rows = stage.get("questions")
            elif isinstance(stage.get("subparts"), list):
                nested_rows = stage.get("subparts")

            # If this stage has nested generated subparts,
            # assign image to nested subparts, not blindly to the stage.
            if nested_rows:
                shared_stage_image = all_rows_share_same_image(source_stage_rows)

                if shared_stage_image:
                    set_image_on_node(stage, shared_stage_image)
                else:
                    remove_image_from_node(stage)

                for sub_index, sub_q in enumerate(nested_rows):
                    if not isinstance(sub_q, dict):
                        continue

                    key = stage_label_key(sub_q, current_stage_key)
                    source_image = source_image_by_stage_label.get(key, "")

                    # fallback within same stage by order
                    if not source_image and sub_index < len(source_stage_rows):
                        source_image = get_first_image(source_stage_rows[sub_index])

                    if source_image:
                        set_image_on_node(sub_q, source_image)
                    else:
                        remove_image_from_node(sub_q)

            else:
                # Stage itself is the generated question.
                key = stage_label_key(stage, current_stage_key)
                source_image = source_image_by_stage_label.get(key, "")

                if not source_image and len(source_stage_rows) == 1:
                    source_image = get_first_image(source_stage_rows[0])

                if not source_image:
                    source_image = all_rows_share_same_image(source_stage_rows)

                if source_image:
                    set_image_on_node(stage, source_image)
                else:
                    remove_image_from_node(stage)

        question["stages"] = stages
        variant["question"] = question
        return variant

    # ==================================================
    # CASE 2: Normal stage variant: question.questions / question.subparts
    # ==================================================
    generated_subquestions = []

    if isinstance(question.get("questions"), list):
        generated_subquestions = question.get("questions")
    elif isinstance(question.get("subparts"), list):
        generated_subquestions = question.get("subparts")

    shared_parent_image = all_rows_share_same_image(source_rows)

    if generated_subquestions:
        # Parent image allowed only if all source rows share the same image.
        if shared_parent_image:
            set_image_on_node(question, shared_parent_image)
        else:
            remove_image_from_node(question)

        for index, sub_q in enumerate(generated_subquestions):
            if not isinstance(sub_q, dict):
                continue

            source_image = source_image_by_label.get(label_key(sub_q), "")

            if not source_image and index < len(source_rows):
                source_image = get_first_image(source_rows[index])

            if source_image:
                set_image_on_node(sub_q, source_image)
            else:
                remove_image_from_node(sub_q)

    else:
        # Single generated question
        if len(source_rows) == 1:
            source_image = get_first_image(source_rows[0])
        else:
            source_image = shared_parent_image

        if source_image:
            set_image_on_node(question, source_image)
        else:
            remove_image_from_node(question)

    variant["question"] = question
    return variant

def fetch_question_source_for_variant(question_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            q.id AS question_id,
            q.paper_id,
            q.question_no,
            q.question_type,
            q.form,
            q.chapter,
            q.verified_form,
            q.verified_chapter,
            q.instructions_en,
            q.instructions_ms,
            q.sequence,
            q.table_data,
            q.given_values,
            q.options,
            q.has_diagram,
            q.diagram_type,
            q.image_path,
            q.display_marks,
            q.difficulty,
            q.difficulty_level,
            m.final_answer AS correct_option,
            m.raw_json AS marking_scheme_json
        FROM questions q
        LEFT JOIN question_marking_links qml
            ON q.id = qml.question_id
        LEFT JOIN marking_schemes m
            ON m.id = qml.marking_scheme_id
        WHERE q.id = %s
        LIMIT 1
    """, (question_id,))

    rows = cursor.fetchall()

    cursor.close()
    conn.close()

    return rows

def fetch_stage_source_for_variant(exercise_stage_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            q.id AS question_id,
            q.exercise_stage_id,
            q.question_no,
            q.part,
            q.subpart,
            q.sub_subpart,
            q.instructions_en,
            q.instructions_ms,
            q.sequence,
            q.table_data,
            q.given_values,
            q.has_diagram,
            q.diagram_type,
            q.image_path,
            q.display_marks,
            q.form,
            q.chapter,
            q.verified_form,
            q.verified_chapter,
            q.difficulty,
            q.difficulty_level,
            q.group_difficulty_level,
            m.raw_json AS marking_scheme_json
        FROM questions q
        LEFT JOIN question_marking_links qml
            ON q.id = qml.question_id
        LEFT JOIN marking_schemes m
            ON m.id = qml.marking_scheme_id
        WHERE q.exercise_stage_id = %s
        ORDER BY
            q.question_no + 0,
            q.part,
            q.subpart,
            q.sub_subpart
    """, (exercise_stage_id,))

    rows = cursor.fetchall()

    cursor.close()
    conn.close()

    return rows


def fetch_group_source_for_variant(group_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            q.id AS question_id,
            q.exercise_stage_id,
            q.group_id,
            q.stage_index,
            q.question_no,
            q.part,
            q.subpart,
            q.sub_subpart,
            q.instructions_en,
            q.instructions_ms,
            q.form,
            q.chapter,
            q.verified_form,
            q.verified_chapter,
            q.group_form,
            q.group_chapter,
            q.sequence,
            q.table_data,
            q.given_values,
            q.has_diagram,
            q.diagram_type,
            q.image_path,
            q.display_marks,
            m.raw_json AS marking_scheme_json
        FROM questions q
        LEFT JOIN question_marking_links qml
            ON q.id = qml.question_id
        LEFT JOIN marking_schemes m
            ON m.id = qml.marking_scheme_id
        WHERE q.group_id = %s
          AND COALESCE(q.group_chapter, '') != 'Mixed'
        ORDER BY
            COALESCE(q.stage_index, 1),
            q.question_no + 0,
            q.part,
            q.subpart,
            q.sub_subpart
    """, (group_id,))

    rows = cursor.fetchall()

    cursor.close()
    conn.close()

    return rows

def build_source_from_rows(rows):
    source_question = []
    source_marking_scheme = []

    for row in rows:
        source_question.append({
            "question_id": row.get("question_id"),
            "exercise_stage_id": row.get("exercise_stage_id"),
            "group_id": row.get("group_id"),
            "stage_index": row.get("stage_index"),
            "question_no": row.get("question_no"),
            "question_type": row.get("question_type"),
            "form": row.get("verified_form") or row.get("form"),
            "chapter": row.get("verified_chapter") or row.get("chapter"),
            "options": parse_db_json(row.get("options"), []),
            "correct_option": row.get("correct_option"),
            "difficulty": row.get("difficulty"),
            "difficulty_level": row.get("difficulty_level"),
            "part": row.get("part"),
            "subpart": row.get("subpart"),
            "sub_subpart": row.get("sub_subpart"),
            "instructions_en": parse_db_json(row.get("instructions_en"), []),
            "instructions_ms": parse_db_json(row.get("instructions_ms"), []),
            "sequence": parse_db_json(row.get("sequence"), []),
            "table_data": parse_db_json(row.get("table_data"), {}),
            "given_values": parse_db_json(row.get("given_values"), {}),
            "has_diagram": row.get("has_diagram"),
            "diagram_type": row.get("diagram_type"),
            "image_path": row.get("image_path"),
            "display_marks": row.get("display_marks"),
        })

        marking_json = row.get("marking_scheme_json")

        if marking_json:
            source_marking_scheme.append(parse_db_json(marking_json, marking_json))

    return source_question, source_marking_scheme

def regenerate_k2_marking_scheme_from_original(
    variant,
    source_question,
    source_marking_scheme,
    language="english",
    image_url = ""
):
    """
    Generate a marking scheme for the generated K2 question.

    The generated question is the source of truth.
    The original marking scheme is only used as method/style/marking guidance.
    """
    language = normalize_response_language(language)
    language_rules = get_response_language_rules(language)

    generated_question = variant.get("question", {}) or {}

    system_prompt = f"""
You are a strict Malaysian SPM Mathematics solver and marking scheme writer.

{language_rules}

TASK:
Generate the marking_scheme for a GENERATED K2 review question.

SOURCE OF TRUTH PRIORITY:
1. GENERATED QUESTION is the source of truth for all numbers, variables, tables, diagrams, and final answers.
2. ORIGINAL MARKING SCHEME is only a guide for:
   - method
   - step style
   - mark allocation
   - SPM marking format
   - units and rounding style
3. Do NOT copy old numbers, old calculations, or old final answers from the original marking scheme.
4. Recalculate everything using the GENERATED QUESTION.
5. Preserve the generated question's part/subpart labels.
6. The total marks in marking_scheme.steps must match the generated question display_marks.
7. Output valid JSON only.

CHAIN OF THOUGHT RULE (CRITICAL):
You MUST fill out the "calculation_scratchpad" object strictly step-by-step BEFORE generating the final `steps` array. 
1. Extract the exact numbers from the GENERATED QUESTION.
2. Solve the math perfectly.
3. Plan how to award the marks based on the `display_marks`.
4. Finally, populate the `steps` array using the exact math from your scratchpad.

OUTPUT FORMAT:
{{
  "calculation_scratchpad": {{
    "step_1_extract_values": "Extract values from the GENERATED QUESTION and diagram.",
    "step_2_perform_math": "Show the exact calculation step-by-step to find the true final answers.",
    "step_3_plan_marks": "Plan how to distribute the marks across the required steps."
  }},
  "max_score": 0,
  "steps": [
    {{
      "display_subpart_label": "(a)",
      "step": "Step title",
      "text": "What the student should do",
      "math": "Raw LaTeX/math working only",
      "marks": 1
    }}
  ],
  "final_answers": {{
    "(a)": "Final answer"
  }}
}}
"""

    user_prompt = f"""
GENERATED QUESTION:
{json.dumps(generated_question, ensure_ascii=False, indent=2)}

ORIGINAL QUESTION:
{json.dumps(source_question, ensure_ascii=False, indent=2)}

ORIGINAL MARKING SCHEME FOR STYLE ONLY:
{json.dumps(source_marking_scheme, ensure_ascii=False, indent=2)}

Generate the marking_scheme for the GENERATED QUESTION now.
"""
    user_content = [{"type": "text", "text": user_prompt}]
    
    # Give the MS generator eyes
    if image_url:
        user_content.append({
            "type": "image_url",
            "image_url": {"url": image_url}
        })
    response = openai_client.chat.completions.create(
        model="gemini-3.5-flash-lite",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.1,
        response_format={"type": "json_object"}
    )

    marking_scheme = AgentOutputProcessor.process(response.choices[0].message.content)
    marking_scheme = AgentOutputProcessor._walk_and_format(marking_scheme)

    return marking_scheme

def validate_regenerated_k2_marking_scheme(variant, marking_scheme):
    issues = []

    if not isinstance(marking_scheme, dict):
        return {
            "valid": False,
            "issues": ["Regenerated K2 marking scheme is not a dictionary."]
        }

    steps = marking_scheme.get("steps") or []
    final_answers = marking_scheme.get("final_answers") or {}

    if not isinstance(steps, list) or not steps:
        issues.append("Regenerated K2 marking scheme has no steps.")

    if not isinstance(final_answers, dict) or not final_answers:
        issues.append("Regenerated K2 marking scheme has no final_answers.")

    total_step_marks = 0

    for step in steps:
        if not isinstance(step, dict):
            issues.append("A marking step is not a dictionary.")
            continue

        if not step.get("display_subpart_label"):
            issues.append("A marking step is missing display_subpart_label.")

        try:
            total_step_marks += int(step.get("marks") or 0)
        except Exception:
            issues.append(f"Invalid marks value in step: {step}")

    question = variant.get("question", {}) or {}
    generated_rows = question.get("questions") or []

    expected_marks = 0

    if isinstance(generated_rows, list) and generated_rows:
        for row in generated_rows:
            if isinstance(row, dict):
                expected_marks += safe_int(row.get("display_marks"), 1)
    else:
        expected_marks = safe_int(question.get("display_marks"), total_step_marks)

    if expected_marks and total_step_marks != expected_marks:
        issues.append(
            f"Mark total mismatch: expected {expected_marks}, got {total_step_marks}."
        )

    marking_scheme["max_score"] = total_step_marks

    return {
        "valid": len(issues) == 0,
        "issues": issues,
        "marking_scheme": marking_scheme
    }

def get_topic_method_rules(source_question, source_marking_scheme=None):
    """
    Add topic-specific rules only when the source question needs them.
    This avoids hardcoding every chapter while still preventing common LLM mistakes.
    """

    text_blob = json.dumps(
        {
            "source_question": source_question,
            "source_marking_scheme": source_marking_scheme or {},
        },
        ensure_ascii=False
    ).lower()

    rules = []

    # ==================================================
    # 1. NUMBER BASES
    # ==================================================
    is_number_base = (
        "number bases" in text_blob
        or "asas nombor" in text_blob
        or "base seven" in text_blob
        or "base eight" in text_blob
        or "base five" in text_blob
        or "base 7" in text_blob
        or "base 8" in text_blob
        or "base 5" in text_blob
        or re.search(r"\$?\d+_\{?\d+\}?\$?", text_blob)
    )
    is_logical_reasoning = (
    "logical reasoning" in text_blob
    or "penaakulan logik" in text_blob
    or "converse" in text_blob
    or "inverse" in text_blob
    or "contrapositive" in text_blob
    or "akas" in text_blob
    or "songsangan" in text_blob
    or "kontrapositif" in text_blob
)
    if is_logical_reasoning:
        rules.append(r"""
    TOPIC METHOD RULE: LOGICAL REASONING

    COMPLETE STATEMENT RULE:
    - If the generated question asks for converse, inverse, or contrapositive, the implication statement MUST be included in the question.
    - Do not write "State the converse of the following statement" without showing the statement.
    - The question must contain an implication in the form:
    "If P, then Q."
    or
    "Jika P, maka Q."

    QUESTION TEXT SYMBOL RULE:
    - In visible question instructions, use Unicode symbols:
    ∪, ∩, ≠, ⊂, ⊆
    - Do not use raw LaTeX commands like \cup, \cap, \neq in visible question text.
    - Raw LaTeX is allowed only in marking_scheme.steps[n].math.

    DIAGRAM RELEVANCE RULE:
    - If the original diagram shows rectangles, squares, graphs, or patterns, do not ask about triangles unless triangles are actually visible or stated.
    - Do not invent a new object that is not visible in the diagram.
    - For pattern diagrams, the generated question must ask about the actual object shown in the diagram.
    """)
    if is_number_base:
        rules.append(r"""
TOPIC METHOD RULE: NUMBER BASES

NUMBER BASE NOTATION RULE:
- A number written as $433_7$ means 433 in base 7, not 4337.
- Do not remove the underscore or base subscript.
- Do not rewrite $433_7$ as 4337.
- Always write base notation using LaTeX, such as $433_7$ or $433_{7}$.
- In instructions_en, instructions_ms, marking_scheme.math, and final_answer, preserve base notation.

BASE CONVERSION METHOD RULE:
- If converting FROM another base TO base 10, use expanded powers.
  Correct example:
  $433_7 = 4(7^2) + 3(7^1) + 3(7^0) = 220_{10}$

- If converting FROM base 10 TO another base, use repeated division by the target base.
  Correct example:
  84 ÷ 8 = 10 remainder 4
  10 ÷ 8 = 1 remainder 2
  1 ÷ 8 = 0 remainder 1
  Therefore, $84_{10} = 124_8$.

- Do not use expanded powers as the main working when converting base 10 to another base.
- Do not use repeated division when converting another base to base 10.

NUMBER BASE QUESTION WORDING RULE:
- If the original number is already written as $433_7$, do not ask "write 4337 in base seven".
- Correct wording:
  "Write $433_7$ in base ten."
  "Convert $433_7$ to base ten."
  "The actual number is $433_7$. Imran guessed 235. Determine whether his guess was correct."

COMPARISON COMPLETION RULE:
- If the question asks whether a guess is correct, the final answer must compare both values and state the conclusion.
- Example:
  $433_7 = 220_{10}$.
  Since $235 \ne 220$, Imran's guess is not correct.
- Do not stop after only converting the number.
""")

    # ==================================================
    # 2. FINANCIAL / BUDGET / AFFORDABILITY
    # ==================================================
    is_financial = (
        "financial" in text_blob
        or "consumer mathematics" in text_blob
        or "budget" in text_blob
        or "afford" in text_blob
        or "price" in text_blob
        or "cost" in text_blob
        or "rm" in text_blob
        or "loan" in text_blob
        or "insurance" in text_blob
        or "tax" in text_blob
        or "cukai" in text_blob
        or "harga" in text_blob
    )

    if is_financial:
        rules.append(r"""
TOPIC METHOD RULE: FINANCIAL / BUDGET / AFFORDABILITY

CHOICE AND QUANTITY CLARITY RULE:
- If the question involves buying/selecting more than one item from multiple brands/types, the wording must clearly state whether the items must be the same type or can be different types.
- If the solution multiplies one item price by 2, the question must explicitly say "two items of the same brand/type".
- If the question only says "buy two bags/items" without saying same brand/type, then the marking scheme must consider mixed combinations.
- Do not ask "which brand can he afford" if mixed-brand combinations are allowed. Instead ask "which combinations can he afford".

AFFORDABILITY FINAL ANSWER RULE:
- If the question asks which brand/item/person/combination can be afforded, the final answer must explicitly state the affordable choice.
- Compare every relevant option.
- Do not only state which option is not affordable.

Correct example:
Brand Q + Brand Q = RM190, affordable.
Brand Q + Brand Z = RM271, affordable.
Brand Z + Brand Z = RM352, not affordable.
Therefore, he can buy two Brand Q bags or one Brand Q and one Brand Z bag.

If same brand is intended:
Two Brand Q bags = RM190, affordable.
Two Brand Z bags = RM352, not affordable.
Therefore, he can afford Brand Q only.
""")

    # ==================================================
    # 3. GRAPHS OF MOTION
    # ==================================================
    is_motion_graph = (
        "graphs of motion" in text_blob
        or "graf gerakan" in text_blob
        or "speed-time" in text_blob
        or "distance-time" in text_blob
        or "velocity-time" in text_blob
        or "speed time" in text_blob
        or "distance time" in text_blob
    )

    if is_motion_graph:
        rules.append(r"""
TOPIC METHOD RULE: GRAPHS OF MOTION

MOTION GRAPH METHOD RULE:
- For a distance-time graph, gradient represents speed.
- For a speed-time or velocity-time graph, area under the graph represents distance.
- Do not confuse gradient and area.
- If the question asks distance from a speed-time graph, use area of the relevant region.
- If the question asks speed from a distance-time graph, use gradient.
- If units are involved, keep units consistent, such as m/s, km/h, seconds, hours.

GRAPH VALUE RULE:
- If image_path exists, do not invent new graph coordinates, times, speeds, or distances not visible in the graph.
- If using a graph reading, every value used must be visible in the graph or stated in the question.
""")

    # ==================================================
    # 4. TRANSFORMATION / ENLARGEMENT
    # ==================================================
    is_transformation = (
        "transformation" in text_blob
        or "transformations" in text_blob
        or "enlargement" in text_blob
        or "reflection" in text_blob
        or "rotation" in text_blob
        or "translation" in text_blob
        or "pembesaran" in text_blob
        or "penjelmaan" in text_blob
    )

    if is_transformation:
        rules.append(r"""
TOPIC METHOD RULE: TRANSFORMATION / ENLARGEMENT

TRANSFORMATION METHOD RULE:
- For enlargement, length scale factor is k.
- Area scale factor is k^2.
- Do not use k when the question asks for area ratio; use k^2.
- Do not use k^2 when the question asks for length ratio; use k.
- For combined transformations, apply the transformations in the correct order stated in the question.

DIAGRAM LOCK RULE:
- If image_path exists, do not invent new points, coordinates, centres, lines of reflection, or scale factors not shown or stated.
- If asking for a different transformation detail, it must be readable from the same diagram.
""")

    # ==================================================
    # 5. PROBABILITY
    # ==================================================
    is_probability = (
        "probability" in text_blob
        or "kebarangkalian" in text_blob
        or "tree diagram" in text_blob
        or "sample space" in text_blob
        or "at least" in text_blob
        or "at most" in text_blob
        or "both" in text_blob
        or "either" in text_blob
    )

    if is_probability:
        rules.append(r"""
TOPIC METHOD RULE: PROBABILITY

PROBABILITY EVENT RULE:
- Clearly define the event being calculated.
- For "at least one", use complement if easier:
  P(at least one) = 1 - P(none).
- For "both", multiply along the relevant branches.
- For "either/or", add mutually exclusive cases.
- Do not confuse "at least one" with "exactly one".
- Do not confuse "not A" with "A".

PROBABILITY ANSWER RULE:
- Final probability must be between 0 and 1.
- Give the answer as a fraction unless the question asks for decimal or percentage.
- If using a tree diagram, every probability used must appear in the tree/question.
""")

    # ==================================================
    # 6. STATISTICS
    # ==================================================
    is_statistics = (
        "statistics" in text_blob
        or "dispersion" in text_blob
        or "mean" in text_blob
        or "median" in text_blob
        or "mode" in text_blob
        or "variance" in text_blob
        or "standard deviation" in text_blob
        or "quartile" in text_blob
        or "interquartile" in text_blob
        or "histogram" in text_blob
        or "ogive" in text_blob
        or "sukatan serakan" in text_blob
    )

    if is_statistics:
        rules.append(r"""
TOPIC METHOD RULE: STATISTICS

STATISTICS METHOD RULE:
- For mean, use total value divided by total frequency.
- For grouped data mean, use midpoint × frequency.
- For variance, use the correct formula and do not confuse variance with standard deviation.
- Standard deviation is the square root of variance.
- For median/quartiles from cumulative frequency or ogive, use the correct position, not just the middle class by appearance.
- If reading from a graph/table, every value used must be visible in the graph/table.

FINAL ANSWER RULE:
- If the question asks for interpretation or comparison, the final answer must include a short conclusion, not only a number.
""")

    # ==================================================
    # 7. GENERAL MATH OUTPUT QUALITY RULE
    # ==================================================
    if rules:
        rules.append(r"""
GENERAL TOPIC-SPECIFIC OUTPUT RULE:
- The "math" field must contain valid mathematical working only.
- Do not place the final answer as a separate step titled "Final answer".
- Do not create a separate marking step titled "Final answer".
- For a single-answer question, store the result in marking_scheme.final_answer.
- For a multi-subpart question, store results in marking_scheme.final_answers using labels such as "(a)", "(b)", "(c)(i)".
- Every generated subpart must have a final answer, either in step.final_answer or in marking_scheme.final_answers.
- If words are needed inside math, wrap them using \text{...}.
- Do not mix raw English/Malay words directly inside LaTeX math.
""")

    return "\n".join(rules)

def _variant_label_tuple(row):
    return (
        str(row.get("part") or "").strip().lower(),
        str(row.get("subpart") or "").strip().lower(),
        str(row.get("sub_subpart") or "").strip().lower(),
    )


def _variant_norm_text(value):
    return re.sub(r"\s+", " ", str(value or "")).strip().lower()


# ==================================================
# SAFE VALUE-ONLY VARIANT HELPERS
# ==================================================
def _visible_label(row):
    """Return human-readable label like (a)(ii) for validator messages."""
    if not isinstance(row, dict):
        return ""

    label = ""
    for key in ["part", "subpart", "sub_subpart"]:
        value = str(row.get(key) or "").strip()
        if value:
            label += f"({value})"
    return label


def _has_nonempty_lines(value):
    return isinstance(value, list) and any(str(line or "").strip() for line in value)


def _has_visible_payload(row):
    """A subquestion must have at least a command/text, table, or image."""
    if not isinstance(row, dict):
        return False

    return (
        _has_nonempty_lines(row.get("instructions_en"))
        or _has_nonempty_lines(row.get("instructions_ms"))
        or bool(row.get("table_data"))
        or bool(row.get("image_path"))
        or bool(row.get("image_urls"))
        or bool(row.get("given_values"))
    )


def _instruction_key(row, field="instructions_en"):
    if not isinstance(row, dict):
        return ""
    lines = row.get(field) or []
    if not isinstance(lines, list):
        lines = [lines]
    return _variant_norm_text(" ".join(str(x or "") for x in lines))


def _source_task_signature(row):
    """
    Lightweight task classifier used only for value-only validation.
    It groups by instruction verb / skill, not by chapter.
    """
    if not isinstance(row, dict):
        return "unknown"

    text = json.dumps(
        {
            "instructions_en": row.get("instructions_en", []),
            "instructions_ms": row.get("instructions_ms", []),
            "table_data": row.get("table_data", {}),
            "diagram_type": row.get("diagram_type", ""),
        },
        ensure_ascii=False,
    ).lower()

    logical_task = classify_logical_reasoning_task(row)
    if logical_task != "general_logical_reasoning":
        return logical_task

    if any(k in text for k in ["shade", "shaded", "lorek", "venn", "∪", "∩", "\\cup", "\\cap"]):
        return "diagram_shading"
    if any(k in text for k in ["complete the table", "lengkapkan jadual", "table", "jadual"]):
        return "table_completion_or_reading"
    if any(k in text for k in ["draw", "plot", "construct", "lukis", "bina"]):
        return "draw_construct"
    if any(k in text for k in ["calculate", "find", "determine", "hitung", "cari", "tentukan"]):
        return "calculation_determine"
    if any(k in text for k in ["state", "write", "nyatakan", "tulis"]):
        return "state_write"
    if any(k in text for k in ["justify", "explain", "reason", "justifikasikan", "terangkan"]):
        return "reasoning_explanation"

    return "general"


def dedupe_table_rows(table_data):
    """Remove exact duplicate table rows without changing row order."""
    if not isinstance(table_data, dict):
        return table_data

    cleaned = {}

    for title, rows in table_data.items():
        if not isinstance(rows, list):
            cleaned[title] = rows
            continue

        seen = set()
        new_rows = []

        for row in rows:
            if isinstance(row, list):
                key = tuple(_variant_norm_text(cell) for cell in row)
            else:
                key = (_variant_norm_text(row),)

            if key in seen:
                continue

            seen.add(key)
            new_rows.append(row)

        cleaned[title] = new_rows

    return cleaned


def _clean_visible_text_value(value):
    """
    Visible question text should use readable Unicode set symbols.
    Keep marking_scheme.math as LaTeX; this function is only applied to question text/table data.
    """
    if isinstance(value, str):
        return (
            value
            .replace("\\\\cup", "∪")
            .replace("\\cup", "∪")
            .replace("\\\\cap", "∩")
            .replace("\\cap", "∩")
            .replace("\\\\neq", "≠")
            .replace("\\neq", "≠")
            .replace("\\\\ne", "≠")
            .replace("\\ne", "≠")
            .replace("\\\\leq", "≤")
            .replace("\\leq", "≤")
            .replace("\\\\geq", "≥")
            .replace("\\geq", "≥")
        )
    if isinstance(value, list):
        return [_clean_visible_text_value(item) for item in value]
    if isinstance(value, dict):
        return {key: _clean_visible_text_value(val) for key, val in value.items()}
    return value


def clean_variant_question_payload(variant):
    """
    Defensive cleanup for generated question JSON:
    - remove duplicate table rows
    - convert visible raw LaTeX set symbols to Unicode
    This does not alter marking_scheme math.
    """
    if not isinstance(variant, dict):
        return variant

    question = variant.get("question") or {}
    if not isinstance(question, dict):
        return variant

    for field in ["instructions_en", "instructions_ms", "table_data", "given_values"]:
        if field in question:
            question[field] = _clean_visible_text_value(question[field])

    if isinstance(question.get("table_data"), dict):
        question["table_data"] = dedupe_table_rows(question.get("table_data", {}))

    rows = question.get("questions") or []
    if isinstance(rows, list):
        for row in rows:
            if not isinstance(row, dict):
                continue
            for field in ["instructions_en", "instructions_ms", "table_data", "given_values"]:
                if field in row:
                    row[field] = _clean_visible_text_value(row[field])
            if isinstance(row.get("table_data"), dict):
                row["table_data"] = dedupe_table_rows(row.get("table_data", {}))

    stages = question.get("stages") or []
    if isinstance(stages, list):
        for stage in stages:
            if not isinstance(stage, dict):
                continue
            for field in ["instructions_en", "instructions_ms", "table_data", "given_values"]:
                if field in stage:
                    stage[field] = _clean_visible_text_value(stage[field])
            if isinstance(stage.get("table_data"), dict):
                stage["table_data"] = dedupe_table_rows(stage.get("table_data", {}))

    variant["question"] = question
    return variant


def validate_value_only_variant_content(variant, source_question, source_mode):
    """
    Generic validation that avoids writing 20+ chapter-specific rules.
    It catches the high-risk failures observed in review variants.
    """
    issues = []

    if not isinstance(variant, dict):
        return {"valid": False, "issues": ["Variant is not a dictionary."]}

    question = variant.get("question") or {}
    if not isinstance(question, dict):
        return {"valid": False, "issues": ["variant.question is not a dictionary."]}

    if source_mode != "stage":
        return {"valid": True, "issues": []}

    source_rows = source_question if isinstance(source_question, list) else [source_question]
    source_rows = [row for row in source_rows if isinstance(row, dict)]
    generated_rows = question.get("questions") or []
    generated_rows = [row for row in generated_rows if isinstance(row, dict)]

    if not generated_rows:
        if not _has_visible_payload(question):
            issues.append("Generated K2 question has no visible question content.")
        return {"valid": len(issues) == 0, "issues": issues}

    # 1. Reject fake/empty subparts.
    for row in generated_rows:
        label = _visible_label(row) or "(unlabelled)"
        if not _has_visible_payload(row):
            issues.append(f"Generated subpart {label} has no visible instruction/table/image content.")

    if len(source_rows) > 1 and len(generated_rows) > 1:
        source_instruction_keys = [_instruction_key(row) for row in source_rows]
        generated_instruction_keys = [_instruction_key(row) for row in generated_rows]

        source_has_different_instructions = len(set(k for k in source_instruction_keys if k)) > 1
        generated_all_same_instruction = (
            len(generated_instruction_keys) > 1
            and len(set(k for k in generated_instruction_keys if k)) == 1
            and bool(next((k for k in generated_instruction_keys if k), ""))
        )

        if source_has_different_instructions and generated_all_same_instruction:
            issues.append(
                "Value-only rule failed: source subparts have different instructions, but generated subparts all use the same instruction."
            )

        rows_with_visual_payload = [
            row for row in generated_rows
            if bool(row.get("table_data")) or bool(row.get("image_path")) or bool(row.get("image_urls"))
        ]
        rows_without_visual_payload = [
            row for row in generated_rows
            if not (bool(row.get("table_data")) or bool(row.get("image_path")) or bool(row.get("image_urls")))
        ]

        if generated_all_same_instruction and rows_with_visual_payload and rows_without_visual_payload:
            issues.append(
                "Fake subpart split detected: same instruction repeated across subparts, but only some subparts contain the table/diagram content."
            )

        # Preserve each subpart task family for high-risk mixed-task stages.
        for src, gen in zip(source_rows, generated_rows):
            src_task = _source_task_signature(src)
            gen_task = _source_task_signature(gen)
            label = _visible_label(src) or _visible_label(gen) or "(unlabelled)"

            if src_task not in ["general", "calculation_determine", "state_write", "reasoning_explanation"]:
                if gen_task != src_task:
                    issues.append(
                        f"Value-only rule failed for {label}: source task '{src_task}' became '{gen_task}'."
                    )

    visible_question_text = json.dumps(
        {
            "instructions_en": question.get("instructions_en", []),
            "instructions_ms": question.get("instructions_ms", []),
            "table_data": question.get("table_data", {}),
            "questions": [
                {
                    "instructions_en": row.get("instructions_en", []),
                    "instructions_ms": row.get("instructions_ms", []),
                    "table_data": row.get("table_data", {}),
                }
                for row in generated_rows
            ],
        },
        ensure_ascii=False,
    )

    if any(raw in visible_question_text for raw in ["\\\\cup", "\\cup", "\\\\cap", "\\cap", "\\\\neq", "\\neq"]):
        issues.append("Visible question text still contains raw LaTeX set commands such as \\cup, \\cap, or \\neq.")

    return {"valid": len(issues) == 0, "issues": issues}
def clean_k2_stage_parent_duplicate_instructions(variant, source_mode):
    """
    If the LLM repeats a subpart command inside the parent stem,
    remove it from the parent instead of rejecting the whole variant.

    Example:
    Parent:
      ["A cyclist travelled 20 km...", "Hence, calculate x."]
    Part (b):
      ["Hence, calculate x."]

    After cleaning:
    Parent:
      ["A cyclist travelled 20 km..."]
    Part (b):
      ["Hence, calculate x."]
    """
    if source_mode != "stage":
        return variant

    if not isinstance(variant, dict):
        return variant

    question = variant.get("question") or {}
    generated_rows = question.get("questions") or []

    if not isinstance(generated_rows, list) or not generated_rows:
        return variant

    def norm_line(value):
        return re.sub(r"\s+", " ", str(value or "")).strip().lower()

    for field in ["instructions_en", "instructions_ms"]:
        parent_lines = question.get(field) or []

        if not isinstance(parent_lines, list):
            continue

        sub_keys = set()

        for row in generated_rows:
            if not isinstance(row, dict):
                continue

            sub_lines = row.get(field) or []

            if isinstance(sub_lines, list):
                for line in sub_lines:
                    key = norm_line(line)
                    if key:
                        sub_keys.add(key)

        cleaned_parent_lines = [
            line for line in parent_lines
            if norm_line(line) not in sub_keys
        ]

        question[field] = cleaned_parent_lines

    variant["question"] = question
    return variant

def validate_k2_stage_variant_structure(variant, source_question, source_mode):
    """
    Reject broken K2 stage variants before they are saved.
    This is needed because prompt rules alone cannot guarantee that the LLM
    will generate the same number of subparts as the source stage.
    """
    if source_mode != "stage":
        return {"valid": True, "issues": []}

    issues = []

    if not isinstance(variant, dict):
        return {
            "valid": False,
            "issues": ["Variant is not a dictionary."]
        }

    question = variant.get("question") or {}
    generated_rows = question.get("questions") or []

    source_rows = source_question if isinstance(source_question, list) else [source_question]
    source_rows = [row for row in source_rows if isinstance(row, dict)]

    source_labels = [_variant_label_tuple(row) for row in source_rows]
    generated_labels = [
        _variant_label_tuple(row)
        for row in generated_rows
        if isinstance(row, dict)
    ]

    # 1. If source stage has multiple extracted rows, generated variant must match.
    if len(source_rows) > 1:
        if not isinstance(generated_rows, list) or len(generated_rows) != len(source_rows):
            issues.append(
                f"Source stage has {len(source_rows)} rows, but generated variant has {len(generated_rows)} rows."
            )

        if generated_labels != source_labels:
            issues.append(
                f"Generated labels {generated_labels} do not match source labels {source_labels}."
            )

    # 2. Parent stem should not duplicate subpart instructions.
    parent_en = question.get("instructions_en") or []
    sub_en = []

    for row in generated_rows:
        if isinstance(row, dict) and isinstance(row.get("instructions_en"), list):
            sub_en.extend(row.get("instructions_en"))

    parent_keys = {_variant_norm_text(x) for x in parent_en if _variant_norm_text(x)}
    sub_keys = {_variant_norm_text(x) for x in sub_en if _variant_norm_text(x)}

    duplicated = parent_keys.intersection(sub_keys)

    if duplicated:
        issues.append(
            f"Parent instructions duplicate subpart instructions: {list(duplicated)}"
        )

    # 3. Reject old question-number references such as "graph in 14(b)".
    text_blob = json.dumps(question, ensure_ascii=False).lower()

    old_number_ref = re.search(
        r"(graph|graf)\s+(in|di)\s+\d+\s*\([a-z]\)",
        text_blob
    )

    if old_number_ref:
        issues.append(
            "Generated question refers to an old question number such as 'graph in 14(b)'. Use 'the graph drawn in part (b)' instead."
        )

    # 4. Graph-dependent variants must include the whole stage, not one subpart only.
    depends_on_graph = (
        "based on the graph" in text_blob
        or "using the graph" in text_blob
        or "from the graph" in text_blob
        or "berdasarkan graf" in text_blob
        or "menggunakan graf" in text_blob
    )

    if depends_on_graph and len(source_rows) > 1 and len(generated_rows) < len(source_rows):
        issues.append(
            "Generated variant refers to a graph but did not include all source stage subparts."
        )

    return {
        "valid": len(issues) == 0,
        "issues": issues
    }


def build_value_only_safety_contract(source_question, source_mode, is_k1_mcq_source=False):
    """
    Prompt contract that makes review generation safer by default.
    This avoids needing detailed rules for every chapter.
    """
    if is_k1_mcq_source:
        return ""

    source_rows = source_question if isinstance(source_question, list) else [source_question]
    source_rows = [row for row in source_rows if isinstance(row, dict)]

    if not source_rows:
        return ""

    subpart_summary = []
    for row in source_rows:
        label = _visible_label(row) or "(no label)"
        task = _source_task_signature(row)
        instruction = " ".join(str(x or "") for x in (row.get("instructions_en") or []))
        instruction = re.sub(r"\s+", " ", instruction).strip()
        if len(instruction) > 140:
            instruction = instruction[:140] + "..."
        subpart_summary.append({
            "label": label,
            "task_type": task,
            "instruction_en": instruction,
            "has_table": bool(row.get("table_data")),
            "has_image_or_diagram": bool(row.get("image_path")) or bool(row.get("has_diagram")),
        })

    return f"""
SAFE DEFAULT REVIEW VARIANT RULE: VALUE-ONLY MUTATION
- Do NOT redesign the question unless explicitly required.
- Preserve the original structure, number of parts, subpart labels, answer type, and solving method.
- Preserve the task type of EACH subpart. Do not copy one subpart's instruction into another subpart.
- Prefer changing only safe values: numbers, names, simple statement values, set labels, and table cell values when they are editable text.
- If a diagram/image is present, keep the image_path and do not invent new visible objects, labels, coordinates, graph values, regions, shapes, or tables.
- If table_data is used as the actual question content, keep the same row count and row meaning. Do not duplicate rows.
- For mixed-task stages, each subpart must remain the same skill as its source subpart.
  Example: if source (a) asks negation/truth value and source (b) asks valid/sound argument, generated (a) must still ask negation/truth value and generated (b) must still ask valid/sound argument.
- Visible question text should use readable Unicode symbols such as ∪, ∩, ≠ instead of raw LaTeX commands like \\cup, \\cap, \\neq.

SOURCE SUBPART TASK MAP:
{json.dumps(subpart_summary, ensure_ascii=False, indent=2)}
"""

def build_k2_stage_structure_contract(source_question, source_mode):
    if source_mode != "stage":
        return ""

    source_rows = source_question if isinstance(source_question, list) else [source_question]
    source_rows = [row for row in source_rows if isinstance(row, dict)]

    if not source_rows:
        return ""

    labels = []

    for row in source_rows:
        part = str(row.get("part") or "").strip()
        subpart = str(row.get("subpart") or "").strip()
        sub_subpart = str(row.get("sub_subpart") or "").strip()

        label = ""
        if part:
            label += f"({part})"
        if subpart:
            label += f"({subpart})"
        if sub_subpart:
            label += f"({sub_subpart})"

        labels.append(label or "(no label)")

    return f"""
SOURCE STRUCTURE CONTRACT FOR K2 STAGE:
- The source stage has exactly {len(source_rows)} extracted question rows.
- The generated variant MUST have exactly {len(source_rows)} objects inside question.questions.
- The generated question.questions labels MUST be exactly this order:
  {labels}
- Do not generate only one selected subpart.
- Do not omit earlier subparts.
- Do not combine all subparts into one instruction.
- If you cannot create a valid variant with this exact structure, still output all required question.questions with matching labels.
"""
def clean_latex_math_string(value):
    """
    Clean generated LaTeX inside marking_scheme.steps[n].math.
    The math field should contain raw LaTeX only, not $...$ wrappers.
    """
    if value is None:
        return value

    text = str(value).strip()

    # Fix common slash typo
    text = text.replace("/frac", "\\frac")

    # Remove $ immediately after \begin{aligned} etc.
    text = re.sub(
        r"(\\begin\{(?:aligned|align|array|matrix|pmatrix|bmatrix|cases)\})\s*\$",
        r"\1 ",
        text
    )

    # Remove $ immediately before \end{aligned} etc.
    text = re.sub(
        r"\$\s*(\\end\{(?:aligned|align|array|matrix|pmatrix|bmatrix|cases)\})",
        r" \1",
        text
    )

    # If the whole math field is wrapped in $...$, remove the wrapper
    if text.startswith("$") and text.endswith("$"):
        text = text[1:-1].strip()

    # If the math field contains a LaTeX environment, remove any remaining $
    if re.search(r"\\begin\{(?:aligned|align|array|matrix|pmatrix|bmatrix|cases)\}", text):
        text = text.replace("$", "")

    return text.strip()


def clean_variant_latex_math_fields(variant):
    """
    Walk through generated marking scheme and clean all step.math fields.
    """
    if not isinstance(variant, dict):
        return variant

    def clean_steps(steps):
        if not isinstance(steps, list):
            return

        for step in steps:
            if not isinstance(step, dict):
                continue

            if "math" in step:
                step["math"] = clean_latex_math_string(step.get("math"))

    marking_scheme = variant.get("marking_scheme") or {}

    # Single-stage marking scheme
    clean_steps(marking_scheme.get("steps"))

    # Group/stage marking scheme
    stages = marking_scheme.get("stages") or []
    if isinstance(stages, list):
        for stage in stages:
            if isinstance(stage, dict):
                clean_steps(stage.get("steps"))

    variant["marking_scheme"] = marking_scheme
    return variant
def safe_int(value, default=0):
    try:
        return int(value)
    except Exception:
        match = re.search(r"\d+", str(value or ""))
        return int(match.group(0)) if match else default


def build_label_from_row(row):
    label = ""

    for key in ["part", "subpart", "sub_subpart"]:
        value = str(row.get(key) or "").strip()
        if value:
            label += f"({value})"

    return label


def ensure_sequence_matches_payload(node):
    sequence = node.get("sequence")

    if not isinstance(sequence, list):
        sequence = ["text_0"]

    has_image = bool(str(node.get("image_path") or "").strip()) or bool(node.get("image_urls"))
    has_table = bool(node.get("table_data")) and node.get("table_data") not in [{}, [], "{}", "[]"]

    if has_image and not any(str(item).startswith("image_") for item in sequence):
        if "text_0" in sequence:
            sequence.insert(sequence.index("text_0") + 1, "image_0")
        else:
            sequence.insert(0, "image_0")

    if has_table and not any(str(item).startswith("table_") for item in sequence):
        sequence.append("table_0")

    if not has_image:
        sequence = [item for item in sequence if not str(item).startswith("image_")]

    if not has_table:
        sequence = [item for item in sequence if not str(item).startswith("table_")]

    node["sequence"] = sequence
    return node

def unwrap_marking_scheme(raw_ms):
    raw_ms = parse_db_json(raw_ms, {})

    if isinstance(raw_ms, dict):
        for key in [
            "marking_scheme",
            "scheme",
            "solution",
            "official_solution",
            "answer_scheme",
            "raw_json",
        ]:
            nested = raw_ms.get(key)
            if isinstance(nested, (dict, list)):
                return nested

    return raw_ms


def extract_steps_from_marking_scheme(raw_ms):
    raw_ms = unwrap_marking_scheme(raw_ms)

    if isinstance(raw_ms, list):
        return raw_ms

    if not isinstance(raw_ms, dict):
        return []

    steps = (
        raw_ms.get("steps")
        or raw_ms.get("rubric")
        or raw_ms.get("marking_steps")
        or raw_ms.get("solution_steps")
        or raw_ms.get("answer_steps")
        or raw_ms.get("scheme_steps")
        or []
    )

    return steps if isinstance(steps, list) else []


def extract_final_answers_from_marking_scheme(raw_ms, label=""):
    raw_ms = unwrap_marking_scheme(raw_ms)

    if not isinstance(raw_ms, dict):
        return {}

    final_answers = (
        raw_ms.get("final_answers")
        or raw_ms.get("final_answer_by_part")
        or raw_ms.get("answers_by_part")
        or {}
    )

    if isinstance(final_answers, dict) and final_answers:
        return final_answers

    final_answer = (
        raw_ms.get("final_answer")
        or raw_ms.get("answer")
        or raw_ms.get("answer_value")
        or raw_ms.get("final")
        or ""
    )

    if label and final_answer != "":
        return {label: final_answer}

    return {}
def normalize_marking_step(step, label="", index=1, default_marks=1):
    if not isinstance(step, dict):
        return None

    required_math = (
        step.get("required_keywords_or_math")
        or step.get("keywords")
        or step.get("expected_math")
        or ""
    )

    if isinstance(required_math, list):
        required_math = ", ".join(str(x) for x in required_math if str(x).strip())

    text = (
        step.get("text")
        or step.get("description")
        or step.get("criteria")
        or step.get("explanation")
        or step.get("working")
        or step.get("method")
        or step.get("expected")
        or step.get("expected_answer")
        or ""
    )

    math = (
        step.get("math")
        or step.get("calculation")
        or step.get("equation")
        or step.get("latex")
        or step.get("working_math")
        or required_math
        or ""
    )

    final_answer = (
        step.get("final_answer")
        or step.get("answer")
        or step.get("answer_value")
        or step.get("final")
        or ""
    )

    marks = safe_int(
        step.get("marks")
        or step.get("max_marks")
        or step.get("mark")
        or step.get("score")
        or default_marks,
        default_marks
    )

    if not text and not math and not final_answer:
        return None

    return {
        "display_subpart_label": step.get("display_subpart_label") or label,
        "step": step.get("step") or step.get("label") or step.get("title") or f"Step {index}",
        "text": text,
        "math": math,
        "marks": marks,
        "final_answer": final_answer,
    }
def build_original_group_retry_variant(rows, group_id, language):
    """
    Bypasses the AI and repackages the original K2 group question 
    into the 'variant' JSON format so the student can retry it exactly as is.
    """
    stages_dict = {}
    ms_dict = {}
    
    for row in rows:
        s_idx = row.get("stage_index") or 1
        
        # Helper to safely parse intro strings into arrays
        def parse_intro(val):
            parsed = parse_db_json(val, [])
            if isinstance(parsed, list): return parsed
            if isinstance(parsed, str) and parsed.strip(): return [parsed]
            return []
            
        # 1. Build the Question Stage
        if s_idx not in stages_dict:
            # Use introductory instructions for the top of the page if available
            # (Requires fetch_group_source_for_variant in app.py to select these columns)
            intro_en = parse_intro(row.get("introductory_instructions_en") if "introductory_instructions_en" in row else None)
            intro_ms = parse_intro(row.get("introductory_instructions_ms") if "introductory_instructions_ms" in row else None)
            
            stages_dict[s_idx] = {
                "stage_index": s_idx,
                "original_exercise_stage_id": row.get("exercise_stage_id"),
                "exercise_stage_id": row.get("exercise_stage_id"),
                "group_id": row.get("group_id"),
                "question_no": row.get("question_no"),

                "instructions_en": intro_en if intro_en else (parse_db_json(row.get("instructions_en"), [])),
                "instructions_ms": intro_ms if intro_ms else (parse_db_json(row.get("instructions_ms"), [])),
                "sequence": parse_db_json(row.get("sequence"), []),
                "table_data": parse_db_json(row.get("table_data"), {}),
                "given_values": parse_db_json(row.get("given_values"), {}),
                "diagram_type": row.get("diagram_type") or "",
                "image_path": row.get("image_path") or "",
                "image_urls": [row.get("image_path")] if row.get("image_path") else [],
                "has_diagram": row.get("has_diagram") or 0,
                "display_marks": row.get("display_marks") or 1,
                "questions": []
            }
        
        # 2. Append the specific subquestion WITH its instructions and marks
        stages_dict[s_idx]["questions"].append({
            "id": row.get("question_id"),
            "question_id": row.get("question_id"),
            "original_question_id": row.get("question_id"),

            "exercise_stage_id": row.get("exercise_stage_id"),
            "original_exercise_stage_id": row.get("exercise_stage_id"),

            "group_id": row.get("group_id"),
            "stage_index": row.get("stage_index"),
            "question_no": row.get("question_no"),

            "part": row.get("part") or "",
            "subpart": row.get("subpart") or "",
            "sub_subpart": row.get("sub_subpart") or "",

            "image_path": row.get("image_path") or "",
            "image_urls": [row.get("image_path")] if row.get("image_path") else [],
            "has_diagram": row.get("has_diagram") or 0,

            "instructions_en": parse_db_json(row.get("instructions_en"), []),
            "instructions_ms": parse_db_json(row.get("instructions_ms"), []),
            "sequence": parse_db_json(row.get("sequence"), []),
            "table_data": parse_db_json(row.get("table_data"), {}),
            "given_values": parse_db_json(row.get("given_values"), {}),

            "display_marks": row.get("display_marks") or 1,
        })
        
        # 3. Build the Marking Scheme Stage
        if s_idx not in ms_dict:
            ms_dict[s_idx] = {
                "stage_index": s_idx,
                "steps": [],
                "final_answers": {}
            }
        
        raw_ms = row.get("marking_scheme_json")

        r_part = row.get("part") or ""
        r_subpart = row.get("subpart") or ""
        r_sub_subpart = row.get("sub_subpart") or ""

        parts = [str(x).strip() for x in [r_part, r_subpart, r_sub_subpart] if x]
        label_str = "".join([f"({p})" for p in parts])

        row_steps = extract_steps_from_marking_scheme(raw_ms)
        final_answers_map = extract_final_answers_from_marking_scheme(raw_ms, label_str)

        for k, v in final_answers_map.items():
            ms_dict[s_idx]["final_answers"][k] = v

        cleaned_steps = []

        for step_index, step in enumerate(row_steps, start=1):
            normalized_step = normalize_marking_step(
                step=step,
                label=label_str,
                index=step_index,
                default_marks=safe_int(row.get("display_marks"), 1)
            )

            if normalized_step:
                normalized_step["part"] = r_part
                normalized_step["subpart"] = r_subpart
                normalized_step["sub_subpart"] = r_sub_subpart
                normalized_step["label"] = label_str
                cleaned_steps.append(normalized_step)

        # Only create a fallback if there is a final answer.
        # Do NOT create fake blank steps.
        if not cleaned_steps and label_str and ms_dict[s_idx]["final_answers"].get(label_str):
            cleaned_steps.append({
                "display_subpart_label": label_str,
                "part": r_part,
                "subpart": r_subpart,
                "sub_subpart": r_sub_subpart,
                "label": label_str,
                "step": "Final answer",
                "text": "",
                "math": "",
                "marks": safe_int(row.get("display_marks"), 1),
                "final_answer": ms_dict[s_idx]["final_answers"].get(label_str)
            })

        ms_dict[s_idx]["steps"].extend(cleaned_steps)
            
    stages_list = [stages_dict[k] for k in sorted(stages_dict.keys())]
    ms_stages_list = [ms_dict[k] for k in sorted(ms_dict.keys())]

    return {
        "variant_type": "number_variant", # Fixed the DB Truncate error!
        "language": language,
        "question": {
            "stages": stages_list
        },
        "marking_scheme": {
            "stages": ms_stages_list
        }
    }
def extract_assignment_variables(text):
    """
    Extract variables from option text like:
    h = -5, k = -25
    x = 3
    """
    text = str(text or "")
    return re.findall(r"\b([a-zA-Z])\s*=", text)


def get_k1_option_texts(question):
    options = question.get("options") or []

    texts = []

    if isinstance(options, list):
        for opt in options:
            if not isinstance(opt, dict):
                continue

            text = (
                opt.get("text_en")
                or opt.get("text")
                or opt.get("value")
                or opt.get("answer")
                or ""
            )

            if text:
                texts.append(str(text))

    return texts


def get_question_text_blob(question):
    lines = []

    for field in ["instructions_en", "instructions_ms"]:
        value = question.get(field) or []

        if isinstance(value, list):
            lines.extend(str(x or "") for x in value)
        elif value:
            lines.append(str(value))

    return " ".join(lines)


def detect_single_requested_variable(question_text):
    """
    Detect question target like:
    Determine the value of k.
    Find the value of x.
    Cari nilai k.
    Tentukan nilai h.
    """
    text = str(question_text or "").lower()

    patterns = [
        r"value\s+of\s+([a-z])\b",
        r"nilai\s+([a-z])\b",
        r"find\s+([a-z])\b",
        r"determine\s+([a-z])\b",
        r"cari\s+([a-z])\b",
        r"tentukan\s+([a-z])\b",
    ]

    found = []

    for pattern in patterns:
        for match in re.findall(pattern, text):
            found.append(match.lower())

    unique = sorted(set(found))

    return unique[0] if len(unique) == 1 else ""


def replace_single_variable_question_with_multi_variable(question, variables):
    """
    If the options answer h and k, but the question asks only k,
    change the question to ask h and k.
    """
    if not variables or len(variables) <= 1:
        return question

    variables = [str(v).strip() for v in variables if str(v).strip()]
    variables_text_en = " and ".join(variables)
    variables_text_ms = " dan ".join(variables)

    def fix_line_en(line):
        line = str(line or "")

        line = re.sub(
            r"\bDetermine\s+the\s+value\s+of\s+[a-z]\b\.?",
            f"Determine the values of {variables_text_en}.",
            line,
            flags=re.IGNORECASE
        )

        line = re.sub(
            r"\bFind\s+the\s+value\s+of\s+[a-z]\b\.?",
            f"Find the values of {variables_text_en}.",
            line,
            flags=re.IGNORECASE
        )

        return line

    def fix_line_ms(line):
        line = str(line or "")

        line = re.sub(
            r"\bTentukan\s+nilai\s+[a-z]\b\.?",
            f"Tentukan nilai {variables_text_ms}.",
            line,
            flags=re.IGNORECASE
        )

        line = re.sub(
            r"\bCari\s+nilai\s+[a-z]\b\.?",
            f"Cari nilai {variables_text_ms}.",
            line,
            flags=re.IGNORECASE
        )

        return line

    if isinstance(question.get("instructions_en"), list):
        question["instructions_en"] = [fix_line_en(line) for line in question["instructions_en"]]

    if isinstance(question.get("instructions_ms"), list):
        question["instructions_ms"] = [fix_line_ms(line) for line in question["instructions_ms"]]

    return question


def align_k1_question_options_and_explanation(variant):
    """
    Fix cases where the K1 question asks for one variable,
    but the MCQ options answer multiple variables.

    Example:
    Question: Determine the value of k.
    Options: h = -5, k = -25

    Fixed:
    Question: Determine the values of h and k.
    """
    if not isinstance(variant, dict):
        return variant

    question = variant.setdefault("question", {})
    marking_scheme = variant.setdefault("marking_scheme", {})

    option_texts = get_k1_option_texts(question)
    question_text = get_question_text_blob(question)

    asked_variable = detect_single_requested_variable(question_text)

    option_variables = []

    for text in option_texts:
        vars_in_option = extract_assignment_variables(text)
        if len(vars_in_option) >= 2:
            option_variables.extend(vars_in_option)

    option_variables = sorted(set(v.lower() for v in option_variables))

    # Main fix: options answer multiple variables but question asks only one.
    if asked_variable and len(option_variables) >= 2:
        question = replace_single_variable_question_with_multi_variable(
            question,
            option_variables
        )

        final_answer = str(marking_scheme.get("final_answer") or "").strip().upper()
        correct_option_text = ""

        for opt in question.get("options") or []:
            if not isinstance(opt, dict):
                continue

            if str(opt.get("label") or "").strip().upper() == final_answer:
                correct_option_text = (
                    opt.get("text_en")
                    or opt.get("text")
                    or opt.get("value")
                    or ""
                )
                break

        if correct_option_text:
            marking_scheme["explanation_en"] = (
                f"The question asks for the values of {' and '.join(option_variables)}. "
                f"The correct option is {final_answer}, which gives {correct_option_text}."
            )

            marking_scheme["explanation_bm"] = (
                f"Soalan meminta nilai {' dan '.join(option_variables)}. "
                f"Pilihan yang betul ialah {final_answer}, iaitu {correct_option_text}."
            )

    variant["question"] = question
    variant["marking_scheme"] = marking_scheme

    return variant

def normalize_k1_answer_value(value):
    text = str(value or "").strip().lower()

    # Remove common wrappers / formatting differences
    text = text.replace("$", "")
    text = text.replace("\\left", "").replace("\\right", "")
    text = text.replace("\\,", "")
    text = text.replace(",", "")
    text = text.replace("rm", "")
    text = text.replace(" ", "")

    # Normalize base notation: 110_{2} -> 110_2
    text = re.sub(r"_\{(\d+)\}", r"_\1", text)

    # Normalize common latex operators
    text = text.replace("\\times", "×")
    text = text.replace("\\div", "÷")
    text = text.replace("\\neq", "≠").replace("\\ne", "≠")

    return text


def get_k1_option_map_from_variant(variant):
    question = variant.get("question") or {}
    raw_options = question.get("options") or []

    if isinstance(raw_options, dict):
        option_list = []
        for label, value in raw_options.items():
            if isinstance(value, dict):
                option_list.append({"label": label, **value})
            else:
                option_list.append({
                    "label": label,
                    "text_en": str(value or ""),
                    "text_ms": str(value or ""),
                    "image_path": ""
                })
    elif isinstance(raw_options, list):
        option_list = raw_options
    else:
        option_list = []

    option_map = {}

    for option in option_list:
        if not isinstance(option, dict):
            continue

        label = str(option.get("label") or "").strip().upper().replace(".", "")

        if label not in ["A", "B", "C", "D"]:
            continue

        text_en = (
            option.get("text_en")
            or option.get("text")
            or option.get("value")
            or option.get("answer")
            or ""
        )

        text_ms = (
            option.get("text_ms")
            or option.get("text_bm")
            or option.get("text_malay")
            or text_en
            or ""
        )

        option_map[label] = {
            "label": label,
            "text_en": str(text_en or "").strip(),
            "text_ms": str(text_ms or text_en or "").strip(),
            "image_path": str(option.get("image_path") or option.get("image") or "")
        }

    return option_map


def validate_k1_mcq_variant_basic(variant):
    issues = []

    if not isinstance(variant, dict):
        return {"valid": False, "issues": ["Variant is not a dictionary."]}

    question = variant.get("question") or {}
    marking_scheme = variant.get("marking_scheme") or {}

    option_map = get_k1_option_map_from_variant(variant)

    if sorted(option_map.keys()) != ["A", "B", "C", "D"]:
        issues.append("K1 variant must have exactly options A, B, C and D.")

    for label in ["A", "B", "C", "D"]:
        option = option_map.get(label) or {}
        has_text = bool(option.get("text_en") or option.get("text_ms"))
        has_image = bool(option.get("image_path"))

        if not has_text and not has_image:
            issues.append(f"Option {label} is empty.")

    final_answer = str(marking_scheme.get("final_answer") or "").strip().upper()

    if final_answer not in ["A", "B", "C", "D"]:
        issues.append("marking_scheme.final_answer must be A, B, C, or D.")

    correct_option = option_map.get(final_answer) or {}
    correct_text = correct_option.get("text_en") or correct_option.get("text_ms") or ""

    if final_answer in ["A", "B", "C", "D"] and not correct_text and not correct_option.get("image_path"):
        issues.append(f"Correct option {final_answer} has no visible answer text/image.")

    # Check duplicated text options
    normalized_texts = []
    for label in ["A", "B", "C", "D"]:
        option = option_map.get(label) or {}
        text = option.get("text_en") or option.get("text_ms") or ""
        norm = normalize_k1_answer_value(text)

        if norm:
            normalized_texts.append(norm)

    if len(normalized_texts) != len(set(normalized_texts)):
        issues.append("K1 options contain duplicate answer values.")

    # Critical scratchpad check
    scratchpad = question.get("calculation_scratchpad") or {}
    true_value = str(scratchpad.get("step_3_true_final_answer") or "").strip()

    if not true_value:
        issues.append("Missing calculation_scratchpad.step_3_true_final_answer.")
    else:
        true_norm = normalize_k1_answer_value(true_value)

        matching_labels = []

        for label, option in option_map.items():
            option_text = option.get("text_en") or option.get("text_ms") or ""
            option_norm = normalize_k1_answer_value(option_text)

            if option_norm == true_norm:
                matching_labels.append(label)

        if not matching_labels:
            issues.append(
                f"The true calculated answer '{true_value}' does not appear in any option."
            )

        elif final_answer not in matching_labels:
            issues.append(
                f"final_answer is {final_answer}, but true answer matches option(s): {matching_labels}."
            )

        elif len(matching_labels) > 1:
            issues.append(
                f"The true answer appears in multiple options: {matching_labels}."
            )

    return {
        "valid": len(issues) == 0,
        "issues": issues
    }

def generate_review_variant(
    source_mode="stage",
    exercise_stage_id=None,
    group_id=None,
    question_id=None,
    parent_variant=None,
    language="english",
    grading_result=None
):
    language = normalize_response_language(language)
    language_rules = get_response_language_rules(language)
    source_mode = str(source_mode or "stage").strip().lower()

    rows = []
    source_question = []
    source_marking_scheme = []
    source_label = ""
    source_type_instruction = ""
    # =========================
    # Local helper: normalize K1 options into A-D list
    # =========================
    def normalize_k1_options_in_variant(variant):
        question = variant.setdefault("question", {})
        raw_options = question.get("options", [])

        if isinstance(raw_options, dict):
            option_list = []
            for label, value in raw_options.items():
                if isinstance(value, dict):
                    option_list.append({"label": label, **value})
                else:
                    option_list.append({
                        "label": label,
                        "text_en": str(value or ""),
                        "text_ms": str(value or ""),
                        "image_path": ""
                    })
        elif isinstance(raw_options, list):
            option_list = raw_options
        else:
            option_list = []

        normalized = []

        for label in ["A", "B", "C", "D"]:
            found = None

            for option in option_list:
                if not isinstance(option, dict):
                    continue

                option_label = str(option.get("label", "")).strip().upper().replace(".", "")

                if option_label == label:
                    found = option
                    break

            found = found or {}

            text_en = (
                found.get("text_en")
                or found.get("text")
                or found.get("value")
                or found.get("answer")
                or ""
            )

            text_ms = (
                found.get("text_ms")
                or found.get("text_bm")
                or found.get("text_malay")
                or text_en
                or ""
            )

            normalized.append({
                "label": label,
                "text_en": str(text_en or ""),
                "text_ms": str(text_ms or text_en or ""),
                "image_path": str(found.get("image_path") or found.get("image") or "")
            })

        question["options"] = normalized
        variant["question"] = question
        return variant

    # =========================
    # Local helper: preserve locked source visual data for K1 diagram/table
    # =========================
    def preserve_k1_locked_visuals(variant, source_data):
        question = variant.setdefault("question", {})

        source_items = source_data if isinstance(source_data, list) else [source_data]
        source_item = next((item for item in source_items if isinstance(item, dict)), {})

        original_image = source_item.get("image_path") or ""
        original_table = source_item.get("table_data") or {}
        original_sequence = source_item.get("sequence") or []
        original_has_diagram = source_item.get("has_diagram")
        original_diagram_type = source_item.get("diagram_type") or ""

        if original_image:
            question["image_path"] = original_image
            question["has_diagram"] = 1

        if original_table:
            question["table_data"] = original_table

        if original_sequence:
            question["sequence"] = original_sequence
        else:
            sequence = ["text_0"]

            if original_image:
                sequence.append("image_0")

            if original_table:
                sequence.append("table_0")

            sequence.append("text_1")
            question["sequence"] = sequence

        if original_has_diagram is not None:
            question["has_diagram"] = int(original_has_diagram or 0)

        question["diagram_type"] = original_diagram_type
        variant["question"] = question

        return variant

    # =========================
    # 1. Decide source
    # =========================
    if source_mode == "variant":
        if not parent_variant:
            return {
                "variant_type": "error",
                "message": "Missing parent_variant for variant source mode."
            }

        source_question = parent_variant.get("question", {})
        source_marking_scheme = parent_variant.get("marking_scheme", {})
        source_label = f"variant:{parent_variant.get('variant_id')}"

        source_type_instruction = """
The source is a previously generated review variant.
Generate a NEW variant based on this parent variant.
Do not copy the exact same question, same numbers, or same final answer.

If the parent variant is a K1 MCQ variant, generate another K1 MCQ variant.
"""

    elif source_mode == "question":
        rows = fetch_question_source_for_variant(question_id)

        if not rows:
            return {
                "variant_type": "error",
                "message": "No source question found."
            }

        source_question, source_marking_scheme = build_source_from_rows(rows)
        source_label = f"question:{question_id}"

        source_type_instruction = """
The source is one individual K1 MCQ question.
Generate ONE similar K1 multiple-choice question only.
Do not generate stages.
Do not generate a subjective answer format.
The new question must have exactly 4 options: A, B, C, and D.
The marking_scheme.final_answer must be the correct option letter only, such as "A", "B", "C", or "D".

K1 DIAGRAM/TABLE LABEL LOCK RULE:
- If the source diagram/table contains a variable label such as M, x, y, P, Q, etc., the generated question MUST ask about the same existing label.
- Do NOT invent a new label that is not visible in the source diagram/table.
- For example, if the source table/diagram contains M, the generated question must ask for M, not N.
- The generated instructions, table_data, image_path, and marking_scheme must all refer to the same label.
"""

    else:
        rows = fetch_stage_source_for_variant(exercise_stage_id)

        if not rows:
            return {
                "variant_type": "error",
                "message": "No source stage question found."
            }

        source_question, source_marking_scheme = build_source_from_rows(rows)
        source_label = f"stage:{exercise_stage_id}"

        source_type_instruction = """
The source is an original DB stage/question.
Generate a review variant for this stage/question.
"""
    if source_mode != "variant":
        if not is_form4_only_source(source_question):
            return {
                "variant_type": "skipped",
                "message": "Review variant generation is enabled for Form 4 only."
            }

    source_rows_for_image = (
        source_question if isinstance(source_question, list) else [source_question]
    )
    source_rows_for_image = (
        source_question if isinstance(source_question, list) else [source_question]
    )

    source_rows_for_image = [
        row for row in source_rows_for_image
        if isinstance(row, dict)
    ]

    # =========================
    # 2. Detect diagram/image/table
    # =========================
    if source_mode == "variant":
        if isinstance(source_question, dict):
            has_diagram = (
                bool(source_question.get("has_diagram"))
                or bool(source_question.get("image_path"))
                or bool(source_question.get("table_data"))
            )
        else:
            has_diagram = any(
                bool(q.get("has_diagram"))
                or bool(q.get("image_path"))
                or bool(q.get("table_data"))
                for q in source_question
                if isinstance(q, dict)
            )
    else:
        has_diagram = any(
            int(row.get("has_diagram") or 0) == 1
            or bool(row.get("image_path"))
            or bool(row.get("table_data"))
            for row in rows
        )

    parent_is_k1_mcq = (
        source_mode == "variant"
        and isinstance(parent_variant, dict)
        and str(parent_variant.get("variant_type") or "").strip() == "k1_mcq_variant"
    )

    is_k1_mcq_source = source_mode == "question" or parent_is_k1_mcq

    # =========================
    # 3. Decide variant type + mode instruction
    # =========================
    if is_k1_mcq_source:
        variant_type = "k1_mcq_variant"

        k1_mutation_policy = """
    K1 REVIEW VARIANT GOAL:
    Generate a question that is related to the original question and tests the same skill,
    but it must not be a direct copy of the original question.

    Choose exactly ONE mutation_type:

    1. text_number_switch
    - Use when the source has no diagram/table/image.
    - Change suitable numerical values and recalculate the answer.
    - Example: change income, tax rate, probability count, matrix values, distance, price, ratio, or base number.

    2. diagram_text_number_switch
    - Use when the source has a diagram/table/image, but the written question contains editable numbers or conditions that are NOT printed inside the visual.
    - Keep the visual unchanged.
    - Change only the written text condition.
    - Example: same price diagram, but change budget amount.
    - Example: same speed-time graph, but change the given distance condition if that distance is only in text.
    - Do NOT change any number printed inside the image.

    3. diagram_target_switch
    - Use when the source has a diagram/table/chart/graph with multiple readable values.
    - Keep the visual unchanged.
    - Ask for a different valid target from the same visual.
    - Example: if original asks mean, ask range, median, mode, or total frequency.
    - Example: if original asks gradient, ask y-intercept, equation, or parallel gradient.
    - Example: if original asks total distance from speed-time graph, ask distance in one interval or average speed.
    - Example: if original asks one set expression in a Venn diagram, ask a related set expression.

    4. representation_switch
    - Use when the same answer can be represented in another form.
    - Example: base number to decimal, decimal to base, equivalent expression, comparison statement, interval statement.
    - Example: if original asks value of M, ask which comparison involving M is true.

    5. reverse_question
    - Use when the formula can be reversed.
    - Example: original gives premium and asks face value; variant gives face value and asks premium.
    - Example: original gives area and asks length; variant gives length and asks area.
    - Example: original gives amount after interest and asks principal; variant gives principal and asks amount.

    6. complement_switch
    - Use for probability, sets, and Venn diagrams.
    - Example: original asks event A; variant asks not A.
    - Example: original asks at least one blue; variant asks no blue.
    - Example: original asks P ∩ Q; variant asks P ∩ Q' or P ∪ Q.

    7. condition_switch
    - Use for inequalities, finance decisions, cash flow, savings, and word problems.
    - Change the condition while keeping the same concept.
    - Example: enough budget becomes minimum saving needed.
    - Example: at least becomes less than, if mathematically valid.

    8. property_switch
    - Use for conceptual MCQs.
    - Example: original asks which is true; variant asks which is false.
    - Example: original asks which is a function; variant asks which is not a function.
    - Example: original asks isometric transformation; variant asks non-isometric transformation.

    9. method_switch
    - Use when the diagram is too locked and no new numerical target is safe.
    - Ask which formula, theorem, relationship, or reason is needed.
    - This is allowed only if it still tests the same skill.

    10. statement_switch
    - Use when the source diagram/table cannot be changed.
    - Ask which statement is true or false based on the same visual.

    11. misconception_switch
    - Use when the student likely made a common mistake.
    - Generate options based on common wrong methods, such as:
    wrong base conversion,
    wrong complement probability,
    wrong area scale factor,
    wrong gradient formula,
    wrong order of combined transformations,
    wrong rounding,
    wrong tax/insurance formula.

    DIAGRAM/TABLE/IMAGE LOCK:
    - If image_path exists, keep the same image_path.
    - If table_data exists, keep the same table_data unless the table is generated as editable text and not printed inside an image.
    - Do NOT change labels, coordinates, graph values, base notation, angles, lengths, frequencies, regions, or shape positions printed in the image.
    - Do NOT invent labels that are not shown in the image/table.
    - If the source only contains M, do not ask for N.
    - If the source only contains Q, do not ask for P unless P also exists in the visual.
    - TRIVIAL REJECTION: Do NOT ask the student to simply read and state a value that is already explicitly printed in the visual (e.g., if the diagram labels a drink as RM 11_2, do not ask "What is the price of the drink?"). The question MUST require calculation (like difference, sum, ratio, etc.).

    ANTI-COPY RULE:
    - The final question sentence must not be the same as the original final question sentence.
    - Do not only replace names.
    - Do not only rephrase the same question.
    - If the original asks "Calculate X", the variant should ask for a related value, comparison, statement, method, reverse value, or complement.
    - OPTION RECALCULATION: The new options MUST be recalculated to match the new question. Do not lazily reuse the original options if the target changed!
    - The marking_scheme.explanation must explain the new target, not the old one.

    MATH ACCURACY & OPTION POPULATION RULE (CRITICAL):
1. You MUST fill out the "calculation_scratchpad" object strictly step-by-step BEFORE generating the question text or options.
2. LATEX VS TEXT RULE:
   - If the answer is a mathematical expression, number, or base (e.g., base 2), you MUST use strict LaTeX wrapping (e.g., `$110_2$`). You are strictly forbidden from using Unicode subscripts (e.g., ₂).
   - If the answer is a full sentence or textual description (e.g., describing a locus or a concept), write it in plain English. Do NOT wrap full sentences in LaTeX `\text{}`.
3. In `step_3_true_final_answer`, write the exact correct result (following the LaTeX vs Text rule).
4. In `step_5_plan_distractors`, write exactly 3 mathematically plausible incorrect answers (following the LaTeX vs Text rule). Do NOT use lazy sequential numbers.
5. EXACT MATCH REQUIREMENT: When populating the final `options` array (A, B, C, D), the `text_en` value MUST be an EXACT, character-for-character copy-paste of the strings you planned in `step_3` and `step_5`. Do not reformat, add newlines, or remove LaTeX tags between the scratchpad and the `options` array.
    OUTPUT REQUIREMENT:
    - Return variant_type = "k1_mcq_variant".
    - Include mutation_type in the JSON.
    - mutation_type must be one of:
    "text_number_switch",
    "diagram_text_number_switch",
    "diagram_target_switch",
    "representation_switch",
    "reverse_question",
    "complement_switch",
    "condition_switch",
    "property_switch",
    "method_switch",
    "statement_switch",
    "misconception_switch".
    - Return exactly 4 options A, B, C, and D.
    - marking_scheme.final_answer must be only one letter: A, B, C, or D that matches the true calculated answer.
    """

        if has_diagram:
            mode_instruction = f"""
    The source is a K1 MCQ question with a diagram/table/image.

    Because this source has a diagram/table/image, DO NOT force a normal number switch.
    Use one of these mutation types first:
    - diagram_text_number_switch, if the editable condition is written outside the image/table.
    - diagram_target_switch, if the same visual has another valid target.
    - representation_switch, if the same value can be asked in another form.
    - statement_switch, if the visual is too fixed but statements can be tested.
    - method_switch, if no safe numerical target can be changed.
    - misconception_switch, if the best review is to test the common mistake.

    {k1_mutation_policy}
    """
        else:
            mode_instruction = f"""
    The source is a K1 MCQ question without a diagram/table/image.

    Because this source has no diagram/table/image, use one of these mutation types first:
    - text_number_switch, for normal calculation questions.
    - reverse_question, for formula-based questions.
    - complement_switch, for probability or sets.
    - condition_switch, for inequalities, finance, savings, and decisions.
    - property_switch, for concept questions.
    - misconception_switch, for common mistake review.

    {k1_mutation_policy}
    """

    elif has_diagram:
        variant_type = "same_diagram_followup"

        mode_instruction = """
    The source is a SINGLE-STAGE K2 structured question with a diagram/table/image.

    K2 SINGLE-STAGE SAME-DIAGRAM VARIANT GOAL:
    Generate one related structured review question using the same diagram/table/image,
    but do not copy the original question exactly.

    Choose exactly ONE mutation_type:

    1. k2_same_diagram_target_switch
    - Use when the diagram has more than one possible value or target.
    - Keep the image_path unchanged.
    - Ask for a different valid target.
    - Example: if original asks average speed, ask duration stopped or distance travelled.
    - Example: if original asks transformation T, ask transformation S or area scale factor.
    - Example: if original asks gradient, ask equation of line or parallel line.

    2. k2_same_table_target_switch
    - Use when the source has a table.
    - Keep the table unchanged.
    - Ask for another value from the same table.
    - Example: active income → passive income → total expenses → cash flow.

    3. k2_graph_reading_switch
    - Use for distance-time, speed-time, quadratic graph, ogive, histogram, stem-and-leaf, dot plot, pie chart.
    - Keep visual values unchanged.
    - Ask a different reading/calculation from the same graph.

    4. k2_probability_event_switch
    - Use for tree diagrams or probability contexts.
    - Change the event, not the whole visual.
    - Example: only one joins → at least one joins → both do not join.

    5. k2_set_expression_switch
    - Use for Venn diagrams.
    - Change the set expression.
    - Example: A ∩ B → A ∪ B' or A ∩ (B ∪ C)'.

    6. k2_transformation_target_switch
    - Use for transformation diagrams.
    - Ask another valid transformation detail.
    - Example: line of reflection, centre, scale factor, image/object area.

    7. k2_method_reasoning_switch
    - Use when the diagram is too locked and no numerical target is safe.
    - Ask for justification, conclusion, theorem, or reasoning.

    8. k2_diagram_text_condition_switch
    - Use when the diagram/image must stay the same, but the written condition outside the image can be changed.
    - Keep the same image_path.
    - Do not change any value printed inside the diagram/image.
    - Change only the values, quantities, budget, target, or condition written outside the image.
    - Use this for diagram-based word problems where the diagram gives fixed prices, measurements, graph values, labels, or objects, but the question text gives an editable condition.
    - Example for number base price questions:
    The image shows prices in different bases. Keep the image unchanged, but change the budget, number of items, or buying condition.
    - Example:
    Original: "The maximum budget allocated to buy three school bags is RM345."
    Variant: "Encik Azrul wants to buy two school bags of different brands. Determine whether the total cost exceeds RM345."
    - The generated question must not only rephrase the original question.

    DIAGRAM/TABLE/IMAGE LOCK:
    - Keep the same image_path.
    - Keep the same table_data if it is part of the source.
    - Do NOT change any printed number, label, coordinate, graph value, angle, length, region, table value, or frequency.
    - Do NOT invent new diagram labels.
    - The generated question must be answerable from the existing visual.
    - TRIVIAL REJECTION: Do NOT ask a question where the answer is just reading a number already printed directly on the image. It must require calculation or reasoning.

    ANTI-COPY RULE:
    - The final instruction sentence must not be the same as the source.
    - Do not only replace names.
    - The new marking scheme must explain the new target, not the old one.

    SAME-DIAGRAM CONDITION SWITCH RULE:
    - If the source diagram/image is locked but the written condition outside the image can be changed, prefer k2_diagram_text_condition_switch.
    - Do not return the same final instruction as the source.
    - Do not only add words like "Justify your answer".
    - For budget/price/number-base diagram questions, change at least one written condition outside the image, such as:
    1. budget amount,
    2. number of items,
    3. same-brand or different-brand condition,
    4. affordable combination target,
    5. minimum extra budget needed.

    OUTPUT FOR GROUP MODE:
    - Return variant_type = "same_diagram_followup" or "number_variant".
    - Include mutation_type.
    - Return question.stages.
    - Return marking_scheme.stages.
    - The number of generated question.stages MUST match the number of source rows/stages.
    - Do NOT return only one stage.
    - Do NOT put grouped subparts inside question.questions.
    - Each source row must become one generated stage.
    - Preserve exact part, subpart, and sub_subpart labels.
    - Do NOT merge subparts into one instruction.
    - Do NOT generate MCQ options.
    """

    else:
        variant_type = "number_variant"

        mode_instruction = """
    The source is a SINGLE-STAGE K2 structured question without a diagram/table/image.

    K2 SINGLE-STAGE TEXT-ONLY VARIANT GOAL:
    Generate one number-switched or condition-switched structured review question.

    Choose exactly ONE mutation_type:

    1. k2_text_number_switch
    - Change suitable numerical values while preserving the same skill and difficulty.
    - Recalculate the full marking scheme.

    2. k2_reverse_formula_switch
    - Use when the formula can be reversed.
    - Example: given premium, find face value → given face value, find premium.
    - Example: given area, find length → given length, find area.
    - Example: given amount, find principal → given principal, find amount.

    3. k2_condition_switch
    - Use for finance, savings, taxation, insurance, loan, budget, cash flow, or inequalities.
    - Change the condition and recalculate the answer.
    - Example: “Can he achieve the goal?” → “Find minimum monthly saving needed.”

    4. k2_probability_event_switch
    - Use for probability word problems.
    - Change the required event.
    - Example: both selected are same → selected are different → at least one.

    5. k2_statistics_target_switch
    - Use for statistics.
    - Example: mean → variance → standard deviation → conclusion.

    6. k2_method_reasoning_switch
    - Use for proof, logic, argument, statement, tessellation, or justification questions.
    - Change the required conclusion/reasoning, not just the wording.

    ANTI-COPY RULE:
    - Change at least 2 numerical values where possible.
    - Do not reuse the same final answer unless unavoidable.
    - The generated marking scheme must match the changed values exactly.

    OUTPUT:
    - Return variant_type = "number_variant".
    - Include mutation_type.
    - Return ONE single K2 stage.
    - If the source stage contains multiple extracted rows/subparts, return all of them inside question.questions.
    - Do NOT merge subparts into one instruction.
    - Preserve the same part/subpart/sub_subpart structure as the source.
    - Do NOT return question.stages unless source_mode is group.
    - Do NOT generate MCQ options.
    """

    # =========================
    # 4. Scope rule
    # =========================
    if source_mode == "group":
        mode_scope_instruction = """
    SCOPE RULE:
    Generate a review variant for the WHOLE grouped question.
    The source contains multiple stages/subparts from the same original question group.
    You must generate all required stages/subparts together, not only one stage.
    Return question.stages and marking_scheme.stages.
    """
    else:
        mode_scope_instruction = """
    SCOPE RULE:
    Generate a review variant for this single stage/question only.
    Return question and marking_scheme directly.
    Do NOT return question.stages.
    Do NOT return marking_scheme.stages.
    """
    # =========================
    # 6. Format source data before sending to LLM
    # =========================
    source_question = AgentOutputProcessor._walk_and_format(source_question)
    source_marking_scheme = AgentOutputProcessor._walk_and_format(source_marking_scheme)
    grading_result = AgentOutputProcessor._walk_and_format(grading_result or {})
    topic_method_rules = get_topic_method_rules(
        source_question=source_question,
        source_marking_scheme=source_marking_scheme
    )
    stage_structure_contract = build_k2_stage_structure_contract(
        source_question=source_question,
        source_mode=source_mode
    )
    value_only_safety_contract = build_value_only_safety_contract(
        source_question=source_question,
        source_mode=source_mode,
        is_k1_mcq_source=is_k1_mcq_source
    )
    # =========================
    # 5. Build system prompt
    # =========================
    system_prompt = r"""
You are an expert Malaysian SPM Mathematics review question generator.

__LANGUAGE_RULES__

__SCOPE_RULE__

TASK:
Generate a targeted review question for a student who did not get full marks.

__SOURCE_TYPE_INSTRUCTION__

__MODE_INSTRUCTION__

__TOPIC_METHOD_RULES__

__STAGE_STRUCTURE_CONTRACT__

__VALUE_ONLY_SAFETY_CONTRACT__

STRICT RULES:
1. Test the same mathematical concept as the source question.
2. Keep the level suitable for SPM Mathematics.
3. The generated marking scheme must match the generated question exactly.
4. Avoid impossible or messy values.
5. Return ONLY valid JSON.
6. Do not mention AI or that the question is generated.

LATEX MATH FIELD RULE:
- In marking_scheme.steps[n].math, write raw LaTeX only.
- Do NOT wrap the math field with $...$.
- Do NOT put $...$ inside \begin{aligned}...\end{aligned}.
- Correct:
  \begin{aligned} 433_7 &= 4(7^2) + 3(7^1) + 3(7^0) \end{aligned}
- Wrong:
  \begin{aligned} $433_7 &= 4(7^2) + 3(7^1) + 3(7^0)$ \end{aligned}

ANTI-DUPLICATION RULES:
1. The new variant must not be identical to the source question.
2. If there is no diagram/table/image, change at least 2 numerical values where possible.
3. If numbers are changed, the final answer must also be recalculated.
4. Do not reuse the same final answer unless mathematically unavoidable.
5. If there is a diagram/table/image, do not change values inside it. Instead, ask a valid related follow-up or preserve the same visual target.

CRITICAL GIVEN INFORMATION RULE:
- Every value used in the marking scheme must appear in the generated question, diagram label, table, or given_values.
- Do not use hidden values in the solution.
- If the solution uses area = 200, then the question must explicitly state "The area of the triangle is 200 m²."
- If a diagram label is changed, the question and marking scheme must remain consistent with that label.
- Do not introduce formulas, multipliers, or objects not visible in the question. For example, do not use 2 × 1/2 unless the question clearly involves two triangles.

If VARIANT TYPE is "k1_mcq_variant", you MUST use the K1 MCQ schema only.
Do not output "stages".
Do not output subjective marking steps unless they are only used as explanation.
SEQUENCE, TABLE, AND IMAGE RULE:

The "sequence" array controls what the frontend displays and in what order.

You MUST include every visible item in sequence:
- "text_0", "text_1", etc. for instructions_en / instructions_ms
- "table_0", "table_1", etc. for table_data
- "image_0", "image_1", etc. for image_path / image_urls / diagram images

TABLE RULE:
If table_data is not empty, sequence MUST include "table_0" at the exact position where the table appears.

IMAGE RULE:
If the question has a diagram, graph, chart, or any image:
1. Set has_diagram = 1.
2. Set diagram_type correctly.
3. Populate image_path or image_urls.
4. Add "image_0" into sequence at the exact position where the image should appear.

If image_path is not empty, sequence MUST include "image_0".
If image_urls has one image, sequence MUST include "image_0".
If image_urls has multiple images, sequence MUST include "image_0", "image_1", etc.
If image_path exists:
- Keep the diagram.
- Do not introduce new hidden values.
- Prefer asking a different readable target from the same diagram.
- If no safe target exists, generate a reasoning/method question instead.
Do NOT output image_path or image_urls without adding the matching image item into sequence.

COMMON VALID SEQUENCES:

Text only:
["text_0"]

Text then table then instruction:
["text_0", "table_0", "text_1"]

Text then image then instruction:
["text_0", "image_0", "text_1"]

Text then table then image then instruction:
["text_0", "table_0", "image_0", "text_1"]

Text then image then table then instruction:
["text_0", "image_0", "table_0", "text_1"]

IMPORTANT:
The sequence must follow the visual order of the question.
Do not place all text first if the table or image appears between the sentences.

DIFFICULTY PRESERVATION RULE:

The generated review variant MUST keep the same difficulty as the source question.

Do not increase or decrease the difficulty.
Do not make the question easier.
Do not make the question harder.

You MUST copy these values from the source question / parent variant:
- difficulty
- difficulty_level
- form
- chapter
- chapter_id

For review chains:
- If generating the first review variant, copy difficulty and difficulty_level from the original source question.
- If generating the next review variant from a previous review variant, copy difficulty and difficulty_level from the parent variant.
- Only the numbers / target / representation may change based on the mutation policy.
- The cognitive demand, number of steps, syllabus scope, and marking weight must remain equivalent.

Example:
If source question difficulty_level = 4 and difficulty = "Hard",
the review variant must also have:
difficulty_level = 4
difficulty = "Hard".

If source question difficulty_level = 3 and difficulty = "Moderate",
the review variant must also have:
difficulty_level = 3
difficulty = "Moderate".

SINGLE-STAGE MULTI-ROW RULE:
- A single-stage K2 question may contain multiple extracted question rows with the same exercise_stage_id.
- If the source single stage contains multiple rows/subparts, the generated variant must also return multiple rows inside question.questions.
- Do not merge all subparts into one instruction.
- Preserve the same subpart structure as the source.
- Example:
  Source has (a), (b), (c), (d) under the same exercise_stage_id.
  Generated variant must also have question.questions with four objects.
- If source has (a)(i), (a)(ii), (b), keep it as (a)(i), (a)(ii), (b).
- Do not convert (a)(i), (a)(ii), (b) into (a), (b), (c).
- Each generated subquestion must have its own part, subpart, sub_subpart, instructions_en, instructions_ms, sequence, and display_marks.

GRAPH STAGE COMPLETENESS RULE:
- If the source stage contains graph drawing, table completion, or "Based on the graph..." subparts, the generated variant must include the full graph stage.
- Do not generate only the graph-reading subpart.
- If the source contains:
  (a) complete table,
  (b) draw graph,
  (c)(i) use graph,
  (c)(ii) use graph,
  then the generated variant must also include all these subparts inside question.questions.
- Do not write "Based on the graph in 14(b)" or refer to the old original question number.
- Use "Based on the graph drawn in part (b)" instead.

For group mode:
- question.stages represents real pages/stages.
- If multiple source rows share the same stage_index, they must be placed inside the same stage.questions array.
- Do not create one stage per subpart.
- Preserve original stage_index.

GROUP MARKING SCHEME RULE:
- marking_scheme.stages must match question.stages, not individual subparts.
- If one question stage contains multiple subquestions inside stage.questions, then the matching marking_scheme stage must contain all marking steps for those subquestions.
- Do not create one marking_scheme stage per subpart.
- Use display_subpart_label such as "(a)(i)", "(a)(ii)", "(b)" inside marking_scheme.stages[n].steps.
- Use final_answers as a map inside the same marking_scheme stage.

SHARED DIAGRAM RULE FOR SINGLE-STAGE K2:
- If the same diagram/image applies to all subparts, put image_path, has_diagram, diagram_type, and image_0 sequence at the parent question level.
- Do not put empty image_path fields inside question.questions if the image is inherited from the parent.
- Subquestion image_path should only be used when that subquestion has its own separate image.

SINGLE-STAGE PARENT STEM RULE:
- question.instructions_en and question.instructions_ms must contain ONLY the shared main question stem/context.
- Do not put part-specific commands inside question.instructions_en.
- Part-specific commands must be placed inside question.questions[n].instructions_en and question.questions[n].instructions_ms.
- Example:
  Main stem: "A cyclist travelled 20 km at a speed of (x - 4) km h^{-1} in (x - 5) hours."
  Part (a): "Write a quadratic equation in x."
  Part (b): "Hence, calculate the value of x."
- Do not duplicate the same part command in both the parent question and the subquestion.

K1 EXPLANATION CONSISTENCY RULE:
- marking_scheme.explanation_en and explanation_bm must explain the generated question only.
- Do not mention objects, numbers, or context that do not appear in the generated question.
- The explanation must use the generated options and the generated final_answer.
- Before returning JSON, check that explanation_en uses the same objects as the question.
- Example: if the question is about red pens and blue pens, the explanation must not mention cups, mushrooms, balls, cards, or other objects.

FINAL CONSISTENCY CHECK BEFORE OUTPUT:
Before returning JSON, check:
1. Is the question solvable using only visible question text, table_data, given_values, and image labels?
2. Does the marking scheme use hidden values not shown in the question?
3. Do question parts match marking scheme parts?
4. For K1, are there exactly 4 options?
5. For K1, is final_answer A/B/C/D?
6. For K1, is the final answer and the explanation aligned?
7. For K2, do marks in steps add up to max_score?
8. For grouped K2, does question.stages length match marking_scheme.stages length?
9. For diagram variants, did it invent values that are not in the diagram or text?
10. Is the question ambigouous? IF yes, make it clearer
11. If any TOPIC METHOD RULE is provided, does every marking step follow that rule exactly?

OUTPUT JSON SCHEMA FOR K1 MCQ:
{
  "variant_type": "k1_mcq_variant",
  "question": {
    "instructions_en": ["English question text"],
    "instructions_ms": ["Malay question text"],
    "sequence": ["text_0"],
    "table_data": {},
    "given_values": {},
    "image_path": "",
    "has_diagram": 0,
    "diagram_type": "",
    "display_marks": 1,
    "calculation_scratchpad": {
      "step_1_identify_values": "List the exact values extracted from the text and diagram.",
      "step_2_perform_math": "Read the instructions_en you just generated above. Perform the exact calculation requested (e.g. sum, difference) step-by-step.",
      "step_3_true_final_answer": "State the exact final calculated value.",
      "step_4_assign_correct_option": "Choose A, B, C, or D to hold the true answer.",
      "step_5_plan_distractors": ["wrong value 1", "wrong value 2", "wrong value 3"]
    },
    "options": [
      {
        "label": "A",
        "text_en": "Must match a value from the scratchpad",
        "text_ms": "Must match a value from the scratchpad",
        "image_path": ""
      },
      {
        "label": "B",
        "text_en": "Option B in English",
        "text_ms": "Option B in Bahasa Melayu",
        "image_path": ""
      },
      {
        "label": "C",
        "text_en": "Option C in English",
        "text_ms": "Option C in Bahasa Melayu",
        "image_path": ""
      },
      {
        "label": "D",
        "text_en": "Option D in English",
        "text_ms": "Option D in Bahasa Melayu",
        "image_path": ""
      }
    ]
  },
  "marking_scheme": {
    "max_score": 1,
    "final_answer": "A",
    "explanation_en": "Short explanation of why this option is correct.",
    "explanation_bm": "Penerangan ringkas mengapa pilihan ini betul."
  }
}

OUTPUT JSON SCHEMA FOR SINGLE STAGE:
{
  "variant_type": "number_variant or same_diagram_followup",
  "mutation_type": "chosen mutation type",
  "question": {
    "stage_index": 1,
    "instructions_en": ["Shared intro text if all subparts share it, otherwise []"],
    "instructions_ms": ["Shared intro text in Malay if applicable, otherwise []"],
    "sequence": ["text_0"],
    "table_data": {},
    "given_values": {},
    "image_path": "",
    "has_diagram": 0,
    "diagram_type": "",
    "display_marks": 3,

    "questions": [
      {
        "part": "a",
        "subpart": "",
        "sub_subpart": "",
        "instructions_en": ["Instruction for part (a)"],
        "instructions_ms": ["Instruction for part (a) in Malay"],
        "sequence": ["text_0"],
        "table_data": {},
        "given_values": {},
        "image_path": "",
        "has_diagram": 0,
        "diagram_type": "",
        "display_marks": 1
      },
      {
        "part": "b",
        "subpart": "",
        "sub_subpart": "",
        "instructions_en": ["Instruction for part (b)"],
        "instructions_ms": ["Instruction for part (b) in Malay"],
        "sequence": ["text_0"],
        "table_data": {},
        "given_values": {},
        "image_path": "",
        "has_diagram": 0,
        "diagram_type": "",
        "display_marks": 1
      }
    ]
  },
  "marking_scheme": {
    "max_score": 3,
    "steps": [
      {
        "display_subpart_label": "(a)",
        "step": "Step title for part (a)",
        "text": "What the student should do",
        "math": "Calculation or formula, if any",
        "marks": 1
      },
      {
        "display_subpart_label": "(b)",
        "step": "Step title for part (b)",
        "text": "What the student should do",
        "math": "Calculation or formula, if any",
        "marks": 1
      }
    ],
    "final_answers": {
      "(a)": "Final answer for part (a)",
      "(b)": "Final answer for part (b)"
    }
  }
}

OUTPUT JSON SCHEMA FOR GROUP:
{
  "variant_type": "number_variant or same_diagram_followup",
  "mutation_type": "chosen mutation type",
  "question": {
    "stages": [
      {
        "stage_index": 1,
        "instructions_en": ["Shared context for this stage"],
        "instructions_ms": ["Konteks bersama untuk peringkat ini"],
        "sequence": ["text_0"],
        "table_data": {},
        "given_values": {},
        "image_path": "",
        "image_urls": [],
        "has_diagram": 0,
        "diagram_type": "",
        "display_marks": 2,
        "questions": [
          {
            "part": "a",
            "subpart": "i",
            "sub_subpart": "",
            "instructions_en": ["Instruction for (a)(i)"],
            "instructions_ms": ["Arahan untuk (a)(i)"],
            "sequence": ["text_0"],
            "table_data": {},
            "given_values": {},
            "image_path": "",
            "image_urls": [],
            "has_diagram": 0,
            "diagram_type": "",
            "display_marks": 1
          },
          {
            "part": "a",
            "subpart": "ii",
            "sub_subpart": "",
            "instructions_en": ["Instruction for (a)(ii)"],
            "instructions_ms": ["Arahan untuk (a)(ii)"],
            "sequence": ["text_0"],
            "table_data": {},
            "given_values": {},
            "image_path": "",
            "image_urls": [],
            "has_diagram": 0,
            "diagram_type": "",
            "display_marks": 1
          }
        ]
      }
    ]
  },
  "marking_scheme": {
    "max_score": 2,
    "stages": [
      {
        "stage_index": 1,
        "max_score": 2,
        "steps": [
          {
            "display_subpart_label": "(a)(i)",
            "step": "Step title for (a)(i)",
            "text": "What the student should do for (a)(i)",
            "math": "Calculation or formula for (a)(i)",
            "marks": 1
          },
          {
            "display_subpart_label": "(a)(ii)",
            "step": "Step title for (a)(ii)",
            "text": "What the student should do for (a)(ii)",
            "math": "Calculation or formula for (a)(ii)",
            "marks": 1
          }
        ],
        "final_answers": {
          "(a)(i)": "Final answer for (a)(i)",
          "(a)(ii)": "Final answer for (a)(ii)"
        }
      }
    ]
  }
}
""".replace("__LANGUAGE_RULES__", language_rules) \
   .replace("__SCOPE_RULE__", mode_scope_instruction) \
   .replace("__SOURCE_TYPE_INSTRUCTION__", source_type_instruction) \
   .replace("__MODE_INSTRUCTION__", mode_instruction) \
   .replace("__TOPIC_METHOD_RULES__", topic_method_rules) \
   .replace("__STAGE_STRUCTURE_CONTRACT__", stage_structure_contract) \
   .replace("__VALUE_ONLY_SAFETY_CONTRACT__", value_only_safety_contract)

    user_prompt = f"""
SOURCE LABEL:
{source_label}

SOURCE MODE:
{source_mode}

VARIANT TYPE:
{variant_type}

SOURCE QUESTION DATA:
{json.dumps(source_question, ensure_ascii=False, indent=2)}

SOURCE MARKING SCHEME:
{json.dumps(source_marking_scheme, ensure_ascii=False, indent=2)}

STUDENT GRADING RESULT:
{json.dumps(grading_result or {}, ensure_ascii=False, indent=2)}

Generate the review variant now.
"""

    # =========================
    # 7. Generate variant
    # =========================
    user_content = [{"type": "text", "text": user_prompt}]
    
    # Give the LLM eyes if the source has a diagram
    source_image_url = ""
    if isinstance(source_question, dict):
        source_image_url = source_question.get("image_path", "")
    elif isinstance(source_question, list) and len(source_question) > 0:
        source_image_url = source_question[0].get("image_path", "")
        
    if source_image_url:
        user_content.append({
            "type": "image_url",
            "image_url": {"url": source_image_url}
        })

    response = openai_client.chat.completions.create(
        model="gemini-3.5-flash-lite", # Make sure you are using a vision-capable model like gpt-4o or gemini-3.5-flash-lite
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
        temperature=0.1,
        response_format={"type": "json_object"}
    )

    variant = AgentOutputProcessor.process(response.choices[0].message.content)
    variant = AgentOutputProcessor._walk_and_format(variant)
    print(variant)
    if not isinstance(variant, dict):
        return {
            "variant_type": "error",
            "message": "Generated variant was not a valid JSON object."
        }
    variant = clean_variant_latex_math_fields(variant)
    variant = clean_variant_question_payload(variant)
    variant = clean_k2_stage_parent_duplicate_instructions(
        variant=variant,
        source_mode=source_mode
    )
    variant = enforce_safe_question_image_placement(
        variant,
        source_rows_for_image
    )

    variant = clean_variant_question_payload(variant)
    variant = clean_variant_question_payload(variant)
    structure_check = validate_k2_stage_variant_structure(
        variant=variant,
        source_question=source_question,
        source_mode=source_mode
    )
    if not structure_check["valid"]:
        print("K2 STAGE VARIANT STRUCTURE FAILED:", structure_check)

        return {
            "variant_type": "error",
            "message": "Generated K2 stage variant failed structure validation.",
            "validation": structure_check
        }

    content_check = validate_value_only_variant_content(
        variant=variant,
        source_question=source_question,
        source_mode=source_mode
    )

    if not content_check["valid"]:
        print("K2 VALUE-ONLY VARIANT CONTENT FAILED:", content_check)

        return {
            "variant_type": "error",
            "message": "Generated K2 variant failed value-only content validation.",
            "validation": content_check
        }

    # =========================
    # 7.5 Regenerate K2 marking scheme from original scheme
    # =========================
    if not is_k1_mcq_source:
        regenerated_marking_scheme = regenerate_k2_marking_scheme_from_original(
            variant=variant,
            source_question=source_question,
            source_marking_scheme=source_marking_scheme,
            language=language
        )

        ms_check = validate_regenerated_k2_marking_scheme(
            variant=variant,
            marking_scheme=regenerated_marking_scheme
        )

        if not ms_check["valid"]:
            print("K2 REGENERATED MARKING SCHEME FAILED:", ms_check)

            return {
                "variant_type": "error",
                "message": "Generated K2 marking scheme failed validation.",
                "validation": ms_check
            }

        variant["marking_scheme"] = ms_check["marking_scheme"]
        # =========================
    # 8. Force metadata
    # =========================
    variant["variant_type"] = variant_type
    variant["source_mode"] = source_mode
    variant["source_key"] = source_label
    variant["source_exercise_stage_id"] = exercise_stage_id
    variant["source_group_id"] = group_id
    variant["source_question_id"] = question_id
    variant["language"] = language

    # =========================
    # 9. K1-specific safety cleanup
    # =========================
    if is_k1_mcq_source:
        allowed_k1_mutations = set(K1_MUTATION_TYPES)

        mutation_type = str(variant.get("mutation_type") or "").strip()

        if mutation_type not in allowed_k1_mutations:
            if has_diagram:
                variant["mutation_type"] = "diagram_target_switch"
            else:
                variant["mutation_type"] = "text_number_switch"

        variant = align_k1_question_options_and_explanation(variant)

        marking_scheme = variant.setdefault("marking_scheme", {})
        final_answer = str(marking_scheme.get("final_answer") or "").strip().upper()

        if is_k1_mcq_source:
            allowed_k1_mutations = set(K1_MUTATION_TYPES)

            mutation_type = str(variant.get("mutation_type") or "").strip()

            if mutation_type not in allowed_k1_mutations:
                if has_diagram:
                    variant["mutation_type"] = "diagram_target_switch"
                else:
                    variant["mutation_type"] = "text_number_switch"

            # Normalize options first
            variant = normalize_k1_options_in_variant(variant)

            marking_scheme = variant.setdefault("marking_scheme", {})
            final_answer = str(marking_scheme.get("final_answer") or "").strip().upper()

            # Do NOT silently default to A
            if final_answer not in ["A", "B", "C", "D"]:
                return {
                    "variant_type": "error",
                    "message": "Generated K1 variant has invalid final_answer.",
                    "validation": {
                        "valid": False,
                        "issues": [f"Invalid final_answer: {final_answer}"]
                    }
                }

            marking_scheme["final_answer"] = final_answer
            marking_scheme["max_score"] = 1
            variant["marking_scheme"] = marking_scheme

            question = variant.setdefault("question", {})
            question["display_marks"] = 1

            if has_diagram:
                variant = preserve_k1_locked_visuals(variant, source_question)
                variant = force_existing_visual_label_for_k1(variant, source_question)

            variant = align_k1_question_options_and_explanation(variant)

            # Final hard validation before saving
            k1_check = validate_k1_mcq_variant_basic(variant)

            if not k1_check["valid"]:
                print("K1 MCQ VARIANT VALIDATION FAILED:", k1_check)

                return {
                    "variant_type": "error",
                    "message": "Generated K1 MCQ variant failed answer-option validation.",
                    "validation": k1_check
                }

        marking_scheme["max_score"] = 1
        variant["marking_scheme"] = marking_scheme

        question = variant.setdefault("question", {})
        question["display_marks"] = 1

        if has_diagram:
            variant = preserve_k1_locked_visuals(variant, source_question)
            variant = force_existing_visual_label_for_k1(variant, source_question)

    # =========================
    # 10. General diagram safety for K2/stage/group variants
    # =========================
    elif has_diagram:
        original_image = ""

        if source_mode == "variant":
            if isinstance(source_question, dict):
                original_image = source_question.get("image_path", "")
            elif isinstance(source_question, list):
                original_image = next(
                    (
                        q.get("image_path")
                        for q in source_question
                        if isinstance(q, dict) and q.get("image_path")
                    ),
                    ""
                )
        else:
            original_image = next(
                (row.get("image_path") for row in rows if row.get("image_path")),
                ""
            )

        variant.setdefault("question", {})
        variant["question"]["image_path"] = (
            variant["question"].get("image_path") or original_image
        )
        variant["question"]["has_diagram"] = (
            1 if original_image else variant["question"].get("has_diagram", 0)
        )

        if not variant["question"].get("sequence"):
            variant["question"]["sequence"] = (
                ["text_0", "image_0"] if original_image else ["text_0"]
            )

    return variant

def flatten_variant_marking_scheme(marking_scheme):
    if not isinstance(marking_scheme, dict):
        return {
            "steps": [],
            "final_answer": "",
            "final_answers": {}
        }

    if isinstance(marking_scheme.get("stages"), list):
        flat_steps = []
        final_answers = {}

        for stage in marking_scheme.get("stages", []):
            stage_index = stage.get("stage_index")

            for step in stage.get("steps", []) or []:
                if isinstance(step, dict):
                    flat_steps.append({
                        **step,
                        "stage_index": stage_index,
                    })

            if isinstance(stage.get("final_answers"), dict):
                final_answers.update(stage.get("final_answers"))

            if stage.get("final_answer"):
                final_answers[f"stage_{stage_index}"] = stage.get("final_answer")

        return {
            "steps": flat_steps,
            "final_answer": marking_scheme.get("final_answer", ""),
            "final_answers": final_answers,
            "stages": marking_scheme.get("stages", []),
        }

    return {
        "steps": marking_scheme.get("steps", []) or [],
        "final_answer": marking_scheme.get("final_answer", ""),
        "final_answers": marking_scheme.get("final_answers", {}),
    }

GRAPH_AND_DRAWING_GRADING_RULES = r"""
    GRAPH / DRAWING / SHADING GRADING RULES

    When the student's answer is a graph, ogive, shading diagram, Venn diagram, or plotted curve, grade the visible drawing directly from the student image.

    Do not grade only from the final written answer.
    Do not require a perfectly beautiful drawing.
    Award marks based on the mathematical features required by the marking scheme.

    GENERAL VISUAL GRADING WORKFLOW
    1. Identify the required graph type:
    - linear graph
    - linear inequality graph
    - quadratic graph
    - ogive / cumulative frequency graph
    - Venn diagram shading
    - region shading
    - graph transformation
    - motion graph
    2. Extract the expected mathematical features from the question, marking scheme, and official solution.
    3. Inspect the student drawing for those features.
    4. Compare feature by feature.
    5. Give partial marks for correct mathematical features even if the drawing is not perfectly neat.
    6. Penalize only if the error changes the mathematical meaning.

    VISUAL EVIDENCE AUDIT
    Before awarding marks for graph/drawing questions, include in your reasoning:
    - axes present or not
    - scale correct or not
    - important points plotted or not
    - line/curve shape correct or not
    - boundary type correct or not
    - shading region correct or not
    - labels/coordinates required by marking scheme present or not
    - final region/answer matches the required condition or not

    LINEAR INEQUALITY GRAPH GRADING
    For inequalities such as:
    y < mx + c
    y <= mx + c
    y > mx + c
    y >= mx + c
    ax + by < c
    ax + by <= c

    Check these features:
    1. Boundary line:
    - correct equation
    - correct gradient
    - correct intercepts or at least two correct plotted points
    2. Boundary type:
    - dashed line for < or >
    - solid line for <= or >=
    3. Shading:
    - correct side of the line
    - use a test point if needed
    - for simultaneous inequalities, shaded region must be the intersection of all required half-planes
    4. Axes and scale:
    - axes drawn clearly
    - reasonable scale
    - important intercepts visible
    5. Labels:
    - label the line/region if required by marking scheme

    Marking guidance:
    - Correct boundary line but wrong shading: award line marks only.
    - Correct shading idea but boundary type wrong: deduct boundary-type mark only.
    - Correct region but untidy shading: do not heavily penalize.
    - If shaded region satisfies the inequality but labels are missing, penalize only if labels are required by the marking scheme.

    QUADRATIC GRAPH GRADING
    For quadratic graphs such as y = ax^2 + bx + c:

    Check these features:
    1. Shape:
    - opens upward if a > 0
    - opens downward if a < 0
    - smooth parabolic curve
    2. Key points:
    - y-intercept
    - x-intercepts / roots if required
    - turning point / vertex if required
    - axis of symmetry if required
    3. Table of values:
    - if a table is required, check substituted values
    - plotted points should match the table
    4. Curve:
    - should pass near the plotted points
    - should not be drawn as straight line segments only
    5. Scale and axes:
    - reasonable axis scale
    - x-axis and y-axis labelled if required

    Marking guidance:
    - Correct table but inaccurate curve: award table marks, reduce graph marks.
    - Correct shape but wrong intercepts: award shape mark only.
    - Correct roots but wrong turning point: award root-related marks only.
    - Minor plotting inaccuracy is acceptable if the intended point is clear.

    OGIVE / CUMULATIVE FREQUENCY GRAPH GRADING
    For ogive questions:

    Check these features:
    1. Cumulative frequency table:
    - cumulative frequencies calculated correctly
    - final cumulative frequency equals total frequency
    2. X-axis:
    - uses upper class boundaries, not midpoints
    - scale is consistent
    3. Y-axis:
    - cumulative frequency scale is consistent
    4. Starting point:
    - should start from lower boundary with cumulative frequency 0 when required
    5. Plotted points:
    - each point should be (upper boundary, cumulative frequency)
    6. Curve:
    - smooth increasing curve
    - should not decrease
    - should pass near plotted points
    7. Readings:
    - median, Q1, Q3, percentile, or estimated value should be read from the curve correctly

    Marking guidance:
    - Correct cumulative frequency table but wrong graph: award table marks only.
    - Correct points but rough curve: award most graph marks.
    - Using class midpoints instead of upper boundaries is a graph-construction error.
    - If the curve is not smooth but points are correct, do not mark everything wrong.
    - If quartile reading is slightly off due to graph scale, allow small tolerance.

    VENN DIAGRAM / SET SHADING GRADING
    For set shading:

    Check:
    1. Correct set expression interpreted.
    2. Correct region shaded.
    3. No extra unwanted region shaded.
    4. Complements are handled correctly.
    5. Intersections and unions are distinguished correctly.

    Common rules:
    - A ∩ B means only the overlapping region.
    - A ∪ B means all regions in A or B.
    - A' means outside A.
    - (A ∩ B)' means everything except the overlap.
    - A - B means the part of A outside B.

    Marking guidance:
    - Correct main region but small over-shading: partial credit.
    - Correct expression but wrong visual shading: explanation marks only, if applicable.
    - If the student shades the complement instead, mark the shading as wrong.

    GRAPH TRANSFORMATION GRADING
    For transformation of graphs:

    Check:
    1. Correct transformation type:
    - translation
    - reflection
    - rotation
    - enlargement
    2. Correct direction and magnitude.
    3. Key points mapped correctly.
    4. Shape preserved when appropriate.
    5. Orientation correct after reflection/rotation.
    6. Scale factor correct for enlargement.

    Marking guidance:
    - Award marks for correct mapped points even if final drawing is rough.
    - If transformation direction is opposite, deduct transformation mark.
    - If shape is correct but position wrong, award shape preservation mark only.

    MOTION GRAPH GRADING
    For distance-time or speed-time graphs:

    Check:
    1. Axes labels and units.
    2. Correct plotted points.
    3. Correct line segment shape:
    - horizontal line = stationary / constant speed depending graph type
    - gradient = speed or acceleration depending graph type
    4. Correct gradient or area calculation when asked.
    5. Correct interpretation of graph sections.

    Marking guidance:
    - Correct calculation but wrong graph interpretation: award calculation marks only.
    - Correct graph reading but arithmetic error: award method marks if visible.

    TOLERANCE RULE
    For hand-drawn graphs:
    - Allow small plotting or reading error if the mathematical intention is clear.
    - Do not require pixel-perfect accuracy.
    - Be stricter when the question asks for exact coordinates, exact intercepts, or exact shaded region.

    OFFICIAL MARKING SCHEME PRIORITY
    If official marking scheme gives specific marks, follow it.
    Map visual features to official marks.
    If the official marking scheme is vague, use the feature checklist above to award fair partial marks.
    """

def grade_review_variant(student_image_base64, variant, language="english"):
    language = normalize_response_language(language)
    language_rules = get_response_language_rules(language)

    safe_image_string = format_image_for_llm(student_image_base64)

    system_prompt = GRAPH_AND_DRAWING_GRADING_RULES + r"""
You are a strict but fair Malaysian SPM Mathematics examiner.

__LANGUAGE_RULES__

You are grading a student's handwritten answer to a GENERATED REVIEW VARIANT.

SOURCE OF TRUTH RULES:
1. The SAVED GENERATED MARKING SCHEME is the source of truth.
2. Do not solve the question again from scratch.
3. Do not create a new marking scheme.
4. Do not use the original DB question or old official marking scheme.
5. The attached student image is the source of truth for what the student wrote or drew.

RUBRIC USAGE RULES:
1. Evaluate every marking step in the saved generated marking scheme.
2. Do not skip any subpart.
3. Grade each subpart separately.
4. Copy the step label from the generated marking scheme where possible.
5. Use marks/max_marks from the generated marking scheme.
6. If the marking scheme contains stages, flatten by stage but preserve stage_index and display_subpart_label.

MARKING RULES:
1. Award marks strictly based on mathematical correctness and the saved generated marking scheme.
2. Accept valid equivalent methods if they reach the same mathematically correct result.
3. If working is required but missing, do not award full marks.
4. If the student shows correct method but wrong arithmetic, award method marks only.
5. If the final answer is numerically correct but the unit is wrong, award 0 for that final-answer step.
6. If handwriting is unclear, say it is unclear and award marks only if enough evidence is visible.
7. Do not invent student working.

VISUAL ANSWER RULES:
1. If the review variant involves graph, drawing, construction, ogive, histogram, box plot, Venn diagram, or shaded region, inspect the student image visually.
2. Do not grade only from written final answer.
3. Award marks for correct visual features according to the marking scheme.
4. Allow small plotting/drawing tolerance if the mathematical intention is clear.
5. For Venn/set shading, grade the visible shaded region, not only the written set expression.

OUTPUT JSON ONLY:
{
  "question_text": "Short summary of the generated review question.",
  "stepwise_evaluation": [
    {
      "display_subpart_label": "(a)",
      "step": "Name of marking step",
      "student_wrote": "Exact visible working or drawing description. If missing, write No working shown.",
      "expected": "Expected answer/method/graph feature from the generated marking scheme.",
      "reason": "Why marks were awarded or lost.",
      "marks_awarded": 0,
      "max_marks": 1
    }
  ],
  "score": 0,
  "max_score": 0,
  "is_correct_for_adaptive": false,
  "summary_feedback": "Short feedback."
}

ADAPTIVE CORRECTNESS RULE:
Set is_correct_for_adaptive to true only if score / max_score >= 0.8.
If max_score is 0, set it to false.
""".replace("__LANGUAGE_RULES__", language_rules)

    marking_scheme = variant.get("marking_scheme", {}) or {}
    question_payload = variant.get("question", {}) or {}
    flat_solution = flatten_variant_marking_scheme(marking_scheme)

    user_prompt = f"""
    STUDENT SELECTED LANGUAGE:
    {language}

    GENERATED REVIEW QUESTION:
    {json.dumps(question_payload, ensure_ascii=False, indent=2)}

    SAVED GENERATED MARKING SCHEME:
    {json.dumps(marking_scheme, ensure_ascii=False, indent=2)}

    FLATTENED MARKING STEPS FOR GRADING:
    {json.dumps(flat_solution, ensure_ascii=False, indent=2)}

    Grade the attached student answer image using ONLY the saved generated marking scheme.

    Do not generate a new solution.
    Do not change the expected answer.
    Do not skip any marking step.
    """

    user_content = [{"type": "text", "text": user_prompt}]

    if safe_image_string:
        user_content.append({
            "type": "image_url",
            "image_url": {"url": safe_image_string}
        })

    response = openai_client.chat.completions.create(
        model="gemini-3.5-flash-lite",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
        temperature=0,
        response_format={"type": "json_object"}
    )

    result = AgentOutputProcessor.process(response.choices[0].message.content)

    marking_scheme = variant.get("marking_scheme", {}) or {}

    result["official_solution"] = flatten_variant_marking_scheme(marking_scheme)

    return result