# AI测试控制台 - AI调用机制说明

## 📋 概述

AI测试控制台支持多种AI模型调用方式,包括本地模型(Ollama)、云端API(DeepSeek/OpenAI)和Mock模式。系统通过统一的LLM客户端进行调用,用户可以灵活切换。

## 🎯 支持的AI提供商

### 1. Ollama (本地模型) ⭐ 推荐
- **类型**: 本地部署
- **优势**: 
  - 完全免费,无API调用费用
  - 数据隐私,不上传到云端
  - 响应速度快(取决于本地硬件)
  - 离线可用
- **要求**: 
  - 需要本地安装Ollama
  - 需要下载模型(如qwen2.5:1.5b)
- **配置**:
  ```env
  DEFAULT_AI_PROVIDER=ollama
  OLLAMA_BASE_URL=http://localhost:11434
  DEFAULT_AI_MODEL=qwen2.5:1.5b
  ```

### 2. DeepSeek (云端API)
- **类型**: 云端API服务
- **优势**: 
  - 无需本地部署
  - 模型性能强大
  - 价格相对便宜
- **要求**: 
  - 需要DeepSeek API Key
  - 需要网络连接
- **配置**:
  ```env
  DEFAULT_AI_PROVIDER=deepseek
  DEEPSEEK_API_KEY=sk-your-api-key
  DEEPSEEK_BASE_URL=https://api.deepseek.com
  DEFAULT_AI_MODEL=deepseek-chat
  ```

### 3. OpenAI (云端API)
- **类型**: 云端API服务
- **优势**: 
  - 模型性能最强
  - 生态完善
- **要求**: 
  - 需要OpenAI API Key
  - 需要网络连接
  - 费用较高
- **配置**:
  ```env
  DEFAULT_AI_PROVIDER=openai
  OPENAI_API_KEY=sk-your-api-key
  OPENAI_BASE_URL=https://api.openai.com/v1
  DEFAULT_AI_MODEL=gpt-3.5-turbo
  ```

### 4. Mock (模拟模式)
- **类型**: 本地模拟
- **用途**: 
  - 开发测试
  - 演示展示
  - 无AI环境时的备选
- **特点**: 
  - 返回预设的固定响应
  - 不需要任何配置
- **配置**:
  ```env
  DEFAULT_AI_PROVIDER=mock
  ```

## 🔧 技术架构

### 调用流程

```
前端 (AiTestConsole.jsx)
    ↓
    POST /api/agent/analyze (仅决策模式)
    或
    POST /api/pipeline/run (完整流程模式)
    ↓
后端 API (agent/controller.py 或 pipeline/controller.py)
    ↓
Agent Service (agent/agent_service.py)
    ↓
LLM Client (agent/llm_client.py)
    ↓
    ├─→ Ollama API (本地)
    ├─→ DeepSeek API (云端)
    ├─→ OpenAI API (云端)
    └─→ Mock (模拟)
```

### 核心组件

#### 1. LLMClient (agent/llm_client.py)
统一的LLM调用客户端,负责:
- 根据配置选择AI提供商
- 处理不同API的请求格式
- 统一错误处理和重试机制
- JSON响应解析和修复

```python
class LLMClient:
    def __init__(self, provider: Optional[str] = None, model: Optional[str] = None):
        # 从配置读取provider和model
        self.provider = provider or config.ai.default_provider
        self.model = model or config.ai.default_model
    
    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        # 根据provider调用不同的API
        if self.provider == 'ollama':
            return self._ollama_generate(...)
        elif self.provider in ['deepseek', 'openai']:
            return self._openai_compatible_generate(...)
        else:  # mock
            return self._mock_generate(...)
```

#### 2. AIClient (ai/ai_client.py)
旧版AI客户端,主要用于其他模块:
- 支持DeepSeek和OpenAI
- 提供重试机制
- JSON格式修复

#### 3. 配置管理 (.env)
所有AI相关配置集中管理:
```env
# 默认提供商和模型
DEFAULT_AI_PROVIDER=ollama
DEFAULT_AI_MODEL=qwen2.5:1.5b

# API配置
DEEPSEEK_API_KEY=sk-xxx
OLLAMA_BASE_URL=http://localhost:11434

# 请求参数
AI_TEMPERATURE=0.2
AI_MAX_TOKENS=4000
AI_TIMEOUT=120
```

## 💡 使用场景

### 场景1: 本地开发 (推荐Ollama)
```env
DEFAULT_AI_PROVIDER=ollama
DEFAULT_AI_MODEL=qwen2.5:1.5b
OLLAMA_BASE_URL=http://localhost:11434
```

**优势**:
- 完全免费
- 响应快速
- 数据隐私

**步骤**:
1. 安装Ollama: `https://ollama.ai`
2. 下载模型: `ollama pull qwen2.5:1.5b`
3. 启动服务: `ollama serve`
4. 配置.env文件
5. 启动平台

### 场景2: 生产环境 (推荐DeepSeek)
```env
DEFAULT_AI_PROVIDER=deepseek
DEEPSEEK_API_KEY=sk-your-real-key
DEFAULT_AI_MODEL=deepseek-chat
```

**优势**:
- 无需本地部署
- 性能稳定
- 价格合理

**步骤**:
1. 注册DeepSeek账号
2. 获取API Key
3. 配置.env文件
4. 启动平台

### 场景3: 演示展示 (使用Mock)
```env
DEFAULT_AI_PROVIDER=mock
```

**优势**:
- 无需任何配置
- 响应稳定可预测
- 适合演示

## 🔄 动态切换

