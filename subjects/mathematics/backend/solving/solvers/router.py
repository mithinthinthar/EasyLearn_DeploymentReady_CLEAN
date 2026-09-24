import json

from solving.config import EXACT_MATCH_THRESHOLD
from solving.rag_retriever import format_rag_context_for_llm, get_rag_strength, get_subpart_rag_context
from solving.solvers.geometry import solve_circle_geometry, solve_polygon_geometry, solve_loci_geometry
from solving.solvers.logics import solve_logical_reasoning
from solving.solvers.mensuration import solve_mensuration
from solving.solvers.graphs import solve_visual_graphs
from solving.solvers.proabability import solve_probability
from solving.solvers.sets_logic import solve_sets_venn
from solving.solvers.statistics import solve_statistics
from solving.solvers.transformations import solve_transformations
from solving.solvers.trigonometry import solve_trigonometry
from solving.solvers.matrices import solve_matrix_math
from solving.solvers.finance import solve_financial_management, solve_taxation_math, solve_insurance_math
from solving.solvers.general import solve_general_math


def get_ordered_subpart_labels(interpreted: dict) -> list:
    subpart_classification = interpreted.get("subpart_classification", {}) or {}
    subparts_present = interpreted.get("subparts_present", []) or []

    ordered = []

    for label in subparts_present:
        label = str(label).strip()
        if label in subpart_classification and label not in ordered:
            ordered.append(label)

    # Add any extra labels not listed in subparts_present
    for label in subpart_classification.keys():
        if label not in ordered:
            ordered.append(label)

    return ordered

def build_subpart_rag_bundle_for_score(subpart_score: float, subpart_rag: dict) -> dict:
    return {
        "mode": "subpart_specific",
        "context": subpart_rag.get("context", ""),
        "stage": None,
        "subpart": subpart_rag,
        "stage_score": None,
        "subpart_score": subpart_score,
        "is_exact_match": subpart_score >= EXACT_MATCH_THRESHOLD,
        "exact_match_type": "subpart" if subpart_score >= EXACT_MATCH_THRESHOLD else None,
        "exact_rubric": subpart_rag.get("combined_rubric") if subpart_score >= EXACT_MATCH_THRESHOLD else None
    }


def get_subpart_rag_contexts_by_label(interpreted: dict, top_k: int = 2) -> dict:
    subpart_classification = interpreted.get("subpart_classification", {})

    if not isinstance(subpart_classification, dict) or len(subpart_classification) < 2:
        return {}

    result = {}

    for subpart_label in get_ordered_subpart_labels(interpreted):
        subpart_info = subpart_classification.get(subpart_label, {})

        if not isinstance(subpart_info, dict):
            continue

        focused_interpreted = build_interpreted_for_one_subpart(
            interpreted=interpreted,
            subpart_label=subpart_label,
            subpart_info=subpart_info,
            previous_answers={}
        )

        subpart_rag = get_subpart_rag_context(
            focused_interpreted,
            top_k=top_k
        )

        subpart_score = float(subpart_rag.get("best_score", 0) or 0)

        mini_bundle = build_subpart_rag_bundle_for_score(
            subpart_score,
            subpart_rag
        )

        result[subpart_label] = {
            "score": subpart_score,
            "strength": get_rag_strength(mini_bundle),
            "is_exact": subpart_score >= EXACT_MATCH_THRESHOLD,
            "context": subpart_rag.get("context", ""),
            "combined_rubric": subpart_rag.get("combined_rubric", "")
        }

    return result

def format_subpart_rag_contexts_by_label(subpart_rag_by_label: dict) -> str:
    if not isinstance(subpart_rag_by_label, dict) or not subpart_rag_by_label:
        return ""

    text = """

==============================
SUBPART-SPECIFIC RAG MAP
==============================

The following RAG contexts were retrieved separately for each uploaded subpart.
Use each context ONLY for its matching uploaded subpart.
Do not apply one subpart's RAG method blindly to another subpart.
"""

    for label, data in subpart_rag_by_label.items():
        score = float(data.get("score", 0) or 0)
        strength = data.get("strength", "ignore")

        text += f"""

--- UPLOADED SUBPART {label} ---
Subpart-specific RAG score: {score}
Subpart-specific RAG strength: {strength}

SUBPART RAG USAGE RULE:
This RAG context follows the same RAG USAGE CONTRACT as the main RAG.
However, it is scoped ONLY to uploaded subpart {label}.
Do not use this subpart's RAG context to solve other subparts.
If it conflicts with the uploaded image or previous_subpart_answers, follow the uploaded image and previous_subpart_answers.

Usage rule:
- Use this context only for subpart {label}.
- Use the uploaded image for actual values.
- Do not copy RAG numbers unless it is an exact match.
"""

        if strength == "ignore":
            text += """
Retrieved context is weak, so ignore it unless it clearly matches the uploaded subpart.
"""
        else:
            text += f"""
{subpart_rag_by_label[label].get("context", "")}
"""

    return text

