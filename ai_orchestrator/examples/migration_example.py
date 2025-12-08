#!/usr/bin/env python3
"""
Migration Example for AI Orchestrator

This example demonstrates how to migrate from a legacy system
to the AI Orchestrator using the MigrationAdapter.
"""

import asyncio
import json
from datetime import datetime

from ai_orchestrator import (
    MigrationAdapter,
    AIOrchestrator,
    AIModel,
    Response,
    TaskType
)


async def mock_legacy_fetch(prompt, data_type):
    """Simulate legacy system data fetching."""
    print(f"  [Legacy System] Fetching {data_type} data...")
    await asyncio.sleep(0.2)

    if data_type == 'gpu':
        return {
            'success': True,
            'data': [
                {"provider": "Legacy-AWS", "gpu": "V100", "price": 3.0}
            ],
            'metadata': {'system': 'legacy', 'timestamp': datetime.now().isoformat()}
        }
    else:
        return {
            'success': True,
            'data': [],
            'metadata': {'system': 'legacy', 'timestamp': datetime.now().isoformat()}
        }


async def mock_model_call(model, request):
    """Mock function for orchestrator."""
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
    print("AI Orchestrator - Migration Example")
    print("=" * 80)
    print()

    # Part 1: Legacy System (Before Migration)
    print("Part 1: Legacy System (Before Migration)")
    print("-" * 80)

    print("\nLegacy approach - Manual model selection:")
    print("  1. Call model API directly")
    print("  2. Manually select which model to use")
    print("  3. No collaboration between models")
    print("  4. No learning or optimization")
    print("  5. Manual error handling")

    # Simulate legacy usage
    print("\nLegacy system in action:")
    legacy_result = await mock_legacy_fetch("Get GPU prices", 'gpu')
    print(f"  Result: {legacy_result['data']}")
    print(f"  System: {legacy_result['metadata']['system']}")
    print()

    # Part 2: Migration Setup
    print("\nPart 2: Setting Up Migration")
    print("-" * 80)

    print("\nStep 1: Initialize MigrationAdapter")
    adapter = MigrationAdapter()
    print("  ✓ MigrationAdapter initialized")
    print(f"  Config path: {adapter.config_path}")

    print("\nStep 2: Check adapter status")
    status = adapter.get_status()
    print(f"  Orchestrator enabled: {status['orchestrator_enabled']}")
    print(f"  Feature flags: {list(status['feature_flags'].keys())[:3]}...")
    print(f"  Legacy enabled: {status['legacy_enabled']}")

    print("\nStep 3: Initialize orchestrator")
    orchestrator = adapter.initialize_orchestrator()
    if orchestrator:
        print("  ✓ Orchestrator initialized successfully")

        # Register some models
        for model_config in [
            {"name": "qwen-max", "provider": "Alibaba", "cost": 0.4, "time": 2.0},
            {"name": "deepseek-v3", "provider": "DeepSeek", "cost": 0.15, "time": 1.8}
        ]:
            model = AIModel(
                name=model_config["name"],
                provider=model_config["provider"],
                cost_per_1m_tokens=model_config["cost"],
                avg_response_time=model_config["time"]
            )
            orchestrator.register_model(model)
        print(f"  ✓ Registered {len(orchestrator.models)} models")
    else:
        print("  ✗ Failed to initialize orchestrator")
        return

    print()

    # Part 3: Backward Compatible API
    print("\nPart 3: Using Backward Compatible API")
    print("-" * 80)

    print("\nThe old API still works with MigrationAdapter:")
    print("  fetch_data_with_collaboration(prompt, data_type, ...)")

    print("\nCalling with adapter:")
    result = await adapter.fetch_data_with_collaboration(
        prompt="Get GPU prices",
        data_type='gpu',
        quality_threshold=0.8,
        cost_limit=0.5,
        timestamp=datetime.now().isoformat()
    )

    print(f"  Success: {result['success']}")
    print(f"  System used: {result['metadata']['system']}")
    if result['success'] and result['data']:
        print(f"  Data: {result['data']}")
    print()

    # Part 4: New API Usage
    print("\nPart 4: Using New AI Orchestrator API")
    print("-" * 80)

    print("\nNew approach with AI Orchestrator:")
    print("  1. Automatic model selection")
    print("  2. Parallel execution")
    print("  3. Result merging with confidence")
    print("  4. Continuous learning")
    print("  5. Performance tracking")

    print("\nCalling orchestrator directly:")
    orchestrator_result = await orchestrator.process_request(
        prompt="Get GPU prices from cloud providers",
        quality_threshold=0.8,
        cost_limit=0.5,
        model_call_func=mock_model_call
    )

    print(f"  ✓ Request completed")
    print(f"  Models used: {orchestrator_result.contributing_models}")
    print(f"  Confidence scores: {orchestrator_result.confidence_scores}")
    print()

    # Part 5: Gradual Migration Strategy
    print("\nPart 5: Gradual Migration Strategy")
    print("-" * 80)

    print("\nStep 1: Enable orchestrator but keep legacy as fallback")
    adapter.toggle_orchestrator(True)
    print("  ✓ Orchestrator enabled")

    print("\nStep 2: Enable features gradually")

    # Enable model selection
    adapter.update_config({
        'feature_flags': {
            'enable_model_selection': True,
            'enable_parallel_execution': False,
            'enable_result_merging': False
        }
    })
    print("  ✓ Enabled model selection only")

    print("\nStep 3: Monitor performance")
    report = orchestrator.generate_performance_report(output_format='dict')
    print(f"  Requests: {report.get('total_requests', 0)}")
    print(f"  Success rate: {report.get('success_rate', 0):.2f}%")

    print("\nStep 4: Enable more features")
    adapter.update_config({
        'feature_flags': {
            'enable_model_selection': True,
            'enable_parallel_execution': True,
            'enable_result_merging': True,
            'enable_validation': True,
            'enable_performance_tracking': True
        }
    })
    print("  ✓ Enabled all major features")

    print()

    # Part 6: Configuration Management
    print("\nPart 6: Configuration Management")
    print("-" * 80)

    print("\nDynamic configuration updates:")

    print("\n  Before update:")
    config = adapter.get_config()
    print(f"    Quality threshold: {config['orchestrator']['default_quality_threshold']}")

    print("\n  Updating configuration...")
    adapter.update_config({
        'orchestrator': {
            'default_quality_threshold': 0.95,
            'default_cost_limit': 0.5
        }
    })

    print("\n  After update:")
    config = adapter.get_config()
    print(f"    Quality threshold: {config['orchestrator']['default_quality_threshold']}")
    print(f"    Cost limit: {config['orchestrator']['default_cost_limit']}")

    print()

    # Part 7: Rollback Capability
    print("\nPart 7: Rollback Capability")
    print("-" * 80)

    print("\nIf issues occur, easy rollback:")

    print("\n  Option 1: Toggle orchestrator off")
    adapter.toggle_orchestrator(False)
    status = adapter.get_status()
    print(f"    Orchestrator enabled: {status['orchestrator_enabled']}")

    print("\n  Option 2: Update configuration")
    adapter.update_config({
        'system': {
            'use_orchestrator': False
        }
    })
    print("    ✓ Configuration updated to use legacy system")

    print("\n  Option 3: Restore orchestrator")
    adapter.toggle_orchestrator(True)
    print("    ✓ Orchestrator restored")

    print()

    # Part 8: Performance Comparison
    print("\nPart 8: Performance Comparison")
    print("-" * 80)

    print("\nLegacy vs Orchestrator:")

    print("\n  Legacy System:")
    print("    - Single model response")
    print("    - No learning")
    print("    - Manual optimization")
    print("    - Basic tracking")

    print("\n  AI Orchestrator:")
    print("    - Multiple models collaborate")
    print("    - Continuous learning")
    print("    - Automatic optimization")
    print("    - Comprehensive metrics")

    report = orchestrator.generate_performance_report(output_format='text')
    print("\n  Performance Report Sample:")
    lines = report.split('\n')
    for line in lines[:15]:
        print(f"    {line}")

    print()

    # Part 9: Best Practices
    print("\nPart 9: Migration Best Practices")
    print("-" * 80)

    print("\n✓ Do's:")
    print("  1. Start with gradual migration")
    print("  2. Keep legacy system as backup initially")
    print("  3. Monitor performance closely")
    print("  4. Test configuration changes in staging")
    print("  5. Document any custom configurations")
    print("  6. Provide feedback to improve models")

    print("\n  Don'ts:")
    print("  1. Don't migrate everything at once")
    print("  2. Don't ignore performance metrics")
    print("  3. Don't skip validation")
    print("  4. Don't forget to update monitoring")
    print("  5. Don't disable rollback capability")

    print()

    # Summary
    print("=" * 80)
    print("Migration Summary")
    print("=" * 80)

    print("\n✓ Migration completed successfully!")
    print("\nKey Achievements:")
    print("  • Backward compatible API maintained")
    print("  • New AI Orchestrator features enabled")
    print("  • Gradual migration path available")
    print("  • Easy rollback capability")
    print("  • Configuration-driven behavior")
    print("  • Performance tracking in place")

    print("\n" + "=" * 80)
    print("Migration Example Completed!")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
