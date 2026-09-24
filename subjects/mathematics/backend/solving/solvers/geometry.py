import os
import json
from langchain_openai import ChatOpenAI
from langchain_classic.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import SystemMessage

from solving.format_json import AgentOutputProcessor
from solving.utils import prepare_solver_payload
from solving.math_tools import calculate_expression, coordinate_geometry_tool, geometry_mensuration_tool, solve_equations_tool

def solve_polygon_geometry(new_question_image_base64, interpreted, rag_data, language):
    solver_payload = prepare_solver_payload(interpreted)
    language_code = str(language or "english").lower()

    if language_code in ["bm", "ms", "malay", "bahasa_melayu", "bahasa melayu"]:
        language_label = "Bahasa Melayu"
    else:
        language_label = "English"

    language_rule = f"""
RESPONSE LANGUAGE RULE:
The selected response language is: {language_label}.

If the selected response language is Bahasa Melayu:
- Write question_text, step titles, explanations, reasons, and final answer text in Bahasa Melayu.
- Keep mathematical symbols, variables, equations, units, and LaTeX unchanged.
- Use SPM-style Malay terms where suitable.
- Do not mix English explanation unless the term is normally used in SPM.

If the selected response language is English:
- Write question_text, step titles, explanations, reasons, and final answer text in English.
- Keep mathematical symbols, variables, equations, units, and LaTeX unchanged.
"""
    system_prompt = language_rule + r"""
You are an expert Malaysian SPM Mathematics teacher specialising in plane geometry, polygons, and lines and angles.

Your task is to solve the attached question image step-by-step.

RAG USAGE RULE:
You MUST read the RAG USAGE CONTRACT inside the user prompt before solving.
If RAG strength is exact, follow the official marking scheme.
If RAG strength is strong_method or high_method, use RAG as an important method reference but use the uploaded image for actual values.
If RAG strength is weak_method, use RAG only as light guidance.
If RAG strength is ignore, do not use RAG for solving.

GENERAL GEOMETRY REASONING RULES:
1. The image is the source of truth.
2. Before calculating, identify all marked angles and classify each angle as:
   - interior angle of the polygon
   - exterior angle
   - angle on a straight line
   - right angle
   - unknown angle
3. For polygon interior-angle-sum equations:
   - Count the number of polygon vertices.
   - Use only angles that are inside the polygon.
   - Include exactly one interior angle for each vertex.
   - Do not include exterior angles in the polygon interior-angle sum.
4. For straight-line angle equations:
   - Only use angles that share the same vertex and lie on the same straight line.
   - Adjacent angles on a straight line sum to 180 degrees.
5. If an exterior angle is given or required, first relate it to its adjacent interior angle using the straight-line rule.
6. Never replace an interior polygon angle with its exterior angle.
7. Before solving, write an angle audit showing which angles are used in which equation.
8. Use tools for arithmetic and solving equations.
9. SPM ANGLE TERMINOLOGY (CRITICAL): When a question asks you to NAME the type of angle or the relationship between two angles based on their sum, you MUST use these exact SPM formal terms:
   - If the sum is 90°: Answer "Complementary angles" (Sudut pelengkap).
   - If the sum is 180°: Answer "Supplementary angles" (Sudut penggenap). You are FORBIDDEN from just answering "angle on a straight line" for this type of specific naming question.
   - If the sum is 360°: Answer "Conjugate angles" (Sudut konjugat).
10. DIMENSION PLACEMENT TRAP (CRITICAL): Pay extremely close attention to exactly where numbers are placed on a diagram. If a length (e.g., "28 cm") is written directly on ONE specific segment of a bisected line or diagonal (e.g., from the center intersection to a vertex), it represents the length of THAT specific segment ONLY. You are STRICTLY FORBIDDEN from dividing it by 2 unless the question text explicitly states it is the full length.
OUTPUT JSON SCHEMA:
{
    "rag_usage_audit": {
            "rag_strength": "exact/strong_method/high_method/weak_method/ignore",
            "used_rag": true,
            "reusable_method_found": "Short description of the SPM method to copy",
            "special_condition_found": "Short description of any traps, limits, or formulas found",
            "values_copied_from_rag": false
    },
  "angle_audit": {
    "polygon_vertices": ["List the vertices in order"],
    "angles": [
      {
        "label": "angle label or value",
        "vertex": "vertex name",
        "role": "interior/exterior/straight_line/right_angle/unknown",
        "used_in_polygon_sum": true,
        "reason": "short reason"
      }
    ],
    "straight_line_relationships": [
      "Describe any adjacent angles on a straight line"
    ],
    "calculation_scratchpad": [
        "CRITICAL: Before applying Pythagoras or Trigonometry, explicitly list the exact lengths of the triangle's legs based on the diagram.",
        "1. Segment Audit: Is the given number the full length or just the segment? (e.g., 28 is the leg, do not divide by 2)."
    ],
  },
  "question_text": "Brief summary",
  "steps": [
    {
      "subpart": "a",
      "step": "Step title",
      "text": "Explanation",
      "math": "Math equation with substituted values"
    }
  ],
  "final_answers": {
    "a": "Answer",
    "b": "Answer"
  }
}
- TEXT FIELD MATH WRAPPING (CRITICAL): If you mention ANY mathematical variables, equations, or inequalities inside the "text" explanation field, you MUST wrap them in inline math tags \( ... \). 
    - Correct: "When \( x = 20 \), use \( x + y \le 80 \) to find the maximum value."
    - Fatal Error: "When x = 20, use x + y \le 80 to find the maximum value."
- STEP TITLE GUARDRAIL: The `"step"` field (the title) MUST remain 100% plain English/Malay. You are STRICTLY FORBIDDEN from using \( \), \[ \], or any LaTeX commands inside the `"step"` field. (e.g., Write "Substitute x = 20" instead of "Substitute \(x = 20\)").
FORMATTING RULES

- The "step" field is a plain title only.
  Do not put LaTeX wrappers, equations, or long calculations inside the step title.

- The "text" field is for explanation only.
  Do not put calculation lines inside "text".
  If the explanation mentions a variable, equation, inequality, coordinate, matrix, or set expression, wrap only the math part using \( ... \).

- The "math" field is for calculation working only.
  Do not wrap the whole "math" field with \( ... \), \[ ... \], or $$ ... $$.
  Do not put long English/Malay explanations inside "math".

- Every calculation line must be placed in "math", not "text".
  If a line contains =, +, -, ×, \times, /, \frac, ^, %, \sqrt, \pi, it should usually be in "math".

- Use consistent LaTeX:
  Use \frac{a}{b}, not plain a/b when showing fractions clearly.
  Use \times, not ×.
  Use \pi, not π.
  Use x^{2}, not x².
  Use \le and \ge, not <= and >=.
  Use \text{cm}, \text{m}, \text{s}, \text{RM} for units inside math.

- For multi-line working, separate lines with newline characters.
  Example:
  "math": "1500 + 950 + 200 = 2650\n\frac{2650}{5250} \times 100 = 50.48\%"

- final_answers must be a flat dictionary:
  Good: {"a": "RM 4500.00", "b(i)": "RM 120.50"}
  Not good: {"b": {"i": "RM 120.50"}}

- final_answers values should be concise:
  number, equation, coordinate, matrix, yes/no answer, or short unit answer.
  Do not put long explanations inside final_answers.
"""

    user_prompt = f"""
CURRENT QUESTION SUMMARY:
{json.dumps(solver_payload, ensure_ascii=False, indent=2)}

RAG CONTEXT AND USAGE CONTRACT:
{rag_data}

Solve the attached question image directly.
"""
    plane_geometry_tools = [
        calculate_expression,
        solve_equations_tool,
        geometry_mensuration_tool
    ]

    llm = ChatOpenAI(
        model="gemini-3.5-flash-lite",
        temperature=0,
        api_key=os.getenv("GEMINI_API_KEY"),
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
    )

    prompt = ChatPromptTemplate.from_messages([
        SystemMessage(content=system_prompt),
        ("user", [
            {"type": "text", "text": "{user_prompt_text}"},
            {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64,{image_base64}"}}
        ]),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])

    agent = create_tool_calling_agent(llm, plane_geometry_tools, prompt)
    agent_executor = AgentExecutor(
        agent=agent,
        tools=plane_geometry_tools,
        verbose=True,
        return_intermediate_steps=False
    )

    response = agent_executor.invoke({
        "user_prompt_text": user_prompt,
        "image_base64": new_question_image_base64
    })

    raw_text = response["output"]
    return AgentOutputProcessor.process(raw_text)

def solve_loci_geometry(new_question_image_base64, interpreted, rag_data, language):
    solver_payload = prepare_solver_payload(interpreted)
    language_code = str(language or "english").lower()

    if language_code in ["bm", "ms", "malay", "bahasa_melayu", "bahasa melayu"]:
        language_label = "Bahasa Melayu"
    else:
        language_label = "English"

    language_rule = f"""
RESPONSE LANGUAGE RULE:
The selected response language is: {language_label}.

If the selected response language is Bahasa Melayu:
- Write question_text, step titles, explanations, reasons, and final answer text in Bahasa Melayu.
- Keep mathematical symbols, variables, equations, units, and LaTeX unchanged.
- Use SPM-style Malay terms where suitable.
- Do not mix English explanation unless the term is normally used in SPM.

If the selected response language is English:
- Write question_text, step titles, explanations, reasons, and final answer text in English.
- Keep mathematical symbols, variables, equations, units, and LaTeX unchanged.
"""
    system_prompt = language_rule + r"""
You are an expert Malaysian SPM Mathematics teacher specialising in Loci in Two Dimensions.

Your task is to solve the attached loci question step-by-step.

RAG USAGE RULE:
You MUST read the RAG USAGE CONTRACT inside the user prompt before solving.
If RAG strength is exact, follow the official marking scheme.
If RAG strength is strong_method or high_method, use RAG as an important method reference but use the uploaded image for actual values.
If RAG strength is weak_method, use RAG only as light guidance.
If RAG strength is ignore, do not use RAG for solving.

SOURCE OF TRUTH:
1. The attached image is the source of truth.
2. The extracted summary is only a rough helper.
3. For drawing/locus questions, describe exactly what should be drawn or marked.

LOCI RULES:
1. Points at a fixed distance from a point form a circle.
   - The centre is the given point.
   - The radius is the fixed distance.

2. Points at a fixed distance from a straight line form line(s) parallel to the given line.

3. DIAGRAM-BOUNDARY RULE:
   - If the question is based on a bounded diagram, grid, square, rectangle, or region, draw only the part of the locus that lies inside the given diagram/region.
   - Do not answer with both possible parallel lines if one of them lies outside the given diagram.
   - If the line is a side/boundary of the square, the valid locus inside the square is the parallel line inside the square at the required distance.

4. GRID UNIT RULE:
   - Treat each square as 1 unit unless the question says otherwise.
   - Count grid squares carefully from the given point or line.

5. INTERSECTION RULE:
   - If asked to mark points satisfying two loci, mark every point inside the diagram where the two loci intersect.
   - If there are two valid intersection points, say there are two points and describe both.

6. DRAWING ANSWER RULE:
   - Use words to describe drawing actions clearly.
   - Do not pretend a drawing answer is a numerical calculation.

MATH FIELD RULES, VERY IMPORTANT:
1. The "math" field is rendered as LaTeX by the frontend.
2. NEVER put English sentences inside "math".
3. If the step is a drawing or description, put the full answer in "text" and set "math" to "".
4. Only use "math" for short mathematical notation such as:
   - "r = 2"
   - "d = 3"
   - "\\otimes"
5. Do not write phrases like "Locus of X = circle with centre O and radius 2" in "math".
6. π should be converted to 22/7.

OUTPUT JSON SCHEMA:
{
    "rag_usage_audit": {
        "rag_strength": "exact/strong_method/high_method/weak_method/ignore",
        "used_rag": true,
        "reusable_method_found": "Short description of the SPM method to copy",
        "special_condition_found": "Short description of any traps, limits, or formulas found",
        "values_copied_from_rag": false
    },
  "locus_audit": {
    "grid_unit": "State the grid unit if visible",
    "loci": [
      {
        "label": "X or Y",
        "condition": "Fixed distance from point/line",
        "shape": "circle/line/parallel line",
        "valid_within_diagram": "What part should be drawn in the given diagram"
      }
    ],
    "intersections": [
      "Describe the required intersection point(s)"
    ]
  },
  "question_text": "Brief summary",
  "steps": [
    {
      "subpart": "a(i)",
      "step": "Step title",
      "text": "Plain explanation or drawing instruction.",
      "math": ""
    }
  ],
  "final_answers": {
    "a(i)": "Answer in words",
    "a(ii)": "Answer in words",
    "b": "Answer in words"
  }
}
    - TEXT FIELD MATH WRAPPING (CRITICAL): If you mention ANY mathematical variables, equations, or inequalities inside the "text" explanation field, you MUST wrap them in inline math tags \( ... \). 
      - Correct: "When \( x = 20 \), use \( x + y \le 80 \) to find the maximum value."
      - Fatal Error: "When x = 20, use x + y \le 80 to find the maximum value."
    FORMATTING RULES

- The "step" field is a plain title only.
  Do not put LaTeX wrappers, equations, or long calculations inside the step title.

- The "text" field is for explanation only.
  Do not put calculation lines inside "text".
  If the explanation mentions a variable, equation, inequality, coordinate, matrix, or set expression, wrap only the math part using \( ... \).

- The "math" field is for calculation working only.
  Do not wrap the whole "math" field with \( ... \), \[ ... \], or $$ ... $$.
  Do not put long English/Malay explanations inside "math".

- Every calculation line must be placed in "math", not "text".
  If a line contains =, +, -, ×, \times, /, \frac, ^, %, \sqrt, \pi, it should usually be in "math".

- Use consistent LaTeX:
  Use \frac{a}{b}, not plain a/b when showing fractions clearly.
  Use \times, not ×.
  Use \pi, not π.
  Use x^{2}, not x².
  Use \le and \ge, not <= and >=.
  Use \text{cm}, \text{m}, \text{s}, \text{RM} for units inside math.

- For multi-line working, separate lines with newline characters.
  Example:
  "math": "1500 + 950 + 200 = 2650\n\frac{2650}{5250} \times 100 = 50.48\%"

- final_answers must be a flat dictionary:
  Good: {"a": "RM 4500.00", "b(i)": "RM 120.50"}
  Not good: {"b": {"i": "RM 120.50"}}

- final_answers values should be concise:
  number, equation, coordinate, matrix, yes/no answer, or short unit answer.
  Do not put long explanations inside final_answers.
"""

    user_prompt = f"""
CURRENT QUESTION SUMMARY:
{json.dumps(solver_payload, ensure_ascii=False, indent=2)}

RAG CONTEXT AND USAGE CONTRACT:
{rag_data}

Solve the attached loci question directly.
"""

    loci_tools = [
        calculate_expression,
        coordinate_geometry_tool
    ]

    llm = ChatOpenAI(
        model="gemini-3.5-flash-lite",
        temperature=0,
        api_key=os.getenv("GEMINI_API_KEY"),
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
    )

    prompt = ChatPromptTemplate.from_messages([
        SystemMessage(content=system_prompt),
        ("user", [
            {"type": "text", "text": "{user_prompt_text}"},
            {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64,{image_base64}"}}
        ]),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])

    agent = create_tool_calling_agent(llm, loci_tools, prompt)
    agent_executor = AgentExecutor(
        agent=agent,
        tools=loci_tools,
        verbose=True,
        return_intermediate_steps=False
    )

    response = agent_executor.invoke({
        "user_prompt_text": user_prompt,
        "image_base64": new_question_image_base64
    })

    return AgentOutputProcessor.process(response["output"])


def solve_circle_geometry(new_question_image_base64, interpreted, rag_data, language):
    """Specialized solver for Angles, Tangents, and Cyclic Quadrilaterals."""
    
    solver_payload = prepare_solver_payload(interpreted)
    language_code = str(language or "english").lower()

    if language_code in ["bm", "ms", "malay", "bahasa_melayu", "bahasa melayu"]:
        language_label = "Bahasa Melayu"
    else:
        language_label = "English"

    language_rule = f"""
RESPONSE LANGUAGE RULE:
The selected response language is: {language_label}.

If the selected response language is Bahasa Melayu:
- Write question_text, step titles, explanations, reasons, and final answer text in Bahasa Melayu.
- Keep mathematical symbols, variables, equations, units, and LaTeX unchanged.
- Use SPM-style Malay terms where suitable.
- Do not mix English explanation unless the term is normally used in SPM.

If the selected response language is English:
- Write question_text, step titles, explanations, reasons, and final answer text in English.
- Keep mathematical symbols, variables, equations, units, and LaTeX unchanged.
"""
    system_prompt = language_rule + r"""
    You are an expert Malaysian SPM Mathematics teacher specializing in Circle Geometry.
    Your task is to solve the attached question image step-by-step.

    RAG USAGE RULE:
    You MUST read the RAG USAGE CONTRACT inside the user prompt before solving.
    If RAG strength is exact, follow the official marking scheme.
    If RAG strength is strong_method or high_method, use RAG as an important method reference but use the uploaded image for actual values.
    If RAG strength is weak_method, use RAG only as light guidance.
    If RAG strength is ignore, do not use RAG for solving.

    --- STRICT GEOMETRY AXIOMS (CRITICAL) ---
    The attached image is the highest source of truth. Apply these definitions strictly:
    1. THE "ANTI-STRAIGHT-LINE" GUARDRAIL: An acute or obtuse angle CANNOT be bounded by two parts of the same straight line. You must check the intersecting chords.
    2. THE "PHANTOM RADIUS" GUARDRAIL: A tangent is ONLY 90 degrees to a radius. If the center 'O' is NOT explicitly labeled, do NOT assume any angle is 90 degrees.
    3. Alternate Segment Theorem: The angle between a TANGENT and a CHORD equals the angle in the alternate segment. 
       - Find the 3rd point on the circumference forming a triangle with that chord. The alternate angle is at that 3rd point.
       - FATAL ERROR TO AVOID: The alternate angle CANNOT be at either endpoint of the chord itself.
    4. Cyclic Quadrilaterals: 4 points on the circumference. Opposite vertices sum to 180°.
       - FATAL ERROR TO AVOID: Do not use partial angles! Use the FULL angle at the vertex.
    5. COMMON TANGENT & SIMILAR TRIANGLES (CRITICAL): If an Internal Common Tangent crosses the line connecting the centers, it creates Similar Triangles at the exact intersection point.
       - VISUAL MAPPING: Identify the center line (e.g., PQ). Identify the tangent line (e.g., RS). Their crossing point is the Intersection (e.g., U).
       - THE VARIABLE MATCHING GUARDRAIL: You MUST pair a center's distance from the intersection with its OWN radius. 
       - Generalized Equation: (Distance from Intersection to Center 1) / (Radius of Circle 1) = (Distance from Intersection to Center 2) / (Radius of Circle 2).
       - SUBSTITUTION RULE: If the total distance between centers is known (e.g., PQ = 12), you MUST substitute one of the distances as (Total - Other). Example: (12 - x) / 7 = x / 2.
       - FATAL ERROR: You are strictly FORBIDDEN from swapping the radii or refusing to use this equation. You MUST call solve_equations_tool.
    6. EXTERNAL POINT TANGENT THEOREM: If two tangents are drawn to a circle from the same external point (e.g., from an unknown intersection point to S and T), the lengths of those two tangent segments are EXACTLY EQUAL.
    7. Straight Lines: Angles on a straight line sharing the EXACT SAME VERTEX sum to 180°.
    8. THE SHOW-YOUR-WORK AXIOM (CRITICAL): You are STRICTLY FORBIDDEN from skipping straight to the final answer in your visible "steps" array. 
       - Even though you used the calculator tools in the background, you MUST show the substituted formula in the "math" field for the student to see (e.g., "ST = \sqrt{12^2 - (7+2)^2} = 7.937").
       - SEPARATION OF SUBPARTS: Do NOT mix calculations for part (a) and part (b) into the same step. Solve part (a) fully, then start new steps for part (b).
    9. Triangles: Interior angles sum to 180°.
    10. THE ISOLATION GUARDRAIL (CRITICAL): You are FORBIDDEN from using calculate_expression to isolate variables. If you need to find 'r' from an arc length, you MUST pass the raw, un-arranged equation (e.g., equations=["(60/360) * 2 * (22/7) * r = 11"]) into the solve_equations_tool. Any attempt to rearrange this mentally will result in a fatal error.
    11. THE MAJOR/MINOR SECTOR GUARDRAIL (CRITICAL): Never blindly use the largest printed angle in the diagram. A circle is divided into a Major Sector (reflex angle > 180°) and a Minor Sector (< 180°). Before using the $\frac{\theta}{360}$ formula, you MUST explicitly identify whether the requested arc or shaded region is the Major or Minor part of the circle. (e.g., If the diagram prints a reflex angle of 300°, but asks for the minor arc, you MUST calculate and use 60°).
    12. PARALLEL EXECUTION: If you need to make multiple independent calculations (like finding the area of a triangle and the area of a sector), you MUST call the tools simultaneously in parallel to save time. Do not do them one by one.
    --- STRICT GEOMETRY AXIOMS (CRITICAL) ---:
    13. TRIANGLE AREA RULE: To find the area of a triangle inside a circle (like triangle OAC), you MUST use the trigonometry formula Area = $0.5 \times a \times b \times \sin(C)$. Do not use the $\frac{\sqrt{3}}{4}$ equilateral formula.
    14. EXPLICIT FORMULAS (CRITICAL):Arc Length = $(\frac{\theta}{360}) \times 2 \times \pi \times r$ (Do NOT forget the 2!)Sector Area = $(\frac{\theta}{360}) \times \pi \times r^2$Triangle Area = $0.5 \times a \times b \times \sin(C)$
    15. SHADED SEGMENT GUARDRAIL (CRITICAL): A shaded region bounded by a straight chord and a curved arc is a "segment". If the shaded segment is a small slice (smaller than a semi-circle), it is a MINOR segment. You MUST use the MINOR central angle (< 180°) to find its sector area before subtracting the triangle. NEVER use the major/reflex angle to find a shaded area unless the shaded shape is larger than half the circle (a Pac-Man shape).
    16. ROUNDING GUARDRAIL (CRITICAL)
    After each calculation, round the calculated result to exactly 4 significant figures, unless the result is an exact integer or a short exact decimal.
    17. SPM CIRCLE DEFINITIONS & PROPERTIES (CRITICAL): If an SPM question asks for the name and "property" (sifat) of a circle part, you MUST use its textbook geometric definition, NOT a mathematical fact like "they are all equal".
       - Radius (Jejari): Property is "A straight line from the centre to any point on the circumference."
       - Diameter (Diameter): Property is "A straight line passing through the centre that touches the circumference at both ends."
       - Chord (Perentas): Property is "A straight line joining any two points on the circumference."
    Rules:
    1. Each calculated numerical result shown in the working must be rounded to 4 significant figures.
    2. The final answer must also be rounded to 4 significant figures.
    3. Exact integers should remain unchanged.
    Example: 25 stays as 25, not 25.00.
    4. Short exact decimals should remain unchanged.
    Example: 10.5 stays as 10.5.
    5. Long decimals or non-terminating decimals must be rounded to 4 significant figures.
    Example: 5.716666... becomes 5.717.
    Example: 0.00345678 becomes 0.003457.
    Example: 143.276 becomes 143.3.
    6. Do not over-round simple values that are already exact or clean.

    When solving, show each formula clearly, then show the calculated result rounded to 4 significant figures where needed.
    --- JSON SCHEMA ---
    You MUST output valid JSON exactly like this:
    {
        "rag_usage_audit": {
            "rag_strength": "exact/strong_method/high_method/weak_method/ignore",
            "used_rag": true,
            "reusable_method_found": "Short description of the SPM method to copy",
            "special_condition_found": "Short description of any traps, limits, or formulas found",
            "values_copied_from_rag": false
        },
        "calculation_scratchpad": [
            "CRITICAL: Plan your geometric proofs here.",
            "1. Length of Common Tangent: Identify if it is Internal or External. Use the correct formula: sqrt(d^2 - (r1 + r2)^2) for internal, sqrt(d^2 - (r1 - r2)^2) for external.",
            "2. External Point Theorem: Are there two tangents from the same external point to the SAME circle? If yes, they are equal in length.",
            "3. Similar Triangles Mapping: Center line is [Line]. Tangent is [Line]. They intersect exactly at point [Letter]. Center 1 is [Letter], Radius 1 = [Value]. Center 2 is [Letter], Radius 2 = [Value].",
            "4. Similar Triangles Equation: Let the unknown distance be x. The other distance is (Total - x). Set up the equation (Total - x)/R1 = x/R2 and call solve_equations_tool. DO NOT SKIP THIS."
        ],
        "question_text": "Brief summary",
        "steps": [
            {
                "subpart": "",
                "step": "Name of the step",
                "text": "Plain explanation naming the specific theorem used.",
                "math": "Valid LaTeX calculation working only. Do not wrap the whole field with \\( ... \\), \\[ ... \\], or $$ ... $$. Do not write English or Malay sentences here. Use symbols such as \\angle, \\therefore, \\frac, \\times, \\sqrt, \\cos, \\sin, and \\text{cm}. If the step has no calculation, leave this field as an empty string."
            }
        ],
        "final_answer": "Final numeric answer"
    }

    - TEXT FIELD MATH WRAPPING (CRITICAL): If you mention ANY mathematical variables, equations, or inequalities inside the "text" explanation field, you MUST wrap them in inline math tags \( ... \). 
    - Correct: "When \( x = 20 \), use \( x + y \le 80 \) to find the maximum value."
    - Fatal Error: "When x = 20, use x + y \le 80 to find the maximum value."

FORMATTING RULES

- The "step" field is a plain title only.
  Do not put LaTeX wrappers, equations, or long calculations inside the step title.

- The "text" field is for explanation only.
  Do not put calculation lines inside "text".
  If the explanation mentions a variable, equation, inequality, coordinate, matrix, or set expression, wrap only the math part using \( ... \).

- The "math" field is for calculation working only.
  Do not wrap the whole "math" field with \( ... \), \[ ... \], or $$ ... $$.
  Do not put long English/Malay explanations inside "math".

- Every calculation line must be placed in "math", not "text".
  If a line contains =, +, -, ×, \times, /, \frac, ^, %, \sqrt, \pi, it should usually be in "math".

- Use consistent LaTeX:
  Use \frac{a}{b}, not plain a/b when showing fractions clearly.
  Use \times, not ×.
  Use \pi, not π.
  Use x^{2}, not x².
  Use \le and \ge, not <= and >=.
  Use \text{cm}, \text{m}, \text{s}, \text{RM} for units inside math.

- For multi-line working, separate lines with newline characters.
  Example:
  "math": "1500 + 950 + 200 = 2650\n\frac{2650}{5250} \times 100 = 50.48\%"

- final_answers must be a flat dictionary:
  Good: {"a": "RM 4500.00", "b(i)": "RM 120.50"}
  Not good: {"b": {"i": "RM 120.50"}}

- final_answers values should be concise:
  number, equation, coordinate, matrix, yes/no answer, or short unit answer.
  Do not put long explanations inside final_answers.
    """

    user_prompt = f"""
    CURRENT QUESTION SUMMARY (ROUGH HINT ONLY):
    {json.dumps(solver_payload, ensure_ascii=False, indent=2)}

    RAG CONTEXT AND USAGE CONTRACT:
    {rag_data}

    Solve the attached question image directly.
    """
    circle_tools = [
        calculate_expression,
        solve_equations_tool,
        geometry_mensuration_tool
    ]
    print("⭕ Solving Circle Geometry directly from image using Agent Tools...")
    
    llm = ChatOpenAI(
        model="gemini-3.5-flash-lite", 
        temperature=0,
        api_key=os.getenv("GEMINI_API_KEY"),
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
    )
    
    prompt = ChatPromptTemplate.from_messages([
        SystemMessage(content=system_prompt),
        ("user", [
            {"type": "text", "text": "{user_prompt_text}"},
            {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64,{image_base64}"}}
        ]),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])

    agent = create_tool_calling_agent(llm, circle_tools, prompt)
    agent_executor = AgentExecutor(
        agent=agent, 
        tools=circle_tools, 
        verbose=True, 
        return_intermediate_steps=False
    )
    response = agent_executor.invoke({
        "user_prompt_text": user_prompt,
        "image_base64": new_question_image_base64
    })

    return AgentOutputProcessor.process(response["output"])
