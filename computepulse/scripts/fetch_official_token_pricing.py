#!/usr/bin/env python3
"""
官方Token价格纯爬虫脚本
100%实时数据，无任何预设值
从官方API文档/定价页面实时爬取
汇率从exchange_rate.json读取（已由其他脚本实时更新）

修改说明：
- 使用token_crawler_base.py中的PureWebCrawler基类
- 保持原有功能不变，支持爬取所有供应商
- 同时支持单个供应商爬虫脚本调用
"""

import json
import os
from datetime import datetime

try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False
    print("[ERROR] beautifulsoup4 required: pip install beautifulsoup4")

# 导入基础爬虫类
from token_crawler_base import PureWebCrawler


def main():
    """主函数：爬取所有供应商并保存数据"""
    if not BS4_AVAILABLE:
        print("[FATAL] beautifulsoup4 is required")
        print("Run: pip install beautifulsoup4")
        return

    crawler = PureWebCrawler()
    data = crawler.crawl_all()
    crawler.save(data)

    print("\n" + "=" * 60)
    print("  [DONE] Pure crawling complete - NO preset data used")
    print("=" * 60)


if __name__ == "__main__":
    main()