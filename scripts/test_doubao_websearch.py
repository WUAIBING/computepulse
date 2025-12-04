#!/usr/bin/env python3
"""Test Doubao API with web search - responses API"""

import os
import requests
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env.local')

VOLC_API_KEY = os.getenv('VOLC_API_KEY')
DOUBAO_ENDPOINT_ID = "doubao-seed-1-6-251015"

print("=" * 60)
print("Doubao API Web Search Test (responses API)")
print("=" * 60)
print(f"\nAPI Key: {VOLC_API_KEY[:10]}...{VOLC_API_KEY[-4:]}")
print(f"Endpoint: {DOUBAO_ENDPOINT_ID}")

headers = {
    "Authorization": f"Bearer {VOLC_API_KEY}",
    "Content-Type": "application/json"
}

# Test: responses API with web_search tool
print("\n[Test] responses API with web_search tool...")
url = "https://ark.cn-beijing.volces.com/api/v3/responses"

# According to Volcengine docs, use this format for web search
payload = {
    "model": DOUBAO_ENDPOINT_ID,
    "stream": False,
    "tools": [{"type": "web_search"}],  # Enable web search
    "input": [
        {
            "role": "user",
            "content": [
                {
                    "type": "input_text",
                    "text": "请联网搜索2025年12月最新的NVIDIA H100 GPU市场价格，包括SXM5和PCIe版本的当前价格"
                }
            ]
        }
    ]
}

print(f"\n请求 URL: {url}")
print(f"请求 Payload:\n{json.dumps(payload, indent=2, ensure_ascii=False)}")

try:
    print("\n发送请求...")
    response = requests.post(url, headers=headers, json=payload, timeout=120)
    print(f"状态码: {response.status_code}")
    
    if response.status_code == 200:
        print("✓ 成功!")
        res_json = response.json()
        
        print(f"\n响应结构: {list(res_json.keys())}")
        
        if 'output' in res_json:
            print(f"\nOutput 项数: {len(res_json['output'])}")
            for i, item in enumerate(res_json['output']):
                print(f"\n--- Output Item {i+1} ---")
                print(f"Type: {item.get('type')}")
                
                if item.get('type') == 'message':
                    if 'content' in item:
                        for content_item in item['content']:
                            if content_item.get('type') == 'text':
                                text = content_item.get('text', '')
                                print(f"\n回复内容:\n{text}")
                
                elif item.get('type') == 'tool_use':
                    print(f"Tool: {item.get('name')}")
                    if 'input' in item:
                        print(f"Tool Input: {item['input']}")
                
                elif item.get('type') == 'tool_result':
                    print(f"Tool ID: {item.get('tool_use_id')}")
                    if 'content' in item:
                        print(f"Tool Result (preview): {str(item['content'])[:200]}...")
        
        # Print full response for debugging
        print(f"\n完整响应:\n{json.dumps(res_json, indent=2, ensure_ascii=False)[:1000]}...")
        
    else:
        print(f"✗ 错误: {response.status_code}")
        print(f"错误信息: {response.text}")
        
except Exception as e:
    print(f"✗ 异常: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
