import json
import re
import cv2
import numpy as np
import pytesseract
import base64
from solving.config import openai_client, SPM_SYLLABUS_MAPPING, SUBTOPIC_TO_TOPIC, TOPIC_LOOKUP, canonical_text
from solving.format_json import AgentOutputProcessor

def format_image_for_llm(image_data):
    if not image_data: return ""
    if image_data.startswith("http://") or image_data.startswith("https://"): return image_data
    if image_data.startswith("data:image"): return image_data
    return f"data:image/jpeg;base64,{image_data}"

def extract_raw_numbers_ocr(image_base64: str) -> list:
    try:
        img_data = base64.b64decode(image_base64)
        nparr = np.frombuffer(img_data, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        gray = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
        custom_config = r'--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789.'
        raw_text = pytesseract.image_to_string(gray, config=custom_config)
        
        cleaned_numbers = []
        for line in raw_text.split('\n'):
            nums_in_line = re.findall(r'\b\d+(?:\.\d+)?\b', line)
            if len(nums_in_line) >= 4:
                for num_str in nums_in_line:
                    cleaned_numbers.append(float(num_str) if '.' in num_str else int(num_str))
        return cleaned_numbers
    except Exception as e:
        print(f"OCR Extraction Warning: {e}")
        return []
    
    
def run_base_extractor(image_base64):
    """
    Read a new question image and convert it into a structured JSON object
    for downstream retrieval and solving.
    """
    print("🔍 Interpreting new question image...")

    system_prompt = """
You are an expert SPM Mathematics interpreter with advanced spatial reasoning.

Your task is to read the uploaded image and convert it into a structured JSON object for a single question.
Do NOT solve the question. Extract only the mathematical information needed for solving.

Return ONLY valid JSON using this exact schema:
{
  "visual_semantic_summary": "",
  "introductory_instructions_ms": "",
  "instructions_en": [],
  "instructions_ms": [],
  "topic": "",
  "subtopic": "",
  "diagram_type": "",
  "subparts_present": ["e.g., a, b, c, i, ii"],
  "subpart_classification": {
    "a": {
      "topic": "",
      "subtopic": "",
      "instruction_en": "",
      "instruction_ms": "",
      "depends_on": []
    }
  },
  "allocated_marks": {},
  "equations": [],
  "expressions": [],
  "variables": [],
  "given_values": {},
  "constraints": {},
  "table_data": {},
  "diagram_data": {},
  "target": ""
}

BILINGUAL & SEQUENCE EXTRACTION RULES:
- The exam is bilingual (Malay and English).
- Separate the text: English sentences go to "instructions_en", Malay go to "instructions_ms".
- Maintain alignment: "instructions_en[0]" must be the exact translation of "instructions_ms[0]".


INTRODUCTORY CONTEXT POSITION RULE:

The introductory context is usually printed beside or immediately after the main question number, before the subpart labels.
Common layout:
Question number + introductory paragraph
(a) actual command
(b) actual command

Example:
3 Izzah cycled 12 km at a speed of (x - 3) kmh⁻¹ in (x - 2) hours.
(a) Write a quadratic equation in terms of x.
(b) Hence, calculate the value of x.

Correct extraction:
For both 3(a) and 3(b):
"introductory_instructions_en": "Izzah cycled 12 km at a speed of (x - 3) kmh⁻¹ in (x - 2) hours."

For 3(a):
"instructions_en": [
  "Write a quadratic equation in terms of x."
]

For 3(b):
"instructions_en": [
  "Hence, calculate the value of x."
]

The actual command is usually the text after the subpart label such as:
- (a), (b), (c)
- (i), (ii), (iii)
- (a)(i), (b)(ii)

Do not treat the introductory paragraph beside the main question number as the command for only part (a). It applies to all related subparts on the same page unless the layout clearly shows otherwise.

EXCEPTION:
If the question has only one main question and no visible subparts, then the full visible question text may be placed directly into instructions_en / instructions_ms, and introductory_instructions_en / introductory_instructions_ms may be left empty.
SEQUENCE AND VISUAL ORDER RULES (CRITICAL)

SUBPART CLASSIFICATION RULE:
If the question has multiple subparts, classify EACH subpart separately.

For every visible subpart such as (a), (b), (i), (ii), (b)(i), or (b)(ii), add one object inside "subpart_classification".

Each object must contain:
- topic: selected strictly from the syllabus mapping top-level keys
- subtopic: selected strictly from the selected topic's subtopic list
- instruction_en: the command for this subpart in English
- instruction_ms: the command for this subpart in Bahasa Melayu
- depends_on: list of earlier subparts this subpart depends on, or [] if none

MULTI-TOPIC GUARDRAIL (CRITICAL): SPM questions frequently mix two completely different topics in one question (e.g., Part (a) is Number Bases, Part (b) is Linear Inequalities). You MUST classify each subpart independently. Do NOT force Part (a) into Part (b)'s topic just because Part (b) is longer.

TEXT GROUPING RULES:
- Group sentences into the same "instructions" entry if they belong to the same visual block.
- If multiple lines appear inside a box, table, or grouped region, combine them into ONE entry using newline "\n".
- Do NOT split short related statements into separate entries if they are visually grouped.
- Only split into multiple entries when the content is clearly separated (e.g. paragraph vs diagram vs another paragraph).
- SUBPART DETECTION: If the question explicitly contains subparts like (a), (b), or (i), (ii), you MUST list them sequentially in the "subparts_present" array. If it is a single question with no subparts, leave the array empty [].

IMPORTANT:
- If a "Diagram/Rajah" is actually a boxed data table, information box, premium table, price list, tax table, insurance details box, or vehicle information box, DO NOT treat it as an image.
- Extract it into table_data as another table, e.g. "Diagram 12".


LOGIC EXTRACTION RULES (CRITICAL FOR SOLVING):
You must translate visual and implicit data into explicit machine-readable JSON.

1.  "visual_semantic_summary": Write a brief, high-level 1-2 sentence summary of the diagram focusing purely on geometric relationships and semantic concepts. Do NOT list coordinates or dense numbers here.
   - CRITICAL EXCEPTION FOR GRAPHS: If the image is a dense graph on grid paper (like an ogive, histogram, or continuous curve), DO NOT attempt to extract the coordinates of the curve. It will cause a system crash. Instead, simply return an empty dictionary {{}} or only extract explicitly printed text labels.
   - LINEAR INEQUALITIES & LINE STYLES (CRITICAL): If the diagram shows a shaded region representing inequalities, you MUST explicitly inspect the texture of every boundary line. State clearly in your `visual_semantic_summary` whether each boundary line is "SOLID" or "DASHED/DOTTED". (Example: "The region is bounded by a solid top line, a solid diagonal line, and a DASHED vertical line on the right").
   - For coordinate graphs or Venn Diagrams: DO NOT extract complex JSON arrays of points or regions. Instead, simply write a 1-2 sentence text summary in the "visual_semantic_summary" field (e.g., "A Cartesian graph with point S plotted at (4,2)" or "A Venn diagram showing sets G, N, and S").
2. "table_data": Extract tables cleanly into this top-level dictionary. 
   - If there are multiple tables, use their titles as keys (e.g., "Table 1"). If there is no title, use "Table_1".
   - Format each table's data as a 2D array (a list of lists) mapping the exact rows and columns to preserve the visual grid.
   - EMPTY CELLS: Preserve visual gaps by using empty strings "".
   - MULTI-LEVEL/MERGED HEADERS: If a header spans multiple columns, DO NOT skip columns. Put the text in the first cell of the span and use empty strings "" for the remaining spanned cells to maintain matrix alignment.
     Example of 1 header spanning 3 columns: [["Main Category", "", ""], ["Sub 1", "Sub 2", "Sub 3"]]
3. "constraints": Extract any real-world logical rules required to solve the problem.
   - Examples: {{"max_capacity": value, "pricing_condition": "condition details", "time_limit": "value"}}.
   - If no logical constraints exist, leave empty {{}}.
4. NUMBER BASE VISION TRAP (CRITICAL): Pay extreme attention to small numbers printed slightly below the baseline in the image, like "1001_2" or "210_3". These are Number Bases. They are NOT fractions like 100 1/2 or 210 3/10. You must extract them exactly as "1001_2" or "1001 base 2".

MATH NOTATION PRESERVATION RULES:
- Preserve vectors, matrices, coordinates, inequalities, and symbolic expressions faithfully.
- If a visual mathematical symbol is unclear, normalize it into plain inline notation.
- Example: a translation vector shown vertically should be written as (-6, 2).
- Do not output broken bracket fragments or partial symbols.
- If the exact visual formatting is unclear, prefer mathematically correct inline text.

IMPORTANT: NO PREAMBLE: Output raw JSON only. Do not write anything outside the {} brackets.

""".strip()
    syllabus_mapping_json = json.dumps(SPM_SYLLABUS_MAPPING, indent=2)
    user_prompt = f"""
STRICT TOPIC & SUBTOPIC SELECTION:
You MUST select the "topic" strictly from the top-level keys in this JSON mapping:
{syllabus_mapping_json}
Once you select a "topic", you MUST select the "subtopic" strictly from the available list of subtopics under that specific topic. Do NOT invent your own subtopics.
TOPIC DISAMBIGUATION (CRITICAL): 
- If the image contains a visual distance-time or speed-time graph, you MUST classify it as "Functions and Graphs" -> "Graphs of Motion". 
- ONLY use "Rates and Motion" for pure text-based word problems about speed and acceleration that do NOT have a graph.
- If the image shows a ladder, shadow, building, or simple right-angled triangle WITHOUT any circles, classify it as "Trigonometry" -> "Trigonometric Ratios". Do NOT classify it as "Angles and Tangents of Circles".
- OGIVE GUARDRAIL: If the diagram is an Ogive (Cumulative Frequency curve), you MUST classify it as "Statistics" -> "Data Handling". Never classify it as a Motion Graph.
- THE AREA/PERIMETER TRAP (CRITICAL Guardrail): 
    - If a question is clearly about "Transformations" (Translation, Reflection, Rotation, Enlargement) on a Cartesian plane, but one of the subparts asks you to calculate the "Area" or "Luas" of a shaded region, YOU MUST CLASSIFY THAT SUBPART AS "Transformations" -> "Enlargement". 
    - DO NOT classify it as "Mensuration" or "Perimeter and Area". 
    - It is an enlargement scale factor question ($Area = k^2 \times Area$). Mixing topics here will crash the downstream solvers.
- If image contains monthly income, active income and fixed expanses that it should be under the topic "Financial Management" and subtopic "Credit and Debt".
- If image contains chargeable income or tax relief it should be under the topic "Financial Management" and subtopic "Taxation".
- If question has property assessment tax, service tax, land tax, electricity bill service tax, it should be under the topic "Financial Management" and subtopic "Taxation".
- If question stated using the matrix method, it should be under the topic "Matrices". If the question stated do not use matrix method then it should not be under the topic "Matrices"
Interpret this SPM Mathematics question image into structured JSON.
Do not solve it.
Do not include any explanation outside the JSON.
""".strip()
    safe_image_string = format_image_for_llm(image_base64)
    user_content = [{"type": "text", "text": user_prompt}]
    if safe_image_string:
        user_content.append({"type": "image_url", "image_url": {"url": safe_image_string}})
    response = openai_client.chat.completions.create(
        model="gemini-3.5-flash-lite",
        messages=[
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": user_content 
            }
        ],
        temperature=0,
        response_format={"type": "json_object"}
    )

    raw_text = response.choices[0].message.content
    result = AgentOutputProcessor.process(raw_text)
    print(result)
    return result

