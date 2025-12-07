"""
Feedback Loop - Captures validation results and user corrections for continuous learning.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from .config import OrchestratorConfig
from .models import TaskType, ValidationResult
from .learning_engine import LearningEngine
from .storage import StorageManager

logger = logging.getLogger(__name__)


class FeedbackLoop:
    """
    Captures feedback and corrections for continuous learning.

    Features:
    - Validation result capture
    - User correction recording
    - Integration with Learning Engine
    - Performance tracking
    """

    def __init__(
        self,
        config: OrchestratorConfig,
        learning_engine: LearningEngine,
        storage: StorageManager
    ):
        """
        Initialize the feedback loop.

        Args:
            config: Orchestrator configuration
            learning_engine: Learning engine for updating confidence scores
            storage: Storage manager for persistence
        """
        self.config = config
        self.learning_engine = learning_engine
        self.storage = storage

        logger.info("Feedback Loop initialized")

    def record_validation_result(
        self,
        request_id: str,
        task_type: TaskType,
        merged_result: Any,
        validation_result: ValidationResult,
        model_responses: Dict[str, Any]
    ) -> None:
        """
        Record the result of data validation.

        Args:
            request_id: ID of the request
            task_type: Type of task
            merged_result: The merged result from AI models
            validation_result: Result of validation
            model_responses: Responses from individual models
        """
        if not self.config.enable_feedback_loop:
            logger.debug("Feedback loop disabled, skipping validation recording")
            return

        try:
            logger.info(f"Recording validation result for request {request_id}")

            # Record feedback for each model
            for model_name, response in model_responses.items():
                was_correct = validation_result.is_valid

                # Record performance
                self.learning_engine.record_performance(
                    model_name=model_name,
                    task_type=task_type,
                    was_correct=was_correct,
                    response_time=response.get('response_time', 0.0),
                    cost=response.get('cost', 0.0),
                    token_count=response.get('token_count', 0)
                )

                logger.debug(
                    f"Recorded validation feedback for {model_name}: "
                    f"correct={was_correct}"
                )

            # Trigger confidence score updates
            self.learning_engine.update_confidence_scores()

            # Log validation details
            logger.info(
                f"Validation completed: valid={validation_result.is_valid}, "
                f"errors={len(validation_result.errors)}, "
                f"warnings={len(validation_result.warnings)}"
            )

        except Exception as e:
            logger.error(f"Error recording validation result: {e}")

    def record_user_correction(
        self,
        request_id: str,
        model_name: str,
        task_type: TaskType,
        original_result: Any,
        corrected_result: Any,
        correction_type: str
    ) -> None:
        """
        Record a user correction to a model's result.

        Args:
            request_id: ID of the request
            model_name: Name of the model that produced the result
            task_type: Type of task
            original_result: The original (incorrect) result
            corrected_result: The corrected result
            correction_type: Type of correction (e.g., "factual", "format", "style")
        """
        if not self.config.enable_feedback_loop:
            logger.debug("Feedback loop disabled, skipping correction recording")
            return

        try:
            logger.info(
                f"Recording user correction for request {request_id}, "
                f"model {model_name}, type {correction_type}"
            )

            # Negative reinforcement: mark as incorrect
            self.learning_engine.record_performance(
                model_name=model_name,
                task_type=task_type,
                was_correct=False,
                response_time=0.0,  # Unknown from correction
                cost=0.0,  # Unknown from correction
                token_count=0  # Unknown from correction
            )

            # Store correction metadata
            correction_data = {
                "request_id": request_id,
                "model_name": model_name,
                "task_type": task_type.value,
                "correction_type": correction_type,
                "original_result": str(original_result),
                "corrected_result": str(corrected_result),
                "timestamp": datetime.now().isoformat()
            }

            # Save to storage
            corrections_file = self.storage.get_corrections_file()
            self.storage._append_to_jsonl(corrections_file, correction_data)

            # Trigger confidence score update
            self.learning_engine.update_confidence_scores()

            logger.info(
                f"User correction recorded for {model_name} on {task_type.value}"
            )

        except Exception as e:
            logger.error(f"Error recording user correction: {e}")

    def record_validation_feedback(
        self,
        request_id: str,
        model_name: str,
        task_type: TaskType,
        was_correct: bool,
        validation_details: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Record explicit validation feedback for a model's response.

        Args:
            request_id: ID of the request
            model_name: Name of the model
            task_type: Type of task
            was_correct: Whether the response was correct
            validation_details: Additional validation details
        """
        if not self.config.enable_feedback_loop:
            logger.debug("Feedback loop disabled, skipping feedback recording")
            return

        try:
            logger.info(
                f"Recording validation feedback for {model_name} "
                f"on request {request_id}: correct={was_correct}"
            )

            # Record performance
            self.learning_engine.record_performance(
                model_name=model_name,
                task_type=task_type,
                was_correct=was_correct,
                response_time=validation_details.get('response_time', 0.0) if validation_details else 0.0,
                cost=validation_details.get('cost', 0.0) if validation_details else 0.0,
                token_count=validation_details.get('token_count', 0) if validation_details else 0
            )

            # Store feedback metadata
            feedback_data = {
                "request_id": request_id,
                "model_name": model_name,
                "task_type": task_type.value,
                "was_correct": was_correct,
                "validation_details": validation_details or {},
                "timestamp": datetime.now().isoformat()
            }

            # Save to storage
            feedback_file = self.storage.get_feedback_file()
            self.storage._append_to_jsonl(feedback_file, feedback_data)

            # Trigger confidence score update
            self.learning_engine.update_confidence_scores()

        except Exception as e:
            logger.error(f"Error recording validation feedback: {e}")

    def record_positive_feedback(
        self,
        request_id: str,
        model_name: str,
        task_type: TaskType,
        feedback_details: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Record positive feedback (model did well).

        Args:
            request_id: ID of the request
            model_name: Name of the model
            task_type: Type of task
            feedback_details: Additional feedback details
        """
        logger.info(
            f"Recording positive feedback for {model_name} "
            f"on request {request_id}"
        )

        self.record_validation_feedback(
            request_id=request_id,
            model_name=model_name,
            task_type=task_type,
            was_correct=True,
            validation_details=feedback_details
        )

    def record_negative_feedback(
        self,
        request_id: str,
        model_name: str,
        task_type: TaskType,
        feedback_details: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Record negative feedback (model did poorly).

        Args:
            request_id: ID of the request
            model_name: Name of the model
            task_type: Type of task
            feedback_details: Additional feedback details
        """
        logger.info(
            f"Recording negative feedback for {model_name} "
            f"on request {request_id}"
        )

        self.record_validation_feedback(
            request_id=request_id,
            model_name=model_name,
            task_type=task_type,
            was_correct=False,
            validation_details=feedback_details
        )

    def get_corrections(
        self,
        model_name: Optional[str] = None,
        task_type: Optional[TaskType] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Retrieve recorded corrections.

        Args:
            model_name: Filter by model name
            task_type: Filter by task type
            limit: Maximum number of corrections to return

        Returns:
            List of correction records
        """
        try:
            corrections_file = self.storage.get_corrections_file()

            # Read corrections from file
            corrections = self.storage._read_from_jsonl(corrections_file)

            # Apply filters
            if model_name:
                corrections = [c for c in corrections if c.get('model_name') == model_name]

            if task_type:
                corrections = [c for c in corrections if c.get('task_type') == task_type.value]

            # Apply limit
            return corrections[:limit]

        except Exception as e:
            logger.error(f"Error retrieving corrections: {e}")
            return []

    def get_feedback_summary(
        self,
        model_name: Optional[str] = None,
        task_type: Optional[TaskType] = None
    ) -> Dict[str, Any]:
        """
        Get a summary of feedback data.

        Args:
            model_name: Filter by model name
            task_type: Filter by task type

        Returns:
            Summary dictionary with statistics
        """
        try:
            feedback_file = self.storage.get_feedback_file()
            feedback_data = self.storage._read_from_jsonl(feedback_file)

            # Apply filters
            if model_name:
                feedback_data = [f for f in feedback_data if f.get('model_name') == model_name]

            if task_type:
                feedback_data = [f for f in feedback_data if f.get('task_type') == task_type.value]

            # Calculate summary statistics
            total_feedback = len(feedback_data)
            correct_count = sum(1 for f in feedback_data if f.get('was_correct', False))
            incorrect_count = total_feedback - correct_count

            accuracy = correct_count / total_feedback if total_feedback > 0 else 0.0

            return {
                "total_feedback": total_feedback,
                "correct_count": correct_count,
                "incorrect_count": incorrect_count,
                "accuracy": accuracy,
                "model_name": model_name,
                "task_type": task_type.value if task_type else None
            }

        except Exception as e:
            logger.error(f"Error generating feedback summary: {e}")
            return {
                "total_feedback": 0,
                "correct_count": 0,
                "incorrect_count": 0,
                "accuracy": 0.0,
                "error": str(e)
            }
