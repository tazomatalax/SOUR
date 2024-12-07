import os
from typing import Dict, List, Optional
import requests
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from dataclasses import dataclass
import logging
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

@dataclass
class MetricInsight:
    metric_name: str
    value: float
    trend: str  # 'increasing', 'decreasing', 'stable'
    significance: str  # 'high', 'medium', 'low'
    interpretation: str
    recommendations: List[str]
    confidence: float

class OllamaAnalyzer:
    def __init__(self, 
                 model_name: Optional[str] = None, 
                 base_url: Optional[str] = None):
        """Initialize Ollama Analyzer with specified model.
        
        Args:
            model_name: Name of the Ollama model to use (e.g., 'mistral', 'llama2')
                       If None, uses OLLAMA_MODEL_NAME from .env
            base_url: Base URL for Ollama API
                     If None, uses OLLAMA_BASE_URL from .env
        """
        self.model_name = model_name or os.getenv('OLLAMA_MODEL_NAME', 'mistral')
        self.base_url = base_url or os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
        
        # Optional OpenAI fallback
        self.openai_key = os.getenv('OPENAI_API_KEY')
        if self.openai_key:
            logger.info("OpenAI API key found, will use as fallback if Ollama is unavailable")
        
        self._check_model_availability()
        
    def _check_model_availability(self):
        """Check if the specified model is available in Ollama."""
        try:
            response = requests.get(f"{self.base_url}/api/tags")
            if response.status_code == 200:
                available_models = [model['name'] for model in response.json()['models']]
                if self.model_name not in available_models:
                    logger.warning(
                        f"Model {self.model_name} not found. Available models: {available_models}"
                    )
        except Exception as e:
            logger.error(f"Error checking Ollama model availability: {e}")
    
    def _generate_ollama_response(self, prompt: str) -> str:
        """Generate response from Ollama model."""
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model_name,
                    "prompt": prompt,
                    "stream": False
                }
            )
            
            if response.status_code == 200:
                return response.json()['response']
            else:
                logger.error(f"Ollama API error: {response.status_code}")
                return ""
                
        except Exception as e:
            logger.error(f"Error generating Ollama response: {e}")
            return ""
            
    def analyze_metrics(self, 
                       current_metrics: Dict[str, float],
                       historical_data: pd.DataFrame,
                       experimental_conditions: Dict[str, str]) -> List[MetricInsight]:
        """Analyze current metrics and generate insights using Ollama."""
        try:
            # Calculate trends from historical data
            trends = self._calculate_trends(historical_data)
            
            # Prepare analysis prompt
            prompt = self._prepare_analysis_prompt(
                current_metrics,
                trends,
                experimental_conditions
            )
            
            # Get response from Ollama
            response = self._generate_ollama_response(prompt)
            
            # Parse response into insights
            insights = self._parse_llm_response(response, current_metrics)
            return insights
            
        except Exception as e:
            logger.error(f"Error in metric analysis: {e}")
            return self._generate_fallback_insights(current_metrics)
    
    def _prepare_analysis_prompt(self,
                               metrics: Dict[str, float],
                               trends: Dict[str, str],
                               conditions: Dict[str, str]) -> str:
        """Prepare prompt for Ollama analysis."""
        prompt = """Analyze the following bioreactor oxygen utilization metrics and provide scientific insights.
        Format your response as JSON with the following structure for each metric:
        {
            "metrics": [
                {
                    "metric_name": "name",
                    "value": numeric_value,
                    "trend": "trend_direction",
                    "significance": "high/medium/low",
                    "interpretation": "scientific interpretation",
                    "recommendations": ["recommendation1", "recommendation2"],
                    "confidence": confidence_value
                }
            ]
        }

        Current Metrics:
        """
        
        for name, value in metrics.items():
            trend = trends.get(name, 'stable')
            prompt += f"\n{name}: {value:.3e} ({trend} trend)"
        
        prompt += "\n\nExperimental Conditions:"
        for cond, val in conditions.items():
            prompt += f"\n{cond}: {val}"
        
        prompt += """
        
        Reference Ranges:
        - DO Drop Rate: Typical range 0.01-0.1 mg/L/s
        - DO Recovery Time: Optimal < 300s
        - OUR: Healthy range 1-10 mg O₂/L/h
        - sOUR: Typical range 0.1-1.0 mg O₂/g/h
        
        Provide detailed scientific analysis focusing on:
        1. Metabolic implications
        2. Process efficiency
        3. Optimization opportunities
        4. Correlations between metrics
        """
        
        return prompt
    
    def _parse_llm_response(self, 
                          response: str, 
                          current_metrics: Dict[str, float]) -> List[MetricInsight]:
        """Parse LLM response into MetricInsight objects."""
        try:
            # Try to find JSON in the response
            start_idx = response.find('{')
            end_idx = response.rfind('}') + 1
            if start_idx >= 0 and end_idx > start_idx:
                json_str = response[start_idx:end_idx]
                data = json.loads(json_str)
                
                insights = []
                for metric in data.get('metrics', []):
                    insight = MetricInsight(
                        metric_name=metric['metric_name'],
                        value=metric.get('value', 0.0),
                        trend=metric.get('trend', 'stable'),
                        significance=metric.get('significance', 'medium'),
                        interpretation=metric['interpretation'],
                        recommendations=metric.get('recommendations', []),
                        confidence=float(metric.get('confidence', 0.8))
                    )
                    insights.append(insight)
                
                return insights
            else:
                logger.warning("No valid JSON found in LLM response")
                return self._generate_fallback_insights(current_metrics)
                
        except Exception as e:
            logger.error(f"Error parsing LLM response: {e}")
            return self._generate_fallback_insights(current_metrics)
    
    def _calculate_trends(self, data: pd.DataFrame) -> Dict[str, str]:
        """Calculate trends for each metric over time."""
        trends = {}
        for column in data.columns:
            if column == 'timestamp':
                continue
                
            recent_data = data[column].tail(10)  # Last 10 points
            if len(recent_data) < 2:
                trends[column] = 'stable'
                continue
                
            # Simple linear regression for trend
            x = np.arange(len(recent_data))
            slope, _ = np.polyfit(x, recent_data, 1)
            
            if abs(slope) < 0.01:  # Threshold for stability
                trends[column] = 'stable'
            elif slope > 0:
                trends[column] = 'increasing'
            else:
                trends[column] = 'decreasing'
                
        return trends
    
    def generate_scientific_text(self, insights: List[MetricInsight]) -> str:
        """Generate scientific text from insights using Ollama."""
        try:
            prompt = """Generate a concise scientific paragraph analyzing these bioreactor metrics:

            """
            for insight in insights:
                prompt += f"""
                {insight.metric_name}:
                - Value: {insight.value:.3e}
                - Trend: {insight.trend}
                - Interpretation: {insight.interpretation}
                """
            
            prompt += """
            Write in academic style, focusing on:
            1. Metabolic implications
            2. Process efficiency
            3. Potential optimizations
            Use proper scientific terminology and cite potential implications.
            """
            
            response = self._generate_ollama_response(prompt)
            return response.strip()
            
        except Exception as e:
            logger.error(f"Error generating scientific text: {e}")
            return self._generate_fallback_text(insights)
    
    def _generate_fallback_insights(self, 
                                  metrics: Dict[str, float]) -> List[MetricInsight]:
        """Generate basic insights when LLM analysis is unavailable."""
        insights = []
        
        for name, value in metrics.items():
            if name == "DO Drop Rate":
                interpretation = (
                    "Indicates metabolic activity rate. "
                    "Higher values suggest increased substrate utilization."
                )
            elif name == "DO Recovery Time":
                interpretation = (
                    "Reflects system's oxygen transfer efficiency. "
                    "Shorter times indicate better mass transfer."
                )
            elif name == "OUR":
                interpretation = (
                    "Quantifies overall oxygen consumption. "
                    "Higher values indicate more active metabolism."
                )
            elif name == "sOUR":
                interpretation = (
                    "Biomass-specific oxygen uptake rate. "
                    "Indicates metabolic efficiency per unit biomass."
                )
            else:
                interpretation = "Basic metric analysis."
                
            insights.append(MetricInsight(
                metric_name=name,
                value=value,
                trend='stable',
                significance='medium',
                interpretation=interpretation,
                recommendations=["Continue monitoring for changes"],
                confidence=0.6
            ))
            
        return insights
    
    def _generate_fallback_text(self, insights: List[MetricInsight]) -> str:
        """Generate basic scientific text when LLM is unavailable."""
        text = "Analysis of oxygen utilization metrics reveals "
        
        for insight in insights:
            text += f"the {insight.metric_name.lower()} was measured at {insight.value:.3e}, "
            text += f"which {insight.interpretation.lower()} "
        
        text += "Further investigation may be warranted to optimize process conditions."
        return text
