from typing import Dict, List, Tuple, Optional
import numpy as np
import pandas as pd
from scipy import stats
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class FeedEvent:
    timestamp: pd.Timestamp
    feed_type: str
    volume: float
    composition: Dict[str, float]

class BioreactorMetrics:
    def __init__(self, 
                kla: float = None,  # Mass transfer coefficient (h⁻¹)
                stability_window: int = 300,  # Window for stability analysis (seconds)
                stability_threshold: float = 0.1,  # Maximum DO variation for stability (mg/L)
                analysis_window: int = 300):  # Default 5-minute window for analysis
        self.feed_events: List[FeedEvent] = []
        self.kla = kla
        self.stability_window = stability_window
        self.stability_threshold = stability_threshold
        self.analysis_window = analysis_window
        self.do_saturation = None  # Will be calculated from data
        
    def add_feed_event(self, event: FeedEvent):
        """Record a new feed event."""
        self.feed_events.append(event)
        
    def calculate_do_drop_rate(self, data: pd.DataFrame, 
                             event_time: pd.Timestamp,
                             window_size: Optional[int] = None) -> Tuple[float, float]:
        """Calculate DO drop rate after a feed event.
        
        Args:
            data: DataFrame with DO measurements
            event_time: Timestamp of feed event
            window_size: Analysis window in seconds (optional)
            
        Returns:
            Tuple of (drop_rate mg/L/s, r_squared)
        """
        window_size = window_size or self.analysis_window
        
        # Get data window after feed event
        mask = (data['timestamp'] >= event_time) & \
               (data['timestamp'] <= event_time + pd.Timedelta(seconds=window_size))
        window_data = data[mask]
        
        if len(window_data) < 10:  # Minimum points for reliable calculation
            logger.warning(f"Insufficient data points for DO drop rate calculation at {event_time}")
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
            logger.warning(f"DO recovery not detected for event at {event_time}")
            return None
            
        recovery_time = (recovered.iloc[0]['timestamp'] - event_time).total_seconds()
        return recovery_time
    
    def calculate_our(self, data: pd.DataFrame,
                     event_time: pd.Timestamp,
                     window_size: Optional[int] = None) -> Optional[float]:
        """Calculate Oxygen Uptake Rate (OUR) after a feed event.
        
        OUR = -ΔDO/Δt · kLa
        
        Args:
            data: DataFrame with DO measurements
            event_time: Timestamp of feed event
            window_size: Analysis window in seconds (optional)
            
        Returns:
            OUR in mg O₂/L/h, or None if calculation not possible
        """
        if self.kla is None:
            logger.error("kLa value not provided, cannot calculate OUR")
            return None
            
        # Calculate DO drop rate
        drop_rate, r_squared = self.calculate_do_drop_rate(data, event_time, window_size)
        
        if r_squared < 0.8:  # Minimum R² threshold for reliable calculation
            logger.warning(f"Poor linear fit (R²={r_squared:.2f}) for OUR calculation at {event_time}")
            return None
        
        # Convert drop rate from mg/L/s to mg/L/h and calculate OUR
        our = -drop_rate * 3600 * self.kla
        return our
    
    def calculate_sour(self, data: pd.DataFrame,
                      event_time: pd.Timestamp,
                      biomass_concentration: float,
                      window_size: Optional[int] = None) -> Optional[float]:
        """Calculate Specific Oxygen Uptake Rate (sOUR) after a feed event.
        
        sOUR = OUR / biomass_concentration
        
        Args:
            data: DataFrame with DO measurements
            event_time: Timestamp of feed event
            biomass_concentration: Biomass concentration in g/L
            window_size: Analysis window in seconds (optional)
            
        Returns:
            sOUR in mg O₂/g biomass/h, or None if calculation not possible
        """
        our = self.calculate_our(data, event_time, window_size)
        
        if our is None:
            return None
            
        if biomass_concentration <= 0:
            logger.error(f"Invalid biomass concentration: {biomass_concentration}")
            return None
            
        return our / biomass_concentration
    
    def calculate_do_response_metrics(self, data: pd.DataFrame,
                                    event_time: pd.Timestamp,
                                    biomass_concentration: Optional[float] = None) -> Dict:
        """Calculate all DO response metrics for a feed event.
        
        Args:
            data: DataFrame with DO measurements
            event_time: Timestamp of feed event
            biomass_concentration: Optional biomass concentration for sOUR calculation
            
        Returns:
            Dictionary containing all calculated metrics
        """
        drop_rate, r_squared = self.calculate_do_drop_rate(data, event_time)
        recovery_time = self.calculate_recovery_time(data, event_time)
        our = self.calculate_our(data, event_time)
        sour = None
        if biomass_concentration is not None:
            sour = self.calculate_sour(data, event_time, biomass_concentration)
            
        return {
            'timestamp': event_time,
            'do_drop_rate': drop_rate,
            'do_drop_r_squared': r_squared,
            'recovery_time': recovery_time,
            'our': our,
            'sour': sour,
            'kla': self.kla,
            'do_saturation': self.do_saturation
        }
        
    def calculate_do_saturation(self, data: pd.DataFrame) -> float:
        """Calculate DO saturation from stable periods in the data.
        
        Args:
            data: DataFrame with 'timestamp' and 'do_value' columns
            
        Returns:
            Estimated DO saturation value (mg/L)
        """
        if len(data) < 2:
            logger.warning("Insufficient data points for DO saturation calculation")
            return None
            
        # Ensure data is sorted by timestamp
        data = data.sort_values('timestamp')
        
        # Calculate time differences and rolling statistics
        data['time_diff'] = (data['timestamp'] - data['timestamp'].shift()).dt.total_seconds()
        rolling_std = data['do_value'].rolling(
            window=self.stability_window // int(data['time_diff'].median()),
            min_periods=3
        ).std()
        
        # Find stable periods where DO variation is below threshold
        stable_periods = data[rolling_std <= self.stability_threshold]
        
        if len(stable_periods) < 1:
            logger.warning("No stable periods found for DO saturation calculation")
            return None
            
        # Use median DO value during stable periods as saturation
        do_saturation = stable_periods['do_value'].median()
        logger.info(f"Calculated DO saturation: {do_saturation:.2f} mg/L")
        
        return do_saturation
        
    def update_do_saturation(self, data: pd.DataFrame):
        """Update DO saturation value based on new data."""
        new_saturation = self.calculate_do_saturation(data)
        if new_saturation is not None:
            self.do_saturation = new_saturation
