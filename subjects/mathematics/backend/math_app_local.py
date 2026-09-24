"""Local, database-only starter API for the EasyLearn Mathematics subject.

This file intentionally avoids Firebase, OpenAI, Cloudinary and Pinecone so the
core Math syllabus and question bank can be tested before cloud services are
configured. Place it beside the existing Mathematics backend ``config.py``.
"""

from __future__ import annotations

import json
import uuid
from datetime import date, datetime
from decimal import Decimal

from dotenv import load_dotenv

# Load .env before importing config.py, because config reads DB_* variables.
load_dotenv()

from flask import Flask, jsonify, request  # noqa: E402
from flask_cors import CORS  # noqa: E402

from config import get_db_connection  # noqa: E402


app = Flask(__name__)
CORS(
    app,
    resources={
        r"/api/*": {
            "origins": [
                "http://localhost:3000",
                "http://127.0.0.1:3000",
                "http://localhost:3001",
                "http://127.0.0.1:3001",
                "http://localhost:3002",
                "http://127.0.0.1:3002",
                "http://localhost:5173",
                "http://127.0.0.1:5173",
            ]
        }
    },
)

# Guest sessions live only while this Python process is running. This is
# deliberate: local testing must not modify the senior project's user records.
LOCAL_PRACTICE_SESSIONS = {}


def json_value(value):
    """Convert MySQL values into values Flask can safely return as JSON."""
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    return value


