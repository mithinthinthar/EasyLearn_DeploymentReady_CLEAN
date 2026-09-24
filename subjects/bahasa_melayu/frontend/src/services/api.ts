import { API_URL } from "./config";
/**
 * Base axios instance pointing at the FastAPI backend.
 * All other service files import from here.
 */

const BASE_URL = API_URL;

function getCurrentUserId(): string {
  try {
    const raw = localStorage.getItem("easylearn_user");
    if (!raw) return "guest";
    const parsed = JSON.parse(raw);
    return parsed?.user_id || "guest";
  } catch {
    return "guest";
  }
}


// ── Types ─────────────────────────────────────────────────────────────────

interface EssayAnswers {
  question_id: string;
  answer: string;
}

interface ComprehensionAnswers {
  question_id: string;
  answer: string;
}

interface SpeakingAudioFiles {
  bacaan: File | Blob;
  r1: File | Blob;
  r2: File | Blob;
  k1: File | Blob;
  k2: File | Blob;
  // Optional reference transcripts (for evaluation/testing mode only)
  ref_bacaan?: string;
  ref_r1?: string;
  ref_r2?: string;
  ref_k1?: string;
  ref_k2?: string;  
}


// ── ESSAY (Paper 1 - Karangan) ────────────────────────────────────────────

export async function getEssayTypes(): Promise<unknown> {
  const res = await fetch(`${BASE_URL}/essay/types`);
  if (!res.ok) throw new Error("Failed to fetch essay types");
  return res.json();
}

export type EssayDifficulty = "easy" | "medium" | "hard";
export type EssayMode = "quiz" | "latihan";

export async function startEssay(
  quizType: string,
  userId: string,
  difficulty?: EssayDifficulty,
  mode: EssayMode = "quiz"
): Promise<unknown> {
  const res = await fetch(`${BASE_URL}/essay/start`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      quiz_type: quizType,
      user_id: userId,
      difficulty,
      mode,
    }),
  });

  if (!res.ok) throw new Error("Failed to start essay");
  return res.json();
}

export async function submitEssay(
  sessionId: string,
  quizType: string,
  userId: string,
  answers: EssayAnswers[]
): Promise<unknown> {
  const res = await fetch(`${BASE_URL}/essay/submit`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      session_id: sessionId,
      quiz_type: quizType,
      user_id: userId,
      answers: answers,
    }),
  });
  if (!res.ok) throw new Error("Failed to submit essay");
  return res.json();
}

export async function retryEssay(
  sessionId: string,
  quizType: string,
  userId: string,
): Promise<unknown> {
  const res = await fetch(`${BASE_URL}/essay/retry`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      session_id: sessionId,
      quiz_type: quizType,
      user_id: userId,
    }),
  });

  if (!res.ok) throw new Error("Failed to retry essay");

  return res.json();
}


// ── COMPREHENSION (Paper 2 - Tatabahasa & Pemahaman) ─────────────────────

export async function getComprehensionTypes(): Promise<unknown> {
  const res = await fetch(`${BASE_URL}/comprehension/types`);
  if (!res.ok) throw new Error("Failed to fetch comprehension types");
  return res.json();
}

export type ComprehensionDifficulty = "easy" | "medium" | "hard";

export type ComprehensionMode = "quiz" | "latihan";

export async function startComprehension(
  quizType: string,
  userId: string,
  difficulty?: ComprehensionDifficulty,
  mode: ComprehensionMode = "quiz"
): Promise<unknown> {
  const res = await fetch(`${BASE_URL}/comprehension/start`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ quiz_type: quizType, user_id: userId, difficulty, mode, }),
  });

  if (!res.ok) throw new Error("Failed to start comprehension");
  return res.json();
}

export async function submitComprehension(
  sessionId: string,
  quizType: string,
  userId: string,  
  answers: ComprehensionAnswers[]
): Promise<unknown> {
  const res = await fetch(`${BASE_URL}/comprehension/submit`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      session_id: sessionId,
      quiz_type: quizType,
      user_id: userId,
      answers: answers,
    }),
  });
  if (!res.ok) throw new Error("Failed to submit comprehension");
  return res.json();
}

export async function submitLatihanComprehension(
  sessionId: string,
  quizType: string,
  userId: string,
  answers: ComprehensionAnswers[]
): Promise<unknown> {
  const res = await fetch(`${BASE_URL}/comprehension/latihan-submit`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      session_id: sessionId,
      quiz_type: quizType,
      user_id: userId,
      answers: answers,
    }),
  });

  if (!res.ok) throw new Error("Failed to submit latihan comprehension");
  return res.json();
}

