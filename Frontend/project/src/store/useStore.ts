import { create } from 'zustand';
import type { Metrics, FeedSettings } from '../types/metrics';
import type { Features } from '../types/system';
import { featureRegistry } from '../utils/featureRegistry';

interface Store {
  metrics: Metrics | null;
  feedSettings: FeedSettings | null;
  isDarkMode: boolean;
  features: Features;
  setMetrics: (metrics: Metrics) => void;
  setFeedSettings: (settings: FeedSettings) => void;
  toggleDarkMode: () => void;
  updateFeatures: (features: Partial<Features>) => void;
}

export const useStore = create<Store>((set) => ({
  metrics: null,
  feedSettings: null,
  isDarkMode: false,
  features: featureRegistry.getAllFeatures(),
  setMetrics: (metrics) => set({ metrics }),
  setFeedSettings: (settings) => set({ feedSettings: settings }),
  toggleDarkMode: () => set((state) => ({ isDarkMode: !state.isDarkMode })),
  updateFeatures: (features) => 
    set((state) => {
      Object.entries(features).forEach(([key, value]) => {
        featureRegistry.setFeature(key as keyof Features, value);
      });
      return { features: featureRegistry.getAllFeatures() };
    })
}));