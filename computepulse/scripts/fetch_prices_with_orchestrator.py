"""
Production-ready data fetching with AI Orchestrator integration.

This script integrates the intelligent AI Orchestrator system with the existing
ComputePulse data fetching workflow.

Supported AI Models:
- Qwen (通义千问) - with search enabled
- DeepSeek - reasoning mode
"""

import dashscope
import json
import os
import sys
import time
import requests
import asyncio
from datetime import datetime, timedelta

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from ai_orchestrator import AIOrchestrator, AIModel, TaskType, OrchestratorConfig

# Set API Keys
dashscope.api_key = os.getenv('DASHSCOPE_API_KEY')

# Try to load from .env.local if not in env
if not dashscope.api_key:
    try:
        with open('.env.local', 'r') as f:
            for line in f:
                if 'DASHSCOPE_API_KEY' in line:
                    dashscope.api_key = line.split('=')[1].strip()
    except:
        pass

# Define paths
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'public', 'data')
os.makedirs(DATA_DIR, exist_ok=True)

GPU_FILE = os.path.join(DATA_DIR, 'gpu_prices.json')
TOKEN_FILE = os.path.join(DATA_DIR, 'token_prices.json')
GRID_FILE = os.path.join(DATA_DIR, 'grid_load.json')
HISTORY_FILE = os.path.join(DATA_DIR, 'history_data.json')

# Initialize AI Orchestrator
print(f"[{datetime.now()}] Initializing AI Orchestrator...")
orchestrator = AIOrchestrator(OrchestratorConfig())

# Register AI models (Qwen and DeepSeek only)
orchestrator.register_model(AIModel(
    name="qwen",
    provider="Alibaba DashScope",
    cost_per_1m_tokens=0.6,
    avg_response_time=3.5
))

orchestrator.register_model(AIModel(
    name="deepseek",
    provider="DeepSeek",
    cost_per_1m_tokens=0.8,
    avg_response_time=5.0
))

print(f"[{datetime.now()}] AI Orchestrator initialized with {len(orchestrator.models)} models")


