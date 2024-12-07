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

            # Initialize database connection
            self.db = DatabaseConnection()
            logger.info("Database connection established")

            # Initialize metrics analyzer
            self.metrics = BioreactorMetrics()
            logger.info("Metrics analyzer initialized")

            # Initialize dashboard
            self.dashboard = BioreactorDashboard()
            logger.info("Dashboard initialized")

        except Exception as e:
            logger.error(f"Initialization failed: {str(e)}")
            self.cleanup()
            raise

    def cleanup(self):
        """Clean up system resources."""
        logger.info("Starting cleanup process...")
        
        if self.db:
            try:
                self.db.close()
                logger.info("Database connection closed")
            except Exception as e:
                logger.error(f"Error closing database connection: {str(e)}")

        if self.dashboard:
            try:
                self.dashboard.shutdown()
                logger.info("Dashboard shutdown complete")
            except Exception as e:
                logger.error(f"Error shutting down dashboard: {str(e)}")

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
        system.initialize()
        system.run()
    except Exception as e:
        logger.critical(f"Fatal error in main program: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
