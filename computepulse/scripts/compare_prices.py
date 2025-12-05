import requests
import os
import json
from dashscope import Generation

# Load API Keys
volc_api_key = os.getenv('VOLC_API_KEY') or os.getenv('VITE_VOLC_API_KEY')
dashscope_api_key = os.getenv('DASHSCOPE_API_KEY') or os.getenv('VITE_DASHSCOPE_API_KEY')

# Fallback load
if not volc_api_key or not dashscope_api_key:
    try:
        with open('.env.local', 'r') as f:
            for line in f:
                if 'VOLC_API_KEY' in line:
                    volc_api_key = line.split('=')[1].strip()
                if 'DASHSCOPE_API_KEY' in line:
                    dashscope_api_key = line.split('=')[1].strip()
    except:
        pass

DOUBAO_ENDPOINT_ID = "doubao-seed-1-6-251015"

prompt = "What is the global average industrial electricity price (or data center electricity price) in 2024/2025? Please provide the value in USD/kWh and the source."

print(f"--- Comparing Electricity Price Search Results ---\n")

# 1. Qwen-Max
print(">>> querying Qwen-Max...")
qwen_result = "Failed"
try:
    response = Generation.call(model='qwen-max', prompt=prompt, enable_search=True, api_key=dashscope_api_key)
    if response.status_code == 200:
        qwen_result = response.output.text
    else:
        qwen_result = f"Error: {response.message}"
except Exception as e:
    qwen_result = f"Exception: {e}"

print(f"\n[Qwen-Max Result]:\n{qwen_result[:500]}...\n")

# 2. Doubao (Retry with 'responses' API which worked for search before)
print(">>> querying Doubao (responses API)...")
doubao_result = "Failed"
try:
    url = "https://ark.cn-beijing.volces.com/api/v3/responses"
    headers = {"Authorization": f"Bearer {volc_api_key}", "Content-Type": "application/json"}
    payload = {
        "model": DOUBAO_ENDPOINT_ID,
        "stream": False,
        "tools": [{"type": "web_search"}],
        "input": [{"role": "user", "content": [{"type": "input_text", "text": prompt}]}]
    }
    response = requests.post(url, headers=headers, json=payload, timeout=60)
    if response.status_code == 200:
        res_json = response.json()
        if 'output' in res_json:
            for item in res_json['output']:
                if item.get('type') == 'message':
                     doubao_result = item['content'][0]['text']
    else:
        doubao_result = f"Error: {response.text}"
except Exception as e:
    doubao_result = f"Exception: {e}"

print(f"\n[Doubao Result]:\n{doubao_result[:500]}...\n")

print("\n--- Comparison Analysis ---")
# Simple analysis
kwh_qwen = "N/A"
kwh_doubao = "N/A"

# Try to extract numbers roughly
import re
nums_qwen = re.findall(r'\$0\.(\d+)', qwen_result)
nums_doubao = re.findall(r'\$0\.(\d+)', doubao_result)

print(f"Detected potential prices in Qwen: {['$0.'+n for n in nums_qwen]}")
print(f"Detected potential prices in Doubao: {['$0.'+n for n in nums_doubao]}")
print("Current system uses: $0.12 (approx)")
