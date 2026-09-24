import os
import json
from langchain_openai import ChatOpenAI
from langchain_classic.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import SystemMessage

from solving.format_json import AgentOutputProcessor
from solving.utils import prepare_solver_payload
# Only import basic tools since logic rarely uses heavy algebra, but might need basic calculation for premises
from solving.math_tools import calculate_expression, solve_equations_tool

def solve_logical_reasoning(new_question_image_base64, interpreted, rag_data, language):
    """Specialized solver for Sets and Logical Reasoning."""
    
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
    You are an expert Malaysian SPM Mathematics teacher specializing in Logical Reasoning and Sets.
    Your task is to solve the attached question image step-by-step.

    RAG USAGE RULE:
    You MUST read the RAG USAGE CONTRACT inside the user prompt before solving.
    If RAG strength is exact, follow the official marking scheme.
    If RAG strength is strong_method or high_method, use RAG as an important method reference but use the uploaded image for actual values.
    If RAG strength is weak_method, use RAG only as light guidance.
    If RAG strength is ignore, do not use RAG for solving.

    --- STRICT LOGIC AXIOMS (CRITICAL) ---
    1. THE SOURCE OF TRUTH: The attached image is the highest source of truth.
    
    2. COMBINING STATEMENTS (AND/OR): When asked to combine two statements to form a TRUE statement, evaluate the truth value of each first:
       - If BOTH are TRUE: You MUST use "and" (dan).
       - If ONE is TRUE and ONE is FALSE: You MUST use "or" (atau).
       - You must explicitly state the truth values in your steps before writing the answer.
    
    3. DEDUCTIVE ARGUMENTS (Form 1, Form 2, Form 3):
       - Form 1: Premise 1: "All A are B." Premise 2: "C is A." Conclusion: "C is B."
       - Form 2 (Modus Ponens): Premise 1: "If p, then q." Premise 2: "p is true." Conclusion: "q is true."
       - Form 3 (Modus Tollens): Premise 1: "If p, then q." Premise 2: "Not q is true." Conclusion: "Not p is true."
       - THE "NOT" GUARDRAIL: If the conclusion is the opposite of p (e.g., 9k \le 54 instead of 9k > 54), it is Form 3. Premise 2 MUST be the exact opposite of q (e.g., k \le 5).

    4. INDUCTIVE ARGUMENTS (Patterns to general conclusions):
       - Assessed as Strong/Weak (Kuat/Lemah) based on whether the conclusion logically follows the pattern.
       - Assessed as Cogent/Not Cogent (Meyakinkan/Tidak Meyakinkan) based on whether the premises are mathematically true.

    5. COUNTER-EXAMPLES (PENYANGKAL):
       - If a statement is false, you MUST provide an object AND its property to disprove it.
       - FATAL ERROR: Just writing the object name (e.g., "Triangle").
       - CORRECT: "A triangle is a polygon but it has 0 diagonals."

    6. IMPLICATIONS:
       - If p, then q.
       - Converse: If q, then p.
       - Inverse: If not p, then not q.
       - Contrapositive: If not q, then not p.
    7. FULL SENTENCES & LANGUAGE (CRITICAL): 
       - You MUST write out the FULL statement text (e.g., "16 is an even number and 16 is a perfect square"). You are STRICTLY FORBIDDEN from using lazy abbreviations like "Statement 1 and Statement 2".
       - You MUST output all explanations, steps, and final answers in ENGLISH. Translate any Malay terms into English before outputting.

    8. LATEX TEXT SPACING (CRITICAL): 
       - If you write English words inside the "math" field, you MUST wrap them in \text{...} so LaTeX preserves the spaces. 
       - CORRECT: \text{16 is even}
       - FATAL ERROR: 16 is even
       - If your step is entirely textual logic, leave the "math" field completely empty ("").
       
    9. INDUCTIVE NUMBER PATTERNS (CRITICAL): 
       - When forming a general conclusion from a number pattern, you MUST preserve the EXACT algebraic structure (brackets, operators) shown in the question. 
       - You are STRICTLY FORBIDDEN from expanding or simplifying the final expression. (e.g., If the pattern is (n^2 - 1) + n, leave it exactly like that. Do NOT simplify to n^2 + n - 1).
       - You MUST append the sequence definition at the end: ", n = 1, 2, 3, ..."
    10. Antecedent does not need to include the word "if" in front.
    
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
            "CRITICAL: Do your logical thinking here BEFORE writing the steps.",
            "1. STATEMENT ANALYSIS: S1 is [True/False] because... S2 is [True/False] because...",
            "2. ARGUMENT ANALYSIS: Is it Deductive or Inductive? Are the premises true? Does the structure follow?",
            "3. COUNTER-EXAMPLE PLAN: Identify an object that fits the premise but breaks the conclusion."
        ],
        "question_text": "Brief summary.",
        "steps": [
            {
                "subpart": "a",
                "step": "Name of the logical step",
                "text": "Plain explanation (e.g., 'Since Statement 1 is true and Statement 2 is false, we combine them using OR.').",
                "math": "Mathematical translation if applicable, otherwise leave empty or use text."
            }
        ],
        "final_answers": {
            "a": "Final answer. Wrap any math in \\( ... \\)."
        }
    }
    LOGIC OUTPUT FORMAT OVERRIDE (CRITICAL):
    - For logical reasoning questions, full logical sentences MUST be written in the "text" field, not the "math" field.
    - The "math" field must contain only pure mathematical expressions, such as: "k \le 5".
    - Do NOT put words like "If", "then", "Premise", "Conclusion" inside the "math" field.
    
    VARIABLE WRAPPING (CRITICAL):
    - In your "text" and "final_answers" fields, if you write a logical sentence that contains mathematical variables or numbers, you MUST wrap ONLY the specific variables/numbers in \( \) tags.
    - CORRECT: "If \( m \) is a multiple of \( 10 \), then the last digit of \( m \) is zero."
    - FATAL ERROR: "If \( m is a multiple of 10 \)..." (Do not wrap English words!)
    - Prefer Unicode symbols for logic/math comparisons:
      Use ≠ instead of \neq
      Use ≤ instead of \leq
      Use ≥ instead of \geq

    CORRECT LOGIC OUTPUT EXAMPLE:
    {
      "steps": [
        {
          "subpart": "a",
          "step": "Contrapositive",
          "text": "The contrapositive is: If \( 3x - 1 ≠ 8 \), then \( x ≠ 3 \).",
          "math": ""
        }
      ],
      "final_answers": {
        "a": "If \( 3x - 1 ≠ 8 \), then \( x ≠ 3 \)",
        "b": "\( k ≤ 5 \)",
        "c": "\( (n^2 - 1) + n \), \( n = 1, 2, 3, ... \)"
      }
    }
    - TEXT FIELD MATH WRAPPING (CRITICAL): If you mention ANY mathematical variables, equations, or inequalities inside the "text" explanation field, you MUST wrap them in inline math tags \( ... \). 
    - Correct: "When \( x = 20 \), use \( x + y \le 80 \) to find the maximum value."
    - Fatal Error: "When x = 20, use x + y \le 80 to find the maximum value."
    - Wrap ONLY the math parts in \\( ... \\). e.g., 'If \\( 3x - 1 \\neq 8 \\), then \\( x \\neq 3 \\).'"
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

    print("🧠 Solving Logical Reasoning directly from image...")
    
    # We provide calculate_expression just in case a premise requires basic math to verify (e.g., 3 * 5 = 15)
    logic_tools = [calculate_expression, solve_equations_tool]
    
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

    agent = create_tool_calling_agent(llm, logic_tools, prompt)
    agent_executor = AgentExecutor(
        agent=agent, 
        tools=logic_tools, 
        verbose=True, 
        return_intermediate_steps=False
    )

    response = agent_executor.invoke({
        "user_prompt_text": user_prompt
    })
    return AgentOutputProcessor.process(response["output"])