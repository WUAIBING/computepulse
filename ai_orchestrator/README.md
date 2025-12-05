# AI Orchestrator - Intelligent Multi-AI Collaboration System

## 概述

AI Orchestrator 是一个智能的多AI协作系统，通过机器学习自动优化AI模型选择，降低成本同时保持高数据质量。

### 核心创新

1. **自适应学习** - 系统从历史数据中学习每个AI模型在不同任务类型下的表现
2. **智能路由** - 根据任务类型和学习到的置信度分数自动选择最优AI模型组合
3. **成本优化** - 通过智能路由减少不必要的AI调用，预期降低50-70%成本
4. **持续改进** - 反馈循环确保系统随时间不断优化

## 架构

```
┌─────────────────────────────────────────────────────────────┐
│                      Client Request                          │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    AI Orchestrator                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │    Task      │→ │   Adaptive   │→ │  Performance │      │
│  │  Classifier  │  │    Router    │  │   Tracker    │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                  Parallel Execution Layer                    │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐              │
│  │   Qwen   │    │ DeepSeek │    │  Doubao  │              │
│  └──────────┘    └──────────┘    └──────────┘              │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                  Result Merger & Validator                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  Confidence  │→ │  Validation  │→ │   Feedback   │      │
│  │   Weighted   │  │    Rules     │  │     Loop     │      │
│  │   Merger     │  │              │  │              │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                     Learning Engine                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  Confidence  │  │  Performance │  │   Storage    │      │
│  │   Scoring    │  │   Analysis   │  │   Manager    │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
```

## 核心组件

### 1. AIOrchestrator
主协调器，负责整个请求处理流程。

```python
from ai_orchestrator import AIOrchestrator, AIModel

# 初始化
orchestrator = AIOrchestrator()

# 注册AI模型
orchestrator.register_model(AIModel(
    name="qwen",
    provider="Alibaba",
    cost_per_1m_tokens=0.6,
    avg_response_time=3.5
))

# 处理请求
result = await orchestrator.process_request(
    prompt="获取GPU价格",
    quality_threshold=0.8
)
```

### 2. LearningEngine
学习引擎，使用EWMA算法计算置信度分数。

**算法特点：**
- 指数加权移动平均（EWMA）
- 近期表现权重更高
- 样本量调整
- 平滑处理避免剧烈变化

```python
# 记录性能
orchestrator.record_feedback(
    request_id="req_123",
    model_name="qwen",
    task_type=TaskType.SIMPLE_QUERY,
    was_correct=True,
    response_time=2.5,
    cost=0.0006
)

# 获取置信度分数
confidence = orchestrator.learning_engine.get_confidence_score(
    "qwen", 
    TaskType.SIMPLE_QUERY
)
```

### 3. TaskClassifier
任务分类器，基于关键词分析自动分类请求。

**支持的任务类型：**
- `SIMPLE_QUERY` - 简单查询
- `COMPLEX_REASONING` - 复杂推理
- `DATA_VALIDATION` - 数据验证
- `PRICE_EXTRACTION` - 价格提取
- `HISTORICAL_ANALYSIS` - 历史分析

### 4. AdaptiveRouter
自适应路由器，根据置信度分数选择最优AI模型组合。

**路由策略：**
- 简单查询 → 1个模型（最快最便宜）
- 复杂推理 → 2个模型（交叉验证）
- 数据验证 → 3个模型（多重验证）
- 低置信度 → 增加模型数量

### 5. StorageManager
存储管理器，持久化学习数据和性能历史。

**存储格式：**
- `confidence_scores.json` - 置信度分数（JSON）
- `performance_history.jsonl` - 性能历史（JSONL，每行一条记录）

## 快速开始

### 安装

```bash
cd computepulse
pip install -r requirements.txt
```

### 运行演示

```bash
python scripts/fetch_prices_optimized_v2.py
```

### 基本使用

```python
import asyncio
from ai_orchestrator import AIOrchestrator, AIModel, TaskType

async def main():
    # 1. 初始化orchestrator
    orchestrator = AIOrchestrator()
    
    # 2. 注册AI模型
    orchestrator.register_model(AIModel(
        name="qwen",
        provider="Alibaba",
        cost_per_1m_tokens=0.6,
        avg_response_time=3.5
    ))
    
    # 3. 处理请求
    result = await orchestrator.process_request(
        prompt="获取最新的GPU价格",
        quality_threshold=0.8,
        cost_limit=0.01
    )
    
    # 4. 查看结果
    print(f"使用的模型: {result.contributing_models}")
    print(f"置信度分数: {result.confidence_scores}")
    
    # 5. 记录反馈（用于学习）
    orchestrator.record_feedback(
        request_id=result.metadata['request_id'],
        model_name="qwen",
        task_type=TaskType.PRICE_EXTRACTION,
        was_correct=True,
        response_time=2.5,
        cost=0.0006
    )
    
    # 6. 查看性能报告
    report = orchestrator.get_performance_report(model_name="qwen")
    print(f"准确率: {report['accuracy']:.1%}")
    print(f"平均响应时间: {report['avg_response_time']:.2f}s")

asyncio.run(main())
```

