"""
Task Classifier for categorizing requests into task types.
"""

import logging
import re
from typing import Tuple

from .models import Request, TaskType
from .config import OrchestratorConfig


logger = logging.getLogger(__name__)


class TaskClassifier:
    """
    Classifies incoming requests into task types based on content analysis.
    
    Uses keyword-based classification with confidence scoring.
    """
    
    def __init__(self, config: OrchestratorConfig):
        self.config = config
        self.classification_confidence = 0.0
        
        # Define keywords for each task type
        self.task_keywords = {
            TaskType.SIMPLE_QUERY: [
                "查找", "获取", "列出", "显示", "what is", "get", "list", "show",
                "价格", "price", "cost", "多少钱"
            ],
            TaskType.COMPLEX_REASONING: [
                "分析", "比较", "评估", "推理", "解释", "为什么",
                "analyze", "compare", "evaluate", "reason", "explain", "why",
                "趋势", "trend", "预测", "predict", "关系", "relationship"
            ],
            TaskType.DATA_VALIDATION: [
                "验证", "检查", "确认", "审核", "质量",
                "validate", "check", "verify", "audit", "quality",
                "正确", "错误", "异常", "correct", "error", "anomaly"
            ],
            TaskType.PRICE_EXTRACTION: [
                "GPU", "Token", "价格", "租赁", "费用", "成本",
                "price", "rental", "fee", "cost", "pricing",
                "H100", "A100", "模型", "model", "API"
            ],
            TaskType.HISTORICAL_ANALYSIS: [
                "历史", "过去", "年度", "趋势", "变化",
                "history", "historical", "past", "annual", "trend", "change",
                "2018", "2019", "2020", "2021", "2022", "2023", "2024"
            ]
        }
    
    def classify(self, request: Request) -> TaskType:
        """
        Classify a request into a task type.
        
        Args:
            request: The incoming request
            
        Returns:
            TaskType enum value
        """
        prompt_lower = request.prompt.lower()
        
        # Calculate scores for each task type
        scores = {}
        for task_type, keywords in self.task_keywords.items():
            score = sum(1 for keyword in keywords if keyword.lower() in prompt_lower)
            scores[task_type] = score
        
        # Find task type with highest score
        if max(scores.values()) == 0:
            # No keywords matched, default to SIMPLE_QUERY
            self.classification_confidence = 0.3
            logger.info(f"No keywords matched, defaulting to SIMPLE_QUERY (low confidence)")
            return TaskType.SIMPLE_QUERY
        
        best_task_type = max(scores, key=scores.get)
        best_score = scores[best_task_type]
        total_score = sum(scores.values())
        
        # Calculate confidence as ratio of best score to total
        self.classification_confidence = best_score / total_score if total_score > 0 else 0.5
        
        # Check for specific patterns that override keyword matching
        if self._is_price_extraction(prompt_lower):
            best_task_type = TaskType.PRICE_EXTRACTION
            self.classification_confidence = 0.9
        elif self._is_validation_request(prompt_lower):
            best_task_type = TaskType.DATA_VALIDATION
            self.classification_confidence = 0.9
        
        logger.info(
            f"Classified request as {best_task_type.value} "
            f"(confidence: {self.classification_confidence:.2f})"
        )
        
        # Update request with task type
        request.task_type = best_task_type
        
        return best_task_type
    
    def _is_price_extraction(self, prompt_lower: str) -> bool:
        """Check if request is specifically about price extraction."""
        price_patterns = [
            r'gpu.*价格',
            r'token.*价格',
            r'price.*gpu',
            r'price.*token',
            r'租赁.*价格',
            r'rental.*price'
        ]
        return any(re.search(pattern, prompt_lower) for pattern in price_patterns)
    
    def _is_validation_request(self, prompt_lower: str) -> bool:
        """Check if request is specifically about validation."""
        validation_patterns = [
            r'验证.*数据',
            r'检查.*质量',
            r'validate.*data',
            r'check.*quality',
            r'异常.*检测',
            r'anomaly.*detect'
        ]
        return any(re.search(pattern, prompt_lower) for pattern in validation_patterns)
    
    def get_confidence(self) -> float:
        """
        Get confidence score for the last classification.
        
        Returns:
            Confidence score between 0 and 1
        """
        return self.classification_confidence
    
    def is_low_confidence(self, threshold: float = 0.5) -> bool:
        """
        Check if the last classification had low confidence.
        
        Args:
            threshold: Confidence threshold
            
        Returns:
            True if confidence is below threshold
        """
        return self.classification_confidence < threshold
