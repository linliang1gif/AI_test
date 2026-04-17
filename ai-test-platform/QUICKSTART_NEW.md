# AI Test Platform - 快速开始指南

## 🎯 项目架构优化完成

### ✅ 已修复的问题

1. **AI客户端依赖** - 添加Mock AI客户端，无需API Key即可测试
2. **导入路径** - 统一项目导入路径
3. **Pytest技能封装** - 简化为最小实现
4. **测试流程** - 创建快速测试脚本

### 📁 新增文件

```
ai-test-platform/
├── ai/
│   └── mock_ai_client.py          # Mock AI客户端（无需API Key）
├── ai_core/
│   └── skills/
│       └── pytest_skill.py        # 简化的Pytest技能
├── diagnose.py                     # 项目诊断工具
├── quick_test.py                   # 快速测试脚本
└── test_workflow.py                # 完整流程测试
```

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 诊断项目

```bash
python diagnose.py
```

这会检查：
- Python版本
- 依赖包
- 目录结构
- 配置文件
- Pytest环境

### 3. 快速测试

```bash
python quick_test.py
```

测试Pytest技能的基本功能。

### 4. 完整流程测试

```bash
python test_workflow.py
```

测试完整的工作流程：
- 配置加载
- AI客户端（Mock模式）
- Pytest技能执行

## 📝 使用说明

### 使用Mock AI客户端（推荐用于测试）

```python
from ai.ai_client import get_ai_client

# 自动使用Mock（如果没有配置API Key）
client = get_ai_client()

# 或显式使用Mock
client = get_ai_client(use_mock=True)

response = client.generate_text("生成测试策略")
```

### 使用Pytest技能

```python
from ai_core.skills.pytest_skill import PytestSkill

skill = PytestSkill()
result = skill.run("path/to/test_file.py")

if result["success"]:
    print("测试通过:", result["result"])
else:
    print("测试失败:", result["error"])
```

## 🔧 配置说明

### 环境变量（.env）

```bash
# 如果不配置API Key，会自动使用Mock模式
DEEPSEEK_API_KEY=sk-your-key-here
OPENAI_API_KEY=sk-your-key-here

# 默认AI提供商
DEFAULT_AI_PROVIDER=deepseek

# 测试配置
BASE_TEST_URL=http://localhost:8000
```

## 📊 项目结构

```
ai-test-platform/
├── ai/                    # AI客户端模块
│   ├── ai_client.py      # 真实AI客户端
│   └── mock_ai_client.py # Mock AI客户端
├── ai_core/              # AI核心功能
│   └── skills/           # 技能模块
│       └── pytest_skill.py
├── config/               # 配置管理
├── executor/             # 测试执行器
│   └── pytest_runner.py
├── parser/               # 文档解析
├── test_design/          # 测试设计
├── automation/           # 自动化脚本生成
├── analysis/             # 结果分析
├── report/               # 报告生成
└── export/               # 导出功能
```

## 🎯 核心功能

### 1. Pytest技能

```python
from ai_core.skills.pytest_skill import PytestSkill

skill = PytestSkill()
result = skill.run("tests/test_example.py")

# 返回格式
{
    "success": True/False,
    "result": {
        "success": True,
        "execution_time": 1.23,
        "summary": {
            "total": 10,
            "passed": 8,
            "failed": 2
        }
    },
    "error": ""
}
```

### 2. Mock AI客户端

无需API Key，返回模拟数据：

```python
from ai.ai_client import get_ai_client

client = get_ai_client(use_mock=True)

# 生成测试策略
strategy = client.generate_text("生成测试策略")

# 生成JSON
modules = client.generate_json("拆分功能模块")
```

## 🐛 故障排除

### 问题1: 依赖缺失

```bash
pip install -r requirements.txt
```

### 问题2: 配置文件不存在

```bash
cp .env.example .env
```

### 问题3: 目录不存在

诊断工具会自动创建必要目录：

```bash
python diagnose.py
```

## 📚 下一步

1. **运行诊断**: `python diagnose.py`
2. **快速测试**: `python quick_test.py`
3. **完整测试**: `python test_workflow.py`
4. **启动平台**: `python start_platform.py`

## 💡 提示

- 使用Mock模式无需配置API Key
- 所有测试输出在 `output/` 目录
- 日志文件在 `logs/` 目录
- 测试报告在 `output/reports/` 目录

## 🎉 完成

项目已优化完成，可以正常运行！
