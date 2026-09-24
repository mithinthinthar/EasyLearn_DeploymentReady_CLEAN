import base64
import json
import re
from solving.config import openai_client, get_db_connection, normalize_response_language, get_response_language_rules, aclient
from solving.format_json import AgentOutputProcessor
from solving.extractor import run_base_extractor, normalize_topic_subtopic, format_image_for_llm
from solving.rag_retriever import get_smart_rag_context, format_rag_context_for_llm
from solving.math_tools import algebra_tool, calculate_expression, coordinate_geometry_tool, financial_math_tool, geometry_mensuration_tool, matrix_tool, solve_equations_tool, statistics_tool
from solving.utils import enhance_shading_contrast
math_tools = [
    calculate_expression,
    algebra_tool,
    solve_equations_tool,
    matrix_tool,
    coordinate_geometry_tool,
    geometry_mensuration_tool,
    statistics_tool,
    financial_math_tool,
]


def normalize_extracted_for_rag(extracted: dict) -> dict:
    if not isinstance(extracted.get("table_data"), dict):
        extracted["table_data"] = {}

    if not isinstance(extracted.get("given_values"), dict):
        extracted["given_values"] = {}

    if not extracted["table_data"]:
        promoted_tables = {}

        for key, value in extracted["given_values"].items():
            key_lower = str(key).lower()

            if (
                "table" in key_lower
                or "jadual" in key_lower
                or isinstance(value, list)
            ):
                promoted_tables[str(key)] = value

        if promoted_tables:
            extracted["table_data"] = promoted_tables

    return extracted


def build_question_text_from_interpreted(interpreted):
    """
    Build a readable question summary from run_base_extractor output.
    Used by Check My Work so frontend does not show 'AI Grading Report'.
    """
    if not isinstance(interpreted, dict):
        return ""

    instructions = (
        interpreted.get("instructions_en")
        or interpreted.get("instructions_ms")
        or []
    )

    if isinstance(instructions, list):
        question_text = " ".join(
            str(item).strip()
            for item in instructions
            if str(item).strip()
        )
    else:
        question_text = str(instructions or "").strip()

    if not question_text:
        question_text = str(interpreted.get("target") or "").strip()

    if not question_text:
        question_text = str(interpreted.get("visual_semantic_summary") or "").strip()

    question_text = re.sub(r"\s+", " ", question_text).strip()

    return question_text[:700]

def enforce_unit_penalty(grading_result):
    """
    Fix inconsistent LLM grading where reason says unit is wrong
    but marks_awarded is still 1.
    """
    total_score = 0

    for step in grading_result.get("stepwise_evaluation", []):
        reason = str(step.get("reason", "")).lower()
        student_wrote = str(step.get("student_wrote", "")).lower()

        unit_error_keywords = [
            "unit written is wrong",
            "unit is wrong",
            "wrong unit",
            "incorrect unit",
            "omits the unit",
            "missing unit",
            "should be 0",
            "strict unit penalty"
        ]

        if any(keyword in reason for keyword in unit_error_keywords):
            step["marks_awarded"] = 0

        try:
            total_score += int(step.get("marks_awarded", 0))
        except:
            step["marks_awarded"] = 0

    grading_result["score"] = total_score
    return grading_result


def build_original_part_label(row: dict) -> str:
    label = ""

    if row.get("part"):
        label += f"({row.get('part')})"
    if row.get("subpart"):
        label += f"({row.get('subpart')})"
    if row.get("sub_subpart"):
        label += f"({row.get('sub_subpart')})"

    return label

def apply_display_subpart_labels(rows: list) -> list:
    """
    Student-facing label rule:
    - If original starts with (a), keep labels.
      Example: (a)(i), (a)(ii), (b) stays the same.
    - If original starts with (c), (d), etc., restart main part from (a).
      Example: (c)(i), (c)(ii), (d) becomes (a)(i), (a)(ii), (b).
    - Only renumber the main letter.
    - Preserve subpart and sub_subpart such as (i), (ii), (iii).
    """

    if not rows:
        return rows

    first_part = str(rows[0].get("part") or "").strip().lower()
    should_renumber = bool(first_part and re.fullmatch(r"[a-z]", first_part) and first_part != "a")

    main_part_map = {}

    for index, row in enumerate(rows):
        original_label = build_original_part_label(row)
        row["original_subpart_label"] = original_label

        original_part = str(row.get("part") or "").strip().lower()

        if should_renumber and re.fullmatch(r"[a-z]", original_part):
            if original_part not in main_part_map:
                main_part_map[original_part] = chr(97 + len(main_part_map))

            display_part = main_part_map[original_part]

            display_label = f"({display_part})"

            if row.get("subpart"):
                display_label += f"({row.get('subpart')})"

            if row.get("sub_subpart"):
                display_label += f"({row.get('sub_subpart')})"

            row["display_subpart_label"] = display_label
        else:
            row["display_subpart_label"] = original_label or f"({chr(97 + index)})"

    return rows

