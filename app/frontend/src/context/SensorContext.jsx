import React, { createContext, useReducer, useMemo } from 'react';

export const SensorDataContext = createContext();
export const TerminalLogContext = createContext();
export const SensorDispatchContext = createContext();
export const HistoryDataContext = createContext();

const initialState = {
  isInitializing: true,
  latestData: {
    breathing: false,
    status: "not_detected",
    direction: "none",
    left_detected: false,
    left_distance: 0,
    left_confidence: 0,
    left_votes: 0,
    left_freq: 0,
    left_power: 0,
    right_detected: false,
    right_distance: 0,
    right_confidence: 0,
    right_votes: 0,
    right_freq: 0,
    right_power: 0,
    fft_conf: 0,
    dl_conf: 0,
    votes: 0,
    voting_window: 32,
    distance: 0,
    freq: 0,
    power: 0,
    entropy: 0,
    timestamp: Date.now()
  },
  history: [],
  terminalLines: [],
  wsConnected: false
};

const reducer = (state, action) => {
  switch (action.type) {
    case 'UPDATE_SENSOR': {
      const payload = action.payload;
      const newHistoryEntry = {
        timestamp: payload.timestamp,
        status: payload.status,
        left_distance: payload.left_distance,
        right_distance: payload.right_distance,
        left_confidence: payload.left_confidence,
        right_confidence: payload.right_confidence,
        left_votes: payload.left_votes,
        right_votes: payload.right_votes,
        direction: payload.direction,
      };
      
      const newHistory = [...state.history, newHistoryEntry];
      const trimmed = newHistory.length > 500
        ? newHistory.slice(-500)
        : newHistory;

      return {
        ...state,
        isInitializing: false,
        latestData: payload,
        history: trimmed
      };
    }
    case 'UPDATE_TERMINAL': {
      const newLineObj = { id: String(Date.now()) + String(Math.random()), text: action.payload.line };
      const newLines = [...state.terminalLines, newLineObj];
      // Use slice(-200) instead of .shift() to keep the reducer pure (no mutation)
      return { ...state, terminalLines: newLines.length > 200 ? newLines.slice(-200) : newLines };
    }
    case 'SET_WS_CONNECTED':
      return { ...state, wsConnected: action.payload };
    default:
      return state;
  }
};

export const SensorProvider = ({ children }) => {
  const [state, dispatch] = useReducer(reducer, initialState);

  const sensorData = useMemo(() => ({
    latestData: state.latestData,
    wsConnected: state.wsConnected,
    isInitializing: state.isInitializing
  }), [state.latestData, state.wsConnected, state.isInitializing]);

  const historyData = useMemo(() => state.history, [state.history]);

  const terminalData = useMemo(() => state.terminalLines, [state.terminalLines]);

  return (
    <SensorDispatchContext.Provider value={dispatch}>
      <SensorDataContext.Provider value={sensorData}>
        <HistoryDataContext.Provider value={historyData}>
          <TerminalLogContext.Provider value={terminalData}>
              {children}
          </TerminalLogContext.Provider>
        </HistoryDataContext.Provider>
      </SensorDataContext.Provider>
    </SensorDispatchContext.Provider>
  );
};
