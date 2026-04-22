import React from 'react';
import { BrowserRouter, Routes, Route, Link, useLocation } from 'react-router-dom';
import Dashboard from './pages/Dashboard';
import History from './pages/History';
import SystemHealth from './pages/SystemHealth';
import Landing from './pages/Landing';
import Header from './components/Header';
import { useSocket } from './hooks/useSocket';

const Navigation = () => {
  const location = useLocation();
  const isActive = (path) => location.pathname === path;

  // We skip Navigation completely on Landing page to maximize space
  if (location.pathname === '/about') return null;

  return (
    <>
      {/* Desktop Sidebar */}
      <nav className="hidden md:flex flex-col fixed left-0 top-12 h-[calc(100vh-48px)] w-64 z-40 bg-[#141414] text-[#AAFF00] font-mono text-xs uppercase border-r border-[#AAFF00]">
        <div className="p-4 border-b border-[#AAFF00]/30">
          <div className="font-black text-[#AAFF00] text-sm">[ SENSOR_01 ]</div>
          <div className="text-[#AAFF00]/70 mt-1">STATUS: ● ACTIVE</div>
        </div>
        <div className="flex-1 flex flex-col">
          <Link to="/" className={`${isActive('/') ? 'bg-[#AAFF00] text-[#141414] font-bold' : 'text-[#AAFF00] hover:bg-[#AAFF00]/10 border-b border-[#AAFF00]/30'} w-full flex items-center gap-2 p-3 cursor-pointer transition-colors`}>
            <span className="material-symbols-outlined text-[18px]">grid_view</span> DASHBOARD
          </Link>
          <Link to="/history" className={`${isActive('/history') ? 'bg-[#AAFF00] text-[#141414] font-bold' : 'text-[#AAFF00] hover:bg-[#AAFF00]/10 border-b border-[#AAFF00]/30'} w-full flex items-center gap-2 p-3 cursor-pointer transition-colors`}>
            <span className="material-symbols-outlined text-[18px]">monitor_heart</span> BIO_METRICS
          </Link>
          <Link to="/health" className={`${isActive('/health') ? 'bg-[#AAFF00] text-[#141414] font-bold' : 'text-[#AAFF00] hover:bg-[#AAFF00]/10 border-b border-[#AAFF00]/30'} w-full flex items-center gap-2 p-3 cursor-pointer transition-colors`}>
            <span className="material-symbols-outlined text-[18px]">settings</span> CONFIG
          </Link>
          <Link to="/about" className="text-[#AAFF00] hover:bg-[#AAFF00]/10 w-full flex items-center gap-2 p-3 border-b border-[#AAFF00]/30 cursor-pointer transition-colors">
            <span className="material-symbols-outlined text-[18px]">info</span> ABOUT
          </Link>
        </div>
      </nav>

      {/* Mobile Bottom Nav */}
      <nav className="md:hidden fixed bottom-0 left-0 w-full h-14 bg-[#141414] border-t border-[#AAFF00] z-50 flex justify-around items-center text-xs font-mono uppercase">
        <Link to="/" className={`${isActive('/') ? 'text-[#AAFF00] border-t-2 border-[#AAFF00] font-bold' : 'text-outline'} flex flex-col items-center justify-center w-full h-full transition-colors`}>
          <span className="material-symbols-outlined text-[20px]">grid_view</span>
        </Link>
        <Link to="/history" className={`${isActive('/history') ? 'text-[#AAFF00] border-t-2 border-[#AAFF00] font-bold' : 'text-outline'} flex flex-col items-center justify-center w-full h-full transition-colors`}>
          <span className="material-symbols-outlined text-[20px]">monitor_heart</span>
        </Link>
        <Link to="/health" className={`${isActive('/health') ? 'text-[#AAFF00] border-t-2 border-[#AAFF00] font-bold' : 'text-outline'} flex flex-col items-center justify-center w-full h-full transition-colors`}>
          <span className="material-symbols-outlined text-[20px]">settings</span>
        </Link>
        <Link to="/about" className={`${isActive('/about') ? 'text-[#AAFF00] border-t-2 border-[#AAFF00] font-bold' : 'text-outline'} flex flex-col items-center justify-center w-full h-full transition-colors`}>
          <span className="material-symbols-outlined text-[20px]">info</span>
        </Link>
      </nav>
    </>
  );
};

const Layout = () => {
  useSocket(); // connect socket
  const location = useLocation();
  const isAbout = location.pathname === '/about';

  return (
    <>
      <Header />
      <Navigation />
      {/* Content Canvas */}
      <div className={`flex-1 flex flex-col pt-12 pb-14 md:pb-0 min-h-screen ${!isAbout ? 'md:pl-64' : ''}`}>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/history" element={<History />} />
          <Route path="/health" element={<SystemHealth />} />
          <Route path="/about" element={<Landing />} />
        </Routes>
      </div>
    </>
  );
};

export default function App() {
  return (
    <BrowserRouter>
      <Layout />
    </BrowserRouter>
  );
}
