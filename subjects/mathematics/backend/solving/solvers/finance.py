import os
import json
from langchain_openai import ChatOpenAI
from langchain_classic.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import SystemMessage
from solving.format_json import AgentOutputProcessor
from solving.utils import prepare_solver_payload
from solving.math_tools import calculate_expression, solve_equations_tool, taxation_tool, insurance_tool
def solve_insurance_math(new_question_image_base64, interpreted, rag_data, language):
    """Specialized solver for Insurance Math: life, motor, property, medical, travel."""
    
    solver_payload = prepare_solver_payload(interpreted)
    language_code = str(language or "english").lower()

    if language_code in ["bm", "ms", "malay", "bahasa_melayu", "bahasa melayu"]:
        language_label = "Bahasa Melayu"
    else:
        language_label = "English"

    language_rule = f"""
RESPONSE LANGUAGE
Selected language: {language_label}

- Write question_text, step titles, explanations, and final answer text in {language_label}.
- Keep mathematical symbols, variables, equations, units, and LaTeX unchanged.
- Use clear SPM-style explanation.
- If the selected language is Bahasa Melayu, use suitable SPM Malay terms.
"""

    system_prompt = language_rule + r"""
You are an expert Malaysian SPM Mathematics teacher specializing in Insurance Mathematics.

TASK
Solve the attached question image step-by-step.
Use the image as the source of actual values.

SOURCE PRIORITY
1. Attached image: source of actual question values.
2. CURRENT QUESTION SUMMARY: rough hint only.
3. RAG context:
   - exact: follow the official marking scheme.
   - strong_method or high_method: use the method, but take values from the image.
   - weak_method: use only as light guidance.
   - ignore: solve from the image only.

GENERAL SOLVING WORKFLOW
1. Identify the insurance type: property, medical, motor, travel, or life.
2. Extract all visible values carefully from the image.
3. If a table is used, trace the row and column before choosing a value.
4. For property co-insurance partial loss questions, use insurance_tool first.
5. Use calculate_expression only for simple arithmetic that is not handled by insurance_tool.
6. Use the exact tool result in the final solution.
7. Solve subparts in order. Later subparts may depend on earlier answers.
8. If the question asks for a comparison, conclusion, or whether a decision is suitable, calculate the required values first, then state the conclusion clearly.

EQUATION TOOL RULE
If a formula contains an unknown value such as Loss, x, premium, insured amount, or compensation:
1. Set up the equation first.
2. If a topic rule gives a rearranged formula, use that rearranged formula and call calculate_expression.
3. If no rearranged formula is given, use solve_equations_tool.
4. Do not replace the unknown with 1.
5. Do not put the known compensation value into the Loss position.
6. Before final answer, substitute the solved value back into the original formula to verify it gives the given compensation.

INSURANCE RULES

A. PROPERTY INSURANCE TOOL RULE

For property co-insurance partial loss questions, the first calculation tool call must be insurance_tool with operation "property_partial_loss".

Do not solve property co-insurance partial loss using calculate_expression unless insurance_tool has already returned the result.

Use insurance_tool with these values:
- insurable_value
- coinsurance_percent
- deductible
- insured_amount, if given
- loss, if given
- compensation, if given
- solve_for

Choose solve_for:
- "compensation" when the question asks for compensation.
- "loss" when the question asks for amount of loss.
- "insured_amount" when the question asks for insurance purchased / amount insured / amount of insurance bought.

Every insurance_tool call must include BOTH:
1. operation
2. values

Correct tool call format:
insurance_tool({
  "operation": "property_partial_loss",
  "values": {
    "insurable_value": 530000,
    "coinsurance_percent": 75,
    "deductible": 20000,
    "loss": 400000,
    "compensation": 330000,
    "solve_for": "insured_amount"
  }
})

Do not call insurance_tool with operation only.

B. MEDICAL INSURANCE
1. Deductible order:
   For medical insurance, subtract the deductible first.

2. Payable balance:
   Payable Balance = Medical Cost - Deductible

3. For 80/20 co-insurance:
   Insurance Company Pays = 80% × Payable Balance
   Policyholder Pays = Deductible + 20% × Payable Balance

C. MOTOR INSURANCE
1. First identify:
   - engine capacity / cc
   - location: Peninsular Malaysia or Sabah/Sarawak
   - coverage type: comprehensive, TPFT, or pure third party
   - sum insured
   - NCD percentage, if given

2. Comprehensive premium:
   Read the base rate from the tariff table using engine capacity.
   Comprehensive Premium =
   Base Rate + ((Sum Insured - 1000) / 1000) × Location Rate

3. Location rate:
   Peninsular Malaysia: RM 26.00
   Sabah/Sarawak: RM 20.30

4. Calculation order:
   First calculate Sum Insured - 1000.
   Then divide by 1000.
   Then multiply by the location rate.
   Then add the base rate.

5. Third Party, Fire and Theft:
   First calculate the comprehensive premium.
   Then multiply by 0.75.

6. Pure Third Party:
   Read the flat third-party premium directly from the tariff table based on engine capacity.
   Do not use the comprehensive premium formula for pure third-party insurance.

7. No Claim Discount:
   Apply NCD after the basic premium has been found.
   Premium after NCD = Basic Premium × (1 - NCD percentage)

D. TRAVEL INSURANCE

1. Split the people in the question before reading the table.
   Identify who is travelling for work, who is travelling for vacation, and how long each person/group is insured.

2. The words "often", "frequently", or "sering" apply only to the person described as travelling often.
   For that person, use the annual premium row.
   This annual-premium rule has priority over the number of days stated for one trip.

3. If Daniel/Ali/etc. travels often for work, and his wife/children join only for a vacation:
   - Use Policyholder annual premium for Daniel/Ali/etc.
   - Use Family premium only for the wife/children vacation group.
   - Do not use the Family 11–18 days row for the person who travels often alone.

4. For a family vacation group, choose:
   - Row: number of vacation days.
   - Column: Family + destination region.

5. Before using a table value, write the table trace in calculation_scratchpad:
   Person/group = ...
   Reason = annual or day-based
   Row = ...
   Column = ...
   Value = RM ...

6. If more than one person/group is involved, calculate each premium separately before adding them.

7. Factors that affect travel insurance premium include:
   - destination
   - duration / number of days
   - number of insured people
   - coverage category, such as individual, couple, or family

E. LIFE INSURANCE
1. Annual Premium = (Face Value / Rate Unit) × Premium Rate
2. For add-on coverage, calculate the add-on face value first.
3. Calculate the add-on premium separately.
4. Total Annual Premium = Basic Premium + Add-on Premium

OUTPUT JSON
Return valid JSON only.

Use exactly this structure:
{
  "rag_usage_audit": {
    "rag_strength": "exact/strong_method/high_method/weak_method/ignore",
    "used_rag": true,
    "reusable_method_found": "",
    "special_condition_found": "",
    "values_copied_from_rag": false
  },
  "calculation_scratchpad": [
    "1. Insurance type identified: ...",
    "2. Extracted values from image: ...",
    "3. Travel insurance split if applicable: Person/group = ..., annual or day-based = ..., row = ..., column = ..., value = RM ...",
    "4. Formula selected: ...",
    "5. Tool calculation result used: ..."
  ],
  "tool_execution_plan": [
    "List the insurance_tool call for property co-insurance questions. Use calculate_expression only for simple arithmetic outside insurance_tool."
  ],
  "question_text": "Brief summary of the question.",
  "steps": [
    {
      "subpart": "a",
      "step": "Name of the step",
      "text": "Plain explanation.",
      "math": "Substituted calculation or equation."
    }
  ],
  "final_answers": {
    "a": "Final answer"
  }
}
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

    print("🛡️ Solving Insurance directly from image...")

    insurance_tools = [
        calculate_expression,
        solve_equations_tool,
        insurance_tool
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
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{new_question_image_base64}"
                }
            }
        ]),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])

    agent = create_tool_calling_agent(llm, insurance_tools, prompt)

    agent_executor = AgentExecutor(
        agent=agent,
        tools=insurance_tools,
        verbose=True,
        return_intermediate_steps=False
    )

    response = agent_executor.invoke({
        "user_prompt_text": user_prompt
    })

    return AgentOutputProcessor.process(response["output"])


def solve_taxation_math(new_question_image_base64, interpreted, rag_data, language):
    """Specialized solver for SPM Taxation Math."""

    solver_payload = prepare_solver_payload(interpreted)
    language_code = str(language or "english").lower()

    if language_code in ["bm", "ms", "malay", "bahasa_melayu", "bahasa melayu"]:
        language_label = "Bahasa Melayu"
    else:
        language_label = "English"

    language_rule = f"""
