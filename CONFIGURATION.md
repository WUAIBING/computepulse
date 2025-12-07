# AI Orchestrator Configuration Guide

## Overview

The AI Orchestrator uses a JSON configuration file (`config.json`) to control all aspects of system behavior. This guide documents all configuration options.

## Configuration File Location

By default, the configuration file is located at:
- Project root: `./config.json`
- Alternative: Path specified when creating `MigrationAdapter` instance

## Configuration Structure

### 1. System Settings

```json
{
  "system": {
    "use_orchestrator": true,
    "migration_mode": "gradual",
    "rollback_enabled": true
  }
}
```

**Options:**
- `use_orchestrator` (boolean): Enable/disable the new AI Orchestrator
  - `true`: Use AI Orchestrator (default)
  - `false`: Fall back to legacy system

- `migration_mode` (string): Migration strategy
  - `"gradual"`: Gradual migration with feature flags
  - `"full"`: Use only new system
  - `"legacy"`: Use only legacy system

- `rollback_enabled` (boolean): Allow rollback to legacy system

### 2. Feature Flags

```json
{
  "feature_flags": {
    "enable_validation": true,
    "enable_performance_tracking": true,
    "enable_feedback_loop": true,
    "enable_model_selection": true,
    "enable_parallel_execution": true,
    "enable_result_merging": true,
    "enable_caching": true,
    "enable_anomaly_detection": true
  }
}
```

**Individual Features:**
- `enable_validation`: Enable data validation (Task 12)
- `enable_performance_tracking`: Enable performance metrics (Task 13)
- `enable_feedback_loop`: Enable learning from feedback
- `enable_model_selection`: Use adaptive model routing
- `enable_parallel_execution`: Execute models concurrently
- `enable_result_merging`: Merge multiple model results
- `enable_caching`: Cache results to avoid redundant calls
- `enable_anomaly_detection`: Detect performance anomalies

### 3. Orchestrator Settings

```json
{
  "orchestrator": {
    "default_quality_threshold": 0.8,
    "default_cost_limit": 1.0,
    "confidence_decay_factor": 0.95,
    "min_samples_for_confidence": 10,
    "confidence_smoothing_factor": 0.7,
    "simple_query_model_count": 1,
    "complex_reasoning_model_count": 2,
    "validation_model_count": 3,
    "model_timeout_seconds": 30.0,
    "enable_early_result_processing": true
  }
}
```

**Quality & Cost:**
- `default_quality_threshold` (float): Minimum acceptable quality score (0.0-1.0)
- `default_cost_limit` (float): Maximum cost per request in USD

**Learning Engine:**
- `confidence_decay_factor` (float): Decay rate for EWMA (0.0-1.0)
- `min_samples_for_confidence` (int): Minimum samples before trusting confidence scores
- `confidence_smoothing_factor` (float): Smoothing factor for score updates

**Model Selection:**
- `simple_query_model_count` (int): Number of models for simple queries
- `complex_reasoning_model_count` (int): Number of models for complex tasks
- `validation_model_count` (int): Number of models for data validation

**Execution:**
- `model_timeout_seconds` (float): Timeout per model call
- `enable_early_result_processing` (boolean): Process results as they arrive

### 4. Model Configuration

```json
{
  "models": [
    {
      "name": "qwen-max",
      "provider": "Alibaba",
      "display_name": "Qwen Max",
      "cost_per_1m_tokens": 0.4,
      "avg_response_time": 2.0,
      "enabled": true,
      "api_config": {
        "type": "dashscope",
        "model_id": "qwen-max",
        "search_enabled": true
      }
    }
  ]
}
```

**Model Properties:**
- `name` (string): Internal model name
- `provider` (string): Provider name
- `display_name` (string): Human-readable name
- `cost_per_1m_tokens` (float): Cost per million tokens in USD
- `avg_response_time` (float): Average response time in seconds
- `enabled` (boolean): Enable/disable this model
- `api_config` (object): Provider-specific API configuration

### 5. Storage Settings

```json
{
  "storage": {
    "base_dir": "./public/data/ai_orchestrator",
    "confidence_scores_file": "confidence_scores.json",
    "performance_history_file": "performance_history.jsonl",
    "corrections_file": "corrections.jsonl",
    "feedback_file": "feedback.jsonl",
    "cleanup_days_to_keep": 90
  }
}
```

**Paths:**
- `base_dir` (string): Base directory for all storage files
- `*_file` (string): Individual file names (relative to base_dir)
- `cleanup_days_to_keep` (int): Days of history to retain

### 6. Performance Tracking

```json
{
  "performance": {
    "enable_performance_tracking": true,
    "enable_anomaly_detection": true,
    "anomaly_threshold": 0.3,
    "max_response_time": 60.0,
    "max_cost_per_request": 1.0,
    "min_confidence_score": 0.5
  }
}
```

**Anomaly Detection:**
- `enable_performance_tracking` (boolean): Enable metrics collection
- `enable_anomaly_detection` (boolean): Enable anomaly detection
- `anomaly_threshold` (float): Threshold for anomaly detection (0.0-1.0)

**Limits:**
- `max_response_time` (float): Maximum acceptable response time
- `max_cost_per_request` (float): Maximum acceptable cost
- `min_confidence_score` (float): Minimum acceptable confidence

### 7. Validation Rules

