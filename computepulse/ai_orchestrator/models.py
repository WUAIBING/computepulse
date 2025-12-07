"""
Data models for the AI Orchestrator system.

This module defines all core data structures used throughout the AI Orchestrator,
including validation logic to ensure data integrity.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
import uuid


class ValidationError(Exception):
    """Raised when data validation fails."""
    pass


class TaskType(Enum):
    """Types of tasks that can be classified."""
    SIMPLE_QUERY = "simple_query"
    COMPLEX_REASONING = "complex_reasoning"
    DATA_VALIDATION = "data_validation"
    PRICE_EXTRACTION = "price_extraction"
    HISTORICAL_ANALYSIS = "historical_analysis"


def validate_confidence_score(score: float, field_name: str = "confidence_score") -> float:
    """Validate that a confidence score is within [0, 1] range."""
    if not isinstance(score, (int, float)):
        raise ValidationError(f"{field_name} must be a number, got {type(score).__name__}")
    if score < 0.0 or score > 1.0:
        raise ValidationError(f"{field_name} must be between 0 and 1, got {score}")
    return float(score)


def validate_positive_number(value: float, field_name: str, allow_zero: bool = True) -> float:
    """Validate that a number is positive (or non-negative if allow_zero)."""
    if not isinstance(value, (int, float)):
        raise ValidationError(f"{field_name} must be a number, got {type(value).__name__}")
    if allow_zero and value < 0:
        raise ValidationError(f"{field_name} must be non-negative, got {value}")
    if not allow_zero and value <= 0:
        raise ValidationError(f"{field_name} must be positive, got {value}")
    return float(value)


def validate_non_empty_string(value: str, field_name: str) -> str:
    """Validate that a string is non-empty."""
    if not isinstance(value, str):
        raise ValidationError(f"{field_name} must be a string, got {type(value).__name__}")
    if not value.strip():
        raise ValidationError(f"{field_name} cannot be empty")
    return value


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
    
    def __post_init__(self):
        """Validate request data after initialization."""
        self.validate()
    
    def validate(self) -> None:
        """Validate all request fields."""
        validate_non_empty_string(self.id, "id")
        validate_non_empty_string(self.prompt, "prompt")
        validate_confidence_score(self.quality_threshold, "quality_threshold")
        if self.cost_limit is not None:
            validate_positive_number(self.cost_limit, "cost_limit", allow_zero=False)
    
    @classmethod
    def create(cls, prompt: str, **kwargs) -> 'Request':
        """Factory method to create a request with auto-generated ID."""
        return cls(
            id=str(uuid.uuid4()),
            prompt=prompt,
            **kwargs
        )


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
    
    def __post_init__(self):
        """Validate response data after initialization."""
        self.validate()
    
    def validate(self) -> None:
        """Validate all response fields."""
        validate_non_empty_string(self.model_name, "model_name")
        validate_positive_number(self.response_time, "response_time")
        if not isinstance(self.token_count, int) or self.token_count < 0:
            raise ValidationError(f"token_count must be a non-negative integer, got {self.token_count}")
        validate_positive_number(self.cost, "cost")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "model_name": self.model_name,
            "content": self.content,
            "response_time": self.response_time,
            "token_count": self.token_count,
            "cost": self.cost,
            "timestamp": self.timestamp.isoformat(),
            "success": self.success,
            "error": self.error
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Response':
        """Create from dictionary."""
        return cls(
            model_name=data["model_name"],
            content=data["content"],
            response_time=data["response_time"],
            token_count=data["token_count"],
            cost=data["cost"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            success=data.get("success", True),
            error=data.get("error")
        )


@dataclass
class AIModel:
    """Represents an AI model configuration."""
    name: str
    provider: str
    cost_per_1m_tokens: float
    avg_response_time: float
    enabled: bool = True
    
    def __post_init__(self):
        """Validate AI model data after initialization."""
        self.validate()
    
    def validate(self) -> None:
        """Validate all AI model fields."""
        validate_non_empty_string(self.name, "name")
        validate_non_empty_string(self.provider, "provider")
        validate_positive_number(self.cost_per_1m_tokens, "cost_per_1m_tokens")
        validate_positive_number(self.avg_response_time, "avg_response_time", allow_zero=False)
    
    def __hash__(self):
        return hash(self.name)
    
    def __eq__(self, other):
        if isinstance(other, AIModel):
            return self.name == other.name
        return False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "name": self.name,
            "provider": self.provider,
            "cost_per_1m_tokens": self.cost_per_1m_tokens,
            "avg_response_time": self.avg_response_time,
            "enabled": self.enabled
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AIModel':
        """Create from dictionary."""
        return cls(
            name=data["name"],
            provider=data["provider"],
            cost_per_1m_tokens=data["cost_per_1m_tokens"],
            avg_response_time=data["avg_response_time"],
            enabled=data.get("enabled", True)
        )


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
    request_id: Optional[str] = None
    
    def __post_init__(self):
        """Validate performance record data after initialization."""
        self.validate()
    
    def validate(self) -> None:
        """Validate all performance record fields."""
        validate_non_empty_string(self.model_name, "model_name")
        if not isinstance(self.task_type, TaskType):
            raise ValidationError(f"task_type must be a TaskType enum, got {type(self.task_type).__name__}")
        if not isinstance(self.was_correct, bool):
            raise ValidationError(f"was_correct must be a boolean, got {type(self.was_correct).__name__}")
        validate_positive_number(self.response_time, "response_time")
        validate_positive_number(self.cost, "cost")
        if not isinstance(self.token_count, int) or self.token_count < 0:
            raise ValidationError(f"token_count must be a non-negative integer, got {self.token_count}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "model": self.model_name,
            "task_type": self.task_type.value,
            "was_correct": self.was_correct,
            "response_time": self.response_time,
            "cost": self.cost,
            "token_count": self.token_count,
            "request_id": self.request_id
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
            token_count=data["token_count"],
            request_id=data.get("request_id")
        )


@dataclass
class MergedResult:
    """Represents a merged result from multiple AI models."""
    data: Any
    contributing_models: List[str]
    confidence_scores: Dict[str, float]
    metadata: Dict[str, Any] = field(default_factory=dict)
    flagged_for_review: bool = False
    
    def __post_init__(self):
        """Validate merged result data after initialization."""
        self.validate()
    
    def validate(self) -> None:
        """Validate all merged result fields."""
        if not isinstance(self.contributing_models, list):
            raise ValidationError("contributing_models must be a list")
        for score in self.confidence_scores.values():
            validate_confidence_score(score, "confidence_score")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "data": self.data,
            "contributing_models": self.contributing_models,
            "confidence_scores": self.confidence_scores,
            "metadata": self.metadata,
            "flagged_for_review": self.flagged_for_review
        }


@dataclass
class ValidationResult:
    """Result of data validation."""
    is_valid: bool
    validated_data: Any
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    task_type: Optional[TaskType] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "is_valid": self.is_valid,
            "validated_data": self.validated_data,
            "errors": self.errors,
            "warnings": self.warnings,
            "task_type": self.task_type.value if self.task_type else None
        }


@dataclass
class ConfidenceScore:
    """Represents a confidence score for a model-task combination."""
    model_name: str
    task_type: TaskType
    score: float
    sample_count: int = 0
    last_updated: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        """Validate confidence score data after initialization."""
        self.validate()
    
    def validate(self) -> None:
        """Validate all confidence score fields."""
        validate_non_empty_string(self.model_name, "model_name")
        if not isinstance(self.task_type, TaskType):
            raise ValidationError(f"task_type must be a TaskType enum, got {type(self.task_type).__name__}")
        validate_confidence_score(self.score, "score")
        if not isinstance(self.sample_count, int) or self.sample_count < 0:
            raise ValidationError(f"sample_count must be a non-negative integer, got {self.sample_count}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "model_name": self.model_name,
            "task_type": self.task_type.value,
            "score": self.score,
            "sample_count": self.sample_count,
            "last_updated": self.last_updated.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ConfidenceScore':
        """Create from dictionary."""
        return cls(
            model_name=data["model_name"],
            task_type=TaskType(data["task_type"]),
            score=data["score"],
            sample_count=data.get("sample_count", 0),
            last_updated=datetime.fromisoformat(data["last_updated"]) if "last_updated" in data else datetime.now()
        )


class RoutingStrategy(Enum):
    """Strategies for routing requests to AI models."""
    SINGLE_FAST = "single_fast"  # Use only the fastest model
    DUAL_VALIDATION = "dual_validation"  # Use two models for cross-validation
    TRIPLE_CONSENSUS = "triple_consensus"  # Use all three models
    ADAPTIVE = "adaptive"  # Dynamically decide based on confidence


@dataclass
class MetricsSummary:
    """Aggregated metrics summary for performance reporting."""
    total_requests: int
    accuracy: float
    avg_response_time: float
    p50_response_time: float
    p95_response_time: float
    p99_response_time: float
    total_cost: float
    avg_cost: float
    success_rate: float
    time_range_start: Optional[datetime] = None
    time_range_end: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "total_requests": self.total_requests,
            "accuracy": self.accuracy,
            "avg_response_time": self.avg_response_time,
            "p50_response_time": self.p50_response_time,
            "p95_response_time": self.p95_response_time,
            "p99_response_time": self.p99_response_time,
            "total_cost": self.total_cost,
            "avg_cost": self.avg_cost,
            "success_rate": self.success_rate,
            "time_range_start": self.time_range_start.isoformat() if self.time_range_start else None,
            "time_range_end": self.time_range_end.isoformat() if self.time_range_end else None
        }