RESPONSE LANGUAGE
Selected language: {language_label}

- Write question_text, step titles, explanations, reasons, and final answer text in {language_label}.
- Keep mathematical symbols, variables, equations, units, and LaTeX unchanged.
- Use clear SPM-style explanation.
- If the selected language is Bahasa Melayu, use suitable SPM Malay terms.
"""

    system_prompt = language_rule + r"""
You are an expert Malaysian SPM Mathematics teacher specializing in Taxation.

TASK
Solve the attached question image step-by-step.
Use the image as the source of actual values.

SOURCE PRIORITY
1. Attached image: source of actual question values.
2. CURRENT QUESTION SUMMARY: rough hint only.
3. RAG context:
   - exact: follow the official marking scheme.
   - strong_method or high_method: use the method, but take values from the image.
   - weak_method: use only as light guidance.
   - ignore: solve from the image only.

GENERAL SOLVING WORKFLOW
1. Identify the taxation type:
   income tax, joint assessment, service tax, electricity bill tax, property assessment tax, quit rent, PCB reconciliation, or road tax.
2. Read wording carefully:
   - "less than", "more than", "each", "monthly", "annual", "half-year", "two nights", "3 days".
3. Extract all visible values from the image.
4. Solve subparts in order. Later subparts may depend on earlier answers.
5. Use taxation_tool for supported tax calculations.
6. Use calculate_expression only for arithmetic not supported by taxation_tool.
   For chargeable income, income tax, property assessment tax, quit rent, and road tax, use taxation_tool first.
