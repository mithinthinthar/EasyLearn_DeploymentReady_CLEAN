"""Local, credential-free FastAPI backend for EasyLearn Bahasa Melayu.

This local checkpoint keeps sessions in memory and provides a small static
practice bank. It intentionally does not impersonate MongoDB, Gemini, speech
recognition, text-to-speech, or production authentication.
"""

from __future__ import annotations

import re
import uuid
from copy import deepcopy
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI(title="EasyLearn BM Local API", version="1.0-local")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
        "http://localhost:3002",
        "http://127.0.0.1:3002",
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


SESSIONS: dict[str, dict[str, Any]] = {}
LATEST_SESSION: dict[tuple[str, str], str] = {}


QUESTION_BANK: dict[str, list[dict[str, Any]]] = {
    "golongan_kata": [
        {
            "question_text": 'Kenal pasti golongan kata bagi perkataan *rajin* dalam ayat: "Aina seorang murid yang rajin."',
            "options": ["Kata Nama", "Kata Kerja", "Kata Adjektif", "Kata Hubung"],
            "answer": "Kata Adjektif",
        },
        {
            "question_text": 'Kenal pasti golongan kata bagi perkataan *membaca* dalam ayat: "Kumar membaca buku di perpustakaan."',
            "options": ["Kata Nama", "Kata Kerja", "Kata Adjektif", "Kata Bilangan"],
            "answer": "Kata Kerja",
        },
        {
            "question_text": 'Kenal pasti golongan kata bagi perkataan *sekolah* dalam ayat: "Mereka berjalan ke sekolah."',
            "options": ["Kata Nama", "Kata Kerja", "Kata Adjektif", "Kata Hubung"],
            "answer": "Kata Nama",
        },
        {
            "question_text": 'Kenal pasti golongan kata bagi perkataan *kerana* dalam ayat: "Dia berehat kerana penat."',
            "options": ["Kata Nama", "Kata Kerja", "Kata Adjektif", "Kata Hubung"],
            "answer": "Kata Hubung",
        },
    ],
    "jenis_ayat": [
        {
            "question_text": "Apakah jenis ayat berikut?\nSila duduk di tempat masing-masing.",
            "options": ["Ayat Penyata", "Ayat Tanya", "Ayat Perintah", "Ayat Seruan"],
            "answer": "Ayat Perintah",
        },
        {
            "question_text": "Apakah jenis ayat berikut?\nBilakah pertandingan itu akan bermula?",
            "options": ["Ayat Penyata", "Ayat Tanya", "Ayat Perintah", "Ayat Seruan"],
            "answer": "Ayat Tanya",
        },
        {
            "question_text": "Apakah jenis ayat berikut?\nWah, cantiknya pemandangan ini!",
            "options": ["Ayat Penyata", "Ayat Tanya", "Ayat Perintah", "Ayat Seruan"],
            "answer": "Ayat Seruan",
        },
        {
            "question_text": "Apakah jenis ayat berikut?\nFarah sedang menyiapkan kerja sekolah.",
            "options": ["Ayat Penyata", "Ayat Tanya", "Ayat Perintah", "Ayat Seruan"],
            "answer": "Ayat Penyata",
        },
    ],
    "kesalahan_bahasa": [
        {
            "question_text": "Kenal pasti kesalahan bahasa dan tulis semula ayat dengan betul: 'Para pelajar-pelajar sedang berhimpun di dewan.'",
            "answer": "Para pelajar sedang berhimpun di dewan.",
            "keywords": ["para pelajar", "berhimpun", "dewan"],
        },
        {
            "question_text": "Kenal pasti kesalahan bahasa dan tulis semula ayat dengan betul: 'Dia paling tercantik di dalam kelas itu.'",
            "answer": "Dia paling cantik di dalam kelas itu.",
            "keywords": ["paling cantik", "kelas"],
        },
        {
            "question_text": "Kenal pasti kesalahan bahasa dan tulis semula ayat dengan betul: 'Mereka saling tolong-menolong antara satu sama lain.'",
            "answer": "Mereka saling menolong.",
            "keywords": ["saling menolong"],
        },
    ],
    "bina_ayat": [
        {
            "question_text": "Bina ayat yang lengkap dan gramatis menggunakan perkataan: kerjasama",
            "answer": "Kerjasama antara semua murid menjayakan program kebersihan sekolah.",
            "target": "kerjasama",
        },
        {
            "question_text": "Bina ayat yang lengkap dan gramatis menggunakan perkataan: memelihara",
            "answer": "Kita mestilah memelihara alam sekitar demi generasi akan datang.",
            "target": "memelihara",
        },
        {
            "question_text": "Bina ayat yang lengkap dan gramatis menggunakan perkataan: bertanggungjawab",
            "answer": "Setiap pelajar bertanggungjawab menjaga kebersihan kelas.",
            "target": "bertanggungjawab",
        },
    ],
    "pemahaman": [
        {
            "passage": "[BAHAN_1]\nAmalan membaca dapat menambah pengetahuan dan meluaskan kosa kata seseorang. Murid yang membaca secara konsisten juga lebih mudah memahami pelbagai mata pelajaran.\n\n[BAHAN_2]\nPerpustakaan sekolah menyediakan buku, majalah dan bahan digital. Program NILAM pula menggalakkan murid merekod serta berkongsi bahan yang dibaca.",
            "question_text": "Nyatakan satu manfaat amalan membaca. [2 markah]",
            "answer": "Amalan membaca dapat menambah pengetahuan.",
            "keywords": ["menambah pengetahuan", "meluaskan kosa kata", "memahami"],
            "marks": 2,
        },
        {
            "passage": "[BAHAN_1]\nAmalan membaca dapat menambah pengetahuan dan meluaskan kosa kata seseorang. Murid yang membaca secara konsisten juga lebih mudah memahami pelbagai mata pelajaran.\n\n[BAHAN_2]\nPerpustakaan sekolah menyediakan buku, majalah dan bahan digital. Program NILAM pula menggalakkan murid merekod serta berkongsi bahan yang dibaca.",
            "question_text": "Bagaimanakah pihak sekolah boleh menggalakkan budaya membaca? [2 markah]",
            "answer": "Sekolah boleh menyediakan bahan bacaan yang menarik dan menjalankan program NILAM.",
            "keywords": ["bahan bacaan", "program nilam", "perpustakaan"],
            "marks": 2,
        },
    ],
    "rumusan": [
        {
            "passage": "[BAHAN_1]\nAktiviti bersukan meningkatkan kecergasan fizikal dan menguatkan daya tahan badan.\n\n[BAHAN_2]\nSukan berpasukan mengajar seseorang bekerjasama, berdisiplin dan menghormati orang lain.\n\n[BAHAN_3]\nMurid boleh bersukan secara selamat dengan melakukan pemanasan badan dan menggunakan peralatan yang sesuai.",
            "question_text": "Tulis satu rumusan tentang manfaat bersukan dan langkah bersukan dengan selamat.",
            "answer": "Bersukan meningkatkan kecergasan, membina kerjasama dan disiplin. Kita hendaklah memanaskan badan serta menggunakan peralatan yang sesuai.",
            "keywords": ["kecergasan", "kerjasama", "disiplin", "pemanasan badan", "peralatan"],
            "marks": 30,
        }
    ],
}


