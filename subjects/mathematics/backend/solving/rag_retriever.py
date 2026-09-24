import json
from solving.config import (
    aclient, index, RAG_NAMESPACE, get_db_connection,
    EXACT_MATCH_THRESHOLD, STAGE_HIGH_THRESHOLD, STAGE_MEDIUM_THRESHOLD
)

def safe_rag_text(value) -> str:
    """
    Converts strings, lists, dicts, numbers, and nested extracted fields
    into safe searchable text for RAG embedding.
    Prevents join errors when extractor returns structured objects.
    """
    if value is None:
        return ""

    if isinstance(value, str):
        return value

    if isinstance(value, (int, float, bool)):
        return str(value)

    if isinstance(value, dict):
        # Nice formatting for variable objects:
        # {"symbol": "x", "meaning": "number of five cent coins"}
        if "symbol" in value and "meaning" in value:
            return f"{value.get('symbol', '')}: {value.get('meaning', '')}"

        return json.dumps(value, ensure_ascii=False)

    if isinstance(value, list):
        return " ".join(
            safe_rag_text(item)
            for item in value
            if safe_rag_text(item)
        )

    return str(value)
def embed_text_for_rag(text: str) -> list:
    text = " ".join(str(text or "").split())

    response = aclient.embeddings.create(
        input=text,
        model="gemini-embedding-2-preview",
        dimensions=768
    )

    return response.data[0].embedding

def build_unseen_rag_search_text(extracted_dict: dict, mode: str = "subquestion") -> str:
    instructions_en = extracted_dict.get("instructions_en", [])
    instructions_ms = extracted_dict.get("instructions_ms", [])

    if isinstance(instructions_en, list):
        instructions_en = " ".join(str(x) for x in instructions_en)

    if isinstance(instructions_ms, list):
        instructions_ms = " ".join(str(x) for x in instructions_ms)

    equations = safe_rag_text(extracted_dict.get("equations", []))
    expressions = safe_rag_text(extracted_dict.get("expressions", []))
    variables = safe_rag_text(extracted_dict.get("variables", []))

    given_values = json.dumps(extracted_dict.get("given_values", {}), ensure_ascii=False)
    table_data = json.dumps(extracted_dict.get("table_data", {}), ensure_ascii=False)
    constraints = json.dumps(extracted_dict.get("constraints", {}), ensure_ascii=False)

    diagram_type = str(extracted_dict.get("diagram_type", ""))
    visual_summary = str(extracted_dict.get("visual_semantic_summary", ""))
    target = str(extracted_dict.get("target", ""))

    topic = str(extracted_dict.get("topic", ""))
    subtopic = str(extracted_dict.get("subtopic", ""))
    subparts_present = json.dumps(extracted_dict.get("subparts_present", []), ensure_ascii=False)

    if mode == "stage":
        text = f"""
        Stage-level SPM Mathematics question.

        English question:
        {instructions_en}

        Malay question:
        {instructions_ms}

        Subparts present:
        {subparts_present}

        Mathematical expressions:
        {equations}
        {expressions}

        Variables:
        {variables}

        Given values:
        {given_values}

        Table data:
        {table_data}

        Diagram type:
        {diagram_type}

        Visual context:
        {visual_summary}

        Constraints:
        {constraints}

        Target:
        {target}

        Topic hint:
        {topic}

        Subtopic hint:
        {subtopic}
        """
    else:
        text = f"""
        Subquestion-level SPM Mathematics question.

        English question:
        {instructions_en}

        Malay question:
        {instructions_ms}

        Mathematical expressions:
        {equations}
        {expressions}

        Variables:
        {variables}

        Given values:
        {given_values}

        Table data:
        {table_data}

        Diagram type:
        {diagram_type}

        Visual context:
        {visual_summary}

        Constraints:
        {constraints}

        Target:
        {target}

        Topic hint:
        {topic}

        Subtopic hint:
        {subtopic}
        """

    return " ".join(text.split())

def query_rag_by_granularity(
    extracted_dict: dict,
    granularity: str,
    top_k: int = 3,
    mode: str = "subquestion"
) -> list:
    search_text = build_unseen_rag_search_text(extracted_dict, mode=mode)
    vector = embed_text_for_rag(search_text)

    result = index.query(
        vector=vector,
        top_k=top_k,
        include_metadata=True,
        namespace=RAG_NAMESPACE,
        filter={
            "granularity": {"$eq": granularity}
        }
    )

    return result.get("matches", [])

