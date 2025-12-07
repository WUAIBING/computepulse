"""
Test script for Learning Engine.
"""

import sys
import os
import tempfile
import shutil

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ai_orchestrator.learning_engine import LearningEngine
from ai_orchestrator.storage import StorageManager
from ai_orchestrator.config import OrchestratorConfig
from ai_orchestrator.models import TaskType


def test_learning_engine():
    """Test the learning engine functionality."""
    # Create temporary storage directory
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Initialize config and storage
        config = OrchestratorConfig(storage_dir=temp_dir)
        storage = StorageManager(config)
        engine = LearningEngine(storage)
        
        print("=" * 60)
        print("Learning Engine Test")
        print("=" * 60)
        
        # Test 1: Record performance data
        print("\n1. Recording performance data...")
        
        # Simulate Qwen performing well on SIMPLE_QUERY
        for i in range(10):
            engine.record_performance(
                model_name="qwen",
                task_type=TaskType.SIMPLE_QUERY,
                was_correct=True,
                response_time=2.0 + i * 0.1,
                cost=0.001,
                token_count=100,
            )
        
        # Simulate DeepSeek performing well on COMPLEX_REASONING
        for i in range(10):
            engine.record_performance(
                model_name="deepseek",
                task_type=TaskType.COMPLEX_REASONING,
                was_correct=True,
                response_time=5.0 + i * 0.2,
                cost=0.003,
                token_count=500,
            )
        
        # Simulate GLM with mixed results on DATA_VALIDATION
        for i in range(10):
            engine.record_performance(
                model_name="glm",
                task_type=TaskType.DATA_VALIDATION,
                was_correct=(i % 3 != 0),  # 70% accuracy
                response_time=3.0,
                cost=0.002,
                token_count=200,
            )
        
        print("   [OK] Recorded 30 performance records")
        
        # Test 2: Update confidence scores
        print("\n2. Updating confidence scores...")
        engine.update_confidence_scores()
        print("   [OK] Confidence scores updated")
        
        # Test 3: Get confidence scores
        print("\n3. Getting confidence scores...")
        
        qwen_simple = engine.get_confidence_score("qwen", TaskType.SIMPLE_QUERY)
        deepseek_reasoning = engine.get_confidence_score("deepseek", TaskType.COMPLEX_REASONING)
        glm_validation = engine.get_confidence_score("glm", TaskType.DATA_VALIDATION)
        
        print(f"   Qwen on SIMPLE_QUERY: {qwen_simple:.3f}")
        print(f"   DeepSeek on COMPLEX_REASONING: {deepseek_reasoning:.3f}")
        print(f"   GLM on DATA_VALIDATION: {glm_validation:.3f}")
        
        # Verify scores make sense (with only 10 samples, scores are adjusted by sample size)
        # With 10 samples out of 100 needed for full confidence, adjustment = 0.1
        # So scores will be closer to 0.5 (default) than to actual accuracy
        assert qwen_simple > 0.5, f"Qwen should have above-default confidence, got {qwen_simple}"
        assert deepseek_reasoning > 0.5, f"DeepSeek should have above-default confidence, got {deepseek_reasoning}"
        assert glm_validation > 0.45, f"GLM should have reasonable confidence, got {glm_validation}"
        print("   [OK] Confidence scores are reasonable")
        
        # Test 4: Get best model for task
        print("\n4. Getting best model for each task...")
        
        best_simple = engine.get_best_model_for_task(TaskType.SIMPLE_QUERY)
        best_reasoning = engine.get_best_model_for_task(TaskType.COMPLEX_REASONING)
        best_validation = engine.get_best_model_for_task(TaskType.DATA_VALIDATION)
        
        print(f"   Best for SIMPLE_QUERY: {best_simple}")
        print(f"   Best for COMPLEX_REASONING: {best_reasoning}")
        print(f"   Best for DATA_VALIDATION: {best_validation}")
        
        assert best_simple == "qwen", f"Expected qwen, got {best_simple}"
        assert best_reasoning == "deepseek", f"Expected deepseek, got {best_reasoning}"
        print("   [OK] Best model selection works correctly")
        
        # Test 5: Get models above threshold
        print("\n5. Getting models above threshold...")
        
        models_above_70 = engine.get_models_above_threshold(TaskType.SIMPLE_QUERY, 0.7)
        print(f"   Models above 0.7 for SIMPLE_QUERY: {models_above_70}")
        
        # Test 6: Apply feedback
        print("\n6. Testing feedback mechanism...")
        
        old_score = engine.get_confidence_score("qwen", TaskType.SIMPLE_QUERY)
        engine.apply_feedback("qwen", TaskType.SIMPLE_QUERY, was_correct=False)
        new_score = engine.get_confidence_score("qwen", TaskType.SIMPLE_QUERY)
        
        print(f"   Qwen score before negative feedback: {old_score:.3f}")
        print(f"   Qwen score after negative feedback: {new_score:.3f}")
        assert new_score < old_score, "Score should decrease after negative feedback"
        print("   [OK] Negative feedback reduces score")
        
        engine.apply_feedback("qwen", TaskType.SIMPLE_QUERY, was_correct=True)
        newer_score = engine.get_confidence_score("qwen", TaskType.SIMPLE_QUERY)
        print(f"   Qwen score after positive feedback: {newer_score:.3f}")
        assert newer_score > new_score, "Score should increase after positive feedback"
        print("   [OK] Positive feedback increases score")
        
        # Test 7: Performance report
        print("\n7. Generating performance report...")
        
        report = engine.get_performance_report(model_name="qwen", task_type=TaskType.SIMPLE_QUERY)
        print(f"   Total requests: {report.total_requests}")
        print(f"   Accuracy: {report.accuracy:.2%}")
        print(f"   Avg response time: {report.avg_response_time:.2f}s")
        print(f"   Avg cost: ${report.avg_cost:.4f}")
        print("   [OK] Performance report generated")
        
        print("\n" + "=" * 60)
        print("[OK] All Learning Engine tests passed!")
        print("=" * 60)
        
    finally:
        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    test_learning_engine()
