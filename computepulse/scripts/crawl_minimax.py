#!/usr/bin/env python3
"""
MiniMax定价爬虫脚本
从MiniMax官方文档爬取最新价格数据
输出到共享文件：public/data/token_pricing_official.json
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False
    print("[ERROR] beautifulsoup4 required: pip install beautifulsoup4")
    sys.exit(1)

from token_crawler_base import PureWebCrawler


def main():
    """主函数：爬取MiniMax定价并保存到共享文件"""
    if not BS4_AVAILABLE:
        print("[FATAL] beautifulsoup4 is required")
        print("Run: pip install beautifulsoup4")
        return

    print("=" * 60)
    print("  MiniMax Token Pricing Crawler")
    print("=" * 60)

    crawler = PureWebCrawler()
    minimax_data = crawler.crawl_minimax()
    crawler.save_provider_data(minimax_data)

    print("\n" + "=" * 60)
    print(f"  [DONE] MiniMax pricing saved to shared file")
    print(f"  Status: {minimax_data.get('crawl_status')}")
    print(f"  Models found: {minimax_data.get('models_found', 0)}")
    print("=" * 60)


if __name__ == "__main__":
    main()