def get_subpart_rag_context(extracted_dict: dict, top_k: int = 3) -> dict:
    matches = query_rag_by_granularity(
        extracted_dict=extracted_dict,
        granularity="subquestion",
        top_k=top_k,
        mode="subquestion"
    )

    if not matches:
        return {
            "context": "No similar subquestion examples found.",
            "matches": [],
            "best_score": 0,
            "is_exact": False
        }

    best_score = float(matches[0].get("score", 0) or 0)
    is_exact = best_score >= EXACT_MATCH_THRESHOLD

    conditions = []
    values = []

    for match in matches:
        meta = match.get("metadata", {}) or {}

        paper_id = int(meta.get("paper_id", 0) or 0)
        question_no = str(meta.get("question_no", "") or "").strip()
        part = str(meta.get("part", "") or "").strip()
        subpart = str(meta.get("subpart", "") or "").strip()
        sub_subpart = str(meta.get("sub_subpart", "") or "").strip()

        if paper_id and question_no:
            conditions.append("""
                (
                    q.paper_id = %s
                    AND q.question_no = %s
                    AND COALESCE(q.part, '') = %s
                    AND COALESCE(q.subpart, '') = %s
                    AND COALESCE(q.sub_subpart, '') = %s
                )
            """)
            values.extend([paper_id, question_no, part, subpart, sub_subpart])

    if not conditions:
        return {
            "context": "Similar subquestion vectors found, but metadata is incomplete.",
            "matches": matches,
            "best_score": best_score,
            "is_exact": is_exact
        }

    where_clause = " OR ".join(conditions)

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

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
            m.raw_json
        FROM questions q
        JOIN question_marking_links qml
            ON q.id = qml.question_id
        JOIN marking_schemes m
            ON qml.marking_scheme_id = m.id
        WHERE {where_clause}
        LIMIT %s
    """, tuple(values + [top_k * 5]))

    rows = cursor.fetchall()
    raw_rubrics = [
        row.get("raw_json")
        for row in rows
        if row.get("raw_json")
    ]
    combined_rubric = "[\n" + ",\n".join(raw_rubrics) + "\n]"
    cursor.close()
    conn.close()

    if not rows:
        return {
            "context": "No linked marking schemes found for similar subquestions.",
            "matches": matches,
            "best_score": best_score,
            "is_exact": is_exact
        }

    context = "\n\n=== SUBQUESTION RAG CONTEXT ===\n"

    for i, row in enumerate(rows, start=1):
        context += f"""
--- SUBQUESTION EXAMPLE {i} ---
Question ID: {row.get("question_id")}
Stage ID: {row.get("exercise_stage_id")}
Question: {row.get("question_no")} {row.get("part") or ""}{row.get("subpart") or ""}{row.get("sub_subpart") or ""}

QUESTION TEXT:
{row.get("instructions_en")}

SEQUENCE:
{row.get("sequence")}

TABLE DATA:
{row.get("table_data")}

GIVEN VALUES:
{row.get("given_values")}

OFFICIAL MARKING SCHEME:
{row.get("raw_json")}
"""

    return {
        "context": context,
        "matches": matches,
        "best_score": best_score,
        "is_exact": is_exact,
        "combined_rubric": combined_rubric
    }

def get_stage_rag_context(extracted_dict: dict, top_k: int = 2) -> dict:
    matches = query_rag_by_granularity(
        extracted_dict=extracted_dict,
        granularity="stage",
        top_k=top_k,
        mode="stage"
    )

    if not matches:
        return {
            "context": "No similar stage examples found.",
            "matches": [],
            "best_score": 0,
            "is_exact": False
        }

    best_score = float(matches[0].get("score", 0) or 0)
    is_exact = best_score >= EXACT_MATCH_THRESHOLD

    stage_ids = []

    for match in matches:
        meta = match.get("metadata", {}) or {}
        stage_id = str(meta.get("exercise_stage_id", "") or "").strip()

        if stage_id and stage_id not in stage_ids:
            stage_ids.append(stage_id)

    if not stage_ids:
        return {
            "context": "Similar stage vectors found, but exercise_stage_id metadata is missing.",
            "matches": matches,
            "best_score": best_score,
            "is_exact": is_exact
        }

    placeholders = ", ".join(["%s"] * len(stage_ids))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

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
            m.raw_json
        FROM questions q
        JOIN question_marking_links qml
            ON q.id = qml.question_id
        JOIN marking_schemes m
            ON qml.marking_scheme_id = m.id
        WHERE q.exercise_stage_id IN ({placeholders})
        ORDER BY
            q.exercise_stage_id,
            q.question_no + 0,
            q.part,
            q.subpart,
            q.sub_subpart
    """, tuple(stage_ids))

    rows = cursor.fetchall()
    raw_rubrics = [
    row.get("raw_json")
    for row in rows
    if row.get("raw_json")
    ]

    combined_rubric = "[\n" + ",\n".join(raw_rubrics) + "\n]"
    cursor.close()
    conn.close()

    if not rows:
        return {
            "context": "No linked marking schemes found for similar stages.",
            "matches": matches,
            "best_score": best_score,
            "is_exact": is_exact,
        }

    context = "\n\n=== STAGE RAG CONTEXT ===\n"
    current_stage_id = None

    for i, row in enumerate(rows, start=1):
        stage_id = row.get("exercise_stage_id")

        if stage_id != current_stage_id:
            current_stage_id = stage_id
            context += f"\n\n--- STAGE EXAMPLE: {stage_id} ---\n"

        context += f"""
Subpart Row {i}
Question ID: {row.get("question_id")}
Question: {row.get("question_no")} {row.get("part") or ""}{row.get("subpart") or ""}{row.get("sub_subpart") or ""}

QUESTION TEXT:
{row.get("instructions_en")}

SEQUENCE:
{row.get("sequence")}

TABLE DATA:
{row.get("table_data")}

GIVEN VALUES:
{row.get("given_values")}

OFFICIAL MARKING SCHEME:
{row.get("raw_json")}
"""

    return {
        "context": context,
        "matches": matches,
        "best_score": best_score,
        "is_exact": is_exact,
        "combined_rubric": combined_rubric
    }

