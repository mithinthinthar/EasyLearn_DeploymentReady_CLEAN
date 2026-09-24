"""
Service layer for SPM Paper 3 (Ujian Lisan) speaking assessment.
Mirrors the structure of quiz_service.py.

Responsibilities:
  - Save 5 uploaded audio files to disk (async)
  - Orchestrate the full scoring pipeline via speaking_scorer.py
  - Build the SpeakingSubmitResponse returned to the router

5 audio clips per submission:
  audio_bacaan  — bacaan mekanis (pronunciation/fluency/grammar only)
  audio_r1      — soalan rangsangan 1
  audio_r2      — soalan rangsangan 2
  audio_k1      — soalan KBAT 1
  audio_k2      — soalan KBAT 2
"""
import uuid
import os
import tempfile
import aiofiles
from pathlib import Path
from typing import Optional, List
import database
from datetime import datetime, timezone, timedelta
from schemas.models import SpeakingSubmitResponse, ClipResult
import json
import time
from google import genai
from google.genai import types
from services.agentic_gemini import _ask_gemini, OutputSchema
from services.adaptive_engine import get_adaptive_difficulty
from services.user_results_memory import get_weak_areas, update_result


SPEAKING_SCHEMA = OutputSchema(
    root_type=dict,
    required_keys=[
        "tema",
        "stimulus_text",
        "soalan_rangsangan",
        "soalan_kbat",
    ],
)


# ─────────────────────────────────────────────────────────────────────────────
# PRODUCTION AUDIO SCORING — GEMINI MULTIMODAL
# ─────────────────────────────────────────────────────────────────────────────
# The original local scorer downloaded Malaysian Faster-Whisper + other models.
# That works on a persistent PC/server, but Vercel Functions have ephemeral disk.
# Production now lets Gemini inspect the ACTUAL audio and return the same result
# shape the frontend already expects.

_AUDIO_MODEL = os.getenv("GEMINI_SPEAKING_MODEL", "gemini-3.5-flash-lite")

_SPM_BAND_DESCRIPTORS = {
    6: "Cemerlang",
    5: "Kepujian",
    4: "Baik",
    3: "Memuaskan",
    2: "Lemah",
    1: "Sangat Lemah",
}

_SPM_TRAIT_DESCRIPTORS = {
    "grammar_vocabulary": {
        6: "Tatabahasa tepat sepenuhnya; kosa kata luas dan tepat.",
        5: "Tatabahasa hampir tepat; kosa kata pelbagai dan sesuai.",
        4: "Tatabahasa sebahagian besar betul; kosa kata memuaskan.",
        3: "Terdapat beberapa kesilapan tatabahasa; kosa kata terhad.",
        2: "Banyak kesilapan tatabahasa; kosa kata sangat terhad.",
        1: "Tatabahasa tidak tepat dan kosa kata sangat lemah.",
    },
    "pronunciation": {
        6: "Sebutan jelas, intonasi semula jadi dan nada sangat sesuai.",
        5: "Sebutan baik, intonasi baik dengan sedikit kepincangan nada.",
        4: "Sebutan memuaskan, intonasi dan nada kebanyakannya betul.",
        3: "Terdapat kesilapan sebutan; intonasi dan nada kadang tidak tepat.",
        2: "Sebutan kerap tidak jelas; intonasi monoton dan nada tidak sesuai.",
        1: "Sebutan tidak jelas, intonasi dan nada sangat lemah.",
    },
    "fluency": {
        6: "Fasih sepenuhnya; tiada gangguan, lancar dan spontan.",
        5: "Fasih dengan sedikit keraguan yang tidak mengganggu.",
        4: "Agak lancar; terdapat beberapa jeda yang tidak ketara.",
        3: "Kelancaran terganggu dengan jeda dan pengulangan yang kerap.",
        2: "Kerap berhenti; pertuturan terputus-putus.",
        1: "Tidak lancar; sangat kerap berhenti atau diam.",
    },
    "ideas": {
        6: "Idea relevan, mendalam, teratur dan sangat bermakna.",
        5: "Idea relevan dan bermakna dengan huraian yang baik.",
        4: "Idea mencukupi dan kebanyakannya relevan.",
        3: "Idea terhad; ada yang tidak relevan atau tidak dihuraikan.",
        2: "Idea sangat terhad dan kebanyakannya tidak relevan.",
        1: "Tiada idea yang jelas atau tidak menjawab soalan.",
    },
}


