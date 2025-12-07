"""
Task Classifier for the AI Orchestrator system.

This module implements intelligent task classification based on keyword analysis,
prompt complexity scoring, and historical pattern matching.
"""

import logging
import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Set

from .models import Request, TaskType


logger = logging.getLogger(__name__)


@dataclass
class ClassificationResult:
    """Result of task classification."""
    task_type: TaskType
    confidence: float
    matched_keywords: List[str]
    complexity_score: float
    
    def to_dict(self) -> dict:
        return {
            "task_type": self.task_type.value,
            "confidence": self.confidence,
            "matched_keywords": self.matched_keywords,
            "complexity_score": self.complexity_score
        }


class TaskClassifier:
    """
    Classifies incoming requests into task types.
    
    Uses keyword analysis, prompt complexity scoring, and configurable
    rules to determine the most appropriate task type for each request.
    """
    
    # Keyword patterns for each task type with weights (Chinese and English)
    # Higher weight = stronger indicator for that task type
    TASK_KEYWORDS: Dict[TaskType, List[Tuple[str, float]]] = {
        TaskType.SIMPLE_QUERY: [
            # Chinese - generic queries (lower weight, easily overridden)
            ("查一下", 0.3), ("是什么", 0.3), ("几点", 0.4), ("哪里", 0.4),
            ("什么是", 0.3), ("告诉我", 0.2), ("请问", 0.2), ("帮我查", 0.3),
            ("天气", 0.5), ("怎么样", 0.3),
            # English
            ("how much", 0.3), ("where", 0.4), ("when", 0.4), ("tell me", 0.2),
        ],
        TaskType.COMPLEX_REASONING: [
            # Chinese - strong reasoning indicators
            ("分析", 0.6), ("推理", 0.7), ("为什么", 0.6), ("原因", 0.5),
            ("解释", 0.5), ("比较", 0.6), ("评估", 0.6), ("预测", 0.6),
            ("判断", 0.5), ("推断", 0.6), ("逻辑", 0.6), ("深入", 0.5),
            ("详细分析", 0.8),
            # English
            ("analyze", 0.6), ("reason", 0.6), ("why", 0.5), ("explain", 0.5),
            ("compare", 0.6), ("evaluate", 0.6), ("predict", 0.6), ("infer", 0.6),
        ],
        TaskType.DATA_VALIDATION: [
            # Chinese - validation indicators (high weight)
            ("验证", 0.8), ("检查", 0.6), ("核实", 0.8), ("确认", 0.5),
            ("校验", 0.8), ("对比", 0.5), ("是否正确", 0.9), ("准确性", 0.7),
            ("一致性", 0.7), ("有效性", 0.6), ("是否准确", 0.9),
            # English
            ("validate", 0.8), ("verify", 0.8), ("check", 0.5), ("confirm", 0.5),
            ("accuracy", 0.6), ("accurate", 0.6), ("correct", 0.5), ("valid", 0.6),
        ],
        TaskType.PRICE_EXTRACTION: [
            # Chinese - price-specific (moderate weight to allow override)
            ("价格", 0.7), ("报价", 0.8), ("费用", 0.7), ("成本", 0.6),
            ("多少钱", 0.9), ("收费", 0.7), ("定价", 0.8), ("汇率", 0.9),
            ("股价", 0.9), ("币价", 0.9), ("算力价格", 0.9), ("GPU价格", 0.8),
            ("最新价格", 1.0), ("当前价格", 1.0),
            # English
            ("price", 0.7), ("cost", 0.6), ("fee", 0.7), ("pricing", 0.8),
            ("quote", 0.7), ("exchange rate", 0.9), ("stock price", 0.9),
            ("gpu price", 0.9), ("bitcoin price", 0.9), ("current price", 1.0),
        ],
        TaskType.HISTORICAL_ANALYSIS: [
            # Chinese - historical indicators (high weight)
            ("历史", 0.8), ("趋势", 0.9), ("走势", 1.0), ("过去", 0.7),
            ("之前", 0.4), ("曾经", 0.5), ("对比历史", 1.0), ("历史数据", 1.0),
            ("时间序列", 1.0), ("变化趋势", 1.0), ("过去一年", 1.2),
            ("价格走势", 1.2), ("价格趋势", 1.2),
            # English
            ("history", 0.8), ("trend", 0.9), ("historical", 0.9), ("past", 0.6),
            ("previous", 0.5), ("time series", 1.0), ("over time", 0.8),
            ("change over", 0.8), ("price trend", 1.2),
        ]
    }
    
    # Complexity indicators
    COMPLEXITY_INDICATORS = [
        # High complexity
        (r"(分析|analyze|推理|reason|比较|compare|评估|evaluate)", 0.3),
        (r"(为什么|why|原因|cause|解释|explain)", 0.2),
        (r"(如果|if|假设|assume|条件|condition)", 0.2),
        (r"(多个|multiple|几个|several|所有|all)", 0.1),
        # Length-based
        (r".{200,}", 0.2),  # Long prompts
        (r".{100,200}", 0.1),  # Medium prompts
    ]
    
    def __init__(
        self,
        low_confidence_threshold: float = 0.5,
        default_task_type: TaskType = TaskType.SIMPLE_QUERY
    ):
        """
        Initialize the task classifier.
        
        Args:
            low_confidence_threshold: Below this, use fallback strategy
            default_task_type: Default type when classification fails
        """
        self.low_confidence_threshold = low_confidence_threshold
        self.default_task_type = default_task_type
        self._last_classification: Optional[ClassificationResult] = None
    
    def classify(self, request: Request) -> TaskType:
        """
        Classify a request into a task type.
        
        Args:
            request: The incoming request with prompt and context
            
        Returns:
            TaskType enum value
        """
        result = self._classify_with_details(request.prompt, request.context)
        self._last_classification = result
        
        # Update request with task type
        request.task_type = result.task_type
        
        logger.info(
            f"Classified request {request.id[:8]}... as {result.task_type.value} "
            f"(confidence: {result.confidence:.2f})"
        )
        
        return result.task_type
    
    def classify_prompt(self, prompt: str) -> ClassificationResult:
        """
        Classify a prompt string directly.
        
        Args:
            prompt: The prompt text to classify
            
        Returns:
            ClassificationResult with details
        """
        return self._classify_with_details(prompt, {})
    
    def get_confidence(self) -> float:
        """Get confidence score for the last classification."""
        if self._last_classification is None:
            return 0.0
        return self._last_classification.confidence
    
    def get_last_result(self) -> Optional[ClassificationResult]:
        """Get the full result of the last classification."""
        return self._last_classification
    
    def _classify_with_details(
        self, 
        prompt: str, 
        context: Dict
    ) -> ClassificationResult:
        """
        Internal classification with full details.
        
        Args:
            prompt: The prompt text
            context: Additional context
            
        Returns:
            ClassificationResult with all details
        """
        prompt_lower = prompt.lower()
        
        # Calculate weighted keyword matches for each task type
        # Process longer keywords first to handle compound terms correctly
        scores: Dict[TaskType, Tuple[float, List[str]]] = {}
        
        for task_type, keyword_weights in self.TASK_KEYWORDS.items():
            matched = []
            total_weight = 0.0
            matched_positions: Set[int] = set()
            
            # Sort by keyword length (descending) to match longer phrases first
            sorted_keywords = sorted(keyword_weights, key=lambda x: len(x[0]), reverse=True)
            
            for keyword, weight in sorted_keywords:
                kw_lower = keyword.lower()
                pos = prompt_lower.find(kw_lower)
                if pos != -1:
                    # Check if this position overlaps with already matched keywords
                    kw_range = set(range(pos, pos + len(kw_lower)))
                    if not kw_range & matched_positions:
                        matched.append(keyword)
                        total_weight += weight
                        matched_positions.update(kw_range)
            
            # Score based on weighted matches
            if matched:
                # Normalize score but allow high-weight matches to dominate
                score = min(1.0, total_weight / 1.5)
                scores[task_type] = (score, matched)
        
        # Calculate complexity score
        complexity_score = self._calculate_complexity(prompt)
        
        # Determine best match
        if scores:
            best_type = max(scores.keys(), key=lambda t: scores[t][0])
            best_score, matched_keywords = scores[best_type]
            
            # Adjust confidence based on complexity
            if best_type == TaskType.COMPLEX_REASONING:
                confidence = min(1.0, best_score + complexity_score * 0.3)
            elif best_type == TaskType.SIMPLE_QUERY:
                confidence = best_score * (1.0 - complexity_score * 0.3)
            else:
                confidence = best_score
            
            return ClassificationResult(
                task_type=best_type,
                confidence=confidence,
                matched_keywords=matched_keywords,
                complexity_score=complexity_score
            )
        
        # No keyword matches - use complexity-based fallback
        if complexity_score > 0.5:
            fallback_type = TaskType.COMPLEX_REASONING
        else:
            fallback_type = self.default_task_type
        
        return ClassificationResult(
            task_type=fallback_type,
            confidence=0.3,  # Low confidence for fallback
            matched_keywords=[],
            complexity_score=complexity_score
        )
    
    def _calculate_complexity(self, prompt: str) -> float:
        """
        Calculate complexity score for a prompt.
        
        Args:
            prompt: The prompt text
            
        Returns:
            Complexity score between 0 and 1
        """
        total_score = 0.0
        
        for pattern, weight in self.COMPLEXITY_INDICATORS:
            if re.search(pattern, prompt, re.IGNORECASE):
                total_score += weight
        
        # Normalize to [0, 1]
        return min(1.0, total_score)
    
    def is_low_confidence(self) -> bool:
        """Check if the last classification had low confidence."""
        return self.get_confidence() < self.low_confidence_threshold
    
    def should_use_multiple_models(self) -> bool:
        """
        Determine if multiple models should be used based on classification.
        
        Returns True if:
        - Classification confidence is low
        - Task type requires validation
        - Task is complex reasoning
        """
        if self._last_classification is None:
            return True
        
        result = self._last_classification
        
        # Low confidence - use multiple models
        if result.confidence < self.low_confidence_threshold:
            return True
        
        # Validation tasks always need multiple models
        if result.task_type == TaskType.DATA_VALIDATION:
            return True
        
        # Complex reasoning benefits from multiple perspectives
        if result.task_type == TaskType.COMPLEX_REASONING:
            return result.confidence < 0.8
        
        return False