7. Use the exact tool result in the final solution.

TOOL CALL FORMAT

Every taxation_tool call must include BOTH:
1. operation
2. values

Correct examples:

taxation_tool({
  "operation": "chargeable_income_components",
  "values": {
    "incomes": [
      {"name": "Lan income", "amount": 19000},
      {"name": "An income", "amount": 42300}
    ],
    "reliefs": [
      {"name": "individual relief", "amount": 9000},
      {"name": "lifestyle", "amount": 2500, "limit": 2500},
      {"name": "life insurance", "amount": 4500},
      {"name": "medical insurance", "amounts": [2200, 1500], "limit": 3000}
    ],
    "exemptions": [
      {"name": "donation", "amounts": [200, 300]}
    ],
    "rebates": [
      {"name": "zakat", "amount": 2000}
    ]
  }
})

taxation_tool({
  "operation": "income_tax",
  "values": {
    "base_tax": 600,
    "next_amount": 12000,
    "next_rate_percent": 8,
    "rebates": 0
  }
})

taxation_tool({
  "operation": "property_assessment_tax",
  "values": {
    "annual_value": 7200,
    "rate_percent": 4
  }
})

TAXATION RULES

A. INCOME TAX FLOW
1. Find total income.
2. Find total reliefs.
3. Find exemptions / approved donations.
4. Chargeable Income = Total Income - Reliefs - Exemptions.
5. For normal individual assessment, use taxation_tool operation "chargeable_income".
6. For joint assessment, use taxation_tool operation "chargeable_income_components".
   Do not use operation "chargeable_income" with a pre-summed reliefs value for joint assessment.
