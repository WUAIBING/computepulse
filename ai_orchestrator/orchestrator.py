"""
Main AI Orchestrator - coordinates all components for intelligent AI collaboration.
"""

import asyncio
import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from .config import OrchestratorConfig
from .models import Request, Response, TaskType, AIModel, MergedResult, ValidationResult
from .storage import StorageManager
from .learning_engine import LearningEngine
from .task_classifier import TaskClassifier
from .adaptive_router import AdaptiveRouter
from .parallel_executor import ParallelExecutor
from .merger import ConfidenceWeightedMerger
from .feedback_loop import FeedbackLoop
from .data_validator import DataValidator
from .performance_tracker import PerformanceTracker


logger = logging.getLogger(__name__)


class AIOrchestrator:
    """
    Main coordinator for the optimized multi-AI collaboration system.
    
    Orchestrates the flow: Classification → Routing → Parallel Execution → 
    Merging → Feedback → Learning
    """
    
    def __init__(self, config: Optional[OrchestratorConfig] = None):
        self.config = config or OrchestratorConfig()

        # Initialize components
        self.storage = StorageManager(self.config)
        self.learning_engine = LearningEngine(self.config, self.storage)
        self.task_classifier = TaskClassifier(self.config)
        self.adaptive_router = AdaptiveRouter(self.config, self.learning_engine)
        self.parallel_executor = ParallelExecutor(self.config)
        self.merger = ConfidenceWeightedMerger()
        self.feedback_loop = FeedbackLoop(self.config, self.learning_engine, self.storage)
        self.data_validator = DataValidator()
        self.performance_tracker = PerformanceTracker(self.config)

        # Available AI models (will be populated by adapters)
        self.models: Dict[str, AIModel] = {}

        logger.info("AI Orchestrator initialized")
    
    def register_model(self, model: AIModel) -> None:
        """
        Register an AI model with the orchestrator.
        
        Args:
            model: AIModel instance to register
        """
        self.models[model.name] = model
        logger.info(f"Registered AI model: {model.name} ({model.provider})")
    
    async def process_request(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]] = None,
        quality_threshold: Optional[float] = None,
        cost_limit: Optional[float] = None,
        model_call_func: Optional[callable] = None
    ) -> MergedResult:
        """
        Process a request through the complete orchestration pipeline.

        Pipeline: Task Classifier → Adaptive Router → Parallel Executor →
                  Merger → Feedback Loop

        Args:
            prompt: The prompt/query to process
            context: Additional context for the request
            quality_threshold: Minimum quality requirement (overrides config)
            cost_limit: Maximum cost limit (overrides config)
            model_call_func: Function to call AI models (model, request) -> Response

        Returns:
            MergedResult with the final output

        Raises:
            RuntimeError: If processing fails at any stage
        """
        # Create request object
        request = Request(
            id=str(uuid.uuid4()),
            prompt=prompt,
            context=context or {},
            quality_threshold=quality_threshold or self.config.default_quality_threshold,
            cost_limit=cost_limit or self.config.default_cost_limit
        )

        logger.info(f"Processing request {request.id}")

        try:
            # Step 1: Task Classification
            logger.info(f"Step 1: Classifying task for request {request.id}")
            task_type = self.task_classifier.classify(request)
            request.task_type = task_type
            classification_confidence = self.task_classifier.get_confidence()

            # Start performance tracking with classified task type
            self.performance_tracker.start_request(
                request_id=request.id,
                task_type=task_type,
                model_count=0,
                prompt_length=len(prompt)
            )

            logger.info(
                f"Task classified as: {task_type.value} "
                f"(confidence: {classification_confidence:.3f})"
            )

            # Step 2: Model Selection with Adaptive Router
            logger.info(f"Step 2: Selecting models for request {request.id}")
            try:
                selected_models = self.adaptive_router.select_models(
                    task_type, request, self.models
                )
            except Exception as e:
                logger.error(f"Model selection failed: {e}")
                raise RuntimeError(f"Failed to select models: {e}")

            if not selected_models:
                logger.error("No models selected for request")
                return MergedResult(
                    data=None,
                    contributing_models=[],
                    confidence_scores={},
                    metadata={
                        "error": "No models available",
                        "request_id": request.id,
                        "task_type": task_type.value,
                        "stage": "model_selection"
                    },
                    flagged_for_review=True
                )

            logger.info(f"Selected {len(selected_models)} models: {[m.name for m in selected_models]}")

            # Update performance tracker with selected model count
            self.performance_tracker.request_history[request.id]['model_count'] = len(selected_models)

            # Step 3: Parallel Execution
            logger.info(f"Step 3: Executing models in parallel for request {request.id}")

            if not model_call_func:
                logger.error("No model_call_func provided")
                raise RuntimeError(
                    "model_call_func is required. Please provide a function to call AI models."
                )

            try:
                responses = await self.parallel_executor.execute(
                    request, selected_models, model_call_func
                )
            except Exception as e:
                logger.error(f"Parallel execution failed: {e}")
                raise RuntimeError(f"Failed to execute models: {e}")

            logger.info(f"Received {len(responses)} responses")

            # Track model responses
            for model_name, response in responses.items():
                self.performance_tracker.track_model_response(
                    request_id=request.id,
                    model_name=model_name,
                    response=response
                )

            # Step 4: Result Merging
            logger.info(f"Step 4: Merging results for request {request.id}")

            # Get confidence scores for selected models
            confidence_scores = {}
            for model in selected_models:
                try:
                    score = self.learning_engine.get_confidence_score(model.name, task_type)
                    confidence_scores[model.name] = score
                except Exception as e:
                    logger.warning(f"Could not get confidence score for {model.name}: {e}")
                    confidence_scores[model.name] = 0.5  # Default score

            try:
                merged_result = self.merger.merge(responses, confidence_scores, task_type)
            except Exception as e:
                logger.error(f"Result merging failed: {e}")
                # Return best-effort result
                best_response = max(
                    responses.values(),
                    key=lambda r: confidence_scores.get(r.model_name, 0.0) if r.success else 0.0
                )
                merged_result = MergedResult(
                    data=best_response.content,
                    contributing_models=[best_response.model_name],
                    confidence_scores={best_response.model_name: confidence_scores.get(best_response.model_name, 0.0)},
                    metadata={"error": str(e), "fallback": True},
                    flagged_for_review=True
                )

            # Calculate total cost
            total_cost = sum(r.cost for r in responses.values() if r.success)

            # Complete request tracking
            self.performance_tracker.complete_request(
                request_id=request.id,
                merged_result=merged_result.data,
                confidence_score=merged_result.confidence_scores.get('average', 0.0),
                total_cost=total_cost
            )

            # Add request metadata
            merged_result.metadata["request_id"] = request.id
            merged_result.metadata["task_type"] = task_type.value
            merged_result.metadata["classification_confidence"] = classification_confidence
            merged_result.metadata["stage"] = "completed"

            # Step 5: Record performance for learning
            logger.info(f"Step 5: Recording performance for request {request.id}")
            try:
                for model_name, response in responses.items():
                    if response.success:
                        self.learning_engine.record_performance(
                            model_name=model_name,
                            task_type=task_type,
                            was_correct=True,  # Assume correct until validated
                            response_time=response.response_time,
                            cost=response.cost,
                            token_count=response.token_count
                        )
            except Exception as e:
                logger.warning(f"Failed to record performance: {e}")

            logger.info(f"Request {request.id} processed successfully")
            return merged_result

        except Exception as e:
            logger.error(f"Request {request.id} failed: {e}")
            # Return error result
            return MergedResult(
                data=None,
                contributing_models=[],
                confidence_scores={},
                metadata={
                    "error": str(e),
                    "request_id": request.id,
                    "task_type": task_type.value if 'task_type' in locals() else None,
                    "stage": "failed"
                },
                flagged_for_review=True
            )

    def record_feedback(
        self,
        request_id: str,
        model_name: str,
        task_type: TaskType,
        was_correct: bool,
        response_time: float = 0.0,
        cost: float = 0.0
    ) -> None:
        """
        Record feedback for a model's performance.
        
        Args:
            request_id: ID of the request
            model_name: Name of the model
            task_type: Type of task
            was_correct: Whether the model's response was correct
            response_time: Time taken (seconds)
            cost: Cost incurred (USD)
        """
        self.learning_engine.record_performance(
            model_name=model_name,
            task_type=task_type,
            was_correct=was_correct,
            response_time=response_time,
            cost=cost
        )
        
        # Trigger confidence score update
        self.learning_engine.update_confidence_scores()
        
        logger.info(f"Recorded feedback for {model_name} on {task_type.value}: correct={was_correct}")
    
    def get_performance_report(
        self,
        model_name: Optional[str] = None,
        task_type: Optional[TaskType] = None
    ) -> Dict:
        """
        Get performance report with optional filtering.

        Args:
            model_name: Filter by model name
            task_type: Filter by task type

        Returns:
            Performance report dictionary
        """
        return self.performance_tracker.get_model_performance(
            model_name=model_name,
            task_type=task_type
        )

    def generate_performance_report(
        self,
        model_name: Optional[str] = None,
        task_type: Optional[TaskType] = None,
        hours: int = 24,
        output_format: str = 'text'
    ) -> str:
        """
        Generate a comprehensive performance report.

        Args:
            model_name: Filter by model name (optional)
            task_type: Filter by task type (optional)
            hours: Time range in hours
            output_format: Output format ('text', 'json', 'dict')

        Returns:
            Performance report in specified format
        """
        return self.performance_tracker.generate_performance_report(
            model_name=model_name,
            task_type=task_type,
            hours=hours,
            output_format=output_format
        )

    def export_metrics(self, file_path: str) -> bool:
        """
        Export all performance metrics to a file.

        Args:
            file_path: Path to export file

        Returns:
            True if successful, False otherwise
        """
        return self.performance_tracker.export_metrics(file_path)
    
    def get_confidence_scores(self, task_type: Optional[TaskType] = None) -> Dict[str, float]:
        """
        Get current confidence scores.
        
        Args:
            task_type: Filter by task type (optional)
            
        Returns:
            Dictionary of model names to confidence scores
        """
        if task_type:
            return self.learning_engine.get_all_scores_for_task(task_type)
        else:
            # Return all scores
            all_scores = {}
            for task_t in TaskType:
                scores = self.learning_engine.get_all_scores_for_task(task_t)
                for model_name, score in scores.items():
                    key = f"{model_name}_{task_t.value}"
                    all_scores[key] = score
            return all_scores

    def validate_data(
        self,
        data: List[Dict[str, Any]],
        data_type: str,
        request_id: Optional[str] = None,
        task_type: Optional[TaskType] = TaskType.DATA_VALIDATION
    ) -> ValidationResult:
        """
        Validate data using the integrated data validator.

        Args:
            data: Data to validate
            data_type: Type of data ('gpu', 'token', 'grid_load')
            request_id: Optional request ID for tracking
            task_type: Task type for validation

        Returns:
            ValidationResult with validation details
        """
        logger.info(f"Validating {data_type} data ({len(data)} records)")

        try:
            if data_type == 'gpu':
                result = self.data_validator.validate_gpu_prices(data)
            elif data_type == 'token':
                result = self.data_validator.validate_token_prices(data)
            elif data_type == 'grid_load':
                result = self.data_validator.validate_grid_load(data)
            else:
                raise ValueError(f"Unknown data type: {data_type}")

            # Record validation result in feedback loop
            if request_id:
                try:
                    # For each model that contributed, record validation feedback
                    model_responses = {
                        'validation': {
                            'response_time': 0.0,
                            'cost': 0.0,
                            'token_count': 0
                        }
                    }

                    self.feedback_loop.record_validation_result(
                        request_id=request_id,
                        task_type=task_type,
                        merged_result=result.validated_data,
                        validation_result=result,
                        model_responses=model_responses
                    )
                except Exception as e:
                    logger.warning(f"Failed to record validation feedback: {e}")

            return result

        except Exception as e:
            logger.error(f"Data validation failed: {e}")
            return ValidationResult(
                is_valid=False,
                validated_data=data,
                errors=[f"Validation failed: {str(e)}"],
                warnings=[],
                task_type=task_type
            )
