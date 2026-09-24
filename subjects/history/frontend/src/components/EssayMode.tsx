import React, { useState, useEffect } from 'react';
import { ArrowLeft, Send, Loader2, CheckCircle, AlertCircle, RefreshCw } from 'lucide-react';
// 1. Import types directly from your index.ts (aliased as '../types')
import { Topic, EssayQuestion, GradingResult } from '../types'; 
import { HISTORY_API_URL } from '../config';
import './EssayMode.css';

interface EssayModeProps {
  topic: Topic;
  onBack: () => void;
}

const EssayMode: React.FC<EssayModeProps> = ({ topic, onBack }) => {
  // 2. Use the imported types for state
  const [question, setQuestion] = useState<EssayQuestion | null>(null);
  const [studentText, setStudentText] = useState('');
  const [result, setResult] = useState<GradingResult | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isGrading, setIsGrading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchRandomQuestion = async () => {
    setIsLoading(true);
    setError(null);
    setResult(null);
    setStudentText('');
    
    try {
      const res = await fetch(`${HISTORY_API_URL}/essay/get?chapter=${topic.chapterNumber}`);
      if (!res.ok) throw new Error("No essay questions found for this chapter.");
      
      const data = await res.json();

      // 3. IMPORTANT: Map Python (snake_case) to TypeScript (camelCase)
      const formattedQuestion: EssayQuestion = {
        id: data.question_id,           // matches 'id' in index.ts
        sectionType: data.section_type, // matches 'sectionType' in index.ts
        question: data.question_text,   // matches 'question' in index.ts
        totalMarks: data.total_marks    // matches 'totalMarks' in index.ts
      };

      setQuestion(formattedQuestion);
    } catch (err) {
      console.error(err);
      setError(err instanceof Error ? err.message : "Failed to load question");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchRandomQuestion();
  }, [topic.chapterNumber]);

  const handleGrade = async () => {
    if (!question || !studentText.trim()) return;

    setIsGrading(true);
    try {
      const res = await fetch(`${HISTORY_API_URL}/api/grade`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          // Send data back in the format Python expects (snake_case)
          section_type: question.sectionType, 
          question_id: question.id,
          // Removed set_id as discussed previously
          student_text: studentText
        }),
      });

      if (!res.ok) throw new Error("Grading failed");
      
      const data: GradingResult = await res.json();
      setResult(data);
    } catch (err) {
      alert("Error grading essay. Please try again.");
    } finally {
      setIsGrading(false);
    }
  };

  if (isLoading) {
    return (
      <div className="quiz-container flex flex-col items-center justify-center min-h-[400px]">
        <Loader2 className="animate-spin text-indigo-600 mb-4" size={40} />
        <p className="text-slate-600 font-medium">Loading essay question...</p>
      </div>
    );
  }

  if (error || !question) {
    return (
      <div className="quiz-container text-center py-12">
        <AlertCircle className="mx-auto text-red-400 mb-4" size={50} />
        <h3 className="text-xl font-bold text-slate-800 mb-2">Error</h3>
        <p className="text-slate-600 mb-6">{error}</p>
        <button onClick={onBack} className="px-6 py-2 bg-slate-200 rounded-lg font-medium hover:bg-slate-300 transition">
          Go Back
        </button>
      </div>
    );
  }

  return (
    <div className="quiz-container max-w-3xl">
      <button onClick={onBack} className="quit-button">
        <ArrowLeft size={16} /> Quit Essay Mode
      </button>

      {/* Question Card */}
      <div className="essay-card">
        <div className="essay-header">
            {/* 5. Access properties using the interface names */}
            <h2 className="essay-question-text">{question.question}</h2>
            <span className="mark-badge">
                {question.totalMarks} Marks
            </span>
        </div>

        <textarea
          value={studentText}
          onChange={(e) => setStudentText(e.target.value)}
          placeholder="Type your answer here..."
          className="essay-textarea"
          disabled={!!result || isGrading}
        />

        <div className="flex justify-end gap-3">
          {!result ? (
            <button
              onClick={handleGrade}
              disabled={isGrading || !studentText.trim()}
              className="submit-button"
            >
              {isGrading ? <Loader2 className="animate-spin" size={20} /> : <Send size={20} />}
              {isGrading ? 'Grading...' : 'Submit Answer'}
            </button>
          ) : (
            <button onClick={fetchRandomQuestion} className="next-button">
              Next Question <RefreshCw size={18} />
            </button>
          )}
        </div>
      </div>

      {/* Results Section */}
      {result && (
        <div className={`result-container ${result.marks_awarded > 0 ? 'success' : 'warning'}`}>
            <div className="result-header">
                <h3 className="result-title">
                    <CheckCircle className="text-emerald-600" /> AI Grading Result
                </h3>
                <div className="result-score">
                    {result.marks_awarded} <span>/ {result.total_marks}</span>
                </div>
            </div>

            {result.breakdown.length > 0 ? (
                <div className="matches-list">
                    <p className="matches-label">Matched Points</p>
                    {result.breakdown.map((item, idx) => (
                        <div key={idx} className="match-card">
                            <p className="student-quote">"{item.student_sentence}"</p>
                            <div className="match-feedback">
                                <CheckCircle size={14} /> Matches: "{item.matched_fact}"
                            </div>
                        </div>
                    ))}
                </div>
            ) : (
               <p className="text-center text-slate-500 italic py-2">No specific points matched the answer scheme. Try to be more precise.</p>
            )}
        </div>
      )}
    </div>
  );
};

export default EssayMode;
