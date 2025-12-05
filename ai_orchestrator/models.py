"""
Data models for the AI Orchestrator system.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class TaskType(Enum):
    """Types of tasks that can be classified."""
    SIMPLE_QUERY = "simple_query"
    COMPLEX_REASONING = "complex_reasoning"
    DATA_VALIDATION = "data_validation"
    PRICE_EXTRACTION = "price_extraction"
    HISTORICAL_ANALYSIS = "historical_analysis"


@dataclass
class Request:
    """Represents an incoming request to the AI orchestrator."""
    id: str
    prompt: str
    context: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    quality_threshold: float = 0.8
    cost_limit: Optional[float] = None
    task_type: Optional[TaskType] = None


@dataclass
class Response:
    """Represents a response from an AI model."""
    model_name: str
    content: str
    response_time: float
    token_count: int
    cost: float
    timestamp: datetime = field(default_factory=datetime.now)
    success: bool = True
    error: Optional[str] = None


@dataclass
class AIModel:
    """Represents an AI model configuration."""
    name: str
    provider: str
    cost_per_1m_tokens: float
    avg_response_time: float
    
    def __hash__(self):
        return hash(self.name)
    
    def __eq__(self, other):
        if isinstance(other, AIModel):
            return self.name == other.name
        return False


@dataclass
class PerformanceRecord:
    """Records performance data for an AI model."""
    timestamp: datetime
    model_name: str
    task_type: TaskType
    was_correct: bool
    response_time: float
    cost: float
    token_count: int
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "model": self.model_name,
            "task_type": self.task_type.value,
            "was_correct": self.was_correct,
            "response_time": self.response_time,
            "cost": self.cost,
            "token_count": self.token_count
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PerformanceRecord':
        """Create from dictionary."""
        return cls(
            timestamp=datetime.fromisoformat(data["timestamp"]),
            model_name=data["model"],
            task_type=TaskType(data["task_type"]),
            was_correct=data["was_correct"],
            response_time=data["response_time"],
            cost=data["cost"],
            token_count=data["token_count"]
        )


@dataclass
class MergedResult:
    """Represents a merged result from multiple AI models."""
    data: Any
    contributing_models: List[str]
    confidence_scores: Dict[str, float]
    metadata: Dict[str, Any] = field(default_factory=dict)
    flagged_for_review: bool = False


@dataclass
class ValidationResult:
    """Result of data validation."""
    is_valid: bool
    validated_data: Any
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    task_type: Optional[TaskType] = None


class RoutingStrategy(Enum):
    """Strategies for routing requests to AI models."""
    SINGLE_FAST = "single_fast"  # Use only the fastest model
    DUAL_VALIDATION = "dual_validation"  # Use two models for cross-validation
    TRIPLE_CONSENSUS = "triple_consensus"  # Use all three models
    ADAPTIVE = "adaptive"  # Dynamically decide based on confidence
