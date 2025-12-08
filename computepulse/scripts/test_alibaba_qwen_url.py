#!/usr/bin/env python3
"""
测试阿里巴巴QWEN定价页面的可访问性
URL: https://bailian.console.aliyun.com/?tab=model#/model-market/detail/qwen3-vl-plus
"""

import requests
from bs4 import BeautifulSoup
import sys

def test_url_accessibility(url):
    """测试URL可访问性"""
    print(f"测试URL: {url}")

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

    try:
        resp = requests.get(url, headers=headers, timeout=15)
        print(f"状态码: {resp.status_code}")
        print(f"内容长度: {len(resp.text)} 字符")

        if resp.status_code == 200:
            # 检查页面内容
            soup = BeautifulSoup(resp.text, 'html.parser')

            # 检查是否有登录页面提示
            page_title = soup.title.string if soup.title else "无标题"
            print(f"页面标题: {page_title}")

            # 检查是否有价格相关信息
            page_text = resp.text.lower()
            price_keywords = ['price', 'pricing', '成本', '费用', '元', '¥', '￥', 'token', 'tokens']
            found_keywords = [kw for kw in price_keywords if kw in page_text]

            print(f"找到的关键词: {found_keywords}")

            # 检查是否有登录提示
            login_indicators = ['login', 'sign in', '登录', '账号', 'password', '阿里云']
            login_found = [ind for ind in login_indicators if ind in page_text]

            if login_found:
                print(f"登录相关词汇: {login_found}")
                print("⚠️  页面可能需要登录")

            # 提取前500字符内容预览
            print("\n页面内容预览 (前500字符):")
            print(resp.text[:500])

        elif resp.status_code == 403 or resp.status_code == 401:
            print("❌ 访问被拒绝（可能需要登录或身份验证）")
        elif resp.status_code == 404:
            print("❌ 页面不存在")
        else:
            print(f"❌ 访问失败: HTTP {resp.status_code}")

    except requests.exceptions.Timeout:
        print("❌ 请求超时")
    except requests.exceptions.ConnectionError:
        print("❌ 连接错误")
    except Exception as e:
        print(f"❌ 错误: {e}")

def main():
    urls = [
        "https://bailian.console.aliyun.com/?tab=model#/model-market/detail/qwen3-vl-plus",
        "https://bailian.aliyun.com/#/model-market/detail/qwen3-vl-plus",
        "https://help.aliyun.com/zh/model-studio/billing"  # 现有定价页面作为对比
    ]

    for url in urls:
        print("\n" + "="*80)
        test_url_accessibility(url)
        print("="*80 + "\n")

if __name__ == "__main__":
    main()