def _clamp01(value) -> float:
    try:
        return max(0.0, min(1.0, float(value)))
    except Exception:
        return 0.0


def _score_to_band(score: float) -> int:
    if score >= 0.90:
        return 6
    if score >= 0.70:
        return 5
    if score >= 0.60:
        return 4
    if score >= 0.40:
        return 3
    if score >= 0.20:
        return 2
    return 1


def _trait_reason(trait: str, score: float) -> str:
    return _SPM_TRAIT_DESCRIPTORS[trait][_score_to_band(score)]


def _clean_json_text(text: str) -> dict:
    raw = (text or "").strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?\s*", "", raw, flags=re.I)
        raw = re.sub(r"\s*```$", "", raw)
    return json.loads(raw)


async def _score_one_clip_cloud(
    file_path: str,
    clip_id: str,
    stimulus_text: str,
    question: Optional[dict] = None,
    reference_text: Optional[str] = None,
) -> dict:
    """Ask Gemini to evaluate one real audio clip directly."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is missing")

    client = genai.Client(api_key=api_key)
    uploaded = client.files.upload(file=file_path)

    is_reading = clip_id == "bacaan"
    question_text = question.get("question_text", "") if question else ""
    question_id = question.get("question_id", "") if question else ""
    category = question.get("category", "") if question else ""

    prompt = f"""
Anda ialah pemeriksa Ujian Lisan SPM Bahasa Melayu.

Dengar fail audio pelajar yang dilampirkan. Nilai AUDIO SEBENAR, bukan teks sahaja.
Kembalikan JSON SAHAJA, tanpa markdown.

KLIP: {clip_id}
JENIS: {"bacaan mekanis" if is_reading else "jawapan lisan"}
BAHAN RANGSANGAN:
{stimulus_text}

SOALAN (jika ada):
{question_text}

TEKS RUJUKAN BACAAN (jika ada):
{reference_text or ""}

Peraturan:
1. Transkripsikan pertuturan dalam "transcription".
2. Jika tiada pertuturan bermakna, set no_speech=true dan semua skor 0.
3. Skor mesti antara 0.0 hingga 1.0.
4. grammar_vocabulary menilai tatabahasa dan kosa kata Bahasa Melayu.
5. pronunciation WAJIB dinilai daripada bunyi sebenar: kejelasan sebutan,
   intonasi dan nada.
6. fluency WAJIB dinilai daripada bunyi sebenar: kelancaran, jeda,
   pengulangan dan keraguan.
7. Untuk klip bacaan, "ideas" mesti null.
8. Untuk klip jawapan, ideas menilai kerelevanan dan kualiti jawapan kepada
   soalan serta bahan rangsangan.
9. Jawapan hendaklah Bahasa Melayu. Jika jelas bahasa lain/gibberish,
   beri skor sangat rendah dan jelaskan sebab.

