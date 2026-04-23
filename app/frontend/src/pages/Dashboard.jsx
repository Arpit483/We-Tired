import React, { useContext } from 'react';
import { SensorDataContext } from '../context/SensorContext';
import SensorPanel from '../components/SensorPanel';
import DirectionRing from '../components/DirectionRing';
import TerminalLog from '../components/TerminalLog';

const SkeletonLoader = () => (
  <div className="flex-1 flex flex-col items-center justify-center bg-[#0a0a0a] h-full">
    <div className="flex flex-col items-center gap-3">
      <span className="material-symbols-outlined text-[40px] text-zinc-700 animate-spin">sync</span>
      <span className="font-mono text-[11px] text-zinc-600 tracking-widest uppercase">INITIALIZING TELEMETRY...</span>
    </div>
  </div>
);

const Dashboard = () => {
  const state = useContext(SensorDataContext);
  const { latestData, isInitializing } = state;

  if (isInitializing) return <SkeletonLoader />;

  return (
    <div className="flex flex-col h-full" style={{ minHeight: 0 }}>
      {/* Three-column sensor grid */}
      <div className="flex-1 grid grid-cols-1 md:grid-cols-12 overflow-hidden" style={{ minHeight: 0 }}>
        {/* Left sensor */}
        <SensorPanel
          side="left"
          name="S1"
          colorPrefix="neon-lime"
          data={{
            distance: latestData.left_distance,
            confidence: latestData.left_confidence,
            freq: latestData.left_freq,
            power: latestData.left_power,
            votes: latestData.left_votes,
            detected: latestData.left_detected,
            voting_window: latestData.voting_window,
          }}
        />

        {/* Center radar */}
        <DirectionRing
          direction={latestData.direction}
          distance={latestData.distance}
          freq={latestData.freq}
          votes={latestData.votes}
        />

        {/* Right sensor */}
        <SensorPanel
          side="right"
          name="S2"
          colorPrefix="neon-coral"
          data={{
            distance: latestData.right_distance,
            confidence: latestData.right_confidence,
            freq: latestData.right_freq,
            power: latestData.right_power,
            votes: latestData.right_votes,
            detected: latestData.right_detected,
            voting_window: latestData.voting_window,
          }}
        />
      </div>

      {/* Draggable terminal — sits at the bottom by default */}
      <TerminalLog />
    </div>
  );
};

export default Dashboard;
