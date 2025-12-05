"""
Optimized data fetching using the new AI Orchestrator system.

This script demonstrates the integration of the intelligent AI collaboration system
with the existing ComputePulse data fetching workflow.
"""

import sys
import os
import json
import asyncio
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from ai_orchestrator import AIOrchestrator, AIModel, TaskType, OrchestratorConfig


# Initialize the orchestrator
config = OrchestratorConfig()
orchestrator = AIOrchestrator(config)

# Register available AI models
qwen_model = AIModel(
    name="qwen",
    provider="Alibaba DashScope",
    cost_per_1m_tokens=0.6,  # Estimated
    avg_response_time=3.5
)

deepseek_model = AIModel(
    name="deepseek",
    provider="DeepSeek",
    cost_per_1m_tokens=0.8,  # Estimated
    avg_response_time=5.0
)

doubao_model = AIModel(
    name="doubao",
    provider="Volcengine",
    cost_per_1m_tokens=1.2,  # Estimated
    avg_response_time=15.0
)

orchestrator.register_model(qwen_model)
orchestrator.register_model(deepseek_model)
orchestrator.register_model(doubao_model)


async def fetch_with_orchestrator(prompt: str, task_type_hint: str = "price_extraction"):
    """
    Fetch data using the AI orchestrator.
    
    Args:
        prompt: The prompt to send
        task_type_hint: Hint about the task type
        
    Returns:
        Merged result from the orchestrator
    """
    print(f"\n{'='*80}")
    print(f"[{datetime.now()}] Fetching data with AI Orchestrator")
    print(f"{'='*80}\n")
    
    # Process request through orchestrator
    result = await orchestrator.process_request(
        prompt=prompt,
        context={"hint": task_type_hint},
        quality_threshold=0.7,  # Require 70% confidence
        cost_limit=None  # No cost limit for now
    )
    
    print(f"\n📊 Orchestrator Result:")
    print(f"  - Task Type: {result.metadata.get('task_type')}")
    print(f"  - Models Used: {', '.join(result.contributing_models)}")
    print(f"  - Confidence Scores:")
    for model, score in result.confidence_scores.items():
        print(f"    • {model}: {score:.3f}")
    print(f"  - Classification Confidence: {result.metadata.get('classification_confidence', 0):.3f}")
    
    if result.flagged_for_review:
        print(f"  ⚠️  Result flagged for manual review")
    
    return result


async def demonstrate_learning():
    """Demonstrate the learning capabilities of the system."""
    print(f"\n{'='*80}")
    print(f"🧠 DEMONSTRATING LEARNING ENGINE")
    print(f"{'='*80}\n")
    
    # Simulate some performance feedback
    print("📝 Recording simulated performance data...\n")
    
    # Qwen performs well on simple queries
    for i in range(10):
        orchestrator.record_feedback(
            request_id=f"sim_{i}",
            model_name="qwen",
            task_type=TaskType.SIMPLE_QUERY,
            was_correct=True if i < 9 else False,  # 90% accuracy
            response_time=2.5,
            cost=0.0006
        )
    
    # DeepSeek performs well on complex reasoning
    for i in range(10):
        orchestrator.record_feedback(
            request_id=f"sim_{i}",
            model_name="deepseek",
            task_type=TaskType.COMPLEX_REASONING,
            was_correct=True if i < 9 else False,  # 90% accuracy
            response_time=5.2,
            cost=0.0008
        )
    
    # Doubao performs well on validation
    for i in range(10):
        orchestrator.record_feedback(
            request_id=f"sim_{i}",
            model_name="doubao",
            task_type=TaskType.DATA_VALIDATION,
            was_correct=True if i < 8 else False,  # 80% accuracy
            response_time=12.0,
            cost=0.0012
        )
    
    print("✅ Performance data recorded\n")
    
    # Show updated confidence scores
    print("📊 Updated Confidence Scores:\n")
    
    for task_type in [TaskType.SIMPLE_QUERY, TaskType.COMPLEX_REASONING, TaskType.DATA_VALIDATION]:
        print(f"  {task_type.value}:")
        scores = orchestrator.get_confidence_scores(task_type)
        for model, score in sorted(scores.items(), key=lambda x: x[1], reverse=True):
            print(f"    • {model}: {score:.3f}")
        print()
    
    # Show performance reports
    print("📈 Performance Reports:\n")
    
    for model_name in ["qwen", "deepseek", "doubao"]:
        report = orchestrator.get_performance_report(model_name=model_name)
        print(f"  {model_name}:")
        print(f"    • Total Requests: {report.get('total_records', 0)}")
        print(f"    • Accuracy: {report.get('accuracy', 0):.1%}")
        print(f"    • Avg Response Time: {report.get('avg_response_time', 0):.2f}s")
        print(f"    • Total Cost: ${report.get('total_cost', 0):.4f}")
        print()


