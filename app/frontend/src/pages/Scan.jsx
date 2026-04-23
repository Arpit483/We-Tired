import React, { useContext, useEffect, useRef, useState } from 'react';
import { ScanContext, SensorDataContext, SensorDispatchContext } from '../context/SensorContext';

const Scan = () => {
  const scan = useContext(ScanContext);
  const sensorData = useContext(SensorDataContext);
  const dispatch = useContext(SensorDispatchContext);

  const [timeLeft, setTimeLeft] = useState(scan.duration);
  const timerRef = useRef(null);
  const resetTimerRef = useRef(null);

  // -------------------------------------------------------------
  // HANDLERS
  // -------------------------------------------------------------
  const initiateScan = async () => {
    try {
      await fetch('/api/scan/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ duration: 10.0 })
      });
      // The scan_started socket event will flip phase to 'scanning'
    } catch (err) {
      console.error('Failed to start scan:', err);
    }
  };

  const stopScan = async () => {
    try {
      await fetch('/api/scan/stop', { method: 'POST' });
      // The scan_complete socket event will flip phase to 'complete'
    } catch (err) {
      console.error('Failed to stop scan:', err);
    }
  };

  const resetScan = () => {
    dispatch({ type: 'SCAN_RESET' });
  };

  // -------------------------------------------------------------
  // COUNTDOWN LOGIC
  // -------------------------------------------------------------
  useEffect(() => {
    if (scan.phase === 'scanning' && scan.startedAt) {
      const durationMs = scan.duration * 1000;
      
      const updateTimer = () => {
        const elapsed = Date.now() - scan.startedAt;
        const remaining = Math.max(0, durationMs - elapsed);
        
        setTimeLeft(remaining / 1000);
        
        if (remaining > 0) {
          timerRef.current = requestAnimationFrame(updateTimer);
        } else {
          // Time's up!
          stopScan();
        }
      };
      
      timerRef.current = requestAnimationFrame(updateTimer);
      
      return () => {
        if (timerRef.current) cancelAnimationFrame(timerRef.current);
      };
    }
  }, [scan.phase, scan.startedAt, scan.duration]);

  // -------------------------------------------------------------
  // AUTO RESET LOGIC (30s after complete)
  // -------------------------------------------------------------
  useEffect(() => {
    if (scan.phase === 'complete') {
      resetTimerRef.current = setTimeout(() => {
        resetScan();
      }, 30000); // 30 seconds
      
      return () => {
        if (resetTimerRef.current) clearTimeout(resetTimerRef.current);
      };
    }
  }, [scan.phase]);

  // -------------------------------------------------------------
  // RENDERERS
  // -------------------------------------------------------------
  const renderIdle = () => (
    <div className="flex flex-col items-center justify-center h-full relative z-10">
      <h2 className="font-display-xl text-5xl sm:text-7xl text-[#AAFF00] tracking-tighter mb-4">SCAN_READY</h2>
      <p className="font-code-sm text-outline tracking-wider mb-12 text-center max-w-lg">
        POINT SENSORS AT TARGET AREA · REMAIN STILL DURING SCAN
      </p>
      
      <button 
        onClick={initiateScan}
        className="border-2 border-[#AAFF00] bg-transparent text-[#AAFF00] hover:bg-[#AAFF00] hover:text-[#0a0a0a] font-label-caps px-8 py-5 text-xl tracking-widest uppercase transition-all shadow-[0_0_15px_rgba(170,255,0,0.2)] hover:shadow-[0_0_25px_rgba(170,255,0,0.5)]"
      >
        [ INITIATE SCAN ]
      </button>
    </div>
  );

  const renderScanning = () => {
    const leftConf = sensorData?.latestData?.left_confidence || 0;
    const rightConf = sensorData?.latestData?.right_confidence || 0;
    
    return (
      <div className="flex flex-col items-center justify-center h-full relative z-10 w-full max-w-2xl mx-auto">
        <style>{`
          @keyframes pulseRing {
            0% { transform: scale(0.8); opacity: 0.8; }
            100% { transform: scale(1.5); opacity: 0; }
          }
          .ring-1 { animation: pulseRing 2s infinite cubic-bezier(0.215, 0.61, 0.355, 1); }
          .ring-2 { animation: pulseRing 2s infinite cubic-bezier(0.215, 0.61, 0.355, 1) 0.6s; }
          .ring-3 { animation: pulseRing 2s infinite cubic-bezier(0.215, 0.61, 0.355, 1) 1.2s; }
          @keyframes blinkFast {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.3; }
          }
          .blink-text { animation: blinkFast 1s infinite; }
        `}</style>

        {/* Pulsing Timer SVG */}
        <div className="relative w-64 h-64 flex items-center justify-center mb-8">
          <svg className="absolute inset-0 w-full h-full pointer-events-none" viewBox="0 0 100 100">
            <circle cx="50" cy="50" r="40" fill="none" stroke="#00FFFF" strokeWidth="1" opacity="0.3" className="ring-1" />
            <circle cx="50" cy="50" r="40" fill="none" stroke="#00FFFF" strokeWidth="1" opacity="0.3" className="ring-2" />
            <circle cx="50" cy="50" r="40" fill="none" stroke="#00FFFF" strokeWidth="1" opacity="0.3" className="ring-3" />
            <circle cx="50" cy="50" r="40" fill="none" stroke="#00FFFF" strokeWidth="2" opacity="0.8" />
          </svg>
          <div className="font-display-xl text-[#00FFFF] text-5xl tracking-tighter">
            {timeLeft.toFixed(1)}s
          </div>
        </div>

        <div className="font-code-sm text-[#00FFFF] tracking-widest text-xl mb-12 blink-text uppercase">
          SCANNING · STAY STILL
        </div>

        {/* Live Confidence Bars */}
        <div className="w-full flex flex-col gap-4 mb-12 px-8">
          <div className="flex flex-col gap-1">
            <div className="flex justify-between font-label-caps text-xs text-outline">
              <span>S1 CONFIDENCE</span>
              <span>{(leftConf * 100).toFixed(0)}%</span>
            </div>
            <div className="h-1 bg-[#1a1a1a] w-full relative">
              <div className="absolute top-0 left-0 h-full bg-[#00FFFF] transition-all duration-100" style={{ width: `${Math.min(100, leftConf * 100)}%` }}></div>
            </div>
          </div>
          <div className="flex flex-col gap-1">
            <div className="flex justify-between font-label-caps text-xs text-outline">
              <span>S2 CONFIDENCE</span>
              <span>{(rightConf * 100).toFixed(0)}%</span>
            </div>
            <div className="h-1 bg-[#1a1a1a] w-full relative">
              <div className="absolute top-0 left-0 h-full bg-[#00FFFF] transition-all duration-100" style={{ width: `${Math.min(100, rightConf * 100)}%` }}></div>
            </div>
          </div>
        </div>

        <button 
          onClick={stopScan}
          className="border border-[#FF5C5C] text-[#FF5C5C] hover:bg-[#FF5C5C] hover:text-[#0a0a0a] font-label-caps px-6 py-2 text-sm tracking-widest uppercase transition-colors"
        >
          [ ABORT ]
        </button>
      </div>
    );
  };

  const renderComplete = () => {
    if (!scan.result) return null;
    
    const detected = scan.result.human_present;
    const titleColor = detected ? 'text-[#AAFF00]' : 'text-[#FF5C5C]';
    const shadowClass = detected ? 'shadow-[0_0_40px_rgba(170,255,0,0.6)]' : '';
    const borderColor = detected ? 'border-[#AAFF00]' : 'border-[#FF5C5C]';

    return (
      <div className="flex flex-col items-center justify-center h-full relative z-10 w-full max-w-4xl mx-auto">
        
        {/* Giant Result */}
        <div className={`px-10 py-6 border-2 ${borderColor} ${shadowClass} mb-12 bg-[#0a0a0a] z-20`}>
          <h2 className={`font-display-xl text-4xl sm:text-6xl ${titleColor} tracking-tighter uppercase leading-none`}>
            {detected ? 'HUMAN DETECTED' : 'NO SIGNAL'}
          </h2>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4 w-full mb-12">
          <div className="border border-[#1a1a1a] bg-[#0d0d0d] p-4 flex flex-col items-center justify-center text-center">
            <span className="font-label-caps text-[10px] text-outline mb-2">AVG CONFIDENCE</span>
            <span className="font-code-sm text-xl text-on-surface">{(scan.result.confidence * 100).toFixed(1)}%</span>
          </div>
          <div className="border border-[#1a1a1a] bg-[#0d0d0d] p-4 flex flex-col items-center justify-center text-center">
            <span className="font-label-caps text-[10px] text-outline mb-2">S1 VOTES</span>
            <span className="font-code-sm text-xl text-[#00FFFF]">{scan.result.sensor1_votes}</span>
          </div>
          <div className="border border-[#1a1a1a] bg-[#0d0d0d] p-4 flex flex-col items-center justify-center text-center">
            <span className="font-label-caps text-[10px] text-outline mb-2">S2 VOTES</span>
            <span className="font-code-sm text-xl text-[#FF5C5C]">{scan.result.sensor2_votes}</span>
          </div>
          <div className="border border-[#1a1a1a] bg-[#0d0d0d] p-4 flex flex-col items-center justify-center text-center">
            <span className="font-label-caps text-[10px] text-outline mb-2">TOTAL FRAMES</span>
            <span className="font-code-sm text-xl text-on-surface">{scan.result.total_frames}</span>
          </div>
          <div className="border border-[#1a1a1a] bg-[#0d0d0d] p-4 flex flex-col items-center justify-center text-center">
            <span className="font-label-caps text-[10px] text-outline mb-2">DURATION</span>
            <span className="font-code-sm text-xl text-on-surface">{scan.result.scan_duration}s</span>
          </div>
        </div>

        <button 
          onClick={resetScan}
          className="border border-outline text-outline hover:text-on-surface hover:border-surface-variant bg-transparent font-label-caps px-8 py-3 tracking-widest uppercase transition-colors"
        >
          [ NEW SCAN ]
        </button>
      </div>
    );
  };

  return (
    <main className="flex-grow flex flex-col min-h-[calc(100vh-60px)] lg:min-h-screen bg-[#0a0a0a] p-6 relative overflow-hidden">
      {/* Decorative Radar Grid Layer */}
      <div 
        className="absolute inset-0 pointer-events-none opacity-10" 
        style={{ 
          backgroundImage: "linear-gradient(#1a1a1a 1px, transparent 1px), linear-gradient(90deg, #1a1a1a 1px, transparent 1px)", 
          backgroundSize: "40px 40px" 
        }}
      ></div>
      <div 
        className="absolute inset-0 pointer-events-none opacity-[0.03]" 
        style={{ 
          backgroundImage: "radial-gradient(circle, #AAFF00 1px, transparent 1px)", 
          backgroundSize: "20px 20px" 
        }}
      ></div>

      <div className="absolute top-6 left-6 font-label-caps text-xs text-outline z-20">
        // SCAN_OPERATIONS_MODE
      </div>

      <div className="flex-1 flex flex-col">
        {scan.phase === 'idle' && renderIdle()}
        {scan.phase === 'scanning' && renderScanning()}
        {scan.phase === 'complete' && renderComplete()}
      </div>
    </main>
  );
};

export default Scan;
