from datetime import datetime, timedelta, date
from decimal import Decimal
from collections import defaultdict
import math

import pandas as pd


GRADE_ORDER = ["G", "E", "D", "C", "C+", "B", "B+", "A-", "A", "A+"]

def is_bm(lang):
    return str(lang or "").lower() == "bm"


def safe_int(value, default=0):
    try:
        if value is None:
            return default
        return int(value)
    except Exception:
        return default


def safe_float(value, default=0.0):
    try:
        if value is None:
            return default
        if isinstance(value, Decimal):
            return float(value)
        return float(value)
    except Exception:
        return default


def clamp(value, min_value, max_value):
    return max(min_value, min(max_value, value))


def format_duration_hm(total_seconds, lang="english"):
    total_seconds = safe_int(total_seconds)
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60

    if is_bm(lang):
        return f"{hours}j {minutes}m"

    return f"{hours}h {minutes}m"


def format_week_delta(delta_seconds, lang="english"):
    delta_seconds = safe_int(delta_seconds)

    if delta_seconds == 0:
        return "Tiada perubahan minggu ini" if is_bm(lang) else "No change this week"

    sign = "+" if delta_seconds > 0 else "-"
    abs_seconds = abs(delta_seconds)
    hours = abs_seconds // 3600
    minutes = (abs_seconds % 3600) // 60

    if is_bm(lang):
        return f"{sign}{hours}j {minutes}m minggu ini"

    return f"{sign}{hours}h {minutes}m this week"


def get_topic_name(row, lang="english"):
    if is_bm(lang):
        return row.get("name_bm") or row.get("name_en") or "Topik Tidak Diketahui"

    return row.get("name_en") or row.get("name_bm") or "Unknown Topic"


def score_to_grade(score):
    score = safe_float(score)

    if score >= 90:
        return "A+"
    if score >= 80:
        return "A"
    if score >= 70:
        return "A-"
    if score >= 65:
        return "B+"
    if score >= 60:
        return "B"
    if score >= 55:
        return "C+"
    if score >= 50:
        return "C"
    if score >= 45:
        return "D"
    if score >= 40:
        return "E"
    return "G"

def grade_to_mid_score(grade):
    mapping = {
        "A+": 95,
        "A": 85,
        "A-": 75,
        "B+": 67,
        "B": 62,
        "C+": 57,
        "C": 52,
        "D": 47,
        "E": 42,
        "G": 30,
    }
    return mapping.get(str(grade or "").upper(), None)

def unpack_grade_model(grade_model):
    """
    Supports:
    1. New model bundle saved by train_grade_regression_model.py
    2. Old raw sklearn model
    """
    if isinstance(grade_model, dict):
        model = grade_model.get("model")
        mode = grade_model.get("mode", "score_regression")
        feature_columns = grade_model.get("feature_columns")
        model_type = grade_model.get("model_type", type(model).__name__ if model else None)
        return model, mode, feature_columns, model_type

    return (
        grade_model,
        "legacy_model",
        None,
        type(grade_model).__name__ if grade_model is not None else None,
    )

def grade_to_performance_band(grade):
    grade = str(grade or "").upper().strip()

    if grade in ["A-", "A", "A+"]:
        return "A range"
    if grade in ["B", "B+"]:
        return "B/B+"
    if grade in ["C", "C+"]:
        return "C/C+"
    if grade in ["D", "E", "G"]:
        return grade

    return "--"


def get_topic_status(accuracy, attempts):
    accuracy = safe_float(accuracy)
    attempts = safe_int(attempts)

    if attempts <= 0:
        return "unpracticed"
    if accuracy >= 80:
        return "mastered"
    if accuracy < 50:
        return "review"
    return "average"


def get_priority_label(priority_score, lang="english"):
    if priority_score >= 75:
        return "Tinggi" if is_bm(lang) else "High"
    if priority_score >= 50:
        return "Sederhana" if is_bm(lang) else "Medium"
    return "Rendah" if is_bm(lang) else "Low"


def get_weekday_labels(lang="english"):
    if is_bm(lang):
        return ["Isn", "Sel", "Rab", "Kha", "Jum", "Sab", "Aha"]
    return ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def format_hour_window(start_hour, duration_minutes):
    start_hour = safe_int(start_hour, 20)
    duration_minutes = safe_int(duration_minutes, 30)

    start_dt = datetime(2000, 1, 1, start_hour, 0)
    end_dt = start_dt + timedelta(minutes=duration_minutes)

    start_str = start_dt.strftime("%I:%M %p").lstrip("0")
    end_str = end_dt.strftime("%I:%M %p").lstrip("0")

    return f"{start_str} - {end_str}"


def get_next_session_label(best_hour, lang="english"):
    best_hour = safe_int(best_hour, 20)
    current_hour = datetime.now().hour

    # If the suggested time has already passed today, avoid saying "Tonight" or "This afternoon".
    if best_hour <= current_hour:
        return "Slot sesuai seterusnya" if is_bm(lang) else "Next suitable slot"

    if best_hour >= 18:
        return "Malam ini" if is_bm(lang) else "Tonight"

    if best_hour >= 12:
        return "Petang ini" if is_bm(lang) else "This afternoon"

    return "Hari ini" if is_bm(lang) else "Today"

STUDY_PATTERN_FEATURE_COLUMNS = [
    "total_sessions",
    "total_questions",
    "questions_per_session",
    "avg_time_per_question",
    "active_days",
    "sessions_last_7_days",
    "active_days_last_7_days",
    "sessions_previous_7_days",
    "study_minutes_last_7_days",
    "study_minutes_previous_7_days",
    "total_study_minutes",
    "avg_session_minutes",
    "max_streak",
    "evening_session_ratio",
    "weekend_session_ratio",
    "active_day_ratio",
    "recent_active_day_ratio",
    "session_growth_ratio",
]

def normalize_persona_name(persona):
    old_to_new = {
        "Consistent Learner": "Consistent Climber",
        "Consistent Achiever": "Consistent Climber",
        "Last-Minute Learner": "Deep Focus Learner",
        "The Crammer": "Deep Focus Learner",
        "Low Activity Learner": "Fresh Starter",
        "Needs Motivation": "Fresh Starter",
        "Balanced Learner": "Flexible Learner",
        "Irregular Learner": "Flexible Learner",
    }

    return old_to_new.get(persona, persona or "Flexible Learner")

