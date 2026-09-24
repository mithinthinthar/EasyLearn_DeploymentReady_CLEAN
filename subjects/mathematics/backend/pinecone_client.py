import os
from pinecone import Pinecone
from dotenv import load_dotenv

load_dotenv()

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY", "").strip()

if PINECONE_API_KEY:
    pc = Pinecone(api_key=PINECONE_API_KEY)
    index = pc.Index(os.getenv("PINECONE_INDEX_NAME", "mathsy-rag"))
else:
    pc = None
    index = None
    print("WARNING: Pinecone is not configured. Chatbot retrieval is disabled.")

CONCEPT_NAMESPACE = os.getenv("PINECONE_CONCEPT_NAMESPACE", "concept_notes")
QUESTION_NAMESPACE = os.getenv("PINECONE_QUESTION_NAMESPACE", "question_bank")