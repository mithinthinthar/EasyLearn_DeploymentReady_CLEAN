from decimal import Decimal
import json
import base64
import copy
import re
from flask import Flask, request, jsonify, g
from functools import wraps
from flask_cors import CORS
import numpy as np
import uuid
from werkzeug.utils import secure_filename
import cloudinary
import cloudinary.uploader
import tempfile
import asyncio
import secrets
import string
import firebase_admin
from firebase_admin import credentials
from openai import AsyncOpenAI

from solving.llm_engine import (
    solve_new_question,
)
from solving.grader import (
    grade_known_stage,
    grade_new_question,
    explain_known_question
)
from solving.variant_generator import (
    build_original_group_retry_variant,
    generate_review_variant,
    grade_review_variant,
)
from solving.config import openai_client
from config import get_db_connection
from dotenv import load_dotenv
from chatbot import get_chatbot_response
from datetime import date, datetime, timedelta
from collections import Counter
import os
# for firebase login and register
import firebase_admin
from firebase_admin import credentials, auth as firebase_auth
from solving.adaptive_engine import (
    update_topic_mastery_after_attempt,
    choose_next_practice_unit
)
# for model training
import joblib
import pandas as pd

# for generating student code
import random
import string

# for chatbot
import json
import re

# for agentic ai chatbot
from chatbot_agent import (
    build_student_state,
    select_tutoring_strategy,
    build_agent_instruction,
)

# for models

# for admin firebase
# Load backend environment variables
BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BACKEND_DIR, ".env"))

cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=(
        os.getenv("CLOUDINARY_API_KEY")
        or os.getenv("CLOUDINARY_CLOUD_API_KEY")
    ),
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
    secure=True
)

# Initialize Firebase Admin exactly once
firebase_service_account_json = os.getenv(
    "FIREBASE_SERVICE_ACCOUNT_JSON", ""
).strip()

firebase_service_account_base64 = os.getenv(
    "FIREBASE_SERVICE_ACCOUNT_BASE64", ""
).strip()

firebase_service_account_path = os.getenv(
    "FIREBASE_SERVICE_ACCOUNT_PATH", ""
).strip()

if not firebase_admin._apps:
    if firebase_service_account_json:
        service_account_info = json.loads(
            firebase_service_account_json
        )

        if "private_key" in service_account_info:
            service_account_info["private_key"] = (
                service_account_info["private_key"]
                .replace("\\n", "\n")
            )

        firebase_credential = credentials.Certificate(
            service_account_info
        )

    elif firebase_service_account_base64:
        decoded_json = base64.b64decode(
            firebase_service_account_base64
        ).decode("utf-8")

        firebase_credential = credentials.Certificate(
            json.loads(decoded_json)
        )

    elif firebase_service_account_path:
        if not os.path.isabs(firebase_service_account_path):
            firebase_service_account_path = os.path.join(
                BACKEND_DIR,
                firebase_service_account_path
            )

        firebase_credential = credentials.Certificate(
            firebase_service_account_path
        )

    else:
        raise RuntimeError(
            "Firebase credentials are missing. "
            "Set FIREBASE_SERVICE_ACCOUNT_PATH in .env."
        )

    firebase_admin.initialize_app(firebase_credential)
    print("Firebase Admin connected successfully.")

def verify_firebase_token(id_token):
    decoded_token = firebase_auth.verify_id_token(id_token)
    return decoded_token

def get_bearer_token():
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return None
    return auth_header.split(" ", 1)[1].strip()


def load_current_user(required_roles=None):
    token = get_bearer_token()
    if not token:
        return None, ("Missing authorization token.", 401)

    try:
        decoded = verify_firebase_token(token)
    except Exception:
        return None, ("Invalid or expired token.", 401)

    firebase_uid = decoded.get("uid")
    email = decoded.get("email")

    conn = None
    cursor = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT *
            FROM users
            WHERE (firebase_uid = %s OR email = %s)
              AND is_active = 1
            LIMIT 1
            """,
            (firebase_uid, email),
        )
        user = cursor.fetchone()

        if not user:
            return None, ("Authenticated user not found in database.", 404)

        if required_roles and user["role"] not in required_roles:
            return None, ("Forbidden.", 403)

        return user, None

    except Exception:
        return None, ("Failed to load authenticated user.", 500)

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def require_auth(*roles):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            required_roles = set(roles) if roles else None
            user, error = load_current_user(required_roles)

            if error:
                message, status_code = error
                return jsonify({"success": False, "message": message}), status_code

            g.current_user = user
            return fn(*args, **kwargs)

        return wrapper
    return decorator

def is_parent_linked_to_student(parent_id, student_id):
    conn = None
    cursor = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT link_id
            FROM parent_student_links
            WHERE parent_id = %s
              AND student_id = %s
              AND is_active = 1
            LIMIT 1
            """,
            (parent_id, student_id),
        )
        link = cursor.fetchone()
        return bool(link)

    except Exception as e:
        print("PARENT LINK CHECK ERROR:", e)
        return False

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# helper function to check if language is Bahasa Melayu
def is_bm(lang):
    return str(lang).lower() == "bm"

# function to generate unique student code
def generate_student_code():
    return "STU-" + "".join(random.choices(string.digits, k=7))

GRADE_ORDER = ["G", "E", "D", "C", "C+", "B", "B+", "A-", "A", "A+"]

def format_duration_hm(total_seconds):
    total_seconds = int(total_seconds or 0)
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    return f"{hours}h {minutes}m"

def format_week_delta(delta_seconds, lang="english"):
    delta_seconds = int(delta_seconds or 0)

    if delta_seconds == 0:
        return "No change this week" if not is_bm(lang) else "Tiada perubahan minggu ini"

    sign = "+" if delta_seconds > 0 else "-"
    abs_seconds = abs(delta_seconds)
    hours = abs_seconds // 3600
    minutes = (abs_seconds % 3600) // 60

    if is_bm(lang):
        return f"{sign}{hours}j {minutes}m minggu ini"
    return f"{sign}{hours}h {minutes}m this week"

def format_hour_window(start_hour, duration_minutes):
    start_hour = int(start_hour if start_hour is not None else 20)
    duration_minutes = int(duration_minutes if duration_minutes else 40)

    start_dt = datetime(2000, 1, 1, start_hour, 0)
    end_dt = start_dt + timedelta(minutes=duration_minutes)

    start_str = start_dt.strftime("%I:%M %p").lstrip("0")
    end_str = end_dt.strftime("%I:%M %p").lstrip("0")
    return f"{start_str} - {end_str}"

def get_weekday_labels(lang="english"):
    if is_bm(lang):
        return ["Isn", "Sel", "Rab", "Kha", "Jum", "Sab", "Aha"]
    return ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

def clamp(value, min_value, max_value):
    return max(min_value, min(max_value, value))

def calculate_prediction_confidence(
    model,
    features,
    predicted_grade,
    total_questions_attempted,
    total_sessions,
    overall_accuracy_percent,
):
    try:
        if model and hasattr(model, "predict_proba"):
            probabilities = model.predict_proba(features)[0]
            classes = list(getattr(model, "classes_", []))

            if predicted_grade in classes:
                return int(round(probabilities[classes.index(predicted_grade)] * 100))

            return int(round(max(probabilities) * 100))
    except Exception as e:
        print("CONFIDENCE CALC ERROR:", e)

    heuristic = 40
    heuristic += min(total_questions_attempted, 200) * 0.18
    heuristic += min(total_sessions, 25) * 1.2
    heuristic += min(overall_accuracy_percent, 100) * 0.18

    return int(clamp(round(heuristic), 35, 95))

def expand_k2_rows_to_full_group(cursor, rows, form=None, chapter=None):
    if not rows:
        return rows

    first_row = rows[0]
    group_id = first_row.get("group_id")
    group_chapter = str(first_row.get("group_chapter") or "").strip()

    if not group_id:
        return rows

    if group_chapter == "Mixed":
        return rows

    cursor.execute("""
        SELECT *
        FROM questions
        WHERE group_id = %s
          AND COALESCE(group_chapter, '') != 'Mixed'
          AND COALESCE(NULLIF(verified_form, ''), form) = %s
          AND COALESCE(NULLIF(verified_chapter, ''), chapter) = %s
        ORDER BY
          COALESCE(stage_index, 1),
          question_no + 0,
          part,
          subpart,
          sub_subpart
    """, (group_id, form, chapter))

    grouped_rows = cursor.fetchall() or []
    return grouped_rows if grouped_rows else rows
def calculate_streaks(session_dates):
    if not session_dates:
        return 0, 0

    unique_dates = sorted(set(session_dates))
    if not unique_dates:
        return 0, 0

    best_streak = 1
    running = 1

    for i in range(1, len(unique_dates)):
        if (unique_dates[i] - unique_dates[i - 1]).days == 1:
            running += 1
        else:
            running = 1
        best_streak = max(best_streak, running)

    today = datetime.now().date()
    latest_date = unique_dates[-1]

    if (today - latest_date).days > 1:
        current_streak = 0
    else:
        current_streak = 1
        for i in range(len(unique_dates) - 1, 0, -1):
            if (unique_dates[i] - unique_dates[i - 1]).days == 1:
                current_streak += 1
            else:
                break

    return current_streak, best_streak

def get_topic_status(accuracy, attempts):
    if attempts <= 0:
        return "unpracticed"
    if accuracy >= 80:
        return "mastered"
    if accuracy < 50:
        return "review"
    return "average"

def get_priority_label(index, lang="english"):
    if index == 0:
        return "High" if not is_bm(lang) else "Tinggi"
    if index == 1:
        return "Medium" if not is_bm(lang) else "Sederhana"
    return "Low" if not is_bm(lang) else "Rendah"

def get_next_session_label(best_hour, lang="english"):
    now = datetime.now()
    if best_hour >= 18:
        return "Tonight" if not is_bm(lang) else "Malam ini"
    if best_hour >= 12:
        return "This afternoon" if not is_bm(lang) else "Petang ini"
    return "Next session" if not is_bm(lang) else "Sesi seterusnya"


#### FOR CHATBOT ####
def normalize_chat_language(raw_language):
    text = str(raw_language or "").strip().lower()
    if text in ["bm", "bahasa melayu", "bahasa_melayu", "malay"]:
        return "bm"
    return "english"


def get_chatbot_display_language(language_code):
    return "Bahasa Melayu" if language_code == "bm" else "English"


def parse_json_column(value):
    """
    MySQL JSON may come back as dict, string, bytes, or None depending on connector.
    This normalizes it into a Python dict/list or None.
    """
    if not value:
        return None

    if isinstance(value, (dict, list)):
        return value

    if isinstance(value, bytes):
        value = value.decode("utf-8")

    if isinstance(value, str):
        try:
            return json.loads(value)
        except Exception:
            return None

    return None


def make_json_safe(value):
    if isinstance(value, Decimal):
        return float(value)

    if isinstance(value, (datetime, date)):
        return value.isoformat()

    if isinstance(value, dict):
        return {
            str(key): make_json_safe(val)
            for key, val in value.items()
        }

    if isinstance(value, list):
        return [make_json_safe(item) for item in value]

    if isinstance(value, tuple):
        return [make_json_safe(item) for item in value]

    return value

def is_valid_quick_snap_context(value):
    return isinstance(value, dict) and value.get("source") == "quick_snap"


def build_quick_snap_chat_title(context, fallback_message, lang="english"):
    if not context:
        return build_chat_title_from_message(fallback_message, lang)

    mode = context.get("mode")

    if mode == "check_my_work":
        mode_label = "Check" if not is_bm(lang) else "Semak"
    elif mode == "solve_question":
        mode_label = "Solve" if not is_bm(lang) else "Selesai"
    else:
        mode_label = "Math"

    question_text = (
        context.get("question_text")
        or context.get("detected_question")
        or context.get("result_summary")
        or fallback_message
        or ""
    )

    question_text = re.sub(r"\s+", " ", str(question_text)).strip()

    generic_titles = {
        "ai grading report",
        "ai solution generated",
        "quick snap result",
        "not available",
    }

    if not question_text or question_text.lower() in generic_titles:
        question_text = re.sub(r"\s+", " ", str(fallback_message or "")).strip()

    if len(question_text) > 48:
        question_text = question_text[:48].rstrip() + "..."

    if not question_text:
        question_text = "Question"

    return f"QS {mode_label}: {question_text}"


def build_quick_snap_llm_message(quick_snap_context, user_message):
    """
    This is sent to LLM only.
    It is NOT saved as the student's visible chat message.
    """
    if not quick_snap_context:
        return user_message

    return f"""
The student is asking a follow-up question about a Quick Snap result.

Important:
- Use the Quick Snap context below to understand what the student is referring to.
- Do NOT repeat the whole solution or marking report unless the student asks for it.
- Answer only the student's specific follow-up question.
- Keep the explanation clear, simple, and suitable for SPM Mathematics.

Quick Snap context:
{json.dumps(quick_snap_context, ensure_ascii=False, indent=2)}

Student follow-up question:
{user_message}
""".strip()


def build_quick_snap_retrieval_query(quick_snap_context, user_message):
    """
    This improves RAG retrieval.
    Instead of searching only 'why is step 2 wrong',
    it searches using the original detected question too.
    """
    if not quick_snap_context:
        return user_message

    question_text = quick_snap_context.get("question_text") or ""
    final_answer = quick_snap_context.get("final_answer") or ""

    return f"""
{question_text}

{final_answer}

{user_message}
""".strip()

def build_chat_title_from_message(message, lang="english"):
    cleaned = " ".join(str(message or "").strip().split())
    if not cleaned:
        return "Chat Baharu" if is_bm(lang) else "New Chat"
    return cleaned[:60] + ("..." if len(cleaned) > 60 else "")

def student_owns_chat_session(chat_session_id, student_id):
    conn = None
    cursor = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT chat_session_id
            FROM chat_sessions
            WHERE chat_session_id = %s
              AND student_id = %s
              AND is_archived = 0
            LIMIT 1
            """,
            (chat_session_id, student_id),
        )
        session = cursor.fetchone()
        return bool(session)

    except Exception as e:
        print("CHAT SESSION OWNERSHIP ERROR:", e)
        return False

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

app = Flask(__name__)
#load grade prediction model
try:
    grade_model = joblib.load("models/grade_score_regressor_model.pkl")
    print("Success: Grade Prediction Model Loaded Successfully!")
except Exception as e:
    print("Warning: Grade model not found. Run train_grade_regression_model.py first.")
    grade_model = None

# load study pattern model
pattern_model = None
pattern_scaler = None
pattern_persona_map = {}

try:
    study_pattern_data = joblib.load("models/study_pattern_model.pkl")
    pattern_model = study_pattern_data.get("model")
    pattern_scaler = study_pattern_data.get("scaler")
    pattern_persona_map = study_pattern_data.get("persona_map", {})
    print("Success: Study Pattern AI Loaded Successfully!")
except Exception as e:
    print("Warning: Study Pattern model not found.")

MATH_FRONTEND_ORIGINS = [
    origin.strip()
    for origin in os.getenv("MATH_FRONTEND_ORIGINS", "").split(",")
    if origin.strip()
]
if not MATH_FRONTEND_ORIGINS:
    MATH_FRONTEND_ORIGINS = [
        "http://localhost:3001",
        "http://127.0.0.1:3001",
    ]

CORS(app, resources={
    r"/api/*": {
        "origins": MATH_FRONTEND_ORIGINS,
        "methods": ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
        "supports_credentials": True
    }
})

@app.route("/")
def home():
    return {"message": "Backend running"}


@app.route("/health")
def health():
    return {"status": "ok", "service": "mathematics-api"}


@app.route("/api/auth/lookup-email", methods=["POST"])
def lookup_email():
    data = request.json or {}
    email = (data.get("email") or "").strip().lower()

    if not email:
        return jsonify({
            "success": False,
            "message": "Email is required."
        }), 400

    conn = None
    cursor = None

    try:
        db_user = None

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT id, role, auth_provider, language, email, is_active
            FROM users
            WHERE email = %s
            LIMIT 1
            """,
            (email,),
        )
        db_user = cursor.fetchone()

        if db_user and int(db_user.get("is_active", 1) or 0) != 1:
            return jsonify({
                "success": False,
                "message": "Your account has been deactivated. Please contact EasyLearn through 'support@mathsy.com'.",
                "account_deactivated": True
            }), 403

        try:
            fb_user = firebase_auth.get_user_by_email(email)
        except firebase_auth.UserNotFoundError:
            return jsonify({
                "success": True,
                "next_step": "password_signup",
                "email": email,
                "db_user_exists": False,
            }), 200

        provider_ids = set()
        for provider in getattr(fb_user, "provider_data", []) or []:
            provider_id = getattr(provider, "provider_id", None)
            if provider_id:
                provider_ids.add(provider_id)

        has_password = "password" in provider_ids
        has_google = "google.com" in provider_ids

        if has_google and not has_password:
            return jsonify({
                "success": True,
                "next_step": "google_only",
                "email": email,
                "db_user_exists": bool(db_user),
                "user_role": db_user["role"] if db_user else None,
                "contact_message": "Please contact system administrator for admin account assistance." if db_user and db_user["role"] == "admin" else None,
            }), 200

        if has_password:
            return jsonify({
                "success": True,
                "next_step": "password_login",
                "email": email,
                "db_user_exists": bool(db_user),
                "email_verified": bool(getattr(fb_user, "email_verified", False)),
                "user_role": db_user["role"] if db_user else None,
                "contact_message": "Please contact system administrator for admin account assistance." if db_user and db_user["role"] == "admin" else None,
            }), 200

        return jsonify({
            "success": True,
            "next_step": "password_signup",
            "email": email,
            "db_user_exists": bool(db_user),
            "user_role": db_user["role"] if db_user else None,
            "contact_message": None,
        }), 200

    except Exception as e:
        print("LOOKUP EMAIL ERROR:", e)
        return jsonify({
            "success": False,
            "message": "Failed to check email."
        }), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@app.route("/api/auth/register", methods=["POST"])
