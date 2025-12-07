"""
Adaptive Router for the AI Orchestrator system.

This module implements intelligent model selection based on task type,
confidence scores, cost constraints, and routing strategies.
"""

import logging
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from .models import AIModel, TaskType, RoutingStrategy
from .learning_engine import LearningEngine


logger = logging.getLogger(__name__)


@dataclass
class RoutingDecision:
    """Result of routing decision."""
    models: List[str]
    strategy: RoutingStrategy
    task_type: TaskType
    confidence_scores: Dict[str, float]
    estimated_cost: float
    reason: str
    
    def to_dict(self) -> dict:
        return {
            "models": self.models,
            "strategy": self.strategy.value,
            "task_type": self.task_type.value,
            "confidence_scores": self.confidence_scores,
            "estimated_cost": self.estimated_cost,
            "reason": self.reason,
        }


class AdaptiveRouter:
    """
    Selects optimal AI model combinations based on task type and performance.
    
    Uses confidence scores from the learning engine to make intelligent
    routing decisions that balance quality, cost, and speed.
    """
    
    # Default routing strategies per task type
    DEFAULT_STRATEGIES: Dict[TaskType, RoutingStrategy] = {
        TaskType.SIMPLE_QUERY: RoutingStrategy.SINGLE_FAST,
        TaskType.COMPLEX_REASONING: RoutingStrategy.DUAL_VALIDATION,
        TaskType.DATA_VALIDATION: RoutingStrategy.DUAL_VALIDATION,
        TaskType.PRICE_EXTRACTION: RoutingStrategy.DUAL_VALIDATION,
        TaskType.HISTORICAL_ANALYSIS: RoutingStrategy.SINGLE_FAST,
    }
    
    def __init__(
        self,
        learning_engine: LearningEngine,
        available_models: Dict[str, AIModel],
        default_quality_threshold: float = 0.5,
        default_cost_limit: Optional[float] = None,
    ):
        """
        Initialize the adaptive router.
        
        Args:
            learning_engine: Learning engine for confidence scores
            available_models: Dictionary of available AI models
            default_quality_threshold: Default minimum confidence threshold
            default_cost_limit: Default maximum cost per request
        """
        self.learning_engine = learning_engine
        self.available_models = available_models
        self.default_quality_threshold = default_quality_threshold
        self.default_cost_limit = default_cost_limit
    
    def select_models(
        self,
        task_type: TaskType,
        quality_threshold: Optional[float] = None,
        cost_limit: Optional[float] = None,
        strategy: Optional[RoutingStrategy] = None,
    ) -> RoutingDecision:
        """
        Select AI models for a task based on learned performance.
        
        Args:
            task_type: The classified task type
            quality_threshold: Minimum acceptable confidence score
            cost_limit: Maximum cost per request (optional)
            strategy: Override routing strategy (optional)
            
        Returns:
            RoutingDecision with selected models and metadata
        """
        threshold = quality_threshold or self.default_quality_threshold
        limit = cost_limit or self.default_cost_limit
        routing_strategy = strategy or self.get_routing_strategy(task_type)
        
        # Get confidence scores for all models on this task type
        model_scores = self._get_model_scores(task_type)
        
        # Filter enabled models
        enabled_models = {
            name: model for name, model in self.available_models.items()
            if model.enabled
        }
        
        if not enabled_models:
            logger.warning("No enabled models available")
            return RoutingDecision(
                models=[],
                strategy=routing_strategy,
                task_type=task_type,
                confidence_scores={},
                estimated_cost=0.0,
                reason="No enabled models available",
            )
        
        # Select models based on strategy
        selected = self._select_by_strategy(
            routing_strategy,
            task_type,
            enabled_models,
            model_scores,
            threshold,
            limit,
        )
        
        # Calculate estimated cost
        estimated_cost = sum(
            self.available_models[name].cost_per_1m_tokens * 0.001  # Assume ~1000 tokens
            for name in selected
            if name in self.available_models
        )
        
        # Build reason string
        reason = self._build_reason(routing_strategy, selected, model_scores, threshold)
        
        return RoutingDecision(
            models=selected,
            strategy=routing_strategy,
            task_type=task_type,
            confidence_scores={name: model_scores.get(name, 0.5) for name in selected},
            estimated_cost=estimated_cost,
            reason=reason,
        )
    
    def get_routing_strategy(self, task_type: TaskType) -> RoutingStrategy:
        """Get the routing strategy for a task type."""
        return self.DEFAULT_STRATEGIES.get(task_type, RoutingStrategy.ADAPTIVE)
    
    def _get_model_scores(self, task_type: TaskType) -> Dict[str, float]:
        """Get confidence scores for all models on a task type."""
        scores = {}
        for model_name in self.available_models:
            scores[model_name] = self.learning_engine.get_confidence_score(
                model_name, task_type
            )
        return scores
    
    def _select_by_strategy(
        self,
        strategy: RoutingStrategy,
        task_type: TaskType,
        enabled_models: Dict[str, AIModel],
        model_scores: Dict[str, float],
        threshold: float,
        cost_limit: Optional[float],
    ) -> List[str]:
        """Select models based on routing strategy."""
        
        if strategy == RoutingStrategy.SINGLE_FAST:
            return self._select_single_fast(enabled_models, model_scores, threshold)
        
        elif strategy == RoutingStrategy.DUAL_VALIDATION:
            return self._select_dual_validation(enabled_models, model_scores, threshold)
        
        elif strategy == RoutingStrategy.TRIPLE_CONSENSUS:
            return self._select_triple_consensus(enabled_models, model_scores, threshold)
        
        elif strategy == RoutingStrategy.ADAPTIVE:
            return self._select_adaptive(
                task_type, enabled_models, model_scores, threshold, cost_limit
            )
        
        # Default: return best model
        return self._select_single_fast(enabled_models, model_scores, threshold)
    
    def _select_single_fast(
        self,
        enabled_models: Dict[str, AIModel],
        model_scores: Dict[str, float],
        threshold: float,
    ) -> List[str]:
        """Select the single best model (fastest with sufficient confidence)."""
        # Filter by threshold
        qualified = [
            (name, model_scores.get(name, 0.5))
            for name in enabled_models
            if model_scores.get(name, 0.5) >= threshold
        ]
        
        if not qualified:
            # Fall back to best available if none meet threshold
            qualified = [
                (name, model_scores.get(name, 0.5))
                for name in enabled_models
            ]
        
        if not qualified:
            return []
        
        # Sort by confidence score (descending), then by response time (ascending)
        qualified.sort(
            key=lambda x: (
                -x[1],  # Higher confidence first
                enabled_models[x[0]].avg_response_time  # Faster response time
            )
        )
        
        return [qualified[0][0]]
    
    def _select_dual_validation(
        self,
        enabled_models: Dict[str, AIModel],
        model_scores: Dict[str, float],
        threshold: float,
    ) -> List[str]:
        """Select two models for cross-validation."""
        # Sort by confidence score
        sorted_models = sorted(
            enabled_models.keys(),
            key=lambda x: model_scores.get(x, 0.5),
            reverse=True
        )
        
        # Return top 2 (or all if less than 2)
        return sorted_models[:2]
    
    def _select_triple_consensus(
        self,
        enabled_models: Dict[str, AIModel],
        model_scores: Dict[str, float],
        threshold: float,
    ) -> List[str]:
        """Select three models for consensus."""
        # Sort by confidence score
        sorted_models = sorted(
            enabled_models.keys(),
            key=lambda x: model_scores.get(x, 0.5),
            reverse=True
        )
        
        # Return top 3 (or all if less than 3)
        return sorted_models[:3]
    
    def _select_adaptive(
        self,
        task_type: TaskType,
        enabled_models: Dict[str, AIModel],
        model_scores: Dict[str, float],
        threshold: float,
        cost_limit: Optional[float],
    ) -> List[str]:
        """Dynamically select models based on confidence and cost."""
        # Sort by confidence score
        sorted_models = sorted(
            enabled_models.keys(),
            key=lambda x: model_scores.get(x, 0.5),
            reverse=True
        )
        
        if not sorted_models:
            return []
        
        best_score = model_scores.get(sorted_models[0], 0.5)
        
        # If best model has very high confidence, use single model
        if best_score >= 0.85:
            return [sorted_models[0]]
        
        # If best model has moderate confidence, use dual validation
        if best_score >= 0.6:
            return sorted_models[:2]
        
        # Low confidence - use triple consensus if available
        if len(sorted_models) >= 3:
            return sorted_models[:3]
        
        return sorted_models[:2]
    
    def _build_reason(
        self,
        strategy: RoutingStrategy,
        selected: List[str],
        model_scores: Dict[str, float],
        threshold: float,
    ) -> str:
        """Build explanation for routing decision."""
        if not selected:
            return "No models selected"
        
        scores_str = ", ".join(
            f"{name}={model_scores.get(name, 0.5):.2f}"
            for name in selected
        )
        
        return f"Strategy: {strategy.value}, Models: {scores_str}, Threshold: {threshold:.2f}"
    
    def update_model_availability(self, model_name: str, enabled: bool) -> None:
        """Update model availability."""
        if model_name in self.available_models:
            self.available_models[model_name].enabled = enabled
            logger.info(f"Model {model_name} {'enabled' if enabled else 'disabled'}")
    
    def add_model(self, model: AIModel) -> None:
        """Add a new model to the router."""
        self.available_models[model.name] = model
        logger.info(f"Added model {model.name} to router")
    
    def remove_model(self, model_name: str) -> None:
        """Remove a model from the router."""
        if model_name in self.available_models:
            del self.available_models[model_name]
            logger.info(f"Removed model {model_name} from router")
