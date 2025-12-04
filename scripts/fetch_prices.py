
import dashscope
import json
import os
import sys
import time
import requests
from datetime import datetime, timedelta
from dashscope import Generation

# Set API Keys
dashscope.api_key = os.getenv('DASHSCOPE_API_KEY')
volc_api_key = os.getenv('VOLC_API_KEY') or os.getenv('VITE_VOLC_API_KEY')

# Try to load from .env.local if not in env (for local dev)
if not dashscope.api_key or not volc_api_key:
    try:
        with open('.env.local', 'r') as f:
            for line in f:
                if 'DASHSCOPE_API_KEY' in line:
                    dashscope.api_key = line.split('=')[1].strip()
                if 'VOLC_API_KEY' in line:
                    volc_api_key = line.split('=')[1].strip()
    except:
        pass

if not dashscope.api_key:
    print("Error: DASHSCOPE_API_KEY not found.")
    # We continue even if one key is missing, to try the other? 
    # But user wants both.
    # sys.exit(1) 

DOUBAO_ENDPOINT_ID = "doubao-seed-1-6-251015"  # Confirmed from API example

def get_doubao_endpoint():
    global DOUBAO_ENDPOINT_ID
    if DOUBAO_ENDPOINT_ID:
        return DOUBAO_ENDPOINT_ID
        
    if not volc_api_key:
        return None
        
    try:
        # Try to list endpoints to find a Doubao one
        url = "https://ark.cn-beijing.volces.com/api/v3/inference_endpoints?page_num=1&page_size=20"
        headers = {"Authorization": f"Bearer {volc_api_key}"}
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if 'items' in data:
                for item in data['items']:
                    # Look for an endpoint that is 'Running' and has 'doubao' in model name
                    if item.get('status') == 'Running':
                        model_ref = item.get('model_reference', {}).get('model_id', '').lower()
                        if 'doubao' in model_ref:
                            DOUBAO_ENDPOINT_ID = item['id']
                            print(f"[{datetime.now()}] Found Doubao Endpoint: {DOUBAO_ENDPOINT_ID} ({model_ref})")
                            return DOUBAO_ENDPOINT_ID
                            
            # If no doubao found, pick the first running one
            if 'items' in data and len(data['items']) > 0:
                for item in data['items']:
                     if item.get('status') == 'Running':
                        DOUBAO_ENDPOINT_ID = item['id']
                        print(f"[{datetime.now()}] Using fallback Endpoint: {DOUBAO_ENDPOINT_ID}")
                        return DOUBAO_ENDPOINT_ID
                        
        print(f"[{datetime.now()}] Warning: No active Doubao endpoint found for the provided API Key.")
    except Exception as e:
        print(f"[{datetime.now()}] Error fetching Doubao endpoint: {e}")
    return None

