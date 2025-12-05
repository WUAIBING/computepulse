"""
Main AI Orchestrator - coordinates all components for intelligent AI collaboration.
"""

import asyncio
import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from .config import OrchestratorConfig
from .models import Request, Response, TaskType, AIModel, MergedResult
from .storage import StorageManager
from .learning_engine import LearningEngine
from .task_classifier import TaskClassifier


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
        cost_limit: Optional[float] = None
    ) -> MergedResult:
        """
        Process a request through the complete orchestration pipeline.
        
        Args:
            prompt: The prompt/query to process
            context: Additional context for the request
            quality_threshold: Minimum quality requirement (overrides config)
            cost_limit: Maximum cost limit (overrides config)
            
        Returns:
            MergedResult with the final output
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
        
        # Step 1: Classify task type
        task_type = self.task_classifier.classify(request)
        
        # Step 2: Select models based on task type and confidence scores
        selected_models = self._select_models(task_type, request)
        
        if not selected_models:
            logger.error("No models selected for request")
            return MergedResult(
                data=None,
                contributing_models=[],
                confidence_scores={},
                metadata={"error": "No models available"},
                flagged_for_review=True
            )
        
        logger.info(f"Selected models: {[m.name for m in selected_models]}")
        
        # Step 3: Execute models in parallel (simplified - actual implementation would use adapters)
        # For now, return a placeholder result
        result = MergedResult(
            data={"status": "processed", "task_type": task_type.value},
            contributing_models=[m.name for m in selected_models],
            confidence_scores={
                m.name: self.learning_engine.get_confidence_score(m.name, task_type)
                for m in selected_models
            },
            metadata={
                "request_id": request.id,
                "task_type": task_type.value,
                "classification_confidence": self.task_classifier.get_confidence()
            }
        )
        
        logger.info(f"Request {request.id} processed successfully")
        
        return result
    
    def _select_models(
        self,
        task_type: TaskType,
        request: Request
    ) -> List[AIModel]:
        """
        Select AI models based on task type and learned confidence scores.
        
        Args:
            task_type: The classified task type
            request: The request object
            
        Returns:
            List of selected AI models
        """
        if not self.models:
            logger.warning("No models registered")
            return []
        
        # Get confidence scores for all models for this task type
        model_scores = []
        for model_name, model in self.models.items():
            confidence = self.learning_engine.get_confidence_score(model_name, task_type)
            model_scores.append((model, confidence))
        
        # Sort by confidence (descending)
        model_scores.sort(key=lambda x: x[1], reverse=True)
        
        # Determine how many models to use based on task type
        if task_type == TaskType.SIMPLE_QUERY:
            count = self.config.simple_query_model_count
        elif task_type == TaskType.COMPLEX_REASONING:
            count = self.config.complex_reasoning_model_count
        elif task_type == TaskType.DATA_VALIDATION:
            count = self.config.validation_model_count
        else:
            count = 2  # Default to 2 models
        
        # If classification confidence is low, use more models
        if self.task_classifier.is_low_confidence():
            count = min(count + 1, len(self.models))
            logger.info(f"Low classification confidence, increasing model count to {count}")
        
        # Select top N models that meet quality threshold
        selected = []
        for model, confidence in model_scores:
            if confidence >= request.quality_threshold or len(selected) == 0:
                # Always select at least one model
                selected.append(model)
                if len(selected) >= count:
                    break
        
        # Apply cost limit if specified
        if request.cost_limit:
            selected = self._apply_cost_limit(selected, request.cost_limit)
        
        return selected
    
    def _apply_cost_limit(
        self,
        models: List[AIModel],
        cost_limit: float
    ) -> List[AIModel]:
        """
        Filter models to stay within cost limit.
        
        Args:
            models: List of models to filter
            cost_limit: Maximum total cost
            
        Returns:
            Filtered list of models
        """
        # Sort by cost (ascending)
        sorted_models = sorted(models, key=lambda m: m.cost_per_1m_tokens)
        
        selected = []
        total_cost = 0.0
        
        for model in sorted_models:
            estimated_cost = model.cost_per_1m_tokens * 0.001  # Estimate for 1K tokens
            if total_cost + estimated_cost <= cost_limit:
                selected.append(model)
                total_cost += estimated_cost
            else:
                logger.warning(f"Skipping {model.name} due to cost limit")
        
        if not selected and models:
            # If no models fit, select the cheapest one
            selected = [sorted_models[0]]
            logger.warning("Cost limit too restrictive, selecting cheapest model only")
        
        return selected
    
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
        return self.learning_engine.get_performance_report(
            model_name=model_name,
            task_type=task_type
        )
    
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
