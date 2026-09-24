# parser_common.py

import os
import re
import json
import base64
import mimetypes
import asyncio

import fitz
import cv2
import pytesseract
import cloudinary
import cloudinary.uploader

from dotenv import load_dotenv
from json_repair import repair_json
from config import get_db_connection

load_dotenv()

# =========================================================
# CLOUDINARY
# =========================================================

cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_CLOUD_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_CLOUD_API_SECRET"),
    secure=True
)

def upload_cropped_diagram(local_crop_path: str, folder: str = "mathsy/question_diagrams"):
    if not local_crop_path or not os.path.exists(local_crop_path):
        return None

    # Explicitly pass the credentials here to bypass any global config issues
    result = cloudinary.uploader.upload(
        local_crop_path,
        folder=folder,
        resource_type="image",
        cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
        api_key=os.getenv("CLOUDINARY_CLOUD_API_KEY"),
        api_secret=os.getenv("CLOUDINARY_CLOUD_API_SECRET")
    )

    return {
        "url": result.get("secure_url"),
        "public_id": result.get("public_id")
    }


# =========================================================
# RATE LIMIT
# =========================================================

RATE_LIMIT_LOCK = None
LAST_API_CALL_TIME = 0.0


async def enforce_rate_limit(seconds: float = 8.0):
    global LAST_API_CALL_TIME, RATE_LIMIT_LOCK

    if RATE_LIMIT_LOCK is None:
        RATE_LIMIT_LOCK = asyncio.Lock()

    async with RATE_LIMIT_LOCK:
        now = asyncio.get_event_loop().time()
        elapsed = now - LAST_API_CALL_TIME
        delay = max(0.0, seconds - elapsed)

        if delay > 0:
            await asyncio.sleep(delay)

        LAST_API_CALL_TIME = asyncio.get_event_loop().time()


# =========================================================
# JSON / IMAGE HELPERS
# =========================================================

def encode_image_to_data_url(image_path: str) -> str:
    mime_type, _ = mimetypes.guess_type(image_path)

    if mime_type is None:
        mime_type = "image/png"

    with open(image_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("utf-8")

    return f"data:{mime_type};base64,{b64}"


def strip_code_fences(text: str) -> str:
    text = str(text or "").strip()

    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)

    return text.strip()


def extract_json_object(text: str) -> str:
    text = strip_code_fences(text)

    start = text.find("{")
    end = text.rfind("}")

    if start == -1 or end == -1 or end < start:
        raise ValueError("No JSON object found in model response.")

    return text[start:end + 1]


def fix_json_string(text: str) -> str:
    text = re.sub(r"<thought>.*?</thought>\s*", "", str(text or ""), flags=re.DOTALL | re.IGNORECASE)
    text = strip_code_fences(text)

    try:
        text = extract_json_object(text)
    except Exception:
        pass

    text = re.sub(r",\s*}", "}", text)
    text = re.sub(r",\s*]", "]", text)

    try:
        json.loads(text)
        return text
    except json.JSONDecodeError:
        return repair_json(text)


def safe_parse_json(raw_text):
    try:
        clean_text = str(raw_text or "").replace("```json", "").replace("```", "").strip()
        return json.loads(clean_text)
    except json.JSONDecodeError:
        try:
            repaired = repair_json(clean_text, return_objects=True)
            return repaired if repaired else []
        except Exception as e:
            print(f"⚠️ FATAL PARSE ERROR: {e}. Skipping corrupted response.")
            return []


def clean_part_label(value: str) -> str:
    value = str(value or "").strip().lower()
    value = value.replace("(", "").replace(")", "")
    return value


# =========================================================
# PDF HELPERS
# =========================================================

def render_pdf_pages(pdf_path: str, out_dir: str, dpi: int = 150, prefix: str = ""):
    os.makedirs(out_dir, exist_ok=True)

    doc = fitz.open(pdf_path)
    page_infos = []

    zoom = dpi / 72
    matrix = fitz.Matrix(zoom, zoom)

    for i, page in enumerate(doc):
        pix = page.get_pixmap(matrix=matrix, alpha=False)

        filename = f"{prefix}_page_{i + 1}.png" if prefix else f"page_{i + 1}.png"
        out_path = os.path.join(out_dir, filename)

        pix.save(out_path)

        page_infos.append({
            "page_no": i + 1,
            "page_image_path": out_path
        })

    doc.close()
    return page_infos


