import { useEffect, useContext, useRef } from 'react';
import { io } from 'socket.io-client';
import { SensorDispatchContext } from '../context/SensorContext';

export const useSocket = () => {
  const dispatch = useContext(SensorDispatchContext);
  const socketRef = useRef(null);

  useEffect(() => {
    // connect to current host
    if (!socketRef.current) {
      socketRef.current = io('http://192.168.137.19:5050', {
        reconnectionDelay: 3000,
        reconnection: true
      });
    }

    socketRef.current.on('connect_error', (err) => {
      console.error("Socket connect_error", err);
    });

    socketRef.current.on('connect', () => {
      dispatch({ type: 'SET_WS_CONNECTED', payload: true });
    });

    socketRef.current.on('disconnect', () => {
      dispatch({ type: 'SET_WS_CONNECTED', payload: false });
    });

    socketRef.current.on('sensor_update', (data) => {
      dispatch({ type: 'UPDATE_SENSOR', payload: data });
    });

    socketRef.current.on('terminal_update', (data) => {
      dispatch({ type: 'UPDATE_TERMINAL', payload: data });
    });

    return () => {
      if (socketRef.current) {
        socketRef.current.disconnect();
        socketRef.current = null;
      }
    };
  }, [dispatch]);
};
