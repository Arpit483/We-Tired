import React, { useContext } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { SensorDataContext } from '../context/SensorContext';

const Header = () => {
  const state = useContext(SensorDataContext);
  const { wsConnected } = state;
  const location = useLocation();
  const isActive = (path) => location.pathname === path;

  return (
    <header className="flex items-center h-11 px-4 w-full bg-[#0a0a0a] border-b border-[#1a1a1a] shrink-0 sticky top-0 z-50">
      {/* Brand */}
      <div className="flex items-center gap-4 mr-6">
        <span className="text-sm font-black text-[#AAFF00] italic font-mono uppercase tracking-widest whitespace-nowrap">
          VITALRADAR_TACTICAL
        </span>
      </div>

      {/* Tab Nav */}
      <nav className="hidden md:flex items-end h-full gap-0 border-r border-[#1f1f1f] pr-6 mr-auto">
        <Link
          to="/"
          className={`px-4 h-full flex items-center font-mono text-[11px] font-bold tracking-widest uppercase border-b-2 transition-colors ${
            isActive('/')
              ? 'border-[#AAFF00] text-[#AAFF00]'
              : 'border-transparent text-zinc-500 hover:text-zinc-300'
          }`}
        >
          DASHBOARD
        </Link>
        <Link
          to="/history"
          className={`px-4 h-full flex items-center font-mono text-[11px] font-bold tracking-widest uppercase border-b-2 transition-colors ${
            isActive('/history')
              ? 'border-[#AAFF00] text-[#AAFF00]'
              : 'border-transparent text-zinc-500 hover:text-zinc-300'
          }`}
        >
          LOGS
        </Link>
        <Link
          to="/health"
          className={`px-4 h-full flex items-center font-mono text-[11px] font-bold tracking-widest uppercase border-b-2 transition-colors ${
            isActive('/health')
              ? 'border-[#AAFF00] text-[#AAFF00]'
              : 'border-transparent text-zinc-500 hover:text-zinc-300'
          }`}
        >
          DIAGNOSTICS
        </Link>
      </nav>

      {/* Right Status */}
      <div className="ml-auto flex items-center gap-4">
        <div className="hidden sm:flex items-center gap-3 text-zinc-600">
          <span className="material-symbols-outlined text-[16px]">sensors</span>
          <span className="material-symbols-outlined text-[16px]">signal_cellular_alt</span>
          <span className="material-symbols-outlined text-[16px]">battery_charging_full</span>
        </div>
        <div className="flex items-center gap-2 bg-[#111] border border-[#222] px-3 py-1">
          <span className="text-[10px] font-mono font-bold tracking-widest uppercase text-zinc-400">
            {wsConnected ? 'SYS_READY' : 'SYS_OFFLINE'}
          </span>
          <div className={`w-2 h-2 rounded-full ${wsConnected ? 'bg-[#AAFF00] animate-pulse shadow-[0_0_6px_rgba(170,255,0,0.9)]' : 'bg-red-500'}`} />
        </div>
      </div>
    </header>
  );
};

export default React.memo(Header);
