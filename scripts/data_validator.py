#!/usr/bin/env python3
"""
Data Validation Module using Doubao AI
Doubao acts as a data quality checker and validator
"""

import json
import os
import requests
from datetime import datetime
from typing import List, Dict, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env.local')

volc_api_key = os.getenv('VOLC_API_KEY')
DOUBAO_ENDPOINT_ID = "doubao-seed-1-6-251015"

def call_doubao_validator(prompt: str, timeout: int = 180) -> Optional[str]:
    """
    Call Doubao API for data validation.
    Uses longer timeout since validation requires deep analysis.
    """
    if not volc_api_key:
        return None
    
    headers = {
        "Authorization": f"Bearer {volc_api_key}",
        "Content-Type": "application/json"
    }
    
    try:
        url = "https://ark.cn-beijing.volces.com/api/v3/responses"
        payload = {
            "model": DOUBAO_ENDPOINT_ID,
            "stream": False,
            "tools": [{"type": "web_search"}],  # Enable web search for validation
            "input": [
                {
                    "role": "user",
                    "content": [{"type": "input_text", "text": prompt}]
                }
            ]
        }
        
        response = requests.post(url, headers=headers, json=payload, timeout=timeout)
        if response.status_code == 200:
            res_json = response.json()
            # Extract message content from output
            if 'output' in res_json:
                for item in res_json['output']:
                    if item.get('type') == 'message' and 'content' in item:
                        for content_item in item['content']:
                            if content_item.get('type') in ['text', 'output_text']:
                                text = content_item.get('text') or content_item.get('output_text')
                                if text:
                                    return text
        else:
            print(f"[{datetime.now()}] Doubao Validator Error: {response.status_code}")
            
    except Exception as e:
        print(f"[{datetime.now()}] Doubao Validator Failed: {e}")
    
    return None

def validate_gpu_prices(gpu_data: List[Dict]) -> Dict:
    """
    Use Doubao to validate GPU price data.
    Returns validation report with anomalies and recommendations.
    """
    print(f"[{datetime.now()}] Doubao: Validating {len(gpu_data)} GPU price records...")
    
    # Prepare data summary for validation
    data_summary = json.dumps(gpu_data, indent=2, ensure_ascii=False)
    
    prompt = f"""你是一个数据质量审核专家。请分析以下 GPU 价格数据，识别异常和问题。

数据：
{data_summary}

请执行以下验证：
1. 价格合理性检查：
   - 识别异常高价或异常低价（与市场平均偏离 >50%）
   - 检查同一 GPU 在不同供应商的价格差异
   - 标注可疑的价格数据

2. 数据完整性检查：
   - 检查是否有重复记录
   - 检查必需字段是否完整
   - 识别数据格式问题

3. 市场趋势验证：
   - 基于最新市场信息，验证价格是否符合当前趋势
   - 识别过时的价格数据

请以 JSON 格式返回验证报告：
{{
  "summary": {{
    "total_records": 数字,
    "valid_records": 数字,
    "suspicious_records": 数字,
    "duplicate_records": 数字
  }},
  "anomalies": [
    {{
      "provider": "供应商",
      "gpu": "GPU型号",
      "price": 价格,
      "issue": "问题描述",
      "severity": "high/medium/low",
      "recommendation": "建议"
    }}
  ],
  "market_insights": "市场趋势分析",
  "overall_quality": "excellent/good/fair/poor"
}}

只返回 JSON，不要其他文字。"""

    result = call_doubao_validator(prompt)
    
    if result:
        try:
            # Parse JSON response
            report = json.loads(result.replace('```json', '').replace('```', '').strip())
            print(f"[{datetime.now()}] Doubao: Validation complete - Quality: {report.get('overall_quality', 'unknown')}")
            return report
        except json.JSONDecodeError as e:
            print(f"[{datetime.now()}] Doubao: Failed to parse validation report: {e}")
            return {"error": "Failed to parse validation report", "raw_response": result}
    else:
        print(f"[{datetime.now()}] Doubao: Validation failed - no response")
        return {"error": "No response from validator"}

