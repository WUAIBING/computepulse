"""
Performance Tracker for the AI Orchestrator system.

This module monitors and reports on AI model performance metrics,
including response times, costs, accuracy, and anomaly detection.
"""

import logging
import statistics
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from .models import TaskType, PerformanceRecord, MetricsSummary
from .storage import StorageManager


logger = logging.getLogger(__name__)


@dataclass
class RequestMetrics:
    """Metrics for a single request."""
    request_id: str
    task_type: TaskType
    models_used: List[str]
    start_time: datetime
    end_time: Optional[datetime] = None
    total_time: float = 0.0
    total_cost: float = 0.0
    success: bool = True
    model_responses: Dict[str, "ModelResponseMetrics"] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "request_id": self.request_id,
            "task_type": self.task_type.value,
            "models_used": self.models_used,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "total_time": self.total_time,
            "total_cost": self.total_cost,
            "success": self.success,
            "model_responses": {k: v.to_dict() for k, v in self.model_responses.items()},
        }


@dataclass
class ModelResponseMetrics:
    """Metrics for a single model response."""
    model_name: str
    response_time: float
    token_count: int
    cost: float
    success: bool
    timestamp: datetime = field(default_factory=datetime.now)
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "model_name": self.model_name,
            "response_time": self.response_time,
            "token_count": self.token_count,
            "cost": self.cost,
            "success": self.success,
            "timestamp": self.timestamp.isoformat(),
            "error": self.error,
        }


