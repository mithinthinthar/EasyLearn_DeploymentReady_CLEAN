import random
from typing import Dict, List, Optional
import math
from solving.config import get_db_connection


CORRECT_STREAK_TO_LEVEL_UP = 2
WRONG_STREAK_TO_LEVEL_DOWN = 2

def difficulty_level_to_score(level):
    level = safe_int(level, 3)

    mapping = {
        1: 30,
        2: 40,
        3: 50,
        4: 65,
        5: 80,
    }
    return mapping.get(level, 50)


def calculate_expected_score(ability_score, difficulty_score):
    ability_score = float(ability_score or 50)
    difficulty_score = float(difficulty_score or 50)

    scale = 15
    return 1 / (1 + math.exp(-(ability_score - difficulty_score) / scale))


def update_elo_ability(old_ability, is_correct, question_difficulty_level, alpha=8):
    old_ability = float(old_ability or 50)
    difficulty_score = difficulty_level_to_score(question_difficulty_level)

    score = 1 if is_correct else 0
    expected = calculate_expected_score(old_ability, difficulty_score)

    new_ability = old_ability + alpha * (score - expected)

    return max(0, min(100, round(new_ability, 2)))


def ability_score_to_difficulty_level(ability_score):
    ability_score = float(ability_score or 50)

    if ability_score < 35:
        return 1
    if ability_score < 45:
        return 2
    if ability_score < 60:
        return 3
    if ability_score < 75:
        return 4

    return 5

def effective_difficulty_level(q: Dict, paper_type: str) -> int:
    """
    For K2, prefer group_difficulty_level because the whole question group
    determines the real difficulty.
    For K1, keep using individual difficulty_level.
    """
    paper_type = str(paper_type or "").strip().lower()

    if paper_type == "kertas2":
        group_level = safe_int(q.get("group_difficulty_level"), 0)

        if 1 <= group_level <= 5:
            return group_level

    level = safe_int(q.get("difficulty_level"), 3)
    return max(1, min(5, level))


def difficulty_label_from_level(level: int) -> str:
    level = safe_int(level, 3)

    if level <= 2:
        return "Easy"

    if level == 3:
        return "Moderate"

    return "Hard"

def safe_int(value, default=3):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default

def get_or_create_topic_mastery(
    conn,
    user_id: int,
    form: str,
    chapter: str,
    paper_type: str
) -> Dict:
    cursor = conn.cursor(dictionary=True, buffered=True)

    cursor.execute("""
        SELECT *
        FROM student_topic_mastery
        WHERE user_id = %s
          AND form = %s
          AND chapter = %s
          AND paper_type = %s
        LIMIT 1
    """, (user_id, form, chapter, paper_type))

    row = cursor.fetchone()

    if row:
        return row

    cursor.execute("""
        INSERT INTO student_topic_mastery (
            user_id, form, chapter, paper_type,
            current_difficulty_level,
            correct_streak, wrong_streak,
            total_attempts, correct_attempts,
            mastery_score, ability_score
        )
        VALUES (%s, %s, %s, %s, 3, 0, 0, 0, 0, 0.00, 50.00)
    """, (user_id, form, chapter, paper_type))

    conn.commit()

    cursor.execute("""
        SELECT *
        FROM student_topic_mastery
        WHERE user_id = %s
          AND form = %s
          AND chapter = %s
          AND paper_type = %s
        LIMIT 1
    """, (user_id, form, chapter, paper_type))

    return cursor.fetchone()
    
