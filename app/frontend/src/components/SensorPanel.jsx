import React from 'react';

// Mini bar chart for WAVEFORM_DELTA
const WaveformDelta = ({ color, samples }) => {
  const defaultHeights = [30, 50, 70, 45, 80, 55, 65, 40, 75, 60, 85, 50];
  let heights;
  if (samples && samples.length > 0) {
    const mapped = samples.map(v => Math.min(100, Math.max(5, v * 100)));
    if (mapped.length < 12) {
      heights = [...Array(12 - mapped.length).fill(10), ...mapped];
    } else {
      heights = mapped.slice(-12);
    }
  } else {
    heights = defaultHeights;
  }
  return (
    <div className="mt-3">
      <div className="font-mono text-[9px] text-zinc-600 tracking-widest mb-2 uppercase">WAVEFORM_DELTA</div>
      <div className="flex items-end gap-[3px] h-10">
        {heights.map((h, i) => (
          <div
            key={i}
            className="flex-1 rounded-sm opacity-80"
            style={{
              height: `${h}%`,
              backgroundColor: color,
              opacity: 0.6 + (i % 3) * 0.15,
            }}
          />
        ))}
      </div>
    </div>
  );
};

const SensorPanel = ({ side, name, colorPrefix, data, samples }) => {
  const isLeft = side === 'left';
  const color = colorPrefix === 'neon-lime' ? '#AAFF00' : '#FF5C5C';
  const colorClass = colorPrefix === 'neon-lime' ? 'text-[#AAFF00]' : 'text-[#FF5C5C]';
  const bgColorClass = colorPrefix === 'neon-lime' ? 'bg-[#AAFF00]' : 'bg-[#FF5C5C]';

  const distance = data.distance || 0;
  const confidence = data.confidence || 0;
  const votes = data.votes || 0;
  const detected = data.detected || false;
  const votingWindow = data.voting_window || 32;
  const freq = data.freq || 0;
  const power = data.power || 0;

  const displayDist = (distance / 100).toFixed(2);

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
          {/* Segmented bar */}
          <div className={`grid grid-cols-10 gap-1 h-4 ${!isLeft ? 'direction-rtl' : ''}`} style={!isLeft ? { direction: 'rtl' } : {}}>
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

        {/* Waveform */}
        <WaveformDelta color={color} samples={samples} />

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

export default React.memo(SensorPanel, (prev, next) => {
  // Compare samples by length + last value to detect new waveform data
  const samplesEqual =
    prev.samples?.length === next.samples?.length &&
    prev.samples?.[prev.samples.length - 1] === next.samples?.[next.samples.length - 1];
  return (
    prev.data.distance === next.data.distance &&
    prev.data.confidence === next.data.confidence &&
    prev.data.votes === next.data.votes &&
    prev.data.detected === next.data.detected &&
    prev.data.freq === next.data.freq &&
    prev.data.power === next.data.power &&
    samplesEqual
  );
});
