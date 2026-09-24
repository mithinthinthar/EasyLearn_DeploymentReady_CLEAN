from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma

BASE_DIR = Path(__file__).resolve().parents[1]
CHROMA_DIR = BASE_DIR / "knowledge_base" / "chroma_db"
COLLECTION_NAME = "mathsy_spm_math_kb"


def main():
    load_dotenv()

    if not os.getenv("OPENAI_API_KEY"):
        raise EnvironmentError("OPENAI_API_KEY is missing in backend .env")

    embeddings = OpenAIEmbeddings(model="text-embedding-3-large")

    vector_store = Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=embeddings,
        persist_directory=str(CHROMA_DIR),
    )

    retriever = vector_store.as_retriever(
        search_type="similarity",
        search_kwargs={"k": 3},
    )

    while True:
        query = input("\nEnter your test question (or type 'exit'): ").strip()
        if query.lower() == "exit":
            break

        docs = retriever.invoke(query)

        print("\n================ RETRIEVED CHUNKS ================\n")

        if not docs:
            print("No documents retrieved.\n")
            continue

        for i, doc in enumerate(docs, start=1):
            metadata = doc.metadata or {}
            print(f"[Chunk {i}]")
            print(f"Source file   : {metadata.get('source_file', '-')}")
            print(f"Topic         : {metadata.get('topic', '-')}")
            print(f"Form          : {metadata.get('form', '-')}")
            print(f"Chapter       : {metadata.get('chapter', '-')}")
            print(f"Content type  : {metadata.get('content_type', '-')}")
            print("\nContent preview:")
            print(doc.page_content[:700])
            print("\n--------------------------------------------------\n")


if __name__ == "__main__":
    main()