def validate_token_prices(token_data: List[Dict]) -> Dict:
    """
    Use Doubao to validate Token price data.
    Returns validation report with anomalies and recommendations.
    """
    print(f"[{datetime.now()}] Doubao: Validating {len(token_data)} Token price records...")
    
    data_summary = json.dumps(token_data, indent=2, ensure_ascii=False)
    
    prompt = f"""你是一个数据质量审核专家。请分析以下大模型 Token 价格数据，识别异常和问题。

数据：
{data_summary}

请执行以下验证：
1. 价格合理性检查：
   - 识别异常高价或异常低价
   - 检查输入/输出价格比例是否合理（通常输出价格是输入的 2-4 倍）
   - 对比同类模型的价格差异

2. 数据完整性检查：
   - 检查是否有重复记录
   - 检查必需字段（provider, model, input_price, output_price）
   - 识别数据格式问题

3. 市场趋势验证：
   - 基于最新市场信息，验证价格是否符合当前趋势
   - 识别过时的价格数据

请以 JSON 格式返回验证报告：
{{
  "summary": {{
    "total_records": 数字,
    "valid_records": 数字,
    "suspicious_records": 数字,
    "duplicate_records": 数字
  }},
  "anomalies": [
    {{
      "provider": "供应商",
      "model": "模型名称",
      "input_price": 输入价格,
      "output_price": 输出价格,
      "issue": "问题描述",
      "severity": "high/medium/low",
      "recommendation": "建议"
    }}
  ],
  "market_insights": "市场趋势分析",
  "overall_quality": "excellent/good/fair/poor"
}}

只返回 JSON，不要其他文字。"""

    result = call_doubao_validator(prompt)
    
    if result:
        try:
            report = json.loads(result.replace('```json', '').replace('```', '').strip())
            print(f"[{datetime.now()}] Doubao: Validation complete - Quality: {report.get('overall_quality', 'unknown')}")
            return report
        except json.JSONDecodeError as e:
            print(f"[{datetime.now()}] Doubao: Failed to parse validation report: {e}")
            return {"error": "Failed to parse validation report", "raw_response": result}
    else:
        print(f"[{datetime.now()}] Doubao: Validation failed - no response")
        return {"error": "No response from validator"}

def cross_validate_sources(qwen_data: List[Dict], deepseek_data: List[Dict]) -> Dict:
    """
    Use Doubao to cross-validate data from different sources.
    Identifies conflicts and provides recommendations.
    """
    print(f"[{datetime.now()}] Doubao: Cross-validating data from Qwen and DeepSeek...")
    
    prompt = f"""你是一个数据交叉验证专家。请对比分析来自两个不同数据源的数据，识别冲突和差异。

Qwen 数据（{len(qwen_data)} 条）：
{json.dumps(qwen_data[:10], indent=2, ensure_ascii=False)}

DeepSeek 数据（{len(deepseek_data)} 条）：
{json.dumps(deepseek_data[:10], indent=2, ensure_ascii=False)}

请执行以下分析：
1. 识别相同 GPU/模型在两个数据源中的价格差异
2. 分析差异的合理性（地区、时间、配置等因素）
3. 推荐应该采用哪个数据源的数据

请以 JSON 格式返回：
{{
  "conflicts": [
    {{
      "item": "GPU/模型名称",
      "qwen_price": 价格,
      "deepseek_price": 价格,
      "difference_percent": 百分比,
      "recommendation": "使用哪个数据源",
      "reason": "原因"
    }}
  ],
  "agreement_rate": "一致性百分比",
  "recommendation": "总体建议"
}}

只返回 JSON，不要其他文字。"""

    result = call_doubao_validator(prompt, timeout=240)  # Longer timeout for cross-validation
    
    if result:
        try:
            report = json.loads(result.replace('```json', '').replace('```', '').strip())
            print(f"[{datetime.now()}] Doubao: Cross-validation complete")
            return report
        except json.JSONDecodeError as e:
            print(f"[{datetime.now()}] Doubao: Failed to parse cross-validation report: {e}")
            return {"error": "Failed to parse report", "raw_response": result}
    else:
        print(f"[{datetime.now()}] Doubao: Cross-validation failed - no response")
        return {"error": "No response from validator"}