ESSAY_PROMPTS = {
    "karangan_pendek": {
        "title": "Karangan Pendek",
        "description": "Latihan karangan ringkas",
        "instructions": "Tulis karangan yang jelas dan tersusun.",
        "question": "Tulis sebuah karangan tentang cara-cara menjaga kebersihan sekolah.",
        "max_score": 30,
    },
    "karangan_panjang": {
        "title": "Karangan Panjang",
        "description": "Latihan karangan panjang",
        "instructions": "Huraikan isi dengan contoh yang sesuai.",
        "question": "Penggunaan teknologi memberikan banyak manfaat kepada pelajar. Bincangkan.",
        "max_score": 70,
    },
}


def normalize(value: Any) -> str:
    return re.sub(r"[^a-z0-9\s]", "", str(value or "").lower()).strip()


def grade_from_percentage(percentage: float) -> str:
    if percentage >= 80:
        return "A"
    if percentage >= 65:
        return "B"
    if percentage >= 50:
        return "C"
    if percentage >= 40:
        return "D"
    return "E"


def public_question(item: dict[str, Any], index: int, difficulty: str) -> dict[str, Any]:
    return {
        "question_id": f"local-{index + 1}",
        "question_text": item["question_text"],
        "question_type": "factual",
        "difficulty": difficulty,
        "options": item.get("options"),
        "passage": item.get("passage"),
        "marks": item.get("marks", 1),
    }


