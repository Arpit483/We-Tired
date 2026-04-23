import React, { useContext } from 'react';
import { SensorDataContext } from '../context/SensorContext';
import SensorPanel from '../components/SensorPanel';
import DirectionRing from '../components/DirectionRing';
import TerminalLog from '../components/TerminalLog';

const SkeletonLoader = () => (
  <div className="flex-1 p-4 md:p-gutter flex flex-col items-center justify-center bg-[#0a0a0a]">
    <div className="flex flex-col items-center gap-4">
      <span className="material-symbols-outlined text-[48px] text-zinc-600 animate-spin">sync</span>
      <span className="font-mono text-xs text-zinc-500 tracking-widest uppercase">INITIALIZING TELEMETRY...</span>
    </div>
  </div>
);

const Dashboard = () => {
  const state = useContext(SensorDataContext);
  const { latestData, isInitializing } = state;

  if (isInitializing) {
    return <SkeletonLoader />;
  }

  return (
    <main className="flex-1 flex flex-col bg-[#0A0A0A] overflow-y-auto overflow-x-hidden min-h-full">
      <div className="flex flex-col md:grid md:grid-cols-12 flex-1">
        
        {/* Center Panel (CYAN) */}
        {/* We place it first in the JSX but order-1 / order-2 classes in DirectionRing will handle mobile/desktop ordering */}
        <DirectionRing 
          direction={latestData.direction}
          distance={latestData.distance}
          freq={latestData.freq}
          votes={latestData.votes}
        />

        {/* Left Panel (S1 LIME) */}
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
            voting_window: latestData.voting_window
          }} 
        />
        
        {/* Right Panel (S2 CORAL) */}
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
            voting_window: latestData.voting_window
          }} 
        />
      </div>
      
      {/* Bottom Terminal Strip */}
      <TerminalLog />
    </main>
  );
};

export default Dashboard;
