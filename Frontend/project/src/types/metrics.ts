export interface Metrics {
  drop_rate: number;
  recovery_time: number;
  our: number;
  sour: number;
  do_saturation: number;
  ph: number;
  temperature: number;
  timestamp: string;
}

export interface FeedSettings {
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
  experimental_feed: {
    toc_concentration: number;
    default_volume: number;
    components: {
      carbon_source: number;
      nitrogen_source: number;
      minerals: number;
    };
  };
}

export interface FeedEvent {
  id: string;
  timestamp: string;
  feed_type: 'control' | 'experimental';
  volume: number;
  notes?: string;
}