def register():
    data = request.json

    token = data.get("token")
    name = data.get("name")
    role = data.get("role")
    language = data.get("language")
    photo_url = data.get("photo_url")

    if role not in ["student", "parent"]:
        return jsonify({
            "success": False,
            "message": "Invalid role"
        }), 400

    if language not in ["english", "bm"]:
        return jsonify({
            "success": False,
            "message": "Please choose a valid language"
        }), 400

    cursor = None
    conn = None

    try:
        decoded = verify_firebase_token(token)

        firebase_uid = decoded.get("uid")
        email = decoded.get("email")
        email_verified = decoded.get("email_verified", False)

        provider_data = decoded.get("firebase", {})
        sign_in_provider = provider_data.get("sign_in_provider", "password")

        if sign_in_provider == "google.com":
            auth_provider = "google"
        else:
            auth_provider = "email"

        if auth_provider == "email" and not email_verified:
            return jsonify({
                "success": False,
                "message": "Please verify your email before completing registration."
            }), 403

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            "SELECT * FROM users WHERE email = %s OR firebase_uid = %s",
            (email, firebase_uid)
        )
        existing_user = cursor.fetchone()

        student_code = None

        if role == "student":
            while True:
                student_code = generate_student_code()
                cursor.execute("SELECT id FROM users WHERE student_code = %s", (student_code,))
                existing_code = cursor.fetchone()
                if not existing_code:
                    break

        if existing_user:
            return jsonify({
                "success": False,
                "message": "Account already exists. Please login instead."
            }), 400

        insert_query = """
            INSERT INTO users (firebase_uid, name, email, role, language, auth_provider, photo_url, student_code)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(insert_query, (
            firebase_uid,
            name,
            email,
            role,
            language,
            auth_provider,
            photo_url,
            student_code
        ))
        conn.commit()

        return jsonify({
            "success": True,
            "message": "User registered successfully"
        })

    except Exception as e:
        print("REGISTER ERROR:", e)
        return jsonify({
            "success": False,
            "message": "Registration failed"
        }), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@app.route("/api/auth/login", methods=["POST"])
def login():
    data = request.json
    token = data.get("token")
    photo_url = data.get("photo_url")

    cursor = None
    conn = None

    try:
        decoded = verify_firebase_token(token)

        firebase_uid = decoded.get("uid")
        email = decoded.get("email")
        email_verified = decoded.get("email_verified", False)

        provider_data = decoded.get("firebase", {})
        sign_in_provider = provider_data.get("sign_in_provider", "")

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        query = "SELECT * FROM users WHERE firebase_uid = %s OR email = %s"
        cursor.execute(query, (firebase_uid, email))
        user = cursor.fetchone()

        if user and int(user.get("is_active", 1) or 0) != 1:
            return jsonify({
                "success": False,
                "message": "Your account has been deactivated. Please contact the administrator.",
                "account_deactivated": True
            }), 403

        if user and sign_in_provider == "password" and not email_verified:
            return jsonify({
                "success": False,
                "message": "Please verify your email before continuing.",
                "requires_verification": True
            }), 403

        if user and photo_url and photo_url != user.get("photo_url"):
            update_query = "UPDATE users SET photo_url = %s WHERE id = %s"
            cursor.execute(update_query, (photo_url, user["id"]))
            conn.commit()
            user["photo_url"] = photo_url

        if not user:
            return jsonify({
                "success": False,
                "message": "No account found. Please complete registration.",
            }), 404

        return jsonify({
            "success": True,
            "message": "Login successful",
            "user": {
                "id": user["id"],
                "name": user["name"],
                "email": user["email"],
                "role": user["role"],
                "language": user["language"],
                "auth_provider": user["auth_provider"],
                "photo_url": user["photo_url"],
                "student_code": user["student_code"]
            }
        })

    except Exception as e:
        print("LOGIN ERROR:", e)
        return jsonify({
            "success": False,
            "message": "Login failed"
        }), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# endpoint for user to update their language preference
@app.route("/api/users/me/language", methods=["PUT"])
@require_auth("student", "parent", "admin")
def update_user_language():
    data = request.json
    language = data.get("language")

    if language not in ["english", "bm"]:
        return jsonify({
            "success": False,
            "message": "Invalid language"
        }), 400

    conn = None
    cursor = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            "UPDATE users SET language = %s WHERE id = %s",
            (language, g.current_user["id"])
        )
        conn.commit()

        return jsonify({
            "success": True,
            "message": "Language updated successfully"
        })

    except Exception as e:
        print("UPDATE LANGUAGE ERROR:", e)
        return jsonify({
            "success": False,
            "message": "Failed to update language"
        }), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def get_student_chatbot_summary(cursor, student_id):
    """
    Build a lightweight learner summary for the chatbot agent.
    Uses practice_sessions, attempts, and chapters.
    """

    summary = {
        "overall_accuracy_percent": 0,
        "recent_accuracy_percent": 0,
        "total_questions_attempted": 0,
        "weak_topics": [],
        "strong_topics": [],
        "study_pattern": "unknown",
    }

    # 1. Overall accuracy + total attempts
    cursor.execute(
        """
        SELECT
            COUNT(*) AS total_attempts,
            ROUND(AVG(is_correct) * 100, 2) AS overall_accuracy
        FROM attempts
        WHERE user_id = %s
        """,
        (student_id,),
    )
    overall = cursor.fetchone() or {}

    summary["total_questions_attempted"] = int(overall.get("total_attempts") or 0)
    summary["overall_accuracy_percent"] = float(overall.get("overall_accuracy") or 0)

    # 2. Recent accuracy from latest 20 attempts
    cursor.execute(
        """
        SELECT
            ROUND(AVG(is_correct) * 100, 2) AS recent_accuracy
        FROM (
            SELECT is_correct
            FROM attempts
            WHERE user_id = %s
            ORDER BY attempted_at DESC
            LIMIT 20
        ) recent_attempts
        """,
        (student_id,),
    )
    recent = cursor.fetchone() or {}
    summary["recent_accuracy_percent"] = float(
        recent.get("recent_accuracy") or summary["overall_accuracy_percent"] or 0
    )

    # 3. Topic-wise performance
    cursor.execute(
        """
        SELECT
            c.name_en AS topic_name,
            COUNT(a.attempt_id) AS attempts_count,
            ROUND(AVG(a.is_correct) * 100, 2) AS topic_accuracy
        FROM attempts a
        LEFT JOIN chapters c
            ON a.chapter_snapshot_id = c.id
        WHERE a.user_id = %s
          AND a.chapter_snapshot_id IS NOT NULL
        GROUP BY a.chapter_snapshot_id, c.name_en
        HAVING attempts_count >= 2
        ORDER BY topic_accuracy ASC, attempts_count DESC
        """,
        (student_id,),
    )
    topic_rows = cursor.fetchall() or []

    weak_topics = []
    strong_topics = []

    for row in topic_rows:
        topic_name = row.get("topic_name") or "Unknown Topic"
        topic_accuracy = float(row.get("topic_accuracy") or 0)

        if topic_accuracy < 60:
            weak_topics.append(topic_name)

        if topic_accuracy >= 80:
            strong_topics.append(topic_name)

    summary["weak_topics"] = weak_topics[:3]
    summary["strong_topics"] = strong_topics[:3]

    # 4. Simple study pattern summary
    cursor.execute(
        """
        SELECT
            COUNT(*) AS total_sessions,
            COUNT(DISTINCT DATE(start_time)) AS active_days,
            ROUND(AVG(duration_seconds), 0) AS avg_duration_seconds,
            SUM(
                CASE
                    WHEN start_time >= DATE_SUB(NOW(), INTERVAL 7 DAY)
                    THEN 1 ELSE 0
                END
            ) AS sessions_last_7_days
        FROM practice_sessions
        WHERE user_id = %s
        """,
        (student_id,),
    )
    pattern = cursor.fetchone() or {}

    total_sessions = int(pattern.get("total_sessions") or 0)
    active_days = int(pattern.get("active_days") or 0)
    sessions_last_7_days = int(pattern.get("sessions_last_7_days") or 0)

    if total_sessions == 0:
        study_pattern = "unknown"
    elif sessions_last_7_days >= 4:
        study_pattern = "consistent"
    elif active_days <= 2 and total_sessions >= 3:
        study_pattern = "last-minute"
    else:
        study_pattern = "irregular"

    summary["study_pattern"] = study_pattern

    return summary

@app.route("/api/chat", methods=["POST"])
@require_auth("student")
def chat():
    conn = None
    cursor = None

    try:
        data = request.json or {}

        user_message = (data.get("message") or "").strip()
        if not user_message:
            return jsonify({
                "success": False,
                "message": "Message is required."
            }), 400

        language_code = normalize_chat_language(
            data.get("language", g.current_user.get("language", "english"))
        )

        chat_session_id = data.get("chat_session_id")
        tutoring_mode = data.get("tutoring_mode")

        incoming_quick_snap_context = data.get("quick_snap_context")
        if not is_valid_quick_snap_context(incoming_quick_snap_context):
            incoming_quick_snap_context = None

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        saved_quick_snap_context = None
        effective_quick_snap_context = None

        # Create a new session automatically if frontend did not send one
        if not chat_session_id:
            title = build_quick_snap_chat_title(
                incoming_quick_snap_context,
                user_message,
                language_code
            )

            source_type = "quick_snap" if incoming_quick_snap_context else "normal"
            source_context_json = (
                json.dumps(incoming_quick_snap_context, ensure_ascii=False)
                if incoming_quick_snap_context
                else None
            )

            cursor.execute(
                """
                INSERT INTO chat_sessions
                (
                    student_id,
                    title,
                    created_language,
                    last_active_language,
                    source_type,
                    source_context_json
                )
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (
                    g.current_user["id"],
                    title,
                    language_code,
                    language_code,
                    source_type,
                    source_context_json,
                ),
            )

            chat_session_id = cursor.lastrowid
            effective_quick_snap_context = incoming_quick_snap_context

        else:
            # Check session ownership + get saved Quick Snap context
            cursor.execute(
                """
                SELECT
                    chat_session_id,
                    source_type,
                    source_context_json
                FROM chat_sessions
                WHERE chat_session_id = %s
                  AND student_id = %s
                  AND is_archived = 0
                LIMIT 1
                """,
                (chat_session_id, g.current_user["id"]),
            )
            session = cursor.fetchone()

            if not session:
                return jsonify({
                    "success": False,
                    "message": "Forbidden."
                }), 403

            saved_quick_snap_context = parse_json_column(
                session.get("source_context_json")
            )

            # If frontend sends context, prefer it and save/update it.
            # If frontend does not send context, reuse saved DB context.
            effective_quick_snap_context = (
                incoming_quick_snap_context or saved_quick_snap_context
            )

            if incoming_quick_snap_context:
                cursor.execute(
                    """
                    UPDATE chat_sessions
                    SET source_type = %s,
                        source_context_json = %s,
                        last_active_language = %s,
                        updated_at = NOW()
                    WHERE chat_session_id = %s
                      AND student_id = %s
                    """,
                    (
                        "quick_snap",
                        json.dumps(incoming_quick_snap_context, ensure_ascii=False),
                        language_code,
                        chat_session_id,
                        g.current_user["id"],
                    ),
                )
            else:
                cursor.execute(
                    """
                    UPDATE chat_sessions
                    SET last_active_language = %s,
                        updated_at = NOW()
                    WHERE chat_session_id = %s
                      AND student_id = %s
                    """,
                    (
                        language_code,
                        chat_session_id,
                        g.current_user["id"],
                    ),
                )

        # Save user message.
        # Important: save ONLY the student's visible question, not the hidden Quick Snap context.
        cursor.execute(
            """
            INSERT INTO chat_messages
            (
                chat_session_id,
                sender,
                message_text,
                message_language,
                tutoring_mode,
                student_state_snapshot_json,
                retrieved_refs_json
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (
                chat_session_id,
                "user",
                user_message,
                language_code,
                tutoring_mode,
                None,
                None,
            ),
        )

        # Get recent conversation history
        cursor.execute(
            """
            SELECT sender, message_text
            FROM chat_messages
            WHERE chat_session_id = %s
            ORDER BY created_at DESC, message_id DESC
            LIMIT 6
            """,
            (chat_session_id,),
        )
        recent_rows = cursor.fetchall() or []
        recent_rows.reverse()

        db_summary = get_student_chatbot_summary(cursor, g.current_user["id"])
        student_state = build_student_state(db_summary)

        # Use the visible student message for intent/strategy
        strategy = select_tutoring_strategy(user_message, student_state)
        agent_instruction = build_agent_instruction(strategy, student_state)

        # Use Quick Snap context only for the LLM prompt
        llm_user_message = build_quick_snap_llm_message(
            effective_quick_snap_context,
            user_message
        )

        retrieval_query = build_quick_snap_retrieval_query(
            effective_quick_snap_context,
            user_message
        )

        chatbot_result = get_chatbot_response(
            llm_user_message,
            language_code,
            history_messages=recent_rows,
            agent_instruction=agent_instruction,
            retrieval_mode=strategy.get("retrieval_mode", "auto"),
            retrieval_query=retrieval_query,
            return_metadata=True,
        )

        assistant_reply = chatbot_result.get("reply", "")
        retrieved_refs_json = chatbot_result.get("retrieved_refs_json")

        # Save assistant reply
        cursor.execute(
            """
            INSERT INTO chat_messages
            (
                chat_session_id,
                sender,
                message_text,
                message_language,
                tutoring_mode,
                student_state_snapshot_json,
                retrieved_refs_json
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (
                chat_session_id,
                "assistant",
                assistant_reply,
                language_code,
                strategy["tutoring_mode"],
                json.dumps(student_state, ensure_ascii=False),
                json.dumps(retrieved_refs_json, ensure_ascii=False),
            ),
        )

        # Keep session fresh
        cursor.execute(
            """
            UPDATE chat_sessions
            SET last_active_language = %s,
                updated_at = NOW()
            WHERE chat_session_id = %s
              AND student_id = %s
            """,
            (
                language_code,
                chat_session_id,
                g.current_user["id"],
            ),
        )

        conn.commit()

        return jsonify({
            "success": True,
            "reply": assistant_reply,
            "chat_session_id": chat_session_id,
            "tutoring_mode": strategy["tutoring_mode"],
            "intent": strategy.get("intent"),
            "retrieval_mode": strategy.get("retrieval_mode"),
            "show_quick_snap_cta": strategy.get("show_quick_snap_cta", False),
            "retrieved_refs_json": retrieved_refs_json,
            "quick_snap_context": effective_quick_snap_context,
        }), 200

    except Exception as e:
        print("CHAT ERROR:", e)
        if conn:
            conn.rollback()
        return jsonify({
            "success": False,
            "message": "Error generating response"
        }), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
    
# # Create the Upload API Endpoint
# @app.route('/api/upload', methods=['POST'])
# def upload_image():
#     # Check if an image was actually sent in the request
#     if 'image' not in request.files:
#         return jsonify({"error": "No image file provided"}), 400

#     file = request.files['image']

#     try:
#         # Send the file straight to Cloudinary
#         upload_result = cloudinary.uploader.upload(file)

#         secure_url = upload_result.get('secure_url')

#         # Return that URL back to your React frontend
#         return jsonify({"message": "Upload successful", "url": secure_url}), 200

#     except Exception as e:
#         return jsonify({"error": str(e)}), 500
    

@app.route('/api/syllabus', methods=['GET'])
def get_syllabus():
    conn = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        query = """
            SELECT
                id,
                form,
                chapter_no,
                name_en,
                name_bm,
                desc_en,
                desc_bm,
                CONCAT(chapter_no, ': ', name_en, ' - ', desc_en) AS chapter_string
            FROM chapters
            ORDER BY
                form,
                CAST(REPLACE(chapter_no, 'Chapter ', '') AS UNSIGNED)
        """

        cursor.execute(query)
        syllabus = cursor.fetchall()

        return jsonify({
            "success": True,
            "syllabus": syllabus
        })

    except Exception as e:
        print("SYLLABUS ERROR:", e)
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500

    finally:
        if conn:
            conn.close()


def parse_json_field(value, default):
    if value is None:
        return default

    if isinstance(value, (dict, list)):
        return value

    try:
        return json.loads(value)
    except Exception:
        return default


def join_instruction_blocks(value):
    items = parse_json_field(value, [])

    if not isinstance(items, list):
        return ""

    return "\n\n".join(str(x).strip() for x in items if str(x).strip())


def get_option_text(options, label, lang="en"):
    if not isinstance(options, list):
        return ""

    for opt in options:
        if not isinstance(opt, dict):
            continue

        if str(opt.get("label", "")).strip().upper() == label:
            text_key = "text_en" if lang == "en" else "text_ms"
            text = str(opt.get(text_key, "") or "").strip()

            # Useful for option-diagram questions where you do not crop images
            if not text:
                text = str(opt.get("visual_description", "") or "").strip()

            return text

    return ""


def get_option_image(options, label):
    if not isinstance(options, list):
        return ""

    for opt in options:
        if not isinstance(opt, dict):
            continue

        if str(opt.get("label", "")).strip().upper() == label:
            return str(opt.get("image_path", "") or "").strip()

    return ""


def answer_letter_to_index(letter):
    letter = str(letter or "").strip().upper()

    mapping = {
        "A": 0,
        "B": 1,
        "C": 2,
        "D": 3,
    }

    return mapping.get(letter, -1)

def get_correct_option_for_question(cursor, question_id):
    cursor.execute("""
        SELECT m.final_answer AS correct_option
        FROM question_marking_links qml
        JOIN marking_schemes m
            ON m.id = qml.marking_scheme_id
        WHERE qml.question_id = %s
        LIMIT 1
    """, (question_id,))

    row = cursor.fetchone()
    return row["correct_option"] if row else ""

def format_k1_question_for_frontend(row, correct_option):
    options = parse_json_field(row.get("options"), [])
    table_data = parse_json_field(row.get("table_data"), {})

    return {
        "id": row.get("id"),
        "question_no": row.get("question_no"),

        "form": row.get("form"),
        "chapter": row.get("chapter"),

        "difficulty": row.get("difficulty") or "Moderate",
        "difficulty_level": row.get("difficulty_level") or 3,

        "question_en": join_instruction_blocks(row.get("instructions_en")),
        "question_bm": join_instruction_blocks(row.get("instructions_ms")),

        "question_image": row.get("image_path") or "",
        "table_data": table_data,

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

        "correct_answer_index": answer_letter_to_index(correct_option),
        "correct_option": correct_option,

        "explanation_en": f"Correct answer: {correct_option}",
        "explanation_bm": f"Jawapan betul: {correct_option}",
        "explanation_image": "",
    }

def format_k2_rows_for_frontend(rows):
    formatted = []

    for row in rows:
        row = dict(row)

        for field in [
            "instructions_en",
            "instructions_ms",
            "sequence",
            "image_urls",
            "table_data",
            "given_values",
            "options"
        ]:
            if row.get(field) and isinstance(row[field], str):
                try:
                    row[field] = json.loads(row[field])
                except json.JSONDecodeError:
                    if field in ["table_data", "given_values"]:
                        row[field] = {}
                    else:
                        row[field] = []

        formatted.append(row)

    return formatted

@app.route("/api/questions/kertas1", methods=["GET"])
def get_kertas1_questions():
    conn = None
    cursor = None

    try:
        form = request.args.get("form")
        chapter = request.args.get("chapter")
        chapter_id = request.args.get("chapter_id")

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # IMPORTANT:
        # Your parser stores chapter as text, not chapter_id.
        # So the cleanest frontend call is:
        # /api/questions/kertas1?form=Form 4&chapter=Chapter 1: ...
        where_clauses = [
            "q.question_type = 'mcq'",
            "COALESCE(q.is_active, 1) = 1"
        ]
        params = []

        if form:
            where_clauses.append("(q.form = %s OR q.verified_form = %s)")
            params.extend([form, form])

        if chapter:
            where_clauses.append("(q.chapter = %s OR q.verified_chapter = %s)")
            params.extend([chapter, chapter])

        # Optional fallback if your old menu only sends chapter_id.
        # Only keep this if your questions table has chapter_id.
        # If not, ignore chapter_id and send chapter string from frontend instead.
        # if chapter_id:
        #     where_clauses.append("q.chapter_id = %s")
        #     params.append(chapter_id)

        where_sql = " AND ".join(where_clauses)

        # If your questions primary key is question_id instead of id,
        # change q.id AS id to q.question_id AS id,
        # and change the join qml.question_id = q.id accordingly.
        query = f"""
            SELECT
                q.id AS id,
                q.question_no,
                q.form,
                q.chapter,
                q.verified_form,
                q.verified_chapter,
                q.difficulty,
                q.difficulty_level,
                q.instructions_en,
                q.instructions_ms,
                q.options,
                q.table_data,
                q.image_path,
                q.visual_semantic_summary,
                m.final_answer AS correct_option
            FROM questions q
            LEFT JOIN question_marking_links qml
                ON qml.question_id = q.id
            LEFT JOIN marking_schemes m
                ON m.id = qml.marking_scheme_id
            WHERE {where_sql}
            ORDER BY CAST(q.question_no AS UNSIGNED)
        """

        cursor.execute(query, params)
        rows = cursor.fetchall()

        questions = []

        for row in rows:
            options = parse_json_field(row.get("options"), [])
            table_data = parse_json_field(row.get("table_data"), {})

            correct_option = row.get("correct_option", "")
            correct_answer_index = answer_letter_to_index(correct_option)

            questions.append({
                "id": row.get("id"),
                "question_no": row.get("question_no"),

                "form": row.get("verified_form") or row.get("form"),
                "chapter": row.get("verified_chapter") or row.get("chapter"),

                "difficulty": row.get("difficulty") or "Easy",
                "difficulty_level": row.get("difficulty_level") or 1,

                "question_en": join_instruction_blocks(row.get("instructions_en")),
                "question_bm": join_instruction_blocks(row.get("instructions_ms")),

                "question_image": row.get("image_path") or "",
                "table_data": table_data,

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

                "correct_answer_index": correct_answer_index,
                "correct_option": correct_option,

                # K1 explanation is generated later, not from official scheme.
                "explanation_en": f"Correct answer: {correct_option}",
                "explanation_bm": f"Jawapan betul: {correct_option}",
                "explanation_image": "",
            })

        return jsonify({
            "success": True,
            "questions": questions
        }), 200

    except Exception as e:
        print("K1 question fetch error:", e)
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
            
@app.route('/api/questions/kertas2', methods=['GET'])
def get_kertas2_questions():
    form_val = request.args.get('form')
    chapter_val = request.args.get('chapter')

    print("KERTAS 2 FORM:", form_val)
    print("KERTAS 2 CHAPTER:", chapter_val)

    if not form_val or not chapter_val:
        return jsonify({
            'success': False,
            'message': 'Missing form or chapter'
        }), 400

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        query = """
            SELECT *
            FROM questions
            WHERE form = %s
                AND chapter = %s
                AND COALESCE(is_active, 1) = 1
            ORDER BY id ASC
        """
        cursor.execute(query, (form_val, chapter_val))
        rows = cursor.fetchall()

        for row in rows:
            for field in ['instructions_en', 'instructions_ms', 'sequence', 'image_urls']:
                if row.get(field) and isinstance(row[field], str):
                    try:
                        row[field] = json.loads(row[field])
                    except json.JSONDecodeError:
                        row[field] = []

        return jsonify({
            'success': True,
            'questions': rows
        })

    except Exception as e:
        print("Error fetching Kertas 2 questions:", e)
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

    finally:
        cursor.close()
        conn.close()


# save students action for model training
@app.route('/api/save-progress', methods=['POST'])
@require_auth("student")
def save_progress():
    try:
        data = request.json

        def format_date_for_mysql(iso_str):
            if not iso_str:
                return None
            try:
                clean_str = iso_str.split('.')[0]
                dt_utc = datetime.strptime(clean_str, "%Y-%m-%dT%H:%M:%S")
                dt_myt = dt_utc + timedelta(hours=8)
                return dt_myt.strftime("%Y-%m-%d %H:%M:%S")
            except Exception as e:
                print("Date parse error:", e)
                return None

        user_id = g.current_user["id"]
        chapter_id = data.get('chapter_id')
        paper_type = data.get('paper_type')
        session_language = data.get('session_language')
        start_time = format_date_for_mysql(data.get('start_time'))
        end_time = format_date_for_mysql(data.get('end_time'))
        highest_streak = data.get('highest_streak', 0)
        total_questions = data.get('total_questions_answered', 0)
        attempts_log = data.get('attempts', [])

        correct_count = sum(1 for a in attempts_log if a.get("is_correct") == 1)
        incorrect_count = len(attempts_log) - correct_count
        accuracy_snapshot = round((correct_count / len(attempts_log)) * 100, 2) if attempts_log else 0.00

        duration_seconds = None
        if start_time and end_time:
            try:
                start_dt = datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
                end_dt = datetime.strptime(end_time, "%Y-%m-%d %H:%M:%S")
                duration_seconds = int((end_dt - start_dt).total_seconds())
            except Exception as e:
                print("Duration calc error:", e)

        user_agent_string = request.headers.get('User-Agent', '')
        device_type = "Desktop"
        if "Mobi" in user_agent_string or "Android" in user_agent_string or "iPhone" in user_agent_string:
            device_type = "Mobile"
        elif "Tablet" in user_agent_string or "iPad" in user_agent_string:
            device_type = "Tablet"

        conn = get_db_connection()
        cursor = conn.cursor()

        session_query = """
            INSERT INTO practice_sessions
            (
                user_id, chapter_id, paper_type, session_language,
                start_time, end_time, duration_seconds, device_type,
                highest_streak, total_questions_answered,
                correct_count, incorrect_count, accuracy_snapshot
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(session_query, (
            user_id, chapter_id, paper_type, session_language,
            start_time, end_time, duration_seconds, device_type,
            highest_streak, total_questions,
            correct_count, incorrect_count, accuracy_snapshot
        ))

        practice_id = cursor.lastrowid

        if attempts_log and len(attempts_log) > 0:
            attempt_query = """
                INSERT INTO attempts
                (
                    user_id,
                    question_id,
                    exercise_stage_id,
                    paper_type,
                    chapter_snapshot_id,
                    chapter_snapshot,
                    difficulty_snapshot,
                    difficulty_level_snapshot,
                    practice_id,
                    is_correct,
                    score,
                    max_score,
                    answer_revealed,
                    time_taken_seconds,
                    attempted_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """

            attempts_data = []

            for attempt in attempts_log:
                attempts_data.append((
                    user_id,
                    attempt.get("question_id"),
                    attempt.get("exercise_stage_id"),

                    attempt.get("paper_type", paper_type),

                    attempt.get("chapter_snapshot_id", chapter_id),
                    attempt.get("chapter_snapshot"),

                    attempt.get("difficulty_snapshot"),
                    attempt.get("difficulty_level_snapshot"),

                    practice_id,

                    int(attempt.get("is_correct", 0) or 0),

                    attempt.get("score"),
                    attempt.get("max_score"),

                    int(attempt.get("answer_revealed", 0) or 0),

                    attempt.get("time_taken_seconds"),
                    format_date_for_mysql(attempt.get("attempted_at"))
                ))

            cursor.executemany(attempt_query, attempts_data)
            session_form = data.get("form") or ""
            session_chapter = data.get("chapter") or ""

            for attempt in attempts_log:
                attempt_paper_type = attempt.get("paper_type", paper_type)
                attempt_chapter = attempt.get("chapter_snapshot") or session_chapter
                attempt_form = attempt.get("form_snapshot") or session_form

                if not attempt_form or not attempt_chapter or not attempt_paper_type:
                    continue

                update_topic_mastery_after_attempt(
                    conn=conn,
                    user_id=user_id,
                    form=attempt_form,
                    chapter=attempt_chapter,
                    paper_type=attempt_paper_type,
                    is_correct=bool(int(attempt.get("is_correct", 0) or 0)),
                    question_difficulty_level=attempt.get("difficulty_level_snapshot") or 3
                )
        conn.commit()
        cursor.close()

        return jsonify({"success": True, "message": "Progress saved successfully!"}), 200

    except Exception as e:
        print("Error saving progress:", e)
        return jsonify({"success": False, "message": "Failed to save progress"}), 500

@app.route("/api/adaptive/next", methods=["GET"])
@require_auth("student")
def get_adaptive_next():
    conn = None
    cursor = None

    try:
        form = request.args.get("form")
        chapter = request.args.get("chapter")
        paper_type = request.args.get("paper_type")

        if not form or not chapter or not paper_type:
            return jsonify({
                "success": False,
                "message": "Missing form, chapter, or paper_type."
            }), 400

        paper_type = str(paper_type).strip().lower()

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        allow_easier = str(
            request.args.get("allow_easier_after_hard_completed", "0")
        ).lower() in ["1", "true", "yes"]
        result = choose_next_practice_unit(
            conn=conn,
            user_id=g.current_user["id"],
            form=form,
            chapter=chapter,
            paper_type=paper_type,
            allow_easier_after_hard_completed=allow_easier
        )
        if not result:
            return jsonify({
                "success": True,
                "questions": [],
                "adaptive": {
                    "status": "no_questions",
                    "form": form,
                    "chapter": chapter,
                    "paper_type": paper_type
                },
                "message": "No adaptive question found."
            }), 200
        if result and result.get("status") != "selected":
            return jsonify({
                "success": True,
                "questions": [],
                "adaptive": result,
                "message": result.get("message", "")
            }), 200

        unit = result.get("unit", {})
        rows = unit.get("rows", [])

        if not rows:
            return jsonify({
                "success": True,
                "questions": [],
                "adaptive": result,
                "message": "No rows found for selected adaptive unit."
            }), 200

        if paper_type == "kertas1":
            row = rows[0]
            correct_option = get_correct_option_for_question(cursor, row["id"])

            questions = [
                format_k1_question_for_frontend(row, correct_option)
            ]

        elif paper_type == "kertas2":
            selected_level = unit.get("difficulty_level") or result.get("selected_difficulty_level") or 3

            try:
                selected_level = int(selected_level)
            except Exception:
                selected_level = 3

            selected_level = max(1, min(5, selected_level))

            if selected_level <= 2:
                selected_label = "Easy"
            elif selected_level == 3:
                selected_label = "Moderate"
            else:
                selected_label = "Hard"

            for row in rows:
                row["adaptive_difficulty_level"] = selected_level
                row["adaptive_difficulty"] = selected_label

            questions = format_k2_rows_for_frontend(rows)

        else:
            return jsonify({
                "success": False,
                "message": "Invalid paper_type."
            }), 400

        return jsonify({
            "success": True,
            "questions": questions,
            "adaptive": {
                "paper_type": paper_type,
                "form": form,
                "chapter": chapter,
                "target_difficulty_level": result.get("target_difficulty_level"),
                "selected_difficulty_level": unit.get("difficulty_level"),
                "exercise_stage_id": unit.get("exercise_stage_id"),
                "question_ids": unit.get("question_ids", []),
            }
        }), 200

    except Exception as e:
        print("ADAPTIVE NEXT ERROR:", e)
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route("/api/practice/start-session", methods=["POST"])
@require_auth("student")
def start_practice_session():
    data = request.json or {}

    chapter_id = data.get("chapter_id")
    paper_type = data.get("paper_type")
    session_language = data.get("session_language", g.current_user.get("language", "english"))

    if not chapter_id or paper_type not in ["kertas1", "kertas2"]:
        return jsonify({
            "success": False,
            "message": "Invalid practice session data."
        }), 400

    conn = None
    cursor = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            """
            INSERT INTO practice_sessions
            (
                user_id,
                chapter_id,
                paper_type,
                session_language,
                start_time,
                end_time,
                duration_seconds,
                highest_streak
            )
            VALUES
            (
                %s,
                %s,
                %s,
                %s,
                NOW(),
                NOW(),
                0,
                0
            )
            """,
            (
                g.current_user["id"],
                chapter_id,
                paper_type,
                session_language,
            )
        )

        conn.commit()

        return jsonify({
            "success": True,
            "practice_id": cursor.lastrowid
        }), 200

    except Exception as e:
        print("START PRACTICE SESSION ERROR:", e)
        return jsonify({
            "success": False,
            "message": "Failed to start practice session."
        }), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def get_k2_stage_group_info(cursor, exercise_stage_id):
    default_info = {
        "is_grouped": False,
        "group_id": None,
        "stage_index": 1,
        "max_stage_index": 1,
        "stage_count": 1,
        "is_final_stage": True
    }

    if not exercise_stage_id:
        return default_info

    cursor.execute("""
        SELECT
            group_id,
            group_chapter,
            COALESCE(stage_index, 1) AS stage_index
        FROM questions
        WHERE exercise_stage_id = %s
        LIMIT 1
    """, (exercise_stage_id,))

    row = cursor.fetchone()

    if not row:
        return default_info

    group_id = row.get("group_id")
    group_chapter = str(row.get("group_chapter") or "").strip()
    stage_index = int(row.get("stage_index") or 1)

    # Mixed group or no group_id should behave as individual stage
    if not group_id or group_chapter == "Mixed":
        return {
            "is_grouped": False,
            "group_id": group_id,
            "stage_index": stage_index,
            "max_stage_index": stage_index,
            "stage_count": 1,
            "is_final_stage": True
        }

    cursor.execute("""
        SELECT
            COUNT(DISTINCT exercise_stage_id) AS stage_count,
            MAX(COALESCE(stage_index, 1)) AS max_stage_index
        FROM questions
        WHERE group_id = %s
          AND COALESCE(group_chapter, '') != 'Mixed'
          AND exercise_stage_id IS NOT NULL
          AND exercise_stage_id != ''
    """, (group_id,))

    group_row = cursor.fetchone() or {}

    stage_count = int(group_row.get("stage_count") or 1)
    max_stage_index = int(group_row.get("max_stage_index") or stage_index)

    # IMPORTANT:
    # If only one stage, it is not a real grouped flow.
    if stage_count <= 1:
        return {
            "is_grouped": False,
            "group_id": group_id,
            "stage_index": stage_index,
            "max_stage_index": stage_index,
            "stage_count": stage_count,
            "is_final_stage": True
        }

    return {
        "is_grouped": True,
        "group_id": group_id,
        "stage_index": stage_index,
        "max_stage_index": max_stage_index,
        "stage_count": stage_count,
        "is_final_stage": stage_index >= max_stage_index
    }

def calculate_group_attempt_result(cursor, user_id, practice_id, group_attempt_id):
    cursor.execute("""
        SELECT
            COALESCE(SUM(score), 0) AS group_score,
            COALESCE(SUM(max_score), 0) AS group_max_score
        FROM attempts
        WHERE user_id = %s
          AND practice_id = %s
          AND group_attempt_id = %s
    """, (user_id, practice_id, group_attempt_id))

    row = cursor.fetchone() or {}

    group_score = float(row.get("group_score") or 0)
    group_max_score = float(row.get("group_max_score") or 0)
    group_is_correct = 1 if group_max_score > 0 and group_score >= group_max_score else 0

    return group_score, group_max_score, group_is_correct

def enqueue_review_variant_after_wrong_attempt(
    cursor,
    conn,
    user_id,
    practice_id,
    attempt,
    save_context,
    language="english"
):
    paper_type = str(attempt.get("paper_type") or "").strip().lower()

    is_correct = bool(int(attempt.get("is_correct", 0) or 0))
    review_variant_id = attempt.get("review_variant_id")
    
    # Check if this is a group question
    is_grouped_k2 = bool(save_context.get("is_grouped_k2"))

    # FIX: If it is a normal question and they got it right, exit.
    # BUT if it is a group question, DO NOT exit yet! We must wait 
    # to evaluate the whole group's score at the bottom of this function.
    if not is_grouped_k2 and is_correct:
        return None

    grading_result = {
        "score": attempt.get("score"),
        "max_score": attempt.get("max_score"),
        "is_correct": 0,
        "answer_revealed": int(attempt.get("answer_revealed", 0) or 0),
        "reason": (
            "Student answered a generated review variant wrongly."
            if review_variant_id
            else "Student answered an original adaptive question wrongly."
        )
    }

    # CASE 1: Wrong generated variant -> queue next generated variant behind existing queue.
    if review_variant_id:
        source_key = f"variant:{review_variant_id}"

        existing = get_existing_review_variant(
            cursor=cursor,
            user_id=user_id,
            source_key=source_key,
            language=language,
            practice_id=practice_id
        )

        if existing:
            return existing["variant_id"]

        global_template = get_global_review_variant_template(
            cursor=cursor,
            source_key=source_key,
            language=language
        )

        if global_template:
            return clone_review_variant_template_for_user(
                cursor=cursor,
                user_id=user_id,
                practice_id=practice_id,
                template_row=global_template
            )

        cursor.execute("""
            SELECT *
            FROM review_variants
            WHERE variant_id = %s
              AND user_id = %s
            LIMIT 1
        """, (review_variant_id, user_id))

        parent_row = cursor.fetchone()

        if not parent_row:
            return None

        parent_variant = format_review_variant_row(parent_row)

        # --- BYPASS AI FOR GROUPS ---
        if parent_variant.get("source_group_id"):
            new_variant = build_original_k2_group_variant(parent_variant["source_group_id"], language)
        else:
            # Single-stage or K1 questions still use normal AI generation
            new_variant = generate_review_variant(
                source_mode="variant",
                parent_variant=parent_variant,
                language=language,
                grading_result=grading_result
            )

        new_variant = make_json_safe(new_variant or {})

        if not new_variant or new_variant.get("variant_type") == "error":
            print("FAILED TO GENERATE CHILD REVIEW VARIANT")
            return None

        new_variant["language"] = language
        new_variant["parent_variant_id"] = review_variant_id

        return insert_review_variant(
            cursor=cursor,
            user_id=user_id,
            practice_id=practice_id,
            source_mode="variant",
            source_key=source_key,
            source_exercise_stage_id=parent_variant.get("source_exercise_stage_id"),
            source_group_id=parent_variant.get("source_group_id"),
            source_question_id=parent_variant.get("source_question_id"),
            variant=new_variant,
            parent_variant_id=review_variant_id
        )

    # CASE 2: Wrong original K1 question.
    if paper_type == "kertas1":
        question_id = attempt.get("question_id")

        if not question_id:
            return None

        source_mode = "question"
        source_key = f"question:{question_id}"

        existing = get_existing_review_variant(
            cursor=cursor,
            user_id=user_id,
            source_key=source_key,
            language=language,
            practice_id=practice_id
        )

        if existing:
            return existing["variant_id"]

        reused_variant_id = reuse_global_template_or_none(
            cursor=cursor,
            user_id=user_id,
            practice_id=practice_id,
            source_key=source_key,
            language=language
        )

        if reused_variant_id:
            return reused_variant_id

        variant = generate_review_variant(
            source_mode="question",
            question_id=question_id,
            language=language,
            grading_result=grading_result
        )

        variant = make_json_safe(variant or {})

        if not variant or variant.get("variant_type") == "error":
            print("FAILED TO GENERATE K1 REVIEW VARIANT:", variant)
            return None

        variant["language"] = language

        return insert_review_variant(
            cursor=cursor,
            user_id=user_id,
            practice_id=practice_id,
            source_mode=source_mode,
            source_key=source_key,
            source_exercise_stage_id=None,
            source_group_id=None,
            source_question_id=question_id,
            variant=variant,
            parent_variant_id=None
        )

    # CASE 3: Wrong original K2 question.
    if paper_type == "kertas2":
        exercise_stage_id = attempt.get("exercise_stage_id")
        group_id = save_context.get("group_id")
        is_grouped_k2 = bool(save_context.get("is_grouped_k2"))
        is_group_final_stage = bool(save_context.get("is_group_final_stage"))
        group_is_correct = save_context.get("group_is_correct")

        # For grouped K2, generate only after final stage if whole group is not full mark.
        if is_grouped_k2:
            if not is_group_final_stage:
                return None

            if int(group_is_correct or 0) == 1:
                return None

            source_mode = "group"
            source_key = f"group:{group_id}"

            existing = get_existing_review_variant(
                cursor=cursor,
                user_id=user_id,
                source_key=source_key,
                language=language,
                practice_id=practice_id
            )

            if existing:
                return existing["variant_id"]

            # --- BYPASS AI GENERATION ---
            # Instead of calling the LLM, we strictly repackage the original question
            variant = build_original_k2_group_variant(group_id, language)
            variant = make_json_safe(variant or {})

            if not variant:
                print("FAILED TO REPACKAGE ORIGINAL K2 GROUP QUESTION")
                return None

            variant["language"] = language

            return insert_review_variant(
                cursor=cursor,
                user_id=user_id,
                practice_id=practice_id,
                source_mode=source_mode,
                source_key=source_key,
                source_exercise_stage_id=None,
                source_group_id=group_id,
                source_question_id=attempt.get("question_id"),
                variant=variant,
                parent_variant_id=None
            )

        # Single-stage K2
        if not exercise_stage_id:
            return None

        source_mode = "stage"
        source_key = f"stage:{exercise_stage_id}"

        existing = get_existing_review_variant(
            cursor=cursor,
            user_id=user_id,
            source_key=source_key,
            language=language,
            practice_id=practice_id
        )

        if existing:
            return existing["variant_id"]

        reused_variant_id = reuse_global_template_or_none(
            cursor=cursor,
            user_id=user_id,
            practice_id=practice_id,
            source_key=source_key,
            language=language
        )

        if reused_variant_id:
            return reused_variant_id

        variant = generate_review_variant(
            source_mode="stage",
            exercise_stage_id=exercise_stage_id,
            language=language,
            grading_result=grading_result
        )

        variant = make_json_safe(variant or {})

        if not variant or variant.get("variant_type") == "error":
            print("FAILED TO GENERATE K2 STAGE REVIEW VARIANT:", variant)
            return None

        variant["language"] = language

        return insert_review_variant(
            cursor=cursor,
            user_id=user_id,
            practice_id=practice_id,
            source_mode=source_mode,
            source_key=source_key,
            source_exercise_stage_id=exercise_stage_id,
            source_group_id=None,
            source_question_id=attempt.get("question_id"),
            variant=variant,
            parent_variant_id=None
        )

    return None

@app.route("/api/practice/save-attempt", methods=["POST"])
@require_auth("student")
def save_single_attempt():
    response_extra = {
    "is_grouped_k2": False,
    "is_group_final_stage": False,
    "group_id": None,
    "group_attempt_id": None,
    "group_stage_count": 1,
    "group_score": None,
    "group_max_score": None,
    "group_is_correct": None,
}
    conn = None
    cursor = None
    try:
        data = request.json or {}
        attempt = data.get("attempt") or {}
        is_testing_skip = bool(
            attempt.get("testing_skip") or attempt.get("is_skipped")
        )
        user_id = g.current_user["id"]
        practice_id = data.get("practice_id")

        if not practice_id:
            return jsonify({
                "success": False,
                "message": "Missing practice_id."
            }), 400

        def format_date_for_mysql(iso_str):
            if not iso_str:
                return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            try:
                clean_str = iso_str.split(".")[0]
                dt_utc = datetime.strptime(clean_str, "%Y-%m-%dT%H:%M:%S")
                dt_myt = dt_utc + timedelta(hours=8)
                return dt_myt.strftime("%Y-%m-%d %H:%M:%S")
            except Exception:
                return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        attempt_paper_type = attempt.get("paper_type") or data.get("paper_type") or ""
        exercise_stage_id = attempt.get("exercise_stage_id")

        stage_group_info = get_k2_stage_group_info(cursor, exercise_stage_id)

        is_grouped_k2 = (
            str(attempt_paper_type).lower() == "kertas2"
            and stage_group_info.get("is_grouped")
        )

        group_id_snapshot = attempt.get("group_id_snapshot") or stage_group_info.get("group_id")
        group_attempt_id = attempt.get("group_attempt_id")

        if is_grouped_k2 and not group_attempt_id:
            group_attempt_id = f"{practice_id}_{group_id_snapshot}"

        is_group_final_stage = 1 if is_grouped_k2 and stage_group_info.get("is_final_stage") else 0
        response_extra.update({
            "is_grouped_k2": bool(is_grouped_k2),
            "is_group_final_stage": bool(is_group_final_stage),
            "group_id": group_id_snapshot,
            "group_attempt_id": group_attempt_id,
            "group_stage_count": int(stage_group_info.get("stage_count") or 1),
        })
        cursor.execute("""
            INSERT INTO attempts
            (
                user_id,
                question_id,
                exercise_stage_id,

                group_attempt_id,
                group_id_snapshot,

                paper_type,
                chapter_snapshot_id,
                chapter_snapshot,
                difficulty_snapshot,
                difficulty_level_snapshot,
                practice_id,
                is_correct,

                group_is_correct,
                group_score,
                group_max_score,
                is_group_final_stage,

                score,
                max_score,
                answer_revealed,
                time_taken_seconds,
                review_variant_id,
                attempted_at
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            user_id,
            attempt.get("question_id"),
            exercise_stage_id,

            group_attempt_id,
            group_id_snapshot if is_grouped_k2 else None,

            attempt_paper_type,
            attempt.get("chapter_snapshot_id"),
            attempt.get("chapter_snapshot"),
            attempt.get("difficulty_snapshot"),
            attempt.get("difficulty_level_snapshot"),
            practice_id,
            int(attempt.get("is_correct", 0) or 0),

            None,
            None,
            None,
            is_group_final_stage,

            attempt.get("score"),
            attempt.get("max_score"),
            int(attempt.get("answer_revealed", 0) or 0),
            attempt.get("time_taken_seconds"),
            attempt.get("review_variant_id"),
            format_date_for_mysql(attempt.get("attempted_at"))
        ))
        if is_testing_skip:
            # If this is a review variant, mark it completed/skipped
            # so it does not appear again.
            review_variant_id = attempt.get("review_variant_id")

            if review_variant_id:
                cursor.execute("""
                    UPDATE review_variants
                    SET status = 'completed'
                    WHERE variant_id = %s
                    AND user_id = %s
                """, (review_variant_id, user_id))

            conn.commit()

            return jsonify({
                "success": True,
                "skipped": True,
                "message": "Question skipped for testing. No grading or review variant generated."
            }), 200
        inserted_attempt_id = cursor.lastrowid
        review_variant_id = attempt.get("review_variant_id")
        is_variant_final_stage = int(attempt.get("is_variant_final_stage", 1) or 1)

        if review_variant_id and is_variant_final_stage:
            cursor.execute("""
                UPDATE review_variants
                SET status = 'completed'
                WHERE variant_id = %s
                AND user_id = %s
            """, (review_variant_id, user_id))
        attempt_form = attempt.get("form_snapshot") or data.get("form") or ""
        attempt_chapter = attempt.get("chapter_snapshot") or data.get("chapter") or ""
        attempt_paper_type = attempt.get("paper_type") or data.get("paper_type") or ""

        should_update_mastery = True
        mastery_is_correct = bool(int(attempt.get("is_correct", 0) or 0))

        # For grouped K2, update mastery only after final stage.
        if is_grouped_k2:
            should_update_mastery = bool(is_group_final_stage)

            if is_group_final_stage:
                group_score, group_max_score, group_is_correct = calculate_group_attempt_result(
                    cursor=cursor,
                    user_id=user_id,
                    practice_id=practice_id,
                    group_attempt_id=group_attempt_id
                )

                cursor.execute("""
                    UPDATE attempts
                    SET
                        group_score = %s,
                        group_max_score = %s,
                        group_is_correct = %s
                    WHERE user_id = %s
                    AND practice_id = %s
                    AND group_attempt_id = %s
                """, (
                    group_score,
                    group_max_score,
                    group_is_correct,
                    user_id,
                    practice_id,
                    group_attempt_id
                ))
                response_extra.update({
                    "group_score": group_score,
                    "group_max_score": group_max_score,
                    "group_is_correct": group_is_correct,
                })
                cursor.execute("""
                    UPDATE attempts
                    SET is_group_final_stage = 1
                    WHERE attempt_id = %s
                """, (inserted_attempt_id,))

                mastery_is_correct = bool(group_is_correct)

        if should_update_mastery and attempt_form and attempt_chapter and attempt_paper_type:
            update_topic_mastery_after_attempt(
                conn=conn,
                user_id=user_id,
                form=attempt_form,
                chapter=attempt_chapter,
                paper_type=attempt_paper_type,
                is_correct=mastery_is_correct,
                question_difficulty_level=attempt.get("difficulty_level_snapshot") or 3
            )
        queued_review_variant_id = None
        save_context = {
            "is_grouped_k2": bool(is_grouped_k2),
            "is_group_final_stage": bool(is_group_final_stage),
            "group_id": group_id_snapshot,
            "group_attempt_id": group_attempt_id,
            "group_stage_count": int(stage_group_info.get("stage_count") or 1),
            "group_score": response_extra.get("group_score"),
            "group_max_score": response_extra.get("group_max_score"),
            "group_is_correct": response_extra.get("group_is_correct"),
        }

        try:
            queued_review_variant_id = enqueue_review_variant_after_wrong_attempt(
                cursor=cursor,
                conn=conn,
                user_id=user_id,
                practice_id=practice_id,
                attempt=attempt,
                save_context=save_context,
                language=data.get("language") or g.current_user.get("language", "english")
            )
        except Exception as variant_error:
            print("QUEUE REVIEW VARIANT AFTER ATTEMPT ERROR:", variant_error)
        conn.commit()

        return jsonify({
            "success": True,
            "message": "Attempt saved successfully.",
            "queued_review_variant_id": queued_review_variant_id,
            **response_extra
        }), 200

    except Exception as e:
        print("SAVE SINGLE ATTEMPT ERROR:", e)
        if conn:
            conn.rollback()
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@app.route("/api/practice/end-session", methods=["POST"])
@require_auth("student")
def end_practice_session():
    data = request.json or {}

    practice_id = data.get("practice_id")
    highest_streak = int(data.get("highest_streak") or 0)

    if not practice_id:
        return jsonify({
            "success": False,
            "message": "practice_id is required."
        }), 400

    conn = None
    cursor = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            """
            UPDATE practice_sessions ps
            LEFT JOIN (
                SELECT
                    practice_id,
                    COUNT(*) AS attempt_count,
                    SUM(CASE WHEN is_correct = 1 THEN 1 ELSE 0 END) AS correct_count,
                    ROUND(
                        SUM(CASE WHEN is_correct = 1 THEN 1 ELSE 0 END)
                        / NULLIF(COUNT(*), 0) * 100,
                        2
                    ) AS accuracy_snapshot
                FROM attempts
                WHERE practice_id = %s
                GROUP BY practice_id
            ) a
                ON a.practice_id = ps.practice_id
            SET
                ps.end_time = NOW(),
                ps.duration_seconds =
                    CASE
                        WHEN COALESCE(a.attempt_count, 0) = 0
                        THEN 0
                        ELSE GREATEST(
                            0,
                            TIMESTAMPDIFF(SECOND, ps.start_time, NOW())
                        )
                    END,
                ps.highest_streak = %s,
                ps.total_questions_answered = COALESCE(a.attempt_count, 0),
                ps.correct_count = COALESCE(a.correct_count, 0),
                ps.accuracy_snapshot = COALESCE(a.accuracy_snapshot, 0)
            WHERE ps.practice_id = %s
            AND ps.user_id = %s
            """,
            (
                practice_id,
                highest_streak,
                practice_id,
                g.current_user["id"],
            )
        )

        conn.commit()

        return jsonify({
            "success": True,
            "message": "Practice session ended."
        }), 200

    except Exception as e:
        print("END PRACTICE SESSION ERROR:", e)
        return jsonify({
            "success": False,
            "message": "Failed to end practice session."
        }), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@app.route('/api/log-activity', methods=['POST'])
