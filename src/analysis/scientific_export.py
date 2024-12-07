from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional
import pandas as pd
import json
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

@dataclass
class ScientificAnnotation:
    timestamp: datetime
    metric_type: str
    value: float
    units: str
    observation: str
    significance: str  # 'high', 'medium', 'low'
    confidence_level: float  # 0.0 to 1.0
    experimental_conditions: Dict[str, str]
    operator: str

class ScientificDataExporter:
    def __init__(self, export_dir: str = "scientific_data"):
        self.export_dir = Path(export_dir)
        self.export_dir.mkdir(exist_ok=True)
        self.annotations_file = self.export_dir / "annotations.json"
        self.load_annotations()

    def load_annotations(self):
        """Load existing annotations from file."""
        if self.annotations_file.exists():
            with open(self.annotations_file, 'r') as f:
                self.annotations = json.load(f)
        else:
            self.annotations = []

    def save_annotations(self):
        """Save annotations to file."""
        with open(self.annotations_file, 'w') as f:
            json.dump(self.annotations, f, indent=2, default=str)

    def add_annotation(self, annotation: ScientificAnnotation):
        """Add a new scientific annotation."""
        annotation_dict = {
            'timestamp': annotation.timestamp.isoformat(),
            'metric_type': annotation.metric_type,
            'value': annotation.value,
            'units': annotation.units,
            'observation': annotation.observation,
            'significance': annotation.significance,
            'confidence_level': annotation.confidence_level,
            'experimental_conditions': annotation.experimental_conditions,
            'operator': annotation.operator
        }
        self.annotations.append(annotation_dict)
        self.save_annotations()

    def format_scientific_value(self, value: float, precision: int = 3) -> str:
        """Format a value in scientific notation with proper precision."""
        return f"{value:.{precision}e}"

    def export_metrics_snapshot(self, 
                              metrics_data: Dict[str, float],
                              conditions: Dict[str, str],
                              timestamp: datetime,
                              output_format: str = 'latex') -> str:
        """Export current metrics in scientific paper format.
        
        Args:
            metrics_data: Dictionary of metric names and values
            conditions: Current experimental conditions
            timestamp: Timestamp of the snapshot
            output_format: 'latex' or 'markdown'
            
        Returns:
            Formatted string ready for inclusion in a paper
        """
        if output_format == 'latex':
            template = (
                "\\begin{table}[h]\n"
                "\\caption{Oxygen Utilization Metrics at %s}\n"
                "\\begin{tabular}{lll}\n"
                "\\hline\n"
                "Metric & Value & Units \\\\\n"
                "\\hline\n"
                "%s"
                "\\hline\n"
                "\\end{tabular}\n"
                "\\label{tab:oxygen_metrics}\n"
                "\\end{table}\n"
            )
            
            rows = []
            for metric, value in metrics_data.items():
                if isinstance(value, float):
                    formatted_value = self.format_scientific_value(value)
                    rows.append(f"{metric} & {formatted_value} & {self.get_units(metric)} \\\\")
            
            conditions_text = "\\begin{itemize}\n"
            for cond, val in conditions.items():
                conditions_text += f"\\item {cond}: {val}\n"
            conditions_text += "\\end{itemize}\n"
            
        else:  # markdown
            template = (
                "## Oxygen Utilization Metrics (%s)\n\n"
                "| Metric | Value | Units |\n"
                "|--------|--------|-------|\n"
                "%s\n\n"
                "### Experimental Conditions\n\n"
                "%s\n"
            )
            
            rows = []
            for metric, value in metrics_data.items():
                if isinstance(value, float):
                    formatted_value = self.format_scientific_value(value)
                    rows.append(f"| {metric} | {formatted_value} | {self.get_units(metric)} |")
            
            conditions_text = ""
            for cond, val in conditions.items():
                conditions_text += f"- {cond}: {val}\n"

        formatted_time = timestamp.strftime("%Y-%m-%d %H:%M:%S")
        return template % (formatted_time, "\n".join(rows), conditions_text)

    def get_units(self, metric_type: str) -> str:
        """Get standard units for each metric type."""
        units = {
            'DO Drop Rate': 'mg/L/s',
            'DO Recovery Time': 's',
            'OUR': 'mg O₂/L/h',
            'sOUR': 'mg O₂/g/h',
            'DO Saturation': 'mg/L',
            'TSS': 'g/L'
        }
        return units.get(metric_type, '-')

    def export_time_series(self,
                          data: pd.DataFrame,
                          metric_columns: List[str],
                          output_format: str = 'latex') -> str:
        """Export time series data in scientific paper format."""
        if output_format == 'latex':
            template = (
                "\\begin{figure}[h]\n"
                "\\centering\n"
                "\\begin{tikzpicture}\n"
                "\\begin{axis}[\n"
                "    xlabel=Time,\n"
                "    ylabel=Value,\n"
                "    grid=major\n"
                "]\n"
                "%s"
                "\\end{axis}\n"
                "\\end{tikzpicture}\n"
                "\\caption{Time series of oxygen utilization metrics}\n"
                "\\label{fig:metrics_time_series}\n"
                "\\end{figure}\n"
            )
            
            plots = []
            for col in metric_columns:
                points = [f"({row['timestamp']},{row[col]})" for _, row in data.iterrows()]
                plots.append(f"\\addplot coordinates {{{' '.join(points)}}};\n")
                
        else:  # markdown
            template = (
                "## Metrics Time Series\n\n"
                "```python\n"
                "import matplotlib.pyplot as plt\n\n"
                "plt.figure(figsize=(10, 6))\n"
                "%s"
                "plt.xlabel('Time')\n"
                "plt.ylabel('Value')\n"
                "plt.legend()\n"
                "plt.grid(True)\n"
                "plt.show()\n"
                "```\n"
            )
            
            plots = []
            for col in metric_columns:
                plots.append(f"plt.plot(data['timestamp'], data['{col}'], label='{col}')")

        return template % "\n".join(plots)

    def generate_paper_section(self, 
                             metrics_data: Dict[str, float],
                             time_series_data: pd.DataFrame,
                             conditions: Dict[str, str],
                             annotations: List[ScientificAnnotation],
                             timestamp: datetime) -> Dict[str, str]:
        """Generate complete paper section with metrics, figures, and annotations."""
        return {
            'metrics_table': self.export_metrics_snapshot(metrics_data, conditions, timestamp),
            'time_series': self.export_time_series(time_series_data, list(metrics_data.keys())),
            'annotations': self.format_annotations(annotations)
        }

    def format_annotations(self, annotations: List[ScientificAnnotation], 
                         output_format: str = 'latex') -> str:
        """Format scientific annotations for paper inclusion."""
        if output_format == 'latex':
            template = (
                "\\begin{table}[h]\n"
                "\\caption{Scientific Observations}\n"
                "\\begin{tabular}{p{0.2\\textwidth}p{0.6\\textwidth}p{0.2\\textwidth}}\n"
                "\\hline\n"
                "Metric & Observation & Confidence \\\\\n"
                "\\hline\n"
                "%s"
                "\\hline\n"
                "\\end{tabular}\n"
                "\\end{table}\n"
            )
            
            rows = []
            for ann in annotations:
                rows.append(
                    f"{ann.metric_type} & {ann.observation} & "
                    f"{ann.confidence_level*100:.1f}\\% \\\\"
                )
        else:
            template = (
                "## Scientific Observations\n\n"
                "| Metric | Observation | Confidence |\n"
                "|--------|-------------|------------|\n"
                "%s\n"
            )
            
            rows = []
            for ann in annotations:
                rows.append(
                    f"| {ann.metric_type} | {ann.observation} | "
                    f"{ann.confidence_level*100:.1f}% |"
                )

        return template % "\n".join(rows)
