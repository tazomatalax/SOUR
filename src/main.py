import os
import sys
import logging
import signal
from typing import Optional
from dotenv import load_dotenv
from data.database import DatabaseConnection
from analysis.metrics import BioreactorMetrics
from visualization.dashboard import BioreactorDashboard

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
        self.db: Optional[DatabaseConnection] = None
        self.metrics: Optional[BioreactorMetrics] = None
        self.dashboard: Optional[BioreactorDashboard] = None
        self._setup_signal_handlers()

    def _setup_signal_handlers(self):
        """Set up handlers for graceful shutdown on SIGINT and SIGTERM."""
        signal.signal(signal.SIGINT, self._handle_shutdown)
        signal.signal(signal.SIGTERM, self._handle_shutdown)

    def _handle_shutdown(self, signum, frame):
        """Handle graceful shutdown of components."""
        logger.info("Shutdown signal received. Starting graceful shutdown...")
        self.cleanup()
        sys.exit(0)

    def initialize(self):
        """Initialize all system components with error handling."""
        try:
            # Load environment variables
            load_dotenv()
            logger.info("Environment variables loaded successfully")

            # Initialize database connection (non-required mode)
            self.db = DatabaseConnection(required=False)

            # Initialize metrics analyzer with conditional database dependency
            self.metrics = BioreactorMetrics(self.db if self.db.is_connected else None)
            logger.info("Metrics analyzer initialized")

            # Initialize dashboard with conditional database dependency
            self.dashboard = BioreactorDashboard(self.db if self.db.is_connected else None)
            logger.info("Dashboard initialized")

            return True

        except Exception as e:
            logger.error(f"Initialization failed: {e}")
            self.cleanup()
            return False

    def cleanup(self):
        """Cleanup system resources."""
        logger.info("Starting cleanup process...")
        try:
            if self.db and self.db.is_connected:
                # Add cleanup for database if needed
                pass
            if self.metrics:
                # Add cleanup for metrics if needed
                pass
            if self.dashboard:
                # Add cleanup for dashboard if needed
                pass
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

    def run(self):
        """Run the bioreactor monitoring system."""
        try:
            logger.info("Starting bioreactor monitoring system...")
            self.dashboard.run_server(debug=False)
        except Exception as e:
            logger.error(f"Error running dashboard: {str(e)}")
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
