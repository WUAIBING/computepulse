"""
Configuration for the AI Orchestrator system.
"""

from dataclasses import dataclass, field
from typing import Dict, Optional
import os


@dataclass
class OrchestratorConfig:
    """Configuration for the AI Orchestrator."""
    
    # Quality and cost thresholds
    default_quality_threshold: float = 0.8
    default_cost_limit: Optional[float] = None
    
    # Learning engine parameters
    confidence_decay_factor: float = 0.95  # For EWMA
    min_samples_for_confidence: int = 10
    confidence_smoothing_factor: float = 0.7
    
    # Routing parameters
    simple_query_model_count: int = 1
    complex_reasoning_model_count: int = 2
    validation_model_count: int = 3
    
    # Parallel execution
    model_timeout_seconds: float = 30.0
    enable_early_result_processing: bool = True
    
    # Storage paths
    storage_dir: str = field(default_factory=lambda: os.path.join(
        os.path.dirname(os.path.dirname(__file__)), 
        'public',
        'data', 
        'ai_orchestrator'
    ))
    confidence_scores_file: str = "confidence_scores.json"
    performance_history_file: str = "performance_history.jsonl"
    
    # Performance tracking
    enable_performance_tracking: bool = True
    enable_anomaly_detection: bool = True
    anomaly_threshold: float = 0.3  # 30% deviation from average
    
    # Feedback loop
    enable_feedback_loop: bool = True
    positive_reinforcement_factor: float = 0.1
    negative_reinforcement_factor: float = 0.15
    
    # Logging
    log_level: str = "INFO"
    enable_detailed_logging: bool = True
    
    # Feature flags
    enable_caching: bool = True
    cache_ttl_seconds: int = 3600  # 1 hour
    
    def __post_init__(self):
        """Ensure storage directory exists."""
        os.makedirs(self.storage_dir, exist_ok=True)
    
    @property
    def confidence_scores_path(self) -> str:
        """Full path to confidence scores file."""
        return os.path.join(self.storage_dir, self.confidence_scores_file)
    
    @property
    def performance_history_path(self) -> str:
        """Full path to performance history file."""
        return os.path.join(self.storage_dir, self.performance_history_file)
    
    def to_dict(self) -> Dict:
        """Convert config to dictionary."""
        return {
            "default_quality_threshold": self.default_quality_threshold,
            "default_cost_limit": self.default_cost_limit,
            "confidence_decay_factor": self.confidence_decay_factor,
            "min_samples_for_confidence": self.min_samples_for_confidence,
            "confidence_smoothing_factor": self.confidence_smoothing_factor,
            "simple_query_model_count": self.simple_query_model_count,
            "complex_reasoning_model_count": self.complex_reasoning_model_count,
            "validation_model_count": self.validation_model_count,
            "model_timeout_seconds": self.model_timeout_seconds,
            "enable_early_result_processing": self.enable_early_result_processing,
            "storage_dir": self.storage_dir,
            "enable_performance_tracking": self.enable_performance_tracking,
            "enable_anomaly_detection": self.enable_anomaly_detection,
            "enable_feedback_loop": self.enable_feedback_loop,
            "log_level": self.log_level,
            "enable_caching": self.enable_caching,
            "cache_ttl_seconds": self.cache_ttl_seconds,
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'OrchestratorConfig':
        """Create config from dictionary."""
        return cls(**{k: v for k, v in data.items() if k in cls.__annotations__})