7. In joint assessment, pass the income, relief, exemption, and rebate components separately.
   Let taxation_tool calculate total_income, total_reliefs, total_exemptions, and chargeable_income.
8. Final Income Tax Payable = Tax Calculated from Table - Total Rebate (RM 400 if applicable + Zakat).

   Correct format:
   taxation_tool({
     "operation": "chargeable_income",
     "values": {
       "total_income": 160000,
       "reliefs": 18500,
       "exemptions": 400
     }
   })
6. Trace the tax table before calculating tax.
7. Use taxation_tool operation "income_tax".
8. Deduct rebates / zakat only after tax is calculated.

B. TAX RELIEFS AND LIMITS
1. If a relief has a maximum limit, compare actual spending with the limit.
2. Claimable relief = smaller of actual spending and the limit.
3. If the question says "each", multiply by the number of people/items first.
4. Keep a clear reliefs total in calculation_scratchpad.

C. TAX TABLE TRACE
Before income tax calculation, identify:
- bracket range
- base amount
- base tax
- rate percentage
- next amount = chargeable income - base amount

Use the tax table values from the image or RAG.
Do not use memory for tax table rates.

D. TOTAL REBATE & RM35000 RULE (CRITICAL)
"Tax Rebate" (Rebat Cukai) consists of TWO components in Malaysia:
1. Zakat / Fitrah payments.
2. Individual Rebate of RM 400.

The RM 400 Individual Rebate is ONLY given if the Chargeable Income is strictly LESS THAN RM 35,000. 

If the question asks to calculate "Total Rebate" (Jumlah Rebat):
- If Chargeable Income < 35000: Total Rebate = RM 400 + Zakat
- If Chargeable Income >= 35000: Total Rebate = 0 + Zakat

When using the taxation_tool for "income_tax", the "rebates" value you pass MUST be the Total Rebate (Zakat + Individual Rebate if applicable).

For joint assessment:
- Check the combined joint chargeable income before deciding whether the RM400 rebate applies.

E. JOINT ASSESSMENT
For joint assessment, husband and wife are treated as one taxpayer.


Before calling taxation_tool for chargeable income, write:
- total_income = combined income
- reliefs = total claimable reliefs only
- exemptions = approved donations only
- rebates = zakat only after tax is calculated

For joint assessment:
- INDIVIDUAL RELIEF TRAP (CRITICAL): Even if the table shows RM 9000 under the Husband column AND RM 9000 under the Wife column, you are STRICTLY FORBIDDEN from adding them together for Joint Assessment. The total Individual Relief is strictly exactly RM 9000. Do NOT calculate 9000 + 9000.
- Husband/wife relief is included only if the table/question explicitly shows a husband/wife relief row.
- Do not automatically add RM4000 just because the assessment is joint.
- If RM4000 appears in the question, identify whether it is spouse relief, life insurance, or another category before using it.
- zakat is not relief.
- zakat is not exemption.
- zakat is rebate after income tax is calculated.
- approved donation is exemption.

If scratchpad says a value is capped, the tool argument must use the capped value.
Example: if medical insurance is RM3500 but limit is RM3000, use 3000.

Use this order:
1. Combine incomes.
2. Combine approved donations / exemptions.
3. Claim individual relief RM9000 once.
4. Claim husband/wife relief RM4000 once.
5. For shared reliefs, add husband amount + wife amount first, then apply one limit.
6. Combine zakat payments as rebates after tax is calculated.
7. Zakat is not subtracted when finding chargeable income.
8. Approved donation is subtracted when finding chargeable income.

Important shared relief method:
- Lifestyle: combine both amounts first, then cap once.
- Life insurance: combine both amounts first, then cap once.
- Medical insurance: combine both amounts first, then cap once.

