import os
from google import genai
from dotenv import load_dotenv

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

EMBED_MODEL = os.getenv("GEMINI_EMBED_MODEL", "gemini-embedding-2-preview")
EMBED_DIMENSION = int(os.getenv("GEMINI_EMBED_DIMENSION", "768"))

def embed_text(text: str) -> list[float]:
    text = (text or "").strip()
    if not text:
        return []

    response = client.models.embed_content(
        model=EMBED_MODEL,
        contents=text,
        config={"output_dimensionality": EMBED_DIMENSION},
    )

    return response.embeddings[0].values