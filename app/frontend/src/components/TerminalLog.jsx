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
    <div className="h-32 bg-[#0A0A0A] border border-outline-variant p-2 font-code-sm text-code-sm overflow-hidden flex flex-col shrink-0">
      <div className="border-b border-outline-variant mb-2 pb-1 flex justify-between text-outline">
        <span>LIVE LOG_STREAM</span>
        <span className="material-symbols-outlined text-[12px]">terminal</span>
      </div>
      <div className="flex flex-col gap-1 overflow-y-auto" ref={containerRef}>
        {lines.map((lineStr, i) => {
          // parse prefix [S1], [S2], [SYS]
          let colorClass = "text-on-surface";
          let prefix = "";
          let rest = lineStr;
          
          if (lineStr.startsWith("[S1]")) {
            colorClass = "neon-lime";
            prefix = "[S1]";
            rest = lineStr.substring(4);
          } else if (lineStr.startsWith("[S2]")) {
            colorClass = "neon-coral";
            prefix = "[S2]";
            rest = lineStr.substring(4);
          } else if (lineStr.startsWith("[SYS]")) {
            colorClass = "neon-cyan";
            prefix = "[SYS]";
            rest = lineStr.substring(5);
          }

          return (
            <div key={i} className="flex gap-2">
              <span className="text-outline">{new Date().toISOString().substring(11, 23)}</span>
              {prefix && <span className={colorClass}>{prefix}</span>}
              <span className="text-on-surface whitespace-pre-wrap">{rest}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default React.memo(TerminalLog);