def get_attempted_stage_ids(
    conn,
    user_id: int,
    paper_type: str = None,
    practice_id=None,
    retry_mode: bool = False
) -> set:
    cursor = conn.cursor(dictionary=True, buffered=True)

    if retry_mode and practice_id:
        cursor.execute("""
            SELECT DISTINCT exercise_stage_id
            FROM attempts
            WHERE user_id = %s
              AND practice_id = %s
              AND paper_type = %s
              AND exercise_stage_id IS NOT NULL
              AND exercise_stage_id != ''
        """, (user_id, practice_id, paper_type))

    elif paper_type:
        cursor.execute("""
            SELECT DISTINCT exercise_stage_id
            FROM attempts
            WHERE user_id = %s
              AND paper_type = %s
              AND exercise_stage_id IS NOT NULL
              AND exercise_stage_id != ''
        """, (user_id, paper_type))

    else:
        cursor.execute("""
            SELECT DISTINCT exercise_stage_id
            FROM attempts
            WHERE user_id = %s
              AND exercise_stage_id IS NOT NULL
              AND exercise_stage_id != ''
        """, (user_id,))

    return {row["exercise_stage_id"] for row in cursor.fetchall()}
def get_attempted_question_ids(
    conn,
    user_id: int,
    paper_type: str = None,
    practice_id=None,
    retry_mode: bool = False
) -> set:
    cursor = conn.cursor(dictionary=True, buffered=True)

    try:
        if retry_mode and practice_id:
            cursor.execute("""
                SELECT DISTINCT question_id
                FROM attempts
                WHERE user_id = %s
                  AND practice_id = %s
                  AND paper_type = %s
                  AND question_id IS NOT NULL
            """, (user_id, practice_id, paper_type))

        elif paper_type:
            cursor.execute("""
                SELECT DISTINCT question_id
                FROM attempts
                WHERE user_id = %s
                  AND paper_type = %s
                  AND question_id IS NOT NULL
            """, (user_id, paper_type))

        else:
            cursor.execute("""
                SELECT DISTINCT question_id
                FROM attempts
                WHERE user_id = %s
                  AND question_id IS NOT NULL
            """, (user_id,))

        return {row["question_id"] for row in cursor.fetchall()}

    finally:
        cursor.close()
def get_candidate_questions(
    conn,
    form: str,
    chapter: str,
    target_level: int,
    paper_type: str
) -> List[Dict]:
    cursor = conn.cursor(dictionary=True, buffered=True)

    paper_type = str(paper_type or "").strip().lower()

    type_filter = ""

    if paper_type == "kertas1":
        type_filter = "AND q.question_type = 'mcq'"
    elif paper_type == "kertas2":
        type_filter = "AND (q.question_type IS NULL OR q.question_type != 'mcq')"

    cursor.execute(f"""
        SELECT
            q.id,
            q.paper_id,
            q.question_no,
            q.question_type,
            q.part,
            q.subpart,
            q.sub_subpart,
            q.group_id,
            q.exercise_stage_id,
            q.stage_index,
            q.unlock_after_stage_id,
            q.form,
            q.chapter,
            q.verified_form,
            q.verified_chapter,
            q.group_form,
            q.group_chapter,
            q.difficulty,
            q.difficulty_level,
            q.group_difficulty_level,
            q.display_marks,
            q.marks_source,
            q.instructions_en,
            q.instructions_ms,
            q.sequence,
            q.table_data,
            q.given_values,
            q.options,
            q.has_diagram,
            q.diagram_type,
            q.image_path
        FROM questions q
        WHERE (q.form = %s OR q.verified_form = %s)
            AND (q.chapter = %s OR q.verified_chapter = %s)
            AND COALESCE(q.is_active, 1) = 1
            AND (q.classification_status IS NULL OR q.classification_status != 'needs_review')
        {type_filter}
        ORDER BY RAND()
        LIMIT 300
    """, (form, form, chapter, chapter))

    return cursor.fetchall()
def get_fresh_units(
    units: List[Dict],
    attempted_question_ids: set,
    attempted_stage_ids: set
) -> List[Dict]:
    fresh_units = []

    for unit in units:
        unit_type = unit.get("unit_type")
        stage_id = unit.get("exercise_stage_id") or unit.get("unit_key")
        question_ids = unit.get("question_ids", [])
        unlock_after_stage_id = str(unit.get("unlock_after_stage_id") or "").strip()

        # K2 stage-based repeat + unlock check
        if unit_type == "stage" and stage_id:
            if stage_id in attempted_stage_ids:
                continue

            if unlock_after_stage_id and unlock_after_stage_id not in attempted_stage_ids:
                continue

            fresh_units.append(unit)

        # K1 / mixed K2 individual question
        else:
            if any(qid not in attempted_question_ids for qid in question_ids):
                fresh_units.append(unit)

    return fresh_units

