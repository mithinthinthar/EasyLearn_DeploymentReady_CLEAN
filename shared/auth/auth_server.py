"""EasyLearn shared identity, roles, relationships, and analytics API.

Firestore is the canonical store for identity and learner interaction data.
Subject databases may still supply read-only learning content, but dashboards,
role IDs, relationships and newly recorded activity all come from Firestore.
"""

import os
import re
import secrets
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Literal, Optional

import firebase_admin
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from firebase_admin import auth, firestore
from firebase_setup import initialize_firebase_admin
from pydantic import BaseModel, Field


ENV_FILE = Path(__file__).with_name(".env")
load_dotenv(ENV_FILE)

COOKIE_NAME = "easylearn_session"
SESSION_LENGTH = timedelta(days=5)
VALID_ROLES = {"student", "teacher", "parent"}
VALID_SUBJECTS = {"history", "mathematics", "bahasa_melayu"}
SUBJECT_LABELS = {
    "history": "History",
    "mathematics": "Mathematics",
    "bahasa_melayu": "Bahasa Melayu",
}

cookie_secure = os.getenv("AUTH_COOKIE_SECURE", "false").lower() == "true"
allow_teacher_self_registration = (
    os.getenv("ALLOW_TEACHER_SELF_REGISTRATION", "true").lower() == "true"
)
allowed_teacher_emails = {
    email.strip().lower()
    for email in os.getenv("ALLOWED_TEACHER_EMAILS", "").split(",")
    if email.strip()
}
allowed_origins = [
    origin.strip()
    for origin in os.getenv("AUTH_ALLOWED_ORIGINS", "").split(",")
    if origin.strip()
]
if not allowed_origins:
    allowed_origins = [
        "http://localhost:4000", "http://localhost:3000",
        "http://localhost:3001", "http://localhost:5173",
        "http://127.0.0.1:4000", "http://127.0.0.1:3000",
        "http://127.0.0.1:3001", "http://127.0.0.1:5173",
    ]

initialize_firebase_admin(base_dir=Path(__file__).resolve().parent, required=True)

db = firestore.client()
users = db.collection("easylearn_users")
events = db.collection("learning_events")
relationships = db.collection("student_relationships")