def call_doubao(prompt):
    endpoint_id = get_doubao_endpoint()
    if not endpoint_id:
        return None
        
    url = "https://ark.cn-beijing.volces.com/api/v3/chat/completions"
    headers = {
        "Authorization": f"Bearer {volc_api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": endpoint_id,
        "messages": [
            {"role": "system", "content": "You are a helpful assistant. Please search the internet if possible to provide accurate pricing data."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.1
        # Note: Ark API doesn't standardly support 'enable_search' param in top level like DashScope.
        # Search is usually configured on the endpoint/bot side. 
        # We hope the endpoint has search enabled.
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        if response.status_code == 200:
            res_json = response.json()
            return res_json['choices'][0]['message']['content']
        else:
            print(f"[{datetime.now()}] Doubao API Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"[{datetime.now()}] Doubao Call Failed: {e}")
    return None

def clean_and_parse_json(content):
    if not content: return []
    try:
        # Remove markdown
        cleaned = content.replace('```json', '').replace('```', '').strip()
        
        # Extract JSON structure
        if '[' in cleaned and ']' in cleaned:
            start = cleaned.find('[')
            end = cleaned.rfind(']') + 1
            cleaned = cleaned[start:end]
        elif '{' in cleaned and '}' in cleaned:
             # For single object (grid load)
            start = cleaned.find('{')
            end = cleaned.rfind('}') + 1
            cleaned = cleaned[start:end]
            
        return json.loads(cleaned)
    except Exception as e:
        print(f"JSON Parse Error: {e} | Content snippet: {content[:100] if content else 'None'}")
        return None

def merge_data(qwen_data, doubao_data, key_func):
    """Merge two lists of dicts based on a unique key."""
    if not qwen_data: qwen_data = []
    if not doubao_data: doubao_data = []
    
    # If data is a dict (not list), just return one or merge keys?
    # For Grid Load (dict), we prefer Qwen (search enabled) but can fallback.
    if isinstance(qwen_data, dict) and isinstance(doubao_data, dict):
        # Simple strategy: Prefer Qwen, but if Qwen missing keys, use Doubao
        merged = doubao_data.copy()
        merged.update(qwen_data)
        return merged
        
    if not isinstance(qwen_data, list) or not isinstance(doubao_data, list):
        return qwen_data if qwen_data else doubao_data

    merged = {key_func(item): item for item in qwen_data}
    
    for item in doubao_data:
        k = key_func(item)
        if k not in merged:
            merged[k] = item
        else:
            # Optional: Average the price if both found? 
            # For now, Qwen is trusted (search enabled), so we keep Qwen's version if conflict.
            pass
            
    return list(merged.values())

# Define paths relative to project root
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'public', 'data')
os.makedirs(DATA_DIR, exist_ok=True)

GPU_FILE = os.path.join(DATA_DIR, 'gpu_prices.json')
TOKEN_FILE = os.path.join(DATA_DIR, 'token_prices.json')
GRID_FILE = os.path.join(DATA_DIR, 'grid_load.json')
HISTORY_FILE = os.path.join(DATA_DIR, 'history_data.json')

def fetch_gpu_prices():
    # Define the prompt for Qwen-Max with search enabled
    prompt = """
    请使用联网搜索功能，查找当前最新的 NVIDIA H100, A100 以及中国 AI 芯片 (华为昇腾 Ascend 910B, 寒武纪 MLU370, 海光 DCU) 的云租赁价格（每小时美元，如果是人民币请按 7.2 汇率换算）。
    请优先搜索以下供应商的价格：
    - 国际: Lambda Labs, RunPod, Vast.ai, CoreWeave, AWS, Google Cloud, Azure
    - 中国: 阿里云, 腾讯云, 百度智能云, 火山引擎 (Volcengine), 华为云, 商汤 (SenseTime)
    
    请将结果整理为一个严格的 JSON 数组格式，不要包含任何 Markdown 标记（如 ```json ... ```）或额外的解释文字。
    JSON 数组中的每个对象应包含以下字段：
    - provider: 供应商名称 (字符串)
    - region: 区域 (字符串，如果未知则填 "Global")
    - gpu: GPU/芯片型号 (字符串，例如 "H100", "A100", "Ascend 910B")
    - price: 每小时价格 (数字，美元)
    
    示例格式：
    [
      {"provider": "Lambda", "region": "US-West", "gpu": "H100", "price": 2.49},
      {"provider": "Aliyun", "region": "China-Hangzhou", "gpu": "Ascend 910B", "price": 1.85}
    ]
    """

    try:
        print(f"[{datetime.now()}] Fetching GPU prices using Qwen-Max...")
        qwen_resp = None
        try:
            qwen_resp = Generation.call(model='qwen-max', prompt=prompt, enable_search=True)
            qwen_content = qwen_resp.output.text if qwen_resp.status_code == 200 else None
        except Exception as e:
            print(f"Qwen GPU Error: {e}")
            qwen_content = None

        print(f"[{datetime.now()}] Fetching GPU prices using Doubao...")
        doubao_content = call_doubao(prompt)
        
        # Parse both
        qwen_data = clean_and_parse_json(qwen_content)
        doubao_data = clean_and_parse_json(doubao_content)
        
        # Merge
        # Read existing data if available to merge with new fetch
        existing_data = []
        if os.path.exists(GPU_FILE):
            try:
                with open(GPU_FILE, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
            except: pass

        final_data = merge_data(qwen_data, doubao_data, existing_data)
        
        if final_data:
            with open(GPU_FILE, 'w', encoding='utf-8') as f:
                json.dump(final_data, f, indent=2, ensure_ascii=False)
            print(f"[{datetime.now()}] GPU Prices updated (Merged: {len(final_data)} records).")
        else:
            print(f"[{datetime.now()}] Failed to fetch/parse GPU prices from both sources.")

    except Exception as e:
        print(f"[{datetime.now()}] GPU Fetch Error: {e}")

def fetch_token_prices():
    prompt = """
    请使用联网搜索功能，查找以下大模型 API 的最新每 1M (一百万) Token 的输入和输出价格（美元，如果是人民币请按 7.2 汇率换算）：
    - 国际: OpenAI (GPT-4o), Anthropic (Claude 3.5), Google (Gemini 1.5), Meta (Llama 3)
    - 中国: 阿里云 (Qwen/通义千问), 百度 (Ernie/文心一言), 智谱 (GLM-4), 月之暗面 (Kimi), 字节跳动 (Doubao/豆包), MiniMax

    请将结果整理为一个严格的 JSON 数组格式，不要包含 Markdown。
    字段：
    - provider: 服务商 (OpenAI, Aliyun, Baidu, etc.)
    - model: 模型名称
    - input_price: 每 1M Token 输入价格 (数字, 美元)
    - output_price: 每 1M Token 输出价格 (数字, 美元)
    
    示例：
    [
      {"provider": "OpenAI", "model": "GPT-4o", "input_price": 5.0, "output_price": 15.0},
      {"provider": "Aliyun", "model": "Qwen-Max", "input_price": 0.55, "output_price": 1.66}
    ]
    """
    try:
        print(f"[{datetime.now()}] Fetching Token prices using Qwen & Doubao...")
        
        # Qwen
        qwen_content = None
        try:
            resp = Generation.call(model='qwen-max', prompt=prompt, enable_search=True)
            if resp.status_code == 200: qwen_content = resp.output.text
        except Exception as e: print(f"Qwen Token Error: {e}")
        
        # Doubao
        doubao_content = call_doubao(prompt)
        
        qwen_data = clean_and_parse_json(qwen_content)
        doubao_data = clean_and_parse_json(doubao_content)
        
        # Read existing
        existing_data = []
        if os.path.exists(TOKEN_FILE):
            try:
                with open(TOKEN_FILE, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
            except: pass

        final_data = merge_data(qwen_data, doubao_data, existing_data)
        
        if final_data:
            with open(TOKEN_FILE, 'w', encoding='utf-8') as f:
                json.dump(final_data, f, indent=2, ensure_ascii=False)
            print(f"[{datetime.now()}] Token Prices updated (Merged: {len(final_data)} records).")
    except Exception as e:
        print(f"[{datetime.now()}] Token Fetch Error: {e}")

def fetch_grid_load():
    prompt = """
    请使用联网搜索功能，查找关于"全球 AI 数据中心能耗"的最新估算数据。
    重点搜索：
    1. 2024/2025年全球 AI 总耗电量预测 (TWh) 或 实时功率 (GW)。
    2. 全球工业/数据中心平均电价 (美元/kWh)。

    请返回一个 JSON 对象，包含以下字段：
    - annual_twh: 年化总耗电量 (TWh, 数字)
    - estimated_gw: 实时预估功率 (GW, 数字, 如果搜不到可用 TWh/8.76 估算)
    - kwh_price: 全球平均电价 (美元/kWh, 数字, 例如 0.12)
    - source: 数据来源 (字符串)
    - active_gpu_est: 全球活跃 AI 芯片估算数量 (数字, 如 4000000)
    
    务必只输出 JSON 格式，不要包含任何 Markdown 代码块标记（如 ```json），也不要包含任何解释性文字。直接以 { 开始，以 } 结束。

    示例：
    {"annual_twh": 120.5, "estimated_gw": 13.7, "kwh_price": 0.13, "source": "IEA 2024 Report", "active_gpu_est": 3500000}
    """
    try:
        print(f"[{datetime.now()}] Fetching Grid Load data using Qwen & Doubao...")
        
        # Qwen
        qwen_content = None
        try:
            response = Generation.call(model='qwen-max', prompt=prompt, enable_search=True)
            if response.status_code == 200:
                qwen_content = response.output.text
        except Exception as e:
            print(f"Qwen Grid Error: {e}")

        # Doubao
        doubao_content = call_doubao(prompt)

        # Parse
        qwen_data = clean_and_parse_json(qwen_content)
        doubao_data = clean_and_parse_json(doubao_content)

        # Merge (Grid load is a single dict, so we use merge_data strategy for dicts)
        final_data = merge_data(qwen_data, doubao_data, None)

        if final_data:
            with open(GRID_FILE, 'w', encoding='utf-8') as f:
                json.dump(final_data, f, indent=2, ensure_ascii=False)
            print(f"[{datetime.now()}] Grid Load data updated.")
        else:
            print(f"[{datetime.now()}] Failed to fetch Grid Load data.")

    except Exception as e:
        print(f"[{datetime.now()}] Grid Load Fetch Error: {e}")

def save_daily_history(gpu_data, token_data, grid_data):
    """Save the daily snapshot to a history file."""
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
        except Exception as e:
            print(f"Error reading history file: {e}")
            # If corrupted, maybe backup and start new? For now, just append to empty list
    
    # Check if today already exists, update if so, else append
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
        print(f"[{datetime.now()}] Daily history saved to {HISTORY_FILE}.")
    except Exception as e:
        print(f"Error saving history: {e}")

def run_all_fetches():
    """Run all fetch tasks and return the data."""
    print(f"[{datetime.now()}] Starting daily fetch task...")
    
    # We need to modify the fetch functions to RETURN data instead of just writing files
    # But since I don't want to rewrite everything, I'll read the files back after fetching
    
    fetch_gpu_prices()
    fetch_token_prices()
    fetch_grid_load()
    
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
        print(f"Error reading fetched files for history: {e}")
        
    save_daily_history(gpu_data, token_data, grid_data)
    print(f"[{datetime.now()}] All tasks completed.")

if __name__ == "__main__":
    # When running in GitHub Actions or manually for a single fetch
    # Check if we are in a CI environment or if an argument is passed to run once
    if os.getenv('GITHUB_ACTIONS') == 'true' or (len(sys.argv) > 1 and sys.argv[1] == '--once'):
        print(f"[{datetime.now()}] Running single fetch task...")
        run_all_fetches()
        sys.exit(0)

    print(f"[{datetime.now()}] Service started. Running initial fetch...")
    run_all_fetches()
    
    while True:
        now = datetime.now()
        # Calculate seconds until next midnight (00:00:00)
        # tomorrow = now + timedelta(days=1)
        # next_run = datetime(tomorrow.year, tomorrow.month, tomorrow.day, 0, 0, 0)
        
        # Use next midnight
        next_run = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        
        seconds_until = (next_run - now).total_seconds()
        print(f"[{datetime.now()}] Sleeping for {seconds_until:.1f} seconds until next run at {next_run}...")
        
        time.sleep(seconds_until)
        
        # After waking up, run tasks
        run_all_fetches()
