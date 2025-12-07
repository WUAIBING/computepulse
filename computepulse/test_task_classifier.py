"""
Test script for Task Classifier.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ai_orchestrator.task_classifier import TaskClassifier, ClassificationResult
from ai_orchestrator.models import TaskType, Request


def test_classifier():
    """Test the task classifier with various prompts."""
    classifier = TaskClassifier()
    
    test_cases = [
        # Simple queries
        ("请查询最新的美元兑人民币汇率", TaskType.PRICE_EXTRACTION),
        ("今天天气怎么样", TaskType.SIMPLE_QUERY),
        ("What is the current Bitcoin price?", TaskType.PRICE_EXTRACTION),
        
        # Complex reasoning
        ("分析一下为什么最近GPU价格上涨，并预测未来趋势", TaskType.COMPLEX_REASONING),
        ("Compare the performance of different AI models and explain why", TaskType.COMPLEX_REASONING),
        
        # Data validation
        ("验证这个数据是否正确：RTX 4090价格为$1599", TaskType.DATA_VALIDATION),
        ("Check if the exchange rate data is accurate", TaskType.DATA_VALIDATION),
        
        # Price extraction
        ("获取NVIDIA RTX 4090的最新价格", TaskType.PRICE_EXTRACTION),
        ("查询当前算力市场的GPU报价", TaskType.PRICE_EXTRACTION),
        
        # Historical analysis
        ("分析过去一年的GPU价格走势", TaskType.HISTORICAL_ANALYSIS),
        ("Show the historical trend of exchange rates", TaskType.HISTORICAL_ANALYSIS),
    ]
    
    print("=" * 70)
    print("Task Classifier Test Results")
    print("=" * 70)
    
    correct = 0
    total = len(test_cases)
    
    for prompt, expected_type in test_cases:
        result = classifier.classify_prompt(prompt)
        is_correct = result.task_type == expected_type
        correct += 1 if is_correct else 0
        
        status = "[OK]" if is_correct else "[FAIL]"
        print(f"\n{status} Prompt: {prompt[:50]}...")
        print(f"   Expected: {expected_type.value}")
        print(f"   Got: {result.task_type.value} (confidence: {result.confidence:.2f})")
        print(f"   Keywords: {result.matched_keywords}")
        print(f"   Complexity: {result.complexity_score:.2f}")
    
    print("\n" + "=" * 70)
    print(f"Accuracy: {correct}/{total} ({correct/total*100:.1f}%)")
    print("=" * 70)
    
    # Test with Request object
    print("\n\nTesting with Request object:")
    request = Request.create(
        prompt="请分析并验证最新的GPU价格数据是否准确",
        quality_threshold=0.8
    )
    task_type = classifier.classify(request)
    print(f"Request task_type: {request.task_type}")
    print(f"Should use multiple models: {classifier.should_use_multiple_models()}")
    print(f"Is low confidence: {classifier.is_low_confidence()}")


if __name__ == "__main__":
    test_classifier()