app = FastAPI(title="EasyLearn Platform API", version="2.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)


class SessionRequest(BaseModel):
    id_token: str
    requested_role: Optional[Literal["student", "teacher", "parent"]] = None


class LinkStudentRequest(BaseModel):
    student_code: str = Field(min_length=4, max_length=32)
    nickname: Optional[str] = Field(default=None, max_length=60)


class LearningEventRequest(BaseModel):
    subject: Literal["history", "mathematics", "bahasa_melayu"]
    activity_type: str = Field(min_length=1, max_length=50)
    title: str = Field(default="Learning activity", max_length=160)
    score: Optional[float] = None
    max_score: Optional[float] = None
    percentage: Optional[float] = Field(default=None, ge=0, le=100)
    questions_answered: int = Field(default=0, ge=0)
    duration_minutes: float = Field(default=0, ge=0)
    metadata: dict = Field(default_factory=dict)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def read_session(request: Request) -> dict:
    session_cookie = request.cookies.get(COOKIE_NAME)
    if not session_cookie:
        raise HTTPException(401, "EasyLearn login session was not found.")
    try:
        return auth.verify_session_cookie(session_cookie, check_revoked=True)
    except Exception as error:
        raise HTTPException(401, "EasyLearn login session is invalid or expired.") from error


def token_identity(decoded_token: dict) -> dict:
    return {
        "uid": decoded_token.get("uid"),
        "email": decoded_token.get("email"),
        "name": decoded_token.get("name") or decoded_token.get("email", "EasyLearn user").split("@")[0],
        "picture": decoded_token.get("picture"),
        "email_verified": decoded_token.get("email_verified", False),
    }


ROLE_ID_PREFIX = {"student": "S", "parent": "P", "teacher": "T"}
ROLE_ID_PATTERN = re.compile(r"^[SPT]-\d{7}$")


def generate_account_id(role: str) -> str:
    """Create a human-readable, role-prefixed ID that is unique in Firestore."""
    prefix = ROLE_ID_PREFIX[role]
    for _ in range(30):
        code = f"{prefix}-{secrets.randbelow(10_000_000):07d}"
        if not list(users.where("accountId", "==", code).limit(1).stream()):
            return code
    raise RuntimeError("Unable to generate a unique EasyLearn account ID.")


def profile_account_id(profile: dict) -> Optional[str]:
    value = profile.get("accountId") or profile.get("studentCode")
    return value if isinstance(value, str) else None


def get_profile(uid: str) -> Optional[dict]:
    snapshot = users.document(uid).get()
    if not snapshot.exists:
        return None
    value = snapshot.to_dict() or {}
    value["uid"] = uid
    return value


def public_profile(profile: dict) -> dict:
    account_id = profile_account_id(profile)
    return {
        "uid": profile.get("uid"),
        "email": profile.get("email"),
        "name": profile.get("name"),
        "picture": profile.get("picture"),
        "email_verified": profile.get("email_verified", False),
        "role": profile.get("role", "student"),
        "account_id": account_id,
        "student_code": account_id if profile.get("role") == "student" else None,
        "created_at": profile.get("createdAt"),
    }


def ensure_profile(decoded_token: dict, requested_role: Optional[str]) -> dict:
    identity = token_identity(decoded_token)
    existing = get_profile(identity["uid"])
    now = utc_now()

    if existing:
        if requested_role and requested_role != existing.get("role"):
            raise HTTPException(
                409,
                f"This Google account is already registered as {existing.get('role')}. Use the matching login type.",
            )
        role = existing.get("role", "student")
        account_id = profile_account_id(existing)
        # Existing accounts are upgraded on their next login. This intentionally
        # replaces legacy EL-/STU- identifiers so every subject sees one format.
        if role in VALID_ROLES and (
            not account_id
            or not ROLE_ID_PATTERN.fullmatch(account_id)
            or not account_id.startswith(f"{ROLE_ID_PREFIX[role]}-")
        ):
            account_id = generate_account_id(role)
        updates = {**identity, "lastLoginAt": now, "accountId": account_id}
        if role == "student":
            updates["studentCode"] = account_id
        users.document(identity["uid"]).set(updates, merge=True)
        return get_profile(identity["uid"]) or existing

    role = requested_role or "student"
    if role not in VALID_ROLES:
        raise HTTPException(400, "Choose Student, Teacher, or Parent.")
    if role == "teacher" and not allow_teacher_self_registration:
        email = (identity.get("email") or "").lower()
        if email not in allowed_teacher_emails:
            raise HTTPException(403, "This teacher email has not been approved.")

    account_id = generate_account_id(role)
    profile = {
        **identity,
        "role": role,
        "accountId": account_id,
        "studentCode": account_id if role == "student" else None,
        "createdAt": now,
        "lastLoginAt": now,
        "status": "active",
    }
    users.document(identity["uid"]).set(profile)
    profile["uid"] = identity["uid"]
    return profile


def current_profile(request: Request, roles: Optional[set[str]] = None) -> dict:
    decoded = read_session(request)
    profile = get_profile(decoded["uid"])
    if not profile:
        raise HTTPException(401, "EasyLearn profile was not found.")
    if roles and profile.get("role") not in roles:
        raise HTTPException(403, "This account does not have permission for this action.")
    return profile


def serialize_timestamp(value):
    return value.isoformat() if hasattr(value, "isoformat") else value


def student_events(student_uid: str) -> list[dict]:
    result = []
    for doc in events.where("studentUid", "==", student_uid).stream():
        item = doc.to_dict() or {}
        # Older History clients incorrectly counted background mastery and
        # recommendation requests as answered questions. Those generated rows
        # have no score, percentage or duration, so hide only that known-empty
        # legacy shape while preserving real quiz and essay results.
        is_legacy_history_background_event = (
            item.get("subject") == "history"
            and item.get("activityType") == "practice"
            and item.get("title") == "History practice"
            and item.get("percentage") is None
            and item.get("score") is None
            and item.get("maxScore") is None
            and not float(item.get("durationMinutes") or 0)
        )
        if is_legacy_history_background_event:
            continue
        item["id"] = doc.id
        item["createdAt"] = serialize_timestamp(item.get("createdAt"))
        result.append(item)
    result.sort(key=lambda item: item.get("createdAt") or "", reverse=True)
    return result


def summarize_subject(items: list[dict], subject: str) -> dict:
    subject_items = [item for item in items if item.get("subject") == subject]
    scored = [float(item["percentage"]) for item in subject_items if item.get("percentage") is not None]
    return {
        "subject": subject,
        "label": SUBJECT_LABELS[subject],
        "attempts": len(subject_items),
        "average_score": round(sum(scored) / len(scored), 1) if scored else None,
        "questions_answered": sum(int(item.get("questionsAnswered") or 0) for item in subject_items),
        "minutes_spent": round(sum(float(item.get("durationMinutes") or 0) for item in subject_items), 1),
        "last_active": subject_items[0].get("createdAt") if subject_items else None,
    }


def student_summary(student: dict) -> dict:
    items = student_events(student["uid"])
    scored = [float(item["percentage"]) for item in items if item.get("percentage") is not None]
    return {
        "student": public_profile(student),
        "overall": {
            "average_score": round(sum(scored) / len(scored), 1) if scored else None,
            "activities": len(items),
            "questions_answered": sum(int(item.get("questionsAnswered") or 0) for item in items),
            "minutes_spent": round(sum(float(item.get("durationMinutes") or 0) for item in items), 1),
        },
        "subjects": [summarize_subject(items, subject) for subject in sorted(VALID_SUBJECTS)],
        "recent_activity": items[:8],
    }


def linked_student_uids(owner_uid: str, owner_role: str) -> list[str]:
    linked = []
    for doc in relationships.where("ownerUid", "==", owner_uid).stream():
        data = doc.to_dict() or {}
        if data.get("ownerRole") == owner_role and data.get("status") == "active":
            linked.append(data.get("studentUid"))
    if owner_role == "teacher" and not linked:
        return [doc.id for doc in users.where("role", "==", "student").stream()]
    return [uid for uid in linked if uid]


def may_view_student(viewer: dict, student_uid: str) -> bool:
    if viewer.get("role") == "student":
        return viewer["uid"] == student_uid
    return student_uid in linked_student_uids(viewer["uid"], viewer.get("role", ""))


@app.get("/")
@app.get("/health")
def health():
    return {"status": "ok", "service": "easylearn-platform", "version": "2.0.0", "database": "firestore"}


@app.post("/auth/session")
def create_session(payload: SessionRequest, response: Response):
    try:
        decoded = auth.verify_id_token(payload.id_token)
        profile = ensure_profile(decoded, payload.requested_role)
        session_cookie = auth.create_session_cookie(payload.id_token, expires_in=SESSION_LENGTH)
        if isinstance(session_cookie, bytes):
            session_cookie = session_cookie.decode("utf-8")
        response.set_cookie(
            key=COOKIE_NAME, value=session_cookie,
            max_age=int(SESSION_LENGTH.total_seconds()), httponly=True,
            secure=cookie_secure, samesite="lax", path="/",
        )
        return {"status": "ok", "user": public_profile(profile)}
    except HTTPException:
        raise
    except Exception as error:
        raise HTTPException(401, "Firebase sign-in token is invalid.") from error


@app.get("/auth/me")
def get_current_user(request: Request):
    return {"authenticated": True, "user": public_profile(current_profile(request))}


@app.post("/auth/custom-token")
def create_custom_token(request: Request):
    profile = current_profile(request)
    token = auth.create_custom_token(profile["uid"], {"role": profile.get("role", "student")})
    if isinstance(token, bytes):
        token = token.decode("utf-8")
    return {"custom_token": token, "user": public_profile(profile)}


@app.post("/auth/logout")
def logout(response: Response):
    response.delete_cookie(COOKIE_NAME, path="/", secure=cookie_secure, httponly=True, samesite="lax")
    return {"status": "ok", "message": "EasyLearn session cleared."}


@app.get("/dashboard/overview")
def dashboard_overview(request: Request):
    profile = current_profile(request)
    role = profile.get("role")
    if role == "student":
        return {"role": role, **student_summary(profile)}

    summaries = []
    for uid in linked_student_uids(profile["uid"], role):
        student = get_profile(uid)
        if student and student.get("role") == "student":
            summaries.append(student_summary(student))
    scored = [s["overall"]["average_score"] for s in summaries if s["overall"]["average_score"] is not None]
    return {
        "role": role,
        "viewer": public_profile(profile),
        "cohort": {
            "students": len(summaries),
            "average_score": round(sum(scored) / len(scored), 1) if scored else None,
            "activities": sum(s["overall"]["activities"] for s in summaries),
            "questions_answered": sum(s["overall"]["questions_answered"] for s in summaries),
        },
        "students": summaries,
    }


@app.get("/dashboard/students/{student_uid}")
def student_dashboard(student_uid: str, request: Request):
    viewer = current_profile(request)
    if not may_view_student(viewer, student_uid):
        raise HTTPException(403, "You are not allowed to view this student.")
    student = get_profile(student_uid)
    if not student or student.get("role") != "student":
        raise HTTPException(404, "Student was not found.")
    return student_summary(student)


@app.get("/relationships/students")
def list_students(request: Request):
    viewer = current_profile(request, {"teacher", "parent"})
    result = []
    for uid in linked_student_uids(viewer["uid"], viewer["role"]):
        student = get_profile(uid)
        if student:
            result.append(public_profile(student))
    return {"students": result}


@app.post("/relationships/students/link")
def link_student(payload: LinkStudentRequest, request: Request):
    viewer = current_profile(request, {"teacher", "parent"})
    matches = list(users.where("studentCode", "==", payload.student_code.strip().upper()).limit(1).stream())
    if not matches:
        raise HTTPException(404, "No student was found with that EasyLearn code.")
    student_doc = matches[0]
    student = student_doc.to_dict() or {}
    if student.get("role") != "student":
        raise HTTPException(400, "That code does not belong to a student.")
    relationships.document(f"{viewer['uid']}_{student_doc.id}").set(
        {
            "ownerUid": viewer["uid"], "ownerRole": viewer["role"],
            "studentUid": student_doc.id, "nickname": payload.nickname,
            "createdAt": utc_now(), "status": "active",
        }, merge=True,
    )
    student["uid"] = student_doc.id
    return {"status": "linked", "student": public_profile(student)}


@app.delete("/relationships/students/{student_uid}")
def unlink_student(student_uid: str, request: Request):
    viewer = current_profile(request, {"teacher", "parent"})
    relationships.document(f"{viewer['uid']}_{student_uid}").delete()
    return {"status": "unlinked"}


@app.post("/events")
def record_event(payload: LearningEventRequest, request: Request):
    student = current_profile(request, {"student"})
    percentage = payload.percentage
    if percentage is None and payload.score is not None and payload.max_score:
        percentage = max(0, min(100, (payload.score / payload.max_score) * 100))
    event = {
        "studentUid": student["uid"],
        "accountId": profile_account_id(student),
        "role": "student",
        "subject": payload.subject,
        "activityType": payload.activity_type, "title": payload.title,
        "score": payload.score, "maxScore": payload.max_score,
        "percentage": round(percentage, 2) if percentage is not None else None,
        "questionsAnswered": payload.questions_answered,
        "durationMinutes": payload.duration_minutes,
        "metadata": payload.metadata,
        "schemaVersion": 2,
        "createdAt": utc_now(),
    }
    reference = events.add(event)[1]
    # History's detailed dashboard reads this compatibility collection. It is
    # still Firestore; learning_events remains the canonical platform record.
    if payload.subject == "history" and payload.activity_type == "practice":
        metadata = payload.metadata or {}
        is_correct = metadata.get("is_correct")
        if is_correct is None and event["percentage"] is not None:
            is_correct = event["percentage"] >= 50
        db.collection("user_interactions").add(
            {
                "user_uid": student["uid"],
                "account_id": profile_account_id(student),
                "question_id": metadata.get("question_id"),
                "chapter_id": metadata.get("chapter_id"),
                "is_correct": bool(is_correct),
                "time_taken_ms": round(payload.duration_minutes * 60_000),
                "score": payload.score,
                "max_score": payload.max_score,
                "percentage": event["percentage"],
                "timestamp": event["createdAt"],
                "source_event_id": reference.id,
            }
        )
    return {"status": "saved", "event_id": reference.id}