Format JSON tepat:
{{
  "transcription": "...",
  "no_speech": false,
  "no_speech_reason": null,
  "grammar_vocabulary": {{
    "score": 0.0,
    "reason": "..."
  }},
  "pronunciation": {{
    "score": 0.0,
    "reason": "...",
    "metrics": {{
      "source": "gemini_audio"
    }}
  }},
  "fluency": {{
    "score": 0.0,
    "reason": "...",
    "metrics": {{
      "source": "gemini_audio"
    }}
  }},
  "ideas": {(
    'null'
    if is_reading else
    '{"score": 0.0, "reason": "...", "question_id": "' + question_id +
    '", "question_text": ' + json.dumps(question_text, ensure_ascii=False) +
    ', "category": "' + category + '"}'
  )}
}}
"""

    response = client.models.generate_content(
        model=_AUDIO_MODEL,
        contents=[prompt, uploaded],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0.1,
        ),
    )

    data = _clean_json_text(response.text)

    no_speech = bool(data.get("no_speech", False))
    transcription = str(data.get("transcription", "") or "").strip()

    grammar = data.get("grammar_vocabulary") or {}
    pronunciation = data.get("pronunciation") or {}
    fluency = data.get("fluency") or {}
    ideas = data.get("ideas")

    if no_speech:
        grammar = {"score": 0.0, "reason": "Tiada pertuturan yang dikesan."}
        pronunciation = {
            "score": 0.0,
            "reason": "Tiada pertuturan yang dikesan.",
            "metrics": {"source": "gemini_audio"},
        }
        fluency = {
            "score": 0.0,
            "reason": "Tiada pertuturan yang dikesan.",
            "metrics": {"source": "gemini_audio"},
        }
        if question:
            ideas = {
                "score": 0.0,
                "reason": "Tiada jawapan lisan yang dapat dinilai.",
                "question_id": question_id,
                "question_text": question_text,
                "category": category,
            }

    grammar["score"] = _clamp01(grammar.get("score", 0))
    grammar.setdefault("reason", _trait_reason("grammar_vocabulary", grammar["score"]))

    pronunciation["score"] = _clamp01(pronunciation.get("score", 0))
    pronunciation.setdefault("reason", _trait_reason("pronunciation", pronunciation["score"]))
    pronunciation.setdefault("metrics", {"source": "gemini_audio"})

    fluency["score"] = _clamp01(fluency.get("score", 0))
    fluency.setdefault("reason", _trait_reason("fluency", fluency["score"]))
    fluency.setdefault("metrics", {"source": "gemini_audio"})

    if question:
        if not isinstance(ideas, dict):
            ideas = {}
        ideas["score"] = _clamp01(ideas.get("score", 0))
        ideas.setdefault("reason", _trait_reason("ideas", ideas["score"]))
        ideas["question_id"] = question_id
        ideas["question_text"] = question_text
        ideas["category"] = category
    else:
        ideas = None

    return {
        "clip_id": clip_id,
        "transcription": transcription,
        "no_speech": no_speech,
        "no_speech_reason": data.get("no_speech_reason"),
        "grammar_vocabulary": grammar,
        "pronunciation": pronunciation,
        "fluency": fluency,
        "ideas": ideas,
        # WER was a local-Whisper diagnostic. It is optional in the response.
        "wer": None,
    }


async def _score_speaking_cloud(
    path_bacaan: str,
    path_r1: str,
    path_r2: str,
    path_k1: str,
    path_k2: str,
    stimulus_text: str,
    soalan_rangsangan: List[dict],
    soalan_kbat: List[dict],
    reference_texts: Optional[dict] = None,
) -> dict:
    t0 = time.time()

    r1_q = {**soalan_rangsangan[0], "category": "soalan_rangsangan"}
    r2_q = {**soalan_rangsangan[1], "category": "soalan_rangsangan"}
    k1_q = {**soalan_kbat[0], "category": "soalan_kbat"}
    k2_q = {**soalan_kbat[1], "category": "soalan_kbat"}

    bacaan_reference = (reference_texts or {}).get("bacaan") or stimulus_text

    jobs = [
        ("bacaan", path_bacaan, None, bacaan_reference),
        ("r1", path_r1, r1_q, None),
        ("r2", path_r2, r2_q, None),
        ("k1", path_k1, k1_q, None),
        ("k2", path_k2, k2_q, None),
    ]

    clips = []
    for clip_id, file_path, question, ref_text in jobs:
        clips.append(
            await _score_one_clip_cloud(
                file_path=file_path,
                clip_id=clip_id,
                stimulus_text=stimulus_text,
                question=question,
                reference_text=ref_text,
            )
        )

    def avg(values):
        values = list(values)
        return round(sum(values) / len(values), 4) if values else 0.0

    grammar_per_clip = [
        {
            "clip_id": c["clip_id"],
            "score": c["grammar_vocabulary"]["score"],
            "reason": c["grammar_vocabulary"]["reason"],
        }
        for c in clips
    ]
    pron_per_clip = [
        {
            "clip_id": c["clip_id"],
            "score": c["pronunciation"]["score"],
            "reason": c["pronunciation"]["reason"],
            "metrics": c["pronunciation"].get("metrics", {}),
        }
        for c in clips
    ]
    fluency_per_clip = [
        {
            "clip_id": c["clip_id"],
            "score": c["fluency"]["score"],
            "reason": c["fluency"]["reason"],
            "metrics": c["fluency"].get("metrics", {}),
        }
        for c in clips
    ]
    ideas_per_question = [
        {
            "clip_id": c["clip_id"],
            "question_id": c["ideas"]["question_id"],
            "question_text": c["ideas"]["question_text"],
            "category": c["ideas"]["category"],
            "score": c["ideas"]["score"],
            "reason": c["ideas"]["reason"],
        }
        for c in clips
        if c.get("ideas") is not None
    ]

    grammar_score = avg(x["score"] for x in grammar_per_clip)
    pron_score = avg(x["score"] for x in pron_per_clip)
    fluency_score = avg(x["score"] for x in fluency_per_clip)
    ideas_score = avg(x["score"] for x in ideas_per_question)

    total = round(
        (grammar_score + pron_score + fluency_score + ideas_score) / 4,
        2,
    )
    overall_band = _score_to_band(total)

    return {
        "clips": clips,
        "grammar_vocabulary": {
            "score": round(grammar_score, 2),
            "reason": _trait_reason("grammar_vocabulary", grammar_score),
            "per_clip": grammar_per_clip,
        },
        "pronunciation": {
            "score": round(pron_score, 2),
            "reason": _trait_reason("pronunciation", pron_score),
            "per_clip": pron_per_clip,
        },
        "fluency": {
            "score": round(fluency_score, 2),
            "reason": _trait_reason("fluency", fluency_score),
            "per_clip": fluency_per_clip,
        },
        "ideas": {
            "score": round(ideas_score, 2),
            "reason": _trait_reason("ideas", ideas_score),
            "per_question": ideas_per_question,
        },
        "bacaan_wer": None,
        "total_score": total,
        "overall_band": overall_band,
        "overall_descriptor": _SPM_BAND_DESCRIPTORS[overall_band],
        "processing_time_s": round(time.time() - t0, 2),
    }



# ── Helper: Get session for resuming speaking if available ───────────────────────
def get_valid_session(session_id: str):
    session = database.speaking_sessions_col.find_one(
        {"session_id": session_id}
    )

    if not session:
        return None

    if session.get("status") != "in_progress":
        return None

    expires_at = session.get("expires_at")

    if isinstance(expires_at, str):
        from dateutil import parser
        expires_at = parser.isoparse(expires_at)

    if not expires_at:
        return None

    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    if datetime.now(timezone.utc) > expires_at:
        database.speaking_sessions_col.update_one(
            {"session_id": session_id},
            {"$set": {"status": "expired"}}
        )
        return None

    return session


# ─────────────────────────────────────────────────────────────────────────────
# CONFIG — AUDIO STORAGE
# ─────────────────────────────────────────────────────────────────────────────

# Temporary directory for uploaded audio files
# Replace with AWS S3 upload in production
AUDIO_UPLOAD_DIR = (
    Path(tempfile.gettempdir()) / "easylearn-speaking"
    if os.getenv("VERCEL")
    else Path("uploads/audio")
)
AUDIO_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


# ─────────────────────────────────────────────────────────────────────────────
# AUDIO FILE HANDLING
# ─────────────────────────────────────────────────────────────────────────────

async def save_audio_file(file, session_id: str, clip_id: str) -> str:
    """
    Saves a single UploadFile to AUDIO_UPLOAD_DIR.
    Filename: <session_id>_<clip_id>.<ext>  e.g. abc123_bacaan.webm
    Returns the saved file path string.
    """
    suffix   = Path(file.filename).suffix if file.filename else ".wav"
    filename = f"{session_id}_{clip_id}{suffix}"
    filepath = AUDIO_UPLOAD_DIR / filename

    async with aiofiles.open(filepath, "wb") as out_file:
        content = await file.read()
        await out_file.write(content)

    return str(filepath)


# ─────────────────────────────────────────────────────────────────────────────
# DATABASE (Paper 3)
# ─────────────────────────────────────────────────────────────────────────────

async def _save_speaking_session(
    session_id: str,
    quiz_type: str,
    session_data: dict,
    user_id: str,
    mode: str = "quiz",
):
    """Save generated questions to MongoDB when /start is called."""
    if database.speaking_sessions_col is None:
        raise RuntimeError("MongoDB not initialized")

    doc = {
        "session_id":  session_id,
        "quiz_type":   quiz_type,
        "tema": session_data["tema"],
        "stimulus_text": session_data["stimulus_text"],
        "soalan_rangsangan": session_data["soalan_rangsangan"],
        "soalan_kbat": session_data["soalan_kbat"],
        "user_id":     user_id,
        "mode":        mode,
        "status":      "in_progress",           
        "created_at":  datetime.now(timezone.utc),
        "expires_at":  datetime.now(timezone.utc) + timedelta(hours=2),        
    }
    database.speaking_sessions_col.insert_one(doc)


async def _save_speaking_result(response, user_id: str):
    """Save scoring result to MongoDB when /submit is called."""
    if database.speaking_results_col is None:
        raise RuntimeError("MongoDB not initialized")

    doc = response.model_dump()
    doc["user_id"]    = user_id
    doc["saved_at"]   = datetime.now(timezone.utc)
    database.speaking_results_col.insert_one(doc)


# ─────────────────────────────────────────────────────────────────────────────
# LISAN GENERATION PROMPTS (Paper 3)
# ─────────────────────────────────────────────────────────────────────────────

_LISAN_PROMPT = """
Anda adalah pemeriksa SPM Bahasa Melayu berpengalaman.
Jana satu set bahan rangsangan Ujian Lisan SPM yang lengkap dan KOHEREN.
Semua bahagian MESTI berkait rapat dengan SATU tema yang sama.

