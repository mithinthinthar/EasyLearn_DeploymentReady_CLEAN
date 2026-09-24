import os
import json
from pathlib import Path
from datetime import datetime

import joblib
import numpy as np
import pandas as pd

from sklearn.cluster import KMeans
from sklearn.metrics import (
    silhouette_score,
    davies_bouldin_score,
    calinski_harabasz_score,
)
from sklearn.preprocessing import StandardScaler

from config import get_db_connection


# =========================================================
# Paths and settings
# =========================================================

MODEL_DIR = Path("models")
MODEL_PATH = MODEL_DIR / "study_pattern_model.pkl"
METRICS_PATH = MODEL_DIR / "study_pattern_metrics.json"

# training source is database
DATA_SOURCE = os.environ.get("STUDY_PATTERN_DATA_SOURCE", "db").lower().strip()

CSV_PATH = os.environ.get(
    "STUDY_PATTERN_CSV_PATH",
    "../model_refinement/synthetic_exports/synthetic_study_pattern_features.csv",
)

PERSONA_COUNT = 5
RANDOM_STATE = 42
MIN_ROWS_REQUIRED = 100


# =========================================================
# Final student-facing personas
# =========================================================

PERSONA_DESCRIPTIONS = {
    "Consistent Climber": {
        "meaning": "Practises regularly across different days.",
        "suggestion": "Keep your routine and continue strengthening weaker topics.",
    },
    "Deep Focus Learner": {
        "meaning": "Prefers longer or more concentrated practice sessions.",
        "suggestion": "Your focus is useful, but try spreading some practice across more days for better memory.",
    },
    "Weekend Learner": {
        "meaning": "Usually practises more during weekends.",
        "suggestion": "Weekend study works well, but adding one short weekday session can improve consistency.",
    },
    "Fresh Starter": {
        "meaning": "Has just started or has limited practice data so far.",
        "suggestion": "Start with a few short sessions so EasyLearn can understand your learning pattern better.",
    },
    "Flexible Learner": {
        "meaning": "Has a moderate or mixed study pattern without one strong habit yet.",
        "suggestion": "Try setting a simple weekly target to make your revision more predictable.",
    },
}