def session_response(session_id: str, session: dict[str, Any]) -> dict[str, Any]:
    quiz_type = session["quiz_type"]
    meta = {
        "golongan_kata": ("Golongan Kata", "Kenal pasti golongan kata."),
        "bina_ayat": ("Bina Ayat", "Bina ayat yang gramatis."),
        "jenis_ayat": ("Jenis Ayat", "Kenal pasti jenis ayat."),
        "kesalahan_bahasa": ("Kesalahan Bahasa", "Betulkan kesalahan bahasa."),
        "pemahaman": ("Pemahaman", "Baca bahan dan jawab soalan."),
        "rumusan": ("Rumusan", "Tulis rumusan berdasarkan bahan."),
    }[quiz_type]
    return {
        "session_id": session_id,
        "quiz_type": quiz_type,
        "paper": "paper2",
        "title": meta[0],
        "description": meta[1],
        "instructions": meta[1],
        "questions": session["public_questions"],
        "time_limit_minutes": None,
    }


@app.get("/")
def root():
    return {"status": "ok", "message": "EasyLearn BM local API is running"}


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "bm-api-local",
        "local_mode": True,
        "mongodb_enabled": False,
        "gemini_enabled": False,
        "offline_question_types": list(QUESTION_BANK),
    }


@app.get("/api/home/recommendations")
def recommendations(user_id: str = "guest"):
    return {
        "mode": "first_time",
        "message": "Mod tempatan: mulakan dengan latihan tatabahasa asas.",
        "items": [
            {"title": "Golongan Kata", "paper": "PAPER 2", "route": "/golongan-kata-latihan", "icon": "🔤", "color": "blue", "reason": "Kukuhkan asas golongan kata."},
            {"title": "Bina Ayat", "paper": "PAPER 2", "route": "/bina-ayat-latihan", "icon": "✏️", "color": "green", "reason": "Latih pembinaan ayat yang gramatis."},
            {"title": "Jenis Ayat", "paper": "PAPER 2", "route": "/jenis-ayat-latihan", "icon": "🧩", "color": "orange", "reason": "Kenal pasti fungsi dan bentuk ayat."},
        ],
    }


@app.get("/api/dashboard/overview")
def dashboard(user_id: str = "guest"):
    return {
        "user_id": user_id,
        "summary": {"average_score": None, "total_questions": 0, "grade_predictor": None, "predicted_percentage": None, "confidence": "low", "total_attempts": 0},
        "trend": [],
        "activity": [],
        "breakdown": [],
        "latest_result": None,
    }


@app.get("/api/comprehension/types")
def comprehension_types():
    return {"types": list(QUESTION_BANK)}


@app.post("/api/comprehension/start")
def start_comprehension(data: dict[str, Any]):
    quiz_type = str(data.get("quiz_type") or "")
    if quiz_type not in QUESTION_BANK:
        raise HTTPException(status_code=400, detail="Jenis latihan tidak tersedia dalam mod tempatan.")
    difficulty = str(data.get("difficulty") or "medium")
    user_id = str(data.get("user_id") or "guest")
    bank = deepcopy(QUESTION_BANK[quiz_type])
    session_id = uuid.uuid4().hex
    session = {
        "quiz_type": quiz_type,
        "user_id": user_id,
        "difficulty": difficulty,
        "bank": bank,
        "public_questions": [public_question(q, i, difficulty) for i, q in enumerate(bank)],
    }
    SESSIONS[session_id] = session
    LATEST_SESSION[(user_id, quiz_type)] = session_id
    return session_response(session_id, session)


@app.get("/api/comprehension/resume-latest")
def resume_comprehension(quiz_type: str, user_id: str):
    session_id = LATEST_SESSION.get((user_id, quiz_type))
    if not session_id or session_id not in SESSIONS:
        raise HTTPException(status_code=404, detail="Tiada sesi tempatan.")
    return session_response(session_id, SESSIONS[session_id])


