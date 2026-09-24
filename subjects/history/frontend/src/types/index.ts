export type PageRoute = 'home' | 'game' | 'dashboard' | 'chatbot' | 'study';
export type StudyModeType = 'flashcard' | 'quiz' | 'essay' | 'recommended-quiz' | null;

// --- Internal UI Types ---
export interface FlashcardData {
  id: number;
  term: string;
  definition: string;
}

export interface QuizQuestion {
  id: number;
  question: string;
  options: string[];
  correctIndex: number;
  explanation: string;
}

// --- Raw API Response Types ---
// These match your Flask API JSON structure exactly
export interface ApiOption {
  option_id: number;
  question_id: number;
  option_text: string;
  is_correct: number; // API returns 0 or 1
}

export interface ApiQuestion {
  chapter: number;
  form: number;
  question_id: number;
  question: string;
  explaination: string;
  options: ApiOption[];
}

//===================== Essay =======================================
export interface EssayQuestion {
  id: string;             // e.g., "1a" matches python "question_id"
  sectionType: string;    // e.g., "Bahagian B (Esei)" matches python "section_type"
  question: string;       // The text to display
  totalMarks: number;
}

// NEW: Interface for the API Response
export interface GradingResult {
  question_id: string;
  marks_awarded: number;
  total_marks: number;
  is_kbat: boolean;
  breakdown: {
    student_sentence: string;
    matched_fact: string;
    score: number;
  }[];
}

export interface Topic {
  id: string;
  chapterNumber: number;
  title: string;
  subtitle: string;
  description: string;
  flashcards: FlashcardData[];
  questions?: QuizQuestion[];
  essays?: EssayQuestion[]; // Added optional essays array
}

export interface HistoryItem {
  date: string;
  accuracy: number;
  questions_answered: number;
}

export interface DashboardData {
  streak: number;
  average_score: number;
  total_questions: number;
  history: HistoryItem[];
}
