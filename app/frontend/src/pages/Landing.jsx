import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';

const Landing = () => {
  const navigate = useNavigate();
  const [scanState, setScanState] = useState('idle'); // idle | countdown | scanning | result
  const [countdown, setCountdown] = useState(10);
  const [result, setResult] = useState(null);
  const timerRef = useRef(null);
  const modelProcessRef = useRef(null);

  const startScan = async () => {
    setScanState('countdown');
    setCountdown(10);
    setResult(null);

    // Start the deep learning background scan via Flask API
    try {
      await fetch('/api/scan/start', { 
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ duration: 10.0 })
      });
    } catch (e) {
      console.error('Failed to start scan:', e);
    }

    // Countdown from 10 to 0
    let count = 10;
    timerRef.current = setInterval(() => {
      count -= 1;
      setCountdown(count);
      if (count <= 0) {
        clearInterval(timerRef.current);
        setScanState('scanning');
        
        // After 1.5 seconds of "scanning" animation, fetch true aggregated result
        setTimeout(async () => {
          try {
            const res = await fetch('/api/scan/stop', { method: 'POST' });
            const data = await res.json();
            setResult(data?.human_present === true);
          } catch {
            setResult(false);
          }
          setScanState('result');
        }, 1500);
      }
    }, 1000);
  };

  const resetScan = () => {
    clearInterval(timerRef.current);
    setScanState('idle');
    setCountdown(10);
    setResult(null);
  };

  useEffect(() => () => clearInterval(timerRef.current), []);

  return (
    <main className="flex-grow flex flex-col lg:flex-row min-h-screen bg-[#141414]">
      {/* Left Pane */}
      <section className="w-full lg:w-1/2 border-b lg:border-b-0 lg:border-r border-surface-variant p-6 md:p-12 flex flex-col justify-center relative overflow-hidden">
        <div className="absolute inset-0 opacity-5 pointer-events-none"
          style={{ backgroundImage: "radial-gradient(#AAFF00 1px, transparent 1px)", backgroundSize: "16px 16px" }} />

        <div className="border border-[#AAFF00] inline-block px-3 py-1 mb-8 self-start bg-[#141414] z-10">
          <span className="font-label-caps text-label-caps text-[#AAFF00]">
            ● RASPBERRY PI 4 · LD2410D DUAL RADAR · TCN+FFT
          </span>
        </div>

        <div className="mb-8 relative z-10">
          <h1 className="font-display-xl text-4xl sm:text-5xl lg:text-7xl text-on-surface mb-2 tracking-tighter uppercase leading-none">VITAL RADAR</h1>
          <h2 className="font-h1 text-2xl sm:text-3xl md:text-4xl neon-lime mb-6 tracking-tight">SURVIVOR DETECTION SYSTEM</h2>
          <p className="font-data-md text-sm sm:text-base text-on-surface-variant max-w-xl border-l-2 border-neon-coral pl-4 leading-relaxed">
            Non-invasive survivor detection system for emergency disaster response. Uses dual LD2410D mmWave radar sensors for micro-movement and respiratory derivation under rubble.
          </p>
        </div>

        <div className="flex flex-col sm:flex-row gap-4 mt-4 relative z-10">
          <button onClick={() => navigate('/')}
            className="border border-neon-cyan bg-transparent text-neon-cyan hover:bg-neon-cyan hover:text-[#141414] font-label-caps text-label-caps px-6 py-4 flex items-center justify-center gap-2 uppercase transition-colors w-full sm:w-auto">
            OPEN DASHBOARD <span>→</span>
          </button>
        </div>

        <div className="mt-12 pt-8 border-t border-surface-variant text-outline font-code-sm text-code-sm uppercase z-10">
          <div>&gt; INIT_SEQUENCE_START</div>
          <div>&gt; RADAR_01: ONLINE | STATUS: ACQUIRING...</div>
          <div>&gt; RADAR_02: ONLINE | STATUS: STANDBY</div>
          <div className="neon-lime">&gt; SYSTEM_READY_</div>
        </div>
      </section>

      {/* Right Pane — SCAN PANEL */}
      <section className="w-full lg:w-1/2 p-6 md:p-12 flex flex-col items-center justify-center relative bg-[#141414]">
        <div className="w-full max-w-lg border border-surface-variant bg-surface-container-lowest p-6 sm:p-8 flex flex-col gap-6 shadow-2xl">

          {/* IDLE STATE */}
          {scanState === 'idle' && (
            <>
              <div className="text-center">
                <div className="text-[#AAFF00] font-mono text-[11px] tracking-widest uppercase mb-2">SCAN_MODULE</div>
                <h3 className="text-white font-mono text-2xl font-bold tracking-tight mb-4">INITIATE SCAN</h3>
                <p className="text-zinc-500 font-mono text-[11px] leading-relaxed">
                  Press SCAN to start a 10-second scan. Stay still during the process.
                </p>
              </div>
              <button
                onClick={startScan}
                className="w-full bg-[#AAFF00] text-[#0a0a0a] font-mono font-black text-lg tracking-widest uppercase py-5 hover:bg-white transition-colors flex items-center justify-center gap-3"
              >
                <span className="material-symbols-outlined text-[20px]">radar</span>
                SCAN HERE
              </button>
            </>
          )}

          {/* COUNTDOWN STATE */}
          {scanState === 'countdown' && (
            <div className="flex flex-col items-center gap-6">
              <div className="text-[#AAFF00] font-mono text-[11px] tracking-widest uppercase">PREPARING SCAN...</div>

              {/* Circular countdown */}
              <div className="relative flex items-center justify-center" style={{ width: 160, height: 160 }}>
                <svg width="160" height="160" viewBox="0 0 160 160" className="absolute">
                  <circle cx="80" cy="80" r="70" fill="none" stroke="#1a1a1a" strokeWidth="8" />
                  <circle
                    cx="80" cy="80" r="70"
                    fill="none"
                    stroke="#AAFF00"
                    strokeWidth="8"
                    strokeLinecap="round"
                    strokeDasharray={`${2 * Math.PI * 70}`}
                    strokeDashoffset={`${2 * Math.PI * 70 * (1 - countdown / 10)}`}
                    transform="rotate(-90 80 80)"
                    style={{ transition: 'stroke-dashoffset 0.9s linear' }}
                  />
                </svg>
                <div className="text-center z-10">
                  <div className="text-[#AAFF00] font-mono text-5xl font-black">{countdown}</div>
                  <div className="text-zinc-500 font-mono text-[10px] tracking-widest">SEC</div>
                </div>
              </div>

              <div className="text-zinc-400 font-mono text-[13px] text-center animate-pulse tracking-widest">
                ⚠ STAY STILL — SCANNING IN PROGRESS
              </div>

              <button onClick={resetScan}
                className="border border-zinc-700 text-zinc-500 font-mono text-[11px] px-4 py-2 hover:border-red-500 hover:text-red-400 transition-colors uppercase tracking-widest">
                CANCEL
              </button>
            </div>
          )}

          {/* SCANNING STATE */}
          {scanState === 'scanning' && (
            <div className="flex flex-col items-center gap-6 py-4">
              <div className="text-[#00CFFF] font-mono text-[11px] tracking-widest uppercase animate-pulse">
                DEEP LEARNING MODEL RUNNING...
              </div>
              <div className="relative" style={{ width: 140, height: 140 }}>
                <svg width="140" height="140" viewBox="0 0 140 140">
                  {[60, 45, 30].map((r, i) => (
                    <circle key={i} cx="70" cy="70" r={r}
                      fill="none" stroke="#00CFFF" strokeWidth="1"
                      opacity={0.3 + i * 0.2}
                      strokeDasharray="4 6" />
                  ))}
                  <circle cx="70" cy="70" r="8" fill="#00CFFF" opacity="0.9" className="animate-pulse" />
                  <line x1="70" y1="10" x2="70" y2="130" stroke="#1a2830" strokeWidth="0.5" opacity="0.5" />
                  <line x1="10" y1="70" x2="130" y2="70" stroke="#1a2830" strokeWidth="0.5" opacity="0.5" />
                </svg>
                {/* Rotating sweep */}
                <div className="absolute inset-0 flex items-center justify-center">
                  <div style={{
                    width: 2, height: 60, background: 'linear-gradient(to top, #00CFFF, transparent)',
                    transformOrigin: 'bottom center',
                    animation: 'spin 1s linear infinite'
                  }} />
                </div>
              </div>
              <div className="text-zinc-300 font-mono text-[13px] text-center tracking-wide">
                ANALYZING RADAR SIGNAL...
              </div>
            </div>
          )}

          {/* RESULT STATE */}
          {scanState === 'result' && (
            <div className="flex flex-col items-center gap-6">
              <div className={`text-[11px] font-mono tracking-widest uppercase ${result ? 'text-[#AAFF00]' : 'text-[#FF5C5C]'}`}>
                SCAN COMPLETE
              </div>

              <div className={`w-32 h-32 rounded-full flex items-center justify-center border-4 ${result ? 'border-[#AAFF00] bg-[#AAFF00]/10' : 'border-[#FF5C5C] bg-[#FF5C5C]/10'}`}>
                <span className={`material-symbols-outlined text-[56px] ${result ? 'text-[#AAFF00]' : 'text-[#FF5C5C]'}`}>
                  {result ? 'person' : 'person_off'}
                </span>
              </div>

              <div className="text-center">
                <div className={`font-mono text-3xl font-black tracking-tight mb-1 ${result ? 'text-[#AAFF00]' : 'text-[#FF5C5C]'}`}>
                  {result ? 'HUMAN DETECTED' : 'NO HUMAN DETECTED'}
                </div>
                <div className="text-zinc-500 font-mono text-[11px] tracking-wider">
                  {result ? 'BREATHING PATTERN CONFIRMED' : 'NO BREATHING SIGNAL FOUND'}
                </div>
              </div>

              <div className="flex gap-3 w-full">
                <button onClick={resetScan}
                  className="flex-1 border border-[#AAFF00] text-[#AAFF00] font-mono font-bold text-[12px] uppercase py-3 hover:bg-[#AAFF00] hover:text-[#0a0a0a] transition-colors tracking-widest">
                  SCAN AGAIN
                </button>
                <button onClick={() => navigate('/')}
                  className="flex-1 border border-zinc-700 text-zinc-400 font-mono text-[12px] uppercase py-3 hover:border-zinc-400 transition-colors tracking-widest">
                  DASHBOARD
                </button>
              </div>
            </div>
          )}

        </div>
      </section>
    </main>
  );
};

export default Landing;
