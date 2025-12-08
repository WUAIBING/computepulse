#!/usr/bin/env python3
"""
Custom Configuration Example for AI Orchestrator

This example demonstrates how to use custom configuration settings
to optimize the orchestrator for specific use cases.
"""

import asyncio
import json
from datetime import datetime

from ai_orchestrator import (
    AIOrchestrator,
    OrchestratorConfig,
    AIModel,
    Response,
    TaskType
)


async def mock_model_call(model, request):
    """Mock function to simulate AI model calls."""
    await asyncio.sleep(0.05)

    return Response(
        model_name=model.name,
        content=f"Response from {model.name}",
        response_time=0.05,
        token_count=100,
        cost=model.cost_per_1m_tokens * 0.1,
        timestamp=datetime.now(),
        success=True
    )


async def main():
    """Main example function."""
    print("=" * 80)
    print("AI Orchestrator - Custom Configuration Example")
    print("=" * 80)
    print()

    # Example 1: High Quality Configuration
    print("Example 1: High Quality Configuration")
    print("-" * 80)

    config_high_quality = OrchestratorConfig(
        default_quality_threshold=0.95,
        default_cost_limit=2.0,
        simple_query_model_count=2,
        complex_reasoning_model_count=3,
        validation_model_count=3,
        model_timeout_seconds=60.0,
        enable_early_result_processing=True
    )

    orchestrator_high = AIOrchestrator(config_high_quality)

    # Register models
    for model_config in [
        {"name": "qwen-max", "provider": "Alibaba", "cost": 0.4, "time": 2.0},
        {"name": "claude-3", "provider": "Anthropic", "cost": 0.6, "time": 2.5},
        {"name": "gpt-4", "provider": "OpenAI", "cost": 0.8, "time": 3.0}
    ]:
        model = AIModel(
            name=model_config["name"],
            provider=model_config["provider"],
            cost_per_1m_tokens=model_config["cost"],
            avg_response_time=model_config["time"]
        )
        orchestrator_high.register_model(model)

    print(f"  Quality threshold: {config_high_quality.default_quality_threshold}")
    print(f"  Cost limit: ${config_high_quality.default_cost_limit}")
    print(f"  Models for simple queries: {config_high_quality.simple_query_model_count}")
    print(f"  Models for complex tasks: {config_high_quality.complex_reasoning_model_count}")
    print()

    # Example 2: Fast & Cheap Configuration
    print("Example 2: Fast & Cheap Configuration")
    print("-" * 80)

    config_fast_cheap = OrchestratorConfig(
        default_quality_threshold=0.7,
        default_cost_limit=0.2,
        simple_query_model_count=1,
        complex_reasoning_model_count=1,
        validation_model_count=2,
        model_timeout_seconds=15.0,
        enable_early_result_processing=True
    )

    orchestrator_fast = AIOrchestrator(config_fast_cheap)

    # Register cheaper models
    for model_config in [
        {"name": "deepseek-v3", "provider": "DeepSeek", "cost": 0.15, "time": 1.5},
        {"name": "doubao-pro", "provider": "ByteDance", "cost": 0.2, "time": 1.2}
    ]:
        model = AIModel(
            name=model_config["name"],
            provider=model_config["provider"],
            cost_per_1m_tokens=model_config["cost"],
            avg_response_time=model_config["time"]
        )
        orchestrator_fast.register_model(model)

    print(f"  Quality threshold: {config_fast_cheap.default_quality_threshold}")
    print(f"  Cost limit: ${config_fast_cheap.default_cost_limit}")
    print(f"  Timeout: {config_fast_cheap.model_timeout_seconds}s")
    print()

    # Example 3: Validation-Focused Configuration
    print("Example 3: Validation-Focused Configuration")
    print("-" * 80)

    config_validation = OrchestratorConfig(
        default_quality_threshold=0.9,
        default_cost_limit=1.0,
        validation_model_count=3,
        model_timeout_seconds=45.0,
        enable_early_result_processing=False  # Wait for all models for validation
    )

    orchestrator_validation = AIOrchestrator(config_validation)

    # Register diverse models for validation
    for model_config in [
        {"name": "qwen-max", "provider": "Alibaba", "cost": 0.4, "time": 2.0},
        {"name": "deepseek-v3", "provider": "DeepSeek", "cost": 0.15, "time": 1.8},
        {"name": "doubao-pro", "provider": "ByteDance", "cost": 0.2, "time": 1.5}
    ]:
        model = AIModel(
            name=model_config["name"],
            provider=model_config["provider"],
            cost_per_1m_tokens=model_config["cost"],
            avg_response_time=model_config["time"]
        )
        orchestrator_validation.register_model(model)

    print(f"  Validation model count: {config_validation.validation_model_count}")
    print(f"  Early result processing: {config_validation.enable_early_result_processing}")
    print()

    # Example 4: Process requests with different configurations
    print("Example 4: Processing Requests")
    print("-" * 80)

    requests = [
        {
            "name": "Simple Query",
            "prompt": "What is the capital of France?",
            "task_type": TaskType.SIMPLE_QUERY,
            "orchestrator": orchestrator_fast
        },
        {
            "name": "Complex Reasoning",
            "prompt": "Analyze the trends in GPU pricing over the past year",
            "task_type": TaskType.COMPLEX_REASONING,
            "orchestrator": orchestrator_high
        },
        {
            "name": "Data Validation",
            "prompt": "Validate this GPU price data for accuracy",
            "task_type": TaskType.DATA_VALIDATION,
            "orchestrator": orchestrator_validation
        }
    ]

    for req in requests:
        print(f"\n  Processing: {req['name']}")
        print(f"    Task type: {req['task_type'].value}")
        print(f"    Prompt: {req['prompt'][:50]}...")

        result = await req["orchestrator"].process_request(
            prompt=req["prompt"],
            quality_threshold=0.8,
            model_call_func=mock_model_call
        )

        print(f"    Models used: {len(result.contributing_models)}")
        print(f"    Confidence: {result.confidence_scores}")

    # Example 5: Performance Comparison
    print("\n" + "=" * 80)
    print("Example 5: Performance Comparison")
    print("=" * 80)

    orchestrators = [
        ("High Quality", orchestrator_high),
        ("Fast & Cheap", orchestrator_fast),
        ("Validation-Focused", orchestrator_validation)
    ]

    for name, orch in orchestrators:
        print(f"\n{name} Configuration:")
        report = orch.generate_performance_report(output_format='dict')
        print(f"  Total requests: {report.get('total_requests', 0)}")
        print(f"  Success rate: {report.get('success_rate', 0):.2f}%")
        print(f"  Avg response time: {report.get('avg_response_time', 0):.3f}s")
        print(f"  Avg cost: ${report.get('avg_cost', 0):.4f}")

    # Example 6: Dynamic Configuration Update
    print("\n" + "=" * 80)
    print("Example 6: Dynamic Configuration")
    print("=" * 80)

    config = OrchestratorConfig()
    orchestrator = AIOrchestrator(config)

    print("\nInitial configuration:")
    print(f"  Quality threshold: {config.default_quality_threshold}")
    print(f"  Model count (simple): {config.simple_query_model_count}")

    # Update configuration dynamically
    config.default_quality_threshold = 0.95
    config.simple_query_model_count = 2

    print("\nUpdated configuration:")
    print(f"  Quality threshold: {config.default_quality_threshold}")
    print(f"  Model count (simple): {config.simple_query_model_count}")

    print("\n" + "=" * 80)
    print("Custom Configuration Example Completed!")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
