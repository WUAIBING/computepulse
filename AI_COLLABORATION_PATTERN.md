# AI 协作模式文档 (Multi-AI Collaboration Pattern)

## 概述 (Overview)

本文档记录了 ComputePulse 项目中使用的三个 AI 模型协作模式，用于实时数据抓取、验证和质量保证。这种模式可以复用到任何需要高质量、实时数据的项目中。

**核心理念：** 多个 AI 模型并行工作，互相验证，取长补短，确保数据的准确性和可靠性。

---

## 三个 AI 模型的角色分工

### 1. Qwen (通义千问) - 快速数据获取者
**API Provider:** 阿里云 DashScope  
**主要特点:**
- ⚡ 响应速度快（通常 2-5 秒）
- 🔍 内置联网搜索功能 (`enable_search=True`)
- 📊 数据覆盖面广，适合快速获取市场数据
- 💰 成本效益高

**适用场景:**
- GPU 价格抓取
- Token 价格抓取
- 市场趋势数据
- 实时新闻和财报数据

**代码示例:**
```python
from dashscope import Generation

def call_qwen_with_search(prompt: str, max_retries: int = 2) -> Optional[str]:
    """Call Qwen API with search enabled."""
    for attempt in range(max_retries):
        try:
            response = Generation.call(
                model='qwen-max',
                prompt=prompt,
                enable_search=True
            )
            if response.status_code == 200:
                return response.output.text
        except Exception as e:
            print(f"Qwen Call Failed (attempt {attempt+1}): {e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # Exponential backoff
    return None
```

---

### 2. DeepSeek - 推理验证者
**API Provider:** 阿里云 DashScope (OpenAI-compatible)  
**主要特点:**
- 🧠 强大的推理能力 (`enable_thinking` 模式)
- ✅ 适合数据验证和逻辑推理
- 📈 对复杂数据关系的理解能力强
- 🎯 高准确度，适合作为数据验证的"第二意见"

**适用场景:**
- 验证 Qwen 获取的数据
- 复杂计算和推理
- 数据趋势分析
- 异常检测

**代码示例:**
```python
from openai import OpenAI

deepseek_client = OpenAI(
    api_key=dashscope.api_key,
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
)

def call_deepseek_with_reasoning(prompt: str, max_retries: int = 2) -> Optional[str]:
    """Call DeepSeek API with reasoning mode."""
    for attempt in range(max_retries):
        try:
            completion = deepseek_client.chat.completions.create(
                model="deepseek-v3.2-exp",
                messages=[{"role": "user", "content": prompt}],
                extra_body={"enable_thinking": False},  # 快速模式
                stream=False,
            )
            if completion.choices and len(completion.choices) > 0:
                return completion.choices[0].message.content
        except Exception as e:
            print(f"DeepSeek Call Failed (attempt {attempt+1}): {e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
    return None
```

---

### 3. Doubao (豆包) - 质量检查者
**API Provider:** 字节跳动火山引擎  
**主要特点:**
- 🔍 强大的 `web_search` 工具
- 🕐 时间感知能力强（自动获取当前时间）
- 🛡️ 适合数据质量验证和异常检测
- ⚠️ 响应较慢（10-30 秒），但数据质量高

**适用场景:**
- 数据质量验证
- 异常数据检测和修复
- 最终数据审核
- 生成验证报告