export async function retryComprehension(
  sessionId: string,
  quizType: string,
  userId: string,
): Promise<unknown> {
  const res = await fetch(`${BASE_URL}/comprehension/retry`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      session_id: sessionId,
      quiz_type: quizType,
      user_id: userId,
    }),
  });

  if (!res.ok) throw new Error("Failed to retry comprehension");

  return res.json();
}


// ── SPEAKING (Paper 3 - Ujian Lisan) ─────────────────────────────────────

export async function getSpeakingTasks(): Promise<unknown> {
  const res = await fetch(`${BASE_URL}/speaking/tasks`);
  if (!res.ok) throw new Error("Failed to fetch speaking tasks");
  return res.json();
}

export type SpeakingDifficulty = "easy" | "medium" | "hard";
export type SpeakingMode = "quiz" | "latihan";

export async function startSpeaking(
  taskType: string,
  userId: string,
  difficulty?: SpeakingDifficulty,
  mode: SpeakingMode = "quiz"
): Promise<unknown> {
  const res = await fetch(`${BASE_URL}/speaking/start`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      task_type: taskType,
      user_id: userId,
      difficulty,
      mode,
    }),
  });

  if (!res.ok) throw new Error("Failed to start speaking session");
  return res.json();
}

export async function submitSpeaking(
  sessionId: string,
  taskType: string,
  userId: string,
  stimulusText: string,
  soalanRangsangan: any,
  soalanKbat: any,
  audioFiles: SpeakingAudioFiles
): Promise<unknown> {
  const formData = new FormData();
  formData.append("session_id", sessionId);
  formData.append("task_type", taskType);
  formData.append("user_id", userId);

  formData.append("stimulus_text", stimulusText);
  formData.append("soalan_rangsangan", JSON.stringify(soalanRangsangan));
  formData.append("soalan_kbat", JSON.stringify(soalanKbat));

  formData.append("audio_bacaan", audioFiles.bacaan);
  formData.append("audio_r1", audioFiles.r1);
  formData.append("audio_r2", audioFiles.r2);
  formData.append("audio_k1", audioFiles.k1);
  formData.append("audio_k2", audioFiles.k2);

  const res = await fetch(`${BASE_URL}/speaking/submit`, {
    method: "POST",
    body: formData,
  });
  if (!res.ok) throw new Error("Failed to submit speaking");
  return res.json();
}

export async function submitLatihanSpeaking(
  sessionId: string,
  taskType: string,
  userId: string,
  stimulusText: string,
  soalanRangsangan: any,
  soalanKbat: any,
  audioFiles: SpeakingAudioFiles
): Promise<unknown> {
  const formData = new FormData();

  formData.append("session_id", sessionId);
  formData.append("task_type", taskType);
  formData.append("user_id", userId);

  formData.append("stimulus_text", stimulusText);
  formData.append("soalan_rangsangan", JSON.stringify(soalanRangsangan));
  formData.append("soalan_kbat", JSON.stringify(soalanKbat));

  formData.append("audio_bacaan", audioFiles.bacaan);
  formData.append("audio_r1", audioFiles.r1);
  formData.append("audio_r2", audioFiles.r2);
  formData.append("audio_k1", audioFiles.k1);
  formData.append("audio_k2", audioFiles.k2);

  const res = await fetch(`${BASE_URL}/speaking/latihan-submit`, {
    method: "POST",
    body: formData,
  });

  if (!res.ok) throw new Error("Failed to submit latihan speaking");

  return res.json();
}

export async function retrySpeaking(
  sessionId: string,
  taskType: string,
  userId: string,
): Promise<unknown> {
  const res = await fetch(`${BASE_URL}/speaking/retry`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      session_id: sessionId,
      task_type: taskType,
      user_id: userId,
    }),
  });

  if (!res.ok) throw new Error("Failed to retry speaking");

  return res.json();
}


// ── LISTENING (Paper 4 - Ujian Mendengar) ─────────────────────────────────

export interface ListeningAnswer {
  question_id: string;
  answer: string;
}

export async function getListeningTasks(): Promise<unknown> {
  const res = await fetch(`${BASE_URL}/listening/tasks`);
  if (!res.ok) throw new Error("Failed to fetch listening tasks");
  return res.json();
}

export type ListeningMode = "quiz" | "latihan";

