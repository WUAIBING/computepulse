#!/usr/bin/env python3
"""
提取DeepSeek页面中的价格信息
"""

import requests
import re
import sys
import io

# 设置UTF-8编码
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def extract_prices_from_text(text):
    """从文本中提取价格信息"""
    print("=== 详细价格搜索 ===")

    # 查找价格模式及其上下文
    price_patterns = [
        r'(\$?\d+\.?\d*\s*(?:USD|CNY|¥|per|/)?)',  # 基础价格模式
        r'(?:price|pricing|成本|费用)[:\s]*(\$?\d+\.?\d*)',  # 价格关键词
        r'(?:input|输入|输出|output)[^$]*(\$\d+\.?\d*)',  # 输入输出价格
    ]

    # 搜索美元价格及其上下文
    usd_contexts = []
    for match in re.finditer(r'(\$\s*\d+[.,]?\d*)', text):
        start = max(0, match.start() - 100)
        end = min(len(text), match.end() + 100)
        context = text[start:end].replace('\n', ' ').replace('\r', ' ')
        usd_contexts.append((match.group(), context))

    print(f"找到 {len(usd_contexts)} 个美元价格上下文:")
    for price, context in usd_contexts[:10]:  # 只显示前10个
        print(f"  价格: {price}")
        print(f"  上下文: ...{context}...")
        print()

    # 搜索包含"price"的行
    print("\n=== 包含'price'的行 ===")
    lines = text.split('\n')
    price_lines = []
    for i, line in enumerate(lines):
        if 'price' in line.lower():
            price_lines.append((i, line.strip()))

    for line_num, line in price_lines[:10]:
        print(f"  行 {line_num}: {line}")

    return usd_contexts

def main():
    url = 'https://api-docs.deepseek.com/quick_start/pricing/'

    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        resp = requests.get(url, timeout=10, headers=headers)

        print(f"URL: {url}")
        print(f"状态码: {resp.status_code}")
        print(f"内容长度: {len(resp.text)}")

        # 提取价格
        prices = extract_prices_from_text(resp.text)

        if not prices:
            print("\n=== 尝试查找隐藏价格 ===")
            # 查找可能是价格的数字序列
            number_patterns = re.findall(r'\b\d+\.?\d*\b', resp.text)
            # 过滤掉明显的非价格数字（年份、版本号等）
            potential_prices = []
            for num in number_patterns:
                if '.' in num and float(num) < 100:  # 可能是价格（小于100的小数）
                    # 检查周围字符
                    idx = resp.text.find(num)
                    start = max(0, idx - 30)
                    end = min(len(resp.text), idx + 30)
                    context = resp.text[start:end].replace('\n', ' ')
                    if any(keyword in context.lower() for keyword in ['token', 'input', 'output', 'per', 'million', 'k']):
                        potential_prices.append((num, context))

            print(f"找到 {len(potential_prices)} 个潜在价格:")
            for num, context in potential_prices[:10]:
                print(f"  数字: {num}")
                print(f"  上下文: ...{context}...")
                print()

        # 显示页面片段以了解结构
        print("\n=== 页面片段 (位置 1000-2000) ===")
        print(resp.text[1000:2000])

    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()