F. SERVICE TAX FROM TOTAL BILL
If the question asks for a service tax rate from a total bill:
1. Identify the base cost first.
2. Apply any time multiplier first, such as nights or days.
3. Tax amount = total paid - base cost.
4. Service tax rate = tax amount / base cost × 100.
G. ELECTRICITY BILL SERVICE TAX

For electricity bill service tax questions, you MUST use taxation_tool with operation "electricity_service_tax".
Correct tool call example:
taxation_tool({
  "operation": "electricity_service_tax",
  "values": {
    "total_usage_kwh": 750,
    "threshold_kwh": 600,
    "taxable_excess_amount": 81.90,
    "service_tax_rate_percent": 6
  }
})

FATAL ERROR:
Do not calculate 0.06 × total bill.
For 750 kWh with threshold 600 kWh, only the final 150 kWh block is taxable.

For electricity bills, service tax is charged only on the monetary value of usage above 600 kWh.

Use this exact calculation pattern:

1. Find the excess block amount:
   taxable_excess_amount = amount for usage above 600 kWh

2. Find the base bill:
   base_bill = sum of all block amounts

3. Find service tax:
   service_tax = tax_rate × taxable_excess_amount

4. Find final bill:
   final_bill = base_bill + service_tax

For a tariff table:
- If the final block represents usage above 600 kWh, its amount is the taxable_excess_amount.
- Do not apply service tax to the whole base_bill.
- Do not use service_tax = tax_rate × base_bill.

Example:
If m = RM51.32 and service tax is 6%,
service_tax = 0.06 × 51.32,
not 0.06 × total bill.
H. PROPERTY ASSESSMENT TAX / CUKAI PINTU
Formula:
Property Assessment Tax = Annual Value × Rate Percent / 100

If monthly rental is given:
Annual Value = monthly rental × 12

If asked for half-year tax:
Half-year tax = annual tax / 2

Use taxation_tool operation "property_assessment_tax".

I. QUIT RENT / CUKAI TANAH
Formula:
Quit Rent = land area × rate per unit area

Use taxation_tool operation "quit_rent".

J. PCB RECONCILIATION
If monthly PCB is given:
Annual PCB = monthly PCB × 12

Compare actual tax payable with annual PCB:
- If tax payable > annual PCB, balance must be paid.
- If annual PCB > tax payable, refund is given.

K. CONCEPT CHECK QUESTIONS
If the question asks whether a method is correct:
1. State whether the method is correct.
2. Mention any partially correct idea.
3. Calculate the correct amount to prove the explanation.
4. Give a clear final answer such as "Yes" or "No".

OUTPUT JSON
Return valid JSON only.

Use exactly this structure:
{
  "rag_usage_audit": {
    "rag_strength": "exact/strong_method/high_method/weak_method/ignore",
    "used_rag": true,
    "reusable_method_found": "",
    "special_condition_found": "",
    "values_copied_from_rag": false
  },
  "calculation_scratchpad": [
    "1. Taxation type identified: ...",
    "2. Extracted values from image: ...",
    "3. Reliefs total: ...",
    "4. Exemptions / donations total: ...",
    "5. Tax table trace: bracket = ..., base amount = ..., base tax = ..., rate = ..., next amount = ...",
    "6. Tool result used: ..."
  ],
  "tool_execution_plan": [
    "List the taxation_tool and calculate_expression calls needed before writing final steps."
  ],
  "question_text": "Brief summary of the question.",
  "steps": [
    {
      "subpart": "a",
      "step": "Name of the step",
      "text": "Plain explanation.",
      "math": "Substituted calculation or equation."
    }
  ],
  "final_answers": {
    "a": "Final answer"
  }
}

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

    print("💰 Solving Taxation directly from image...")

    tax_tools = [
        taxation_tool,
        calculate_expression
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
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{new_question_image_base64}"
                }
            }
        ]),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])

    agent = create_tool_calling_agent(llm, tax_tools, prompt)

    agent_executor = AgentExecutor(
        agent=agent,
        tools=tax_tools,
        verbose=True,
        return_intermediate_steps=False
    )

    response = agent_executor.invoke({
        "user_prompt_text": user_prompt
    })

    return AgentOutputProcessor.process(response["output"])
