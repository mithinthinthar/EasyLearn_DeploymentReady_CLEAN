from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Dict, List

from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter


BASE_DIR = Path(__file__).resolve().parents[1]
RAW_DIR = BASE_DIR / "knowledge_base" / "raw"
CHROMA_DIR = BASE_DIR / "knowledge_base" / "chroma_db"
COLLECTION_NAME = "mathsy_spm_math_kb"


def parse_markdown_metadata(text: str, filename: str) -> Dict[str, str]:
    """
    Reads simple metadata from markdown headings like:
    # Topic: Number Bases
    ## Form: Form 4
    ## Chapter: 1
    ## Type: Notes
    """
    metadata = {
        "source_file": filename,
        "topic": "",
        "form": "",
        "chapter": "",
        "content_type": "",
    }

    topic_match = re.search(r"^#\s*Topic:\s*(.+)$", text, re.MULTILINE)
    form_match = re.search(r"^##\s*Form:\s*(.+)$", text, re.MULTILINE)
    chapter_match = re.search(r"^##\s*Chapter:\s*(.+)$", text, re.MULTILINE)
    type_match = re.search(r"^##\s*Type:\s*(.+)$", text, re.MULTILINE)

    if topic_match:
        metadata["topic"] = topic_match.group(1).strip()
    if form_match:
        metadata["form"] = form_match.group(1).strip()
    if chapter_match:
        metadata["chapter"] = chapter_match.group(1).strip()
    if type_match:
        metadata["content_type"] = type_match.group(1).strip()

    return metadata


def load_markdown_documents(raw_dir: Path) -> List[Document]:
    documents: List[Document] = []

    if not raw_dir.exists():
        raise FileNotFoundError(f"Raw knowledge base folder not found: {raw_dir}")

    for file_path in sorted(raw_dir.glob("*.md")):
        text = file_path.read_text(encoding="utf-8").strip()
        if not text:
            continue

        metadata = parse_markdown_metadata(text, file_path.name)
        documents.append(
            Document(
                page_content=text,
                metadata=metadata,
            )
        )

    return documents


def chunk_documents(documents: List[Document]) -> List[Document]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=120,
        length_function=len,
        is_separator_regex=False,
    )

    chunked_docs = splitter.split_documents(documents)

    for i, doc in enumerate(chunked_docs):
        # attach a stable chunk index
        doc.metadata["chunk_index"] = i

    return chunked_docs


def build_vector_store(documents: List[Document]) -> None:
    load_dotenv()

    if not os.getenv("OPENAI_API_KEY"):
        raise EnvironmentError("OPENAI_API_KEY is missing. Put it in your backend .env file.")

    CHROMA_DIR.mkdir(parents=True, exist_ok=True)

    embeddings = OpenAIEmbeddings(
        model="text-embedding-3-large"
    )

    vector_store = Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=embeddings,
        persist_directory=str(CHROMA_DIR),
    )

    # clear old collection contents for clean rebuild
    existing = vector_store.get()
    ids = existing.get("ids", [])
    if ids:
        vector_store.delete(ids=ids)

    vector_store.add_documents(documents)

    print(f"Knowledge base built successfully.")
    print(f"Collection: {COLLECTION_NAME}")
    print(f"Persisted at: {CHROMA_DIR}")
    print(f"Chunks stored: {len(documents)}")


def main() -> None:
    print(f"Loading markdown files from: {RAW_DIR}")
    raw_docs = load_markdown_documents(RAW_DIR)
    print(f"Loaded files: {len(raw_docs)}")

    if not raw_docs:
        print("No markdown files found. Put .md files into backend/knowledge_base/raw/")
        return

    chunked_docs = chunk_documents(raw_docs)
    print(f"Chunked documents: {len(chunked_docs)}")

    build_vector_store(chunked_docs)


if __name__ == "__main__":
    main()