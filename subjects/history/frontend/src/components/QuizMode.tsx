import React, { useState, useEffect, useRef } from 'react';
import { X, ChevronRight, Check, Trophy, Loader2, AlertCircle } from 'lucide-react';
import { Topic, QuizQuestion, ApiQuestion } from '../types';
import './QuizMode.css';
import { useAuth } from '../context/AuthContext';
import { HISTORY_API_URL, LOCAL_MODE } from '../config';

const PLATFORM_URL = process.env.REACT_APP_SHARED_AUTH_URL || (["localhost", "127.0.0.1"].includes(window.location.hostname) ? 'http://localhost:4500' : '/platform-api');

interface QuizModeProps {
  topic: Topic;
  onBack: () => void;
  isTestMode?: boolean;
  // When provided, QuizMode skips its own fetch and uses these directly
  recommendedQuestions?: ApiQuestion[];
}

const QuizMode: React.FC<QuizModeProps> = ({
  topic,
  onBack,
  isTestMode = false,
  recommendedQuestions,
}) => {
  const { user } = useAuth();
  const [questions, setQuestions] = useState<QuizQuestion[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [currentQIndex, setCurrentQIndex] = useState(0);
  const [selectedOption, setSelectedOption] = useState<number | null>(null);
  const [isAnswered, setIsAnswered] = useState(false);
  const [score, setScore] = useState(0);
  const [showResults, setShowResults] = useState(false);
  const [startTime, setStartTime] = useState<number>(Date.now());
  const submittedQuestions = useRef<Set<string>>(new Set());

  useEffect(() => {
    setStartTime(Date.now());
  }, [currentQIndex]);

  // Helper: convert ApiQuestion[] -> QuizQuestion[]
  const formatQuestions = (data: ApiQuestion[]): QuizQuestion[] =>
    data.map(q => ({
      id: q.question_id,
      question: q.question,
      options: q.options.map(o => o.option_text),
      correctIndex: q.options.findIndex(opt => opt.is_correct === 1),
      explanation: q.explaination,
    }));

  useEffect(() => {
    // If pre-fetched questions are passed in (recommended quiz), skip the API call
    if (recommendedQuestions && recommendedQuestions.length > 0) {
      setQuestions(formatQuestions(recommendedQuestions));
      setIsLoading(false);
      return;
    }

    // Normal flow: fetch by chapter number
    const controller = new AbortController();
    const signal = controller.signal;

    const fetchQuestions = async () => {
      if (!topic.chapterNumber) {
        setError("Invalid chapter number");
        setIsLoading(false);
        return;
      }

      try {
        setIsLoading(true);
        const response = await fetch(
          `${HISTORY_API_URL}/questions/chapter?chapter=${topic.chapterNumber}`,
          { signal }
        );

        if (!response.ok) throw new Error('Failed to contact server.');

        const data: ApiQuestion[] = await response.json();

        if (!signal.aborted) {
          setQuestions(formatQuestions(data));
          setIsLoading(false);
        }
      } catch (err) {
        if (err instanceof Error && err.name === 'AbortError') return;
        console.error("Error fetching quiz:", err);
        if (!signal.aborted) {
          setError(err instanceof Error ? err.message : 'An error occurred while loading questions.');
          setIsLoading(false);
        }
      }
    };

    fetchQuestions();
    return () => controller.abort();
  }, [topic.chapterNumber, recommendedQuestions]);

  // --- LOADING VIEW ---
  if (isLoading) {
    return (
      <div className="quiz-container flex flex-col items-center justify-center min-h-[400px]">
        <Loader2 className="animate-spin text-indigo-600 mb-4" size={40} />
        <p className="text-slate-600 font-medium">Loading questions...</p>
      </div>
    );
  }

  // --- ERROR VIEW ---
  if (error) {
    return (
      <div className="quiz-container flex flex-col items-center justify-center min-h-[400px] text-center">
        <AlertCircle className="text-red-500 mb-4" size={50} />
        <h3 className="text-xl font-bold text-slate-800 mb-2">Error</h3>
        <p className="text-slate-600 mb-6">{error}</p>
        <button onClick={onBack} className="px-6 py-2 bg-slate-200 rounded-lg font-medium hover:bg-slate-300 transition">
          Go Back
        </button>
      </div>
    );
  }

  // --- EMPTY STATE VIEW ---
  if (questions.length === 0) {
    return (
      <div className="quiz-container text-center py-12">
        <p className="text-slate-500 text-lg">No questions found for this chapter.</p>
        <button onClick={onBack} className="mt-6 px-6 py-2 bg-slate-200 rounded-lg font-medium hover:bg-slate-300 transition">
          Go Back
        </button>
      </div>
    );
  }

  const question = questions[currentQIndex];
  const totalQ = questions.length;

  const handleOptionClick = (index: number) => {
    if (isAnswered && !isTestMode) return;
    setSelectedOption(index);
  };

  const saveInteraction = async (isCorrect: boolean) => {
    if (LOCAL_MODE || !user || !question) return;
    const submissionKey = `${topic.id}:${question.id}`;
    if (submittedQuestions.current.has(submissionKey)) return;
    submittedQuestions.current.add(submissionKey);
    const timeTaken = Date.now() - startTime;
    try {
      await fetch(`${PLATFORM_URL}/events`, {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          subject: 'history',
          activity_type: 'practice',
          title: `${topic.subtitle} quiz`,
          percentage: isCorrect ? 100 : 0,
          score: isCorrect ? 1 : 0,
          max_score: 1,
          questions_answered: 1,
          duration_minutes: Math.max(0.1, timeTaken / 60000),
          metadata: {
            question_id: question.id,
            chapter_id: topic.id,
            is_correct: isCorrect,
          },
        }),
      });
    } catch (error) {
      console.error("Error saving interaction:", error);
    }
  };

  const handleSubmitAnswer = () => {
    if (selectedOption === null) return;
    const isCorrect = selectedOption === question.correctIndex;
    if (isCorrect) setScore((s) => s + 1);
    saveInteraction(isCorrect);
    if (!isTestMode) {
      setIsAnswered(true);
    } else {
      handleNext();
    }
  };

  const handleNext = () => {
    if (currentQIndex < totalQ - 1) {
      setCurrentQIndex((p) => p + 1);
      setSelectedOption(null);
      setIsAnswered(false);
    } else {
      setShowResults(true);
    }
  };

  if (showResults) {
    const percentage = Math.round((score / totalQ) * 100);
    return (
      <div className="results-container">
        <div className="trophy-icon">
          <Trophy className="text-yellow-600" size={40} />
        </div>
        <h2 className="results-title">{isTestMode ? 'Test Completed!' : 'Quiz Completed!'}</h2>
        <p className="results-subtitle">You have finished {topic.subtitle}.</p>
        <div className="score-display">
          <span className="score-number">{percentage}</span>
          <span className="score-percent">%</span>
        </div>
        <p className="score-detail">Score: {score} / {totalQ} correct</p>
        <button onClick={onBack} className="results-button">Return to Home</button>
      </div>
    );
  }

  return (
    <div className="quiz-container">
      <button onClick={onBack} className="quit-button">
        <X size={16} /> Quit {isTestMode ? 'Test' : 'Quiz'}
      </button>

      <div className="progress-bar-container">
        <div className="progress-track">
          <div
            className="progress-fill"
            style={{ width: `${((currentQIndex + 1) / totalQ) * 100}%` }}
          ></div>
        </div>
        <span className="progress-text">Q {currentQIndex + 1} / {totalQ}</span>
      </div>

      <div className="question-section">
        <h3 className="question-text">{question.question}</h3>
      </div>

      <div className="options-list">
        {question.options.map((option, idx) => {
          let optionClass = "option-button";
          if (isAnswered && !isTestMode) {
            if (idx === question.correctIndex) optionClass += " correct";
            else if (idx === selectedOption) optionClass += " incorrect";
            else optionClass += " disabled";
          } else if (selectedOption === idx) {
            optionClass += " selected";
          }

          return (
            <button
              key={idx}
              onClick={() => handleOptionClick(idx)}
              disabled={isAnswered && !isTestMode}
              className={optionClass}
            >
              <span>{option}</span>
              {isAnswered && !isTestMode && idx === question.correctIndex && <Check size={20} className="text-emerald-600" />}
              {isAnswered && !isTestMode && idx === selectedOption && idx !== question.correctIndex && <X size={20} className="text-red-500" />}
            </button>
          );
        })}
      </div>

      <div className="action-section">
        {isAnswered && !isTestMode && (
          <div className={`feedback-box ${selectedOption === question.correctIndex ? 'correct' : 'incorrect'}`}>
            <p className="feedback-title">
              {selectedOption === question.correctIndex ? 'Correct!' : 'Incorrect'}
            </p>
            <p className="feedback-text">{question.explanation}</p>
          </div>
        )}

        {!isAnswered && !isTestMode ? (
          <button
            onClick={handleSubmitAnswer}
            disabled={selectedOption === null}
            className="submit-button"
          >
            Submit Answer
          </button>
        ) : (
          <button
            onClick={isTestMode ? handleSubmitAnswer : handleNext}
            disabled={isTestMode && selectedOption === null}
            className="next-button"
          >
            {currentQIndex < totalQ - 1 ? 'Next Question' : 'View Results'} <ChevronRight size={18} />
          </button>
        )}
      </div>
    </div>
  );
};

export default QuizMode;