**代码示例:**
```python
import requests

def call_doubao_with_search(prompt: str, max_retries: int = 2) -> Optional[str]:
    """Call Doubao API with web search enabled."""
    endpoint_id = "doubao-seed-1-6-251015"  # Your endpoint ID
    headers = {
        "Authorization": f"Bearer {volc_api_key}",
        "Content-Type": "application/json"
    }
    
    for attempt in range(max_retries):
        try:
            url = "https://ark.cn-beijing.volces.com/api/v3/responses"
            payload = {
                "model": endpoint_id,
                "stream": False,
                "tools": [{"type": "web_search"}],  # 启用联网搜索
                "input": [
                    {
                        "role": "user",
                        "content": [{"type": "input_text", "text": prompt}]
                    }
                ]
            }
            
            response = requests.post(url, headers=headers, json=payload, timeout=120)
            if response.status_code == 200:
                res_json = response.json()
                # Extract text from response
                if 'output' in res_json:
                    for item in res_json['output']:
                        if item.get('type') == 'message' and 'content' in item:
                            for content_item in item['content']:
                                if content_item.get('type') in ['text', 'output_text']:
                                    text = content_item.get('text') or content_item.get('output_text')
                                    if text:
                                        return text
        except Exception as e:
            print(f"Doubao Call Failed (attempt {attempt+1}): {e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
    
    return None
```

---

## 协作模式架构

### 模式 1: 并行获取 + 优先级合并 (Parallel Fetch + Priority Merge)

**工作流程:**
```
┌─────────────────────────────────────────────────────────────┐
│                    用户请求数据                              │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
        ┌───────────────────┴───────────────────┐
        │                                       │
        ▼                                       ▼
┌──────────────┐                      ┌──────────────┐
│   Qwen API   │                      │ DeepSeek API │
│  (快速获取)   │                      │  (推理验证)   │
└──────────────┘                      └──────────────┘
        │                                       │
        │                                       │
        └───────────────────┬───────────────────┘
                            ▼
                    ┌──────────────┐
                    │  数据验证层   │
                    │ (Validation)  │
                    └──────────────┘
                            │
                            ▼
                    ┌──────────────┐
                    │  优先级合并   │
                    │ DeepSeek > Qwen │
                    │  > Existing   │
                    └──────────────┘
                            │
                            ▼
                    ┌──────────────┐
                    │  返回最终数据 │
                    └──────────────┘
```

**代码实现:**
```python
def fetch_data_with_collaboration():
    """并行获取数据，按优先级合并"""
    
    # 1. 并行调用多个 AI
    qwen_content = call_qwen_with_search(prompt)
    deepseek_content = call_deepseek_with_reasoning(prompt)
    doubao_content = call_doubao_with_search(prompt) if ENABLE_DOUBAO else None
    
    # 2. 解析 JSON 响应
    qwen_data = clean_and_parse_json(qwen_content)
    deepseek_data = clean_and_parse_json(deepseek_content)
    doubao_data = clean_and_parse_json(doubao_content) if doubao_content else None
    
    # 3. 数据验证
    if isinstance(qwen_data, list):
        qwen_data = [item for item in qwen_data if validate_data(item)]
    if isinstance(deepseek_data, list):
        deepseek_data = [item for item in deepseek_data if validate_data(item)]
    
    # 4. 加载现有数据作为后备
    existing_data = load_existing_data()
    
    # 5. 优先级合并 (DeepSeek > Qwen > Doubao > Existing)
    final_data = merge_data_improved(
        qwen_data, 
        deepseek_data, 
        doubao_data, 
        existing_data
    )
    
    return final_data
```

---

### 模式 2: 数据验证 + 自动修复 (Validation + Auto-Fix)

**工作流程:**
```
┌─────────────────────────────────────────────────────────────┐
│              Qwen + DeepSeek 获取初始数据                     │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
                    ┌──────────────┐
                    │  Doubao 验证  │
                    │ (Quality Check)│
                    └──────────────┘
                            │
                ┌───────────┴───────────┐
                │                       │
                ▼                       ▼
        ┌──────────────┐        ┌──────────────┐
        │  数据正常     │        │  发现异常     │
        │  直接使用     │        │  自动修复     │
        └──────────────┘        └──────────────┘
                │                       │
                │                       ▼
                │               ┌──────────────┐
                │               │ Doubao 搜索  │
                │               │  正确数据     │
                │               └──────────────┘
                │                       │
                └───────────────────────┘
                            │
                            ▼
                    ┌──────────────┐
                    │  保存修复后   │
                    │    的数据     │
                    └──────────────┘
```

