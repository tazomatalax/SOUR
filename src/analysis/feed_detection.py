import numpy as np
import pandas as pd
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class FeedDetector:
    def __init__(self, 
                 weight_threshold: float = 0.005,  # 5g minimum weight change
                 time_window: int = 60,  # 60 seconds window
                 noise_filter: float = 0.002):  # 2g noise filter
        self.weight_threshold = weight_threshold
        self.time_window = time_window
        self.noise_filter = noise_filter
        self.last_detection_time = None
        
    def detect_feed_events(self, data: pd.DataFrame, feed_logger=None) -> List[Dict]:
        """Detect feed events from weight data changes.
        
        Args:
            data: DataFrame with columns ['timestamp', 'R1_Weight_Bal', 'R2_Weight_Bal']
            feed_logger: Optional FeedEventLogger instance to record events
            
        Returns:
            List of detected feed events
        """
        if data.empty:
            return []
            
        # Ensure timestamp column is datetime
        if 'timestamp' not in data.columns:
            logger.error("No timestamp column in data")
            return []
            
        # Ensure data is sorted by timestamp
        data = data.sort_values('timestamp')
        
        # Rename weight columns for consistency
        data = data.rename(columns={
            'R1_Weight_Bal': 'reactor_weight',
            'R2_Weight_Bal': 'feed_bottle_weight'
        })
        
        # Calculate weight changes
        data['reactor_weight_change'] = data['reactor_weight'].diff()
        data['feed_bottle_weight_change'] = data['feed_bottle_weight'].diff()
        
        # Apply noise filter
        data.loc[abs(data['reactor_weight_change']) < self.noise_filter, 'reactor_weight_change'] = 0
        data.loc[abs(data['feed_bottle_weight_change']) < self.noise_filter, 'feed_bottle_weight_change'] = 0
        
        feed_events = []
        
        # Find significant weight changes
        significant_changes = data[
            (abs(data['reactor_weight_change']) > self.weight_threshold) &
            (abs(data['feed_bottle_weight_change']) > self.weight_threshold)
        ]
        
        for _, row in significant_changes.iterrows():
            # Skip if too close to last detection
            current_time = pd.to_datetime(row['timestamp'])
            if (self.last_detection_time and 
                (current_time - self.last_detection_time).total_seconds() < self.time_window):
                continue
                
            # Verify opposite weight changes (reactor up, feed bottle down)
            if row['reactor_weight_change'] > 0 and row['feed_bottle_weight_change'] < 0:
                volume = abs(row['feed_bottle_weight_change'])  # Assuming 1g = 1mL
                
                event = {
                    'timestamp': current_time,
                    'feed_type': 'auto_detected',
                    'volume': volume / 1000,  # Convert to liters
                    'reactor_weight_change': row['reactor_weight_change'],
                    'feed_bottle_weight_change': row['feed_bottle_weight_change']
                }
                
                feed_events.append(event)
                self.last_detection_time = current_time
                
                # Log the detected event if logger provided
                if feed_logger:
                    feed_logger.log_event(
                        feed_type='auto_detected',
                        volume=event['volume'],
                        components={},
                        operator='AUTO_DETECT',
                        notes=f"Automatically detected feed event. "
                              f"Reactor weight change: {event['reactor_weight_change']:.2f}g, "
                              f"Feed bottle change: {event['feed_bottle_weight_change']:.2f}g"
                    )
                
        return feed_events
