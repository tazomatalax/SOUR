from typing import Dict, List, Optional
from ..core.feature import Feature
from .data_collection import DataCollectionFeature
from .metrics import MetricsFeature
from ..analysis.ai_insights import OllamaAnalyzer, MetricInsight
import logging

logger = logging.getLogger(__name__)

class AIInsightsFeature(Feature):
    def __init__(self, data_collection: Optional[DataCollectionFeature] = None,
                 metrics: Optional[MetricsFeature] = None):
        super().__init__("ai_insights")
        self.data_collection = data_collection
        self.metrics = metrics
        self.analyzer = OllamaAnalyzer()
        self.latest_insights: List[MetricInsight] = []
        self.latest_metrics = {
            "drop_rate": 0,
            "recovery_time": 0,
            "our": 0,
            "sour": 0
        }
        self._initialize_if_enabled()

    def _initialize_if_enabled(self):
        """Initialize the feature if enabled in config."""
        if not self.is_enabled():
            logger.info("AI Insights feature is disabled")
            return
        logger.info("Initializing AI Insights feature")
        self.analyzer = OllamaAnalyzer()

    def is_enabled(self) -> bool:
        """Check if the feature is enabled in config."""
        return self.get_config('enabled', False)

    def update_metrics(self, metrics: Dict[str, float]):
        """Update latest metrics."""
        self.latest_metrics.update(metrics)

    def get_latest_insights(self) -> List[MetricInsight]:
        """Get the most recent AI insights."""
        if not self.is_enabled():
            return []
        return self.latest_insights

    def analyze_current_state(self) -> List[MetricInsight]:
        """Analyze current state and return insights."""
        if not self.is_enabled():
            return []

        try:
            if not self.metrics or not self.data_collection:
                logger.warning("Required features not available for AI analysis")
                return []

            # Get current data
            current_data = self.data_collection.get_latest_data()
            if current_data.empty:
                logger.warning("No current data available for AI analysis")
                return []

            # Get historical data for trend analysis
            historical_data = self.data_collection.get_historical_data(hours=2)

            # Get current experimental conditions
            conditions = {
                "Temperature": f"{current_data['Reactor_1_DO_T_Value'].iloc[-1]:.1f}°C",
                "pH": f"{current_data['Reactor_1_PH_Value'].iloc[-1]:.2f}"
            }

            # Run AI analysis
            self.latest_insights = self.analyzer.analyze_metrics(
                self.latest_metrics,
                historical_data,
                conditions
            )
            return self.latest_insights

        except Exception as e:
            logger.error(f"Error in AI analysis: {e}")
            return []

    def generate_scientific_report(self) -> str:
        """Generate a scientific report from current insights."""
        if not self.is_enabled() or not self.latest_insights:
            return ""

        try:
            return self.analyzer.generate_scientific_text(self.latest_insights)
        except Exception as e:
            logger.error(f"Error generating scientific report: {e}")
            return f"Error generating report: {str(e)}"