def build_practice_units(question_rows: List[Dict], paper_type: str) -> List[Dict]:
    """
    Converts DB question rows into adaptive display units.

    K1:
        each MCQ question is one unit.

    K2:
        mixed chapter rows are individual question units.
        normal grouped rows are grouped by exercise_stage_id.
    """

    paper_type = str(paper_type or "").strip().lower()

    stage_units = {}
    individual_units = []

    for q in question_rows:
        question_type = str(q.get("question_type", "") or "").strip().lower()
        group_chapter = str(q.get("group_chapter", "") or "").strip()

        # =========================
        # K1: always individual MCQ
        # =========================
        if paper_type == "kertas1" or question_type == "mcq":
            individual_units.append({
                "unit_type": "question",
                "unit_key": f"QID_{q['id']}",
                "question_ids": [q["id"]],
                "exercise_stage_id": "",
                "difficulty_level": safe_int(q.get("difficulty_level", 3)),
                "rows": [q],
            })
            continue

        # =========================
        # K2 mixed chapter: individual
        # =========================
        if group_chapter == "Mixed":
            actual_chapter = (
                q.get("verified_chapter")
                or q.get("chapter")
                or q.get("group_chapter")
                or ""
            )

            actual_form = (
                q.get("verified_form")
                or q.get("form")
                or q.get("group_form")
                or ""
            )

            stage_id = q.get("exercise_stage_id") or f"{q.get('group_id')}_S{q.get('stage_index') or 1}"

            # Important:
            # Mixed groups should split by actual chapter, but still group same-stage same-chapter rows.
            mixed_stage_key = f"{stage_id}__{actual_form}__{actual_chapter}"

            if mixed_stage_key not in stage_units:
                stage_units[mixed_stage_key] = {
                    "unit_type": "stage",
                    "unit_key": mixed_stage_key,
                    "question_ids": [],
                    "exercise_stage_id": stage_id,
                    "group_id": q.get("group_id"),
                    "stage_index": safe_int(q.get("stage_index"), 1),
                    "unlock_after_stage_id": q.get("unlock_after_stage_id") or "",
                    "form": actual_form,
                    "chapter": actual_chapter,
                    "difficulty_level": 1,
                    "difficulty": "Easy",
                    "rows": [],
                }

            stage_units[mixed_stage_key]["question_ids"].append(q["id"])
            stage_units[mixed_stage_key]["rows"].append(q)

            level = effective_difficulty_level(q, paper_type)
            stage_units[mixed_stage_key]["difficulty_level"] = max(
                stage_units[mixed_stage_key]["difficulty_level"],
                level
            )

            stage_units[mixed_stage_key]["difficulty"] = difficulty_label_from_level(
                stage_units[mixed_stage_key]["difficulty_level"]
            )

            continue

        # =========================
        # K2 normal: stage-based
        # =========================
        stage_id = q.get("exercise_stage_id") or f"{q.get('group_id')}_S1"

        if stage_id not in stage_units:
            stage_units[stage_id] = {
                "unit_type": "stage",
                "unit_key": stage_id,
                "question_ids": [],
                "exercise_stage_id": stage_id,
                "group_id": q.get("group_id"),
                "stage_index": safe_int(q.get("stage_index"), 1),
                "unlock_after_stage_id": q.get("unlock_after_stage_id") or "",
                "difficulty_level": 1,
                "difficulty": 'Easy',
                "rows": [],
            }

        stage_units[stage_id]["question_ids"].append(q["id"])
        stage_units[stage_id]["rows"].append(q)
        # Use hardest subpart as stage difficulty
        level = effective_difficulty_level(q, paper_type)
        stage_units[stage_id]["difficulty_level"] = max(
            stage_units[stage_id]["difficulty_level"],
            level
        )

        stage_units[stage_id]["difficulty"] = difficulty_label_from_level(
            stage_units[stage_id]["difficulty_level"]
        )

    return list(stage_units.values()) + individual_units