def evaluate_answer(item: dict[str, Any], answer: str) -> tuple[bool, float]:
    clean_answer = normalize(answer)
    clean_correct = normalize(item.get("answer"))
    if item.get("options"):
        correct = clean_answer == clean_correct
        return correct, 1.0 if correct else 0.0
    if item.get("target"):
        correct = normalize(item["target"]) in clean_answer and len(clean_answer.split()) >= 4
        return correct, 1.0 if correct else 0.0
    keywords = [normalize(word) for word in item.get("keywords", [])]
    matches = sum(1 for word in keywords if word and word in clean_answer)
    threshold = 1 if len(keywords) <= 2 else 2
    correct = matches >= threshold or clean_answer == clean_correct
    return correct, min(1.0, matches / max(1, threshold))


def submit_comprehension_impl(data: dict[str, Any]):
    session_id = str(data.get("session_id") or "")
    session = SESSIONS.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Sesi tempatan tidak ditemui.")
    answer_map = {str(a.get("question_id")): str(a.get("answer") or "") for a in data.get("answers", [])}
    feedbacks = []
    total = 0.0
    max_score = 0.0
    for index, item in enumerate(session["bank"]):
        question_id = f"local-{index + 1}"
        answer = answer_map.get(question_id, "")
        correct, ratio = evaluate_answer(item, answer)
        marks = float(item.get("marks", 1))
        awarded = round(marks * ratio, 2)
        total += awarded
        max_score += marks
        feedbacks.append({
            "question_id": question_id,
            "question_text": item["question_text"],
            "user_answer": answer,
            "correct_answer": item["answer"],
            "is_correct": correct,
            "score": awarded,
            "marks_awarded": awarded,
            "max_marks": marks,
            "feedback": "Jawapan diterima dalam semakan tempatan." if correct else "Bandingkan jawapan anda dengan contoh jawapan yang diberikan.",
        })
    percentage = round((total / max_score * 100) if max_score else 0, 1)
    return {
        "session_id": session_id,
        "quiz_type": session["quiz_type"],
        "total_score": round(total, 2),
        "max_score": round(max_score, 2),
        "percentage": percentage,
        "grade": grade_from_percentage(percentage),
        "time_taken_seconds": None,
        "question_feedbacks": feedbacks,
        "essay_rubric": None,
        "overall_feedback": "Keputusan ini menggunakan semakan peraturan tempatan, bukan penilaian AI.",
        "suggestions": ["Semak contoh jawapan.", "Baca nota sebelum mencuba semula."],
        "local_mode": True,
    }


@app.post("/api/comprehension/submit")
def submit_comprehension(data: dict[str, Any]):
    return submit_comprehension_impl(data)


@app.post("/api/comprehension/latihan-submit")
def submit_latihan_comprehension(data: dict[str, Any]):
    return submit_comprehension_impl(data)


@app.post("/api/comprehension/retry")
def retry_comprehension(data: dict[str, Any]):
    old = SESSIONS.get(str(data.get("session_id") or ""))
    quiz_type = str(data.get("quiz_type") or (old or {}).get("quiz_type") or "")
    return start_comprehension({"quiz_type": quiz_type, "user_id": data.get("user_id", "guest"), "difficulty": (old or {}).get("difficulty", "medium")})


@app.get("/api/essay/types")
def essay_types():
    return {"types": list(ESSAY_PROMPTS)}


@app.post("/api/essay/start")
def start_essay(data: dict[str, Any]):
    quiz_type = str(data.get("quiz_type") or "")
    prompt = ESSAY_PROMPTS.get(quiz_type)
    if not prompt:
        raise HTTPException(status_code=400, detail="Jenis karangan tidak tersedia.")
    session_id = uuid.uuid4().hex
    question = {"question_id": "local-essay-1", "question_text": prompt["question"], "question_type": "open_ended", "difficulty": data.get("difficulty") or "medium", "options": None, "passage": None, "marks": prompt["max_score"]}
    SESSIONS[session_id] = {"quiz_type": quiz_type, "user_id": data.get("user_id", "guest"), "essay_prompt": prompt, "public_questions": [question]}
    return {"session_id": session_id, "quiz_type": quiz_type, "paper": "paper1", "title": prompt["title"], "description": prompt["description"], "instructions": prompt["instructions"], "questions": [question], "time_limit_minutes": None}