```json
{
  "validation": {
    "enable_validation": true,
    "auto_validate_results": true,
    "validation_timeout": 180,
    "gpu_price": {
      "min_price": 0.01,
      "max_price": 1000.0,
      "required_fields": ["provider", "gpu", "price", "region"]
    },
    "token_price": {
      "min_price": 0.001,
      "max_price": 100.0,
      "required_fields": ["provider", "model", "input_price", "output_price"],
      "output_to_input_ratio": {
        "min": 1.5,
        "max": 5.0
      }
    },
    "grid_load": {
      "min_load": 0.0,
      "max_load": 100.0,
      "required_fields": ["region", "timestamp", "load_percentage"]
    }
  }
}
```

**Validation Settings:**
- `enable_validation` (boolean): Enable data validation
- `auto_validate_results` (boolean): Automatically validate results
- `validation_timeout` (float): Timeout for validation in seconds

**Data Type Rules:**
- `gpu_price`: GPU price validation rules
- `token_price`: Token price validation rules
- `grid_load`: Grid load validation rules

### 8. Logging

```json
{
  "logging": {
    "level": "INFO",
    "enable_detailed_logging": true,
    "log_file": "./logs/ai_orchestrator.log",
    "max_log_size_mb": 100,
    "backup_count": 5
  }
}
```

**Log Settings:**
- `level` (string): Log level (DEBUG, INFO, WARNING, ERROR)
- `enable_detailed_logging` (boolean): Enable detailed logs
- `log_file` (string): Path to log file
- `max_log_size_mb` (int): Maximum log file size in MB
- `backup_count` (int): Number of backup log files to keep

### 9. Legacy System

```json
{
  "legacy_system": {
    "enabled": false,
    "api_endpoint": "http://localhost:8000",
    "api_key": null,
    "timeout": 30,
    "retry_count": 3,
    "retry_delay": 1.0
  }
}
```

**Legacy Settings:**
- `enabled` (boolean): Enable legacy system
- `api_endpoint` (string): Legacy system API endpoint
- `api_key` (string): API key for legacy system
- `timeout` (int): Request timeout in seconds
- `retry_count` (int): Number of retries on failure
- `retry_delay` (float): Delay between retries in seconds

### 10. API Keys

```json
{
  "api_keys": {
    "dashscope": null,
    "volcengine": null,
    "openai": null,
    "description": "API keys should be set via environment variables or .env file"
  }
}
```

**Note:** API keys should be set via environment variables or `.env` file for security, not in this configuration file.

## Usage Examples

### Basic Usage

```python
from ai_orchestrator import MigrationAdapter

# Initialize with default config
adapter = MigrationAdapter()
orchestrator = adapter.initialize_orchestrator()

# Check status
status = adapter.get_status()
print(status)
```

### Custom Configuration Path

```python
adapter = MigrationAdapter(config_path='/path/to/custom-config.json')
```

### Dynamic Configuration Update

```python
adapter.update_config({
    'system': {
        'use_orchestrator': False  # Switch to legacy
    }
})
```

### Toggle Feature Flag

```python
adapter.update_config({
    'feature_flags': {
        'enable_validation': False  # Disable validation
    }
})
```

### Toggle Orchestrator

```python
adapter.toggle_orchestrator(False)  # Disable orchestrator
adapter.toggle_orchestrator(True)   # Enable orchestrator
```

## Migration Strategies

### Gradual Migration (Recommended)

1. Start with `use_orchestrator: false` (legacy only)
2. Enable orchestrator: `use_orchestrator: true`
3. Gradually enable feature flags:
   - Week 1: `enable_model_selection`, `enable_parallel_execution`
   - Week 2: `enable_result_merging`, `enable_validation`
   - Week 3: `enable_performance_tracking`, `enable_feedback_loop`
4. Monitor performance and adjust thresholds
5. Disable legacy system: `legacy_system.enabled: false`

### Full Migration

Set configuration:
```json
{
  "system": {
    "use_orchestrator": true,
    "migration_mode": "full"
  },
  "legacy_system": {
    "enabled": false
  }
}
```

### Rollback

If issues occur:
```python
adapter.toggle_orchestrator(False)  # Fall back to legacy
```

Or update config:
```json
{
  "system": {
    "use_orchestrator": false
  }
}
```

## Configuration Validation

The system validates configuration on startup and provides warnings for:
- Missing required fields
- Invalid value ranges
- Deprecated options
- Missing model configurations

Check logs for validation warnings.

## Best Practices

1. **Version Control**: Keep `config.json` in version control
2. **Environment Variables**: Use environment variables for sensitive data
3. **Backup**: Keep backups of working configurations
4. **Testing**: Test configuration changes in staging environment
5. **Monitoring**: Monitor performance metrics after configuration changes
6. **Documentation**: Document any custom configurations

## Troubleshooting

### Configuration Not Loading

Check:
- File path is correct
- File is valid JSON
- File permissions are readable

### Features Not Working

Check:
- Feature flag is enabled
- Orchestrator is enabled
- Model is enabled and configured
- Check logs for validation errors

### Performance Issues

Adjust:
- `model_timeout_seconds`: Increase timeout
- `simple_query_model_count`: Reduce for faster responses
- `enable_early_result_processing`: Enable for faster results

### Cost Issues

Adjust:
- `default_cost_limit`: Lower cost limit
- `simple_query_model_count`: Use fewer models
- Model costs in `models` configuration
