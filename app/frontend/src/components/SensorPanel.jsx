import React from 'react';

// Real-time signal power bar driven by actual sensor data.
// Normalises FFT peak_power (0–300+ range) to 0–100% for display.
const WaveformDelta = ({ color, power }) => {
  const normalised = Math.min(1.0, (power || 0) / 300);
  const pct = (normalised * 100).toFixed(1);
  return (
    <div className="mt-3">
      <div className="flex items-center justify-between mb-1">
        <div className="font-mono text-[9px] text-zinc-600 tracking-widest uppercase">SIGNAL_POWER</div>
        <div className="font-mono text-[9px] tracking-widest" style={{ color }}>{pct}%</div>
      </div>
      <div className="h-2 w-full bg-[#111] overflow-hidden rounded-sm">
        <div
          className="h-full rounded-sm transition-all duration-200"
          style={{ width: `${pct}%`, backgroundColor: color, boxShadow: `0 0 6px ${color}60` }}
        />
      </div>
    </div>
  );
};

const SensorPanel = ({ side, name, colorPrefix, data }) => {
  const isLeft = side === 'left';
  const color = colorPrefix === 'neon-lime' ? '#AAFF00' : '#FF5C5C';
  const colorClass = colorPrefix === 'neon-lime' ? 'text-[#AAFF00]' : 'text-[#FF5C5C]';
  const bgColorClass = colorPrefix === 'neon-lime' ? 'bg-[#AAFF00]' : 'bg-[#FF5C5C]';

  const distance    = data.distance    || 0;
  const confidence  = data.confidence  || 0;
  const votes       = data.votes       || 0;
  const detected    = data.detected    || false;
  const votingWindow = data.voting_window || 32;
  const freq        = data.freq        || 0;
  const power       = data.power       || 0;

  // distance already sent as metres from deep_optimized.py (divided by 100)
  const displayDist = distance.toFixed(2);

  const orderClass = isLeft ? 'order-2 md:order-1' : 'order-3 md:order-3';

  return (
    <section
      className={`${orderClass} md:col-span-3 flex flex-col bg-[#0a0a0a] border-r border-[#1a1a1a] overflow-hidden`}
      style={{ minHeight: 0 }}
    >
      {/* Panel Header */}
      <div className={`flex items-center justify-between px-4 py-2 border-b border-[#1a1a1a] ${!isLeft ? 'flex-row-reverse' : ''}`}>
        <div className={!isLeft ? 'text-right' : ''}>
          <div className={`${colorClass} font-mono text-[10px] font-bold tracking-widest uppercase`}>
            {name}_{isLeft ? 'PRIMARY' : 'SECONDARY'}_SENSOR
          </div>
          <div className="text-zinc-600 font-mono text-[9px] mt-0.5">
            ID: VRT-{isLeft ? '0091' : '0092'}-{isLeft ? 'L' : 'R'}
          </div>
        </div>
        {isLeft && (
          <div className="border border-[#AAFF00]/50 px-2 py-0.5 text-[#AAFF00] font-mono text-[9px] font-bold tracking-widest">
            LINK_UP
          </div>
        )}
      </div>

      {/* Panel Body */}
      <div className="flex-1 flex flex-col p-4 gap-4 overflow-hidden">

        {/* Segmented Voting */}
        <div>
          <div className={`flex items-baseline gap-1 mb-2 ${!isLeft ? 'justify-end' : ''}`}>
            <span className={`${colorClass} font-mono text-3xl font-black`}>{votes}</span>
            <span className="text-zinc-500 font-mono text-sm">/ {votingWindow}</span>
            <span className="text-zinc-600 font-mono text-[9px] ml-2 tracking-widest uppercase">SEGMENTED_VOTING</span>
          </div>
          <div
            className={`grid grid-cols-10 gap-1 h-4`}
            style={!isLeft ? { direction: 'rtl' } : {}}
          >
            {Array.from({ length: 10 }).map((_, i) => {
              const filled = i < Math.round((votes / votingWindow) * 10);
              return (
                <div
                  key={i}
                  className="rounded-sm"
                  style={{
                    backgroundColor: filled ? color : '#1f1f1f',
                    boxShadow: filled ? `0 0 4px ${color}80` : 'none',
                  }}
                />
              );
            })}
          </div>
        </div>

        {/* Distance readout */}
        <div className={!isLeft ? 'text-right' : ''}>
          <div className="text-zinc-600 font-mono text-[9px] uppercase tracking-widest mb-1">Target_Distance</div>
          <div className={`${colorClass} font-mono text-4xl font-black leading-none`}>
            {displayDist}<span className="text-zinc-500 text-base ml-1 font-normal">m</span>
          </div>
        </div>

        {/* Confidence bar */}
        <div>
          <div className={`text-zinc-600 font-mono text-[9px] uppercase tracking-widest mb-1 ${!isLeft ? 'text-right' : ''}`}>Signal_Confidence</div>
          <div className={`h-1.5 w-full bg-[#1a1a1a] overflow-hidden flex ${!isLeft ? 'flex-row-reverse' : ''}`}>
            <div
              className="h-full transition-all duration-300"
              style={{ width: `${Math.min(100, confidence * 100)}%`, backgroundColor: color }}
            />
          </div>
          <div className={`font-mono text-[9px] mt-1 ${colorClass} ${!isLeft ? 'text-right' : ''}`}>
            {(confidence * 100).toFixed(1)}% {detected ? 'LOCKED' : 'SEARCHING'}
          </div>
        </div>

        {/* Live signal power bar */}
        <WaveformDelta color={color} power={power} />

        {/* Breathing status */}
        <div className="mt-auto">
          <div className="text-zinc-600 font-mono text-[9px] uppercase tracking-widest mb-2">BREATHING_MONITOR</div>
          <div
            className={`p-3 font-mono text-[13px] font-black uppercase tracking-widest text-center ${
              detected
                ? `${bgColorClass} text-[#0a0a0a]`
                : 'bg-[#111] border border-[#1f1f1f] text-zinc-600'
            }`}
          >
            {detected ? (
              <><span>BREATHING</span><br /><span>DETECTED</span></>
            ) : 'STANDBY / NO SIGNAL'}
          </div>
        </div>
      </div>
    </section>
  );
};

export default React.memo(SensorPanel, (prev, next) =>
  prev.data.distance   === next.data.distance   &&
  prev.data.confidence === next.data.confidence &&
  prev.data.votes      === next.data.votes      &&
  prev.data.detected   === next.data.detected   &&
  prev.data.freq       === next.data.freq       &&
  prev.data.power      === next.data.power
);
