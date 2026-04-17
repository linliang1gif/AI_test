# 🎉 Ollama本地模型已集成

## ✅ 当前状态

**Ollama运行状态**: 🟢 正常运行
**可用模型**: 2个
- `qwen2.5:1.5b` (推荐，速度快)
- `qwen2.5-coder:latest` (代码生成专用)

## 🚀 快速使用

### 方式1: 双击运行（推荐）

```
测试本地模型.bat    # 测试Ollama连接和功能
演示本地模型.bat    # 完整功能演示
```

### 方式2: Python代码

```python
from ai.ai_client import get_ai_client

# 使用Ollama
client = get_ai_client(use_ollama=True)

# 生成文本
response = client.generate_text("写一个Python函数")
print(response)
```

### 方式3: 直接使用OllamaAIClient

```python
from ai.mock_ai_client import OllamaAIClient

# 指定模型
client = OllamaAIClient(
    base_url="http://localhost:11434",
    model="qwen2.5:1.5b"  # 或 "qwen2.5-coder:latest"
)

response = client.generate_text("你的提示词")
```

## 📊 三种AI模式对比

| 模式 | 优点 | 缺点 | 使用场景 |
|------|------|------|----------|
| **Mock** | 无需配置，秒级响应 | 固定数据 | 快速测试、演示 |
| **Ollama** | 本地运行，免费，隐私 | 需要安装 | 日常开发、测试 |
| **云端API** | 效果最好 | 需要API Key | 生产环境 |

## 🎯 使用建议

### 开发测试阶段
```python
# 使用Ollama本地模型
client = get_ai_client(use_ollama=True)
```

### 快速验证阶段
```python
# 使用Mock模式
client = get_ai_client(use_mock=True)
```

### 生产环境
```python
# 使用云端API
client = get_ai_client(provider="deepseek")
```

## 💡 代码示例

### 示例1: 生成测试策略
```python
from ai.ai_client import get_ai_client

client = get_ai_client(use_ollama=True)

strategy = client.generate_text("""
为电商系统生成测试策略，包括：
1. 功能测试范围
2. 性能测试指标
3. 安全测试要点
""")

print(strategy)
```

### 示例2: 生成测试用例
```python
from ai.ai_client import get_ai_client

client = get_ai_client(use_ollama=True)

testcases = client.generate_text("""
为购物车功能生成5个测试用例，包括：
- 添加商品
- 删除商品
- 修改数量
- 清空购物车
- 结算
""")

print(testcases)
```

### 示例3: 代码生成
```python
from ai.mock_ai_client import OllamaAIClient

# 使用代码专用模型
client = OllamaAIClient(
    model="qwen2.5-coder:latest"
)

code = client.generate_text("""
写一个Python类，实现：
1. 用户注册
2. 用户登录
3. 密码加密
""")

print(code)
```

## 🔧 配置说明

### .env配置（可选）
```bash
# Ollama配置
OLLAMA_BASE_URL=http://localhost:11434
DEFAULT_OLLAMA_MODEL=qwen2.5:1.5b
```

### 切换模型
```python
from ai.mock_ai_client import OllamaAIClient

# 使用快速模型
client = OllamaAIClient(model="qwen2.5:1.5b")

# 使用代码模型
client = OllamaAIClient(model="qwen2.5-coder:latest")
```

## 📝 测试脚本

### 1. 测试连接
```bash
# 双击运行
测试本地模型.bat

# 或命令行
d:\python311\python.exe test_ollama.py
```

### 2. 完整演示
```bash
# 双击运行
演示本地模型.bat

# 或命令行
d:\python311\python.exe demo_ollama.py
```

## 🎊 总结

✅ **Ollama已集成** - 可以直接使用
✅ **2个模型可用** - qwen2.5:1.5b 和 qwen2.5-coder
✅ **简单易用** - 一行代码即可调用
✅ **完全免费** - 本地运行，无需API Key
✅ **隐私安全** - 数据不出本地

**推荐使用**: `qwen2.5:1.5b` (速度快，效果好)

---

**更新时间**: 2026-03-20
**状态**: 🟢 可用