export async function startListening(
  taskType: string,
  userId: string,
  difficulty: string,
  mode: ListeningMode = "quiz"
): Promise<any> {
  const res = await fetch(`${BASE_URL}/listening/start`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      task_type: taskType,
      user_id: userId,
      difficulty,
      mode,
    }),
  });

  if (!res.ok) {
    const text = await res.text();
    console.error("startListening error:", text);
    throw new Error("Failed to start listening session");
  }

  return res.json();
}

export async function submitListening(
  sessionId: string,
  taskType: string,
  userId: string,
  answers: ListeningAnswer[]
): Promise<any> {
  const res = await fetch(`${BASE_URL}/listening/submit`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      session_id: sessionId,
      task_type: taskType,
      user_id: userId,
      answers,
    }),
  });

  if (!res.ok) {
    const text = await res.text();
    console.error("submitListening error:", text);
    throw new Error("Failed to submit listening answers");
  }

  return res.json();
}

export async function submitLatihanListening(
  sessionId: string,
  taskType: string,
  userId: string,
  answers: ListeningAnswer[]
): Promise<any> {
  const res = await fetch(`${BASE_URL}/listening/latihan-submit`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      session_id: sessionId,
      task_type: taskType,
      user_id: userId,
      answers,
    }),
  });

  if (!res.ok) {
    const text = await res.text();
    console.error("submitLatihanListening error:", text);
    throw new Error("Failed to submit listening latihan answers");
  }

  return res.json();
}

export async function retryListening(
  sessionId: string,
  taskType: string,
  userId: string,
): Promise<unknown> {
  const res = await fetch(`${BASE_URL}/listening/retry`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      session_id: sessionId,
      task_type: taskType,
      user_id: userId,
    }),
  });

  if (!res.ok) throw new Error("Failed to retry listening");

  return res.json();
}


// ── AI CHAT ───────────────────────────────────────────────────────────────

export async function askAI(message: string): Promise<string> {
  const res = await fetch(`${BASE_URL}/ai/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message }),
  });

  if (!res.ok) {
    console.error("AI chat error:", res.status, await res.text());
    throw new Error("Failed to get AI reply");
  }

  const data = await res.json();
  return data.reply ?? "⚠️ Tiada jawapan dijana";
}


// ── DASHBOARD ───────────────────────────────────────────────────────────

export async function getDashboardOverview(): Promise<unknown> {
  const userId = getCurrentUserId();
  const res = await fetch(
    `${BASE_URL}/dashboard/overview?user_id=${encodeURIComponent(userId)}`
  );

  if (!res.ok) throw new Error("Failed to fetch dashboard overview");
  return res.json();
}


// ── HOME ───────────────────────────────────────────────────────────────

let homeRecommendationsLoading: Promise<unknown> | null = null;

export async function getHomeRecommendations(): Promise<unknown> {
  const userId = getCurrentUserId();

  if (homeRecommendationsLoading) {
    return homeRecommendationsLoading;
  }

  homeRecommendationsLoading = fetch(
    `${BASE_URL}/home/recommendations?user_id=${encodeURIComponent(userId)}`
  )
    .then((res) => {
      if (!res.ok) {
        throw new Error("Failed to fetch home recommendations");
      }

      return res.json();
    })
    .finally(() => {
      homeRecommendationsLoading = null;
    });

  return homeRecommendationsLoading;
}


// ── LATIHAN AI MARKING ─────────────────────────────────────────────────────

export interface LatihanEssayMarkRequest {
  essay_type: "karangan_pendek" | "karangan_panjang";
  difficulty: "easy" | "medium" | "hard";
  question: string;
  answer: string;
}

export interface LatihanEssayMarkResponse {
  essay_type: string;
  difficulty: string;
  mark: number;
  max_mark: number;
  percentage: number;
  grade: string;
  word_count: number;
  feedback: string;
  suggestions: string[];
  rubric: {
    content_score: number;
    language_score: number;
    grammar_score: number;
    vocabulary_score: number;
    coherence_score: number;
  };
  relevance: {
    score: number;
    percentage: number;
    reason: string;
    is_off_topic: boolean;
  };
}

export async function markLatihanEssay(
  payload: LatihanEssayMarkRequest
): Promise<LatihanEssayMarkResponse> {
  const res = await fetch(`${BASE_URL}/latihan/essay/mark`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => null);
    throw new Error(errorData?.detail || "Failed to mark latihan essay");
  }

  return res.json();
}