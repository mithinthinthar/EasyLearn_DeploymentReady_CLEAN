import os
import json
from langchain_openai import ChatOpenAI
from langchain_classic.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import SystemMessage

from solving.format_json import AgentOutputProcessor
from solving.utils import prepare_solver_payload
from solving.math_tools import algebra_tool, calculate_expression, coordinate_geometry_tool, financial_math_tool, geometry_mensuration_tool, matrix_tool, solve_equations_tool, statistics_tool

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


def solve_general_math(new_question_image_base64, interpreted, rag_data, language):
    """
    Solves a new uploaded question.
    1. Extract data only for RAG/search support.
    2. Retrieve similar SPM examples.
    3. Let the solver solve directly from the original image using top-down Chain of Thought.
    """
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
    You are an expert Malaysian SPM Mathematics teacher.
    Your task is to solve the attached question image step-by-step.

    RAG USAGE RULE:
    You MUST read the RAG USAGE CONTRACT inside the user prompt before solving.
    If RAG strength is exact, follow the official marking scheme.
    If RAG strength is strong_method or high_method, use RAG as an important method reference but use the uploaded image for actual values.
    If RAG strength is weak_method, use RAG only as light guidance.
    If RAG strength is ignore, do not use RAG for solving.

    --- STRICT SOLVING AXIOMS (CRITICAL) ---
    1. THE SOURCE OF TRUTH: The attached image is the highest source of truth. The extracted JSON is only a rough helper.
    2. THE MENTAL MATH BAN (CRITICAL): You are FORBIDDEN from doing arithmetic, algebra, or matrix multiplication in your head. You MUST use the `calculate_expression`, `matrix_tool`, or `solve_equations_tool` for EVERY calculation and copy the EXACT result from the tool output. Never invent or guess numbers.
    3. THE "TEACHER" GUARDRAIL: Do NOT skip intermediate steps just because a tool gave you the final answer! You are teaching a student.
       - If the question specifies "Using the matrix method", you CANNOT just output the final x and y values. You MUST explicitly map out the steps: Form the matrix, show the inverse matrix formula (with the determinant), show the matrix multiplication, and then the final answer.
       - Always break down your logic into 4 to 5 detailed, pedagogical steps.
    4. SUBPART DEPENDENCY RULE: If the question has multiple subparts (e.g., a, b, c), you MUST solve them in order. Substitute values derived in part (a) into part (b).
    5. FUNDAMENTAL ARITHMETIC LAWS (CRITICAL): When explaining arithmetic expansions, factorisations, or structural manipulations, you MUST strictly restrict your theoretical explanations to only these 4 fundamental laws:
       - Commutative Law: a + b = b + a and a \times b = b \times a
       - Associative Law: (a + b) + c = a + (b + c) and (a \times b) \times c = a \times (b \times c)
       - Distributive Law: a \times (b \pm c) = a \times b \pm a \times c
       - Identity Law: a + 0 = a, a + (-a) = 0, a \times 0 = 0, a \times 1 = a, and a \times \frac{1}{a} = 1
       You are FORBIDDEN from using advanced university-level terminology (e.g., rings, fields, abelian groups). Whenever a structural manipulation is performed, explicitly name which of these 4 laws is being applied in the explanation text.
    6. NUMBER BASES (CRITICAL): If you see numbers with a subscript like 1001_2 or 210_3, it indicates base 2 and base 3. To convert to base 10, multiply each digit by the base raised to its positional power (e.g., 2^0, 2^1, etc.) using `calculate_expression`. You are STRICTLY FORBIDDEN from interpreting the subscript as a fraction (like 1/2).
    7. INEQUALITIES FORMATTING: When writing final answers for inequalities, always use proper LaTeX commands `\le` and `\ge`. Do NOT use standard keyboard symbols like `<=` or `>=`.
    8. THE MENTAL MATH & COUNTING BAN (CRITICAL): 
       - You are FORBIDDEN from calculating the total frequency mentally. You MUST pass the addition equation into the `calculate_expression` tool.
       - SQUARE ROOT GUARDRAIL: You are STRICTLY FORBIDDEN from calculating standard deviation (square roots) in your head. You MUST pass the variance into the `calculate_expression` tool using the syntax `sqrt(variance)` (e.g., `sqrt(0.694375)`). Never guess the decimal!
       - ALIGNMENT OVERRIDE (CRITICAL): The equation you pass to `calculate_expression` MUST perfectly match the row counts you just wrote in your scratchpad. If you wrote '4, 5, 5, 2, 2' in your scratchpad, you MUST pass exactly '4+5+5+2+2' to the tool. Do NOT mix up numbers!
       - IF the table is completely blank and you MUST count raw data, call the `statistics_tool` with operation='frequency_distribution'.
    9. THE SHOW-YOUR-WORK AXIOM (CRITICAL): When calculating variance or standard deviation, you are STRICTLY FORBIDDEN from skipping straight to the final square root in your visible "steps" array. Even though you used the calculator tools perfectly in the background, you MUST generate explicit, separate steps in your JSON output showing the mathematical derivation:
       - You MUST show a step for the Mean with substituted numbers (e.g., \frac{8.9 + 9.4 + ...}{8}).
       - You MUST show a step for the Variance with substituted numbers (e.g., \frac{8.9^2 + 9.4^2 + ...}{8} - Mean^2).
       - Only THEN can you show the final Standard Deviation step.
    10. TOOL SYNTAX GUARDRAIL (CRITICAL): When passing equations to `solve_equations_tool`, they MUST be valid, clean mathematical strings (e.g., 'x = 3*y' and '35*x + 3*y = 1620'). You are STRICTLY FORBIDDEN from passing question marks ('?'), uncalculated ratios, or descriptive text into the tool.
    11. THE MENTAL MATH BAN (FATAL ERROR): You are strictly forbidden from guessing solutions to simultaneous equations in your head. You MUST use the `solve_equations_tool`. If you guess the values of x and y without a successful tool return, you will fail.
    12. THE DISCRETE ENTITY ROUNDING TRAP (CRITICAL): If the final answer represents discrete, physical, indivisible real-world entities (e.g., number of people, visitors, cars, coins, trees, animals), it MUST be a whole number. 
       - If your mathematical model or equation outputs a decimal (e.g., 91148.4375 visitors), you MUST round it to the nearest whole number (e.g., 91148) for your final answer. 
       - You are STRICTLY FORBIDDEN from outputting a decimal for a discrete entity in the `final_answers` field.
    13. SPM VARIATION (UBAHAN) METHOD & ROUNDING TRAP (CRITICAL): If the question states "varies directly", "varies inversely", or "varies jointly":
       - Step 1: You MUST find the constant 'k' first.
       - Step 2 (THE ROUNDING TRAP): If 'k' is a long decimal, you MUST round it to 2 decimal places or 3-4 significant figures (e.g., 3.3203... becomes 3.32) BEFORE substituting it into the final equation! Do NOT use the exact infinite fraction for the final step, or your final answer will mismatch the official SPM marking scheme.
       - Step 3: Rewrite the equation (e.g., V = 3.32 * S^3). 
       - Step 4: Substitute the new value into this rounded equation to get the final answer. Do NOT add base values back to the final answer unless explicitly asked for the "total including original".
    VARIATION RELATIONSHIP CLASSIFIER (CRITICAL):
    - Before writing any variation formula, you MUST identify the relationship for EACH variable separately.
    - If the question says "directly proportional to A", place A in the numerator.
    - If the question says "inversely proportional to B", place B in the denominator.
    - If the question says "directly proportional to A and inversely proportional to B", the formula MUST be:
    y = kA / B
    - If the question says "inversely proportional to A and directly proportional to B", the formula MUST be:
    y = kB / A
    - You MUST write this classification in the steps before finding k.

    RAG CONFLICT OVERRIDE FOR VARIATION:
    - If RAG suggests a variation formula but the image states a different direct/inverse relationship, IGNORE the RAG formula.
    - The attached image is the source of truth.
    - Never copy a RAG formula like y = kxy unless the image clearly says the variable is directly proportional to BOTH x and y.
    
    TABLE DATA ROLE GUARDRAIL (CRITICAL):
    - BEFORE FORMING EQUATION using the Table DATA, IDENTIFY IF THE information inside THE PASSAGE can form EQUATION.
    - Before forming equations, identify the role of each number.
    - Do NOT automatically use table values to form the main equation.
    - If the sentence gives total quantities, total score, total price, or total number of items, those sentence values usually form the equation.
    - If a table shows groups, students, teams, or categories, those values may only be for comparison in later subparts.
    - For quiz-score questions:
    1. If the question says the total number of Mathematics and Science questions are M and S, and the total score is T, form Mx + Sy = T.
    2. If the table shows questions answered by Group A and Group B, use the table only to calculate each group’s score after x and y are found.
    - Always explain why each equation is formed from the sentence or table.
    --- JSON SCHEMA ---
    You MUST output valid JSON exactly like this for your final response:
    {
        "rag_usage_audit": {
            "rag_strength": "exact/strong_method/high_method/weak_method/ignore",
            "used_rag": true,
            "reusable_method_found": "Short description of the SPM method to copy",
            "special_condition_found": "Short description of any traps, limits, or formulas found",
            "values_copied_from_rag": false
        },
        "calculation_scratchpad": [
            "CRITICAL: Follow this dynamic checklist to prevent Table Distraction:",
            "1. DATA SOURCE SEPARATION: Explicitly list the variables and numbers found in the PARAGRAPH text separately from the numbers found in the TABLE.",
            "2. MAIN EQUATION FORMATION: If the paragraph describes a global 'Total' (e.g., total score, total items, total price), you MUST build your primary simultaneous equations using the PARAGRAPH numbers. Do NOT use specific table rows to form the base equation.",
            "3. SUBPART EVALUATION: After using the tools to solve for the variables (x, y), apply those variables to the specific rows in the TABLE (e.g., Group A/B, Shop A/B) to calculate their individual outcomes."
        ],
        "question_text": "Brief summary of the overall question.",
        "steps": [
            {
                "subpart": "a",
                "step": "Name of the mathematical step",
                "text": "Plain explanation of what you are doing.",
                "math": "Pure LaTeX equation showing the evaluated math"
            }
        ],
        "final_answers": {
            "a": "Final numeric answer. CRITICAL: If your answer mixes English words and math, you MUST wrap ONLY the math portions in \\( ... \\) tags (e.g., 'Shade \\( (A' \\cap B) \\cup C \\)')."
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
    CURRENT QUESTION SUMMARY (ROUGH HINT ONLY):
    {json.dumps(solver_payload, ensure_ascii=False, indent=2)}

    RAG CONTEXT AND USAGE CONTRACT:
    {rag_data}

    Solve the attached question image directly.
    """

    print("🧠 Solving directly from image using RAG methods...")
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

    # Create the tool-calling agent and executor
    agent = create_tool_calling_agent(llm, math_tools, prompt)
    agent_executor = AgentExecutor(
        agent=agent, 
        tools=math_tools, 
        verbose=True, # Set to False in production to hide tool logs
        return_intermediate_steps=False
    )

    # Invoke the agent pipeline
    response = agent_executor.invoke({
        "user_prompt_text": user_prompt,
        "image_base64": new_question_image_base64
    })

    raw_text = response["output"]
    
    # Your existing safe JSON parser will cleanly strip away any markdown block characters
    return AgentOutputProcessor.process(raw_text)
