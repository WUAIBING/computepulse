#!/usr/bin/env python3
"""Test Doubao as a data validator"""

import json
import os
import sys

# Add parent directory to path
sys.path.append(os.path.dirname(__file__))

from data_validator import validate_gpu_prices, validate_token_prices

print("=" * 80)
print("Doubao 数据验证测试")
print("=" * 80)

# Load current data
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'public', 'data')

print("\n[1] 加载数据...")
try:
    with open(os.path.join(DATA_DIR, 'gpu_prices.json'), 'r', encoding='utf-8') as f:
        gpu_data = json.load(f)
    print(f"✓ 加载了 {len(gpu_data)} 条 GPU 价格数据")
    
    with open(os.path.join(DATA_DIR, 'token_prices.json'), 'r', encoding='utf-8') as f:
        token_data = json.load(f)
    print(f"✓ 加载了 {len(token_data)} 条 Token 价格数据")
    
except Exception as e:
    print(f"✗ 加载数据失败: {e}")
    sys.exit(1)

# Test GPU validation
print("\n" + "=" * 80)
print("[2] 测试 GPU 价格验证...")
print("=" * 80)

gpu_report = validate_gpu_prices(gpu_data)

if 'error' in gpu_report:
    print(f"✗ 验证失败: {gpu_report['error']}")
else:
    print("\n📊 验证摘要:")
    summary = gpu_report.get('summary', {})
    print(f"  总记录数: {summary.get('total_records', 0)}")
    print(f"  有效记录: {summary.get('valid_records', 0)}")
    print(f"  可疑记录: {summary.get('suspicious_records', 0)}")
    print(f"  重复记录: {summary.get('duplicate_records', 0)}")
    print(f"  整体质量: {gpu_report.get('overall_quality', 'unknown')}")
    
    if 'anomalies' in gpu_report and len(gpu_report['anomalies']) > 0:
        print(f"\n⚠️  发现 {len(gpu_report['anomalies'])} 个异常:")
        for i, anomaly in enumerate(gpu_report['anomalies'][:5], 1):
            print(f"\n  [{i}] {anomaly.get('provider')} - {anomaly.get('gpu')}")
            print(f"      价格: ${anomaly.get('price')}")
            print(f"      问题: {anomaly.get('issue')}")
            print(f"      严重程度: {anomaly.get('severity')}")
            print(f"      建议: {anomaly.get('recommendation')}")
    
    if 'market_insights' in gpu_report:
        print(f"\n💡 市场洞察:")
        print(f"  {gpu_report['market_insights']}")
    
    # Save report
    report_file = os.path.join(DATA_DIR, 'validation_report_gpu.json')
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(gpu_report, f, indent=2, ensure_ascii=False)
    print(f"\n✓ 验证报告已保存: {report_file}")

# Test Token validation
print("\n" + "=" * 80)
print("[3] 测试 Token 价格验证...")
print("=" * 80)

token_report = validate_token_prices(token_data)

if 'error' in token_report:
    print(f"✗ 验证失败: {token_report['error']}")
else:
    print("\n📊 验证摘要:")
    summary = token_report.get('summary', {})
    print(f"  总记录数: {summary.get('total_records', 0)}")
    print(f"  有效记录: {summary.get('valid_records', 0)}")
    print(f"  可疑记录: {summary.get('suspicious_records', 0)}")
    print(f"  重复记录: {summary.get('duplicate_records', 0)}")
    print(f"  整体质量: {token_report.get('overall_quality', 'unknown')}")
    
    if 'anomalies' in token_report and len(token_report['anomalies']) > 0:
        print(f"\n⚠️  发现 {len(token_report['anomalies'])} 个异常:")
        for i, anomaly in enumerate(token_report['anomalies'][:5], 1):
            print(f"\n  [{i}] {anomaly.get('provider')} - {anomaly.get('model')}")
            print(f"      输入价格: ${anomaly.get('input_price')}")
            print(f"      输出价格: ${anomaly.get('output_price')}")
            print(f"      问题: {anomaly.get('issue')}")
            print(f"      严重程度: {anomaly.get('severity')}")
            print(f"      建议: {anomaly.get('recommendation')}")
    
    if 'market_insights' in token_report:
        print(f"\n💡 市场洞察:")
        print(f"  {token_report['market_insights']}")
    
    # Save report
    report_file = os.path.join(DATA_DIR, 'validation_report_token.json')
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(token_report, f, indent=2, ensure_ascii=False)
    print(f"\n✓ 验证报告已保存: {report_file}")

print("\n" + "=" * 80)
print("测试完成")
print("=" * 80)
