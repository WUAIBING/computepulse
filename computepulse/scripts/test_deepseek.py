#!/usr/bin/env python3
"""Test DeepSeek model via Alibaba Cloud DashScope API"""

import os
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env.local')

# 初始化OpenAI客户端（使用阿里云百炼 API）
client = OpenAI(
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
)

print("=" * 80)
print("DeepSeek 模型测试（通过阿里云百炼 API）")
print("=" * 80)

# Test 1: Web search capability
print("\n[测试 1] 联网搜索能力测试")
print("-" * 80)
print("查询：英伟达最新财报数据\n")

try:
    completion = client.chat.completions.create(
        model="deepseek-v3.2-exp",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "请搜索英伟达（NVIDIA）最新财报数据，重点关注数据中心业务收入和 GPU 销售情况。"}
        ],
        extra_body={"enable_search": True}  # 开启联网搜索
    )
    
    print("✓ 搜索成功！\n")
    print("回复内容：")
    print(completion.choices[0].message.content)
    print("\n")
    
except Exception as e:
    print(f"✗ 错误: {e}\n")

# Test 2: Web search + thinking mode
print("=" * 80)
print("\n[测试 2] 联网搜索 + 思考模式")
print("-" * 80)
print("查询：H100 GPU 当前市场价格\n")

try:
    completion2 = client.chat.completions.create(
        model="deepseek-v3.2-exp",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "请搜索当前主流云服务商的 NVIDIA H100 GPU 租赁价格（每小时美元），并以 JSON 格式返回。"}
        ],
        extra_body={
            "enable_search": True,      # 开启联网搜索
            "enable_thinking": True     # 开启思考模式
        },
        stream=True,
        stream_options={"include_usage": True}
    )
    
    reasoning_content = ""
    answer_content = ""
    is_answering = False
    
    print("思考过程：\n")
    
    for chunk in completion2:
        if not chunk.choices:
            print("\n\nToken 消耗：")
            print(chunk.usage)
            continue
        
        delta = chunk.choices[0].delta
        
        # 收集思考内容
        if hasattr(delta, "reasoning_content") and delta.reasoning_content is not None:
            if not is_answering:
                print(delta.reasoning_content, end="", flush=True)
            reasoning_content += delta.reasoning_content
        
        # 收集回复内容
        if hasattr(delta, "content") and delta.content:
            if not is_answering:
                print("\n\n回复内容：\n")
                is_answering = True
            print(delta.content, end="", flush=True)
            answer_content += delta.content
    
    print("\n")
    
except Exception as e:
    print(f"✗ 错误: {e}\n")

# Test 3: Token price query
print("=" * 80)
print("\n[测试 3] Token 价格查询")
print("-" * 80)
print("查询：主流大模型 API 价格\n")

try:
    completion3 = client.chat.completions.create(
        model="deepseek-v3.2-exp",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "请搜索以下大模型的最新 API 价格（每百万 tokens）：GPT-4o, Claude 3.5, Gemini 1.5 Pro, Qwen-Max, DeepSeek-V3"}
        ],
        extra_body={"enable_search": True}
    )
    
    print("✓ 搜索成功！\n")
    print("回复内容：")
    print(completion3.choices[0].message.content)
    print("\n")
    
except Exception as e:
    print(f"✗ 错误: {e}\n")

print("=" * 80)
print("测试完成")
print("=" * 80)