@require_auth("student", "parent", "admin")
def log_activity():
    try:
        data = request.json
        action_type = data.get('action_type')
        timestamp = data.get('timestamp')

        def format_date_for_mysql(iso_str):
            if not iso_str:
                return None
            try:
                clean_str = iso_str.split('.')[0]
                dt_utc = datetime.strptime(clean_str, "%Y-%m-%dT%H:%M:%S")
                dt_myt = dt_utc + timedelta(hours=8)
                return dt_myt.strftime("%Y-%m-%d %H:%M:%S")
            except Exception as e:
                print("Date parse error:", e)
                return None

        clean_time = format_date_for_mysql(timestamp)

        conn = get_db_connection()
        cursor = conn.cursor()

        query = """
            INSERT INTO activity_logs (user_id, action_type, created_at)
            VALUES (%s, %s, %s)
        """
        cursor.execute(query, (g.current_user["id"], action_type, clean_time))

        conn.commit()
        cursor.close()

        return jsonify({"success": True}), 200

    except Exception as e:
        print("Error logging activity:", e)
        return jsonify({"success": False, "message": "Failed to log activity"}), 500

def build_quick_snap_solve_response(pipeline_result):
    return {
        "success": True,
        "status": "success",
        "mode": "solve_question",
        "result_type": "solution",
        "question_text":
            pipeline_result.get("question_text")
            or pipeline_result.get("display_parsed_equation")
            or pipeline_result.get("parsed_equation")
            or pipeline_result.get("equation")
            or pipeline_result.get("input_text")
            or "",
        "steps": pipeline_result.get("steps", []),
        "final_answer": pipeline_result.get("final_answer") or pipeline_result.get("answer") or "",
        "message": pipeline_result.get("message", ""),
        "quick_snap_context": {
            "source": "quick_snap",
            "mode": "solve_question",
            "result_type": "solution",
            "question_text":
                pipeline_result.get("question_text")
                or pipeline_result.get("display_parsed_equation")
                or pipeline_result.get("parsed_equation")
                or pipeline_result.get("equation")
                or pipeline_result.get("input_text")
                or "",
            "result_summary": pipeline_result.get("answer") or pipeline_result.get("final_answer") or "",
        }
    }


def build_quick_snap_check_response(raw_result):
    return {
        "success": True,
        "status": "success",
        "mode": "check_my_work",
        "result_type": "work_check",
        "question_text": raw_result.get("question_text", ""),
        "score": raw_result.get("score"),
        "max_score": raw_result.get("max_score"),
        "correctness_summary": raw_result.get("correctness_summary", ""),
        "message": raw_result.get("message", ""),
        "quick_snap_context": {
            "source": "quick_snap",
            "mode": "check_my_work",
            "result_type": "work_check",
            "question_text": raw_result.get("question_text", ""),
            "result_summary": raw_result.get("correctness_summary", ""),
        }
    }




@app.route("/api/quick-snap/log", methods=["POST"])
@require_auth("student")
def quick_snap_log():
    conn = None
    cursor = None

    try:
        data = request.json or {}

        mode = data.get("mode")
        result_type = data.get("result_type")
        follow_up_chat_opened = 1 if data.get("follow_up_chat_opened") else 0
        timestamp = data.get("timestamp")

        if mode not in ["solve_question", "check_my_work"]:
            return jsonify({
                "success": False,
                "message": "Invalid mode."
            }), 400

        if not result_type:
            return jsonify({
                "success": False,
                "message": "result_type is required."
            }), 400

        def format_date_for_mysql(iso_str):
            if not iso_str:
                return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            try:
                clean_str = iso_str.split(".")[0]
                dt_utc = datetime.strptime(clean_str, "%Y-%m-%dT%H:%M:%S")
                dt_myt = dt_utc + timedelta(hours=8)
                return dt_myt.strftime("%Y-%m-%d %H:%M:%S")
            except Exception:
                return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        created_at = format_date_for_mysql(timestamp)

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO quick_snap_events
            (user_id, mode, result_type, follow_up_chat_opened, created_at)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (
                g.current_user["id"],
                mode,
                result_type,
                follow_up_chat_opened,
                created_at,
            ),
        )

        conn.commit()

        return jsonify({
            "success": True,
            "message": "Quick Snap event logged successfully."
        }), 200

    except Exception as e:
        print("QUICK SNAP LOG ERROR:", e)
        return jsonify({
            "success": False,
            "message": "Failed to log Quick Snap event."
        }), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

