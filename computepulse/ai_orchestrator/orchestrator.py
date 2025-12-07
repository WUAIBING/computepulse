"""
Main AI Orchestrator - coordinates all components for intelligent AI collaboration.
"""

import asyncio
import logging
import uuid
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from .config import OrchestratorConfig
from .models import Request, Response, TaskType, AIModel, MergedResult
from .storage import StorageManager
from .learning_engine import LearningEngine
from .task_classifier import TaskClassifier
from .cache import ResponseCache, create_cache


logger = logging.getLogger(__name__)


class AIOrchestrator:
    """
    Main coordinator for the optimized multi-AI collaboration system.
    
    Orchestrates the flow: Classification → Routing → Parallel Execution → 
    Merging → Feedback → Learning
    """
    
    def __init__(
        self,
        config: Optional[OrchestratorConfig] = None,
        enable_cache: bool = True,
        cache_max_size: int = 1000,
        cache_ttl_seconds: float = 3600.0
    ):
        self.config = config or OrchestratorConfig()

        # Initialize components
        self.storage = StorageManager(self.config)
        self.learning_engine = LearningEngine(self.storage)
        self.task_classifier = TaskClassifier(
            low_confidence_threshold=self.config.default_quality_threshold
        )

        # Initialize cache
        self.enable_cache = enable_cache
        self._cache: Optional[ResponseCache] = None
        if enable_cache:
            self._cache = create_cache(
                cache_type="lru",
                max_size=cache_max_size,
                ttl_seconds=cache_ttl_seconds
            )

        # Available AI models (will be populated by adapters)
        self.models: Dict[str, AIModel] = {}

        logger.info(f"AI Orchestrator initialized (cache: {enable_cache})")
    
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
        model_call_func: Optional[Callable] = None,
        use_cache: bool = True
    ) -> MergedResult:
        """
        Process a request through the complete orchestration pipeline.

        Args:
            prompt: The prompt/query to process
            context: Additional context for the request
            quality_threshold: Minimum quality requirement (overrides config)
            cost_limit: Maximum cost limit (overrides config)
            model_call_func: Async function to call AI models (required)
            use_cache: Whether to use cache for this request

        Returns:
            MergedResult with the final output
        """
        quality = quality_threshold or self.config.default_quality_threshold
        cost = cost_limit or self.config.default_cost_limit

        # Check cache first
        if use_cache and self._cache and self.enable_cache:
            cached_result = await self._cache.get(
                prompt=prompt,
                quality_threshold=quality,
                cost_limit=cost
            )
            if cached_result is not None:
                logger.info("Cache hit - returning cached result")
                cached_result.metadata["cache_hit"] = True
                return cached_result

        # Create request object
        request = Request(
            id=str(uuid.uuid4()),
            prompt=prompt,
            context=context or {},
            quality_threshold=quality,
            cost_limit=cost
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

        # Step 3: Execute models in parallel
        if model_call_func:
            # Execute real model calls
            responses = await self._execute_models_parallel(
                selected_models, request, model_call_func
            )
            result_data = self._merge_responses(responses)
        else:
            # No model call function - return placeholder
            result_data = {"status": "processed", "task_type": task_type.value}

        result = MergedResult(
            data=result_data,
            contributing_models=[m.name for m in selected_models],
            confidence_scores={
                m.name: self.learning_engine.get_confidence_score(m.name, task_type)
                for m in selected_models
            },
            metadata={
                "request_id": request.id,
                "task_type": task_type.value,
                "classification_confidence": self.task_classifier.get_confidence(),
                "cache_hit": False
            }
        )

        # Cache the result
        if use_cache and self._cache and self.enable_cache:
            await self._cache.set(
                prompt=prompt,
                value=result,
                task_type=task_type.value,
                quality_threshold=quality,
                cost_limit=cost,
                models_used=[m.name for m in selected_models]
            )

        logger.info(f"Request {request.id} processed successfully")

        return result

    async def _execute_models_parallel(
        self,
        models: List[AIModel],
        request: Request,
        model_call_func: Callable
    ) -> List[Response]:
        """Execute model calls in parallel."""
        tasks = [
            model_call_func(model, request)
            for model in models
        ]
        responses = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out exceptions
        valid_responses = []
        for resp in responses:
            if isinstance(resp, Response):
                valid_responses.append(resp)
            elif isinstance(resp, Exception):
                logger.error(f"Model call failed: {resp}")

        return valid_responses

    def _merge_responses(self, responses: List[Response]) -> Any:
        """Merge multiple model responses."""
        if not responses:
            return None
        if len(responses) == 1:
            return responses[0].content

        # Simple merge: return first successful response
        # More sophisticated merging is handled by the Merger component
        for resp in responses:
            if resp.success:
                return resp.content

        return responses[0].content if responses else None
    
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

    # Cache management methods

    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache stats or empty dict if cache disabled
        """
        if self._cache:
            return self._cache.get_stats()
        return {"enabled": False}

    async def invalidate_cache(
        self,
        prompt: Optional[str] = None,
        task_type: Optional[str] = None,
        model_name: Optional[str] = None
    ) -> int:
        """
        Invalidate cache entries.

        Args:
            prompt: Specific prompt to invalidate
            task_type: Invalidate all entries for task type
            model_name: Invalidate all entries using model

        Returns:
            Number of entries invalidated
        """
        if not self._cache:
            return 0

        if prompt:
            removed = await self._cache.invalidate(prompt)
            return 1 if removed else 0
        elif task_type:
            return await self._cache.invalidate_by_task_type(task_type)
        elif model_name:
            return await self._cache.invalidate_by_model(model_name)
        else:
            return await self._cache.clear()

    async def clear_cache(self) -> int:
        """
        Clear all cache entries.

        Returns:
            Number of entries cleared
        """
        if self._cache:
            return await self._cache.clear()
        return 0

    def generate_performance_report(self, output_format: str = 'text') -> Any:
        """
        Generate a comprehensive performance report.

        Args:
            output_format: 'text', 'dict', or 'json'

        Returns:
            Performance report in specified format
        """
        report_data = {
            "total_requests": 0,
            "success_rate": 0.0,
            "avg_response_time": 0.0,
            "avg_cost": 0.0,
            "models": {},
            "cache_stats": self.get_cache_stats()
        }

        # Get learning engine stats
        perf_report = self.learning_engine.get_performance_report()
        if perf_report:
            # Convert PerformanceReport to dict if needed
            if hasattr(perf_report, '__dict__'):
                report_data["total_requests"] = getattr(perf_report, 'total_requests', 0)
                report_data["success_rate"] = getattr(perf_report, 'accuracy', 0) * 100
                report_data["avg_response_time"] = getattr(perf_report, 'avg_response_time', 0)
                report_data["avg_cost"] = getattr(perf_report, 'avg_cost', 0)
            elif isinstance(perf_report, dict):
                report_data.update(perf_report)

        if output_format == 'dict':
            return report_data
        elif output_format == 'json':
            import json
            return json.dumps(report_data, indent=2, default=str)
        else:
            # Text format
            lines = [
                "=" * 50,
                "AI Orchestrator Performance Report",
                "=" * 50,
                f"Total Requests: {report_data.get('total_requests', 0)}",
                f"Success Rate: {report_data.get('success_rate', 0):.2f}%",
                f"Avg Response Time: {report_data.get('avg_response_time', 0):.3f}s",
                f"Avg Cost: ${report_data.get('avg_cost', 0):.4f}",
                "",
                "Cache Statistics:",
                f"  Hits: {report_data['cache_stats'].get('hits', 0)}",
                f"  Misses: {report_data['cache_stats'].get('misses', 0)}",
                f"  Hit Rate: {report_data['cache_stats'].get('hit_rate', '0%')}",
                "=" * 50
            ]
            return "\n".join(lines)

    def export_metrics(self, filepath: str) -> None:
        """
        Export metrics to a JSON file.

        Args:
            filepath: Path to export file
        """
        import json
        report = self.generate_performance_report(output_format='dict')
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, default=str)