def normalize_part_key(value: str) -> str:
    return re.sub(r"[\s()]", "", str(value or "").lower())


def force_display_subpart_labels(result: dict, rubric_rows: list) -> dict:
    """
    Ensures frontend always receives display_subpart_label.
    Do not rely only on the LLM to output it.
    """

    if not isinstance(result, dict):
        return result

    labels = []
    label_by_key = {}

    for index, row in enumerate(rubric_rows):
        display_label = (
            row.get("display_subpart_label")
            or build_original_part_label(row)
            or f"({chr(97 + index)})"
        )

        original_label = build_original_part_label(row)

        labels.append(display_label)

        possible_keys = [
            original_label,
            row.get("display_subpart_label"),
            row.get("part"),
            row.get("subpart"),
            row.get("sub_subpart"),
        ]

        if row.get("part") and row.get("subpart"):
            possible_keys.append(f"{row.get('part')}({row.get('subpart')})")
            possible_keys.append(f"({row.get('part')})({row.get('subpart')})")

        if row.get("part") and row.get("subpart") and row.get("sub_subpart"):
            possible_keys.append(
                f"({row.get('part')})({row.get('subpart')})({row.get('sub_subpart')})"
            )

        for key in possible_keys:
            norm = normalize_part_key(key)
            if norm:
                label_by_key[norm] = display_label

    def infer_label(step, idx, total_steps):
        if not isinstance(step, dict):
            return ""

        if step.get("display_subpart_label"):
            return step.get("display_subpart_label")

        for key_name in ["subpart", "part", "question_part", "label"]:
            norm = normalize_part_key(step.get(key_name))
            if norm in label_by_key:
                return label_by_key[norm]

        text = f"{step.get('step', '')} {step.get('text', '')} {step.get('reason', '')}"
        match = re.search(r"\([a-z]\)\([ivx]+\)|\([a-z]\)|[a-z]\([ivx]+\)", text.lower())

        if match:
            norm = normalize_part_key(match.group(0))
            if norm in label_by_key:
                return label_by_key[norm]

        # Safe fallback for cases like your screenshot:
        # 2 subquestions, 2 solution cards => assign (a), (b)
        if total_steps == len(labels):
            return labels[idx]

        # If only one subpart, assign the only label
        if len(labels) == 1:
            return labels[0]

        return ""

    def patch_steps(steps):
        if not isinstance(steps, list):
            return steps

        total_steps = len(steps)

        for idx, step in enumerate(steps):
            if not isinstance(step, dict):
                continue

            label = infer_label(step, idx, total_steps)

            if label:
                step["display_subpart_label"] = label

        return steps

    if isinstance(result.get("stepwise_evaluation"), list):
        result["stepwise_evaluation"] = patch_steps(result["stepwise_evaluation"])

    if isinstance(result.get("steps"), list):
        result["steps"] = patch_steps(result["steps"])

    if isinstance(result.get("official_solution"), dict):
        result["official_solution"]["steps"] = patch_steps(
            result["official_solution"].get("steps", [])
        )

    return result

def fetch_official_rubrics_for_stage(exercise_stage_id: str, question_ids=None):
    """
    Fetch marking schemes for the current displayed exercise stage.

    If question_ids is provided, only fetch those question rows.
    This is important for Mixed groups where one exercise_stage_id may contain
    rows from different chapters.
    """

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    clean_question_ids = [
        int(qid) for qid in (question_ids or [])
        if str(qid).isdigit()
    ]

    params = [exercise_stage_id]
    question_filter = ""

    if clean_question_ids:
        placeholders = ",".join(["%s"] * len(clean_question_ids))
        question_filter = f" AND q.id IN ({placeholders})"
        params.extend(clean_question_ids)

    cursor.execute(f"""
        SELECT
            q.id AS question_id,
            q.paper_id,
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
            q.image_path,

            m.id AS marking_scheme_id,
            m.raw_json,
            m.answer_image_path
        FROM questions q
        JOIN question_marking_links qml
            ON q.id = qml.question_id
        JOIN marking_schemes m
            ON qml.marking_scheme_id = m.id
        WHERE q.exercise_stage_id = %s
          {question_filter}
        ORDER BY
            q.question_no + 0,
            q.part,
            q.subpart,
            q.sub_subpart
    """, tuple(params))

    rows = cursor.fetchall()

    cursor.close()
    conn.close()

    rows = apply_display_subpart_labels(rows)

    return rows

