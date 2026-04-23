import React from 'react';

const DirectionRing = ({ direction, distance, freq, votes }) => {
  const isDetected = direction !== 'none';
  const isLeft = direction === 'move_left';
  const isRight = direction === 'move_right';
  const isCenter = direction === 'center';

  const confPercent = isDetected ? '99.8%' : '--%';
  const ringColor = isDetected ? '#00CFFF' : '#1f2a30';
  const glowColor = isDetected ? 'rgba(0,207,255,0.3)' : 'transparent';

  let dirLabel = 'CENTER';
  if (isLeft) dirLabel = 'MOVE_LEFT';
  if (isRight) dirLabel = 'MOVE_RIGHT';
  if (!isDetected) dirLabel = 'SCANNING';

  return (
    <section className="order-1 md:order-2 md:col-span-6 flex flex-col bg-[#0a0a0a] overflow-hidden">
      {/* Center panel header */}
      <div className="flex items-center justify-between px-4 py-2 border-b border-[#1a1a1a]">
        <div>
          <div className="text-white font-mono text-[10px] font-bold tracking-[0.15em] uppercase">
            TACTICAL_OVERLAY_01
          </div>
          <div className="text-zinc-600 font-mono text-[9px] tracking-wider">
            ACTIVE_MONITORING_MODE: FUSED_TELEMETRY
          </div>
        </div>
        <div className="text-right hidden sm:block">
          <div className="text-zinc-400 font-mono text-[9px] tracking-wider">POS: 34.0522° N</div>
          <div className="text-zinc-600 font-mono text-[9px] tracking-wider">118.2437° W</div>
        </div>
      </div>

      {/* Radar Ring */}
      <div className="flex-1 flex flex-col items-center justify-center p-4 relative">
        {/* Direction arrows */}
        <div className="flex items-center justify-between w-full max-w-sm mb-4 z-10">
          <span className={`font-mono text-[10px] tracking-widest ${isLeft ? 'text-[#AAFF00]' : 'text-zinc-700'}`}>
            ‹ — LEFT
          </span>
          <span className={`font-mono text-[11px] font-bold tracking-widest ${isCenter ? 'text-white' : 'text-zinc-600'}`}>
            ▲ {dirLabel}
          </span>
          <span className={`font-mono text-[10px] tracking-widest ${isRight ? 'text-[#FF5C5C]' : 'text-zinc-700'}`}>
            RIGHT — ›
          </span>
        </div>

        {/* SVG Radar */}
        <div className="relative flex items-center justify-center" style={{ width: 220, height: 220 }}>
          <svg width="220" height="220" viewBox="0 0 220 220" className="absolute inset-0">
            {/* Outer rings */}
            {[100, 80, 60, 40].map((r, i) => (
              <circle
                key={i}
                cx="110" cy="110" r={r}
                fill="none"
                stroke={i === 0 ? ringColor : '#1a2830'}
                strokeWidth={i === 0 ? 1.5 : 0.8}
                opacity={i === 0 ? 0.8 : 0.4}
                strokeDasharray={i === 1 ? '4 6' : i === 2 ? '2 8' : 'none'}
              />
            ))}
            {/* Cross hairs */}
            <line x1="110" y1="10" x2="110" y2="210" stroke="#1a2830" strokeWidth="0.5" opacity="0.5" />
            <line x1="10" y1="110" x2="210" y2="110" stroke="#1a2830" strokeWidth="0.5" opacity="0.5" />
            {/* Glow dot at center when detected */}
            {isDetected && (
              <circle cx="110" cy="110" r="6" fill={ringColor} opacity="0.9">
                <animate attributeName="r" values="4;8;4" dur="2s" repeatCount="indefinite" />
                <animate attributeName="opacity" values="0.9;0.3;0.9" dur="2s" repeatCount="indefinite" />
              </circle>
            )}
            {/* Sweeping sector */}
            {isDetected && (
              <path
                d="M110,110 L110,10 A100,100 0 0,1 180,60 Z"
                fill="url(#radarGrad)"
                opacity="0.15"
              >
                <animateTransform attributeName="transform" type="rotate" from="0 110 110" to="360 110 110" dur="4s" repeatCount="indefinite" />
              </path>
            )}
            <defs>
              <radialGradient id="radarGrad" cx="50%" cy="50%" r="50%">
                <stop offset="0%" stopColor={ringColor} stopOpacity="0.4" />
                <stop offset="100%" stopColor={ringColor} stopOpacity="0" />
              </radialGradient>
            </defs>
          </svg>

          {/* Center confidence text */}
          <div className="relative z-10 text-center">
            <div
              className="font-mono font-black leading-none"
              style={{
                fontSize: 40,
                color: ringColor,
                textShadow: `0 0 20px ${glowColor}`,
              }}
            >
              {confPercent}
            </div>
            <div className="font-mono text-[9px] text-zinc-500 tracking-widest mt-1 uppercase">
              {isDetected ? 'DETECTION' : 'NO_SIGNAL'}
            </div>
          </div>
        </div>

        {/* Metrics strip */}
        <div className="grid grid-cols-3 gap-2 w-full max-w-sm mt-4">
          <div className="text-center">
            <div className="text-zinc-600 font-mono text-[9px] uppercase tracking-widest mb-1">AVL_VELOCITY</div>
            <div className="text-white font-mono text-lg font-bold">
              4.2 <span className="text-zinc-500 text-[10px] font-normal">km/h</span>
            </div>
          </div>
          <div className="text-center border-x border-[#1a1a1a]">
            <div className="font-mono text-[9px] uppercase tracking-widest mb-1" style={{ color: ringColor }}>FUSED_RANGE</div>
            <div className="text-white font-mono text-lg font-bold">
              {distance ? distance.toFixed(2) : '--'} <span className="text-zinc-500 text-[10px] font-normal">m</span>
            </div>
          </div>
          <div className="text-center">
            <div className="text-zinc-600 font-mono text-[9px] uppercase tracking-widest mb-1">ERROR_MARGIN</div>
            <div className="text-white font-mono text-lg font-bold">
              ±0.02 <span className="text-zinc-500 text-[10px] font-normal">cm</span>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default React.memo(DirectionRing);
