import React from 'react';

const SensorPanel = ({ side, name, colorPrefix, data }) => {
  const isLeft = side === 'left';
  
  // Mappings for colors based on the colorPrefix prop
  const bgActive = colorPrefix === 'neon-lime' ? 'bg-neon-lime' : 'bg-neon-coral';
  const textActive = colorPrefix === 'neon-lime' ? 'text-neon-lime' : 'text-neon-coral';
  const textShadow = colorPrefix === 'neon-lime' ? 'shadow-[0_0_8px_rgba(170,255,0,0.5)]' : 'shadow-[0_0_8px_rgba(255,92,92,0.4)]';
  const orderClass = isLeft ? 'order-2 md:order-1' : 'order-3 md:order-3';
  const borderClass = isLeft ? 'border-b md:border-b-0 md:border-r border-zinc-800' : 'md:border-l border-zinc-800';
  
  const distance = data.distance || 0;
  const confidence = data.confidence || 0;
  const votes = data.votes || 0;
  const detected = data.detected || false;
  const votingWindow = data.voting_window || 32;

  // Segmented voting grid logic
  const cells = 10;
  const activeCells = Math.round((votes / votingWindow) * cells);
  
  return (
    <section className={`${orderClass} md:col-span-3 lg:col-span-3 ${borderClass} p-4 md:p-6 flex flex-col justify-between bg-zinc-950/40`}>
      <header className={`flex justify-between items-start border-b border-zinc-800 pb-3 mb-6 ${!isLeft ? 'flex-row-reverse' : ''}`}>
        <div className={!isLeft ? 'text-right' : ''}>
          <span className={`block ${textActive} font-mono text-[11px] font-bold tracking-widest uppercase`}>
            {name}_SECONDARY_{side.toUpperCase()}
          </span>
          <span className="block text-zinc-600 font-mono text-[9px] mt-1">ID: VRT-0091-{isLeft ? 'L' : 'R'}</span>
        </div>
        {isLeft && (
          <div className={`px-2 py-0.5 ${bgActive}/10 border border-${colorPrefix}/30 ${textActive} text-[9px] font-mono rounded-sm`}>
            LINK_UP
          </div>
        )}
      </header>
      
      <div className={`flex-1 space-y-6 flex flex-col ${!isLeft ? 'items-end' : ''}`}>
        <div className={`telemetry-module ${!isLeft ? 'text-right' : ''}`}>
          <label className="text-zinc-500 font-mono text-[10px] uppercase tracking-widest block mb-2">Target_Distance</label>
          <div className={`flex items-baseline gap-1 ${!isLeft ? 'justify-end' : ''}`}>
            <span className={`font-telemetry-lg text-4xl md:text-[40px] leading-none ${textActive} font-bold tracking-tighter`}>
              {distance.toFixed(1)}
            </span>
            <span className={`${textActive} opacity-60 font-mono text-sm font-bold`}>m</span>
          </div>
        </div>
        
        <div className="space-y-5 w-full">
          <div>
            <label className={`text-zinc-500 font-mono text-[10px] uppercase tracking-widest block mb-2 ${!isLeft ? 'text-right' : ''}`}>
              Signal_Confidence
            </label>
            <div className={`h-2 w-full bg-zinc-900 border border-zinc-800 overflow-hidden flex rounded-full ${!isLeft ? 'flex-row-reverse' : ''}`}>
              <div 
                className={`h-full ${bgActive} ${textShadow} transition-all duration-300`} 
                style={{ width: `${Math.min(100, Math.max(0, confidence * 100))}%` }}
              ></div>
            </div>
            <div className={`flex ${!isLeft ? 'justify-end' : 'justify-between'} mt-2`}>
              <span className={`text-[9px] font-mono ${textActive} font-bold tracking-wider`}>
                {(confidence * 100).toFixed(1)}% {detected ? 'LOCKED' : 'SEARCHING'}
              </span>
            </div>
          </div>
          
          <div>
            <label className={`text-zinc-500 font-mono text-[10px] uppercase tracking-widest block mb-2 ${!isLeft ? 'text-right' : ''}`}>
              Segmented_Voting
            </label>
            <div 
              className={`grid grid-cols-10 gap-0.5 md:gap-1 h-3 min-w-[150px] ${!isLeft ? 'flex-row-reverse' : ''}`}
              style={!isLeft ? { direction: 'rtl' } : {}}
            >
              {Array.from({ length: cells }).map((_, i) => (
                <div 
                  key={i} 
                  className={`rounded-sm ${i < activeCells ? `${bgActive} ${textShadow}` : 'bg-zinc-800/80 border border-zinc-700/30'}`}
                ></div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default React.memo(SensorPanel, (prev, next) => {
  return prev.data.distance === next.data.distance &&
         prev.data.confidence === next.data.confidence &&
         prev.data.freq === next.data.freq &&
         prev.data.power === next.data.power &&
         prev.data.votes === next.data.votes &&
         prev.data.detected === next.data.detected;
});