**代码实现:**
```python
def validate_and_fix_with_doubao(gpu_data: List[Dict], token_data: List[Dict]) -> tuple:
    """使用 Doubao 验证和修复数据质量问题"""
    
    # 1. 验证数据
    gpu_report = validate_gpu_prices(gpu_data)
    token_report = validate_token_prices(token_data)
    
    fixed_gpu_data = gpu_data.copy()
    fixed_token_data = token_data.copy()
    
    # 2. 如果发现异常，自动修复
    if 'anomalies' in gpu_report and len(gpu_report['anomalies']) > 0:
        print(f"⚠️  Found {len(gpu_report['anomalies'])} GPU price anomalies")
        
        # 使用 Doubao 搜索正确数据
        fixed_gpu_data, fix_summary = fix_anomalies(
            gpu_data, 
            gpu_report['anomalies'], 
            'gpu'
        )
        
        if fix_summary['fixed'] > 0:
            print(f"✅ Auto-fixed {fix_summary['fixed']} GPU records")
            # 保存修复后的数据
            save_data(fixed_gpu_data, GPU_FILE)
    
    return fixed_gpu_data, fixed_token_data
```

---

## 数据合并策略

### 优先级规则
```python
def merge_data_improved(
    qwen_data: Optional[Any],
    deepseek_data: Optional[Any],
    doubao_data: Optional[Any],
    existing_data: Optional[Any],
    key_func: Optional[callable] = None
) -> Any:
    """
    优先级: DeepSeek > Qwen > Doubao > Existing
    
    原因:
    - DeepSeek: 推理能力强，数据准确度高
    - Qwen: 速度快，覆盖面广
    - Doubao: 验证能力强，但速度慢
    - Existing: 历史数据，作为最后的后备
    """
    
    # 处理字典类型（如 grid_load）
    if isinstance(deepseek_data, dict) or isinstance(qwen_data, dict):
        merged = {}
        if isinstance(existing_data, dict):
            merged.update(existing_data)
        if isinstance(doubao_data, dict):
            merged.update(doubao_data)
        if isinstance(qwen_data, dict):
            merged.update(qwen_data)
        if isinstance(deepseek_data, dict):
            merged.update(deepseek_data)  # 最高优先级
        return merged if merged else existing_data
    
    # 处理列表类型（如 GPU/Token prices）
    if not key_func:
        key_func = lambda x: f"{x.get('provider', '')}_{x.get('model', '')}_{x.get('gpu', '')}"
    
    merged_dict = {}
    
    # 按优先级添加数据
    if isinstance(existing_data, list):
        for item in existing_data:
            merged_dict[key_func(item)] = item
    
    if isinstance(doubao_data, list):
        for item in doubao_data:
            merged_dict[key_func(item)] = item
    
    if isinstance(qwen_data, list):
        for item in qwen_data:
            merged_dict[key_func(item)] = item
    
    if isinstance(deepseek_data, list):
        for item in deepseek_data:
            merged_dict[key_func(item)] = item  # 覆盖之前的数据
    
    return list(merged_dict.values()) if merged_dict else (existing_data or [])
```

---

## 数据验证规则

### 1. GPU 价格验证
```python
GPU_PRICE_MIN = 0.1   # 最低合理价格 (USD/小时)
GPU_PRICE_MAX = 50.0  # 最高合理价格 (USD/小时)

def validate_gpu_price(item: Dict) -> bool:
    """验证 GPU 价格数据"""
    required_fields = ['provider', 'gpu', 'price']
    
    # 检查必需字段
    for field in required_fields:
        if field not in item:
            return False
    
    # 验证价格范围
    price = item.get('price', 0)
    if not isinstance(price, (int, float)):
        return False
    
    if not (GPU_PRICE_MIN <= price <= GPU_PRICE_MAX):
        print(f"Price out of range: ${price}")
        return False
    
    return True
```

