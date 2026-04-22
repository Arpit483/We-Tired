import React, { useRef, useEffect, useContext } from 'react';
import { TerminalLogContext } from '../context/SensorContext';

const TerminalLog = () => {
  const lines = useContext(TerminalLogContext);
  const containerRef = useRef(null);

  useEffect(() => {
    if (containerRef.current) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight;
    }
  }, [lines.length]); // scroll on new lines

  return (
    <footer className="h-48 md:h-56 bg-[#09090b] border-t border-zinc-800 p-4 font-mono flex flex-col shrink-0 w-full mt-auto">
      <div className="flex justify-between items-center mb-3">
        <div className="flex items-center gap-2">
          <span className="material-symbols-outlined text-sm text-zinc-500">terminal</span>
          <span className="text-[11px] font-bold text-zinc-400 uppercase tracking-widest">System_Console_Output</span>
        </div>
        <div className="flex items-center gap-4">
          <span className="text-[10px] text-zinc-600 hidden sm:inline">BAUD_RATE: 115200</span>
        </div>
      </div>
      <div 
        className="flex-1 overflow-y-auto space-y-1 custom-scrollbar pr-2 bg-black/40 border border-zinc-800/50 rounded p-3" 
        ref={containerRef}
      >
        {lines.length === 0 && (
          <p className="text-zinc-500 text-[10px] font-mono leading-tight">
            <span className="text-neon-lime font-bold">[SYSTEM]</span> WAITING_FOR_DATA_STREAM...
          </p>
        )}
        {lines.map((lineObj) => {
          const lineStr = lineObj.text;
          let colorClass = "text-zinc-400";
          let prefix = "";
          let rest = lineStr;
          
          if (lineStr.startsWith("[S1]")) {
            colorClass = "text-neon-lime";
            prefix = "[S1]";
            rest = lineStr.substring(4);
          } else if (lineStr.startsWith("[S2]")) {
            colorClass = "text-neon-coral";
            prefix = "[S2]";
            rest = lineStr.substring(4);
          } else if (lineStr.startsWith("[SYS]")) {
            colorClass = "text-neon-cyan";
            prefix = "[SYS]";
            rest = lineStr.substring(5);
          }

          return (
            <p key={lineObj.id} className="text-zinc-400 text-[11px] font-mono leading-tight">
              {prefix && <span className={`${colorClass} font-bold mr-1`}>{prefix}</span>}
              <span className="whitespace-pre-wrap">{rest}</span>
            </p>
          );
        })}
      </div>
    </footer>
  );
};

export default React.memo(TerminalLog);
