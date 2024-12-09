export interface Features {
  data_collection: boolean;
  real_time_metrics: boolean;
  visualization: boolean;
  feed_tracking: boolean;
  export: boolean;
  ai_insights: boolean;
}

export interface SystemConfig {
  visualization: {
    update_interval: number;
    plot_history: number;
    dashboard_port: number;
  };
  feed: {
    default_rate: number;
    minimum_interval: number;
    maximum_rate: number;
    control_feed: {
      glucose_concentration: number;
      toc_concentration: number;
      default_volume: number;
      components: {
        glucose: number;
        yeast_extract: number;
        minerals: number;
      };
    };
  };
}

export interface RealTimeMetrics {
  LB_MFC_1_SP: number;
  LB_MFC_1_PV: number;
  Reactor_1_DO_Value_PPM: number;
  Reactor_1_DO_T_Value: number;
  Reactor_1_PH_Value: number;
  Reactor_1_PH_T_Value: number;
}

export const METRIC_RANGES = {
  DO_VALUE: { min: 0, max: 100 },
  PH_VALUE: { min: 0, max: 14 },
  TEMPERATURE: { min: 0, max: 50 }
} as const;

export const FEED_CONSTRAINTS = {
  MIN_VOLUME: 0.01,
  MAX_VOLUME: 2.0,
  VOLUME_STEP: 0.1
} as const;