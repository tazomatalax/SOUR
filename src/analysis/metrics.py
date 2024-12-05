from typing import Dict, List, Tuple, Optional
import numpy as np
import pandas as pd
from scipy import stats
from dataclasses import dataclass

@dataclass
class FeedEvent:
    timestamp: pd.Timestamp
    feed_type: str
    volume: float
    composition: Dict[str, float]

class BioreactorMetrics:
    def __init__(self):
        self.feed_events: List[FeedEvent] = []
        
    def add_feed_event(self, event: FeedEvent):
        """Record a new feed event."""
        self.feed_events.append(event)
        
    def calculate_do_drop_rate(self, data: pd.DataFrame, 
                             event_time: pd.Timestamp,
                             window_size: int = 300) -> Tuple[float, float]:
        """Calculate DO drop rate after a feed event.
        
        Args:
            data: DataFrame with DO measurements
            event_time: Timestamp of feed event
            window_size: Analysis window in seconds
            
        Returns:
            Tuple of (drop_rate, r_squared)
        """
        # Get data window after feed event
        mask = (data['timestamp'] >= event_time) & \
               (data['timestamp'] <= event_time + pd.Timedelta(seconds=window_size))
        window_data = data[mask]
        
        if len(window_data) < 10:  # Minimum points for reliable calculation
            return 0.0, 0.0
            
        # Calculate time in seconds from event
        time_delta = (window_data['timestamp'] - event_time).dt.total_seconds()
        
        # Linear regression on DO values
        slope, intercept, r_value, _, _ = stats.linregress(
            time_delta, window_data['do_value']
        )
        
        return slope, r_value**2
        
    def calculate_recovery_time(self, data: pd.DataFrame,
                              event_time: pd.Timestamp,
                              recovery_threshold: float = 0.95) -> Optional[float]:
        """Calculate time until DO recovers to threshold of initial value.
        
        Args:
            data: DataFrame with DO measurements
            event_time: Timestamp of feed event
            recovery_threshold: Fraction of initial DO to consider as recovered
            
        Returns:
            Recovery time in seconds, or None if not recovered
        """
        initial_do = data[data['timestamp'] <= event_time]['do_value'].iloc[-1]
        recovery_value = initial_do * recovery_threshold
        
        # Get data after event
        post_event = data[data['timestamp'] >= event_time]
        
        # Find first point where DO exceeds recovery threshold
        recovered = post_event[post_event['do_value'] >= recovery_value]
        
        if len(recovered) == 0:
            return None
            
        recovery_time = (recovered.iloc[0]['timestamp'] - event_time).total_seconds()
        return recovery_time
        
    def calculate_carbon_oxygen_ratio(self, feed_event: FeedEvent,
                                    do_consumption: float) -> float:
        """Calculate molar C:O ratio for a feed event.
        
        Args:
            feed_event: Feed event details
            do_consumption: Total oxygen consumed (mol)
            
        Returns:
            Molar carbon to oxygen ratio
        """
        if feed_event.feed_type == 'control':
            # Calculate carbon content from glucose
            glucose_mol = feed_event.volume * feed_event.composition['glucose'] / 180.156  # g/mol
            carbon_mol = glucose_mol * 6  # 6 carbons per glucose
        else:
            # Calculate from TOC
            toc_g = feed_event.volume * feed_event.composition['toc']
            carbon_mol = toc_g / 12.01  # g/mol for carbon
            
        return carbon_mol / do_consumption if do_consumption > 0 else 0.0