def get_study_persona_content(
    persona,
    lang="english",
    sessions_last_7_days=0,
    active_days_this_week=0,
):
    """
    Returns bilingual display text for the study pattern card.

    persona_key remains in English for internal/debug use.
    persona display, proof, and suggestion are translated based on lang.
    """
    persona = normalize_persona_name(persona)

    selected_lang = "bm" if is_bm(lang) else "english"

    content = {
        "Consistent Climber": {
            "english": {
                "display": "Consistent Climber",
                "proof": f"You practised across {active_days_this_week} active day(s) this week.",
                "suggestion": "Keep this routine and focus on topics that still need review.",
            },
            "bm": {
                "display": "Pelajar Konsisten",
                "proof": f"Anda telah berlatih pada {active_days_this_week} hari aktif minggu ini.",
                "suggestion": "Teruskan rutin ini dan fokus pada topik yang masih perlu diulang kaji.",
            },
        },
        "Deep Focus Learner": {
            "english": {
                "display": "Deep Focus Learner",
                "proof": f"You completed {sessions_last_7_days} recent session(s) with a more concentrated practice style.",
                "suggestion": "Your focus is useful, but try spreading some practice across more days for better memory.",
            },
            "bm": {
                "display": "Pelajar Fokus Mendalam",
                "proof": f"Anda telah melengkapkan {sessions_last_7_days} sesi baru-baru ini dengan gaya latihan yang lebih tertumpu.",
                "suggestion": "Fokus anda sangat baik, tetapi cuba sebarkan latihan ke beberapa hari berbeza untuk membantu ingatan.",
            },
        },
        "Weekend Learner": {
            "english": {
                "display": "Weekend Learner",
                "proof": "Your practice pattern shows more activity during weekends.",
                "suggestion": "Weekend study works well, but adding one short weekday session can improve consistency.",
            },
            "bm": {
                "display": "Pelajar Hujung Minggu",
                "proof": "Corak latihan anda menunjukkan lebih banyak aktiviti pada hujung minggu.",
                "suggestion": "Belajar pada hujung minggu adalah baik, tetapi menambah satu sesi pendek pada hari biasa boleh meningkatkan konsistensi.",
            },
        },
        "Fresh Starter": {
            "english": {
                "display": "Fresh Starter",
                "proof": "You are still building your practice record.",
                "suggestion": "Complete a few more short sessions so EasyLearn can understand your learning pattern better.",
            },
            "bm": {
                "display": "Pelajar Baru Bermula",
                "proof": "Anda masih sedang membina rekod latihan anda.",
                "suggestion": "Lengkapkan beberapa sesi pendek lagi supaya EasyLearn boleh memahami corak pembelajaran anda dengan lebih baik.",
            },
        },
        "Flexible Learner": {
            "english": {
                "display": "Flexible Learner",
                "proof": f"You had {sessions_last_7_days} session(s) in the last 7 days.",
                "suggestion": "Try setting a simple weekly target to make your revision more consistent.",
            },
            "bm": {
                "display": "Pelajar Fleksibel",
                "proof": f"Anda mempunyai {sessions_last_7_days} sesi dalam 7 hari yang lalu.",
                "suggestion": "Cuba tetapkan sasaran mingguan yang mudah supaya ulang kaji anda menjadi lebih konsisten.",
            },
        },
        "High Achiever": {
            "english": {
                "display": "High Achiever",
                "proof": "Your practice record shows strong overall performance and consistent learning effort.",
                "suggestion": "Keep challenging yourself with higher-difficulty questions to maintain your progress.",
            },
            "bm": {
                "display": "Pelajar Berprestasi Tinggi",
                "proof": "Rekod latihan anda menunjukkan prestasi keseluruhan yang baik dan usaha pembelajaran yang konsisten.",
                "suggestion": "Terus cabar diri anda dengan soalan yang lebih sukar untuk mengekalkan kemajuan.",
            },
        },
    }

    if persona not in content:
        persona = "Flexible Learner"

    return content[persona][selected_lang]

def refine_study_persona_key(persona_key, session_summary, performance=None):
    """
    Refines the K-Means persona using direct behavioural evidence.

    K-Means assigns a cluster based on all features, but some individual students
    inside a cluster may not strongly match the cluster's display persona.
    These guardrails keep the dashboard label explainable to students.
    """
    performance = performance or {}

    persona_key = normalize_persona_name(persona_key)

    total_sessions = safe_int(session_summary.get("total_sessions"))
    active_days = safe_int(session_summary.get("active_days"))
    sessions_last_7_days = safe_int(session_summary.get("sessions_last_7_days"))
    active_days_this_week = safe_int(session_summary.get("active_days_this_week"))

    weekend_ratio = safe_float(session_summary.get("weekend_session_ratio"))
    avg_session_minutes = safe_float(session_summary.get("avg_session_seconds")) / 60

    total_questions = safe_float(performance.get("total_attempts"))
    questions_per_session = (
        total_questions / total_sessions
        if total_sessions > 0
        else 0
    )

    active_day_ratio = (
        active_days / total_sessions
        if total_sessions > 0
        else 0
    )

    # Very little data should not be forced into a strong behavioural label.
    if total_sessions <= 3:
        return "Fresh Starter"

    # Weekend Learner must have clear weekend evidence.
    # If weekend activity is below 40%, do not display Weekend Learner.
    if persona_key == "Weekend Learner" and weekend_ratio < 0.40:
        if active_day_ratio >= 0.60 and active_days >= 8:
            return "Consistent Climber"

        if avg_session_minutes >= 25 or questions_per_session >= 15:
            return "Deep Focus Learner"

        return "Flexible Learner"

    # If weekend activity is clearly dominant, Weekend Learner is valid.
    if weekend_ratio >= 0.50 and total_sessions >= 4:
        return "Weekend Learner"

    # If practice is spread across many days, Consistent Climber is more explainable.
    if active_day_ratio >= 0.65 and active_days >= 8:
        return "Consistent Climber"

    # Longer or heavier sessions suggest Deep Focus.
    if avg_session_minutes >= 25 or questions_per_session >= 15:
        return "Deep Focus Learner"

    # If recent activity is low, use Fresh Starter only for limited total history.
    if total_sessions < 8 and sessions_last_7_days <= 1:
        return "Fresh Starter"

    return persona_key or "Flexible Learner"

def predict_study_persona_from_model(
    pattern_model,
    pattern_scaler,
    pattern_persona_map,
    performance,
    session_summary,
):
    if pattern_model is None or pattern_scaler is None:
        return None

    total_sessions = safe_float(session_summary.get("total_sessions"))
    total_questions = safe_float(performance.get("total_attempts"))
    active_days = safe_float(session_summary.get("active_days"))
    sessions_last_7_days = safe_float(session_summary.get("sessions_last_7_days"))
    active_days_last_7_days = safe_float(session_summary.get("active_days_last_7_days"))
    sessions_previous_7_days = safe_float(session_summary.get("sessions_previous_7_days"))
    study_minutes_last_7_days = safe_float(session_summary.get("study_minutes_last_7_days"))
    study_minutes_previous_7_days = safe_float(session_summary.get("study_minutes_previous_7_days"))

    session_growth_ratio = (
        (sessions_last_7_days - sessions_previous_7_days) / sessions_previous_7_days
        if sessions_previous_7_days > 0
        else sessions_last_7_days
    )

    questions_per_session = (
        total_questions / total_sessions
        if total_sessions > 0
        else 0
    )

    active_day_ratio = (
        active_days / total_sessions
        if total_sessions > 0
        else 0
    )

    recent_active_day_ratio = (
        active_days_last_7_days / sessions_last_7_days
        if sessions_last_7_days > 0
        else 0
    )

    features = {
        "total_sessions": total_sessions,
        "total_questions": total_questions,
        "questions_per_session": questions_per_session,
        "avg_time_per_question": safe_float(performance.get("avg_time_per_question")),
        "active_days": active_days,
        "sessions_last_7_days": sessions_last_7_days,
        "active_days_last_7_days": active_days_last_7_days,
        "total_study_minutes": safe_float(session_summary.get("total_study_seconds")) / 60,
        "avg_session_minutes": safe_float(session_summary.get("avg_session_seconds")) / 60,
        "max_streak": safe_float(session_summary.get("max_streak")),
        "evening_session_ratio": safe_float(session_summary.get("evening_session_ratio")),
        "weekend_session_ratio": safe_float(session_summary.get("weekend_session_ratio")),
        "active_day_ratio": active_day_ratio,
        "recent_active_day_ratio": recent_active_day_ratio,
        "sessions_previous_7_days": sessions_previous_7_days,
        "study_minutes_last_7_days": study_minutes_last_7_days,
        "study_minutes_previous_7_days": study_minutes_previous_7_days,
        "session_growth_ratio": session_growth_ratio,
    }

    try:
        import pandas as pd

        model_columns = getattr(pattern_model, "feature_names_in_", None)

        if model_columns is None:
            model_columns = STUDY_PATTERN_FEATURE_COLUMNS

        input_df = pd.DataFrame(
            [[features.get(column, 0) for column in model_columns]],
            columns=model_columns,
        )

        scaled = pattern_scaler.transform(input_df)
        cluster_id = int(pattern_model.predict(scaled)[0])

        persona = pattern_persona_map.get(cluster_id)

        if persona is None:
            persona = pattern_persona_map.get(str(cluster_id))

        return normalize_persona_name(persona)

    except Exception as error:
        print("STUDY PATTERN MODEL ERROR:", error)
        return None
    
