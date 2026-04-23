import React, { useRef, useEffect, useContext, useState, useCallback } from 'react';
import { TerminalLogContext } from '../context/SensorContext';

const DraggableTerminal = () => {
  const lines = useContext(TerminalLogContext);
  const scrollRef = useRef(null);
  const dragRef = useRef(null);
  const isDragging = useRef(false);
  const dragStart = useRef({ x: 0, y: 0, top: 0, left: 0 });

  // Default: docked to bottom, full width
  const [pos, setPos] = useState({ top: null, left: null, width: null, height: 180 });
  const [isDocked, setIsDocked] = useState(true);
  const [isMinimized, setIsMinimized] = useState(false);

  // Auto-scroll on new lines
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [lines.length]);

  // Drag handlers
  const onMouseDown = useCallback((e) => {
    if (isDocked) {
      // Detach from dock before dragging
      const rect = dragRef.current.getBoundingClientRect();
      setPos({ top: rect.top, left: rect.left, width: rect.width, height: rect.height });
      setIsDocked(false);
      // Let state settle before dragging
      setTimeout(() => {
        isDragging.current = true;
      }, 10);
    } else {
      isDragging.current = true;
    }
    const rect = dragRef.current.getBoundingClientRect();
    dragStart.current = { x: e.clientX, y: e.clientY, top: rect.top, left: rect.left };
    e.preventDefault();
  }, [isDocked]);

  useEffect(() => {
    const onMove = (e) => {
      if (!isDragging.current) return;
      const dx = e.clientX - dragStart.current.x;
      const dy = e.clientY - dragStart.current.y;
      setPos((p) => ({
        ...p,
        top: Math.max(0, dragStart.current.top + dy),
        left: Math.max(0, dragStart.current.left + dx),
      }));
    };
    const onUp = () => { isDragging.current = false; };
    window.addEventListener('mousemove', onMove);
    window.addEventListener('mouseup', onUp);
    return () => {
      window.removeEventListener('mousemove', onMove);
      window.removeEventListener('mouseup', onUp);
    };
  }, []);

  const dockToBottom = () => {
    setIsDocked(true);
    setPos({ top: null, left: null, width: null, height: 180 });
  };

  const containerStyle = isDocked
    ? { position: 'relative', width: '100%', height: isMinimized ? 36 : pos.height }
    : {
        position: 'fixed',
        top: pos.top ?? 100,
        left: pos.left ?? 100,
        width: pos.width ?? 700,
        height: isMinimized ? 36 : pos.height,
        zIndex: 9999,
        boxShadow: '0 8px 40px rgba(0,0,0,0.8)',
        resize: isMinimized ? 'none' : 'both',
        overflow: 'hidden',
        minWidth: 320,
        minHeight: 36,
      };

  return (
    <div ref={dragRef} style={containerStyle} className="bg-[#080808] border-t border-[#1a1a1a] font-mono flex flex-col">
      {/* Title bar (drag handle) */}
      <div
        onMouseDown={onMouseDown}
        className="flex items-center justify-between px-4 py-2 border-b border-[#1a1a1a] cursor-grab active:cursor-grabbing select-none shrink-0 bg-[#0d0d0d]"
      >
        <div className="flex items-center gap-2">
          <span className="material-symbols-outlined text-[13px] text-zinc-500">terminal</span>
          <span className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest">SYSTEM_CONSOLE_OUTPUT</span>
        </div>
        <div className="flex items-center gap-4">
          <span className="text-[9px] text-zinc-600 hidden sm:inline tracking-wider">
            BAUD_RATE: 115200
          </span>
          <span className="text-[9px] text-zinc-600 hidden sm:inline tracking-wider">
            BUFFER_OK: {lines.length > 0 ? '99.4%' : '0.0%'}
          </span>
          {/* Controls */}
          {!isDocked && (
            <button
              onMouseDown={(e) => e.stopPropagation()}
              onClick={dockToBottom}
              title="Dock to bottom"
              className="text-zinc-600 hover:text-[#AAFF00] text-[10px] tracking-wider transition-colors"
            >
              DOCK
            </button>
          )}
          <button
            onMouseDown={(e) => e.stopPropagation()}
            onClick={() => setIsMinimized((v) => !v)}
            title={isMinimized ? 'Expand' : 'Minimize'}
            className="text-zinc-600 hover:text-zinc-300 transition-colors"
          >
            <span className="material-symbols-outlined text-[14px]">{isMinimized ? 'expand_more' : 'remove'}</span>
          </button>
        </div>
      </div>

      {/* Log output */}
      {!isMinimized && (
        <div
          ref={scrollRef}
          className="flex-1 overflow-y-auto px-4 py-2 space-y-0.5"
          style={{ scrollbarWidth: 'thin', scrollbarColor: '#1f1f1f #080808' }}
        >
          {lines.length === 0 && (
            <p className="text-zinc-700 text-[10px]">
              <span className="text-[#AAFF00] font-bold">[SYSTEM]</span> WAITING_FOR_DATA_STREAM...
            </p>
          )}
          {lines.map((lineObj) => {
            const text = lineObj.text;
            // Parse timestamp from [HH:MM:SS] prefix if present, else show line as-is
            const tsMatch = text.match(/^\[(\d{2}:\d{2}:\d{2})\](.*)/s);
            const timestamp = tsMatch ? tsMatch[1] : null;
            const body = tsMatch ? tsMatch[2] : text;

            let prefixColor = 'text-zinc-500';
            let prefix = '';
            let rest = body;

            if (body.includes('[S1]') || body.startsWith(' [S1]') || text.startsWith('[S1]')) {
              prefixColor = 'text-[#AAFF00]';
              prefix = '[S1]';
              rest = body.replace('[S1]', '');
            } else if (body.includes('[S2]') || text.startsWith('[S2]')) {
              prefixColor = 'text-[#FF5C5C]';
              prefix = '[S2]';
              rest = body.replace('[S2]', '');
            } else if (body.toLowerCase().includes('warning') || body.toLowerCase().includes('warn')) {
              prefixColor = 'text-yellow-400';
            } else if (body.toLowerCase().includes('error')) {
              prefixColor = 'text-red-500';
            } else if (body.toLowerCase().includes('ok') || body.toLowerCase().includes('ready')) {
              prefixColor = 'text-[#AAFF00]';
            } else if (body.toLowerCase().includes('lock') || body.toLowerCase().includes('detect')) {
              prefixColor = 'text-[#00CFFF]';
            }

            // Highlight important keywords
            const highlightLine = (str) => {
              if (str.toLowerCase().includes('combined_telemetry_lock') || str.toLowerCase().includes('lock: obtained')) {
                return <span className="text-[#00CFFF]">{str}</span>;
              }
              if (str.toLowerCase().includes('warning') || str.toLowerCase().includes('drift')) {
                return <span className="text-yellow-400">{str}</span>;
              }
              return <span className="text-zinc-400">{str}</span>;
            };

            return (
              <p key={lineObj.id} className="text-[10px] leading-5 flex items-start gap-2 whitespace-pre-wrap">
                {timestamp && (
                  <span className="text-zinc-700 shrink-0">[{timestamp}]</span>
                )}
                {prefix && (
                  <span className={`${prefixColor} font-bold shrink-0`}>{prefix}</span>
                )}
                {highlightLine(rest)}
              </p>
            );
          })}
        </div>
      )}
    </div>
  );
};

export default DraggableTerminal;
