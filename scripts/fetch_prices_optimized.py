#!/usr/bin/env python3
"""
Optimized price fetching script with improved error handling,
data validation, and merge logic.

Data Sources:
1. Qwen (通义千问) - Fast, reliable, with search
2. DeepSeek - Fast, with reasoning mode
3. Doubao (豆包) - Optional, slow but has web_search tool
"""

import dashscope
import json
import os
import sys
import time
import requests
from datetime import datetime, timedelta
from dashscope import Generation
from openai import OpenAI
from typing import List, Dict, Optional, Any

# Set API Keys
dashscope.api_key = os.getenv('DASHSCOPE_API_KEY')
volc_api_key = os.getenv('VOLC_API_KEY') or os.getenv('VITE_VOLC_API_KEY')

# Try to load from .env.local if not in env
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

# Initialize DeepSeek client (via Alibaba Cloud DashScope)
deepseek_client = None
if dashscope.api_key:
    try:
        deepseek_client = OpenAI(
            api_key=dashscope.api_key,
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        )
    except Exception as e:
        print(f"[{datetime.now()}] Warning: Failed to initialize DeepSeek client: {e}")

DOUBAO_ENDPOINT_ID = "doubao-seed-1-6-251015"  # Confirmed from API example
ENABLE_DOUBAO = False  # Disabled by default due to slow response time

# Data validation thresholds
GPU_PRICE_MIN = 0.1  # Minimum reasonable GPU price per hour (USD)
GPU_PRICE_MAX = 50.0  # Maximum reasonable GPU price per hour (USD)
TOKEN_PRICE_MIN = 0.001  # Minimum reasonable token price per 1M (USD)
TOKEN_PRICE_MAX = 100.0  # Maximum reasonable token price per 1M (USD)
KWH_PRICE_MIN = 0.01  # Minimum reasonable electricity price (USD/kWh)
KWH_PRICE_MAX = 1.0  # Maximum reasonable electricity price (USD/kWh)

def get_doubao_endpoint():
    """Get Doubao endpoint ID with caching."""
    global DOUBAO_ENDPOINT_ID
    if DOUBAO_ENDPOINT_ID:
        return DOUBAO_ENDPOINT_ID
        
    if not volc_api_key:
        return None
        
    try:
        url = "https://ark.cn-beijing.volces.com/api/v3/inference_endpoints?page_num=1&page_size=20"
        headers = {"Authorization": f"Bearer {volc_api_key}"}
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if 'items' in data:
                for item in data['items']:
                    if item.get('status') == 'Running':
                        model_ref = item.get('model_reference', {}).get('model_id', '').lower()
                        if 'doubao' in model_ref:
                            DOUBAO_ENDPOINT_ID = item['id']
                            print(f"[{datetime.now()}] Found Doubao Endpoint: {DOUBAO_ENDPOINT_ID}")
                            return DOUBAO_ENDPOINT_ID
                            
                # Fallback to first running endpoint
                for item in data['items']:
                    if item.get('status') == 'Running':
                        DOUBAO_ENDPOINT_ID = item['id']
                        print(f"[{datetime.now()}] Using fallback Endpoint: {DOUBAO_ENDPOINT_ID}")
                        return DOUBAO_ENDPOINT_ID
                        
        print(f"[{datetime.now()}] Warning: No active Doubao endpoint found.")
    except Exception as e:
        print(f"[{datetime.now()}] Error fetching Doubao endpoint: {e}")
    return None

