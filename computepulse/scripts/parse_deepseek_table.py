#!/usr/bin/env python3
"""
解析DeepSeek定价表格
"""

import requests
from bs4 import BeautifulSoup
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def parse_table_structure(url):
    """解析表格结构"""
    headers = {'User-Agent': 'Mozilla/5.0'}
    resp = requests.get(url, timeout=10, headers=headers)
    soup = BeautifulSoup(resp.text, 'html.parser')

    print("=== 查找所有表格 ===")
    tables = soup.find_all('table')
    print(f"找到 {len(tables)} 个表格")

    for table_idx, table in enumerate(tables):
        print(f"\n--- 表格 {table_idx} ---")

        # 获取表格属性
        table_attrs = dict(table.attrs)
        print(f"表格属性: {table_attrs}")

        # 解析行
        rows = table.find_all('tr')
        print(f"行数: {len(rows)}")

        for row_idx, row in enumerate(rows):
            print(f"\n  行 {row_idx}:")

            # 获取行属性
            row_attrs = dict(row.attrs)
            if row_attrs:
                print(f"    行属性: {row_attrs}")

            # 解析单元格
            cells = row.find_all(['td', 'th'])
            print(f"    单元格数: {len(cells)}")

            for cell_idx, cell in enumerate(cells):
                cell_text = cell.get_text(strip=True)
                cell_attrs = dict(cell.attrs)

                # 检查是否有rowspan或colspan
                rowspan = cell_attrs.get('rowspan', '1')
                colspan = cell_attrs.get('colspan', '1')

                print(f"      单元格 {cell_idx}: '{cell_text}'")
                if rowspan != '1' or colspan != '1':
                    print(f"        属性: rowspan={rowspan}, colspan={colspan}")

                # 检查是否有价格信息
                if '$' in cell_text:
                    print(f"        ★ 包含价格: {cell_text}")
                elif any(price_term in cell_text.lower() for price_term in ['price', 'token', 'input', 'output']):
                    print(f"        ☆ 价格相关: {cell_text}")

        # 尝试提取表格数据为结构化格式
        print(f"\n--- 表格 {table_idx} 结构化数据 ---")
        extract_structured_data(table)

def extract_structured_data(table):
    """提取结构化数据"""
    data = []
    rows = table.find_all('tr')

    for row in rows:
        row_data = []
        cells = row.find_all(['td', 'th'])

        for cell in cells:
            cell_text = cell.get_text(strip=True)
            # 清理文本
            cell_text = cell_text.replace('\xa0', ' ').replace('\n', ' ').strip()
            row_data.append(cell_text)

        if row_data:
            data.append(row_data)

    # 打印表格数据
    for i, row in enumerate(data):
        print(f"  行 {i}: {row}")

    return data

def find_pricing_section(soup):
    """查找定价部分"""
    print("\n=== 查找定价相关部分 ===")

    # 查找包含"PRICING"的文本
    pricing_elements = []
    for element in soup.find_all(['div', 'section', 'article', 'p', 'h1', 'h2', 'h3', 'h4']):
        text = element.get_text(strip=True)
        if 'pricing' in text.lower() and len(text) < 200:
            pricing_elements.append((element.name, text))

    print(f"找到 {len(pricing_elements)} 个定价相关元素:")
    for tag, text in pricing_elements[:10]:
        print(f"  <{tag}>: {text}")

    # 查找所有包含美元符号的文本
    print("\n=== 包含美元符号的文本 ===")
    all_text = soup.get_text()
    lines = all_text.split('\n')
    dollar_lines = []

    for line in lines:
        line = line.strip()
        if '$' in line and len(line) < 200:
            dollar_lines.append(line)

    print(f"找到 {len(dollar_lines)} 行包含美元符号:")
    for line in dollar_lines[:20]:
        print(f"  {line}")

def main():
    url = 'https://api-docs.deepseek.com/quick_start/pricing/'

    print(f"分析URL: {url}")

    headers = {'User-Agent': 'Mozilla/5.0'}
    resp = requests.get(url, timeout=10, headers=headers)
    soup = BeautifulSoup(resp.text, 'html.parser')

    # 1. 解析表格结构
    parse_table_structure(url)

    # 2. 查找定价部分
    find_pricing_section(soup)

    # 3. 尝试简单的价格提取
    print("\n=== 简单价格提取 ===")
    all_text = soup.get_text()

    # 查找价格模式
    import re
    price_patterns = re.findall(r'(\$?\d+\.?\d*)\s*(?:per\s*)?(?:1M\s*)?(?:tokens?|TOKENS?|input|output|INPUT|OUTPUT|cache|CACHE)', all_text, re.IGNORECASE)
    print(f"价格模式匹配: {price_patterns}")

    # 查找完整的定价行
    pricing_lines = []
    for line in all_text.split('\n'):
        line = line.strip()
        if ('$' in line and ('token' in line.lower() or 'input' in line.lower() or 'output' in line.lower())):
            pricing_lines.append(line)

    print(f"\n定价行 ({len(pricing_lines)} 行):")
    for line in pricing_lines[:10]:
        print(f"  {line}")

if __name__ == "__main__":
    main()