### 2. Token 价格验证
```python
TOKEN_PRICE_MIN = 0.001   # 最低合理价格 (USD/1M tokens)
TOKEN_PRICE_MAX = 100.0   # 最高合理价格 (USD/1M tokens)

def validate_token_price(item: Dict) -> bool:
    """验证 Token 价格数据"""
    required_fields = ['provider', 'model', 'input_price', 'output_price']
    
    for field in required_fields:
        if field not in item:
            return False
    
    # 验证价格范围
    for price_field in ['input_price', 'output_price']:
        price = item.get(price_field)
        
        if price is None:
            return False  # 跳过空值
        
        if not isinstance(price, (int, float)):
            return False
        
        if not (TOKEN_PRICE_MIN <= price <= TOKEN_PRICE_MAX):
            return False
    
    return True
```

---

## 错误处理和重试机制

### 指数退避重试 (Exponential Backoff)
```python
def call_api_with_retry(api_func, prompt: str, max_retries: int = 2):
    """通用的 API 调用重试机制"""
    for attempt in range(max_retries):
        try:
            result = api_func(prompt)
            if result:
                return result
        except Exception as e:
            print(f"API Call Failed (attempt {attempt+1}/{max_retries}): {e}")
            
            if attempt < max_retries - 1:
                # 指数退避: 2^0=1秒, 2^1=2秒, 2^2=4秒...
                sleep_time = 2 ** attempt
                print(f"Retrying in {sleep_time} seconds...")
                time.sleep(sleep_time)
    
    return None
```

---

## 最佳实践

### 1. Prompt 设计原则
```python
# ✅ 好的 Prompt
prompt = """
请使用联网搜索功能查找最新数据。

搜索要求：
1. 获取 2024 年最新的 GPU 价格
2. 搜索权威来源：NVIDIA 官网、AWS、Google Cloud
3. 价格单位：美元/小时

返回 JSON 格式：
[
  {"provider": "AWS", "gpu": "H100", "price": 3.2}
]

要求：
- 只返回 JSON，不要包含 Markdown 标记
- 必须基于真实搜索结果，不要编造
"""

# ❌ 不好的 Prompt（包含示例数据）
prompt = """
获取 GPU 价格，例如：
[
  {"provider": "AWS", "gpu": "H100", "price": 3.2}
]
"""
# 问题：AI 可能直接返回示例数据，而不是搜索真实数据
```

### 2. 数据源优先级
```
1. 官方网站 > 财报 > 新闻报道
2. 最新数据 > 历史数据
3. 多个来源交叉验证
```

### 3. 性能优化
```python
# 可选：禁用慢速 AI
ENABLE_DOUBAO = False  # Doubao 响应慢，可在快速模式下禁用

# 并行调用（不等待）
import concurrent.futures

def fetch_all_parallel():
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        future_qwen = executor.submit(call_qwen_with_search, prompt)
        future_deepseek = executor.submit(call_deepseek_with_reasoning, prompt)
        future_doubao = executor.submit(call_doubao_with_search, prompt)
        
        qwen_data = future_qwen.result()
        deepseek_data = future_deepseek.result()
        doubao_data = future_doubao.result()
    
    return qwen_data, deepseek_data, doubao_data
```

---

## 成本分析

### API 调用成本（估算）
| AI 模型 | 成本/1M Tokens | 平均响应时间 | 推荐使用场景 |
|---------|---------------|-------------|-------------|
| Qwen    | ¥0.4-0.8      | 2-5 秒      | 日常数据获取 |
| DeepSeek| ¥0.5-1.0      | 3-8 秒      | 数据验证 |
| Doubao  | ¥0.8-2.0      | 10-30 秒    | 质量检查 |

### 成本优化建议
1. **日常模式**: 只使用 Qwen + DeepSeek
2. **质量模式**: 启用 Doubao 进行额外验证
3. **快速模式**: 只使用 Qwen，适合开发测试

