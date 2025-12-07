"""
AI Orchestrator - Optimized Multi-AI Collaboration System

This module implements an intelligent AI collaboration system that learns from
historical performance data to optimize AI model selection, reduce costs, and
maintain high data quality.

Core Components:
- AIOrchestrator: Main coordinator for request processing
- LearningEngine: Learns which AI models perform best for different tasks
- AdaptiveRouter: Intelligently selects AI models based on learned performance
- TaskClassifier: Categorizes requests into task types
- ParallelExecutor: Executes AI model calls concurrently
- ConfidenceWeightedMerger: Merges results using confidence-based weighting
- PerformanceTracker: Monitors and reports on AI model performance
- FeedbackLoop: Captures validation results for continuous learning
- StorageManager: Persists learning data and performance history
"""

__version__ = "1.0.0"
__author__ = "ComputePulse Team"

from .orchestrator import AIOrchestrator
from .models import (
    TaskType,
    Request,
    Response,
    AIModel,
    PerformanceRecord,
    MergedResult,
    ValidationResult,
    ConfidenceScore,
    RoutingStrategy,
    MetricsSummary,
    ValidationError,
    validate_confidence_score,
    validate_positive_number,
    validate_non_empty_string,
)
from .config import OrchestratorConfig
from .storage import StorageManager, StorageError
from .task_classifier import TaskClassifier, ClassificationResult
from .learning_engine import LearningEngine, PerformanceReport
from .adaptive_router import AdaptiveRouter, RoutingDecision
from .parallel_executor import ParallelExecutor, ExecutionResult
from .merger import ConfidenceWeightedMerger, MergeMetadata
from .cache import ResponseCache, SemanticCache, CacheEntry, CacheStats, create_cache
from .async_storage import AsyncStorageManager

__all__ = [
    "AIOrchestrator",
    "TaskClassifier",
    "ClassificationResult",
    "LearningEngine",
    "PerformanceReport",
    "AdaptiveRouter",
    "RoutingDecision",
    "ParallelExecutor",
    "ExecutionResult",
    "ConfidenceWeightedMerger",
    "MergeMetadata",
    "TaskType",
    "Request",
    "Response",
    "AIModel",
    "PerformanceRecord",
    "MergedResult",
    "ValidationResult",
    "ConfidenceScore",
    "RoutingStrategy",
    "MetricsSummary",
    "ValidationError",
    "OrchestratorConfig",
    "StorageManager",
    "StorageError",
    "validate_confidence_score",
    "validate_positive_number",
    "validate_non_empty_string",
    "ResponseCache",
    "SemanticCache",
    "CacheEntry",
    "CacheStats",
    "create_cache",
    "AsyncStorageManager",
]