##### Parent Helper Functions #####
# Checks if the parent is linked to the student 
# Builds the payload for grade prediction
def build_grade_prediction_payload(user_id, lang="english"):
    conn = None
    cursor = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT 
                COUNT(*) as total_questions_attempted,
                COALESCE(AVG(is_correct), 0) as overall_accuracy,
                COALESCE(AVG(time_taken_seconds), 0) as avg_time_per_question,
                COALESCE(SUM(CASE WHEN paper_type = 'kertas1' THEN 1 ELSE 0 END), 0) as paper1_attempts,
                COALESCE(SUM(CASE WHEN paper_type = 'kertas2' THEN 1 ELSE 0 END), 0) as paper2_attempts,
                MAX(attempted_at) as last_attempted_at
            FROM attempts
            WHERE user_id = %s
            """,
            (user_id,),
        )
        attempt_stats = cursor.fetchone() or {}

        cursor.execute(
            """
            SELECT
                COUNT(*) as total_sessions,
                COALESCE(SUM(duration_seconds), 0) as total_study_seconds,
                COALESCE(MAX(highest_streak), 0) as max_streak,
                COALESCE(SUM(
                    CASE 
                        WHEN YEARWEEK(start_time, 1) = YEARWEEK(CURDATE(), 1)
                        THEN COALESCE(duration_seconds, 0)
                        ELSE 0
                    END
                ), 0) as current_week_seconds,
                COALESCE(SUM(
                    CASE 
                        WHEN YEARWEEK(start_time, 1) = YEARWEEK(DATE_SUB(CURDATE(), INTERVAL 1 WEEK), 1)
                        THEN COALESCE(duration_seconds, 0)
                        ELSE 0
                    END
                ), 0) as previous_week_seconds,
                MAX(COALESCE(end_time, start_time)) as last_session_at
            FROM practice_sessions
            WHERE user_id = %s
            """,
            (user_id,),
        )
        session_stats = cursor.fetchone() or {}

        total_questions_attempted = int(attempt_stats.get("total_questions_attempted") or 0)
        overall_accuracy_raw = float(attempt_stats.get("overall_accuracy") or 0)
        overall_accuracy_percent = int(round(overall_accuracy_raw * 100))
        avg_time_per_question = float(attempt_stats.get("avg_time_per_question") or 0)
        paper1_attempts = int(attempt_stats.get("paper1_attempts") or 0)
        paper2_attempts = int(attempt_stats.get("paper2_attempts") or 0)

        total_sessions = int(session_stats.get("total_sessions") or 0)
        total_study_seconds = int(session_stats.get("total_study_seconds") or 0)
        max_streak = int(session_stats.get("max_streak") or 0)
        current_week_seconds = int(session_stats.get("current_week_seconds") or 0)
        previous_week_seconds = int(session_stats.get("previous_week_seconds") or 0)

        last_updated_at = session_stats.get("last_session_at") or attempt_stats.get("last_attempted_at")

        if not grade_model or total_questions_attempted == 0:
            return {
                "grade": "N/A",
                "confidence": 0,
                "accuracy": overall_accuracy_percent,
                "message": "No practice data yet." if not is_bm(lang) else "Belum ada data latihan.",
                "total_questions_attempted": total_questions_attempted,
                "paper1_attempts": paper1_attempts,
                "paper2_attempts": paper2_attempts,
                "total_study_time": format_duration_hm(total_study_seconds),
                "total_study_seconds": total_study_seconds,
                "this_week_delta": format_week_delta(current_week_seconds - previous_week_seconds, lang),
                "practice_accuracy": overall_accuracy_percent,
                "last_updated_at": last_updated_at.isoformat() if last_updated_at else None,
            }

        features = [[
            total_questions_attempted,
            overall_accuracy_raw,
            avg_time_per_question,
            total_sessions,
            max_streak,
        ]]

        predicted_grade = grade_model.predict(features)[0]
        confidence_score = calculate_prediction_confidence(
            grade_model,
            features,
            predicted_grade,
            total_questions_attempted,
            total_sessions,
            overall_accuracy_percent,
        )

        if is_bm(lang):
            if predicted_grade in ["A+", "A", "A-"]:
                feedback_msg = "Prestasi keseluruhan sangat baik. Teruskan momentum ini."
            elif predicted_grade in ["B+", "B", "B-"]:
                feedback_msg = "Prestasi semakin stabil. Tumpukan pada topik yang masih lemah."
            elif predicted_grade in ["C+", "C", "D"]:
                feedback_msg = "Masih ada ruang penambahbaikan. Ulang kaji topik berisiko tinggi dengan lebih konsisten."
            else:
                feedback_msg = "Teruskan berlatih. Lebih banyak data latihan akan membantu ramalan menjadi lebih tepat."
        else:
            if predicted_grade in ["A+", "A", "A-"]:
                feedback_msg = "Overall performance is strong. Keep maintaining this momentum."
            elif predicted_grade in ["B+", "B", "B-"]:
                feedback_msg = "Performance is becoming more stable. Focus on weaker topics next."
            elif predicted_grade in ["C+", "C", "D"]:
                feedback_msg = "There is still room to improve. Revise higher-risk topics more consistently."
            else:
                feedback_msg = "Keep practicing. More learning data will help make the prediction more reliable."

        return {
            "grade": predicted_grade,
            "confidence": confidence_score,
            "accuracy": overall_accuracy_percent,
            "message": feedback_msg,
            "total_questions_attempted": total_questions_attempted,
            "paper1_attempts": paper1_attempts,
            "paper2_attempts": paper2_attempts,
            "total_study_time": format_duration_hm(total_study_seconds),
            "total_study_seconds": total_study_seconds,
            "this_week_delta": format_week_delta(current_week_seconds - previous_week_seconds, lang),
            "practice_accuracy": overall_accuracy_percent,
            "last_updated_at": last_updated_at.isoformat() if last_updated_at else None,
        }

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# Builds the payload for topic recommendation
def build_topic_recommendation_payload(user_id, lang="english"):
    conn = None
    cursor = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        query = """
            SELECT 
                c.id as chapter_id,
                c.form,
                c.chapter_no,
                c.name_en,
                c.name_bm,
                c.spm_weightage_percentage,
                COUNT(a.attempt_id) as total_attempts,
                COALESCE(AVG(a.is_correct), 0) as accuracy,
                MAX(a.attempted_at) as last_practiced
            FROM chapters c
            LEFT JOIN attempts a
                ON a.chapter_snapshot_id = c.id
               AND a.user_id = %s
            WHERE c.spm_weightage_percentage > 0
            GROUP BY c.id, c.form, c.chapter_no, c.name_en, c.name_bm, c.spm_weightage_percentage
        """
        cursor.execute(query, (user_id,))
        topics_data = cursor.fetchall()

        recommendations = []
        topic_breakdown = []
        now = datetime.now()

        mastery_stats = {
            "total": 0,
            "mastered": 0,
            "average": 0,
            "review": 0,
        }

        for topic in topics_data:
            chapter_id = topic["chapter_id"]
            topic_name = topic["name_bm"] if is_bm(lang) else topic["name_en"]
            weightage = float(topic["spm_weightage_percentage"] or 0)
            attempts = int(topic["total_attempts"] or 0)
            accuracy_raw = float(topic["accuracy"] or 0)
            accuracy_percent = int(round(accuracy_raw * 100))
            last_practiced = topic["last_practiced"]

            status = get_topic_status(accuracy_percent, attempts)
            days_since = (now - last_practiced).days if last_practiced else 999

            if status != "unpracticed":
                mastery_stats["total"] += 1
                mastery_stats[status] += 1

            topic_breakdown.append({
                "chapter_id": chapter_id,
                "form": topic["form"],
                "chapter_no": topic["chapter_no"],
                "topic_name": topic_name,
                "accuracy": accuracy_percent,
                "total_attempts": attempts,
                "status": status,
                "weightage": weightage,
                "last_practiced": last_practiced.isoformat() if last_practiced else None,
                "is_weak_highlight": status == "review",
            })

            priority_score = 0
            reason = ""
            action_text = ""

            if attempts == 0:
                priority_score = weightage * 1.8
                reason = (
                    "Topik ini belum pernah dibuat dan mempunyai pemberat SPM yang tinggi."
                    if is_bm(lang)
                    else "This topic has not been practiced yet and carries high SPM weightage."
                )
                action_text = (
                    f"Mulakan latihan asas untuk {topic_name}."
                    if is_bm(lang)
                    else f"Start a basic practice session for {topic_name}."
                )
            else:
                weakness_factor = (100 - accuracy_percent)
                recency_factor = min(days_since, 30)

                priority_score = (weightage * 0.55) + (weakness_factor * 0.35) + (recency_factor * 0.10)

                if accuracy_percent < 50:
                    reason = (
                        f"Ketepatan hanya {accuracy_percent}% dan topik ini perlu diulang kaji segera."
                        if is_bm(lang)
                        else f"Accuracy is only {accuracy_percent}%, so this topic needs urgent review."
                    )
                elif days_since >= 14:
                    reason = (
                        f"Topik ini tidak dibuat selama {days_since} hari."
                        if is_bm(lang)
                        else f"This topic has not been practiced for {days_since} days."
                    )
                else:
                    reason = (
                        "Topik ini sesuai untuk pengukuhan seterusnya."
                        if is_bm(lang)
                        else "This topic is suitable for reinforcement next."
                    )

                if accuracy_percent < 50:
                    action_text = (
                        f"Latih 8 soalan tahap sederhana untuk {topic_name}."
                        if is_bm(lang)
                        else f"Practice 8 medium-level questions for {topic_name}."
                    )
                else:
                    action_text = (
                        f"Semak semula {topic_name} dengan 5 soalan pengukuhan."
                        if is_bm(lang)
                        else f"Reinforce {topic_name} with 5 review questions."
                    )

            recommendations.append({
                "chapter_id": chapter_id,
                "topic_name": topic_name,
                "priority_score": round(priority_score, 2),
                "reason": reason,
                "accuracy": accuracy_percent,
                "total_attempts": attempts,
                "urgency": "high" if priority_score >= 45 else "medium" if priority_score >= 25 else "low",
                "action_text": action_text,
            })

        recommendations.sort(key=lambda x: x["priority_score"], reverse=True)
        topic_breakdown.sort(key=lambda x: ({"review": 0, "average": 1, "mastered": 2, "unpracticed": 3}[x["status"]], x["accuracy"]))

        top_3_recommendations = recommendations[:3]
        for index, item in enumerate(top_3_recommendations):
            item["priority_label"] = get_priority_label(index, lang)

        return {
            "recommendations": top_3_recommendations,
            "summary": mastery_stats,
            "topics": topic_breakdown,
        }

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# Build payload for study pattern analyzer 
def build_study_pattern_payload(user_id, lang="english"):
    if not pattern_model:
        return {
            "persona": "N/A",
            "proof": "AI model not loaded." if not is_bm(lang) else "Model AI belum dimuatkan.",
            "suggestion": "-",
            "total_time": "0h 0m",
            "color": "#6b7280",
        }

    conn = None
    cursor = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        query = """
            SELECT 
                COUNT(DISTINCT s.practice_id) as total_sessions,
                COUNT(a.attempt_id) as total_questions,
                IFNULL(AVG(a.time_taken_seconds), 0) as avg_time_per_question
            FROM users u
            LEFT JOIN attempts a ON u.id = a.user_id
            LEFT JOIN practice_sessions s ON a.practice_id = s.practice_id
            WHERE u.id = %s;
        """
        cursor.execute(query, (user_id,))
        stats = cursor.fetchone()

        total_sessions = stats["total_sessions"]
        total_questions = stats["total_questions"]
        avg_time = float(stats["avg_time_per_question"])

        total_seconds = total_questions * avg_time
        hours = int(total_seconds // 3600)
        minutes = int((total_seconds % 3600) // 60)
        time_string = f"{hours}h {minutes}m"

        if total_sessions == 0:
            return {
                "persona": "Peneroka Baharu" if is_bm(lang) else "New Explorer",
                "proof": "Belum ada sesi latihan diselesaikan." if is_bm(lang) else "No completed practice sessions yet.",
                "suggestion": "Mulakan sesi latihan untuk membolehkan AI menganalisis corak pembelajaran." if is_bm(lang) else "Start a practice session so the AI can analyze the learning pattern.",
                "total_time": "0h 0m",
                "color": "#6b7280",
            }

        questions_per_session = total_questions / total_sessions

        features = pd.DataFrame(
            [[total_sessions, questions_per_session, avg_time]],
            columns=["total_sessions", "questions_per_session", "avg_time_per_question"]
        )

        scaled_features = pattern_scaler.transform(features)
        cluster_id = pattern_model.predict(scaled_features)[0]
        persona = pattern_persona_map[cluster_id]

        if persona == "Consistent Achiever":
            persona_text = "Pelajar Konsisten" if is_bm(lang) else "Consistent Achiever"
            proof = (
                f"Berlatih secara konsisten dalam {total_sessions} sesi."
                if is_bm(lang)
                else f"Practices consistently across {total_sessions} sessions."
            )
            suggestion = (
                "Teruskan momentum pembelajaran yang stabil ini."
                if is_bm(lang)
                else "Keep maintaining this steady study rhythm."
            )
            color = "#1ac089"
        elif persona == "The Crammer":
            persona_text = "Pelajar Last-Minute" if is_bm(lang) else "The Crammer"
            proof = (
                f"Banyak soalan setiap sesi ({int(questions_per_session)} soalan/sesi) tetapi tidak begitu kerap."
                if is_bm(lang)
                else f"Does many questions per session ({int(questions_per_session)} questions/session) but less frequently."
            )
            suggestion = (
                "Bahagikan masa belajar kepada sesi kecil yang lebih kerap."
                if is_bm(lang)
                else "Break study into smaller and more frequent sessions."
            )
            color = "#D97706"
        else:
            persona_text = "Perlu Motivasi" if is_bm(lang) else "Needs Motivation"
            proof = (
                "Sesi latihan singkat dan tidak kerap."
                if is_bm(lang)
                else "Practice sessions are brief and infrequent."
            )
            suggestion = (
                "Cuba sasarkan sedikit soalan setiap hari untuk bina konsistensi."
                if is_bm(lang)
                else "Try a small daily question goal to build consistency."
            )
            color = "#EF4444"

        return {
            "persona": persona_text,
            "proof": proof,
            "suggestion": suggestion,
            "total_time": time_string,
            "color": color,
        }

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def build_study_schedule_payload(user_id, lang="english", recommendation_data=None):
    conn = None
    cursor = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT 
                DATE(start_time) as study_date,
                HOUR(start_time) as study_hour,
                COALESCE(duration_seconds, 0) as duration_seconds
            FROM practice_sessions
            WHERE user_id = %s
            ORDER BY start_time ASC
            """,
            (user_id,),
        )
        sessions = cursor.fetchall()

        pattern_data = build_study_pattern_payload(user_id, lang)

        if not sessions:
            default_time_window = "8:00 PM - 8:40 PM"
            return {
                "pattern_type": pattern_data.get("persona", "N/A"),
                "best_time_window": default_time_window,
                "recommended_session_length_minutes": 40,
                "recommended_session_length_label": "40 mins" if not is_bm(lang) else "40 minit",
                "weekly_target_sessions": 3,
                "weekly_progress": {
                    "completed": 0,
                    "target": 3,
                    "label": "0/3 sessions completed" if not is_bm(lang) else "0/3 sesi selesai",
                },
                "next_suggested_session": {
                    "label": "Tonight" if not is_bm(lang) else "Malam ini",
                    "time_window": default_time_window,
                    "focus_topic": "Mixed revision" if not is_bm(lang) else "Ulang kaji campuran",
                    "chapter_id": None,
                },
                "weekly_plan": [],
            }

        hours = [row["study_hour"] for row in sessions if row["study_hour"] is not None]
        best_hour = Counter(hours).most_common(1)[0][0] if hours else 20

        durations = [int(row["duration_seconds"] or 0) for row in sessions if int(row["duration_seconds"] or 0) > 0]
        avg_duration_minutes = int(round((sum(durations) / len(durations)) / 60 / 5) * 5) if durations else 40
        avg_duration_minutes = clamp(avg_duration_minutes, 30, 45)

        best_time_window = format_hour_window(best_hour, avg_duration_minutes)

        persona = str(pattern_data.get("persona", "")).lower()
        if "consistent" in persona or "konsisten" in persona:
            weekly_target_sessions = 4
        elif "crammer" in persona or "last-minute" in persona:
            weekly_target_sessions = 4
        else:
            weekly_target_sessions = 3

        current_yearweek = datetime.now().strftime("%Y-%U")
        this_week_completed = 0
        session_dates = []

        for row in sessions:
            study_date = row["study_date"]
            if study_date:
                session_dates.append(study_date)
                if study_date.strftime("%Y-%U") == current_yearweek:
                    this_week_completed += 1

        top_recommendation = (recommendation_data or {}).get("recommendations", [])
        top_recommendation = top_recommendation[0] if top_recommendation else None

        focus_topic = (
            top_recommendation["topic_name"]
            if top_recommendation
            else ("Mixed revision" if not is_bm(lang) else "Ulang kaji campuran")
        )

        chapter_id = top_recommendation["chapter_id"] if top_recommendation else None

        weekly_progress_label = (
            f"{this_week_completed}/{weekly_target_sessions} sessions completed"
            if not is_bm(lang)
            else f"{this_week_completed}/{weekly_target_sessions} sesi selesai"
        )

        weekday_labels = get_weekday_labels(lang)
        preferred_day_indexes = [0, 2, 4, 6] if weekly_target_sessions >= 4 else [1, 3, 5]

        weekly_plan = []
        for day_index in preferred_day_indexes[:weekly_target_sessions]:
            weekly_plan.append({
                "day_label": weekday_labels[day_index],
                "time_window": best_time_window,
                "focus_topic": focus_topic,
            })

        return {
            "pattern_type": pattern_data.get("persona", "N/A"),
            "best_time_window": best_time_window,
            "recommended_session_length_minutes": avg_duration_minutes,
            "recommended_session_length_label": (
                f"{avg_duration_minutes} mins"
                if not is_bm(lang)
                else f"{avg_duration_minutes} minit"
            ),
            "weekly_target_sessions": weekly_target_sessions,
            "weekly_progress": {
                "completed": this_week_completed,
                "target": weekly_target_sessions,
                "label": weekly_progress_label,
            },
            "next_suggested_session": {
                "label": get_next_session_label(best_hour, lang),
                "time_window": best_time_window,
                "focus_topic": focus_topic,
                "chapter_id": chapter_id,
            },
            "weekly_plan": weekly_plan,
        }

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def build_consistency_payload(user_id, lang="english", study_schedule_data=None):
    conn = None
    cursor = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT DISTINCT DATE(start_time) as study_date
            FROM practice_sessions
            WHERE user_id = %s
            ORDER BY study_date ASC
            """,
            (user_id,),
        )
        rows = cursor.fetchall()

        session_dates = [row["study_date"] for row in rows if row["study_date"]]
        current_streak, best_streak = calculate_streaks(session_dates)

        schedule = study_schedule_data or {
            "weekly_target_sessions": 3,
            "weekly_progress": {"completed": 0, "target": 3, "label": "0/3"},
            "next_suggested_session": {
                "label": "Tonight" if not is_bm(lang) else "Malam ini",
                "time_window": "8:00 PM - 8:40 PM",
                "focus_topic": "Mixed revision" if not is_bm(lang) else "Ulang kaji campuran",
            },
        }

        next_reminder = (
            f"{schedule['next_suggested_session']['label']}, {schedule['next_suggested_session']['time_window']} - {schedule['next_suggested_session']['focus_topic']}"
        )

        return {
            "current_streak_days": current_streak,
            "best_streak_days": best_streak,
            "weekly_target_sessions": schedule["weekly_target_sessions"],
            "weekly_completed_sessions": schedule["weekly_progress"]["completed"],
            "weekly_progress_label": schedule["weekly_progress"]["label"],
            "next_session_reminder": next_reminder,
        }

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def build_topic_mastery_payload(user_id, lang="english", recommendation_data=None):
    recommendation_data = recommendation_data or build_topic_recommendation_payload(user_id, lang)

    summary = recommendation_data.get("summary", {})
    topics = recommendation_data.get("topics", [])

    weak_topics = [topic for topic in topics if topic.get("status") == "review"][:3]

    return {
        "mastered_count": summary.get("mastered", 0),
        "average_count": summary.get("average", 0),
        "review_count": summary.get("review", 0),
        "topics": topics,
        "weak_topics": weak_topics,
    }


def build_performance_trend_payload(user_id, lang="english"):
    conn = None
    cursor = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT 
                s.practice_id,
                COALESCE(s.accuracy_snapshot, 0) as accuracy_snapshot,
                s.paper_type,
                COALESCE(s.end_time, s.start_time) as session_time
            FROM practice_sessions s
            WHERE s.user_id = %s
            ORDER BY COALESCE(s.end_time, s.start_time) DESC
            LIMIT 10
            """,
            (user_id,),
        )
        rows = cursor.fetchall()
        rows.reverse()

        trend_points = []
        for index, row in enumerate(rows, start=1):
            session_time = row["session_time"]
            label = session_time.strftime("%d %b") if session_time else f"S{index}"

            trend_points.append({
                "label": label,
                "accuracy": float(row["accuracy_snapshot"] or 0),
                "paper_type": row["paper_type"],
            })

        trend_direction = "stable"
        if len(trend_points) >= 2:
            first_value = trend_points[0]["accuracy"]
            last_value = trend_points[-1]["accuracy"]
            if last_value > first_value:
                trend_direction = "up"
            elif last_value < first_value:
                trend_direction = "down"

        return {
            "points": trend_points,
            "trend_direction": trend_direction,
        }

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def build_ai_performance_overview_payload(user_id, lang="english", grade_data=None, recommendation_data=None):
    grade_data = grade_data or build_grade_prediction_payload(user_id, lang)
    recommendation_data = recommendation_data or build_topic_recommendation_payload(user_id, lang)

    topics = recommendation_data.get("topics", [])
    recommendations = recommendation_data.get("recommendations", [])

    practiced_topics = [topic for topic in topics if topic.get("total_attempts", 0) > 0]
    strength_topic = max(practiced_topics, key=lambda x: x["accuracy"], default=None)
    concern_topic = next((topic for topic in topics if topic.get("status") == "review"), None)
    next_recommendation = recommendations[0] if recommendations else None

    if strength_topic:
        strength_text = (
            f"Anda menunjukkan prestasi yang baik dalam {strength_topic['topic_name']}."
            if is_bm(lang)
            else f"You are doing well in {strength_topic['topic_name']}."
        )
    else:
        strength_text = (
            "Belum cukup data untuk mengenal pasti kekuatan utama."
            if is_bm(lang)
            else "There is not enough data yet to identify your strongest area."
        )

    if concern_topic:
        concern_text = (
            f"Konsistensi anda dalam {concern_topic['topic_name']} masih lemah."
            if is_bm(lang)
            else f"Your consistency in {concern_topic['topic_name']} is still weak."
        )
    else:
        concern_text = (
            "Tiada kebimbangan utama dikesan buat masa ini."
            if is_bm(lang)
            else "No major concern is detected at the moment."
        )

    if next_recommendation:
        next_action_text = next_recommendation.get("action_text")
    else:
        next_action_text = (
            "Teruskan sesi latihan seterusnya untuk menjana cadangan yang lebih tepat."
            if is_bm(lang)
            else "Continue your next practice session to generate more precise recommendations."
        )

    return {
        "predicted_grade": grade_data.get("grade", "N/A"),
        "confidence": grade_data.get("confidence", 0),
        "strength": strength_text,
        "concern": concern_text,
        "next_best_action": next_action_text,
    }

def build_study_heatmap_payload(user_id, selected_year):
    conn = None
    cursor = None

    try:
        if not selected_year:
            selected_year = datetime.now().year

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT
                DATE(start_time) as activity_date,
                COALESCE(SUM(duration_seconds), 0) as total_seconds
            FROM practice_sessions
            WHERE user_id = %s
              AND YEAR(start_time) = %s
            GROUP BY DATE(start_time)
            ORDER BY activity_date ASC
            """,
            (user_id, selected_year),
        )
        rows = cursor.fetchall()

        seconds_by_date = {
            row["activity_date"]: int(row["total_seconds"] or 0)
            for row in rows
            if row["activity_date"]
        }

        year_start = datetime(selected_year, 1, 1).date()
        year_end = datetime(selected_year, 12, 31).date()

        cells = []
        active_days = 0
        best_minutes = 0

        day = year_start
        while day <= year_end:
            minutes = int(round((seconds_by_date.get(day, 0)) / 60))

            if minutes > 0:
                active_days += 1

            best_minutes = max(best_minutes, minutes)

            if minutes == 0:
                intensity = 0
            elif minutes < 15:
                intensity = 1
            elif minutes < 30:
                intensity = 2
            elif minutes < 60:
                intensity = 3
            else:
                intensity = 4

            cells.append({
                "date": day.isoformat(),
                "minutes": minutes,
                "intensity": intensity,
            })

            day += timedelta(days=1)

        return {
            "cells": cells,
            "active_days": active_days,
            "best_minutes": best_minutes,
        }

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def build_student_dashboard_payload(user_id, lang="english", selected_year=None):
    from dashboard_intelligence import build_dashboard_intelligence
    if not selected_year:
        selected_year = datetime.now().year

    grade_data = build_grade_prediction_payload(user_id, lang)
    recommendation_data = build_topic_recommendation_payload(user_id, lang)
    study_pattern_data = build_study_pattern_payload(user_id, lang)
    study_schedule_data = build_study_schedule_payload(user_id, lang, recommendation_data)
    consistency_data = build_consistency_payload(user_id, lang, study_schedule_data)
    topic_mastery_data = build_topic_mastery_payload(user_id, lang, recommendation_data)
    performance_trend_data = build_performance_trend_payload(user_id, lang)
    ai_overview_data = build_ai_performance_overview_payload(
        user_id,
        lang,
        grade_data,
        recommendation_data,
    )

    return {
        "kpis": {
            "predicted_grade": {
                "grade": grade_data.get("grade", "N/A"),
                "confidence": grade_data.get("confidence", 0),
            },
            "practice_accuracy": {
                "accuracy": grade_data.get("practice_accuracy", 0),
            },
            "total_questions_attempted": {
                "total": grade_data.get("total_questions_attempted", 0),
                "paper1": grade_data.get("paper1_attempts", 0),
                "paper2": grade_data.get("paper2_attempts", 0),
            },
            "total_study_time": {
                "total": grade_data.get("total_study_time", "0h 0m"),
                "this_week_delta": grade_data.get("this_week_delta", "No change this week"),
            },
            "last_updated_at": grade_data.get("last_updated_at"),
        },
        "ai_overview": ai_overview_data,
        "study_pattern": study_pattern_data,
        "study_schedule": study_schedule_data,
        "study_heatmap": build_study_heatmap_payload(user_id, selected_year),
        "consistency": consistency_data,
        "topic_recommendations": recommendation_data.get("recommendations", []),
        "topic_mastery": topic_mastery_data,
        "performance_trend": performance_trend_data,
    }


@app.route("/api/student/dashboard/<int:student_id>", methods=["GET"])
@require_auth("student", "parent", "admin")
def get_student_dashboard(student_id):
    from dashboard_intelligence import build_dashboard_intelligence
    conn = None
    cursor = None

    try:
        # Access control
        if g.current_user["role"] == "student" and g.current_user["id"] != student_id:
            return jsonify({
                "success": False,
                "message": "Forbidden."
            }), 403

        if g.current_user["role"] == "parent":
            if not is_parent_linked_to_student(g.current_user["id"], student_id):
                return jsonify({
                    "success": False,
                    "message": "Forbidden."
                }), 403

        lang = request.args.get("lang", g.current_user.get("language", "english"))
        year = request.args.get("year", datetime.now().year)

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        dashboard = build_dashboard_intelligence(
            cursor=cursor,
            student_id=student_id,
            lang=lang,
            year=year,
            grade_model=grade_model,
            pattern_model=pattern_model,
            pattern_scaler=pattern_scaler,
            pattern_persona_map=pattern_persona_map,
        )

        return jsonify({
            "success": True,
            **dashboard
        }), 200

    except Exception as e:
        print("STUDENT DASHBOARD ERROR:", e)
        return jsonify({
            "success": False,
            "message": "Failed to load dashboard data."
        }), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
    
# Endpoint for student to create a new chat session
@app.route("/api/chat/sessions", methods=["POST"])
@require_auth("student")
def create_chat_session():
    conn = None
    cursor = None

    try:
        data = request.json or {}
        language_code = normalize_chat_language(
            data.get("language", g.current_user.get("language", "english"))
        )
        title = (data.get("title") or "").strip() or (
            "Chat Baharu" if is_bm(language_code) else "New Chat"
        )

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO chat_sessions
            (
                student_id,
                title,
                created_language,
                last_active_language,
                source_type,
                source_context_json
            )
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (
                g.current_user["id"],
                title,
                language_code,
                language_code,
                "normal",
                None,
            ),
        )

        chat_session_id = cursor.lastrowid
        conn.commit()

        return jsonify({
            "success": True,
            "chat_session_id": chat_session_id,
            "title": title,
            "created_language": language_code,
        }), 201

    except Exception as e:
        print("CREATE CHAT SESSION ERROR:", e)
        return jsonify({
            "success": False,
            "message": "Failed to create chat session."
        }), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# Endpoint for student to get list of their chat sessions with last message preview
@app.route("/api/chat/sessions", methods=["GET"])
@require_auth("student")
def get_chat_sessions():
    conn = None
    cursor = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT
                cs.chat_session_id,
                cs.title,
                cs.created_language,
                cs.last_active_language,
                cs.created_at,
                cs.updated_at,
                cs.source_type,
                (
                    SELECT cm.message_text
                    FROM chat_messages cm
                    WHERE cm.chat_session_id = cs.chat_session_id
                        AND cm.sender = 'user'
                    ORDER BY cm.created_at DESC, cm.message_id DESC
                    LIMIT 1
                ) AS last_message_preview
            FROM chat_sessions cs
            WHERE cs.student_id = %s
              AND cs.is_archived = 0
            ORDER BY cs.updated_at DESC, cs.chat_session_id DESC
            """,
            (g.current_user["id"],),
        )

        sessions = cursor.fetchall() or []

        for row in sessions:
            row["source_type"] = row.get("source_type") or "normal"
            row["is_quick_snap_session"] = row.get("source_type") == "quick_snap"

            if row.get("created_at"):
                row["created_at"] = row["created_at"].isoformat()

            if row.get("updated_at"):
                row["updated_at"] = row["updated_at"].isoformat()

        return jsonify({
            "success": True,
            "sessions": sessions
        }), 200

    except Exception as e:
        print("GET CHAT SESSIONS ERROR:", e)
        return jsonify({
            "success": False,
            "message": "Failed to load chat sessions."
        }), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# Endpoint for student to get messages of a specific chat session
@app.route("/api/chat/sessions/<int:chat_session_id>/messages", methods=["GET"])
@require_auth("student")
def get_chat_session_messages(chat_session_id):
    conn = None
    cursor = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT
                chat_session_id,
                source_type,
                source_context_json
            FROM chat_sessions
            WHERE chat_session_id = %s
              AND student_id = %s
              AND is_archived = 0
            LIMIT 1
            """,
            (chat_session_id, g.current_user["id"]),
        )
        session = cursor.fetchone()

        if not session:
            return jsonify({
                "success": False,
                "message": "Chat session not found."
            }), 404

        cursor.execute(
            """
            SELECT
                message_id,
                sender,
                message_text,
                message_language,
                tutoring_mode,
                retrieved_refs_json,
                created_at
            FROM chat_messages
            WHERE chat_session_id = %s
            ORDER BY created_at ASC, message_id ASC
            """,
            (chat_session_id,),
        )

        messages = cursor.fetchall() or []

        for msg in messages:
            if msg.get("created_at"):
                msg["created_at"] = msg["created_at"].isoformat()

            msg["retrieved_refs_json"] = parse_json_column(
                msg.get("retrieved_refs_json")
            )

        quick_snap_context = parse_json_column(
            session.get("source_context_json")
        )

        return jsonify({
            "success": True,
            "messages": messages,
            "source_type": session.get("source_type") or "normal",
            "quick_snap_context": quick_snap_context,
        }), 200

    except Exception as e:
        print("GET CHAT MESSAGES ERROR:", e)
        return jsonify({
            "success": False,
            "message": "Failed to load chat messages."
        }), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# Endpoint for student to update chat session title
@app.route("/api/chat/sessions/<int:chat_session_id>/title", methods=["PATCH"])
@require_auth("student")
def update_chat_session_title(chat_session_id):
    conn = None
    cursor = None

    try:
        if not student_owns_chat_session(chat_session_id, g.current_user["id"]):
            return jsonify({
                "success": False,
                "message": "Forbidden."
            }), 403

        data = request.json or {}
        title = (data.get("title") or "").strip()

        if not title:
            return jsonify({
                "success": False,
                "message": "Title is required."
            }), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            UPDATE chat_sessions
            SET title = %s,
                updated_at = NOW()
            WHERE chat_session_id = %s
              AND student_id = %s
              AND is_archived = 0
            """,
            (title, chat_session_id, g.current_user["id"]),
        )

        conn.commit()

        return jsonify({
            "success": True,
            "message": "Chat title updated successfully."
        }), 200

    except Exception as e:
        print("UPDATE CHAT TITLE ERROR:", e)
        return jsonify({
            "success": False,
            "message": "Failed to update chat title."
        }), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# Endpoint for student to delete (archive) a chat session
@app.route("/api/chat/sessions/<int:chat_session_id>", methods=["DELETE"])
@require_auth("student")
def delete_chat_session(chat_session_id):
    conn = None
    cursor = None

    try:
        if not student_owns_chat_session(chat_session_id, g.current_user["id"]):
            return jsonify({
                "success": False,
                "message": "Forbidden."
            }), 403

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            UPDATE chat_sessions
            SET is_archived = 1,
                updated_at = NOW()
            WHERE chat_session_id = %s
              AND student_id = %s
              AND is_archived = 0
            """,
            (chat_session_id, g.current_user["id"]),
        )

        conn.commit()

        return jsonify({
            "success": True,
            "message": "Chat hidden successfully."
        }), 200

    except Exception as e:
        print("DELETE CHAT SESSION ERROR:", e)
        return jsonify({
            "success": False,
            "message": "Failed to delete chat."
        }), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


#### PARENT MODULE ####
# Endpoint for parent to view their linked children
@app.route("/api/parent/children", methods=["GET"])
@require_auth("parent")
def get_parent_children():
    conn = None
    cursor = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT
                u.id,
                u.name,
                u.email,
                u.photo_url,
                u.language,
                u.student_code,
                psl.nickname,
                psl.linked_at
            FROM parent_student_links psl
            JOIN users u ON u.id = psl.student_id
            WHERE psl.parent_id = %s
              AND psl.is_active = 1
              AND u.is_active = 1
            ORDER BY psl.linked_at DESC
            """,
            (g.current_user["id"],),
        )

        children = cursor.fetchall()

        return jsonify({
            "success": True,
            "children": children
        }), 200

    except Exception as e:
        print("GET PARENT CHILDREN ERROR:", e)
        return jsonify({
            "success": False,
            "message": "Failed to load linked children."
        }), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# endpoint for parent to link a child using student code