def collect_answer_images_from_rubric_rows(rubric_rows):
    """
    Collect official answer diagram images from marking scheme rows.
    Supports:
    - plain URL string
    - JSON string list: [{"url": "..."}]
    - JSON string dict: {"url": "..."}
    - Python list/dict if MySQL connector returns JSON directly
    """

    answer_images = []
    seen_urls = set()

    for row in rubric_rows:
        raw_value = row.get("answer_image_path")

        if not raw_value:
            continue

        # Convert MySQL JSON/string into Python object if possible
        parsed = raw_value

        if isinstance(raw_value, bytes):
            raw_value = raw_value.decode("utf-8")

        if isinstance(raw_value, str):
            raw_value = raw_value.strip()

            if not raw_value:
                continue

            try:
                parsed = json.loads(raw_value)
            except Exception:
                parsed = raw_value

        # Normalize to list
        if isinstance(parsed, list):
            image_items = parsed
        else:
            image_items = [parsed]

        original_part_label = build_original_part_label(row)
        # Use student-facing label for answer image matching.
        # Important if original is (c) but display is (a).
        part_label = row.get("display_subpart_label") or original_part_label

        for item in image_items:
            if isinstance(item, dict):
                url = (
                    item.get("url")
                    or item.get("answer_image_path")
                    or item.get("image_path")
                    or item.get("secure_url")
                    or ""
                )
                title = item.get("title") or f"Official answer diagram {part_label}".strip()
            else:
                url = str(item or "").strip()
                title = f"Official answer diagram {part_label}".strip()

            url = str(url or "").strip()

            if not url or url in seen_urls:
                continue

            seen_urls.add(url)

            answer_images.append({
                "subpart": part_label,
                "display_subpart_label": part_label,
                "original_subpart_label": original_part_label,
                "title": title,
                "url": url
            })

    return answer_images


