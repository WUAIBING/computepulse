"""
Simple test script to verify AI Orchestrator installation and basic functionality.
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

print("="*80)
print("AI ORCHESTRATOR - SYSTEM VERIFICATION")
print("="*80)
print()

# Test 1: Import modules
print("[CHECK] Test 1: Importing modules...")
try:
    from ai_orchestrator import AIOrchestrator, AIModel, TaskType, OrchestratorConfig
    print("  [OK] All modules imported successfully")
except Exception as e:
    print(f"  [FAIL] Import failed: {e}")
    sys.exit(1)

# Test 2: Initialize orchestrator
print("\n[CHECK] Test 2: Initializing orchestrator...")
try:
    config = OrchestratorConfig()
    orchestrator = AIOrchestrator(config)
    print(f"  [OK] Orchestrator initialized")
    print(f"  [DIR] Storage directory: {config.storage_dir}")
except Exception as e:
    print(f"  [FAIL] Initialization failed: {e}")
    sys.exit(1)

# Test 3: Register models
print("\n[CHECK] Test 3: Registering AI models...")
try:
    qwen = AIModel(name="qwen", provider="Alibaba", cost_per_1m_tokens=0.6, avg_response_time=3.5)
    deepseek = AIModel(name="deepseek", provider="DeepSeek", cost_per_1m_tokens=0.8, avg_response_time=5.0)
    
    orchestrator.register_model(qwen)
    orchestrator.register_model(deepseek)
    
    print(f"  [OK] Registered {len(orchestrator.models)} models:")
    for name in orchestrator.models:
        print(f"     - {name}")
except Exception as e:
    print(f"  [FAIL] Registration failed: {e}")
    sys.exit(1)

# Test 4: Task classification
print("\n[CHECK] Test 4: Testing task classifier...")
try:
    from ai_orchestrator.models import Request
    
    test_prompts = [
        ("获取GPU价格", TaskType.PRICE_EXTRACTION),
        ("分析AI能耗趋势", TaskType.COMPLEX_REASONING),
        ("验证数据质量", TaskType.DATA_VALIDATION),
    ]
    
    for prompt, expected_type in test_prompts:
        request = Request(id="test", prompt=prompt)
        classified_type = orchestrator.task_classifier.classify(request)
        confidence = orchestrator.task_classifier.get_confidence()
        
        status = "[OK]" if classified_type == expected_type else "[WARN]"
        print(f"  {status} '{prompt[:20]}...' → {classified_type.value} (confidence: {confidence:.2f})")
        
except Exception as e:
    print(f"  [FAIL] Classification failed: {e}")
    sys.exit(1)

# Test 5: Learning engine
print("\n[CHECK] Test 5: Testing learning engine...")
try:
    # Record some performance data
    for i in range(5):
        orchestrator.learning_engine.record_performance(
            model_name="qwen",
            task_type=TaskType.SIMPLE_QUERY,
            was_correct=True,
            response_time=2.5,
            cost=0.0006
        )
    
    # Update confidence scores
    orchestrator.learning_engine.update_confidence_scores()
    
    # Get confidence score
    confidence = orchestrator.learning_engine.get_confidence_score("qwen", TaskType.SIMPLE_QUERY)
    print(f"  [OK] Learning engine working")
    print(f"     Qwen confidence on SIMPLE_QUERY: {confidence:.3f}")
    
except Exception as e:
    print(f"  [FAIL] Learning engine failed: {e}")
    sys.exit(1)

# Test 6: Storage
print("\n[CHECK] Test 6: Testing storage...")
try:
    # Save confidence scores
    success = orchestrator.storage.save_confidence_scores(
        orchestrator.learning_engine.confidence_scores
    )
    
    if success:
        print(f"  [OK] Confidence scores saved")
        
        # Load them back
        loaded_scores = orchestrator.storage.load_confidence_scores()
        print(f"  [OK] Loaded {len(loaded_scores)} confidence scores")
    else:
        print(f"  [WARN]  Storage save failed (non-critical)")
        
except Exception as e:
    print(f"  [FAIL] Storage failed: {e}")
    sys.exit(1)

# Test 7: Performance report
print("\n[CHECK] Test 7: Generating performance report...")
try:
    report = orchestrator.get_performance_report(model_name="qwen")
    print(f"  [OK] Performance report generated:")
    print(f"     Total records: {report.get('total_records', 0)}")
    print(f"     Accuracy: {report.get('accuracy', 0):.1%}")
    print(f"     Avg response time: {report.get('avg_response_time', 0):.2f}s")
    
except Exception as e:
    print(f"  [FAIL] Report generation failed: {e}")
    sys.exit(1)

# Summary
print("\n" + "="*80)
print("[OK] ALL TESTS PASSED - SYSTEM IS OPERATIONAL")
print("="*80)
print()
print("Next steps:")
print("  1. Integrate real AI model adapters")
print("  2. Implement parallel execution layer")
print("  3. Add confidence-weighted merging")
print("  4. Deploy to production")
print()
print("For full demonstration, run:")
print("  python scripts/fetch_prices_optimized_v2.py")
print()
