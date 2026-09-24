/**
 * TypeScript types that mirror the backend Pydantic schemas.
 */

// ── Quiz ─────────────────────────────────────────────────────────────────────

export type QuizType =
  | "karangan_pendek"
  | "karangan_panjang"
  | "golongan_kata"
  | "bina_ayat"
  | "jenis_ayat"
  | "kesalahan_bahasa"
  | "pemahaman"
  | "rumusan" ;

export type PaperType = "paper1" | "paper2" | "paper3";

export interface QuizQuestion {
  question_id: string;
  question_text: string;
  question_type: "factual" | "inferential" | "evaluative" | "open_ended";
  difficulty: "low" | "medium" | "high";
  options?: string[] | null;
  passage?: string | null;
}

export interface QuizStartResponse {
  session_id: string;
  quiz_type: QuizType;
  paper: PaperType;
  title: string;
  description: string;
  instructions: string;
  questions: QuizQuestion[];
  time_limit_minutes?: number | null;
}

export interface QuizAnswer {
  question_id: string;
  answer: string;
}

export interface EssayRubric {
  content_score: number;
  language_score: number;
  grammar_score: number;
  vocabulary_score: number;
  coherence_score: number;
  total_score: number;
  max_score: number;
  grade: "A" | "B" | "C" | "D" | "E" | "F";
}

export interface QuestionFeedback {
  question_id: string;
  question_text: string;
  user_answer: string;
  correct_answer?: string | null;
  is_correct?: boolean | null;
  score: number;
  feedback: string;
}

export interface QuizSubmitResponse {
  session_id: string;
  quiz_type: QuizType;
  total_score: number;
  max_score: number;
  percentage: number;
  grade?: string | null;
  time_taken_seconds?: number | null;
  question_feedbacks: QuestionFeedback[];
  essay_rubric?: EssayRubric | null;
  overall_feedback: string;
  suggestions: string[];
}