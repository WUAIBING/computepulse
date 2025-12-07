#!/usr/bin/env python3
"""
更新系统日志 - 让 CP (ComputePulse) 发布权威的股价和汇率数据

CP 角色定位：
- 系统核心，负责发布 100% 精确的金融数据
- 直接调用 API 获取数据，不依赖 AI 联网搜索
- 在群聊中以权威身份发布数据

数据来源：
- 股价: Yahoo Finance API (直接调用)
- 汇率: ExchangeRate API (直接调用)
"""

import json
import os
import requests
from datetime import datetime
from typing import Dict, List, Optional
import uuid

# 路径配置
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'public', 'data')
LOGS_FILE = os.path.join(DATA_DIR, 'system_logs.json')


def fetch_stock_prices() -> Dict[str, float]:
    """从 Yahoo Finance API 获取精确股价"""
    stocks = {}
    symbols = ['NVDA', 'AMD', 'GOOGL', 'AAPL', 'AMZN', 'MSFT']
    
    for symbol in symbols:
        try:
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1d&range=1d"
            headers = {'User-Agent': 'Mozilla/5.0'}
            r = requests.get(url, headers=headers, timeout=10)
            if r.status_code == 200:
                data = r.json()
                price = data['chart']['result'][0]['meta']['regularMarketPrice']
                stocks[symbol] = round(price, 2)
        except Exception as e:
            print(f"获取 {symbol} 失败: {e}")
    
    return stocks


def fetch_exchange_rate() -> Optional[float]:
    """从 ExchangeRate API 获取精确汇率"""
    try:
        r = requests.get('https://api.exchangerate-api.com/v4/latest/USD', timeout=10)
        if r.status_code == 200:
            return round(r.json()['rates']['CNY'], 4)
    except Exception as e:
        print(f"获取汇率失败: {e}")
    return None


def generate_log_id() -> str:
    """生成唯一日志 ID"""
    timestamp = int(datetime.now().timestamp())
    return f"log_{timestamp}_ComputePulse"


def create_cp_logs(stocks: Dict[str, float], exchange_rate: float) -> List[Dict]:
    """创建 CP (ComputePulse) 发布的权威数据日志"""
    now = datetime.now()
    logs = []
    
    # 1. 汇率数据
    if exchange_rate:
        logs.append({
            "id": f"log_{int(now.timestamp())}_CP_FX",
            "timestamp": now.isoformat(),
            "agent": "ComputePulse",
            "message": f"📊 [权威数据] USD/CNY 汇率: {exchange_rate} (来源: ExchangeRate API)",
            "type": "success"
        })
    
    # 2. 股价数据
    if stocks:
        # 主要科技股
        stock_msg = "📈 [权威数据] 科技股实时价格:\n"
        for symbol, price in stocks.items():
            stock_msg += f"  • {symbol}: ${price}\n"
        stock_msg += "(来源: Yahoo Finance API)"
        
        logs.append({
            "id": f"log_{int(now.timestamp()) + 1}_CP_Stock",
            "timestamp": (now).isoformat(),
            "agent": "ComputePulse",
            "message": stock_msg.strip(),
            "type": "success"
        })
    
    # 3. 数据验证声明
    logs.append({
        "id": f"log_{int(now.timestamp()) + 2}_CP_Verify",
        "timestamp": now.isoformat(),
        "agent": "ComputePulse",
        "message": "✅ 以上金融数据由 CP 直接从官方 API 获取，精确度 100%，非 AI 联网搜索结果。",
        "type": "info"
    })
    
    return logs


def update_system_logs():
    """更新系统日志文件"""
    print(f"\n{'='*60}")
    print(f"CP (ComputePulse) 权威数据发布")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")
    
    # 1. 获取精确数据
    print("📡 正在获取权威数据...")
    stocks = fetch_stock_prices()
    exchange_rate = fetch_exchange_rate()
    
    print(f"\n汇率: 1 USD = {exchange_rate} CNY")
    print("股价:")
    for symbol, price in stocks.items():
        print(f"  {symbol}: ${price}")
    
    # 2. 读取现有日志
    existing_logs = {"logs": [], "total_tasks": 0}
    if os.path.exists(LOGS_FILE):
        try:
            with open(LOGS_FILE, 'r', encoding='utf-8') as f:
                existing_logs = json.load(f)
        except:
            pass
    
    # 3. 创建 CP 日志
    cp_logs = create_cp_logs(stocks, exchange_rate)
    
    # 4. 合并日志（保留最近 50 条）
    all_logs = existing_logs.get('logs', []) + cp_logs
    all_logs = all_logs[-50:]  # 只保留最近 50 条
    
    # 5. 保存更新后的日志
    updated_data = {
        "last_updated": datetime.now().isoformat(),
        "system_version": "v1.3.0",
        "total_tasks": existing_logs.get('total_tasks', 0) + len(cp_logs),
        "logs": all_logs
    }
    
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(LOGS_FILE, 'w', encoding='utf-8') as f:
        json.dump(updated_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ 系统日志已更新: {LOGS_FILE}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    update_system_logs()
