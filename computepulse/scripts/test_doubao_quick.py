#!/usr/bin/env python3
"""
Quick test for Doubao API with manual API key input.
"""

import requests
import json

print("=" * 60)
print("Doubao API Quick Test")
print("=" * 60)

# Prompt for API key
api_key = input("\n请输入你的 VOLC_API_KEY: ").strip()

if not api_key:
    print("❌ API Key 不能为空")
    exit(1)

print(f"\n✓ API Key: {api_key[:10]}...{api_key[-4:]}")

# Test endpoint
endpoint_id = "doubao-seed-1-6-251015"
print(f"✓ Endpoint ID: {endpoint_id}")

# Test 1: responses API with web search
print("\n[测试 1] responses API (with web_search)...")
try:
    url = "https://ark.cn-beijing.volces.com/api/v3/responses"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": endpoint_id,
        "stream": False,
        "reasoning_effort": "low",
        "tools": [{"type": "web_search"}],
        "input": [
            {
                "role": "user",
                "content": [{"type": "input_text", "text": "Hello, test"}]
            }
        ]
    }
    
    response = requests.post(url, headers=headers, json=payload, timeout=30)
    
    if response.status_code == 200:
        print("✅ responses API 工作正常!")
        result = response.json()
        if 'output' in result:
            for item in result['output']:
                if item.get('type') == 'message':
                    print(f"   响应: {item['content'][0]['text'][:100]}...")
    else:
        print(f"❌ 错误: {response.status_code}")
        print(f"   响应: {response.text[:200]}")
        
except Exception as e:
    print(f"❌ 异常: {e}")

# Test 2: chat/completions API
print("\n[测试 2] chat/completions API...")
try:
    url = "https://ark.cn-beijing.volces.com/api/v3/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": endpoint_id,
        "reasoning_effort": "low",
        "messages": [
            {"role": "user", "content": "Hello, test"}
        ],
        "max_tokens": 50
    }
    
    response = requests.post(url, headers=headers, json=payload, timeout=30)
    
    if response.status_code == 200:
        print("✅ chat/completions API 工作正常!")
        result = response.json()
        if 'choices' in result:
            print(f"   响应: {result['choices'][0]['message']['content'][:100]}...")
    else:
        print(f"❌ 错误: {response.status_code}")
        print(f"   响应: {response.text[:200]}")
        
except Exception as e:
    print(f"❌ 异常: {e}")

print("\n" + "=" * 60)
print("测试完成")
print("=" * 60)
