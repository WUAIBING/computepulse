#!/usr/bin/env python3
"""Simple test for Doubao API - chat/completions only"""

import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env.local')

VOLC_API_KEY = os.getenv('VOLC_API_KEY')
DOUBAO_ENDPOINT_ID = "doubao-seed-1-6-251015"

print("=" * 60)
print("Doubao API Simple Test")
print("=" * 60)
print(f"\nAPI Key: {VOLC_API_KEY[:10]}...{VOLC_API_KEY[-4:]}")
print(f"Endpoint: {DOUBAO_ENDPOINT_ID}")

headers = {
    "Authorization": f"Bearer {VOLC_API_KEY}",
    "Content-Type": "application/json"
}

# Test: chat/completions API with reasoning_effort
print("\n[Test] chat/completions API with reasoning_effort='low'...")
url = "https://ark.cn-beijing.volces.com/api/v3/chat/completions"
payload = {
    "model": DOUBAO_ENDPOINT_ID,
    "reasoning_effort": "low",
    "messages": [
        {
            "role": "system", 
            "content": "You are a helpful assistant with access to current market data. Provide accurate and up-to-date pricing information."
        },
        {
            "role": "user", 
            "content": "请提供当前NVIDIA H100 GPU的市场价格信息，包括不同版本（SXM5和PCIe）的价格范围"
        }
    ],
    "temperature": 0.1
}

try:
    print("\n发送请求...")
    response = requests.post(url, headers=headers, json=payload, timeout=60)
    print(f"状态码: {response.status_code}")
    
    if response.status_code == 200:
        print("✓ 成功!")
        res_json = response.json()
        
        if 'choices' in res_json and len(res_json['choices']) > 0:
            content = res_json['choices'][0]['message']['content']
            print(f"\n回复内容:\n{content}")
            
            # Check if reasoning_content exists
            if 'reasoning_content' in res_json['choices'][0]['message']:
                reasoning = res_json['choices'][0]['message']['reasoning_content']
                print(f"\n思考过程:\n{reasoning[:200]}...")
        else:
            print(f"响应结构: {list(res_json.keys())}")
    else:
        print(f"✗ 错误: {response.status_code}")
        print(f"错误信息: {response.text}")
        
except Exception as e:
    print(f"✗ 异常: {e}")

print("\n" + "=" * 60)