# Must match dashboard_intelligence.py
FEATURE_COLUMNS = [
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


RAW_NUMERIC_COLUMNS = [
    "total_sessions",
    "total_questions",
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
]


# =========================================================
# Utility functions
# =========================================================

def safe_float(value, default=0.0):
    try:
        if value is None:
            return default
        return float(value)
    except Exception:
        return default


def safe_int(value, default=0):
    try:
        if value is None:
            return default
        return int(value)
    except Exception:
        return default


def rank_series(series, ascending=True):
    return series.rank(ascending=ascending, method="dense")


# =========================================================
# Data loading
# =========================================================

def fetch_study_pattern_dataset_from_db():
    """
    Fetches study behaviour data from MySQL.

    One row = one student.
    Features are built from practice_sessions and attempts.
    """
    conn = None
    cursor = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        query = """
            SELECT
                u.id AS user_id,

                COALESCE(s.total_sessions, 0) AS total_sessions,
                COALESCE(a.total_questions, 0) AS total_questions,
                COALESCE(a.avg_time_per_question, 0) AS avg_time_per_question,

                COALESCE(s.active_days, 0) AS active_days,
                COALESCE(s.sessions_last_7_days, 0) AS sessions_last_7_days,
                COALESCE(s.active_days_last_7_days, 0) AS active_days_last_7_days,

                COALESCE(s.sessions_previous_7_days, 0) AS sessions_previous_7_days,
                COALESCE(s.study_minutes_last_7_days, 0) AS study_minutes_last_7_days,
                COALESCE(s.study_minutes_previous_7_days, 0) AS study_minutes_previous_7_days,

                COALESCE(s.total_study_minutes, 0) AS total_study_minutes,
                COALESCE(s.avg_session_minutes, 0) AS avg_session_minutes,
                COALESCE(s.max_streak, 0) AS max_streak,

                COALESCE(s.evening_session_ratio, 0) AS evening_session_ratio,
                COALESCE(s.weekend_session_ratio, 0) AS weekend_session_ratio

            FROM users u

            LEFT JOIN (
                SELECT
                    user_id,

                    COUNT(*) AS total_sessions,
                    COUNT(DISTINCT DATE(start_time)) AS active_days,

                    SUM(IFNULL(duration_seconds, 0)) / 60 AS total_study_minutes,
                    AVG(IFNULL(duration_seconds, 0)) / 60 AS avg_session_minutes,
                    MAX(IFNULL(highest_streak, 0)) AS max_streak,

                    SUM(
                        CASE
                            WHEN start_time >= DATE_SUB(NOW(), INTERVAL 7 DAY)
                            THEN 1 ELSE 0
                        END
                    ) AS sessions_last_7_days,

                    COUNT(
                        DISTINCT CASE
                            WHEN start_time >= DATE_SUB(NOW(), INTERVAL 7 DAY)
                            THEN DATE(start_time)
                        END
                    ) AS active_days_last_7_days,

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
                            THEN IFNULL(duration_seconds, 0) ELSE 0
                        END
                    ) / 60 AS study_minutes_last_7_days,

                    SUM(
                        CASE
                            WHEN start_time >= DATE_SUB(NOW(), INTERVAL 14 DAY)
                             AND start_time < DATE_SUB(NOW(), INTERVAL 7 DAY)
                            THEN IFNULL(duration_seconds, 0) ELSE 0
                        END
                    ) / 60 AS study_minutes_previous_7_days,

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
                GROUP BY user_id
            ) s ON s.user_id = u.id

            LEFT JOIN (
                SELECT
                    user_id,
                    COUNT(*) AS total_questions,
                    AVG(IFNULL(time_taken_seconds, 0)) AS avg_time_per_question
                FROM attempts
                GROUP BY user_id
            ) a ON a.user_id = u.id

            WHERE u.role = 'student'
              AND COALESCE(s.total_sessions, 0) > 0
        """

        cursor.execute(query)
        rows = cursor.fetchall() or []

        if not rows:
            return pd.DataFrame()

        return pd.DataFrame(rows)

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def fetch_study_pattern_dataset_from_csv(csv_path):
    """
    Optional CSV mode.

    This is useful for checking or reproducing training from exported data.
    DB mode is still recommended for final dashboard-aligned training.
    """
    path = Path(csv_path)

    if not path.exists():
        raise FileNotFoundError(f"CSV file not found: {path}")

    df = pd.read_csv(path)

    if df.empty:
        raise RuntimeError(f"CSV file is empty: {path}")

    return df


def load_training_dataset():
    if DATA_SOURCE == "csv":
        print(f"Loading study behaviour data from CSV: {CSV_PATH}")
        df = fetch_study_pattern_dataset_from_csv(CSV_PATH)
    else:
        print("Fetching study behaviour data from database...")
        df = fetch_study_pattern_dataset_from_db()

    if df.empty:
        raise RuntimeError(
            "No study pattern data found. Generate synthetic practice_sessions first."
        )

    return df


# =========================================================
# Feature preparation
# =========================================================

def prepare_features(df):
    df = df.copy()

    for column in RAW_NUMERIC_COLUMNS:
        if column not in df.columns:
            df[column] = 0

        df[column] = pd.to_numeric(df[column], errors="coerce").fillna(0)

    # Derived feature 1: average question volume per session
    df["questions_per_session"] = np.where(
        df["total_sessions"] > 0,
        df["total_questions"] / df["total_sessions"],
        0,
    )

    # Derived feature 2: spread of practice across days
    df["active_day_ratio"] = np.where(
        df["total_sessions"] > 0,
        df["active_days"] / df["total_sessions"],
        0,
    )

    # Derived feature 3: recent spread of practice
    df["recent_active_day_ratio"] = np.where(
        df["sessions_last_7_days"] > 0,
        df["active_days_last_7_days"] / df["sessions_last_7_days"],
        0,
    )

    # Derived feature 4: recent session growth compared to previous week
    df["session_growth_ratio"] = np.where(
        df["sessions_previous_7_days"] > 0,
        (df["sessions_last_7_days"] - df["sessions_previous_7_days"])
        / df["sessions_previous_7_days"],
        df["sessions_last_7_days"],
    )

    df.replace([np.inf, -np.inf], 0, inplace=True)
    df.fillna(0, inplace=True)

    # Clip ratio features to reduce extreme outlier impact.
    ratio_columns = [
        "evening_session_ratio",
        "weekend_session_ratio",
        "active_day_ratio",
        "recent_active_day_ratio",
    ]

    for column in ratio_columns:
        df[column] = df[column].clip(lower=0, upper=1)

    # Session growth can be negative or positive, but avoid extreme values dominating clustering.
    df["session_growth_ratio"] = df["session_growth_ratio"].clip(lower=-1, upper=10)

    for column in FEATURE_COLUMNS:
        if column not in df.columns:
            df[column] = 0

        df[column] = pd.to_numeric(df[column], errors="coerce").fillna(0)

    X = df[FEATURE_COLUMNS].copy()

    return X, df


# =========================================================
# Persona mapping
# =========================================================

def build_persona_map(cluster_centers):
    """
    Assign 5 student-friendly personas to K-Means clusters.

    The assignment is rule-based after clustering.
    This keeps K-Means unsupervised but makes cluster names understandable.
    """
    centers = cluster_centers.copy()

    centers["fresh_starter_score"] = (
        rank_series(centers["total_sessions"], ascending=True)
        + rank_series(centers["total_questions"], ascending=True)
        + rank_series(centers["total_study_minutes"], ascending=True)
        + rank_series(centers["active_days"], ascending=True)
    )

    centers["consistent_climber_score"] = (
        rank_series(centers["active_days"], ascending=False)
        + rank_series(centers["total_sessions"], ascending=False)
        + rank_series(centers["max_streak"], ascending=False)
        + rank_series(centers["active_day_ratio"], ascending=False)
        + rank_series(centers["recent_active_day_ratio"], ascending=False)
    )

    centers["deep_focus_score"] = (
        rank_series(centers["questions_per_session"], ascending=False)
        + rank_series(centers["avg_session_minutes"], ascending=False)
        + rank_series(centers["active_day_ratio"], ascending=True)
        + rank_series(centers["recent_active_day_ratio"], ascending=True)
    )

    centers["weekend_learner_score"] = (
        rank_series(centers["weekend_session_ratio"], ascending=False)
        + rank_series(centers["total_questions"], ascending=False)
    )

    assigned = {}
    used_clusters = set()

    def assign_persona(score_column, persona_name):
        available = centers[~centers["cluster_id"].isin(used_clusters)]

        if available.empty:
            return

        selected = available.sort_values(score_column, ascending=True).iloc[0]
        cluster_id = int(selected["cluster_id"])

        assigned[cluster_id] = persona_name
        used_clusters.add(cluster_id)

    assign_persona("fresh_starter_score", "Fresh Starter")
    assign_persona("consistent_climber_score", "Consistent Climber")
    assign_persona("deep_focus_score", "Deep Focus Learner")
    assign_persona("weekend_learner_score", "Weekend Learner")

    remaining = centers[~centers["cluster_id"].isin(used_clusters)]

    for _, row in remaining.iterrows():
        assigned[int(row["cluster_id"])] = "Flexible Learner"

    return assigned, centers


# =========================================================
# Evaluation helpers
# =========================================================

def evaluate_clustering(X_scaled, labels):
    unique_labels = set(labels)

    if len(unique_labels) <= 1:
        return {
            "silhouette_score": -1,
            "davies_bouldin_score": -1,
            "calinski_harabasz_score": -1,
        }

    return {
        "silhouette_score": round(float(silhouette_score(X_scaled, labels)), 4),
        "davies_bouldin_score": round(float(davies_bouldin_score(X_scaled, labels)), 4),
        "calinski_harabasz_score": round(float(calinski_harabasz_score(X_scaled, labels)), 4),
    }


def train_candidate_kmeans(X_scaled, k):
    model = KMeans(
        n_clusters=k,
        random_state=RANDOM_STATE,
        n_init=20,
    )

    labels = model.fit_predict(X_scaled)
    scores = evaluate_clustering(X_scaled, labels)

    return model, labels, scores


# =========================================================
# Main training
# =========================================================

def train_study_pattern_model():
    raw_df = load_training_dataset()

    X, prepared_df = prepare_features(raw_df)

    if len(prepared_df) < MIN_ROWS_REQUIRED:
        raise RuntimeError(
            f"Not enough study pattern data. Rows found: {len(prepared_df)}. "
            f"Recommended: at least {MIN_ROWS_REQUIRED} student profiles for clustering."
        )

    print(f"Study pattern rows: {len(prepared_df)}")
    print(f"Training source: {DATA_SOURCE}")
    print("Scaling features...")

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    print("Training and comparing K-Means models...")

    candidate_results = []
    candidate_range = [3, 4, 5, 6, 7]

    selected_model = None
    selected_labels = None
    selected_scores = None

    for k in candidate_range:
        candidate_model, candidate_labels, candidate_scores = train_candidate_kmeans(
            X_scaled,
            k,
        )

        candidate_result = {
            "k": k,
            "silhouette_score": candidate_scores["silhouette_score"],
            "davies_bouldin_score": candidate_scores["davies_bouldin_score"],
            "calinski_harabasz_score": candidate_scores["calinski_harabasz_score"],
            "selected_for_dashboard": k == PERSONA_COUNT,
        }

        candidate_results.append(candidate_result)

        print(
            f" - K={k}: "
            f"silhouette={candidate_scores['silhouette_score']:.4f}, "
            f"davies_bouldin={candidate_scores['davies_bouldin_score']:.4f}, "
            f"calinski_harabasz={candidate_scores['calinski_harabasz_score']:.4f}"
            f"{'selected for dashboard personas' if k == PERSONA_COUNT else ''}"
        )

        if k == PERSONA_COUNT:
            selected_model = candidate_model
            selected_labels = candidate_labels
            selected_scores = candidate_scores

    if selected_model is None:
        raise RuntimeError("Selected K-Means model was not created.")

    prepared_df["cluster"] = selected_labels

    cluster_centers = pd.DataFrame(
        scaler.inverse_transform(selected_model.cluster_centers_),
        columns=FEATURE_COLUMNS,
    )
    cluster_centers["cluster_id"] = cluster_centers.index

    persona_map, scored_centers = build_persona_map(cluster_centers)

    cluster_distribution = {
        str(int(cluster_id)): int(count)
        for cluster_id, count in prepared_df["cluster"].value_counts().sort_index().items()
    }

    center_records = []

    for _, row in cluster_centers.iterrows():
        cluster_id = int(row["cluster_id"])

        record = {
            "cluster_id": cluster_id,
            "persona": persona_map.get(cluster_id, "Flexible Learner"),
        }

        for column in FEATURE_COLUMNS:
            record[column] = round(float(row[column]), 4)

        center_records.append(record)

    source_persona_distribution = None

    if "persona" in prepared_df.columns:
        source_persona_distribution = {
            str(k): int(v)
            for k, v in prepared_df["persona"].value_counts().items()
        }

    metrics = {
        "trained_at": datetime.now().isoformat(timespec="seconds"),
        "data_source": DATA_SOURCE,
        "csv_path": CSV_PATH if DATA_SOURCE == "csv" else None,
        "model_type": "KMeans",
        "selected_k": PERSONA_COUNT,
        "selection_reason": (
            "K=5 is intentionally selected to support five interpretable "
            "student-facing study pattern personas in the dashboard."
        ),
        "silhouette_score": selected_scores["silhouette_score"],
        "davies_bouldin_score": selected_scores["davies_bouldin_score"],
        "calinski_harabasz_score": selected_scores["calinski_harabasz_score"],
        "candidate_results": candidate_results,
        "total_rows": int(len(prepared_df)),
        "feature_columns": FEATURE_COLUMNS,
        "cluster_distribution": cluster_distribution,
        "source_persona_distribution": source_persona_distribution,
        "persona_map": {
            str(k): v for k, v in persona_map.items()
        },
        "persona_descriptions": PERSONA_DESCRIPTIONS,
        "cluster_centers": center_records,
        "note": (
            "The study pattern model applies time-based behavioural analysis and "
            "K-Means clustering. Temporal features such as recent sessions, previous-week "
            "sessions, study-minute changes, active-day ratio, evening study ratio, and "
            "weekend study ratio are extracted from practice logs. These features are "
            "scaled using StandardScaler and clustered using K-Means to identify "
            "interpretable learner patterns."
        ),
    }

    MODEL_DIR.mkdir(parents=True, exist_ok=True)

    joblib.dump(
        {
            "model": selected_model,
            "scaler": scaler,
            "persona_map": persona_map,
            "feature_columns": FEATURE_COLUMNS,
            "persona_descriptions": PERSONA_DESCRIPTIONS,
            "cluster_centers": center_records,
            "metrics_summary": {
                "selected_k": PERSONA_COUNT,
                "silhouette_score": selected_scores["silhouette_score"],
                "davies_bouldin_score": selected_scores["davies_bouldin_score"],
                "calinski_harabasz_score": selected_scores["calinski_harabasz_score"],
            },
        },
        MODEL_PATH,
    )

    with open(METRICS_PATH, "w", encoding="utf-8") as file:
        json.dump(metrics, file, indent=2)

    print("\n==================================================")
    print("Success: Study Pattern AI trained successfully!")
    print(f"Model saved to: {MODEL_PATH}")
    print(f"Metrics saved to: {METRICS_PATH}")
    print(f"Selected K: {PERSONA_COUNT}")
    print(f"Silhouette score: {selected_scores['silhouette_score']:.4f}")
    print(f"Davies-Bouldin score: {selected_scores['davies_bouldin_score']:.4f}")
    print(f"Calinski-Harabasz score: {selected_scores['calinski_harabasz_score']:.4f}")
    print("Persona map:")

    for cluster_id, persona in sorted(persona_map.items()):
        print(f" - Cluster {cluster_id}: {persona}")

    print("\nCluster distribution:")
    for cluster_id, count in cluster_distribution.items():
        persona = persona_map.get(int(cluster_id), "Flexible Learner")
        print(f" - Cluster {cluster_id} ({persona}): {count} students")


if __name__ == "__main__":
    train_study_pattern_model()