# AI Orchestrator Deployment Guide

## Table of Contents

1. [Pre-Deployment Checklist](#pre-deployment-checklist)
2. [Deployment Steps](#deployment-steps)
3. [Post-Deployment Verification](#post-deployment-verification)
4. [Rollback Procedures](#rollback-procedures)
5. [Monitoring Setup](#monitoring-setup)
6. [Troubleshooting](#troubleshooting)

---

## Pre-Deployment Checklist

### Environment Requirements

- [ ] Python 3.10+ installed
- [ ] All dependencies installed (`pip install -r requirements.txt`)
- [ ] aiofiles installed for async I/O (optional but recommended)
- [ ] Storage directory writable
- [ ] API keys configured (if using external AI services)

### Configuration Verification

- [ ] `config.json` exists and is valid JSON
- [ ] Model configurations are correct
- [ ] Cost limits set appropriately
- [ ] Quality thresholds configured
- [ ] Storage paths are correct
- [ ] Cache settings tuned for workload

### Code Quality Checks

- [ ] All tests pass (`python -m pytest`)
- [ ] No syntax errors
- [ ] Type checking passes (`mypy ai_orchestrator/`)
- [ ] Code review completed

### Data Preparation

- [ ] Backup existing confidence scores
- [ ] Backup performance history
- [ ] Review historical data for anomalies

### Infrastructure

- [ ] Sufficient disk space for logs and data
- [ ] Memory requirements met
- [ ] Network connectivity to AI providers

---

## Deployment Steps

### Step 1: Backup Current State

```bash
# Create backup directory
mkdir -p backups/$(date +%Y%m%d)

# Backup configuration
cp config.json backups/$(date +%Y%m%d)/

# Backup data files
cp -r data/ backups/$(date +%Y%m%d)/
```

### Step 2: Update Dependencies

```bash
# Update pip
pip install --upgrade pip

# Install/update requirements
pip install -r requirements.txt

# Optional: Install aiofiles for async I/O
pip install aiofiles
```

### Step 3: Validate Configuration

```python
# Run configuration validation
python -c "
from ai_orchestrator import OrchestratorConfig
import json

# Load and validate config
with open('config.json') as f:
    config = json.load(f)

print('Configuration valid')
print(f'Models configured: {len(config.get(\"models\", []))}')
print(f'Feature flags: {config.get(\"feature_flags\", {})}')
"
```

### Step 4: Run Pre-Deployment Tests

```bash
# Run unit tests
python -m pytest tests/ -v

# Run integration tests
python -m pytest tests/integration/ -v --timeout=60
```

### Step 5: Deploy Application

```bash
# If using gradual migration
python -c "
from ai_orchestrator import MigrationAdapter

adapter = MigrationAdapter()
adapter.toggle_orchestrator(True)
print('Orchestrator enabled')
"

# Restart application/service
# systemctl restart computepulse  # or your service manager
```

### Step 6: Enable Features Gradually

```python
# Week 1: Model selection only
from ai_orchestrator import MigrationAdapter

adapter = MigrationAdapter()
adapter.update_config({
    'feature_flags': {
        'enable_model_selection': True,
        'enable_parallel_execution': False,
        'enable_result_merging': False,
        'enable_validation': False
    }
})

# Week 2: Add parallel execution
adapter.update_config({
    'feature_flags': {
        'enable_model_selection': True,
        'enable_parallel_execution': True,
        'enable_result_merging': False,
        'enable_validation': False
    }
})

# Week 3: Full features
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

---

## Post-Deployment Verification

### Immediate Checks (First 5 Minutes)

- [ ] Application starts without errors
- [ ] No crash logs in error output
- [ ] Basic health check passes
- [ ] Can initialize orchestrator

```python
# Quick health check
from ai_orchestrator import AIOrchestrator

orchestrator = AIOrchestrator()
print("Orchestrator initialized successfully")
print(f"Cache enabled: {orchestrator.enable_cache}")
print(f"Models: {len(orchestrator.models)}")
```

### Short-Term Monitoring (First Hour)

- [ ] Request processing works
- [ ] Response times acceptable
- [ ] No memory leaks
- [ ] Cache hit rates reasonable
- [ ] No unexpected errors

```python
# Check performance report
from ai_orchestrator import AIOrchestrator

orchestrator = AIOrchestrator()
report = orchestrator.generate_performance_report(output_format='dict')
print(f"Requests: {report.get('total_requests', 0)}")
print(f"Cache stats: {report.get('cache_stats', {})}")
```

### Extended Monitoring (First 24 Hours)

- [ ] Success rate above threshold
- [ ] Cost within budget
- [ ] Learning engine updating scores
- [ ] Storage operations completing
- [ ] No degradation over time

---

## Rollback Procedures

### Quick Rollback (< 5 minutes)

Disable orchestrator immediately:

```python
from ai_orchestrator import MigrationAdapter

adapter = MigrationAdapter()
adapter.toggle_orchestrator(False)
print("Rolled back to legacy system")
```

### Configuration Rollback

Restore previous configuration:

```bash
# Restore from backup
cp backups/YYYYMMDD/config.json .

# Restart application
# systemctl restart computepulse
```

### Full Rollback

Complete rollback to previous version:

```bash
# 1. Stop application
# systemctl stop computepulse

# 2. Restore all files from backup
cp -r backups/YYYYMMDD/* .

# 3. Restart application
# systemctl start computepulse

# 4. Verify
python -c "from ai_orchestrator import AIOrchestrator; print('OK')"
```

### Data Recovery

Restore data files if corrupted:

```bash
# Restore confidence scores
cp backups/YYYYMMDD/data/confidence_scores.json data/

# Restore performance history
cp backups/YYYYMMDD/data/performance_history.jsonl data/

# Verify data integrity
python -c "
from ai_orchestrator import StorageManager, OrchestratorConfig

storage = StorageManager(OrchestratorConfig())
scores = storage.load_confidence_scores()
print(f'Loaded {len(scores)} confidence scores')
"
```

---

## Monitoring Setup

### Key Metrics to Monitor

1. **Request Metrics**
   - Total requests per minute
   - Success rate
   - Error rate
   - Response time (p50, p95, p99)

2. **Model Metrics**
   - Models used per request
   - Confidence scores trends
   - Cost per request
   - Token usage

3. **Cache Metrics**
   - Hit rate
   - Miss rate
   - Eviction rate
   - Memory usage

4. **System Metrics**
   - CPU usage
   - Memory usage
   - Disk I/O
   - Network latency

### Logging Configuration

```python
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ai_orchestrator.log'),
        logging.StreamHandler()
    ]
)

# Enable debug logging for troubleshooting
# logging.getLogger('ai_orchestrator').setLevel(logging.DEBUG)
```

### Alert Thresholds

| Metric | Warning | Critical |
|--------|---------|----------|
| Error Rate | > 5% | > 10% |
| Response Time (p95) | > 5s | > 10s |
| Cache Hit Rate | < 50% | < 20% |
| Cost per Hour | > $10 | > $50 |
| Memory Usage | > 80% | > 95% |

### Health Check Endpoint

```python
async def health_check():
    """Health check for monitoring systems."""
    from ai_orchestrator import AIOrchestrator

    try:
        orchestrator = AIOrchestrator()
        stats = orchestrator.get_cache_stats()

        return {
            "status": "healthy",
            "cache_enabled": orchestrator.enable_cache,
            "models_registered": len(orchestrator.models),
            "cache_entries": stats.get("total_entries", 0)
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }
```

---

## Troubleshooting

### Common Issues

#### Issue: "No models available"

**Cause:** No models registered with orchestrator

**Solution:**
```python
from ai_orchestrator import AIOrchestrator, AIModel

orchestrator = AIOrchestrator()

# Register at least one model
model = AIModel(
    name="qwen-max",
    provider="Alibaba",
    cost_per_1m_tokens=0.4,
    avg_response_time=2.0
)
orchestrator.register_model(model)
```

#### Issue: High Memory Usage

**Cause:** Cache too large or memory leak

**Solution:**
```python
# Reduce cache size
orchestrator = AIOrchestrator(
    cache_max_size=500,  # Reduce from default 1000
    cache_ttl_seconds=1800  # Reduce TTL
)

# Clear cache if needed
await orchestrator.clear_cache()
```

#### Issue: Slow Response Times

**Cause:** Too many models, slow AI providers, no caching

**Solution:**
```python
# Use fewer models
config = OrchestratorConfig(
    simple_query_model_count=1,
    complex_reasoning_model_count=2
)

# Enable early result processing
config.enable_early_result_processing = True

# Ensure cache is enabled
orchestrator = AIOrchestrator(config, enable_cache=True)
```

#### Issue: Storage Errors

**Cause:** Disk full, permission issues, corrupted files

**Solution:**
```bash
# Check disk space
df -h

# Check permissions
ls -la data/

# Reset storage
python -c "
from ai_orchestrator import StorageManager, OrchestratorConfig

storage = StorageManager(OrchestratorConfig())
storage.reset_memory_fallback()
"
```

#### Issue: Low Cache Hit Rate

**Cause:** High prompt variability, short TTL

**Solution:**
```python
# Increase TTL
orchestrator = AIOrchestrator(
    cache_ttl_seconds=7200  # 2 hours
)

# Check cache stats
stats = orchestrator.get_cache_stats()
print(f"Hit rate: {stats['hit_rate']}")
```

### Emergency Contacts

- On-call Engineer: [Your contact info]
- Escalation Path: [Your escalation path]
- Documentation: [Link to internal docs]

---

## Appendix

### Configuration Reference

See `CONFIGURATION.md` for complete configuration options.

### API Reference

See `ai_orchestrator/API.md` for complete API documentation.

### Migration Guide

See `MIGRATION_GUIDE.md` for migration procedures.

---

**Version:** 1.0.0
**Last Updated:** 2025-12-08