def fetch_overall_performance(cursor, student_id):
    cursor.execute(
        """
        SELECT
            COUNT(*) AS total_attempts,
            ROUND(AVG(is_correct) * 100, 2) AS overall_accuracy,
            ROUND(AVG(time_taken_seconds), 2) AS avg_time_per_question,
            SUM(CASE WHEN paper_type = 'kertas1' THEN 1 ELSE 0 END) AS paper1_attempts,
            SUM(CASE WHEN paper_type = 'kertas2' THEN 1 ELSE 0 END) AS paper2_attempts,
            ROUND(AVG(CASE WHEN paper_type = 'kertas1' THEN is_correct END) * 100, 2) AS paper1_accuracy,
            ROUND(AVG(CASE WHEN paper_type = 'kertas2' THEN is_correct END) * 100, 2) AS paper2_accuracy,
            ROUND(
                SUM(COALESCE(score, is_correct, 0))
                / NULLIF(SUM(COALESCE(NULLIF(max_score, 0), 1)), 0)
                * 100,
                2
            ) AS score_ratio_percent,
            ROUND(
                AVG(
                    CASE
                        WHEN difficulty_level_snapshot >= 4
                        THEN is_correct
                    END
                ) * 100,
                2
            ) AS hard_accuracy_percent
        FROM attempts
        WHERE user_id = %s
        """,
        (student_id,),
    )
    row = cursor.fetchone() or {}

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

    return {
        "total_attempts": safe_int(row.get("total_attempts")),
        "overall_accuracy": safe_float(row.get("overall_accuracy")),
        "recent_accuracy": safe_float(
            recent.get("recent_accuracy"),
            safe_float(row.get("overall_accuracy")),
        ),
        "avg_time_per_question": safe_float(row.get("avg_time_per_question")),
        "score_ratio_percent": safe_float(row.get("score_ratio_percent")),
        "hard_accuracy_percent": safe_float(row.get("hard_accuracy_percent")),

        "paper1_attempts": safe_int(row.get("paper1_attempts")),
        "paper2_attempts": safe_int(row.get("paper2_attempts")),
        "paper1_accuracy": safe_float(row.get("paper1_accuracy")),
        "paper2_accuracy": safe_float(row.get("paper2_accuracy")),
    }


def fetch_session_summary(cursor, student_id):
    cursor.execute(
        """
        SELECT
            COUNT(*) AS total_sessions,
            COUNT(DISTINCT DATE(start_time)) AS active_days,
            SUM(GREATEST(IFNULL(duration_seconds, 0), 0)) AS total_study_seconds,
            ROUND(AVG(GREATEST(IFNULL(duration_seconds, 0), 0)), 0) AS avg_session_seconds,
            MAX(IFNULL(highest_streak, 0)) AS max_streak,

            SUM(
                CASE
                    WHEN start_time >= DATE_SUB(NOW(), INTERVAL 7 DAY)
                    THEN 1 ELSE 0
                END
            ) AS sessions_last_7_days,

            SUM(
                CASE
                    WHEN start_time >= DATE_SUB(NOW(), INTERVAL 14 DAY)
                    AND start_time < DATE_SUB(NOW(), INTERVAL 7 DAY)
                    THEN 1 ELSE 0
                END
            ) AS sessions_previous_7_days,

            SUM(
                CASE
                    WHEN start_time >= DATE_SUB(NOW(), INTERVAL 7 DAY)
                    THEN GREATEST(IFNULL(duration_seconds, 0), 0) ELSE 0
                END
            ) AS study_seconds_this_week,

            SUM(
                CASE
                    WHEN start_time >= DATE_SUB(NOW(), INTERVAL 14 DAY)
                    AND start_time < DATE_SUB(NOW(), INTERVAL 7 DAY)
                    THEN GREATEST(IFNULL(duration_seconds, 0), 0) ELSE 0
                END
            ) AS study_seconds_previous_week,

            COUNT(
                DISTINCT CASE
                    WHEN start_time >= DATE_SUB(NOW(), INTERVAL 7 DAY)
                    THEN DATE(start_time)
                END
            ) AS active_days_this_week,

            COUNT(
                DISTINCT CASE
                    WHEN start_time >= DATE_SUB(NOW(), INTERVAL 7 DAY)
                    THEN DATE(start_time)
                END
            ) AS active_days_last_7_days,

            ROUND(AVG(HOUR(start_time)), 0) AS avg_start_hour,

            SUM(
                CASE
                    WHEN HOUR(start_time) BETWEEN 18 AND 23
                    THEN 1 ELSE 0
                END
            ) / NULLIF(COUNT(*), 0) AS evening_session_ratio,

            SUM(
                CASE
                    WHEN DAYOFWEEK(start_time) IN (1, 7)
                    THEN 1 ELSE 0
                END
            ) / NULLIF(COUNT(*), 0) AS weekend_session_ratio

        FROM practice_sessions
        WHERE user_id = %s
            AND total_questions_answered > 0
        """,
        (student_id,),
    )

    row = cursor.fetchone() or {}

    cursor.execute(
        """
        SELECT
            HOUR(start_time) AS preferred_start_hour,
            COUNT(*) AS session_count,
            SUM(GREATEST(IFNULL(duration_seconds, 0), 0)) AS total_seconds
        FROM practice_sessions
        WHERE user_id = %s
        AND total_questions_answered > 0
        GROUP BY HOUR(start_time)
        ORDER BY session_count DESC, total_seconds DESC
        LIMIT 1
        """,
        (student_id,),
    )

    preferred_hour_row = cursor.fetchone() or {}

    cursor.execute(
        """
        SELECT DATE(start_time) AS session_date
        FROM practice_sessions
        WHERE user_id = %s
        AND total_questions_answered > 0
        ORDER BY start_time ASC
        """,
        (student_id,),
    )
    date_rows = cursor.fetchall() or []

    session_dates = []
    for date_row in date_rows:
        session_date = date_row.get("session_date")

        if isinstance(session_date, datetime):
            session_dates.append(session_date.date())
        elif isinstance(session_date, date):
            session_dates.append(session_date)

    current_streak, best_streak = calculate_streaks(session_dates)

    return {
        "total_sessions": safe_int(row.get("total_sessions")),
        "active_days": safe_int(row.get("active_days")),
        "total_study_seconds": safe_int(row.get("total_study_seconds")),
        "avg_session_seconds": safe_int(row.get("avg_session_seconds")),
        "max_streak": max(safe_int(row.get("max_streak")), best_streak),
        "current_streak": current_streak,
        "best_streak": best_streak,
        "sessions_last_7_days": safe_int(row.get("sessions_last_7_days")),
        "study_seconds_this_week": safe_int(row.get("study_seconds_this_week")),
        "study_seconds_previous_week": safe_int(row.get("study_seconds_previous_week")),
        "active_days_this_week": safe_int(row.get("active_days_this_week")),
        "avg_start_hour": safe_int(row.get("avg_start_hour"), 20),
        "session_dates": session_dates,
        "active_days_last_7_days": safe_int(row.get("active_days_last_7_days")),
        "evening_session_ratio": safe_float(row.get("evening_session_ratio")),
        "weekend_session_ratio": safe_float(row.get("weekend_session_ratio")),
        "sessions_previous_7_days": safe_int(row.get("sessions_previous_7_days")),
        "study_minutes_last_7_days": safe_float(row.get("study_seconds_this_week")) / 60,
        "study_minutes_previous_7_days": safe_float(row.get("study_seconds_previous_week")) / 60,
        "preferred_start_hour": safe_int(
            preferred_hour_row.get("preferred_start_hour"),
            safe_int(row.get("avg_start_hour"), 20),
        ),
    }


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


