import { Features } from '../types/system';

class FeatureRegistry {
  private static instance: FeatureRegistry;
  private features: Features = {
    data_collection: true,
    real_time_metrics: true,
    visualization: true,
    feed_tracking: true,
    export: true,
    ai_insights: false
  };

  private constructor() {}

  static getInstance(): FeatureRegistry {
    if (!FeatureRegistry.instance) {
      FeatureRegistry.instance = new FeatureRegistry();
    }
    return FeatureRegistry.instance;
  }

  isEnabled(feature: keyof Features): boolean {
    return this.features[feature];
  }

  setFeature(feature: keyof Features, enabled: boolean): void {
    this.features[feature] = enabled;
  }

  getAllFeatures(): Features {
    return { ...this.features };
  }
}

export const featureRegistry = FeatureRegistry.getInstance();