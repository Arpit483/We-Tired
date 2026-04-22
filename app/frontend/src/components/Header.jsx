import React, { useContext } from 'react';
import { SensorDataContext } from '../context/SensorContext';

const Header = () => {
  const state = useContext(SensorDataContext);
  const { wsConnected } = state;

  return (
    <header className="flex justify-between items-center h-14 px-4 w-full bg-[#0a0a0a] border-zinc-800 border-b shrink-0 sticky top-0 z-40">
      <div className="flex items-center gap-2 md:gap-4">
        <span className="text-sm md:text-lg font-black text-neon-lime italic font-mono uppercase tracking-widest">
          VITALRADAR_TACTICAL
        </span>
        <div className="hidden md:block h-4 w-px bg-zinc-800"></div>
        <nav className="hidden md:flex gap-4">
          <span className="font-mono uppercase tracking-widest text-xs text-neon-lime border-b-2 border-neon-lime h-14 flex items-center">
            DASHBOARD
          </span>
          {/* React Router could be used here later if these aren't managed by App.jsx Navigation */}
        </nav>
      </div>
      
      <div className="flex items-center gap-3 md:gap-4">
        <div className="hidden sm:flex items-center gap-2 text-zinc-500">
          <span className="material-symbols-outlined text-sm">sensors</span>
          <span className="material-symbols-outlined text-sm">signal_cellular_alt</span>
        </div>
        <div className="bg-zinc-900 border border-zinc-800 px-3 py-1 flex items-center rounded-sm">
          <span className="text-[10px] font-mono text-zinc-400 mr-2 uppercase tracking-wider">
            {wsConnected ? 'SYS_READY' : 'SYS_DISCONNECTED'}
          </span>
          <div className={`w-2 h-2 ${wsConnected ? 'bg-neon-lime animate-pulse shadow-[0_0_8px_rgba(170,255,0,0.8)]' : 'bg-red-600'} rounded-full`}></div>
        </div>
      </div>
    </header>
  );
};

export default React.memo(Header);
