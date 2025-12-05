#!/usr/bin/env python3
"""
Orchestrator-powered price fetching script.
Coordinates multiple AI models to fetch, validate, and merge price data.
"""

import sys
import os
import asyncio
import json
import logging
from datetime import datetime

# Add project root to python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai_orchestrator.orchestrator import AIOrchestrator
from ai_orchestrator.models import AIModel, TaskType
from ai_orchestrator.config import OrchestratorConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'public', 'data')
GPU_FILE = os.path.join(DATA_DIR, 'gpu_prices.json')
TOKEN_FILE = os.path.join(DATA_DIR, 'token_prices.json')
GRID_FILE = os.path.join(DATA_DIR, 'grid_load.json')

async def fetch_gpu_prices(orchestrator: AIOrchestrator):
    """Fetch GPU prices using the orchestrator."""
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
    
    result = await orchestrator.process_request(
        prompt=prompt,
        quality_threshold=0.8,
        cost_limit=0.1
    )
    
    if result.data:
        logger.info(f"Successfully fetched {len(result.data)} GPU price records")
        save_json(result.data, GPU_FILE)
    else:
        logger.warning("Failed to fetch GPU prices")

async def fetch_token_prices(orchestrator: AIOrchestrator):
    """Fetch Token prices using the orchestrator."""
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
    
    result = await orchestrator.process_request(
        prompt=prompt,
        quality_threshold=0.8,
        cost_limit=0.1
    )
    
    if result.data:
        logger.info(f"Successfully fetched {len(result.data)} token price records")
        save_json(result.data, TOKEN_FILE)
    else:
        logger.warning("Failed to fetch Token prices")

async def fetch_grid_load(orchestrator: AIOrchestrator):
    """Fetch Grid Load data using the orchestrator."""
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
    
    result = await orchestrator.process_request(
        prompt=prompt,
        quality_threshold=0.7
    )
    
    if result.data:
        logger.info("Successfully fetched Grid Load data")
        save_json(result.data, GRID_FILE)
    else:
        logger.warning("Failed to fetch Grid Load data")

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
    # Initialize Orchestrator
    config = OrchestratorConfig()
    orchestrator = AIOrchestrator(config)
    
    # Register Models (Mocking adapter registration for now)
    # In a real scenario, we would load these from a config or adapter registry
    orchestrator.register_model(AIModel(name="qwen-max", provider="Alibaba", cost_per_1m_tokens=0.4, avg_response_time=2.0))
    orchestrator.register_model(AIModel(name="doubao-pro", provider="ByteDance", cost_per_1m_tokens=0.2, avg_response_time=1.5))
    
    # Run tasks
    await fetch_gpu_prices(orchestrator)
    await fetch_token_prices(orchestrator)
    await fetch_grid_load(orchestrator)
    
    logger.info("All tasks completed.")

if __name__ == "__main__":
    asyncio.run(main())