async def main():
    """Main demonstration function."""
    print(f"\n{'='*80}")
    print(f"🚀 AI ORCHESTRATOR DEMONSTRATION")
    print(f"{'='*80}\n")
    
    print(f"System initialized with {len(orchestrator.models)} AI models:")
    for model_name, model in orchestrator.models.items():
        print(f"  • {model_name} ({model.provider})")
    print()
    
    # Example 1: GPU Price Query (Simple Query)
    gpu_prompt = """
    请使用联网搜索功能，查找当前最新的 NVIDIA H100 和 A100 的云租赁价格。
    返回 JSON 格式。
    """
    
    result1 = await fetch_with_orchestrator(gpu_prompt, "price_extraction")
    
    # Example 2: Complex Analysis (Complex Reasoning)
    analysis_prompt = """
    分析全球 AI 数据中心能耗趋势，比较 2023 和 2024 年的变化，
    并解释主要驱动因素。
    """
    
    result2 = await fetch_with_orchestrator(analysis_prompt, "complex_reasoning")
    
    # Example 3: Data Validation
    validation_prompt = """
    验证以下 GPU 价格数据的合理性：
    H100: $2.50/hour
    A100: $1.20/hour
    检查是否有异常。
    """
    
    result3 = await fetch_with_orchestrator(validation_prompt, "data_validation")
    
    # Demonstrate learning
    await demonstrate_learning()
    
    # Show how the system adapts
    print(f"\n{'='*80}")
    print(f"🎯 ADAPTIVE ROUTING DEMONSTRATION")
    print(f"{'='*80}\n")
    
    print("After learning, the system will now intelligently route requests:\n")
    
    # Simple query should now prefer Qwen (high confidence)
    print("1. Simple Query → Should prefer Qwen (learned high confidence)")
    result4 = await fetch_with_orchestrator("获取 GPU 价格", "simple_query")
    
    # Complex reasoning should prefer DeepSeek
    print("\n2. Complex Reasoning → Should prefer DeepSeek (learned high confidence)")
    result5 = await fetch_with_orchestrator("分析 AI 能耗趋势", "complex_reasoning")
    
    print(f"\n{'='*80}")
    print(f"✅ DEMONSTRATION COMPLETE")
    print(f"{'='*80}\n")
    
    print("Key Benefits Demonstrated:")
    print("  ✓ Intelligent task classification")
    print("  ✓ Adaptive model selection based on learned performance")
    print("  ✓ Cost optimization through smart routing")
    print("  ✓ Continuous learning from feedback")
    print("  ✓ Performance tracking and reporting")
    print()
    
    print("Next Steps:")
    print("  1. Integrate actual AI model adapters (Qwen, DeepSeek, Doubao)")
    print("  2. Implement parallel execution layer")
    print("  3. Add confidence-weighted result merging")
    print("  4. Deploy to production and monitor performance")
    print()


if __name__ == "__main__":
    asyncio.run(main())