def call_qwen_with_search(prompt: str, max_retries: int = 2):
    """Call Qwen API with search enabled."""
    from dashscope import Generation
    
    for attempt in range(max_retries):
        try:
            response = Generation.call(
                model='qwen-plus',  # Use qwen-plus for better search support
                prompt=prompt,
                enable_search=True
            )
            if response.status_code == 200:
                return response.output.text
        except Exception as e:
            print(f"Qwen Call Failed (attempt {attempt+1}): {e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
    return None


def call_deepseek_with_reasoning(prompt: str, max_retries: int = 2):
    """Call DeepSeek API with reasoning mode."""
    from openai import OpenAI
    
    deepseek_client = OpenAI(
        api_key=dashscope.api_key,
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    )
    
    for attempt in range(max_retries):
        try:
            completion = deepseek_client.chat.completions.create(
                model="deepseek-v3",
                messages=[{"role": "user", "content": prompt}],
                stream=False,
            )
            if completion.choices and len(completion.choices) > 0:
                return completion.choices[0].message.content
        except Exception as e:
            print(f"DeepSeek Call Failed (attempt {attempt+1}): {e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
    return None


def clean_and_parse_json(content):
    """Clean and parse JSON from AI response."""
    if not content:
        return []
    try:
        cleaned = content.replace('```json', '').replace('```', '').strip()
        
        if '[' in cleaned and ']' in cleaned:
            start = cleaned.find('[')
            end = cleaned.rfind(']') + 1
            cleaned = cleaned[start:end]
        elif '{' in cleaned and '}' in cleaned:
            start = cleaned.find('{')
            end = cleaned.rfind('}') + 1
            cleaned = cleaned[start:end]
            
        return json.loads(cleaned)
    except Exception as e:
        print(f"JSON Parse Error: {e}")
        return None


async def fetch_with_orchestrator(prompt: str, task_type: TaskType, data_type: str):
    """
    Fetch data using the AI Orchestrator for intelligent model selection.
    """
    print(f"\n[{datetime.now()}] 🤖 Using AI Orchestrator for {data_type} data...")
    
    start_time = time.time()
    
    result = await orchestrator.process_request(
        prompt=prompt,
        context={"data_type": data_type},
        quality_threshold=0.7
    )
    
    responses = {}
    
    if "qwen" in result.contributing_models:
        print(f"  → Calling Qwen (confidence: {result.confidence_scores.get('qwen', 0):.2f})")
        qwen_content = call_qwen_with_search(prompt)
        if qwen_content:
            responses["qwen"] = clean_and_parse_json(qwen_content)
    
    if "deepseek" in result.contributing_models:
        print(f"  → Calling DeepSeek (confidence: {result.confidence_scores.get('deepseek', 0):.2f})")
        deepseek_content = call_deepseek_with_reasoning(prompt)
        if deepseek_content:
            responses["deepseek"] = clean_and_parse_json(deepseek_content)
    
    elapsed_time = time.time() - start_time
    
    # Priority: DeepSeek > Qwen
    final_data = None
    for model_name in ["deepseek", "qwen"]:
        if model_name in responses and responses[model_name]:
            final_data = responses[model_name]
            break
    
    # Record feedback for learning
    for model_name in responses:
        was_correct = responses[model_name] is not None and len(responses[model_name]) > 0
        orchestrator.record_feedback(
            request_id=result.metadata['request_id'],
            model_name=model_name,
            task_type=task_type,
            was_correct=was_correct,
            response_time=elapsed_time / len(responses) if responses else elapsed_time,
            cost=orchestrator.models[model_name].cost_per_1m_tokens * 0.001
        )
    
    print(f"  ✅ Completed in {elapsed_time:.2f}s using {len(responses)} model(s)")
    
    return final_data


async def fetch_gpu_prices():
    """Fetch GPU prices using AI Orchestrator."""
    prompt = """
    请使用联网搜索功能，查找当前最新的 NVIDIA H100, A100 以及中国 AI 芯片的云租赁价格。
    返回严格的 JSON 数组格式，不要包含 Markdown 标记。
    
    格式：
    [
      {"provider": "Lambda", "region": "US-West", "gpu": "H100", "price": 2.49}
    ]
    """
    
    try:
        data = await fetch_with_orchestrator(prompt, TaskType.PRICE_EXTRACTION, "gpu")
        
        if data:
            with open(GPU_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"[{datetime.now()}] ✅ GPU Prices updated ({len(data)} records)")
        else:
            print(f"[{datetime.now()}] ⚠️  Failed to fetch GPU prices")
            
    except Exception as e:
        print(f"[{datetime.now()}] ❌ GPU Fetch Error: {e}")


async def fetch_token_prices():
    """Fetch token prices using AI Orchestrator."""
    prompt = """
    请使用联网搜索功能，查找大模型 API 的最新价格（每 1M Token）。
    返回严格的 JSON 数组格式。
    
    格式：
    [
      {"provider": "OpenAI", "model": "GPT-4o", "input_price": 5.0, "output_price": 15.0}
    ]
    """
    
    try:
        data = await fetch_with_orchestrator(prompt, TaskType.PRICE_EXTRACTION, "token")
        
        if data:
            with open(TOKEN_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"[{datetime.now()}] ✅ Token Prices updated ({len(data)} records)")
        else:
            print(f"[{datetime.now()}] ⚠️  Failed to fetch token prices")
            
    except Exception as e:
        print(f"[{datetime.now()}] ❌ Token Fetch Error: {e}")


async def fetch_grid_load():
    """Fetch grid load data using AI Orchestrator."""
    prompt = """
    请使用联网搜索功能，查找全球 AI 数据中心能耗的最新数据。
    返回严格的 JSON 对象格式。
    
    格式：
    {"annual_twh": 120.5, "estimated_gw": 13.7, "kwh_price": 0.13, "source": "IEA 2024"}
    """
    
    try:
        data = await fetch_with_orchestrator(prompt, TaskType.SIMPLE_QUERY, "grid")
        
        if data:
            with open(GRID_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"[{datetime.now()}] ✅ Grid Load data updated")
        else:
            print(f"[{datetime.now()}] ⚠️  Failed to fetch grid load data")
            
    except Exception as e:
        print(f"[{datetime.now()}] ❌ Grid Load Fetch Error: {e}")


def save_daily_history(gpu_data, token_data, grid_data):
    """Save daily snapshot to history file."""
    today_str = datetime.now().strftime('%Y-%m-%d')
    
    entry = {
        "date": today_str,
        "timestamp": datetime.now().isoformat(),
        "gpu_prices": gpu_data,
        "token_prices": token_data,
        "grid_load": grid_data
    }
    
    history = []
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                history = json.load(f)
        except:
            pass
    
    updated = False
    for i, item in enumerate(history):
        if item.get('date') == today_str:
            history[i] = entry
            updated = True
            break
    
    if not updated:
        history.append(entry)
        
    try:
        with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(history, f, indent=2, ensure_ascii=False)
        print(f"[{datetime.now()}] ✅ Daily history saved")
    except Exception as e:
        print(f"[{datetime.now()}] ❌ History save error: {e}")


async def run_all_fetches():
    """Run all fetch tasks with AI Orchestrator."""
    print(f"\n{'='*80}")
    print(f"[{datetime.now()}] 🚀 Starting AI Orchestrator-powered data fetch")
    print(f"{'='*80}\n")
    
    print("📊 Current AI Model Confidence Scores:")
    for task_type in [TaskType.PRICE_EXTRACTION, TaskType.SIMPLE_QUERY]:
        scores = orchestrator.get_confidence_scores(task_type)
        if scores:
            print(f"\n  {task_type.value}:")
            for model, score in sorted(scores.items(), key=lambda x: x[1], reverse=True):
                print(f"    • {model}: {score:.3f}")
    print()
    
    await fetch_gpu_prices()
    await fetch_token_prices()
    await fetch_grid_load()
    
    gpu_data = []
    token_data = []
    grid_data = {}
    
    try:
        if os.path.exists(GPU_FILE):
            with open(GPU_FILE, 'r', encoding='utf-8') as f:
                gpu_data = json.load(f)
        if os.path.exists(TOKEN_FILE):
            with open(TOKEN_FILE, 'r', encoding='utf-8') as f:
                token_data = json.load(f)
        if os.path.exists(GRID_FILE):
            with open(GRID_FILE, 'r', encoding='utf-8') as f:
                grid_data = json.load(f)
    except Exception as e:
        print(f"[{datetime.now()}] ⚠️  Error reading files: {e}")
        
    save_daily_history(gpu_data, token_data, grid_data)
    
    print(f"\n{'='*80}")
    print("📈 AI Orchestrator Performance Report")
    print(f"{'='*80}\n")
    
    for model_name in ["qwen", "deepseek"]:
        report = orchestrator.get_performance_report(model_name=model_name)
        if report.get('total_records', 0) > 0:
            print(f"{model_name}:")
            print(f"  • Requests: {report['total_records']}")
            print(f"  • Accuracy: {report['accuracy']:.1%}")
            print(f"  • Avg Time: {report['avg_response_time']:.2f}s")
            print(f"  • Total Cost: ${report['total_cost']:.4f}")
            print()
    
    print(f"{'='*80}")
    print(f"[{datetime.now()}] ✅ All tasks completed")
    print(f"{'='*80}\n")


if __name__ == "__main__":
    if os.getenv('GITHUB_ACTIONS') == 'true' or (len(sys.argv) > 1 and sys.argv[1] == '--once'):
        print(f"[{datetime.now()}] Running single fetch with AI Orchestrator...")
        asyncio.run(run_all_fetches())
        sys.exit(0)

    print(f"[{datetime.now()}] AI Orchestrator service started")
    print(f"[{datetime.now()}] Running initial fetch...")
    asyncio.run(run_all_fetches())
    
    while True:
        now = datetime.now()
        next_run = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        seconds_until = (next_run - now).total_seconds()
        
        print(f"[{datetime.now()}] 💤 Sleeping until {next_run} ({seconds_until/3600:.1f} hours)...")
        time.sleep(seconds_until)
        
        asyncio.run(run_all_fetches())