def build_subpart_rag_bundle(focused_interpreted: dict, subpart_label: str, top_k: int = 2) -> dict:
    subpart_rag = get_subpart_rag_context(focused_interpreted, top_k=top_k)
    subpart_score = float(subpart_rag.get("best_score", 0) or 0)

    return {
        "mode": f"subpart_specific_{subpart_label}",
        "context": subpart_rag.get("context", ""),
        "stage": None,
        "subpart": subpart_rag,
        "stage_score": None,
        "subpart_score": subpart_score,
        "is_exact_match": subpart_score >= EXACT_MATCH_THRESHOLD,
        "exact_match_type": "subpart" if subpart_score >= EXACT_MATCH_THRESHOLD else None,
        "exact_rubric": subpart_rag.get("combined_rubric") if subpart_score >= EXACT_MATCH_THRESHOLD else None
    }

def build_interpreted_for_one_subpart(
    interpreted: dict,
    subpart_label: str,
    subpart_info: dict,
    previous_answers: dict
) -> dict:
    focused = dict(interpreted)

    focused["topic"] = subpart_info.get("topic", interpreted.get("topic", ""))
    focused["subtopic"] = subpart_info.get("subtopic", interpreted.get("subtopic", ""))

    focused["solve_only_subpart"] = subpart_label
    focused["subparts_present"] = [subpart_label]
    focused["previous_subpart_answers"] = previous_answers

    instruction_en = str(subpart_info.get("instruction_en", "")).strip()
    instruction_ms = str(subpart_info.get("instruction_ms", "")).strip()

    if instruction_en:
        focused["instructions_en"] = [instruction_en]

    if instruction_ms:
        focused["instructions_ms"] = [instruction_ms]

    focused["target"] = instruction_en or instruction_ms or interpreted.get("target", "")

    # Keep shared context because subparts usually depend on the same table/diagram
    focused["given_values"] = interpreted.get("given_values", {})
    focused["constraints"] = interpreted.get("constraints", {})
    focused["table_data"] = interpreted.get("table_data", {})
    focused["diagram_data"] = interpreted.get("diagram_data", {})
    focused["visual_semantic_summary"] = interpreted.get("visual_semantic_summary", "")
    focused["introductory_instructions_ms"] = interpreted.get("introductory_instructions_ms", "")

    return focused

def solve_mixed_stage_single_pass(
    image_base64,
    interpreted,
    stage_rag_data,
    subpart_rag_by_label
):
    """
    Solves a mixed-topic multi-subpart question in ONE LLM call.
    Uses subpart-specific RAG only as method guidance.
    """

