"""
Real-time Data Fetching with Enhanced Sources
实时数据抓取 - 增强版数据源

Features:
- 每小时更新GPU出货量和价格
- 实时追踪电网负载和电价
- 监控AI行业新闻和财报
- 多维度数据交叉验证
"""

import sys
import os
import json
import asyncio
from datetime import datetime, timedelta
import time

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from ai_orchestrator import AIOrchestrator, AIModel, TaskType, OrchestratorConfig

# Initialize orchestrator
config = OrchestratorConfig()
orchestrator = AIOrchestrator(config)

# Register AI models
orchestrator.register_model(AIModel(
    name="qwen", provider="Alibaba", cost_per_1m_tokens=0.6, avg_response_time=3.5
))
orchestrator.register_model(AIModel(
    name="deepseek", provider="DeepSeek", cost_per_1m_tokens=0.8, avg_response_time=5.0
))
orchestrator.register_model(AIModel(
    name="doubao", provider="Volcengine", cost_per_1m_tokens=1.2, avg_response_time=15.0
))

# Data paths
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'public', 'data')
os.makedirs(DATA_DIR, exist_ok=True)

REALTIME_DIR = os.path.join(DATA_DIR, 'realtime')
os.makedirs(REALTIME_DIR, exist_ok=True)


async def fetch_gpu_shipment_data():
    """
    抓取GPU出货量数据 - 每小时更新
    
    数据源:
    - NVIDIA财报和新闻发布
    - AMD/Intel GPU出货数据
    - 中国AI芯片厂商（华为、寒武纪等）
    - 云服务商采购公告
    """
    print(f"\n{'='*80}")
    print(f"[{datetime.now()}] 📦 Fetching GPU Shipment Data")
    print(f"{'='*80}\n")
    
    prompt = """
    请使用联网搜索功能，查找以下GPU/AI芯片的最新出货量和部署数据：
    
    1. NVIDIA GPU出货量（最近24小时）:
       - H100/H200 出货量
       - A100 出货量
       - 主要客户：Microsoft, Google, Meta, Amazon, Tesla, xAI等
    
    2. 其他厂商GPU出货:
       - AMD MI300系列
       - Intel Gaudi系列
    
    3. 中国AI芯片出货:
       - 华为昇腾910B/910C
       - 寒武纪MLU系列
       - 海光DCU
    
    4. 云服务商GPU部署:
       - AWS新增GPU数量
       - Google Cloud新增TPU/GPU
       - Azure新增GPU
       - 阿里云/腾讯云/百度云新增AI芯片
    
    请搜索最新的新闻、财报、采购公告，返回JSON格式：
    [
      {
        "timestamp": "2024-12-05T10:00:00Z",
        "vendor": "NVIDIA",
        "model": "H100",
        "shipment_count": 50000,
        "customer": "Microsoft",
        "source": "新闻来源",
        "confidence": "high/medium/low"
      }
    ]
    
    要求：
    - 只返回JSON，不要Markdown标记
    - 必须基于真实搜索结果
    - 标注数据来源和置信度
    """
    
    result = await orchestrator.process_request(
        prompt=prompt,
        context={"data_type": "gpu_shipment"},
        quality_threshold=0.7
    )
    
    # Save to file
    output_file = os.path.join(REALTIME_DIR, 'gpu_shipments.json')
    
    # Load existing data
    existing_data = []
    if os.path.exists(output_file):
        try:
            with open(output_file, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
        except:
            pass
    
    # Append new data (keep last 168 hours = 7 days)
    if isinstance(result.data, dict) and 'status' not in result.data:
        # Real data from AI
        new_entry = {
            "timestamp": datetime.now().isoformat(),
            "data": result.data,
            "models_used": result.contributing_models,
            "confidence_scores": result.confidence_scores
        }
        existing_data.append(new_entry)
        
        # Keep only last 7 days
        cutoff_time = datetime.now() - timedelta(days=7)
        existing_data = [
            entry for entry in existing_data
            if datetime.fromisoformat(entry["timestamp"]) > cutoff_time
        ]
    
    # Save
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(existing_data, f, indent=2, ensure_ascii=False)
    
    print(f"✅ GPU shipment data saved: {len(existing_data)} records")
    return result


async def fetch_active_gpu_count():
    """
    计算全球活跃GPU总数 - 基于出货量和退役率
    """
    print(f"\n{'='*80}")
    print(f"[{datetime.now()}] 🔢 Calculating Active GPU Count")
    print(f"{'='*80}\n")
    
    prompt = """
    请使用联网搜索功能，计算全球当前活跃的AI训练GPU总数。
    
    需要考虑的因素：
    1. 历史出货量（2020-2024）
    2. GPU生命周期（通常3-5年）
    3. 退役率（每年约20-30%）
    4. 主要数据中心的GPU部署数量
    
    搜索以下信息：
    - NVIDIA历年GPU出货量
    - 主要云服务商的GPU集群规模
    - AI公司的GPU采购数据
    - 研究机构的估算报告
    
    返回JSON格式：
    {
      "total_active_gpus": 5200000,
      "breakdown": {
        "h100": 800000,
        "a100": 2500000,
        "v100": 1200000,
        "others": 700000
      },
      "growth_rate_monthly": 0.08,
      "sources": ["来源1", "来源2"],
      "confidence": "high",
      "last_updated": "2024-12-05"
    }
    
    要求：
    - 基于真实搜索结果
    - 提供计算逻辑
    - 标注数据来源
    """
    
    result = await orchestrator.process_request(
        prompt=prompt,
        context={"data_type": "active_gpu_count"},
        quality_threshold=0.8
    )
    
    # Save to file
    output_file = os.path.join(REALTIME_DIR, 'active_gpu_count.json')
    
    data_to_save = {
        "timestamp": datetime.now().isoformat(),
        "data": result.data,
        "models_used": result.contributing_models,
        "confidence_scores": result.confidence_scores
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data_to_save, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Active GPU count saved")
    return result


async def fetch_electricity_prices():
    """
    抓取实时电价数据 - 每小时更新
    
    数据源:
    - 各国电网实时电价
    - 数据中心所在地区电价
    - 可再生能源价格
    """
    print(f"\n{'='*80}")
    print(f"[{datetime.now()}] ⚡ Fetching Real-time Electricity Prices")
    print(f"{'='*80}\n")
    
    prompt = """
    请使用联网搜索功能，查找全球主要数据中心地区的实时电价。
    
    重点地区：
    1. 美国：
       - 德克萨斯州（大量数据中心）
       - 俄勒冈州（AWS、Google）
       - 弗吉尼亚州（AWS最大集群）
       - 加州（多个AI公司）
    
    2. 欧洲：
       - 爱尔兰（Meta、Google）
       - 荷兰（多个数据中心）
       - 瑞典（可再生能源）
    
    3. 亚洲：
       - 中国（阿里云、腾讯云）
       - 新加坡（AWS、Google）
       - 日本（多个数据中心）
    
    搜索内容：
    - 实时电价（美元/kWh）
    - 工业用电价格
    - 峰谷电价差异
    - 可再生能源占比
    
    返回JSON格式：
    [
      {
        "region": "Texas, USA",
        "price_kwh": 0.085,
        "currency": "USD",
        "timestamp": "2024-12-05T10:00:00Z",
        "peak_price": 0.12,
        "off_peak_price": 0.06,
        "renewable_percentage": 35,
        "source": "ERCOT"
      }
    ]
    
    要求：
    - 实时或最近24小时数据
    - 标注数据来源
    - 区分峰谷电价
    """
    
    result = await orchestrator.process_request(
        prompt=prompt,
        context={"data_type": "electricity_prices"},
        quality_threshold=0.7
    )
    
    # Save to file
    output_file = os.path.join(REALTIME_DIR, 'electricity_prices.json')
    
    # Load existing data
    existing_data = []
    if os.path.exists(output_file):
        try:
            with open(output_file, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
        except:
            pass
    
    # Append new data (keep last 24 hours)
    new_entry = {
        "timestamp": datetime.now().isoformat(),
        "data": result.data,
        "models_used": result.contributing_models
    }
    existing_data.append(new_entry)
    
    # Keep only last 24 hours
    cutoff_time = datetime.now() - timedelta(hours=24)
    existing_data = [
        entry for entry in existing_data
        if datetime.fromisoformat(entry["timestamp"]) > cutoff_time
    ]
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(existing_data, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Electricity prices saved: {len(existing_data)} hourly records")
    return result


async def fetch_ai_industry_news():
    """
    抓取AI行业新闻 - 每小时更新
    
    关注：
    - GPU采购公告
    - 数据中心建设
    - AI公司融资
    - 政策法规变化
    """
    print(f"\n{'='*80}")
    print(f"[{datetime.now()}] 📰 Fetching AI Industry News")
    print(f"{'='*80}\n")
    
    prompt = """
    请使用联网搜索功能，查找最近24小时内的AI行业重要新闻。
    
    重点关注：
    1. GPU/AI芯片相关：
       - NVIDIA新产品发布
       - 大规模GPU采购公告
       - AI芯片厂商动态
    
    2. 数据中心建设：
       - 新数据中心开工/投产
       - 数据中心扩容计划
       - 能源供应协议
    
    3. AI公司动态：
       - OpenAI, Anthropic, Google, Meta等
       - 大规模融资
       - 算力采购计划
    
    4. 政策法规：
       - AI监管政策
       - 能源政策
       - 出口管制
    
    返回JSON格式：
    [
      {
        "timestamp": "2024-12-05T09:30:00Z",
        "title": "Microsoft采购10万张H100 GPU",
        "category": "gpu_purchase",
        "impact": "high",
        "summary": "简短摘要",
        "source": "新闻来源",
        "url": "链接"
      }
    ]
    
    要求：
    - 最近24小时新闻
    - 评估影响程度（high/medium/low）
    - 提供新闻来源
    """
    
    result = await orchestrator.process_request(
        prompt=prompt,
        context={"data_type": "industry_news"},
        quality_threshold=0.7
    )
    
    # Save to file
    output_file = os.path.join(REALTIME_DIR, 'industry_news.json')
    
    # Load existing data
    existing_data = []
    if os.path.exists(output_file):
        try:
            with open(output_file, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
        except:
            pass
    
    # Append new data (keep last 7 days)
    new_entry = {
        "fetch_timestamp": datetime.now().isoformat(),
        "news": result.data,
        "models_used": result.contributing_models
    }
    existing_data.append(new_entry)
    
    # Keep only last 7 days
    cutoff_time = datetime.now() - timedelta(days=7)
    existing_data = [
        entry for entry in existing_data
        if datetime.fromisoformat(entry["fetch_timestamp"]) > cutoff_time
    ]
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(existing_data, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Industry news saved: {len(existing_data)} batches")
    return result


async def fetch_energy_consumption_realtime():
    """
    计算实时能耗 - 基于活跃GPU数量和电价
    """
    print(f"\n{'='*80}")
    print(f"[{datetime.now()}] 🔋 Calculating Real-time Energy Consumption")
    print(f"{'='*80}\n")
    
    prompt = """
    请使用联网搜索功能，计算全球AI数据中心的实时能耗。
    
    需要的数据：
    1. 当前活跃GPU数量（约500-600万张）
    2. 每张GPU功耗（H100: 700W, A100: 400W等）
    3. PUE（数据中心能效比，通常1.2-1.5）
    4. 利用率（通常60-80%）
    
    计算公式：
    总功耗(GW) = GPU数量 × 平均功耗 × PUE × 利用率 / 1,000,000,000
    
    返回JSON格式：
    {
      "timestamp": "2024-12-05T10:00:00Z",
      "total_power_gw": 3.2,
      "breakdown": {
        "gpu_power_gw": 2.4,
        "cooling_power_gw": 0.5,
        "other_power_gw": 0.3
      },
      "daily_energy_twh": 0.077,
      "annual_projection_twh": 28.1,
      "cost_per_hour_usd": 384000,
      "sources": ["来源"],
      "assumptions": {
        "active_gpus": 5200000,
        "avg_power_per_gpu_w": 550,
        "pue": 1.3,
        "utilization": 0.75
      }
    }
    
    要求：
    - 基于最新数据
    - 说明计算假设
    - 提供数据来源
    """
    
    result = await orchestrator.process_request(
        prompt=prompt,
        context={"data_type": "energy_consumption"},
        quality_threshold=0.8
    )
    
    # Save to file
    output_file = os.path.join(REALTIME_DIR, 'energy_consumption.json')
    
    # Load existing data
    existing_data = []
    if os.path.exists(output_file):
        try:
            with open(output_file, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
        except:
            pass
    
    # Append new data (keep last 24 hours)
    new_entry = {
        "timestamp": datetime.now().isoformat(),
        "data": result.data,
        "models_used": result.contributing_models
    }
    existing_data.append(new_entry)
    
    # Keep only last 24 hours
    cutoff_time = datetime.now() - timedelta(hours=24)
    existing_data = [
        entry for entry in existing_data
        if datetime.fromisoformat(entry["timestamp"]) > cutoff_time
    ]
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(existing_data, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Energy consumption saved: {len(existing_data)} hourly records")
    return result


async def run_hourly_update():
    """运行一次完整的小时更新"""
    print(f"\n{'='*80}")
    print(f"🚀 STARTING HOURLY DATA UPDATE")
    print(f"{'='*80}\n")
    
    start_time = time.time()
    
    # 并行执行所有数据抓取
    results = await asyncio.gather(
        fetch_gpu_shipment_data(),
        fetch_active_gpu_count(),
        fetch_electricity_prices(),
        fetch_ai_industry_news(),
        fetch_energy_consumption_realtime(),
        return_exceptions=True
    )
    
    elapsed_time = time.time() - start_time
    
    # 统计结果
    success_count = sum(1 for r in results if not isinstance(r, Exception))
    
    print(f"\n{'='*80}")
    print(f"✅ HOURLY UPDATE COMPLETE")
    print(f"{'='*80}\n")
    print(f"  • Tasks completed: {success_count}/5")
    print(f"  • Time elapsed: {elapsed_time:.1f}s")
    print(f"  • Next update: {(datetime.now() + timedelta(hours=1)).strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 显示AI Orchestrator性能报告
    print(f"📊 AI Orchestrator Performance:")
    for model_name in ["qwen", "deepseek", "doubao"]:
        report = orchestrator.get_performance_report(model_name=model_name)
        if report.get('total_records', 0) > 0:
            print(f"  {model_name}:")
            print(f"    • Requests: {report['total_records']}")
            print(f"    • Accuracy: {report['accuracy']:.1%}")
            print(f"    • Avg Time: {report['avg_response_time']:.2f}s")
            print(f"    • Total Cost: ${report['total_cost']:.4f}")


async def main():
    """主函数 - 持续运行，每小时更新一次"""
    print(f"\n{'='*80}")
    print(f"🌟 REAL-TIME DATA FETCHING SYSTEM")
    print(f"{'='*80}\n")
    print(f"Features:")
    print(f"  ✓ Hourly GPU shipment tracking")
    print(f"  ✓ Real-time electricity prices")
    print(f"  ✓ AI industry news monitoring")
    print(f"  ✓ Active GPU count calculation")
    print(f"  ✓ Energy consumption tracking")
    print()
    print(f"Data will be saved to: {REALTIME_DIR}")
    print()
    
    # 检查是否是单次运行
    if len(sys.argv) > 1 and sys.argv[1] == '--once':
        print("Running once...")
        await run_hourly_update()
        return
    
    # 持续运行模式
    print("Running continuously (hourly updates)...")
    print("Press Ctrl+C to stop")
    print()
    
    while True:
        try:
            await run_hourly_update()
            
            # 等待到下一个整点
            now = datetime.now()
            next_hour = (now + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
            sleep_seconds = (next_hour - now).total_seconds()
            
            print(f"💤 Sleeping for {sleep_seconds/60:.1f} minutes until next update...")
            await asyncio.sleep(sleep_seconds)
            
        except KeyboardInterrupt:
            print("\n\n⚠️  Stopping real-time data fetching...")
            break
        except Exception as e:
            print(f"\n❌ Error in main loop: {e}")
            print("Retrying in 5 minutes...")
            await asyncio.sleep(300)


if __name__ == "__main__":
    asyncio.run(main())