Langkah:
1. Pilih SATU tema semasa yang sesuai untuk pelajar tingkatan 5
2. Tulis petikan bahan rangsangan berdasarkan tema tersebut
3. Jana semua soalan berkait dengan petikan dan tema yang sama

Format petikan:
- 150–200 patah perkataan
- Bahasa Melayu formal
- Gaya rencana/artikel

Format soalan rangsangan (2 sahaja):
- Berdasarkan petikan
- 1 faktual
- 1 inferensi

Format soalan KBAT (2 sahaja):
- Berkait dengan tema
- Perlu pemikiran kritis
- Aras analisis / penilaian

Kembalikan JSON sahaja:
{
  "tema": "<tema>",
  "stimulus_text": "<petikan>",
  "soalan_rangsangan": [
    {"question_id": "r1", "question_text": "<soalan>"},
    {"question_id": "r2", "question_text": "<soalan>"}
  ],
  "soalan_kbat": [
    {"question_id": "k1", "question_text": "<soalan>"},
    {"question_id": "k2", "question_text": "<soalan>"}
  ]
}
"""

DIFFICULTY_RULES = {
    "easy": {
        "topic": "tema harian yang dekat dengan kehidupan pelajar seperti sekolah, keluarga, kesihatan, hobi atau amalan baik",
        "stimulus": "petikan mudah dengan isi yang jelas, ayat tidak terlalu panjang dan maksud yang terus",
        "questions": "soalan rangsangan mudah yang boleh dijawab terus berdasarkan petikan",
        "kbat": "soalan KBAT asas yang meminta pendapat, sebab atau cadangan mudah",
    },
    "medium": {
        "topic": "tema semasa berkaitan remaja, masyarakat, pendidikan, teknologi, alam sekitar atau kesihatan awam",
        "stimulus": "petikan sederhana dengan beberapa isi utama, contoh dan hubungan sebab-akibat",
        "questions": "soalan rangsangan yang memerlukan pemahaman dan sedikit inferens",
        "kbat": "soalan KBAT yang meminta huraian, kesan, kepentingan atau langkah penyelesaian",
    },
    "hard": {
        "topic": "tema mencabar seperti isu global, ekonomi, etika teknologi, perpaduan, kepimpinan, jati diri atau masa depan negara",
        "stimulus": "petikan matang dan analitis dengan isu pelbagai dimensi serta idea yang lebih abstrak",
        "questions": "soalan rangsangan yang memerlukan inferens, analisis dan penilaian",
        "kbat": "soalan KBAT tinggi yang memerlukan hujah matang, penilaian kritis dan cadangan bernas",
    },
}


# ─────────────────────────────────────────────────────────────────────────────
# QUESTION GENERATION (Paper 3)
# ─────────────────────────────────────────────────────────────────────────────

async def generate_questions_for_type(
    session_id: str,
    user_id: str,
    requested_difficulty: Optional[str] = None,
    mode: str = "quiz",
) -> dict:
    weak_areas = get_weak_areas(user_id)

    # LATIHAN MODE:
    # Only use selected easy/medium/hard if frontend sends requested_difficulty.
    if requested_difficulty:
        difficulty = requested_difficulty

        if difficulty not in DIFFICULTY_RULES:
            difficulty = "medium"

        rule = DIFFICULTY_RULES[difficulty]

        adaptive_prompt = _LISAN_PROMPT + f"""