def grade_new_question(
    question_image_base64,
    student_working_base64,
    language,
    confirmed_coordinates=None,
    coordinate_input=None,
    interpreted=None
):
    """
    Generates a bespoke rubric for an unseen question using RAG and a solved golden path, 
    then grades the student's working against it.
    """
    print("🔍 Extracting metadata from new question...")

    if isinstance(interpreted, dict) and interpreted:
        extracted_text = interpreted
    else:
        extracted_text = run_base_extractor(question_image_base64)

    extracted_text = normalize_topic_subtopic(extracted_text)
    extracted_text = normalize_extracted_for_rag(extracted_text)
    detected_question_text = build_question_text_from_interpreted(extracted_text)
    language = normalize_response_language(language)
    language_rules = get_response_language_rules(language)
    language_label = "Bahasa Melayu" if language == "bm" else "English"
    allocated_marks_raw = extracted_text.get("allocated_marks", {})
    diagram_type = str(extracted_text.get("diagram_type", "")).lower()
    question_text = str(detected_question_text).lower()
    
    if "venn" in diagram_type or "shade" in question_text or "lorek" in question_text:
        print("🔍 Shading detected. Applying OpenCV contrast enhancement...")
        student_working_base64 = enhance_shading_contrast(student_working_base64)
    total_marks = 0

    if isinstance(allocated_marks_raw, dict):
        for v in allocated_marks_raw.values():
            try:
                total_marks += float(v)
            except (TypeError, ValueError):
                pass
    else:
        try:
            total_marks = float(allocated_marks_raw)
        except (TypeError, ValueError):
            total_marks = 0
    allocated_marks = extracted_text.get("allocated_marks", {})
    total_marks = allocated_marks.get("total") or allocated_marks.get("subpart_marks") or 3 # Fallback to 3 if undetected
    print("📚 Fetching similar marking schemes via RAG...")
    rag_bundle = get_smart_rag_context(extracted_text, purpose="grade")
    rag_context = format_rag_context_for_llm(rag_bundle, purpose="grade")

    print("GRADING RAG MODE:", rag_bundle["mode"])
    print("STAGE SCORE:", rag_bundle.get("stage_score"))
    print("SUBPART SCORE:", rag_bundle.get("subpart_score"))
    
    is_exact_match = bool(rag_bundle.get("is_exact_match", False))

    if is_exact_match:
        print("⚡ EXACT MATCH FOUND! Bypassing generation and using official rubric.")
        print("EXACT MATCH TYPE:", rag_bundle.get("exact_match_type"))

        generated_rubric = rag_bundle.get("exact_rubric") or rag_context
    else:
        print("🧠 Solving the question to create a Golden Path...")
        # We reuse your excellent solver here!
        from solving.llm_engine import solve_new_question
        golden_solution = solve_new_question(
            question_image_base64,
            interpreted=extracted_text,
            confirmed_coordinates=confirmed_coordinates,
            coordinate_input=coordinate_input,
            language=language
        )

        if isinstance(golden_solution, dict) and golden_solution.get("needs_user_coordinates"):
            return {
                "status": "needs_user_coordinates",
                "needs_user_coordinates": True,
                "result_type": "coordinate_confirmation",
                "question_text": golden_solution.get(
                    "question_text",
                    "Transformation question needs exact coordinates"
                ),
                "reason": golden_solution.get(
                    "reason",
                    "Please enter the coordinates for the required points before grading."
                ),
                "coordinate_input": golden_solution.get("coordinate_input", {}),
                "pending_interpreted": extracted_text,
                "steps": [],
                "final_answers": {}
            }
        
        rubric_system_prompt = f"""
        You are a strict Malaysian SPM Mathematics curriculum designer.
        Your task is to convert the provided 'Golden Solution' into a strict JSON marking scheme.
        
        CRITICAL RULES:
        1. SPM MARKING STYLE (GRANULARITY): Do NOT lump multiple marks into a single step. You MUST strictly mimic the granular, step-by-step mark distribution seen in the provided 'SPM EXAMPLES' (e.g., separating method marks from final answer marks).
        2. THE ANTI-LAZY GUARDRAIL (CRITICAL): You are strictly FORBIDDEN from lumping multiple marks into a single step. You MUST generate at least 2 to 4 separate JSON objects in your array for a multi-mark question.
        3. THE ALLOCATED MARKS GUARDRAIL (CRITICAL): The total marks for this question is strictly {total_marks}. 
           You MUST generate exactly {total_marks} marks worth of steps. The sum of the `max_marks` for all steps in your JSON array MUST equal exactly {total_marks}.
        4. RAG SEPARATION GUARDRAIL: You must ONLY use the 'SMART RAG CONTEXT' to learn the *style* and *formatting* of SPM marking schemes. You are STRICTLY FORBIDDEN from copying any numbers, variables, or math from the RAG context. All mathematical truths MUST come entirely from the 'GOLDEN SOLUTION'.
        5. Output valid JSON ONLY.
        
        JSON SCHEMA:
        {{
            "rubric": [
                {{
                    "subpart": "e.g., a, b(i) or leave empty if none",
                    "step": "Specific milestone",
                    "max_marks": 1,
                    "required_keywords_or_math": ["The exact math equation or value to hunt for"],
                    "acceptable_alternative_methods": ["List any valid alternative mathematical workflows here"]
                }}
            ]
        }}
        """
        
        rubric_user_prompt = f"""
        SMART RAG CONTEXT FOR MARKING STYLE:
        {rag_context}
        
        ALLOCATED MARKS BREAKDOWN: 
        {json.dumps(allocated_marks_raw)}
        
        GOLDEN SOLUTION TO CONVERT:
        {json.dumps(golden_solution)}
        """

        print("📋 Converting Golden Solution to JSON rubric...")
        rubric_response = openai_client.chat.completions.create(
            model="gemini-3.5-flash-lite", 
            messages=[
                {"role": "system", "content": rubric_system_prompt},
                {"role": "user", "content": [{"type": "text", "text": rubric_user_prompt}]}
            ],
            temperature=0.1,
            response_format={"type": "json_object"}
        )
        generated_rubric = rubric_response.choices[0].message.content
        print(generated_rubric) # Log the generated rubric for debugging
        print("✅ Rubric Generated Successfully.")

    # ==========================================
    # STEP B: GRADE THE STUDENT WORKING
    # ==========================================
    grading_language_block = f"""
    STUDENT SELECTED LANGUAGE:
    {language_label}

    {language_rules}

    LANGUAGE OUTPUT RULE:
    Return all student-facing fields in {language_label}, including:
    - question_text
    - step
    - student_wrote
    - reason
    - summary_feedback if any

    Keep mathematical symbols, equations, variables, units, and LaTeX unchanged.
    """
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
    grading_system_prompt = GRAPH_AND_DRAWING_GRADING_RULES + grading_language_block + r"""
    You are a strict but fair Malaysian SPM Mathematics Examiner.
    Grade the attached student working using the provided JSON Marking Scheme as a baseline.

    CRITICAL GRADING RULES:
    1. THE ANTI-LAZY MAPPING (RELEVANT STEPS ONLY):
    You MUST output an evaluation object for EVERY step in the rubric that applies to the provided "QUESTION CONTEXT". 
    CRITICAL EXCEPTION: If the Marking Scheme includes steps for DIFFERENT questions or subparts NOT present in the student's question context, you MUST COMPLETELY IGNORE THEM. Do NOT add them to the stepwise_evaluation array, and do NOT count their marks towards the max_score.

    2. VISUAL DIAGRAM GRADING:
    If the rubric evaluates a drawing, graph, box plot, ogive, histogram, or geometry construction, visually inspect the drawn answer.

    3. MISSING WORKING:
    If the step requires text/math and none is found, write "No working shown" and award 0 marks.
    This rule is waived if the student provided a correct drawing instead.

    4. EQUATION HUNTING:
    Analyze every equation the student wrote and map it to the correct rubric step.

    5. VALID ALTERNATIVE METHOD:
    If the student's working does not match the rubric's primary method, check whether it is mathematically equivalent.
    Do not write "No working shown" if valid alternative math is present.

    6. UNIT PENALTY:
    If the numerical answer is correct but the unit is explicitly wrong, award 0 marks for that specific final-answer step.

    7. STRICT NUMERIC VERIFICATION:
    If the method is correct but the final calculated number is wrong, award method marks only if the rubric allows it.
    Do not award the final answer mark.

    8. NO "ERROR CARRIED FORWARD" (ECF) LENIENCY (CRITICAL):
    Do NOT award marks for "internal consistency". If a student makes an arithmetic, expansion, factorization, or substitution error, any subsequent equation derived from that error is mathematically invalid. You MUST verify their math line-by-line. If their equation does not match the rubric's required math because of a previous error, you MUST award 0 marks for that step.

    OUTPUT JSON ONLY.
    Return exactly this schema:

    {
    "math_verification_scratchpad": "Recalculate the student's math line-by-line. Compare it strictly against the rubric's required math. Explicitly flag any arithmetic or algebraic errors. State whether the student's step is a valid derivation or an invalid 'error carried forward'.",
    "question_text": "Short detected question summary copied from the question context if available. Never write AI Grading Report.",
    "stepwise_evaluation": [
        {
        "step": "Name of the step evaluated copied exactly from the rubric",
        "student_wrote": "The exact equation the student wrote, OR a description of where their drawing aligns. If missing, write No working shown.",
        "reason": "Explain why the mark was awarded or lost based on visual alignment or mathematical accuracy.",
        "marks_awarded": 0,
        "max_marks": 1
        }
    ],
    "score": 0,
    "max_score": 0,
    "summary_feedback": "Short feedback in the selected language."
    }
    """
    
    grading_user_prompt = f"""
STUDENT SELECTED LANGUAGE:
{language_label}

GENERATED RUBRIC:
{generated_rubric}

QUESTION CONTEXT:
{json.dumps(extracted_text, ensure_ascii=False, indent=2)}

Please grade the attached student working.

The response language must be {language_label}.
"""

    print("💯 Grading student working against generated rubric...")
    grading_response = openai_client.chat.completions.create(
        model="gemini-3.5-flash-lite",
        messages=[
            {"role": "system", "content": grading_system_prompt},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": grading_user_prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{student_working_base64}"}}
                ]
            }
        ],
        temperature=0,
        response_format={"type": "json_object"} # ✨ Enforces JSON output
    )
    raw_text = grading_response.choices[0].message.content
    print(raw_text) # Log the raw response for debugging
    grading_result = AgentOutputProcessor.process(raw_text)
    grading_result = enforce_unit_penalty(grading_result)

    grading_result["question_text"] = detected_question_text or "AI Grading Report"

    return grading_result



