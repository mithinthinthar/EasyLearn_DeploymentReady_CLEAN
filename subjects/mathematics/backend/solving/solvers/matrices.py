
import os
import json
from langchain_openai import ChatOpenAI
from langchain_classic.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import SystemMessage

from solving.format_json import AgentOutputProcessor
from solving.utils import prepare_solver_payload
from solving.math_tools import calculate_expression, solve_equations_tool, matrix_tool

def solve_matrix_math(new_question_image_base64, interpreted, rag_data, language):
    """Specialized solver for SPM Matrices."""
    
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
    You are an expert Malaysian SPM Mathematics teacher specializing in Matrices.

    Your task:
    Solve the attached SPM Mathematics matrix question step-by-step.

    SOURCE PRIORITY:
    1. The attached image is the source of truth for numbers, variables, and wording.
    2. CURRENT QUESTION SUMMARY is only a rough helper.
    3. RAG context is only a method reference unless the RAG contract says exact match.

    RAG USAGE:
    Read the RAG USAGE CONTRACT inside the user prompt.
    - exact: follow the official marking scheme.
    - strong_method / high_method: use the method, but use values from the image.
    - weak_method: use only as light guidance.
    - ignore: solve from the image only.

    REQUIRED MATRIX WORKFLOW:

    A. For determinant / no inverse questions:
    1. Extract the matrix from the image.
    2. Use the determinant condition for a non-invertible matrix:
    det(matrix) = 0.
    3. Call matrix_tool or solve_equations_tool where needed.
    4. Copy the exact tool result into the final answer.

    B. For identity matrix questions:
    1. If the question says AB = I, treat B as A inverse.
    2. Use matrix_tool to find the inverse of the known matrix.
    3. Equate corresponding entries to find unknowns.

    C. For matrix-method word problems:
    1. Define the variables clearly.
    2. Write raw_equations exactly from the word problem.
    Example:
    M + S = 34
    M + 3 = 3*(S + 3)
    3. Pass these raw equations directly to solve_equations_tool.
    4. Use the tool result as the answer values.
    5. If the question says "using matrix method", also show the matrix equation and inverse-matrix working in the visible steps.

    AGE WORD-PROBLEM RULE:
    For "A years later, X will be n times Y", write:
    X + A = n(Y + A)

    Example:
    M + 3 = 3(S + 3)

    Pass this raw equation directly to solve_equations_tool.
    The final values must satisfy the original future-age equation.

    MATRIX METHOD DISPLAY RULE:
    If the question says "using matrix method", the visible steps must include:
    1. The simultaneous equations.
    2. The matrix equation AX = B.
    3. The inverse formula:
    X = 1 / ((a)(d) - (b)(c)) * [[d, -b], [-c, a]] * B
    4. The final values with their real-world meaning.

    ANSWER VERIFICATION RULE:
    Before final output, substitute the final values back into the original raw equations.
    If any equation fails, correct the equations and solve again.

    OUTPUT JSON ONLY:
    {
    "rag_usage_audit": {
        "rag_strength": "exact/strong_method/high_method/weak_method/ignore",
        "used_rag": true,
        "reusable_method_found": "Short method summary",
        "special_condition_found": "Short trap or condition summary",
        "values_copied_from_rag": false
    },
    "calculation_scratchpad": [
        "Raw equations extracted from the question.",
        "Tool results copied exactly.",
        "Verification by substitution."
    ],
    "tool_execution_plan": [
        "List the tools called and the exact values returned."
    ],
    "question_text": "Brief summary.",
    "steps": [
        {
        "subpart": "a",
        "step": "Plain step title",
        "text": "Plain explanation.",
        "math": "Pure LaTeX only"
        }
    ],
    "final_answers": {
        "a": "Final answer",
        "b(i)": "Final answer"
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
  Do not put long explanations inside final_answers.ags.
    """

    user_prompt = f"""
    CURRENT QUESTION SUMMARY (ROUGH HINT ONLY):
    {json.dumps(solver_payload, ensure_ascii=False, indent=2)}

    RAG CONTEXT AND USAGE CONTRACT:
    {rag_data}

    Solve the attached question image directly.
    """

    print("🟩 Solving Matrices directly from image...")
    matrix_tools = [calculate_expression, solve_equations_tool, matrix_tool]
    
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

    agent = create_tool_calling_agent(llm, matrix_tools, prompt)
    agent_executor = AgentExecutor(
        agent=agent, 
        tools=matrix_tools, 
        verbose=True, 
        return_intermediate_steps=False
    )
    response = agent_executor.invoke({
        "user_prompt_text": user_prompt,
        "image_base64": new_question_image_base64
    })

    return AgentOutputProcessor.process(response["output"])