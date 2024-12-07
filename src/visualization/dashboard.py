from typing import Dict, List
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
from data.feed_events import FeedEventLogger

logger = logging.getLogger(__name__)

class BioreactorDashboard:
    def __init__(self):
        self.app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
        self.settings_file = Path("feed_settings.json")
        self.settings = self.load_settings()
        self.feed_logger = FeedEventLogger()
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
                            ])
                        ], width=9)
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
                ], label="Settings")
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
            Output('current-metrics', 'children'),
            [Input('graph-update', 'n_intervals')]
        )
        def update_metrics(n):
            # This would fetch current values from SQL database
            return html.Div([
                dbc.Row([
                    dbc.Col([
                        html.H5("MFC1"),
                        html.P(f"Set Point: -- L/min"),
                        html.P(f"Process Value: -- L/min")
                    ], width=4),
                    dbc.Col([
                        html.H5("DO"),
                        html.P(f"Value: -- mg/L"),
                        html.P(f"Temperature: -- °C")
                    ], width=4),
                    dbc.Col([
                        html.H5("pH"),
                        html.P(f"Value: --"),
                        html.P(f"Temperature: -- °C")
                    ], width=4)
                ], className="mb-3"),
                dbc.Row([
                    dbc.Col([
                        html.H5("Feed Status"),
                        html.P(f"Pump Time On: -- s"),
                        html.P(f"Pump Time Off: -- s")
                    ], width=4),
                    dbc.Col([
                        html.H5("Weight"),
                        html.P(f"Current: -- g")
                    ], width=4)
                ])
            ])

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
    
    def run_server(self, debug=True, port=8050):
        """Start the Dash server."""
        self.app.run_server(debug=debug, port=port)
