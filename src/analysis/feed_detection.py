import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import logging
from data.feed_events import FeedEventLogger

logger = logging.getLogger(__name__)

class FeedDetector:
    def __init__(self, 
                 weight_threshold: float = 0.05,  # 50g minimum weight change
                 time_window: int = 60,  # 60 seconds window
                 noise_filter: float = 0.02):  # 20g noise filter
        self.weight_threshold = weight_threshold
        self.time_window = time_window
        self.noise_filter = noise_filter
        self.feed_logger = FeedEventLogger()
        self.last_detection_time = None
        
    def detect_feed_events(self, data: pd.DataFrame) -> List[Dict]:
        """
        Detect feed events from weight data changes.
        
        Args:
            data: DataFrame with columns ['timestamp', 'reactor_weight', 'feed_bottle_weight']
            
        Returns:
            List of detected feed events
        """
        if data.empty:
            return []
            
        # Ensure data is sorted by timestamp
        data = data.sort_values('timestamp')
        
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
                
                # Determine feed type based on weight changes
                feed_type = self._determine_feed_type(volume)
                
                event = {
                    'timestamp': row['timestamp'],
                    'feed_type': feed_type,
                    'volume': volume / 1000,  # Convert to liters
                    'reactor_weight_change': row['reactor_weight_change'],
                    'feed_bottle_weight_change': row['feed_bottle_weight_change']
                }
                
                feed_events.append(event)
                self.last_detection_time = current_time
                
                # Log the detected event
                self._log_detected_event(event)
                
        return feed_events
    
    def _determine_feed_type(self, volume: float) -> str:
        """
        Determine feed type based on volume and historical data.
        This is a simple implementation - could be enhanced with machine learning.
        """
        # Get recent feed events
        recent_events = self.feed_logger.get_events(
            start_time=(datetime.now() - timedelta(hours=24)).isoformat()
        )
        
        if recent_events:
            # Use most common recent feed type
            feed_types = [event['feed_type'] for event in recent_events]
            return max(set(feed_types), key=feed_types.count)
        
        # Default to control feed if no recent history
        return 'control_feed'
    
    def _log_detected_event(self, event: Dict):
        """Log automatically detected feed event."""
        try:
            self.feed_logger.log_event(
                feed_type=event['feed_type'],
                volume=event['volume'],
                components={},  # Components will be filled from settings
                operator='AUTO_DETECT',
                notes=f"Automatically detected feed event. "
                      f"Reactor weight change: {event['reactor_weight_change']:.2f}g, "
                      f"Feed bottle change: {event['feed_bottle_weight_change']:.2f}g"
            )
            logger.info(f"Automatically detected and logged feed event: {event}")
        except Exception as e:
            logger.error(f"Error logging detected feed event: {e}")