def normalize_topic_subtopic(extracted: dict) -> dict:
    if not isinstance(extracted, dict):
        return extracted

    raw_topic = extracted.get("topic", "")
    raw_subtopic = extracted.get("subtopic", "")

    topic_key = canonical_text(raw_topic)
    subtopic_key = canonical_text(raw_subtopic)

    # Case 1: LLM wrongly puts subtopic into topic field
    if topic_key in SUBTOPIC_TO_TOPIC and topic_key not in TOPIC_LOOKUP:
        corrected = SUBTOPIC_TO_TOPIC[topic_key]
        extracted["topic"] = corrected["topic"]
        extracted["subtopic"] = corrected["subtopic"]
        return extracted

    # Case 2: topic is valid, subtopic is valid under same topic
    if topic_key in TOPIC_LOOKUP:
        correct_topic = TOPIC_LOOKUP[topic_key]
        allowed_subtopics = {
            canonical_text(s): s
            for s in SPM_SYLLABUS_MAPPING[correct_topic]
        }

        if subtopic_key in allowed_subtopics:
            extracted["topic"] = correct_topic
            extracted["subtopic"] = allowed_subtopics[subtopic_key]
            return extracted

    # Case 3: subtopic is valid but under another topic
    if subtopic_key in SUBTOPIC_TO_TOPIC:
        corrected = SUBTOPIC_TO_TOPIC[subtopic_key]
        extracted["topic"] = corrected["topic"]
        extracted["subtopic"] = corrected["subtopic"]
        return extracted

    return extracted