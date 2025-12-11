"""
Learning Engine for calculating and updating confidence scores.
"""

import logging
from collections import defaultdict
from typing import Dict, List, Tuple, Optional
import math

from .models import AIModel, TaskType, PerformanceRecord
from .config import OrchestratorConfig
from .storage import StorageManager


logger = logging.getLogger(__name__)


class LearningEngine:
    """
    Analyzes performance data and updates confidence scores for AI models.
    
    Uses Exponentially Weighted Moving Average (EWMA) to calculate confidence
    scores, giving more weight to recent performance data.
    """
    
    def __init__(self, config: OrchestratorConfig, storage: StorageManager):
        self.config = config
        self.storage = storage
        
        # Load existing confidence scores
        self.confidence_scores: Dict[Tuple[str, TaskType], float] = (
            storage.load_confidence_scores()
        )
        
        # Cache for performance history (model_name, task_type) -> List[PerformanceRecord]
        self.performance_cache: Dict[Tuple[str, TaskType], List[PerformanceRecord]] = defaultdict(list)
        
        logger.info(f"Learning Engine initialized with {len(self.confidence_scores)} existing scores")
    
    def record_performance(
        self,
        model_name: str,
        task_type: TaskType,
        was_correct: bool,
        response_time: float,
        cost: float,
        token_count: int = 0
    ) -> None:
        """
        Record a performance data point.
        
        Args:
            model_name: Name of the AI model
            task_type: Type of task performed
            was_correct: Whether the model's response was correct
            response_time: Time taken to respond (seconds)
            cost: Cost of the request (USD)
            token_count: Number of tokens used
        """
        from datetime import datetime
        
        record = PerformanceRecord(
            timestamp=datetime.now(),
            model_name=model_name,
            task_type=task_type,
            was_correct=was_correct,
            response_time=response_time,
            cost=cost,
            token_count=token_count
        )
        
        # Append to storage
        self.storage.append_performance_record(record)
        
        # Add to cache
        key = (model_name, task_type)
        self.performance_cache[key].append(record)
        
        logger.debug(f"Recorded performance for {model_name} on {task_type.value}: correct={was_correct}")
    
    def calculate_confidence_score(
        self,
        performance_history: List[PerformanceRecord]
    ) -> float:
        """
        Calculate confidence score using Exponentially Weighted Moving Average.
        
        Recent performance has more weight than older performance.
        
        Args:
            performance_history: List of performance records (newest first)
            
        Returns:
            Confidence score between 0 and 1
        """
        if not performance_history:
            return 0.5  # Default neutral score for new models
        
        decay_factor = self.config.confidence_decay_factor
        
        # Calculate weighted accuracy
        total_weight = 0.0
        weighted_correct = 0.0
        
        # Reverse to process oldest first, then apply decay
        for i, record in enumerate(reversed(performance_history)):
            weight = decay_factor ** i
            total_weight += weight
            
            if record.was_correct:
                weighted_correct += weight
        
        accuracy = weighted_correct / total_weight if total_weight > 0 else 0.5
        
        # Adjust for sample size (more data = more confidence in the score)
        sample_size = len(performance_history)
        min_samples = self.config.min_samples_for_confidence
        
        # Base adjustment
        confidence_adjustment = min(1.0, sample_size / min_samples)
        
        # BOOST: If accuracy is exceptional (>0.9) even with few samples (but >2), trust it faster
        # This allows "Pro Preview" models to prove themselves quickly
        if accuracy > 0.9 and sample_size > 2 and confidence_adjustment < 1.0:
            confidence_adjustment = min(1.0, confidence_adjustment * 1.5)
            
        # Final score: blend between accuracy and neutral (0.5) based on sample size
        confidence = accuracy * confidence_adjustment + 0.5 * (1 - confidence_adjustment)
        
        return confidence
    
    def update_confidence_scores(self) -> None:
        """
        Recalculate confidence scores based on accumulated performance data.
        
        This should be called periodically or after significant new data is collected.
        """
        logger.info("Updating confidence scores...")
        
        # Get all unique (model, task_type) combinations from storage
        all_records = self.storage.query_performance_history(limit=10000)
        
        # Group by (model_name, task_type)
        grouped_records: Dict[Tuple[str, TaskType], List[PerformanceRecord]] = defaultdict(list)
        for record in all_records:
            key = (record.model_name, record.task_type)
            grouped_records[key].append(record)
        
        # Calculate new scores
        updated_count = 0
        for key, records in grouped_records.items():
            model_name, task_type = key
            
            # Sort by timestamp (newest first for EWMA)
            records.sort(key=lambda r: r.timestamp, reverse=True)
            
            # Calculate new confidence score
            new_score = self.calculate_confidence_score(records)
            
            # Get old score for comparison
            old_score = self.confidence_scores.get(key, 0.5)
            
            # Apply smoothing to avoid drastic changes
            smoothing = self.config.confidence_smoothing_factor
            smoothed_score = smoothing * new_score + (1 - smoothing) * old_score
            
            # Update score
            self.confidence_scores[key] = smoothed_score
            
            # Log significant changes
            if abs(new_score - old_score) > 0.1:
                logger.info(
                    f"{model_name} confidence for {task_type.value} "
                    f"changed: {old_score:.3f} → {smoothed_score:.3f} "
                    f"(based on {len(records)} samples)"
                )
            
            updated_count += 1
        
        # Persist updated scores
        self.storage.save_confidence_scores(self.confidence_scores)
        
        logger.info(f"Updated {updated_count} confidence scores")
    
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
            Confidence score between 0 and 1 (default 0.5 for unknown combinations)
        """
        return self.confidence_scores.get((model_name, task_type), 0.5)
    
    def get_all_scores_for_task(
        self,
        task_type: TaskType
    ) -> Dict[str, float]:
        """
        Get confidence scores for all models for a specific task type.
        
        Args:
            task_type: Type of task
            
        Returns:
            Dictionary mapping model names to confidence scores
        """
        scores = {}
        for (model_name, t_type), score in self.confidence_scores.items():
            if t_type == task_type:
                scores[model_name] = score
        
        return scores
    
    def get_performance_report(
        self,
        model_name: Optional[str] = None,
        task_type: Optional[TaskType] = None
    ) -> Dict:
        """
        Generate a performance report with filtering.
        
        Args:
            model_name: Filter by model name (optional)
            task_type: Filter by task type (optional)
            
        Returns:
            Dictionary with performance metrics and trends
        """
        summary = self.storage.get_performance_summary(
            model_name=model_name,
            task_type=task_type
        )
        
        # Add confidence scores
        if model_name and task_type:
            summary["confidence_score"] = self.get_confidence_score(model_name, task_type)
        elif task_type:
            summary["confidence_scores"] = self.get_all_scores_for_task(task_type)
        
        return summary
    
    def detect_underperformance(
        self,
        model_name: str,
        task_type: TaskType,
        threshold: float = 0.6
    ) -> bool:
        """
        Detect if a model is consistently underperforming for a task type.
        
        Args:
            model_name: Name of the AI model
            task_type: Type of task
            threshold: Confidence threshold below which model is underperforming
            
        Returns:
            True if model is underperforming, False otherwise
        """
        confidence = self.get_confidence_score(model_name, task_type)
        
        # Check if we have enough data
        records = self.storage.query_performance_history(
            model_name=model_name,
            task_type=task_type,
            limit=100
        )
        
        if len(records) < self.config.min_samples_for_confidence:
            return False  # Not enough data to determine
        
        is_underperforming = confidence < threshold
        
        if is_underperforming:
            logger.warning(
                f"{model_name} is underperforming on {task_type.value} "
                f"(confidence: {confidence:.3f} < {threshold:.3f})"
            )
        
        return is_underperforming
