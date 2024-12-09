import { useEffect, useCallback } from 'react';
import { mockWebSocketManager } from '../utils/mockWebSocket';
import { useStore } from '../store/useStore';
import { RealTimeMetrics } from '../types/system';
import { Metrics } from '../types/metrics';

const calculateMetrics = (data: RealTimeMetrics): Metrics => {
  return {
    do_saturation: (data.Reactor_1_DO_Value_PPM / 1000) * 100,
    drop_rate: data.LB_MFC_1_PV,
    recovery_time: Math.abs(10 * Math.sin(Date.now() / 5000)), // Simulated recovery time
    our: Math.abs(0.5 + 0.1 * Math.sin(Date.now() / 7000)), // Simulated OUR
    sour: Math.abs(0.2 + 0.05 * Math.sin(Date.now() / 9000)), // Simulated SOUR
    ph: data.Reactor_1_PH_Value,
    temperature: data.Reactor_1_DO_T_Value,
    timestamp: new Date().toISOString()
  };
};

export const useWebSocket = () => {
  const { setMetrics } = useStore();

  const handleData = useCallback((data: RealTimeMetrics) => {
    const calculatedMetrics = calculateMetrics(data);
    setMetrics(calculatedMetrics);
  }, [setMetrics]);

  useEffect(() => {
    mockWebSocketManager.connect();
    const unsubscribe = mockWebSocketManager.subscribe(handleData);

    return () => {
      unsubscribe();
      mockWebSocketManager.disconnect();
    };
  }, [handleData]);
};