def has_explicit_subparts(extracted: dict) -> bool:
    subparts = extracted.get("subparts_present", [])

    if not isinstance(subparts, list):
        return False

    cleaned = [
        str(x).strip().lower()
        for x in subparts
        if str(x).strip()
    ]

    # If extractor says ["total"] or empty, treat as no subparts
    if not cleaned:
        return False

    if cleaned == ["total"]:
        return False

    return True

def has_shared_stage_context(extracted: dict) -> bool:
    subparts = extracted.get("subparts_present", []) or []
    table_data = extracted.get("table_data", {}) or {}
    diagram_type = str(extracted.get("diagram_type", "") or "").strip()
    visual_summary = str(extracted.get("visual_semantic_summary", "") or "").strip()

    return (
        len(subparts) >= 2
        or bool(table_data)
        or bool(diagram_type)
        or bool(visual_summary)
    )



def get_rag_strength(rag_bundle: dict) -> str:
    if rag_bundle.get("is_exact_match"):
        return "exact"

    stage_score = float(rag_bundle.get("stage_score") or 0)
    subpart_score = float(rag_bundle.get("subpart_score") or 0)
    best_score = max(stage_score, subpart_score)

    if best_score >= 0.90:
        return "strong_method"

    if best_score >= STAGE_HIGH_THRESHOLD:
        return "high_method"

    if best_score >= STAGE_MEDIUM_THRESHOLD:
        return "weak_method"

    return "ignore"


def build_rag_usage_contract(rag_bundle: dict, purpose: str = "solve") -> str:
    rag_strength = get_rag_strength(rag_bundle)

    if purpose == "solve":
        return f"""
==============================
RAG USAGE CONTRACT
==============================

RAG strength: {rag_strength}

You MUST follow this policy:

1. If RAG strength is "exact":
   - Treat the official marking scheme in RAG as the authoritative solution.
   - Follow the official method, final answer, units, rounding, and subpart structure.
   - Still check the uploaded image for confirmation.

2. If RAG strength is "strong_method" or "high_method":
   - Use RAG as an important method reference.
   - Identify reusable method patterns, special conditions, hidden rules, subpart dependencies, and SPM marking style.
   - Do NOT copy numerical answers from RAG unless the uploaded question is exactly the same.
   - If RAG contains a condition that also appears in the uploaded question, apply that condition.
   - Examples of conditions: service tax only on excess usage, deductible, co-insurance, prorated block, rounding rule, graph-reading convention, diagram-boundary rule.

3. If RAG strength is "weak_method":
   - Use RAG only as light guidance.
   - Do not force the RAG method if the uploaded image is different.

4. If RAG strength is "ignore":
   - Ignore RAG for solving.
   - Solve directly from the uploaded image.

Before writing the final JSON, verify:
- Did I solve every subpart in the uploaded question?
- Did I use the uploaded image as the source of values?
- Did I apply any relevant special condition from RAG?
- Did I avoid copying unrelated RAG numbers?
"""
    
    return f"""
==============================
RAG USAGE CONTRACT
==============================

RAG strength: {rag_strength}

For grading:
- If exact, use the official marking scheme as the source of truth.
- If strong/high, use RAG mainly for SPM marking granularity and acceptable alternatives.
- If weak, use RAG only as light reference.
- If ignore, grade mainly from the generated rubric and uploaded student work.
"""

