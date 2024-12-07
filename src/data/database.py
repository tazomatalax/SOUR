import os
from typing import Dict, List, Optional
import pandas as pd
import pyodbc
from sqlalchemy import create_engine, text
import urllib
from pathlib import Path

class DatabaseConnection:
    def __init__(self):
        self.reactor_engine = self._create_reactor_engine()
        self.dashboard_engine = self._create_dashboard_engine()
        self.initialize_dashboard_database()
        
    def _create_reactor_engine(self):
        """Create SQLAlchemy engine for read-only Reactor database connection."""
        server = os.getenv('REACTOR_DB_SERVER')
        database = os.getenv('REACTOR_DB_NAME')
        username = os.getenv('REACTOR_DB_USER')
        password = os.getenv('REACTOR_DB_PASSWORD')
        
        params = urllib.parse.quote_plus(
            'DRIVER={SQL Server};'
            f'SERVER={server};'
            f'DATABASE={database};'
            f'UID={username};'
            f'PWD={password}'
        )
        
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
        
        try:
            with self.dashboard_engine.connect() as conn:
                conn.execute(feed_params_table)
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