MAKLUMAT PELAJAR:
- Tahap kesukaran sasaran: **{difficulty}**

WAJIB ikut tahap kesukaran ini:
- easy = mudah
- medium = sederhana
- hard = sukar / KBAT

Panduan tahap ini:
- Tema: {rule["topic"]}
- Petikan: {rule["stimulus"]}
- Soalan rangsangan: {rule["questions"]}
- Soalan KBAT: {rule["kbat"]}

Pastikan petikan dan soalan yang dijana benar-benar sepadan dengan tahap **{difficulty}**.
"""

    # QUIZ MODE:
    # If no selected difficulty is sent, keep the original adaptive behavior.
    else:
        difficulty = get_adaptive_difficulty(user_id, "lisan")

        adaptive_prompt = _LISAN_PROMPT + f"""
MAKLUMAT PELAJAR:
- Tahap kesukaran sasaran: **{difficulty}**
"""

    if weak_areas:
        adaptive_prompt += f"""
- Kawasan lemah pelajar: {", ".join(weak_areas)}
Pelajar menunjukkan kelemahan dalam aspek tersebut. Fokuskan soalan yang dapat membantu memperbaiki kemahiran ini secara berperingkat dan jelas.
"""

    data = await _ask_gemini(adaptive_prompt, schema=SPEAKING_SCHEMA,)
    
    if not data:
        raise ValueError("Failed to generate speaking questions from Gemini")

    # Normalize IDs
    for q in data.get("soalan_rangsangan", []):
        if not q.get("question_id"):
            q["question_id"] = str(uuid.uuid4())

    for q in data.get("soalan_kbat", []):
        if not q.get("question_id"):
            q["question_id"] = str(uuid.uuid4())

    result = {
        "tema": data.get("tema", ""),
        "stimulus_text": data.get("stimulus_text", ""),
        "soalan_rangsangan": data.get("soalan_rangsangan", []),
        "soalan_kbat": data.get("soalan_kbat", []),
    }

    await _save_speaking_session(
        session_id,
        "lisan",
        {
            "tema":              result["tema"],
            "stimulus_text":     result["stimulus_text"],
            "soalan_rangsangan": result["soalan_rangsangan"],
            "soalan_kbat":       result["soalan_kbat"],
        },
        user_id=user_id,
        mode=mode,
    )

    return result


# ─────────────────────────────────────────────────────────────────────────────
# MAIN SCORING ORCHESTRATOR
# ─────────────────────────────────────────────────────────────────────────────

async def score_speaking_submission(
    session_id:        str,
    task_type:         str,
    user_id:           str,
    path_bacaan:       str,
    path_r1:           str,
    path_r2:           str,
    path_k1:           str,
    path_k2:           str,
    stimulus_text:     str,
    soalan_rangsangan: List[dict],   # [{"question_id": str, "question_text": str}]
    soalan_kbat:       List[dict],   # [{"question_id": str, "question_text": str}]
    reference_texts:   Optional[dict] = None,
) -> SpeakingSubmitResponse:
    """
    Runs the full SPM Lisan scoring pipeline across 5 audio clips
    and builds the SpeakingSubmitResponse returned to the router.

    Parameters
    ----------
    session_id        : UUID from the session store in speaking.py
    task_type         : "lisan"
    path_bacaan       : saved path for bacaan mekanis clip
    path_r1 / path_r2 : saved paths for soalan rangsangan clips
    path_k1 / path_k2 : saved paths for soalan KBAT clips
    stimulus_text     : Gemini-generated bahan rangsangan petikan
    soalan_rangsangan : 2 questions directly based on the petikan
    soalan_kbat       : 2 KBAT questions related to the same theme
    """

    """Look up the session's stored questions, then score the speaking."""
    session = get_valid_session(session_id)

    if not session:
        raise ValueError(
            f"Session '{session_id}' not found or has expired. "
            "Please call /api/speaking/start first."
        )

    if session.get("mode", "quiz") != "quiz":
        raise ValueError("This session is a latihan session and cannot be submitted as a quiz.")

    try:
        result = await _score_speaking_cloud(
            path_bacaan        = path_bacaan,
            path_r1            = path_r1,
            path_r2            = path_r2,
            path_k1            = path_k1,
            path_k2            = path_k2,
            stimulus_text      = stimulus_text,
            soalan_rangsangan  = soalan_rangsangan,
            soalan_kbat        = soalan_kbat,
            reference_texts    = reference_texts or {},
        )
    except Exception as e:
        import traceback
        print("SCORING CRASH:")
        print(str(e))
        print(traceback.format_exc())
        raise

    if not result:
        raise ValueError("score_speaking returned None")

    required_keys = ["clips", "grammar_vocabulary", "pronunciation", "fluency", "ideas"]

    missing = [k for k in required_keys if k not in result]
    if missing:
        raise ValueError(f"Missing keys in scoring result: {missing}")

    # ── Build ClipResult list from raw scorer output ──────────────────────────
    clip_objects = [
        ClipResult(
            clip_id=c["clip_id"],
            transcription=c["transcription"],
            no_speech=c.get("no_speech", False),
            no_speech_reason=c.get("no_speech_reason", None),

            grammar_vocabulary=c["grammar_vocabulary"],

            pronunciation=c["pronunciation"],

            fluency=c["fluency"],

            ideas=c.get("ideas"),

            wer=c.get("wer"),
        )
        for c in result["clips"]
    ]

    result_response = SpeakingSubmitResponse(
        session_id    = session_id,
        task_type     = task_type,

        # Per-clip results
        clips = clip_objects,

        # Trait 1 — grammar & vocabulary # tatabahasa & kosa kata
        grammar_vocabulary = result["grammar_vocabulary"],

        # Trait 2 — pronunciation # sebutan, intonasi & nada
        pronunciation      = result["pronunciation"],
 
        # Trait 3 — fluency # kefasihan & kelancaran
        fluency            = result["fluency"],

        # Trait 4 — ideas # idea & bermakna
        ideas              = result["ideas"],
        
        bacaan_wer         = result["bacaan_wer"],

        # Overall band
        total_score         = result["total_score"],
        overall_band        = result["overall_band"],
        overall_descriptor  = result["overall_descriptor"],

        # Evaluation
        processing_time_s = result["processing_time_s"],
    )

    database.speaking_sessions_col.update_one(
        {"session_id": session_id},
        {"$set": {"status": "completed"}}
    )

    await _save_speaking_result(result_response, user_id=user_id)

    update_result(
        user_id=user_id,
        quiz_type="lisan",
        raw_score=result["total_score"],
        max_score=1.0
    )

    return result_response

