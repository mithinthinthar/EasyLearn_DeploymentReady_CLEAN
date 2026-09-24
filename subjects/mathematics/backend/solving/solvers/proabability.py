import os
import json
from langchain_openai import ChatOpenAI
from langchain_classic.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import SystemMessage

from solving.format_json import AgentOutputProcessor
from solving.utils import prepare_solver_payload
from solving.math_tools import calculate_expression, solve_equations_tool

def solve_probability(new_question_image_base64, interpreted, rag_data, language):
    """Specialized solver for Simple Probability and Combined Events."""
    
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
    You are an expert Malaysian SPM Mathematics teacher specializing in Probability.
    Your task is to solve the attached question image step-by-step.

    RAG USAGE RULE:
    You MUST read the RAG USAGE CONTRACT inside the user prompt before solving.
    If RAG strength is exact, follow the official marking scheme.
    If RAG strength is strong_method or high_method, use RAG as an important method reference but use the uploaded image for actual values.
    If RAG strength is weak_method, use RAG only as light guidance.
    If RAG strength is ignore, do not use RAG for solving.

    --- STRICT PROBABILITY AXIOMS (CRITICAL) ---
    1. THE SOURCE OF TRUTH: The attached image is the highest source of truth.
    
    2. THE "WITHOUT REPLACEMENT" RULE (TANPA PEMULANGAN):
       - If an item is drawn and NOT replaced, the total denominator for the SECOND draw MUST decrease by 1.
       - If the second item drawn is the SAME category as the first, its numerator MUST also decrease by 1.
       - If the second item drawn is a DIFFERENT category, its numerator stays the same, but the denominator still decreases by 1.

    3. THE "WITH REPLACEMENT" RULE (DENGAN PEMULANGAN):
       - If an item is replaced, the denominator and numerators for the second draw remain EXACTLY the same as the first draw.

    4. TREE DIAGRAM SUM RULE:
       - The probabilities on all branches originating from the EXACT SAME node MUST add up to exactly 1.
       - Use this rule to find missing fractions on a tree diagram. (e.g., if top branch is 3/5, bottom branch must be 2/5).

    5. COMBINED EVENTS ARITHMETIC:
       - "AND" (Dan / Both / Kedua-dua): Multiply the probabilities along the path (e.g., P(A) * P(B)).
       - "OR" (Atau / Different / At least one): Add the probabilities of the different valid paths (e.g., Path 1 + Path 2).

    6. FILLING IN DIAGRAMS:
       - If the question asks to complete a diagram (like filling in boxes), clearly state what goes in the top box, middle box, etc. Look carefully at the "Kesudahan/Outcome" column. The outcome of path B then M is strictly written as (B, M).
    7. THE "HENCE / SETERUSNYA" SAMPLE SPACE RULE (CRITICAL SPM RULE):
        - If a question asks to "List the sample space... Hence find the probability", you are STRICTLY FORBIDDEN from using the multiplication or addition formulas (e.g., P(A) * P(B)).
        - You MUST use the counting method. You MUST explicitly list the exact subset of favorable outcomes drawn from the main sample space (e.g., {(55, N), (63, N), (67, N)}).
        - The math output MUST show the raw fraction of n(favorable) / n(total_sample_space) based on the count (e.g., \frac{3}{15}).

    --- JSON SCHEMA ---
    You MUST output valid JSON exactly like this for your final response:
    {
        "rag_usage_audit": {
            "rag_strength": "exact/strong_method/high_method/weak_method/ignore",
            "used_rag": true,
            "reusable_method_found": "Short description of the SPM method to copy",
            "special_condition_found": "Short description of any traps or formats found",
            "values_copied_from_rag": false
        },
        "calculation_scratchpad": [
            "CRITICAL: Map out the inventory here BEFORE calculating.",
            "1. REPLACEMENT CHECK: Is it with or without replacement?",
            "2. INITIAL STATE: Total = X. Item A = Y, Item B = Z.",
            "3. AFTER DRAW 1 (If A is drawn): Total = X-1. Item A = Y-1, Item B = Z.",
            "4. AFTER DRAW 1 (If B is drawn): Total = X-1. Item A = Y, Item B = Z-1.",
            "5. VERIFY TREE: Do the branches from each node add up to 1?"
            "FOR SAMPLE SPACE QUESTION
            - Use the counting method and EXPLICITLY list out the exact subset of favorable outcomes drawn from the main sample space"
        ],
        "question_text": "Brief summary.",
        "steps": [
            {
                "subpart": "a",
                "step": "Name of the step",
                "text": "Plain explanation.",
                "math": "Standalone LaTeX equation WITH NUMBERS PLUGGED IN."
            }
        ],
        "final_answers": {
            "b": "",
            "b(i)": "",
            "b(ii)": ""
        }
    }
    - FINAL ANSWER FORMAT: You must standardize the "final_answers" field. Output EACH subpart as its own separate key (e.g., "b", "b(i)", "b(ii)"). Do NOT lump them together into one key.
    - SET NOTATION: When outputting sets in the final answer, use standard braces like {...}. Do NOT escape them with backslashes like \\{...\\} unless they are inside a pure LaTeX block.
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

    print("🎲 Solving Probability directly from image...")
    
    prob_tools = [calculate_expression, solve_equations_tool]
    
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

    agent = create_tool_calling_agent(llm, prob_tools, prompt)
    agent_executor = AgentExecutor(
        agent=agent, 
        tools=prob_tools, 
        verbose=True, 
        return_intermediate_steps=False
    )

    response = agent_executor.invoke({
        "user_prompt_text": user_prompt
    })
    return AgentOutputProcessor.process(response["output"])