class PerformanceTracker:
    """
    Tracks and reports on AI model performance.
    
    Provides request tracking, model response tracking, metrics aggregation,
    and anomaly detection capabilities.
    """
    
    # Anomaly detection thresholds
    ANOMALY_RESPONSE_TIME_MULTIPLIER = 3.0  # 3x average is anomaly
    ANOMALY_MIN_SAMPLES = 10  # Need at least 10 samples for anomaly detection
    
    def __init__(self, storage: StorageManager):
        """
        Initialize the performance tracker.
        
        Args:
            storage: Storage manager for persistence
        """
        self.storage = storage
        self._active_requests: Dict[str, RequestMetrics] = {}
        self._model_baselines: Dict[Tuple[str, TaskType], Dict[str, float]] = {}
    
    def generate_request_id(self) -> str:
        """Generate a unique request ID."""
        return str(uuid.uuid4())
    
    def start_request(
        self,
        task_type: TaskType,
        models_used: List[str],
        request_id: Optional[str] = None,
    ) -> str:
        """
        Start tracking a new request.
        
        Args:
            task_type: Type of task being processed
            models_used: List of model names being used
            request_id: Optional custom request ID
            
        Returns:
            The request ID
        """
        if request_id is None:
            request_id = self.generate_request_id()
        
        metrics = RequestMetrics(
            request_id=request_id,
            task_type=task_type,
            models_used=models_used,
            start_time=datetime.now(),
        )
        
        self._active_requests[request_id] = metrics
        logger.debug(f"Started tracking request {request_id[:8]}...")
        
        return request_id
    
    def end_request(
        self,
        request_id: str,
        success: bool = True,
    ) -> Optional[RequestMetrics]:
        """
        End tracking for a request.
        
        Args:
            request_id: The request ID
            success: Whether the request was successful
            
        Returns:
            The completed request metrics, or None if not found
        """
        metrics = self._active_requests.pop(request_id, None)
        if metrics is None:
            logger.warning(f"Request {request_id} not found in active requests")
            return None
        
        metrics.end_time = datetime.now()
        metrics.total_time = (metrics.end_time - metrics.start_time).total_seconds()
        metrics.success = success
        
        # Calculate total cost from model responses
        metrics.total_cost = sum(
            r.cost for r in metrics.model_responses.values()
        )
        
        logger.debug(
            f"Completed request {request_id[:8]}... "
            f"time={metrics.total_time:.2f}s cost=${metrics.total_cost:.4f}"
        )
        
        return metrics
    
    def track_model_response(
        self,
        request_id: str,
        model_name: str,
        response_time: float,
        token_count: int,
        cost: float,
        success: bool,
        error: Optional[str] = None,
    ) -> None:
        """
        Track metrics for an individual model response.
        
        Args:
            request_id: The request ID
            model_name: Name of the model
            response_time: Response time in seconds
            token_count: Number of tokens used
            cost: Cost of the request
            success: Whether the response was successful
            error: Error message if failed
        """
        metrics = self._active_requests.get(request_id)
        if metrics is None:
            logger.warning(f"Request {request_id} not found, creating standalone tracking")
            return
        
        response_metrics = ModelResponseMetrics(
            model_name=model_name,
            response_time=response_time,
            token_count=token_count,
            cost=cost,
            success=success,
            error=error,
        )
        
        metrics.model_responses[model_name] = response_metrics
        
        # Check for anomalies
        self._check_anomaly(model_name, metrics.task_type, response_time)
        
        logger.debug(
            f"Tracked {model_name} response: time={response_time:.2f}s "
            f"tokens={token_count} cost=${cost:.4f}"
        )
    
    def _check_anomaly(
        self,
        model_name: str,
        task_type: TaskType,
        response_time: float,
    ) -> None:
        """Check if a response time is anomalous."""
        key = (model_name, task_type)
        baseline = self._model_baselines.get(key)
        
        if baseline is None:
            return
        
        avg_time = baseline.get("avg_response_time", 0)
        sample_count = baseline.get("sample_count", 0)
        
        if sample_count < self.ANOMALY_MIN_SAMPLES:
            return
        
        if response_time > avg_time * self.ANOMALY_RESPONSE_TIME_MULTIPLIER:
            logger.warning(
                f"ANOMALY: {model_name} response time {response_time:.2f}s "
                f"is {response_time/avg_time:.1f}x the average ({avg_time:.2f}s) "
                f"for {task_type.value}"
            )
    
    def update_baselines(self) -> None:
        """Update baseline metrics from historical data."""
        # Get recent performance history
        history = self.storage.query_performance_history(limit=10000)
        
        # Group by model and task type
        grouped: Dict[Tuple[str, TaskType], List[PerformanceRecord]] = {}
        for record in history:
            key = (record.model_name, record.task_type)
            if key not in grouped:
                grouped[key] = []
            grouped[key].append(record)
        
        # Calculate baselines
        for key, records in grouped.items():
            response_times = [r.response_time for r in records]
            self._model_baselines[key] = {
                "avg_response_time": statistics.mean(response_times) if response_times else 0,
                "sample_count": len(records),
            }
        
        logger.info(f"Updated baselines for {len(grouped)} model-task combinations")
    
    def get_metrics_summary(
        self,
        model_name: Optional[str] = None,
        task_type: Optional[TaskType] = None,
        time_range_days: Optional[int] = None,
    ) -> MetricsSummary:
        """
        Get aggregated metrics for a time period.
        
        Args:
            model_name: Optional model name filter
            task_type: Optional task type filter
            time_range_days: Optional time range in days
            
        Returns:
            MetricsSummary with aggregated metrics
        """
        # Query history
        history = self.storage.query_performance_history(
            model_name=model_name,
            task_type=task_type,
            limit=10000,
        )
        
        # Apply time range filter
        time_range_start = None
        time_range_end = datetime.now()
        
        if time_range_days:
            time_range_start = time_range_end - timedelta(days=time_range_days)
            history = [r for r in history if r.timestamp >= time_range_start]
        
        if not history:
            return MetricsSummary(
                total_requests=0,
                accuracy=0.0,
                avg_response_time=0.0,
                p50_response_time=0.0,
                p95_response_time=0.0,
                p99_response_time=0.0,
                total_cost=0.0,
                avg_cost=0.0,
                success_rate=0.0,
                time_range_start=time_range_start,
                time_range_end=time_range_end,
            )
        
        # Calculate metrics
        total = len(history)
        correct = sum(1 for r in history if r.was_correct)
        response_times = sorted([r.response_time for r in history])
        costs = [r.cost for r in history]
        
        return MetricsSummary(
            total_requests=total,
            accuracy=correct / total,
            avg_response_time=statistics.mean(response_times),
            p50_response_time=self._percentile(response_times, 50),
            p95_response_time=self._percentile(response_times, 95),
            p99_response_time=self._percentile(response_times, 99),
            total_cost=sum(costs),
            avg_cost=statistics.mean(costs),
            success_rate=correct / total,
            time_range_start=time_range_start,
            time_range_end=time_range_end,
        )
    
    def _percentile(self, sorted_data: List[float], percentile: int) -> float:
        """Calculate percentile from sorted data."""
        if not sorted_data:
            return 0.0
        
        index = (len(sorted_data) - 1) * percentile / 100
        lower = int(index)
        upper = lower + 1
        
        if upper >= len(sorted_data):
            return sorted_data[-1]
        
        weight = index - lower
        return sorted_data[lower] * (1 - weight) + sorted_data[upper] * weight
    
    def get_model_comparison(
        self,
        task_type: Optional[TaskType] = None,
        time_range_days: int = 7,
    ) -> Dict[str, Dict[str, Any]]:
        """
        Get comparison metrics across all models.
        
        Args:
            task_type: Optional task type filter
            time_range_days: Time range in days
            
        Returns:
            Dictionary mapping model names to their metrics
        """
        history = self.storage.query_performance_history(
            task_type=task_type,
            limit=10000,
        )
        
        # Apply time filter
        cutoff = datetime.now() - timedelta(days=time_range_days)
        history = [r for r in history if r.timestamp >= cutoff]
        
        # Group by model
        by_model: Dict[str, List[PerformanceRecord]] = {}
        for record in history:
            if record.model_name not in by_model:
                by_model[record.model_name] = []
            by_model[record.model_name].append(record)
        
        # Calculate metrics per model
        comparison = {}
        for model_name, records in by_model.items():
            response_times = [r.response_time for r in records]
            costs = [r.cost for r in records]
            correct = sum(1 for r in records if r.was_correct)
            
            comparison[model_name] = {
                "total_requests": len(records),
                "accuracy": correct / len(records) if records else 0,
                "avg_response_time": statistics.mean(response_times) if response_times else 0,
                "avg_cost": statistics.mean(costs) if costs else 0,
                "total_cost": sum(costs),
            }
        
        return comparison
