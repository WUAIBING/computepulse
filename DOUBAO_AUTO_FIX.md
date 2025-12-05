# Doubao 自动修复机制

## 🎯 概述

Doubao 不仅能发现数据问题，还能**自动修复**它们！

```
发现问题 → 分析问题 → 自动修复 → 验证修复
```

---

## 🔧 修复策略

### 按严重程度分级处理

| 严重程度 | 标识 | 处理策略 | 示例 |
|---------|------|---------|------|
| **高 (High)** | 🔴 | 自动移除或标记 | 价格异常高（偏离 >100%） |
| **中 (Medium)** | 🟡 | 标记需审核 | 价格偏离 50-100% |
| **低 (Low)** | 🟢 | 保留并记录 | 轻微格式问题 |

### 自动修复流程

```python
def fix_anomalies(data, anomalies, data_type):
    """
    1. 识别异常记录
    2. 根据严重程度决定处理方式
    3. 高严重度 → 移除
    4. 中严重度 → 标记需审核
    5. 低严重度 → 保留
    """
```

---

## 🤖 智能修复功能

### Doubao 联网搜索修复

对于无法自动判断的问题，Doubao 可以：
1. 使用 web_search 工具联网搜索
2. 找到正确的价格信息
3. 返回修正后的数据

```python
def ask_doubao_to_fix(anomaly, data_type):
    """
    让 Doubao 联网搜索正确的价格
    
    输入：异常数据
    输出：修正后的数据 + 数据来源
    """
```

### 示例：修复异常高价

**问题**：
```json
{
  "provider": "阿里云",
  "gpu": "H100",
  "price": 27.78,
  "issue": "价格异常高，比市场平均高 10 倍"
}
```

**Doubao 分析**：
1. 🔍 联网搜索阿里云 H100 官方价格
2. 📊 对比市场平均价格
3. 💡 发现可能是配置错误（包含了其他服务）

**修复结果**：
```json
{
  "provider": "阿里云",
  "region": "China-Hangzhou",
  "gpu": "H100",
  "price": 2.8,
  "source": "阿里云官网 2025年12月价格",
  "_fixed_by": "doubao",
  "_original_price": 27.78
}
```

---

## 📋 修复类型

### 1. 价格异常修复

**高价异常**：
- 检测：价格 > 市场平均 × 2
- 处理：联网搜索正确价格或移除
- 示例：$27.78 → $2.8

**低价异常**：
- 检测：价格 < 市场平均 × 0.5
- 处理：验证是否为促销价或错误
- 示例：$0.5 → 移除（不合理）

### 2. 重复数据修复

**检测**：
```python
key = f"{provider}_{region}_{gpu}"
# 相同 key 的记录视为重复
```

**处理**：
- 保留最新的记录
- 移除旧记录
- 记录合并日志

### 3. 数据完整性修复

**缺失字段**：
- 检测：必需字段为空
- 处理：尝试从其他来源补全或移除

**格式错误**：
- 检测：数据类型不匹配
- 处理：自动转换或标记

### 4. 市场趋势修复

**过时数据**：
- 检测：价格与当前市场趋势不符
- 处理：联网搜索最新价格
- 标记：添加 `_updated_date` 字段

---

## 🔄 完整修复流程

### 步骤 1：数据采集

```python
# Qwen + DeepSeek 采集数据
gpu_data = fetch_from_sources()
```

### 步骤 2：基础验证

```python
# 价格范围验证
validated_data = [item for item in gpu_data if validate_price(item)]
```

### 步骤 3：Doubao 深度验证

```python
# Doubao 分析数据质量
report = validate_gpu_prices(validated_data)
```

### 步骤 4：自动修复

```python
# 根据验证报告自动修复
fixed_data, summary = fix_anomalies(validated_data, report['anomalies'], 'gpu')

print(f"✅ 修复了 {summary['fixed']} 条记录")
print(f"🗑️  移除了 {summary['removed']} 条无效记录")
print(f"⚠️  {summary['manual_review']} 条需要人工审核")
```

### 步骤 5：智能修复（可选）

```python
# 对于无法自动修复的，让 Doubao 联网搜索
for anomaly in high_severity_anomalies:
    corrected = ask_doubao_to_fix(anomaly, 'gpu')
    if corrected:
        apply_fix(corrected)
```

### 步骤 6：保存修复后的数据

```python
# 保存到文件
save_data(fixed_data)

# 保存修复日志
save_fix_log(summary)
```

---

## 📊 修复报告

### 修复摘要

```json
{
  "timestamp": "2025-12-04T23:50:00",
  "total_records": 77,
  "anomalies_found": 5,
  "fixes_applied": {
    "auto_fixed": 2,
    "removed": 1,
    "manual_review": 2
  },
  "data_quality": {
    "before": "fair",
    "after": "good"
  }
}
```

### 详细修复日志

```json
{
  "fixes": [
    {
      "record_id": "阿里云_China_H100",
      "issue": "价格异常高",
      "action": "price_corrected",
      "before": {"price": 27.78},
      "after": {"price": 2.8},
      "source": "阿里云官网",
      "confidence": "high"
    },
    {
      "record_id": "TestCloud_Global_H100",
      "issue": "价格异常低，供应商不可信",
      "action": "removed",
      "reason": "无法验证供应商真实性"
    }
  ]
}
```

---

## 🎯 修复策略详解

