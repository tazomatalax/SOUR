from flask import Flask, jsonify, request
from flask_cors import CORS
import logging
from typing import Optional
from ..features.visualization import VisualizationFeature
from ..features.data_collection import DataCollectionFeature
from ..features.metrics import MetricsFeature
from ..features.feed_tracking import FeedTrackingFeature
from ..features.ai_insights_feature import AIInsightsFeature

logger = logging.getLogger(__name__)

def create_api_app(
    data_collection: Optional[DataCollectionFeature] = None,
    metrics: Optional[MetricsFeature] = None,
    feed_tracking: Optional[FeedTrackingFeature] = None,
    ai_insights: Optional[AIInsightsFeature] = None,
    visualization: Optional[VisualizationFeature] = None
):
    app = Flask(__name__)
    CORS(app)  # Enable CORS for all routes

    @app.route('/api/metrics/latest', methods=['GET'])
    def get_latest_metrics():
        try:
            if metrics:
                latest = metrics.get_latest_metrics()
                return jsonify(latest)
            return jsonify({"error": "Metrics feature not initialized"}), 500
        except Exception as e:
            logger.error(f"Error getting latest metrics: {e}")
            return jsonify({"error": str(e)}), 500

    @app.route('/api/feed/settings', methods=['GET', 'POST'])
    def handle_feed_settings():
        try:
            if feed_tracking:
                if request.method == 'GET':
                    return jsonify(feed_tracking.get_settings())
                else:
                    settings = request.json
                    feed_tracking.update_settings(settings)
                    return jsonify({"message": "Settings updated successfully"})
            return jsonify({"error": "Feed tracking feature not initialized"}), 500
        except Exception as e:
            logger.error(f"Error handling feed settings: {e}")
            return jsonify({"error": str(e)}), 500

    @app.route('/api/insights', methods=['GET'])
    def get_ai_insights():
        try:
            if ai_insights:
                insights = ai_insights.get_latest_insights()
                return jsonify(insights)
            return jsonify({"error": "AI insights feature not initialized"}), 500
        except Exception as e:
            logger.error(f"Error getting AI insights: {e}")
            return jsonify({"error": str(e)}), 500

    @app.route('/api/data/historical', methods=['GET'])
    def get_historical_data():
        try:
            if data_collection:
                start_time = request.args.get('start_time')
                end_time = request.args.get('end_time')
                data = data_collection.get_historical_data(start_time, end_time)
                return jsonify(data)
            return jsonify({"error": "Data collection feature not initialized"}), 500
        except Exception as e:
            logger.error(f"Error getting historical data: {e}")
            return jsonify({"error": str(e)}), 500

    return app
