import React, { useMemo } from 'react';

const DirectionRing = ({ direction, distance, freq, votes }) => {
  const arrow = useMemo(() => {
    switch (direction) {
      case 'center': return '● CENTER';
      case 'move_right': return '→ RIGHT';
      case 'move_left': return '← LEFT';
      default: return '— NONE';
    }
  }, [direction]);

  const isDetected = direction !== 'none';

  return (
    <div className="border border-neon-cyan flex flex-col h-full bg-[#141414]">
      <div className="border-b border-neon-cyan p-2 flex justify-between items-center text-neon-cyan font-label-caps text-label-caps">
        <span>[ SYS ]</span>
        <span>MERGED TELEMETRY</span>
      </div>
      <div className="p-4 flex flex-col gap-6 flex-1 items-center justify-center text-center">
        
        <div className="flex flex-col items-center gap-2 my-auto">
          <div className="w-16 h-16 border-2 border-neon-cyan rounded-full flex items-center justify-center mb-4 opacity-80">
            <span className="material-symbols-outlined text-[32px] text-neon-cyan">my_location</span>
          </div>
          <span className="font-code-sm text-code-sm text-outline uppercase tracking-widest">Target Vector</span>
          <span className={`font-data-lg text-data-lg text-neon-cyan ${isDetected ? 'pulse-text' : ''}`}>{arrow}</span>
        </div>
        
        <div className="grid grid-cols-1 gap-2 w-full mt-auto">
          <div className="border border-surface-variant p-2 flex justify-between items-center">
            <span className="font-code-sm text-code-sm text-outline">AVG DIST</span>
            <span className="font-data-md text-data-md text-neon-cyan">{distance?.toFixed(1) || '0.0'} cm</span>
          </div>
          <div className="border border-surface-variant p-2 flex justify-between items-center">
            <span className="font-code-sm text-code-sm text-outline">AVG FREQ</span>
            <span className="font-data-md text-data-md text-neon-cyan">{freq?.toFixed(3) || '0.000'} Hz</span>
          </div>
          <div className="border border-surface-variant p-2 flex justify-between items-center">
            <span className="font-code-sm text-code-sm text-outline">AGREEMENT</span>
            <span className="font-data-md text-data-md text-neon-cyan">{votes || 0} / 64</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default React.memo(DirectionRing, (prev, next) => {
  return prev.direction === next.direction &&
         prev.distance === next.distance &&
         prev.freq === next.freq &&
         prev.votes === next.votes;
});
