from typing import Dict, List
import dash
from dash import dcc, html
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State, ALL
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd

class BioreactorDashboard:
    def __init__(self):
        self.app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
        self.setup_layout()
        self.setup_callbacks()
        
    def setup_layout(self):
        """Create the dashboard layout."""
        self.app.layout = dbc.Container([
            dbc.Row([
                dbc.Col(html.H1("Bioreactor Monitoring System"), width=12)
            ]),
            
            # Feed Configuration Section
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("Feed Configuration"),
                        dbc.CardBody([
                            html.Div([
                                html.Label("Feed Type"),
                                dbc.Select(
                                    id="feed-type-select",
                                    options=[
                                        {"label": "Control Feed", "value": "control"},
                                        {"label": "Test Feed", "value": "test"}
                                    ],
                                    className="mb-3"
                                ),
                                html.Label("Test Feed TOC (mg/L)"),
                                dbc.Input(
                                    id="toc-input",
                                    type="number",
                                    placeholder="Enter TOC value",
                                    className="mb-3"
                                ),
                                html.Label("Glucose Solution Concentration (g/L)"),
                                dbc.Input(
                                    id="glucose-conc-input",
                                    type="number",
                                    placeholder="Enter glucose concentration",
                                    className="mb-3"
                                ),
                                dbc.Button(
                                    "Update Feed Parameters",
                                    id="update-feed-btn",
                                    color="primary",
                                    className="mt-2"
                                )
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
                                interval=5000,  # 5 seconds
                                n_intervals=0
                            )
                        ])
                    ])
                ], width=12)
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
            Output("feed-type-select", "disabled"),
            [Input("update-feed-btn", "n_clicks")],
            [State("feed-type-select", "value"),
             State("toc-input", "value"),
             State("glucose-conc-input", "value")]
        )
        def update_feed_parameters(n_clicks, feed_type, toc, glucose_conc):
            if n_clicks is None:
                return False
                
            # Here you would save the feed parameters to your system
            # For now, just disable the feed type selection after parameters are set
            return True
    
    def run_server(self, debug=True, port=8050):
        """Start the Dash server."""
        self.app.run_server(debug=debug, port=port)
