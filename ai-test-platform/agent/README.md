# Test Agent - AI测试决策中心 V2

## 📖 功能概述

Test Agent 是一个智能测试决策服务，通过AI分析需求文档和代码变更，自动判断是否需要执行测试，并输出测试范围和优先级。

**V2升级**: 输出从"分析结果"升级为"可执行决策指令"，可直接驱动 Strategy Engine、Orchestrator、CI/CD Pipeline。

## 🎯 核心能力

### V1 基础能力
- ✅ 智能分析需求变更
- ✅ 解析Git代码差异
- ✅ 判断测试必要性
- ✅ 识别影响模块
- ✅ 评估测试优先级（P0/P1/P2）
- ✅ 预估测试工作量
- ✅ 评估风险等级
- ✅ 记录决策历史
- ✅ 支持多种LLM（Ollama/OpenAI/DeepSeek/Mock）

### V2 增强能力 ✨
- ✨ **action**: 可执行指令（run_tests/skip）
- ✨ **confidence**: 决策置信度（0-1）
- ✨ **test_scope**: 测试范围（类型+用例数）
- ✨ **execution_hint**: 执行建议（并行+重试）
- ✨ **timestamp**: ISO时间戳

**详细使用指南**: 查看 [V2_USAGE.md](./V2_USAGE.md)

## 🏗️ 模块结构

```
agent/
├── __init__.py              # 模块初始化
├── controller.py            # API路由控制器
├── test_agent_service.py    # 核心决策服务
├── llm_client.py            # LLM调用客户端
└── README.md                # 本文档
```

## 📡 API接口

### 1. 分析测试需求

**POST** `/agent/analyze`

分析需求和代码变更，决策是否需要测试。

**请求体：**
```json
{
  "requirement": "需求描述文本",
  "git_diff": "代码变更内容（可选）"
}
```

**响应：**
```json
{
  // V1 基础字段
  "need_test": true,
  "modules": ["订单模块", "支付模块"],
  "priority": "P0",
  "reason": "核心交易逻辑变更，涉及支付流程",
  "test_types": ["功能测试", "接口测试"],
  "estimated_effort": "4小时",
  "risk_level": "高",
  
  // V2 增强字段 ✨
  "action": "run_tests",
  "confidence": 0.9,
  "test_scope": {
    "types": ["api", "ui"],
    "estimated_cases": 30
  },
  "execution_hint": {
    "parallel": true,
    "retry": 1
  },
  "timestamp": "2026-03-23T14:49:44.341713",
  
  // 元数据
  "analyzed_at": "2024-03-21T10:30:00",
  "duration": "2.5s",
  "provider": "ollama",
  "model": "qwen2.5:1.5b"
}
```

### 2. 获取决策历史

**GET** `/agent/history?limit=10`

获取最近的决策记录。

**响应：**
```json
{
  "success": true,
  "data": [...],
  "count": 10
}
```

### 3. 获取统计信息

**GET** `/agent/statistics`

获取决策统计数据。

**响应：**
```json
{
  "success": true,
  "data": {
    "total_decisions": 50,
    "need_test_count": 35,
    "no_test_count": 15,
    "need_test_rate": "70.0%",
    "priority_distribution": {
      "P0": 10,
      "P1": 20,
      "P2": 5
    }
  }
}
```

### 4. 健康检查

**GET** `/agent/health`

检查服务状态。

## 🚀 使用示例

### Python调用

```python
import requests

# 分析需求
response = requests.post("http://localhost:8000/agent/analyze", json={
    "requirement": "新增用户注册功能，支持手机号和邮箱注册",
    "git_diff": "diff --git a/user/views.py ..."
})

result = response.json()
print(f"需要测试: {result['need_test']}")
print(f"影响模块: {result['modules']}")
print(f"优先级: {result['priority']}")
```

### cURL调用

```bash
curl -X POST http://localhost:8000/agent/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "requirement": "修复订单计算bug",
    "git_diff": "diff --git a/order/calc.py ..."
  }'
```

## 🔧 配置说明

### LLM Provider配置

在 `.env` 文件中配置：

```env
# 默认Provider和Model
DEFAULT_AI_PROVIDER=ollama
DEFAULT_AI_MODEL=qwen2.5:1.5b

# Ollama配置
OLLAMA_BASE_URL=http://localhost:11434

# DeepSeek配置
DEEPSEEK_API_KEY=your-api-key
DEEPSEEK_BASE_URL=https://api.deepseek.com

# OpenAI配置
OPENAI_API_KEY=your-api-key
OPENAI_BASE_URL=https://api.openai.com/v1
```

