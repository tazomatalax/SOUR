import os
from typing import Dict, List, Optional
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

class DatabaseConnection:
    def __init__(self):
        load_dotenv()
        self.engine = self._create_db_engine()
        
    def _create_db_engine(self):
        """Create SQLAlchemy engine from environment variables."""
        db_type = os.getenv('DB_TYPE', 'sqlite')  # Default to SQLite if not specified
        
        if db_type == 'sqlite':
            # Use SQLite as default/fallback
            db_path = os.getenv('DB_PATH', 'bioreactor.db')
            return create_engine(f'sqlite:///{db_path}')
        else:
            # PostgreSQL or other database types
            db_params = {
                'host': os.getenv('DB_HOST'),
                'database': os.getenv('DB_NAME'),
                'user': os.getenv('DB_USER'),
                'password': os.getenv('DB_PASSWORD')
            }
            
            if db_type == 'postgresql':
                connection_string = f"postgresql://{db_params['user']}:{db_params['password']}@{db_params['host']}/{db_params['database']}"
            else:
                raise ValueError(f"Unsupported database type: {db_type}")
                
            return create_engine(connection_string)
    
    def initialize_database(self):
        """Initialize database tables if they don't exist."""
        feed_params_table = text("""
            IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[feed_parameters]') AND type in (N'U'))
            BEGIN
                CREATE TABLE feed_parameters (
                    id INT IDENTITY(1,1) PRIMARY KEY,
                    feed_type VARCHAR(50) NOT NULL,
                    toc_value FLOAT,
                    glucose_concentration FLOAT,
                    timestamp DATETIME DEFAULT GETDATE()
                )
            END
        """)
        
        try:
            with self.engine.connect() as conn:
                conn.execute(feed_params_table)
                conn.commit()
                print("Database initialized successfully")
        except Exception as e:
            print(f"Error initializing database: {e}")
    
    def get_latest_data(self, minutes: int = 5) -> pd.DataFrame:
        """Fetch the latest data from the database."""
        query = text("""
            SELECT 
                DateTime,
                LB_MFC_1_SP,
                LB_MFC_1_PV,
                Reactor_1_DO_Value_PPM,
                Reactor_1_DO_T_Value,
                Reactor_1_PH_Value,
                Reactor_1_PH_T_Value,
                R1_Weight_Bal,
                LB_Perastaltic_P_1,
                R1_Perastaltic_1_Time,
                R1_Perastaltic_1_Time_off
            FROM process_data
            WHERE DateTime >= DATEADD(minute, -:minutes, GETDATE())
            ORDER BY DateTime ASC
        """)
        
        try:
            with self.engine.connect() as conn:
                df = pd.read_sql_query(query, conn, params={'minutes': minutes})
            return df
        except Exception as e:
            print(f"Error fetching data: {e}")
            return pd.DataFrame()

    def get_current_values(self) -> Dict:
        """Get the most recent values for all monitored parameters."""
        query = text("""
            SELECT TOP 1
                LB_MFC_1_SP,
                LB_MFC_1_PV,
                Reactor_1_DO_Value_PPM,
                Reactor_1_DO_T_Value,
                Reactor_1_PH_Value,
                Reactor_1_PH_T_Value,
                R1_Weight_Bal,
                LB_Perastaltic_P_1,
                R1_Perastaltic_1_Time,
                R1_Perastaltic_1_Time_off
            FROM process_data
            ORDER BY DateTime DESC
        """)
        
        try:
            with self.engine.connect() as conn:
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
                        'weight': result.R1_Weight_Bal,
                        'pump': {
                            'status': result.LB_Perastaltic_P_1,
                            'time_on': result.R1_Perastaltic_1_Time,
                            'time_off': result.R1_Perastaltic_1_Time_off
                        }
                    }
                return {}
        except Exception as e:
            print(f"Error fetching current values: {e}")
            return {}

    def save_feed_parameters(self, feed_type: str, toc: float = None, glucose_conc: float = None) -> bool:
        """Save feed parameters to the database."""
        query = text("""
            INSERT INTO feed_parameters (feed_type, toc_value, glucose_concentration, timestamp)
            VALUES (:feed_type, :toc, :glucose_conc, GETDATE())
        """)
        
        try:
            with self.engine.connect() as conn:
                conn.execute(query, {
                    'feed_type': feed_type,
                    'toc': toc,
                    'glucose_conc': glucose_conc
                })
                conn.commit()
                return True
        except Exception as e:
            print(f"Error saving feed parameters: {e}")
            return False

    def get_feed_parameters(self) -> Dict:
        """Get the current feed parameters."""
        query = text("""
            SELECT TOP 1
                feed_type,
                toc_value,
                glucose_concentration
            FROM feed_parameters
            ORDER BY timestamp DESC
        """)
        
        try:
            with self.engine.connect() as conn:
                result = conn.execute(query).fetchone()
                if result:
                    return {
                        'feed_type': result.feed_type,
                        'toc': result.toc_value,
                        'glucose_conc': result.glucose_concentration
                    }
                return {}
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
        
        with self.engine.connect() as conn:
            df = pd.read_sql_query(
                query, 
                conn, 
                params={'start_time': start_time, 'end_time': end_time}
            )
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            return df
