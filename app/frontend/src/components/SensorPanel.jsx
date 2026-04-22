import React from 'react';
import VotesBar from './VotesBar';

const SensorPanel = ({ side, name, colorPrefix, data }) => {
  const borderClass = `border-${colorPrefix}`;
  const textClass = `text-${colorPrefix}`;
  const bgClass = `bg-${colorPrefix}`;

  return (
    <div className={`border ${borderClass} flex flex-col h-full bg-[#141414]`}>
      <div className={`border-b ${borderClass} p-2 flex justify-between items-center ${textClass} font-label-caps text-label-caps`}>
        <span>[ {name} ]</span>
        <span>{side.toUpperCase()}</span>
      </div>
      <div className="p-4 flex flex-col gap-6 flex-1">
        <div className="flex flex-col items-center justify-center py-8">
          <span className={`font-h1 text-h1 ${textClass}`}>{data.distance?.toFixed(1) || '0.0'}</span>
          <span className={`font-label-caps text-label-caps ${textClass}`}>cm</span>
        </div>
        
        <div className="flex flex-col gap-4">
          <div className="flex flex-col gap-1">
            <div className={`flex justify-between font-code-sm text-code-sm ${textClass}`}>
              <span>CONF {data.confidence?.toFixed(3) || '0.000'}</span>
              <span>{data.detected ? 'DETECTED' : 'SEARCHING'}</span>
            </div>
            <div className={`w-full h-2 border ${borderClass} p-[1px] flex`}>
              <div className={`${bgClass} h-full`} style={{ width: `${Math.min(100, Math.max(0, (data.confidence || 0) * 100))}%` }}></div>
            </div>
          </div>
          
          <div className="flex flex-col gap-1">
            <div className={`flex justify-between font-code-sm text-code-sm ${textClass}`}>
              <span>VOTES {data.votes || 0} / 32</span>
            </div>
            <VotesBar votes={data.votes || 0} total={32} colorClass={bgClass} />
          </div>
          
          <div className={`grid grid-cols-2 gap-2 mt-4 border-t ${borderClass} pt-4`}>
            <div className={`border ${borderClass} p-2 flex flex-col items-center`}>
              <span className={`font-code-sm text-code-sm ${textClass} opacity-70`}>FREQ</span>
              <span className={`font-data-md text-data-md ${textClass}`}>{data.freq?.toFixed(3) || '0.000'} Hz</span>
            </div>
            <div className={`border ${borderClass} p-2 flex flex-col items-center`}>
              <span className={`font-code-sm text-code-sm ${textClass} opacity-70`}>POWER</span>
              <span className={`font-data-md text-data-md ${textClass}`}>{data.power?.toFixed(1) || '0.0'}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
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
