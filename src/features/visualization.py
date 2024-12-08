import logging
from typing import Dict, Any, List, Optional
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.graph_objs as go
from datetime import datetime, timedelta
from ..core.feature import Feature
from .data_collection import DataCollectionFeature
from .metrics import MetricsFeature
from .feed_tracking import FeedTrackingFeature
from ..analysis.scientific_export import ScientificDataExporter, ScientificAnnotation
from pathlib import Path
import json
import jsonschema
import dash_bootstrap_components as dbc

logger = logging.getLogger(__name__)

class VisualizationFeature(Feature):
    def __init__(self, data_collection: Optional[DataCollectionFeature] = None,
                 metrics: Optional[MetricsFeature] = None,
                 feed_tracking: Optional[FeedTrackingFeature] = None):
        super().__init__("visualization")
        self.data_collection = data_collection
        self.metrics = metrics
        self.feed_tracking = feed_tracking
        self.app = None
        self.settings_file = Path("feed_settings.json")
        self.settings = self._load_settings()
        self.scientific_exporter = ScientificDataExporter()
        self.latest_metrics = {
            "drop_rate": 0,
            "recovery_time": 0,
            "our": 0,
            "sour": 0
        }
        self._initialize_if_enabled()
    
    def _initialize_if_enabled(self):
        """Initialize the feature if it's enabled in config."""
        if self.is_enabled:
            self.on_enable()
    
    def on_enable(self):
        """Initialize Dash app when feature is enabled."""
        try:
            self.app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
            self._setup_layout()
            self._setup_callbacks()
            logger.info("Visualization feature enabled")
        except Exception as e:
            logger.error(f"Failed to enable visualization: {e}")
            self.disable()

    def on_disable(self):
        """Clean up when feature is disabled."""
        self.app = None
        logger.info("Visualization feature disabled")
    
    def _setup_layout(self):
        """Set up the Dash app layout."""
        if not self.app:
            return
            
        self.app.layout = dbc.Container([
            dcc.Interval(
                id='interval-component',
                interval=self.get_config('update_interval', 5) * 1000,
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
                            # Oxygen Utilization Metrics Card
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
                                    ])
                                ])
                            ], className="mt-3")
                        ], width=9)
                    ], className="mb-4"),
                    
                    # Graphs Section
                    dbc.Row([
                        dbc.Col([
                            dbc.Card([
                                dbc.CardHeader("Process Monitoring"),
                                dbc.CardBody([
                                    dcc.Graph(id='main-graph'),
                                ])
                            ])
                        ], width=12)
                    ])
                ], label="Monitoring"),
                
                # Settings Tab
                dbc.Tab([
                    dbc.Row([
                        dbc.Col(html.H2("Feed Settings"), width=12)
                    ]),
                    dbc.Row([
                        dbc.Col([
                            dbc.Card([
                                dbc.CardHeader("Control Feed Settings"),
                                dbc.CardBody([
                                    dbc.Input(
                                        id="control-glucose-conc",
                                        type="number",
                                        placeholder="Glucose Concentration (g/L)",
                                        value=self.settings["control_feed"]["glucose_concentration"],
                                        className="mb-3"
                                    ),
                                    dbc.Input(
                                        id="control-toc-conc",
                                        type="number",
                                        placeholder="TOC Concentration (g/L)",
                                        value=self.settings["control_feed"]["toc_concentration"],
                                        className="mb-3"
                                    ),
                                    dbc.Input(
                                        id="control-volume",
                                        type="number",
                                        placeholder="Default Volume (L)",
                                        value=self.settings["control_feed"]["default_volume"],
                                        className="mb-3"
                                    ),
                                    html.H6("Components"),
                                    dbc.Input(
                                        id="control-comp-glucose",
                                        type="number",
                                        placeholder="Glucose (g/L)",
                                        value=self.settings["control_feed"]["components"]["glucose"],
                                        className="mb-2"
                                    ),
                                    dbc.Input(
                                        id="control-comp-yeast",
                                        type="number",
                                        placeholder="Yeast Extract (g/L)",
                                        value=self.settings["control_feed"]["components"]["yeast_extract"],
                                        className="mb-2"
                                    ),
                                    dbc.Input(
                                        id="control-comp-minerals",
                                        type="number",
                                        placeholder="Minerals (g/L)",
                                        value=self.settings["control_feed"]["components"]["minerals"],
                                        className="mb-2"
                                    )
                                ])
                            ])
                        ], width=6),
                        dbc.Col([
                            dbc.Card([
                                dbc.CardHeader("Experimental Feed Settings"),
                                dbc.CardBody([
                                    dbc.Input(
                                        id="exp-toc-conc",
                                        type="number",
                                        placeholder="TOC Concentration (g/L)",
                                        value=self.settings["experimental_feed"]["toc_concentration"],
                                        className="mb-3"
                                    ),
                                    dbc.Input(
                                        id="exp-volume",
                                        type="number",
                                        placeholder="Default Volume (L)",
                                        value=self.settings["experimental_feed"]["default_volume"],
                                        className="mb-3"
                                    ),
                                    html.H6("Components"),
                                    dbc.Input(
                                        id="exp-comp-carbon",
                                        type="number",
                                        placeholder="Carbon Source (g/L)",
                                        value=self.settings["experimental_feed"]["components"]["carbon_source"],
                                        className="mb-2"
                                    ),
                                    dbc.Input(
                                        id="exp-comp-nitrogen",
                                        type="number",
                                        placeholder="Nitrogen Source (g/L)",
                                        value=self.settings["experimental_feed"]["components"]["nitrogen_source"],
                                        className="mb-2"
                                    ),
                                    dbc.Input(
                                        id="exp-comp-minerals",
                                        type="number",
                                        placeholder="Minerals (g/L)",
                                        value=self.settings["experimental_feed"]["components"]["minerals"],
                                        className="mb-2"
                                    )
                                ])
                            ])
                        ], width=6)
                    ]),
                    dbc.Row([
                        dbc.Col([
                            dbc.Button("Save Settings", id="save-settings-btn", color="primary", className="mt-3"),
                            html.Div(id="settings-save-status", className="mt-2")
                        ], width=12)
                    ])
                ], label="Settings"),
                
                # Export Tab
                dbc.Tab([
                    dbc.Row([
                        dbc.Col(html.H2("Scientific Data Export"), width=12)
                    ]),
                    dbc.Row([
                        dbc.Col([
                            dbc.Card([
                                dbc.CardHeader("Export Current Metrics"),
                                dbc.CardBody([
                                    dbc.Select(
                                        id="export-format-select",
                                        options=[
                                            {"label": "Markdown", "value": "markdown"},
                                            {"label": "LaTeX", "value": "latex"}
                                        ],
                                        value="markdown",
                                        className="mb-3"
                                    ),
                                    dbc.Input(
                                        id="operator-name-scientific",
                                        type="text",
                                        placeholder="Operator Name",
                                        className="mb-3"
                                    ),
                                    dbc.Button(
                                        "Export Current Metrics",
                                        id="export-metrics-btn",
                                        color="primary",
                                        className="mb-3"
                                    ),
                                    html.Div(id="export-preview", className="mt-3")
                                ])
                            ]),
                            dbc.Card([
                                dbc.CardHeader("Add Scientific Annotation"),
                                dbc.CardBody([
                                    dbc.Select(
                                        id="metric-type-select",
                                        options=[
                                            {"label": "DO Drop Rate", "value": "drop_rate"},
                                            {"label": "Recovery Time", "value": "recovery_time"},
                                            {"label": "OUR", "value": "our"},
                                            {"label": "sOUR", "value": "sour"}
                                        ],
                                        className="mb-3"
                                    ),
                                    dbc.Textarea(
                                        id="observation-text",
                                        placeholder="Scientific Observation",
                                        className="mb-3"
                                    ),
                                    dbc.Select(
                                        id="significance-select",
                                        options=[
                                            {"label": "High", "value": "high"},
                                            {"label": "Medium", "value": "medium"},
                                            {"label": "Low", "value": "low"}
                                        ],
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
                                    dbc.Button(
                                        "Add Annotation",
                                        id="add-annotation-btn",
                                        color="primary"
                                    ),
                                    html.Div(id="export-status", className="mt-2")
                                ])
                            ], className="mt-3")
                        ], width=12)
                    ])
                ], label="Export")
            ])
        ])

    def _setup_callbacks(self):
        """Setup Dash callbacks for interactivity."""
        if not self.app:
            return

        @self.app.callback(
            [Output('current-metrics', 'children'),
             Output('do-saturation', 'children'),
             Output('do-drop-rate', 'children'),
             Output('do-recovery-time', 'children'),
             Output('our-value', 'children')],
            [Input('interval-component', 'n_intervals')]
        )
        def update_metrics(n):
            try:
                if not self.metrics or not self.data_collection:
                    return "No data available", "N/A", "N/A", "N/A", "N/A"

                # Get latest data from data collection feature
                current_data = self.data_collection.get_latest_data()
                
                if current_data.empty:
                    return "No data available", "N/A", "N/A", "N/A", "N/A"

                # Get metrics from metrics feature
                metrics_data = self.metrics.calculate_metrics(current_data)
                
                # Update latest metrics
                self.latest_metrics.update(metrics_data)

                # Create metrics display
                metrics_display = html.Div([
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
                    ])
                ])

                return (
                    metrics_display,
                    f"{metrics_data.get('do_saturation', 'N/A')} mg/L",
                    f"{abs(metrics_data.get('drop_rate', 0)):.3f} mg/L/s",
                    f"{metrics_data.get('recovery_time', 'N/A')} s",
                    f"{metrics_data.get('our', 'N/A')} mg O₂/L/h"
                )

            except Exception as e:
                logger.error(f"Error updating metrics: {e}")
                return "Error", "Error", "Error", "Error", "Error"

        @self.app.callback(
            Output('main-graph', 'figure'),
            [Input('interval-component', 'n_intervals')]
        )
        def update_graph(n):
            try:
                if not self.data_collection:
                    return go.Figure()

                data = self.data_collection.get_historical_data(hours=2)
                feed_events = self.feed_tracking.get_recent_events() if self.feed_tracking else None

                return self._create_main_plot(data, feed_events)

            except Exception as e:
                logger.error(f"Error updating graph: {e}")
                return go.Figure()

        @self.app.callback(
            Output("feed-status", "children"),
            [Input("add-feed-btn", "n_clicks")],
            [dash.dependencies.State("feed-type-select", "value"),
             dash.dependencies.State("feed-volume", "value"),
             dash.dependencies.State("operator-name", "value")]
        )
        def log_feed_event(n_clicks, feed_type, volume, operator):
            if not n_clicks or not self.feed_tracking:
                return ""

            if not feed_type or not volume:
                return html.Div("Feed type and volume are required!", style={"color": "red"})

            try:
                self.feed_tracking.log_feed_event(
                    feed_type=feed_type,
                    volume=volume,
                    operator=operator
                )
                return html.Div("Feed event logged successfully!", style={"color": "green"})
            except Exception as e:
                return html.Div(f"Error logging feed event: {str(e)}", style={"color": "red"})

        @self.app.callback(
            Output("settings-save-status", "children"),
            [Input("save-settings-btn", "n_clicks")],
            [dash.dependencies.State("control-glucose-conc", "value"),
             dash.dependencies.State("control-toc-conc", "value"),
             dash.dependencies.State("control-volume", "value"),
             dash.dependencies.State("control-comp-glucose", "value"),
             dash.dependencies.State("control-comp-yeast", "value"),
             dash.dependencies.State("control-comp-minerals", "value"),
             dash.dependencies.State("exp-toc-conc", "value"),
             dash.dependencies.State("exp-volume", "value"),
             dash.dependencies.State("exp-comp-carbon", "value"),
             dash.dependencies.State("exp-comp-nitrogen", "value"),
             dash.dependencies.State("exp-comp-minerals", "value")]
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
                
                self._save_settings()
                return html.Div("Settings saved successfully!", style={"color": "green"})
                
            except Exception as e:
                logger.error(f"Error saving settings: {e}")
                return html.Div(f"Error saving settings: {str(e)}", style={"color": "red"})

        @self.app.callback(
            Output("export-preview", "children"),
            [Input("export-metrics-btn", "n_clicks"),
             Input("export-format-select", "value")],
            [dash.dependencies.State("operator-name-scientific", "value")]
        )
        def update_export_preview(n_clicks, format_type, operator):
            if not n_clicks:
                return "Click 'Export Current Metrics' to preview"
                
            try:
                # Get current metrics
                metrics_data = {
                    "DO Saturation": self.metrics.do_saturation if self.metrics else "N/A",
                    "DO Drop Rate": self.latest_metrics.get("drop_rate", 0),
                    "DO Recovery Time": self.latest_metrics.get("recovery_time", 0),
                    "OUR": self.latest_metrics.get("our", 0),
                    "sOUR": self.latest_metrics.get("sour", 0)
                }
                
                if all(v == 'N/A' for v in metrics_data.values()):
                    return "No live data available"
                
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
            [dash.dependencies.State("metric-type-select", "value"),
             dash.dependencies.State("observation-text", "value"),
             dash.dependencies.State("significance-select", "value"),
             dash.dependencies.State("confidence-level", "value"),
             dash.dependencies.State("operator-name-scientific", "value")]
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

    def _load_settings(self) -> Dict:
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
        except Exception as e:
            logger.error(f"Error loading settings: {e}")
            return default_settings

    def _save_settings(self):
        """Save current settings to JSON file."""
        with open(self.settings_file, 'w') as f:
            json.dump(self.settings, f, indent=4)

    def _create_main_plot(self, data, feed_events=None):
        """Create the main monitoring plot."""
        fig = go.Figure()

        if data.empty:
            return fig

        # Add DO trace
        fig.add_trace(
            go.Scatter(
                name='DO',
                x=data.index,
                y=data['Reactor_1_DO_Value_PPM'],
                mode='lines',
                line=dict(color='blue')
            )
        )

        # Add feed event markers if available
        if feed_events:
            feed_times = [event['timestamp'] for event in feed_events]
            feed_types = [event['feed_type'] for event in feed_events]
            
            fig.add_trace(
                go.Scatter(
                    name='Feed Events',
                    x=feed_times,
                    y=[data['Reactor_1_DO_Value_PPM'].max()] * len(feed_times),
                    mode='markers',
                    marker=dict(
                        symbol='triangle-down',
                        size=12,
                        color='red'
                    ),
                    text=feed_types,
                    hovertemplate="Feed Event<br>Type: %{text}<br>Time: %{x}"
                )
            )

        fig.update_layout(
            height=600,
            title="Process Monitoring",
            xaxis_title="Time",
            yaxis_title="DO (mg/L)",
            showlegend=True
        )

        return fig

    def run(self):
        """Run the visualization server."""
        if self.app and self.is_enabled:
            port = self.get_config('port', 8050)
            self.app.run_server(debug=False, port=port)
