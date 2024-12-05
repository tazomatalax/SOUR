# Bioreactor Experiment Monitoring System

This software system monitors and analyzes bioreactor experiments comparing different nutrient feed types through dissolved oxygen (DO) response analysis.

## Features

- Real-time data visualization from SQL/Grafana sources
- Live computation of key metrics (DO drop rates, recovery times)
- Feed event tracking and analysis
- Carbon-to-oxygen consumption calculations
- Comparative analysis tools
- Data export capabilities

## Setup

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment variables:
Create a `.env` file with your database credentials:
```
DB_HOST=your_host
DB_NAME=your_database
DB_USER=your_username
DB_PASSWORD=your_password
```

4. Run the application:
```bash
python src/main.py
```

## Project Structure

- `src/`
  - `data/` - Data handling and database connections
  - `analysis/` - Metric calculations and analysis
  - `visualization/` - Plotting and dashboard components
  - `utils/` - Helper functions and utilities
  - `config/` - Configuration files
  - `main.py` - Application entry point

## Usage

1. Start the application using the command above
2. Access the web interface at http://localhost:8050
3. Configure feed parameters in the settings panel
4. Monitor real-time data and analysis
