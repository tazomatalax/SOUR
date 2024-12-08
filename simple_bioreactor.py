import os
import pandas as pd
import pyodbc
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
import urllib
from typing import Dict, Optional
import logging
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimpleBioreactor:
    def __init__(self):
        """Initialize the simplified bioreactor monitoring system."""
        # Load environment variables
        load_dotenv()
        
        # Database connection parameters
        self.server = os.getenv('MSSQL_SERVER', 'localhost')
        self.database = os.getenv('MSSQL_DATABASE', 'dbreactor')
        self.username = os.getenv('MSSQL_USERNAME', 'dbreactor')
        self.password = os.getenv('MSSQL_PASSWORD', '')
        self.driver = os.getenv('MSSQL_DRIVER', '{ODBC Driver 17 for SQL Server}')
        self.port = os.getenv('MSSQL_PORT', '1433')
        
        # Analysis parameters
        self.stability_window = 300  # 5 minutes for stability analysis
        self.stability_threshold = 0.1  # mg/L
        self.analysis_window = 300  # 5 minutes for analysis
        
        # Initialize database connection
        self.engine = self._create_database_connection()
    
    def _create_database_connection(self):
        """Create database connection using SQLAlchemy."""
        try:
            conn_str = (
                f"DRIVER={self.driver};"
                f"SERVER={self.server},{self.port};"
                f"DATABASE={self.database};"
                f"UID={self.username};PWD={self.password};"
            )
            params = urllib.parse.quote_plus(conn_str)
            engine = create_engine(f'mssql+pyodbc:///?odbc_connect={params}')
            
            # Test connection
            with engine.connect() as conn:
                conn.execute(text("SELECT @@version"))
            logger.info("Database connection established successfully")
            return engine
            
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            raise
    
    def get_current_values(self) -> Dict:
        """Get the most recent values for all monitored parameters."""
        query = text("""
            SELECT TOP 1
                DateTime,
                Reactor_1_DO_Value_PPM as do_value,
                Reactor_1_DO_T_Value as do_temp,
                Reactor_1_PH_Value as ph_value,
                Reactor_1_PH_T_Value as ph_temp,
                R1_Weight_Bal as reactor_weight,
                Reactor_1_Speed_RPM as speed,
                Reactor_1_Torque_Real as torque
            FROM ReactorData
            ORDER BY DateTime DESC
        """)
        
        try:
            with self.engine.connect() as conn:
                result = conn.execute(query).fetchone()
                if result:
                    return {
                        'timestamp': result.DateTime,
                        'do': {
                            'value': result.do_value,
                            'temp': result.do_temp
                        },
                        'ph': {
                            'value': result.ph_value,
                            'temp': result.ph_temp
                        },
                        'weight': result.reactor_weight,
                        'speed': result.speed,
                        'torque': result.torque
                    }
                return {}
        except Exception as e:
            logger.error(f"Error fetching current values: {e}")
            return {}
    
    def get_historical_data(self, minutes: int = 60) -> pd.DataFrame:
        """Get historical data for the specified time window."""
        query = text("""
            SELECT 
                DateTime,
                Reactor_1_DO_Value_PPM as do_value,
                Reactor_1_DO_T_Value as do_temp,
                Reactor_1_PH_Value as ph_value,
                Reactor_1_PH_T_Value as ph_temp,
                R1_Weight_Bal as reactor_weight,
                Reactor_1_Speed_RPM as speed,
                Reactor_1_Torque_Real as torque
            FROM ReactorData
            WHERE DateTime >= DATEADD(minute, -:minutes, GETDATE())
            ORDER BY DateTime ASC
        """)
        
        try:
            with self.engine.connect() as conn:
                df = pd.read_sql_query(query, conn, params={'minutes': minutes})
                return df
        except Exception as e:
            logger.error(f"Error fetching historical data: {e}")
            return pd.DataFrame()
    
    def calculate_do_metrics(self, data: pd.DataFrame) -> Dict:
        """Calculate DO-related metrics from the provided data."""
        try:
            if data.empty:
                return {}
            
            # Calculate DO drop rate (mg/L/s)
            do_values = data['do_value']
            time_diff = (data['DateTime'].max() - data['DateTime'].min()).total_seconds()
            do_drop = do_values.max() - do_values.min()
            do_drop_rate = abs(do_drop / time_diff) if time_diff > 0 else 0
            
            # Calculate average DO
            avg_do = do_values.mean()
            
            # Calculate DO stability
            do_std = do_values.std()
            is_stable = do_std <= self.stability_threshold if not pd.isna(do_std) else False
            
            return {
                'average_do': avg_do,
                'do_drop_rate': do_drop_rate,
                'do_stability': is_stable,
                'do_std': do_std
            }
            
        except Exception as e:
            logger.error(f"Error calculating DO metrics: {e}")
            return {}

def main():
    """Main function to demonstrate the simplified bioreactor monitoring."""
    try:
        # Initialize the bioreactor system
        bioreactor = SimpleBioreactor()
        
        # Get current values
        current_data = bioreactor.get_current_values()
        print("\nCurrent Values:")
        print(f"DO: {current_data.get('do', {}).get('value', 'N/A')} mg/L")
        print(f"pH: {current_data.get('ph', {}).get('value', 'N/A')}")
        print(f"Temperature: {current_data.get('do', {}).get('temp', 'N/A')}°C")
        
        # Get historical data and calculate metrics
        historical_data = bioreactor.get_historical_data(minutes=30)
        if not historical_data.empty:
            metrics = bioreactor.calculate_do_metrics(historical_data)
            print("\nCalculated Metrics:")
            print(f"Average DO: {metrics.get('average_do', 'N/A'):.2f} mg/L")
            print(f"DO Drop Rate: {metrics.get('do_drop_rate', 'N/A'):.3f} mg/L/s")
            print(f"DO Stability: {'Stable' if metrics.get('do_stability', False) else 'Unstable'}")
            print(f"DO Standard Deviation: {metrics.get('do_std', 'N/A'):.3f} mg/L")
        
    except Exception as e:
        logger.error(f"Error in main function: {e}")

if __name__ == "__main__":
    main()