def fetch_topic_performance(cursor, student_id, lang="english"):
    cursor.execute(
        """
        SELECT
            c.id AS chapter_id,
            c.form,
            c.chapter_no,
            c.name_en,
            c.name_bm,

            COALESCE(w.weightage_percentage, 0) AS spm_weightage_percentage,
            COALESCE(w.total_marks, 0) AS exam_total_marks,
            COALESCE(w.question_count, 0) AS exam_question_count,

            COUNT(a.attempt_id) AS attempts,

            ROUND(AVG(a.is_correct) * 100, 2) AS accuracy,

            ROUND(
                SUM(COALESCE(a.score, a.is_correct, 0))
                / NULLIF(SUM(COALESCE(NULLIF(a.max_score, 0), 1)), 0)
                * 100,
                2
            ) AS score_ratio_percent,

            SUM(CASE WHEN a.is_correct = 0 THEN 1 ELSE 0 END) AS mistakes,
            MAX(a.attempted_at) AS last_practiced_at,

            SUM(
                CASE 
                    WHEN a.attempted_at >= DATE_SUB(NOW(), INTERVAL 14 DAY)
                    THEN 1 ELSE 0 
                END
            ) AS recent_attempts,

            ROUND(
                AVG(
                    CASE
                        WHEN a.attempted_at >= DATE_SUB(NOW(), INTERVAL 14 DAY)
                        THEN a.is_correct
                    END
                ) * 100,
                2
            ) AS recent_accuracy,

            ROUND(
                (
                    SUM(
                        CASE 
                            WHEN a.attempted_at >= DATE_SUB(NOW(), INTERVAL 14 DAY)
                            THEN COALESCE(a.score, a.is_correct, 0)
                            ELSE 0
                        END
                    )
                    /
                    NULLIF(
                        SUM(
                            CASE 
                                WHEN a.attempted_at >= DATE_SUB(NOW(), INTERVAL 14 DAY)
                                THEN COALESCE(NULLIF(a.max_score, 0), 1)
                                ELSE 0
                            END
                        ),
                        0
                    )
                ) * 100,
                2
            ) AS recent_score_ratio_percent

        FROM chapters c

        LEFT JOIN chapter_exam_weightage w
            ON w.chapter_id = c.id
           AND w.source_name = 'SPM 2021-2024 Paper Analysis'
           AND w.is_active = 1

        LEFT JOIN attempts a
            ON a.chapter_snapshot_id = c.id
           AND a.user_id = %s

        GROUP BY
            c.id,
            c.form,
            c.chapter_no,
            c.name_en,
            c.name_bm,
            w.weightage_percentage,
            w.total_marks,
            w.question_count

        ORDER BY 
            CAST(REPLACE(LOWER(c.form), 'form ', '') AS UNSIGNED) ASC,
            CAST(c.chapter_no AS UNSIGNED) ASC,
            c.id ASC
        """,
        (student_id,),
    )

    rows = cursor.fetchall() or []
    topics = []

    for row in rows:
        attempts = safe_int(row.get("attempts"))
        accuracy = safe_float(row.get("accuracy"))
        score_ratio = safe_float(row.get("score_ratio_percent"), accuracy)

        status = get_topic_status(accuracy, attempts)

        topics.append(
            {
                "chapter_id": row.get("chapter_id"),
                "form": row.get("form"),
                "chapter_no": row.get("chapter_no"),
                "name": get_topic_name(row, lang),
                "name_en": row.get("name_en"),
                "name_bm": row.get("name_bm"),

                # New weightage source from chapter_exam_weightage
                "spm_weightage_percentage": safe_float(row.get("spm_weightage_percentage")),
                "exam_total_marks": safe_float(row.get("exam_total_marks")),
                "exam_question_count": safe_int(row.get("exam_question_count")),

                # Student performance
                "attempts": attempts,
                "accuracy": round(accuracy, 2),
                "score_ratio_percent": round(score_ratio, 2),
                "mistakes": safe_int(row.get("mistakes")),

                # Recent behaviour
                "recent_attempts": safe_int(row.get("recent_attempts")),
                "recent_accuracy": safe_float(row.get("recent_accuracy"), accuracy),
                "recent_score_ratio_percent": safe_float(
                    row.get("recent_score_ratio_percent"),
                    score_ratio,
                ),

                "last_practiced_at": row.get("last_practiced_at"),
                "status": status,
            }
        )

    return topics


def calculate_topic_summary(topic_rows):
    practiced_topics = [topic for topic in topic_rows if topic["attempts"] > 0]

    if not practiced_topics:
        return {
            "avg_topic_mastery": 0,
            "weak_topic_count": 0,
            "strong_topic_count": 0,
            "mastered_count": 0,
            "average_count": 0,
            "review_count": 0,
        }

    mastered_count = sum(1 for topic in practiced_topics if topic["status"] == "mastered")
    review_count = sum(1 for topic in practiced_topics if topic["status"] == "review")
    average_count = sum(1 for topic in practiced_topics if topic["status"] == "average")

    avg_topic_mastery = sum(topic["accuracy"] for topic in practiced_topics) / len(practiced_topics)

    return {
        "avg_topic_mastery": round(avg_topic_mastery, 2),
        "weak_topic_count": review_count,
        "strong_topic_count": mastered_count,
        "mastered_count": mastered_count,
        "average_count": average_count,
        "review_count": review_count,
    }


def calculate_consistency_score(session_summary):
    total_sessions = session_summary["total_sessions"]
    active_days = session_summary["active_days"]
    sessions_last_7_days = session_summary["sessions_last_7_days"]
    current_streak = session_summary["current_streak"]

    if total_sessions <= 0:
        return 0

    score = 0
    score += min(sessions_last_7_days, 5) * 12
    score += min(active_days, 20) * 1.5
    score += min(current_streak, 7) * 4

    return int(clamp(round(score), 0, 100))


def build_feature_vector(performance, session_summary, topic_summary):
    total_sessions = session_summary["total_sessions"]
    total_study_minutes = session_summary["total_study_seconds"] / 60
    avg_session_minutes = session_summary["avg_session_seconds"] / 60
    consistency_score = calculate_consistency_score(session_summary)

    return {
        "total_questions_attempted": performance["total_attempts"],
        "overall_accuracy": performance["overall_accuracy"] / 100,
        "overall_accuracy_percent": performance["overall_accuracy"],
        "recent_accuracy": performance["recent_accuracy"] / 100,
        "recent_accuracy_percent": performance["recent_accuracy"],
        "paper1_accuracy": performance["paper1_accuracy"] / 100,
        "paper1_accuracy_percent": performance["paper1_accuracy"],
        "paper2_accuracy": performance["paper2_accuracy"] / 100,
        "paper2_accuracy_percent": performance["paper2_accuracy"],
        "score_ratio_percent": performance["score_ratio_percent"],
        "hard_accuracy_percent": performance["hard_accuracy_percent"],  
        "avg_time_per_question": performance["avg_time_per_question"],
        "total_sessions": total_sessions,
        "active_days": session_summary["active_days"],
        "total_study_minutes": round(total_study_minutes, 2),
        "avg_session_minutes": round(avg_session_minutes, 2),
        "study_consistency_score": consistency_score,
        "max_streak": session_summary["max_streak"],
        "avg_topic_mastery": topic_summary["avg_topic_mastery"],
        "weak_topic_count": topic_summary["weak_topic_count"],
        "strong_topic_count": topic_summary["strong_topic_count"],
    }


