import { useState, useEffect, useRef } from 'react';

export const useSystemHealth = () => {
  const [health, setHealth] = useState({
    cpu_percent: 0,
    ram_percent: 0,
    cpu_temp: 0,
    s1_connected: false,
    s2_connected: false,
    uptime: 0
  });

  const timerRef = useRef(null);

  useEffect(() => {
    let active = true;

    const fetchHealth = async () => {
      try {
        const res = await fetch('http://192.168.137.19:5050/api/system');
        if (res.ok && active) {
          const data = await res.json();
          setHealth(data);
        }
      } catch (e) {
        console.error("Health fetch error", e);
      }
      
      if (active) {
        timerRef.current = setTimeout(fetchHealth, 2000);
      }
    };

    fetchHealth();

    return () => {
      active = false;
      if (timerRef.current) {
        clearTimeout(timerRef.current);
      }
    };
  }, []);

  return health;
};
