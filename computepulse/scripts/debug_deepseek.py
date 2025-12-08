#!/usr/bin/env python3
"""
调试DeepSeek定价页面结构
"""

import requests
import re
import sys
import io

# 设置标准输出编码为UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def test_url(url):
    """测试URL并分析页面结构"""
    print(f"测试URL: {url}")

    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        resp = requests.get(url, timeout=10, headers=headers)
        print(f"状态码: {resp.status_code}")
        print(f"内容长度: {len(resp.text)} 字符")

        # 检查常见价格模式
        print("\n=== 价格模式搜索 ===")

        # 美元价格模式
        usd_matches = re.findall(r'\$\s*\d+[.,]?\d*', resp.text)
        print(f"美元价格 ($): {len(usd_matches)} 个")
        if usd_matches:
            print(f"  样本: {usd_matches[:10]}")

        # 人民币价格模式
        cny_matches = re.findall(r'[¥￥]\s*\d+[.,]?\d*', resp.text)
        print(f"人民币价格 (¥/￥): {len(cny_matches)} 个")
        if cny_matches:
            print(f"  样本: {cny_matches[:10]}")

        # 数字价格模式（可能无货币符号）
        price_matches = re.findall(r'(?:price|价格|费用|cost|定价)[:：\s]*\d+[.,]?\d*', resp.text, re.IGNORECASE)
        print(f"价格关键词: {len(price_matches)} 个")
        if price_matches:
            print(f"  样本: {price_matches[:10]}")

        # 查找表格
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(resp.text, 'html.parser')

        print("\n=== 表格分析 ===")
        tables = soup.find_all('table')
        print(f"表格数量: {len(tables)}")

        for i, table in enumerate(tables):
            rows = table.find_all('tr')
            print(f"  表格 {i}: {len(rows)} 行")

            # 显示前几行内容
            for j, row in enumerate(rows[:5]):  # 只显示前5行
                cells = row.find_all(['td', 'th'])
                cell_texts = [cell.get_text(strip=True) for cell in cells]
                print(f"    行 {j}: {cell_texts}")

        # 查找所有包含"deepseek"的文本
        print("\n=== 包含'deepseek'的文本 ===")
        deepseek_texts = []
        for text in soup.stripped_strings:
            if 'deepseek' in text.lower():
                deepseek_texts.append(text[:200])

        print(f"找到 {len(deepseek_texts)} 个相关文本")
        for i, text in enumerate(deepseek_texts[:5]):
            print(f"  {i}: {text}")

        # 查找所有链接
        print("\n=== 页面链接 ===")
        links = soup.find_all('a', href=True)
        pricing_links = [link for link in links if 'pricing' in link['href'].lower() or 'price' in link['href'].lower()]
        print(f"定价相关链接: {len(pricing_links)} 个")
        for link in pricing_links[:5]:
            print(f"  - {link.get_text(strip=True)[:50]} -> {link['href']}")

        # 查找可能的JSON数据
        print("\n=== 可能的JSON数据 ===")
        script_tags = soup.find_all('script')
        json_like = []
        for script in script_tags:
            if script.string and ('price' in script.string.lower() or 'pricing' in script.string.lower()):
                json_like.append(script.string[:500])

        print(f"包含价格信息的script标签: {len(json_like)} 个")
        for i, json_text in enumerate(json_like[:3]):
            print(f"  Script {i} (前500字符): {json_text}")

    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # 测试两个可能的URL
    urls = [
        'https://api-docs.deepseek.com/zh-cn/quick_start/pricing/',
        'https://api-docs.deepseek.com/quick_start/pricing/',
        'https://platform.deepseek.com/pricing'
    ]

    for url in urls:
        print("\n" + "="*80)
        test_url(url)
        print("="*80 + "\n")