#!/usr/bin/env python3
"""
Orchestrator-powered price fetching script.
Coordinates multiple AI models to fetch, validate, and merge price data.

This script uses the Migration Adapter for backward compatibility
and supports gradual migration from the legacy system.
"""

import sys
import os
import asyncio
import json
import logging
from datetime import datetime
from typing import Callable, Dict, Any
from dotenv import load_dotenv

# Load environment variables
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env.local')
load_dotenv(env_path)

# Add project root to python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
computepulse_path = os.path.join(project_root, 'computepulse')
# Add computepulse first so its ai_orchestrator is found
sys.path.insert(0, computepulse_path)
sys.path.insert(0, project_root)

from ai_orchestrator.migration_adapter import MigrationAdapter
from ai_orchestrator.models import AIModel, Request, Response

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Now add computepulse/ai_orchestrator to path to import adapters
computepulse_ai_path = os.path.join(computepulse_path, 'ai_orchestrator')
sys.path.insert(0, computepulse_ai_path)

try:
    from adapters.qwen_adapter import QwenAdapter
    from adapters.deepseek_adapter import DeepSeekAdapter
    from adapters.glm_adapter import GLMAdapter
    from adapters.minimax_adapter import MiniMaxAdapter
    from adapters.kimi_adapter import KimiAdapter
    from adapters.gemini_adapter import GeminiAdapter
except ImportError as e:
    logger.error(f"Failed to import adapters: {e}")
    # Fallback: try relative import
    sys.path.insert(0, computepulse_path)
    from ai_orchestrator.adapters.qwen_adapter import QwenAdapter
    from ai_orchestrator.adapters.deepseek_adapter import DeepSeekAdapter
    from ai_orchestrator.adapters.glm_adapter import GLMAdapter
    from ai_orchestrator.adapters.minimax_adapter import MiniMaxAdapter
    from ai_orchestrator.adapters.kimi_adapter import KimiAdapter
    from ai_orchestrator.adapters.gemini_adapter import GeminiAdapter

# Constants
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'public', 'data')
GPU_FILE = os.path.join(DATA_DIR, 'gpu_prices.json')
TOKEN_FILE = os.path.join(DATA_DIR, 'token_prices.json')
GRID_FILE = os.path.join(DATA_DIR, 'grid_load.json')

# Model call function for AI Orchestrator
async def model_call_func(model: AIModel, request: Request) -> Response:
    """
    Call AI model adapter based on model name.

    Args:
        model: AIModel instance with name, provider, etc.
        request: Request object with prompt and context

    Returns:
        Response object with model's output
    """
    logger.info(f"Calling model: {model.name} (provider: {model.provider})")

    # Map model names to adapter classes
    adapter_map = {
        'qwen': QwenAdapter,
        'qwen-max': QwenAdapter,
        'deepseek': DeepSeekAdapter,
        'deepseek-v3': DeepSeekAdapter,
        'glm': GLMAdapter,
        'glm-4-flash': GLMAdapter,
        'minimax': MiniMaxAdapter,
        'kimi': KimiAdapter,
        'gemini': GeminiAdapter,
        'gemini-3-pro-preview': GeminiAdapter,
    }

    model_name_lower = model.name.lower()
    adapter_class = None

    # Find adapter class by checking if model name contains key
    for key, adapter_cls in adapter_map.items():
        if key in model_name_lower:
            adapter_class = adapter_cls
            break

    if not adapter_class:
        logger.error(f"No adapter found for model: {model.name}")
        return Response(
            model_name=model.name,
            content=f"Error: No adapter found for model {model.name}",
            response_time=0.0,
            token_count=0,
            cost=0.0,
            success=False,
            error=f"No adapter found for model {model.name}"
        )

    # Get API key from environment
    api_key = None
    if any(keyword in model_name_lower for keyword in ['qwen', 'deepseek', 'kimi']):
        api_key = os.getenv('DASHSCOPE_API_KEY')
    elif 'glm' in model_name_lower:
        api_key = os.getenv('ZHIPU_API_KEY')
    elif 'minimax' in model_name_lower:
        api_key = os.getenv('MINIMAX_API_KEY')
    elif 'gemini' in model_name_lower:
        api_key = os.getenv('GEMINI_API_KEY')

    if not api_key:
        logger.error(f"API key not found for model: {model.name}")
        return Response(
            model_name=model.name,
            content=f"Error: API key not configured for model {model.name}",
            response_time=0.0,
            token_count=0,
            cost=0.0,
            success=False,
            error=f"API key not configured for model {model.name}"
        )

    try:
        # Determine model name to use
        # Use adapter's DEFAULT_MODEL if available, otherwise use model.name
        if hasattr(adapter_class, 'DEFAULT_MODEL'):
            actual_model_name = adapter_class.DEFAULT_MODEL
            logger.debug(f"Using default model name for {model.name}: {actual_model_name}")
        else:
            actual_model_name = model.name

        # Create adapter instance
        adapter = adapter_class(
            model_name=actual_model_name,
            api_key=api_key,
            timeout=30.0,
            max_retries=3
        )

        # Set cost if available
        if hasattr(model, 'cost_per_1m_tokens'):
            adapter.cost_per_1m_tokens = model.cost_per_1m_tokens

        # Call model with retry and timeout
        start_time = datetime.now()
        adapter_response = await adapter.call_with_timeout(
            prompt=request.prompt,
            timeout=30.0
        )
        response_time = (datetime.now() - start_time).total_seconds()

        # Convert AdapterResponse to Response
        return Response(
            model_name=model.name,
            content=adapter_response.content,
            response_time=response_time,
            token_count=adapter_response.token_count,
            cost=adapter_response.cost,
            timestamp=adapter_response.timestamp,
            success=adapter_response.success,
            error=adapter_response.error
        )

    except Exception as e:
        logger.error(f"Error calling model {model.name}: {e}")
        return Response(
            model_name=model.name,
            content=f"Error: {str(e)}",
            response_time=0.0,
            token_count=0,
            cost=0.0,
            success=False,
            error=str(e)
        )


