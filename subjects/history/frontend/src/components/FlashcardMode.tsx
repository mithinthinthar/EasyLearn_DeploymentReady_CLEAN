import React, { useState } from 'react';
import { ChevronLeft, ChevronRight } from 'lucide-react';
import { Topic } from '../types';
import './FlashcardMode.css';

interface FlashcardModeProps {
  topic: Topic;
  onBack: () => void;
}

const FlashcardMode: React.FC<FlashcardModeProps> = ({ topic, onBack }) => {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isFlipped, setIsFlipped] = useState(false);
  const cards = topic.flashcards;

  const nextCard = () => {
    setIsFlipped(false);
    setTimeout(() => setCurrentIndex((i) => (i + 1) % cards.length), 200);
  };

  const prevCard = () => {
    setIsFlipped(false);
    setTimeout(() => setCurrentIndex((i) => (i - 1 + cards.length) % cards.length), 200);
  };

  return (
    <div className="flashcard-container">
      <div className="flashcard-header">
        <button onClick={onBack} className="back-button">
          <ChevronLeft size={16} /> Back to Chapters
        </button>
        <span className="counter">{currentIndex + 1} / {cards.length}</span>
      </div>
      
      <div className="topic-info">
        <h2 className="topic-title">{topic.title}</h2>
        <h1 className="topic-subtitle">{topic.subtitle}</h1>
      </div>

      {/* The Card - Added 'group' class here manually */}
      <div 
        className="flashcard-scene group"
        onClick={() => setIsFlipped(!isFlipped)}
      >
        <div className={`flashcard ${isFlipped ? 'is-flipped' : ''}`}>
          <div className="flashcard-face flashcard-front">
            <span className="card-label">Question</span>
            <h3 className="card-term">{cards[currentIndex].term}</h3>
            <p className="click-hint">Click to flip</p>
          </div>
          <div className="flashcard-face flashcard-back">
            <span className="card-label-back">Answer</span>
            <p className="card-definition">{cards[currentIndex].definition}</p>
          </div>
        </div>
      </div>

      {/* Controls */}
      <div className="flashcard-controls">
        <button onClick={prevCard} className="control-button prev">
          <ChevronLeft size={24} />
        </button>
        <button onClick={nextCard} className="control-button next">
          <ChevronRight size={24} />
        </button>
      </div>
    </div>
  );
};

export default FlashcardMode;