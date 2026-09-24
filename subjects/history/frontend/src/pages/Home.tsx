import React, { useState } from 'react';
import { Brain, Check, Pen, Loader2, AlertCircle } from 'lucide-react';
import { Topic, StudyModeType } from '../types';
import { ApiQuestion } from '../types';
import { TOPICS } from '../data/topics';
import './Home.css';
import { getAuth } from "firebase/auth";
import { HISTORY_API_URL, LOCAL_MODE } from '../config';

const ESSAY_CHAPTERS = new Set([1, 2, 3, 4, 5]);

interface HomeProps {
  onStart: (topic: Topic, mode: StudyModeType, prefetchedQuestions?: ApiQuestion[]) => void;
}

const Home: React.FC<HomeProps> = ({ onStart }) => {
  const [isLoading, setIsLoading] = useState(false);
  const [recError, setRecError] = useState<string | null>(null);

  const studyModes = [
    { id: 'flashcard', icon: Brain, label: 'Flash Cards', color: 'blue' },
    { id: 'quiz', icon: Check, label: 'Quick Quiz', color: 'emerald' },
    { id: 'essay', icon: Pen, label: 'Essay Practice', color: 'orange' }
  ];

  // Called when user clicks "Quick Quiz" under Recommended for You
  const handleRecommendedQuiz = async () => {
    setIsLoading(true);
    setRecError(null);

    try {
      if (LOCAL_MODE) {
        // Firebase recommendations are unavailable locally. Start a normal
        // chapter quiz instead so this card remains useful in guest mode.
        const availableTopics = TOPICS.filter(topic => topic.chapterNumber);
        const randomTopic = availableTopics[Math.floor(Math.random() * availableTopics.length)];

        if (!randomTopic) {
          throw new Error("No quiz chapters are available.");
        }

        onStart(randomTopic, 'quiz');
        return;
      }

      const auth = getAuth();
      const user = auth.currentUser;
      if (!user) throw new Error("Not logged in");
      const token = await user.getIdToken();

      // Step 1: POST /quiz/recommendation — updates the weakest chapter in Firestore
      const recResponse = await fetch(`${HISTORY_API_URL}/quiz/recommendation`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
      });

      if (!recResponse.ok) {
        const err = await recResponse.json();
        throw new Error(err.error || 'Failed to update recommendation');
      }

      // Step 2: GET /recommend/quiz — fetch questions for the recommended chapter
      const quizResponse = await fetch(`${HISTORY_API_URL}/recommend/quiz`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`
        },
      });

      if (!quizResponse.ok) {
        const err = await quizResponse.json();
        throw new Error(err.error || 'Failed to fetch recommended questions');
      }

      const data: ApiQuestion[] = await quizResponse.json();

      if (!data || data.length === 0) {
        throw new Error('No questions found for your recommended chapter.');
      }

      // Step 3: Build a synthetic Topic from the first question's chapter
      const chapter = data[0].chapter;
      const matchedTopic = TOPICS.find(t => t.chapterNumber === chapter) ?? {
        id: `ch${chapter}`,
        chapterNumber: chapter,
        title: `Chapter ${chapter}`,
        subtitle: `Chapter ${chapter}`,
        description: 'Recommended chapter based on your mastery level.',
      } as Topic;

      // Step 4: Launch QuizMode with pre-fetched questions (skips QuizMode's own fetch)
      onStart(matchedTopic, 'recommended-quiz', data);

    } catch (error) {
      console.error("Recommended quiz failed:", error);
      setRecError(error instanceof Error ? error.message : 'Something went wrong.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <main className="home-container">
      <div className="welcome-section">
        <h1 className="welcome-title">Welcome back.</h1>
        <p className="welcome-text">Select a chapter below to begin your session.</p>
      </div>

      {/* RECOMMENDATION SECTION */}
      <section className="recommendation-section">
        <div className="rec-header">
          <h2 className="rec-title">Recommended for You</h2>
        </div>

        {recError && (
          <div className="rec-error">
            <AlertCircle size={16} />
            <span>{recError}</span>
          </div>
        )}

        <div className="rec-grid">
          {/* Recommended Quiz Card — fetches & launches immediately */}
          <div
            className="rec-card rec-emerald"
            onClick={!isLoading ? handleRecommendedQuiz : undefined}
            style={{ cursor: isLoading ? 'not-allowed' : 'pointer' }}
          >
            <div className="rec-icon-box">
              {isLoading ? <Loader2 size={24} className="animate-spin" /> : <Check size={24} />}
            </div>
            <div className="rec-info">
              <span className="rec-label">{LOCAL_MODE ? 'Local Practice' : 'Weak Areas'}</span>
              <h3 className="rec-card-title">{isLoading ? 'Loading...' : 'Quick Quiz'}</h3>
            </div>
          </div>

          {/* Flash Cards — static, uses first topic as placeholder */}
          <div
            className="rec-card rec-blue"
            onClick={() => onStart(TOPICS[0], 'flashcard')}
            style={{ cursor: 'pointer' }}
          >
            <div className="rec-icon-box">
              <Brain size={24} />
            </div>
            <div className="rec-info">
              <span className="rec-label">Daily Review</span>
              <h3 className="rec-card-title">Flash Cards</h3>
            </div>
          </div>

          {/* Essay Practice — static */}
          <div
            className="rec-card rec-orange"
            onClick={() => onStart(TOPICS[0], 'essay')}
            style={{ cursor: 'pointer' }}
          >
            <div className="rec-icon-box">
              <Pen size={24} />
            </div>
            <div className="rec-info">
              <span className="rec-label">Writing Practice</span>
              <h3 className="rec-card-title">Essay Practice</h3>
            </div>
          </div>
        </div>
      </section>

      <div className="topics-grid">
        {TOPICS.map((topic) => (
          <div key={topic.id} className="topic-card group">
            <div className="topic-content">
              <span className="topic-label">{topic.title}</span>
              <h2 className="topic-heading">{topic.subtitle}</h2>
              <p className="topic-description">{topic.description}</p>
            </div>

            <div className="mode-buttons">
              {studyModes.map((mode) => {
                const isMissingEssay = mode.id === 'essay' && !ESSAY_CHAPTERS.has(topic.chapterNumber);

                return (
                  <button
                    key={mode.id}
                    onClick={() => onStart(topic, mode.id as StudyModeType)}
                    className={`mode-button mode-${mode.color} ${isMissingEssay ? 'mode-disabled' : ''}`}
                    disabled={isMissingEssay}
                    title={isMissingEssay ? 'The supplied essay dataset contains Chapters 1–5 only.' : mode.label}
                  >
                    <mode.icon size={22} className="mb-2 opacity-80" />
                    <span className="mode-label">{isMissingEssay ? 'No Essay Data' : mode.label}</span>
                  </button>
                );
              })}
            </div>
          </div>
        ))}
      </div>
    </main>
  );
};

export default Home;
