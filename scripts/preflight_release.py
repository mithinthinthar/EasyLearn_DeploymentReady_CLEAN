from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

FORBIDDEN_NAMES = {".env", ".env.local"}
FORBIDDEN_SUFFIXES = {".pem", ".key", ".crt", ".p12", ".pfx"}
FORBIDDEN_DIRS = {"node_modules", ".venv", "venv", "__pycache__", ".git", ".vercel", "dist", "build"}

# These patterns target credentials that should never be in the sanitized release.
SECRET_PATTERNS = [
    ("private key", re.compile(r"-----BEGIN (?:RSA )?PRIVATE KEY-----")),
    ("OpenAI-style secret", re.compile(r"\bsk-[A-Za-z0-9_-]{20,}")),
    ("MongoDB credentials", re.compile(r"mongodb(?:\+srv)?://[^\s:/]+:[^\s@]+@", re.I)),
]

# Public Firebase Web API keys are intentionally not treated as secrets here.
TEXT_SUFFIXES = {
    ".py", ".js", ".jsx", ".ts", ".tsx", ".json", ".md", ".txt", ".html", ".css",
    ".yml", ".yaml", ".toml", ".ini", ".cfg", ".mjs", ".cjs", ".ps1", ".sh"
}

errors: list[str] = []
python_files = 0

for path in ROOT.rglob("*"):
    rel = path.relative_to(ROOT)
    if any(part in FORBIDDEN_DIRS for part in rel.parts):
        continue
    if not path.is_file():
        continue

    if path.name in FORBIDDEN_NAMES:
        errors.append(f"forbidden local env file: {rel}")
    if path.suffix.lower() in FORBIDDEN_SUFFIXES:
        errors.append(f"forbidden credential/certificate file: {rel}")
    low_name = path.name.lower()
    if ("service-account" in low_name or "service_account" in low_name or "firebase-admin" in low_name) and path.suffix.lower() == ".json":
        errors.append(f"possible Firebase Admin credential file: {rel}")

    if path.suffix.lower() == ".py":
        try:
            ast.parse(path.read_text(encoding="utf-8", errors="strict"), filename=str(rel))
            python_files += 1
        except Exception as exc:
            errors.append(f"Python syntax/read error in {rel}: {exc}")

    if path.suffix.lower() in TEXT_SUFFIXES or path.name.startswith(".env.example"):
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        for label, pattern in SECRET_PATTERNS:
            if pattern.search(text):
                errors.append(f"possible {label} in {rel}")

required = [
    ROOT / "vercel.mjs",
    ROOT / "scripts" / "build-all.mjs",
    ROOT / "deploy" / "DEPLOYMENT-GUIDE.md",
    ROOT / "deploy" / "FINAL-TEST-CHECKLIST.md",
    ROOT / "shared" / "auth" / "Dockerfile",
    ROOT / "subjects" / "history" / "backend" / "Dockerfile",
    ROOT / "subjects" / "mathematics" / "backend" / "Dockerfile",
    ROOT / "subjects" / "bahasa_melayu" / "backend" / "Dockerfile",
]
for item in required:
    if not item.exists():
        errors.append(f"missing required deployment file: {item.relative_to(ROOT)}")

if errors:
    print("PRE-FLIGHT FAILED")
    for err in errors:
        print(f"- {err}")
    sys.exit(1)

print("PRE-FLIGHT PASSED")
print(f"Python files parsed: {python_files}")
print("No private env/certificate/service-account files detected.")
print("No high-confidence secret patterns detected (Firebase Web API keys are intentionally allowed).")
