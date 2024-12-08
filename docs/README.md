# SOUR (Specific Oxygen Uptake Rate) Bioreactor Monitoring System

## Overview

SOUR is a sophisticated real-time monitoring and analysis system designed for bioreactor experiments that compare different nutrient feed types through dissolved oxygen (DO) response analysis. The system provides comprehensive tools for tracking, analyzing, and visualizing key bioreactor metrics with a focus on oxygen utilization patterns.

## Core Functionality

### 1. Real-Time Monitoring

- **Process Parameters**
  - Dissolved Oxygen (DO) levels in mg/L
  - pH values and temperature
  - Mass Flow Controller (MFC) settings and readings
  - Reactor and feed bottle weights
  - Peristaltic pump operation times

### 2. Feed Event Management

- **Automated Feed Detection**
  - Weight-based detection of feed events
  - Classification of feed types (control vs. experimental)
  - Logging of feed volumes and timestamps

- **Manual Feed Logging**
  - User interface for manual feed event recording
  - Configurable feed compositions
  - Operator notes and annotations

### 3. Oxygen Utilization Analysis

- **Key Metrics Calculation**
  - DO Drop Rate (mg/L/s)
  - DO Recovery Time (s)
  - Oxygen Uptake Rate (OUR) in mg O₂/L/h
  - Specific Oxygen Uptake Rate (sOUR) in mg O₂/g/h
  - DO Saturation levels

- **Advanced Analytics**
  - Real-time trend analysis
  - Statistical validation (R² calculations)
  - Biomass-specific normalization
  - Historical data comparison

### 4. Scientific Data Export

- **Data Formatting**
  - LaTeX and Markdown export options
  - Publication-ready tables and figures
  - Time series visualization
  - Scientific annotations with metadata

### 5. AI-Powered Insights

- **Automated Analysis**
  - Pattern recognition in oxygen utilization
  - Metabolic activity assessment
  - Process efficiency evaluation
  - Optimization recommendations

## Technical Details

### System Components

1. **Data Acquisition**
   - SQL database integration for sensor data
   - Real-time data polling and processing
   - Configurable sampling rates

2. **Process Control**
   - Feed event triggering
   - Pump control interface
   - Safety monitoring and alerts

3. **Analysis Engine**
   - Real-time metric calculations
   - Statistical analysis tools
   - Machine learning integration
   - Data validation and filtering

4. **User Interface**
   - Web-based dashboard
   - Interactive plotting
   - Configuration management
   - Event logging interface

### Key Parameters

- **DO Analysis**
  - Stability Window: 300s default
  - Stability Threshold: 0.1 mg/L
  - Analysis Window: 300s default
  - kLa (Mass Transfer Coefficient): Configurable

- **Feed Detection**
  - Weight Threshold: 50g minimum
  - Time Window: 60s
  - Noise Filter: 20g

### Data Management

- **Storage**
  - SQL database for time-series data
  - JSON configuration files
  - Scientific annotations in structured format
  - Automated logging and backup

- **Export Formats**
  - LaTeX for academic publications
  - Markdown for documentation
  - CSV for raw data
  - Plotly figures for visualization

## Configuration

The system uses environment variables for key settings:
- Database credentials
- Analysis parameters (kLa, stability windows, etc.)
- AI model configuration
- Export preferences

Feed settings are managed through a JSON configuration file:
- Control feed composition
- Experimental feed parameters
- Default volumes and concentrations

## Dependencies

- Python 3.x
- Dash for web interface
- Pandas for data analysis
- NumPy for numerical computations
- SQLAlchemy for database management
- Plotly for visualization
- Ollama for AI analysis

## Usage

1. Set up environment variables in `.env` file
2. Configure feed settings in `feed_settings.json`
3. Start the monitoring system:
   ```bash
   python src/main.py
   ```
4. Access the dashboard through web browser
5. Monitor experiments and analyze results
6. Export data for publication

## Safety Features

- Automated data validation
- Error logging and monitoring
- Graceful shutdown handling
- Database connection resilience
- Input validation and sanitization

## Future Enhancements

1. Advanced machine learning models for process optimization
2. Enhanced visualization capabilities
3. Additional export format support
4. Extended analysis parameters
5. Integration with other bioreactor systems