def grade_known_stage(student_image_base64, exercise_stage_id,language, question_ids=None):
    """
    Grades a student's answer for the current displayed exercise stage.
    The stage may contain multiple subparts.
    """

    rubric_rows = fetch_official_rubrics_for_stage(
        exercise_stage_id,
        question_ids=question_ids
    )

    if not rubric_rows:
        return {
            "success": False,
            "message": "No marking scheme found for this exercise stage."
        }
    language = normalize_response_language(language)
    language_rules = get_response_language_rules(language)
    language_label = "Bahasa Melayu" if language == "bm" else "English"
    official_rubrics = [row["raw_json"] for row in rubric_rows]
    answer_images = collect_answer_images_from_rubric_rows(rubric_rows)
    combined_rubric = "[\n" + ",\n".join(official_rubrics) + "\n]"

    question_context = [
        {
            "question_id": row["question_id"],
            "question_no": row["question_no"],

            # Original DB labels, used internally only
            "part": row["part"],
            "subpart": row["subpart"],
            "sub_subpart": row["sub_subpart"],
            "original_subpart_label": row.get("original_subpart_label", ""),

            # Student-facing label
            "display_subpart_label": row.get("display_subpart_label", ""),

            "instructions_en": row["instructions_en"],
            "instructions_ms": row["instructions_ms"],
            "sequence": row["sequence"],
            "table_data": row["table_data"],
            "given_values": row["given_values"],
            "image_path": row["image_path"],
        }
        for row in rubric_rows
    ]
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
    GRADE_KNOWN_SYSTEM_PROMPT = GRAPH_AND_DRAWING_GRADING_RULES + r"""
You are a strict but fair Malaysian SPM Mathematics examiner.

__LANGUAGE_RULES__

Your task is to grade the student's handwritten answer using ONLY the provided OFFICIAL MARKING SCHEME.

CRITICAL ROLE RULES:
1. You are NOT solving the question.
2. You are NOT generating a new solution.
3. You are only comparing the student's visible working against the official marking scheme.
4. The official marking scheme is the source of truth for marks, final answers, accepted methods, units, tolerances, and conditional rules.
5. The attached student image is the source of truth for what the student wrote or drew.

OFFICIAL ANSWER DIAGRAM RULE:
If official answer diagrams are provided, use them as visual reference for graph, box plot, histogram, ogive, construction, or shaded-region answers.
Compare the student's drawn answer against the official answer diagram and the official marking scheme.
Do not require written equations if the rubric expects a drawing.

RUBRIC USAGE RULES:
1. The official rubric is a JSON array. You MUST evaluate EVERY rubric object and EVERY marking step inside it.
2. Do not skip any subpart in the stage.
3. Grade each subpart separately.
4. Copy the step label from the rubric where possible.
5. Use the marks value from the rubric step as max_marks.
6. If a rubric object has no clear step list, create one evaluation item based on final_answer, answer_value, graph_validation, or drawing_validation.

MARKING RULES:
1. Award marks strictly based on mathematical correctness and the official rubric.
2. If the student uses a valid alternative method, award marks if it reaches the same mathematically correct result and does not violate method_policy.
3. If method_policy.working_required is true, do not award full marks for a final answer without sufficient working.
4. If method_policy.required_method is stated, only accept that method unless the rubric allows alternatives.
5. Apply rounding_and_tolerance if provided.
6. Apply conditional_marking_rules and notes when relevant.
7. Do not penalize harmless extra working unless it contradicts the answer.
8. If the student writes a correct method but wrong arithmetic final value, award method marks if the rubric allows it, but do not award final answer marks.

VISUAL ANSWER RULES:
1. If the answer is a graph, drawing, construction, histogram, ogive, box plot, or shaded region, visually inspect the student's image.
2. Do not require written equations for drawing/graph marks unless the rubric requires them.
3. Use graph_validation for plotted points, axes, curves, scales, shaded regions, and tolerances.
4. Use drawing_validation for shapes, dimensions, angles, construction lines, and allowed alternatives.

VENN DIAGRAM SHADING RULE:
For every Venn diagram shaded-region step, you MUST perform a strict visual audit.
IMPORTANT FOR SET / VENN SHADING:
For shaded-region steps, ignore any written set expression above or beside the diagram when deciding marks.
The written expression may be correct, but the diagram can still be wrong.
Grade only the visible shaded region inside the student diagram.
If the student writes the correct expression but shades the wrong or incomplete region, award 0 for the shaded-region mark.
In visual_audit.student_shaded_regions, describe only the visible shaded areas, not the written formula.
For each shaded-region step, identify:
1. official_image_used: the official answer diagram subpart label, e.g. "(b)(ii)".
2. student_diagram_checked: the student drawing label checked, e.g. "(b)(ii)".
3. required_shaded_regions: regions that must be shaded according to the official answer diagram/rubric.
4. student_shaded_regions: regions visibly shaded by the student.
5. missing_required_regions: required regions that are not shaded.
6. extra_wrong_regions: forbidden regions shaded by the student.
7. visual_match: true only if there are no missing_required_regions and no extra_wrong_regions.

STRICT MARK RULE:
- Award full marks for a Venn shaded-region step only when visual_match is true.
- If the student shades only part of a required region, visual_match must be false.
- If the student shades the wrong overlap or misses a required overlap, visual_match must be false.
- If the student image contains multiple Venn diagrams, use only the diagram with the same subpart label as the rubric step.
- Do not give marks just because the drawing looks similar.

EVIDENCE RULES:
1. Quote or summarize exactly what the student wrote.
2. If the working is not visible, write "No working shown".
3. If handwriting is unclear, write "Unclear / not legible" and award marks only if enough evidence is visible.
4. Do not invent student working.

DISPLAY SUBPART LABEL RULE:
- Each question_context item contains original_subpart_label and display_subpart_label.
- Use display_subpart_label as the student-facing label.
- Do not use original_subpart_label in student-facing output.
- If original_subpart_label is "(c)(i)" and display_subpart_label is "(a)(i)", show "(a)(i)".
- If original_subpart_label is "(c)(ii)" and display_subpart_label is "(a)(ii)", show "(a)(ii)".
- Do not flatten "(a)(i)" into "(a)".
- Do not convert "(c)(i)" and "(c)(ii)" into separate main parts like "(a)" and "(b)".
- In every step or stepwise_evaluation item, include the correct display_subpart_label exactly.

If the student's selected language is English.
Return all explanation text, step titles, reasons, and final answers in English only.

If the official marking scheme contains Bahasa Melayu, translate it into English.
Do not copy Malay wording unless the selected language is bm.

The "math" field must only contain mathematical expressions/equations.
If the answer is a word or sentence, put it in "text", not "math".

Do the same for if the student's selected language is Malay.

OUTPUT RULES:
Return ONLY valid JSON.
Do not include markdown.

JSON schema:
{
  "stepwise_evaluation": [
    {
      "subpart": "a, b, a(i), etc.",
      "display_subpart_label": "(a), (b)(i), etc.",
      "step": "Name of the marking step",
      "student_wrote": "Exact visible working or drawing description. Wrap math in $...$ where helpful.",
      "expected": "Expected answer, method, keyword, graph feature, or drawing feature from the rubric.",
      "reason": "Short reason why marks were awarded or lost.",
      "marks_awarded": 0,
      "max_marks": 1,
      "visual_audit": {
        "official_image_used": "",
        "student_diagram_checked": "",
        "required_shaded_regions": [],
        "intersection_checks": {
        "is_X_only_shaded": true,
        "is_X_intersect_Y_shaded": true,
        "is_Y_intersect_Z_shaded": false,
        "is_Z_only_shaded": true
        }
        "missing_required_regions": [],
        "extra_wrong_regions": [],
        "visual_match": false,

      }
    }
  ],
  "score": 0,
  "max_score": 0,
  "is_correct_for_adaptive": false,
  "summary_feedback": "Short student-friendly feedback. Do not reveal the full official solution."
}

ADAPTIVE CORRECTNESS RULE:
Set is_correct_for_adaptive to true only if score / max_score >= 0.8.
If max_score is 0, set is_correct_for_adaptive to false.
""".replace("__LANGUAGE_RULES__", language_rules)

    grading_user_prompt = f"""
STUDENT SELECTED LANGUAGE:
{language_label}
QUESTION CONTEXT:
{json.dumps(question_context, ensure_ascii=False, indent=2, default=str)}

OFFICIAL MARKING SCHEME JSON ARRAY:
{combined_rubric}

Please grade the attached student answer image against the official marking scheme.

Remember:
- Grade only.
- Do not generate a full solution.
- Do not reveal the full official answer.
- The response language must be {language_label}.
"""
    user_content = [
        {"type": "text", "text": grading_user_prompt}
    ]

    for img in answer_images:
        safe_img_url = format_image_for_llm(img["url"])

        if not safe_img_url:
            continue

        label = img.get("display_subpart_label") or img.get("subpart") or ""

        user_content.append({
            "type": "text",
            "text": (
                f"OFFICIAL ANSWER DIAGRAM FOR SUBPART {label}: "
                f"{img.get('title', '')}. "
                f"Use this image ONLY when grading the student's diagram labelled {label}. "
                f"Ignore this image for other subparts."
            )
        })

        user_content.append({
            "type": "image_url",
            "image_url": {"url": safe_img_url}
        })

    user_content.append({
        "type": "text",
        "text": "STUDENT ANSWER IMAGE TO GRADE:"
    })

    student_image_url = format_image_for_llm(student_image_base64)

    user_content.append({
        "type": "image_url",
        "image_url": {
            "url": student_image_url
        }
    })
    response = openai_client.chat.completions.create(
        model="gemini-3.5-flash-lite",
        messages=[
            {"role": "system", "content": GRADE_KNOWN_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": user_content
            }
        ],
        temperature=0.1,
        response_format={"type": "json_object"}
    )

    raw_text = response.choices[0].message.content
    print(raw_text)
    grading_result = AgentOutputProcessor.process(raw_text)

    grading_result = force_display_subpart_labels(grading_result, rubric_rows)


    return grading_result

