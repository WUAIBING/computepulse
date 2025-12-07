"""
Test script for AI model adapters.
Tests each adapter's real capabilities.
"""

import os
import sys
import asyncio
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env.local
env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env.local')
load_dotenv(env_path)

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ai_orchestrator.adapters.qwen_adapter import QwenAdapter
from ai_orchestrator.adapters.deepseek_adapter import DeepSeekAdapter
from ai_orchestrator.adapters.kimi_adapter import KimiAdapter
from ai_orchestrator.adapters.glm_adapter import GLMAdapter
from ai_orchestrator.adapters.minimax_adapter import MiniMaxAdapter

# Test prompt - asking for real-time data to test web search
TEST_PROMPT = "请查询最新的美元兑人民币汇率是多少？请标注数据的时间和来源。"

def print_result(name: str, response):
    """Print test result."""
    print(f"\n{'='*60}")
    print(f"[BOT] {name}")
    print(f"{'='*60}")
    print(f"[OK] Success: {response.success}")
    print(f"[TIME] Response Time: {response.response_time:.2f}s")
    print(f"[TOKEN] Token Count: {response.token_count}")
    if response.error:
        print(f"[FAIL] Error: {response.error}")
    else:
        print(f"[RESPONSE] Response (first 500 chars):")
        print(response.content[:500] if len(response.content) > 500 else response.content)
    print()

async def test_qwen():
    """Test Qwen adapter."""
    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        print("[FAIL] DASHSCOPE_API_KEY not set")
        return
    
    adapter = QwenAdapter(api_key=api_key, enable_search=True)
    response = await adapter.call_async(TEST_PROMPT)
    print_result("Qwen3-Max (通义千问)", response)

async def test_deepseek():
    """Test DeepSeek adapter."""
    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        print("[FAIL] DASHSCOPE_API_KEY not set")
        return
    
    adapter = DeepSeekAdapter(api_key=api_key, enable_thinking=True, enable_search=True)
    response = await adapter.call_async(TEST_PROMPT)
    print_result("DeepSeek-V3.2 (深度求索)", response)
    if response.raw_response and "reasoning" in response.raw_response:
        print(f"[REASONING] Reasoning (first 300 chars):")
        print(response.raw_response["reasoning"][:300])

async def test_kimi():
    """Test Kimi adapter via DashScope compatible mode."""
    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        print("[FAIL] DASHSCOPE_API_KEY not set")
        return
    
    # Use DashScope compatible mode for Kimi
    adapter = KimiAdapter(
        api_key=api_key,
        model_name="Moonshot-Kimi-K2-Instruct",  # DashScope Kimi model
        enable_search=True
    )
    response = await adapter.call_async(TEST_PROMPT)
    print_result("Kimi (via DashScope)", response)

async def test_glm():
    """Test GLM adapter."""
    api_key = os.getenv("ZHIPU_API_KEY")
    if not api_key:
        print("[FAIL] ZHIPU_API_KEY not set")
        return
    
    adapter = GLMAdapter(api_key=api_key, enable_web_search=True)
    response = await adapter.call_async(TEST_PROMPT)
    print_result("GLM-4-Flash (智谱清言)", response)

async def test_minimax():
    """Test MiniMax adapter."""
    api_key = os.getenv("MINIMAX_API_KEY")
    if not api_key:
        print("[FAIL] MINIMAX_API_KEY not set")
        return
    
    adapter = MiniMaxAdapter(api_key=api_key)
    response = await adapter.call_async(TEST_PROMPT)
    print_result("MiniMax (MiniMax)", response)

async def main():
    """Run all adapter tests."""
    print("\n" + "="*60)
    print("[TEST] AI Adapter Test Suite")
    print(f"[TIME] Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"[PROMPT] Test Prompt: {TEST_PROMPT}")
    print("="*60)
    
    # Test each adapter
    print("\n[TEST] Testing Qwen...")
    await test_qwen()
    
    print("\n[TEST] Testing DeepSeek...")
    await test_deepseek()
    
    print("\n[TEST] Testing Kimi...")
    await test_kimi()
    
    print("\n[TEST] Testing GLM...")
    await test_glm()
    
    print("\n[TEST] Testing MiniMax...")
    await test_minimax()
    
    print("\n" + "="*60)
    print("[OK] All tests completed!")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(main())
