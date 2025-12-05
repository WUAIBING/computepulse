#!/usr/bin/env python3
"""Test Doubao API - NVIDIA financial report analysis with web search"""

import os
import requests
import json
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
        response = requests.post(url, headers=headers, json=payload, timeout=180)
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
            
            # Get usage stats
            usage = res_json.get('usage', {})
            
            return {
                'success': True,
                'message': message_text,
                'usage': usage,
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
print("豆包 AI - 英伟达财报分析测试")
print("=" * 80)

# Prompt for NVIDIA financial analysis
prompt = """请联网搜索并分析以下内容：

1. 英伟达（NVIDIA）最新财报数据（最近发布的季度财报）
   重点关注：
   - 数据中心业务收入和同比增长
   - GPU 销售数据和市场份额
   - AI 芯片（H100, H200, Blackwell GB200）的出货量和价格信息
   - 未来业务展望和新产品规划

2. 基于最新财报数据，分析并推测：
   - H100 GPU 当前的市场供需状况
   - H100 SXM5 和 PCIe 版本的当前合理价格区间
   - GPU 云租赁价格趋势（美元/小时）
   - 未来 GPU 价格走势预测

请以结构化的方式呈现分析结果，包括：
- 财报关键数据（营收、增长率、市场份额）
- 价格分析（采购价、租赁价、市场价）
- 市场趋势判断（供需平衡、竞争格局、技术迭代）

要求：
- 必须基于最新数据（自动获取当前时间）
- 明确标注数据来源和发布时间
- 如果某些数据不可得，请说明并基于已知信息合理推测"""

print("\n📊 查询内容：")
print("-" * 80)
print(prompt)
print("-" * 80)

print("\n🔍 正在联网搜索英伟达财报数据...")
print("⏳ 这可能需要 1-2 分钟，请耐心等待...\n")

result = call_doubao_with_search(prompt)

if result['success']:
    print("✅ 查询成功！\n")
    print("=" * 80)
    print("📈 豆包分析结果：")
    print("=" * 80)
    print(result['message'])
    print("=" * 80)
    
    print(f"\n📊 Token 使用统计：")
    usage = result['usage']
    print(f"  输入 tokens: {usage.get('input_tokens', 0):,}")
    print(f"  输出 tokens: {usage.get('output_tokens', 0):,}")
    print(f"  总计 tokens: {usage.get('total_tokens', 0):,}")
    
else:
    print("❌ 查询失败")
    print(f"错误信息: {result.get('error', 'Unknown error')}")

print("\n" + "=" * 80)
