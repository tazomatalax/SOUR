from typing import Dict, List, Optional
import dash
from dash import dcc, html
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State, ALL
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import json
import jsonschema
from pathlib import Path
import logging
from datetime import datetime
from data.feed_events import FeedEventLogger
from analysis.feed_detection import FeedDetector
from analysis.metrics import BioreactorMetrics
from data.database import DatabaseConnection
from analysis.scientific_export import ScientificDataExporter, ScientificAnnotation
from analysis.ai_insights import OllamaAnalyzer, MetricInsight
import os

logger = logging.getLogger(__name__)

class BioreactorDashboard:
    def __init__(self, db: Optional[DatabaseConnection] = None):
        self.app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
        self.settings_file = Path("feed_settings.json")
        self.settings = self.load_settings()
        self.feed_logger = FeedEventLogger()
        self.feed_detector = FeedDetector()
        self.metrics = BioreactorMetrics(
            db=db,
            kla=float(os.getenv('KLA_DEFAULT', 10.0)),
            stability_window=int(os.getenv('STABILITY_WINDOW', 300)),
            stability_threshold=float(os.getenv('STABILITY_THRESHOLD', 0.1)),
            analysis_window=int(os.getenv('ANALYSIS_WINDOW', 300))
        )
        self.db = db
        self.scientific_exporter = ScientificDataExporter()
        self.ai_analyzer = OllamaAnalyzer()  # Will use env variables for configuration
        self.latest_metrics = {
            "drop_rate": 0,
            "recovery_time": 0,
            "our": 0,
            "sour": 0
        }
        self.setup_layout()
        self.setup_callbacks()
        
    def load_settings(self) -> Dict:
        """Load settings from JSON file or create with defaults."""
        schema_path = Path(__file__).parent.parent / "schemas" / "feed_settings_schema.json"
        with open(schema_path, 'r') as f:
            schema = json.load(f)
            
        default_settings = {
            "control_feed": {
                "glucose_concentration": 500.0,
                "toc_concentration": 200.0,
                "default_volume": 0.1,
                "components": {
                    "glucose": 500.0,
                    "yeast_extract": 10.0,
                    "minerals": 5.0
                }
            },
            "experimental_feed": {
                "toc_concentration": 200.0,
                "default_volume": 0.1,
                "components": {
                    "carbon_source": 200.0,
                    "nitrogen_source": 20.0,
                    "minerals": 5.0
                }
            }
        }
        
        try:
            if self.settings_file.exists():
                with open(self.settings_file, 'r') as f:
                    settings = json.load(f)
                    jsonschema.validate(instance=settings, schema=schema)
                    return settings
            return default_settings
        except jsonschema.exceptions.ValidationError as e:
            logger.error(f"Settings validation error: {e}")
            return default_settings
        except Exception as e:
            logger.error(f"Error loading settings: {e}")
            return default_settings
        
    def save_settings(self):
        """Save current settings to JSON file."""
        with open(self.settings_file, 'w') as f:
            json.dump(self.settings, f, indent=4)
    
    def setup_layout(self):
        """Create the dashboard layout."""
        self.app.layout = dbc.Container([
            # Add interval component for periodic updates
            dcc.Interval(
                id='interval-component',
                interval=10000,
                n_intervals=0
            ),
            dbc.Tabs([
                # Main Monitoring Tab
                dbc.Tab([
                    dbc.Row([
                        dbc.Col(html.H1("Bioreactor Monitoring System"), width=12)
                    ]),
                    # Feed Configuration Section
                    dbc.Row([
                        dbc.Col([
                            dbc.Card([
                                dbc.CardHeader("Quick Feed Actions"),
                                dbc.CardBody([
                                    html.Div([
                                        html.Label("Feed Type"),
                                        dbc.Select(
                                            id="feed-type-select",
                                            options=[
                                                {"label": "Control Feed", "value": "control"},
                                                {"label": "Experimental Feed", "value": "experimental"}
                                            ],
                                            className="mb-3"
                                        ),
                                        dbc.Input(
                                            id="feed-volume",
                                            type="number",
                                            placeholder="Feed Volume (L)",
                                            className="mb-3"
                                        ),
                                        dbc.Input(
                                            id="operator-name",
                                            type="text",
                                            placeholder="Operator Name",
                                            className="mb-3"
                                        ),
                                        dbc.Textarea(
                                            id="feed-notes",
                                            placeholder="Feed Notes",
                                            className="mb-3"
                                        ),
                                        dbc.Button(
                                            "Add Feed Event",
                                            id="add-feed-btn",
                                            color="primary",
                                            className="mt-2"
                                        ),
                                        html.Div(id="feed-status", className="mt-2")
                                    ])
                                ])
                            ])
                        ], width=3),
                        
                        # Current Metrics Display
                        dbc.Col([
                            dbc.Card([
                                dbc.CardHeader("Current Process Values"),
                                dbc.CardBody(id="current-metrics")
                            ]),
                            # Add Oxygen Utilization Metrics Card
                            dbc.Card([
                                dbc.CardHeader("Oxygen Utilization Metrics"),
                                dbc.CardBody([
                                    dbc.Row([
                                        dbc.Col([
                                            html.H6("DO Saturation"),
                                            html.P(id="do-saturation", className="lead")
                                        ], width=6),
                                        dbc.Col([
                                            html.H6("DO Drop Rate"),
                                            html.P(id="do-drop-rate", className="lead")
                                        ], width=6)
                                    ]),
                                    dbc.Row([
                                        dbc.Col([
                                            html.H6("DO Recovery Time"),
                                            html.P(id="do-recovery-time", className="lead")
                                        ], width=6),
                                        dbc.Col([
                                            html.H6("Oxygen Uptake Rate (OUR)"),
                                            html.P(id="our-value", className="lead")
                                        ], width=6)
                                    ]),
                                    dbc.Row([
                                        dbc.Col([
                                            html.H6("Specific OUR (sOUR)"),
                                            html.P(id="sour-value", className="lead")
                                        ], width=12)
                                    ])
                                ])
                            ], className="mt-3")
                        ], width=9)
                    ], className="mb-4"),
                    
                    # Auto-detection status section
                    dbc.Row([
                        dbc.Col([
                            dbc.Card([
                                dbc.CardHeader("Automatic Feed Detection"),
                                dbc.CardBody([
                                    html.Div(id="auto-feed-status")
                                ])
                            ])
                        ], width=12)
                    ], className="mb-4"),
                    
                    # Graphs Section
                    dbc.Row([
                        dbc.Col([
                            dbc.Card([
                                dbc.CardHeader("Process Monitoring"),
                                dbc.CardBody([
                                    dcc.Graph(id='main-graph'),
                                    dcc.Interval(
                                        id='graph-update',
                                        interval=5000,
                                        n_intervals=0
                                    )
                                ])
                            ])
                        ], width=12)
                    ])
                ], label="Monitoring"),
                
                # Settings Tab
                dbc.Tab([
                    dbc.Row([
                        dbc.Col(html.H2("Feed Settings"), width=12, className="mb-4")
                    ]),
                    
                    # Control Feed Settings
                    dbc.Row([
                        dbc.Col([
                            dbc.Card([
                                dbc.CardHeader("Control Feed Settings"),
                                dbc.CardBody([
                                    html.Div([
                                        html.Label("Glucose Concentration (g/L)"),
                                        dbc.Input(
                                            id="control-glucose-conc",
                                            type="number",
                                            value=self.settings["control_feed"]["glucose_concentration"],
                                            className="mb-3"
                                        ),
                                        html.Label("TOC Concentration (g/L)"),
                                        dbc.Input(
                                            id="control-toc-conc",
                                            type="number",
                                            value=self.settings["control_feed"]["toc_concentration"],
                                            className="mb-3"
                                        ),
                                        html.Label("Default Volume (L)"),
                                        dbc.Input(
                                            id="control-volume",
                                            type="number",
                                            value=self.settings["control_feed"]["default_volume"],
                                            className="mb-3"
                                        ),
                                        html.H5("Components", className="mt-4"),
                                        html.Label("Glucose (g/L)"),
                                        dbc.Input(
                                            id="control-comp-glucose",
                                            type="number",
                                            value=self.settings["control_feed"]["components"]["glucose"],
                                            className="mb-3"
                                        ),
                                        html.Label("Yeast Extract (g/L)"),
                                        dbc.Input(
                                            id="control-comp-yeast",
                                            type="number",
                                            value=self.settings["control_feed"]["components"]["yeast_extract"],
                                            className="mb-3"
                                        ),
                                        html.Label("Minerals (g/L)"),
                                        dbc.Input(
                                            id="control-comp-minerals",
                                            type="number",
                                            value=self.settings["control_feed"]["components"]["minerals"],
                                            className="mb-3"
                                        )
                                    ])
                                ])
                            ])
                        ], width=6),
                        
                        # Experimental Feed Settings
                        dbc.Col([
                            dbc.Card([
                                dbc.CardHeader("Experimental Feed Settings"),
                                dbc.CardBody([
                                    html.Div([
                                        html.Label("TOC Concentration (g/L)"),
                                        dbc.Input(
                                            id="exp-toc-conc",
                                            type="number",
                                            value=self.settings["experimental_feed"]["toc_concentration"],
                                            className="mb-3"
                                        ),
                                        html.Label("Default Volume (L)"),
                                        dbc.Input(
                                            id="exp-volume",
                                            type="number",
                                            value=self.settings["experimental_feed"]["default_volume"],
                                            className="mb-3"
                                        ),
                                        html.H5("Components", className="mt-4"),
                                        html.Label("Carbon Source (g/L)"),
                                        dbc.Input(
                                            id="exp-comp-carbon",
                                            type="number",
                                            value=self.settings["experimental_feed"]["components"]["carbon_source"],
                                            className="mb-3"
                                        ),
                                        html.Label("Nitrogen Source (g/L)"),
                                        dbc.Input(
                                            id="exp-comp-nitrogen",
                                            type="number",
                                            value=self.settings["experimental_feed"]["components"]["nitrogen_source"],
                                            className="mb-3"
                                        ),
                                        html.Label("Minerals (g/L)"),
                                        dbc.Input(
                                            id="exp-comp-minerals",
                                            type="number",
                                            value=self.settings["experimental_feed"]["components"]["minerals"],
                                            className="mb-3"
                                        )
                                    ])
                                ])
                            ])
                        ], width=6)
                    ]),
                    
                    # Save Settings Button
                    dbc.Row([
                        dbc.Col([
                            dbc.Button(
                                "Save Settings",
                                id="save-settings-btn",
                                color="success",
                                className="mt-4"
                            ),
                            html.Div(id="settings-save-status", className="mt-2")
                        ], width=12)
                    ])
                ], label="Settings"),
                
                # Scientific Export Tab
                dbc.Tab([
                    dbc.Row([
                        dbc.Col(html.H2("Scientific Data Export"), width=12)
                    ]),
                    dbc.Row([
                        dbc.Col([
                            dbc.Card([
                                dbc.CardHeader("Add Scientific Annotation"),
                                dbc.CardBody([
                                    dbc.Select(
                                        id="metric-type-select",
                                        options=[
                                            {"label": "DO Drop Rate", "value": "DO Drop Rate"},
                                            {"label": "DO Recovery Time", "value": "DO Recovery Time"},
                                            {"label": "OUR", "value": "OUR"},
                                            {"label": "sOUR", "value": "sOUR"},
                                            {"label": "DO Saturation", "value": "DO Saturation"}
                                        ],
                                        placeholder="Select Metric",
                                        className="mb-3"
                                    ),
                                    dbc.Textarea(
                                        id="observation-text",
                                        placeholder="Scientific observation...",
                                        className="mb-3"
                                    ),
                                    dbc.Select(
                                        id="significance-select",
                                        options=[
                                            {"label": "High", "value": "high"},
                                            {"label": "Medium", "value": "medium"},
                                            {"label": "Low", "value": "low"}
                                        ],
                                        placeholder="Significance Level",
                                        className="mb-3"
                                    ),
                                    dbc.Input(
                                        id="confidence-level",
                                        type="number",
                                        min=0,
                                        max=1,
                                        step=0.1,
                                        placeholder="Confidence Level (0-1)",
                                        className="mb-3"
                                    ),
                                    dbc.Input(
                                        id="operator-name-scientific",
                                        type="text",
                                        placeholder="Operator Name",
                                        className="mb-3"
                                    ),
                                    dbc.Button(
                                        "Add Annotation",
                                        id="add-annotation-btn",
                                        color="primary",
                                        className="mt-2"
                                    )
                                ])
                            ], className="mb-3"),
                            
                            dbc.Card([
                                dbc.CardHeader("Export Options"),
                                dbc.CardBody([
                                    dbc.Select(
                                        id="export-format-select",
                                        options=[
                                            {"label": "LaTeX", "value": "latex"},
                                            {"label": "Markdown", "value": "markdown"}
                                        ],
                                        value="latex",
                                        className="mb-3"
                                    ),
                                    dbc.Button(
                                        "Generate AI Analysis",
                                        id="generate-ai-btn",
                                        color="warning",
                                        className="me-2 mb-3"
                                    ),
                                    html.Div(id="ai-analysis-output", className="mb-3"),
                                    dbc.Button(
                                        "Export Current Metrics",
                                        id="export-metrics-btn",
                                        color="success",
                                        className="me-2"
                                    ),
                                    dbc.Button(
                                        "Export Time Series",
                                        id="export-timeseries-btn",
                                        color="info",
                                        className="me-2"
                                    ),
                                    dbc.Button(
                                        "Export Full Report",
                                        id="export-report-btn",
                                        color="primary"
                                    )
                                ])
                            ])
                        ], width=4),
                        
                        dbc.Col([
                            dbc.Card([
                                dbc.CardHeader("Export Preview"),
                                dbc.CardBody([
                                    html.Pre(
                                        id="export-preview",
                                        style={
                                            "white-space": "pre-wrap",
                                            "font-family": "monospace"
                                        }
                                    )
                                ])
                            ])
                        ], width=8)
                    ])
                ], label="Scientific Export")
            ])
        ], fluid=True)
        
    def create_main_plot(self, data: pd.DataFrame, feed_events: List[Dict] = None) -> go.Figure:
        """Create the main monitoring plot.
        
        Args:
            data: DataFrame with sensor data
            feed_events: List of feed event dictionaries
            
        Returns:
            Plotly figure object
        """
        fig = make_subplots(
            rows=3, cols=1,
            shared_xaxis=True,
            subplot_titles=('Dissolved Oxygen', 'pH & Temperature', 'Weights'),
            vertical_spacing=0.05
        )
        
        # DO plot
        fig.add_trace(
            go.Scatter(x=data['timestamp'], y=data['do_value'],
                      name='DO', line=dict(color='blue')),
            row=1, col=1
        )
        
        # pH and Temperature
        fig.add_trace(
            go.Scatter(x=data['timestamp'], y=data['ph_value'],
                      name='pH', line=dict(color='red')),
            row=2, col=1
        )
        fig.add_trace(
            go.Scatter(x=data['timestamp'], y=data['temperature'],
                      name='Temperature', line=dict(color='orange')),
            row=2, col=1
        )
        
        # Weights
        fig.add_trace(
            go.Scatter(x=data['timestamp'], y=data['reactor_weight'],
                      name='Reactor Weight', line=dict(color='green')),
            row=3, col=1
        )
        fig.add_trace(
            go.Scatter(x=data['timestamp'], y=data['feed_bottle_weight'],
                      name='Feed Bottle Weight', line=dict(color='purple')),
            row=3, col=1
        )
        
        # Add feed events if provided
        if feed_events:
            for event in feed_events:
                for i in range(1, 4):
                    fig.add_vline(
                        x=event['timestamp'],
                        line_dash="dash",
                        line_color="gray",
                        row=i, col=1
                    )
        
        fig.update_layout(height=800, showlegend=True)
        return fig
    
    def setup_callbacks(self):
        """Setup Dash callbacks for interactivity."""
        @self.app.callback(
            [Output('current-metrics', 'children'),
             Output('auto-feed-status', 'children')],
            [Input('graph-update', 'n_intervals')]
        )
        def update_metrics_and_detect_feeds(n):
            # Get latest data
            try:
                db = DatabaseConnection()  # Create instance first
                with db:  # Then use it in context manager
                    current_data = db.get_latest_data(minutes=5)
                
                if not current_data.empty:
                    # Detect feed events
                    detected_events = self.feed_detector.detect_feed_events(current_data)
                    
                    # Create feed status message
                    if detected_events:
                        latest_event = detected_events[-1]
                        feed_status = html.Div([
                            html.H5(" Feed Detected!", className="text-success"),
                            html.P([
                                f"Time: {pd.to_datetime(latest_event['timestamp']).strftime('%H:%M:%S')}", html.Br(),
                                f"Type: {latest_event['feed_type']}", html.Br(),
                                f"Volume: {latest_event['volume']*1000:.0f}mL"
                            ])
                        ])
                    else:
                        feed_status = html.Div("No recent feed events detected", className="text-muted")
                    
                    # Create metrics display
                    metrics = html.Div([
                        dbc.Row([
                            dbc.Col([
                                html.H5("MFC1"),
                                html.P(f"Set Point: {current_data['LB_MFC_1_SP'].iloc[-1]:.1f} L/min"),
                                html.P(f"Process Value: {current_data['LB_MFC_1_PV'].iloc[-1]:.1f} L/min")
                            ], width=4),
                            dbc.Col([
                                html.H5("DO"),
                                html.P(f"Value: {current_data['Reactor_1_DO_Value_PPM'].iloc[-1]:.1f} mg/L"),
                                html.P(f"Temperature: {current_data['Reactor_1_DO_T_Value'].iloc[-1]:.1f}°C")
                            ], width=4),
                            dbc.Col([
                                html.H5("pH"),
                                html.P(f"Value: {current_data['Reactor_1_PH_Value'].iloc[-1]:.2f}"),
                                html.P(f"Temperature: {current_data['Reactor_1_PH_T_Value'].iloc[-1]:.1f}°C")
                            ], width=4)
                        ], className="mb-3"),
                        dbc.Row([
                            dbc.Col([
                                html.H5("Feed Status"),
                                html.P(f"Pump Time On: {current_data['R1_Perastaltic_1_Time'].iloc[-1]:.0f}s"),
                                html.P(f"Pump Time Off: {current_data['R1_Perastaltic_1_Time_off'].iloc[-1]:.0f}s")
                            ], width=4),
                            dbc.Col([
                                html.H5("Weight"),
                                html.P(f"Reactor: {current_data['R1_Weight_Bal'].iloc[-1]:.1f}g"),
                                html.P(f"Feed Bottle: {current_data['R2_Weight_Bal'].iloc[-1]:.1f}g")
                            ], width=4)
                        ])
                    ])
                    
                    return metrics, feed_status
                    
                return html.Div("No data available"), html.Div("Feed detection unavailable", className="text-muted")
                
            except Exception as e:
                logger.error(f"Error updating metrics and detecting feeds: {e}")
                return html.Div(f"Error: {str(e)}"), html.Div("Feed detection error", className="text-danger")
        
        @self.app.callback(
            Output('main-graph', 'figure'),
            [Input('graph-update', 'n_intervals')]
        )
        def update_graph(n):
            # Create figure with secondary y-axis
            fig = make_subplots(specs=[[{"secondary_y": True}]])
            
            # Here you would fetch data from SQL database
            # Example structure:
            # timestamps = [...]
            # do_values = [...]
            # ph_values = [...]
            
            # Add DO trace
            fig.add_trace(
                go.Scatter(
                    name='DO',
                    x=[],  # timestamps
                    y=[],  # do_values
                    mode='lines',
                    line=dict(color='blue')
                ),
                secondary_y=False
            )
            
            # Add pH trace
            fig.add_trace(
                go.Scatter(
                    name='pH',
                    x=[],  # timestamps
                    y=[],  # ph_values
                    mode='lines',
                    line=dict(color='red')
                ),
                secondary_y=True
            )
            
            fig.update_layout(
                height=600,
                title="Process Monitoring",
                xaxis_title="Time",
                yaxis_title="DO (mg/L)",
                yaxis2_title="pH"
            )
            
            return fig
            
        @self.app.callback(
            Output("feed-status", "children"),
            [Input("add-feed-btn", "n_clicks")],
            [State("feed-type-select", "value"),
             State("feed-volume", "value"),
             State("operator-name", "value"),
             State("feed-notes", "value")]
        )
        def log_feed_event(n_clicks, feed_type, volume, operator, notes):
            if not n_clicks:
                return ""
                
            if not feed_type or not volume:
                return html.Div("Feed type and volume are required!", style={"color": "red"})
                
            try:
                components = self.settings[feed_type]["components"]
                self.feed_logger.log_event(
                    feed_type=feed_type,
                    volume=volume,
                    components=components,
                    operator=operator,
                    notes=notes
                )
                return html.Div("Feed event logged successfully!", style={"color": "green"})
            except Exception as e:
                return html.Div(f"Error logging feed event: {str(e)}", style={"color": "red"})
        
        @self.app.callback(
            Output("settings-save-status", "children"),
            [Input("save-settings-btn", "n_clicks")],
            [State("control-glucose-conc", "value"),
             State("control-toc-conc", "value"),
             State("control-volume", "value"),
             State("control-comp-glucose", "value"),
             State("control-comp-yeast", "value"),
             State("control-comp-minerals", "value"),
             State("exp-toc-conc", "value"),
             State("exp-volume", "value"),
             State("exp-comp-carbon", "value"),
             State("exp-comp-nitrogen", "value"),
             State("exp-comp-minerals", "value")]
        )
        def save_settings_callback(n_clicks, *values):
            if not n_clicks:
                return ""
                
            try:
                # Update control feed settings
                self.settings["control_feed"].update({
                    "glucose_concentration": values[0],
                    "toc_concentration": values[1],
                    "default_volume": values[2],
                    "components": {
                        "glucose": values[3],
                        "yeast_extract": values[4],
                        "minerals": values[5]
                    }
                })
                
                # Update experimental feed settings
                self.settings["experimental_feed"].update({
                    "toc_concentration": values[6],
                    "default_volume": values[7],
                    "components": {
                        "carbon_source": values[8],
                        "nitrogen_source": values[9],
                        "minerals": values[10]
                    }
                })
                
                self.save_settings()
                return html.Div("Settings saved successfully!", style={"color": "green"})
                
            except Exception as e:
                return html.Div(f"Error saving settings: {str(e)}", style={"color": "red"})
        
        @self.app.callback(
            [Output("do-saturation", "children"),
             Output("do-drop-rate", "children"),
             Output("do-recovery-time", "children"),
             Output("our-value", "children"),
             Output("sour-value", "children")],
            [Input("interval-component", "n_intervals")]
        )
        def update_oxygen_metrics(n):
            try:
                # Get the latest DO data from the database
                query = """
                    SELECT DateTime as timestamp, Reactor_1_DO_Value_PPM as do_value 
                    FROM ReactorData 
                    WHERE DateTime >= DATEADD(hour, -2, GETDATE())
                    ORDER BY DateTime DESC
                """
                do_data = pd.read_sql(query, self.db.reactor_engine)
                
                # Update DO saturation based on recent data
                self.metrics.update_do_saturation(do_data)
                
                if self.metrics.do_saturation is None:
                    logger.warning("Could not determine DO saturation from data")
                    return "No stable DO", "No data", "No data", "No data", "No data"
                
                # Get the latest feed event
                latest_feed = self.feed_logger.get_latest_feed_event()
                
                if latest_feed is None:
                    return (f"{self.metrics.do_saturation:.2f} mg/L", 
                           "No data", "No data", "No data", "No data")
                
                # Get the latest TSS value from manual inputs
                tss_query = """
                    SELECT tss_value 
                    FROM process_parameters 
                    ORDER BY timestamp DESC 
                    LIMIT 1
                """
                tss_df = pd.read_sql(tss_query, self.db.dashboard_engine)
                biomass_concentration = tss_df['tss_value'].iloc[0] if not tss_df.empty else None
                
                # Calculate metrics
                event_time = pd.Timestamp(latest_feed['timestamp'])
                drop_rate, r_squared = self.metrics.calculate_do_drop_rate(do_data, event_time)
                recovery_time = self.metrics.calculate_recovery_time(do_data, event_time)
                our = self.metrics.calculate_our(do_data, event_time)
                sour = self.metrics.calculate_sour(do_data, event_time, biomass_concentration) if biomass_concentration else None
                
                # Update latest metrics
                self.latest_metrics.update({
                    "drop_rate": drop_rate if drop_rate else 0,
                    "recovery_time": recovery_time if recovery_time else 0,
                    "our": our if our else 0,
                    "sour": sour if sour else 0
                })
                
                # Format output strings
                saturation_str = f"{self.metrics.do_saturation:.2f} mg/L"
                drop_rate_str = f"{abs(drop_rate):.3f} mg/L/s (R² = {r_squared:.2f})" if drop_rate else "No data"
                recovery_str = f"{recovery_time:.1f} s" if recovery_time else "Not recovered"
                our_str = f"{our:.2f} mg O₂/L/h" if our else "No data"
                sour_str = f"{sour:.2f} mg O₂/g/h" if sour else "No data"
                
                return saturation_str, drop_rate_str, recovery_str, our_str, sour_str
                
            except Exception as e:
                logger.error(f"Error updating oxygen metrics: {e}")
                self.latest_metrics = {k: 0 for k in self.latest_metrics}
                return "Error", "Error", "Error", "Error", "Error"
        
        @self.app.callback(
            Output("export-preview", "children"),
            [Input("export-metrics-btn", "n_clicks"),
             Input("export-format-select", "value")],
            [State("operator-name-scientific", "value")]
        )
        def update_export_preview(n_clicks, format_type, operator):
            if not n_clicks:
                return "Click 'Export Current Metrics' to preview"
                
            try:
                # Get current metrics
                metrics_data = {
                    "DO Saturation": self.metrics.do_saturation,
                    "DO Drop Rate": self.latest_metrics.get("drop_rate", 0),
                    "DO Recovery Time": self.latest_metrics.get("recovery_time", 0),
                    "OUR": self.latest_metrics.get("our", 0),
                    "sOUR": self.latest_metrics.get("sour", 0)
                }
                
                if all(v == 'No data' for v in metrics_data.values()):
                    return "No live data available - Database connection is down"
                
                # Get current conditions
                conditions = {
                    "Temperature": "25°C",  # Add actual sensor data if available
                    "pH": "7.0",
                    "Operator": operator or "Unknown"
                }
                
                return self.scientific_exporter.export_metrics_snapshot(
                    metrics_data,
                    conditions,
                    datetime.now(),
                    format_type
                )
                
            except Exception as e:
                logger.error(f"Error generating export preview: {e}")
                return f"Error: {str(e)}"
        
        @self.app.callback(
            Output("export-status", "children"),
            [Input("add-annotation-btn", "n_clicks")],
            [State("metric-type-select", "value"),
             State("observation-text", "value"),
             State("significance-select", "value"),
             State("confidence-level", "value"),
             State("operator-name-scientific", "value")]
        )
        def add_scientific_annotation(n_clicks, metric_type, observation, 
                                   significance, confidence, operator):
            if not n_clicks:
                return ""
                
            try:
                if not all([metric_type, observation, significance, 
                           confidence, operator]):
                    return "Please fill all fields"
                
                # Get current value for the selected metric
                current_value = self.latest_metrics.get(
                    metric_type.lower().replace(" ", "_"),
                    0
                )
                
                annotation = ScientificAnnotation(
                    timestamp=datetime.now(),
                    metric_type=metric_type,
                    value=current_value,
                    units=self.scientific_exporter.get_units(metric_type),
                    observation=observation,
                    significance=significance,
                    confidence_level=float(confidence),
                    experimental_conditions={
                        "Temperature": "25°C",
                        "pH": "7.0"
                    },
                    operator=operator
                )
                
                self.scientific_exporter.add_annotation(annotation)
                return "Annotation added successfully"
                
            except Exception as e:
                logger.error(f"Error adding annotation: {e}")
                return f"Error: {str(e)}"
        
        @self.app.callback(
            Output("ai-analysis-output", "children"),
            [Input("generate-ai-btn", "n_clicks")],
            [State("export-format-select", "value")]
        )
        def generate_ai_analysis(n_clicks, format_type):
            if not n_clicks:
                return ""
                
            try:
                # Get current metrics and historical data
                current_metrics = {
                    "DO Saturation": self.metrics.do_saturation,
                    "DO Drop Rate": self.latest_metrics.get("drop_rate", 0),
                    "DO Recovery Time": self.latest_metrics.get("recovery_time", 0),
                    "OUR": self.latest_metrics.get("our", 0),
                    "sOUR": self.latest_metrics.get("sour", 0)
                }
                
                # Get historical data for trend analysis
                query = """
                    SELECT DateTime as timestamp, Reactor_1_DO_Value_PPM as do_value 
                    FROM ReactorData 
                    WHERE DateTime >= DATEADD(hour, -24, GETDATE())
                    ORDER BY DateTime ASC
                """
                historical_data = pd.read_sql(query, self.db.reactor_engine)
                
                # Get current conditions
                conditions = {
                    "Temperature": "25°C",
                    "pH": "7.0",
                    "Feed Type": self.feed_logger.get_latest_feed_event().get("feed_type", "Unknown")
                }
                
                # Generate AI insights
                insights = self.ai_analyzer.analyze_metrics(
                    current_metrics,
                    historical_data,
                    conditions
                )
                
                # Generate scientific text
                scientific_text = self.ai_analyzer.generate_scientific_text(insights)
                
                # Format output based on selected format
                if format_type == "latex":
                    output = (
                        "\\begin{quote}\n"
                        f"{scientific_text}\n"
                        "\\end{quote}\n\n"
                        "\\begin{itemize}\n"
                    )
                    
                    for insight in insights:
                        output += (
                            f"\\item \\textbf{{{insight.metric_name}}}: "
                            f"{insight.interpretation} "
                            f"(Confidence: {insight.confidence*100:.0f}\\%)\n"
                        )
                    
                    output += "\\end{itemize}"
                    
                else:  # markdown
                    output = f"> {scientific_text}\n\n"
                    for insight in insights:
                        output += (
                            f"- **{insight.metric_name}**: "
                            f"{insight.interpretation} "
                            f"(Confidence: {insight.confidence*100:.0f}%)\n"
                        )
                
                return dbc.Card([
                    dbc.CardHeader("AI Analysis"),
                    dbc.CardBody([
                        html.Pre(
                            output,
                            style={
                                "white-space": "pre-wrap",
                                "font-family": "monospace"
                            }
                        )
                    ])
                ])
                
            except Exception as e:
                logger.error(f"Error in AI analysis: {e}")
                return html.Div(
                    f"Error generating AI analysis: {str(e)}",
                    style={"color": "red"}
                )
    
    def run_server(self, debug=True, port=8050):
        """Start the Dash server."""
        self.app.run_server(debug=debug, port=port)
