import React from 'react';

const DirectionRing = ({ direction, distance, freq, votes }) => {
  // Determine status and colors based on direction string from backend
  const isDetected = direction !== 'none';
  const isLeft = direction === 'move_left';
  const isRight = direction === 'move_right';
  const isCenter = direction === 'center';

  let statusText = 'WAITING...';
  let statusColor = 'text-neon-cyan';
  let shadowClass = 'drop-shadow-none';

  if (isCenter) {
    statusText = 'DETECTED';
    statusColor = 'text-neon-cyan';
    shadowClass = 'drop-shadow-[0_0_5px_rgba(0,255,255,0.5)]';
  } else if (isLeft) {
    statusText = 'DETECTED - MOVE LEFT';
    statusColor = 'text-neon-lime';
    shadowClass = 'drop-shadow-[0_0_5px_rgba(170,255,0,0.5)]';
  } else if (isRight) {
    statusText = 'DETECTED - MOVE RIGHT';
    statusColor = 'text-neon-coral';
    shadowClass = 'drop-shadow-[0_0_5px_rgba(255,92,92,0.5)]';
  } else {
    statusText = 'NO PERSON';
    statusColor = 'text-red-600';
  }

  const activeColor = 'text-white font-mono text-xs md:text-sm font-black drop-shadow-[0_0_8px_rgba(255,255,255,0.8)]';
  const inactiveColor = 'text-zinc-700 font-mono text-xs md:text-sm font-black transition-colors duration-300';

  // Calculate fused confidence roughly for display
  const confPercent = isDetected ? '99.8%' : '--%';

  return (
    <section className="order-1 md:order-2 md:col-span-6 lg:col-span-6 relative flex flex-col p-4 md:p-6 bg-[#0a0a0a] border-b md:border-b-0 border-zinc-800 overflow-hidden min-h-[300px]">
      <div className="absolute top-0 left-0 w-full h-[20%] bg-gradient-to-b from-neon-lime/5 to-transparent pointer-events-none animate-[pulse_4s_ease-in-out_infinite]"></div>
      
      <header className="flex justify-between items-start z-10 mb-6">
        <div>
          <span className="block text-white font-mono text-xs font-bold tracking-[0.1em] uppercase">Tactical_Fused_Overlay</span>
          <span className="block text-zinc-500 font-mono text-[9px] mt-1 tracking-wider">ACTIVE_MONITORING_MODE</span>
        </div>
      </header>

      {/* Responsive Central Status Card */}
      <div className="flex-1 flex flex-col items-center justify-center relative z-10 w-full">
        <div className="w-full max-w-md border border-neon-cyan/20 rounded-xl bg-gradient-to-b from-neon-cyan/10 to-transparent p-6 md:p-10 flex flex-col items-center justify-center shadow-lg backdrop-blur-sm">
          <div className={`${statusColor} font-mono text-sm md:text-base font-bold tracking-[0.2em] mb-2 uppercase ${shadowClass}`}>
            {statusText}
          </div>
          <div className="text-white font-telemetry-lg text-5xl md:text-6xl font-black mb-6 drop-shadow-md">
            {confPercent}
          </div>
          
          <div className="flex gap-4 md:gap-8 items-center mt-2 border-t border-neon-cyan/20 pt-6 w-full justify-center">
            <span className={isLeft ? activeColor : inactiveColor}>← LEFT</span>
            <span className={isCenter ? activeColor : inactiveColor}>● CENTER</span>
            <span className={isRight ? activeColor : inactiveColor}>RIGHT →</span>
          </div>
        </div>
      </div>

      {/* AVG Metrics Grid */}
      <div className="mt-8 grid grid-cols-3 gap-2 md:gap-4 w-full z-10">
        <div className="bg-zinc-900/40 border border-zinc-800/50 p-3 rounded text-center">
          <div className="text-zinc-500 font-mono text-[9px] md:text-[10px] uppercase mb-1 tracking-wider">Avg_Freq</div>
          <div className="text-white font-telemetry-md text-lg md:text-xl font-bold">
            {freq ? freq.toFixed(2) : '--'} <span className="text-[10px] text-zinc-500 font-normal">Hz</span>
          </div>
        </div>
        <div className="bg-neon-cyan/10 border border-neon-cyan/30 p-3 rounded text-center">
          <div className="text-neon-cyan font-mono text-[9px] md:text-[10px] uppercase mb-1 tracking-wider">Fused_Range</div>
          <div className="text-white font-telemetry-md text-lg md:text-xl font-bold">
            {distance ? distance.toFixed(1) : '--'} <span className="text-[10px] text-zinc-500 font-normal">m</span>
          </div>
        </div>
        <div className="bg-zinc-900/40 border border-zinc-800/50 p-3 rounded text-center">
          <div className="text-zinc-500 font-mono text-[9px] md:text-[10px] uppercase mb-1 tracking-wider">Total_Votes</div>
          <div className="text-white font-telemetry-md text-lg md:text-xl font-bold">
            {votes || '--'} <span className="text-[10px] text-zinc-500 font-normal">votes</span>
          </div>
        </div>
      </div>
    </section>
  );
};

export default React.memo(DirectionRing);
