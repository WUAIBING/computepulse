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
    从 Yahoo Finance API 获取精确股价
    
    Args:
        symbol: 股票代码 (如 NVDA, AMD, GOOGL)
        
    Returns:
        包含精确股价信息的字典
    """
    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1d&range=1d"
        headers = {'User-Agent': 'Mozilla/5.0'}
        
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            result = data['chart']['result'][0]
            meta = result['meta']
            
            return {
                'symbol': symbol,
                'price': meta['regularMarketPrice'],
                'currency': meta['currency'],
                'exchange': meta['exchangeName'],
                'market_state': meta.get('marketState', 'unknown'),
                'timestamp': datetime.now().isoformat(),
                'source': 'Yahoo Finance API'
            }
    except Exception as e:
        print(f"❌ 获取 {symbol} 股价失败: {e}")
    
    return None


def fetch_all_stock_prices(symbols: list) -> Dict:
    """
    批量获取多个股票的精确价格
    
    Args:
        symbols: 股票代码列表
        
    Returns:
        包含所有股票价格的字典
    """
    print(f"\n📊 获取精确股价 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    results = {}
    
    for symbol in symbols:
        data = fetch_stock_price(symbol)
        if data:
            results[symbol] = data
            print(f"✅ {symbol}: ${data['price']:.2f} ({data['exchange']})")
        else:
            print(f"❌ {symbol}: 获取失败")
    
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
        
        print(f"\n✅ 数据已保存到: {STOCK_FILE}")
        return True
    except Exception as e:
        print(f"❌ 保存失败: {e}")
        return False


def main():
    """主函数"""
    # 要获取的股票列表
    symbols = ['NVDA', 'AMD', 'GOOGL', 'AAPL', 'AMZN', 'MSFT', 'META', 'TSLA']
    
    # 获取精确股价
    prices = fetch_all_stock_prices(symbols)
    
    # 保存数据
    if prices:
        save_stock_prices(prices)
    
    print("\n" + "="*60)
    print("结论：")
    print("- 对于需要 100% 精确的金融数据，直接调用 API")
    print("- 不要依赖 AI 联网搜索，因为搜索结果不可控")
    print("- AI 联网搜索适合获取趋势、新闻等非精确数据")
    print("="*60)


if __name__ == "__main__":
    main()
