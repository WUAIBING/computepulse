# Doubao API 配置指南

## 🔧 问题诊断

根据测试结果，Doubao API 返回 401 错误的原因是：

1. **API Key 未配置** 或
2. **Endpoint ID 不正确** 或
3. **API Key 权限不足**

## ✅ 解决方案

### 步骤 1：获取正确的 Endpoint ID

根据 API 示例和测试：

正确的 Endpoint ID 是：**`doubao-seed-1-6-251015`**

✅ **已确认**：脚本中的 `DOUBAO_ENDPOINT_ID` 使用 `doubao-seed-1-6-251015`

**注意**：控制台 URL 中显示的是模型 ID (`doubao-seed-1-6`)，但实际 API 调用需要使用完整的 endpoint ID (`doubao-seed-1-6-251015`)

### 步骤 2：配置 API Key

#### 方法 A：使用环境变量（推荐用于 GitHub Actions）

```bash
# Linux/Mac
export VOLC_API_KEY="your-api-key-here"

# Windows PowerShell
$env:VOLC_API_KEY="your-api-key-here"

# Windows CMD
set VOLC_API_KEY=your-api-key-here
```

#### 方法 B：使用 .env.local 文件（推荐用于本地开发）

创建或编辑 `.env.local` 文件：

```bash
VOLC_API_KEY=your-api-key-here
DASHSCOPE_API_KEY=your-dashscope-key-here
```

**注意**：`.env.local` 应该在 `.gitignore` 中，不要提交到 Git！

### 步骤 3：获取 API Key

1. 访问火山引擎控制台：
   https://console.volcengine.com/ark/region:ark+cn-beijing/apiKey

2. 创建或复制现有的 API Key

3. 确保 API Key 有以下权限：
   - ✅ 访问推理端点
   - ✅ 使用网络搜索功能

### 步骤 4：验证配置

运行诊断脚本：

```bash
python scripts/diagnose_doubao.py
```

预期输出：
```
✓ API Key found: sk-xxxxxx...xxxx
✓ Found X endpoints
✓ chat/completions API works!
✓ responses API (with search) works!
```

### 步骤 5：测试数据抓取

```bash
python scripts/fetch_prices_optimized.py --once
```

如果配置正确，应该看到：
```
[2025-12-04 XX:XX:XX] Fetching GPU prices...
[2025-12-04 XX:XX:XX] GPU Prices updated: X records (Qwen: X, Doubao: X)
```

## 🔍 常见问题

### Q1: 仍然收到 401 错误

**可能原因**：
- API Key 过期
- API Key 没有访问该 endpoint 的权限
- Endpoint ID 不正确

**解决方法**：
1. 在控制台重新生成 API Key
2. 检查 API Key 的权限设置
3. 确认 endpoint 状态为"运行中"

### Q2: Endpoint ID 应该用哪个？

有两种 ID 格式：

1. **模型 ID**（如 `doubao-seed-1-6`）
   - 用于 `chat/completions` API
   - 不支持 `responses` API

2. **端点 ID**（如 `ep-20241204xxxxxx-xxxxx`）
   - 用于 `responses` API
   - 支持网络搜索功能

**推荐**：使用端点 ID 以启用网络搜索功能。

### Q3: 如何找到端点 ID？

1. 访问：https://console.volcengine.com/ark/region:ark+cn-beijing/endpoint
2. 找到你的 Doubao 端点
3. 复制端点 ID（格式：`ep-xxxxxxxx-xxxxx`）

### Q4: 网络搜索功能如何启用？

在创建或编辑端点时：
1. 进入端点配置
2. 找到"工具"或"Tools"设置
3. 启用"网络搜索"（Web Search）

## 📝 配置检查清单

使用此清单确保配置正确：

- [ ] API Key 已配置（环境变量或 .env.local）
- [ ] API Key 有效且未过期
- [ ] Endpoint ID 正确（`doubao-seed-1-6` 或 `ep-xxx`）
- [ ] Endpoint 状态为"运行中"
- [ ] API Key 有访问该 endpoint 的权限
- [ ] 网络搜索功能已启用（如果使用 responses API）
- [ ] 诊断脚本运行成功
- [ ] 数据抓取测试成功

## 🚀 GitHub Actions 配置

如果在 GitHub Actions 中使用，需要添加 Secret：

1. 进入 GitHub 仓库设置
2. Settings → Secrets and variables → Actions
3. 添加新 Secret：
   - Name: `VOLC_API_KEY`
   - Value: 你的 API Key

4. 在 workflow 文件中使用：
```yaml
- name: Fetch prices
  env:
    VOLC_API_KEY: ${{ secrets.VOLC_API_KEY }}
    DASHSCOPE_API_KEY: ${{ secrets.DASHSCOPE_API_KEY }}
  run: python scripts/fetch_prices.py --once
```

## 🧠 Reasoning Effort（思考程度）

Doubao-seed-1-6-251015 版本支持思考程度调节，可以平衡速度和质量：

| 模式 | 说明 | 适用场景 | 速度 |
|------|------|----------|------|
| `minimal` | 不思考 | 简单查询、快速响应 | ⚡⚡⚡ 最快 |
| `low` | 基础思考 | **价格抓取**（推荐） | ⚡⚡ 快 |
| `medium` | 中等思考 | 复杂分析 | ⚡ 中等 |
| `high` | 深度思考 | 复杂推理任务 | 🐌 慢 |

**当前配置**：脚本使用 `low` 模式，适合价格数据抓取任务。

**优化建议**：
- 价格抓取：使用 `low` 或 `minimal`（当前使用 `low`）
- 数据分析：使用 `medium`
- 复杂推理：使用 `high`

## 📊 API 使用建议

### 成本优化

1. **使用缓存**：避免频繁调用 API
2. **批量处理**：一次调用获取多个数据
3. **设置配额**：在控制台设置每日配额限制
4. **调整思考程度**：使用 `low` 或 `minimal` 提高速度，降低成本

### 可靠性提升

1. **重试机制**：已在优化脚本中实现
2. **降级策略**：Doubao 失败时使用 Qwen
3. **监控告警**：设置失败率告警

### 数据质量

1. **启用搜索**：确保获取最新数据
2. **数据验证**：已在优化脚本中实现
3. **多源对比**：Qwen + Doubao 双重验证

## 🔗 相关链接

- [火山引擎 Ark 控制台](https://console.volcengine.com/ark)
- [API 文档](https://www.volcengine.com/docs/82379/1099475)
- [模型详情](https://console.volcengine.com/ark/region:ark+cn-beijing/model/detail?Id=doubao-seed-1-6)
- [端点管理](https://console.volcengine.com/ark/region:ark+cn-beijing/endpoint)
- [API Key 管理](https://console.volcengine.com/ark/region:ark+cn-beijing/apiKey)

## 💡 下一步

配置完成后：

1. ✅ 运行诊断脚本验证配置
2. ✅ 测试数据抓取
3. ✅ 部署优化脚本到生产环境
4. ✅ 监控运行状态
5. ✅ 定期检查数据质量

---

**需要帮助？** 查看测试报告 `TEST_REPORT.md` 或优化文档 `DATA_FETCHING_OPTIMIZATION.md`
