from datetime import datetime, timedelta
from typing import Dict, Optional
import json
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class FeedEventLogger:
    def __init__(self, log_file: str = "feed_events.json"):
        self.log_file = Path("data") / log_file
        self.log_file.parent.mkdir(exist_ok=True)
        if not self.log_file.exists():
            self._initialize_log_file()
        self.events = []

    def _initialize_log_file(self):
        """Initialize an empty log file with proper structure."""
        with open(self.log_file, 'w') as f:
            json.dump({"events": []}, f, indent=4)

    def log_event(self, feed_type: str, volume: float, components: Dict[str, float],
                  operator: Optional[str] = None, notes: Optional[str] = None):
        """Log a feed event with timestamp and details."""
        event = {
            "timestamp": datetime.now().isoformat(),
            "feed_type": feed_type,
            "volume": volume,
            "components": components,
            "operator": operator,
            "notes": notes
        }

        try:
            with open(self.log_file, 'r') as f:
                log_data = json.load(f)
            
            log_data["events"].append(event)
            
            with open(self.log_file, 'w') as f:
                json.dump(log_data, f, indent=4)
                
            logger.info(f"Feed event logged successfully: {feed_type}")
        except Exception as e:
            logger.error(f"Error logging feed event: {e}")
        self.events.append(event)

    def get_events(self, start_time: Optional[str] = None, 
                  end_time: Optional[str] = None,
                  feed_type: Optional[str] = None) -> list:
        """Retrieve feed events with optional filtering."""
        try:
            with open(self.log_file, 'r') as f:
                log_data = json.load(f)
            
            events = log_data["events"]
            
            if start_time:
                events = [e for e in events if e["timestamp"] >= start_time]
            if end_time:
                events = [e for e in events if e["timestamp"] <= end_time]
            if feed_type:
                events = [e for e in events if e["feed_type"] == feed_type]
                
            return events
        except Exception as e:
            logger.error(f"Error retrieving feed events: {e}")
            return []

    def get_recent_events(self, hours: int = 24) -> list:
        """Get feed events from the last N hours."""
        cutoff = datetime.now() - timedelta(hours=hours)
        return [e for e in self.events if e['timestamp'] >= cutoff]
        
    def get_latest_feed_event(self):
        """Get the most recent feed event."""
        if not self.events:
            return None
        return max(self.events, key=lambda x: x['timestamp'])