def explain_known_question(image_base64, exercise_stage_id, language, question_ids=None):
    """
    Fetches the official rubric for a known DB question and uses the AI
    to expand it into a fully explained, pedagogical step-by-step solution.
    """
    print(f"🎓 Generating pedagogical solution for Exercise Stage {exercise_stage_id}...")
    language = normalize_response_language(language)
    language_rules = get_response_language_rules(language)
    language_label = "Bahasa Melayu" if language == "bm" else "English"
    rubric_rows = fetch_official_rubrics_for_stage(
        exercise_stage_id,
        question_ids=question_ids
    )
    answer_images = collect_answer_images_from_rubric_rows(rubric_rows)

    if not rubric_rows:
        return {
            "success": False,
            "message": "No marking scheme found for this exercise stage."
        }

    official_rubrics = [row["raw_json"] for row in rubric_rows]
    combined_rubric = "[\n" + ",\n".join(official_rubrics) + "\n]"

    question_context = [
        {
            "question_id": row["question_id"],
            "question_no": row["question_no"],

            # Original DB labels, used internally only
            "part": row["part"],
            "subpart": row["subpart"],
            "sub_subpart": row["sub_subpart"],
            "original_subpart_label": row.get("original_subpart_label", ""),

            # Student-facing label
            "display_subpart_label": row.get("display_subpart_label", ""),

            "instructions_en": row["instructions_en"],
            "instructions_ms": row["instructions_ms"],
            "sequence": row["sequence"],
            "table_data": row["table_data"],
            "given_values": row["given_values"],
            "image_path": row["image_path"],
        }
        for row in rubric_rows
    ]
    # 3. Prompt the LLM
    EXPLAIN_KNOWN_SYSTEM_PROMPT = r"""
    You are an expert, friendly Malaysian SPM Mathematics teacher.

    __LANGUAGE_RULES__

    Your task is to explain how to solve the given SPM Mathematics question step-by-step.

    SOURCE OF TRUTH RULES:
    1. The OFFICIAL MARKING SCHEME is the source of truth for the correct final answer, accepted method, required steps, units, tolerances, and graph/drawing requirements.
    2. The QUESTION TEXT and attached question image are the source of truth for the problem statement, diagram, table, and given values.
    3. If the marking scheme and your own calculation conflict, follow the marking scheme, but explain the steps clearly.
    4. Do not invent extra information that is not in the question or marking scheme.

    TEACHING STYLE RULES:
    1. Explain like a helpful SPM Mathematics teacher.
    2. Use simple, student-friendly language.
    3. Show why each formula or method is used.
    4. Break the solution into clear steps.
    5. For multi-subpart questions, solve each subpart separately and label them clearly.
    6. If a later subpart depends on an earlier subpart, explicitly mention that dependency.
    7. Keep the explanation concise but complete.
    8. Do not mention internal rubric IDs or database details.

    MATHEMATICS RULES:
    1. Use the official marking scheme to guide the solution structure.
    2. Show substituted values, not only formulas.
    3. For calculations, show the important working needed for SPM marks.
    4. Use correct units.
    5. Follow rounding_and_tolerance from the rubric.
    6. Accept equivalent forms only if mathematically valid.
    7. For graphs or drawings, explain what the student should draw/check instead of pretending it is a numerical calculation.
    8. For construction/graph questions, describe the required visual features clearly.

    DISPLAY SUBPART LABEL RULE:
    - Each question_context item contains original_subpart_label and display_subpart_label.
    - Use display_subpart_label as the student-facing label.
    - Do not use original_subpart_label in student-facing output.
    - If original_subpart_label is "(c)(i)" and display_subpart_label is "(a)(i)", show "(a)(i)".
    - If original_subpart_label is "(c)(ii)" and display_subpart_label is "(a)(ii)", show "(a)(ii)".
    - Do not flatten "(a)(i)" into "(a)".
    - Do not convert "(c)(i)" and "(c)(ii)" into separate main parts like "(a)" and "(b)".
    - In every step or stepwise_evaluation item, include the correct display_subpart_label exactly.

    OUTPUT RULES:
    Return ONLY valid JSON.
    Do not include markdown.
    Do not include explanations outside JSON.

    JSON schema:
    {
    "question_text": "Brief summary of the question.",
    "steps": [
        {
        "subpart": "a, b, a(i), etc.",
        "step": "Short step title",
        "text": "Clear explanation in words.",
        "math": "Only the working/calculation needed before the final answer. Do not put the final answer here if it is already shown in final_answers. If there is no useful working, leave this as an empty string. Do not wrap with $$."
        }
    ],
    "final_answers": {
        "(a)(i)": "Final answer for part (a)(i)",
        "(a)(ii)": "Final answer for part (a)(ii)",
        "(b)": "Final answer for part (b)"
    }
    "common_mistakes": [
        "One or two common mistakes students should avoid."
    ]
    }
    FINAL ANSWER KEY RULE:
    - The keys in final_answers must match display_subpart_label exactly.
    - Use "(a)(i)", "(a)(ii)", "(b)", "(c)" when those are the display labels.
    - Do not use only "a" when the actual display label is "(a)(i)".

    MATH FORMATTING:
    1. In the math field, put only math or calculation lines.
    2. Do not put long prose inside the math field.
    3. Use LaTeX such as \\frac, \\times, \\begin{aligned} where helpful.
    4. Escape JSON backslashes properly.
    5. For 1-mark subparts, put the final answer in final_answers, not in math.
    6. Do not put only the final answer in math. The math field is for working/calculation only.
    7. If the working would be exactly the same as the final answer, leave math as an empty string.
    8. Use valid LaTeX syntax such as x^2 or x^{2}, and \\frac{a}{b}. Never output /frac.
    """.replace("__LANGUAGE_RULES__", language_rules)

    explain_user_prompt = f"""
    STUDENT SELECTED LANGUAGE:
    {language_label}
    QUESTION DATA:
    {question_context}

    OFFICIAL MARKING SCHEME JSON ARRAY:
    {combined_rubric}

    Generate a student-friendly step-by-step solution.

    Important:
    - Your solution must match the official marking scheme.
    - Explain every subpart included in the rubric.
    - If the question has a diagram/table, use the attached image and question data to explain it properly.
    - The response language must be {language_label}.
    """

    safe_image_string = format_image_for_llm(image_base64)

    user_content = [
        {"type": "text", "text": explain_user_prompt}
    ]

    # Add official answer diagrams if available
    for img in answer_images:
        label = img.get("display_subpart_label") or img.get("subpart") or ""

        user_content.append({
            "type": "text",
            "text": (
                f"OFFICIAL ANSWER DIAGRAM FOR SUBPART {label}: "
                f"{img.get('title', '')}. "
                f"Use this image ONLY when grading the rubric step with the same subpart label. "
                f"If grading another subpart, ignore this image."
            )
        })

        user_content.append({
            "type": "image_url",
            "image_url": {"url": img["url"]}
        })

    # Add question image if available
    if safe_image_string:
        user_content.append({
            "type": "text",
            "text": "QUESTION IMAGE:"
        })
        user_content.append({
            "type": "image_url",
            "image_url": {"url": safe_image_string}
        })

    response = openai_client.chat.completions.create(
        model="gemini-3.5-flash-lite",
        messages=[
            {"role": "system", "content": EXPLAIN_KNOWN_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": user_content
            }
        ],
        temperature=0.1,
        response_format={"type": "json_object"}
    )

    raw_text = response.choices[0].message.content

    result = AgentOutputProcessor.process(raw_text)
    result = force_display_subpart_labels(result, rubric_rows)
    result["answer_images"] = answer_images

    return result

