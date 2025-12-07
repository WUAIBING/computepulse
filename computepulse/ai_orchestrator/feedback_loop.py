"""
Feedback Loop for the AI Orchestrator system.

This module captures validation results and user corrections,
feeding them back to the learning engine for continuous improvement.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from .models import TaskType, ValidationResult
from .learning_engine import LearningEngine


logger = logging.getLogger(__name__)


class CorrectionType(Enum):
    """Types of user corrections."""
    VALUE_CORRECTION = "value_correction"  # User corrected a specific value
    MISSING_DATA = "missing_data"  # User added missing data
    WRONG_FORMAT = "wrong_format"  # Data was in wrong format
    INVALID_DATA = "invalid_data"  # Data was invalid/incorrect
    PARTIAL_CORRECT = "partial_correct"  # Some data was correct, some not


@dataclass
class ModelFeedback:
    """Feedback for a single model's response."""
    model_name: str
    was_correct: bool
    response_time: float
    cost: float
    token_count: int
    error_type: Optional[str] = None
    error_details: Optional[str] = None


@dataclass
class ValidationFeedback:
    """Feedback from validation results."""
    request_id: str
    task_type: TaskType
    timestamp: datetime
    model_feedbacks: List[ModelFeedback]
    ground_truth: Optional[Any] = None
    validation_passed: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class UserCorrection:
    """Record of a user correction."""
    request_id: str
    correction_type: CorrectionType
    original_data: Any
    corrected_data: Any
    timestamp: datetime
    affected_models: List[str]
    notes: Optional[str] = None


