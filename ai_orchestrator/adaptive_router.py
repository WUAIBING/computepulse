"""
Adaptive Router - Intelligently selects AI models based on learned performance.
"""

import logging
from typing import Dict, List, Optional, Tuple

from .config import OrchestratorConfig
from .models import AIModel, Request, TaskType, RoutingStrategy
from .learning_engine import LearningEngine

logger = logging.getLogger(__name__)


class AdaptiveRouter:
    """
    Intelligently selects AI models based on:
    - Historical performance data
    - Task type requirements
    - Cost constraints
    - Quality thresholds
    """

    def __init__(self, config: OrchestratorConfig, learning_engine: LearningEngine):
        """
        Initialize the adaptive router.

        Args:
            config: Orchestrator configuration
            learning_engine: Learning engine for confidence scores
        """
        self.config = config
        self.learning_engine = learning_engine
        logger.info("Adaptive Router initialized")

    def select_models(
        self,
        task_type: TaskType,
        request: Request,
        available_models: Dict[str, AIModel]
    ) -> List[AIModel]:
        """
        Select AI models based on task type and learned performance.

        Args:
            task_type: The classified task type
            request: The request object with constraints
            available_models: Dictionary of available AI models

        Returns:
            List of selected AI models

        Raises:
            ValueError: If no models are available or selection fails
        """
        if not available_models:
            raise ValueError("No AI models available for routing")

        logger.info(f"Selecting models for task type: {task_type.value}")

        try:
            # Get confidence scores for all models for this task type
            model_scores = self._get_model_scores(task_type, available_models)

            if not model_scores:
                logger.warning(f"No confidence scores available for {task_type.value}")
                # Fallback: select based on task type configuration
                return self._select_by_config(task_type, available_models, request)

            # Determine routing strategy based on task type and confidence
            strategy = self._determine_routing_strategy(task_type, model_scores, request)

            # Select models using the determined strategy
            selected_models = self._select_by_strategy(strategy, task_type, model_scores, request)

            # Apply cost constraints
            if request.cost_limit:
                selected_models = self._apply_cost_limit(selected_models, request.cost_limit)

            # Ensure at least one model is selected
            if not selected_models and available_models:
                # Select the cheapest model as fallback
                cheapest = min(available_models.values(), key=lambda m: m.cost_per_1m_tokens)
                selected_models = [cheapest]
                logger.warning("Cost limit too restrictive, selecting cheapest model")

            logger.info(f"Selected {len(selected_models)} models: {[m.name for m in selected_models]}")
            return selected_models

        except Exception as e:
            logger.error(f"Error in model selection: {e}")
            # Return cheapest model as emergency fallback
            if available_models:
                cheapest = min(available_models.values(), key=lambda m: m.cost_per_1m_tokens)
                return [cheapest]
            raise

    def _get_model_scores(
        self,
        task_type: TaskType,
        available_models: Dict[str, AIModel]
    ) -> List[Tuple[AIModel, float]]:
        """
        Get confidence scores for all available models for a task type.

        Args:
            task_type: The task type
            available_models: Available models

        Returns:
            List of (model, confidence_score) tuples
        """
        model_scores = []

        for model_name, model in available_models.items():
            try:
                confidence = self.learning_engine.get_confidence_score(model_name, task_type)
                model_scores.append((model, confidence))
                logger.debug(f"Model {model_name} confidence for {task_type.value}: {confidence:.3f}")
            except Exception as e:
                logger.warning(f"Could not get confidence score for {model_name}: {e}")
                # Use default low confidence for models without history
                model_scores.append((model, 0.5))

        return model_scores

    def _determine_routing_strategy(
        self,
        task_type: TaskType,
        model_scores: List[Tuple[AIModel, float]],
        request: Request
    ) -> RoutingStrategy:
        """
        Determine the routing strategy based on task type and confidence scores.

        Args:
            task_type: The task type
            model_scores: List of (model, confidence) tuples
            request: The request

        Returns:
            Routing strategy to use
        """
        # Calculate average confidence
        if model_scores:
            avg_confidence = sum(score for _, score in model_scores) / len(model_scores)
            max_confidence = max(score for _, score in model_scores)
            min_confidence = min(score for _, score in model_scores)
        else:
            avg_confidence = 0.5
            max_confidence = 0.5
            min_confidence = 0.5

        # Determine strategy based on task type and confidence distribution
        if task_type == TaskType.DATA_VALIDATION:
            # Use triple consensus for validation tasks
            return RoutingStrategy.TRIPLE_CONSENSUS
        elif task_type == TaskType.COMPLEX_REASONING:
            # Use dual validation for complex reasoning
            return RoutingStrategy.DUAL_VALIDATION
        elif max_confidence > 0.9 and (max_confidence - min_confidence) > 0.3:
            # High confidence in one model, use it alone
            return RoutingStrategy.SINGLE_FAST
        elif avg_confidence < request.quality_threshold:
            # Low confidence overall, use multiple models
            return RoutingStrategy.TRIPLE_CONSENSUS
        else:
            # Default to adaptive strategy
            return RoutingStrategy.ADAPTIVE

    def _select_by_strategy(
        self,
        strategy: RoutingStrategy,
        task_type: TaskType,
        model_scores: List[Tuple[AIModel, float]],
        request: Request
    ) -> List[AIModel]:
        """
        Select models using the specified routing strategy.

        Args:
            strategy: Routing strategy to use
            task_type: The task type
            model_scores: List of (model, confidence) tuples
            request: The request

        Returns:
            List of selected models
        """
        if not model_scores:
            return []

        # Sort by confidence (descending)
        sorted_models = sorted(model_scores, key=lambda x: x[1], reverse=True)

        if strategy == RoutingStrategy.SINGLE_FAST:
            # Select only the highest confidence model
            return [sorted_models[0][0]]

        elif strategy == RoutingStrategy.DUAL_VALIDATION:
            # Select top 2 models
            return [model for model, _ in sorted_models[:2]]

        elif strategy == RoutingStrategy.TRIPLE_CONSENSUS:
            # Select top 3 models (or all if less than 3)
            count = min(3, len(sorted_models))
            return [model for model, _ in sorted_models[:count]]

        elif strategy == RoutingStrategy.ADAPTIVE:
            # Dynamically determine count based on quality threshold
            count = 2  # Default
            for i, (model, confidence) in enumerate(sorted_models):
                if confidence >= request.quality_threshold:
                    count = i + 1
                    break
            count = min(count, len(sorted_models))
            return [model for model, _ in sorted_models[:count]]

        else:
            # Fallback to dual validation
            count = min(2, len(sorted_models))
            return [model for model, _ in sorted_models[:count]]

    def _select_by_config(
        self,
        task_type: TaskType,
        available_models: Dict[str, AIModel],
        request: Request
    ) -> List[AIModel]:
        """
        Fallback selection based on configuration when confidence scores unavailable.

        Args:
            task_type: The task type
            available_models: Available models
            request: The request

        Returns:
            List of selected models
        """
        # Determine count based on task type
        if task_type == TaskType.SIMPLE_QUERY:
            count = self.config.simple_query_model_count
        elif task_type == TaskType.COMPLEX_REASONING:
            count = self.config.complex_reasoning_model_count
        elif task_type == TaskType.DATA_VALIDATION:
            count = self.config.validation_model_count
        else:
            count = 2

        # Select models by cost (cheapest first)
        sorted_models = sorted(
            available_models.values(),
            key=lambda m: m.cost_per_1m_tokens
        )

        count = min(count, len(sorted_models))
        return sorted_models[:count]

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
        if not models or not cost_limit:
            return models

        # Sort by cost (ascending)
        sorted_models = sorted(models, key=lambda m: m.cost_per_1m_tokens)

        selected = []
        total_cost = 0.0

        for model in sorted_models:
            # Estimate cost for 1K tokens (typical request)
            estimated_cost = model.cost_per_1m_tokens * 0.001

            if total_cost + estimated_cost <= cost_limit:
                selected.append(model)
                total_cost += estimated_cost
            else:
                logger.debug(f"Skipping {model.name} due to cost limit")

        if not selected and models:
            # If no models fit, select the cheapest one
            selected = [sorted_models[0]]

        return selected
