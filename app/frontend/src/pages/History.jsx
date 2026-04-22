import React, { useContext, useEffect, useState } from 'react';
import { HistoryDataContext } from '../context/SensorContext';
import BreathingChart from '../components/BreathingChart';
import DetectionTable from '../components/DetectionTable';

const History = () => {
  const history = useContext(HistoryDataContext);
  const [dbHistory, setDbHistory] = useState([]);

  useEffect(() => {
    fetch('http://192.168.137.19:5050/api/history').then(res => res.json()).then(data => setDbHistory(data)).catch(e => console.error(e));
  }, []);

  const displayData = history.length > 0 ? history : dbHistory;

  return (
    <main className="flex-1 p-4 md:p-gutter flex flex-col gap-4 md:gap-md pb-12">
      <header className="mb-2 md:mb-sm">
        <h1 className="font-h1 text-2xl md:text-h1 text-on-surface uppercase border-b-2 border-surface-variant pb-2 inline-block">DETECTION LOG</h1>
      </header>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 md:gap-md">
        <div className="bento-border-dim p-sm flex flex-col bg-surface-container-lowest">
          <div className="font-label-caps text-label-caps text-cyan mb-2 border-b border-surface-variant pb-1 flex items-center gap-2">
            <span className="material-symbols-outlined text-[14px]">timeline</span>
            DETECTIONS LOGGED
          </div>
          <div className="font-data-lg text-data-lg text-on-surface mt-2">{displayData.length}</div>
        </div>
        <div className="bento-border p-sm flex flex-col bg-[#141414]">
          <div className="font-label-caps text-label-caps text-[#AAFF00] mb-2 border-b border-[#AAFF00]/50 pb-1 flex items-center gap-2">
            <span className="material-symbols-outlined text-[14px]">sensors</span>
            S1 ACTIVE
          </div>
          <div className="font-data-lg text-data-lg text-[#AAFF00] mt-2">●</div>
        </div>
      </div>

      <div className="bento-border-dim bg-surface-container-lowest flex flex-col">
        <div className="border-b border-surface-variant p-sm flex justify-between items-center bg-surface-container">
          <div className="font-label-caps text-label-caps text-on-surface flex items-center gap-2">
            <span className="material-symbols-outlined text-[14px]">monitoring</span>
            [ SYS_CONFIDENCE_METRICS ]
          </div>
        </div>
        <BreathingChart data={displayData} />
        <div className="border-t border-surface-variant p-2 flex gap-6 bg-surface-container font-code-sm text-code-sm pl-4">
          <div className="flex items-center gap-2 text-[#AAFF00]">
            <span className="w-3 h-0.5 bg-[#AAFF00] inline-block"></span>
            S1_CONFIDENCE
          </div>
          <div className="flex items-center gap-2 text-[#FF5C5C]">
            <span className="w-3 h-0.5 bg-[#FF5C5C] inline-block border-t border-dashed border-[#FF5C5C]"></span>
            S2_CONFIDENCE
          </div>
        </div>
      </div>

      <DetectionTable data={displayData} />
    </main>
  );
};

export default History;