def fix_anomalies(data: List[Dict], anomalies: List[Dict], data_type: str) -> tuple:
    """
    Automatically fix data anomalies based on Doubao's recommendations.
    
    Args:
        data: Original data list
        anomalies: List of anomalies from validation report
        data_type: 'gpu' or 'token'
    
    Returns:
        tuple: (fixed_data, fix_summary)
    """
    print(f"[{datetime.now()}] Doubao: Attempting to fix {len(anomalies)} anomalies...")
    
    fixed_data = data.copy()
    fix_summary = {
        'fixed': 0,
        'removed': 0,
        'manual_review': 0
    }
    
    # Build anomaly lookup
    anomaly_map = {}
    for anomaly in anomalies:
        if data_type == 'gpu':
            key = f"{anomaly.get('provider')}_{anomaly.get('gpu')}"
        else:  # token
            key = f"{anomaly.get('provider')}_{anomaly.get('model')}"
        anomaly_map[key] = anomaly
    
    # Process each record
    fixed_records = []
    for record in fixed_data:
        if data_type == 'gpu':
            key = f"{record.get('provider')}_{record.get('gpu')}"
        else:
            key = f"{record.get('provider')}_{record.get('model')}"
        
        if key in anomaly_map:
            anomaly = anomaly_map[key]
            severity = anomaly.get('severity', 'low')
            recommendation = anomaly.get('recommendation', '')
            
            # Auto-fix based on severity and recommendation
            if severity == 'high':
                # High severity: remove the record
                if '删除' in recommendation or '移除' in recommendation or 'remove' in recommendation.lower():
                    print(f"[{datetime.now()}]   🗑️  Removing: {key} (high severity)")
                    fix_summary['removed'] += 1
                    continue  # Skip this record
                else:
                    # Needs manual review
                    print(f"[{datetime.now()}]   ⚠️  Manual review needed: {key}")
                    fix_summary['manual_review'] += 1
                    fixed_records.append(record)
            
            elif severity == 'medium':
                # Medium severity: try to fix or flag for review
                if '核实' in recommendation or '确认' in recommendation:
                    # Keep but flag
                    record['_needs_review'] = True
                    record['_issue'] = anomaly.get('issue')
                    fix_summary['manual_review'] += 1
                    fixed_records.append(record)
                else:
                    # Keep as is
                    fixed_records.append(record)
            
            else:  # low severity
                # Low severity: keep the record
                fixed_records.append(record)
        else:
            # No anomaly, keep the record
            fixed_records.append(record)
    
    fix_summary['fixed'] = len(data) - len(fixed_records) - fix_summary['removed']
    
    return fixed_records, fix_summary

def ask_doubao_to_fix(anomaly: Dict, data_type: str) -> Optional[Dict]:
    """
    Ask Doubao to provide a corrected version of the data.
    Uses web search to find the correct information.
    """
    if data_type == 'gpu':
        prompt = f"""你发现了一个 GPU 价格数据异常：

供应商：{anomaly.get('provider')}
GPU：{anomaly.get('gpu')}
当前价格：${anomaly.get('price')}/小时
问题：{anomaly.get('issue')}

请使用联网搜索，找到该 GPU 在该供应商的正确价格，并返回修正后的数据。

返回 JSON 格式：
{{
  "provider": "供应商",
  "region": "区域",
  "gpu": "GPU型号",
  "price": 正确价格（数字）,
  "source": "数据来源"
}}

只返回 JSON，不要其他文字。"""
    
    else:  # token
        prompt = f"""你发现了一个 Token 价格数据异常：

供应商：{anomaly.get('provider')}
模型：{anomaly.get('model')}
输入价格：${anomaly.get('input_price')}/百万tokens
输出价格：${anomaly.get('output_price')}/百万tokens
问题：{anomaly.get('issue')}

请使用联网搜索，找到该模型的正确价格，并返回修正后的数据。

返回 JSON 格式：
{{
  "provider": "供应商",
  "model": "模型名称",
  "input_price": 正确输入价格（数字）,
  "output_price": 正确输出价格（数字）,
  "source": "数据来源"
}}

只返回 JSON，不要其他文字。"""
    
    result = call_doubao_validator(prompt, timeout=240)
    
    if result:
        try:
            fixed_data = json.loads(result.replace('```json', '').replace('```', '').strip())
            return fixed_data
        except json.JSONDecodeError:
            return None
    
    return None

if __name__ == "__main__":
    # Test validation
    print("=" * 80)
    print("Doubao Data Validator Test")
    print("=" * 80)
    
    # Load test data
    try:
        with open('../public/data/gpu_prices.json', 'r', encoding='utf-8') as f:
            gpu_data = json.load(f)
        
        report = validate_gpu_prices(gpu_data)
        print("\nValidation Report:")
        print(json.dumps(report, indent=2, ensure_ascii=False))
        
    except Exception as e:
        print(f"Test failed: {e}")
