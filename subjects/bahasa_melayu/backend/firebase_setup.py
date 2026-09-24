"""Cloud/local Firebase Admin bootstrap for EasyLearn backends."""
import base64
import json
import os
from pathlib import Path

import firebase_admin
from firebase_admin import credentials


def _service_account_dict(raw: str) -> dict:
    data = json.loads(raw)
    if "private_key" in data and isinstance(data["private_key"], str):
        data["private_key"] = data["private_key"].replace("\\n", "\n")
    return data


def initialize_firebase_admin(base_dir: Path | None = None, required: bool = True, default_path: Path | None = None) -> bool:
    """Initialize firebase_admin from JSON, base64, a file path, or ADC.

    Production-friendly preference order:
      FIREBASE_SERVICE_ACCOUNT_JSON
      FIREBASE_SERVICE_ACCOUNT_BASE64
      FIREBASE_SERVICE_ACCOUNT_PATH / FIREBASE_CREDENTIALS_PATH
      default_path (local compatibility)
      FIREBASE_USE_ADC=true
    """
    if firebase_admin._apps:
        return True

    raw_json = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON", "").strip()
    raw_b64 = os.getenv("FIREBASE_SERVICE_ACCOUNT_BASE64", "").strip()
    raw_path = (
        os.getenv("FIREBASE_SERVICE_ACCOUNT_PATH", "").strip()
        or os.getenv("FIREBASE_CREDENTIALS_PATH", "").strip()
    )
    use_adc = os.getenv("FIREBASE_USE_ADC", "false").lower() == "true"

    try:
        if raw_json:
            firebase_admin.initialize_app(credentials.Certificate(_service_account_dict(raw_json)))
            return True
        if raw_b64:
            decoded = base64.b64decode(raw_b64).decode("utf-8")
            firebase_admin.initialize_app(credentials.Certificate(_service_account_dict(decoded)))
            return True
        if raw_path:
            path = Path(raw_path)
            if not path.is_absolute() and base_dir:
                path = base_dir / path
            if not path.is_file():
                raise RuntimeError(f"Firebase credential file was not found: {path}")
            firebase_admin.initialize_app(credentials.Certificate(str(path)))
            return True
        if default_path and default_path.is_file():
            firebase_admin.initialize_app(credentials.Certificate(str(default_path)))
            return True
        if use_adc:
            firebase_admin.initialize_app()
            return True
    except Exception:
        if required:
            raise
        return False

    if required:
        raise RuntimeError(
            "Firebase Admin credentials are missing. Set FIREBASE_SERVICE_ACCOUNT_JSON, "
            "FIREBASE_SERVICE_ACCOUNT_BASE64, FIREBASE_SERVICE_ACCOUNT_PATH, or FIREBASE_USE_ADC=true."
        )
    return False
