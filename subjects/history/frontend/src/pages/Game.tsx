import React, { useState } from 'react';
import { Gamepad2, ChevronLeft } from 'lucide-react';
import BucketGame from '../components/BucketGame';
import './Game.css';

interface GameProps {
  onGoHome: () => void;
}

const Game: React.FC<GameProps> = ({ onGoHome }) => {
  const [selectedSubtopic, setSelectedSubtopic] = useState<string | null>(null);

  const levels = [
    { id: "1.1", title: "Ciri-ciri Negara Bangsa Kerajaan Alam Melayu" },
    { id: "1.2", title: "Ciri-ciri Negara Bangsa Kesultanan Melayu Melaka" }
  ];

  if (selectedSubtopic) {
    return (
      <BucketGame 
        subtopic={selectedSubtopic} 
        onBack={() => setSelectedSubtopic(null)} 
      />
    );
  }

  return (
    <main className="game-container">
      <div className="game-header text-center mb-12">
        <div className="game-icon-wrapper">
          <Gamepad2 size={48} />
        </div>
        <h1 className="game-title">Sejarah Arcade</h1>
        <p className="game-description">Select a chapter to start the Bucket Sorter game.</p>
      </div>

      {/* --- YouTube Video Section --- */}
      <div className="flex justify-center mb-12 max-w-3xl mx-auto px-4">
        <div className="w-full aspect-video rounded-2xl overflow-hidden shadow-md border border-slate-100">
          <iframe
            className="w-full h-full"
            src="https://www.youtube.com/embed/9zbNSBsSqRg?si=JgO7XZeJ3yBhX-fc"
            title="Tutorial Video"
            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
            allowFullScreen
          ></iframe>
        </div>
      </div>
      {/* ----------------------------- */}

      <div className="levels-grid grid grid-cols-1 md:grid-cols-2 gap-6 max-w-4xl mx-auto">
        {levels.map((level) => (
          <button
            key={level.id}
            onClick={() => setSelectedSubtopic(level.id)}
            className="level-card p-8 bg-white rounded-2xl border border-slate-100 shadow-sm hover:border-indigo-500 hover:shadow-md transition-all text-left"
          >
            <span className="text-indigo-600 font-bold text-sm">Chapter {level.id}</span>
            <h2 className="text-xl font-extrabold text-slate-900 mt-2">{level.title}</h2>
          </button>
        ))}
      </div>

      <button onClick={onGoHome} className="mt-12 text-slate-500 font-medium hover:text-slate-800">
        Back Home
      </button>
    </main>
  );
};

export default Game;