# AI Orchestrator API Documentation

## Table of Contents

1. [Overview](#overview)
2. [Core Components](#core-components)
3. [API Reference](#api-reference)
4. [Usage Examples](#usage-examples)
5. [Migration Guide](#migration-guide)
6. [Best Practices](#best-practices)
7. [Troubleshooting](#troubleshooting)

---

## Overview

The AI Orchestrator is an intelligent multi-AI collaboration system that optimizes AI model selection, reduces costs, and maintains high data quality through continuous learning. It orchestrates multiple AI models working together to provide accurate, cost-effective, and validated results.

### Key Features

- **Intelligent Model Selection**: Adaptive routing based on historical performance
- **Parallel Execution**: Concurrent AI model calls for faster results
- **Confidence-Based Merging**: Smart result combination using confidence scores
- **Continuous Learning**: Feedback loop improves performance over time
- **Data Validation**: Built-in validation for GPU prices, token prices, and grid load
- **Performance Tracking**: Comprehensive metrics and anomaly detection
- **Gradual Migration**: Seamless transition from legacy systems

---

## Core Components

### 1. AIOrchestrator
Main coordinator that orchestrates the entire workflow.

**Workflow:**
```
Task Classification → Model Selection → Parallel Execution → Result Merging → Feedback
```

### 2. AdaptiveRouter
Intelligently selects AI models based on:
- Historical performance data
- Task type requirements
- Cost constraints
- Quality thresholds

### 3. ParallelExecutor
Executes AI model calls concurrently using asyncio.
- Per-model timeout handling
- Early result processing
- Exception handling

### 4. ConfidenceWeightedMerger
Merges results from multiple models using confidence-based weighting.
- Weighted voting for list data
- Weighted average for scalar data
- Metadata preservation

### 5. FeedbackLoop
Captures validation results and user corrections for continuous learning.
- Validation result capture
- User correction recording
- Performance tracking

### 6. DataValidator
Validates data quality for various data types.
- GPU price validation
- Token price validation
- Grid load validation

### 7. PerformanceTracker
Monitors and reports on system performance.
- Request tracking
- Model metrics
- Anomaly detection
- Performance reports

### 8. MigrationAdapter
Provides backward compatibility and gradual migration support.
- Legacy API compatibility
- Feature flags
- Configuration-driven behavior

---

## API Reference

### AIOrchestrator

#### Constructor

```python
from ai_orchestrator import AIOrchestrator, OrchestratorConfig

# Using default configuration
orchestrator = AIOrchestrator()

# Using custom configuration
config = OrchestratorConfig(
    default_quality_threshold=0.9,
    default_cost_limit=0.5,
    simple_query_model_count=1,
    complex_reasoning_model_count=2
)
orchestrator = AIOrchestrator(config)
```

**Parameters:**
- `config` (OrchestratorConfig, optional): Configuration instance. Defaults to `OrchestratorConfig()`.

#### Methods

##### register_model(model)

Register an AI model with the orchestrator.

**Parameters:**
- `model` (AIModel): AIModel instance containing model configuration

**Example:**
```python
from ai_orchestrator import AIModel

model = AIModel(
    name="qwen-max",
    provider="Alibaba",
    cost_per_1m_tokens=0.4,
    avg_response_time=2.0
)
orchestrator.register_model(model)
```

##### async process_request(prompt, context=None, quality_threshold=None, cost_limit=None, model_call_func=None)

Process a request through the complete orchestration pipeline.

**Parameters:**
- `prompt` (str): The prompt/query to process
- `context` (Dict[str, Any], optional): Additional context for the request
- `quality_threshold` (float, optional): Minimum quality requirement (overrides config)
- `cost_limit` (float, optional): Maximum cost limit (overrides config)
- `model_call_func` (callable, optional): Function to call AI models (model, request) → Response

**Returns:**
- `MergedResult`: Merged result from AI models

**Example:**
```python
import asyncio

async def call_model(model, request):
    # Your AI model calling logic here
    # This should return a Response object
    from ai_orchestrator import Response
    from datetime import datetime

    return Response(
        model_name=model.name,
        content="AI model response",
        response_time=1.5,
        token_count=100,
        cost=0.04,
        timestamp=datetime.now()
    )

async def main():
    result = await orchestrator.process_request(
        prompt="What is the price of H100 GPUs?",
        quality_threshold=0.8,
        cost_limit=0.1,
        model_call_func=call_model
    )

    print(f"Result: {result.data}")
    print(f"Models: {result.contributing_models}")
    print(f"Confidence: {result.confidence_scores}")

asyncio.run(main())
```

##### validate_data(data, data_type, request_id=None, task_type=None)

Validate data using the integrated data validator.

**Parameters:**
- `data` (List[Dict]): Data to validate
- `data_type` (str): Type of data ('gpu', 'token', 'grid_load')
- `request_id` (str, optional): Request ID for tracking
- `task_type` (TaskType, optional): Task type for validation

**Returns:**
- `ValidationResult`: Validation result with details

**Example:**
```python
gpu_data = [
    {"provider": "AWS", "gpu": "H100", "price": 5.0, "region": "us-east-1"}
]

result = orchestrator.validate_data(gpu_data, 'gpu')
print(f"Valid: {result.is_valid}")
print(f"Errors: {result.errors}")
print(f"Warnings: {result.warnings}")
```

##### generate_performance_report(model_name=None, task_type=None, hours=24, output_format='text')

Generate a comprehensive performance report.

**Parameters:**
- `model_name` (str, optional): Filter by model name
- `task_type` (TaskType, optional): Filter by task type
- `hours` (int): Time range in hours
- `output_format` (str): Output format ('text', 'json', 'dict')

**Returns:**
- `str` or `Dict`: Performance report in specified format

**Example:**
```python
# Text report
report = orchestrator.generate_performance_report(output_format='text')
print(report)

# JSON report
report = orchestrator.generate_performance_report(output_format='json')
print(report)

# Filter by model
report = orchestrator.generate_performance_report(
    model_name='qwen-max',
    hours=48
)
```

##### export_metrics(file_path)

Export all performance metrics to a file.

**Parameters:**
- `file_path` (str): Path to export file

**Returns:**
- `bool`: True if successful, False otherwise

**Example:**
```python
success = orchestrator.export_metrics('./metrics.json')
if success:
    print("Metrics exported successfully")
```

##### get_confidence_scores(task_type=None)

Get current confidence scores.

**Parameters:**
- `task_type` (TaskType, optional): Filter by task type

**Returns:**
- `Dict[str, float]`: Dictionary of model names to confidence scores

**Example:**
```python
scores = orchestrator.get_confidence_scores()
print(scores)

# Filter by task type
scores = orchestrator.get_confidence_scores(TaskType.DATA_VALIDATION)
print(scores)
```

##### record_feedback(request_id, model_name, task_type, was_correct, response_time=0.0, cost=0.0)

Record feedback for a model's performance.

**Parameters:**
- `request_id` (str): ID of the request
- `model_name` (str): Name of the model
- `task_type` (TaskType): Type of task
- `was_correct` (bool): Whether the model's response was correct
- `response_time` (float, optional): Time taken (seconds)
- `cost` (float, optional): Cost incurred (USD)

**Example:**
```python
orchestrator.record_feedback(
    request_id='req-123',
    model_name='qwen-max',
    task_type=TaskType.DATA_VALIDATION,
    was_correct=True,
    response_time=1.5,
    cost=0.04
)
```

---

### MigrationAdapter

#### Constructor

```python
from ai_orchestrator import MigrationAdapter

# Using default config path
adapter = MigrationAdapter()

# Using custom config path
adapter = MigrationAdapter(config_path='/path/to/config.json')
```

#### Methods

##### initialize_orchestrator()

Initialize the AI Orchestrator with configured models.

**Returns:**
- `AIOrchestrator` or `None`: Initialized orchestrator or None if failed

**Example:**
```python
orchestrator = adapter.initialize_orchestrator()
if orchestrator:
    print("Orchestrator initialized successfully")
else:
    print("Failed to initialize orchestrator")
```

##### async fetch_data_with_collaboration(prompt, data_type='gpu', quality_threshold=0.8, cost_limit=None, **kwargs)

Fetch data using AI collaboration (backward compatible).

**Parameters:**
- `prompt` (str): Prompt for data fetching
- `data_type` (str): Type of data ('gpu', 'token', 'grid_load')
- `quality_threshold` (float): Minimum quality threshold
- `cost_limit` (float, optional): Maximum cost limit
- `**kwargs`: Additional arguments

**Returns:**
- `Dict[str, Any]`: Dictionary with fetched data and metadata

**Example:**
```python
import asyncio

async def main():
    result = await adapter.fetch_data_with_collaboration(
        prompt="Get H100 GPU prices",
        data_type='gpu',
        quality_threshold=0.8,
        cost_limit=0.1
    )

    if result['success']:
        print(f"Data: {result['data']}")
        print(f"Metadata: {result['metadata']}")
    else:
        print(f"Error: {result['error']}")

asyncio.run(main())
```

##### get_status()

Get current status of the migration adapter.

**Returns:**
- `Dict[str, Any]`: Status dictionary

**Example:**
```python
status = adapter.get_status()
print(json.dumps(status, indent=2))
```

##### toggle_orchestrator(enabled)

Toggle orchestrator usage on/off.

**Parameters:**
- `enabled` (bool): Whether to enable orchestrator

**Example:**
```python
adapter.toggle_orchestrator(False)  # Switch to legacy
adapter.toggle_orchestrator(True)   # Switch to orchestrator
```

##### update_config(updates)

Update configuration dynamically.

**Parameters:**
- `updates` (Dict[str, Any]): Dictionary of configuration updates

**Example:**
```python
adapter.update_config({
    'system': {
        'use_orchestrator': False
    },
    'feature_flags': {
        'enable_validation': False
    }
})
```

---

### DataValidator

#### Constructor

```python
from ai_orchestrator import DataValidator

validator = DataValidator()
```

#### Methods

##### validate_gpu_prices(data)

Validate GPU price data.

**Parameters:**
- `data` (List[Dict]): List of GPU price records

**Returns:**
- `ValidationResult`: Validation result

##### validate_token_prices(data)

Validate token price data.

**Parameters:**
- `data` (List[Dict]): List of token price records

**Returns:**
- `ValidationResult`: Validation result

##### validate_grid_load(data)

Validate grid load data.

**Parameters:**
- `data` (List[Dict]): List of grid load records

**Returns:**
- `ValidationResult`: Validation result

---

### Models

#### AIModel

Represents an AI model configuration.

**Attributes:**
- `name` (str): Model name
- `provider` (str): Provider name
- `cost_per_1m_tokens` (float): Cost per million tokens
- `avg_response_time` (float): Average response time

**Example:**
```python
model = AIModel(
    name="qwen-max",
    provider="Alibaba",
    cost_per_1m_tokens=0.4,
    avg_response_time=2.0
)
```

#### Request

Represents an incoming request.

**Attributes:**
- `id` (str): Request ID
- `prompt` (str): Prompt text
- `context` (Dict): Additional context
- `timestamp` (datetime): Request timestamp
- `quality_threshold` (float): Quality threshold
- `cost_limit` (float, optional): Cost limit
- `task_type` (TaskType, optional): Task type

#### Response

Represents a response from an AI model.

**Attributes:**
- `model_name` (str): Name of the model
- `content` (str): Response content
- `response_time` (float): Response time
- `token_count` (int): Number of tokens
- `cost` (float): Cost incurred
- `timestamp` (datetime): Response timestamp
- `success` (bool): Success status
- `error` (str, optional): Error message

#### MergedResult

Represents a merged result from multiple AI models.

**Attributes:**
- `data` (Any): Merged data
- `contributing_models` (List[str]): List of model names
- `confidence_scores` (Dict[str, float]): Confidence scores
- `metadata` (Dict): Additional metadata
- `flagged_for_review` (bool): Whether flagged for review

#### ValidationResult

Represents a validation result.

**Attributes:**
- `is_valid` (bool): Whether data is valid
- `validated_data` (Any): Validated data
- `errors` (List[str]): List of errors
- `warnings` (List[str]): List of warnings
- `task_type` (TaskType, optional): Task type

---

## Usage Examples

### Example 1: Basic Usage with Default Settings

```python
import asyncio
from ai_orchestrator import AIOrchestrator, AIModel, Response
from datetime import datetime

# Initialize orchestrator
orchestrator = AIOrchestrator()

# Register models
model1 = AIModel(
    name="qwen-max",
    provider="Alibaba",
    cost_per_1m_tokens=0.4,
    avg_response_time=2.0
)

model2 = AIModel(
    name="doubao-pro",
    provider="ByteDance",
    cost_per_1m_tokens=0.2,
    avg_response_time=1.5
)

orchestrator.register_model(model1)
orchestrator.register_model(model2)

# Define model calling function
async def call_model(model, request):
    # Simulate AI model call
    await asyncio.sleep(0.1)
    return Response(
        model_name=model.name,
        content=f"Response from {model.name}",
        response_time=model.avg_response_time,
        token_count=100,
        cost=model.cost_per_1m_tokens * 0.1,
        timestamp=datetime.now()
    )

# Process a request
async def main():
    result = await orchestrator.process_request(
        prompt="What is the price of H100 GPUs?",
        model_call_func=call_model
    )

    print(f"Result: {result.data}")
    print(f"Models used: {result.contributing_models}")
    print(f"Confidence scores: {result.confidence_scores}")

asyncio.run(main())
```

### Example 2: Custom Configuration

```python
from ai_orchestrator import AIOrchestrator, OrchestratorConfig, TaskType

# Create custom configuration
config = OrchestratorConfig(
    default_quality_threshold=0.9,
    default_cost_limit=0.5,
    simple_query_model_count=1,
    complex_reasoning_model_count=3,
    validation_model_count=3,
    model_timeout_seconds=60.0,
    enable_early_result_processing=True
)

orchestrator = AIOrchestrator(config)

# Process with custom thresholds
async def main():
    result = await orchestrator.process_request(
        prompt="Analyze GPU price trends",
        quality_threshold=0.9,
        cost_limit=0.5,
        model_call_func=call_model
    )

    print(f"High quality result: {result.data}")

asyncio.run(main())
```

### Example 3: Adding a New AI Model

```python
from ai_orchestrator import AIModel, AIOrchestrator

# Create new model
new_model = AIModel(
    name="deepseek-v3",
    provider="DeepSeek",
    cost_per_1m_tokens=0.15,
    avg_response_time=1.8
)

# Register with orchestrator
orchestrator = AIOrchestrator()
orchestrator.register_model(new_model)

# Verify registration
print(f"Registered models: {list(orchestrator.models.keys())}")

# Check confidence scores
scores = orchestrator.get_confidence_scores()
print(f"Confidence scores: {scores}")
```

### Example 4: Using Migration Adapter

```python
import asyncio
from ai_orchestrator import MigrationAdapter

# Initialize adapter
adapter = MigrationAdapter()

# Initialize orchestrator
orchestrator = adapter.initialize_orchestrator()

# Check status
status = adapter.get_status()
print(f"Status: {status}")

# Fetch data (backward compatible)
async def main():
    result = await adapter.fetch_data_with_collaboration(
        prompt="Get latest GPU prices",
        data_type='gpu',
        quality_threshold=0.8
    )

    print(f"Success: {result['success']}")
    print(f"Data: {result['data']}")

asyncio.run(main())
```

### Example 5: Data Validation

```python
from ai_orchestrator import DataValidator

validator = DataValidator()

# Validate GPU prices
gpu_data = [
    {"provider": "AWS", "gpu": "H100", "price": 5.0, "region": "us-east-1"},
    {"provider": "Azure", "gpu": "V100", "price": -1.0, "region": "eastus"}  # Invalid
]

result = validator.validate_gpu_prices(gpu_data)
print(f"Valid: {result.is_valid}")
print(f"Errors: {result.errors}")
print(f"Validated data: {result.validated_data}")
```

### Example 6: Performance Tracking

```python
from ai_orchestrator import AIOrchestrator

orchestrator = AIOrchestrator()

# ... process requests ...

# Generate performance report
report = orchestrator.generate_performance_report(
    output_format='text'
)
print(report)

# Export metrics
orchestrator.export_metrics('./performance_metrics.json')

# Get model-specific performance
model_perf = orchestrator.get_performance_report(
    model_name='qwen-max'
)
print(f"Model performance: {model_perf}")
```

---

## Migration Guide

### Why Migrate?

The AI Orchestrator offers several advantages over the legacy system:

| Feature | Legacy System | AI Orchestrator |
|---------|---------------|-----------------|
| Model Selection | Manual | Intelligent (adaptive) |
| Execution | Sequential | Parallel (concurrent) |
| Result Merging | First response | Confidence-weighted |
| Learning | None | Continuous (feedback loop) |
| Validation | Manual | Automatic |
| Performance Tracking | Basic | Comprehensive |
| Cost Control | Manual | Automatic |
| Scalability | Limited | High |

### Migration Strategies

#### Strategy 1: Gradual Migration (Recommended)

**Phase 1: Setup**
1. Install the AI Orchestrator
2. Create configuration file
3. Test with small requests

```python
from ai_orchestrator import MigrationAdapter

adapter = MigrationAdapter()
orchestrator = adapter.initialize_orchestrator()
```

**Phase 2: Parallel Run**
1. Keep legacy system running
2. Send same requests to both systems
3. Compare results
4. Monitor performance

**Phase 3: Gradual Feature Enable**
1. Start with `enable_model_selection: true`
2. Add `enable_parallel_execution: true`
3. Enable `enable_result_merging: true`
4. Enable `enable_validation: true`
5. Enable `enable_performance_tracking: true`

**Phase 4: Full Migration**
1. Disable legacy system
2. Update all code to use orchestrator
3. Monitor and adjust thresholds

#### Strategy 2: Direct Migration

For new projects or complete system overhauls:

```python
# 1. Initialize orchestrator
orchestrator = AIOrchestrator()

# 2. Register all models
for model_config in model_configs:
    model = AIModel(**model_config)
    orchestrator.register_model(model)

# 3. Replace all fetch calls
# Old:
# result = fetch_data_with_collaboration(prompt, data_type)

# New:
result = await orchestrator.process_request(
    prompt=prompt,
    quality_threshold=0.8,
    cost_limit=1.0,
    model_call_func=your_model_call_func
)
```

### API Compatibility

#### Old API (Legacy)

```python
result = fetch_data_with_collaboration(
    prompt="Get GPU prices",
    data_type="gpu",
    quality_threshold=0.8,
    cost_limit=0.1
)
```

#### New API (AI Orchestrator)

```python
# Option 1: Direct (recommended)
result = await orchestrator.process_request(
    prompt="Get GPU prices",
    quality_threshold=0.8,
    cost_limit=0.1,
    model_call_func=call_model_func
)

# Option 2: Via Migration Adapter (backward compatible)
result = await adapter.fetch_data_with_collaboration(
    prompt="Get GPU prices",
    data_type="gpu",
    quality_threshold=0.8,
    cost_limit=0.1
)
```

### Configuration Changes

#### Legacy System
No configuration file - hardcoded settings.

#### AI Orchestrator
Uses `config.json` for all settings:

```json
{
  "system": {
    "use_orchestrator": true
  },
  "orchestrator": {
    "default_quality_threshold": 0.8,
    "default_cost_limit": 1.0
  },
  "models": [
    {
      "name": "qwen-max",
      "provider": "Alibaba",
      "cost_per_1m_tokens": 0.4,
      "avg_response_time": 2.0,
      "enabled": true
    }
  ]
}
```

### Common Migration Issues

#### Issue 1: Model Call Function Required

**Problem:**
```
RuntimeError: model_call_func is required
```

**Solution:**
Provide a model calling function:

```python
async def call_model(model, request):
    # Your implementation
    return Response(...)

result = await orchestrator.process_request(
    prompt="...",
    model_call_func=call_model
)
```

#### Issue 2: No Models Registered

**Problem:**
```
ValueError: No AI models available for routing
```

**Solution:**
Register at least one model:

```python
model = AIModel(name="...", provider="...", ...)
orchestrator.register_model(model)
```

#### Issue 3: Low Confidence Scores

**Problem:**
Results have low confidence scores initially.

**Solution:**
This is normal for new systems. As feedback is collected, confidence scores improve. You can:
1. Lower quality threshold initially
2. Use more models per request
3. Provide feedback via `record_feedback()`

### Rollback Procedure

If issues occur during migration:

```python
# Option 1: Toggle orchestrator off
adapter.toggle_orchestrator(False)

# Option 2: Update configuration
adapter.update_config({
    'system': {
        'use_orchestrator': False
    }
})

# Option 3: Update config.json
{
  "system": {
    "use_orchestrator": false
  }
}
```

---

## Best Practices

### 1. Model Selection

**Do:**
- Register models with accurate cost and response time
- Use 2-3 models for complex tasks
- Use 1 model for simple queries
- Monitor confidence scores

**Don't:**
- Register too many models (increases cost)
- Use models with incorrect cost data
- Ignore confidence score trends

### 2. Quality and Cost Control

**Do:**
- Set appropriate quality thresholds
- Monitor cost per request
- Use cost limits for budget control
- Track cost trends over time

**Don't:**
- Set quality threshold too low
- Ignore cost accumulation
- Use unlimited cost mode in production

### 3. Performance Optimization

**Do:**
- Enable early result processing
- Set appropriate timeouts
- Monitor performance metrics
- Use parallel execution for speed

**Don't:**
- Set timeouts too low (causes failures)
- Ignore performance anomalies
- Run without performance tracking

### 4. Data Validation

**Do:**
- Validate all data before use
- Review validation errors and warnings
- Fix data issues at the source
- Use validation feedback for learning

**Don't:**
- Skip validation steps
- Ignore validation warnings
- Accept invalid data

### 5. Feedback and Learning

**Do:**
- Provide feedback for all results
- Record corrections when found
- Monitor confidence score trends
- Use feedback to improve accuracy

**Don't:**
- Skip feedback collection
- Ignore negative feedback
- Forget to trigger confidence updates

### 6. Error Handling

**Do:**
- Handle exceptions gracefully
- Log errors for debugging
- Provide fallback mechanisms
- Monitor error rates

**Don't:**
- Ignore exceptions
- Fail silently
- Leave errors unlogged

### 7. Configuration Management

**Do:**
- Version control config files
- Use environment variables for secrets
- Test configuration changes
- Document custom configurations

**Don't:**
- Hardcode credentials
- Skip configuration validation
- Make untested changes in production

---

## Troubleshooting

### Common Errors

#### Error: "No models available"

**Cause:** No models registered with orchestrator.

**Solution:**
```python
model = AIModel(name="...", provider="...", ...)
orchestrator.register_model(model)
```

#### Error: "model_call_func is required"

**Cause:** No function provided to call AI models.

**Solution:**
```python
async def call_model(model, request):
    # Your model calling logic
    return Response(...)

result = await orchestrator.process_request(
    prompt="...",
    model_call_func=call_model
)
```

#### Error: "All model calls failed"

**Cause:** All model calls timed out or failed.

**Solution:**
1. Check model API keys and credentials
2. Increase timeout values
3. Verify model endpoints
4. Check network connectivity

#### Error: "Low confidence scores"

**Cause:** Insufficient training data or poor model performance.

**Solution:**
1. Provide more feedback
2. Lower quality threshold temporarily
3. Add more models
4. Check model configurations

### Performance Issues

#### Issue: Slow Response Times

**Possible Causes:**
- Too many models selected
- Models have high latency
- Network issues

**Solutions:**
- Reduce model count
- Check model response times
- Enable early result processing
- Optimize model calling function

#### Issue: High Costs

**Possible Causes:**
- Too many models per request
- Models have high per-token cost
- No cost limits

**Solutions:**
- Reduce model count
- Set cost limits
- Use cheaper models
- Optimize token usage

#### Issue: Low Accuracy

**Possible Causes:**
- Poor model selection
- Inadequate validation
- Insufficient feedback

**Solutions:**
- Review confidence scores
- Add validation steps
- Provide more feedback
- Adjust quality thresholds

### Debugging Tips

1. **Enable Detailed Logging:**
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

2. **Check Status:**
```python
status = adapter.get_status()
print(json.dumps(status, indent=2))
```

3. **Generate Performance Report:**
```python
report = orchestrator.generate_performance_report(output_format='text')
print(report)
```

4. **Export Metrics:**
```python
orchestrator.export_metrics('./debug_metrics.json')
```

5. **Monitor Confidence Scores:**
```python
scores = orchestrator.get_confidence_scores()
print(scores)
```

---

## Support

For issues, questions, or contributions:

- Check this documentation first
- Review configuration guide (CONFIGURATION.md)
- Check existing issues in the repository
- Create a new issue with detailed information

---

## Changelog

### Version 1.0.0
- Initial release
- Core orchestration functionality
- Adaptive model selection
- Parallel execution
- Result merging
- Data validation
- Performance tracking
- Migration adapter
- Configuration system

---

## License

Copyright (c) 2025 ComputePulse Team. All rights reserved.
