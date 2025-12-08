#!/usr/bin/env python3
"""
Basic Usage Example for AI Orchestrator

This example demonstrates the simplest way to use the AI Orchestrator
with default settings and a single AI model.
"""

import asyncio
import json
from datetime import datetime

# Import AI Orchestrator components
from ai_orchestrator import AIOrchestrator, AIModel, Response, TaskType


async def mock_model_call(model, request):
    """
    Mock function to simulate AI model calls.

    In a real application, this would call your actual AI model API.
    """
    print(f"  [Model Call] {model.name} processing request: {request.prompt[:50]}...")

    # Simulate API call delay
    await asyncio.sleep(0.1)

    # Return mock response
    return Response(
        model_name=model.name,
        content=f"Mock response from {model.name} for: {request.prompt[:50]}...",
        response_time=0.1,
        token_count=150,
        cost=model.cost_per_1m_tokens * 0.15,
        timestamp=datetime.now(),
        success=True
    )


async def main():
    """Main example function."""
    print("=" * 80)
    print("AI Orchestrator - Basic Usage Example")
    print("=" * 80)
    print()

    # Step 1: Create the orchestrator with default settings
    print("Step 1: Creating AI Orchestrator...")
    orchestrator = AIOrchestrator()
    print("  ✓ Orchestrator created with default configuration")
    print()

    # Step 2: Register AI models
    print("Step 2: Registering AI models...")
    models = [
        AIModel(
            name="qwen-max",
            provider="Alibaba",
            cost_per_1m_tokens=0.4,
            avg_response_time=2.0
        ),
        AIModel(
            name="doubao-pro",
            provider="ByteDance",
            cost_per_1m_tokens=0.2,
            avg_response_time=1.5
        ),
        AIModel(
            name="deepseek-v3",
            provider="DeepSeek",
            cost_per_1m_tokens=0.15,
            avg_response_time=1.8
        )
    ]

    for model in models:
        orchestrator.register_model(model)
        print(f"  ✓ Registered: {model.name} ({model.provider})")
    print()

    # Step 3: Process a request
    print("Step 3: Processing a request...")
    prompt = """
    Please search for the latest NVIDIA H100 GPU cloud rental prices from major providers.
    Include AWS, Google Cloud, Azure, and any other major cloud providers.
    Return the results as a JSON list with provider, price, and region information.
    """

    print(f"  Prompt: {prompt[:100]}...")
    print()

    result = await orchestrator.process_request(
        prompt=prompt,
        quality_threshold=0.8,
        cost_limit=0.5,
        model_call_func=mock_model_call
    )

    print()
    print("Step 4: Processing results...")
    print(f"  ✓ Request completed successfully")
    print(f"  ✓ Data received: {type(result.data)}")
    print(f"  ✓ Contributing models: {result.contributing_models}")
    print(f"  ✓ Confidence scores: {result.confidence_scores}")
    print(f"  ✓ Flagged for review: {result.flagged_for_review}")
    print()

    # Step 5: Display metadata
    print("Step 5: Request metadata:")
    for key, value in result.metadata.items():
        print(f"  - {key}: {value}")
    print()

    # Step 6: Validate the result
    print("Step 6: Validating result...")
    # Note: In a real scenario, you'd validate the actual data
    print("  ✓ Validation completed (mock)")
    print()

    # Step 7: Generate performance report
    print("Step 7: Performance report:")
    report = orchestrator.generate_performance_report(output_format='dict')
    print(f"  - Total requests: {report.get('total_requests', 0)}")
    print(f"  - Success rate: {report.get('success_rate', 0):.2f}%")
    print(f"  - Average response time: {report.get('avg_response_time', 0):.3f}s")
    print(f"  - Average cost: ${report.get('avg_cost', 0):.4f}")
    print()

    # Step 8: Get confidence scores
    print("Step 8: Confidence scores by task type:")
    for task_type in TaskType:
        scores = orchestrator.get_confidence_scores(task_type)
        if scores:
            print(f"  {task_type.value}:")
            for model, score in scores.items():
                print(f"    - {model}: {score:.3f}")
    print()

    # Step 9: Simulate feedback
    print("Step 9: Recording feedback...")
    for model_name in result.contributing_models:
        orchestrator.record_feedback(
            request_id=result.metadata.get('request_id', 'unknown'),
            model_name=model_name,
            task_type=TaskType.DATA_VALIDATION,
            was_correct=True,
            response_time=0.1,
            cost=0.04
        )
    print("  ✓ Feedback recorded for all models")
    print()

    print("=" * 80)
    print("Example completed successfully!")
    print("=" * 80)


if __name__ == "__main__":
    # Run the example
    asyncio.run(main())