### 策略 1：自动移除

**触发条件**：
- 严重程度 = 高
- 建议包含"删除"、"移除"、"remove"

**执行**：
```python
if severity == 'high' and '删除' in recommendation:
    # 移除记录
    continue
```

**日志**：
```
🗑️  Removing: 阿里云_H100 (high severity)
```

### 策略 2：标记审核

**触发条件**：
- 严重程度 = 高，但不建议删除
- 严重程度 = 中

**执行**：
```python
record['_needs_review'] = True
record['_issue'] = anomaly['issue']
record['_severity'] = anomaly['severity']
```

**日志**：
```
⚠️  Manual review needed: 阿里云_H100
```

### 策略 3：智能修复

**触发条件**：
- 价格异常但供应商可信
- 有明确的修复建议

**执行**：
```python
# Doubao 联网搜索正确价格
corrected = ask_doubao_to_fix(anomaly, 'gpu')
if corrected:
    apply_correction(record, corrected)
```

**日志**：
```
✅ Auto-fixed: 阿里云_H100 ($27.78 → $2.8)
```

---

## 🚀 使用方法

### 自动修复（集成在主流程中）

```bash
# 数据采集 + 验证 + 自动修复
python scripts/fetch_prices_optimized.py --once
```

输出示例：
```
[2025-12-04 23:50:00] Starting Doubao data validation and fixing...
[2025-12-04 23:52:30] ⚠️  Found 5 GPU price anomalies
[2025-12-04 23:52:35] ✅ Auto-fixed 2 GPU records
[2025-12-04 23:52:35] 🗑️  Removed 1 invalid GPU records
[2025-12-04 23:52:35] Fixed GPU data saved
  🔴 阿里云 H100: 价格异常高，比市场平均高 10 倍
  🟡 TestCloud H100: 供应商不可信，需要人工核实
```

### 测试自动修复

```bash
# 测试修复功能
python scripts/test_auto_fix.py
```

### 查看修复报告

```bash
# 查看验证报告（包含修复建议）
cat public/data/validation_report_gpu.json
```

---

## ⚙️ 配置选项

### 启用/禁用自动修复

```python
# 在 fetch_prices_optimized.py 中
ENABLE_AUTO_FIX = True  # 默认启用
```

### 调整修复阈值

```python
# 价格偏离阈值
PRICE_DEVIATION_HIGH = 2.0  # 2倍视为异常高
PRICE_DEVIATION_LOW = 0.5   # 0.5倍视为异常低
```

### 配置修复策略

```python
# 修复策略配置
FIX_STRATEGY = {
    'high_severity': 'remove',      # 高严重度：移除
    'medium_severity': 'flag',      # 中严重度：标记
    'low_severity': 'keep',         # 低严重度：保留
    'enable_smart_fix': True,       # 启用智能修复
    'smart_fix_timeout': 240        # 智能修复超时（秒）
}
```

---

## 📈 效果评估

### 修复前 vs 修复后

| 指标 | 修复前 | 修复后 | 改善 |
|------|--------|--------|------|
| 总记录数 | 77 | 75 | -2 (移除无效) |
| 异常记录 | 5 | 2 | -60% |
| 数据质量 | Fair | Good | +1 级 |
| 需人工审核 | 5 | 2 | -60% |

### 修复成功率

- **自动修复成功率**：40% (2/5)
- **自动移除成功率**：20% (1/5)
- **需人工审核**：40% (2/5)

---

## 🎯 最佳实践

### 1. 定期运行验证和修复

```bash
# 每天运行一次
0 0 * * * python scripts/fetch_prices_optimized.py --once
```

### 2. 监控修复日志

```bash
# 查看修复摘要
grep "Auto-fixed" logs/fetch.log
grep "Removed" logs/fetch.log
```

### 3. 人工审核高优先级问题

```bash
# 查找需要人工审核的记录
jq '.[] | select(._needs_review == true)' public/data/gpu_prices.json
```

### 4. 定期清理标记

```python
# 清理已审核的标记
for record in data:
    if '_needs_review' in record:
        # 审核后移除标记
        del record['_needs_review']
```

---

## 💡 未来改进

### 1. 机器学习辅助

- 训练模型识别异常模式
- 自动学习正常价格范围
- 预测价格趋势

### 2. 多源交叉验证

- 对比多个数据源
- 投票决定正确值
- 提高修复准确性

### 3. 实时修复

- 在数据采集时实时验证
- 立即修复明显错误
- 减少后处理时间

### 4. 用户反馈循环

- 收集用户对修复的反馈
- 优化修复策略
- 持续改进准确性

---

## 📝 总结

### Doubao 的双重角色

1. **数据审核员** 🔍
   - 发现数据问题
   - 分析问题严重程度
   - 提供修复建议

2. **数据修复员** 🔧
   - 自动修复简单问题
   - 联网搜索正确信息
   - 智能更正错误数据

### 核心优势

- ✅ **自动化**：减少人工干预
- ✅ **智能化**：联网搜索正确信息
- ✅ **可追溯**：完整的修复日志
- ✅ **可配置**：灵活的修复策略

### 数据质量保证

通过 Doubao 的自动修复，ComputePulse 的数据质量从 **Fair** 提升到 **Good**，异常记录减少 **60%**！

---

**文档版本**：1.0  
**更新时间**：2025年12月04日  
**维护者**：ComputePulse Team
