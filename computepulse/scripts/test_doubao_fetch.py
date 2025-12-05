#!/usr/bin/env python3
"""Test Doubao data fetching with web search"""

import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env.local')

VOLC_API_KEY = os.getenv('VOLC_API_KEY')
DOUBAO_ENDPOINT_ID = "doubao-seed-1-6-251015"

def call_doubao_with_search(prompt: str) -> str:
    """Call Doubao API with web search"""
    headers = {
        "Authorization": f"Bearer {VOLC_API_KEY}",
        "Content-Type": "application/json"
    }
    
    url = "https://ark.cn-beijing.volces.com/api/v3/responses"
    payload = {
        "model": DOUBAO_ENDPOINT_ID,
        "stream": False,
        "tools": [{"type": "web_search"}],
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
        if 'output' in res_json:
            for item in res_json['output']:
                if item.get('type') == 'message' and 'content' in item:
                    for content_item in item['content']:
                        if content_item.get('type') in ['text', 'output_text']:
                            text = content_item.get('text') or content_item.get('output_text')
                            if text:
                                return text
    return None

print("=" * 60)
print("测试豆包数据抓取（联网搜索）")
print("=" * 60)

# Test GPU prices
print("\n[1] 测试 GPU 价格抓取...")
gpu_prompt = """请联网搜索当前（2025年12月）主流GPU算力的市场价格，包括：
- NVIDIA H100 (SXM5和PCIe版本)
- NVIDIA A100
- NVIDIA L40S
- AMD MI300X

请以JSON格式返回，包含：型号、类型、价格（美元/小时）、数据来源。
如果找不到2025年的最新数据，请明确说明。"""

gpu_result = call_doubao_with_search(gpu_prompt)
if gpu_result:
    print("✓ GPU 价格结果:")
    print(gpu_result[:500] + "..." if len(gpu_result) > 500 else gpu_result)
else:
    print("✗ 获取失败")

# Test Token prices
print("\n" + "=" * 60)
print("\n[2] 测试 Token 价格抓取...")
token_prompt = """请联网搜索当前（2025年12月）主流大模型的API价格，包括：
- GPT-4
- Claude 3.5
- Gemini Pro
- 文心一言
- 通义千问

请以JSON格式返回，包含：模型名称、价格（美元/百万tokens）、数据来源。
如果找不到2025年的最新数据，请明确说明。"""

token_result = call_doubao_with_search(token_prompt)
if token_result:
    print("✓ Token 价格结果:")
    print(token_result[:500] + "..." if len(token_result) > 500 else token_result)
else:
    print("✗ 获取失败")

print("\n" + "=" * 60)
print("测试完成")
print("=" * 60)