@app.route("/api/parent/children/link", methods=["POST"])
@require_auth("parent")
def link_child_to_parent():
    conn = None
    cursor = None

    try:
        data = request.json or {}
        student_code = (data.get("student_code") or "").strip()
        nickname = (data.get("nickname") or "").strip() or None

        if not student_code:
            return jsonify({
                "success": False,
                "message": "Student code is required."
            }), 400

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Find student
        cursor.execute(
            """
            SELECT id, name, email, photo_url, language, student_code
            FROM users
            WHERE student_code = %s
              AND role = 'student'
              AND is_active = 1
            LIMIT 1
            """,
            (student_code,),
        )
        student = cursor.fetchone()

        if not student:
            return jsonify({
                "success": False,
                "message": "Student code not found."
            }), 404

        # Check any existing link, active or inactive
        cursor.execute(
            """
            SELECT link_id, is_active, nickname
            FROM parent_student_links
            WHERE parent_id = %s
              AND student_id = %s
            LIMIT 1
            """,
            (g.current_user["id"], student["id"]),
        )
        existing_link = cursor.fetchone()

        # Already active
        if existing_link and existing_link["is_active"] == 1:
            return jsonify({
                "success": False,
                "message": "This child is already linked."
            }), 409

        # Previously unlinked -> reactivate same row
        if existing_link and existing_link["is_active"] == 0:
            final_nickname = nickname if nickname else None

            cursor.execute(
                """
                UPDATE parent_student_links
                SET is_active = 1,
                    nickname = %s,
                    linked_at = NOW(),
                    unlinked_at = NULL
                WHERE link_id = %s
                """,
                (final_nickname, existing_link["link_id"]),
            )
            conn.commit()

            return jsonify({
                "success": True,
                "message": "Child linked successfully.",
                "child": {
                    "id": student["id"],
                    "name": student["name"],
                    "email": student["email"],
                    "photo_url": student["photo_url"],
                    "language": student["language"],
                    "student_code": student["student_code"],
                    "nickname": final_nickname,
                }
            }), 200

        # First-time link
        cursor.execute(
            """
            INSERT INTO parent_student_links (parent_id, student_id, nickname)
            VALUES (%s, %s, %s)
            """,
            (g.current_user["id"], student["id"], nickname),
        )
        conn.commit()

        return jsonify({
            "success": True,
            "message": "Child linked successfully.",
            "child": {
                "id": student["id"],
                "name": student["name"],
                "email": student["email"],
                "photo_url": student["photo_url"],
                "language": student["language"],
                "student_code": student["student_code"],
                "nickname": nickname,
            }
        }), 201

    except Exception as e:
        print("LINK CHILD ERROR:", e)
        return jsonify({
            "success": False,
            "message": "Failed to link child."
        }), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# endpoint for parent to unlink a child
@app.route("/api/parent/children/<int:student_id>", methods=["DELETE"])
@require_auth("parent")
def unlink_child_from_parent(student_id):
    conn = None
    cursor = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            UPDATE parent_student_links
            SET is_active = 0,
                unlinked_at = NOW()
            WHERE parent_id = %s
              AND student_id = %s
              AND is_active = 1
            """,
            (g.current_user["id"], student_id),
        )

        if cursor.rowcount == 0:
            return jsonify({
                "success": False,
                "message": "Linked child not found."
            }), 404

        conn.commit()

        return jsonify({
            "success": True,
            "message": "Child unlinked successfully."
        }), 200

    except Exception as e:
        print("UNLINK CHILD ERROR:", e)
        return jsonify({
            "success": False,
            "message": "Failed to unlink child."
        }), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def get_child_display_name(child):
    return (
        child.get("nickname")
        or child.get("name")
        or "the student"
    )


def parentize_text(text, child_name, lang="english"):
    """
    Convert student-facing dashboard sentences into parent-facing sentences.

    "Your current accuracy is 55.7%."
    -> "XX's current accuracy is 55.7%."
    """
    if not text:
        return text

    text = str(text)

    # BM simple fallback for now
    if str(lang).lower() == "bm":
        replacements = [
            (r"\bAnda telah\b", f"{child_name} telah"),
            (r"\banda telah\b", f"{child_name} telah"),
            (r"\bAnda mempunyai\b", f"{child_name} mempunyai"),
            (r"\banda mempunyai\b", f"{child_name} mempunyai"),
            (r"\bAnda\b", child_name),
            (r"\banda\b", child_name),

            # Common possessive phrases
            (r"\bprestasi anda\b", f"prestasi {child_name}"),
            (r"\bketepatan anda\b", f"ketepatan {child_name}"),
            (r"\bpembelajaran anda\b", f"pembelajaran {child_name}"),
            (r"\blatihan anda\b", f"latihan {child_name}"),
            (r"\brutin anda\b", f"rutin {child_name}"),
        ]

        for pattern, replacement in replacements:
            text = re.sub(pattern, replacement, text)

        # Convert direct student instructions into parent-facing advice
        instruction_replacements = [
            (r"^Teruskan\b", f"Galakkan {child_name} untuk meneruskan"),
            (r"^Cuba\b", f"Galakkan {child_name} untuk mencuba"),
            (r"^Fokus\b", f"Galakkan {child_name} untuk fokus"),
            (r"^Lengkapkan\b", f"Galakkan {child_name} untuk melengkapkan"),
            (r"^Ulang kaji\b", f"Galakkan {child_name} untuk mengulang kaji"),
            (r"\. Teruskan latihan\b", f". Galakkan {child_name} untuk terus berlatih"),
            (r"\. Teruskan\b", f". Galakkan {child_name} untuk meneruskan"),
            (r"\. Cuba\b", f". Galakkan {child_name} untuk mencuba"),
            (r"\. Fokus\b", f". Galakkan {child_name} untuk fokus"),
            (r"\. Ulang kaji\b", f". Galakkan {child_name} untuk mengulang kaji"),
        ]

        for pattern, replacement in instruction_replacements:
            text = re.sub(pattern, replacement, text)

        return text

    replacements = [
        # Direct subject replacements
        (r"\bYou have\b", f"{child_name} has"),
        (r"\byou have\b", f"{child_name} has"),
        (r"\bYou are\b", f"{child_name} is"),
        (r"\byou are\b", f"{child_name} is"),
        (r"\bYou were\b", f"{child_name} was"),
        (r"\byou were\b", f"{child_name} was"),
        (r"\bYou practised\b", f"{child_name} practised"),
        (r"\byou practised\b", f"{child_name} practised"),
        (r"\bYou practiced\b", f"{child_name} practised"),
        (r"\byou practiced\b", f"{child_name} practised"),
        (r"\bYou completed\b", f"{child_name} completed"),
        (r"\byou completed\b", f"{child_name} completed"),
        (r"\bYou had\b", f"{child_name} had"),
        (r"\byou had\b", f"{child_name} had"),

        # Possessive replacements
        (r"\bYour\b", f"{child_name}'s"),
        (r"\byour\b", f"{child_name}'s"),

        # Instruction-style sentences
        (r"^Keep\b", f"Encourage {child_name} to keep"),
        (r"^Try\b", f"Encourage {child_name} to try"),
        (r"^Do\b", f"Encourage {child_name} to do"),
        (r"^Complete\b", f"Encourage {child_name} to complete"),
        (r"^Focus\b", f"Encourage {child_name} to focus"),
        (r"^Review\b", f"Encourage {child_name} to review"),

        (r"\. Keep practising\b", f". Encourage {child_name} to keep practising"),
        (r"\. Keep practicing\b", f". Encourage {child_name} to keep practising"),
        (r"\. Try\b", f". Encourage {child_name} to try"),
        (r"\. Focus\b", f". Encourage {child_name} to focus"),
        (r"\. Review\b", f". Encourage {child_name} to review"),

        # Extra fallback
        (r"Keep practising to maintain", f"Encourage {child_name} to keep practising to maintain"),
        (r"Keep practicing to maintain", f"Encourage {child_name} to keep practising to maintain"),
    ]

    for pattern, replacement in replacements:
        text = re.sub(pattern, replacement, text)

    return text


def parentize_dashboard_data(dashboard_data, child, lang="english"):
    """
    Convert the dashboard output into parent-friendly wording.
    This keeps the same data structure, so frontend can still reuse
    the StudentDashboard UI logic.
    """
    parent_data = copy.deepcopy(dashboard_data)
    child_name = get_child_display_name(child)

    # 1. AI overview
    ai_overview = parent_data.get("ai_overview", {})

    for key in ["strength", "concern", "prediction_reason"]:
        if key in ai_overview:
            ai_overview[key] = parentize_text(ai_overview[key], child_name, lang)

    # 2. Predicted grade reason
    predicted_grade = parent_data.get("kpis", {}).get("predicted_grade", {})
    if "reason" in predicted_grade:
        predicted_grade["reason"] = parentize_text(
            predicted_grade["reason"],
            child_name,
            lang
        )

    # 3. Study pattern
    study_pattern = parent_data.get("study_pattern", {})

    for key in ["proof", "suggestion"]:
        if key in study_pattern:
            study_pattern[key] = parentize_text(
                study_pattern[key],
                child_name,
                lang
            )

    # 4. Study schedule
    study_schedule = parent_data.get("study_schedule", {})

    for key in ["schedule_reason"]:
        if key in study_schedule:
            study_schedule[key] = parentize_text(
                study_schedule[key],
                child_name,
                lang
            )

    # 5. Topic recommendations
    recommendations = parent_data.get("topic_recommendations", [])

    for topic in recommendations:
        if "reason" in topic:
            topic["reason"] = parentize_text(topic["reason"], child_name, lang)

        if "action" in topic:
            action = topic.get("action") or ""

            # Convert action into parent-facing encouragement
            if action:
                action = parentize_text(action, child_name, lang)

                if str(lang).lower() != "bm":
                    if not action.lower().startswith("encourage"):
                        action = f"Encourage {child_name} to {action[0].lower()}{action[1:]}"

                topic["action"] = action

    return parent_data

# endpoint for parent to view their child's dashboard (only children they have access to)
@app.route("/api/parent/children/<int:student_id>/dashboard", methods=["GET"])
@require_auth("parent")
def get_parent_child_dashboard(student_id):
    from dashboard_intelligence import build_dashboard_intelligence
    lang = request.args.get("lang", "english")
    year = request.args.get("year", datetime.now().year)

    try:
        year = int(year)
    except Exception:
        year = datetime.now().year

    # Security: parent can only view linked child
    if not is_parent_linked_to_student(g.current_user["id"], student_id):
        return jsonify({
            "success": False,
            "message": "You are not allowed to view this student."
        }), 403

    conn = None
    cursor = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Get linked child profile
        cursor.execute("""
            SELECT
                u.id,
                u.name,
                u.email,
                u.student_code,
                u.photo_url,
                psl.nickname,
                psl.linked_at
            FROM users u
            JOIN parent_student_links psl
                ON psl.student_id = u.id
            WHERE psl.parent_id = %s
              AND psl.student_id = %s
              AND psl.is_active = 1
              AND u.role = 'student'
              AND u.is_active = 1
            LIMIT 1
        """, (g.current_user["id"], student_id))

        child = cursor.fetchone()

        if not child:
            return jsonify({
                "success": False,
                "message": "Linked child not found."
            }), 404

        # Reuse the same dashboard intelligence used by student dashboard
        dashboard_data = build_dashboard_intelligence(
            cursor=cursor,
            student_id=student_id,
            grade_model=grade_model,
            pattern_model=pattern_model,
            pattern_scaler=pattern_scaler,
            pattern_persona_map=pattern_persona_map,
            lang=lang,
            year=year
        )

        dashboard_data = parentize_dashboard_data(
            dashboard_data,
            child,
            lang
        )

        response_data = {
            "success": True,
            "child": child,
            **dashboard_data
        }

        return jsonify(make_json_safe(response_data)), 200

    except TypeError:
        # Fallback in case build_dashboard_intelligence uses positional arguments
        try:
            dashboard_data = build_dashboard_intelligence(
                cursor,
                student_id,
                grade_model,
                pattern_model,
                pattern_scaler,
                pattern_persona_map,
                lang,
                year
            )

            dashboard_data = parentize_dashboard_data(
                dashboard_data,
                child,
                lang
            )
            response_data = {
                "success": True,
                "child": child,
                **dashboard_data
            }

            return jsonify(make_json_safe(response_data)), 200

        except Exception as fallback_error:
            print("PARENT CHILD DASHBOARD FALLBACK ERROR:", fallback_error)
            return jsonify({
                "success": False,
                "message": "Failed to load child dashboard."
            }), 500

    except Exception as e:
        print("PARENT CHILD DASHBOARD ERROR:", e)
        return jsonify({
            "success": False,
            "message": "Failed to load child dashboard."
        }), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# =====================================================================
# AI SOLVER ENDPOINT (Mode: "solve_question")
# =====================================================================
@app.route('/api/ai/solve', methods=['POST'])
def api_solve_question():
    data = request.json
    image_b64 = data.get('image')
    language = data.get("language","english")
    
    if not image_b64:
        return jsonify({"success": False, "message": "No image provided"}), 400

    try:
        # The frontend FileReader usually appends "data:image/jpeg;base64," to the string.
        # We need to strip that out before sending it to OpenAI/Gemini.
        if ',' in image_b64:
            image_b64 = image_b64.split(',')[1]
        confirmed_coordinates = data.get("confirmed_coordinates")
        coordinate_input = data.get("coordinate_input")
        interpreted = data.get("interpreted")

        solution = solve_new_question(
            image_b64,
            interpreted=interpreted,
            confirmed_coordinates=confirmed_coordinates,
            coordinate_input=coordinate_input,
            language=language
        )
        
        return jsonify({"success": True, "result": solution}), 200

    except Exception as e:
        print(f"AI SOLVER ERROR: {e}")
        return jsonify({"success": False, "message": "Failed to generate solution."}), 500


# =====================================================================
# AI GRADER ENDPOINT (Mode: "check_my_work")
# =====================================================================
@app.route('/api/ai/grade-new', methods=['POST'])
def api_grade_new_question():
    data = request.json
    question_image_b64 = data.get('question_image')
    student_image_b64 = data.get('student_image')
    language = data.get("language","english")
    confirmed_coordinates = data.get("confirmed_coordinates")
    coordinate_input = data.get("coordinate_input")
    interpreted = data.get("interpreted")
    if not question_image_b64 or not student_image_b64:
        return jsonify({
            "success": False,
            "message": "Both question and student working images are required."
        }), 400

    try:
        # Clean the base64 strings
        if ',' in question_image_b64:
            question_image_b64 = question_image_b64.split(',')[1]

        if ',' in student_image_b64:
            student_image_b64 = student_image_b64.split(',')[1]

        # Run the LLM grading function
        grading_report = grade_new_question(
            question_image_b64,
            student_image_b64,
            language=language,
            confirmed_coordinates=confirmed_coordinates,
            coordinate_input=coordinate_input,
            interpreted=interpreted
        )

        return jsonify({
            "success": True,
            "result": grading_report
        }), 200

    except Exception as e:
        print(f"AI GRADING ERROR: {e}")
        return jsonify({
            "success": False,
            "message": "Failed to grade working."
        }), 500

@app.route("/api/ai/grade-known-stage", methods=["POST"])
def grade_known_stage_route():
    data = request.get_json()

    student_image = data.get("student_image", "")
    exercise_stage_id = data.get("exercise_stage_id", "")
    language = data.get("language","english") 
    question_ids = data.get("question_ids") or []
    if not student_image or not exercise_stage_id:
        return jsonify({
            "success": False,
            "message": "Missing student_image or exercise_stage_id."
        }), 400

    if "," in student_image:
        student_image = student_image.split(",", 1)[1]

    result = grade_known_stage(
        student_image_base64=student_image,
        exercise_stage_id=exercise_stage_id,
        language=language,
        question_ids=question_ids
    )

    return jsonify({
        "success": True,
        "result": result
    })

@app.route('/api/ai/explain-known', methods=['POST', 'OPTIONS'])
def api_explain_known():
    if request.method == "OPTIONS":
        return jsonify({"success": True}), 200

    try:
        data = request.get_json() or {}

        image_base64 = data.get("question_image", "")
        exercise_stage_id = data.get("exercise_stage_id", "")
        language = data.get("language","english")
        question_ids = data.get("question_ids") or []
        if not exercise_stage_id:
            return jsonify({
                "success": False,
                "message": "Missing exercise_stage_id."
            }), 400

        if image_base64 and image_base64.startswith("data:image"):
            image_base64 = image_base64.split(",", 1)[1]

        solution_json = explain_known_question(
            image_base64=image_base64,
            exercise_stage_id=exercise_stage_id,
            language=language,
            question_ids=question_ids
        )

        if isinstance(solution_json, dict) and solution_json.get("success") is False:
            return jsonify(solution_json), 404

        return jsonify({
            "success": True,
            "result": solution_json
        }), 200

    except Exception as e:
        print(f"Error in explain_known_question: {e}")
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500
def get_existing_review_variant(cursor, user_id, source_key, language, practice_id=None):
    params = [user_id, source_key, language]
    practice_filter = ""

    if practice_id:
        practice_filter = "AND practice_id = %s"
        params.append(practice_id)

    cursor.execute(f"""
        SELECT *
        FROM review_variants
        WHERE user_id = %s
          AND source_key = %s
          AND language = %s
          AND status = 'queued'
          {practice_filter}
        ORDER BY variant_id DESC
        LIMIT 1
    """, tuple(params))

    return cursor.fetchone()

def get_global_review_variant_template(cursor, source_key, language):
    """
    Find any already-generated variant for the same source question/stage/group,
    regardless of which user generated it.

    This is used as a reusable template to avoid calling AI again.
    """
    cursor.execute("""
        SELECT *
        FROM review_variants
        WHERE source_key = %s
          AND language = %s
          AND question_json IS NOT NULL
          AND marking_scheme_json IS NOT NULL
        ORDER BY variant_id ASC
        LIMIT 1
    """, (source_key, language))

    return cursor.fetchone()

def clone_review_variant_template_for_user(
    cursor,
    user_id,
    practice_id,
    template_row
):
    """
    Copy an existing variant from any user into the current user's review queue.
    This allows cross-user reuse while keeping status/practice_id separate.
    """

    cursor.execute("""
        INSERT INTO review_variants (
            user_id,
            practice_id,
            source_mode,
            source_key,
            source_exercise_stage_id,
            source_group_id,
            source_question_id,
            parent_variant_id,
            variant_type,
            language,
            question_json,
            marking_scheme_json,
            status
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, NULL, %s, %s, %s, %s, 'queued')
        ON DUPLICATE KEY UPDATE
        variant_id = LAST_INSERT_ID(variant_id),
        practice_id = VALUES(practice_id),
        variant_type = VALUES(variant_type),
        language = VALUES(language),
        question_json = VALUES(question_json),
        marking_scheme_json = VALUES(marking_scheme_json),
        status = 'queued'
    """, (
        user_id,
        practice_id,
        template_row.get("source_mode"),
        template_row.get("source_key"),
        template_row.get("source_exercise_stage_id"),
        template_row.get("source_group_id"),
        template_row.get("source_question_id"),
        template_row.get("variant_type"),
        template_row.get("language"),
        template_row.get("question_json"),
        template_row.get("marking_scheme_json"),
    ))

    return cursor.lastrowid


def reuse_global_template_or_none(cursor, user_id, practice_id, source_key, language):
    global_template = get_global_review_variant_template(
        cursor=cursor,
        source_key=source_key,
        language=language
    )

    if not global_template:
        return None

    return clone_review_variant_template_for_user(
        cursor=cursor,
        user_id=user_id,
        practice_id=practice_id,
        template_row=global_template
    )
def insert_review_variant(
    cursor,
    user_id,
    practice_id,
    source_mode,
    source_key,
    source_exercise_stage_id,
    source_group_id,
    source_question_id,
    variant,
    parent_variant_id=None
):
    variant = make_json_safe(variant)
    question_json = make_json_safe(variant.get("question") or {})
    marking_scheme_json = make_json_safe(variant.get("marking_scheme") or {})
    variant_type = variant.get("variant_type") or "number_variant"
    language = variant.get("language") or "english"

    cursor.execute("""
        INSERT INTO review_variants (
            user_id,
            practice_id,
            source_mode,
            source_key,
            source_exercise_stage_id,
            source_group_id,
            source_question_id,
            parent_variant_id,
            variant_type,
            language,
            question_json,
            marking_scheme_json,
            status
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'queued')
        ON DUPLICATE KEY UPDATE
            variant_id = LAST_INSERT_ID(variant_id),
            practice_id = VALUES(practice_id),
            status = 'queued'
    """, (
        user_id,
        practice_id,
        source_mode,
        source_key,
        source_exercise_stage_id,
        source_group_id,
        source_question_id,
        parent_variant_id,
        variant_type,
        language,
        json.dumps(question_json, ensure_ascii=False),
        json.dumps(marking_scheme_json, ensure_ascii=False),
    ))

    return cursor.lastrowid

def fetch_group_source_for_variant(group_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            q.id AS question_id,
            q.exercise_stage_id,
            q.group_id,
            q.stage_index,
            q.question_no,
            q.part,
            q.subpart,
            q.sub_subpart,
            q.instructions_en,
            q.instructions_ms,
            q.sequence,
            q.table_data,
            q.given_values,
            q.has_diagram,
            q.diagram_type,
            q.image_path,
            q.display_marks,
            m.raw_json AS marking_scheme_json
        FROM questions q
        LEFT JOIN question_marking_links qml
            ON q.id = qml.question_id
        LEFT JOIN marking_schemes m
            ON m.id = qml.marking_scheme_id
        WHERE q.group_id = %s
          AND COALESCE(q.group_chapter, '') != 'Mixed'
        ORDER BY
            COALESCE(q.stage_index, 1),
            q.question_no + 0,
            q.part,
            q.subpart,
            q.sub_subpart
    """, (group_id,))

    rows = cursor.fetchall()

    cursor.close()
    conn.close()

    return rows

def build_original_k2_group_variant(group_id, language):
    """
    Repackage the original K2 group question exactly as a review variant.
    """
    rows = fetch_group_source_for_variant(group_id)

    if not rows:
        return None

    variant = build_original_group_retry_variant(
        rows=rows,
        group_id=group_id,
        language=language
    )

    if not variant or variant.get("variant_type") == "error":
        return None

    variant["source_mode"] = "group"
    variant["source_key"] = f"group:{group_id}"
    variant["source_group_id"] = group_id
    variant["language"] = language

    return variant

def format_review_variant_row(row):
    row = make_json_safe(row)
    question_json = parse_json_column(row.get("question_json")) or {}
    marking_scheme_json = parse_json_column(row.get("marking_scheme_json")) or {}

    return {
        "variant_id": row.get("variant_id"),
        "variant_type": row.get("variant_type"),
        "source_mode": row.get("source_mode"),
        "source_key": row.get("source_key"),
        "source_exercise_stage_id": row.get("source_exercise_stage_id"),
        "source_group_id": row.get("source_group_id"),
        "source_question_id": row.get("source_question_id"),
        "parent_variant_id": row.get("parent_variant_id"),
        "language": row.get("language"),
        "question": question_json,
        "marking_scheme": marking_scheme_json,
        "status": row.get("status"),
    }

