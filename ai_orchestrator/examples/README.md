# AI Orchestrator Examples

This directory contains practical examples demonstrating how to use the AI Orchestrator in various scenarios.

## Running the Examples

All examples are standalone Python scripts. Run them using:

```bash
python basic_usage.py
python custom_configuration.py
python adding_new_model.py
python migration_example.py
```

## Examples Overview

### 1. Basic Usage (`basic_usage.py`)

**Purpose:** Learn the fundamentals of the AI Orchestrator

**What it demonstrates:**
- Creating an AI Orchestrator instance
- Registering AI models
- Processing a request
- Handling responses
- Basic performance tracking
- Recording feedback

**Key concepts:**
- Default configuration
- Model registration
- Request processing
- Response handling

**Run it:**
```bash
python basic_usage.py
```

---

### 2. Custom Configuration (`custom_configuration.py`)

**Purpose:** Learn how to configure the orchestrator for different use cases

**What it demonstrates:**
- Creating custom configuration objects
- High-quality configuration
- Fast & cheap configuration
- Validation-focused configuration
- Processing requests with different configs
- Dynamic configuration updates

**Use cases:**
- Quality-critical applications
- Budget-constrained applications
- High-volume data validation
- Real-time systems

**Run it:**
```bash
python custom_configuration.py
```

---

### 3. Adding New Models (`adding_new_model.py`)

**Purpose:** Learn how to add and manage AI models

**What it demonstrates:**
- Adding new models to the orchestrator
- Configuring model parameters (cost, response time)
- Monitoring model performance
- Recording feedback
- Managing model lifecycle
- Specialized model configurations

**Key concepts:**
- Model registration
- Performance monitoring
- Confidence score tracking
- Model lifecycle management

**Run it:**
```bash
python adding_new_model.py
```

---

### 4. Migration Example (`migration_example.py`)

**Purpose:** Learn how to migrate from legacy systems to AI Orchestrator

**What it demonstrates:**
- Setting up MigrationAdapter
- Backward compatible API usage
- New orchestrator API usage
- Gradual migration strategy
- Configuration management
- Rollback procedures

**Key concepts:**
- MigrationAdapter
- Backward compatibility
- Feature flags
- Gradual migration
- Rollback capability

**Run it:**
```bash
python migration_example.py
```

---

## Common Patterns

### Pattern 1: Basic Setup

```python
from ai_orchestrator import AIOrchestrator, AIModel

# Create orchestrator
orchestrator = AIOrchestrator()

# Register models
model = AIModel(
    name="qwen-max",
    provider="Alibaba",
    cost_per_1m_tokens=0.4,
    avg_response_time=2.0
)
orchestrator.register_model(model)

# Process request
result = await orchestrator.process_request(
    prompt="Your prompt here",
    model_call_func=your_model_call_func
)
```

### Pattern 2: Custom Configuration

```python
from ai_orchestrator import AIOrchestrator, OrchestratorConfig

config = OrchestratorConfig(
    default_quality_threshold=0.9,
    default_cost_limit=0.5,
    simple_query_model_count=1,
    complex_reasoning_model_count=3
)

orchestrator = AIOrchestrator(config)
```

### Pattern 3: Using MigrationAdapter

```python
from ai_orchestrator import MigrationAdapter

adapter = MigrationAdapter()
orchestrator = adapter.initialize_orchestrator()

# Backward compatible
result = await adapter.fetch_data_with_collaboration(
    prompt="Your prompt",
    data_type='gpu'
)
```

### Pattern 4: Model Call Function

```python
async def call_model(model, request):
    # Your AI model API call here
    # Return Response object
    return Response(
        model_name=model.name,
        content="Model response",
        response_time=1.5,
        token_count=100,
        cost=0.04,
        timestamp=datetime.now()
    )

result = await orchestrator.process_request(
    prompt="...",
    model_call_func=call_model
)
```

---

## Example Output

Each example produces detailed output showing:

1. **Setup steps** - What components are being initialized
2. **Configuration** - Settings being used
3. **Processing** - Request handling details
4. **Results** - Response data and metadata
5. **Performance** - Metrics and reports
6. **Best practices** - Recommendations

Example output structure:

```
========================================
AI Orchestrator - Basic Usage Example
========================================

Step 1: Creating AI Orchestrator...
  ✓ Orchestrator created with default configuration

Step 2: Registering AI models...
  ✓ Registered: qwen-max (Alibaba)
  ✓ Registered: doubao-pro (ByteDance)
  ...

Step 3: Processing a request...
  Prompt: Please search for the latest...
  [Model Call] qwen-max processing request...
  [Model Call] doubao-pro processing request...

Step 4: Processing results...
  ✓ Request completed successfully
  ✓ Data received: <class 'str'>
  ✓ Contributing models: ['qwen-max', 'doubao-pro']
  ...
```

---

## Modifying Examples

### Adding Your Own Models

Replace the mock model configurations with your actual models:

```python
# Replace this:
model = AIModel(
    name="qwen-max",
    provider="Alibaba",
    cost_per_1m_tokens=0.4,
    avg_response_time=2.0
)

# With your model:
model = AIModel(
    name="your-model-name",
    provider="your-provider",
    cost_per_1m_tokens=0.5,  # Your actual cost
    avg_response_time=2.0    # Your actual response time
)
```

### Using Real API Calls

Replace the mock `call_model` function with your actual API calls:

```python
async def your_actual_model_call(model, request):
    # Call your AI model API
, using OpenAI    # For example:
    response = openai.ChatCompletion.create(
        model=model.name,
        messages=[{"role": "user", "content": request.prompt}]
    )

    # Return Response object
    return Response(
        model_name=model.name,
        content=response.choices[0].message.content,
        response_time=response.response_time,
        token_count=response.usage.total_tokens,
        cost=calculate_cost(response.usage),
        timestamp=datetime.now()
    )
```

### Custom Prompts

Change the prompts in the examples to match your use case:

```python
prompt = """
Your custom prompt here.
Be specific about what you want the AI to do.
Include format requirements.
"""
```

---

## Troubleshooting Examples

### Error: "No models available"

**Solution:** Register at least one model before processing requests.

### Error: "model_call_func is required"

**Solution:** Provide a model call function when calling `process_request()`.

### Error: "Low confidence scores"

**Solution:** This is normal for new systems. Provide feedback to improve scores.

### Import Errors

**Solution:** Make sure you're in the correct directory and the package is installed:

```bash
cd /path/to/ai_orchestrator
python basic_usage.py
```

---

## Next Steps

After running the examples:

1. **Read the API Documentation** (`../API.md`) for detailed reference
2. **Review Configuration Guide** (`../../CONFIGURATION.md`) for all settings
3. **Check Migration Guide** for transition strategies
4. **Run the test suite** to verify installation
5. **Start with your own use case** using the patterns from examples

---

## Additional Resources

- **API Documentation**: `../API.md`
- **Configuration Guide**: `../../CONFIGURATION.md`
- **Migration Guide**: See `migration_example.py`
- **GitHub Repository**: Check for updates and issues

---

## Support

If you encounter issues with the examples:

1. Check the troubleshooting section above
2. Review the API documentation
3. Check configuration settings
4. Verify your Python environment
5. Create an issue with error details

---

## License

These examples are part of the AI Orchestrator project.
See the main project license for details.
