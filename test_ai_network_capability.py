#!/usr/bin/env python3
"""
独立测试脚本：验证5个AI模型联网获取今天（2025-12-07）实时汇率的能力
不要使用现有代码，完全从头实现
"""

import os
import json
import time
import re
import requests
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Tuple
import sys

# 尝试导入必要的库
try:
    import dashscope
    from openai import OpenAI
except ImportError:
    print("缺少必要的库，正在安装...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "dashscope", "openai", "requests", "python-dotenv"])
    import dashscope
    from openai import OpenAI

# 加载环境变量
from dotenv import load_dotenv
load_dotenv('.env.local')

# 配置
TODAY = "2025-12-07"
TEST_PROMPT = """
Please search for the current real-time USD to CNY exchange rate for TODAY (2025-12-07).

IMPORTANT:
1. You MUST use web search to get the latest real-time data
2. The rate must be for today, 2025-12-07
3. Include the exact timestamp when the rate was valid
4. Mention the data source (e.g., XE.com, Bloomberg, Reuters, etc.)

Output valid JSON ONLY:
{
    "from": "USD",
    "to": "CNY",
    "rate": 7.25,
    "timestamp": "2025-12-07T10:30:00Z",
    "source": "web_search_result",
    "date_verified": "2025-12-07"
}
"""

def get_baseline_exchange_rate() -> Optional[float]:
    """从独立API获取今天真实汇率作为基准"""
    print("\n" + "="*60)
    print("获取基准汇率...")
    print("="*60)

    sources = [
        ("ExchangeRate-API", "https://api.exchangerate-api.com/v4/latest/USD"),
        ("Frankfurter", "https://api.frankfurter.app/latest?from=USD&to=CNY"),
    ]

    rates = []
    for name, url in sources:
        try:
            print(f"尝试从 {name} 获取汇率...")
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if "rates" in data and "CNY" in data["rates"]:
                    rate = data["rates"]["CNY"]
                    rates.append(rate)
                    print(f"  [OK]{name}: 1 USD = {rate} CNY")
                elif "CNY" in data:  # Frankfurter格式
                    rate = data["CNY"]
                    rates.append(rate)
                    print(f"  [OK]{name}: 1 USD = {rate} CNY")
                else:
                    print(f"  [FAIL]{name}: 未找到CNY汇率")
            else:
                print(f"  [FAIL]{name}: HTTP {response.status_code}")
        except Exception as e:
            print(f"  [FAIL]{name}: {e}")

    if rates:
        avg_rate = sum(rates) / len(rates)
        print(f"\n基准汇率平均值: 1 USD = {avg_rate:.4f} CNY")
        return avg_rate
    else:
        print("警告: 无法从API获取基准汇率，使用合理估计值 7.25")
        return 7.25

def extract_json_from_response(text: str) -> Optional[Dict[str, Any]]:
    """从响应文本中提取JSON"""
    if not text:
        return None

    # 尝试直接解析
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # 尝试提取JSON对象
    json_patterns = [
        r'\{[^{}]*\}',  # 简单对象
        r'\{.*\}',  # 复杂对象（可能跨多行）
    ]

    for pattern in json_patterns:
        matches = re.findall(pattern, text, re.DOTALL)
        for match in matches:
            try:
                # 清理可能的markdown代码块
                clean_match = match.replace('```json', '').replace('```', '').strip()
                return json.loads(clean_match)
            except json.JSONDecodeError:
                continue

    return None

def analyze_response(response_text: str, baseline_rate: float) -> Dict[str, Any]:
    """分析AI响应"""
    analysis = {
        "success": False,
        "rate": None,
        "timestamp": None,
        "is_today": False,
        "has_source": False,
        "has_real_time_keywords": False,
        "error": None,
        "raw_response": response_text[:500] + "..." if len(response_text) > 500 else response_text
    }

    if not response_text:
        analysis["error"] = "空响应"
        return analysis

    # 1. 检查是否包含今天日期关键词
    today_keywords = [TODAY, "today", "2025-12-07", "December 7, 2025", "12/07/2025"]
    for keyword in today_keywords:
        if keyword.lower() in response_text.lower():
            analysis["is_today"] = True
            break

    # 2. 检查实时数据关键词
    real_time_keywords = ["real-time", "real time", "live", "current", "latest", "as of today", "updated"]
    for keyword in real_time_keywords:
        if keyword.lower() in response_text.lower():
            analysis["has_real_time_keywords"] = True
            break

    # 3. 检查数据来源
    sources = ["xe.com", "bloomberg", "reuters", "yahoo finance", "investing.com", "forex", "financial times"]
    for source in sources:
        if source in response_text.lower():
            analysis["has_source"] = True
            break

    # 4. 提取JSON数据
    data = extract_json_from_response(response_text)
    if data:
        analysis["rate"] = data.get("rate")
        analysis["timestamp"] = data.get("timestamp")

        # 5. 验证汇率
        if analysis["rate"]:
            # 检查汇率合理性
            if 6.5 <= analysis["rate"] <= 8.0:
                # 检查与基准汇率的差异
                diff = abs(analysis["rate"] - baseline_rate)
                if diff <= 0.5:  # 允许±0.5的差异
                    analysis["success"] = True
                    analysis["diff_from_baseline"] = diff
                else:
                    analysis["error"] = f"汇率差异过大: {diff:.4f}"
            else:
                analysis["error"] = f"汇率超出合理范围: {analysis['rate']}"
        else:
            analysis["error"] = "未找到汇率数据"
    else:
        analysis["error"] = "无法解析JSON数据"

    return analysis

def test_qwen() -> Tuple[str, float]:
    """测试Qwen（通义千问）联网搜索能力"""
    print("\n" + "="*60)
    print("测试 Qwen (通义千问) - 启用联网搜索")
    print("="*60)

    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        return "错误: 未设置DASHSCOPE_API_KEY", 0.0

    dashscope.api_key = api_key
    start_time = time.time()

    try:
        response = dashscope.Generation.call(
            model='qwen-max',
            prompt=TEST_PROMPT,
            enable_search=True  # 启用联网搜索
        )

        if response.status_code == 200:
            response_text = response.output.text
            elapsed = time.time() - start_time
            print(f"响应时间: {elapsed:.2f}秒")
            return response_text, elapsed
        else:
            error_msg = f"API错误: {response.status_code} - {response.message}"
            print(error_msg)
            return error_msg, time.time() - start_time
    except Exception as e:
        error_msg = f"异常: {str(e)}"
        print(error_msg)
        return error_msg, time.time() - start_time

def test_deepseek() -> Tuple[str, float]:
    """测试DeepSeek联网搜索能力"""
    print("\n" + "="*60)
    print("测试 DeepSeek - 尝试启用联网搜索")
    print("="*60)

    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        return "错误: 未设置DASHSCOPE_API_KEY", 0.0

    # 通过DashScope的OpenAI兼容API
    client = OpenAI(
        api_key=api_key,
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
    )

    start_time = time.time()

    try:
        # 尝试启用搜索功能
        completion = client.chat.completions.create(
            model="deepseek-v3.2-exp",
            messages=[
                {"role": "system", "content": "You are DeepSeek, an AI assistant with real-time internet access. When asked for current information like exchange rates, use web search to get the latest data."},
                {"role": "user", "content": TEST_PROMPT}
            ],
            extra_body={"enable_search": True},  # 尝试启用搜索
            timeout=30
        )

        response_text = completion.choices[0].message.content
        elapsed = time.time() - start_time
        print(f"响应时间: {elapsed:.2f}秒")
        return response_text, elapsed
    except Exception as e:
        error_msg = f"异常: {str(e)}"
        print(error_msg)
        return error_msg, time.time() - start_time

def test_kimi() -> Tuple[str, float]:
    """测试Kimi（月之暗面）联网搜索能力"""
    print("\n" + "="*60)
    print("测试 Kimi (月之暗面) - 专门配置实时搜索")
    print("="*60)

    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        return "错误: 未设置DASHSCOPE_API_KEY", 0.0

    # Kimi通过DashScope的OpenAI兼容API
    client = OpenAI(
        api_key=api_key,
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
    )

    start_time = time.time()

    try:
        completion = client.chat.completions.create(
            model="Moonshot-Kimi-K2-Instruct",  # Kimi模型
            messages=[
                {"role": "system", "content": "You are Kimi, an AI assistant with real-time internet access. When asked for current information like exchange rates or news, you MUST use your search tool to find the latest data. Do not say you cannot access live data."},
                {"role": "user", "content": TEST_PROMPT}
            ],
            extra_body={"enable_search": True},  # 启用搜索
            timeout=30
        )

        response_text = completion.choices[0].message.content
        elapsed = time.time() - start_time
        print(f"响应时间: {elapsed:.2f}秒")
        return response_text, elapsed
    except Exception as e:
        error_msg = f"异常: {str(e)}"
        print(error_msg)
        return error_msg, time.time() - start_time

def test_glm() -> Tuple[str, float]:
    """测试GLM-4联网搜索能力"""
    print("\n" + "="*60)
    print("测试 GLM-4 (智谱) - 独立web搜索API")
    print("="*60)

    api_key = os.getenv("ZHIPU_API_KEY")
    if not api_key:
        return "错误: 未设置ZHIPU_API_KEY", 0.0

    # 智谱OpenAI兼容API
    client = OpenAI(
        api_key=api_key,
        base_url="https://open.bigmodel.cn/api/paas/v4"
    )

    start_time = time.time()

    try:
        # GLM-4可能支持搜索功能
        completion = client.chat.completions.create(
            model="glm-4",  # GLM-4模型
            messages=[
                {"role": "system", "content": "You are GLM-4, an AI assistant with web search capability. When asked for real-time information like exchange rates, use your search function to get the latest data."},
                {"role": "user", "content": TEST_PROMPT}
            ],
            timeout=30
        )

        response_text = completion.choices[0].message.content
        elapsed = time.time() - start_time
        print(f"响应时间: {elapsed:.2f}秒")
        return response_text, elapsed
    except Exception as e:
        error_msg = f"异常: {str(e)}"
        print(error_msg)
        return error_msg, time.time() - start_time

def test_minimax() -> Tuple[str, float]:
    """测试MiniMax联网搜索能力"""
    print("\n" + "="*60)
    print("测试 MiniMax - 推理模式（不支持原生搜索）")
    print("="*60)

    api_key = os.getenv("MINIMAX_API_KEY")
    if not api_key:
        return "错误: 未设置MINIMAX_API_KEY", 0.0

    # MiniMax OpenAI兼容API
    client = OpenAI(
        api_key=api_key,
        base_url="https://api.minimax.chat/v1"
    )

    start_time = time.time()

    try:
        # MiniMax M2模型，启用推理模式
        completion = client.chat.completions.create(
            model="MiniMax-M2",  # MiniMax M2模型
            messages=[
                {"role": "system", "content": "You are MiniMax M2, a strategic AI assistant. You are good at reasoning and analysis. If asked for real-time data like exchange rates, provide your best reasoning based on available knowledge, or clearly state if you cannot access live data."},
                {"role": "user", "content": TEST_PROMPT}
            ],
            extra_body={"reasoning_split": True},  # 启用推理模式
            timeout=30
        )

        response_text = completion.choices[0].message.content
        elapsed = time.time() - start_time
        print(f"响应时间: {elapsed:.2f}秒")
        return response_text, elapsed
    except Exception as e:
        error_msg = f"异常: {str(e)}"
        print(error_msg)
        return error_msg, time.time() - start_time

def generate_report(results: List[Dict[str, Any]], baseline_rate: float):
    """生成测试报告"""
    print("\n" + "="*80)
    print("AI模型联网能力测试报告 - 实时汇率获取验证")
    print(f"测试日期: {TODAY}")
    print(f"基准汇率: {baseline_rate:.4f} CNY/USD")
    print("="*80)

    success_count = 0
    today_count = 0
    source_count = 0

    for i, result in enumerate(results, 1):
        agent_name = result["agent"]
        analysis = result["analysis"]

        status = "[OK] 成功" if analysis["success"] else "[FAIL] 失败"
        today_flag = "[OK]" if analysis["is_today"] else "[FAIL]"
        source_flag = "[OK]" if analysis["has_source"] else "[FAIL]"
        real_time_flag = "[OK]" if analysis["has_real_time_keywords"] else "[FAIL]"

        print(f"\n{i}. {agent_name}:")
        print(f"   状态: {status}")
        print(f"   响应时间: {result['response_time']:.2f}秒")

        if analysis["rate"]:
            print(f"   获取汇率: {analysis['rate']}")
            if "diff_from_baseline" in analysis:
                print(f"   与基准差异: {analysis['diff_from_baseline']:.4f}")

        if analysis["timestamp"]:
            print(f"   时间戳: {analysis['timestamp']}")

        print(f"   是否为今天: {today_flag}")
        print(f"   有数据来源: {source_flag}")
        print(f"   实时关键词: {real_time_flag}")

        if analysis["error"]:
            print(f"   错误: {analysis['error']}")

        # 统计
        if analysis["success"]:
            success_count += 1
        if analysis["is_today"]:
            today_count += 1
        if analysis["has_source"]:
            source_count += 1

        # 显示原始响应片段
        if analysis["raw_response"]:
            print(f"   响应片段: {analysis['raw_response'][:200]}...")

    # 总结统计
    print("\n" + "="*80)
    print("测试总结:")
    print(f"   总测试模型: {len(results)}")
    print(f"   成功获取实时汇率: {success_count}")
    print(f"   包含今天日期: {today_count}")
    print(f"   提及数据来源: {source_count}")

    # 评估整体联网能力
    if success_count >= 3:
        print("\n[SUCCESS] 结论: 多数AI模型支持联网获取实时数据")
    elif success_count >= 1:
        print("\n[WARNING] 结论: 部分AI模型支持联网获取实时数据")
    else:
        print("\n[FAIL] 结论: AI模型联网获取实时数据能力有限")

    # 保存详细结果到文件
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = f"ai_network_test_report_{timestamp}.json"

    report_data = {
        "test_date": TODAY,
        "baseline_rate": baseline_rate,
        "results": results,
        "summary": {
            "total_models": len(results),
            "success_count": success_count,
            "today_count": today_count,
            "source_count": source_count
        }
    }

    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report_data, f, indent=2, ensure_ascii=False)

    print(f"\n详细报告已保存到: {report_file}")

def main():
    """主测试函数"""
    print("="*80)
    print("AI模型联网能力测试 - 实时汇率获取验证")
    print(f"测试日期: {TODAY}")
    print("="*80)

    # 1. 获取基准汇率
    baseline_rate = get_baseline_exchange_rate()

    # 2. 定义测试顺序（按预期成功率排序）
    test_functions = [
        ("Kimi (月之暗面)", test_kimi),
        ("Qwen (通义千问)", test_qwen),
        ("GLM-4 (智谱)", test_glm),
        ("DeepSeek", test_deepseek),
        ("MiniMax", test_minimax)
    ]

    results = []

    # 3. 执行测试
    for agent_name, test_func in test_functions:
        print(f"\n>>> 开始测试: {agent_name}")

        response_text, response_time = test_func()

        # 分析响应
        analysis = analyze_response(response_text, baseline_rate)

        results.append({
            "agent": agent_name,
            "response_time": response_time,
            "analysis": analysis
        })

        # 短暂延迟，避免API限制
        time.sleep(2)

    # 4. 生成报告
    generate_report(results, baseline_rate)

if __name__ == "__main__":
    main()