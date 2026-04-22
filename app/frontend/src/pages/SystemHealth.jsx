import React from 'react';
import { useSystemHealth } from '../hooks/useSystemHealth';

const AsciiBar = ({ percent, width = 10, errorThreshold = 80 }) => {
  const filledChars = Math.max(0, Math.min(width, Math.round((percent / 100) * width)));
  const emptyChars = width - filledChars;
  const bar = `[${'▓'.repeat(filledChars)}${'░'.repeat(emptyChars)}] ${Math.round(percent)}%`;
  const isError = percent >= errorThreshold;
  return <span className={isError ? 'text-error' : ''}>{bar}</span>;
};

const SystemHealth = () => {
  const health = useSystemHealth();

  const handleRestart = async () => {
    try {
      await fetch('/api/restart', { method: 'POST' });
    } catch (e) {
      console.error(e);
    }
  };

  const handleStop = async () => {
    try {
      await fetch('/api/stop', { method: 'POST' });
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <main className="flex-1 p-4 md:p-gutter flex flex-col gap-4 md:gap-gutter pb-12">
      <div className="mb-2 md:mb-sm">
        <h1 className="font-h1 text-2xl md:text-h1 text-outline-h1 tracking-tighter">SYSTEM STATUS</h1>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 md:gap-gutter flex-1">
        {/* Left Panel: HARDWARE */}
        <section className="col-span-1 lg:col-span-6 bento-border bg-surface flex flex-col">
          <header className="p-sm bento-border-b flex items-center gap-2 bg-surface-container-low">
            <span className="font-label-caps text-label-caps text-outline">HARDWARE</span>
            <span className="material-symbols-outlined text-outline text-[16px]">developer_board</span>
          </header>
          <div className="p-md flex flex-col gap-lg flex-1">
            <div className="flex items-center gap-2">
              <span className="text-primary text-[12px]">●</span>
              <span className="font-data-md text-data-md text-on-surface">RASPBERRY PI 4 MODEL B</span>
            </div>

            {/* ASCII Metrics */}
            <div className="flex flex-col gap-sm font-code-sm text-code-sm text-on-surface-variant">
              <div className="flex justify-between items-center">
                <span>CPU_LOAD</span>
                <AsciiBar percent={health.cpu_percent} />
              </div>
              <div className="flex justify-between items-center">
                <span>MEM_ALLOC</span>
                <AsciiBar percent={health.ram_percent} />
              </div>
              <div className="flex justify-between items-center">
                <span>CORE_TEMP</span>
                <AsciiBar percent={health.cpu_temp} errorThreshold={80} />
              </div>
            </div>

            {/* Port Status Table */}
            <div className="mt-auto">
              <div className="font-label-caps text-label-caps text-outline mb-sm border-b border-outline pb-xs">I/O INTERFACES</div>
              <div className="flex flex-col border-l border-outline pl-xs gap-xs font-code-sm text-code-sm">
                <div className="flex items-center justify-between">
                  <span className="text-on-surface">/dev/ttyUSB0</span>
                  {health.s1_connected ? (
                    <span className="text-tertiary">● RX/TX ACTIVE</span>
                  ) : (
                    <span className="text-error">○ OFFLINE</span>
                  )}
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-on-surface">/dev/ttyUSB1</span>
                  {health.s2_connected ? (
                    <span className="text-tertiary">● RX/TX ACTIVE</span>
                  ) : (
                    <span className="text-error">○ OFFLINE</span>
                  )}
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Right Panel: MODEL & PIPELINE */}
        <section className="col-span-1 lg:col-span-6 bento-border bg-surface flex flex-col">
          <header className="p-sm bento-border-b flex items-center justify-between bg-surface-container-low">
            <div className="flex items-center gap-2">
              <span className="font-label-caps text-label-caps text-outline">MODEL & PIPELINE</span>
              <span className="material-symbols-outlined text-outline text-[16px]">memory</span>
            </div>
            <span className="font-code-sm text-code-sm text-primary">● STREAMING</span>
          </header>
          <div className="p-md flex flex-col gap-lg flex-1">
            <div className="inline-block bg-primary text-on-primary font-data-md text-data-md px-sm py-xs border border-on-primary w-max">
              [ CNN + LSTM ] v2.4.1
            </div>

            <div className="flex flex-col bento-border">
              <div className="flex justify-between items-center p-xs bento-border-b font-code-sm text-code-sm">
                <span className="text-outline">PARAM</span>
                <span className="text-outline">VALUE</span>
              </div>
              <div className="flex justify-between items-center p-xs bento-border-b font-data-md text-data-md text-on-surface">
                <span>WINDOW_SIZE</span>
                <span>256</span>
              </div>
              <div className="flex justify-between items-center p-xs bento-border-b font-data-md text-data-md text-on-surface">
                <span>THRESHOLD</span>
                <span>0.85</span>
              </div>
              <div className="flex justify-between items-center p-xs font-data-md text-data-md text-on-surface">
                <span>FREQ_RANGE</span>
                <span>0.5-2.0 Hz</span>
              </div>
            </div>

            <div className="flex gap-md mt-auto">
              <div className="flex-1 bg-surface-container-high bento-border p-sm flex flex-col items-center justify-center">
                <span className="font-label-caps text-label-caps text-outline mb-xs">FFT PEAK</span>
                <span className="font-data-lg text-data-lg text-primary">1.2 Hz</span>
              </div>
              <div className="flex-1 bg-surface-container-high bento-border p-sm flex flex-col items-center justify-center">
                <span className="font-label-caps text-label-caps text-outline mb-xs">DL CONF</span>
                <span className="font-data-lg text-data-lg text-tertiary">94.2%</span>
              </div>
            </div>
          </div>
        </section>
      </div>

      <div className="flex flex-col md:flex-row gap-gutter mt-sm pt-sm border-t border-outline">
        <button onClick={handleRestart} className="flex-1 bg-tertiary text-on-tertiary font-data-md text-data-md p-sm border border-tertiary flex items-center justify-center gap-2 hover:invert transition-none">
          <span className="material-symbols-outlined text-[20px]">refresh</span>
          RESTART DETECTION
        </button>
        <button onClick={handleStop} className="flex-1 bg-error text-on-error font-data-md text-data-md p-sm border border-error flex items-center justify-center gap-2 hover:invert transition-none">
          <span className="material-symbols-outlined text-[20px]">stop_circle</span>
          STOP SYSTEM
        </button>
      </div>
    </main>
  );
};

export default SystemHealth;
