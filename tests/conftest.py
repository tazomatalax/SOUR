import pytest
import os
import yaml
from pathlib import Path

@pytest.fixture
def test_config():
    """Create a test configuration."""
    return {
        'features': {
            'data_collection': True,
            'real_time_metrics': True,
            'feed_tracking': True,
            'visualization': True
        },
        'database': {
            'host': 'localhost',
            'port': 5432,
            'required': False
        },
        'metrics': {
            'do_threshold': 20.0,
            'recovery_threshold': 95.0
        },
        'feed': {
            'control_feed': {
                'glucose_concentration': 500,
                'toc_concentration': 200
            },
            'experimental_feed': {
                'toc_concentration': 18
            }
        }
    }

@pytest.fixture
def mock_db_connection(mocker):
    """Create a mock database connection."""
    mock = mocker.Mock()
    mock.is_connected = True
    mock.query.return_value = []
    return mock