@app.route("/api/review/generate-next-variant", methods=["POST"])
@require_auth("student")
def generate_next_review_variant_route():
    conn = None
    cursor = None

    try:
        data = request.get_json() or {}
        user_id = g.current_user["id"]
        practice_id = data.get("practice_id")
        parent_variant_id = data.get("parent_variant_id")
        grading_result = data.get("grading_result") or {}
        language = normalize_chat_language(data.get("language", "english"))

        if not parent_variant_id:
            return jsonify({
                "success": False,
                "message": "Missing parent_variant_id."
            }), 400

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT *
            FROM review_variants
            WHERE variant_id = %s
              AND user_id = %s
            LIMIT 1
        """, (parent_variant_id, user_id))

        parent_row = cursor.fetchone()

        if not parent_row:
            return jsonify({
                "success": False,
                "message": "Parent review variant not found."
            }), 404

        parent_variant = format_review_variant_row(parent_row)

        new_variant = generate_review_variant(
            source_mode="variant",
            parent_variant=parent_variant,
            language=language,
            grading_result=grading_result
        )

        new_variant = make_json_safe(new_variant)
        new_variant["language"] = language
        new_variant["parent_variant_id"] = parent_variant_id

        source_key = f"variant:{parent_variant_id}"

        variant_id = insert_review_variant(
            cursor=cursor,
            user_id=user_id,
            practice_id=practice_id,
            source_mode="variant",
            source_key=source_key,
            source_exercise_stage_id=parent_variant.get("source_exercise_stage_id"),
            source_group_id=parent_variant.get("source_group_id"),
            source_question_id=parent_variant.get("source_question_id"),
            variant=new_variant,
            parent_variant_id=parent_variant_id
        )

        conn.commit()

        cursor.execute("""
            SELECT *
            FROM review_variants
            WHERE variant_id = %s
            LIMIT 1
        """, (variant_id,))

        saved = cursor.fetchone()

        return jsonify({
            "success": True,
            "variant": format_review_variant_row(saved)
        }), 201

    except Exception as e:
        if conn:
            conn.rollback()

        print("GENERATE NEXT REVIEW VARIANT ERROR:", e)
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
            
@app.route("/api/review/ensure-variant", methods=["POST"])
@require_auth("student")
def ensure_review_variant_route():
    conn = None
    cursor = None

    try:
        data = request.get_json() or {}

        user_id = g.current_user["id"]
        practice_id = data.get("practice_id")
        source_mode = str(data.get("source_mode") or "stage").strip().lower()
        group_id = data.get("group_id")
        exercise_stage_id = data.get("exercise_stage_id")
        source_question_id = data.get("question_id")
        grading_result = make_json_safe(data.get("grading_result") or {})
        language = normalize_chat_language(data.get("language", "english"))
        
        if source_mode == "group":
            if not group_id:
                return jsonify({"success": False, "message": "Missing group_id."}), 400
            source_key = f"group:{group_id}"
        elif source_mode == "question":
            if not source_question_id:
                return jsonify({"success": False, "message": "Missing question_id."}), 400
            source_key = f"question:{source_question_id}"
        else:
            if not exercise_stage_id:
                return jsonify({
                    "success": False,
                    "message": "Missing exercise_stage_id."
                }), 400
            source_key = f"stage:{exercise_stage_id}"

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        existing = get_existing_review_variant(
            cursor=cursor,
            user_id=user_id,
            source_key=source_key,
            language=language,
            practice_id=practice_id
        )

        if existing:
            return jsonify({
                "success": True,
                "reused": True,
                "variant": format_review_variant_row(existing)
            }), 200
        reused_variant_id = reuse_global_template_or_none(
            cursor=cursor,
            user_id=user_id,
            practice_id=practice_id,
            source_key=source_key,
            language=language
        )

        if reused_variant_id:
            cursor.execute("""
                SELECT *
                FROM review_variants
                WHERE variant_id = %s
                LIMIT 1
            """, (reused_variant_id,))

            reused = cursor.fetchone()
            conn.commit()

            return jsonify({
                "success": True,
                "reused": True,
                "variant": format_review_variant_row(reused)
            }), 200
        variant = generate_review_variant(
            source_mode=source_mode,
            exercise_stage_id=exercise_stage_id if source_mode == "stage" else None,
            group_id=group_id if source_mode == "group" else None,
            question_id=source_question_id if source_mode == "question" else None,
            language=language,
            grading_result=grading_result
        )

        variant = make_json_safe(variant or {})

        if not variant or variant.get("variant_type") == "error":
            return jsonify({
                "success": False,
                "message": variant.get("message", "Failed to generate review variant.")
            }), 500

        variant["language"] = language

        # Insert only AFTER variant has been generated
        variant_id = insert_review_variant(
            cursor=cursor,
            user_id=user_id,
            practice_id=practice_id,
            source_mode=source_mode,
            source_key=source_key,
            source_exercise_stage_id=exercise_stage_id if source_mode == "stage" else None,
            source_group_id=group_id if source_mode == "group" else None,
            source_question_id=source_question_id,
            variant=variant,
            parent_variant_id=None
        )
        conn.commit()

        cursor.execute("""
            SELECT *
            FROM review_variants
            WHERE variant_id = %s
            LIMIT 1
        """, (variant_id,))

        saved = cursor.fetchone()

        return jsonify({
            "success": True,
            "reused": False,
            "variant": format_review_variant_row(saved)
        }), 201

    except Exception as e:
        if conn:
            conn.rollback()

        print("ENSURE REVIEW VARIANT ERROR:", e)
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route("/api/review/grade-variant", methods=["POST"])
@require_auth("student")
def grade_review_variant_route():
    conn = None
    cursor = None

    try:
        data = request.get_json() or {}

        user_id = g.current_user["id"]
        variant_id = data.get("variant_id")
        student_image = data.get("student_image", "")
        language = normalize_chat_language(data.get("language", "english"))

        if not variant_id or not student_image:
            return jsonify({
                "success": False,
                "message": "Missing variant_id or student_image."
            }), 400

        if "," in student_image:
            student_image = student_image.split(",", 1)[1]

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT *
            FROM review_variants
            WHERE variant_id = %s
              AND user_id = %s
            LIMIT 1
        """, (variant_id, user_id))

        row = cursor.fetchone()

        if not row:
            return jsonify({
                "success": False,
                "message": "Review variant not found."
            }), 404

        variant = format_review_variant_row(row)

        result = grade_review_variant(
            student_image_base64=student_image,
            variant=variant,
            language=language
        )

        cursor.execute("""
            UPDATE review_variants
            SET status = 'completed'
            WHERE variant_id = %s
              AND user_id = %s
        """, (variant_id, user_id))

        conn.commit()

        return jsonify({
            "success": True,
            "result": result
        }), 200

    except Exception as e:
        if conn:
            conn.rollback()

        print("GRADE REVIEW VARIANT ERROR:", e)
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route("/api/questions/kertas1/explain", methods=["POST"])
@require_auth("student")
def explain_k1_question():
    data = request.json or {}

    question_text = str(data.get("question_text") or "").strip()
    options = data.get("options") or []
    correct_option = str(data.get("correct_option") or "").strip().upper()
    selected_option = str(data.get("selected_option") or "").strip().upper()
    language = str(data.get("language") or "english").strip().lower()
    question_image = str(data.get("question_image") or "").strip()
    table_data = data.get("table_data") or {}
    chapter = str(data.get("chapter") or "").strip()
    difficulty = str(data.get("difficulty") or "").strip()
    difficulty_level = str(data.get("difficulty_level") or "").strip()

    if not question_text or correct_option not in ["A", "B", "C", "D"]:
        return jsonify({
            "success": False,
            "message": "Missing question text or valid correct option."
        }), 400

    safe_options = []

    for option in options:
        if not isinstance(option, dict):
            continue

        label = str(option.get("label") or "").strip().upper()

        if label not in ["A", "B", "C", "D"]:
            continue

        safe_options.append({
            "label": label,
            "text_en": str(option.get("text_en") or ""),
            "text_bm": str(option.get("text_bm") or option.get("text_ms") or option.get("text_en") or ""),
            "image_path": str(option.get("image_path") or ""),
        })

    system_prompt = r"""
You are an expert Malaysian SPM Mathematics tutor.

TASK:
Generate a clear explanation for a Kertas 1 multiple-choice SPM Mathematics question.

GROUND TRUTH:
The official correct option is provided by the system.
You must end with that official option.
However, your reasoning must still be mathematically valid and must not invent false claims.

UNIVERSAL EXPLANATION WORKFLOW:
1. Identify the question type from the question, options, table, and diagram if available.
2. Determine the key mathematical rule, formula, or visual feature needed.
3. Check the option values A, B, C, and D before making any comparison.
4. Explain the shortest valid method to reach the official answer.
5. Reject wrong options only using true mathematical reasons.
6. If the student selected a wrong option, explain the likely misconception briefly.
7. If all options share a property, do NOT say that property identifies the answer.
8. Never say "only option ___" unless it is actually unique among A, B, C, and D.
9. Do not guess diagram details if the diagram is unclear. Use cautious wording such as "from the given diagram".
10. Use SPM-level language. Be clear, but not too long.

QUESTION-TYPE GUIDANCE:
- Algebra: show substitution, simplification, factorisation, equation solving, or inequality logic.
- Graphs: use shape, gradient, intercept, vertex, width, scale, shaded region, or transformation features.
- Geometry: use angle rules, similarity/congruence, Pythagoras, trigonometry, area, perimeter, or circle theorems.
- Statistics: use frequency, mean, median, mode, quartile, cumulative frequency, probability, or data interpretation.
- Financial mathematics: show formula, substitution, rate, tax, interest, insurance, or instalment calculation.
- Sets/Venn diagrams: explain union, intersection, complement, and shaded regions carefully.
- Tables: read the correct row/column and show how the value is obtained.
- Units/rounding: include units where needed and round only when appropriate.

OUTPUT REQUIREMENTS:
Return ONLY valid JSON:
{
  "explanation_en": "English explanation here.",
  "explanation_bm": "Malay explanation here."
}

Use LaTeX for maths and wrap maths in $...$.
The final sentence must clearly state the official correct option.
"""
    correct_option_text_en = ""
    correct_option_text_bm = ""

    for option in safe_options:
        if option["label"] == correct_option:
            correct_option_text_en = option.get("text_en", "")
            correct_option_text_bm = option.get("text_bm", "")
            break

    question_text_en = str(data.get("question_text_en") or question_text).strip()
    question_text_bm = str(data.get("question_text_bm") or "").strip()

    user_prompt = f"""
    QUESTION TEXT EN:
    {question_text_en}

    QUESTION TEXT BM:
    {question_text_bm}

    CHAPTER / TOPIC:
    {chapter}

    DIFFICULTY:
    {difficulty} / {difficulty_level}

    OPTIONS:
    {json.dumps(safe_options, ensure_ascii=False, indent=2)}

    TABLE DATA:
    {json.dumps(table_data, ensure_ascii=False, indent=2)}

    STUDENT SELECTED OPTION:
    {selected_option}

    OFFICIAL CORRECT OPTION:
    {correct_option}

    OFFICIAL CORRECT OPTION TEXT EN:
    {correct_option_text_en}

    OFFICIAL CORRECT OPTION TEXT BM:
    {correct_option_text_bm}

    USER LANGUAGE:
    {language}

    Generate a mathematically valid explanation.

    Before writing the final explanation:
    - Compare all four options.
    - Do not make uniqueness claims unless true.
    - If a diagram/table is involved, base the explanation on the visible/table evidence.
    - The final answer must remain the official correct option: {correct_option}.
    """

    user_content = [{"type": "text", "text": user_prompt}]

    if question_image:
        user_content.append({
            "type": "image_url",
            "image_url": {
                "url": question_image
            }
        })

    response = openai_client.chat.completions.create(
        model="gemini-3.5-flash-lite",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
        temperature=0.1,
        response_format={"type": "json_object"},
    )

    result = json.loads(response.choices[0].message.content)

    explanation_en = str(result.get("explanation_en") or "").strip()
    explanation_bm = str(result.get("explanation_bm") or "").strip()

    if not explanation_en:
        explanation_en = f"The correct answer is {correct_option}."

    if not explanation_bm:
        explanation_bm = f"Jawapan yang betul ialah {correct_option}."

    return jsonify({
        "success": True,
        "explanation_en": explanation_en,
        "explanation_bm": explanation_bm,
    }), 200


def get_active_review_variant(cursor, user_id, practice_id, language):
    cursor.execute("""
        SELECT *
        FROM review_variants
        WHERE user_id = %s
          AND practice_id = %s
          AND language = %s
          AND status = 'active'
        ORDER BY variant_id ASC
        LIMIT 1
    """, (user_id, practice_id, language))

    return cursor.fetchone()


def get_next_queued_review_variant(cursor, user_id, practice_id, language):
    cursor.execute("""
        SELECT *
        FROM review_variants
        WHERE user_id = %s
          AND practice_id = %s
          AND language = %s
          AND status = 'queued'
        ORDER BY variant_id ASC
        LIMIT 1
    """, (user_id, practice_id, language))

    return cursor.fetchone()

def mark_review_variant_active(cursor, user_id, variant_id):
    cursor.execute("""
        UPDATE review_variants
        SET status = 'active'
        WHERE variant_id = %s
          AND user_id = %s
          AND status = 'queued'
    """, (variant_id, user_id))

@app.route("/api/practice/next-item", methods=["GET"])
@require_auth("student")
def get_next_practice_item():
    conn = None
    cursor = None

    try:
        user_id = g.current_user["id"]

        practice_id = request.args.get("practice_id")
        form = request.args.get("form")
        chapter = request.args.get("chapter")
        paper_type = str(request.args.get("paper_type") or "").strip().lower()
        language = normalize_chat_language(
            request.args.get("language", g.current_user.get("language", "english"))
        )
        retry_mode = str(request.args.get("retry_mode", "0")).lower() in ["1", "true", "yes"]

        if not practice_id or not form or not chapter or paper_type not in ["kertas1", "kertas2"]:
            return jsonify({
                "success": False,
                "message": "Missing practice_id, form, chapter, or valid paper_type."
            }), 400

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True, buffered=True)

        # 1. If a review variant is already active, resume it first.
        active_variant = get_active_review_variant(
            cursor=cursor,
            user_id=user_id,
            practice_id=practice_id,
            language=language
        )

        if active_variant:
            return jsonify({
                "success": True,
                "item_type": "review_variant",
                "paper_type": paper_type,
                "variant": format_review_variant_row(active_variant),
                "adaptive": {
                    "status": "review_active"
                }
            }), 200

        # 2. Try normal adaptive question first.
        # Important: allow_easier_after_hard_completed=True means:
        # finish ALL normal questions before showing review queue.
        adaptive_result = choose_next_practice_unit(
            conn=conn,
            user_id=user_id,
            form=form,
            chapter=chapter,
            paper_type=paper_type,
            allow_easier_after_hard_completed=True,
            retry_mode=retry_mode,
            practice_id=practice_id
        )

        if adaptive_result and adaptive_result.get("status") == "selected":
            unit = adaptive_result.get("unit", {})
            rows = unit.get("rows", [])

            if paper_type == "kertas1":
                row = rows[0]
                correct_option = get_correct_option_for_question(cursor, row["id"])
                questions = [format_k1_question_for_frontend(row, correct_option)]

            else:
                rows = expand_k2_rows_to_full_group(cursor, rows, form, chapter)

                selected_level = (
                    unit.get("difficulty_level")
                    or adaptive_result.get("selected_difficulty_level")
                    or 3
                )

                try:
                    selected_level = int(selected_level)
                except Exception:
                    selected_level = 3

                selected_level = max(1, min(5, selected_level))

                if selected_level <= 2:
                    selected_label = "Easy"
                elif selected_level == 3:
                    selected_label = "Moderate"
                else:
                    selected_label = "Hard"

                for row in rows:
                    row["adaptive_difficulty_level"] = selected_level
                    row["adaptive_difficulty"] = selected_label

                questions = format_k2_rows_for_frontend(rows)

            return jsonify({
                "success": True,
                "item_type": "normal_question",
                "paper_type": paper_type,
                "questions": questions,
                "adaptive": adaptive_result
            }), 200

        # 3. Normal adaptive is fully finished.
        # Now return the oldest queued review variant.
        queued_variant = get_next_queued_review_variant(
            cursor=cursor,
            user_id=user_id,
            practice_id=practice_id,
            language=language
        )

        if queued_variant:
            mark_review_variant_active(
                cursor=cursor,
                user_id=user_id,
                variant_id=queued_variant["variant_id"]
            )
            conn.commit()

            cursor.execute("""
                SELECT *
                FROM review_variants
                WHERE variant_id = %s
                LIMIT 1
            """, (queued_variant["variant_id"],))

            active_saved = cursor.fetchone()

            return jsonify({
                "success": True,
                "item_type": "review_variant",
                "paper_type": paper_type,
                "variant": format_review_variant_row(active_saved),
                "adaptive": {
                    "status": "review_started"
                }
            }), 200

        # 4. No normal question and no queued review variant.
        return jsonify({
            "success": True,
            "item_type": "session_complete",
            "paper_type": paper_type,
            "questions": [],
            "variant": None,
            "adaptive": {
                "status": "all_completed"
            }
        }), 200

    except Exception as e:
        print("NEXT PRACTICE ITEM ERROR:", e)
        if conn:
            conn.rollback()

        return jsonify({
            "success": False,
            "message": str(e)
        }), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


# ==================================================
# ADMIN MODULE APIs
# ==================================================

def admin_safe_count(cursor, table_name, where_sql="1=1", params=None):
    params = params or []

    try:
        cursor.execute(f"SELECT COUNT(*) AS total FROM {table_name} WHERE {where_sql}", params)
        row = cursor.fetchone() or {}
        return int(row.get("total") or 0)
    except Exception as e:
        print(f"ADMIN COUNT ERROR [{table_name}]:", e)
        return 0


@app.route("/api/admin/overview", methods=["GET"])
@require_auth("admin")
def admin_overview():
    conn = None
    cursor = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        total_students = admin_safe_count(cursor, "users", "role = %s AND is_active = 1", ["student"])
        total_parents = admin_safe_count(cursor, "users", "role = %s AND is_active = 1", ["parent"])
        total_admins = admin_safe_count(cursor, "users", "role = %s AND is_active = 1", ["admin"])
        total_questions = admin_safe_count(cursor, "questions", "COALESCE(is_active, 1) = 1")
        total_attempts = admin_safe_count(cursor, "attempts")
        total_chat_messages = admin_safe_count(cursor, "chat_messages")

        question_breakdown = {
            "kertas1": 0,
            "kertas2": 0,
        }

        try:
            cursor.execute("""
                SELECT
                    SUM(CASE WHEN question_type = 'mcq' THEN 1 ELSE 0 END) AS kertas1,
                    SUM(CASE WHEN question_type IS NULL OR question_type != 'mcq' THEN 1 ELSE 0 END) AS kertas2
                FROM questions
                WHERE COALESCE(is_active, 1) = 1
            """)
            row = cursor.fetchone() or {}
            question_breakdown["kertas1"] = int(row.get("kertas1") or 0)
            question_breakdown["kertas2"] = int(row.get("kertas2") or 0)
        except Exception as e:
            print("ADMIN QUESTION BREAKDOWN ERROR:", e)

        attempt_breakdown = {
            "kertas1": 0,
            "kertas2": 0,
        }

        try:
            cursor.execute("""
                SELECT
                    SUM(CASE WHEN paper_type = 'kertas1' THEN 1 ELSE 0 END) AS kertas1,
                    SUM(CASE WHEN paper_type = 'kertas2' THEN 1 ELSE 0 END) AS kertas2
                FROM attempts
            """)
            row = cursor.fetchone() or {}
            attempt_breakdown["kertas1"] = int(row.get("kertas1") or 0)
            attempt_breakdown["kertas2"] = int(row.get("kertas2") or 0)
        except Exception as e:
            print("ADMIN ATTEMPT BREAKDOWN ERROR:", e)

        weak_topics = []

        try:
            cursor.execute("""
                SELECT
                    CONCAT(c.form, ' Chapter ', c.chapter_no, ': ', c.name_en) AS topic_name,
                    COUNT(*) AS attempts_count,
                    SUM(CASE WHEN a.paper_type = 'kertas1' THEN 1 ELSE 0 END) AS k1_attempts,
                    SUM(CASE WHEN a.paper_type = 'kertas2' THEN 1 ELSE 0 END) AS k2_attempts,
                    ROUND(AVG(a.is_correct) * 100, 2) AS accuracy
                FROM attempts a
                JOIN chapters c
                    ON c.id = a.chapter_snapshot_id
                WHERE a.chapter_snapshot_id IS NOT NULL
                GROUP BY a.chapter_snapshot_id, c.form, c.chapter_no, c.name_en
                HAVING attempts_count >= 1
                ORDER BY accuracy ASC, attempts_count DESC
                LIMIT 6
            """)
            weak_topics = cursor.fetchall() or []
        except Exception as e:
            print("ADMIN WEAK TOPICS ERROR:", e)

        topic_usage = []

        try:
            cursor.execute("""
                SELECT
                    CONCAT(c.form, ' Chapter ', c.chapter_no, ': ', c.name_en) AS topic_name,
                    COUNT(*) AS total_attempts,
                    SUM(CASE WHEN a.paper_type = 'kertas1' THEN 1 ELSE 0 END) AS k1_attempts,
                    SUM(CASE WHEN a.paper_type = 'kertas2' THEN 1 ELSE 0 END) AS k2_attempts
                FROM attempts a
                JOIN chapters c
                    ON c.id = a.chapter_snapshot_id
                WHERE a.chapter_snapshot_id IS NOT NULL
                GROUP BY a.chapter_snapshot_id, c.form, c.chapter_no, c.name_en
                HAVING total_attempts >= 1
                ORDER BY total_attempts DESC
                LIMIT 12
            """)
            topic_usage = cursor.fetchall() or []
        except Exception as e:
            print("ADMIN TOPIC USAGE ERROR:", e)

        return jsonify({
            "success": True,
            "overview": {
                "total_students": total_students,
                "total_parents": total_parents,
                "total_admins": total_admins,
                "total_questions": total_questions,
                "total_attempts": total_attempts,
                "total_chat_messages": total_chat_messages,
                "question_breakdown": question_breakdown,
                "attempt_breakdown": attempt_breakdown,
                "weak_topics": make_json_safe(weak_topics),
                "topic_usage": make_json_safe(topic_usage),
            }
        }), 200

    except Exception as e:
        print("ADMIN OVERVIEW ERROR:", e)
        return jsonify({
            "success": False,
            "message": "Failed to load admin overview."
        }), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route("/api/admin/review-variants", methods=["GET"])
@require_auth("admin")
def admin_get_review_variants():
    conn = None
    cursor = None

    try:
        search = str(request.args.get("search") or "").strip()
        variant_type = str(request.args.get("variant_type") or "all").strip().lower()

        where_clauses = ["1=1"]
        params = []

        if variant_type != "all":
            where_clauses.append("rv.variant_type = %s")
            params.append(variant_type)

        if search:
            like = f"%{search}%"
            where_clauses.append("""
                (
                    rv.source_key LIKE %s
                    OR rv.variant_type LIKE %s
                    OR rv.source_mode LIKE %s
                    OR rv.language LIKE %s
                    OR CAST(rv.question_json AS CHAR) LIKE %s
                )
            """)
            params.extend([like, like, like, like, like])

        where_sql = " AND ".join(where_clauses)

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute(f"""
            SELECT
                rv.variant_id,
                rv.user_id,
                u.name AS student_name,
                rv.practice_id,
                rv.source_mode,
                rv.source_key,
                rv.source_question_id,
                rv.variant_type,
                rv.language,
                rv.question_json,
                rv.marking_scheme_json,
                rv.attempt_count,
                rv.correct_count,
                rv.last_score,
                rv.last_max_score,
                rv.status,
                rv.created_at,
                rv.updated_at
            FROM review_variants rv
            LEFT JOIN users u
                ON u.id = rv.user_id
            WHERE {where_sql}
            ORDER BY rv.created_at DESC, rv.variant_id DESC
            LIMIT 200
        """, params)

        rows = cursor.fetchall() or []

        for row in rows:
            row["question_json"] = parse_json_field(row.get("question_json"), {})
            row["marking_scheme_json"] = parse_json_field(row.get("marking_scheme_json"), {})

        return jsonify({
            "success": True,
            "variants": make_json_safe(rows)
        }), 200

    except Exception as e:
        print("ADMIN GET REVIEW VARIANTS ERROR:", e)
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@app.route("/api/admin/review-variants/<int:variant_id>", methods=["GET"])
@require_auth("admin")
def admin_get_review_variant_detail(variant_id):
    conn = None
    cursor = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT
                rv.*,
                u.name AS student_name,
                u.email AS student_email
            FROM review_variants rv
            LEFT JOIN users u
                ON u.id = rv.user_id
            WHERE rv.variant_id = %s
            LIMIT 1
        """, (variant_id,))

        row = cursor.fetchone()

        if not row:
            return jsonify({
                "success": False,
                "message": "Review variant not found."
            }), 404

        row["question_json"] = parse_json_field(row.get("question_json"), {})
        row["marking_scheme_json"] = parse_json_field(row.get("marking_scheme_json"), {})

        return jsonify({
            "success": True,
            "variant": make_json_safe(row)
        }), 200

    except Exception as e:
        print("ADMIN GET REVIEW VARIANT DETAIL ERROR:", e)
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@app.route("/api/admin/review-variants/<int:variant_id>", methods=["PATCH"])
@require_auth("admin")
def admin_update_review_variant(variant_id):
    data = request.json or {}

    question_json = data.get("question_json")
    marking_scheme_json = data.get("marking_scheme_json")

    if not isinstance(question_json, dict):
        return jsonify({
            "success": False,
            "message": "Invalid question JSON."
        }), 400

    if not isinstance(marking_scheme_json, dict):
        return jsonify({
            "success": False,
            "message": "Invalid marking scheme JSON."
        }), 400

    conn = None
    cursor = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            UPDATE review_variants
            SET
                question_json = %s,
                marking_scheme_json = %s,
                updated_at = NOW()
            WHERE variant_id = %s
        """, (
            json.dumps(question_json, ensure_ascii=False),
            json.dumps(marking_scheme_json, ensure_ascii=False),
            variant_id
        ))

        if cursor.rowcount == 0:
            return jsonify({
                "success": False,
                "message": "Review variant not found."
            }), 404

        conn.commit()

        return jsonify({
            "success": True,
            "message": "Review variant updated successfully."
        }), 200

    except Exception as e:
        if conn:
            conn.rollback()

        print("ADMIN UPDATE REVIEW VARIANT ERROR:", e)

        return jsonify({
            "success": False,
            "message": str(e)
        }), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
                        