def build_model_input_dataframe(grade_model, features):
    """
    Builds the exact feature dataframe needed by the saved grade model.
    Supports model bundle, raw sklearn pipeline/model, and fallback columns.
    """
    model, mode, bundle_columns, model_type = unpack_grade_model(grade_model)

    default_17_columns = [
        "total_questions_attempted",
        "overall_accuracy",
        "recent_accuracy",
        "paper1_accuracy",
        "paper2_accuracy",
        "score_ratio_percent",
        "hard_accuracy_percent",
        "avg_time_per_question",
        "total_sessions",
        "active_days",
        "total_study_minutes",
        "avg_session_minutes",
        "study_consistency_score",
        "max_streak",
        "avg_topic_mastery",
        "weak_topic_count",
        "strong_topic_count",
    ]

    default_5_columns = [
        "total_questions_attempted",
        "overall_accuracy",
        "avg_time_per_question",
        "total_sessions",
        "max_streak",
    ]

    if bundle_columns:
        columns = list(bundle_columns)
    elif model is not None and hasattr(model, "feature_names_in_"):
        columns = list(model.feature_names_in_)
    elif model is not None and hasattr(model, "steps") and hasattr(model.steps[0][1], "feature_names_in_"):
        columns = list(model.steps[0][1].feature_names_in_)
    else:
        expected_count = getattr(model, "n_features_in_", None)
        columns = default_17_columns if expected_count == 17 else default_5_columns

    values = [features.get(column, 0) for column in columns]

    return pd.DataFrame([values], columns=columns)

def heuristic_score(features):
    accuracy_component = features["overall_accuracy_percent"] * 0.48
    recent_component = features["recent_accuracy_percent"] * 0.18
    topic_component = features["avg_topic_mastery"] * 0.12
    consistency_component = features["study_consistency_score"] * 0.12
    volume_component = min(features["total_questions_attempted"], 100) * 0.07
    session_component = min(features["total_sessions"], 20) * 0.5

    penalty = min(features["weak_topic_count"] * 2.5, 12)

    score = (
        accuracy_component
        + recent_component
        + topic_component
        + consistency_component
        + volume_component
        + session_component
        - penalty
    )

    return round(clamp(score, 0, 100), 2)


def predict_grade_with_status(grade_model, features, lang="english"):
    total_attempts = safe_int(features.get("total_questions_attempted"))
    total_sessions = safe_int(features.get("total_sessions"))
    overall_accuracy = safe_float(features.get("overall_accuracy_percent"))
    recent_accuracy = safe_float(features.get("recent_accuracy_percent"))

    if total_attempts < 15 or total_sessions < 3:
        return {
            "grade": "--",
            "score": None,
            "confidence": 0,
            "status": "insufficient_data",
            "reason": (
                "Lengkapkan sekurang-kurangnya 15 soalan dan 3 sesi latihan untuk membuka ramalan gred yang lebih dipercayai."
                if is_bm(lang)
                else "Complete at least 15 practice questions and 3 practice sessions to unlock a more reliable grade prediction."
            ),
        }

    predicted_score = None
    predicted_grade = None
    model_confidence = None
    model_used = False

    model, model_mode, model_feature_columns, model_type = unpack_grade_model(grade_model)

    try:
        if model is not None:
            model_input = build_model_input_dataframe(grade_model, features)
            raw_prediction = model.predict(model_input)[0]

            # New regression model returns numeric score.
            predicted_score = round(clamp(safe_float(raw_prediction), 0, 100), 2)
            predicted_grade = score_to_grade(predicted_score)
            model_used = True

            # Only classifier models have predict_proba.
            if hasattr(model, "predict_proba"):
                probabilities = model.predict_proba(model_input)[0]
                classes = list(getattr(model, "classes_", []))

                if predicted_grade in classes:
                    model_confidence = int(round(probabilities[classes.index(predicted_grade)] * 100))
                else:
                    model_confidence = int(round(max(probabilities) * 100))

    except Exception as error:
        print("GRADE MODEL PREDICTION ERROR:", error)

    fallback_score = heuristic_score(features)
    fallback_grade = score_to_grade(fallback_score)

    if predicted_score is None:
        predicted_score = fallback_score

    if not predicted_grade:
        predicted_grade = fallback_grade

    data_volume_score = min(total_attempts / 60, 1) * 35
    session_score = min(total_sessions / 12, 1) * 20
    consistency_score = min(features.get("study_consistency_score", 0) / 100, 1) * 20
    accuracy_stability_score = max(0, 25 - abs(overall_accuracy - recent_accuracy) * 0.5)

    heuristic_confidence = int(
        clamp(
            round(data_volume_score + session_score + consistency_score + accuracy_stability_score),
            35,
            92,
        )
    )

    if model_confidence is not None:
        confidence = int(
            clamp(
                round((heuristic_confidence * 0.7) + (model_confidence * 0.3)),
                35,
                95,
            )
        )
    else:
        confidence = heuristic_confidence

    if total_attempts >= 40 and total_sessions >= 8:
        status = "reliable"
    elif total_attempts >= 20:
        status = "developing"
    else:
        status = "early_prediction"

    if is_bm(lang):
        if status == "reliable":
            reason = (
                f"Ramalan ini berdasarkan {total_attempts} percubaan, "
                f"prestasi latihan keseluruhan, ketepatan terkini {round(recent_accuracy, 1)}%, "
                f"penguasaan topik, dan konsistensi latihan anda."
            )
        else:
            reason = (
                f"Ramalan awal ini menganggarkan gred anda sebagai {predicted_grade}. "
                "Lebih banyak latihan akan meningkatkan kebolehpercayaan ramalan."
            )
    else:
        if status == "reliable":
            reason = (
                f"This prediction is based on {total_attempts} attempts, "
                f"your overall practice performance, {round(recent_accuracy, 1)}% recent accuracy, "
                f"topic mastery, and study consistency."
            )
        else:
            reason = (
                f"Early prediction estimates your grade as {predicted_grade}. "
                "More practice will improve prediction reliability."
            )

    return {
        "grade": predicted_grade,
        "score": round(safe_float(predicted_score), 2),
        "confidence": int(clamp(confidence, 35, 95)),
        "status": status,
        "reason": reason,
        "model_used": model_used,
        "model_type": model_type,
        "prediction_mode": model_mode,
    }

def build_topic_mastery(topic_rows, lang="english"):
    mastered_count = 0
    average_count = 0
    review_count = 0

    topics = []

    for topic in topic_rows:
        status = topic["status"]

        if status == "mastered":
            mastered_count += 1
        elif status == "review":
            review_count += 1
        elif status == "average":
            average_count += 1

        topics.append(
            {
                "chapter_id": topic["chapter_id"],
                "form": topic.get("form"),
                "chapter_no": topic.get("chapter_no"),
                "topic": topic["name"],
                "name": topic["name"],
                "topic_name": topic["name"],         
                "accuracy": round(topic["accuracy"], 2),
                "attempts": topic["attempts"],
                "total_attempts": topic["attempts"],
                "status": status,
                "is_weak_highlight": status == "review",
            }
        )

    return {
        "mastered_count": mastered_count,
        "average_count": average_count,
        "review_count": review_count,
        "topics": topics,
    }


def days_since(dt):
    if not dt:
        return 999

    if isinstance(dt, datetime):
        target_date = dt.date()
    elif isinstance(dt, date):
        target_date = dt
    else:
        return 999

    return (datetime.now().date() - target_date).days