class FeedbackLoop:
    """
    Captures validation results and user corrections for learning.
    
    Integrates with the Learning Engine to update confidence scores
    based on model performance feedback.
    """
    
    def __init__(
        self,
        learning_engine: LearningEngine,
        positive_weight: float = 1.0,
        negative_weight: float = 1.5,  # Negative feedback has more impact
    ):
        """
        Initialize the feedback loop.
        
        Args:
            learning_engine: Learning engine for score updates
            positive_weight: Weight for positive feedback
            negative_weight: Weight for negative feedback
        """
        self.learning_engine = learning_engine
        self.positive_weight = positive_weight
        self.negative_weight = negative_weight
        
        # In-memory feedback history (recent only)
        self._recent_feedbacks: List[ValidationFeedback] = []
        self._recent_corrections: List[UserCorrection] = []
        self._max_history = 1000
    
    def record_validation(
        self,
        request_id: str,
        task_type: TaskType,
        model_responses: Dict[str, Dict[str, Any]],
        validation_result: ValidationResult,
        ground_truth: Optional[Any] = None,
    ) -> ValidationFeedback:
        """
        Record validation results for learning.
        
        Args:
            request_id: Unique identifier for the request
            task_type: Type of task performed
            model_responses: Responses from each model with metadata
            validation_result: Result of validation checks
            ground_truth: Known correct answer (if available)
            
        Returns:
            ValidationFeedback record
        """
        model_feedbacks = []
        
        for model_name, response_data in model_responses.items():
            # Determine if model was correct
            was_correct = self._evaluate_model_correctness(
                model_name,
                response_data,
                validation_result,
                ground_truth,
            )
            
            feedback = ModelFeedback(
                model_name=model_name,
                was_correct=was_correct,
                response_time=response_data.get("response_time", 0.0),
                cost=response_data.get("cost", 0.0),
                token_count=response_data.get("token_count", 0),
                error_type=response_data.get("error_type"),
                error_details=response_data.get("error_details"),
            )
            model_feedbacks.append(feedback)
            
            # Record performance in learning engine
            self.learning_engine.record_performance(
                model_name=model_name,
                task_type=task_type,
                was_correct=was_correct,
                response_time=feedback.response_time,
                cost=feedback.cost,
                token_count=feedback.token_count,
                request_id=request_id,
            )
            
            # Apply immediate feedback
            weight = self.positive_weight if was_correct else self.negative_weight
            self.learning_engine.apply_feedback(
                model_name=model_name,
                task_type=task_type,
                was_correct=was_correct,
                weight=weight,
            )
        
        # Create feedback record
        feedback_record = ValidationFeedback(
            request_id=request_id,
            task_type=task_type,
            timestamp=datetime.now(),
            model_feedbacks=model_feedbacks,
            ground_truth=ground_truth,
            validation_passed=validation_result.is_valid,
        )
        
        # Store in history
        self._add_to_history(feedback_record)
        
        logger.info(
            f"Recorded validation feedback for request {request_id[:8]}... "
            f"({len(model_feedbacks)} models, passed={validation_result.is_valid})"
        )
        
        return feedback_record
    
    def record_user_correction(
        self,
        request_id: str,
        correction_type: CorrectionType,
        original_data: Any,
        corrected_data: Any,
        affected_models: List[str],
        task_type: TaskType,
        notes: Optional[str] = None,
    ) -> UserCorrection:
        """
        Record when a user manually corrects data.
        
        Args:
            request_id: Request ID being corrected
            correction_type: Type of correction
            original_data: Original (incorrect) data
            corrected_data: User-provided correct data
            affected_models: Models that provided incorrect data
            task_type: Type of task
            notes: Optional notes about the correction
            
        Returns:
            UserCorrection record
        """
        correction = UserCorrection(
            request_id=request_id,
            correction_type=correction_type,
            original_data=original_data,
            corrected_data=corrected_data,
            timestamp=datetime.now(),
            affected_models=affected_models,
            notes=notes,
        )
        
        # Apply negative feedback to affected models
        for model_name in affected_models:
            self.learning_engine.apply_feedback(
                model_name=model_name,
                task_type=task_type,
                was_correct=False,
                weight=self.negative_weight * 1.5,  # Extra penalty for user corrections
            )
            
            logger.info(
                f"Applied correction penalty to {model_name} for {task_type.value}"
            )
        
        # Store correction
        self._recent_corrections.append(correction)
        if len(self._recent_corrections) > self._max_history:
            self._recent_corrections.pop(0)
        
        logger.info(
            f"Recorded user correction for request {request_id[:8]}... "
            f"(type={correction_type.value}, affected={len(affected_models)} models)"
        )
        
        return correction
    
    def record_simple_feedback(
        self,
        model_name: str,
        task_type: TaskType,
        was_correct: bool,
        response_time: float = 0.0,
        cost: float = 0.0,
    ) -> None:
        """
        Record simple feedback without full validation context.
        
        Args:
            model_name: Name of the model
            task_type: Type of task
            was_correct: Whether the response was correct
            response_time: Response time in seconds
            cost: Cost of the request
        """
        self.learning_engine.record_performance(
            model_name=model_name,
            task_type=task_type,
            was_correct=was_correct,
            response_time=response_time,
            cost=cost,
            token_count=0,
        )
        
        weight = self.positive_weight if was_correct else self.negative_weight
        self.learning_engine.apply_feedback(
            model_name=model_name,
            task_type=task_type,
            was_correct=was_correct,
            weight=weight,
        )
    
    def _evaluate_model_correctness(
        self,
        model_name: str,
        response_data: Dict[str, Any],
        validation_result: ValidationResult,
        ground_truth: Optional[Any],
    ) -> bool:
        """
        Evaluate if a model's response was correct.
        
        Args:
            model_name: Name of the model
            response_data: Model's response data
            validation_result: Validation result
            ground_truth: Known correct answer
            
        Returns:
            True if model was correct
        """
        # If we have ground truth, compare directly
        if ground_truth is not None:
            model_output = response_data.get("content") or response_data.get("data")
            return self._compare_outputs(model_output, ground_truth)
        
        # Otherwise, use validation result
        if not validation_result.is_valid:
            # Check if this model's errors are in the validation errors
            model_errors = response_data.get("errors", [])
            if model_errors:
                return False
        
        # If validation passed and no specific errors, assume correct
        return validation_result.is_valid
    
    def _compare_outputs(self, output: Any, ground_truth: Any) -> bool:
        """
        Compare model output with ground truth.
        
        Args:
            output: Model's output
            ground_truth: Known correct answer
            
        Returns:
            True if outputs match
        """
        if output is None:
            return False
        
        # String comparison (case-insensitive, whitespace-normalized)
        if isinstance(ground_truth, str) and isinstance(output, str):
            return ground_truth.strip().lower() == output.strip().lower()
        
        # Numeric comparison (with tolerance)
        if isinstance(ground_truth, (int, float)) and isinstance(output, (int, float)):
            tolerance = abs(ground_truth) * 0.01  # 1% tolerance
            return abs(ground_truth - output) <= tolerance
        
        # List comparison
        if isinstance(ground_truth, list) and isinstance(output, list):
            if len(ground_truth) != len(output):
                return False
            return all(
                self._compare_outputs(a, b) 
                for a, b in zip(ground_truth, output)
            )
        
        # Dict comparison
        if isinstance(ground_truth, dict) and isinstance(output, dict):
            if set(ground_truth.keys()) != set(output.keys()):
                return False
            return all(
                self._compare_outputs(ground_truth[k], output[k])
                for k in ground_truth.keys()
            )
        
        # Default: exact match
        return ground_truth == output
    
    def _add_to_history(self, feedback: ValidationFeedback) -> None:
        """Add feedback to history, maintaining max size."""
        self._recent_feedbacks.append(feedback)
        if len(self._recent_feedbacks) > self._max_history:
            self._recent_feedbacks.pop(0)
    
    def get_recent_feedbacks(
        self,
        limit: int = 100,
        task_type: Optional[TaskType] = None,
    ) -> List[ValidationFeedback]:
        """
        Get recent feedback records.
        
        Args:
            limit: Maximum number of records
            task_type: Optional filter by task type
            
        Returns:
            List of recent feedbacks
        """
        feedbacks = self._recent_feedbacks
        
        if task_type:
            feedbacks = [f for f in feedbacks if f.task_type == task_type]
        
        return feedbacks[-limit:]
    
    def get_recent_corrections(
        self,
        limit: int = 100,
        correction_type: Optional[CorrectionType] = None,
    ) -> List[UserCorrection]:
        """
        Get recent user corrections.
        
        Args:
            limit: Maximum number of records
            correction_type: Optional filter by correction type
            
        Returns:
            List of recent corrections
        """
        corrections = self._recent_corrections
        
        if correction_type:
            corrections = [c for c in corrections if c.correction_type == correction_type]
        
        return corrections[-limit:]
    
    def get_model_accuracy_summary(
        self,
        model_name: Optional[str] = None,
    ) -> Dict[str, Dict[str, float]]:
        """
        Get accuracy summary for models from recent feedbacks.
        
        Args:
            model_name: Optional filter by model name
            
        Returns:
            Dict of model_name -> {correct, total, accuracy}
        """
        summary: Dict[str, Dict[str, float]] = {}
        
        for feedback in self._recent_feedbacks:
            for model_feedback in feedback.model_feedbacks:
                if model_name and model_feedback.model_name != model_name:
                    continue
                
                name = model_feedback.model_name
                if name not in summary:
                    summary[name] = {"correct": 0, "total": 0, "accuracy": 0.0}
                
                summary[name]["total"] += 1
                if model_feedback.was_correct:
                    summary[name]["correct"] += 1
        
        # Calculate accuracy
        for name in summary:
            total = summary[name]["total"]
            if total > 0:
                summary[name]["accuracy"] = summary[name]["correct"] / total
        
        return summary
    
    def trigger_confidence_update(self) -> None:
        """Trigger a full confidence score update in the learning engine."""
        self.learning_engine.update_confidence_scores()
        logger.info("Triggered confidence score update from feedback loop")
