"""
generate_synthetic_learning_data.py

Purpose:
- Generate realistic synthetic EasyLearn student learning data.
- Write synthetic data directly into MySQL.
- Export CSV datasets for model refinement / checking.

Main tables written:
- users
- practice_sessions
- attempts
- student_topic_mastery
- activity_logs

Main tables read:
- chapters
- questions
- papers

Important K2 logic:
- Same-chapter grouped K2 questions are treated as staged grouped flows.
- Mixed grouped K2 questions are separated by their actual verified chapter and are NOT locked
  as one cross-chapter group.

Run from backend folder:
    python model_refinement/generate_synthetic_learning_data.py --students 300 --reset-synthetic --export-csv

Dry run CSV only:
    python model_refinement/generate_synthetic_learning_data.py --students 50 --dry-run --export-csv
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
import random
import string
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta, date
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


# ---------------------------------------------------------
# Import backend config.py safely
# ---------------------------------------------------------

CURRENT_FILE = Path(__file__).resolve()
CURRENT_DIR = CURRENT_FILE.parent
BACKEND_DIR = CURRENT_DIR.parent

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

try:
    from config import get_db_connection
except Exception as exc:
    raise RuntimeError(
        "Could not import get_db_connection from backend/config.py. "
        "Place this file under backend/model_refinement/ and run from backend."
    ) from exc


# ---------------------------------------------------------
# Constants
# ---------------------------------------------------------

SYNTHETIC_EMAIL_DOMAIN = "mathsy.synthetic"
SYNTHETIC_EMAIL_PREFIX = "synthetic.student"
SYNTHETIC_FIREBASE_PREFIX = "synthetic_learning_"
SYNTHETIC_STUDENT_CODE_PREFIX = "STU-SYN"

GRADE_ORDER = ["G", "E", "D", "C", "C+", "B", "B+", "A-", "A", "A+"]

OUTPUT_DIR = BACKEND_DIR / "model_refinement" / "synthetic_exports"

DEVICE_TYPES = ["Desktop", "Laptop", "Mobile", "Tablet"]
LANGUAGES = ["english", "bm"]

PROFILE_TEMPLATES = [
    {
        "name": "Consistent Climber",
        "weight": 0.24,
        "ability_range": (0.58, 0.86),
        "sessions_range": (45, 80),
        "preferred_hours": [19, 20, 21],
        "active_weekdays": [0, 1, 2, 3, 4],
        "session_gap_bias": "regular",
    },
    {
        "name": "Flexible Learner",
        "weight": 0.22,
        "ability_range": (0.45, 0.78),
        "sessions_range": (28, 55),
        "preferred_hours": [16, 20, 21, 22],
        "active_weekdays": [0, 1, 2, 3, 4, 5, 6],
        "session_gap_bias": "irregular",
    },
    {
        "name": "Deep Focus Learner",
        "weight": 0.18,
        "ability_range": (0.48, 0.82),
        "sessions_range": (18, 38),
        "preferred_hours": [20, 21, 22],
        "active_weekdays": [1, 2, 3, 4, 5],
        "session_gap_bias": "long_sessions",
    },
    {
        "name": "Weekend Learner",
        "weight": 0.16,
        "ability_range": (0.42, 0.76),
        "sessions_range": (22, 48),
        "preferred_hours": [10, 11, 15, 16, 20],
        "active_weekdays": [5, 6],
        "session_gap_bias": "regular",
    },
    {
        "name": "Fresh Starter",
        "weight": 0.12,
        "ability_range": (0.30, 0.62),
        "sessions_range": (8, 24),
        "preferred_hours": [15, 20, 21],
        "active_weekdays": [0, 2, 5],
        "session_gap_bias": "low_activity",
    },
    {
        "name": "High Achiever",
        "weight": 0.08,
        "ability_range": (0.78, 0.96),
        "sessions_range": (50, 90),
        "preferred_hours": [18, 19, 20],
        "active_weekdays": [0, 1, 2, 3, 4, 5],
        "session_gap_bias": "regular",
    },
]

# ---------------------------------------------------------
# Synthetic target score construction
# ---------------------------------------------------------
# These weights are used only for constructing synthetic target labels because real student SPM results are unavailable.
# The target score is built from observable learning behaviour:
# - score_ratio_percent: actual marks gained during practice
# - avg_topic_mastery: topic-level mastery
# - study_consistency_score: learning consistency

TARGET_SCORE_RATIO_WEIGHT = 0.50
TARGET_TOPIC_MASTERY_WEIGHT = 0.35
TARGET_CONSISTENCY_WEIGHT = 0.15
TARGET_CURVE_MULTIPLIER = 1.15
TARGET_EXAM_NOISE_STD = 1.5
TARGET_NOISE_SEED_BASE = 20260512
TARGET_SPEED_PENALTY_WEIGHT = 0.50

# ---------------------------------------------------------
# Data classes
# ---------------------------------------------------------

@dataclass
class Chapter:
    id: int
    form: str
    chapter_no: str
    name_en: str
    name_bm: str
    weightage: float

    @property
    def label(self) -> str:
        return f"{self.chapter_no}: {self.name_en}"


@dataclass
class SyntheticStudentProfile:
    synthetic_index: int
    name: str
    email: str
    firebase_uid: str
    student_code: str
    language: str
    persona: str
    hidden_ability: float
    target_score: float
    target_grade: str
    weak_chapter_ids: List[int]
    strong_chapter_ids: List[int]
    preferred_paper_type: str
    created_user_id: Optional[int] = None


@dataclass
class PracticeUnit:
    unit_type: str  # k1_question, k2_stage, k2_group_chain
    chapter_id: int
    form: str
    chapter_label: str
    paper_type: str
    difficulty_level: int
    difficulty_label: str
    rows: List[Dict[str, Any]] = field(default_factory=list)
    stages: List["PracticeUnit"] = field(default_factory=list)
    group_id: Optional[str] = None
    exercise_stage_id: Optional[str] = None
    stage_index: int = 1
    is_mixed_group_split: bool = False


# ---------------------------------------------------------
# Basic helpers
# ---------------------------------------------------------

def norm(value: Any) -> str:
    return " ".join(str(value or "").strip().lower().split())


def safe_int(value: Any, default: int = 0) -> int:
    try:
        if value is None:
            return default
        return int(value)
    except Exception:
        return default


def safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except Exception:
        return default


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def random_token(length: int = 10) -> str:
    alphabet = string.ascii_letters + string.digits
    return "".join(random.choices(alphabet, k=length))


def score_to_grade(score: float) -> str:
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


def build_synthetic_target_score(
    synthetic_index: int,
    score_ratio_percent: float,
    avg_topic_mastery: float,
    study_consistency_score: float,
    avg_time_per_question: float, 
) -> float:
    """
    Build a synthetic final performance score from observable learning behaviour.

    This avoids using hidden_ability as the training label source.
    A small deterministic noise is added to simulate exam-day variation.
    """
    # 1. Calculate the base score
    base_score = (
        safe_float(score_ratio_percent) * TARGET_SCORE_RATIO_WEIGHT
        + safe_float(avg_topic_mastery) * TARGET_TOPIC_MASTERY_WEIGHT
        + safe_float(study_consistency_score) * TARGET_CONSISTENCY_WEIGHT
    )

    # 2. Calculate the speed penalty
    avg_time_minutes = safe_float(avg_time_per_question) / 60.0
    speed_penalty = avg_time_minutes * TARGET_SPEED_PENALTY_WEIGHT

    # 3. Apply the penalty to get the final raw score
    raw_score = base_score - speed_penalty

    curved_score = raw_score * TARGET_CURVE_MULTIPLIER

    # Deterministic per student, so repeated runs with same generated data are reproducible.
    rng = random.Random(TARGET_NOISE_SEED_BASE + safe_int(synthetic_index))
    exam_noise = rng.gauss(0, TARGET_EXAM_NOISE_STD)

    final_score = clamp(curved_score + exam_noise, 20, 98)

    return round(final_score, 2)

def difficulty_label_from_level(level: int) -> str:
    level = safe_int(level, 3)
    if level <= 2:
        return "Easy"
    if level == 3:
        return "Moderate"
    return "Hard"


def parse_json_maybe(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, (dict, list)):
        return value
    if isinstance(value, bytes):
        value = value.decode("utf-8")
    if isinstance(value, str):
        try:
            return json.loads(value)
        except Exception:
            return value
    return value


def weighted_choice(items: List[Dict[str, Any]], weight_key: str) -> Dict[str, Any]:
    total = sum(float(item.get(weight_key, 1)) for item in items)
    pick = random.uniform(0, total)
    current = 0.0
    for item in items:
        current += float(item.get(weight_key, 1))
        if current >= pick:
            return item
    return items[-1]


def ensure_output_dir() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------
# DB helpers
# ---------------------------------------------------------

def table_exists(cursor, table_name: str) -> bool:
    cursor.execute("SHOW TABLES LIKE %s", (table_name,))
    return cursor.fetchone() is not None


def get_table_columns(cursor, table_name: str) -> set:
    cursor.execute(f"DESCRIBE `{table_name}`")
    rows = cursor.fetchall()
    return {row["Field"] if isinstance(row, dict) else row[0] for row in rows}


def insert_row(cursor, table_name: str, row: Dict[str, Any], columns_cache: Dict[str, set]) -> int:
    if table_name not in columns_cache:
        columns_cache[table_name] = get_table_columns(cursor, table_name)

    allowed = columns_cache[table_name]
    filtered = {key: value for key, value in row.items() if key in allowed}

    if not filtered:
        raise ValueError(f"No matching columns to insert into {table_name}")

    keys = list(filtered.keys())
    placeholders = ", ".join(["%s"] * len(keys))
    column_sql = ", ".join(f"`{key}`" for key in keys)

    sql = f"INSERT INTO `{table_name}` ({column_sql}) VALUES ({placeholders})"
    cursor.execute(sql, [filtered[key] for key in keys])
    return int(cursor.lastrowid)


def update_row_by_id(cursor, table_name: str, id_column: str, id_value: int, row: Dict[str, Any], columns_cache: Dict[str, set]) -> None:
    if table_name not in columns_cache:
        columns_cache[table_name] = get_table_columns(cursor, table_name)

    allowed = columns_cache[table_name]
    filtered = {key: value for key, value in row.items() if key in allowed}

    if not filtered:
        return

    set_sql = ", ".join(f"`{key}` = %s" for key in filtered.keys())
    sql = f"UPDATE `{table_name}` SET {set_sql} WHERE `{id_column}` = %s"
    cursor.execute(sql, list(filtered.values()) + [id_value])


# ---------------------------------------------------------
# Cleanup
# ---------------------------------------------------------

def get_synthetic_user_ids(cursor) -> List[int]:
    cursor.execute(
        """
        SELECT id
        FROM users
        WHERE email LIKE %s
           OR firebase_uid LIKE %s
           OR student_code LIKE %s
        """,
        (
            f"{SYNTHETIC_EMAIL_PREFIX}%",
            f"{SYNTHETIC_FIREBASE_PREFIX}%",
            f"{SYNTHETIC_STUDENT_CODE_PREFIX}%",
        ),
    )
    rows = cursor.fetchall() or []
    return [int(row["id"]) for row in rows]


def reset_synthetic_data(conn, cursor) -> int:
    user_ids = get_synthetic_user_ids(cursor)
    if not user_ids:
        return 0

    placeholders = ", ".join(["%s"] * len(user_ids))

    # Use explicit table names so parent_student_links is not parsed wrongly.
    delete_steps = [
        (
            "chat_messages",
            f"""
            DELETE cm
            FROM chat_messages cm
            JOIN chat_sessions cs
                ON cm.chat_session_id = cs.chat_session_id
            WHERE cs.student_id IN ({placeholders})
            """,
        ),
        (
            "chat_sessions",
            f"DELETE FROM chat_sessions WHERE student_id IN ({placeholders})",
        ),
        (
            "review_variants",
            f"DELETE FROM review_variants WHERE user_id IN ({placeholders})",
        ),
        (
            "quick_snap_events",
            f"DELETE FROM quick_snap_events WHERE user_id IN ({placeholders})",
        ),
        (
            "attempts",
            f"DELETE FROM attempts WHERE user_id IN ({placeholders})",
        ),
        (
            "practice_sessions",
            f"DELETE FROM practice_sessions WHERE user_id IN ({placeholders})",
        ),
        (
            "student_topic_mastery",
            f"DELETE FROM student_topic_mastery WHERE user_id IN ({placeholders})",
        ),
        (
            "activity_logs",
            f"DELETE FROM activity_logs WHERE user_id IN ({placeholders})",
        ),
        (
            "parent_student_links",
            f"DELETE FROM parent_student_links WHERE parent_id IN ({placeholders})",
        ),
        (
            "parent_student_links",
            f"DELETE FROM parent_student_links WHERE student_id IN ({placeholders})",
        ),
    ]

    for table_name, sql in delete_steps:
        if table_exists(cursor, table_name):
            cursor.execute(sql, user_ids)

    cursor.execute(f"DELETE FROM users WHERE id IN ({placeholders})", user_ids)
    conn.commit()
    return len(user_ids)

# ---------------------------------------------------------
# Load reference data
# ---------------------------------------------------------

def load_chapters(cursor) -> Tuple[List[Chapter], Dict[str, Chapter]]:
    cursor.execute(
        """
        SELECT id, form, chapter_no, name_en, name_bm, spm_weightage_percentage
        FROM chapters
        ORDER BY
            CAST(REPLACE(LOWER(form), 'form ', '') AS UNSIGNED),
            CAST(REPLACE(LOWER(chapter_no), 'chapter ', '') AS UNSIGNED)
        """
    )
    rows = cursor.fetchall() or []

    chapters: List[Chapter] = []
    chapter_lookup: Dict[str, Chapter] = {}

    for row in rows:
        chapter = Chapter(
            id=int(row["id"]),
            form=row["form"],
            chapter_no=row["chapter_no"],
            name_en=row["name_en"],
            name_bm=row["name_bm"],
            weightage=safe_float(row["spm_weightage_percentage"]),
        )
        chapters.append(chapter)

        possible_keys = {
            norm(f"{chapter.form} {chapter.label}"),
            norm(f"{chapter.form} {chapter.chapter_no}: {chapter.name_en}"),
            norm(f"{chapter.form} {chapter.chapter_no} {chapter.name_en}"),
            norm(f"{chapter.form} {chapter.name_en}"),
            norm(chapter.label),
            norm(chapter.name_en),
        }

        for key in possible_keys:
            chapter_lookup[key] = chapter

    return chapters, chapter_lookup


def load_questions(cursor) -> List[Dict[str, Any]]:
    cursor.execute(
        """
        SELECT
            q.*,
            p.paper_type AS source_paper_type,
            p.exam_name,
            p.year
        FROM questions q
        LEFT JOIN papers p
            ON q.paper_id = p.id
        WHERE (q.classification_status IS NULL OR q.classification_status != 'needs_review')
        """
    )
    rows = cursor.fetchall() or []

    normalized_rows = []
    for row in rows:
        item = dict(row)
        for key in [
            "instructions_en", "instructions_ms", "sequence", "equations",
            "expressions", "variables", "given_values", "table_data",
            "constraints", "options", "raw_json"
        ]:
            if key in item:
                item[key] = parse_json_maybe(item[key])
        normalized_rows.append(item)

    return normalized_rows


def resolve_question_chapter(row: Dict[str, Any], chapter_lookup: Dict[str, Chapter]) -> Optional[Chapter]:
    form_candidates = [
        row.get("verified_form"),
        row.get("form"),
        row.get("group_form"),
    ]

    chapter_candidates = [
        row.get("verified_chapter"),
        row.get("chapter"),
        row.get("group_chapter"),
    ]

    for form_value in form_candidates:
        for chapter_value in chapter_candidates:
            if not form_value or not chapter_value:
                continue

            key = norm(f"{form_value} {chapter_value}")
            if key in chapter_lookup:
                return chapter_lookup[key]

            key2 = norm(chapter_value)
            if key2 in chapter_lookup:
                candidate = chapter_lookup[key2]
                if norm(candidate.form) == norm(form_value):
                    return candidate

    return None


# ---------------------------------------------------------
# Build practice units
# ---------------------------------------------------------

def infer_paper_type(row: Dict[str, Any]) -> str:
    source_paper_type = norm(row.get("source_paper_type"))
    question_type = norm(row.get("question_type"))

    if source_paper_type in {"kertas1", "kertas 1"}:
        return "kertas1"

    if source_paper_type in {"kertas2", "kertas 2"}:
        return "kertas2"

    if question_type == "mcq":
        return "kertas1"

    return "kertas2"


def is_mixed_group(row: Dict[str, Any]) -> bool:
    return norm(row.get("group_chapter")) == "mixed" or norm(row.get("group_form")) == "mixed"


def effective_difficulty_level(row: Dict[str, Any], paper_type: str, mixed_split: bool) -> int:
    """
    K1:
        use individual difficulty_level.

    K2 same-chapter grouped:
        use group_difficulty_level because the whole group difficulty matters.

    K2 mixed grouped:
        use individual/stage difficulty_level because the group is split by actual chapter.
    """
    paper_type = norm(paper_type)

    if paper_type == "kertas2" and not mixed_split and row.get("group_id"):
        group_level = safe_int(row.get("group_difficulty_level"), 0)
        if 1 <= group_level <= 5:
            return group_level

    level = safe_int(row.get("difficulty_level"), 3)
    return int(clamp(level, 1, 5))


def row_max_marks(row: Dict[str, Any], paper_type: str) -> float:
    if paper_type == "kertas1":
        return 1.0

    display_marks = safe_float(row.get("display_marks"), 0.0)
    if display_marks > 0:
        return display_marks

    marks = safe_float(row.get("marks"), 0.0)
    if marks > 0:
        return marks

    return 1.0


def make_stage_unit(
    key: str,
    rows: List[Dict[str, Any]],
    chapter: Chapter,
    mixed_split: bool,
) -> PracticeUnit:
    levels = [
        effective_difficulty_level(row, "kertas2", mixed_split=mixed_split)
        for row in rows
    ]
    level = max(levels) if levels else 3

    first = rows[0]
    exercise_stage_id = first.get("exercise_stage_id") or key
    stage_index = safe_int(first.get("stage_index"), 1)

    return PracticeUnit(
        unit_type="k2_stage",
        chapter_id=chapter.id,
        form=chapter.form,
        chapter_label=chapter.label,
        paper_type="kertas2",
        difficulty_level=level,
        difficulty_label=difficulty_label_from_level(level),
        rows=rows,
        group_id=first.get("group_id"),
        exercise_stage_id=exercise_stage_id,
        stage_index=stage_index,
        is_mixed_group_split=mixed_split,
    )


def build_practice_units(
    question_rows: List[Dict[str, Any]],
    chapter_lookup: Dict[str, Chapter],
) -> Dict[Tuple[int, str], List[PracticeUnit]]:
    units_by_chapter_paper: Dict[Tuple[int, str], List[PracticeUnit]] = defaultdict(list)

    # Same-chapter K2 grouped questions are stored here first.
    same_chapter_group_rows: Dict[str, Dict[int, List[Dict[str, Any]]]] = defaultdict(lambda: defaultdict(list))
    same_chapter_group_chapter: Dict[str, Chapter] = {}

    # Mixed K2 groups or ungrouped K2 stages.
    k2_stage_rows: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    k2_stage_chapter: Dict[str, Chapter] = {}
    k2_stage_mixed: Dict[str, bool] = {}

    for row in question_rows:
        chapter = resolve_question_chapter(row, chapter_lookup)
        if not chapter:
            # Skip Foundation/unknown/messy rows that are not linked to SPM Form 4/5 chapters.
            continue

        paper_type = infer_paper_type(row)

        if paper_type == "kertas1":
            level = effective_difficulty_level(row, "kertas1", mixed_split=False)
            unit = PracticeUnit(
                unit_type="k1_question",
                chapter_id=chapter.id,
                form=chapter.form,
                chapter_label=chapter.label,
                paper_type="kertas1",
                difficulty_level=level,
                difficulty_label=difficulty_label_from_level(level),
                rows=[row],
            )
            units_by_chapter_paper[(chapter.id, "kertas1")].append(unit)
            continue

        # K2
        mixed_split = is_mixed_group(row)
        group_id = str(row.get("group_id") or "").strip()
        stage_index = safe_int(row.get("stage_index"), 1)
        exercise_stage_id = str(row.get("exercise_stage_id") or "").strip()

        if group_id and not mixed_split:
            chain_key = f"group::{group_id}::{chapter.id}"
            same_chapter_group_rows[chain_key][stage_index].append(row)
            same_chapter_group_chapter[chain_key] = chapter
            continue

        # Mixed group or ungrouped K2 = chapter-specific stage unit.
        # Important: mixed groups are split by actual verified chapter, no cross-chapter unlock.
        stage_key_base = exercise_stage_id or f"QID_{row.get('id')}_S{stage_index}"
        stage_key = f"stage::{stage_key_base}::{chapter.id}"
        k2_stage_rows[stage_key].append(row)
        k2_stage_chapter[stage_key] = chapter
        k2_stage_mixed[stage_key] = mixed_split

    # Convert same-chapter grouped K2 into chain units.
    for chain_key, stages_map in same_chapter_group_rows.items():
        chapter = same_chapter_group_chapter[chain_key]
        group_id = chain_key.split("::")[1]

        stage_units: List[PracticeUnit] = []
        for stage_index in sorted(stages_map.keys()):
            rows = stages_map[stage_index]
            stage_key = f"{chain_key}::stage::{stage_index}"
            stage_unit = make_stage_unit(
                key=stage_key,
                rows=rows,
                chapter=chapter,
                mixed_split=False,
            )
            stage_units.append(stage_unit)

        if not stage_units:
            continue

        chain_level = max(stage.difficulty_level for stage in stage_units)

        chain_unit = PracticeUnit(
            unit_type="k2_group_chain",
            chapter_id=chapter.id,
            form=chapter.form,
            chapter_label=chapter.label,
            paper_type="kertas2",
            difficulty_level=chain_level,
            difficulty_label=difficulty_label_from_level(chain_level),
            stages=stage_units,
            group_id=group_id,
            is_mixed_group_split=False,
        )
        units_by_chapter_paper[(chapter.id, "kertas2")].append(chain_unit)

    # Convert mixed/ungrouped stages into normal stage units.
    for stage_key, rows in k2_stage_rows.items():
        chapter = k2_stage_chapter[stage_key]
        mixed_split = k2_stage_mixed[stage_key]
        stage_unit = make_stage_unit(
            key=stage_key,
            rows=rows,
            chapter=chapter,
            mixed_split=mixed_split,
        )
        units_by_chapter_paper[(chapter.id, "kertas2")].append(stage_unit)

    return units_by_chapter_paper


# ---------------------------------------------------------
# Student profile generation
# ---------------------------------------------------------

def create_student_profiles(students_count: int, chapters: List[Chapter]) -> List[SyntheticStudentProfile]:
    profiles: List[SyntheticStudentProfile] = []

    valid_chapters = [chapter for chapter in chapters if norm(chapter.form) in {"form 4", "form 5"}]

    for index in range(1, students_count + 1):
        template = weighted_choice(PROFILE_TEMPLATES, "weight")
        low, high = template["ability_range"]
        hidden_ability = random.uniform(low, high)

        # Choose weak/strong topics so recommendation has something meaningful.
        weak_count = random.randint(2, 5)
        strong_count = random.randint(2, 4)

        shuffled = valid_chapters[:]
        random.shuffle(shuffled)

        weak_chapters = shuffled[:weak_count]
        remaining = [chapter for chapter in shuffled if chapter.id not in {c.id for c in weak_chapters}]
        strong_chapters = remaining[:strong_count]

        # Hidden final score: not directly copied from accuracy, but correlated.
        consistency_bonus = {
            "Consistent Climber": 7,
            "High Achiever": 8,
            "Flexible Learner": 2,
            "Deep Focus Learner": 1,
            "Weekend Learner": 1,
            "Fresh Starter": -8,
        }.get(template["name"], 0)

        topic_penalty = weak_count * 1.5
        noise = random.gauss(0, 1.2)

        target_score = clamp(
            hidden_ability * 100 + consistency_bonus - topic_penalty + noise,
            25,
            98,
        )
        target_grade = score_to_grade(target_score)

        language = random.choices(["english", "bm"], weights=[0.7, 0.3], k=1)[0]

        preferred_paper_type = random.choices(
            ["kertas1", "kertas2", "mixed"],
            weights=[0.42, 0.28, 0.30],
            k=1,
        )[0]

        profile = SyntheticStudentProfile(
            synthetic_index=index,
            name=f"Synthetic Student {index:03d} ({target_grade} Level)",
            email=f"{SYNTHETIC_EMAIL_PREFIX}{index:04d}@{SYNTHETIC_EMAIL_DOMAIN}",
            firebase_uid=f"{SYNTHETIC_FIREBASE_PREFIX}{index:04d}_{random_token(12)}",
            student_code=f"{SYNTHETIC_STUDENT_CODE_PREFIX}{index:04d}",
            language=language,
            persona=template["name"],
            hidden_ability=round(hidden_ability, 4),
            target_score=round(target_score, 2),
            target_grade=target_grade,
            weak_chapter_ids=[chapter.id for chapter in weak_chapters],
            strong_chapter_ids=[chapter.id for chapter in strong_chapters],
            preferred_paper_type=preferred_paper_type,
        )
        profiles.append(profile)

    return profiles


def template_for_persona(persona: str) -> Dict[str, Any]:
    for template in PROFILE_TEMPLATES:
        if template["name"] == persona:
            return template
    return PROFILE_TEMPLATES[0]


# ---------------------------------------------------------
# Session date generation
# ---------------------------------------------------------

def generate_session_start_times(profile: SyntheticStudentProfile, days_back: int) -> List[datetime]:
    template = template_for_persona(profile.persona)
    min_sessions, max_sessions = template["sessions_range"]
    session_count = random.randint(min_sessions, max_sessions)

    today = datetime.now().replace(minute=0, second=0, microsecond=0)
    start_window = today - timedelta(days=days_back)

    starts: List[datetime] = []

    if template["session_gap_bias"] == "low_activity":
        chosen_days = sorted(random.sample(range(days_back), min(session_count, days_back)))
        for day_offset in chosen_days:
            session_date = start_window + timedelta(days=day_offset)
            starts.append(make_time_on_date(session_date, template))
    else:
        # Regular-ish or irregular spread.
        for _ in range(session_count):
            day_offset = random.randint(0, days_back - 1)
            session_date = start_window + timedelta(days=day_offset)

            if template["session_gap_bias"] == "regular":
                # Prefer active weekdays.
                tries = 0
                while session_date.weekday() not in template["active_weekdays"] and tries < 10:
                    day_offset = random.randint(0, days_back - 1)
                    session_date = start_window + timedelta(days=day_offset)
                    tries += 1

            starts.append(make_time_on_date(session_date, template))

    starts = sorted(starts)

    # Avoid exact duplicate timestamps.
    deduped = []
    seen = set()
    for value in starts:
        while value in seen:
            value += timedelta(minutes=random.randint(5, 25))
        seen.add(value)
        deduped.append(value)

    return deduped


def make_time_on_date(base_date: datetime, template: Dict[str, Any]) -> datetime:
    hour = random.choice(template["preferred_hours"])
    minute = random.choice([0, 5, 10, 15, 20, 30, 40, 45, 50])
    return base_date.replace(hour=hour, minute=minute, second=0, microsecond=0)


# ---------------------------------------------------------
# Ability and scoring simulation
# ---------------------------------------------------------

def chapter_adjusted_ability(profile: SyntheticStudentProfile, chapter_id: int) -> float:
    ability = profile.hidden_ability

    if chapter_id in profile.weak_chapter_ids:
        ability -= random.uniform(0.14, 0.26)

    if chapter_id in profile.strong_chapter_ids:
        ability += random.uniform(0.08, 0.16)

    # Small day-to-day variance.
    ability += random.gauss(0, 0.035)

    return clamp(ability, 0.08, 0.98)


def probability_correct(profile: SyntheticStudentProfile, chapter_id: int, difficulty_level: int, paper_type: str) -> float:
    ability = chapter_adjusted_ability(profile, chapter_id)

    # Higher difficulty reduces probability.
    difficulty_penalty = {
        1: -0.05,
        2: 0.04,
        3: 0.13,
        4: 0.24,
        5: 0.34,
    }.get(difficulty_level, 0.13)

    p = ability - difficulty_penalty

    if paper_type == "kertas2":
        # K2 is harder to fully score.
        p -= 0.07

    persona_adjustment = {
        "High Achiever": 0.025,
        "Consistent Climber": 0.015,
        "Weekend Learner": 0.005,
        "Deep Focus Learner": 0.005,
        "Fresh Starter": -0.03,
        "Flexible Learner": 0.00,
    }.get(profile.persona, 0.0)

    p += persona_adjustment

    return clamp(p, 0.04, 0.96)

def simulate_k1_answer(profile: SyntheticStudentProfile, unit: PracticeUnit) -> Tuple[int, float, float, int]:
    p = probability_correct(profile, unit.chapter_id, unit.difficulty_level, "kertas1")
    is_correct = 1 if random.random() < p else 0
    score = 1.0 if is_correct else 0.0
    max_score = 1.0

    base_time = {
        1: 35,
        2: 50,
        3: 70,
        4: 95,
        5: 120,
    }.get(unit.difficulty_level, 70)

    if not is_correct:
        base_time *= random.uniform(1.05, 1.35)

    time_taken = int(max(8, random.gauss(base_time, base_time * 0.25)))
    return is_correct, score, max_score, time_taken


def simulate_k2_score(profile: SyntheticStudentProfile, unit: PracticeUnit, row: Dict[str, Any]) -> Tuple[int, float, float, int]:
    max_score = row_max_marks(row, "kertas2")
    p_full = probability_correct(profile, unit.chapter_id, unit.difficulty_level, "kertas2")

    # K2 can be partial, not only correct/wrong.
    roll = random.random()

    if roll < p_full:
        score = max_score
    else:
        # Partial marks depend on ability.
        ability = chapter_adjusted_ability(profile, unit.chapter_id)
        if ability >= 0.75:
            ratio = random.choice([0.5, 0.6, 0.7, 0.8])
        elif ability >= 0.55:
            ratio = random.choice([0.25, 0.4, 0.5, 0.6])
        else:
            ratio = random.choice([0.0, 0.0, 0.25, 0.4])

        score = round(max_score * ratio, 2)

    is_correct = 1 if score >= max_score else 0

    base_time = {
        1: 75,
        2: 110,
        3: 150,
        4: 220,
        5: 300,
    }.get(unit.difficulty_level, 150)

    if score < max_score:
        base_time *= random.uniform(1.05, 1.45)

    time_taken = int(max(30, random.gauss(base_time, base_time * 0.22)))
    return is_correct, score, max_score, time_taken


# ---------------------------------------------------------
# Mastery logic
# ---------------------------------------------------------

def empty_mastery_state() -> Dict[str, Any]:
    return {
        "current_difficulty_level": 1,
        "correct_streak": 0,
        "wrong_streak": 0,
        "total_attempts": 0,
        "correct_attempts": 0,
        "mastery_score": 0.0,
        "last_practiced_at": None,
    }


def update_mastery_state(state: Dict[str, Any], is_correct: int, attempted_at: datetime) -> None:
    state["total_attempts"] += 1

    if is_correct:
        state["correct_attempts"] += 1
        state["correct_streak"] += 1
        state["wrong_streak"] = 0

        if state["correct_streak"] >= 3:
            state["current_difficulty_level"] = min(5, state["current_difficulty_level"] + 1)
            state["correct_streak"] = 0
    else:
        state["wrong_streak"] += 1
        state["correct_streak"] = 0

        if state["wrong_streak"] >= 2:
            state["current_difficulty_level"] = max(1, state["current_difficulty_level"] - 1)
            state["wrong_streak"] = 0

    state["mastery_score"] = round(
        (state["correct_attempts"] / max(1, state["total_attempts"])) * 100,
        2,
    )
    state["last_practiced_at"] = attempted_at


# ---------------------------------------------------------
# Unit selection
# ---------------------------------------------------------

def choose_session_chapter_and_paper(
    profile: SyntheticStudentProfile,
    chapters: List[Chapter],
    units_by_chapter_paper: Dict[Tuple[int, str], List[PracticeUnit]],
) -> Tuple[Optional[Chapter], Optional[str]]:
    available_pairs = [
        (chapter_id, paper_type)
        for (chapter_id, paper_type), units in units_by_chapter_paper.items()
        if units
    ]

    if not available_pairs:
        return None, None

    chapter_by_id = {chapter.id: chapter for chapter in chapters}

    # Paper preference.
    if profile.preferred_paper_type == "mixed":
        paper_weights = {"kertas1": 0.58, "kertas2": 0.42}
    elif profile.preferred_paper_type == "kertas1":
        paper_weights = {"kertas1": 0.78, "kertas2": 0.22}
    else:
        paper_weights = {"kertas1": 0.36, "kertas2": 0.64}

    weighted_options = []

    for chapter_id, paper_type in available_pairs:
        chapter = chapter_by_id.get(chapter_id)
        if not chapter:
            continue

        weight = 1.0
        weight *= paper_weights.get(paper_type, 0.5)

        # Weak chapters are more likely to be practiced.
        if chapter_id in profile.weak_chapter_ids:
            weight *= 2.3

        # Strong chapters still appear, but less.
        if chapter_id in profile.strong_chapter_ids:
            weight *= 0.75

        # SPM weightage slightly increases chance.
        #if chapter.weightage > 0:
        #    weight *= 1 + (chapter.weightage / 40)

        weighted_options.append((chapter_id, paper_type, weight))

    total = sum(item[2] for item in weighted_options)
    pick = random.uniform(0, total)
    current = 0.0

    for chapter_id, paper_type, weight in weighted_options:
        current += weight
        if current >= pick:
            return chapter_by_id[chapter_id], paper_type

    chapter_id, paper_type, _ = weighted_options[-1]
    return chapter_by_id[chapter_id], paper_type


def choose_units_for_session(
    profile: SyntheticStudentProfile,
    chapter: Chapter,
    paper_type: str,
    units_by_chapter_paper: Dict[Tuple[int, str], List[PracticeUnit]],
) -> List[PracticeUnit]:
    units = units_by_chapter_paper.get((chapter.id, paper_type), [])
    if not units:
        return []

    if paper_type == "kertas1":
        count = random.randint(4, 9)
    else:
        count = random.randint(1, 3)

    # Prefer questions near student's current ability.
    ability_level = int(clamp(round(profile.hidden_ability * 5), 1, 5))

    def unit_weight(unit: PracticeUnit) -> float:
        distance = abs(unit.difficulty_level - ability_level)
        weight = 1 / (1 + distance)

        if chapter.id in profile.weak_chapter_ids and unit.difficulty_level <= 3:
            weight *= 1.25

        if profile.persona == "High Achiever" and unit.difficulty_level >= 4:
            weight *= 1.35

        return weight

    selected = []
    available = units[:]
    random.shuffle(available)

    for _ in range(min(count, len(available))):
        total = sum(unit_weight(unit) for unit in available)
        pick = random.uniform(0, total)
        current = 0.0

        chosen_index = 0
        for index, unit in enumerate(available):
            current += unit_weight(unit)
            if current >= pick:
                chosen_index = index
                break

        selected.append(available.pop(chosen_index))

    return selected


# ---------------------------------------------------------
# Generate and write data
# ---------------------------------------------------------

def create_user(cursor, profile: SyntheticStudentProfile, columns_cache: Dict[str, set]) -> int:
    user_row = {
        "firebase_uid": profile.firebase_uid,
        "name": profile.name,
        "email": profile.email,
        "role": "student",
        "language": profile.language,
        "auth_provider": "email",
        "photo_url": None,
        "student_code": profile.student_code,
        "is_active": 1,
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
    }

    user_id = insert_row(cursor, "users", user_row, columns_cache)
    profile.created_user_id = user_id
    return user_id


def write_activity_log(cursor, user_id: int, action_type: str, created_at: datetime, columns_cache: Dict[str, set]) -> None:
    if not table_exists(cursor, "activity_logs"):
        return

    insert_row(
        cursor,
        "activity_logs",
        {
            "user_id": user_id,
            "action_type": action_type,
            "created_at": created_at,
        },
        columns_cache,
    )


def write_mastery_rows(
    cursor,
    profile: SyntheticStudentProfile,
    mastery_states: Dict[Tuple[int, int, str], Dict[str, Any]],
    chapters_by_id: Dict[int, Chapter],
    columns_cache: Dict[str, set],
) -> None:
    user_id = profile.created_user_id
    if not user_id:
        return

    for (student_id, chapter_id, paper_type), state in mastery_states.items():
        if student_id != user_id:
            continue

        chapter = chapters_by_id.get(chapter_id)
        if not chapter:
            continue

        row = {
            "user_id": user_id,
            "form": chapter.form,
            "chapter": chapter.label,
            "paper_type": paper_type,
            "current_difficulty_level": state["current_difficulty_level"],
            "correct_streak": state["correct_streak"],
            "wrong_streak": state["wrong_streak"],
            "total_attempts": state["total_attempts"],
            "correct_attempts": state["correct_attempts"],
            "mastery_score": state["mastery_score"],
            "last_practiced_at": state["last_practiced_at"],
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
        }

        insert_row(cursor, "student_topic_mastery", row, columns_cache)


def generate_for_student(
    cursor,
    profile: SyntheticStudentProfile,
    chapters: List[Chapter],
    units_by_chapter_paper: Dict[Tuple[int, str], List[PracticeUnit]],
    columns_cache: Dict[str, set],
    days_back: int,
    dry_run: bool,
    export_attempt_rows: List[Dict[str, Any]],
    export_session_rows: List[Dict[str, Any]],
    mastery_states: Dict[Tuple[int, int, str], Dict[str, Any]],
) -> None:
    user_id = profile.created_user_id
    if not user_id:
        return

    start_times = generate_session_start_times(profile, days_back)

    if not dry_run:
        write_activity_log(cursor, user_id, "login", start_times[0] if start_times else datetime.now(), columns_cache)
        write_activity_log(cursor, user_id, "viewed_dashboard", (start_times[0] + timedelta(minutes=1)) if start_times else datetime.now(), columns_cache)

    for session_index, start_time in enumerate(start_times, start=1):
        chapter, paper_type = choose_session_chapter_and_paper(profile, chapters, units_by_chapter_paper)
        if not chapter or not paper_type:
            continue

        selected_units = choose_units_for_session(profile, chapter, paper_type, units_by_chapter_paper)
        if not selected_units:
            continue

        device_type = random.choice(DEVICE_TYPES)
        session_language = profile.language if random.random() < 0.85 else random.choice(LANGUAGES)

        practice_id = -1

        if not dry_run:
            practice_id = insert_row(
                cursor,
                "practice_sessions",
                {
                    "user_id": user_id,
                    "chapter_id": chapter.id,
                    "paper_type": paper_type,
                    "session_language": session_language,
                    "start_time": start_time,
                    "end_time": start_time,
                    "duration_seconds": 0,
                    "device_type": device_type,
                    "highest_streak": 0,
                    "total_questions_answered": 0,
                    "correct_count": 0,
                    "incorrect_count": 0,
                    "accuracy_snapshot": 0,
                },
                columns_cache,
            )

        attempt_time = start_time
        session_attempt_count = 0
        session_correct_count = 0
        session_total_seconds = 0
        running_streak = 0
        highest_streak = 0

        for unit in selected_units:
            if unit.unit_type == "k1_question":
                row = unit.rows[0]
                is_correct, score, max_score, time_taken = simulate_k1_answer(profile, unit)
                attempt_time += timedelta(seconds=random.randint(10, 45))
                session_total_seconds += time_taken
                session_attempt_count += 1
                session_correct_count += is_correct

                if is_correct:
                    running_streak += 1
                    highest_streak = max(highest_streak, running_streak)
                else:
                    running_streak = 0

                mastery_key = (user_id, unit.chapter_id, "kertas1")
                state = mastery_states.setdefault(mastery_key, empty_mastery_state())
                update_mastery_state(state, is_correct, attempt_time)

                attempt_row = {
                    "user_id": user_id,
                    "question_id": int(row["id"]),
                    "paper_type": "kertas1",
                    "chapter_snapshot_id": unit.chapter_id,
                    "chapter_snapshot": unit.chapter_label,
                    "difficulty_snapshot": unit.difficulty_label,
                    "difficulty_level_snapshot": unit.difficulty_level,
                    "selected_option_index": random.randint(0, 3),
                    "practice_id": practice_id,
                    "is_correct": is_correct,
                    "score": score,
                    "max_score": max_score,
                    "answer_revealed": 1,
                    "time_taken_seconds": time_taken,
                    "attempted_at": attempt_time,
                }

                if not dry_run:
                    insert_row(cursor, "attempts", attempt_row, columns_cache)

                export_attempt_rows.append(make_export_attempt(profile, practice_id, attempt_row, unit, row))

            elif unit.unit_type == "k2_stage":
                stage_result = write_k2_stage_attempts(
                    cursor=cursor,
                    profile=profile,
                    unit=unit,
                    practice_id=practice_id,
                    start_attempt_time=attempt_time,
                    columns_cache=columns_cache,
                    dry_run=dry_run,
                    export_attempt_rows=export_attempt_rows,
                    mastery_states=mastery_states,
                    group_attempt_id=None,
                    final_group_score=None,
                    final_group_max_score=None,
                    is_final_stage=True,
                    group_is_correct=None,
                )
                attempt_time = stage_result["last_attempt_time"]
                session_attempt_count += stage_result["attempt_count"]
                session_correct_count += stage_result["correct_count"]
                session_total_seconds += stage_result["duration_seconds"]
                highest_streak = max(highest_streak, stage_result["highest_streak"])

            elif unit.unit_type == "k2_group_chain":
                group_attempt_id = f"SYN-GRP-{user_id}-{session_index}-{unit.group_id}-{random_token(6)}"

                # First simulate all stage scores so final stage can store group total.
                simulated_stages = []
                group_score = 0.0
                group_max_score = 0.0

                for stage in unit.stages:
                    simulated_rows = []
                    for row in stage.rows:
                        is_correct, score, max_score, time_taken = simulate_k2_score(profile, stage, row)
                        simulated_rows.append((row, is_correct, score, max_score, time_taken))
                        group_score += score
                        group_max_score += max_score
                    simulated_stages.append((stage, simulated_rows))

                final_group_is_correct = 1 if group_max_score > 0 and group_score >= group_max_score else 0

                for stage_position, (stage, simulated_rows) in enumerate(simulated_stages):
                    is_final_stage = stage_position == len(simulated_stages) - 1
                    stage_result = write_k2_stage_attempts(
                        cursor=cursor,
                        profile=profile,
                        unit=stage,
                        practice_id=practice_id,
                        start_attempt_time=attempt_time,
                        columns_cache=columns_cache,
                        dry_run=dry_run,
                        export_attempt_rows=export_attempt_rows,
                        mastery_states=mastery_states,
                        group_attempt_id=group_attempt_id,
                        final_group_score=round(group_score, 2),
                        final_group_max_score=round(group_max_score, 2),
                        is_final_stage=is_final_stage,
                        group_is_correct=final_group_is_correct,
                        precomputed_rows=simulated_rows,
                    )

                    attempt_time = stage_result["last_attempt_time"]
                    session_attempt_count += stage_result["attempt_count"]
                    session_correct_count += stage_result["correct_count"]
                    session_total_seconds += stage_result["duration_seconds"]
                    highest_streak = max(highest_streak, stage_result["highest_streak"])

        # Add small navigation/reading time.
        session_total_seconds += random.randint(45, 180)

        end_time = start_time + timedelta(seconds=session_total_seconds)
        incorrect_count = session_attempt_count - session_correct_count
        accuracy = round((session_correct_count / session_attempt_count) * 100, 2) if session_attempt_count else 0

        if not dry_run:
            update_row_by_id(
                cursor,
                "practice_sessions",
                "practice_id",
                practice_id,
                {
                    "end_time": end_time,
                    "duration_seconds": session_total_seconds,
                    "highest_streak": highest_streak,
                    "total_questions_answered": session_attempt_count,
                    "correct_count": session_correct_count,
                    "incorrect_count": incorrect_count,
                    "accuracy_snapshot": accuracy,
                },
                columns_cache,
            )

            write_activity_log(cursor, user_id, f"practiced_{paper_type}", end_time, columns_cache)

            # Some dashboard/chatbot usage after practice.
            if random.random() < 0.28:
                write_activity_log(cursor, user_id, "viewed_dashboard", end_time + timedelta(minutes=random.randint(1, 4)), columns_cache)
            if random.random() < 0.10:
                write_activity_log(cursor, user_id, "used_chatbot", end_time + timedelta(minutes=random.randint(2, 8)), columns_cache)

        export_session_rows.append(
            {
                "synthetic_student_index": profile.synthetic_index,
                "user_id": user_id,
                "practice_id": practice_id,
                "persona": profile.persona,
                "chapter_id": chapter.id,
                "chapter": chapter.label,
                "form": chapter.form,
                "paper_type": paper_type,
                "session_language": session_language,
                "device_type": device_type,
                "start_time": start_time.isoformat(sep=" "),
                "end_time": end_time.isoformat(sep=" "),
                "duration_seconds": session_total_seconds,
                "highest_streak": highest_streak,
                "total_questions_answered": session_attempt_count,
                "correct_count": session_correct_count,
                "incorrect_count": incorrect_count,
                "accuracy_snapshot": accuracy,
            }
        )


def write_k2_stage_attempts(
    cursor,
    profile: SyntheticStudentProfile,
    unit: PracticeUnit,
    practice_id: int,
    start_attempt_time: datetime,
    columns_cache: Dict[str, set],
    dry_run: bool,
    export_attempt_rows: List[Dict[str, Any]],
    mastery_states: Dict[Tuple[int, int, str], Dict[str, Any]],
    group_attempt_id: Optional[str],
    final_group_score: Optional[float],
    final_group_max_score: Optional[float],
    is_final_stage: bool,
    group_is_correct: Optional[int],
    precomputed_rows: Optional[List[Tuple[Dict[str, Any], int, float, float, int]]] = None,
) -> Dict[str, Any]:
    attempt_time = start_attempt_time
    attempt_count = 0
    correct_count = 0
    duration_seconds = 0
    running_streak = 0
    highest_streak = 0

    rows_to_write = precomputed_rows

    if rows_to_write is None:
        rows_to_write = []
        for row in unit.rows:
            is_correct, score, max_score, time_taken = simulate_k2_score(profile, unit, row)
            rows_to_write.append((row, is_correct, score, max_score, time_taken))

    for row, is_correct, score, max_score, time_taken in rows_to_write:
        attempt_time += timedelta(seconds=random.randint(20, 75))
        attempt_count += 1
        correct_count += is_correct
        duration_seconds += time_taken

        if is_correct:
            running_streak += 1
            highest_streak = max(highest_streak, running_streak)
        else:
            running_streak = 0

        mastery_key = (profile.created_user_id, unit.chapter_id, "kertas2")
        state = mastery_states.setdefault(mastery_key, empty_mastery_state())
        update_mastery_state(state, is_correct, attempt_time)

        attempt_row = {
            "user_id": profile.created_user_id,
            "question_id": int(row["id"]),
            "exercise_stage_id": unit.exercise_stage_id,
            "group_attempt_id": group_attempt_id,
            "group_id_snapshot": unit.group_id,
            "paper_type": "kertas2",
            "chapter_snapshot_id": unit.chapter_id,
            "chapter_snapshot": unit.chapter_label,
            "difficulty_snapshot": unit.difficulty_label,
            "difficulty_level_snapshot": unit.difficulty_level,
            "practice_id": practice_id,
            "is_correct": is_correct,
            "group_is_correct": group_is_correct if is_final_stage and group_attempt_id else None,
            "group_score": final_group_score if is_final_stage and group_attempt_id else None,
            "group_max_score": final_group_max_score if is_final_stage and group_attempt_id else None,
            "is_group_final_stage": 1 if is_final_stage and group_attempt_id else 0,
            "score": score,
            "max_score": max_score,
            "answer_revealed": 1,
            "time_taken_seconds": time_taken,
            "attempted_at": attempt_time,
            "review_variant_id": None,
        }

        if not dry_run:
            insert_row(cursor, "attempts", attempt_row, columns_cache)

        export_attempt_rows.append(make_export_attempt(profile, practice_id, attempt_row, unit, row))

    return {
        "last_attempt_time": attempt_time,
        "attempt_count": attempt_count,
        "correct_count": correct_count,
        "duration_seconds": duration_seconds,
        "highest_streak": highest_streak,
    }


def make_export_attempt(
    profile: SyntheticStudentProfile,
    practice_id: int,
    attempt_row: Dict[str, Any],
    unit: PracticeUnit,
    question_row: Dict[str, Any],
) -> Dict[str, Any]:
    return {
        "synthetic_student_index": profile.synthetic_index,
        "user_id": profile.created_user_id,
        "persona": profile.persona,
        "target_score": profile.target_score,
        "target_grade": profile.target_grade,
        "practice_id": practice_id,
        "question_id": attempt_row.get("question_id"),
        "paper_type": attempt_row.get("paper_type"),
        "unit_type": unit.unit_type,
        "chapter_id": unit.chapter_id,
        "chapter": unit.chapter_label,
        "form": unit.form,
        "question_no": question_row.get("question_no"),
        "part": question_row.get("part"),
        "subpart": question_row.get("subpart"),
        "sub_subpart": question_row.get("sub_subpart"),
        "group_id": question_row.get("group_id"),
        "group_chapter": question_row.get("group_chapter"),
        "is_mixed_group_split": int(unit.is_mixed_group_split),
        "exercise_stage_id": attempt_row.get("exercise_stage_id"),
        "stage_index": unit.stage_index,
        "difficulty_level": attempt_row.get("difficulty_level_snapshot"),
        "difficulty": attempt_row.get("difficulty_snapshot"),
        "is_correct": attempt_row.get("is_correct"),
        "score": attempt_row.get("score"),
        "max_score": attempt_row.get("max_score"),
        "group_attempt_id": attempt_row.get("group_attempt_id"),
        "group_score": attempt_row.get("group_score"),
        "group_max_score": attempt_row.get("group_max_score"),
        "is_group_final_stage": attempt_row.get("is_group_final_stage"),
        "time_taken_seconds": attempt_row.get("time_taken_seconds"),
        "attempted_at": attempt_row.get("attempted_at").isoformat(sep=" ") if isinstance(attempt_row.get("attempted_at"), datetime) else attempt_row.get("attempted_at"),
    }


# ---------------------------------------------------------
# Feature engineering for CSV outputs
# ---------------------------------------------------------

def calculate_streak_from_dates(session_dates: List[date]) -> Tuple[int, int]:
    if not session_dates:
        return 0, 0

    unique_dates = sorted(set(session_dates))
    best = 1
    running = 1

    for i in range(1, len(unique_dates)):
        if (unique_dates[i] - unique_dates[i - 1]).days == 1:
            running += 1
        else:
            running = 1
        best = max(best, running)

    today = datetime.now().date()
    latest = unique_dates[-1]

    if (today - latest).days > 1:
        current = 0
    else:
        current = 1
        for i in range(len(unique_dates) - 1, 0, -1):
            if (unique_dates[i] - unique_dates[i - 1]).days == 1:
                current += 1
            else:
                break

    return current, best


def build_csv_feature_datasets(
    profiles: List[SyntheticStudentProfile],
    attempt_rows: List[Dict[str, Any]],
    session_rows: List[Dict[str, Any]],
    chapters: List[Chapter],
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
    attempts_by_student = defaultdict(list)
    sessions_by_student = defaultdict(list)

    for row in attempt_rows:
        attempts_by_student[row["synthetic_student_index"]].append(row)

    for row in session_rows:
        sessions_by_student[row["synthetic_student_index"]].append(row)

    grade_features = []
    study_features = []
    topic_features = []

    chapter_ids = [chapter.id for chapter in chapters]

    for profile in profiles:
        attempts = attempts_by_student[profile.synthetic_index]
        sessions = sessions_by_student[profile.synthetic_index]

        total_attempts = len(attempts)
        correct_attempts = sum(safe_int(row["is_correct"]) for row in attempts)
        overall_accuracy_percent = round((correct_attempts / total_attempts) * 100, 2) if total_attempts else 0

        recent_attempts = sorted(attempts, key=lambda x: x.get("attempted_at") or "")[-20:]
        recent_accuracy_percent = (
            round(sum(safe_int(row["is_correct"]) for row in recent_attempts) / len(recent_attempts) * 100, 2)
            if recent_attempts else overall_accuracy_percent
        )

        paper1_attempts = [row for row in attempts if row["paper_type"] == "kertas1"]
        paper2_attempts = [row for row in attempts if row["paper_type"] == "kertas2"]

        paper1_accuracy_percent = (
            round(sum(safe_int(row["is_correct"]) for row in paper1_attempts) / len(paper1_attempts) * 100, 2)
            if paper1_attempts else 0
        )
        paper2_accuracy_percent = (
            round(sum(safe_int(row["is_correct"]) for row in paper2_attempts) / len(paper2_attempts) * 100, 2)
            if paper2_attempts else 0
        )

        avg_time = (
            round(sum(safe_int(row["time_taken_seconds"]) for row in attempts) / total_attempts, 2)
            if total_attempts else 0
        )

        score_rows = [row for row in attempts if safe_float(row.get("max_score")) > 0]
        score_ratio_percent = (
            round(
                sum(safe_float(row.get("score")) for row in score_rows)
                / sum(safe_float(row.get("max_score")) for row in score_rows)
                * 100,
                2,
            )
            if score_rows else 0
        )

        total_sessions = len(sessions)
        session_dates = []
        durations = []

        for session in sessions:
            start_text = session.get("start_time")
            if isinstance(start_text, str):
                start_dt = datetime.fromisoformat(start_text)
            else:
                start_dt = start_text
            session_dates.append(start_dt.date())
            durations.append(safe_int(session.get("duration_seconds")))

        active_days = len(set(session_dates))
        current_streak, best_streak = calculate_streak_from_dates(session_dates)

        total_study_minutes = round(sum(durations) / 60, 2)
        avg_session_minutes = round((sum(durations) / max(1, len(durations))) / 60, 2)

        sessions_last_7 = []
        sessions_prev_7 = []
        now = datetime.now()

        for session in sessions:
            start_dt = datetime.fromisoformat(session["start_time"])
            if start_dt >= now - timedelta(days=7):
                sessions_last_7.append(session)
            elif now - timedelta(days=14) <= start_dt < now - timedelta(days=7):
                sessions_prev_7.append(session)

        active_days_last_7 = len({datetime.fromisoformat(s["start_time"]).date() for s in sessions_last_7})
        study_minutes_last_7 = round(sum(safe_int(s["duration_seconds"]) for s in sessions_last_7) / 60, 2)
        study_minutes_previous_7 = round(sum(safe_int(s["duration_seconds"]) for s in sessions_prev_7) / 60, 2)

        questions_per_session = round(total_attempts / total_sessions, 2) if total_sessions else 0
        evening_sessions = [
            s for s in sessions
            if datetime.fromisoformat(s["start_time"]).hour >= 18
        ]
        weekend_sessions = [
            s for s in sessions
            if datetime.fromisoformat(s["start_time"]).weekday() in [5, 6]
        ]

        evening_ratio = round(len(evening_sessions) / total_sessions, 4) if total_sessions else 0
        weekend_ratio = round(len(weekend_sessions) / total_sessions, 4) if total_sessions else 0
        active_day_ratio = round(active_days / total_sessions, 4) if total_sessions else 0
        recent_active_day_ratio = round(active_days_last_7 / len(sessions_last_7), 4) if sessions_last_7 else 0

        session_growth_ratio = (
            round((len(sessions_last_7) - len(sessions_prev_7)) / len(sessions_prev_7), 4)
            if sessions_prev_7 else len(sessions_last_7)
        )

        topic_rows_for_student = []
        topic_accuracies = []

        for chapter_id in chapter_ids:
            topic_attempts = [row for row in attempts if safe_int(row.get("chapter_id")) == chapter_id]
            if not topic_attempts:
                continue

            topic_correct = sum(safe_int(row["is_correct"]) for row in topic_attempts)
            topic_accuracy = round(topic_correct / len(topic_attempts) * 100, 2)
            topic_accuracies.append(topic_accuracy)

            topic_rows_for_student.append(
                {
                    "synthetic_student_index": profile.synthetic_index,
                    "user_id": profile.created_user_id,
                    "persona": profile.persona,
                    "chapter_id": chapter_id,
                    "attempts": len(topic_attempts),
                    "correct_attempts": topic_correct,
                    "accuracy_percent": topic_accuracy,
                    "avg_score_ratio_percent": round(
                        sum(safe_float(row.get("score")) for row in topic_attempts)
                        / max(1, sum(safe_float(row.get("max_score")) for row in topic_attempts))
                        * 100,
                        2,
                    ),
                    "is_hidden_weak_topic": int(chapter_id in profile.weak_chapter_ids),
                    "is_hidden_strong_topic": int(chapter_id in profile.strong_chapter_ids),
                }
            )

        weak_topic_count = sum(1 for value in topic_accuracies if value < 50)
        strong_topic_count = sum(1 for value in topic_accuracies if value >= 80)
        avg_topic_mastery = round(sum(topic_accuracies) / len(topic_accuracies), 2) if topic_accuracies else 0

        study_consistency_score = int(
            clamp(
                min(len(sessions_last_7), 5) * 12
                + min(active_days, 20) * 1.5
                + min(current_streak, 7) * 4,
                0,
                100,
            )
        )

        calibrated_target_score = build_synthetic_target_score(
            synthetic_index=profile.synthetic_index,
            score_ratio_percent=score_ratio_percent,
            avg_topic_mastery=avg_topic_mastery,
            study_consistency_score=study_consistency_score,
            avg_time_per_question=avg_time, 
        )

        calibrated_target_grade = score_to_grade(calibrated_target_score)


        hard_attempts = [row for row in attempts if safe_int(row.get("difficulty_level")) >= 4]
        hard_accuracy_percent = (
            round(sum(safe_int(row["is_correct"]) for row in hard_attempts) / len(hard_attempts) * 100, 2)
            if hard_attempts else 0
        )

        grade_features.append(
            {
                "synthetic_student_index": profile.synthetic_index,
                "user_id": profile.created_user_id,
                "persona": profile.persona,
                "hidden_ability": profile.hidden_ability,
                "total_questions_attempted": total_attempts,
                "overall_accuracy": round(overall_accuracy_percent / 100, 4),
                "overall_accuracy_percent": overall_accuracy_percent,
                "recent_accuracy": round(recent_accuracy_percent / 100, 4),
                "recent_accuracy_percent": recent_accuracy_percent,
                "paper1_accuracy": round(paper1_accuracy_percent / 100, 4),
                "paper1_accuracy_percent": paper1_accuracy_percent,
                "paper2_accuracy": round(paper2_accuracy_percent / 100, 4),
                "paper2_accuracy_percent": paper2_accuracy_percent,
                "avg_time_per_question": avg_time,
                "total_sessions": total_sessions,
                "active_days": active_days,
                "total_study_minutes": total_study_minutes,
                "avg_session_minutes": avg_session_minutes,
                "study_consistency_score": study_consistency_score,
                "max_streak": best_streak,
                "avg_topic_mastery": avg_topic_mastery,
                "weak_topic_count": weak_topic_count,
                "strong_topic_count": strong_topic_count,
                "score_ratio_percent": score_ratio_percent,
                "hard_accuracy_percent": hard_accuracy_percent,
                "original_profile_target_score": profile.target_score,
                "original_profile_target_grade": profile.target_grade,
                "target_score": calibrated_target_score,
                "target_grade": calibrated_target_grade,
            }
        )

        study_features.append(
            {
                "synthetic_student_index": profile.synthetic_index,
                "user_id": profile.created_user_id,
                "persona": profile.persona,
                "total_sessions": total_sessions,
                "total_questions": total_attempts,
                "questions_per_session": questions_per_session,
                "avg_time_per_question": avg_time,
                "active_days": active_days,
                "sessions_last_7_days": len(sessions_last_7),
                "active_days_last_7_days": active_days_last_7,
                "sessions_previous_7_days": len(sessions_prev_7),
                "study_minutes_last_7_days": study_minutes_last_7,
                "study_minutes_previous_7_days": study_minutes_previous_7,
                "total_study_minutes": total_study_minutes,
                "avg_session_minutes": avg_session_minutes,
                "max_streak": best_streak,
                "evening_session_ratio": evening_ratio,
                "weekend_session_ratio": weekend_ratio,
                "active_day_ratio": active_day_ratio,
                "recent_active_day_ratio": recent_active_day_ratio,
                "session_growth_ratio": session_growth_ratio,
                "pattern_label": profile.persona,
            }
        )

        topic_features.extend(topic_rows_for_student)

    return grade_features, study_features, topic_features


def write_csv(path: Path, rows: List[Dict[str, Any]]) -> None:
    if not rows:
        return

    path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = sorted({key for row in rows for key in row.keys()})

    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


# ---------------------------------------------------------
# Main
# ---------------------------------------------------------

def run(args) -> None:
    random.seed(args.seed)
    ensure_output_dir()

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    columns_cache: Dict[str, set] = {}

    try:
        if args.reset_synthetic and not args.dry_run:
            deleted_count = reset_synthetic_data(conn, cursor)
            print(f"Deleted {deleted_count} previous synthetic users and related records.")

        chapters, chapter_lookup = load_chapters(cursor)
        questions = load_questions(cursor)

        if not chapters:
            raise RuntimeError("No chapters found. Import chapters first.")

        if not questions:
            raise RuntimeError("No questions found in `questions` table. Import question bank first.")

        units_by_chapter_paper = build_practice_units(questions, chapter_lookup)

        total_units = sum(len(units) for units in units_by_chapter_paper.values())
        k1_units = sum(len(units) for (chapter_id, paper), units in units_by_chapter_paper.items() if paper == "kertas1")
        k2_units = sum(len(units) for (chapter_id, paper), units in units_by_chapter_paper.items() if paper == "kertas2")

        print(f"Loaded {len(chapters)} chapters.")
        print(f"Loaded {len(questions)} raw question rows.")
        print(f"Built {total_units} practice units: K1={k1_units}, K2={k2_units}.")

        profiles = create_student_profiles(args.students, chapters)

        export_student_rows: List[Dict[str, Any]] = []
        export_attempt_rows: List[Dict[str, Any]] = []
        export_session_rows: List[Dict[str, Any]] = []
        mastery_states: Dict[Tuple[int, int, str], Dict[str, Any]] = {}

        if args.dry_run:
            # Assign fake negative IDs only for CSV checking.
            for profile in profiles:
                profile.created_user_id = -profile.synthetic_index
        else:
            for profile in profiles:
                create_user(cursor, profile, columns_cache)

        chapters_by_id = {chapter.id: chapter for chapter in chapters}

        for profile in profiles:
            export_student_rows.append(
                {
                    "synthetic_student_index": profile.synthetic_index,
                    "user_id": profile.created_user_id,
                    "name": profile.name,
                    "email": profile.email,
                    "student_code": profile.student_code,
                    "language": profile.language,
                    "persona": profile.persona,
                    "hidden_ability": profile.hidden_ability,
                    "target_score": profile.target_score,
                    "target_grade": profile.target_grade,
                    "preferred_paper_type": profile.preferred_paper_type,
                    "weak_chapter_ids": json.dumps(profile.weak_chapter_ids),
                    "strong_chapter_ids": json.dumps(profile.strong_chapter_ids),
                }
            )

            generate_for_student(
                cursor=cursor,
                profile=profile,
                chapters=chapters,
                units_by_chapter_paper=units_by_chapter_paper,
                columns_cache=columns_cache,
                days_back=args.days_back,
                dry_run=args.dry_run,
                export_attempt_rows=export_attempt_rows,
                export_session_rows=export_session_rows,
                mastery_states=mastery_states,
            )

            if not args.dry_run and profile.synthetic_index % args.commit_every == 0:
                conn.commit()
                print(f"Committed {profile.synthetic_index}/{args.students} students...")

        if not args.dry_run:
            for profile in profiles:
                write_mastery_rows(
                    cursor=cursor,
                    profile=profile,
                    mastery_states=mastery_states,
                    chapters_by_id=chapters_by_id,
                    columns_cache=columns_cache,
                )

            conn.commit()

        grade_features, study_features, topic_features = build_csv_feature_datasets(
            profiles=profiles,
            attempt_rows=export_attempt_rows,
            session_rows=export_session_rows,
            chapters=chapters,
        )

        if args.export_csv:
            write_csv(OUTPUT_DIR / "synthetic_students.csv", export_student_rows)
            write_csv(OUTPUT_DIR / "synthetic_practice_sessions.csv", export_session_rows)
            write_csv(OUTPUT_DIR / "synthetic_attempts.csv", export_attempt_rows)
            write_csv(OUTPUT_DIR / "synthetic_grade_training.csv", grade_features)
            write_csv(OUTPUT_DIR / "synthetic_study_pattern_features.csv", study_features)
            write_csv(OUTPUT_DIR / "synthetic_topic_performance.csv", topic_features)

            print(f"CSV exported to: {OUTPUT_DIR}")

        print("Done.")
        print(f"Students generated: {len(profiles)}")
        print(f"Sessions generated: {len(export_session_rows)}")
        print(f"Attempts generated: {len(export_attempt_rows)}")
        print(f"Grade training rows: {len(grade_features)}")
        print(f"Study pattern rows: {len(study_features)}")
        print(f"Topic performance rows: {len(topic_features)}")

        if args.dry_run:
            print("Dry run only. No database records were inserted.")

    except Exception:
        if not args.dry_run:
            conn.rollback()
        raise

    finally:
        cursor.close()
        conn.close()


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate synthetic EasyLearn learning data into DB and CSV."
    )

    parser.add_argument(
        "--students",
        type=int,
        default=300,
        help="Number of synthetic students to generate.",
    )

    parser.add_argument(
        "--days-back",
        type=int,
        default=100,
        help="Generate practice history across this many past days.",
    )

    parser.add_argument(
        "--reset-synthetic",
        action="store_true",
        help="Delete previous synthetic users and related records before generating.",
    )

    parser.add_argument(
        "--export-csv",
        action="store_true",
        help="Export generated synthetic data/features to CSV.",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Do not write into DB. Useful for checking CSV output only.",
    )

    parser.add_argument(
        "--seed",
        type=int,
        default=44,
        help="Random seed for reproducible generation.",
    )

    parser.add_argument(
        "--commit-every",
        type=int,
        default=25,
        help="Commit DB inserts after every N students.",
    )

    return parser


if __name__ == "__main__":
    arg_parser = build_arg_parser()
    run(arg_parser.parse_args())