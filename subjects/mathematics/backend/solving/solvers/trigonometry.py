
import os
import json
from langchain_openai import ChatOpenAI
from langchain_classic.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import SystemMessage

from solving.format_json import AgentOutputProcessor
from solving.utils import prepare_solver_payload
from solving.math_tools import calculate_expression, solve_equations_tool, algebra_tool


def solve_trigonometry(new_question_image_base64, interpreted, rag_data, language):
    """Specialized solver for Trigonometry, Elevation/Depression, and Special Angles."""
    
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
    You are an expert Malaysian SPM Mathematics teacher specializing in Trigonometry.
    Your task is to solve the attached question image step-by-step.

    RAG USAGE RULE:
    You MUST read the RAG USAGE CONTRACT inside the user prompt before solving.
    If RAG strength is exact, follow the official marking scheme.
    If RAG strength is strong_method or high_method, use RAG as an important method reference but use the uploaded image for actual values.
    If RAG strength is weak_method, use RAG only as light guidance.
    If RAG strength is ignore, do not use RAG for solving.

    --- STRICT TRIGONOMETRY AXIOMS (CRITICAL) ---
    1. THE "NO CALCULATOR" GUARDRAIL (CRITICAL): If the question states "Without using a calculator" (Tanpa menggunakan kalkulator), you are FORBIDDEN from using decimals. You MUST use exact Special Angles (Sudut Khas) and leave your final answer in exact surd form (e.g., 2\sqrt{2} + 1).
       - \sin(45^\circ) = \cos(45^\circ) = \frac{1}{\sqrt{2}}
       - \tan(45^\circ) = 1
       - \sin(30^\circ) = \cos(60^\circ) = \frac{1}{2}
       - \sin(60^\circ) = \cos(30^\circ) = \frac{\sqrt{3}}{2}
       - \tan(30^\circ) = \frac{1}{\sqrt{3}}
       - \tan(60^\circ) = \sqrt{3}
    2. RIGHT-ANGLED TRIANGLES: Use SOH CAH TOA.
       - \sin(\theta) = Opposite / Hypotenuse
       - \cos(\theta) = Adjacent / Hypotenuse
       - \tan(\theta) = Opposite / Adjacent
    3. HEIGHT & DISTANCE MAPPING: Pay extreme attention to the diagram. If a ladder leans on a wall, and a camera is 1m *above* the ladder, you must calculate the triangle's opposite side, then ADD the 1m to get the final height.
    4. TRIGONOMETRIC GRAPH TRANSFORMATIONS ("STATE THE EFFECT"): If a question asks "State the effect on the graph" (Nyatakan kesan ke atas graf) when a parameter like amplitude changes, you MUST use standard SPM phrasing.
       - FATAL ERROR: Do NOT use geometric transformation terms like "vertical stretch" or "horizontal compression".
       - FOR AMPLITUDE CHANGES: You MUST explicitly calculate and state the new maximum and minimum values. Formula: New Max = (Vertical Shift) + New Amplitude. New Min = (Vertical Shift) - New Amplitude. 
       - ACCEPTED SPM PHRASING: "The shape of the graph changes. The new maximum value is X and the minimum value is Y."
    
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
        "tool_execution_plan": [
            "CRITICAL: Write down EXACTLY which tools you called and the exact values returned."
        ],
        "calculation_scratchpad": [
            "CRITICAL: Do algebraic manipulation of surds here."
        ],
        "question_text": "Brief summary",
        "steps": [
            {
                "subpart": "a",
                "step": "Name of the step",
                "text": "Pure explanation. No LaTeX here.",
                "math": "Standalone LaTeX equation WITH NUMBERS PLUGGED IN."
            }
        ],
        "final_answers": {
            "a": "Final exact answer (e.g., 2\\sqrt{2} + 1)"
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
    CURRENT QUESTION SUMMARY (ROUGH HINT ONLY):
    {json.dumps(solver_payload, ensure_ascii=False, indent=2)}

    RAG CONTEXT AND USAGE CONTRACT:
    {rag_data}

    Solve the attached question image directly.
    """

    print("📐 Solving Trigonometry directly from image...")
    # Give it access to calculate and algebra tools in case it needs to simplify surds
    trig_tools = [calculate_expression, algebra_tool, solve_equations_tool]
    
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
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{new_question_image_base64}"}}
        ]),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])

    agent = create_tool_calling_agent(llm, trig_tools, prompt)
    agent_executor = AgentExecutor(
        agent=agent, 
        tools=trig_tools, 
        verbose=True, 
        return_intermediate_steps=False
    )
    response = agent_executor.invoke({
        "user_prompt_text": user_prompt,
        "image_base64": new_question_image_base64
    })

    return AgentOutputProcessor.process(response["output"])