def extract_json_from_string(text: str):
    """
    Extract JSON from a string that may contain extra text.
    Returns parsed JSON object or None if extraction fails.
    """
    import json
    import re

    # First try to parse the whole string
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Try to find JSON array
    array_match = re.search(r'\[\s*\{.*\}\s*\]', text, re.DOTALL)
    if array_match:
        try:
            return json.loads(array_match.group(0))
        except json.JSONDecodeError:
            pass

    # Try to find JSON object
    object_match = re.search(r'\{\s*".*"\s*:\s*.+\s*\}', text, re.DOTALL)
    if object_match:
        try:
            return json.loads(object_match.group(0))
        except json.JSONDecodeError:
            pass

    # Try to find content between ```json and ``` markers
    json_block_match = re.search(r'```json\s*(.*?)\s*```', text, re.DOTALL)
    if json_block_match:
        try:
            return json.loads(json_block_match.group(1))
        except json.JSONDecodeError:
            pass

    # Try to find content between ``` and ``` (generic code block)
    code_block_match = re.search(r'```\s*(.*?)\s*```', text, re.DOTALL)
    if code_block_match:
        try:
            return json.loads(code_block_match.group(1))
        except json.JSONDecodeError:
            pass

    return None


async def fetch_gpu_prices(adapter: MigrationAdapter):
    """Fetch GPU prices using the adapter."""
    logger.info("Fetching GPU prices...")

    prompt = """
    请使用联网搜索功能，查找当前最新的 NVIDIA H100, A100 以及中国 AI 芯片 (华为昇腾 Ascend 910B, 寒武纪 MLU370) 的云租赁价格。
    优先搜索: Lambda Labs, RunPod, Vast.ai, AWS, Google Cloud, 阿里云, 腾讯云, 火山引擎.

    返回 JSON 格式列表:
    [
      {"provider": "Lambda", "gpu": "H100", "price": 2.49, "region": "US-East", "currency": "USD"},
      ...
    ]
    """

    result = await adapter.fetch_data_with_collaboration(
        prompt=prompt,
        data_type='gpu',
        quality_threshold=0.8,
        cost_limit=0.1,
        timestamp=datetime.now().isoformat(),
        model_call_func=model_call_func
    )

    if result.get('success') and result.get('data'):
        data = result['data']

        # Try to extract JSON from string if needed
        if isinstance(data, str):
            extracted = extract_json_from_string(data)
            if extracted is not None:
                data = extracted
                logger.debug("Successfully extracted JSON from string")
            else:
                # If extraction fails, try direct json.loads as last resort
                try:
                    data = json.loads(data)
                    logger.debug("Successfully parsed JSON string")
                except json.JSONDecodeError:
                    logger.warning(f"Failed to parse JSON from string: {data[:100]}...")

        if isinstance(data, list):
            logger.info(f"Successfully fetched {len(data)} GPU price records")
            save_json(data, GPU_FILE)
        else:
            logger.warning(f"Unexpected data format: {type(data)}. Data: {str(data)[:200]}...")
    else:
        logger.warning(f"Failed to fetch GPU prices: {result.get('error', 'Unknown error')}")

