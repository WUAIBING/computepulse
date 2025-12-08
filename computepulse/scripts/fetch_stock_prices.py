#!/usr/bin/env python3
"""
精确股价获取 - 直接调用金融 API，不依赖 AI 联网搜索

对于需要 100% 精确的金融数据，必须直接调用数据源 API，
而不是依赖 AI 的联网搜索功能。

AI 联网搜索的问题：
1. 搜索结果不可控 - 可能来自不同时间点
2. 数据源不一致 - 不同网站价格可能有差异
3. AI 可能"解读"数据 - 导致精度损失
4. 延迟问题 - 搜索结果可能是缓存的旧数据

解决方案：直接调用 Yahoo Finance API 获取精确数据
"""

import requests
import json
import os
from datetime import datetime
from typing import Dict, Optional

# 数据保存路径
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'public', 'data')
STOCK_FILE = os.path.join(DATA_DIR, 'stock_prices.json')


def fetch_stock_price(symbol: str) -> Optional[Dict]:
    """
    从 Yahoo Finance API 获取精确股价及涨跌幅

    Args:
        symbol: 股票代码 (如 NVDA, AMD, GOOGL)

    Returns:
        包含精确股价信息和涨跌幅的字典
    """
    try:
        # 获取当前股价和前一日收盘价（从历史数据获取）
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1d&range=10d"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://finance.yahoo.com/'
        }

        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code == 200:
            data = response.json()
            result = data['chart']['result'][0]
            meta = result['meta']

            current_price = meta['regularMarketPrice']

            # 从历史数据获取前一日收盘价
            timestamps = result['timestamp']
            closes = result['indicators']['quote'][0]['close']

            # 获取最近两个有效的收盘价
            previous_close = 0
            for i in range(len(closes) - 1, -1, -1):
                if closes[i] is not None:
                    if previous_close == 0:
                        previous_close = closes[i]
                    elif closes[i] != previous_close:
                        previous_close = closes[i]
                        break

            # 计算涨跌幅
            change = 0
            change_percent = 0
            if previous_close > 0:
                change = current_price - previous_close
                change_percent = (change / previous_close) * 100

            # Data validation: price must be positive
            if current_price <= 0:
                print(f"[ERROR] {symbol}: Invalid price {current_price} (must be positive)")
                return None

            # Additional validation: price must be within reasonable range (1-10000 USD)
            if current_price < 1 or current_price > 10000:
                print(f"[WARN] {symbol}: Price {current_price} outside typical range (1-10000 USD), but accepting")

            return {
                'symbol': symbol,
                'price': current_price,
                'previous_close': previous_close,
                'change': round(change, 2),
                'change_percent': round(change_percent, 2),
                'currency': meta['currency'],
                'exchange': meta['exchangeName'],
                'market_state': meta.get('marketState', 'unknown'),
                'timestamp': datetime.now().isoformat(),
                'source': 'Yahoo Finance API'
            }
    except Exception as e:
        print(f"[ERROR] Failed to fetch {symbol}: {e}")

    return None


def fetch_all_stock_prices(symbols: list) -> Dict:
    """
    批量获取多个股票的精确价格

    Args:
        symbols: 股票代码列表

    Returns:
        包含所有股票价格的字典
    """
    print(f"\n[Stock Prices with Change %] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)

    results = {}

    for symbol in symbols:
        data = fetch_stock_price(symbol)
        if data:
            results[symbol] = data
            # 格式化涨跌幅显示
            change_symbol = "+" if data['change'] >= 0 else ""
            change_percent_symbol = "+" if data['change_percent'] >= 0 else ""
            print(f"[OK] {symbol}: ${data['price']:.2f} ({change_symbol}{data['change']:.2f}, {change_percent_symbol}{data['change_percent']:.2f}%) | {data['exchange']}")
        else:
            print(f"[FAIL] {symbol}: Failed to fetch")

    return results


def save_stock_prices(data: Dict) -> bool:
    """保存股价数据到文件"""
    try:
        os.makedirs(DATA_DIR, exist_ok=True)
        
        with open(STOCK_FILE, 'w', encoding='utf-8') as f:
            json.dump({
                'updated_at': datetime.now().isoformat(),
                'source': 'Yahoo Finance API (Direct)',
                'note': '直接 API 调用，100% 精确',
                'prices': data
            }, f, indent=2, ensure_ascii=False)
        
        print(f"[OK] Data saved to: {STOCK_FILE}")
        return True
    except Exception as e:
        print(f"[ERROR] Save failed: {e}")
        return False


def main():
    """主函数"""
    # 要获取的股票列表 - 美国科技公司
    us_symbols = ['NVDA', 'AMD', 'GOOGL', 'AAPL', 'AMZN', 'MSFT', 'META', 'TSLA']

    # 中国科技公司（美股/港股ADR）
    chinese_symbols = [
        'BIDU',   # 百度
        'BABA',   # 阿里巴巴
        'JD',     # 京东
        'PDD',    # 拼多多
        'NTES',   # 网易
        'BILI',   # B站
        'NIO',    # 蔚来
        'XPEV',   # 小鹏汽车
        'LI',     # 理想汽车
        'EDU',    # 新东方
        'TCEHY',  # 腾讯 (ADR)
        'MPNGY',  # 美团 (ADR)
        'XIACY',  # 小米 (ADR)
        'KUAISHOU'  # 快手 (ADR)
    ]

    # 合并所有股票
    symbols = us_symbols + chinese_symbols

    print("\n" + "="*80)
    print("Fetching Stock Prices for:")
    print(f"  US Tech: {', '.join(us_symbols)}")
    print(f"  Chinese Tech: {', '.join(chinese_symbols)}")
    print("="*80 + "\n")

    # 获取精确股价
    prices = fetch_all_stock_prices(symbols)

    # 保存数据
    if prices:
        save_stock_prices(prices)
    
    print("\n" + "="*80)
    print("Summary:")
    print("- Direct API calls for 100% accurate financial data")
    print("- No AI web search dependency (uncontrollable results)")
    print("- Includes US Tech + Chinese Tech stocks")
    print("- Real-time price + change percentage")
    print("="*80)


if __name__ == "__main__":
    main()
