#!/usr/bin/env python3
"""Quick test for Doubao API with detailed error logging"""

import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env.local')

VOLC_API_KEY = os.getenv('VOLC_API_KEY')
DOUBAO_ENDPOINT_ID = "doubao-seed-1-6-251015"

print("=" * 60)
print("Doubao API Search Test with Detailed Error Logging")
print("=" * 60)
print(f"\nAPI Key: {VOLC_API_KEY[:10]}...{VOLC_API_KEY[-4:]}")
print(f"Endpoint: {DOUBAO_ENDPOINT_ID}")

headers = {
    "Authorization": f"Bearer {VOLC_API_KEY}",
    "Content-Type": "application/json"
}

# Test 1: responses API with web search
print("\n[Test 1] responses API with web_search...")
url = "https://ark.cn-beijing.volces.com/api/v3/responses"
payload = {
    "model": DOUBAO_ENDPOINT_ID,
    "stream": False,
    "tools": [{"type": "web_search"}],
    "input": [
        {
            "role": "user",
            "content": [{"type": "input_text", "text": "请搜索当前NVIDIA H100 GPU的市场价格"}]
        }
    ]
}

try:
    response = requests.post(url, headers=headers, json=payload, timeout=30)
    print(f"Status Code: {response.status_code}")
    print(f"Response Headers: {dict(response.headers)}")
    print(f"Response Body: {response.text[:500]}")
    
    if response.status_code == 200:
        print("✓ Success!")
        res_json = response.json()
        print(f"Response structure: {list(res_json.keys())}")
    else:
        print(f"✗ Error: {response.status_code}")
        
except Exception as e:
    print(f"✗ Exception: {e}")

# Test 2: chat/completions API
print("\n[Test 2] chat/completions API...")
url2 = "https://ark.cn-beijing.volces.com/api/v3/chat/completions"
payload2 = {
    "model": DOUBAO_ENDPOINT_ID,
    "reasoning_effort": "low",
    "messages": [
        {"role": "user", "content": "请搜索当前NVIDIA H100 GPU的市场价格"}
    ]
}

try:
    response2 = requests.post(url2, headers=headers, json=payload2, timeout=30)
    print(f"Status Code: {response2.status_code}")
    print(f"Response Body: {response2.text[:500]}")
    
    if response2.status_code == 200:
        print("✓ Success!")
    else:
        print(f"✗ Error: {response2.status_code}")
        
except Exception as e:
    print(f"✗ Exception: {e}")

print("\n" + "=" * 60)