def extract_pdf_page_texts(pdf_path: str):
    doc = fitz.open(pdf_path)
    pages = []

    for i, page in enumerate(doc):
        text = page.get_text("text") or ""

        is_scanned = False
        if len(text.strip()) < 50 and len(page.get_images()) > 0:
            is_scanned = True

        pages.append({
            "page_no": i + 1,
            "text": text.strip(),
            "is_scanned": is_scanned
        })

    doc.close()
    return pages


def page_in_selected_range(page_no: int, start_page: int = None, end_page: int = None, page_numbers=None) -> bool:
    if page_numbers:
        return page_no in page_numbers

    if start_page is not None and page_no < start_page:
        return False

    if end_page is not None and page_no > end_page:
        return False

    return True


# Database connections use the central cloud-aware config.get_db_connection.


def to_json(value):
    return json.dumps(value, ensure_ascii=False)


def insert_paper(conn, title, paper_type, file_path=None, exam_name=None, subject=None, year=None):
    sql = """
    INSERT INTO papers (title, paper_type, file_path, exam_name, subject, year)
    VALUES (%s, %s, %s, %s, %s, %s)
    """

    values = (title, paper_type, file_path, exam_name, subject, year)

    cursor = conn.cursor()
    cursor.execute(sql, values)
    conn.commit()

    return cursor.lastrowid
def insert_question(conn, paper_id, question_data, image_path=None):
    sql = """
    INSERT INTO questions (
        paper_id, question_no, part, subpart, sub_subpart,
        question_type, topic, subtopic, form, chapter,

        group_id, verified_form, verified_chapter,
        classification_status, classification_confidence,

        difficulty_level, group_difficulty_level,
        group_form, group_chapter,

        exercise_stage_id, stage_index, unlock_after_stage_id,
        display_marks, marks_source,

        instructions_en, instructions_ms, sequence,
        equations, expressions, variables,

        given_values, table_data, constraints, options, target,

        has_diagram, diagram_type, difficulty, marks,
        visual_semantic_summary,

        raw_json, image_path
    )
    VALUES (
        %s, %s, %s, %s, %s,
        %s, %s, %s, %s, %s,

        %s, %s, %s, %s, %s,

        %s, %s, %s, %s,

        %s, %s, %s, %s, %s,

        %s, %s, %s, %s, %s, %s,

        %s, %s, %s, %s, %s,

        %s, %s, %s, %s, %s,

        %s, %s
    )
    """

    def safe_int(value, default=0):
        try:
            return int(value)
        except (TypeError, ValueError):
            return default

    def safe_float(value, default=0.0):
        try:
            return float(value)
        except (TypeError, ValueError):
            return default

    values = (
        paper_id,

        question_data.get("question_no", ""),
        question_data.get("part", ""),
        question_data.get("subpart", ""),
        question_data.get("sub_subpart", ""),

        question_data.get("question_type", ""),
        question_data.get("topic", ""),
        question_data.get("subtopic", ""),
        question_data.get("form", ""),
        question_data.get("chapter", ""),

        question_data.get("group_id", ""),
        question_data.get("verified_form", ""),
        question_data.get("verified_chapter", ""),
        question_data.get("classification_status", "unclassified"),
        safe_float(question_data.get("classification_confidence", 0.0)),

        safe_int(question_data.get("difficulty_level", 3), 3),
        safe_int(question_data.get("group_difficulty_level", 3), 3),

        question_data.get("group_form", ""),
        question_data.get("group_chapter", ""),

        question_data.get("exercise_stage_id", ""),
        safe_int(question_data.get("stage_index", 1), 1),
        question_data.get("unlock_after_stage_id", ""),

        safe_float(question_data.get("display_marks", 0.0)),
        question_data.get("marks_source", ""),

        to_json(question_data.get("instructions_en", [])),
        to_json(question_data.get("instructions_ms", [])),
        to_json(question_data.get("sequence", [])),

        to_json(question_data.get("equations", [])),
        to_json(question_data.get("expressions", [])),
        to_json(question_data.get("variables", [])),

        to_json(question_data.get("given_values", {})),
        to_json(question_data.get("table_data", {})),
        to_json(question_data.get("constraints", {})),
        to_json(question_data.get("options", [])),
        question_data.get("target", ""),

        bool(question_data.get("has_diagram", False)),
        question_data.get("diagram_type", ""),
        question_data.get("difficulty", ""),
        safe_float(question_data.get("marks", 0.0)),
        question_data.get("visual_semantic_summary", ""),

        to_json(question_data),
        image_path
    )

    cursor = conn.cursor()
    cursor.execute(sql, values)
    conn.commit()

    return cursor.lastrowid

