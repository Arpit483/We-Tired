import React, { useMemo, useDeferredValue } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, ReferenceArea, ResponsiveContainer } from 'recharts';

const BreathingChart = ({ data }) => {
  const deferredData = useDeferredValue(data);

  const chartData = useMemo(() => {
    return deferredData.map(d => {
      const date = new Date(d.timestamp);
      return {
        time: `${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}`,
        s1Conf: d.left_confidence || 0,
        s2Conf: d.right_confidence || 0,
      };
    });
  }, [data]);

  return (
    <div className="p-4 relative h-64 flex flex-col justify-between w-full">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={chartData} margin={{ top: 5, right: 5, left: -20, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#36343a" vertical={false} />
          <XAxis dataKey="time" stroke="#948e9c" tick={{ fill: '#948e9c', fontSize: 10 }} />
          <YAxis stroke="#948e9c" domain={[0, 1]} tick={{ fill: '#948e9c', fontSize: 10 }} />
          <ReferenceArea y1={0.15} y2={0.67} fill="#AAFF00" fillOpacity={0.05} strokeOpacity={0.2} stroke="#AAFF00" />
          <Line type="monotone" dataKey="s1Conf" stroke="#AAFF00" strokeWidth={2} dot={false} isAnimationActive={false} />
          <Line type="monotone" dataKey="s2Conf" stroke="#FF5C5C" strokeWidth={1.5} strokeDasharray="4 2" dot={false} isAnimationActive={false} />
        </LineChart>
      </ResponsiveContainer>
      <div className="absolute top-1/3 right-10 font-code-sm text-code-sm text-[#AAFF00]/50">[ BREATHING_ZONE ]</div>
    </div>
  );
};

export default React.memo(BreathingChart, (prev, next) => prev.data.length === next.data.length);