def make_json_safe(value):
    if isinstance(value, dict):
        return {key: make_json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [make_json_safe(item) for item in value]
    return json_value(value)


def parse_json_field(value, default):
    if value is None:
        return default
    if isinstance(value, (dict, list)):
        return value
    try:
        return json.loads(value)
    except (TypeError, ValueError):
        return default


def join_instruction_blocks(value):
    blocks = parse_json_field(value, [])
    if not isinstance(blocks, list):
        return str(value or "")
    return "\n\n".join(str(block).strip() for block in blocks if str(block).strip())


def get_option_text(options, label, language="en"):
    key = "text_en" if language == "en" else "text_ms"
    for option in options if isinstance(options, list) else []:
        if not isinstance(option, dict):
            continue
        if str(option.get("label", "")).strip().upper() == label:
            return str(option.get(key) or option.get("visual_description") or "").strip()
    return ""


def get_option_image(options, label):
    for option in options if isinstance(options, list) else []:
        if not isinstance(option, dict):
            continue
        if str(option.get("label", "")).strip().upper() == label:
            return str(option.get("image_path") or "").strip()
    return ""


def answer_letter_to_index(letter):
    return {"A": 0, "B": 1, "C": 2, "D": 3}.get(str(letter or "").strip().upper(), -1)


@app.get("/")
def home():
    return jsonify(
        {
            "service": "math-api-local",
            "status": "ok",
            "message": "Local Math backend is running",
        }
    )


@app.get("/health")
def health():
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT COUNT(*) AS count FROM chapters")
        chapter_count = cursor.fetchone()["count"]
        cursor.execute("SELECT COUNT(*) AS count FROM questions")
        question_count = cursor.fetchone()["count"]
        cursor.execute("SELECT COUNT(*) AS count FROM users")
        user_count = cursor.fetchone()["count"]
        return jsonify(
            {
                "service": "math-api-local",
                "status": "ok",
                "database_connected": True,
                "firebase_enabled": False,
                "ai_enabled": False,
                "chapter_count": chapter_count,
                "question_count": question_count,
                "user_count": user_count,
            }
        )
    except Exception as exc:
        return jsonify(
            {
                "service": "math-api-local",
                "status": "error",
                "database_connected": False,
                "message": str(exc),
            }
        ), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@app.get("/api/syllabus")
def syllabus():
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT
                id, form, chapter_no, name_en, name_bm, desc_en, desc_bm,
                CONCAT(chapter_no, ': ', name_en, ' - ', desc_en) AS chapter_string
            FROM chapters
            ORDER BY form, CAST(REPLACE(chapter_no, 'Chapter ', '') AS UNSIGNED)
            """
        )
        return jsonify({"success": True, "syllabus": cursor.fetchall()})
    except Exception as exc:
        return jsonify({"success": False, "message": str(exc)}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@app.get("/api/questions/kertas1")
def kertas1_questions():
    form = request.args.get("form")
    chapter = request.args.get("chapter")
    where = ["LOWER(q.question_type) = 'mcq'", "COALESCE(q.is_active, 1) = 1"]
    params = []

    if form:
        where.append("(q.form = %s OR q.verified_form = %s)")
        params.extend([form, form])
    if chapter:
        where.append("(q.chapter = %s OR q.verified_chapter = %s)")
        params.extend([chapter, chapter])

    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            f"""
            SELECT
                q.id, q.question_no, q.form, q.chapter,
                q.verified_form, q.verified_chapter,
                q.difficulty, q.difficulty_level,
                q.instructions_en, q.instructions_ms,
                q.options, q.table_data, q.image_path,
                m.final_answer AS correct_option
            FROM questions q
            LEFT JOIN question_marking_links qml ON qml.question_id = q.id
            LEFT JOIN marking_schemes m ON m.id = qml.marking_scheme_id
            WHERE {' AND '.join(where)}
            ORDER BY CAST(q.question_no AS UNSIGNED), q.id
            """,
            params,
        )
        results = []
        for row in cursor.fetchall():
            options = parse_json_field(row.get("options"), [])
            correct = row.get("correct_option") or ""
            results.append(
                {
                    "id": row.get("id"),
                    "question_no": row.get("question_no"),
                    "form": row.get("verified_form") or row.get("form"),
                    "chapter": row.get("verified_chapter") or row.get("chapter"),
                    "difficulty": row.get("difficulty") or "Easy",
                    "difficulty_level": row.get("difficulty_level") or 1,
                    "question_en": join_instruction_blocks(row.get("instructions_en")),
                    "question_bm": join_instruction_blocks(row.get("instructions_ms")),
                    "question_image": row.get("image_path") or "",
                    "table_data": parse_json_field(row.get("table_data"), {}),
                    "optA_en": get_option_text(options, "A", "en"),
                    "optB_en": get_option_text(options, "B", "en"),
                    "optC_en": get_option_text(options, "C", "en"),
                    "optD_en": get_option_text(options, "D", "en"),
                    "optA_bm": get_option_text(options, "A", "bm"),
                    "optB_bm": get_option_text(options, "B", "bm"),
                    "optC_bm": get_option_text(options, "C", "bm"),
                    "optD_bm": get_option_text(options, "D", "bm"),
                    "optA_image": get_option_image(options, "A"),
                    "optB_image": get_option_image(options, "B"),
                    "optC_image": get_option_image(options, "C"),
                    "optD_image": get_option_image(options, "D"),
                    "correct_answer_index": answer_letter_to_index(correct),
                    "correct_option": correct,
                    "explanation_en": f"Correct answer: {correct}",
                    "explanation_bm": f"Jawapan betul: {correct}",
                    "explanation_image": "",
                }
            )
        return jsonify({"success": True, "questions": make_json_safe(results)})
    except Exception as exc:
        return jsonify({"success": False, "message": str(exc)}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@app.get("/api/questions/kertas2")
def kertas2_questions():
    form = request.args.get("form")
    chapter = request.args.get("chapter")
    if not form or not chapter:
        return jsonify({"success": False, "message": "Missing form or chapter"}), 400

    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT *
            FROM questions
            WHERE (form = %s OR verified_form = %s)
              AND (chapter = %s OR verified_chapter = %s)
              AND LOWER(question_type) <> 'mcq'
              AND COALESCE(is_active, 1) = 1
            ORDER BY id
            """,
            (form, form, chapter, chapter),
        )
        rows = cursor.fetchall()
        for row in rows:
            for field in (
                "instructions_en",
                "instructions_ms",
                "sequence",
                "image_urls",
                "table_data",
                "given_values",
                "options",
            ):
                if field in row:
                    default = {} if field in {"table_data", "given_values"} else []
                    row[field] = parse_json_field(row.get(field), default)
        return jsonify({"success": True, "questions": make_json_safe(rows)})
    except Exception as exc:
        return jsonify({"success": False, "message": str(exc)}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@app.post("/api/practice/start-session")
def start_local_practice_session():
    data = request.get_json(silent=True) or {}
    chapter_id = data.get("chapter_id")
    paper_type = str(data.get("paper_type") or "").lower()

    if not chapter_id or paper_type not in {"kertas1", "kertas2"}:
        return jsonify({"success": False, "message": "Invalid practice session data."}), 400

    practice_id = uuid.uuid4().hex
    LOCAL_PRACTICE_SESSIONS[practice_id] = {
        "chapter_id": chapter_id,
        "paper_type": paper_type,
        "language": data.get("session_language") or "english",
        "seen_question_ids": set(),
        "attempts": [],
    }
    return jsonify({"success": True, "practice_id": practice_id})


@app.get("/api/practice/next-item")
def next_local_practice_item():
    practice_id = request.args.get("practice_id")
    form = request.args.get("form")
    chapter = request.args.get("chapter")
    paper_type = str(request.args.get("paper_type") or "").lower()
    session = LOCAL_PRACTICE_SESSIONS.get(practice_id)

    if not session:
        return jsonify({"success": False, "message": "Local practice session was not found."}), 404
    if not form or not chapter or paper_type not in {"kertas1", "kertas2"}:
        return jsonify({"success": False, "message": "Missing form, chapter, or paper type."}), 400

    if paper_type == "kertas1":
        response = kertas1_questions()
    else:
        response = kertas2_questions()

    # Both local question routes return Flask Response objects on success.
    if isinstance(response, tuple):
        response_object, status_code = response
        if status_code >= 400:
            return response
        payload = response_object.get_json() or {}
    else:
        payload = response.get_json() or {}

    questions = payload.get("questions") or []
    unseen = [q for q in questions if q.get("id") not in session["seen_question_ids"]]

    if not unseen:
        return jsonify(
            {
                "success": True,
                "item_type": "session_complete",
                "paper_type": paper_type,
                "questions": [],
                "variant": None,
                "adaptive": {"status": "all_completed", "local_mode": True},
            }
        )

    first = unseen[0]
    if paper_type == "kertas1":
        selected = [first]
    else:
        group_id = str(first.get("group_id") or "").strip()
        group_chapter = str(first.get("group_chapter") or "").strip()
        stage_id = str(first.get("exercise_stage_id") or "").strip()

        if group_id and group_chapter.lower() != "mixed":
            selected = [q for q in unseen if str(q.get("group_id") or "").strip() == group_id]
        elif stage_id:
            selected = [
                q for q in unseen
                if str(q.get("exercise_stage_id") or "").strip() == stage_id
            ]
        else:
            selected = [first]

    session["seen_question_ids"].update(q.get("id") for q in selected if q.get("id") is not None)

    return jsonify(
        {
            "success": True,
            "item_type": "normal_question",
            "paper_type": paper_type,
            "questions": make_json_safe(selected),
            "adaptive": {"status": "selected", "local_mode": True},
        }
    )


@app.post("/api/practice/save-attempt")
def save_local_attempt():
    data = request.get_json(silent=True) or {}
    practice_id = data.get("practice_id")
    session = LOCAL_PRACTICE_SESSIONS.get(practice_id)
    if not session:
        return jsonify({"success": False, "message": "Local practice session was not found."}), 404

    attempt = data.get("attempt") or {}
    session["attempts"].append(attempt)
    return jsonify(
        {
            "success": True,
            "message": "Attempt kept in local guest memory.",
            "queued_review_variant_id": None,
            "is_grouped_k2": False,
            "is_group_final_stage": True,
            "group_id": attempt.get("group_id_snapshot"),
            "group_attempt_id": None,
            "group_stage_count": 1,
            "group_score": attempt.get("score"),
            "group_max_score": attempt.get("max_score"),
            "group_is_correct": attempt.get("is_correct"),
        }
    )


@app.post("/api/practice/end-session")
def end_local_practice_session():
    data = request.get_json(silent=True) or {}
    session = LOCAL_PRACTICE_SESSIONS.get(data.get("practice_id"))
    if not session:
        return jsonify({"success": False, "message": "Local practice session was not found."}), 404
    return jsonify(
        {
            "success": True,
            "message": "Local practice session ended.",
            "attempt_count": len(session["attempts"]),
        }
    )


@app.post("/api/questions/kertas1/explain")
def explain_local_kertas1():
    data = request.get_json(silent=True) or {}
    correct = str(data.get("correct_option") or "").strip().upper()
    selected = str(data.get("selected_option") or "").strip().upper()
    is_correct = bool(data.get("is_correct"))

    if is_correct:
        explanation_en = f"Correct. You selected {selected}, which matches the answer {correct}."
        explanation_bm = f"Betul. Anda memilih {selected}, yang sepadan dengan jawapan {correct}."
    else:
        explanation_en = f"Your answer was {selected}. The stored correct answer is {correct}. AI reasoning is disabled in local mode."
        explanation_bm = f"Jawapan anda ialah {selected}. Jawapan betul yang disimpan ialah {correct}. Penerangan AI dinyahaktifkan dalam mod tempatan."

    return jsonify(
        {
            "success": True,
            "explanation_en": explanation_en,
            "explanation_bm": explanation_bm,
            "local_mode": True,
        }
    )


@app.post("/api/log-activity")
def log_local_activity():
    return jsonify({"success": True, "saved": False, "local_mode": True})


@app.put("/api/users/me/language")
def update_local_language():
    data = request.get_json(silent=True) or {}
    language = data.get("language")
    if language not in {"english", "bm"}:
        return jsonify({"success": False, "message": "Invalid language."}), 400
    return jsonify({"success": True, "language": language, "local_mode": True})


if __name__ == "__main__":
    # Math uses port 5001 so it does not conflict with History on port 5000.
    app.run(host="127.0.0.1", port=5001, debug=True)
