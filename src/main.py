import os
from dotenv import load_dotenv
from data.database import DatabaseConnection
from analysis.metrics import BioreactorMetrics
from visualization.dashboard import BioreactorDashboard

def main():
    # Load environment variables
    load_dotenv()
    
    # Initialize components
    db = DatabaseConnection()
    metrics = BioreactorMetrics()
    dashboard = BioreactorDashboard()
    
    # Start the dashboard
    dashboard.run_server(debug=True)

if __name__ == "__main__":
    main()