def build_topic_recommendations(topic_rows, lang="english", limit=3):
    """
    Personalized content-based topic recommendation.

    Main principle:
    1. Student weakness/performance comes first.
    2. SPM chapter weightage is only a supporting exam-priority factor.
    3. Unattempted topics receive cold-start support, but should not always outrank proven weak topics.
    4. Mastered topics are reduced unless there are no weaker topics available.
    """
    scored = []

    for topic in topic_rows:
        attempts = safe_int(topic.get("attempts"))
        accuracy = safe_float(topic.get("accuracy"))
        score_ratio = safe_float(topic.get("score_ratio_percent"), accuracy)
        recent_accuracy = safe_float(topic.get("recent_accuracy"), accuracy)
        recent_score_ratio = safe_float(topic.get("recent_score_ratio_percent"), score_ratio)

        weightage = safe_float(topic.get("spm_weightage_percentage"))
        mistakes = safe_int(topic.get("mistakes"))
        gap_days = days_since(topic.get("last_practiced_at"))

        # -------------------------------------------------
        # 1. Personal weakness component
        # -------------------------------------------------
        # Use both accuracy and score ratio.
        # Accuracy is useful for Kertas 1 / correct-wrong attempts.
        # Score ratio is useful for Kertas 2 partial marks.
        if attempts > 0:
            accuracy_weakness = 100 - accuracy
            score_ratio_weakness = 100 - score_ratio

            weakness_component = (
                accuracy_weakness * 0.55
                + score_ratio_weakness * 0.45
            )
        else:
            # No personal evidence yet.
            # Do not treat it as fully weak.
            weakness_component = 45

        # -------------------------------------------------
        # 2. Recent weakness component
        # -------------------------------------------------
        if topic.get("recent_attempts", 0) > 0:
            recent_component = (
                (100 - recent_accuracy) * 0.5
                + (100 - recent_score_ratio) * 0.5
            )
        else:
            recent_component = 0

        # -------------------------------------------------
        # 3. Mistake component
        # -------------------------------------------------
        mistake_component = min(mistakes, 10) * 2.2

        # -------------------------------------------------
        # 4. Recency component
        # -------------------------------------------------
        # Long gap increases priority, but it should not dominate weakness.
        if attempts > 0:
            recency_component = min(gap_days, 30) * 0.45
        else:
            recency_component = 0

        # -------------------------------------------------
        # 5. Exam weightage component
        # -------------------------------------------------
        # Weightage is supporting only.
        # It has slightly more effect for unattempted topics.
        if attempts == 0:
            weightage_component = min(weightage, 12) * 1.2
        else:
            weightage_component = min(weightage, 12) * 0.8

        # -------------------------------------------------
        # 6. Practice evidence component
        # -------------------------------------------------
        # Enough attempts means the weakness evidence is more trustworthy.
        evidence_component = min(attempts, 8) * 1.5

        # -------------------------------------------------
        # 7. Cold-start component
        # -------------------------------------------------
        if attempts == 0:
            cold_start_component = 12
        elif attempts < 3:
            cold_start_component = 6
        else:
            cold_start_component = 0

        priority_score = (
            weakness_component * 0.45
            + recent_component * 0.15
            + mistake_component
            + recency_component
            + weightage_component
            + evidence_component
            + cold_start_component
        )

        # -------------------------------------------------
        # Guardrail: reduce mastered topics
        # -------------------------------------------------
        # If the student is already strong in this topic,
        # do not let weightage/recency push it too high.
        is_mastered = attempts >= 5 and accuracy >= 80 and score_ratio >= 80

        if is_mastered:
            priority_score *= 0.35

        # -------------------------------------------------
        # Priority category
        # -------------------------------------------------
        if attempts > 0 and (accuracy < 50 or score_ratio < 50):
            recommendation_type = "weakness"
        elif attempts == 0:
            recommendation_type = "coverage"
        elif is_mastered:
            recommendation_type = "maintenance"
        else:
            recommendation_type = "strengthening"

        scored.append(
            {
                "priority_score": priority_score,
                "topic": topic,
                "debug": {
                    "weakness_component": round(weakness_component, 2),
                    "recent_component": round(recent_component, 2),
                    "mistake_component": round(mistake_component, 2),
                    "recency_component": round(recency_component, 2),
                    "weightage_component": round(weightage_component, 2),
                    "evidence_component": round(evidence_component, 2),
                    "cold_start_component": round(cold_start_component, 2),
                    "is_mastered": is_mastered,
                    "recommendation_type": recommendation_type,
                },
            }
        )

    scored.sort(key=lambda item: item["priority_score"], reverse=True)

    recommendations = []

    for item in scored[:limit]:
        priority_score = item["priority_score"]
        topic = item["topic"]
        debug = item["debug"]

        attempts = safe_int(topic.get("attempts"))
        accuracy = safe_float(topic.get("accuracy"))
        score_ratio = safe_float(topic.get("score_ratio_percent"), accuracy)
        weightage = safe_float(topic.get("spm_weightage_percentage"))
        priority = get_priority_label(priority_score, lang)

        recommendation_type = debug["recommendation_type"]

        if is_bm(lang):
            if recommendation_type == "weakness":
                reason = (
                    f"Topik ini dicadangkan kerana prestasi anda masih lemah "
                    f"dengan ketepatan {round(accuracy, 1)}% dan skor latihan {round(score_ratio, 1)}%."
                )
                if weightage >= 7:
                    reason += f" Topik ini juga mempunyai keutamaan peperiksaan SPM yang tinggi, iaitu {round(weightage, 2)}%."
                action = "Fokus pada latihan asas dahulu, kemudian semak semula kesilapan anda."

            elif recommendation_type == "coverage":
                reason = (
                    f"Topik ini belum banyak dilatih. Keutamaan peperiksaannya ialah {round(weightage, 2)}%, "
                    "jadi topik ini sesuai dimasukkan dalam ulang kaji anda."
                )
                action = "Mulakan dengan beberapa soalan mudah untuk membina rekod prestasi."

            elif recommendation_type == "maintenance":
                reason = (
                    "Topik ini sudah agak kuat, tetapi masih boleh dibuat sebagai latihan penyelenggaraan."
                )
                action = "Buat latihan ringkas sekali-sekala untuk mengekalkan penguasaan."

            else:
                reason = (
                    f"Topik ini boleh diperkukuhkan lagi. Ketepatan semasa anda ialah {round(accuracy, 1)}%."
                )

                if weightage >= 7:
                    reason += f" Topik ini juga mempunyai keutamaan peperiksaan SPM yang tinggi, iaitu {round(weightage, 2)}%."
                action = "Buat latihan ringkas dan semak kesilapan terkini."
        else:
            if recommendation_type == "weakness":
                reason = (
                    f"This topic is recommended because your performance is still weak, "
                    f"with {round(accuracy, 1)}% accuracy and {round(score_ratio, 1)}% practice score."
                )
                if weightage >= 7:
                    reason += f" This topic also has high SPM exam priority at {round(weightage, 2)}%."
                action = "Focus on basic practice first, then review your mistakes."

            elif recommendation_type == "coverage":
                reason = (
                    f"This topic has not been practised much. Its exam priority is {round(weightage, 2)}%, "
                    "so it is useful to include in your revision."
                )
                action = "Start with a few easy questions to build your performance record."

            elif recommendation_type == "maintenance":
                reason = (
                    "This topic is already quite strong, but it can still be used for maintenance practice."
                )
                action = "Do a short review occasionally to maintain your mastery."

            else:
                reason = (
                    f"This topic can be strengthened further. Your current accuracy is {round(accuracy, 1)}%."
                )

                if weightage >= 7:
                    reason += f" It also has high SPM exam priority at {round(weightage, 2)}%."
                action = "Do a short practice set and review your recent mistakes."

        recommendations.append(
            {
                "chapter_id": topic["chapter_id"],
                "topic": topic["name"],
                "name": topic["name"],
                "accuracy": round(accuracy, 2),
                "score_ratio_percent": round(score_ratio, 2),
                "attempts": attempts,
                "mistakes": safe_int(topic.get("mistakes")),
                "spm_weightage_percentage": round(weightage, 2),
                "exam_total_marks": safe_float(topic.get("exam_total_marks")),
                "exam_question_count": safe_int(topic.get("exam_question_count")),
                "priority": priority,
                "priority_score": round(priority_score, 2),
                "recommendation_type": recommendation_type,
                "reason": reason,
                "action": action,
            }
        )

    return recommendations


