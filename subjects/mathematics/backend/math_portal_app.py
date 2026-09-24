from __future__ import annotations

import secrets

from flask import jsonify, request

from firebase_admin import firestore

from app import app, verify_firebase_token
from config import get_db_connection


def generate_student_code(cursor) -> str:
    for _ in range(30):
        student_code = f"STU-{secrets.randbelow(10_000_000):07d}"

        cursor.execute(
            "SELECT id FROM users WHERE student_code = %s LIMIT 1",
            (student_code,),
        )

        if cursor.fetchone() is None:
            return student_code

    raise RuntimeError("Unable to create a unique student code")


def user_json(user: dict) -> dict:
    return {
        "id": user["id"],
        "firebase_uid": user.get("firebase_uid"),
        "name": user.get("name"),
        "email": user.get("email"),
        "role": user.get("role"),
        "language": user.get("language"),
        "auth_provider": user.get("auth_provider"),
        "photo_url": user.get("photo_url"),
        "student_code": user.get("student_code"),
        "is_active": bool(user.get("is_active", 1)),
    }


@app.route(
    "/api/auth/portal-login",
    methods=["POST", "OPTIONS"],
)
def portal_login():
    if request.method == "OPTIONS":
        return "", 204

    data = request.get_json(silent=True) or {}
    token = data.get("token")
    supplied_picture = data.get("photo_url")

    if not token:
        return jsonify(
            {
                "success": False,
                "message": "Firebase token is required.",
            }
        ), 400

    connection = None
    cursor = None

    try:
        decoded = verify_firebase_token(token)

        firebase_uid = decoded.get("uid")
        email = (decoded.get("email") or "").strip().lower()
        email_verified = bool(decoded.get("email_verified"))
        name = (decoded.get("name") or "").strip()
        picture = supplied_picture or decoded.get("picture")
        shared_snapshot = firestore.client().collection("easylearn_users").document(firebase_uid).get()
        shared_profile = shared_snapshot.to_dict() if shared_snapshot.exists else {}
        portal_role = shared_profile.get("role") or decoded.get("role", "student")
        if portal_role not in {"student", "teacher", "parent"}:
            portal_role = "student"
        name = shared_profile.get("name") or name
        picture = shared_profile.get("picture") or picture
        shared_account_id = shared_profile.get("accountId") or shared_profile.get("studentCode")

        if not firebase_uid or not email:
            return jsonify(
                {
                    "success": False,
                    "message": "Firebase account information is incomplete.",
                }
            ), 401

        if not email_verified:
            return jsonify(
                {
                    "success": False,
                    "message": "The Google email is not verified.",
                }
            ), 403

        if not name:
            name = (
                email.split("@")[0]
                .replace(".", " ")
                .replace("_", " ")
                .replace("-", " ")
                .title()
            )

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        # First try the permanent Firebase UID.
        cursor.execute(
            """
            SELECT *
            FROM users
            WHERE firebase_uid = %s
            LIMIT 1
            """,
            (firebase_uid,),
        )

        user = cursor.fetchone()

        # If this is the account's first Portal login, match its email.
        if user is None:
            cursor.execute(
                """
                SELECT *
                FROM users
                WHERE email = %s
                LIMIT 1
                """,
                (email,),
            )

            user = cursor.fetchone()

        if user is None:
            student_code = shared_account_id if portal_role == "student" else None

            cursor.execute(
                """
                INSERT INTO users (
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
                VALUES (
                    %s,
                    %s,
                    %s,
                    %s,
                    'english',
                    'google',
                    %s,
                    %s,
                    1
                )
                """,
                (
                    firebase_uid,
                    name,
                    email,
                    portal_role,
                    picture,
                    student_code,
                ),
            )

            connection.commit()
            new_user_id = cursor.lastrowid

            cursor.execute(
                """
                SELECT *
                FROM users
                WHERE id = %s
                LIMIT 1
                """,
                (new_user_id,),
            )

            user = cursor.fetchone()

        else:
            # The shared Portal is authoritative for the account role.
            cursor.execute(
                """
                UPDATE users
                SET
                    firebase_uid = %s,
                    name = %s,
                    photo_url = COALESCE(%s, photo_url),
                    role = %s,
                    student_code = %s,
                    is_active = 1
                WHERE id = %s
                """,
                (
                    firebase_uid,
                    name,
                    picture,
                    portal_role,
                    shared_account_id if portal_role == "student" else None,
                    user["id"],
                ),
            )

            connection.commit()

            cursor.execute(
                """
                SELECT *
                FROM users
                WHERE id = %s
                LIMIT 1
                """,
                (user["id"],),
            )

            user = cursor.fetchone()

        return jsonify(
            {
                "success": True,
                "user": user_json(user),
            }
        ), 200

    except Exception as error:
        if connection is not None:
            connection.rollback()

        print("PORTAL MATHEMATICS LOGIN ERROR:", error)

        return jsonify(
            {
                "success": False,
                "message": str(error),
            }
        ), 500

    finally:
        if cursor is not None:
            cursor.close()

        if connection is not None:
            connection.close()