def choose_next_practice_unit(
    conn,
    user_id: int,
    form: str,
    chapter: str,
    paper_type: str,
    allow_easier_after_hard_completed: bool = False,
    retry_mode: bool = False,
    practice_id=None
) -> Optional[Dict]:

    paper_type = str(paper_type or "").strip().lower()

    mastery = get_or_create_topic_mastery(
        conn=conn,
        user_id=user_id,
        form=form,
        chapter=chapter,
        paper_type=paper_type
    )

    target_level = safe_int(mastery.get("current_difficulty_level", 1), 1)
    target_level = max(1, min(5, target_level))

    attempted_question_ids = get_attempted_question_ids(
        conn,
        user_id,
        paper_type,
        practice_id=practice_id,
        retry_mode=retry_mode
    )

    attempted_stage_ids = get_attempted_stage_ids(
        conn,
        user_id,
        paper_type,
        practice_id=practice_id,
        retry_mode=retry_mode
    )

    candidates = get_candidate_questions(
        conn=conn,
        form=form,
        chapter=chapter,
        target_level=target_level,
        paper_type=paper_type
    )

    units = build_practice_units(candidates, paper_type)

    if not units:
        return {
            "status": "no_questions",
            "paper_type": paper_type,
            "form": form,
            "chapter": chapter,
            "target_difficulty_level": target_level,
            "unit": None
        }

    fresh_units = get_fresh_units(
        units=units,
        attempted_question_ids=attempted_question_ids,
        attempted_stage_ids=attempted_stage_ids
    )

    if not fresh_units:
        return {
            "status": "all_completed",
            "paper_type": paper_type,
            "form": form,
            "chapter": chapter,
            "target_difficulty_level": target_level,
            "unit": None
        }

    continuation_units = [
        unit for unit in fresh_units
        if str(unit.get("unlock_after_stage_id") or "").strip() in attempted_stage_ids
    ]

    if continuation_units:
        continuation_units.sort(
            key=lambda unit: (
                str(unit.get("group_id") or ""),
                safe_int(unit.get("stage_index"), 999)
            )
        )

        selected = continuation_units[0]

        return {
            "status": "selected",
            "paper_type": paper_type,
            "form": form,
            "chapter": chapter,
            "target_difficulty_level": target_level,
            "selected_difficulty_level": selected.get("difficulty_level"),
            "unit": selected
        }
    selected = None

    # ==================================================
    # CASE 1: Student is already at level 5
    # ==================================================
    if target_level >= 5:
        level_5_units = [
            unit for unit in fresh_units
            if safe_int(unit.get("difficulty_level", 3)) == 5
        ]

        if level_5_units:
            selected = random.choice(level_5_units)

        else:
            easier_units = [
                unit for unit in fresh_units
                if safe_int(unit.get("difficulty_level", 3)) < 5
            ]

            if easier_units and not allow_easier_after_hard_completed:
                return {
                    "status": "hard_completed",
                    "message": "You have completed all hard questions. Do you want to continue with the remaining easier questions?",
                    "paper_type": paper_type,
                    "form": form,
                    "chapter": chapter,
                    "target_difficulty_level": target_level,
                    "remaining_easier_count": len(easier_units),
                    "unit": None
                }

            if easier_units and allow_easier_after_hard_completed:
                selected = random.choice(easier_units)

    # ==================================================
    # CASE 2: Target level is 1-4
    # Always go upward only
    # Example target 4: try 4, then 5
    # ==================================================
    else:
        for level in range(target_level, 6):
            level_units = [
                unit for unit in fresh_units
                if safe_int(unit.get("difficulty_level", 3)) == level
            ]

            if level_units:
                selected = random.choice(level_units)
                break

        if not selected:
            lower_units = [
                unit for unit in fresh_units
                if safe_int(unit.get("difficulty_level", 3)) < target_level
            ]
            # When the practice flow wants to finish ALL normal questions,
            # allow remaining easier questions after same/harder questions are done.
            if lower_units and allow_easier_after_hard_completed:
                selected = random.choice(lower_units)
            else:
                return {
                    "status": "no_upward_question_found",
                    "message": "No same-level or harder questions are available.",
                    "paper_type": paper_type,
                    "form": form,
                    "chapter": chapter,
                    "target_difficulty_level": target_level,
                    "remaining_easier_count": len(lower_units),
                    "unit": None
                }

    if not selected:
        return {
            "status": "all_completed",
            "paper_type": paper_type,
            "form": form,
            "chapter": chapter,
            "target_difficulty_level": target_level,
            "unit": None
        }

    return {
        "status": "selected",
        "paper_type": paper_type,
        "form": form,
        "chapter": chapter,
        "target_difficulty_level": target_level,
        "selected_difficulty_level": selected.get("difficulty_level"),
        "unit": selected
    }


