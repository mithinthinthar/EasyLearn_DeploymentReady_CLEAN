from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, EmailStr
from google.oauth2 import id_token
from google.auth.transport import requests
from datetime import datetime
import os
import hmac
import hashlib
import secrets
import database
from pathlib import Path
import firebase_admin
from firebase_admin import auth as firebase_auth, firestore as firebase_firestore
from firebase_setup import initialize_firebase_admin

router = APIRouter()


def ensure_firebase_admin():
    try:
        initialize_firebase_admin(base_dir=Path(__file__).resolve().parents[1], required=True)
    except Exception as error:
        raise HTTPException(status_code=503, detail="Firebase Admin credentials are not configured for Bahasa Melayu") from error


class GoogleLoginRequest(BaseModel):
    token: str


class EmailRegisterRequest(BaseModel):
    email: EmailStr
    password: str


class EmailLoginRequest(BaseModel):
    email: EmailStr
    password: str


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)

    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        100_000,
    ).hex()

    return f"{salt}${password_hash}"


def verify_password(password: str, stored_password: str) -> bool:
    try:
        salt, password_hash = stored_password.split("$", 1)

        check_hash = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt.encode("utf-8"),
            100_000,
        ).hex()

        return hmac.compare_digest(check_hash, password_hash)
    except Exception:
        return False


def validate_password(password: str):
    if len(password) < 6:
        raise HTTPException(
            status_code=400,
            detail="Password must be at least 6 characters",
        )


def merge_auth_provider(current_provider, new_provider: str) -> str:
    providers = set()

    if current_provider:
        for provider in str(current_provider).split(","):
            provider = provider.strip()
            if provider:
                providers.add(provider)

    providers.add(new_provider)

    return ",".join(sorted(providers))


def user_response(user_id: str, email: str, picture=None, role="student", name=None, student_code=None):
    return {
        "user_id": user_id,
        "email": email,
        "picture": picture,
        "role": role,
        "name": name,
        "student_code": student_code,
    }


@router.post("/portal-login")
def portal_login(request: Request):
    """Use the HttpOnly session created by the one EasyLearn Portal login."""
    if database.users_col is None:
        raise HTTPException(status_code=500, detail="Database not connected yet")
    ensure_firebase_admin()
    session_cookie = request.cookies.get("easylearn_session")
    if not session_cookie:
        raise HTTPException(status_code=401, detail="EasyLearn Portal session was not found")
    try:
        decoded = firebase_auth.verify_session_cookie(session_cookie, check_revoked=True)
    except Exception as error:
        raise HTTPException(status_code=401, detail="EasyLearn Portal session is invalid") from error

    firebase_uid = decoded["uid"]
    email = (decoded.get("email") or "").strip().lower()
    name = decoded.get("name") or email.split("@")[0]
    picture = decoded.get("picture")
    profile = firebase_firestore.client().collection("easylearn_users").document(firebase_uid).get()
    profile_data = profile.to_dict() if profile.exists else {}
    role = profile_data.get("role", "student")
    name = profile_data.get("name") or name
    picture = profile_data.get("picture") or picture
    user = database.users_col.find_one({"firebase_uid": firebase_uid}) or database.users_col.find_one({"email": email})
    student_code = profile_data.get("studentCode") if role == "student" else None
    account_id = profile_data.get("accountId") or student_code
    fields = {"firebase_uid": firebase_uid, "email": email, "name": name, "picture": picture, "role": role, "accountId": account_id, "last_login_at": datetime.utcnow()}
    if user:
        database.users_col.update_one({"_id": user["_id"]}, {"$set": fields})
        user_id = str(user["_id"])
    else:
        fields.update({"auth_provider": "firebase_portal", "created_at": datetime.utcnow()})
        user_id = str(database.users_col.insert_one(fields).inserted_id)
    return user_response(user_id, email, picture, role, name, student_code)


@router.post("/register")
def register(data: EmailRegisterRequest):
    if database.users_col is None:
        raise HTTPException(status_code=500, detail="Database not connected yet")

    email = data.email.strip().lower()
    password = data.password.strip()

    validate_password(password)

    existing_user = database.users_col.find_one({"email": email})

    if existing_user:
        if existing_user.get("password_hash"):
            raise HTTPException(
                status_code=409,
                detail="Email already registered. Please sign in.",
            )

        database.users_col.update_one(
            {"_id": existing_user["_id"]},
            {
                "$set": {
                    "password_hash": hash_password(password),
                    "auth_provider": merge_auth_provider(
                        existing_user.get("auth_provider"),
                        "email",
                    ),
                    "last_login_at": datetime.utcnow(),
                }
            },
        )

        return user_response(
            str(existing_user["_id"]),
            existing_user["email"],
            existing_user.get("picture"),
        )

    result = database.users_col.insert_one(
        {
            "email": email,
            "password_hash": hash_password(password),
            "auth_provider": "email",
            "created_at": datetime.utcnow(),
            "last_login_at": datetime.utcnow(),
        }
    )

    return user_response(str(result.inserted_id), email)


@router.post("/email-login")
def email_login(data: EmailLoginRequest):
    if database.users_col is None:
        raise HTTPException(status_code=500, detail="Database not connected yet")

    email = data.email.strip().lower()
    password = data.password.strip()

    user = database.users_col.find_one({"email": email})

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password. Please sign up first.",
        )

    password_hash = user.get("password_hash")

    if not password_hash:
        raise HTTPException(
            status_code=409,
            detail="This email was created with Google. Click Sign up once to add a password, or continue with Google.",
        )

    if not verify_password(password, password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    database.users_col.update_one(
        {"_id": user["_id"]},
        {"$set": {"last_login_at": datetime.utcnow()}},
    )

    return user_response(
        str(user["_id"]),
        user["email"],
        user.get("picture"),
    )


@router.post("/login")
def login(data: GoogleLoginRequest):
    if database.users_col is None:
        raise HTTPException(status_code=500, detail="Database not connected yet")

    google_client_id = os.getenv("GOOGLE_CLIENT_ID", "").strip()

    if not google_client_id:
        raise HTTPException(status_code=500, detail="GOOGLE_CLIENT_ID is not configured")

    try:
        idinfo = id_token.verify_oauth2_token(
            data.token,
            requests.Request(),
            google_client_id,
        )
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid Google token")

    email = (idinfo.get("email") or "").strip().lower()
    email_verified = bool(idinfo.get("email_verified"))
    picture = idinfo.get("picture")
    name = idinfo.get("name")

    if not email:
        raise HTTPException(status_code=401, detail="Google account email not found")

    if not email_verified:
        raise HTTPException(status_code=401, detail="Google email is not verified")

    user = database.users_col.find_one({"email": email})

    if not user:
        result = database.users_col.insert_one(
            {
                "email": email,
                "google_sub": idinfo.get("sub"),
                "name": name,
                "picture": picture,
                "auth_provider": "google",
                "created_at": datetime.utcnow(),
                "last_login_at": datetime.utcnow(),
            }
        )

        return user_response(str(result.inserted_id), email, picture)

    database.users_col.update_one(
        {"_id": user["_id"]},
        {
            "$set": {
                "google_sub": idinfo.get("sub"),
                "name": name,
                "picture": picture,
                "auth_provider": merge_auth_provider(
                    user.get("auth_provider"),
                    "google",
                ),
                "last_login_at": datetime.utcnow(),
            }
        },
    )

    return user_response(str(user["_id"]), email, picture)
