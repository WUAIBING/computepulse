# Migration Guide: Legacy System to AI Orchestrator

## Table of Contents

1. [Introduction](#introduction)
2. [Why Migrate?](#why-migrate)
3. [Migration Strategies](#migration-strategies)
4. [Step-by-Step Migration](#step-by-step-migration)
5. [API Comparison](#api-comparison)
6. [Configuration Changes](#configuration-changes)
7. [Common Issues and Solutions](#common-issues-and-solutions)
8. [Rollback Procedures](#rollback-procedures)
9. [Performance Considerations](#performance-considerations)
10. [Best Practices](#best-practices)

---

## Introduction

This guide helps you migrate from legacy ComputePulse systems to the new AI Orchestrator. The AI Orchestrator provides intelligent model selection, parallel execution, result merging, and continuous learning capabilities.

### What You'll Gain

- **Intelligent Model Selection**: Automatic selection of best models based on historical performance
- **Parallel Execution**: Faster results through concurrent model calls
- **Confidence-Based Merging**: Smart combination of multiple model results
- **Continuous Learning**: System improves over time through feedback
- **Comprehensive Monitoring**: Performance tracking and anomaly detection
- **Cost Optimization**: Automatic cost control and budget management

---

## Why Migrate?

### Comparison Table

| Feature | Legacy System | AI Orchestrator |
|---------|---------------|-----------------|
| **Model Selection** | Manual/Static | Intelligent/Adaptive |
| **Execution Model** | Sequential | Parallel (Concurrent) |
| **Result Handling** | First response | Confidence-weighted merging |
| **Learning** | None | Continuous feedback loop |
| **Validation** | Manual | Automatic with rules |
| **Performance Tracking** | Basic | Comprehensive metrics |
| **Cost Control** | Manual | Automatic with limits |
| **Scalability** | Limited | High (horizontal scaling) |
| **Error Handling** | Basic | Advanced with fallbacks |
| **Configuration** | Hardcoded | JSON-based, dynamic |
| **Monitoring** | Limited | Full observability |

### Benefits

1. **Better Results**: Multiple models collaborate for higher accuracy
2. **Lower Costs**: Intelligent routing reduces unnecessary API calls
3. **Faster Response**: Parallel execution speeds up processing
4. **Higher Quality**: Validation and confidence scoring ensure quality
5. **Continuous Improvement**: Learning system gets better over time
6. **Easier Maintenance**: Configuration-driven, no code changes needed

---

## Migration Strategies

### Strategy 1: Gradual Migration (Recommended)

**Best for:** Production systems with high availability requirements

**Timeline:** 2-4 weeks

**Phases:**
1. **Setup & Testing** (Week 1)
2. **Parallel Run** (Week 2)
3. **Feature Activation** (Week 3)
4. **Full Migration** (Week 4)

**Pros:**
- Low risk
- Easy rollback
- Monitor performance at each step
- Can stop at any phase

**Cons:**
- Takes longer
- Requires maintaining two systems temporarily
- More complex testing

---

### Strategy 2: Direct Migration

**Best for:** New projects or complete system overhauls

**Timeline:** 1-2 weeks

**Steps:**
1. Set up AI Orchestrator
2. Replace all API calls
3. Test thoroughly
4. Deploy

**Pros:**
- Faster migration
- Clean slate
- No dual maintenance

**Cons:**
- Higher risk
- Difficult rollback
- Need comprehensive testing

---

### Strategy 3: Feature-by-Feature Migration

**Best for:** Systems with well-defined feature boundaries

**Steps:**
1. Migrate one feature at a time
2. Validate each feature before moving to next
3. Gradually expand coverage

**Pros:**
- Very low risk
- Easy to isolate issues
- Can learn from each feature

**Cons:**
- Longest migration time
- Complex coordination
- Hybrid system complexity

---

## Step-by-Step Migration

### Phase 1: Setup & Preparation

#### Step 1: Install AI Orchestrator

```bash
# Ensure you have the latest version
pip install -r requirements.txt
```

#### Step 2: Review Current System

Document your current:
- AI models in use
- API endpoints
- Configuration settings
- Performance metrics
- Cost structure

#### Step 3: Create Configuration File

Create `config.json`:

```json
{
  "version": "1.0.0",
  "system": {
    "use_orchestrator": true,
    "migration_mode": "gradual",
    "rollback_enabled": true
  },
  "feature_flags": {
    "enable_model_selection": true,
    "enable_parallel_execution": true,
    "enable_result_merging": true,
    "enable_validation": true,
    "enable_performance_tracking": true
  },
  "orchestrator": {
    "default_quality_threshold": 0.8,
    "default_cost_limit": 1.0,
    "simple_query_model_count": 1,
    "complex_reasoning_model_count": 2,
    "validation_model_count": 3
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

#### Step 4: Test Setup

```python
from ai_orchestrator import MigrationAdapter

adapter = MigrationAdapter()
orchestrator = adapter.initialize_orchestrator()

if orchestrator:
    print("✓ Setup successful")
else:
    print("✗ Setup failed")
```

---

### Phase 2: Parallel Run

#### Step 5: Implement MigrationAdapter

Replace old imports:

```python
# Old:
# from your_legacy_module import fetch_data_with_collaboration

# New:
from ai_orchestrator import MigrationAdapter

adapter = MigrationAdapter()
```

#### Step 6: Keep Legacy System Running

Maintain both systems:

```python
# Old system (still running)
legacy_result = await legacy_fetch_data(prompt, data_type)

# New system (testing)
orchestrator = adapter.initialize_orchestrator()
if orchestrator:
    new_result = await orchestrator.process_request(
        prompt=prompt,
        quality_threshold=0.8,
        model_call_func=your_model_call_func
    )
```

#### Step 7: Compare Results

Log both results and compare:
- Response quality
- Response time
- Cost
- Accuracy

---

### Phase 3: Feature Activation

#### Step 8: Enable Features Gradually

**Week 1: Model Selection**

```python
adapter.update_config({
    'feature_flags': {
        'enable_model_selection': True,
        'enable_parallel_execution': False,
        'enable_result_merging': False
    }
})
```

**Week 2: Add Parallel Execution**

```python
adapter.update_config({
    'feature_flags': {
        'enable_model_selection': True,
        'enable_parallel_execution': True,
        'enable_result_merging': False
    }
})
```

**Week 3: Add Result Merging**

```python
adapter.update_config({
    'feature_flags': {
        'enable_model_selection': True,
        'enable_parallel_execution': True,
        'enable_result_merging': True
    }
})
```

**Week 4: Add Validation & Tracking**

```python
adapter.update_config({
    'feature_flags': {
        'enable_model_selection': True,
        'enable_parallel_execution': True,
        'enable_result_merging': True,
        'enable_validation': True,
        'enable_performance_tracking': True
    }
})
```

#### Step 9: Monitor Performance

Generate regular reports:

```python
report = orchestrator.generate_performance_report(
    output_format='text'
)
print(report)

# Export metrics
orchestrator.export_metrics('./metrics.json')
```

---

### Phase 4: Full Migration

#### Step 10: Disable Legacy System

```python
adapter.update_config({
    'legacy_system': {
        'enabled': false
    },
    'system': {
        'use_orchestrator': true,
        'migration_mode': 'full'
    }
})
```

#### Step 11: Update All Code

Replace all legacy calls:

```python
# Old:
result = await legacy_fetch_data(prompt, data_type)

# New:
result = await orchestrator.process_request(
    prompt=prompt,
    quality_threshold=0.8,
    model_call_func=your_model_call_func
)
```

#### Step 12: Final Validation

Run comprehensive tests:
- Unit tests
- Integration tests
- Performance tests
- Load tests

---

## API Comparison

### Old API (Legacy)

```python
# Simple call
result = await fetch_data_with_collaboration(
    prompt="Get GPU prices",
    data_type="gpu",
    quality_threshold=0.8,
    cost_limit=0.1
)

# Check result
if result['success']:
    data = result['data']
    metadata = result['metadata']
else:
    error = result['error']
```

### New API (AI Orchestrator)

```python
# Initialize once
orchestrator = AIOrchestrator()
orchestrator.register_model(model1)
orchestrator.register_model(model2)

# Process request
result = await orchestrator.process_request(
    prompt="Get GPU prices",
    quality_threshold=0.8,
    cost_limit=0.1,
    model_call_func=call_model_function
)

# Check result
if result.data:
    data = result.data
    models = result.contributing_models
    confidence = result.confidence_scores
else:
    # Handle error
    pass
```

### Backward Compatible API (MigrationAdapter)

```python
# Same as old API
adapter = MigrationAdapter()

result = await adapter.fetch_data_with_collaboration(
    prompt="Get GPU prices",
    data_type="gpu",
    quality_threshold=0.8,
    cost_limit=0.1
)

# Result format is similar
if result['success']:
    data = result['data']
    metadata = result['metadata']
```

---

## Configuration Changes

### Legacy System

No configuration file. Settings are hardcoded:

```python
# In your code
QUALITY_THRESHOLD = 0.8
COST_LIMIT = 0.1
MODEL_TIMEOUT = 30
```

### AI Orchestrator

Uses `config.json`:

```json
{
  "orchestrator": {
    "default_quality_threshold": 0.8,
    "default_cost_limit": 0.1,
    "model_timeout_seconds": 30.0
  },
  "models": [
    {
      "name": "qwen-max",
      "provider": "Alibaba",
      "cost_per_1m_tokens": 0.4,
      "avg_response_time": 2.0
    }
  ]
}
```

### Dynamic Updates

```python
# Update configuration at runtime
adapter.update_config({
    'orchestrator': {
        'default_quality_threshold': 0.9,
        'default_cost_limit': 0.5
    }
})
```

---

## Common Issues and Solutions

### Issue 1: "No models available"

**Symptoms:**
```
ValueError: No AI models available for routing
```

**Cause:** No models registered with orchestrator

**Solution:**
```python
model = AIModel(
    name="qwen-max",
    provider="Alibaba",
    cost_per_1m_tokens=0.4,
    avg_response_time=2.0
)
orchestrator.register_model(model)
```

---

### Issue 2: "model_call_func is required"

**Symptoms:**
```
RuntimeError: model_call_func is required
```

**Cause:** No function provided to call AI models

**Solution:**
```python
async def call_model(model, request):
    # Your AI model API call here
    return Response(...)

result = await orchestrator.process_request(
    prompt="...",
    model_call_func=call_model
)
```

---

### Issue 3: High Costs

**Symptoms:**
- Costs higher than expected
- Budget overruns

**Solutions:**
1. Set cost limits:
```python
result = await orchestrator.process_request(
    prompt="...",
    cost_limit=0.5  # Set limit
)
```

2. Use fewer models:
```python
config = OrchestratorConfig(
    simple_query_model_count=1,  # Reduce models
    complex_reasoning_model_count=2
)
```

3. Use cheaper models:
```json
{
  "models": [
    {
      "name": "deepseek-v3",
      "cost_per_1m_tokens": 0.15  // Cheaper
    }
  ]
}
```

---

### Issue 4: Low Accuracy

**Symptoms:**
- Results not accurate
- Low confidence scores

**Solutions:**
1. Provide feedback:
```python
orchestrator.record_feedback(
    request_id="req-123",
    model_name="qwen-max",
    task_type=TaskType.DATA_VALIDATION,
    was_correct=False  # Mark as incorrect
)
```

2. Adjust quality threshold:
```python
result = await orchestrator.process_request(
    prompt="...",
    quality_threshold=0.9  // Higher threshold
)
```

3. Use more models:
```python
config = OrchestratorConfig(
    validation_model_count=3  // More models
)
```

---

### Issue 5: Slow Performance

**Symptoms:**
- Long response times
- Timeouts

**Solutions:**
1. Reduce model count:
```python
config = OrchestratorConfig(
    simple_query_model_count=1
)
```

2. Enable early result processing:
```python
config = OrchestratorConfig(
    enable_early_result_processing=True
)
```

3. Increase timeout:
```python
config = OrchestratorConfig(
    model_timeout_seconds=60.0
)
```

---

### Issue 6: Import Errors

**Symptoms:**
```
ModuleNotFoundError: No module named 'ai_orchestrator'
```

**Solutions:**
1. Check Python path:
```bash
cd /path/to/project
python your_script.py
```

2. Install package:
```bash
pip install -e .
```

3. Check virtual environment:
```bash
which python
pip list | grep ai_orchestrator
```

---

## Rollback Procedures

### Option 1: Toggle Orchestrator Off

```python
adapter.toggle_orchestrator(False)
# Now uses legacy system
```

### Option 2: Update Configuration

```python
adapter.update_config({
    'system': {
        'use_orchestrator': false
    }
})
```

### Option 3: Edit config.json

```json
{
  "system": {
    "use_orchestrator": false
  }
}
```

### Option 4: Quick Rollback Script

```python
# rollback.py
from ai_orchestrator import MigrationAdapter

adapter = MigrationAdapter()
adapter.toggle_orchestrator(False)
print("Rolled back to legacy system")
```

---

## Performance Considerations

### Response Time

**Legacy System:**
- Single model: ~2-5 seconds
- No parallelization

**AI Orchestrator:**
- Parallel models: ~1-3 seconds (faster with more models)
- Overhead: ~0.1-0.5 seconds for orchestration

**Optimization Tips:**
- Enable early result processing
- Use appropriate model count
- Set reasonable timeouts

### Cost

**Legacy System:**
- Pay for single model per request
- No cost optimization

**AI Orchestrator:**
- Pay for multiple models (can be more or less)
- Intelligent routing saves costs
- Cost limits prevent overruns

**Cost Optimization:**
- Use cost limits
- Select appropriate models
- Enable quality thresholds

### Accuracy

**Legacy System:**
- Depends on single model
- No validation

**AI Orchestrator:**
- Multiple models collaborate
- Confidence scoring
- Automatic validation

**Accuracy Tips:**
- Provide feedback regularly
- Use validation features
- Monitor confidence scores

---

## Best Practices

### 1. Planning

✓ **Do:**
- Plan migration strategy
- Set clear milestones
- Document current system
- Prepare rollback plan

✗ **Don't:**
- Rush migration
- Skip testing
- Ignore performance metrics

### 2. Testing

✓ **Do:**
- Test in staging environment
- Run parallel systems
- Compare results
- Monitor performance

✗ **Don't:**
- Deploy without testing
- Skip load testing
- Ignore errors

### 3. Configuration

✓ **Do:**
- Version control config files
- Use environment variables for secrets
- Document custom settings
- Test configuration changes

✗ **Don't:**
- Hardcode credentials
- Skip validation
- Make untested changes

### 4. Monitoring

✓ **Do:**
- Generate regular reports
- Track key metrics
- Set up alerts
- Review confidence scores

✗ **Don't:**
- Ignore performance data
- Skip anomaly detection
- Forget to review costs

### 5. Feedback

✓ **Do:**
- Provide feedback for results
- Record corrections
- Monitor learning progress
- Adjust based on feedback

✗ **Don't:**
- Skip feedback collection
- Ignore negative feedback
- Forget to trigger updates

### 6. Maintenance

✓ **Do:**
- Update models regularly
- Review configuration periodically
- Clean old data
- Update documentation

✗ **Don't:**
- Ignore outdated models
- Let configuration drift
- Accumulate unused data

---

## Timeline Template

### Week 1: Setup

- [ ] Install AI Orchestrator
- [ ] Create configuration file
- [ ] Test basic functionality
- [ ] Document current system
- [ ] Set up monitoring

### Week 2: Parallel Run

- [ ] Keep legacy system running
- [ ] Run both systems
- [ ] Compare results
- [ ] Identify issues
- [ ] Adjust configuration

### Week 3: Feature Activation

- [ ] Enable model selection
- [ ] Enable parallel execution
- [ ] Enable result merging
- [ ] Monitor performance
- [ ] Collect feedback

### Week 4: Full Migration

- [ ] Disable legacy system
- [ ] Update all code
- [ ] Run comprehensive tests
- [ ] Validate performance
- [ ] Document changes

---

## Success Criteria

Migration is successful when:

1. ✓ All tests pass
2. ✓ Performance meets or exceeds legacy system
3. ✓ Costs are within budget
4. ✓ Accuracy is improved or maintained
5. ✓ Team is trained on new system
6. ✓ Documentation is complete
7. ✓ Monitoring is in place
8. ✓ Rollback plan is tested

---

## Getting Help

### Documentation
- API Documentation: `ai_orchestrator/API.md`
- Configuration Guide: `CONFIGURATION.md`
- Examples: `ai_orchestrator/examples/`

### Support Channels
1. Check documentation first
2. Review error logs
3. Check configuration
4. Create issue with details

### What to Include in Issues
- Error message
- Configuration file (sanitized)
- Steps to reproduce
- Expected vs actual behavior
- Log files

---

## Conclusion

Migrating to the AI Orchestrator provides significant benefits in terms of accuracy, cost, and performance. By following this guide and the gradual migration strategy, you can minimize risk and ensure a smooth transition.

Remember:
- Take your time
- Test thoroughly
- Monitor closely
- Have a rollback plan
- Don't hesitate to ask for help

Good luck with your migration!

---

## Appendix

### Quick Reference

**Initialize:**
```python
from ai_orchestrator import MigrationAdapter
adapter = MigrationAdapter()
orchestrator = adapter.initialize_orchestrator()
```

**Process Request:**
```python
result = await orchestrator.process_request(
    prompt="...",
    model_call_func=your_func
)
```

**Generate Report:**
```python
report = orchestrator.generate_performance_report()
```

**Rollback:**
```python
adapter.toggle_orchestrator(False)
```

### Useful Commands

```bash
# Run example
python ai_orchestrator/examples/basic_usage.py

# Generate report
python -c "from ai_orchestrator import *; ..."

# Test configuration
python -c "from ai_orchestrator import MigrationAdapter; ..."
```

---

**Version:** 1.0.0
**Last Updated:** 2025-12-08
