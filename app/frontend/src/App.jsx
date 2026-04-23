import React from 'react';
import { BrowserRouter, Routes, Route, Link, useLocation } from 'react-router-dom';
import Dashboard from './pages/Dashboard';
import History from './pages/History';
import SystemHealth from './pages/SystemHealth';
import Landing from './pages/Landing';
import Scan from './pages/Scan';
import Header from './components/Header';
import { useSocket } from './hooks/useSocket';

const Sidebar = () => {
  const location = useLocation();
  const isActive = (path) => location.pathname === path;

  return (
    <aside className="hidden md:flex flex-col w-52 shrink-0 bg-[#0a0a0a] border-r border-[#1a1a1a] h-[calc(100vh-44px)] sticky top-11">
      {/* Operator info */}
      <div className="p-4 border-b border-[#1a1a1a]">
        <div className="text-[#AAFF00] font-mono text-[10px] font-bold tracking-widest uppercase">SYS_OPERATOR</div>
        <div className="text-zinc-500 font-mono text-[9px] mt-0.5 tracking-wider">SECTOR_07_ACTIVE</div>
      </div>

      {/* Nav items */}
      <nav className="flex flex-col flex-1">
        {[
          { to: '/', icon: 'grid_view', label: 'DASHBOARD' },
          { to: '/scan', icon: 'radar', label: 'SCAN' },
          { to: '/history', icon: 'monitor_heart', label: 'LOGS' },
          { to: '/health', icon: 'settings', label: 'DIAGNOSTICS' },
          { to: '/about', icon: 'tune', label: 'MISSION_CONFIG' },
        ].map(({ to, icon, label }) => (
          <Link
            key={to}
            to={to}
            className={`flex items-center gap-3 px-4 py-3 font-mono text-[11px] font-bold tracking-widest uppercase border-b border-[#141414] transition-colors ${
              isActive(to)
                ? 'bg-[#AAFF00] text-[#0a0a0a]'
                : 'text-zinc-500 hover:text-zinc-300 hover:bg-[#111]'
            }`}
          >
            <span className="material-symbols-outlined text-[16px]">{icon}</span>
            {label}
          </Link>
        ))}
      </nav>

      {/* Power Off */}
      <div className="border-t border-[#1a1a1a] p-4">
        <div
          className="flex items-center gap-2 text-zinc-600 font-mono text-[10px] tracking-widest cursor-pointer hover:text-red-400 transition-colors"
          onClick={async () => {
            if (window.confirm('Stop VitalRadar detection system?')) {
              try { await fetch('/api/stop', { method: 'POST' }); }
              catch(e) { console.error(e); }
            }
          }}
        >
          <span className="material-symbols-outlined text-[14px]">power_settings_new</span>
          POWER_OFF
        </div>
      </div>
    </aside>
  );
};

const Layout = () => {
  useSocket();
  const location = useLocation();
  const isAbout = location.pathname === '/about';

  return (
    <div className="flex flex-col h-screen overflow-hidden bg-[#0a0a0a]">
      <Header />
      <div className="flex flex-1 overflow-hidden">
        <Sidebar />
        <main className="flex-1 overflow-y-auto overflow-x-hidden">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/scan" element={<Scan />} />
            <Route path="/history" element={<History />} />
            <Route path="/health" element={<SystemHealth />} />
            <Route path="/about" element={<Landing />} />
          </Routes>
        </main>
      </div>

      {/* Mobile Bottom Nav */}
      <nav className="md:hidden fixed bottom-0 left-0 w-full h-12 bg-[#0a0a0a] border-t border-[#1a1a1a] z-50 flex justify-around items-center">
        {[
          { to: '/', icon: 'grid_view' },
          { to: '/scan', icon: 'radar' },
          { to: '/history', icon: 'monitor_heart' },
          { to: '/health', icon: 'settings' },
          { to: '/about', icon: 'tune' },
        ].map(({ to, icon }) => (
          <Link key={to} to={to} className={`flex items-center justify-center w-full h-full ${location.pathname === to ? 'text-[#AAFF00]' : 'text-zinc-600'}`}>
            <span className="material-symbols-outlined text-[20px]">{icon}</span>
          </Link>
        ))}
      </nav>
    </div>
  );
};

export default function App() {
  return (
    <BrowserRouter>
      <Layout />
    </BrowserRouter>
  );
}