def solve_mixed_stage_with_dependencies(image_base64, interpreted, rag_data, language):
    subpart_classification = interpreted.get("subpart_classification", {}) or {}

    merged_result = {
        "question_text": interpreted.get("target", ""),
        "steps": [],
        "final_answers": {},
        "subpart_solver_audit": []
    }

    previous_answers = {}
    ordered_labels = get_ordered_subpart_labels(interpreted)

    for subpart_label in ordered_labels:
        subpart_info = subpart_classification.get(subpart_label, {})

        if not isinstance(subpart_info, dict):
            continue

        focused_interpreted = build_interpreted_for_one_subpart(
            interpreted=interpreted,
            subpart_label=subpart_label,
            subpart_info=subpart_info,
            previous_answers=previous_answers
        )

        topic = focused_interpreted.get("topic", "")
        subtopic = focused_interpreted.get("subtopic", "")
        solver_fn = route_solver_for_subpart(topic, subtopic)

        subpart_rag_bundle = build_subpart_rag_bundle(
            focused_interpreted,
            subpart_label,
            top_k=2
        )

        subpart_rag_data = format_rag_context_for_llm(
            subpart_rag_bundle,
            purpose="solve"
        )

        focused_rag_data = rag_data + f"""

        ==============================
        SUBPART-SPECIFIC RAG CONTEXT
        ==============================
        The following RAG context was retrieved specifically for uploaded subpart {subpart_label}.
        Use it mainly for this subpart only.

        {subpart_rag_data}

        ==============================
        CURRENT SUBPART FOCUS
        ==============================
        Solve ONLY subpart {subpart_label}.

        Do not solve other subparts unless needed to understand dependency.

        Previous subpart answers:
        {json.dumps(previous_answers, ensure_ascii=False, indent=2)}

        Dependency rule:
        - If this subpart depends on an earlier answer, use the value from Previous subpart answers.
        - Do not change previous answers unless there is a clear arithmetic inconsistency.
        - Keep the original full image as the source of truth for shared tables, diagrams, and values.
        """

        sub_result = solver_fn(
            image_base64,
            focused_interpreted,
            focused_rag_data,
            language=language
        )

        # Merge steps
        sub_steps = sub_result.get("steps", [])
        if isinstance(sub_steps, list):
            for step in sub_steps:
                if isinstance(step, dict):
                    step["subpart"] = subpart_label
                    merged_result["steps"].append(step)

        # Merge final answer
        sub_final = sub_result.get("final_answers") or sub_result.get("final_answer") or ""

        if isinstance(sub_final, dict):
            answer_value = (
                sub_final.get(subpart_label)
                or sub_final.get(subpart_label.replace("(", "").replace(")", ""))
                or next(iter(sub_final.values()), "")
            )
        else:
            answer_value = sub_final

        previous_answers[subpart_label] = answer_value
        merged_result["final_answers"][subpart_label] = answer_value

        merged_result["subpart_solver_audit"].append({
            "subpart": subpart_label,
            "topic": topic,
            "subtopic": subtopic,
            "solver": solver_fn.__name__,
            "depends_on": subpart_info.get("depends_on", []),
            "subpart_rag_mode": subpart_rag_bundle.get("mode"),
            "subpart_rag_score": subpart_rag_bundle.get("subpart_score"),
            "subpart_rag_strength": get_rag_strength(subpart_rag_bundle),
            "subpart_rag_exact": subpart_rag_bundle.get("is_exact_match"),
            "previous_answers_available": dict(previous_answers)
        })

    return merged_result

def route_solver_for_subpart(topic: str, subtopic: str):
    """Semantic router that points a topic to its specialized Python agent."""
    if subtopic in ["Angles and Tangents of Circles", "Circles"]:
        return solve_circle_geometry

    if topic in ["Mensuration", "3D Geometry"]:
        return solve_mensuration

    if topic in ["Functions and Graphs", "Coordinate Geometry", "Graph Theory"]:
        return solve_visual_graphs

    if topic == "Geometry" and subtopic in ["Polygons", "Lines and Angles"]:
        return solve_polygon_geometry

    if topic == "Geometry" and subtopic == "Loci in Two Dimensions":
        return solve_loci_geometry

    if topic == "Probability":
        return solve_probability
    
    if topic == "Logical Reasoning":
        return solve_logical_reasoning
    
    if topic == "Sets and Logic":
        return solve_sets_venn
    
    if topic == "Statistics":
        return solve_statistics

    if topic == "Transformations":
        return solve_transformations
    
    if topic == "Trigonometry":
        return solve_trigonometry

    if topic == "Matrices":
        return solve_matrix_math
    
    if subtopic == "Savings and Investments" or subtopic == "Credit and Debt":
        return solve_financial_management
    
    if subtopic == "Taxation":
        return solve_taxation_math

    if subtopic == "Insurance":
        return solve_insurance_math

    return solve_general_math

def should_use_mixed_subpart_solver(interpreted: dict) -> bool:
    """Checks if a question mixes multiple topics requiring different agents."""
    subpart_classification = interpreted.get("subpart_classification", {})

    if not isinstance(subpart_classification, dict) or len(subpart_classification) < 2:
        return False

    solvers_needed = set()

    for info in subpart_classification.values():
        if not isinstance(info, dict):
            continue

        topic = str(info.get("topic", "")).strip()
        subtopic = str(info.get("subtopic", "")).strip()

        if topic and subtopic:
            solver_fn = route_solver_for_subpart(topic, subtopic)
            solvers_needed.add(solver_fn.__name__)

    return len(solvers_needed) > 1