系统支持运行时动态切换AI提供商:

### 方式1: 环境变量
修改`.env`文件中的`DEFAULT_AI_PROVIDER`,重启服务生效。

### 方式2: API参数
在API调用时指定provider:
```python
llm_client = LLMClient(provider='ollama', model='qwen2.5:1.5b')
```

### 方式3: 前端选择器 (计划中)
未来可在前端添加AI提供商选择器,实时切换。

## 📊 性能对比

| 提供商 | 响应速度 | 成本 | 隐私性 | 准确度 | 推荐场景 |
|--------|---------|------|--------|--------|----------|
| Ollama | ⚡⚡⚡ 快 | 💰 免费 | 🔒 高 | ⭐⭐⭐ 中 | 开发/测试 |
| DeepSeek | ⚡⚡ 中 | 💰💰 低 | 🔒 中 | ⭐⭐⭐⭐ 高 | 生产环境 |
| OpenAI | ⚡⚡ 中 | 💰💰💰 高 | 🔒 中 | ⭐⭐⭐⭐⭐ 最高 | 高要求场景 |
| Mock | ⚡⚡⚡ 快 | 💰 免费 | 🔒 高 | ⭐ 低 | 演示/测试 |

## 🛠️ 配置示例

### 完整配置 (.env)
```env
# ============================================
# AI配置 - 选择一个提供商
# ============================================

# 方案1: 使用Ollama本地模型 (推荐开发环境)
DEFAULT_AI_PROVIDER=ollama
DEFAULT_AI_MODEL=qwen2.5:1.5b
OLLAMA_BASE_URL=http://localhost:11434

# 方案2: 使用DeepSeek云端API (推荐生产环境)
# DEFAULT_AI_PROVIDER=deepseek
# DEFAULT_AI_MODEL=deepseek-chat
# DEEPSEEK_API_KEY=sk-your-api-key
# DEEPSEEK_BASE_URL=https://api.deepseek.com

# 方案3: 使用OpenAI云端API
# DEFAULT_AI_PROVIDER=openai
# DEFAULT_AI_MODEL=gpt-3.5-turbo
# OPENAI_API_KEY=sk-your-api-key
# OPENAI_BASE_URL=https://api.openai.com/v1

# 方案4: 使用Mock模拟模式 (演示/测试)
# DEFAULT_AI_PROVIDER=mock

# ============================================
# AI请求参数
# ============================================
AI_TIMEOUT=120
AI_TEMPERATURE=0.2
AI_MAX_TOKENS=4000
```

## 🔍 调试和监控

### 查看AI调用日志
系统会在控制台输出AI调用信息:
```
🤖 使用AI提供商: ollama
📝 模型: qwen2.5:1.5b
⏱️  响应时间: 2.3秒
✅ 调用成功
```

### 错误处理
当AI调用失败时,系统会:
1. 打印详细错误信息
2. 自动重试(最多3次)
3. 返回默认响应(保证系统可用)

### 性能监控
可以通过日志分析:
- 平均响应时间
- 成功率
- 错误类型分布

## 📝 最佳实践

### 1. 开发阶段
- 使用Ollama本地模型
- 快速迭代,无成本
- 数据隐私有保障

### 2. 测试阶段
- 使用Mock模式进行单元测试
- 使用Ollama进行集成测试
- 确保系统在无AI环境下也能运行

### 3. 生产阶段
- 使用DeepSeek或OpenAI
- 配置API Key环境变量
- 监控API调用量和成本
- 设置合理的超时和重试策略

### 4. 混合使用
- 低优先级任务使用Ollama
- 高优先级任务使用DeepSeek/OpenAI
- 根据负载动态切换

## 🚀 快速开始

### 使用Ollama (推荐新手)

1. 安装Ollama
```bash
# Windows/Mac: 下载安装包
https://ollama.ai/download

# Linux
curl -fsSL https://ollama.ai/install.sh | sh
```

2. 下载模型
```bash
ollama pull qwen2.5:1.5b
```

3. 配置.env
```env
DEFAULT_AI_PROVIDER=ollama
DEFAULT_AI_MODEL=qwen2.5:1.5b
```

4. 启动平台
```bash
python start_platform.py
```

5. 访问AI测试控制台
```
http://localhost:5000/ai-console
```

## ❓ 常见问题

### Q1: 如何知道当前使用的是哪个AI提供商?
A: 查看`.env`文件中的`DEFAULT_AI_PROVIDER`配置,或在后端日志中查看。

### Q2: Ollama模型下载很慢怎么办?
A: 可以使用国内镜像或手动下载模型文件。

### Q3: DeepSeek API Key在哪里获取?
A: 访问 https://platform.deepseek.com 注册并获取。

### Q4: 可以同时使用多个AI提供商吗?
A: 可以,但需要在代码中显式指定provider参数。

### Q5: Mock模式返回的数据准确吗?
A: Mock模式返回的是预设的固定数据,仅用于测试和演示,不代表真实AI分析结果。

## 📚 相关文档

- [Ollama双模型部署完成报告.md](./Ollama双模型部署完成报告.md)
- [DeepSeek集成完成报告.md](./DeepSeek集成完成报告.md)
- [AI模型切换功能完成报告.md](./AI模型切换功能完成报告.md)
- [双模型使用指南.md](./双模型使用指南.md)

---

**总结**: AI测试控制台通过统一的LLM客户端支持多种AI调用方式,既可以使用免费的本地Ollama模型,也可以使用强大的云端API。推荐开发环境使用Ollama,生产环境使用DeepSeek,演示环境使用Mock模式。