@app.route("/api/admin/questions", methods=["GET"])
@require_auth("admin")
def admin_get_questions():
    conn = None
    cursor = None

    try:
        search = str(request.args.get("search") or "").strip()
        paper_type = str(request.args.get("paper_type") or "all").strip().lower()
        status = str(request.args.get("status") or "all").strip().lower()
        form = str(request.args.get("form") or "all").strip()
        difficulty = str(request.args.get("difficulty") or "all").strip()

        where_clauses = ["1=1"]
        params = []

        if paper_type == "kertas1":
            where_clauses.append("q.question_type = 'mcq'")
        elif paper_type == "kertas2":
            where_clauses.append("(q.question_type IS NULL OR q.question_type != 'mcq')")

        if status == "active":
            where_clauses.append("COALESCE(q.is_active, 1) = 1")
        elif status == "inactive":
            where_clauses.append("COALESCE(q.is_active, 1) = 0")

        if form != "all":
            where_clauses.append("(q.form = %s OR q.verified_form = %s)")
            params.extend([form, form])

        if difficulty != "all":
            where_clauses.append("q.difficulty = %s")
            params.append(difficulty)

        if search:
            like = f"%{search}%"
            where_clauses.append("""
                (
                    q.question_no LIKE %s
                    OR q.form LIKE %s
                    OR q.chapter LIKE %s
                    OR q.verified_form LIKE %s
                    OR q.verified_chapter LIKE %s
                    OR q.part LIKE %s
                    OR q.subpart LIKE %s
                    OR q.instructions_en LIKE %s
                    OR q.instructions_ms LIKE %s
                )
            """)
            params.extend([like, like, like, like, like, like, like, like, like])

        where_sql = " AND ".join(where_clauses)

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        query = f"""
            SELECT
                q.id,
                q.question_no,
                q.part,
                q.subpart,
                q.sub_subpart,
                q.question_type,
                CASE
                    WHEN q.question_type = 'mcq' THEN 'kertas1'
                    ELSE 'kertas2'
                END AS paper_type,
                q.form,
                q.chapter,
                q.verified_form,
                q.verified_chapter,
                q.difficulty,
                q.difficulty_level,
                q.instructions_en,
                q.instructions_ms,
                q.image_path,
                COALESCE(q.is_active, 1) AS is_active,
                q.created_at
            FROM questions q
            WHERE {where_sql}
            ORDER BY
                q.created_at DESC,
                CAST(q.question_no AS UNSIGNED) ASC,
                q.part ASC,
                q.subpart ASC
            LIMIT 200
        """

        cursor.execute(query, params)
        rows = cursor.fetchall() or []

        return jsonify({
            "success": True,
            "questions": make_json_safe(rows)
        }), 200

    except Exception as e:
        print("ADMIN GET QUESTIONS ERROR:", e)
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@app.route("/api/admin/questions/<int:question_id>/status", methods=["PATCH"])
@require_auth("admin")
def admin_update_question_status(question_id):
    conn = None
    cursor = None

    try:
        data = request.json or {}
        is_active = int(data.get("is_active", 1))

        if is_active not in [0, 1]:
            return jsonify({
                "success": False,
                "message": "Invalid question status."
            }), 400

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT id
            FROM questions
            WHERE id = %s
            LIMIT 1
        """, (question_id,))
        question = cursor.fetchone()

        if not question:
            return jsonify({
                "success": False,
                "message": "Question not found."
            }), 404

        cursor.execute("""
            UPDATE questions
            SET is_active = %s
            WHERE id = %s
        """, (is_active, question_id))

        conn.commit()

        return jsonify({
            "success": True,
            "message": "Question status updated successfully.",
            "question_id": question_id,
            "is_active": is_active
        }), 200

    except Exception as e:
        if conn:
            conn.rollback()

        print("ADMIN UPDATE QUESTION STATUS ERROR:", e)
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@app.route("/api/admin/users", methods=["GET"])
@require_auth("admin")
def admin_get_users():
    conn = None
    cursor = None

    try:
        search = str(request.args.get("search") or "").strip()
        role = str(request.args.get("role") or "all").strip().lower()
        status = str(request.args.get("status") or "all").strip().lower()

        where_clauses = ["1=1"]
        params = []

        if role in ["student", "parent", "admin"]:
            where_clauses.append("role = %s")
            params.append(role)

        if status == "active":
            where_clauses.append("is_active = 1")
        elif status == "inactive":
            where_clauses.append("is_active = 0")

        if search:
            like = f"%{search}%"
            where_clauses.append("(name LIKE %s OR email LIKE %s OR student_code LIKE %s)")
            params.extend([like, like, like])

        where_sql = " AND ".join(where_clauses)

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        query = f"""
            SELECT
                id,
                name,
                email,
                role,
                language,
                auth_provider,
                photo_url,
                student_code,
                is_active,
                created_at,
                updated_at
            FROM users
            WHERE {where_sql}
            ORDER BY created_at DESC
            LIMIT 200
        """

        cursor.execute(query, params)
        rows = cursor.fetchall() or []

        return jsonify({
            "success": True,
            "users": make_json_safe(rows)
        }), 200

    except Exception as e:
        print("ADMIN GET USERS ERROR:", e)
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@app.route("/api/admin/users/<int:user_id>/status", methods=["PATCH"])
@require_auth("admin")
def admin_update_user_status(user_id):
    conn = None
    cursor = None

    try:
        data = request.json or {}
        is_active = int(data.get("is_active", 1))

        if is_active not in [0, 1]:
            return jsonify({
                "success": False,
                "message": "Invalid user status."
            }), 400

        if int(user_id) == int(g.current_user["id"]):
            return jsonify({
                "success": False,
                "message": "You cannot deactivate your own admin account."
            }), 400

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT id, role
            FROM users
            WHERE id = %s
            LIMIT 1
        """, (user_id,))
        target_user = cursor.fetchone()

        if not target_user:
            return jsonify({
                "success": False,
                "message": "User not found."
            }), 404

        cursor.execute("""
            UPDATE users
            SET is_active = %s
            WHERE id = %s
        """, (is_active, user_id))

        conn.commit()

        return jsonify({
            "success": True,
            "message": "User status updated successfully.",
            "user_id": user_id,
            "is_active": is_active
        }), 200

    except Exception as e:
        if conn:
            conn.rollback()

        print("ADMIN UPDATE USER STATUS ERROR:", e)
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@app.route("/api/admin/questions/<int:question_id>", methods=["GET"])
@require_auth("admin")
def admin_get_question_detail(question_id):
    conn = None
    cursor = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT *
            FROM questions
            WHERE id = %s
            LIMIT 1
        """, (question_id,))

        question = cursor.fetchone()

        if not question:
            return jsonify({
                "success": False,
                "message": "Question not found."
            }), 404

        # Parse JSON-like fields for frontend display
        for field in [
            "instructions_en",
            "instructions_ms",
            "sequence",
            "options",
            "table_data",
            "given_values",
            "image_urls",
            "raw_json",
        ]:
            if field in question:
                default_value = {} if field in ["table_data", "given_values", "raw_json"] else []
                question[field] = parse_json_field(question.get(field), default_value)

        cursor.execute("""
            SELECT m.*
            FROM question_marking_links qml
            JOIN marking_schemes m
                ON m.id = qml.marking_scheme_id
            WHERE qml.question_id = %s
            ORDER BY m.id ASC
        """, (question_id,))

        marking_schemes = cursor.fetchall() or []

        for scheme in marking_schemes:
            for field in [
                "steps",
                "keywords",
                "final_answers",
                "final_answer_by_part",
                "raw_json",
            ]:
                if field in scheme:
                    default_value = {} if field in ["final_answers", "final_answer_by_part", "raw_json"] else []
                    scheme[field] = parse_json_field(scheme.get(field), default_value)

        return jsonify({
            "success": True,
            "question": make_json_safe(question),
            "marking_schemes": make_json_safe(marking_schemes),
        }), 200

    except Exception as e:
        print("ADMIN QUESTION DETAIL ERROR:", e)
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route("/api/admin/questions/<int:question_id>", methods=["PATCH"])
@require_auth("admin")
def admin_update_question(question_id):
    data = request.json or {}
    question = data.get("question") or {}
    marking_scheme = data.get("marking_scheme")

    if not isinstance(question, dict):
        return jsonify({
            "success": False,
            "message": "Invalid question payload."
        }), 400

    conn = None
    cursor = None

    def to_json_value(value, default):
        if value is None:
            value = default
        return json.dumps(value, ensure_ascii=False)

    def to_int(value, default=0):
        try:
            return int(value)
        except Exception:
            return default

    def to_float(value, default=0):
        try:
            return float(value)
        except Exception:
            return default

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT *
            FROM questions
            WHERE id = %s
            LIMIT 1
        """, (question_id,))

        existing_question = cursor.fetchone()

        if not existing_question:
            return jsonify({
                "success": False,
                "message": "Question not found."
            }), 404

        raw_json = dict(question)
        raw_json["correct_option"] = question.get("correct_option", "")

        cursor.execute("""
            UPDATE questions
            SET
                question_no = %s,
                part = %s,
                subpart = %s,
                sub_subpart = %s,
                question_type = %s,
                form = %s,
                chapter = %s,
                verified_form = %s,
                verified_chapter = %s,
                difficulty = %s,
                difficulty_level = %s,
                group_id = %s,
                group_form = %s,
                group_chapter = %s,
                group_difficulty_level = %s,
                exercise_stage_id = %s,
                stage_index = %s,
                unlock_after_stage_id = %s,
                display_marks = %s,
                marks = %s,
                marks_source = %s,
                instructions_en = %s,
                instructions_ms = %s,
                sequence = %s,
                options = %s,
                table_data = %s,
                given_values = %s,
                raw_json = %s
            WHERE id = %s
        """, (
            str(question.get("question_no") or ""),
            str(question.get("part") or ""),
            str(question.get("subpart") or ""),
            str(question.get("sub_subpart") or ""),
            str(question.get("question_type") or existing_question.get("question_type") or ""),
            str(question.get("form") or question.get("verified_form") or ""),
            str(question.get("chapter") or question.get("verified_chapter") or ""),
            str(question.get("verified_form") or question.get("form") or ""),
            str(question.get("verified_chapter") or question.get("chapter") or ""),
            str(question.get("difficulty") or "Moderate"),
            to_int(question.get("difficulty_level"), 3),
            str(question.get("group_id") or ""),
            str(question.get("group_form") or ""),
            str(question.get("group_chapter") or ""),
            to_int(question.get("group_difficulty_level"), 3),
            str(question.get("exercise_stage_id") or ""),
            to_int(question.get("stage_index"), 1),
            str(question.get("unlock_after_stage_id") or ""),
            to_float(question.get("display_marks"), 0),
            to_int(question.get("marks") or question.get("display_marks"), 0),
            str(question.get("marks_source") or ""),
            to_json_value(question.get("instructions_en"), []),
            to_json_value(question.get("instructions_ms"), []),
            to_json_value(question.get("sequence"), []),
            to_json_value(question.get("options"), []),
            to_json_value(question.get("table_data"), {}),
            to_json_value(question.get("given_values"), {}),
            to_json_value(raw_json, {}),
            question_id
        ))

        if isinstance(marking_scheme, dict):
            correct_option = str(question.get("correct_option") or "").strip().upper()

            # For K1, keep marking scheme final answer synced with correct option.
            if correct_option in ["A", "B", "C", "D"]:
                marking_scheme["answer_type"] = marking_scheme.get("answer_type") or "mcq"
                marking_scheme["final_answer"] = correct_option
                marking_scheme["answer_value"] = correct_option
                marking_scheme["correct_option"] = correct_option
                marking_scheme["subpart_marks"] = marking_scheme.get("subpart_marks") or 1
                marking_scheme["question_total_marks"] = marking_scheme.get("question_total_marks") or 1

            cursor.execute("""
                SELECT m.id
                FROM question_marking_links qml
                JOIN marking_schemes m
                    ON m.id = qml.marking_scheme_id
                WHERE qml.question_id = %s
                ORDER BY m.id ASC
                LIMIT 1
            """, (question_id,))

            linked_scheme = cursor.fetchone()

            final_answer = marking_scheme.get("final_answer", "")

            if isinstance(final_answer, (dict, list)):
                final_answer_text = json.dumps(final_answer, ensure_ascii=False)
            else:
                final_answer_text = str(final_answer or "")

            if linked_scheme:
                cursor.execute("""
                    UPDATE marking_schemes
                    SET
                        question_no = %s,
                        part = %s,
                        subpart = %s,
                        sub_subpart = %s,
                        group_id = %s,
                        subpart_marks = %s,
                        question_total_marks = %s,
                        answer_type = %s,
                        final_answer = %s,
                        answer_value = %s,
                        answer_range = %s,
                        units = %s,
                        rounding_and_tolerance = %s,
                        method_policy = %s,
                        conditional_marking_rules = %s,
                        method = %s,
                        steps = %s,
                        drawing_validation = %s,
                        graph_validation = %s,
                        notes = %s,
                        raw_json = %s
                    WHERE id = %s
                """, (
                    str(question.get("question_no") or marking_scheme.get("question_no") or ""),
                    str(question.get("part") or marking_scheme.get("part") or ""),
                    str(question.get("subpart") or marking_scheme.get("subpart") or ""),
                    str(question.get("sub_subpart") or marking_scheme.get("sub_subpart") or ""),
                    str(question.get("group_id") or marking_scheme.get("group_id") or ""),
                    to_float(marking_scheme.get("subpart_marks") or question.get("display_marks"), 0),
                    to_float(marking_scheme.get("question_total_marks"), 0),
                    str(marking_scheme.get("answer_type") or ""),
                    final_answer_text,
                    str(marking_scheme.get("answer_value") or ""),
                    to_json_value(marking_scheme.get("answer_range"), []),
                    str(marking_scheme.get("units") or ""),
                    to_json_value(marking_scheme.get("rounding_and_tolerance"), {}),
                    to_json_value(marking_scheme.get("method_policy"), {}),
                    to_json_value(marking_scheme.get("conditional_marking_rules"), []),
                    str(marking_scheme.get("method") or ""),
                    to_json_value(marking_scheme.get("steps"), []),
                    to_json_value(marking_scheme.get("drawing_validation"), {}),
                    to_json_value(marking_scheme.get("graph_validation"), {}),
                    to_json_value(marking_scheme.get("notes"), []),
                    to_json_value(marking_scheme, {}),
                    linked_scheme["id"]
                ))

        conn.commit()

        return jsonify({
            "success": True,
            "message": "Question updated successfully.",
            "question_id": question_id
        }), 200

    except Exception as e:
        if conn:
            conn.rollback()

        print("ADMIN UPDATE QUESTION ERROR:", e)

        return jsonify({
            "success": False,
            "message": str(e)
        }), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route("/api/admin/users/<int:user_id>", methods=["GET"])
@require_auth("admin")
def admin_get_user_detail(user_id):
    conn = None
    cursor = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT
                id,
                firebase_uid,
                name,
                email,
                role,
                language,
                auth_provider,
                photo_url,
                student_code,
                is_active,
                created_at,
                updated_at
            FROM users
            WHERE id = %s
            LIMIT 1
        """, (user_id,))

        user = cursor.fetchone()

        if not user:
            return jsonify({
                "success": False,
                "message": "User not found."
            }), 404

        stats = {
            "total_attempts": 0,
            "total_sessions": 0,
            "overall_accuracy": 0,
            "last_practice_at": None,
            "kertas1_attempts": 0,
            "kertas2_attempts": 0,
            "weak_topics": [],
        }

        if user.get("role") == "student":
            cursor.execute("""
                SELECT
                    COUNT(*) AS total_attempts,
                    ROUND(AVG(is_correct) * 100, 2) AS overall_accuracy,
                    SUM(CASE WHEN paper_type = 'kertas1' THEN 1 ELSE 0 END) AS kertas1_attempts,
                    SUM(CASE WHEN paper_type = 'kertas2' THEN 1 ELSE 0 END) AS kertas2_attempts
                FROM attempts
                WHERE user_id = %s
            """, (user_id,))

            attempt_stats = cursor.fetchone() or {}

            stats["total_attempts"] = int(attempt_stats.get("total_attempts") or 0)
            stats["overall_accuracy"] = float(attempt_stats.get("overall_accuracy") or 0)
            stats["kertas1_attempts"] = int(attempt_stats.get("kertas1_attempts") or 0)
            stats["kertas2_attempts"] = int(attempt_stats.get("kertas2_attempts") or 0)

            cursor.execute("""
                SELECT
                    COUNT(*) AS total_sessions,
                    MAX(start_time) AS last_practice_at
                FROM practice_sessions
                WHERE user_id = %s
            """, (user_id,))

            session_stats = cursor.fetchone() or {}
            stats["total_sessions"] = int(session_stats.get("total_sessions") or 0)
            stats["last_practice_at"] = session_stats.get("last_practice_at")

            cursor.execute("""
                SELECT
                    COALESCE(chapter_snapshot, 'Unknown Chapter') AS topic_name,
                    COUNT(*) AS attempts_count,
                    ROUND(AVG(is_correct) * 100, 2) AS accuracy
                FROM attempts
                WHERE user_id = %s
                  AND chapter_snapshot IS NOT NULL
                  AND chapter_snapshot != ''
                GROUP BY chapter_snapshot
                HAVING attempts_count >= 2
                ORDER BY accuracy ASC, attempts_count DESC
                LIMIT 5
            """, (user_id,))

            stats["weak_topics"] = cursor.fetchall() or []

        linked_students = []

        if user.get("role") == "parent":
            try:
                cursor.execute("""
                    SELECT
                        psl.link_id,
                        psl.nickname,
                        psl.linked_at,
                        psl.is_active,
                        s.id AS student_id,
                        s.name AS student_name,
                        s.email AS student_email,
                        s.student_code
                    FROM parent_student_links psl
                    JOIN users s
                        ON s.id = psl.student_id
                    WHERE psl.parent_id = %s
                      AND psl.is_active = 1
                    ORDER BY psl.linked_at DESC
                """, (user_id,))

                linked_students = cursor.fetchall() or []
            except Exception as e:
                print("ADMIN PARENT LINKED STUDENTS ERROR:", e)
                linked_students = []
                
        return jsonify({
            "success": True,
            "user": make_json_safe(user),
            "stats": make_json_safe(stats),
            "linked_students": make_json_safe(linked_students)
        }), 200

    except Exception as e:
        print("ADMIN USER DETAIL ERROR:", e)
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# ==================================================
# ADMIN IMPORT DRAFT APIs
# ==================================================

@app.route("/api/admin/users/admin", methods=["POST"])
@require_auth("admin")
def admin_create_admin_user():
    data = request.json or {}

    name = str(data.get("name") or "").strip()
    email = str(data.get("email") or "").strip().lower()
    language = "english"

    if not name:
        return jsonify({
            "success": False,
            "message": "Admin name is required."
        }), 400

    if not email or "@" not in email:
        return jsonify({
            "success": False,
            "message": "Valid admin email is required."
        }), 400

    conn = None
    cursor = None

    def generate_temp_password(length=16):
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        return "".join(secrets.choice(alphabet) for _ in range(length))

    try:
        firebase_uid = None
        reset_link = None

        try:
            firebase_user = firebase_auth.get_user_by_email(email)
            firebase_uid = firebase_user.uid
        except Exception:
            temp_password = generate_temp_password()

            firebase_user = firebase_auth.create_user(
                email=email,
                password=temp_password,
                display_name=name,
                email_verified=False,
                disabled=False
            )

            firebase_uid = firebase_user.uid

        reset_link = firebase_auth.generate_password_reset_link(email)

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT id, role
            FROM users
            WHERE email = %s
            LIMIT 1
        """, (email,))

        existing = cursor.fetchone()

        if existing and existing.get("role") != "admin":
            return jsonify({
                "success": False,
                "message": f"This email already belongs to a {existing.get('role')} account."
            }), 400

        if existing and existing.get("role") == "admin":
            cursor.execute("""
                UPDATE users
                SET
                    firebase_uid = %s,
                    name = %s,
                    language = %s,
                    auth_provider = 'email',
                    is_active = 1
                WHERE id = %s
            """, (firebase_uid, name, language, existing["id"]))

            admin_id = existing["id"]
        else:
            cursor.execute("""
                INSERT INTO users
                (
                    firebase_uid,
                    name,
                    email,
                    role,
                    language,
                    auth_provider,
                    photo_url,
                    student_code,
                    is_active
                )
                VALUES
                (
                    %s,
                    %s,
                    %s,
                    'admin',
                    %s,
                    'email',
                    NULL,
                    NULL,
                    1
                )
            """, (firebase_uid, name, email, language))

            admin_id = cursor.lastrowid

        conn.commit()

        return jsonify({
            "success": True,
            "message": "Admin account added successfully.",
            "admin_id": admin_id,
            "firebase_uid": firebase_uid,
            "password_reset_link": reset_link
        }), 201

    except Exception as e:
        if conn:
            conn.rollback()

        print("ADMIN CREATE ADMIN USER ERROR:", e)

        return jsonify({
            "success": False,
            "message": str(e)
        }), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route("/api/admin/import-batches", methods=["POST"])
@require_auth("admin")
def admin_create_import_batch():
    conn = None
    cursor = None

    try:
        data = request.json or {}

        paper_type = str(data.get("paper_type") or "").strip().lower()
        source_type = str(data.get("source_type") or "pdf").strip().lower()
        title = str(data.get("title") or "").strip()
        original_file_name = str(data.get("original_file_name") or "").strip()
        items = data.get("items") or []

        if paper_type not in ["kertas1", "kertas2"]:
            return jsonify({
                "success": False,
                "message": "Invalid paper type."
            }), 400

        if source_type not in ["pdf", "manual"]:
            source_type = "pdf"

        if not title:
            title = f"{paper_type.upper()} Import Draft"

        if not isinstance(items, list):
            items = []

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            INSERT INTO admin_import_batches
            (
                paper_type,
                source_type,
                title,
                original_file_name,
                status,
                total_items,
                created_by
            )
            VALUES (%s, %s, %s, %s, 'draft', %s, %s)
        """, (
            paper_type,
            source_type,
            title,
            original_file_name,
            len(items),
            g.current_user["id"]
        ))

        batch_id = cursor.lastrowid

        for item in items:
            if not isinstance(item, dict):
                continue

            parsed_json = make_json_safe(item)

            cursor.execute("""
                INSERT INTO admin_import_items
                (
                    batch_id,
                    question_no,
                    part,
                    subpart,
                    status,
                    parsed_json,
                    admin_edited_json,
                    image_url,
                    image_public_id
                )
                VALUES (%s, %s, %s, %s, 'draft', %s, %s, %s, %s)
            """, (
                batch_id,
                str(item.get("question_no") or ""),
                str(item.get("part") or ""),
                str(item.get("subpart") or ""),
                json.dumps(parsed_json, ensure_ascii=False),
                json.dumps(parsed_json, ensure_ascii=False),
                item.get("diagram_path") or item.get("image_path") or "",
                item.get("_diagram_public_id") or item.get("image_public_id") or ""
            ))

        conn.commit()

        return jsonify({
            "success": True,
            "message": "Import batch created.",
            "batch_id": batch_id
        }), 201

    except Exception as e:
        if conn:
            conn.rollback()

        print("ADMIN CREATE IMPORT BATCH ERROR:", e)
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@app.route("/api/admin/import-batches", methods=["GET"])
@require_auth("admin")
def admin_get_import_batches():
    conn = None
    cursor = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT
                b.*,
                u.name AS created_by_name
            FROM admin_import_batches b
            LEFT JOIN users u
                ON u.id = b.created_by
            WHERE b.status IN ('draft', 'reviewing')
            ORDER BY b.created_at DESC
            LIMIT 100
        """)
        batches = cursor.fetchall() or []

        return jsonify({
            "success": True,
            "batches": make_json_safe(batches)
        }), 200

    except Exception as e:
        print("ADMIN GET IMPORT BATCHES ERROR:", e)
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@app.route("/api/admin/import-batches/<int:batch_id>", methods=["GET"])
@require_auth("admin")
def admin_get_import_batch_detail(batch_id):
    conn = None
    cursor = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT *
            FROM admin_import_batches
            WHERE batch_id = %s
            LIMIT 1
        """, (batch_id,))

        batch = cursor.fetchone()

        if not batch:
            return jsonify({
                "success": False,
                "message": "Import batch not found."
            }), 404

        cursor.execute("""
            SELECT *
            FROM admin_import_items
            WHERE batch_id = %s
            ORDER BY
                CAST(question_no AS UNSIGNED),
                part,
                subpart,
                item_id
        """, (batch_id,))

        items = cursor.fetchall() or []

        for item in items:
            item["parsed_json"] = parse_json_field(item.get("parsed_json"), {})
            item["admin_edited_json"] = parse_json_field(item.get("admin_edited_json"), {})

        return jsonify({
            "success": True,
            "batch": make_json_safe(batch),
            "items": make_json_safe(items)
        }), 200

    except Exception as e:
        print("ADMIN GET IMPORT BATCH DETAIL ERROR:", e)
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@app.route("/api/admin/import-items/<int:item_id>", methods=["PATCH"])
@require_auth("admin")
def admin_update_import_item(item_id):
    conn = None
    cursor = None

    try:
        data = request.json or {}

        status = str(data.get("status") or "draft").strip().lower()
        admin_edited_json = data.get("admin_edited_json")
        admin_notes = str(data.get("admin_notes") or "").strip()

        if status not in ["draft", "approved", "skipped", "saved"]:
            return jsonify({
                "success": False,
                "message": "Invalid item status."
            }), 400

        if not isinstance(admin_edited_json, dict):
            return jsonify({
                "success": False,
                "message": "admin_edited_json must be an object."
            }), 400

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT item_id
            FROM admin_import_items
            WHERE item_id = %s
            LIMIT 1
        """, (item_id,))

        item = cursor.fetchone()

        if not item:
            return jsonify({
                "success": False,
                "message": "Import item not found."
            }), 404

        cursor.execute("""
            UPDATE admin_import_items
            SET
                question_no = %s,
                part = %s,
                subpart = %s,
                status = %s,
                admin_edited_json = %s,
                admin_notes = %s
            WHERE item_id = %s
        """, (
            str(admin_edited_json.get("question_no") or ""),
            str(admin_edited_json.get("part") or ""),
            str(admin_edited_json.get("subpart") or ""),
            status,
            json.dumps(make_json_safe(admin_edited_json), ensure_ascii=False),
            admin_notes,
            item_id
        ))

        conn.commit()

        return jsonify({
            "success": True,
            "message": "Import item updated."
        }), 200

    except Exception as e:
        if conn:
            conn.rollback()

        print("ADMIN UPDATE IMPORT ITEM ERROR:", e)
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route("/api/admin/import-items/<int:item_id>/image", methods=["DELETE"])
@require_auth("admin")
def admin_delete_import_item_image(item_id):
    conn = None
    cursor = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT item_id, image_public_id, admin_edited_json
            FROM admin_import_items
            WHERE item_id = %s
            LIMIT 1
        """, (item_id,))

        item = cursor.fetchone()

        if not item:
            return jsonify({
                "success": False,
                "message": "Import item not found."
            }), 404

        image_public_id = item.get("image_public_id")

        # Delete from Cloudinary only if this image was uploaded there.
        # Parser local image paths may not have Cloudinary public_id.
        if image_public_id:
            try:
                cloudinary.uploader.destroy(
                    image_public_id,
                    resource_type="image"
                )
            except Exception as cloudinary_error:
                print("CLOUDINARY DELETE WARNING:", cloudinary_error)

        edited_json = parse_json_field(item.get("admin_edited_json"), {})

        edited_json["diagram_path"] = ""
        edited_json["image_path"] = ""
        edited_json["_diagram_image_path"] = ""
        edited_json["_diagram_public_id"] = ""
        edited_json["_manual_image_deleted"] = True
        edited_json["has_diagram"] = False
        edited_json["diagram_type"] = ""

        cursor.execute("""
            UPDATE admin_import_items
            SET
                image_url = '',
                image_public_id = '',
                admin_edited_json = %s
            WHERE item_id = %s
        """, (
            json.dumps(make_json_safe(edited_json), ensure_ascii=False),
            item_id
        ))

        conn.commit()

        return jsonify({
            "success": True,
            "message": "Image removed."
        }), 200

    except Exception as e:
        if conn:
            conn.rollback()

        print("ADMIN DELETE IMPORT ITEM IMAGE ERROR:", e)
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route("/api/admin/import-items/<int:item_id>/image", methods=["POST"])
@require_auth("admin")
def admin_replace_import_item_image(item_id):
    conn = None
    cursor = None

    try:
        if "image" not in request.files:
            return jsonify({
                "success": False,
                "message": "No image file uploaded."
            }), 400

        image_file = request.files["image"]

        if not image_file.filename:
            return jsonify({
                "success": False,
                "message": "Invalid image file."
            }), 400

        safe_name = secure_filename(image_file.filename)
        public_id = f"admin_import_{item_id}_{uuid.uuid4().hex}"

        uploaded = cloudinary.uploader.upload(
            image_file,
            folder="mathsy/admin_import_images",
            public_id=public_id,
            resource_type="image",
            overwrite=True
        )

        image_url = uploaded.get("secure_url") or uploaded.get("url")
        image_public_id = uploaded.get("public_id")

        if not image_url:
            return jsonify({
                "success": False,
                "message": "Cloudinary upload failed."
            }), 500

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT item_id, admin_edited_json
            FROM admin_import_items
            WHERE item_id = %s
            LIMIT 1
        """, (item_id,))

        item = cursor.fetchone()

        if not item:
            return jsonify({
                "success": False,
                "message": "Import item not found."
            }), 404

        edited_json = parse_json_field(item.get("admin_edited_json"), {})
        edited_json["diagram_path"] = image_url
        edited_json["image_path"] = image_url
        edited_json["_manual_image_replaced"] = True

        cursor.execute("""
            UPDATE admin_import_items
            SET
                image_url = %s,
                image_public_id = %s,
                admin_edited_json = %s
            WHERE item_id = %s
        """, (
            image_url,
            image_public_id,
            json.dumps(make_json_safe(edited_json), ensure_ascii=False),
            item_id
        ))

        conn.commit()

        return jsonify({
            "success": True,
            "message": "Image uploaded.",
            "image_url": image_url,
            "image_public_id": image_public_id,
            "file_name": safe_name
        }), 200

    except Exception as e:
        if conn:
            conn.rollback()

        print("ADMIN REPLACE IMPORT ITEM IMAGE ERROR:", e)
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@app.route("/api/admin/import-batches/<int:batch_id>/status", methods=["PATCH"])
@require_auth("admin")
def admin_update_import_batch_status(batch_id):
    conn = None
    cursor = None

    try:
        data = request.json or {}
        status = str(data.get("status") or "").strip().lower()

        if status not in ["draft", "reviewing", "completed", "cancelled"]:
            return jsonify({
                "success": False,
                "message": "Invalid batch status."
            }), 400

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            UPDATE admin_import_batches
            SET status = %s
            WHERE batch_id = %s
        """, (status, batch_id))

        conn.commit()

        return jsonify({
            "success": True,
            "message": "Batch status updated."
        }), 200

    except Exception as e:
        if conn:
            conn.rollback()

        print("ADMIN UPDATE IMPORT BATCH STATUS ERROR:", e)
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def save_uploaded_pdf(uploaded_file, folder_name="admin_uploads"):
    if not uploaded_file or not uploaded_file.filename:
        raise ValueError("Invalid PDF file.")

    upload_root = os.path.join(tempfile.gettempdir(), "mathsy_admin_uploads", folder_name)
    os.makedirs(upload_root, exist_ok=True)

    safe_name = secure_filename(uploaded_file.filename)
    unique_name = f"{uuid.uuid4().hex}_{safe_name}"
    file_path = os.path.join(upload_root, unique_name)

    uploaded_file.save(file_path)

    return file_path, safe_name


def run_async_parser(coro):
    try:
        return asyncio.run(coro)
    except RuntimeError:
        loop = asyncio.new_event_loop()
        try:
            asyncio.set_event_loop(loop)
            return loop.run_until_complete(coro)
        finally:
            loop.close()
            asyncio.set_event_loop(None)

@app.route("/api/admin/import/k1/parse-draft", methods=["POST"])
@require_auth("admin")
def admin_parse_k1_pdf_to_draft():
    from parser import pdf_k1_parser
    conn = None
    cursor = None

    question_pdf_path = None
    marking_pdf_path = None

    try:
        question_pdf = request.files.get("question_pdf")
        marking_pdf = request.files.get("marking_pdf")

        if not question_pdf:
            return jsonify({
                "success": False,
                "message": "Please upload the K1 question PDF."
            }), 400

        if not marking_pdf:
            return jsonify({
                "success": False,
                "message": "Please upload the K1 answer key / marking PDF."
            }), 400

        title = str(request.form.get("title") or "Kertas 1 Import Draft").strip()
        exam_name = str(request.form.get("exam_name") or "SPM Trial").strip()
        year = int(request.form.get("year") or datetime.now().year)

        question_start_page = int(request.form.get("question_start_page") or 1)
        question_end_page_raw = request.form.get("question_end_page")
        question_end_page = int(question_end_page_raw) if question_end_page_raw else None

        marking_start_page = int(request.form.get("marking_start_page") or 1)
        marking_end_page_raw = request.form.get("marking_end_page")
        marking_end_page = int(marking_end_page_raw) if marking_end_page_raw else None

        question_pdf_path, question_original_name = save_uploaded_pdf(
            question_pdf,
            folder_name="k1_questions"
        )

        marking_pdf_path, marking_original_name = save_uploaded_pdf(
            marking_pdf,
            folder_name="k1_marking"
        )

        async_client = AsyncOpenAI(
            api_key=os.getenv("GEMINI_API_KEY"),
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
        )

        # Important:
        # Reset parser semaphores to avoid "bound to different event loop" issue
        # when parser endpoint is called multiple times.
        pdf_k1_parser.K1_QUESTION_SEMAPHORE = None
        pdf_k1_parser.K1_MARKING_SEMAPHORE = None

        output_prefix = f"Admin_K1_{uuid.uuid4().hex[:8]}"

        # 1. Extract K1 answer key
        answer_key = run_async_parser(
            pdf_k1_parser.parse_k1_answer_key_pdf(
                marking_pdf_path=marking_pdf_path,
                openai_client=async_client,
                output_prefix=output_prefix,
                start_page=marking_start_page,
                end_page=marking_end_page,
                model="gemini-3.5-flash-lite",
                out_dir=pdf_k1_parser.MARKING_IMG_DIR
            )
        )

        # 2. Render K1 question pages
        page_infos = pdf_k1_parser.render_pdf_pages(
            pdf_path=question_pdf_path,
            out_dir=pdf_k1_parser.QUESTION_IMG_DIR,
            dpi=150,
            prefix=output_prefix
        )

        selected_page_infos = []

        for page_info in page_infos:
            page_no = int(page_info["page_no"])

            if not pdf_k1_parser.page_in_selected_range(
                page_no,
                start_page=question_start_page,
                end_page=question_end_page
            ):
                continue

            selected_page_infos.append(page_info)

        print(f"Queued {len(selected_page_infos)} K1 question pages.")

        async def run_k1_question_pages():
            async def parse_one_page(page_info):
                page_no = int(page_info["page_no"])

                try:
                    print(f"Queueing K1 question page {page_no}...")

                    return await asyncio.wait_for(
                        pdf_k1_parser.smart_k1_question_wrapper(
                            page_info=page_info,
                            question_pdf_path=question_pdf_path,
                            question_client=async_client,
                            question_model="gemini-3.5-flash-lite",
                            output_prefix=output_prefix,
                            crop_dir=pdf_k1_parser.QUESTION_CROP_DIR
                        ),
                        timeout=240
                    )

                except asyncio.TimeoutError:
                    print(f"⚠️ K1 question page {page_no} timed out. Skipping this page.")
                    return []

                except Exception as e:
                    print(f"⚠️ K1 question page {page_no} failed: {e}")
                    return []

            return await asyncio.gather(
                *[parse_one_page(page_info) for page_info in selected_page_infos],
                return_exceptions=True
            )

        results = run_async_parser(run_k1_question_pages())

        print("Success: Finished all K1 question page tasks. Combining results...")

        all_questions = []

        for result in results:
            if isinstance(result, Exception):
                print("⚠️ K1 result exception:", result)
                continue

            if isinstance(result, list):
                all_questions.extend(result)
            else:
                print("⚠️ Unexpected K1 result type:", type(result), result)

        print(f"Total extracted K1 questions before classification: {len(all_questions)}")

        def normalize_k1_qno(value):
            text = str(value or "").strip()
            text = text.replace("Question", "").replace("Q", "").strip()
            return text


        def score_k1_question_completeness(q):
            score = 0

            instructions_en = q.get("instructions_en") or []
            instructions_ms = q.get("instructions_ms") or []

            if isinstance(instructions_en, str):
                score += len(instructions_en)
            elif isinstance(instructions_en, list):
                score += sum(len(str(x)) for x in instructions_en)

            if isinstance(instructions_ms, str):
                score += len(instructions_ms)
            elif isinstance(instructions_ms, list):
                score += sum(len(str(x)) for x in instructions_ms)

            options = q.get("options") or []

            if isinstance(options, list):
                score += len(options) * 50

                for opt in options:
                    if isinstance(opt, dict):
                        score += len(str(opt.get("text_en") or ""))
                        score += len(str(opt.get("text_ms") or ""))

                        if opt.get("image_path"):
                            score += 30

            if q.get("diagram_path") or q.get("_diagram_image_path") or q.get("image_path"):
                score += 80

            if q.get("correct_option"):
                score += 20

            return score


        deduped_questions = {}

        for q in all_questions:
            qno = normalize_k1_qno(q.get("question_no"))

            if not qno:
                continue

            existing = deduped_questions.get(qno)

            if not existing:
                deduped_questions[qno] = q
                continue

            current_score = score_k1_question_completeness(q)
            existing_score = score_k1_question_completeness(existing)

            if current_score > existing_score:
                deduped_questions[qno] = q

        all_questions = list(deduped_questions.values())

        all_questions.sort(
            key=lambda item: int(normalize_k1_qno(item.get("question_no")))
            if normalize_k1_qno(item.get("question_no")).isdigit()
            else 9999
        )

        print(f"Total extracted K1 questions after deduplication: {len(all_questions)}")

        # 3. Apply classifier and prepare draft items
        all_questions = pdf_k1_parser.apply_verified_chapters(all_questions)

        draft_items = []

        for q in all_questions:
            q["form"] = q.get("verified_form") or q.get("form", "")
            q["chapter"] = q.get("verified_chapter") or q.get("chapter", "")

            level, label = pdf_k1_parser.calculate_k1_difficulty(q)
            q["difficulty_level"] = level
            q["difficulty"] = label

            q = pdf_k1_parser.prepare_k1_question_for_insert(q)

            question_no = str(q.get("question_no") or "").strip()
            correct_option = answer_key.get(question_no, "")

            q["correct_option"] = correct_option
            q["answer_key_found"] = bool(correct_option)

            if correct_option:
                q["marking_scheme"] = pdf_k1_parser.build_k1_marking_scheme(
                    question_no=question_no,
                    correct_option=correct_option
                )
            else:
                q["marking_scheme"] = None

            q["source_pdf_name"] = question_original_name
            q["source_marking_pdf_name"] = marking_original_name
            q["exam_name"] = exam_name
            q["year"] = year

            draft_items.append(make_json_safe(q))

        if not draft_items:
            return jsonify({
                "success": False,
                "message": "No K1 questions were extracted. Try setting question_start_page correctly or parse fewer pages first."
            }), 400

        print(f"Creating admin import batch with {len(draft_items)} draft items...")

        # 4. Save into admin import draft tables
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            INSERT INTO admin_import_batches
            (
                paper_type,
                source_type,
                title,
                original_file_name,
                status,
                total_items,
                created_by
            )
            VALUES (%s, %s, %s, %s, 'draft', %s, %s)
        """, (
            "kertas1",
            "pdf",
            title,
            question_original_name,
            len(draft_items),
            g.current_user["id"]
        ))

        batch_id = cursor.lastrowid

        for item in draft_items:
            cursor.execute("""
                INSERT INTO admin_import_items
                (
                    batch_id,
                    question_no,
                    part,
                    subpart,
                    status,
                    parsed_json,
                    admin_edited_json,
                    image_url,
                    image_public_id
                )
                VALUES (%s, %s, %s, %s, 'draft', %s, %s, %s, %s)
            """, (
                batch_id,
                str(item.get("question_no") or ""),
                "",
                "",
                json.dumps(item, ensure_ascii=False),
                json.dumps(item, ensure_ascii=False),
                item.get("diagram_path") or item.get("_diagram_image_path") or "",
                item.get("_diagram_public_id") or ""
            ))

        conn.commit()

        print(f"Admin K1 import batch created: {batch_id}")

        missing_answer_questions = [
            str(item.get("question_no"))
            for item in draft_items
            if not item.get("answer_key_found")
        ]

        return jsonify({
            "success": True,
            "message": "K1 PDF parsed into draft successfully.",
            "batch_id": batch_id,
            "total_questions": len(draft_items),
            "answer_key_count": len(answer_key),
            "missing_answer_questions": missing_answer_questions,
        }), 201

    except Exception as e:
        if conn:
            conn.rollback()

        print("ADMIN PARSE K1 PDF TO DRAFT ERROR:", e)

        return jsonify({
            "success": False,
            "message": str(e)
        }), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route("/api/admin/import/k2/parse-draft", methods=["POST"])