def solve_financial_management(new_question_image_base64, interpreted, rag_data, language):
    """Specialized solver for Cash Flow, ROI, Loans, Savings Goals, and Financial Management."""

    solver_payload = prepare_solver_payload(interpreted)
    language_code = str(language or "english").lower()

    if language_code in ["bm", "ms", "malay", "bahasa_melayu", "bahasa melayu"]:
        language_label = "Bahasa Melayu"
    else:
        language_label = "English"

    language_rule = f"""
RESPONSE LANGUAGE
Selected language: {language_label}

- Write question_text, step titles, explanations, reasons, and final answer text in {language_label}.
- Keep mathematical symbols, variables, equations, units, and LaTeX unchanged.
- Use clear SPM-style explanation.
- If the selected language is Bahasa Melayu, use suitable SPM Malay terms.
"""

    system_prompt = language_rule + r"""
You are an expert Malaysian SPM Mathematics teacher specializing in Financial Management.

TASK
Solve the attached question image step-by-step.
Use the image as the source of actual values.

SOURCE PRIORITY
1. Attached image: source of actual question values.
2. CURRENT QUESTION SUMMARY: rough hint only.
3. RAG context:
   - exact: follow the official marking scheme.
   - strong_method or high_method: use the method, but take values from the image.
   - weak_method: use only as light guidance.
   - ignore: solve from the image only.

GENERAL SOLVING WORKFLOW
1. Identify the question type:
   cash flow, income classification, expense classification, savings goal, loan, simple interest, investment, ROI, asset/liability, or feasibility.
2. Extract all visible values from the image.
3. Classify income and expenses before calculating cash flow.
4. Use calculate_expression for all arithmetic involving money, percentages, interest, totals, repayments, savings, or cash flow.
5. If a formula contains an unknown such as monthly saving, principal, time, rate, or cash flow, set up the equation first and use solve_equations_tool.
6. Use the exact tool result in the solution.
7. Solve subparts in order. Later subparts may depend on earlier answers.

BILINGUAL WORDING RULE
SPM papers may contain bilingual wording differences.
If the English wording sounds inconsistent with the table or Malay text, use the Malay text as the main meaning.
Common examples:
- "perbelanjaan tetap" = fixed expenses
- "perbelanjaan tidak tetap" = variable expenses
- "pendapatan aktif" = active income
- "pendapatan pasif" = passive income
- "aliran tunai" = cash flow
- "simpanan" = savings

FINANCIAL MANAGEMENT RULES

A. INCOME CLASSIFICATION
Active income:
- salary
- wages
- allowance
- commission from work
- business income from active work

Passive income:
- rent received
- dividends
- bank interest
- royalties

Income increases cash flow.

B. EXPENSE CLASSIFICATION
Fixed expenses:
- house instalment
- car instalment
- loan repayment
- insurance premium
- fixed monthly commitment

Variable expenses:
- groceries
- utility bills
- petrol
- entertainment
- emergency spending
- expenses that can change monthly

Expenses reduce cash flow.

C. CASH FLOW
Use:
Cash Flow = Total Income - Target Savings - Total Expenses

Total Expenses = Fixed Expenses + Variable Expenses

If the question gives a savings target as a percentage:
Target Savings = Total Income × percentage

Then subtract Target Savings when calculating cash flow.

D. PERCENTAGE CHANGE
If an income or expense increases by X%:
New Amount = Original Amount × (1 + X/100)

If an income or expense decreases by X%:
New Amount = Original Amount × (1 - X/100)

Apply the percentage change only to the item stated in the question.

E. SIMPLE INTEREST LOAN
Use:
Interest = Principal × Rate × Time

Rate must be in decimal form:
3.5% = 0.035

Total Repayment = Principal + Interest

If monthly repayment is asked:
Monthly Repayment = Total Repayment / Number of Months

If time is given in months:
Time in years = months / 12

F. SAVINGS GOAL
If the question asks how much must be saved monthly:
Monthly Savings Needed = Total Goal Amount / Number of Months

If time is given in years:
Number of Months = years × 12

G. FEASIBILITY / FINANCIAL WISDOM
A financial plan is feasible only if:
1. monthly cash flow is positive, and
2. required monthly savings is not more than the available monthly surplus.

If cash flow is positive:
The person is financially wise because income exceeds expenses.

If cash flow is negative:
The person is not financially wise because expenses exceed income.

If required savings is greater than surplus:
The goal is not feasible.

H. ASSETS AND LIABILITIES
Assets:
- cash
- savings
- property
- investments
- valuable owned items

Liabilities:
- debts
- loans
- credit card balance
- unpaid bills

A house is an asset.
A housing loan is a liability.

I. INVESTMENT / ROI
Dividend = Dividend Rate × Investment Amount
Capital Gain = Selling Price - Buying Price
Total Return = Dividend + Capital Gain

PROPERTY / REAL ESTATE ROI TRAP (CRITICAL):
When calculating ROI for a property bought with a loan in the SPM syllabus, you MUST follow these exact steps:
1. Net Return = Selling Price + Rental Income (if any) - [Down Payment + Total Loan Repaid + Stamp Duty + Legal Fees + Agent Commission + Other Expenses].
2. The Denominator (Total Investment) MUST be the full original Purchase Price (Harga Belian) of the property. You are STRICTLY FORBIDDEN from dividing by only the down payment.
3. ROI = (Net Return / Purchase Price) × 100%.

J. Rounding
Use full precision during tool calculation.
For final money values, display to 2 decimal places unless the question says otherwise.
For non-money long decimals, display to 4 significant figures unless the question says otherwise.
Do not paste long raw calculator decimals into final answers.

TOOL USE RULES
- Use calculate_expression for every arithmetic step.
- Use solve_equations_tool when an unknown must be solved.
- Do not invent calculated results that did not come from a tool.
- The math shown in steps must match the tool result.
- If the scratchpad, tool result, and final answer disagree, recheck and use the tool result from the correct expression.

OUTPUT JSON
Return valid JSON only.

Use exactly this structure:
{
  "rag_usage_audit": {
    "rag_strength": "exact/strong_method/high_method/weak_method/ignore",
    "used_rag": true,
    "reusable_method_found": "",
    "special_condition_found": "",
    "values_copied_from_rag": false
  },
  "calculation_scratchpad": [
    "1. Financial management type identified: ...",
    "2. Extracted values from image: ...",
    "3. Income classification: active = [...], passive = [...], total income = ...",
    "4. Expense classification: fixed = [...], variable = [...], total expenses = ...",
    "5. Formula selected: ...",
    "6. Tool result used: ..."
  ],
  "tool_execution_plan": [
    "List the calculate_expression and solve_equations_tool calls needed before writing final steps."
  ],
  "question_text": "Brief summary of the question.",
  "steps": [
    {
      "subpart": "a",
      "step": "Name of the step",
      "text": "Plain explanation.",
      "math": "Substituted calculation or equation."
    }
  ],
  "final_answers": {
    "a": "Final answer"
  }
}

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

    print("💵 Solving Financial Management directly from image...")

    finance_tools = [
        calculate_expression,
        solve_equations_tool
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
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{new_question_image_base64}"
                }
            }
        ]),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])

    agent = create_tool_calling_agent(llm, finance_tools, prompt)

    agent_executor = AgentExecutor(
        agent=agent,
        tools=finance_tools,
        verbose=True,
        return_intermediate_steps=False
    )

    response = agent_executor.invoke({
        "user_prompt_text": user_prompt
    })

    return AgentOutputProcessor.process(response["output"])