async def fetch_token_prices(adapter: MigrationAdapter):
    """Fetch Token prices using the adapter."""
    logger.info("Fetching Token prices...")

    prompt = """
    请使用联网搜索功能，查找当前最新的 LLM API 价格 (每 1M Tokens)。
    模型: GPT-4o, Claude 3.5 Sonnet, Gemini 1.5 Pro, DeepSeek-V3, Qwen-Max, Doubao-Pro.

    返回 JSON 格式列表:
    [
      {"provider": "OpenAI", "model": "GPT-4o", "input_price": 2.5, "output_price": 10.0, "currency": "USD"},
      ...
    ]
    """

    result = await adapter.fetch_data_with_collaboration(
        prompt=prompt,
        data_type='token',
        quality_threshold=0.8,
        cost_limit=0.1,
        timestamp=datetime.now().isoformat(),
        model_call_func=model_call_func
    )

    if result.get('success') and result.get('data'):
        data = result['data']

        # Try to extract JSON from string if needed
        if isinstance(data, str):
            extracted = extract_json_from_string(data)
            if extracted is not None:
                data = extracted
                logger.debug("Successfully extracted JSON from string")
            else:
                # If extraction fails, try direct json.loads as last resort
                try:
                    data = json.loads(data)
                    logger.debug("Successfully parsed JSON string")
                except json.JSONDecodeError:
                    logger.warning(f"Failed to parse JSON from string: {data[:100]}...")

        if isinstance(data, list):
            logger.info(f"Successfully fetched {len(data)} token price records")
            save_json(data, TOKEN_FILE)
        else:
            logger.warning(f"Unexpected data format: {type(data)}. Data: {str(data)[:200]}...")
    else:
        logger.warning(f"Failed to fetch Token prices: {result.get('error', 'Unknown error')}")

async def fetch_grid_load(adapter: MigrationAdapter):
    """Fetch Grid Load data using the adapter."""
    logger.info("Fetching Grid Load data...")

    prompt = """
    请估算当前全球 AI 数据中心的总能耗 (GW) 和平均电价 ($/kWh)。
    参考来源: IEA 报告, Digiconomist, NVIDIA 出货量估算.

    返回 JSON 格式对象:
    {
      "active_gpu_est": 4500000,
      "total_power_gw": 45.5,
      "kwh_price": 0.12,
      "annual_twh": 400,
      "timestamp": "..."
    }
    """

    result = await adapter.fetch_data_with_collaboration(
        prompt=prompt,
        data_type='grid_load',
        quality_threshold=0.7,
        timestamp=datetime.now().isoformat(),
        model_call_func=model_call_func
    )

    if result.get('success') and result.get('data'):
        data = result['data']

        # Try to extract JSON from string if needed
        if isinstance(data, str):
            extracted = extract_json_from_string(data)
            if extracted is not None:
                data = extracted
                logger.debug("Successfully extracted JSON from string")
            else:
                # If extraction fails, try direct json.loads as last resort
                try:
                    data = json.loads(data)
                    logger.debug("Successfully parsed JSON string")
                except json.JSONDecodeError:
                    logger.warning(f"Failed to parse JSON from string: {data[:100]}...")

        if isinstance(data, dict):
            logger.info("Successfully fetched Grid Load data")
            save_json(data, GRID_FILE)
        else:
            logger.warning(f"Unexpected data format: {type(data)}. Data: {str(data)[:200]}...")
    else:
        logger.warning(f"Failed to fetch Grid Load data: {result.get('error', 'Unknown error')}")

def save_json(data, filepath):
    """Save data to JSON file."""
    try:
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        logger.info(f"Saved data to {filepath}")
    except Exception as e:
        logger.error(f"Error saving to {filepath}: {e}")

async def main():
    """Main execution flow."""
    # Initialize Migration Adapter
    adapter = MigrationAdapter()

    # Initialize orchestrator with configured models
    orchestrator = adapter.initialize_orchestrator()

    if not orchestrator:
        logger.error("Failed to initialize orchestrator")
        return

    # Print status
    status = adapter.get_status()
    logger.info(f"Adapter Status: {json.dumps(status, indent=2)}")

    # Run tasks
    await fetch_gpu_prices(adapter)
    await fetch_token_prices(adapter)
    await fetch_grid_load(adapter)

    # Print performance report
    report = orchestrator.generate_performance_report(output_format='text')
    logger.info("\n" + "=" * 80)
    logger.info("Performance Report:")
    logger.info("=" * 80)
    logger.info(report)

    logger.info("All tasks completed.")

if __name__ == "__main__":
    asyncio.run(main())
