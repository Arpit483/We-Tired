import React from 'react';

const DetectionTable = ({ data }) => {
  return (
    <div className="bento-border-dim bg-[#141414] overflow-x-auto">
      <div className="border-b border-surface-variant p-sm flex justify-between items-center bg-surface-container">
        <div className="font-label-caps text-label-caps text-on-surface">RAW_STREAM_DATA</div>
        <button className="font-label-caps text-label-caps text-cyan border border-cyan px-2 py-1 hover:bg-cyan/10 transition-colors flex items-center gap-1">
          <span className="material-symbols-outlined text-[14px]">download</span> EXPORT
        </button>
      </div>
      <table className="w-full text-left font-body-reg text-body-reg whitespace-nowrap">
        <thead className="bg-[#1A1A1A] font-label-caps text-label-caps text-outline border-b border-surface-variant">
          <tr>
            <th className="p-3 font-normal">TIMESTAMP</th>
            <th className="p-3 font-normal">S1 DIST (cm)</th>
            <th className="p-3 font-normal">S2 DIST (cm)</th>
            <th className="p-3 font-normal">S1 CONF</th>
            <th className="p-3 font-normal">S2 CONF</th>
            <th className="p-3 font-normal">S1 VOTES</th>
            <th className="p-3 font-normal">S2 VOTES</th>
            <th className="p-3 font-normal">STATUS</th>
            <th className="p-3 font-normal">DIRECTION</th>
          </tr>
        </thead>
        <tbody className="text-on-surface">
          {data.slice().reverse().slice(0, 50).map((row, i) => {
            const date = new Date(row.timestamp);
            const timeStr = `${date.toISOString().substring(0, 10)} ${date.toISOString().substring(11, 23)}`;
            
            let statusColor = 'text-outline';
            let statusText = '○ IDLE';
            if (row.status === 'detected') {
              statusColor = 'text-[#AAFF00]';
              statusText = '● TRACKING';
            } else if (row.status === 'high_chance') {
              statusColor = 'text-amber';
              statusText = '● ACQUIRING';
            } else if (row.left_detected && !row.right_detected) {
              statusColor = 'text-[#FF5C5C]';
              statusText = '○ LOST_S2';
            }

            return (
              <tr key={i} className={`${i % 2 === 1 ? 'bg-[#1A1A1A]' : ''} border-b border-surface-variant/50 hover:bg-surface-variant/20 transition-colors`}>
                <td className="p-3 font-code-sm text-code-sm">{timeStr}</td>
                <td className="p-3">{row.left_distance?.toFixed(2) || '--'}</td>
                <td className="p-3 text-outline">{row.right_distance?.toFixed(2) || '--'}</td>
                <td className="p-3 text-[#AAFF00]">{row.left_confidence?.toFixed(2) || '--'}</td>
                <td className="p-3 text-outline">{row.right_confidence?.toFixed(2) || '--'}</td>
                <td className="p-3">{row.left_votes || '0'}</td>
                <td className="p-3 text-outline">{row.right_votes || '0'}</td>
                <td className="p-3"><span className={statusColor}>{statusText}</span></td>
                <td className="p-3">{row.direction || '--'}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
};

export default React.memo(DetectionTable, (prev, next) => prev.data.length === next.data.length);
