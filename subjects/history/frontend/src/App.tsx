import React, { useState } from 'react';
import '@fontsource/lexend/500.css';
import '@fontsource/lexend/600.css';
import '@fontsource/lexend/700.css';
import '@fontsource/quicksand/400.css';
import '@fontsource/quicksand/500.css';
import '@fontsource/quicksand/600.css';
import '@fontsource/quicksand/700.css';
import { useAuth } from './context/AuthContext';
import Header from './components/Header';
import Home from './pages/Home';
import Dashboard from './pages/Dashbaord';
import Game from './pages/Game';
import FlashcardMode from './components/FlashcardMode';
import QuizMode from './components/QuizMode';
import EssayMode from './components/EssayMode';
import HistoryChatbot from './components/HistoryChatbot';
import { PageRoute, Topic, StudyModeType } from './types';
import { ApiQuestion } from './types';
import './App.css';

function App() {
  const { user, portalUser } = useAuth();
  const [currentPage, setCurrentPage] = useState<PageRoute>('dashboard');
  const [selectedTopic, setSelectedTopic] = useState<Topic | null>(null);
  const [studyMode, setStudyMode] = useState<StudyModeType>(null);

  const [recommendedQuestions, setRecommendedQuestions] = useState<ApiQuestion[] | null>(null);

    const startStudy = (topic: Topic, mode: StudyModeType, prefetchedQuestions?: ApiQuestion[]) => {
    setSelectedTopic(topic);
    setStudyMode(mode);
    setRecommendedQuestions(prefetchedQuestions ?? null);
    setCurrentPage('study');
  };

  const goHome = () => {
    setCurrentPage('home');
    setSelectedTopic(null);
    setStudyMode(null);
    setRecommendedQuestions(null);
  };

  const renderPage = () => {
    switch (currentPage) {
      case 'home':
        return <Home onStart={startStudy} />;
      case 'dashboard':
        return <Dashboard onPractice={() => setCurrentPage('home')} />;
      case 'game':
        return <Game onGoHome={goHome} />;
      case 'chatbot':
        return <Dashboard onPractice={() => setCurrentPage('home')} />;
      case 'study':
        if (!selectedTopic) return null;
        if (studyMode === 'flashcard') return <FlashcardMode topic={selectedTopic} onBack={goHome} />;
        if (studyMode === 'quiz') return <QuizMode topic={selectedTopic} onBack={goHome} isTestMode={false} />;
        if (studyMode === 'recommended-quiz') return (
          <QuizMode
            topic={selectedTopic}
            onBack={goHome}
            isTestMode={false}
            // Pass pre-fetched questions so QuizMode skips its own fetch
            recommendedQuestions={recommendedQuestions ?? undefined}
          />
        );
        if (studyMode === 'essay') return <EssayMode topic={selectedTopic} onBack={goHome} />;
        // if (studyMode === 'test') return <QuizMode topic={selectedTopic} onBack={goHome} isTestMode={true} />;
        return null;
      default:
        return <Home onStart={startStudy} />;
    }
  };

  //   if (loading) {
  //     return <div className="min-h-screen flex items-center justify-center"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div></div>;
  // }

  if (!user || !portalUser) return null;

  const handleNavigate = (page: PageRoute) => {
    if (portalUser.role !== 'student' && page !== 'dashboard') {
      setCurrentPage('dashboard');
      return;
    }
    setCurrentPage(page);
  };

  return (
    <div className="app-container">
      <Header currentPage={currentPage} onNavigate={handleNavigate} />
      {renderPage()}
      {portalUser.role === 'student' && <HistoryChatbot />}
    </div>
  );
}

export default App;
