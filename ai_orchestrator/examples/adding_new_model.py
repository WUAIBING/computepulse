#!/usr/bin/env python3
"""
Adding New AI Model Example for AI Orchestrator

This example demonstrates how to add new AI models to the orchestrator,
configure them properly, and monitor their performance.
"""

import asyncio
import json
from datetime import datetime

from ai_orchestrator import (
    AIOrchestrator,
    AIModel,
    Response,
    TaskType
)


async def mock_model_call(model, request):
    """Mock function to simulate AI model calls."""
    await asyncio.sleep(0.05)

    # Simulate different response characteristics based on model
    base_response = f"Response from {model.name}"

    return Response(
        model_name=model.name,
        content=base_response,
        response_time=model.avg_response_time,
        token_count=100,
        cost=model.cost_per_1m_tokens * 0.1,
        timestamp=datetime.now(),
        success=True
    )


async def main():
    """Main example function."""
    print("=" * 80)
    print("AI Orchestrator - Adding New AI Model Example")
    print("=" * 80)
    print()

    # Step 1: Create orchestrator
    print("Step 1: Creating AI Orchestrator...")
    orchestrator = AIOrchestrator()
    print("  ✓ Orchestrator created")
    print()

    # Step 2: Add initial models
    print("Step 2: Adding initial models...")
    initial_models = [
        {
            "name": "qwen-max",
            "provider": "Alibaba",
            "cost": 0.4,
            "time": 2.0,
            "description": "Fast and reliable with search"
        },
        {
            "name": "glm-4-flash",
            "provider": "ZHIPU AI",
            "cost": 0.2,
            "time": 1.5,
            "description": "Fast Chinese model"
        }
    ]

    for model_config in initial_models:
        model = AIModel(
            name=model_config["name"],
            provider=model_config["provider"],
            cost_per_1m_tokens=model_config["cost"],
            avg_response_time=model_config["time"]
        )
        orchestrator.register_model(model)
        print(f"  ✓ Added: {model_config['name']} - {model_config['description']}")
    print()

    # Step 3: Check initial state
    print("Step 3: Checking initial model state...")
    print(f"  Registered models: {list(orchestrator.models.keys())}")
    print()

    # Step 4: Add a new model
    print("Step 4: Adding a new AI model...")
    new_model = AIModel(
        name="deepseek-v3",
        provider=" "DeepSeek",
        cost_per_1m_tokens=0.15,
        avg_response_time=1.8
    )

    orchestrator.register_model(new_model)
    print(f"  ✓ Added new model: {new_model.name}")
    print(f"    Provider: {new_model.provider}")
    print(f"    Cost: ${new_model.cost_per_1m_tokens}/1M tokens")
    print(f"    Avg response time: {new_model.avg_response_time}s")
    print()

    # Step 5: Add another model with specific configuration
    print("Step 5: Adding a premium model...")
    premium_model = AIModel(
        name="gpt-4-turbo",
        provider="OpenAI",
        cost_per_1m_tokens=1.0,
        avg_response_time=2.5
    )

    orchestrator.register_model(premium_model)
    print(f"  ✓ Added premium model: {premium_model.name}")
    print(f"    This model is more expensive but potentially higher quality")
    print()

    # Step 6: Process a request to test all models
    print("Step 6: Processing request with all models...")
    prompt = "What are the latest developments in AI?"

    result = await orchestrator.process_request(
        prompt=prompt,
        quality_threshold=0.8,
        cost_limit=0.5,
        model_call_func=mock_model_call
    )

    print(f"  ✓ Request processed")
    print(f"  Models used: {result.contributing_models}")
    print(f"  Confidence scores:")
    for model, score in result.confidence_scores.items():
        print(f"    - {model}: {score:.3f}")
    print()

    # Step 7: Check confidence scores
    print("Step 7: Checking confidence scores by task type...")
    for task_type in TaskType:
        scores = orchestrator.get_confidence_scores(task_type)
        if scores:
            print(f"  {task_type.value}:")
            for model_name, score in scores.items():
                print(f"    - {model_name}: {score:.3f}")
    print()

    # Step 8: Simulate feedback for new model
    print("Step 8: Recording feedback for new model...")
    orchestrator.record_feedback(
        request_id="test-123",
        model_name="deepseek-v3",
        task_type=TaskType.COMPLEX_REASONING,
        was_correct=True,
        response_time=1.8,
        cost=0.015
    )
    print("  ✓ Feedback recorded for deepseek-v3")
    print()

    # Step 9: Generate performance report
    print("Step 9: Generating performance report...")
    report = orchestrator.generate_performance_report(output_format='dict')
    print(f"  Total requests: {report.get('total_requests', 0)}")
    print(f"  Success rate: {report.get('success_rate', 0):.2f}%")
    print(f"  Average response time: {report.get('avg_response_time', 0):.3f}s")
    print(f"  Average cost: ${report.get('avg_cost', 0):.4f}")
    print()

    # Step 10: Get model-specific performance
    print("Step 10: Model-specific performance...")
    for model_name in orchestrator.models.keys():
        model_perf = orchestrator.get_performance_report(model_name=model_name)
        if model_perf:
            print(f"  {model_name}:")
            print(f"    Requests: {model_perf.get('total_requests', 0)}")
            print(f"    Success rate: {model_perf.get('success_rate', 0):.2f}%")
            print(f"    Avg response time: {model_perf.get('avg_response_time', 0):.3f}s")
            print(f"    Total cost: ${model_perf.get('total_cost', 0):.4f}")
    print()

    # Step 11: Disable a model
    print("Step 11: Disabling a model...")
    # Note: There's no direct disable method, but we can demonstrate
    # the concept by checking if a model is in the list
    print(f"  Currently registered models: {list(orchestrator.models.keys())}")
    print("  (In a real scenario, you would remove or disable the model)")
    print()

    # Step 12: Best practices for model management
    print("Step 12: Model management best practices...")
    print("  ✓ Register models with accurate cost and response time data")
    print("  ✓ Monitor confidence scores regularly")
    print("  ✓ Provide feedback to improve model performance")
    print("  ✓ Remove or disable underperforming models")
    print("  ✓ Balance cost and quality based on use case")
    print()

    # Step 13: Advanced - Custom model configuration
    print("Step 13: Advanced - Custom model scenarios...")

    # Scenario 1: High-volume, low-cost
    print("\n  Scenario 1: High-volume, low-cost tasks")
    budget_model = AIModel(
        name="budget-optimizer",
        provider="BudgetAI",
        cost_per_1m_tokens=0.05,  # Very cheap
        avg_response_time=3.0  # Slower but acceptable
    )
    orchestrator.register_model(budget_model)
    print(f"    ✓ Added budget model: {budget_model.name}")

    # Scenario 2: Specialized model
    print("\n  Scenario 2: Specialized model for specific tasks")
    specialized_model = AIModel(
        name="code-specialist",
        provider="CodeAI",
        cost_per_1m_tokens=0.8,  # More expensive
        avg_response_time=2.0  # Good speed
    )
    orchestrator.register_model(specialized_model)
    print(f"    ✓ Added specialized model: {specialized_model.name}")

    # Scenario 3: Experimental model
    print("\n  Scenario 3: Experimental model (monitor closely)")
    experimental_model = AIModel(
        name="experimental-v1",
        provider="ResearchLab",
        cost_per_1m_tokens=0.3,
        avg_response_time=2.5
    )
    orchestrator.register_model(experimental_model)
    print(f"    ✓ Added experimental model: {experimental_model.name}")
    print("    ⚠ Monitor this model closely for quality and stability")

    print()

    # Final summary
    print("=" * 80)
    print("Final Model Inventory")
    print("=" * 80)
    print(f"\nTotal models registered: {len(orchestrator.models)}")
    print("\nModel details:")
    for name, model in orchestrator.models.items():
        print(f"  - {name}")
        print(f"    Provider: {model.provider}")
        print(f"    Cost: ${model.cost_per_1m_tokens}/1M tokens")
        print(f"    Avg response time: {model.avg_response_time}s")

    print("\n" + "=" * 80)
    print("Adding New AI Model Example Completed!")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