## 配置

### 配置文件

```python
from ai_orchestrator import OrchestratorConfig

config = OrchestratorConfig(
    # 质量和成本阈值
    default_quality_threshold=0.8,
    default_cost_limit=None,
    
    # 学习引擎参数
    confidence_decay_factor=0.95,  # EWMA衰减因子
    min_samples_for_confidence=10,  # 最小样本量
    confidence_smoothing_factor=0.7,  # 平滑因子
    
    # 路由参数
    simple_query_model_count=1,
    complex_reasoning_model_count=2,
    validation_model_count=3,
    
    # 并行执行
    model_timeout_seconds=30.0,
    
    # 存储路径
    storage_dir="data/ai_orchestrator"
)

orchestrator = AIOrchestrator(config)
```

## 性能指标

### 预期效果

| 指标 | 第1个月 | 第3个月 | 第6个月 |
|------|---------|---------|---------|
| 成本降低 | 30-50% | 50-70% | 60-75% |
| 准确率提升 | +3-5% | +5-10% | +8-12% |
| 响应速度 | +20% | +30% | +35% |

### 监控指标

```python
# 获取性能报告
report = orchestrator.get_performance_report()

print(f"总请求数: {report['total_records']}")
print(f"准确率: {report['accuracy']:.1%}")
print(f"平均响应时间: {report['avg_response_time']:.2f}s")
print(f"总成本: ${report['total_cost']:.4f}")
print(f"平均成本: ${report['avg_cost']:.6f}")

# 获取置信度分数
scores = orchestrator.get_confidence_scores(TaskType.SIMPLE_QUERY)
for model, score in scores.items():
    print(f"{model}: {score:.3f}")
```

## 集成到现有系统

### 替换现有的fetch_prices.py

```python
# 旧代码
qwen_data = call_qwen_with_search(prompt)
deepseek_data = call_deepseek_with_reasoning(prompt)
doubao_data = call_doubao_with_search(prompt)
final_data = merge_data(qwen_data, deepseek_data, doubao_data)

# 新代码（使用orchestrator）
result = await orchestrator.process_request(prompt)
final_data = result.data

# 记录反馈以便学习
orchestrator.record_feedback(
    request_id=result.metadata['request_id'],
    model_name="qwen",
    task_type=TaskType.PRICE_EXTRACTION,
    was_correct=validate_data(final_data),
    response_time=2.5,
    cost=0.0006
)
```

## 学习机制详解

### EWMA算法

```python
def calculate_confidence_score(performance_history):
    """
    使用指数加权移动平均计算置信度分数
    
    公式: confidence = Σ(correct_i * decay^i) / Σ(decay^i)
    其中 decay = 0.95（可配置）
    """
    decay_factor = 0.95
    total_weight = 0.0
    weighted_correct = 0.0
    
    for i, record in enumerate(reversed(performance_history)):
        weight = decay_factor ** i
        total_weight += weight
        if record.was_correct:
            weighted_correct += weight
    
    accuracy = weighted_correct / total_weight
    
    # 样本量调整
    sample_size = len(performance_history)
    confidence_adjustment = min(1.0, sample_size / 100)
    
    # 最终分数
    confidence = accuracy * confidence_adjustment + 0.5 * (1 - confidence_adjustment)
    
    return confidence
```

### 学习过程

1. **记录性能** - 每次AI调用后记录结果
2. **计算置信度** - 使用EWMA算法计算新的置信度分数
3. **平滑处理** - 避免分数剧烈变化
4. **持久化** - 保存到存储
5. **应用到路由** - 下次请求使用更新后的分数

## 故障处理

### 存储失败

系统会自动降级到内存模式：

```python
# 存储失败时
logger.error("Storage failed, using in-memory fallback")
# 系统继续运行，使用内存中的数据
```

### AI模型失败

系统会自动使用其他可用模型：

```python
# 如果Qwen失败
# 系统自动使用DeepSeek和Doubao
# 不会中断服务
```

### 低置信度处理

当所有模型置信度都很低时：

```python
if all(score < 0.5 for score in confidence_scores.values()):
    # 标记结果需要人工审核
    result.flagged_for_review = True
    logger.warning("Low confidence, flagged for manual review")
```

## 未来路线图

### Phase 2: 高级学习算法（3-6个月）
- Thompson Sampling
- Upper Confidence Bound (UCB)
- 上下文感知路由

### Phase 3: 预测智能（6-12个月）
- 性能趋势预测
- 异常检测
- 主动模型切换

### Phase 4: 神经网络优化（12-18个月）
- 神经网络任务分类器
- 端到端强化学习
- 自动特征提取

### Phase 5: 分布式架构（18-24个月）
- 分布式置信度存储
- 跨实例学习共享
- 自动扩展

## 贡献

欢迎贡献！请查看 [ROADMAP.md](../specs/ai-collaboration-optimization/ROADMAP.md) 了解未来计划。

## 许可证

MIT License

## 联系方式

- 项目: ComputePulse
- 文档: [Design Document](../specs/ai-collaboration-optimization/design.md)
- 需求: [Requirements](../specs/ai-collaboration-optimization/requirements.md)