def call_doubao_with_search(prompt: str, max_retries: int = 2, reasoning_effort: str = "low") -> Optional[str]:
    """
    Call Doubao API with web search enabled using responses API.
    Includes retry logic for better reliability.
    
    Args:
        prompt: The prompt to send to the API
        max_retries: Maximum number of retry attempts
        reasoning_effort: Not used for responses API (only chat/completions supports it)
    """
    endpoint_id = DOUBAO_ENDPOINT_ID or get_doubao_endpoint()
    if not endpoint_id:
        return None
    
    headers = {
        "Authorization": f"Bearer {volc_api_key}",
        "Content-Type": "application/json"
    }
    
    for attempt in range(max_retries):
        try:
            # Use responses API with web_search tool for real-time data
            url = "https://ark.cn-beijing.volces.com/api/v3/responses"
            payload = {
                "model": endpoint_id,
                "stream": False,
                "tools": [{"type": "web_search"}],  # Enable web search
                "input": [
                    {
                        "role": "user",
                        "content": [{"type": "input_text", "text": prompt}]
                    }
                ]
            }
            
            response = requests.post(url, headers=headers, json=payload, timeout=120)
            if response.status_code == 200:
                res_json = response.json()
                # Extract message content from output
                if 'output' in res_json:
                    for item in res_json['output']:
                        if item.get('type') == 'message' and 'content' in item:
                            for content_item in item['content']:
                                # Handle both 'text' and 'output_text' types
                                if content_item.get('type') in ['text', 'output_text']:
                                    text = content_item.get('text') or content_item.get('output_text')
                                    if text:
                                        return text
            
            if response.status_code != 200:
                print(f"[{datetime.now()}] Doubao API Error (attempt {attempt+1}): {response.status_code}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                    
        except Exception as e:
            print(f"[{datetime.now()}] Doubao Call Failed (attempt {attempt+1}): {e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
    
    return None

def call_qwen_with_search(prompt: str, max_retries: int = 2) -> Optional[str]:
    """
    Call Qwen API with search enabled.
    Includes retry logic for better reliability.
    """
    for attempt in range(max_retries):
        try:
            response = Generation.call(
                model='qwen-max',
                prompt=prompt,
                enable_search=True
            )
            if response.status_code == 200:
                return response.output.text
            else:
                print(f"[{datetime.now()}] Qwen API Error (attempt {attempt+1}): {response.message}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
        except Exception as e:
            print(f"[{datetime.now()}] Qwen Call Failed (attempt {attempt+1}): {e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
    
    return None

def call_deepseek_with_reasoning(prompt: str, max_retries: int = 2) -> Optional[str]:
    """
    Call DeepSeek API with reasoning mode enabled.
    Uses OpenAI-compatible API via Alibaba Cloud DashScope.
    Includes retry logic for better reliability.
    """
    if not deepseek_client:
        return None
    
    for attempt in range(max_retries):
        try:
            completion = deepseek_client.chat.completions.create(
                model="deepseek-v3.2-exp",
                messages=[{"role": "user", "content": prompt}],
                extra_body={"enable_thinking": False},  # Disable thinking for faster response
                stream=False,
            )
            
            if completion.choices and len(completion.choices) > 0:
                return completion.choices[0].message.content
            else:
                print(f"[{datetime.now()}] DeepSeek API Error (attempt {attempt+1}): No response")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                    
        except Exception as e:
            print(f"[{datetime.now()}] DeepSeek Call Failed (attempt {attempt+1}): {e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
    
    return None

def clean_and_parse_json(content: Optional[str]) -> Optional[Any]:
    """Parse JSON from LLM response with better error handling."""
    if not content:
        return None
    
    try:
        # Remove markdown code blocks
        cleaned = content.replace('```json', '').replace('```', '').strip()
        
        # Extract JSON structure
        if '[' in cleaned and ']' in cleaned:
            start = cleaned.find('[')
            end = cleaned.rfind(']') + 1
            cleaned = cleaned[start:end]
        elif '{' in cleaned and '}' in cleaned:
            start = cleaned.find('{')
            end = cleaned.rfind('}') + 1
            cleaned = cleaned[start:end]
        else:
            print(f"[{datetime.now()}] No JSON structure found in response")
            return None
            
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        print(f"[{datetime.now()}] JSON Parse Error: {e}")
        print(f"Content snippet: {content[:200] if content else 'None'}")
        return None
    except Exception as e:
        print(f"[{datetime.now()}] Unexpected error parsing JSON: {e}")
        return None

def validate_gpu_price(item: Dict) -> bool:
    """Validate GPU price data."""
    required_fields = ['provider', 'gpu', 'price']
    
    # Check required fields
    for field in required_fields:
        if field not in item:
            print(f"[{datetime.now()}] Missing required field '{field}' in GPU data")
            return False
    
    # Validate price range
    price = item.get('price', 0)
    if not isinstance(price, (int, float)):
        print(f"[{datetime.now()}] Invalid price type for {item.get('provider')}: {type(price)}")
        return False
    
    if not (GPU_PRICE_MIN <= price <= GPU_PRICE_MAX):
        print(f"[{datetime.now()}] Price out of range for {item.get('provider')}: ${price}")
        return False
    
    return True

def validate_token_price(item: Dict) -> bool:
    """Validate token price data."""
    required_fields = ['provider', 'model', 'input_price', 'output_price']
    
    # Check required fields
    for field in required_fields:
        if field not in item:
            print(f"[{datetime.now()}] Missing required field '{field}' in token data")
            return False
    
    # Validate price ranges (allow None for missing data, but filter them out)
    for price_field in ['input_price', 'output_price']:
        price = item.get(price_field)
        
        # Skip items with null prices
        if price is None:
            print(f"[{datetime.now()}] Null {price_field} for {item.get('model')}, skipping")
            return False
        
        if not isinstance(price, (int, float)):
            print(f"[{datetime.now()}] Invalid {price_field} type for {item.get('model')}")
            return False
        
        if not (TOKEN_PRICE_MIN <= price <= TOKEN_PRICE_MAX):
            print(f"[{datetime.now()}] {price_field} out of range for {item.get('model')}: ${price}")
            return False
    
    return True

def validate_grid_data(data: Dict) -> bool:
    """Validate grid load data."""
    if not isinstance(data, dict):
        return False
    
    # Check kWh price if present
    if 'kwh_price' in data:
        price = data['kwh_price']
        if not isinstance(price, (int, float)):
            return False
        if not (KWH_PRICE_MIN <= price <= KWH_PRICE_MAX):
            print(f"[{datetime.now()}] kWh price out of range: ${price}")
            return False
    
    return True

def merge_data_improved(
    qwen_data: Optional[Any],
    deepseek_data: Optional[Any],
    doubao_data: Optional[Any],
    existing_data: Optional[Any],
    key_func: Optional[callable] = None
) -> Any:
    """
    Improved merge logic that properly handles existing data.
    
    Priority: DeepSeek > Qwen > Doubao > Existing data
    (DeepSeek has reasoning mode, Qwen is fast and reliable, Doubao is slow)
    """
    # Handle dict type (for grid load)
    if isinstance(deepseek_data, dict) or isinstance(qwen_data, dict) or isinstance(doubao_data, dict) or isinstance(existing_data, dict):
        merged = {}
        if isinstance(existing_data, dict):
            merged.update(existing_data)
        if isinstance(doubao_data, dict):
            merged.update(doubao_data)
        if isinstance(qwen_data, dict):
            merged.update(qwen_data)
        if isinstance(deepseek_data, dict):
            merged.update(deepseek_data)  # DeepSeek has highest priority
        return merged if merged else existing_data
    
    # Handle list type (for GPU and token prices)
    if not key_func:
        # Default key function
        key_func = lambda x: f"{x.get('provider', '')}_{x.get('model', '')}_{x.get('gpu', '')}"
    
    # Initialize with existing data
    merged_dict = {}
    if isinstance(existing_data, list):
        for item in existing_data:
            key = key_func(item)
            merged_dict[key] = item
    
    # Add/update with Doubao data (lowest priority of new data)
    if isinstance(doubao_data, list):
        for item in doubao_data:
            key = key_func(item)
            if key not in merged_dict:
                merged_dict[key] = item
    
    # Add/update with Qwen data
    if isinstance(qwen_data, list):
        for item in qwen_data:
            key = key_func(item)
            merged_dict[key] = item
    
    # Add/update with DeepSeek data (highest priority)
    if isinstance(deepseek_data, list):
        for item in deepseek_data:
            key = key_func(item)
            merged_dict[key] = item
    
    return list(merged_dict.values()) if merged_dict else (existing_data or [])

# Define paths
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'public', 'data')
os.makedirs(DATA_DIR, exist_ok=True)

GPU_FILE = os.path.join(DATA_DIR, 'gpu_prices.json')
TOKEN_FILE = os.path.join(DATA_DIR, 'token_prices.json')
GRID_FILE = os.path.join(DATA_DIR, 'grid_load.json')
HISTORY_FILE = os.path.join(DATA_DIR, 'history_data.json')

def fetch_gpu_prices():
    """Fetch GPU prices with improved error handling and validation."""
    prompt = """
    请使用联网搜索功能完成以下任务：
    
    1. 搜索英伟达（NVIDIA）最新财报数据，重点关注：
       - H100/H200/Blackwell GPU 的价格信息
       - 数据中心业务收入和增长趋势
       - GPU 出货量和市场供需状况
    
    2. 搜索当前主流云服务商的 GPU 租赁价格（每小时美元）
    
    目标 GPU 型号：
    - NVIDIA: H100, H200, A100, L40S, Blackwell GB200
    - 中国 AI 芯片: 华为昇腾 Ascend 910B, 寒武纪 MLU370, 海光 DCU
    
    云服务商：
    - 国际: Lambda Labs, RunPod, Vast.ai, CoreWeave, AWS, Google Cloud, Azure
    - 中国: 阿里云, 腾讯云, 百度智能云, 火山引擎, 华为云, 商汤
    
    请基于最新财报数据和实际市场价格，返回 JSON 数组格式（人民币按 7.2 汇率换算为美元）：
    [
      {"provider": "Lambda", "region": "US-West", "gpu": "H100", "price": 2.13},
      {"provider": "Aliyun", "region": "China", "gpu": "Ascend 910B", "price": 1.85}
    ]
    
    要求：
    - 只返回 JSON 数组，不要包含 Markdown 标记或解释文字
    - 必须基于最新数据（自动获取当前时间）
    - 如果找不到确切的租赁价格，可以基于财报数据和市场趋势合理推测
    """

    try:
        print(f"[{datetime.now()}] Fetching GPU prices...")
        
        # Fetch from multiple sources with retry
        qwen_content = call_qwen_with_search(prompt)
        deepseek_content = call_deepseek_with_reasoning(prompt)
        doubao_content = call_doubao_with_search(prompt) if ENABLE_DOUBAO else None
        
        # Parse responses
        qwen_data = clean_and_parse_json(qwen_content)
        deepseek_data = clean_and_parse_json(deepseek_content)
        doubao_data = clean_and_parse_json(doubao_content) if doubao_content else None
        
        # Validate data
        if isinstance(qwen_data, list):
            qwen_data = [item for item in qwen_data if validate_gpu_price(item)]
        if isinstance(deepseek_data, list):
            deepseek_data = [item for item in deepseek_data if validate_gpu_price(item)]
        if isinstance(doubao_data, list):
            doubao_data = [item for item in doubao_data if validate_gpu_price(item)]
        
        # Load existing data
        existing_data = []
        if os.path.exists(GPU_FILE):
            try:
                with open(GPU_FILE, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
            except Exception as e:
                print(f"[{datetime.now()}] Error loading existing GPU data: {e}")
        
        # Merge with improved logic
        key_func = lambda x: f"{x.get('provider', '')}_{x.get('region', '')}_{x.get('gpu', '')}"
        final_data = merge_data_improved(qwen_data, deepseek_data, doubao_data, existing_data, key_func)
        
        if final_data and len(final_data) > 0:
            with open(GPU_FILE, 'w', encoding='utf-8') as f:
                json.dump(final_data, f, indent=2, ensure_ascii=False)
            qwen_count = len(qwen_data) if qwen_data else 0
            deepseek_count = len(deepseek_data) if deepseek_data else 0
            doubao_count = len(doubao_data) if doubao_data else 0
            print(f"[{datetime.now()}] GPU Prices updated: {len(final_data)} records (Qwen: {qwen_count}, DeepSeek: {deepseek_count}, Doubao: {doubao_count})")
        else:
            print(f"[{datetime.now()}] No valid GPU price data fetched, keeping existing data")

    except Exception as e:
        print(f"[{datetime.now()}] GPU Fetch Error: {e}")

def fetch_token_prices():
    """Fetch token prices with improved error handling and validation."""
    prompt = """
    请使用联网搜索功能查找以下大模型 API 的最新官方定价：
    
    目标模型：
    - 国际: OpenAI (GPT-4o, GPT-4o-mini, o1), Anthropic (Claude 3.5 Sonnet), Google (Gemini 2.0, Gemini 1.5 Pro), Meta (Llama 3)
    - 中国: 阿里云 (Qwen/通义千问), 百度 (Ernie/文心一言), 智谱 (GLM-4), 月之暗面 (Kimi), 字节跳动 (Doubao/豆包), MiniMax, DeepSeek
    
    请搜索每个模型的官方定价页面，获取每 1M (一百万) Token 的输入和输出价格。
    
    返回 JSON 数组格式（人民币按 7.2 汇率换算为美元）：
    [
      {"provider": "OpenAI", "model": "GPT-4o", "input_price": 5.0, "output_price": 15.0},
      {"provider": "Aliyun", "model": "Qwen-Max", "input_price": 0.55, "output_price": 1.66}
    ]
    
    要求：
    - 只返回 JSON 数组，不要包含 Markdown 标记或解释文字
    - 必须基于最新官方定价（自动获取当前时间）
    - 价格单位：美元/百万 tokens
    """
    
    try:
        print(f"[{datetime.now()}] Fetching Token prices...")
        
        # Fetch from multiple sources
        qwen_content = call_qwen_with_search(prompt)
        deepseek_content = call_deepseek_with_reasoning(prompt)
        doubao_content = call_doubao_with_search(prompt) if ENABLE_DOUBAO else None
        
        # Parse responses
        qwen_data = clean_and_parse_json(qwen_content)
        deepseek_data = clean_and_parse_json(deepseek_content)
        doubao_data = clean_and_parse_json(doubao_content) if doubao_content else None
        
        # Validate data
        if isinstance(qwen_data, list):
            qwen_data = [item for item in qwen_data if validate_token_price(item)]
        if isinstance(deepseek_data, list):
            deepseek_data = [item for item in deepseek_data if validate_token_price(item)]
        if isinstance(doubao_data, list):
            doubao_data = [item for item in doubao_data if validate_token_price(item)]
        
        # Load existing data
        existing_data = []
        if os.path.exists(TOKEN_FILE):
            try:
                with open(TOKEN_FILE, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
            except Exception as e:
                print(f"[{datetime.now()}] Error loading existing token data: {e}")
        
        # Merge with improved logic
        key_func = lambda x: f"{x.get('provider', '')}_{x.get('model', '')}"
        final_data = merge_data_improved(qwen_data, deepseek_data, doubao_data, existing_data, key_func)
        
        if final_data and len(final_data) > 0:
            with open(TOKEN_FILE, 'w', encoding='utf-8') as f:
                json.dump(final_data, f, indent=2, ensure_ascii=False)
            qwen_count = len(qwen_data) if qwen_data else 0
            deepseek_count = len(deepseek_data) if deepseek_data else 0
            doubao_count = len(doubao_data) if doubao_data else 0
            print(f"[{datetime.now()}] Token Prices updated: {len(final_data)} records (Qwen: {qwen_count}, DeepSeek: {deepseek_count}, Doubao: {doubao_count})")
        else:
            print(f"[{datetime.now()}] No valid token price data fetched, keeping existing data")
            
    except Exception as e:
        print(f"[{datetime.now()}] Token Fetch Error: {e}")

def fetch_grid_load():
    """Fetch grid load data with improved error handling and validation."""
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
    
    务必只输出 JSON 格式，不要包含任何 Markdown 代码块标记，也不要包含任何解释性文字。

    示例：
    {"annual_twh": 120.5, "estimated_gw": 13.7, "kwh_price": 0.13, "source": "IEA 2024 Report", "active_gpu_est": 3500000}
    """
    
    try:
        print(f"[{datetime.now()}] Fetching Grid Load data...")
        
        # Fetch from multiple sources
        qwen_content = call_qwen_with_search(prompt)
        deepseek_content = call_deepseek_with_reasoning(prompt)
        doubao_content = call_doubao_with_search(prompt) if ENABLE_DOUBAO else None
        
        # Parse responses
        qwen_data = clean_and_parse_json(qwen_content)
        deepseek_data = clean_and_parse_json(deepseek_content)
        doubao_data = clean_and_parse_json(doubao_content) if doubao_content else None
        
        # Validate data
        if qwen_data and not validate_grid_data(qwen_data):
            qwen_data = None
        if deepseek_data and not validate_grid_data(deepseek_data):
            deepseek_data = None
        if doubao_data and not validate_grid_data(doubao_data):
            doubao_data = None
        
        # Load existing data
        existing_data = {}
        if os.path.exists(GRID_FILE):
            try:
                with open(GRID_FILE, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
            except Exception as e:
                print(f"[{datetime.now()}] Error loading existing grid data: {e}")
        
        # Merge with improved logic
        final_data = merge_data_improved(qwen_data, deepseek_data, doubao_data, existing_data)
        
        if final_data:
            with open(GRID_FILE, 'w', encoding='utf-8') as f:
                json.dump(final_data, f, indent=2, ensure_ascii=False)
            print(f"[{datetime.now()}] Grid Load data updated")
        else:
            print(f"[{datetime.now()}] No valid grid load data fetched, keeping existing data")

    except Exception as e:
        print(f"[{datetime.now()}] Grid Load Fetch Error: {e}")

def fetch_annual_energy_history():
    """Fetch historical annual AI energy consumption data from 2018-2024."""
    prompt = """
    请使用联网搜索功能，查找全球AI数据中心的历史年度能耗数据。
    
    搜索要求：
    1. 获取2018年至2024年每年的全球AI数据中心总能耗（单位：TWh太瓦时）
    2. 2018年是AI大规模应用的起点，从这一年开始统计
    3. 搜索权威来源：IEA（国际能源署）、BloombergNEF、学术研究报告等
    4. 如果某年数据缺失，可以基于趋势合理估算
    
    请返回一个 JSON 数组，包含每年的数据：
    [
      {"year": "2018", "value": 15.2, "source": "IEA Report"},
      {"year": "2019", "value": 22.5, "source": "BloombergNEF"},
      {"year": "2020", "value": 35.8, "source": "Academic Study"},
      {"year": "2021", "value": 52.3, "source": "IEA Report"},
      {"year": "2022", "value": 68.7, "source": "BloombergNEF"},
      {"year": "2023", "value": 85.4, "source": "IEA Report"},
      {"year": "2024", "value": 120.0, "source": "Forecast"}
    ]
    
    要求：
    - 只返回 JSON 数组，不要包含 Markdown 标记或解释文字
    - value 单位为 TWh（太瓦时）
    - 必须包含2018-2024年的完整数据
    - 数据应该呈现增长趋势，符合AI行业发展规律
    """
    
    try:
        print(f"[{datetime.now()}] Fetching Annual Energy History data...")
        
        # Fetch from multiple sources
        qwen_content = call_qwen_with_search(prompt)
        deepseek_content = call_deepseek_with_reasoning(prompt)
        doubao_content = call_doubao_with_search(prompt) if ENABLE_DOUBAO else None
        
        # Parse responses
        qwen_data = clean_and_parse_json(qwen_content)
        deepseek_data = clean_and_parse_json(deepseek_content)
        doubao_data = clean_and_parse_json(doubao_content) if doubao_content else None
        
        # Validate data (should be a list with year and value)
        def validate_annual_data(data):
            if not isinstance(data, list) or len(data) == 0:
                return False
            for item in data:
                if not isinstance(item, dict):
                    return False
                if 'year' not in item or 'value' not in item:
                    return False
                if not isinstance(item['value'], (int, float)) or item['value'] <= 0:
                    return False
            return True
        
        if qwen_data and not validate_annual_data(qwen_data):
            qwen_data = None
        if deepseek_data and not validate_annual_data(deepseek_data):
            deepseek_data = None
        if doubao_data and not validate_annual_data(doubao_data):
            doubao_data = None
        
        # Load existing data
        annual_file = os.path.join(DATA_DIR, 'annual_energy.json')
        existing_data = []
        if os.path.exists(annual_file):
            try:
                with open(annual_file, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
            except Exception as e:
                print(f"[{datetime.now()}] Error loading existing annual data: {e}")
        
        # Merge with improved logic (prefer DeepSeek > Qwen > Doubao > Existing)
        final_data = deepseek_data or qwen_data or doubao_data or existing_data
        
        if final_data and len(final_data) > 0:
            # Sort by year
            final_data = sorted(final_data, key=lambda x: x['year'])
            
            with open(annual_file, 'w', encoding='utf-8') as f:
                json.dump(final_data, f, indent=2, ensure_ascii=False)
            print(f"[{datetime.now()}] Annual Energy History updated: {len(final_data)} years")
        else:
            print(f"[{datetime.now()}] No valid annual energy data fetched, keeping existing data")

    except Exception as e:
        print(f"[{datetime.now()}] Annual Energy Fetch Error: {e}")

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
        except Exception as e:
            print(f"[{datetime.now()}] Error reading history file: {e}")
    
    # Update or append today's entry
    updated = False
    for i, item in enumerate(history):
        if item.get('date') == today_str:
            history[i] = entry
            updated = True
            break
    
    if not updated:
        history.append(entry)
    
    # Keep only last 90 days
    if len(history) > 90:
        history = history[-90:]
        
    try:
        with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(history, f, indent=2, ensure_ascii=False)
        print(f"[{datetime.now()}] Daily history saved ({len(history)} days)")
    except Exception as e:
        print(f"[{datetime.now()}] Error saving history: {e}")

def validate_and_fix_with_doubao(gpu_data: List[Dict], token_data: List[Dict]) -> tuple:
    """
    Use Doubao to validate and fix data quality issues.
    Doubao acts as both a data quality checker and fixer.
    
    Returns:
        tuple: (fixed_gpu_data, fixed_token_data, reports)
    """
    if not volc_api_key:
        print(f"[{datetime.now()}] Doubao validation skipped: API key not configured")
        return gpu_data, token_data, {}
    
    print(f"[{datetime.now()}] Starting Doubao data validation and fixing...")
    
    try:
        # Import validation module
        import sys
        sys.path.append(os.path.dirname(__file__))
        from data_validator import validate_gpu_prices, validate_token_prices, fix_anomalies
        
        reports = {}
        fixed_gpu_data = gpu_data.copy()
        fixed_token_data = token_data.copy()
        
        # Validate and fix GPU prices
        gpu_report = validate_gpu_prices(gpu_data)
        if 'error' not in gpu_report:
            reports['gpu'] = gpu_report
            
            # Save validation report
            report_file = os.path.join(DATA_DIR, 'validation_report_gpu.json')
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(gpu_report, f, indent=2, ensure_ascii=False)
            print(f"[{datetime.now()}] GPU validation report saved")
            
            # Auto-fix anomalies
            if 'anomalies' in gpu_report and len(gpu_report['anomalies']) > 0:
                print(f"[{datetime.now()}] ⚠️  Found {len(gpu_report['anomalies'])} GPU price anomalies")
                
                # Attempt to fix
                fixed_gpu_data, fix_summary = fix_anomalies(gpu_data, gpu_report['anomalies'], 'gpu')
                
                if fix_summary['fixed'] > 0:
                    print(f"[{datetime.now()}] ✅ Auto-fixed {fix_summary['fixed']} GPU records")
                    print(f"[{datetime.now()}] 🗑️  Removed {fix_summary['removed']} invalid GPU records")
                    
                    # Save fixed data
                    with open(GPU_FILE, 'w', encoding='utf-8') as f:
                        json.dump(fixed_gpu_data, f, indent=2, ensure_ascii=False)
                    print(f"[{datetime.now()}] Fixed GPU data saved")
                
                # Log remaining issues
                for anomaly in gpu_report['anomalies'][:3]:
                    severity = anomaly.get('severity', 'unknown')
                    emoji = '🔴' if severity == 'high' else '🟡' if severity == 'medium' else '🟢'
                    print(f"  {emoji} {anomaly.get('provider')} {anomaly.get('gpu')}: {anomaly.get('issue')}")
        
        # Validate and fix Token prices
        token_report = validate_token_prices(token_data)
        if 'error' not in token_report:
            reports['token'] = token_report
            
            report_file = os.path.join(DATA_DIR, 'validation_report_token.json')
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(token_report, f, indent=2, ensure_ascii=False)
            print(f"[{datetime.now()}] Token validation report saved")
            
            # Auto-fix anomalies
            if 'anomalies' in token_report and len(token_report['anomalies']) > 0:
                print(f"[{datetime.now()}] ⚠️  Found {len(token_report['anomalies'])} Token price anomalies")
                
                fixed_token_data, fix_summary = fix_anomalies(token_data, token_report['anomalies'], 'token')
                
                if fix_summary['fixed'] > 0:
                    print(f"[{datetime.now()}] ✅ Auto-fixed {fix_summary['fixed']} Token records")
                    print(f"[{datetime.now()}] 🗑️  Removed {fix_summary['removed']} invalid Token records")
                    
                    # Save fixed data
                    with open(TOKEN_FILE, 'w', encoding='utf-8') as f:
                        json.dump(fixed_token_data, f, indent=2, ensure_ascii=False)
                    print(f"[{datetime.now()}] Fixed Token data saved")
                
                for anomaly in token_report['anomalies'][:3]:
                    severity = anomaly.get('severity', 'unknown')
                    emoji = '🔴' if severity == 'high' else '🟡' if severity == 'medium' else '🟢'
                    print(f"  {emoji} {anomaly.get('provider')} {anomaly.get('model')}: {anomaly.get('issue')}")
        
        print(f"[{datetime.now()}] Doubao validation and fixing completed")
        return fixed_gpu_data, fixed_token_data, reports
        
    except Exception as e:
        print(f"[{datetime.now()}] Doubao validation error: {e}")
        return gpu_data, token_data, {}

def run_all_fetches():
    """Run all fetch tasks."""
    print(f"[{datetime.now()}] Starting daily fetch task...")
    
    fetch_gpu_prices()
    fetch_token_prices()
    fetch_grid_load()
    fetch_annual_energy_history()
    
    # Load data for history and validation
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
        print(f"[{datetime.now()}] Error reading fetched files for history: {e}")
    
    # Run Doubao validation and auto-fix
    if gpu_data or token_data:
        fixed_gpu_data, fixed_token_data, reports = validate_and_fix_with_doubao(gpu_data, token_data)
        
        # Update data if fixes were applied
        if fixed_gpu_data != gpu_data:
            gpu_data = fixed_gpu_data
        if fixed_token_data != token_data:
            token_data = fixed_token_data
        
    save_daily_history(gpu_data, token_data, grid_data)
    print(f"[{datetime.now()}] All tasks completed.")

if __name__ == "__main__":
    if os.getenv('GITHUB_ACTIONS') == 'true' or (len(sys.argv) > 1 and sys.argv[1] == '--once'):
        print(f"[{datetime.now()}] Running single fetch task...")
        run_all_fetches()
        sys.exit(0)

    print(f"[{datetime.now()}] Service started. Running initial fetch...")
    run_all_fetches()
    
    while True:
        now = datetime.now()
        next_run = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        seconds_until = (next_run - now).total_seconds()
        print(f"[{datetime.now()}] Sleeping until {next_run}...")
        
        time.sleep(seconds_until)
        run_all_fetches()