def build_performance_trend(cursor, student_id):
    cursor.execute(
        """
        SELECT *
        FROM (
            SELECT
                DATE(start_time) AS practice_date,
                ROUND(
                    COALESCE(
                        SUM(correct_count) / NULLIF(SUM(total_questions_answered), 0) * 100,
                        AVG(accuracy_snapshot)
                    ),
                    2
                ) AS accuracy,
                COUNT(*) AS sessions_that_day,
                SUM(total_questions_answered) AS questions_that_day
            FROM practice_sessions
            WHERE user_id = %s
            AND total_questions_answered > 0
            GROUP BY DATE(start_time)
            ORDER BY practice_date DESC
            LIMIT 14
        ) recent_days
        ORDER BY practice_date ASC
        """,
        (student_id,),
    )

    rows = cursor.fetchall() or []
    points = []

    for row in rows:
        practice_date = row.get("practice_date")

        if isinstance(practice_date, (datetime, date)):
            label = practice_date.strftime("%d %b")
        else:
            label = str(practice_date or "")

        points.append(
            {
                "label": label,
                "accuracy": round(safe_float(row.get("accuracy")), 2),
                "sessions": safe_int(row.get("sessions_that_day")),
                "questions": safe_int(row.get("questions_that_day")),
            }
        )

    if len(points) >= 4:
        split_index = len(points) // 2

        earlier_points = points[:split_index]
        recent_points = points[split_index:]

        earlier_avg = sum(point["accuracy"] for point in earlier_points) / len(earlier_points)
        recent_avg = sum(point["accuracy"] for point in recent_points) / len(recent_points)

        trend_change = recent_avg - earlier_avg

        if trend_change >= 5:
            trend_direction = "up"
        elif trend_change <= -5:
            trend_direction = "down"
        else:
            trend_direction = "stable"

    elif len(points) >= 2:
        first = points[0]["accuracy"]
        last = points[-1]["accuracy"]
        trend_change = last - first

        if trend_change >= 5:
            trend_direction = "up"
        elif trend_change <= -5:
            trend_direction = "down"
        else:
            trend_direction = "stable"

    else:
        trend_direction = "stable"
        trend_change = 0

    return {
        "points": points,
        "trend_direction": trend_direction,
        "trend_change": round(trend_change, 2),
    }


def build_study_pattern(
    session_summary,
    performance=None,
    lang="english",
    pattern_model=None,
    pattern_scaler=None,
    pattern_persona_map=None,
):
    performance = performance or {}
    pattern_persona_map = pattern_persona_map or {}

    total_sessions = session_summary["total_sessions"]
    sessions_last_7_days = session_summary["sessions_last_7_days"]
    active_days_this_week = session_summary["active_days_this_week"]
    total_time = format_duration_hm(session_summary["total_study_seconds"], lang)
    consistency_score = calculate_consistency_score(session_summary)

    model_persona = predict_study_persona_from_model(
        pattern_model=pattern_model,
        pattern_scaler=pattern_scaler,
        pattern_persona_map=pattern_persona_map,
        performance=performance,
        session_summary=session_summary,
    )

    # 1. Decide persona key
    if total_sessions == 0:
        persona_key = "Fresh Starter"

    elif model_persona:
        raw_persona_key = normalize_persona_name(model_persona)

        persona_key = refine_study_persona_key(
            persona_key=raw_persona_key,
            session_summary=session_summary,
            performance=performance,
        )

    else:
        # Rule-based fallback if model cannot be used
        if sessions_last_7_days >= 4 and active_days_this_week >= 3:
            persona_key = "Consistent Climber"

        elif sessions_last_7_days >= 4 and active_days_this_week <= 2:
            persona_key = "Deep Focus Learner"

        elif session_summary.get("weekend_session_ratio", 0) >= 0.5 and total_sessions >= 4:
            persona_key = "Weekend Learner"

        elif sessions_last_7_days <= 1:
            persona_key = "Fresh Starter"

        else:
            persona_key = "Flexible Learner"

    persona_key = refine_study_persona_key(
        persona_key=persona_key,
        session_summary=session_summary,
        performance=performance,
    )

    # 2. Convert persona/proof/suggestion into selected language.
    persona_content = get_study_persona_content(
        persona=persona_key,
        lang=lang,
        sessions_last_7_days=sessions_last_7_days,
        active_days_this_week=active_days_this_week,
    )

    return {
        "persona": persona_content["display"],
        "persona_key": persona_key,
        "proof": persona_content["proof"],
        "suggestion": persona_content["suggestion"],
        "total_time": total_time,
        "consistency_score": consistency_score,
    }

def build_study_schedule(session_summary, recommendations, lang="english", study_pattern=None):
    consistency_score = calculate_consistency_score(session_summary)

    raw_best_hour = (
        session_summary.get("preferred_start_hour")
        or session_summary.get("avg_start_hour")
        or 20
    )

    raw_best_hour = safe_int(raw_best_hour, 20)

    # Only suggest reasonable study hours: 6:00 AM to 10:00 PM.
    # If student mostly practises too late/too early, fall back to 8:00 PM.
    if 6 <= raw_best_hour <= 22:
        best_hour = raw_best_hour
    else:
        best_hour = 20

    study_pattern = study_pattern or {}
    persona_key = normalize_persona_name(
        study_pattern.get("persona_key") or study_pattern.get("persona") or "Flexible Learner"
    )

    # Persona-aware schedule adjustment.
    if persona_key == "Consistent Climber":
        weekly_target = 4 if consistency_score >= 50 else 3
        session_length_minutes = 25 if consistency_score >= 70 else 20

        schedule_reason = (
            "Jadual ini mengekalkan rutin konsisten anda dengan sasaran mingguan yang sesuai."
            if is_bm(lang)
            else "This schedule maintains your consistent routine with a suitable weekly target."
        )

    elif persona_key == "Deep Focus Learner":
        weekly_target = 3
        session_length_minutes = 25

        schedule_reason = (
            "Jadual ini mengekalkan sesi fokus anda, tetapi membantu menyebarkan latihan dengan lebih teratur."
            if is_bm(lang)
            else "This schedule keeps your focused sessions while helping you spread practice more regularly."
        )

    elif persona_key == "Weekend Learner":
        weekly_target = 3
        session_length_minutes = 20

        schedule_reason = (
            "Jadual ini mengekalkan rutin hujung minggu anda dan menggalakkan satu sesi pendek pada hari biasa."
            if is_bm(lang)
            else "This schedule keeps your weekend routine while encouraging one short weekday session."
        )

    elif persona_key == "Fresh Starter":
        weekly_target = 3
        session_length_minutes = 15

        schedule_reason = (
            "Jadual ini bermula dengan sesi pendek supaya anda boleh membina tabiat belajar secara perlahan."
            if is_bm(lang)
            else "This schedule starts with short sessions so you can gradually build a study habit."
        )

    else:
        weekly_target = 3
        session_length_minutes = 20 if consistency_score >= 40 else 15

        schedule_reason = (
            "Jadual ini membantu menjadikan corak ulang kaji anda lebih konsisten."
            if is_bm(lang)
            else "This schedule helps make your revision pattern more consistent."
        )

    actual_completed = session_summary["sessions_last_7_days"]
    completed = min(actual_completed, weekly_target)
    focus_topic = recommendations[0]["topic"] if recommendations else (
        "Topik ulang kaji" if is_bm(lang) else "Revision topic"
    )
    chapter_id = recommendations[0]["chapter_id"] if recommendations else None

    if is_bm(lang):
        pattern_type = "Jadual Ulang Kaji Dicadangkan"
        length_label = f"{session_length_minutes} minit"
        progress_label = f"{completed}/{weekly_target} sesi minggu ini"
    else:
        pattern_type = "Suggested Revision Schedule"
        length_label = f"{session_length_minutes} minutes"
        progress_label = f"{completed}/{weekly_target} sessions this week"

    return {
        "pattern_type": pattern_type,
        "persona_key_used": persona_key,
        "schedule_reason": schedule_reason,
        "best_time_window": format_hour_window(best_hour, session_length_minutes),
        "recommended_session_length_label": length_label,
        "weekly_target_sessions": weekly_target,
        "weekly_progress": {
            "completed": completed,
            "actual_completed": actual_completed,
            "target": weekly_target,
            "label": progress_label,
        },
        "next_suggested_session": {
            "label": get_next_session_label(best_hour, lang),
            "time_window": format_hour_window(best_hour, session_length_minutes),
            "focus_topic": focus_topic,
            "chapter_id": chapter_id,
        },
    }


