import React, { useContext } from 'react';
import { SensorDataContext } from '../context/SensorContext';

const Header = () => {
  const state = useContext(SensorDataContext);
  const { latestData, wsConnected } = state;

  return (
    <header className="fixed flex justify-between items-center w-full px-4 h-12 top-0 border-b border-[#AAFF00] bg-[#141414] text-[#AAFF00] font-mono text-sm tracking-tight uppercase z-50">
      <div className="flex items-center gap-2 text-xl font-black text-[#AAFF00] tracking-tighter">
        <span className={wsConnected ? "pulse-text" : ""}>◎</span> VITALRADAR_v1.0
      </div>
      
      {latestData.status === 'detected' && (
        <div className="border border-[#AAFF00] text-[#AAFF00] px-3 py-1 font-label-caps text-label-caps flex items-center gap-2">
          <span>●</span> BREATHING DETECTED
        </div>
      )}
      {latestData.status === 'high_chance' && (
        <div className="border border-[#FFB000] text-[#FFB000] px-3 py-1 font-label-caps text-label-caps flex items-center gap-2">
          <span>◐</span> HIGH CHANCE
        </div>
      )}

      <div className="flex gap-4">
        <span className="material-symbols-outlined text-[#AAFF00] hover:bg-[#AAFF00] hover:text-[#141414] cursor-pointer">sensors</span>
        <span className="material-symbols-outlined text-[#AAFF00] hover:bg-[#AAFF00] hover:text-[#141414] cursor-pointer">settings_input_component</span>
        <span className="material-symbols-outlined text-[#AAFF00] hover:bg-[#AAFF00] hover:text-[#141414] cursor-pointer">power_settings_new</span>
      </div>
    </header>
  );
};

export default React.memo(Header);