async def score_latihan_speaking_submission(
    session_id:        str,
    task_type:         str,
    user_id:           str,
    path_bacaan:       str,
    path_r1:           str,
    path_r2:           str,
    path_k1:           str,
    path_k2:           str,
    stimulus_text:     str,
    soalan_rangsangan: List[dict],
    soalan_kbat:       List[dict],
    reference_texts:   Optional[dict] = None,
) -> SpeakingSubmitResponse:
    """
    Runs speaking marking for latihan only.

    This intentionally does NOT:
    - save to speaking results collection
    - call update_result(...)
    - affect dashboard marks
    """
    session = get_valid_session(session_id)

    if not session:
        raise ValueError(
            f"Session '{session_id}' not found or has expired. "
            "Please call /api/speaking/start first."
        )

    if session.get("mode", "quiz") != "latihan":
        raise ValueError(
            "This session is a quiz session and cannot be submitted as latihan."
        )

    try:
        result = await _score_speaking_cloud(
            path_bacaan        = path_bacaan,
            path_r1            = path_r1,
            path_r2            = path_r2,
            path_k1            = path_k1,
            path_k2            = path_k2,
            stimulus_text      = stimulus_text,
            soalan_rangsangan  = soalan_rangsangan,
            soalan_kbat        = soalan_kbat,
            reference_texts    = reference_texts or {},
        )
    except Exception as e:
        import traceback
        print("LATIHAN SPEAKING SCORING CRASH:")
        print(str(e))
        print(traceback.format_exc())
        raise

    if not result:
        raise ValueError("score_speaking returned None")

    required_keys = ["clips", "grammar_vocabulary", "pronunciation", "fluency", "ideas"]

    missing = [k for k in required_keys if k not in result]
    if missing:
        raise ValueError(f"Missing keys in scoring result: {missing}")

    clip_objects = [
        ClipResult(
            clip_id=c["clip_id"],
            transcription=c.get("transcription", ""),
            no_speech=c.get("no_speech", False),
            no_speech_reason=c.get("no_speech_reason", None),
            grammar_vocabulary=c["grammar_vocabulary"],
            pronunciation=c["pronunciation"],
            fluency=c["fluency"],
            ideas=c.get("ideas"),
            wer=c.get("wer"),
        )
        for c in result["clips"]
    ]

    result_response = SpeakingSubmitResponse(
        session_id    = session_id,
        task_type     = task_type,
        clips         = clip_objects,

        grammar_vocabulary = result["grammar_vocabulary"],
        pronunciation      = result["pronunciation"],
        fluency            = result["fluency"],
        ideas              = result["ideas"],

        bacaan_wer         = result["bacaan_wer"],
        total_score        = result["total_score"],
        overall_band       = result["overall_band"],
        overall_descriptor = result["overall_descriptor"],
        processing_time_s  = result["processing_time_s"],
    )

    database.speaking_sessions_col.update_one(
        {"session_id": session_id},
        {"$set": {"status": "completed"}}
    )

    return result_response