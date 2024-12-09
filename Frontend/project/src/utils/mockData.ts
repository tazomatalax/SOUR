import { RealTimeMetrics } from '../types/system';

export function generateMockMetrics(): RealTimeMetrics {
  const now = Date.now();
  const sinValue = Math.sin(now / 10000); // Creates a smooth sine wave
  
  return {
    LB_MFC_1_SP: 0.5 + 0.1 * sinValue,
    LB_MFC_1_PV: 0.48 + 0.1 * sinValue + Math.random() * 0.02,
    Reactor_1_DO_Value_PPM: 800 + 100 * sinValue + Math.random() * 20,
    Reactor_1_DO_T_Value: 37 + Math.random() * 0.2,
    Reactor_1_PH_Value: 7.0 + 0.2 * sinValue + Math.random() * 0.1,
    Reactor_1_PH_T_Value: 37 + Math.random() * 0.2
  };
}