def level_up_by_band(current_level: int) -> int:
    current_level = safe_int(current_level, 1)

    # Easy level 1/2 -> Moderate level 3
    if current_level <= 2:
        return 3

    # Moderate level 3 -> Hard level 4
    if current_level == 3:
        return 4

    # Hard stays within hard cap
    return min(5, current_level)


def level_down_by_band(current_level: int) -> int:
    current_level = safe_int(current_level, 1)

    # Hard level 4/5 -> Moderate level 3
    if current_level >= 4:
        return 3

    # Moderate level 3 -> Easy level 2
    if current_level == 3:
        return 2

    # Easy stays at minimum
    return max(1, current_level)

def update_topic_mastery_after_attempt(
    conn,
    user_id: int,
    form: str,
    chapter: str,
    paper_type: str,
    is_correct: bool,
    question_difficulty_level: int = 3
):
    paper_type = str(paper_type or "").strip().lower()

    mastery = get_or_create_topic_mastery(
        conn=conn,
        user_id=user_id,
        form=form,
        chapter=chapter,
        paper_type=paper_type
    )

    current_level = safe_int(mastery.get("current_difficulty_level", 1), 1)
    correct_streak = safe_int(mastery.get("correct_streak", 0), 0)
    wrong_streak = safe_int(mastery.get("wrong_streak", 0), 0)

    total_attempts = safe_int(mastery.get("total_attempts", 0), 0)
    correct_attempts = safe_int(mastery.get("correct_attempts", 0), 0)
    
    total_attempts += 1

    if is_correct:
        correct_attempts += 1
        correct_streak += 1
        wrong_streak = 0
    else:
        wrong_streak += 1
        correct_streak = 0

    old_ability = float(mastery.get("ability_score") or 50)

    new_ability = update_elo_ability(
        old_ability=old_ability,
        is_correct=is_correct,
        question_difficulty_level=question_difficulty_level,
        alpha=8
    )

    current_level = ability_score_to_difficulty_level(new_ability)
    mastery_score = round((correct_attempts / total_attempts) * 100, 2)

    cursor = conn.cursor()
    cursor.execute("""
        UPDATE student_topic_mastery
        SET
            current_difficulty_level = %s,
            correct_streak = %s,
            wrong_streak = %s,
            total_attempts = %s,
            correct_attempts = %s,
            mastery_score = %s,
            ability_score = %s,
            last_practiced_at = NOW()
        WHERE user_id = %s
        AND form = %s
        AND chapter = %s
        AND paper_type = %s
    """, (
        current_level,
        correct_streak,
        wrong_streak,
        total_attempts,
        correct_attempts,
        mastery_score,
        new_ability,
        user_id,
        form,
        chapter,
        paper_type
    ))

    conn.commit()

    return {
        "current_difficulty_level": current_level,
        "correct_streak": correct_streak,
        "wrong_streak": wrong_streak,
        "total_attempts": total_attempts,
        "correct_attempts": correct_attempts,
        "mastery_score": mastery_score,
        "ability_score": new_ability
    }
