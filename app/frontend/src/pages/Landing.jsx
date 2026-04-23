import React from 'react';
import { useNavigate } from 'react-router-dom';

const Landing = () => {
  const navigate = useNavigate();

  return (
    <main className="flex-grow flex flex-col lg:flex-row min-h-screen bg-[#141414]">
      {/* Left Pane: Text & Actions */}
      <section className="w-full lg:w-1/2 border-b lg:border-b-0 lg:border-r border-surface-variant p-6 md:p-12 flex flex-col justify-center relative overflow-hidden">
        {/* Background Grid Texture */}
        <div className="absolute inset-0 opacity-5 pointer-events-none" style={{ backgroundImage: "radial-gradient(#AAFF00 1px, transparent 1px)", backgroundSize: "16px 16px" }}></div>
        
        {/* Header Info */}
        <div className="border border-[#AAFF00] inline-block px-3 py-1 mb-8 self-start bg-[#141414] z-10">
          <span className="font-label-caps text-label-caps text-[#AAFF00]">● RASPBERRY PI 4 · LD2410 DUAL RADAR · CNN+LSTM</span>
        </div>
        
        {/* Typography */}
        <div className="mb-8 relative z-10">
          <h1 className="font-display-xl text-4xl sm:text-5xl lg:text-7xl text-on-surface mb-2 tracking-tighter uppercase leading-none break-words">VITAL RADAR</h1>
          <h2 className="font-h1 text-2xl sm:text-3xl md:text-4xl neon-lime mb-6 tracking-tight">SURVIVOR DETECTION SYSTEM</h2>
          <p className="font-data-md text-sm sm:text-base text-on-surface-variant max-w-xl border-l-2 border-neon-coral pl-4 leading-relaxed">
            Non-invasive survivor detection system designed exclusively for emergency disaster response and search & rescue operations. Utilizing dual LD2410 mmWave radar sensors for micro-movement and respiratory derivation under rubble.
          </p>
        </div>
        
        {/* Actions */}
        <div className="flex flex-col sm:flex-row gap-4 mt-4 relative z-10">
          <button onClick={() => navigate('/')} className="border border-neon-cyan bg-transparent text-neon-cyan hover:bg-neon-cyan hover:text-[#141414] font-label-caps text-label-caps px-6 py-4 flex items-center justify-center gap-2 uppercase transition-colors w-full sm:w-auto">
            OPEN DASHBOARD <span className="font-body-reg">→</span>
          </button>
        </div>
        
        {/* Terminal Output Decorative */}
        <div className="mt-12 pt-8 border-t border-surface-variant text-outline font-code-sm text-code-sm uppercase z-10">
          <div>&gt; INIT_SEQUENCE_START</div>
          <div>&gt; RADAR_01: ONLINE | STATUS: ACQUIRING...</div>
          <div>&gt; RADAR_02: ONLINE | STATUS: STANDBY</div>
          <div className="neon-lime">&gt; SYSTEM_READY_</div>
        </div>
      </section>

      {/* Right Pane: Simplified Technical Block */}
      <section className="w-full lg:w-1/2 p-6 md:p-12 flex flex-col items-center justify-center relative bg-[#141414]">
        <div className="w-full max-w-lg border border-surface-variant bg-surface-container-lowest p-6 sm:p-8 flex flex-col gap-6 shadow-2xl">
          <div className="border-b border-surface-variant pb-4 mb-2">
            <h3 className="font-label-caps text-label-caps text-[#AAFF00] flex items-center gap-2">
              <span className="material-symbols-outlined text-[20px]">policy</span>
              OPERATIONAL PROTOCOL
            </h3>
          </div>
          
          <div className="flex flex-col gap-6 font-body-reg text-sm sm:text-base text-on-surface-variant">
            <div className="flex gap-4 items-start">
              <span className="text-[#AAFF00] font-bold mt-1">01.</span>
              <p className="leading-relaxed">Deploy Pi 4 unit at structure perimeter. Ensure dual sensors (S1/S2) face the primary debris zone to maximize signal penetration.</p>
            </div>
            <div className="flex gap-4 items-start">
              <span className="text-neon-cyan font-bold mt-1">02.</span>
              <p className="leading-relaxed">Monitor the live telemetry dashboard. The system evaluates 0.15Hz - 0.67Hz (human breathing frequency) filtering out background structural shifting.</p>
            </div>
            <div className="flex gap-4 items-start">
              <span className="text-neon-coral font-bold mt-1">03.</span>
              <p className="leading-relaxed">Wait for stable confidence &gt; 0.85 and 32-window voting consensus before authorizing extraction procedures.</p>
            </div>
          </div>

          <div className="mt-8 p-4 border border-outline border-dashed bg-[#141414] text-center rounded-sm">
            <span className="font-code-sm text-code-sm text-outline tracking-wider">DESIGNED FOR DISASTER RESPONSE OPERATIONS</span>
          </div>
        </div>
      </section>
    </main>
  );
};

export default Landing;
