#!/usr/bin/env python3
"""Test Doubao's automatic data fixing capabilities"""

import json
import os
import sys

# Add parent directory to path
sys.path.append(os.path.dirname(__file__))

from data_validator import validate_gpu_prices, fix_anomalies, ask_doubao_to_fix

print("=" * 80)
print("Doubao 自动修复测试")
print("=" * 80)

# Create test data with known issues
test_gpu_data = [
    # Normal data
    {"provider": "AWS", "region": "US-East", "gpu": "H100", "price": 2.79},
    {"provider": "Lambda Labs", "region": "US-West", "gpu": "H100", "price": 2.5},
    
    # Anomaly 1: Price too high (should be flagged)
    {"provider": "阿里云", "region": "China-Hangzhou", "gpu": "H100", "price": 27.78},
    
    # Anomaly 2: Price too low (suspicious)
    {"provider": "TestCloud", "region": "Global", "gpu": "H100", "price": 0.5},
    
    # Anomaly 3: Duplicate
    {"provider": "AWS", "region": "US-East", "gpu": "H100", "price": 2.8},
]

print("\n[1] 测试数据（包含已知问题）:")
print(json.dumps(test_gpu_data, indent=2, ensure_ascii=False))

print("\n" + "=" * 80)
print("[2] 运行 Doubao 验证...")
print("=" * 80)

# Validate
report = validate_gpu_prices(test_gpu_data)

if 'error' in report:
    print(f"✗ 验证失败: {report['error']}")
    sys.exit(1)

print("\n📊 验证结果:")
summary = report.get('summary', {})
print(f"  总记录数: {summary.get('total_records', 0)}")
print(f"  有效记录: {summary.get('valid_records', 0)}")
print(f"  可疑记录: {summary.get('suspicious_records', 0)}")
print(f"  整体质量: {report.get('overall_quality', 'unknown')}")

if 'anomalies' in report and len(report['anomalies']) > 0:
    print(f"\n⚠️  发现 {len(report['anomalies'])} 个异常:")
    for i, anomaly in enumerate(report['anomalies'], 1):
        print(f"\n  [{i}] {anomaly.get('provider')} - {anomaly.get('gpu')}")
        print(f"      价格: ${anomaly.get('price')}")
        print(f"      问题: {anomaly.get('issue')}")
        print(f"      严重程度: {anomaly.get('severity')}")
        print(f"      建议: {anomaly.get('recommendation')}")

print("\n" + "=" * 80)
print("[3] 运行自动修复...")
print("=" * 80)

# Auto-fix
fixed_data, fix_summary = fix_anomalies(test_gpu_data, report.get('anomalies', []), 'gpu')

print(f"\n✅ 修复摘要:")
print(f"  修复记录: {fix_summary['fixed']}")
print(f"  移除记录: {fix_summary['removed']}")
print(f"  需人工审核: {fix_summary['manual_review']}")

print(f"\n📋 修复后的数据（{len(fixed_data)} 条）:")
print(json.dumps(fixed_data, indent=2, ensure_ascii=False))

print("\n" + "=" * 80)
print("[4] 测试 Doubao 智能修复（联网搜索正确价格）...")
print("=" * 80)

# Test intelligent fix for one anomaly
if report.get('anomalies'):
    test_anomaly = report['anomalies'][0]
    print(f"\n尝试修复: {test_anomaly.get('provider')} {test_anomaly.get('gpu')}")
    print(f"当前价格: ${test_anomaly.get('price')}")
    print(f"问题: {test_anomaly.get('issue')}")
    
    print("\n🔍 Doubao 正在联网搜索正确价格...")
    corrected = ask_doubao_to_fix(test_anomaly, 'gpu')
    
    if corrected:
        print("\n✅ Doubao 找到了正确的数据:")
        print(json.dumps(corrected, indent=2, ensure_ascii=False))
    else:
        print("\n⚠️  Doubao 无法自动修复，需要人工审核")

print("\n" + "=" * 80)
print("测试完成")
print("=" * 80)

print("\n💡 自动修复策略:")
print("  🔴 高严重度: 自动移除或标记为需人工审核")
print("  🟡 中严重度: 标记为需审核，保留数据")
print("  🟢 低严重度: 保留数据，记录问题")
print("\n  🤖 智能修复: Doubao 可以联网搜索正确价格并自动更正")
