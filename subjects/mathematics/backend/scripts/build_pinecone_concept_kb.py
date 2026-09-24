from __future__ import annotations

import os
import re
import sys
from pathlib import Path
from typing import Dict, List
import time

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(BACKEND_DIR))

from dotenv import load_dotenv
from pinecone_client import index, CONCEPT_NAMESPACE
from embeddings import embed_text

load_dotenv()

RAW_DIR = BACKEND_DIR / "knowledge_base" / "raw"
PROGRESS_FILE = BACKEND_DIR / "knowledge_base" / "ingested_concept_files.txt"

#set True if want to wipe ONLY concept namespace before rebuild
RESET_NAMESPACE_BEFORE_INGEST = False

# For files that don't follow the naming convention, define their metadata manually here
SPECIAL_FILE_METADATA = {
    "lower_secondary_foundations": {
        "topic": "Lower Secondary Foundations",
        "form": "Lower Secondary Bridge",
        "chapter_no": 0,
        "chapter_label": "Foundations",
        "content_type": "foundation_review",
        "category": "foundations",
    },
    "exam_format_and_rules": {
        "topic": "Exam Format and Rules",
        "form": "SPM General",
        "chapter_no": 0,
        "chapter_label": "Exam Strategy",
        "content_type": "exam_guide",
        "category": "exam_strategy",
    },
    "kbat_strategies": {
        "topic": "KBAT Strategies",
        "form": "SPM General",
        "chapter_no": 0,
        "chapter_label": "Exam Strategy",
        "content_type": "exam_strategy",
        "category": "exam_strategy",
    },
    "calculator_techniques": {
        "topic": "Calculator Techniques",
        "form": "SPM General",
        "chapter_no": 0,
        "chapter_label": "Practical Guide",
        "content_type": "practical_guide",
        "category": "exam_strategy",
    },
    "common_student_mistakes": {
        "topic": "Common Student Mistakes",
        "form": "SPM General",
        "chapter_no": 0,
        "chapter_label": "Exam Strategy",
        "content_type": "mistake_guide",
        "category": "exam_strategy",
    },
    "formula_sheet_guide": {
        "topic": "Formula Sheet Guide",
        "form": "SPM General",
        "chapter_no": 0,
        "chapter_label": "Exam Strategy",
        "content_type": "formula_guide",
        "category": "exam_strategy",
    },
    "kssm_mathematics_chapters": {
        "topic": "KSSM Mathematics Chapters",
        "form": "SPM General",
        "chapter_no": 0,
        "chapter_label": "Curriculum Map",
        "content_type": "chapter_map",
        "category": "curriculum_reference",
    },
}


def slug_to_title(slug: str) -> str:
    return slug.replace("_", " ").strip().title()


def infer_metadata(md_file: Path) -> Dict:
    stem = md_file.stem

    if stem in SPECIAL_FILE_METADATA:
        meta = SPECIAL_FILE_METADATA[stem].copy()
    else:
        match = re.match(r"f(?P<form>\d)_c(?P<chapter>\d+)_(?P<topic>.+)", stem)
        if not match:
            meta = {
                "topic": slug_to_title(stem),
                "form": "Unknown",
                "chapter_no": 0,
                "chapter_label": "Unknown",
                "content_type": "topic_notes",
                "category": "unknown",
            }
        else:
            form_no = match.group("form")
            chapter_no = int(match.group("chapter"))
            topic_slug = match.group("topic")

            meta = {
                "topic": slug_to_title(topic_slug),
                "form": f"Form {form_no}",
                "chapter_no": chapter_no,
                "chapter_label": f"Form {form_no} Chapter {chapter_no}",
                "content_type": "topic_notes",
                "category": f"form{form_no}_syllabus",
            }

    meta.update(
        {
            "kb_type": "concept_notes",
            "language": "english",
            "curriculum": "SPM Mathematics",
            "source_file": md_file.name,
            "source_path": str(md_file.relative_to(BACKEND_DIR)).replace("\\", "/"),
        }
    )
    return meta


def split_markdown_sections(text: str) -> List[str]:
    text = text.strip()
    if not text:
        return []

    # Split on markdown headings but keep the heading in each section
    parts = re.split(r"(?=^#{1,6}\s)", text, flags=re.MULTILINE)
    sections = [part.strip() for part in parts if part.strip()]
    return sections


def chunk_sections(sections: List[str], chunk_size: int = 1800, overlap: int = 250) -> List[str]:
    if not sections:
        return []

    chunks = []
    current = ""

    for section in sections:
        if not current:
            current = section
            continue

        if len(current) + 2 + len(section) <= chunk_size:
            current += "\n\n" + section
        else:
            chunks.append(current.strip())
            tail = current[-overlap:] if overlap > 0 else ""
            current = (tail + "\n\n" + section).strip()

    if current.strip():
        chunks.append(current.strip())

    return chunks


def prepare_vectors(md_file: Path) -> List[Dict]:
    text = md_file.read_text(encoding="utf-8").strip()
    if not text:
        return []

    metadata_base = infer_metadata(md_file)
    sections = split_markdown_sections(text)
    chunks = chunk_sections(sections)

    vectors = []

    for i, chunk in enumerate(chunks):
        embedding = embed_text(chunk)
        time.sleep(1)
        if not embedding:
            continue

        record_id = f"concept::{md_file.stem}::chunk_{i:03d}"

        metadata = metadata_base.copy()
        metadata["chunk_index"] = i
        metadata["chunk_text"] = chunk[:35000] 

        vectors.append(
            {
                "id": record_id,
                "values": embedding,
                "metadata": metadata,
            }
        )

    return vectors

def main():
    if not RAW_DIR.exists():
        raise FileNotFoundError(f"Raw KB folder not found: {RAW_DIR}")

    md_files = sorted(RAW_DIR.rglob("*.md"))
    completed_files = load_completed_files()
    if not md_files:
        print("No .md files found.")
        return

    if RESET_NAMESPACE_BEFORE_INGEST:
        print(f"Deleting all records in namespace: {CONCEPT_NAMESPACE}")
        index.delete(delete_all=True, namespace=CONCEPT_NAMESPACE)

    total_files = 0
    total_chunks = 0

    for md_file in md_files:
        if md_file.name in completed_files:
            print(f"Skipping already completed file: {md_file.name}")
            continue

        vectors = prepare_vectors(md_file)
        if not vectors:
            continue

        print("UPSERTING TO NAMESPACE =", CONCEPT_NAMESPACE)

        index.upsert(vectors=vectors, namespace=CONCEPT_NAMESPACE)

        total_files += 1
        total_chunks += len(vectors)
        print(f"Upserted {len(vectors)} chunks from {md_file.name}")
        mark_file_completed(md_file)

    print("\nDone.")
    print(f"Namespace: {CONCEPT_NAMESPACE}")
    print(f"Files processed: {total_files}")
    print(f"Chunks upserted: {total_chunks}")


def load_completed_files() -> set[str]:
    if not PROGRESS_FILE.exists():
        return set()
    return set(
        line.strip()
        for line in PROGRESS_FILE.read_text(encoding="utf-8").splitlines()
        if line.strip()
    )


def mark_file_completed(md_file: Path) -> None:
    PROGRESS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with PROGRESS_FILE.open("a", encoding="utf-8") as f:
        f.write(md_file.name + "\n")

if __name__ == "__main__":
    main()