### 切换Provider

系统会自动使用 `.env` 中配置的默认Provider，也可以通过前端AI模型切换器全局切换。

## 📊 决策规则

### 需要测试的情况（need_test: true）

- ✅ 核心业务逻辑变更（订单、支付、用户等）
- ✅ 数据库结构变更
- ✅ API接口变更
- ✅ 安全相关变更
- ✅ 性能优化
- ✅ Bug修复

### 无需测试的情况（need_test: false）

- ❌ 纯文档更新
- ❌ 注释修改
- ❌ 代码格式化
- ❌ 日志输出调整
- ❌ 配置文件微调（非关键配置）

### 优先级定义

- **P0**: 核心功能，必须立即测试（如支付、登录）
- **P1**: 重要功能，应该测试（如订单管理、用户管理）
- **P2**: 一般功能，可以延后测试（如统计报表、日志查看）

## 🧪 测试

运行测试脚本：

```bash
python test_agent_module.py
```

## 📝 日志记录

决策历史自动保存到：
- 内存：最近100条记录
- 文件：`output/agent_logs/decision_YYYYMMDD.jsonl`

日志格式：
```json
{
  "timestamp": "2024-03-21T10:30:00",
  "requirement": "需求描述...",
  "git_diff": "代码变更...",
  "decision": {
    "need_test": true,
    "modules": [...],
    "priority": "P0",
    ...
  }
}
```

## 💡 使用场景

### 场景1: CI/CD集成

在CI/CD流程中，每次代码提交时自动调用Test Agent分析：

```yaml
# .github/workflows/test.yml
- name: Analyze Test Need
  run: |
    curl -X POST http://test-agent:8000/agent/analyze \
      -d '{"requirement": "${{ github.event.head_commit.message }}", 
           "git_diff": "$(git diff HEAD~1)"}'
```

### 场景2: 需求评审

在需求评审阶段，使用Test Agent评估测试工作量：

```python
# 评审会议中
result = analyze_requirement(requirement_doc)
print(f"预估测试工作量: {result['estimated_effort']}")
print(f"风险等级: {result['risk_level']}")
```

### 场景3: 测试计划

根据Test Agent的分析结果，自动生成测试计划：

```python
decisions = get_all_decisions()
p0_items = [d for d in decisions if d['priority'] == 'P0']
# 优先安排P0测试任务
```

## 🎉 特性

- **智能决策**: 基于AI的智能分析，准确率高
- **多Provider支持**: 灵活切换不同的LLM
- **Mock模式**: 无需真实LLM即可测试
- **历史记录**: 完整的决策历史追溯
- **标准JSON**: 输出格式统一，易于集成
- **日志持久化**: 自动保存决策记录

## 🔍 故障排查

### 问题1: 连接失败

```
❌ 连接失败! 请确保后端服务已启动
```

**解决方案**: 启动后端服务
```bash
python backend_api_server.py
```

### 问题2: LLM调用超时

```
❌ Ollama调用失败: timeout
```

**解决方案**: 
1. 检查Ollama服务是否运行: `ollama list`
2. 增加超时时间（在llm_client.py中）
3. 切换到其他Provider

### 问题3: JSON解析失败

```
⚠️  JSON解析失败
```

**解决方案**: 
- 系统会自动返回默认决策
- 检查LLM模型是否支持JSON输出
- 尝试使用temperature=0.1降低随机性

## 📚 扩展开发

### 添加新的分析维度

在 `test_agent_service.py` 中修改 `_build_analysis_prompt()` 方法：

```python
prompt += """
## 新增分析维度
5. **测试覆盖率**: 评估需要的测试覆盖率
6. **自动化可行性**: 判断是否适合自动化测试
"""
```

### 自定义决策规则

在 `_normalize_result()` 方法中添加业务规则：

```python
# 如果涉及支付模块，强制设为P0
if "支付" in str(normalized["modules"]):
    normalized["priority"] = "P0"
```

## 📞 支持

如有问题，请查看：
- API文档: http://localhost:8000/docs
- 测试脚本: test_agent_module.py
- 日志文件: output/agent_logs/
