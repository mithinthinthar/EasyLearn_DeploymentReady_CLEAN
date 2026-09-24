from __future__ import annotations

import re
import sys
from collections import Counter
from pathlib import Path
from typing import List

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(BACKEND_DIR))

from pinecone_client import index, CONCEPT_NAMESPACE

RAW_DIR = BACKEND_DIR / "knowledge_base" / "raw"


def split_markdown_sections(text: str) -> List[str]:
    text = text.strip()
    if not text:
        return []

    parts = re.split(r"(?=^#{1,6}\s)", text, flags=re.MULTILINE)
    return [part.strip() for part in parts if part.strip()]


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


def expected_ids_for_file(md_file: Path) -> list[str]:
    text = md_file.read_text(encoding="utf-8").strip()
    sections = split_markdown_sections(text)
    chunks = chunk_sections(sections)

    return [
        f"concept::{md_file.stem}::chunk_{i:03d}"
        for i in range(len(chunks))
    ]


def batched(items: list[str], size: int = 100):
    for i in range(0, len(items), size):
        yield items[i:i + size]


def main():
    md_files = sorted(RAW_DIR.rglob("*.md"))

    if not md_files:
        print(f"No .md files found in {RAW_DIR}")
        return

    expected_ids = []
    expected_by_file = {}

    for md_file in md_files:
        ids = expected_ids_for_file(md_file)
        expected_by_file[md_file.name] = len(ids)
        expected_ids.extend(ids)

    print("Checking Pinecone concept namespace...")
    print("Namespace:", CONCEPT_NAMESPACE)
    print("Expected files:", len(md_files))
    print("Expected chunks:", len(expected_ids))
    print()

    found_ids = set()
    metadata_by_id = {}

    for batch_ids in batched(expected_ids, 100):
        result = index.fetch(ids=batch_ids, namespace=CONCEPT_NAMESPACE)

        vectors = getattr(result, "vectors", None)
        if vectors is None and isinstance(result, dict):
            vectors = result.get("vectors", {})

        for vector_id, vector_data in vectors.items():
            found_ids.add(vector_id)

            metadata = getattr(vector_data, "metadata", None)
            if metadata is None and isinstance(vector_data, dict):
                metadata = vector_data.get("metadata", {})

            metadata_by_id[vector_id] = metadata or {}

    missing_ids = sorted(set(expected_ids) - found_ids)

    print("Found chunks in Pinecone:", len(found_ids))
    print("Missing chunks:", len(missing_ids))
    print()

    count_by_file = Counter()
    count_by_topic = Counter()

    for metadata in metadata_by_id.values():
        source_file = metadata.get("source_file", "UNKNOWN")
        topic = metadata.get("topic", "UNKNOWN")
        count_by_file[source_file] += 1
        count_by_topic[topic] += 1

    print("=== Chunks by source file ===")
    for file_name in sorted(expected_by_file.keys()):
        expected = expected_by_file[file_name]
        found = count_by_file.get(file_name, 0)
        status = "OK" if expected == found else "MISSING"
        print(f"{status:8} {file_name}: {found}/{expected}")

    print()
    print("=== Chunks by topic ===")
    for topic, count in count_by_topic.most_common():
        print(f"{topic}: {count}")

    print()
    print("=== Sample loaded chunks ===")

    for vector_id in sorted(list(found_ids))[:10]:
        metadata = metadata_by_id.get(vector_id, {})
        chunk_text = metadata.get("chunk_text", "")
        snippet = chunk_text.replace("\n", " ")[:250]

        print()
        print("ID:", vector_id)
        print("Source:", metadata.get("source_file"))
        print("Topic:", metadata.get("topic"))
        print("Form:", metadata.get("form"))
        print("Chapter:", metadata.get("chapter_label"))
        print("Snippet:", snippet)

    if missing_ids:
        print()
        print("=== Missing chunk IDs ===")
        for missing_id in missing_ids[:50]:
            print(missing_id)

        if len(missing_ids) > 50:
            print(f"... and {len(missing_ids) - 50} more")


if __name__ == "__main__":
    main()