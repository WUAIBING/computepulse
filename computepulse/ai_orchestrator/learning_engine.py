"""
Learning Engine for the AI Orchestrator system.

This module implements the learning engine that tracks AI model performance,
calculates confidence scores using EWMA, and provides performance analysis.
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

from .models import (
    TaskType,
    PerformanceRecord,
    ConfidenceScore,
    MetricsSummary,
)
from .storage import StorageManager


logger = logging.getLogger(__name__)


@dataclass
class PerformanceReport:
    """Performance report for AI models."""
    model_name: Optional[str]
    task_type: Optional[TaskType]
    total_requests: int
    accuracy: float
    avg_response_time: float
    avg_cost: float
    confidence_score: float
    time_range_start: Optional[datetime]
    time_range_end: Optional[datetime]
    
    def to_dict(self) -> dict:
        return {
            "model_name": self.model_name,
            "task_type": self.task_type.value if self.task_type else None,
            "total_requests": self.total_requests,
            "accuracy": self.accuracy,
            "avg_response_time": self.avg_response_time,
            "avg_cost": self.avg_cost,
            "confidence_score": self.confidence_score,
            "time_range_start": self.time_range_start.isoformat() if self.time_range_start else None,
            "time_range_end": self.time_range_end.isoformat() if self.time_range_end else None,
        }


class LearningEngine:
    """
    Learns from AI model performance to optimize future selections.
    
    Uses exponentially weighted moving average (EWMA) to calculate
    confidence scores that reflect recent performance more heavily.
    """
    
    # Default confidence score for new model-task combinations
    DEFAULT_CONFIDENCE = 0.5
    
    # EWMA decay factor (higher = more weight on recent data)
    DECAY_FACTOR = 0.95
    
    # Smoothing factor for score updates (prevents drastic changes)
    SMOOTHING_FACTOR = 0.7
    
    # Minimum samples for full confidence
    MIN_SAMPLES_FOR_FULL_CONFIDENCE = 100
    
    def __init__(
        self,
        storage: StorageManager,
        decay_factor: float = 0.95,
        smoothing_factor: float = 0.7,
    ):
        """
        Initialize the learning engine.
        
        Args:
            storage: Storage manager for persistence
            decay_factor: EWMA decay factor
            smoothing_factor: Score update smoothing factor
        """
        self.storage = storage
        self.decay_factor = decay_factor
        self.smoothing_factor = smoothing_factor
        
        # In-memory confidence scores cache
        self._confidence_scores: Dict[Tuple[str, TaskType], ConfidenceScore] = {}
        
        # Load existing scores from storage
        self._load_confidence_scores()
    
    def _load_confidence_scores(self) -> None:
        """Load confidence scores from storage."""
        try:
            scores = self.storage.load_confidence_scores()
            for score in scores:
                key = (score.model_name, score.task_type)
                self._confidence_scores[key] = score
            logger.info(f"Loaded {len(scores)} confidence scores from storage")
        except Exception as e:
            logger.warning(f"Failed to load confidence scores: {e}")
    
    def _save_confidence_scores(self) -> None:
        """Save confidence scores to storage."""
        try:
            scores = list(self._confidence_scores.values())
            self.storage.save_confidence_scores(scores)
        except Exception as e:
            logger.error(f"Failed to save confidence scores: {e}")
    
    def record_performance(
        self,
        model_name: str,
        task_type: TaskType,
        was_correct: bool,
        response_time: float,
        cost: float,
        token_count: int = 0,
        request_id: Optional[str] = None,
    ) -> None:
        """
        Record a performance data point.
        
        Args:
            model_name: Name of the AI model
            task_type: Type of task performed
            was_correct: Whether the response was correct
            response_time: Response time in seconds
            cost: Cost of the request
            token_count: Number of tokens used
            request_id: Optional request ID for tracking
        """
        record = PerformanceRecord(
            timestamp=datetime.now(),
            model_name=model_name,
            task_type=task_type,
            was_correct=was_correct,
            response_time=response_time,
            cost=cost,
            token_count=token_count,
            request_id=request_id,
        )
        
        # Append to storage
        self.storage.append_performance_record(record)
        
        logger.debug(
            f"Recorded performance: {model_name} on {task_type.value} - "
            f"correct={was_correct}, time={response_time:.2f}s"
        )
    
    def update_confidence_scores(self) -> None:
        """Recalculate confidence scores based on accumulated data."""
        # Get all unique model-task combinations from history
        history = self.storage.query_performance_history(limit=10000)
        
        # Group by model and task type
        grouped: Dict[Tuple[str, TaskType], List[PerformanceRecord]] = {}
        for record in history:
            key = (record.model_name, record.task_type)
            if key not in grouped:
                grouped[key] = []
            grouped[key].append(record)
        
        # Update scores for each combination
        for (model_name, task_type), records in grouped.items():
            new_score = self._calculate_confidence_score(records)
            self._update_score(model_name, task_type, new_score, len(records))
        
        # Save updated scores
        self._save_confidence_scores()
        
        logger.info(f"Updated {len(grouped)} confidence scores")
    
    def _calculate_confidence_score(
        self, 
        performance_history: List[PerformanceRecord]
    ) -> float:
        """
        Calculate confidence score using EWMA.
        
        Args:
            performance_history: List of performance records
            
        Returns:
            Confidence score between 0 and 1
        """
        if not performance_history:
            return self.DEFAULT_CONFIDENCE
        
        # Sort by timestamp (most recent first)
        sorted_history = sorted(
            performance_history, 
            key=lambda r: r.timestamp, 
            reverse=True
        )
        
        # Calculate weighted accuracy using EWMA
        total_weight = 0.0
        weighted_correct = 0.0
        
        for i, record in enumerate(sorted_history):
            weight = self.decay_factor ** i
            total_weight += weight
            
            if record.was_correct:
                weighted_correct += weight
        
        accuracy = weighted_correct / total_weight if total_weight > 0 else 0.5
        
        # Adjust for sample size
        sample_size = len(performance_history)
        confidence_adjustment = min(
            1.0, 
            sample_size / self.MIN_SAMPLES_FOR_FULL_CONFIDENCE
        )
        
        # Final score: blend accuracy with default based on sample size
        confidence = (
            accuracy * confidence_adjustment + 
            self.DEFAULT_CONFIDENCE * (1 - confidence_adjustment)
        )
        
        return confidence
    
    def _update_score(
        self,
        model_name: str,
        task_type: TaskType,
        new_score: float,
        sample_count: int,
    ) -> None:
        """
        Update confidence score with smoothing.
        
        Args:
            model_name: Name of the AI model
            task_type: Type of task
            new_score: Newly calculated score
            sample_count: Number of samples used
        """
        key = (model_name, task_type)
        old_score_obj = self._confidence_scores.get(key)
        old_score = old_score_obj.score if old_score_obj else self.DEFAULT_CONFIDENCE
        
        # Apply smoothing
        smoothed_score = (
            self.smoothing_factor * new_score + 
            (1 - self.smoothing_factor) * old_score
        )
        
        # Create or update score object
        self._confidence_scores[key] = ConfidenceScore(
            model_name=model_name,
            task_type=task_type,
            score=smoothed_score,
            sample_count=sample_count,
            last_updated=datetime.now(),
        )
        
        # Log significant changes
        if abs(new_score - old_score) > 0.1:
            logger.info(
                f"{model_name} confidence for {task_type.value} "
                f"changed: {old_score:.2f} → {smoothed_score:.2f}"
            )
    
    def get_confidence_score(
        self, 
        model_name: str, 
        task_type: TaskType
    ) -> float:
        """
        Get current confidence score for a model on a task type.
        
        Args:
            model_name: Name of the AI model
            task_type: Type of task
            
        Returns:
            Confidence score between 0 and 1
        """
        key = (model_name, task_type)
        score_obj = self._confidence_scores.get(key)
        return score_obj.score if score_obj else self.DEFAULT_CONFIDENCE
    
    def get_all_confidence_scores(
        self, 
        model_name: Optional[str] = None
    ) -> Dict[Tuple[str, TaskType], float]:
        """
        Get all confidence scores, optionally filtered by model.
        
        Args:
            model_name: Optional model name filter
            
        Returns:
            Dictionary of (model, task_type) -> score
        """
        result = {}
        for key, score_obj in self._confidence_scores.items():
            if model_name is None or key[0] == model_name:
                result[key] = score_obj.score
        return result
    
    def get_performance_report(
        self,
        model_name: Optional[str] = None,
        task_type: Optional[TaskType] = None,
        time_range_days: Optional[int] = None,
    ) -> PerformanceReport:
        """
        Generate performance report with filtering.
        
        Args:
            model_name: Optional model name filter
            task_type: Optional task type filter
            time_range_days: Optional time range in days
            
        Returns:
            PerformanceReport with aggregated metrics
        """
        # Query history with filters
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
            history = [
                r for r in history 
                if r.timestamp >= time_range_start
            ]
        
        if not history:
            return PerformanceReport(
                model_name=model_name,
                task_type=task_type,
                total_requests=0,
                accuracy=0.0,
                avg_response_time=0.0,
                avg_cost=0.0,
                confidence_score=self.DEFAULT_CONFIDENCE,
                time_range_start=time_range_start,
                time_range_end=time_range_end,
            )
        
        # Calculate metrics
        total = len(history)
        correct = sum(1 for r in history if r.was_correct)
        accuracy = correct / total
        avg_response_time = sum(r.response_time for r in history) / total
        avg_cost = sum(r.cost for r in history) / total
        
        # Get confidence score
        if model_name and task_type:
            confidence = self.get_confidence_score(model_name, task_type)
        else:
            confidence = self.DEFAULT_CONFIDENCE
        
        return PerformanceReport(
            model_name=model_name,
            task_type=task_type,
            total_requests=total,
            accuracy=accuracy,
            avg_response_time=avg_response_time,
            avg_cost=avg_cost,
            confidence_score=confidence,
            time_range_start=time_range_start,
            time_range_end=time_range_end,
        )
    
    def get_best_model_for_task(
        self, 
        task_type: TaskType,
        min_confidence: float = 0.0,
    ) -> Optional[str]:
        """
        Get the best performing model for a task type.
        
        Args:
            task_type: Type of task
            min_confidence: Minimum confidence threshold
            
        Returns:
            Model name or None if no model meets threshold
        """
        best_model = None
        best_score = min_confidence
        
        for (model_name, tt), score_obj in self._confidence_scores.items():
            if tt == task_type and score_obj.score > best_score:
                best_score = score_obj.score
                best_model = model_name
        
        return best_model
    
    def get_models_above_threshold(
        self,
        task_type: TaskType,
        threshold: float = 0.5,
    ) -> List[Tuple[str, float]]:
        """
        Get all models above a confidence threshold for a task.
        
        Args:
            task_type: Type of task
            threshold: Minimum confidence threshold
            
        Returns:
            List of (model_name, score) tuples, sorted by score descending
        """
        models = []
        
        for (model_name, tt), score_obj in self._confidence_scores.items():
            if tt == task_type and score_obj.score >= threshold:
                models.append((model_name, score_obj.score))
        
        # Sort by score descending
        models.sort(key=lambda x: x[1], reverse=True)
        return models
    
    def apply_feedback(
        self,
        model_name: str,
        task_type: TaskType,
        was_correct: bool,
        weight: float = 1.0,
    ) -> None:
        """
        Apply immediate feedback to update confidence score.
        
        This is a lightweight update that doesn't require full recalculation.
        
        Args:
            model_name: Name of the AI model
            task_type: Type of task
            was_correct: Whether the response was correct
            weight: Weight of this feedback (default 1.0)
        """
        key = (model_name, task_type)
        current = self._confidence_scores.get(key)
        
        if current is None:
            current = ConfidenceScore(
                model_name=model_name,
                task_type=task_type,
                score=self.DEFAULT_CONFIDENCE,
                sample_count=0,
            )
        
        # Calculate adjustment
        if was_correct:
            adjustment = 0.02 * weight  # Positive reinforcement
        else:
            adjustment = -0.05 * weight  # Negative reinforcement (stronger)
        
        # Apply adjustment with bounds
        new_score = max(0.0, min(1.0, current.score + adjustment))
        
        self._confidence_scores[key] = ConfidenceScore(
            model_name=model_name,
            task_type=task_type,
            score=new_score,
            sample_count=current.sample_count + 1,
            last_updated=datetime.now(),
        )
        
        logger.debug(
            f"Applied feedback to {model_name}/{task_type.value}: "
            f"{current.score:.3f} → {new_score:.3f}"
        )
