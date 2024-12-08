import pytest
from datetime import datetime, timedelta
from src.features.data_collection import DataCollectionFeature
from src.features.metrics import MetricsFeature
from src.features.feed_tracking import FeedTrackingFeature, FeedEvent
from src.features.visualization import VisualizationFeature

class TestDataCollectionFeature:
    def test_initialization(self, test_config, mock_db_connection):
        feature = DataCollectionFeature()
        assert feature.is_enabled
        assert feature.feature_name == "data_collection"
    
    def test_data_collection(self, test_config, mock_db_connection):
        feature = DataCollectionFeature()
        data = feature.collect_data()
        assert isinstance(data, dict)
        assert "timestamp" in data
        assert "measurements" in data

    def test_disable_feature(self, test_config):
        feature = DataCollectionFeature()
        feature.disable()
        assert not feature.is_enabled
        data = feature.collect_data()
        assert data == {}

class TestMetricsFeature:
    def test_initialization(self, test_config):
        feature = MetricsFeature()
        assert feature.is_enabled
        assert feature.feature_name == "real_time_metrics"
    
    def test_do_metrics_calculation(self, test_config):
        feature = MetricsFeature()
        metrics = feature.calculate_do_metrics({
            "timestamp": datetime.now(),
            "do_level": 50.0
        })
        assert isinstance(metrics, dict)
        assert "do_drop_rate" in metrics
        assert "recovery_time" in metrics
    
    def test_feed_metrics_calculation(self, test_config):
        feature = MetricsFeature()
        metrics = feature.calculate_feed_metrics({
            "feed_type": "control",
            "volume": 0.1
        })
        assert isinstance(metrics, dict)
        assert "carbon_consumption_rate" in metrics
        assert "oxygen_consumption_rate" in metrics

class TestFeedTrackingFeature:
    def test_initialization(self, test_config):
        feature = FeedTrackingFeature()
        assert feature.is_enabled
        assert feature.feature_name == "feed_tracking"
    
    def test_record_feed_event(self, test_config):
        feature = FeedTrackingFeature()
        event = feature.record_feed_event("control", 0.1)
        assert isinstance(event, FeedEvent)
        assert event.feed_type == "control"
        assert event.volume == 0.1
    
    def test_get_recent_events(self, test_config):
        feature = FeedTrackingFeature()
        # Add some test events
        feature.record_feed_event("control", 0.1)
        feature.record_feed_event("experimental", 0.2)
        
        events = feature.get_recent_events(hours=1)
        assert len(events) == 2
        assert all(isinstance(e, FeedEvent) for e in events)
    
    def test_calculate_feed_statistics(self, test_config):
        feature = FeedTrackingFeature()
        # Add some test events
        feature.record_feed_event("control", 0.1)
        feature.record_feed_event("experimental", 0.2)
        
        stats = feature.calculate_feed_statistics()
        assert isinstance(stats, dict)
        assert stats["feed_events_count"] == 2
        assert stats["total_control_volume"] == 0.1
        assert stats["total_experimental_volume"] == 0.2

class TestVisualizationFeature:
    def test_initialization(self, test_config):
        feature = VisualizationFeature()
        assert feature.is_enabled
        assert feature.feature_name == "visualization"
    
    def test_create_do_figure(self, test_config):
        feature = VisualizationFeature()
        figure = feature._create_do_figure()
        assert isinstance(figure, dict)
        assert "data" in figure
        assert "layout" in figure
    
    def test_create_feed_figure(self, test_config):
        feature = VisualizationFeature()
        figure = feature._create_feed_figure()
        assert isinstance(figure, dict)
        assert "data" in figure
        assert "layout" in figure
    
    def test_create_metrics_display(self, test_config):
        feature = VisualizationFeature()
        display = feature._create_metrics_display()
        assert isinstance(display, list)
        # Should be empty without metrics feature
        assert len(display) == 0
