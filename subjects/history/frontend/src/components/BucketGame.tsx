import React, { useState, useEffect } from 'react';
import { ChevronLeft, CheckCircle2, Trophy, AlertCircle } from 'lucide-react';
import axios from 'axios';
import { HISTORY_API_URL } from '../config';
import './BucketGame.css';

interface BucketGameProps {
  subtopic: string;
  onBack: () => void;
}

const BucketGame: React.FC<BucketGameProps> = ({ subtopic, onBack }) => {
  const [gameData, setGameData] = useState<any>(null);
  const [selectedCardIdx, setSelectedCardIdx] = useState<number | null>(null);
  const [matchedCardIndices, setMatchedCardIndices] = useState<Set<number>>(new Set());
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Game Stats
  const [stats, setStats] = useState({
    correct: 0,
    wrong: 0,
    streak: 0,
    bestStreak: 0
  });
  const [shakeCard, setShakeCard] = useState<number | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setError(null);
        const response = await axios.get(`${HISTORY_API_URL}/game/bucket?subtopic=${subtopic}`);
        setGameData(response.data);
      } catch (err) {
        console.error("Failed to load game data", err);
        setError("Arcade data could not be loaded. Make sure the History API is running on port 5000.");
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [subtopic]);

  const handleBucketClick = (bucketId: string) => {
    if (selectedCardIdx === null) return;

    const selectedCard = gameData.cards[selectedCardIdx];
    
    if (selectedCard.target === bucketId) {
      // ✅ SUCCESS LOGIC
      setStats(prev => ({
        ...prev,
        correct: prev.correct + 1,
        streak: prev.streak + 1,
        bestStreak: Math.max(prev.bestStreak, prev.streak + 1)
      }));
      setMatchedCardIndices(prev => new Set(prev).add(selectedCardIdx));
      setSelectedCardIdx(null);
    } else {
      // ❌ MISTAKE LOGIC
      setStats(prev => ({
        ...prev,
        wrong: prev.wrong + 1,
        streak: 0
      }));
      setShakeCard(selectedCardIdx);
      setTimeout(() => setShakeCard(null), 500);
      setSelectedCardIdx(null);
    }
  };

  if (loading) return (
    <div className="flex flex-col items-center justify-center p-24">
      <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mb-4"></div>
      <p className="text-slate-500 font-medium">Loading Chapter {subtopic} facts...</p>
    </div>
  );

  if (error || !gameData) return (
    <div className="flex flex-col items-center justify-center p-24 text-center">
      <AlertCircle className="text-rose-500 mb-4" size={48} />
      <h2 className="text-xl font-bold text-slate-900 mb-2">Arcade unavailable</h2>
      <p className="text-slate-500 mb-6">{error || "No Arcade data was returned."}</p>
      <button onClick={onBack} className="px-6 py-3 bg-slate-900 text-white rounded-xl font-bold">
        Back to Arcade
      </button>
    </div>
  );

  const isGameComplete = matchedCardIndices.size === gameData.cards.length;
  const totalAttempts = stats.correct + stats.wrong;
  const accuracy = totalAttempts > 0 ? Math.round((stats.correct / totalAttempts) * 100) : 100;

  return (
    <div className="bucket-game-layout max-w-6xl mx-auto p-6">
      <button onClick={onBack} className="flex items-center gap-2 text-slate-400 mb-8 hover:text-indigo-600 transition-colors">
        <ChevronLeft size={20} /> Back to Arcade
      </button>

      <div className="game-info mb-10 text-center">
        <h1 className="text-2xl font-bold text-slate-900 mb-1">Bab {gameData.chapter}</h1>
        <p className="text-slate-500">{gameData.title}</p>
      </div>

      {/* Live Stats Dashboard */}
      <div className="stats-bar flex justify-center gap-12 mb-12 bg-white p-6 rounded-2xl border border-slate-100 shadow-sm">
        <div className="stat-item text-center">
          <div className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1">Accuracy</div>
          <div className={`text-2xl font-black ${accuracy > 70 ? 'text-slate-900' : 'text-rose-500'}`}>
            {accuracy}%
          </div>
        </div>
        
        <div className="stat-item text-center px-12 border-x border-slate-100">
          <div className="text-[10px] font-black text-indigo-400 uppercase tracking-widest mb-1">Current Combo</div>
          <div className="text-2xl font-black text-indigo-600 flex items-center justify-center gap-2">
            <Trophy size={20} className={stats.streak > 0 ? 'animate-bounce' : 'opacity-20'} />
            {stats.streak}x
          </div>
        </div>

        <div className="stat-item text-center">
          <div className="text-[10px] font-black text-rose-400 uppercase tracking-widest mb-1">Mistakes</div>
          <div className="text-2xl font-black text-rose-500 flex items-center justify-center gap-2">
            <AlertCircle size={20} className={stats.wrong > 0 ? 'opacity-100' : 'opacity-20'} />
            {stats.wrong}
          </div>
        </div>
      </div>

      {isGameComplete ? (
        <div className="completion-card text-center py-20 bg-slate-900 rounded-[3rem] text-white shadow-2xl animate-in zoom-in duration-300">
          <CheckCircle2 size={80} className="text-emerald-400 mx-auto mb-6" />
          <h2 className="text-4xl font-black mb-2">Chapter Mastered!</h2>
          <p className="text-slate-400 text-lg mb-8 max-w-md mx-auto">
            Excellent! You maintained a {accuracy}% accuracy and reached a best streak of {stats.bestStreak}.
          </p>
          <div className="flex gap-4 justify-center">
            <button onClick={onBack} className="px-8 py-4 bg-white text-slate-900 rounded-2xl font-black hover:bg-slate-100 transition-all">
              Choose Another Level
            </button>
          </div>
        </div>
      ) : (
        <>
          {/* Card Deck Section */}
          <div className="cards-section mb-20">
            <h3 className="text-xs font-bold text-slate-400 uppercase tracking-widest text-center mb-6">Select a Fact Card</h3>
            <div className="flex flex-wrap gap-4 justify-center">
              {gameData.cards.map((card: any, idx: number) => (
                !matchedCardIndices.has(idx) && (
                  <button
                    key={idx}
                    onClick={() => setSelectedCardIdx(idx)}
                    className={`card-item p-5 rounded-2xl border-2 text-sm font-bold transition-all max-w-[220px] shadow-sm
                      ${selectedCardIdx === idx 
                        ? 'border-indigo-500 bg-indigo-50 text-indigo-700 -translate-y-2 shadow-indigo-100 shadow-xl' 
                        : 'border-white bg-white hover:border-slate-200 text-slate-700'}
                      ${shakeCard === idx ? 'card-shake' : ''}`}
                  >
                    {card.text}
                  </button>
                )
              ))}
            </div>
          </div>

          {/* Buckets Section */}
          <div className="buckets-grid grid grid-cols-2 md:grid-cols-4 gap-6">
            {gameData.buckets.map((bucket: any) => (
              <div
                key={bucket.id}
                onClick={() => handleBucketClick(bucket.id)}
                className={`bucket-container cursor-pointer group transition-all active:scale-95 
                  ${selectedCardIdx !== null ? 'ring-2 ring-indigo-500 ring-offset-4 ring-opacity-20 rounded-3xl' : ''}`}
              >
                <div className="bucket-top h-36 bg-slate-50 rounded-t-[2.5rem] border-2 border-b-0 border-slate-100 group-hover:bg-indigo-50 group-hover:border-indigo-200 transition-all flex flex-col items-center justify-center">
                  <div className={`w-12 h-12 rounded-full flex items-center justify-center transition-all
                    ${selectedCardIdx !== null ? 'bg-indigo-600 text-white animate-bounce' : 'bg-slate-200 text-slate-400'}`}>
                    <CheckCircle2 size={24} />
                  </div>
                  <span className="text-[10px] font-black text-slate-300 mt-2 uppercase tracking-tighter">Drop Here</span>
                </div>
                <div className="bucket-bottom p-5 bg-slate-900 text-white text-center rounded-b-3xl font-black shadow-lg">
                  {bucket.label}
                </div>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
};

export default BucketGame;
