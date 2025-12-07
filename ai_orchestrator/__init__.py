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
from .models import TaskType, Request, Response, AIModel, MergedResult, ValidationResult
from .config import OrchestratorConfig
from .adaptive_router import AdaptiveRouter
from .parallel_executor import ParallelExecutor
from .merger import ConfidenceWeightedMerger
from .feedback_loop import FeedbackLoop
from .data_validator import DataValidator
from .performance_tracker import PerformanceTracker
from .migration_adapter import MigrationAdapter, fetch_data_with_collaboration

__all__ = [
    "AIOrchestrator",
    "TaskType",
    "Request",
    "Response",
    "AIModel",
    "MergedResult",
    "ValidationResult",
    "OrchestratorConfig",
    "AdaptiveRouter",
    "ParallelExecutor",
    "ConfidenceWeightedMerger",
    "FeedbackLoop",
    "DataValidator",
    "PerformanceTracker",
    "MigrationAdapter",
    "fetch_data_with_collaboration",
]