def get_smart_rag_context(extracted: dict, purpose: str = "solve") -> dict:
    """
    purpose:
    - "solve": solve unseen uploaded question
    - "grade": grade unseen student working
    """

    def build_bundle(
        mode,
        context,
        stage=None,
        subpart=None,
        stage_score=None,
        subpart_score=None,
        is_exact_match=False,
        exact_match_type=None,
        exact_rubric=None
    ):
        return {
            "mode": mode,
            "context": context,
            "stage": stage,
            "subpart": subpart,
            "stage_score": stage_score,
            "subpart_score": subpart_score,
            "is_exact_match": is_exact_match,
            "exact_match_type": exact_match_type,
            "exact_rubric": exact_rubric
        }

    has_subparts = has_explicit_subparts(extracted)

    # ==================================================
    # CASE 1: No explicit subparts
    # Use subquestion RAG directly
    # ==================================================
    if not has_subparts:
        subpart_rag = get_subpart_rag_context(extracted, top_k=3)
        subpart_score = float(subpart_rag.get("best_score", 0) or 0)

        return build_bundle(
            mode="single_question_subpart_only",
            context=subpart_rag["context"],
            stage=None,
            subpart=subpart_rag,
            stage_score=None,
            subpart_score=subpart_score,
            is_exact_match=subpart_score >= EXACT_MATCH_THRESHOLD,
            exact_match_type="subpart" if subpart_score >= EXACT_MATCH_THRESHOLD else None,
            exact_rubric=subpart_rag.get("combined_rubric") if subpart_score >= EXACT_MATCH_THRESHOLD else None
        )

    # ==================================================
    # CASE 2: Has subparts
    # Stage-first logic
    # ==================================================
    stage_rag = get_stage_rag_context(extracted, top_k=2)
    stage_score = float(stage_rag.get("best_score", 0) or 0)
    shared_context = has_shared_stage_context(extracted)

    print("STAGE RAG SCORE:", stage_score)

    # Exact stage match
    if stage_score >= EXACT_MATCH_THRESHOLD:
        return build_bundle(
            mode="stage_exact",
            context=stage_rag["context"],
            stage=stage_rag,
            subpart=None,
            stage_score=stage_score,
            subpart_score=None,
            is_exact_match=True,
            exact_match_type="stage",
            exact_rubric=stage_rag.get("combined_rubric", "")
        )

    # ==================================================
    # SOLVE MODE
    # ==================================================
    if purpose == "solve":
        if stage_score >= STAGE_HIGH_THRESHOLD:
            return build_bundle(
                mode="stage_only",
                context=stage_rag["context"],
                stage=stage_rag,
                subpart=None,
                stage_score=stage_score,
                subpart_score=None
            )

        if shared_context and stage_score >= STAGE_MEDIUM_THRESHOLD:
            subpart_rag = get_subpart_rag_context(extracted, top_k=2)
            subpart_score = float(subpart_rag.get("best_score", 0) or 0)

            combined_context = f"""
STAGE RAG CONTEXT:
Use this for full-question structure, shared diagram/table context, and subpart dependency.
{stage_rag["context"]}

SUBQUESTION RAG CONTEXT:
Use this only as extra method guidance for similar smaller parts.
{subpart_rag["context"]}
"""

            return build_bundle(
                mode="stage_plus_subpart",
                context=combined_context,
                stage=stage_rag,
                subpart=subpart_rag,
                stage_score=stage_score,
                subpart_score=subpart_score,
                is_exact_match=subpart_score >= EXACT_MATCH_THRESHOLD,
                exact_match_type="subpart" if subpart_score >= EXACT_MATCH_THRESHOLD else None,
                exact_rubric=subpart_rag.get("combined_rubric") if subpart_score >= EXACT_MATCH_THRESHOLD else None
            )

        subpart_rag = get_subpart_rag_context(extracted, top_k=3)
        subpart_score = float(subpart_rag.get("best_score", 0) or 0)

        return build_bundle(
            mode="subpart_only",
            context=subpart_rag["context"],
            stage=stage_rag,
            subpart=subpart_rag,
            stage_score=stage_score,
            subpart_score=subpart_score,
            is_exact_match=subpart_score >= EXACT_MATCH_THRESHOLD,
            exact_match_type="subpart" if subpart_score >= EXACT_MATCH_THRESHOLD else None,
            exact_rubric=subpart_rag.get("combined_rubric") if subpart_score >= EXACT_MATCH_THRESHOLD else None
        )

    # ==================================================
    # GRADE MODE
    # ==================================================
    if purpose == "grade":
        subpart_rag = get_subpart_rag_context(extracted, top_k=3)
        subpart_score = float(subpart_rag.get("best_score", 0) or 0)

        # Exact subpart match is very useful for grading
        if subpart_score >= EXACT_MATCH_THRESHOLD:
            return build_bundle(
                mode="subpart_exact_for_grading",
                context=subpart_rag["context"],
                stage=stage_rag,
                subpart=subpart_rag,
                stage_score=stage_score,
                subpart_score=subpart_score,
                is_exact_match=True,
                exact_match_type="subpart",
                exact_rubric=subpart_rag.get("combined_rubric", "")
            )

        if shared_context and stage_score >= STAGE_MEDIUM_THRESHOLD:
            combined_context = f"""
STAGE RAG CONTEXT:
Use this for full-question context, shared diagram/table data, and dependency between subparts.
{stage_rag["context"]}

SUBQUESTION RAG CONTEXT:
Use this mainly for marking scheme granularity, method marks, answer marks, and acceptable alternatives.
{subpart_rag["context"]}
"""

            return build_bundle(
                mode="stage_plus_subpart_for_grading",
                context=combined_context,
                stage=stage_rag,
                subpart=subpart_rag,
                stage_score=stage_score,
                subpart_score=subpart_score
            )

        return build_bundle(
            mode="subpart_only_for_grading",
            context=subpart_rag["context"],
            stage=stage_rag,
            subpart=subpart_rag,
            stage_score=stage_score,
            subpart_score=subpart_score
        )

    # Safety fallback
    subpart_rag = get_subpart_rag_context(extracted, top_k=3)
    subpart_score = float(subpart_rag.get("best_score", 0) or 0)

    return build_bundle(
        mode="fallback_subpart_only",
        context=subpart_rag["context"],
        stage=stage_rag,
        subpart=subpart_rag,
        stage_score=stage_score,
        subpart_score=subpart_score
    )


