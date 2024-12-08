import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from ..core.feature import Feature

logger = logging.getLogger(__name__)

class FeedEvent:
    def __init__(self, feed_type: str, volume: float, timestamp: datetime):
        self.feed_type = feed_type
        self.volume = volume
        self.timestamp = timestamp
        self.metrics: Dict[str, float] = {}

class FeedTrackingFeature(Feature):
    def __init__(self):
        super().__init__("feed_tracking")
        self._feed_events: List[FeedEvent] = []
        self._initialize_if_enabled()
    
    def _initialize_if_enabled(self):
        """Initialize the feature if it's enabled in config."""
        if self.is_enabled:
            self.on_enable()
    
    def on_enable(self):
        """Initialize feed tracking when feature is enabled."""
        try:
            self._feed_events.clear()
            logger.info("Feed tracking feature enabled")
        except Exception as e:
            logger.error(f"Failed to enable feed tracking: {e}")
            self.disable()
    
    def on_disable(self):
        """Clean up when feature is disabled."""
        self._feed_events.clear()
        logger.info("Feed tracking feature disabled")
    
    def record_feed_event(self, feed_type: str, volume: float) -> Optional[FeedEvent]:
        """Record a new feed event."""
        if not self.is_enabled:
            logger.warning("Attempted to record feed event while feature is disabled")
            return None
            
        try:
            # Validate feed type exists in config
            feed_config = self.config.get('feed', {})
            if f"{feed_type}_feed" not in feed_config:
                raise ValueError(f"Unknown feed type: {feed_type}")
            
            # Validate volume against configuration
            max_rate = feed_config.get('maximum_rate', 2.0)
            if volume > max_rate:
                raise ValueError(f"Feed volume {volume} exceeds maximum rate {max_rate}")
            
            # Create and record event
            event = FeedEvent(feed_type, volume, datetime.now())
            self._feed_events.append(event)
            logger.info(f"Recorded {feed_type} feed event: {volume}L")
            return event
            
        except Exception as e:
            logger.error(f"Error recording feed event: {e}")
            return None
    
    def get_recent_events(self, hours: float = 1.0) -> List[FeedEvent]:
        """Get feed events from the last specified hours."""
        if not self.is_enabled:
            return []
            
        try:
            cutoff = datetime.now() - timedelta(hours=hours)
            return [event for event in self._feed_events if event.timestamp >= cutoff]
        except Exception as e:
            logger.error(f"Error retrieving recent events: {e}")
            return []
    
    def calculate_feed_statistics(self) -> Dict[str, Any]:
        """Calculate statistics for feed events."""
        if not self.is_enabled:
            return {}
            
        try:
            stats = {
                "total_control_volume": 0.0,
                "total_experimental_volume": 0.0,
                "feed_events_count": len(self._feed_events),
                "average_interval": 0.0
            }
            
            # Calculate statistics
            if self._feed_events:
                for event in self._feed_events:
                    if event.feed_type == "control":
                        stats["total_control_volume"] += event.volume
                    elif event.feed_type == "experimental":
                        stats["total_experimental_volume"] += event.volume
                
                # Calculate average interval
                if len(self._feed_events) > 1:
                    intervals = []
                    for i in range(1, len(self._feed_events)):
                        interval = (self._feed_events[i].timestamp - 
                                  self._feed_events[i-1].timestamp).total_seconds()
                        intervals.append(interval)
                    stats["average_interval"] = sum(intervals) / len(intervals)
            
            return stats
            
        except Exception as e:
            logger.error(f"Error calculating feed statistics: {e}")
            return {}
