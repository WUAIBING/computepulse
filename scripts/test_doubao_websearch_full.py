#!/usr/bin/env python3
"""Test Doubao API with web search - extract full response"""

import os
import requests
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env.local')

VOLC_API_KEY = os.getenv('VOLC_API_KEY')
DOUBAO_ENDPOINT_ID = "doubao-seed-1-6-251015"

print("=" * 60)
print("Doubao 联网搜索测试 - 完整回复")
print("=" * 60)

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
            "content": [
                {
                    "type": "input_text",
                    "text": "请联网搜索2025年12月最新的NVIDIA H100 GPU市场价格，包括SXM5和PCIe版本的当前价格。要求必须是2025年的最新数据，不要2024年的旧数据。"
                }
            ]
        }
    ]
}

try:
    print("\n发送请求...")
    response = requests.post(url, headers=headers, json=payload, timeout=120)
    
    if response.status_code == 200:
        print("✓ 成功!\n")
        res_json = response.json()
        
        # Extract message content
        if 'output' in res_json:
            print(f"Output 项数: {len(res_json['output'])}\n")
            
            for i, item in enumerate(res_json['output']):
                item_type = item.get('type')
                print(f"[{i+1}] Type: {item_type}")
                
                if item_type == 'message':
                    if 'content' in item:
                        print(f"    Content 项数: {len(item['content'])}")
                        for j, content_item in enumerate(item['content']):
                            content_type = content_item.get('type')
                            print(f"    [{j+1}] Content Type: {content_type}")
                            
                            if content_type in ['text', 'output_text']:
                                text = content_item.get('text', '') or content_item.get('output_text', '')
                                print("\n" + "=" * 60)
                                print("豆包回复（联网搜索结果）:")
                                print("=" * 60)
                                print(text)
                                print("=" * 60 + "\n")
        
        # Show usage stats
        if 'usage' in res_json:
            usage = res_json['usage']
            print(f"\n使用统计:")
            print(f"  输入 tokens: {usage.get('input_tokens', 0)}")
            print(f"  输出 tokens: {usage.get('output_tokens', 0)}")
            print(f"  总计 tokens: {usage.get('total_tokens', 0)}")
        
    else:
        print(f"✗ 错误: {response.status_code}")
        print(f"错误信息: {response.text}")
        
except Exception as e:
    print(f"✗ 异常: {type(e).__name__}: {e}")

print("\n" + "=" * 60)