def format_rag_context_for_llm(rag_bundle: dict, purpose: str = "solve") -> str:
    """
    Adds instructions so the LLM understands how to use stage RAG vs subquestion RAG.
    """

    mode = rag_bundle.get("mode", "")
    stage_score = rag_bundle.get("stage_score")
    subpart_score = rag_bundle.get("subpart_score")
    exact_match = rag_bundle.get("is_exact_match", False)
    exact_type = rag_bundle.get("exact_match_type")

    raw_context = rag_bundle.get("context", "")
    rag_strength = get_rag_strength(rag_bundle)
    rag_contract = build_rag_usage_contract(rag_bundle, purpose)
    if purpose == "solve":
        purpose_rules = """
SOLVING USAGE RULES:
- The uploaded question image is always the source of truth.
- Use STAGE RAG to understand the full-question method, shared diagram/table context, and dependency between subparts.
- Use SUBQUESTION RAG only as supporting method guidance for similar smaller parts.
- Do not copy numerical answers from RAG unless the question is clearly an exact match.
- If RAG conflicts with the uploaded image, follow the uploaded image.
"""
    else:
        purpose_rules = """
GRADING USAGE RULES:
- The uploaded student working image is the source of truth for what the student wrote.
- Use SUBQUESTION RAG mainly to imitate SPM marking granularity, method marks, answer marks, and acceptable alternatives.
- Use STAGE RAG to understand shared context, diagrams, tables, and dependency between subparts.
- Do not copy answers from RAG unless the question is clearly an exact match.
- If RAG conflicts with the uploaded question image, follow the uploaded question image.
"""

    return f"""
==============================
RAG RETRIEVAL GUIDE
==============================

RAG mode selected by backend: {mode}
RAG strength: {rag_strength}
Stage similarity score: {stage_score}
Subquestion similarity score: {subpart_score}
Exact match detected: {exact_match}
Exact match type: {exact_type}

Meaning of RAG sections:
1. STAGE RAG CONTEXT
   - Retrieved from a whole exercise stage.
   - May contain the introductory paragraph, shared table, shared diagram, and multiple subparts.
   - Best for understanding overall question flow and subpart dependency.

2. SUBQUESTION RAG CONTEXT
   - Retrieved from individual subquestions/subparts.
   - Best for understanding local solving method and marking scheme style.
   - More useful for rubric generation and grading granularity.

{purpose_rules}

{rag_contract}
==============================
RETRIEVED RAG CONTEXT
==============================
{raw_context}
"""