@app.get("/api/essay/resume-latest")
def resume_essay(quiz_type: str, user_id: str):
    raise HTTPException(status_code=404, detail="Tiada sesi karangan tempatan.")


def essay_result(session_id: str, answer: str, quiz_type: str):
    prompt = ESSAY_PROMPTS[quiz_type]
    words = len(answer.split())
    target = 80 if quiz_type == "karangan_pendek" else 180
    percentage = round(min(85.0, max(20.0, words / target * 80.0)), 1) if words else 0.0
    max_score = prompt["max_score"]
    total = round(max_score * percentage / 100, 1)
    component = round(total / 5, 1)
    return {
        "session_id": session_id,
        "quiz_type": quiz_type,
        "total_score": total,
        "max_score": max_score,
        "percentage": percentage,
        "grade": grade_from_percentage(percentage),
        "time_taken_seconds": None,
        "question_feedbacks": [{"question_id": "local-essay-1", "question_text": prompt["question"], "user_answer": answer, "correct_answer": None, "is_correct": None, "score": total, "feedback": "Semakan tempatan hanya menganggarkan kelengkapan berdasarkan panjang jawapan."}],
        "essay_rubric": {"content_score": component, "language_score": component, "grammar_score": component, "vocabulary_score": component, "coherence_score": component, "total_score": total, "max_score": max_score, "grade": grade_from_percentage(percentage)},
        "overall_feedback": "Ini ialah anggaran tempatan, bukan pemarkahan AI atau markah rasmi.",
        "suggestions": ["Pastikan isi menjawab tajuk.", "Gunakan penanda wacana.", "Semak tatabahasa dan ejaan."],
        "local_mode": True,
    }


@app.post("/api/essay/submit")
def submit_essay(data: dict[str, Any]):
    session_id = str(data.get("session_id") or "")
    session = SESSIONS.get(session_id)
    if not session or session.get("quiz_type") not in ESSAY_PROMPTS:
        raise HTTPException(status_code=404, detail="Sesi karangan tempatan tidak ditemui.")
    answers = data.get("answers") or []
    answer = str(answers[0].get("answer") or "") if answers else ""
    return essay_result(session_id, answer, session["quiz_type"])


@app.post("/api/essay/retry")
def retry_essay(data: dict[str, Any]):
    old = SESSIONS.get(str(data.get("session_id") or "")) or {}
    return start_essay({"quiz_type": old.get("quiz_type") or data.get("quiz_type"), "user_id": data.get("user_id", "guest")})


@app.post("/api/latihan/essay/mark")
def mark_latihan_essay(data: dict[str, Any]):
    quiz_type = str(data.get("essay_type") or "karangan_pendek")
    answer = str(data.get("answer") or "")
    if len(answer.split()) < 20:
        raise HTTPException(status_code=400, detail="Karangan terlalu pendek. Tulis sekurang-kurangnya 20 patah perkataan.")
    result = essay_result("local-latihan", answer, quiz_type)
    rubric = result["essay_rubric"]
    return {
        "essay_type": quiz_type,
        "difficulty": data.get("difficulty", "medium"),
        "mark": result["total_score"],
        "max_mark": result["max_score"],
        "percentage": result["percentage"],
        "grade": result["grade"],
        "word_count": len(answer.split()),
        "feedback": result["overall_feedback"],
        "suggestions": result["suggestions"],
        "rubric": {"content_score": rubric["content_score"], "language_score": rubric["language_score"], "grammar_score": rubric["grammar_score"], "vocabulary_score": rubric["vocabulary_score"], "coherence_score": rubric["coherence_score"]},
        "relevance": {"score": 0, "percentage": 0, "reason": "Semakan kesesuaian tajuk memerlukan AI dan dinyahaktifkan dalam mod tempatan.", "is_off_topic": False},
    }


@app.get("/api/speaking/tasks")
def speaking_tasks():
    return {"tasks": [], "message": "Latihan pertuturan memerlukan perkhidmatan audio/AI."}


@app.get("/api/listening/tasks")
def listening_tasks():
    return {"tasks": [], "message": "Latihan mendengar memerlukan penjanaan audio/AI."}


@app.post("/api/ai/chat")
def ai_chat():
    raise HTTPException(status_code=503, detail="AI Chat dinyahaktifkan dalam mod tempatan.")
