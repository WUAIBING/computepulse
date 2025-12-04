#!/usr/bin/env python3
"""Test if Doubao can automatically detect current real-world time"""

import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env.local')

VOLC_API_KEY = os.getenv('VOLC_API_KEY')
DOUBAO_ENDPOINT_ID = "doubao-seed-1-6-251015"

def call_doubao_with_search(prompt: str) -> dict:
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
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        if response.status_code == 200:
            res_json = response.json()
            
            # Extract message content
            message_text = None
            if 'output' in res_json:
                for item in res_json['output']:
                    if item.get('type') == 'message' and 'content' in item:
                        for content_item in item['content']:
                            if content_item.get('type') in ['text', 'output_text']:
                                message_text = content_item.get('text') or content_item.get('output_text')
                                break
            
            return {
                'success': True,
                'message': message_text,
                'status_code': response.status_code
            }
        else:
            return {
                'success': False,
                'error': f"Status {response.status_code}: {response.text}",
                'status_code': response.status_code
            }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

print("=" * 80)
print("测试豆包的时间感知能力")
print("=" * 80)

# Test 1: Simple time query
print("\n[测试 1] 简单时间查询")
print("-" * 80)
prompt1 = "请告诉我现在是几年几月几日？"
print(f"提问：{prompt1}")
print("正在查询...\n")

result1 = call_doubao_with_search(prompt1)
if result1['success']:
    print(f"回答：{result1['message']}\n")
else:
    print(f"错误：{result1.get('error')}\n")

# Test 2: Search with implicit time
print("=" * 80)
print("\n[测试 2] 隐式时间搜索（不明确说明时间）")
print("-" * 80)
prompt2 = "请搜索英伟达最新财报数据"
print(f"提问：{prompt2}")
print("正在搜索...\n")

result2 = call_doubao_with_search(prompt2)
if result2['success']:
    print(f"回答：{result2['message'][:500]}...")
else:
    print(f"错误：{result2.get('error')}")

print("\n" + "=" * 80)
print("测试完成")
print("=" * 80)