def insert_question(conn, paper_id, question_data, image_path=None):
    sql = """
    INSERT INTO questions (
        paper_id, question_no, part, subpart, sub_subpart,
        question_type, topic, subtopic, form, chapter,

        group_id, verified_form, verified_chapter,
        classification_status, classification_confidence,

        difficulty_level, group_difficulty_level,
        group_form, group_chapter,

        exercise_stage_id, stage_index, unlock_after_stage_id,
        display_marks, marks_source,

        instructions_en, instructions_ms, sequence,
        equations, expressions, variables,

        given_values, table_data, constraints, options, target,

        has_diagram, diagram_type, difficulty, marks,
        visual_semantic_summary,

        raw_json, image_path
    )
    VALUES (
        %s, %s, %s, %s, %s,
        %s, %s, %s, %s, %s,

        %s, %s, %s, %s, %s,

        %s, %s, %s, %s,

        %s, %s, %s, %s, %s,

        %s, %s, %s, %s, %s, %s,

        %s, %s, %s, %s, %s,

        %s, %s, %s, %s, %s,

        %s, %s
    )
    """

    def safe_int(value, default=0):
        try:
            return int(value)
        except (TypeError, ValueError):
            return default

    def safe_float(value, default=0.0):
        try:
            return float(value)
        except (TypeError, ValueError):
            return default

    values = (
        paper_id,

        question_data.get("question_no", ""),
        question_data.get("part", ""),
        question_data.get("subpart", ""),
        question_data.get("sub_subpart", ""),

        question_data.get("question_type", ""),
        question_data.get("topic", ""),
        question_data.get("subtopic", ""),
        question_data.get("form", ""),
        question_data.get("chapter", ""),

        question_data.get("group_id", ""),
        question_data.get("verified_form", ""),
        question_data.get("verified_chapter", ""),
        question_data.get("classification_status", "unclassified"),
        safe_float(question_data.get("classification_confidence", 0.0)),

        safe_int(question_data.get("difficulty_level", 3), 3),
        safe_int(question_data.get("group_difficulty_level", 3), 3),

        question_data.get("group_form", ""),
        question_data.get("group_chapter", ""),

        question_data.get("exercise_stage_id", ""),
        safe_int(question_data.get("stage_index", 1), 1),
        question_data.get("unlock_after_stage_id", ""),

        safe_float(question_data.get("display_marks", 0.0)),
        question_data.get("marks_source", ""),

        to_json(question_data.get("instructions_en", [])),
        to_json(question_data.get("instructions_ms", [])),
        to_json(question_data.get("sequence", [])),

        to_json(question_data.get("equations", [])),
        to_json(question_data.get("expressions", [])),
        to_json(question_data.get("variables", [])),

        to_json(question_data.get("given_values", {})),
        to_json(question_data.get("table_data", {})),
        to_json(question_data.get("constraints", {})),
        to_json(question_data.get("options", [])),
        question_data.get("target", ""),

        bool(question_data.get("has_diagram", False)),
        question_data.get("diagram_type", ""),
        question_data.get("difficulty", ""),
        safe_float(question_data.get("marks", 0.0)),
        question_data.get("visual_semantic_summary", ""),

        to_json(question_data),
        image_path
    )

    cursor = conn.cursor()
    cursor.execute(sql, values)
    conn.commit()

    return cursor.lastrowid

