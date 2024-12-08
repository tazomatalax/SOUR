import os
import sys
import logging
import signal
import yaml
from typing import Optional
from dotenv import load_dotenv
from core.feature_registry import FeatureRegistry
from features.data_collection import DataCollectionFeature
from features.metrics import MetricsFeature
from features.feed_tracking import FeedTrackingFeature
from features.visualization import VisualizationFeature

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('bioreactor.log')
    ]
)
logger = logging.getLogger(__name__)

class BioreactorSystem:
    def __init__(self):
        self.registry = FeatureRegistry()
        self._setup_signal_handlers()
        self._register_features()

    def _setup_signal_handlers(self):
        """Set up handlers for graceful shutdown on SIGINT and SIGTERM."""
        signal.signal(signal.SIGINT, self._handle_shutdown)
        signal.signal(signal.SIGTERM, self._handle_shutdown)

    def _handle_shutdown(self, signum, frame):
        """Handle graceful shutdown of components."""
        logger.info("Shutdown signal received. Starting graceful shutdown...")
        self.cleanup()
        sys.exit(0)

    def _register_features(self):
        """Register all available features."""
        self.registry.register_feature_class("data_collection", DataCollectionFeature)
        self.registry.register_feature_class("metrics", MetricsFeature)
        self.registry.register_feature_class("feed_tracking", FeedTrackingFeature)
        self.registry.register_feature_class("visualization", VisualizationFeature)

    def initialize(self):
        """Initialize all system components with error handling."""
        try:
            # Load environment variables
            load_dotenv()
            logger.info("Environment variables loaded successfully")

            # Initialize features in dependency order
            data_collection = self.registry.initialize_feature("data_collection")
            if not data_collection:
                logger.error("Failed to initialize data collection")
                return False

            metrics = self.registry.initialize_feature("metrics", 
                                                     data_collection=data_collection)
            if not metrics:
                logger.error("Failed to initialize metrics")
                return False

            feed_tracking = self.registry.initialize_feature("feed_tracking")
            if not feed_tracking:
                logger.error("Failed to initialize feed tracking")
                return False

            visualization = self.registry.initialize_feature("visualization",
                                                          data_collection=data_collection,
                                                          metrics=metrics,
                                                          feed_tracking=feed_tracking)
            if not visualization:
                logger.error("Failed to initialize visualization")
                return False

            logger.info("All features initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Initialization failed: {e}")
            self.cleanup()
            return False

    def cleanup(self):
        """Cleanup system resources."""
        logger.info("Starting cleanup process...")
        try:
            self.registry.cleanup()
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

    def run(self):
        """Run the bioreactor monitoring system."""
        try:
            logger.info("Starting bioreactor monitoring system...")
            visualization = self.registry.get_feature("visualization")
            if visualization and visualization.is_enabled:
                visualization.run_server(debug=False)
            else:
                logger.error("Visualization feature not available")
                raise RuntimeError("Cannot start system without visualization")
        except Exception as e:
            logger.error(f"Error running system: {str(e)}")
            self.cleanup()
            raise

def main():
    system = BioreactorSystem()
    try:
        if system.initialize():
            system.run()
    except Exception as e:
        logger.critical(f"Fatal error in main program: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