---

## 实际应用案例

### 案例 1: GPU 价格抓取
```python
def fetch_gpu_prices():
    """抓取 GPU 价格"""
    prompt = """
    请使用联网搜索功能完成以下任务：
    
    1. 搜索英伟达（NVIDIA）最新财报数据
    2. 搜索主流云服务商的 GPU 租赁价格
    
    目标 GPU: H100, H200, A100, L40S
    云服务商: AWS, Google Cloud, Azure, Lambda Labs
    
    返回 JSON 数组格式：
    [
      {"provider": "Lambda", "region": "US-West", "gpu": "H100", "price": 2.13}
    ]
    """
    
    # 并行获取
    qwen_data = call_qwen_with_search(prompt)
    deepseek_data = call_deepseek_with_reasoning(prompt)
    
    # 验证和合并
    final_data = merge_and_validate(qwen_data, deepseek_data)
    
    # 保存
    save_data(final_data, 'gpu_prices.json')
```

### 案例 2: 历史数据抓取
```python
def fetch_annual_energy_history():
    """抓取历史年度能耗数据"""
    prompt = """
    请使用联网搜索功能，查找全球 AI 数据中心的历史年度能耗数据。
    
    搜索要求：
    1. 获取 2018-2024 年每年的全球 AI 数据中心总能耗（TWh）
    2. 搜索权威来源：IEA、BloombergNEF、学术研究报告
    
    返回 JSON 数组：
    [
      {"year": "2018", "value": 78.2, "source": "IEA Report"}
    ]
    
    要求：
    - 数据应该基于真实搜索结果，不要编造
    - 每个数据点必须标注真实来源
    """
    
    # 使用 DeepSeek 的推理能力处理历史数据
    deepseek_data = call_deepseek_with_reasoning(prompt)
    qwen_data = call_qwen_with_search(prompt)
    
    # DeepSeek 优先（推理能力强）
    final_data = deepseek_data or qwen_data
    
    return final_data
```

---

## 监控和日志

### 日志格式
```python
import logging
from datetime import datetime

def log_api_call(model: str, status: str, data_count: int = 0):
    """记录 API 调用"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{timestamp}] {model} API: {status} - {data_count} records")

# 使用示例
log_api_call("Qwen", "Success", len(qwen_data))
log_api_call("DeepSeek", "Success", len(deepseek_data))
log_api_call("Doubao", "Failed", 0)
```

### 数据质量报告
```python
def generate_quality_report(data: List[Dict]) -> Dict:
    """生成数据质量报告"""
    return {
        "total_records": len(data),
        "valid_records": len([d for d in data if validate_data(d)]),
        "sources": list(set([d.get('source', 'Unknown') for d in data])),
        "timestamp": datetime.now().isoformat()
    }
```

---

## 总结

### 核心优势
1. **高可靠性**: 多个 AI 互相验证，降低错误率
2. **高可用性**: 一个 AI 失败，其他 AI 可以补充
3. **高质量**: 自动验证和修复异常数据
4. **可扩展**: 易于添加新的 AI 模型

### 适用场景
- 实时数据抓取
- 市场价格监控
- 新闻和财报分析
- 数据质量保证
- 任何需要高质量数据的应用

### 未来改进方向
1. 添加更多 AI 模型（如 Claude、GPT-4）
2. 实现智能路由（根据任务类型选择最佳 AI）
3. 添加机器学习模型预测数据趋势
4. 实现实时异常检测和告警

---

## 参考资源

- [Qwen API 文档](https://help.aliyun.com/zh/dashscope/)
- [DeepSeek API 文档](https://platform.deepseek.com/docs)
- [Doubao API 文档](https://www.volcengine.com/docs/82379)
- [ComputePulse 项目](https://github.com/WUAIBING/computepulse)

---

**文档版本:** 1.0  
**最后更新:** 2024-12-05  
**作者:** ComputePulse Team
