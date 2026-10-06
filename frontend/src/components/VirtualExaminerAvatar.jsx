import React, { useState, useEffect } from 'react';

/**
 * AutoViva Virtual Human Examiner Avatar Component
 * 
 * Features:
 * - Professional Human Faculty/Examiner visual appearance (Prof. Sterling / Virtual Examiner)
 * - Animated lip/mouth movements synchronized during speech playback (AI_SPEAKING)
 * - Periodic natural human eye blinking
 * - Distinct interactive states: AI_SPEAKING, LISTENING / STUDENT_SPEAKING, AI_PROCESSING, EVALUATED
 * - Integrated soundwave / visual feedback indicators
 */
export default function VirtualExaminerAvatar({ examinerState = 'AI_SPEAKING' }) {
  const [mouthOpenRatio, setMouthOpenRatio] = useState(0);
  const [isBlinking, setIsBlinking] = useState(false);

  // 1. Animated Lip / Mouth Movement Loop during Speech (AI_SPEAKING)
  useEffect(() => {
    let interval = null;
    if (examinerState === 'AI_SPEAKING') {
      interval = setInterval(() => {
        // Randomize mouth openness to mimic dynamic human speech phonemes
        setMouthOpenRatio(Math.random() * 0.8 + 0.2);
      }, 130);
    } else {
      setMouthOpenRatio(0);
    }
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [examinerState]);

  // 2. Natural Human Eye Blinking Loop (Blinks every 3.5s)
  useEffect(() => {
    const blinkInterval = setInterval(() => {
      setIsBlinking(true);
      setTimeout(() => setIsBlinking(false), 160);
    }, 3800);

    return () => clearInterval(blinkInterval);
  }, []);

  // Compute mouth SVG height & path based on speaking state
  const mouthHeight = examinerState === 'AI_SPEAKING' ? 4 + mouthOpenRatio * 14 : 3;
  const mouthWidth = examinerState === 'AI_SPEAKING' ? 24 + mouthOpenRatio * 6 : 22;

  return (
    <div className="w-full aspect-[16/10] rounded-2xl overflow-hidden bg-slate-900 relative flex items-center justify-center shadow-inner border border-slate-700/50">
      
      {/* Background Ambient Lighting & Academic Office Gradient */}
      <div className={`absolute inset-0 transition-all duration-700 ${
        examinerState === 'AI_SPEAKING' ? 'bg-gradient-to-b from-slate-900 via-teal-950/60 to-slate-900' :
        examinerState === 'STUDENT_SPEAKING' ? 'bg-gradient-to-b from-slate-900 via-emerald-950/60 to-slate-900' :
        examinerState === 'AI_PROCESSING' ? 'bg-gradient-to-b from-slate-900 via-indigo-950/60 to-slate-900' :
        'bg-gradient-to-b from-slate-900 via-slate-800 to-slate-900'
      }`}></div>

      {/* Background Academic Bookshelf Grid Silhouette */}
      <div className="absolute inset-0 opacity-10 bg-[radial-gradient(#38bdf8_1px,transparent_1px)] [background-size:16px_16px] pointer-events-none"></div>

      {/* Status Overlay Badge */}
      <div className="absolute top-3 left-3 z-20 flex items-center gap-2">
        <span className={`px-2.5 py-1 rounded-xl text-[10px] font-bold font-mono uppercase tracking-wider flex items-center gap-1.5 shadow-md border ${
          examinerState === 'AI_SPEAKING' ? 'bg-teal-500/20 text-teal-300 border-teal-500/40 animate-pulse' :
          examinerState === 'STUDENT_SPEAKING' ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40' :
          examinerState === 'AI_PROCESSING' ? 'bg-indigo-500/20 text-indigo-300 border-indigo-500/40 animate-pulse' :
          'bg-slate-700/50 text-slate-300 border-slate-600'
        }`}>
          <span className={`w-2 h-2 rounded-full ${
            examinerState === 'AI_SPEAKING' ? 'bg-teal-400 animate-ping' :
            examinerState === 'STUDENT_SPEAKING' ? 'bg-emerald-400' :
            examinerState === 'AI_PROCESSING' ? 'bg-indigo-400 animate-spin' :
            'bg-slate-400'
          }`}></span>
          {examinerState === 'AI_SPEAKING' ? 'Examiner Speaking...' :
           examinerState === 'STUDENT_SPEAKING' ? 'Listening to Response' :
           examinerState === 'AI_PROCESSING' ? 'Evaluating Answer...' :
           'Examiner Ready'}
        </span>
      </div>

      {/* Audio Waveform Equalizer overlay during Speech */}
      {examinerState === 'AI_SPEAKING' && (
        <div className="absolute top-3 right-3 z-20 flex items-center gap-1 px-2 py-1 bg-teal-950/80 rounded-lg border border-teal-500/30">
          {[40, 80, 50, 90, 60].map((h, i) => (
            <div
              key={i}
              className="w-1 bg-teal-400 rounded-full animate-pulse"
              style={{
                height: `${Math.max(4, (h * mouthOpenRatio))}px`,
                animationDelay: `${i * 80}ms`
              }}
            ></div>
          ))}
        </div>
      )}

      {/* HUMAN VIRTUAL EXAMINER VECTOR AVATAR */}
      <svg
        viewBox="0 0 400 300"
        className="w-full h-full max-h-[290px] z-10 drop-shadow-2xl transition-transform duration-500"
      >
        <defs>
          {/* Skin Gradients */}
          <radialGradient id="skinGrad" cx="50%" cy="40%" r="60%">
            <stop offset="0%" stopColor="#FDDFD0" />
            <stop offset="70%" stopColor="#F6C4B0" />
            <stop offset="100%" stopColor="#E2A791" />
          </radialGradient>

          {/* Suit Jacket Gradient */}
          <linearGradient id="suitGrad" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#1E293B" />
            <stop offset="100%" stopColor="#0F172A" />
          </linearGradient>

          {/* Hair Gradient */}
          <linearGradient id="hairGrad" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stopColor="#475569" />
            <stop offset="100%" stopColor="#1E293B" />
          </linearGradient>

          {/* Glasses Frame Gradient */}
          <linearGradient id="glassesGrad" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#334155" />
            <stop offset="100%" stopColor="#0F172A" />
          </linearGradient>
        </defs>

        {/* 1. Academic Suit Jacket & Shoulders */}
        <path
          d="M 60 300 L 130 200 C 160 190, 240 190, 270 200 L 340 300 Z"
          fill="url(#suitGrad)"
        />
        {/* Shirt Collar */}
        <polygon points="175,200 200,240 225,200" fill="#FFFFFF" />
        <polygon points="160,200 175,200 200,240" fill="#E2E8F0" />
        <polygon points="225,200 240,200 200,240" fill="#E2E8F0" />
        {/* Academic Red Tie */}
        <polygon points="195,215 205,215 210,290 190,290" fill="#991B1B" />

        {/* 2. Neck */}
        <rect x="178" y="160" width="44" height="48" rx="8" fill="#F6C4B0" />
        <path d="M 178 185 C 200 195, 200 195, 222 185 Z" fill="#E2A791" opacity="0.5" />

        {/* 3. Ears */}
        <ellipse cx="140" cy="125" rx="10" ry="16" fill="#F6C4B0" />
        <ellipse cx="260" cy="125" rx="10" ry="16" fill="#F6C4B0" />

        {/* 4. Head / Face Contour */}
        <path
          d="M 144 110 C 144 55, 256 55, 256 110 C 256 155, 230 178, 200 178 C 170 178, 144 155, 144 110 Z"
          fill="url(#skinGrad)"
        />

        {/* 5. Professional Hair Style (Distinguished Academic Silver-Gray) */}
        <path
          d="M 140 100 C 138 50, 170 32, 200 32 C 230 32, 262 50, 260 100 C 250 82, 235 70, 200 70 C 165 70, 150 82, 140 100 Z"
          fill="url(#hairGrad)"
        />

        {/* 6. Eyebrows (Slightly animated based on state) */}
        <path
          d={examinerState === 'AI_PROCESSING' ? "M 158 92 Q 172 84 186 90" : "M 158 94 Q 172 88 186 94"}
          stroke="#334155" strokeWidth="3.5" strokeLinecap="round" fill="none"
        />
        <path
          d={examinerState === 'AI_PROCESSING' ? "M 214 90 Q 228 84 242 92" : "M 214 94 Q 228 88 242 94"}
          stroke="#334155" strokeWidth="3.5" strokeLinecap="round" fill="none"
        />

        {/* 7. Eyes & Blink State */}
        {isBlinking ? (
          <>
            <line x1="162" y1="106" x2="182" y2="106" stroke="#334155" strokeWidth="3.5" strokeLinecap="round" />
            <line x1="218" y1="106" x2="238" y2="106" stroke="#334155" strokeWidth="3.5" strokeLinecap="round" />
          </>
        ) : (
          <>
            {/* Left Eye */}
            <ellipse cx="172" cy="106" rx="9" ry="6" fill="#FFFFFF" />
            <circle cx="172" cy="106" r="4.5" fill="#0F172A" />
            <circle cx="174" cy="104" r="1.5" fill="#FFFFFF" />

            {/* Right Eye */}
            <ellipse cx="228" cy="106" rx="9" ry="6" fill="#FFFFFF" />
            <circle cx="228" cy="106" r="4.5" fill="#0F172A" />
            <circle cx="230" cy="104" r="1.5" fill="#FFFFFF" />
          </>
        )}

        {/* 8. Professional Glasses Frame */}
        <rect x="154" y="94" width="36" height="24" rx="6" fill="none" stroke="url(#glassesGrad)" strokeWidth="3.5" />
        <rect x="210" y="94" width="36" height="24" rx="6" fill="none" stroke="url(#glassesGrad)" strokeWidth="3.5" />
        <line x1="190" y1="104" x2="210" y2="104" stroke="#334155" strokeWidth="3" />

        {/* 9. Nose */}
        <path d="M 200 106 L 195 132 L 205 132" fill="none" stroke="#E2A791" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" />

        {/* 10. ANIMATED LIPS & MOUTH (Synchronized Speech Animation) */}
        {examinerState === 'AI_SPEAKING' ? (
          <g>
            {/* Dynamic Open Mouth Oval during Speech */}
            <ellipse
              cx="200"
              cy="154"
              rx={mouthWidth / 2}
              ry={mouthHeight / 2}
              fill="#7F1D1D"
              stroke="#991B1B"
              strokeWidth="2"
            />
            {/* Teeth Line */}
            {mouthHeight > 6 && (
              <path
                d={`M ${200 - mouthWidth / 3} ${154 - mouthHeight / 4} L ${200 + mouthWidth / 3} ${154 - mouthHeight / 4}`}
                stroke="#FFFFFF"
                strokeWidth="2.5"
              />
            )}
          </g>
        ) : examinerState === 'EVALUATED' ? (
          /* Approving Smile */
          <path d="M 186 150 Q 200 164 214 150" fill="none" stroke="#991B1B" strokeWidth="3.5" strokeLinecap="round" />
        ) : (
          /* Resting Neutral Mouth */
          <path d="M 188 152 Q 200 156 212 152" fill="none" stroke="#991B1B" strokeWidth="3.5" strokeLinecap="round" />
        )}

      </svg>

      {/* Examiner Active Pulse Border Glow */}
      {examinerState === 'AI_SPEAKING' && (
        <div className="absolute inset-0 border-4 border-teal-500/50 rounded-2xl pointer-events-none animate-pulse"></div>
      )}
    </div>
  );
}
