"""PyMongo-shaped Firestore adapter for the existing BM services.

The BM code uses only a small subset of collection methods. Keeping those
method names preserves all assessment features while moving sessions, results
and users into the same Firestore project as the EasyLearn portal.
"""

from __future__ import annotations

import os
import uuid
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Iterable

import firebase_admin
from dotenv import load_dotenv
from firebase_admin import firestore
from firebase_setup import initialize_firebase_admin


load_dotenv()

client = None
db = None
connected = False
users_col = None
essay_sessions_col = None
essay_results_col = None
comprehension_sessions_col = None
comprehension_results_col = None
speaking_sessions_col = None
speaking_results_col = None
listening_sessions_col = None
listening_results_col = None
user_results_col = None


def _matches(document: dict[str, Any], query: dict[str, Any]) -> bool:
    for key, expected in (query or {}).items():
        actual = document.get(key)
        if isinstance(expected, dict):
            for operator, value in expected.items():
                if operator == "$gt" and not (actual is not None and actual > value):
                    return False
                if operator == "$lt" and not (actual is not None and actual < value):
                    return False
                if operator == "$gte" and not (actual is not None and actual >= value):
                    return False
                if operator == "$lte" and not (actual is not None and actual <= value):
                    return False
                if operator == "$in" and actual not in value:
                    return False
        elif actual != expected:
            return False
    return True


def _project(document: dict[str, Any], projection: dict[str, int] | None):
    if not projection:
        return deepcopy(document)
    excluded = {key for key, enabled in projection.items() if not enabled}
    included = {key for key, enabled in projection.items() if enabled}
    if included:
        return {key: deepcopy(value) for key, value in document.items() if key in included or key == "_id"}
    return {key: deepcopy(value) for key, value in document.items() if key not in excluded}


class FirestoreCollection:
    def __init__(self, name: str):
        self.reference = db.collection(name)

    def create_index(self, *args, **kwargs):
        return None

    def _documents(self) -> Iterable[tuple[Any, dict[str, Any]]]:
        for snapshot in self.reference.stream():
            data = snapshot.to_dict() or {}
            data["_id"] = snapshot.id
            yield snapshot.reference, data

    def find_one(self, query=None, projection=None, sort=None):
        matches = [data for _, data in self._documents() if _matches(data, query or {})]
        for field, direction in reversed(sort or []):
            matches.sort(key=lambda value: value.get(field) or "", reverse=direction < 0)
        return _project(matches[0], projection) if matches else None

    def find(self, query=None, projection=None):
        return [_project(data, projection) for _, data in self._documents() if _matches(data, query or {})]

    def insert_one(self, document):
        data = deepcopy(document)
        preferred = data.pop("_id", None) or data.get("firebase_uid") or data.get("session_id")
        doc_id = str(preferred or uuid.uuid4().hex)
        self.reference.document(doc_id).set(data)
        return SimpleNamespace(inserted_id=doc_id)

    def update_one(self, query, update, upsert=False):
        for reference, data in self._documents():
            if _matches(data, query):
                reference.set(deepcopy(update.get("$set", update)), merge=True)
                return SimpleNamespace(matched_count=1, modified_count=1)
        if upsert:
            payload = {key: value for key, value in query.items() if not isinstance(value, dict)}
            payload.update(deepcopy(update.get("$set", update)))
            result = self.insert_one(payload)
            return SimpleNamespace(matched_count=0, modified_count=0, upserted_id=result.inserted_id)
        return SimpleNamespace(matched_count=0, modified_count=0)

    def update_many(self, query, update):
        count = 0
        values = deepcopy(update.get("$set", update))
        for reference, data in self._documents():
            if _matches(data, query):
                reference.set(values, merge=True)
                count += 1
        return SimpleNamespace(matched_count=count, modified_count=count)

    def replace_one(self, query, document, upsert=False):
        for reference, data in self._documents():
            if _matches(data, query):
                reference.set(deepcopy(document))
                return SimpleNamespace(matched_count=1, modified_count=1)
        if upsert:
            result = self.insert_one(document)
            return SimpleNamespace(matched_count=0, modified_count=0, upserted_id=result.inserted_id)
        return SimpleNamespace(matched_count=0, modified_count=0)


def connect_firestore():
    global client, db, connected
    global users_col, essay_sessions_col, essay_results_col
    global comprehension_sessions_col, comprehension_results_col
    global speaking_sessions_col, speaking_results_col
    global listening_sessions_col, listening_results_col, user_results_col

    if connected:
        return
    initialize_firebase_admin(base_dir=Path(__file__).resolve().parent, required=True)

    db = firestore.client()
    client = db
    users_col = FirestoreCollection("easylearn_users")
    essay_sessions_col = FirestoreCollection("bm_essay_sessions")
    essay_results_col = FirestoreCollection("bm_essay_results")
    comprehension_sessions_col = FirestoreCollection("bm_comprehension_sessions")
    comprehension_results_col = FirestoreCollection("bm_comprehension_results")
    speaking_sessions_col = FirestoreCollection("bm_speaking_sessions")
    speaking_results_col = FirestoreCollection("bm_speaking_results")
    listening_sessions_col = FirestoreCollection("bm_listening_sessions")
    listening_results_col = FirestoreCollection("bm_listening_results")
    user_results_col = FirestoreCollection("bm_user_results")
    connected = True
    print("✅ Bahasa Melayu connected to EasyLearn Firestore")


def connect_mongo():
    """Compatibility entrypoint retained for main.py."""
    connect_firestore()


def start_db():
    connect_firestore()