def insert_marking_scheme(conn, paper_id, marking_data):
    final_ans = marking_data.get("final_answer", "")
    if isinstance(final_ans, (list, dict)):
        final_ans = to_json(final_ans)
    else:
        final_ans = str(final_ans)
        
    sql = """
    INSERT INTO marking_schemes (
        paper_id, group_id, question_no, part, subpart, sub_subpart,
        subpart_marks, question_total_marks, answer_type, final_answer, 
        answer_value, answer_range, units, rounding_and_tolerance, method_policy, conditional_marking_rules,
        method, steps, drawing_validation, graph_validation, notes, raw_json, answer_image_path
    )
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    
    values = (
        paper_id,
        marking_data.get("group_id", ""),
        marking_data.get("question_no", ""),
        marking_data.get("part", ""),
        marking_data.get("subpart", ""),
        marking_data.get("sub_subpart", ""),
        float(marking_data.get("subpart_marks", 0.0)),
        float(marking_data.get("question_total_marks", 0.0)),
        marking_data.get("answer_type", ""),
        final_ans,
        marking_data.get("answer_value", ""),
        to_json(marking_data.get("answer_range", [])),
        marking_data.get("units", ""),
        
        # ✨ NEW FIELDS
        to_json(marking_data.get("rounding_and_tolerance", {})),
        to_json(marking_data.get("method_policy", {})),
        to_json(marking_data.get("conditional_marking_rules", [])),
        
        marking_data.get("method", ""),
        to_json(marking_data.get("steps", [])),
        
        # ✨ NEW VALIDATION FIELDS
        to_json(marking_data.get("drawing_validation", {})),
        to_json(marking_data.get("graph_validation", {})),
        
        to_json(marking_data.get("notes", [])),
        to_json(marking_data),
        marking_data.get("answer_image_path", "")
    )

    cursor = conn.cursor()
    cursor.execute(sql, values)
    conn.commit()
    return cursor.lastrowid


def insert_question_marking_link(conn, question_id, marking_scheme_id, match_status="matched_exact"):
    sql = """
    INSERT INTO question_marking_links (question_id, marking_scheme_id, match_status)
    VALUES (%s, %s, %s)
    """

    cursor = conn.cursor()
    cursor.execute(sql, (question_id, marking_scheme_id, match_status))
    conn.commit()

    return cursor.lastrowid


def crop_diagram_above_anchor(pdf_path: str, page_no: int, image_path: str, out_path: str, dpi: int = 150, padding_percent: float = 0.10):
    """
    Finds the anchor, ERASES the instruction paragraphs (using PyMuPDF or OCR), 
    and uses Anchor Gravity Clustering to perfectly isolate the diagram.
    """
    doc = fitz.open(pdf_path)
    page = doc[page_no - 1]
    page_center_x = page.rect.width / 2
    zoom = dpi / 72

    # 1. Read image first so we can use it for OCR if needed
    img = cv2.imread(image_path)
    if img is None:
        doc.close()
        return None
        
    h_img, w_img = img.shape[:2]

    # Check if page is native or scanned (if native text is < 50 chars, it's a scan)
    is_scanned = len(page.get_text("text").strip()) < 50

    valid_anchor_y = None
    ocr_data = None

    # ==========================================
    # 2. FIND THE ANCHOR (Native vs OCR)
    # ==========================================
    if not is_scanned:
        # --- NATIVE PyMuPDF SEARCH ---
        text_rects = page.search_for("Diagram") + page.search_for("Rajah")
        for rect in text_rects:
            word_center_x = (rect.x0 + rect.x1) / 2
            if abs(word_center_x - page_center_x) < 100:
                valid_anchor_y = int(rect.y0 * zoom)
                break 
    else:
        # --- OCR FALLBACK SEARCH ---
        gray_for_ocr = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        ocr_data = pytesseract.image_to_data(gray_for_ocr, output_type=pytesseract.Output.DICT)
        
        img_center_x = w_img / 2
        
        for i in range(len(ocr_data['text'])):
            word = ocr_data['text'][i].strip().lower()
            conf = int(ocr_data['conf'][i])
            if conf > 50 and ("diagram" in word or "rajah" in word):
                x, y, w, h = ocr_data['left'][i], ocr_data['top'][i], ocr_data['width'][i], ocr_data['height'][i]
                word_center_x = x + (w / 2)
                # Check if it's near the center
                if abs(word_center_x - img_center_x) < (100 * zoom):
                    valid_anchor_y = y
                    break

    if valid_anchor_y is None:
        doc.close()
        return None

    anchor_y = valid_anchor_y

    # ==========================================
    # 3. MARGIN ERASER
    # ==========================================
    margin_width = int(w_img * 0.15)
    cv2.rectangle(img, (0, 0), (margin_width, h_img), (255, 255, 255), -1)
    cv2.rectangle(img, (w_img - margin_width, 0), (w_img, h_img), (255, 255, 255), -1)

    # ==========================================
    # 4. TEXT ERASER (Native vs OCR)
    # ==========================================
    if not is_scanned:
        # --- NATIVE TEXT ERASER ---
        for b in page.get_text("blocks"):
            if b[6] == 0: 
                text_str = b[4].replace('\n', ' ').replace('\r', '').strip()
                cv_x0, cv_y0 = int(b[0] * zoom), int(b[1] * zoom)
                cv_x1, cv_y1 = int(b[2] * zoom), int(b[3] * zoom)
                
                if cv_y1 < anchor_y:
                    is_long_enough = len(text_str) > 15
                    digit_count = sum(c.isdigit() for c in text_str)
                    is_number_heavy = digit_count >= (len(text_str) / 4) 
                    distance_to_anchor = anchor_y - cv_y1
                    is_near_bottom = distance_to_anchor < 80 
                    
                    if is_long_enough:
                        if is_number_heavy and is_near_bottom:
                            continue 
                        cv2.rectangle(img, (max(0, cv_x0-5), max(0, cv_y0-5)), (cv_x1+5, cv_y1+5), (255, 255, 255), -1)
    else:
        # --- OCR TEXT ERASER ---
        lines = {}
        for i in range(len(ocr_data['text'])):
            if int(ocr_data['conf'][i]) > 30:
                text_str = ocr_data['text'][i].strip()
                if not text_str: continue
                
                block_line_id = f"{ocr_data['block_num'][i]}_{ocr_data['line_num'][i]}"
                x, y, w, h = ocr_data['left'][i], ocr_data['top'][i], ocr_data['width'][i], ocr_data['height'][i]
                
                if block_line_id not in lines:
                    lines[block_line_id] = {"text": "", "x0": x, "y0": y, "x1": x+w, "y1": y+h}
                
                lines[block_line_id]["text"] += " " + text_str
                lines[block_line_id]["x0"] = min(lines[block_line_id]["x0"], x)
                lines[block_line_id]["y0"] = min(lines[block_line_id]["y0"], y)
                lines[block_line_id]["x1"] = max(lines[block_line_id]["x1"], x+w)
                lines[block_line_id]["y1"] = max(lines[block_line_id]["y1"], y+h)

        for line in lines.values():
            cv_y1 = line["y1"]
            if cv_y1 < anchor_y:
                text_str = line["text"]
                is_long_enough = len(text_str) > 15
                digit_count = sum(c.isdigit() for c in text_str)
                is_number_heavy = len(text_str) > 0 and digit_count >= (len(text_str) / 4)
                distance_to_anchor = anchor_y - cv_y1
                is_near_bottom = distance_to_anchor < 80
                
                if is_long_enough:
                    if is_number_heavy and is_near_bottom:
                        continue
                    cv2.rectangle(img, (max(0, line["x0"]-5), max(0, line["y0"]-5)), (line["x1"]+5, line["y1"]+5), (255, 255, 255), -1)

    doc.close()

    # ==========================================
    # 5. FIND REMAINING INK
    # ==========================================
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY_INV)
    search_roi = thresh[0:anchor_y, 0:img.shape[1]]
    contours, _ = cv2.findContours(search_roi, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if not contours:
        return None

    # ==========================================
    # 6. ANCHOR GRAVITY CLUSTERING
    # ==========================================
    all_boxes = [cv2.boundingRect(c) for c in contours]
    valid_boxes = [b for b in all_boxes if b[2] * b[3] > 20]
    
    if not valid_boxes:
        return None

    valid_boxes.sort(key=lambda b: anchor_y - (b[1] + b[3]))
    core_boxes = [valid_boxes[0]]
    
    while True:
        added = False
        c_min_x = min(b[0] for b in core_boxes)
        c_min_y = min(b[1] for b in core_boxes)
        c_max_x = max(b[0] + b[2] for b in core_boxes)
        c_max_y = max(b[1] + b[3] for b in core_boxes)
        
        for b in valid_boxes:
            if b in core_boxes:
                continue
                
            x, y, w, h = b
            if (c_min_x - 150) < (x + w) and x < (c_max_x + 150) and \
               (c_min_y - 150) < (y + h) and y < (c_max_y + 150):
                core_boxes.append(b)
                added = True
                
        if not added:
            break 
            
    final_min_x = min(b[0] for b in core_boxes)
    final_min_y = min(b[1] for b in core_boxes)
    final_max_x = max(b[0] + b[2] for b in core_boxes)
    final_max_y = max(b[1] + b[3] for b in core_boxes)

    # ==========================================
    # 7. APPLY PADDING & CROP
    # ==========================================
    box_width = final_max_x - final_min_x
    box_height = final_max_y - final_min_y
    
    pad_x = max(int(box_width * padding_percent), 20)
    pad_y = max(int(box_height * padding_percent), 20)

    x0 = max(0, final_min_x - pad_x)
    y0 = max(0, final_min_y - pad_y)
    x1 = min(img.shape[1], final_max_x + pad_x)
    y1 = min(anchor_y, final_max_y + pad_y) 

    cropped = img[y0:y1, x0:x1]
    cv2.imwrite(out_path, cropped)
    
    return out_path