def build_consistency(session_summary, lang="english", weekly_target_override=None):
    consistency_score = calculate_consistency_score(session_summary)

    if weekly_target_override is not None:
        target = safe_int(weekly_target_override, 3)
    else:
        target = 4 if consistency_score >= 70 else 3

    actual_completed = session_summary["sessions_last_7_days"]
    completed = min(actual_completed, target)

    label = (
        f"{completed}/{target} sesi minggu ini"
        if is_bm(lang)
        else f"{completed}/{target} sessions this week"
    )

    return {
        "weekly_target_sessions": target,
        "weekly_completed_sessions": completed,
        "weekly_actual_sessions": actual_completed,
        "weekly_progress_label": label,
        "consistency_score": consistency_score,
    }


def build_study_heatmap(cursor, student_id, year):
    year = safe_int(year, datetime.now().year)

    cursor.execute(
        """
        SELECT
            DATE(start_time) AS study_date,
            SUM(GREATEST(IFNULL(duration_seconds, 0), 0)) AS total_seconds
        FROM practice_sessions
        WHERE user_id = %s
          AND YEAR(start_time) = %s
        GROUP BY DATE(start_time)
        """,
        (student_id, year),
    )

    rows = cursor.fetchall() or {}
    by_date = {}

    for row in rows:
        study_date = row.get("study_date")

        if isinstance(study_date, datetime):
            key = study_date.date().isoformat()
        elif isinstance(study_date, date):
            key = study_date.isoformat()
        else:
            key = str(study_date)

        minutes = safe_int(row.get("total_seconds")) // 60
        by_date[key] = minutes

    start_date = date(year, 1, 1)
    end_date = date(year, 12, 31)

    cells = []
    active_days = 0
    best_minutes = 0

    current = start_date
    while current <= end_date:
        key = current.isoformat()
        minutes = by_date.get(key, 0)
        best_minutes = max(best_minutes, minutes)

        if minutes > 0:
            active_days += 1

        if minutes >= 60:
            intensity = 4
        elif minutes >= 30:
            intensity = 3
        elif minutes >= 10:
            intensity = 2
        elif minutes > 0:
            intensity = 1
        else:
            intensity = 0

        cells.append(
            {
                "date": key,
                "minutes": minutes,
                "intensity": intensity,
            }
        )

        current += timedelta(days=1)

    return {
        "cells": cells,
        "active_days": active_days,
        "best_minutes": best_minutes,
    }


def build_ai_overview(prediction, recommendations, topic_summary, performance, lang="english"):
    if is_bm(lang):
        if topic_summary["strong_topic_count"] > 0:
            strength = f"Anda mempunyai {topic_summary['strong_topic_count']} topik yang kuat. Teruskan latihan untuk mengekalkan prestasi."
        else:
            strength = "Teruskan membuat latihan supaya sistem dapat mengenal pasti kekuatan anda."

        if recommendations:
            concern = f"Topik utama untuk diberi perhatian ialah {recommendations[0]['topic']}."
        else:
            concern = "Lengkapkan lebih banyak latihan untuk mendapatkan cadangan topik yang lebih tepat."
    else:
        if topic_summary["strong_topic_count"] > 0:
            strength = f"You have {topic_summary['strong_topic_count']} strong topic(s). Keep practising to maintain your performance."
        else:
            strength = "Continue practising so the system can identify your strengths."

        if recommendations:
            concern = f"Your main revision focus should be {recommendations[0]['topic']}."
        else:
            concern = "Complete more practice to unlock more accurate topic recommendations."

    grade = prediction.get("grade", "--")
    score = prediction.get("score", None)
    confidence = prediction.get("confidence", 0)
    reason = prediction.get("reason") or ""

    if score is not None:
        score_text = f"{round(safe_float(score))}/100"
    else:
        score_text = "--"

    if is_bm(lang):
        prediction_summary = (
            f"Gred ramalan anda ialah {grade} dengan skor anggaran {score_text} "
            f"dan tahap keyakinan {confidence}%. {reason}"
        )
    else:
        prediction_summary = (
            f"Your predicted grade is {grade} with an estimated score of {score_text} "
            f"and {confidence}% confidence. {reason}"
        )

    return {
        "strength": strength,
        "concern": concern,
        "prediction_reason": prediction_summary,
    }

def build_dashboard_intelligence(
    cursor,
    student_id,
    lang="english",
    year=None,
    grade_model=None,
    pattern_model=None,
    pattern_scaler=None,
    pattern_persona_map=None,
):
    """
    Main function to call from /api/student/dashboard/<student_id>.

    It returns the same high-level keys your StudentDashboard.js already expects,
    but with richer model-ready fields.
    """

    selected_year = safe_int(year, datetime.now().year)

    performance = fetch_overall_performance(cursor, student_id)
    session_summary = fetch_session_summary(cursor, student_id)
    topic_rows = fetch_topic_performance(cursor, student_id, lang)
    topic_summary = calculate_topic_summary(topic_rows)
    features = build_feature_vector(performance, session_summary, topic_summary)

    prediction = predict_grade_with_status(grade_model, features, lang)
    recommendations = build_topic_recommendations(topic_rows, lang, limit=3)
    study_pattern = build_study_pattern(
        session_summary=session_summary,
        performance=performance,
        lang=lang,
        pattern_model=pattern_model,
        pattern_scaler=pattern_scaler,
        pattern_persona_map=pattern_persona_map,
    )
    study_schedule = build_study_schedule(
        session_summary=session_summary,
        recommendations=recommendations,
        lang=lang,
        study_pattern=study_pattern,
    )
    consistency = build_consistency(
        session_summary=session_summary,
        lang=lang,
        weekly_target_override=study_schedule.get("weekly_target_sessions"),
    )

    dashboard = {
        "kpis": {
            "predicted_grade": prediction,
            "practice_accuracy": {
                "accuracy": round(performance["overall_accuracy"], 2),
                "recent_accuracy": round(performance["recent_accuracy"], 2),
            },
            "total_questions_attempted": {
                "total": performance["total_attempts"],
                "paper1": performance["paper1_attempts"],
                "paper2": performance["paper2_attempts"],
            },
            "total_study_time": {
                "total": format_duration_hm(session_summary["total_study_seconds"], lang),
                "this_week_delta": format_week_delta(
                    session_summary["study_seconds_this_week"]
                    - session_summary["study_seconds_previous_week"],
                    lang,
                ),
            },
            "last_updated_at": datetime.now().isoformat(timespec="seconds"),
        },
        "ai_overview": build_ai_overview(
            prediction,
            recommendations,
            topic_summary,
            performance,
            lang,
        ),
        "topic_recommendations": recommendations,
        "topic_mastery": build_topic_mastery(topic_rows, lang),
        "performance_trend": build_performance_trend(cursor, student_id),
        "study_pattern": study_pattern,
        "study_schedule": study_schedule,
        "consistency": consistency,
        "study_heatmap": build_study_heatmap(cursor, student_id, selected_year),
        "debug_features": features,
    }

    return dashboard