@require_auth("admin")
def admin_parse_k2_pdf_to_draft():
    from parser import pdf_k2_parser, parser_common
    conn = None
    cursor = None

    try:
        question_pdf = request.files.get("question_pdf")
        marking_pdf = request.files.get("marking_pdf")

        if not question_pdf:
            return jsonify({
                "success": False,
                "message": "Please upload the K2 question PDF."
            }), 400

        if not marking_pdf:
            return jsonify({
                "success": False,
                "message": "Please upload the K2 marking scheme PDF."
            }), 400

        title = str(request.form.get("title") or "Kertas 2 Import Draft").strip()
        exam_name = str(request.form.get("exam_name") or "SPM Trial").strip()
        year = str(request.form.get("year") or datetime.now().year)

        question_start_page = int(request.form.get("question_start_page") or 1)
        question_end_page_raw = request.form.get("question_end_page")
        question_end_page = int(question_end_page_raw) if question_end_page_raw else None

        marking_start_page = int(request.form.get("marking_start_page") or 1)
        marking_end_page_raw = request.form.get("marking_end_page")
        marking_end_page = int(marking_end_page_raw) if marking_end_page_raw else None

        question_pdf_path, question_original_name = save_uploaded_pdf(
            question_pdf,
            folder_name="k2_questions"
        )

        marking_pdf_path, marking_original_name = save_uploaded_pdf(
            marking_pdf,
            folder_name="k2_marking"
        )

        # Reset async locks/semaphores to avoid different event loop errors.
        pdf_k2_parser.PAGE_SEMAPHORE = None
        pdf_k2_parser.MARKING_SEMAPHORE = None
        parser_common.RATE_LIMIT_LOCK = None
        parser_common.LAST_API_CALL_TIME = 0.0

        output_prefix = f"Admin_K2_{uuid.uuid4().hex[:8]}"

        async_question_client = AsyncOpenAI(
            api_key=os.getenv("GEMINI_API_KEY"),
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
        )

        async_marking_client = AsyncOpenAI(
            api_key=os.getenv("GEMINI_API_KEY"),
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
            max_retries=3
        )

        result = run_async_parser(
            pdf_k2_parser.process_question_and_marking_pdfs_full_page(
                question_pdf_path=question_pdf_path,
                marking_pdf_path=marking_pdf_path,
                question_client=async_question_client,
                marking_client=async_marking_client,
                exam_name=exam_name,
                subject="Mathematics",
                year=year,
                question_model="gemini-3.5-flash-lite",
                marking_model="gemini-3.5-flash-lite",
                question_start_page=question_start_page,
                question_end_page=question_end_page,
                marking_start_page=marking_start_page,
                marking_end_page=marking_end_page,
                output_prefix=output_prefix,
                save_to_db=False
            )
        )

        parsed_questions = result.get("questions", []) if isinstance(result, dict) else []
        parsed_markings = result.get("markings", []) if isinstance(result, dict) else []

        if not parsed_questions:
            return jsonify({
                "success": False,
                "message": "No K2 questions were extracted. Try adjusting the start/end pages."
            }), 400

        marking_by_key = {}

        for marking in parsed_markings:
            key = (
                str(marking.get("question_no") or "").strip().lower(),
                str(marking.get("part") or "").strip().lower(),
                str(marking.get("subpart") or "").strip().lower(),
                str(marking.get("sub_subpart") or "").strip().lower(),
            )
            marking_by_key[key] = marking

        draft_items = []

        for q in parsed_questions:
            key = (
                str(q.get("question_no") or "").strip().lower(),
                str(q.get("part") or "").strip().lower(),
                str(q.get("subpart") or "").strip().lower(),
                str(q.get("sub_subpart") or "").strip().lower(),
            )

            q["question_type"] = q.get("question_type") or "Structured"
            q["form"] = q.get("verified_form") or q.get("form", "")
            q["chapter"] = q.get("verified_chapter") or q.get("chapter", "")
            q["source_pdf_name"] = question_original_name
            q["source_marking_pdf_name"] = marking_original_name
            q["exam_name"] = exam_name
            q["year"] = year
            q["marking_scheme"] = marking_by_key.get(key)

            draft_items.append(make_json_safe(q))

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            INSERT INTO admin_import_batches
            (
                paper_type,
                source_type,
                title,
                original_file_name,
                status,
                total_items,
                created_by
            )
            VALUES (%s, %s, %s, %s, 'draft', %s, %s)
        """, (
            "kertas2",
            "pdf",
            title,
            question_original_name,
            len(draft_items),
            g.current_user["id"]
        ))

        batch_id = cursor.lastrowid

        for item in draft_items:
            cursor.execute("""
                INSERT INTO admin_import_items
                (
                    batch_id,
                    question_no,
                    part,
                    subpart,
                    status,
                    parsed_json,
                    admin_edited_json,
                    image_url,
                    image_public_id
                )
                VALUES (%s, %s, %s, %s, 'draft', %s, %s, %s, %s)
            """, (
                batch_id,
                str(item.get("question_no") or ""),
                str(item.get("part") or ""),
                str(item.get("subpart") or ""),
                json.dumps(item, ensure_ascii=False),
                json.dumps(item, ensure_ascii=False),
                item.get("_diagram_image_path") or item.get("diagram_path") or item.get("image_path") or "",
                item.get("_diagram_public_id") or ""
            ))

        conn.commit()

        return jsonify({
            "success": True,
            "message": "K2 PDF parsed into draft successfully.",
            "batch_id": batch_id,
            "total_questions": len(draft_items),
            "marking_count": len(parsed_markings)
        }), 201

    except Exception as e:
        if conn:
            conn.rollback()

        print("ADMIN PARSE K2 PDF TO DRAFT ERROR:", e)

        return jsonify({
            "success": False,
            "message": str(e)
        }), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route("/api/admin/import-batches/<int:batch_id>/save-approved-k1", methods=["POST"])
@require_auth("admin")
def admin_save_approved_k1_import_batch(batch_id):
    from parser.parser_common import (
        insert_paper, insert_question, insert_marking_scheme,
        insert_question_marking_link,
    )
    conn = None
    cursor = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT *
            FROM admin_import_batches
            WHERE batch_id = %s
            LIMIT 1
        """, (batch_id,))

        batch = cursor.fetchone()

        if not batch:
            return jsonify({
                "success": False,
                "message": "Import batch not found."
            }), 404

        if batch.get("paper_type") != "kertas1":
            return jsonify({
                "success": False,
                "message": "This save endpoint is only for Kertas 1 batches."
            }), 400

        cursor.execute("""
            SELECT COUNT(*) AS pending_count
            FROM admin_import_items
            WHERE batch_id = %s
            AND status NOT IN ('approved', 'skipped', 'saved')
        """, (batch_id,))

        pending_row = cursor.fetchone() or {}
        pending_count = int(pending_row.get("pending_count") or 0)

        if pending_count > 0:
            return jsonify({
                "success": False,
                "message": f"{pending_count} question(s) still need to be approved or skipped before completing this import."
            }), 400

        cursor.execute("""
            SELECT *
            FROM admin_import_items
            WHERE batch_id = %s
              AND status = 'approved'
              AND saved_question_id IS NULL
            ORDER BY CAST(question_no AS UNSIGNED), item_id
        """, (batch_id,))

        approved_items = cursor.fetchall() or []

        if not approved_items:
            cursor.execute("""
                UPDATE admin_import_batches
                SET status = 'completed'
                WHERE batch_id = %s
            """, (batch_id,))

            conn.commit()

            return jsonify({
                "success": True,
                "message": "Import review completed. No approved questions were imported.",
                "paper_id": None,
                "saved_count": 0,
                "skipped_count": 0,
                "saved_question_ids": []
            }), 200

        # Create one paper record for this import batch.
        paper_id = insert_paper(
            conn=conn,
            title=batch.get("title") or batch.get("original_file_name") or f"K1 Import Batch {batch_id}",
            paper_type="kertas1",
            file_path=batch.get("original_file_name") or "",
            exam_name="SPM Trial",
            subject="Mathematics",
            year=datetime.now().year
        )

        saved_count = 0
        skipped_count = 0
        saved_question_ids = []

        for item in approved_items:
            edited_json = parse_json_field(item.get("admin_edited_json"), {})

            if not isinstance(edited_json, dict):
                skipped_count += 1
                continue

            # K1 must have question number and correct option.
            question_no = str(edited_json.get("question_no") or item.get("question_no") or "").strip()
            correct_option = str(
                edited_json.get("correct_option")
                or edited_json.get("answer_value")
                or ""
            ).strip().upper()

            marking_scheme = edited_json.get("marking_scheme")

            if correct_option not in ["A", "B", "C", "D"]:
                skipped_count += 1
                continue

            # Make sure required K1 fields exist.
            edited_json["question_no"] = question_no
            edited_json["question_type"] = "mcq"
            edited_json["part"] = ""
            edited_json["subpart"] = ""
            edited_json["sub_subpart"] = ""
            edited_json["marks"] = 1
            edited_json["display_marks"] = 1
            edited_json["marks_source"] = edited_json.get("marks_source") or "mcq_answer_key"

            edited_json["verified_form"] = edited_json.get("verified_form") or edited_json.get("form", "")
            edited_json["verified_chapter"] = edited_json.get("verified_chapter") or edited_json.get("chapter", "")

            edited_json["form"] = edited_json.get("form") or edited_json.get("verified_form", "")
            edited_json["chapter"] = edited_json.get("chapter") or edited_json.get("verified_chapter", "")

            edited_json["group_id"] = ""
            edited_json["group_form"] = ""
            edited_json["group_chapter"] = ""
            edited_json["exercise_stage_id"] = ""
            edited_json["stage_index"] = 1
            edited_json["unlock_after_stage_id"] = ""

            edited_json["difficulty_level"] = int(edited_json.get("difficulty_level") or 3)
            edited_json["group_difficulty_level"] = int(
                edited_json.get("group_difficulty_level")
                or edited_json.get("difficulty_level")
                or 3
            )

            image_path = (
                item.get("image_url")
                or edited_json.get("image_path")
                or edited_json.get("diagram_path")
                or edited_json.get("_diagram_image_path")
                or None
            )

            question_id = insert_question(
                conn=conn,
                paper_id=paper_id,
                question_data=edited_json,
                image_path=image_path
            )

            if not isinstance(marking_scheme, dict):
                marking_scheme = {
                    "group_id": "",
                    "question_no": question_no,
                    "part": "",
                    "subpart": "",
                    "sub_subpart": "",
                    "subpart_marks": 1.0,
                    "question_total_marks": 1.0,
                    "answer_type": "mcq",
                    "final_answer": correct_option,
                    "answer_value": correct_option,
                    "correct_option": correct_option,
                    "steps": [],
                    "answer_range": [],
                    "units": "",
                    "method": "",
                    "rounding_and_tolerance": {},
                    "method_policy": {
                        "required_method": "",
                        "forbidden_methods": [],
                        "working_required": False
                    },
                    "conditional_marking_rules": [],
                    "graph_validation": {},
                    "drawing_validation": {},
                    "notes": [
                        "Kertas 1 MCQ marking scheme. Award 1 mark if selected option matches correct_option."
                    ],
                    "answer_image_path": ""
                }

            marking_scheme["question_no"] = question_no
            marking_scheme["answer_type"] = "mcq"
            marking_scheme["final_answer"] = correct_option
            marking_scheme["answer_value"] = correct_option
            marking_scheme["correct_option"] = correct_option
            marking_scheme["subpart_marks"] = float(marking_scheme.get("subpart_marks") or 1.0)
            marking_scheme["question_total_marks"] = float(marking_scheme.get("question_total_marks") or 1.0)

            marking_id = insert_marking_scheme(
                conn=conn,
                paper_id=paper_id,
                marking_data=marking_scheme
            )

            insert_question_marking_link(
                conn=conn,
                question_id=question_id,
                marking_scheme_id=marking_id,
                match_status="matched_exact"
            )

            cursor.execute("""
                UPDATE admin_import_items
                SET status = 'saved',
                    saved_question_id = %s
                WHERE item_id = %s
            """, (question_id, item["item_id"]))

            saved_count += 1
            saved_question_ids.append(question_id)

        cursor.execute("""
            UPDATE admin_import_batches
            SET status = 'completed'
            WHERE batch_id = %s
        """, (batch_id,))

        conn.commit()

        return jsonify({
            "success": True,
            "message": "Approved K1 draft items saved into question bank.",
            "paper_id": paper_id,
            "saved_count": saved_count,
            "skipped_count": skipped_count,
            "saved_question_ids": saved_question_ids
        }), 200

    except Exception as e:
        if conn:
            conn.rollback()

        print("ADMIN SAVE APPROVED K1 IMPORT ERROR:", e)
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route("/api/admin/import-batches/<int:batch_id>/save-approved-k2", methods=["POST"])
@require_auth("admin")
def admin_save_approved_k2_import_batch(batch_id):
    from parser.parser_common import (
        insert_paper, insert_question, insert_marking_scheme,
        insert_question_marking_link,
    )
    conn = None
    cursor = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT *
            FROM admin_import_batches
            WHERE batch_id = %s
            LIMIT 1
        """, (batch_id,))

        batch = cursor.fetchone()

        if not batch:
            return jsonify({
                "success": False,
                "message": "Import batch not found."
            }), 404

        if batch.get("paper_type") != "kertas2":
            return jsonify({
                "success": False,
                "message": "This save endpoint is only for Kertas 2 batches."
            }), 400

        cursor.execute("""
            SELECT COUNT(*) AS pending_count
            FROM admin_import_items
            WHERE batch_id = %s
              AND status NOT IN ('approved', 'skipped', 'saved')
        """, (batch_id,))

        pending_row = cursor.fetchone() or {}
        pending_count = int(pending_row.get("pending_count") or 0)

        if pending_count > 0:
            return jsonify({
                "success": False,
                "message": f"{pending_count} item(s) still need to be approved or skipped before completing this import."
            }), 400

        cursor.execute("""
            SELECT *
            FROM admin_import_items
            WHERE batch_id = %s
              AND status = 'approved'
              AND saved_question_id IS NULL
            ORDER BY CAST(question_no AS UNSIGNED), part, subpart, item_id
        """, (batch_id,))

        approved_items = cursor.fetchall() or []

        if not approved_items:
            cursor.execute("""
                UPDATE admin_import_batches
                SET status = 'completed'
                WHERE batch_id = %s
            """, (batch_id,))

            conn.commit()

            return jsonify({
                "success": True,
                "message": "Import review completed. No approved K2 questions were imported.",
                "paper_id": None,
                "saved_count": 0,
                "skipped_count": 0,
                "saved_question_ids": []
            }), 200

        paper_id = insert_paper(
            conn=conn,
            title=batch.get("title") or batch.get("original_file_name") or f"K2 Import Batch {batch_id}",
            paper_type="kertas2",
            file_path=batch.get("original_file_name") or "",
            exam_name="SPM Trial",
            subject="Mathematics",
            year=datetime.now().year
        )

        saved_count = 0
        skipped_count = 0
        saved_question_ids = []

        for item in approved_items:
            edited_json = parse_json_field(item.get("admin_edited_json"), {})

            if not isinstance(edited_json, dict):
                skipped_count += 1
                continue

            question_no = str(edited_json.get("question_no") or item.get("question_no") or "").strip()

            edited_json["question_no"] = question_no
            edited_json["question_type"] = edited_json.get("question_type") or "Structured"

            edited_json["verified_form"] = edited_json.get("verified_form") or edited_json.get("form", "")
            edited_json["verified_chapter"] = edited_json.get("verified_chapter") or edited_json.get("chapter", "")

            edited_json["form"] = edited_json.get("form") or edited_json.get("verified_form", "")
            edited_json["chapter"] = edited_json.get("chapter") or edited_json.get("verified_chapter", "")

            edited_json["difficulty_level"] = int(edited_json.get("difficulty_level") or 3)
            edited_json["group_difficulty_level"] = int(
                edited_json.get("group_difficulty_level")
                or edited_json.get("difficulty_level")
                or 3
            )

            marking_scheme = edited_json.get("marking_scheme")

            image_path = (
                item.get("image_url")
                or edited_json.get("_diagram_image_path")
                or edited_json.get("diagram_path")
                or edited_json.get("image_path")
                or None
            )

            question_id = insert_question(
                conn=conn,
                paper_id=paper_id,
                question_data=edited_json,
                image_path=image_path
            )

            if isinstance(marking_scheme, dict):
                marking_scheme["question_no"] = question_no
                marking_scheme["part"] = edited_json.get("part", "")
                marking_scheme["subpart"] = edited_json.get("subpart", "")
                marking_scheme["sub_subpart"] = edited_json.get("sub_subpart", "")
                marking_scheme["group_id"] = edited_json.get("group_id", "")
                marking_scheme["subpart_marks"] = float(
                    marking_scheme.get("subpart_marks")
                    or edited_json.get("display_marks")
                    or edited_json.get("marks")
                    or 0
                )

                marking_id = insert_marking_scheme(
                    conn=conn,
                    paper_id=paper_id,
                    marking_data=marking_scheme
                )

                insert_question_marking_link(
                    conn=conn,
                    question_id=question_id,
                    marking_scheme_id=marking_id,
                    match_status="matched_exact"
                )

            cursor.execute("""
                UPDATE admin_import_items
                SET status = 'saved',
                    saved_question_id = %s
                WHERE item_id = %s
            """, (question_id, item["item_id"]))

            saved_count += 1
            saved_question_ids.append(question_id)

        cursor.execute("""
            UPDATE admin_import_batches
            SET status = 'completed'
            WHERE batch_id = %s
        """, (batch_id,))

        conn.commit()

        return jsonify({
            "success": True,
            "message": "Approved K2 draft items saved into question bank.",
            "paper_id": paper_id,
            "saved_count": saved_count,
            "skipped_count": skipped_count,
            "saved_question_ids": saved_question_ids
        }), 200

    except Exception as e:
        if conn:
            conn.rollback()

        print("ADMIN SAVE APPROVED K2 IMPORT ERROR:", e)

        return jsonify({
            "success": False,
            "message": str(e)
        }), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
            

# Register the EasyLearn shared-portal login bridge.
# This module attaches /api/auth/portal-login to the existing Flask app.
import math_portal_app  # noqa: E402,F401


if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=5001,
        debug=True,
        use_reloader=False
    )

    # FOR RUNNING IN RAILWAY
    # port = int(os.environ.get("PORT", 8080))
    # app.run(host="0.0.0.0", port=port, debug=False)