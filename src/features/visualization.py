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
        self._initialize_if_enabled()
    
    def _initialize_if_enabled(self):
        """Initialize the feature if it's enabled in config."""
        if self.is_enabled:
            self.on_enable()
    
    def on_enable(self):
        """Initialize Dash app when feature is enabled."""
        try:
            self.app = dash.Dash(__name__)
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
            
        self.app.layout = html.Div([
            html.H1("Bioreactor Monitoring Dashboard"),
            
            # DO Monitoring Section
            html.Div([
                html.H2("Dissolved Oxygen Monitoring"),
                dcc.Graph(id='do-graph'),
                dcc.Interval(
                    id='do-update',
                    interval=self.get_config('update_interval', 5) * 1000
                )
            ]),
            
            # Feed Events Section
            html.Div([
                html.H2("Feed Events"),
                dcc.Graph(id='feed-graph'),
                html.Div(id='feed-stats')
            ]),
            
            # Metrics Section
            html.Div([
                html.H2("Real-time Metrics"),
                html.Div(id='metrics-display'),
                dcc.Interval(
                    id='metrics-update',
                    interval=self.get_config('update_interval', 5) * 1000
                )
            ])
        ])
    
    def _setup_callbacks(self):
        """Set up the Dash app callbacks."""
        if not self.app:
            return
            
        @self.app.callback(
            Output('do-graph', 'figure'),
            Input('do-update', 'n_intervals')
        )
        def update_do_graph(n):
            return self._create_do_figure()
        
        @self.app.callback(
            Output('feed-graph', 'figure'),
            Input('do-update', 'n_intervals')
        )
        def update_feed_graph(n):
            return self._create_feed_figure()
        
        @self.app.callback(
            Output('metrics-display', 'children'),
            Input('metrics-update', 'n_intervals')
        )
        def update_metrics(n):
            return self._create_metrics_display()
    
    def _create_do_figure(self) -> Dict[str, Any]:
        """Create the DO monitoring figure."""
        try:
            # Create test data for visualization
            return {
                'data': [
                    {
                        'x': [datetime.now() - timedelta(minutes=i) for i in range(10)],
                        'y': [50.0 + i for i in range(10)],
                        'type': 'scatter',
                        'name': 'DO Level'
                    }
                ],
                'layout': {
                    'title': 'Dissolved Oxygen Levels',
                    'xaxis': {'title': 'Time'},
                    'yaxis': {'title': 'DO (%)'}
                }
            }
        except Exception as e:
            logger.error(f"Error creating DO figure: {e}")
            return {}
    
    def _create_feed_figure(self) -> Dict[str, Any]:
        """Create the feed events figure."""
        try:
            # Create test data for visualization
            return {
                'data': [
                    {
                        'x': [datetime.now() - timedelta(hours=i) for i in range(5)],
                        'y': [0.1, 0.2, 0.1, 0.15, 0.1],
                        'type': 'scatter',
                        'mode': 'markers',
                        'name': 'Feed Events'
                    }
                ],
                'layout': {
                    'title': 'Feed Events',
                    'xaxis': {'title': 'Time'},
                    'yaxis': {'title': 'Volume (L)'}
                }
            }
        except Exception as e:
            logger.error(f"Error creating feed figure: {e}")
            return {}
    
    def _create_metrics_display(self) -> List[html.Div]:
        """Create the metrics display."""
        try:
            if self.metrics and self.metrics.is_enabled:
                # Get metrics data
                do_metrics = self.metrics.calculate_do_metrics({})
                feed_metrics = self.metrics.calculate_feed_metrics({})
                
                # Create display elements
                return [
                    html.Div([
                        html.H3("DO Metrics"),
                        html.P(f"Drop Rate: {do_metrics.get('do_drop_rate', 0):.2f} %/min"),
                        html.P(f"Recovery Time: {do_metrics.get('recovery_time', 0):.2f} min")
                    ]),
                    html.Div([
                        html.H3("Feed Metrics"),
                        html.P(f"Carbon Consumption: {feed_metrics.get('carbon_consumption_rate', 0):.2f} g/L/h"),
                        html.P(f"Oxygen Consumption: {feed_metrics.get('oxygen_consumption_rate', 0):.2f} g/L/h")
                    ])
                ]
            return []
        except Exception as e:
            logger.error(f"Error creating metrics display: {e}")
            return []
    
    def run_server(self, debug: bool = False):
        """Run the Dash server."""
        if not self.is_enabled or not self.app:
            logger.warning("Cannot run server: visualization is disabled or not initialized")
            return
            
        try:
            port = self.get_config('dashboard_port', 8050)
            self.app.run_server(debug=debug, port=port)
        except Exception as e:
            logger.error(f"Error running visualization server: {e}")
