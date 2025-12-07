"""
Performance Tracker - Monitors and reports on AI model performance.

This module provides comprehensive tracking of:
- Request processing times
- Model response times
- Cost tracking
- Accuracy metrics
- Anomaly detection
"""

import json
import logging
from collections import defaultdict, deque
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
import statistics

from .models import TaskType, AIModel, Response
from .config import OrchestratorConfig

logger = logging.getLogger(__name__)


class PerformanceTracker:
    """
    Tracks and reports on AI model and system performance.

    Features:
    - Request tracking with unique IDs
    - Model response tracking
    - Metrics aggregation (p50, p95, p99)
    - Anomaly detection
    - Performance report generation
    """

    def __init__(self, config: OrchestratorConfig):
        """
        Initialize the performance tracker.

        Args:
            config: Orchestrator configuration
        """
        self.config = config
        self.request_history: Dict[str, Dict[str, Any]] = {}
        self.model_metrics: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            'response_times': deque(maxlen=1000),
            'costs': deque(maxlen=1000),
            'success_count': 0,
            'failure_count': 0,
            'task_types': defaultdict(int)
        })

        # Rolling window for recent performance (last 24 hours)
        self.recent_requests: deque = deque(maxlen=10000)

        logger.info("Performance Tracker initialized")

    def start_request(
        self,
        request_id: str,
        task_type: TaskType,
        model_count: int,
        prompt_length: int
    ) -> None:
        """
        Track the start of a request.

        Args:
            request_id: Unique request identifier
            task_type: Type of task being processed
            model_count: Number of models being used
            prompt_length: Length of the prompt
        """
        if not self.config.enable_performance_tracking:
            return

        request_data = {
            'request_id': request_id,
            'task_type': task_type.value,
            'start_time': datetime.now().isoformat(),
            'model_count': model_count,
            'prompt_length': prompt_length,
            'models_used': [],
            'status': 'in_progress'
        }

        self.request_history[request_id] = request_data
        self.recent_requests.append(request_data)

        logger.debug(
            f"Started tracking request {request_id}: "
            f"task={task_type.value}, models={model_count}"
        )

    def track_model_response(
        self,
        request_id: str,
        model_name: str,
        response: Response
    ) -> None:
        """
        Track a model's response to a request.

        Args:
            request_id: Request identifier
            model_name: Name of the AI model
            response: Response object from the model
        """
        if not self.config.enable_performance_tracking:
            return

        # Update model metrics
        metrics = self.model_metrics[model_name]
        metrics['response_times'].append(response.response_time)
        metrics['costs'].append(response.cost)

        if response.success:
            metrics['success_count'] += 1
        else:
            metrics['failure_count'] += 1

        # Update request data
        if request_id in self.request_history:
            self.request_history[request_id]['models_used'].append({
                'model_name': model_name,
                'response_time': response.response_time,
                'cost': response.cost,
                'success': response.success,
                'timestamp': response.timestamp.isoformat()
            })

        logger.debug(
            f"Tracked response from {model_name} for request {request_id}: "
            f"time={response.response_time:.2f}s, cost=${response.cost:.4f}"
        )

    def complete_request(
        self,
        request_id: str,
        merged_result: Any,
        confidence_score: float,
        total_cost: float
    ) -> None:
        """
        Mark a request as completed.

        Args:
            request_id: Request identifier
            merged_result: Final merged result
            confidence_score: Confidence score of the result
            total_cost: Total cost for all models
        """
        if not self.config.enable_performance_tracking:
            return

        if request_id not in self.request_history:
            logger.warning(f"Request {request_id} not found in history")
            return

        request_data = self.request_history[request_id]
        request_data['end_time'] = datetime.now().isoformat()
        request_data['status'] = 'completed'
        request_data['total_cost'] = total_cost
        request_data['confidence_score'] = confidence_score

        # Calculate total response time
        start = datetime.fromisoformat(request_data['start_time'])
        end = datetime.fromisoformat(request_data['end_time'])
        request_data['total_time'] = (end - start).total_seconds()

        # Check for anomalies
        self._detect_request_anomalies(request_data)

        logger.info(
            f"Completed request {request_id}: "
            f"time={request_data['total_time']:.2f}s, "
            f"cost=${total_cost:.4f}, "
            f"confidence={confidence_score:.3f}"
        )

    def _detect_request_anomalies(self, request_data: Dict[str, Any]) -> None:
        """
        Detect anomalies in request performance.

        Args:
            request_data: Request data to analyze
        """
        if not self.config.enable_anomaly_detection:
            return

        anomalies = []

        # Check response time anomaly
        total_time = request_data.get('total_time', 0)
        if total_time > 60:  # Longer than 1 minute
            anomalies.append(f"Long response time: {total_time:.2f}s")

        # Check cost anomaly
        total_cost = request_data.get('total_cost', 0)
        if total_cost > 1.0:  # More than $1
            anomalies.append(f"High cost: ${total_cost:.4f}")

        # Check confidence anomaly
        confidence = request_data.get('confidence_score', 0)
        if confidence < 0.5:
            anomalies.append(f"Low confidence: {confidence:.3f}")

        if anomalies:
            logger.warning(
                f"Anomalies detected in request {request_data['request_id']}: "
                f"{', '.join(anomalies)}"
            )

    def get_model_performance(
        self,
        model_name: str,
        task_type: Optional[TaskType] = None
    ) -> Dict[str, Any]:
        """
        Get performance metrics for a specific model.

        Args:
            model_name: Name of the model
            task_type: Optional task type filter

        Returns:
            Dictionary with performance metrics
        """
        if model_name not in self.model_metrics:
            return {}

        metrics = self.model_metrics[model_name]

        # Calculate percentiles for response times
        response_times = list(metrics['response_times'])
        if response_times:
            p50 = statistics.median(response_times)
            p95 = self._percentile(response_times, 95)
            p99 = self._percentile(response_times, 99)
            avg_time = statistics.mean(response_times)
        else:
            p50 = p95 = p99 = avg_time = 0.0

        # Calculate cost metrics
        costs = list(metrics['costs'])
        if costs:
            avg_cost = statistics.mean(costs)
            total_cost = sum(costs)
        else:
            avg_cost = total_cost = 0.0

        # Calculate success rate
        total_requests = metrics['success_count'] + metrics['failure_count']
        success_rate = (
            metrics['success_count'] / total_requests if total_requests > 0 else 0.0
        ) * 100

        return {
            'model_name': model_name,
            'task_type': task_type.value if task_type else 'all',
            'total_requests': total_requests,
            'success_count': metrics['success_count'],
            'failure_count': metrics['failure_count'],
            'success_rate': success_rate,
            'avg_response_time': avg_time,
            'p50_response_time': p50,
            'p95_response_time': p95,
            'p99_response_time': p99,
            'avg_cost': avg_cost,
            'total_cost': total_cost,
            'task_type_breakdown': dict(metrics['task_types'])
        }

    def get_system_performance(self, hours: int = 24) -> Dict[str, Any]:
        """
        Get overall system performance metrics.

        Args:
            hours: Number of hours to analyze

        Returns:
            Dictionary with system-wide metrics
        """
        cutoff_time = datetime.now() - timedelta(hours=hours)

        # Filter recent requests
        recent = []
        for req in self.recent_requests:
            try:
                req_time = datetime.fromisoformat(req['start_time'])
                if req_time >= cutoff_time:
                    recent.append(req)
            except (ValueError, KeyError):
                continue

        if not recent:
            return {
                'time_range_hours': hours,
                'total_requests': 0,
                'avg_response_time': 0.0,
                'avg_cost': 0.0,
                'success_rate': 0.0
            }

        # Calculate metrics
        response_times = [req.get('total_time', 0) for req in recent if 'total_time' in req]
        costs = [req.get('total_cost', 0) for req in recent if 'total_cost' in req]

        completed_requests = [req for req in recent if req.get('status') == 'completed']
        failed_requests = [req for req in recent if req.get('status') == 'failed']

        return {
            'time_range_hours': hours,
            'total_requests': len(recent),
            'completed_requests': len(completed_requests),
            'failed_requests': len(failed_requests),
            'success_rate': (
                len(completed_requests) / len(recent) * 100 if recent else 0.0
            ),
            'avg_response_time': statistics.mean(response_times) if response_times else 0.0,
            'p95_response_time': self._percentile(response_times, 95) if response_times else 0.0,
            'avg_cost': statistics.mean(costs) if costs else 0.0,
            'total_cost': sum(costs) if costs else 0.0,
            'models_used': self._get_models_used_stats(recent)
        }

    def _get_models_used_stats(self, requests: List[Dict[str, Any]]) -> Dict[str, int]:
        """Get statistics on model usage."""
        model_counts = defaultdict(int)
        for req in requests:
            for model_data in req.get('models_used', []):
                model_name = model_data.get('model_name', 'unknown')
                model_counts[model_name] += 1
        return dict(model_counts)

    def _percentile(self, data: List[float], percentile: int) -> float:
        """
        Calculate percentile value.

        Args:
            data: List of numeric values
            percentile: Percentile to calculate (0-100)

        Returns:
            Percentile value
        """
        if not data:
            return 0.0

        sorted_data = sorted(data)
        index = (percentile / 100) * (len(sorted_data) - 1)

        if index.is_integer():
            return sorted_data[int(index)]
        else:
            lower = sorted_data[int(index)]
            upper = sorted_data[int(index) + 1]
            return lower + (upper - lower) * (index - int(index))

    def generate_performance_report(
        self,
        model_name: Optional[str] = None,
        task_type: Optional[TaskType] = None,
        hours: int = 24,
        output_format: str = 'dict'
    ) -> str:
        """
        Generate a comprehensive performance report.

        Args:
            model_name: Filter by model name
            task_type: Filter by task type
            hours: Time range in hours
            output_format: Output format ('dict', 'json', 'text')

        Returns:
            Performance report in specified format
        """
        logger.info(f"Generating performance report (hours={hours}, model={model_name})")

        # Get base metrics
        if model_name:
            report_data = self.get_model_performance(model_name, task_type)
        else:
            report_data = self.get_system_performance(hours)

        # Add timestamp and filters
        report_data['generated_at'] = datetime.now().isoformat()
        task_type_value = task_type.value if task_type else None
        report_data['filters'] = {
            'model_name': model_name,
            'task_type': task_type_value,
            'time_range_hours': hours
        }

        # Format output
        if output_format == 'json':
            return json.dumps(report_data, indent=2, ensure_ascii=False)
        elif output_format == 'text':
            return self._format_text_report(report_data)
        else:
            return report_data

    def _format_text_report(self, data: Dict[str, Any]) -> str:
        """
        Format report as human-readable text.

        Args:
            data: Report data dictionary

        Returns:
            Formatted text report
        """
        lines = []
        lines.append("=" * 80)
        lines.append("AI Orchestrator Performance Report")
        lines.append("=" * 80)
        lines.append(f"Generated: {data.get('generated_at', 'N/A')}")
        lines.append("")

        # Filters
        filters = data.get('filters', {})
        if filters.get('model_name'):
            lines.append(f"Model: {filters['model_name']}")
        else:
            lines.append("Model: All models")

        if filters.get('task_type'):
            lines.append(f"Task Type: {filters['task_type']}")
        else:
            lines.append("Task Type: All tasks")

        lines.append(f"Time Range: {filters.get('time_range_hours', 24)} hours")
        lines.append("")

        # Overall metrics
        lines.append("Overall Metrics:")
        lines.append("-" * 80)
        lines.append(f"Total Requests: {data.get('total_requests', 0)}")
        lines.append(f"Completed: {data.get('completed_requests', 0)}")
        lines.append(f"Failed: {data.get('failed_requests', 0)}")
        lines.append(f"Success Rate: {data.get('success_rate', 0):.2f}%")
        lines.append("")

        # Performance metrics
        lines.append("Performance:")
        lines.append("-" * 80)
        lines.append(f"Avg Response Time: {data.get('avg_response_time', 0):.3f}s")
        lines.append(f"P95 Response Time: {data.get('p95_response_time', 0):.3f}s")
        lines.append(f"P99 Response Time: {data.get('p99_response_time', 0):.3f}s")
        lines.append("")

        # Cost metrics
        lines.append("Cost Metrics:")
        lines.append("-" * 80)
        lines.append(f"Total Cost: ${data.get('total_cost', 0):.4f}")
        lines.append(f"Avg Cost per Request: ${data.get('avg_cost', 0):.4f}")
        lines.append("")

        # Model breakdown (for system report)
        if 'models_used' in data and data['models_used']:
            lines.append("Model Usage:")
            lines.append("-" * 80)
            for model, count in sorted(
                data['models_used'].items(),
                key=lambda x: x[1],
                reverse=True
            ):
                lines.append(f"{model}: {count} requests")
            lines.append("")

        lines.append("=" * 80)

        return "\n".join(lines)

    def export_metrics(self, file_path: str) -> bool:
        """
        Export all metrics to a JSON file.

        Args:
            file_path: Path to export file

        Returns:
            True if successful, False otherwise
        """
        try:
            export_data = {
                'exported_at': datetime.now().isoformat(),
                'request_history': self.request_history,
                'model_metrics': {
                    model: {
                        'response_times': list(metrics['response_times']),
                        'costs': list(metrics['costs']),
                        'success_count': metrics['success_count'],
                        'failure_count': metrics['failure_count'],
                        'task_types': dict(metrics['task_types'])
                    }
                    for model, metrics in self.model_metrics.items()
                }
            }

            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)

            logger.info(f"Exported metrics to {file_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to export metrics: {e}")
            return False
