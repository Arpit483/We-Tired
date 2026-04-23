import { useEffect, useContext, useRef, useCallback } from 'react';
import { io } from 'socket.io-client';
import { SensorDispatchContext } from '../context/SensorContext';

/**
 * HIGH-05 fix: wrap dispatch in useCallback with [] deps so its reference never
 * changes, preventing the useEffect from re-running (and the socket from
 * disconnecting) on every context update at 10 Hz.
 *
 * The socket is created once and torn down only on true component unmount.
 */
export const useSocket = () => {
  const rawDispatch = useContext(SensorDispatchContext);
  const socketRef   = useRef(null);

  // Stable dispatch reference — never changes across renders
  const dispatch = useCallback(rawDispatch, []); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    // Only create the socket once
    if (!socketRef.current) {
      socketRef.current = io(window.location.origin, {
        reconnectionDelay: 3000,
        reconnection: true,
      });
    }

    const socket = socketRef.current;

    socket.on('connect_error', (err) => {
      console.error('Socket connect_error', err);
    });

    socket.on('connect', () => {
      dispatch({ type: 'SET_WS_CONNECTED', payload: true });
    });

    socket.on('disconnect', () => {
      dispatch({ type: 'SET_WS_CONNECTED', payload: false });
    });

    socket.on('sensor_update', (data) => {
      dispatch({ type: 'UPDATE_SENSOR', payload: data });
    });

    socket.on('terminal_update', (data) => {
      dispatch({ type: 'UPDATE_TERMINAL', payload: data });
    });

    // Cleanup runs only when the component truly unmounts ([] dep array)
    return () => {
      socket.off('connect_error');
      socket.off('connect');
      socket.off('disconnect');
      socket.off('sensor_update');
      socket.off('terminal_update');
      socket.disconnect();
      socketRef.current = null;
    };
  }, []); // eslint-disable-line react-hooks/exhaustive-deps
};
