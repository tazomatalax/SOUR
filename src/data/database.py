import os
from typing import Dict, List, Optional
import pandas as pd
import pyodbc
from dotenv import load_dotenv
import logging
from sqlalchemy import create_engine, text
import urllib
from pathlib import Path

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class DatabaseConnection:
    def __init__(self, required: bool = False):
        """Initialize database connections using environment variables.
        
        Args:
            required (bool): If True, raises exceptions on connection failure.
                           If False, continues with limited functionality.
        """
        self.is_connected = False
        self.required = required
        
        # MS SQL Server connection string components
        self.server = os.getenv('MSSQL_SERVER', 'localhost')
        self.database = os.getenv('MSSQL_DATABASE', 'SOUR')
        self.username = os.getenv('MSSQL_USERNAME', 'sa')
        self.password = os.getenv('MSSQL_PASSWORD', '')
        self.driver = os.getenv('MSSQL_DRIVER', '{ODBC Driver 17 for SQL Server}')
        self.port = os.getenv('MSSQL_PORT', '1433')
        self.trusted_connection = os.getenv('MSSQL_TRUSTED_CONNECTION', 'yes')
        
        try:
            self.conn_str = self._build_connection_string()
            self.reactor_engine = self._create_reactor_engine()
            self.dashboard_engine = self._create_dashboard_engine()
            self.initialize_dashboard_database()
            self._test_connection()
            self.is_connected = True
            logger.info("Database connection established successfully")
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            if self.required:
                raise
            logger.warning("Continuing with limited functionality (no database connection)")
        
    def _build_connection_string(self) -> str:
        """Build the connection string using environment variables."""
        conn_str = (
            f"DRIVER={self.driver};"
            f"SERVER={self.server},{self.port};"
            f"DATABASE={self.database};"
        )
        
        # Use trusted connection if specified, otherwise use username/password
        if self.trusted_connection.lower() == 'yes':
            conn_str += "Trusted_Connection=yes;"
        else:
            conn_str += f"UID={self.username};PWD={self.password};"
        
        return conn_str
        
    def _test_connection(self):
        """Test the database connection and log the result."""
        try:
            with pyodbc.connect(self.conn_str) as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT @@version")
                    version = cursor.fetchone()[0]
                    logger.info(f"Successfully connected to MS SQL Server: {version}")
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise

    def _create_reactor_engine(self):
        """Create SQLAlchemy engine for read-only Reactor database connection."""
        params = urllib.parse.quote_plus(self.conn_str)
        
        return create_engine(f'mssql+pyodbc:///?odbc_connect={params}')

    def _create_dashboard_engine(self):
        """Create SQLAlchemy engine for local SQLite dashboard database."""
        # Create data directory if it doesn't exist
        data_dir = Path('data')
        data_dir.mkdir(exist_ok=True)
        
        # SQLite database will be stored in data/dashboard.db
        db_path = data_dir / 'dashboard.db'
        return create_engine(f'sqlite:///{db_path}')

    def initialize_dashboard_database(self):
        """Initialize dashboard database tables if they don't exist."""
        feed_params_table = text("""
            CREATE TABLE IF NOT EXISTS feed_parameters (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                feed_type VARCHAR(50) NOT NULL,
                toc_value FLOAT,
                glucose_concentration FLOAT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        process_params_table = text("""
            CREATE TABLE IF NOT EXISTS process_parameters (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tss_value FLOAT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        try:
            with self.dashboard_engine.connect() as conn:
                conn.execute(feed_params_table)
                conn.execute(process_params_table)
                conn.commit()
                print("Dashboard database initialized successfully")
        except Exception as e:
            print(f"Error initializing dashboard database: {e}")

    def get_latest_data(self, minutes: int = 5) -> pd.DataFrame:
        """Fetch the latest data from the reactor database."""
        query = text("""
            SELECT 
                DateTime,
                -- MFC1 values
                LB_MFC_1_SP,
                LB_MFC_1_PV,
                -- Reactor 1 DO
                Reactor_1_DO_Value_PPM,
                Reactor_1_DO_T_Value,
                -- Reactor 1 pH
                Reactor_1_PH_Value,
                Reactor_1_PH_T_Value,
                -- Weights
                R1_Weight_Bal,
                R2_Weight_Bal,
                -- Pump 1 settings
                LB_Perastaltic_P_1,
                R1_Perastaltic_1_Time,
                R1_Perastaltic_1_Time_off,
                -- Speed and torque
                Reactor_1_Speed_RPM,
                Reactor_1_Torque_Real
            FROM ReactorData
            WHERE DateTime >= DATEADD(minute, -:minutes, GETDATE())
            ORDER BY DateTime ASC
        """)
        
        try:
            with self.reactor_engine.connect() as conn:
                df = pd.read_sql_query(query, conn, params={'minutes': minutes})
            return df
        except Exception as e:
            print(f"Error fetching data: {e}")
            return pd.DataFrame()

    def get_current_values(self) -> Dict:
        """Get the most recent values for all monitored parameters."""
        query = text("""
            SELECT TOP 1
                -- MFC1 values
                LB_MFC_1_SP,
                LB_MFC_1_PV,
                -- Reactor 1 DO
                Reactor_1_DO_Value_PPM,
                Reactor_1_DO_T_Value,
                -- Reactor 1 pH
                Reactor_1_PH_Value,
                Reactor_1_PH_T_Value,
                -- Weights
                R1_Weight_Bal,
                R2_Weight_Bal,
                -- Pump 1 settings
                LB_Perastaltic_P_1,
                R1_Perastaltic_1_Time,
                R1_Perastaltic_1_Time_off,
                -- Speed and torque
                Reactor_1_Speed_RPM,
                Reactor_1_Torque_Real
            FROM ReactorData
            ORDER BY DateTime DESC
        """)
        
        try:
            with self.reactor_engine.connect() as conn:
                result = conn.execute(query).fetchone()
                if result:
                    return {
                        'mfc1': {
                            'sp': result.LB_MFC_1_SP,
                            'pv': result.LB_MFC_1_PV
                        },
                        'do': {
                            'value': result.Reactor_1_DO_Value_PPM,
                            'temp': result.Reactor_1_DO_T_Value
                        },
                        'ph': {
                            'value': result.Reactor_1_PH_Value,
                            'temp': result.Reactor_1_PH_T_Value
                        },
                        'weights': {
                            'r1': result.R1_Weight_Bal,
                            'r2': result.R2_Weight_Bal
                        },
                        'pump': {
                            'status': result.LB_Perastaltic_P_1,
                            'time_on': result.R1_Perastaltic_1_Time,
                            'time_off': result.R1_Perastaltic_1_Time_off
                        },
                        'operation': {
                            'speed': result.Reactor_1_Speed_RPM,
                            'torque': result.Reactor_1_Torque_Real
                        }
                    }
                return {}
        except Exception as e:
            print(f"Error fetching current values: {e}")
            return {}

    def save_feed_parameters(self, feed_type: str, toc: float = None, glucose_conc: float = None) -> bool:
        """Save feed parameters to the dashboard database."""
        query = text("""
            INSERT INTO feed_parameters (feed_type, toc_value, glucose_concentration)
            VALUES (:feed_type, :toc, :glucose_conc)
        """)
        
        try:
            with self.dashboard_engine.connect() as conn:
                conn.execute(query, 
                           {"feed_type": feed_type, 
                            "toc": toc, 
                            "glucose_conc": glucose_conc})
                conn.commit()
                print("Feed parameters saved successfully")
        except Exception as e:
            print(f"Error saving feed parameters: {e}")

    def get_feed_parameters(self) -> Dict:
        """Get the current feed parameters."""
        query = text("""
            SELECT feed_type, toc_value, glucose_concentration, timestamp
            FROM feed_parameters
            ORDER BY timestamp DESC
            LIMIT 1
        """)
        
        try:
            with self.dashboard_engine.connect() as conn:
                result = conn.execute(query).fetchone()
                if result:
                    return {
                        'feed_type': result[0],
                        'toc_value': result[1],
                        'glucose_concentration': result[2],
                        'timestamp': result[3]
                    }
        except Exception as e:
            print(f"Error fetching feed parameters: {e}")
        
        return {}

    def get_historical_data(self, start_time: str, end_time: str) -> pd.DataFrame:
        """Fetch historical data between specified timestamps.
        
        Args:
            start_time: Start timestamp in ISO format
            end_time: End timestamp in ISO format
            
        Returns:
            DataFrame containing the historical sensor data
        """
        query = text("""
            SELECT timestamp, do_value, ph_value, temperature, 
                   agitation, reactor_weight, feed_bottle_weight
            FROM sensor_data
            WHERE timestamp BETWEEN :start_time AND :end_time
            ORDER BY timestamp ASC
        """)
        
        with self.reactor_engine.connect() as conn:
            df = pd.read_sql_query(
                query, 
                conn, 
                params={'start_time': start_time, 'end_time': end_time}
            )
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            return df
