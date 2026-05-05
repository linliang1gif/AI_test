# AI Test Platform - 企业级AI自动化测试平台 🚀

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18.2+-61dafb.svg)](https://reactjs.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 🚀 推荐启动方式（Phase A+ V2 主线）

> **重要**: V2 主线启动入口为 `backend/app.py`。`backend_api_server.py` 已标记为 **legacy**，仅保留兼容，**不推荐**作为主入口。

### 后端启动（推荐）

```bash
uvicorn backend.app:create_app --factory --host 0.0.0.0 --port 8000
```

- V2 路由由 `backend/router_registry.py` 集中注册（39+ 模块）
- 启动时自动执行 DB 迁移（含 Phase C1 code_compare 5 张新表）
- CORS 默认仅允许本地开发白名单（`localhost:5173/5174`、`127.0.0.1:5173/5174`）

### 前端启动

```bash
cd frontend
npm install
npm run dev   # 默认 http://localhost:5173
```

### CORS 配置（生产环境）

通过环境变量 `CORS_ALLOW_ORIGINS` 配置允许的前端来源（逗号分隔）：

```bash
# .env 示例
CORS_ALLOW_ORIGINS=https://test-platform.example.com,https://admin.example.com
```

留空时使用本地开发白名单：

```
http://localhost:5173
http://localhost:5174
http://127.0.0.1:5173
http://127.0.0.1:5174
```

**Phase C2 安全收口**：
- ❌ 不再使用 `allow_origins=["*"]`
- ✅ Git clone 阻断 localhost / 127.0.0.1 / 内网 IP / 169.254.169.254 / `file://` / `ftp://`
- ✅ Git URL token 日志脱敏

### 本地开发 .env 示例

```bash
APP_MODE=mock
USE_MOCK_DATA=true
AI_PROVIDER=none
AI_ANALYSIS_MODE=rule
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000

# CORS（留空使用本地白名单）
CORS_ALLOW_ORIGINS=

# Git clone（仅本地调试需要时打开）
ALLOW_LOCAL_GIT_HTTP=false
```

---

## 🎯 项目概述

AI Test Platform 是一个**企业级**的完整测试生命周期管理平台，实现从需求分析到自动化测试执行的全流程自动化。

## 🚀 本地Mock模式快速启动（推荐新手）

### 1. 环境准备

```bash
# 克隆项目
git clone <repository>
cd ai-test-platform

# 创建虚拟环境
python -m venv venv

# 激活虚拟环境 (Windows)
venv\Scripts\activate

# 安装后端依赖
pip install -r requirements.txt

# 安装前端依赖
cd frontend
npm install
cd ..
```

### 2. 配置Mock模式

```bash
# 复制配置文件
cp .env.example .env

# .env中确认以下配置（默认已是Mock模式）
APP_MODE=mock
USE_MOCK_DATA=true
MOCK_API_BASE_URL=https://httpbin.org
AI_PROVIDER=none
AI_ANALYSIS_MODE=rule
```

### 3. 启动服务

**方式A：使用启动脚本（推荐）**
```bash
# 启动后端
scripts\start_local_backend.bat

# 启动前端（新终端）
scripts\start_local_frontend.bat
```

**方式B：手动启动**
```bash
# 启动后端
venv\Scripts\python.exe backend_api_server.py

# 启动前端（新终端）
cd frontend
npm run dev
```

### 4. 验收测试

```bash
# 运行smoke测试
python scripts\smoke_p0_7_local.py

# 检查环境就绪
python scripts\verify_local_ready.py

# 检查API契约
python scripts\check_api_contract.py
```

预期结果：
- ✅ 后端: http://localhost:8000
- ✅ 前端: http://localhost:5173 或 5174
- ✅ API文档: http://localhost:8000/docs
- ✅ Smoke通过率: 100%

### 5. 切换到Real模式

当需要连接真实被测系统时：

```bash
# 修改.env
APP_MODE=real
TARGET_API_BASE_URL=https://your-real-api.com
TARGET_API_TOKEN=your_token_here

# 重启后端服务
```

📖 **详细文档**: [docs/local_mock_mode.md](docs/local_mock_mode.md)

## 常见问题

### Q1: pydantic版本冲突怎么处理？

**症状**: `SystemError: The installed pydantic-core version is incompatible`

**解决**:
```bash
# 使用虚拟环境
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### Q2: /api-specs 前端路由404？

**症状**: 访问 http://localhost:5173/api-specs 返回404

**原因**: Vite代理配置问题

**解决**: 检查 `frontend/vite.config.js`
```javascript
proxy: {
  '/api/': {  // 注意末尾的斜杠
    target: 'http://127.0.0.1:8000',
    // ...
  }
}
```

### Q3: 405错误算通过吗？

**不算！** 只有2xx才算成功。

如果遇到405，说明接口方法不支持，需要：
1. 检查后端是否实现了该方法
2. 检查前端调用的方法是否正确

### Q4: .env文件要提交吗？

**绝对不要！**

`.env` 包含敏感配置，已在 `.gitignore` 中排除。

**正确做法**:
- ✅ 提交 `.env.example` 作为模板
- ✅ 本地维护 `.env`
- ❌ 不要提交 `.env`
- ❌ 不要在代码中硬编码Token

### Q5: 推荐的开发流程？

```bash
# 1. 启动服务
scripts\start_local_backend.bat
scripts\start_local_frontend.bat

# 2. 运行smoke验收
python scripts\smoke_p0_7_local.py

# 3. 开始开发
# ... 修改代码 ...

# 4. 开发后再次验收
python scripts\smoke_p0_7_local.py
python scripts\check_api_contract.py

# 5. 提交代码
git add .
git commit -m "feat: xxx"
```

## 🚀 快速开始（完整流程）

### 方式1: AI测试控制台（推荐 - 10秒上手）

**最快的测试方式** - 一键执行五阶段AI测试流程

1. **启动服务**（如果未运行）
   ```bash
   python backend_api_server.py
   cd frontend && npm run dev
   ```

2. **打开控制台**
   ```
   浏览器访问: http://localhost:5173/ai-test-console
   ```

3. **执行测试**
   - 输入需求描述
   - 选择优先级（P0/P1/P2）
   - 点击"🚀 Run AI Test"
   - 10-20秒查看结果

**适用场景**: 代码提交验证、快速回归测试、Bug修复验证

📖 **详细文档**: `快速入门_AI控制台.md`

**快速测试**: 
```bash
python quick_test.py  # 3步验证，10秒完成
```

### 方式2: 传统完整流程

**完整的测试设计流程** - 生成测试文档和自动化脚本

1. 访问: http://localhost:5173/projects
2. 上传需求文档和Swagger
3. AI生成测试用例Excel
4. AI生成pytest自动化脚本
5. 执行测试并生成报告

**适用场景**: 新功能开发、需要测试文档、完整测试设计

📖 **详细文档**: `完整流程使用说明.md`

---

### 🆕 五阶段AI自动化测试系统

**核心架构**: Agent → Strategy → Orchestrator → Self-Healing → Report

```
┌─────────────────────────────────────────────────────────────┐
│                    AI Test Pipeline                         │
│                   (一键自动测试入口)                          │
└─────────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        ▼                   ▼                   ▼
   🤖 Test Agent      📋 Strategy         ⚡ Orchestrator
   (AI决策中心)        (策略引擎)          (执行调度器)
        │                   │                   │
        └───────────────────┼───────────────────┘
                            ▼
                    🔧 Self-Healing
                     (自动修复)
                            │
                            ▼
                      📊 Report
                     (智能报告)
```

### ✨ 核心特性

- **🤖 AI决策**: 智能判断是否需要测试，避免无效测试
- **📋 策略生成**: 基于规则引擎生成最优测试策略
- **⚡ 自动执行**: 并行调度，3-5x加速测试执行
- **🔧 失败自愈**: 6种错误类型自动识别和修复
- **📊 智能报告**: AI总结测试结果和风险点
- **🔍 全链路追踪**: trace_id + timeline完整记录
- **🌐 Web可视化**: 现代化的React管理界面

## 🔄 五阶段自动化测试流程

### 一键执行模式（推荐）

```
需求 + Git Diff
    ↓
【阶段1】Test Agent - AI决策分析
    ├─ 判断是否需要测试
    ├─ 评估风险等级
    └─ 输出决策指令（V2增强）
    ↓
【阶段2】Strategy Engine - 策略生成
    ├─ 应用业务规则
    ├─ 生成测试计划
    └─ 输出结构化策略（V2增强）
    ↓
【阶段3】Orchestrator - 自动执行
    ├─ 并行调度测试
    ├─ 3种Runner（API/UI/Integration）
    └─ 输出执行结果
    ↓
【阶段4】Self-Healing - 自动修复（条件触发）
    ├─ 分析失败原因（6种错误类型）
    ├─ 应用修复策略
    └─ 自动重试验证
    ↓
【阶段5】Report - 智能报告
    ├─ 统计测试结果
    ├─ AI总结风险点
    └─ 生成完整报告
```

### 传统流程模式

```
需求文档 (Web上传)
    ↓
AI需求解析 (RequirementAgent)
    ↓
AI功能模块拆分 (TestDesignAgent)
    ↓
AI生成测试点 (TestCaseAgent)
    ↓
AI生成测试场景矩阵
    ↓
AI生成完整测试用例
    ↓
Swagger/OpenAPI自动解析
    ↓
自动生成接口自动化脚本
    ↓
执行pytest测试
    ↓
AI分析Bug + Self Healing自动修复
    ↓
测试覆盖率分析
    ↓
生成企业级测试报告
    ↓
Web界面展示结果
```

## 🛠 技术栈

- **Python 3.11** - 核心开发语言
- **FastAPI** - Web API框架 + 可视化界面
- **pytest** - 测试框架 + 自动化执行
- **requests** - HTTP客户端
- **openpyxl** - Excel处理
- **AI模型** - DeepSeek/OpenAI
- **Allure** - 测试报告
- **Jinja2** - 模板引擎
- **uvicorn** - ASGI服务器

## 📁 企业级项目结构

```
ai-test-platform/
├── agent/                        # 🆕 阶段1: Test Agent (AI决策中心)
│   ├── llm_client.py            # LLM统一客户端
│   ├── test_agent_service.py    # AI决策服务（V2增强）
│   ├── controller.py            # API控制器（4个接口）
│   └── __init__.py
├── strategy/                     # 🆕 阶段2: Strategy Engine (策略引擎)
│   ├── rules.py                 # 业务规则引擎
│   ├── strategy_service.py      # 策略生成服务（V2增强）
│   ├── controller.py            # API控制器（1个接口）
│   └── __init__.py
├── orchestrator/                 # 🆕 阶段3: Orchestrator (执行调度器)
│   ├── base_runner.py           # Runner基类 + 3种实现
│   ├── orchestrator_service.py  # 调度服务（并行执行）
│   ├── controller.py            # API控制器（4个接口）
│   └── __init__.py
├── self_healing/                 # 🆕 阶段4: Self-Healing (自动修复)
│   ├── analyzer.py              # 错误分析器（6种类型）
│   ├── fixer.py                 # 修复策略引擎
│   ├── healing_service.py       # 修复服务（重试机制）
│   ├── controller.py            # API控制器（5个接口）
│   └── __init__.py
├── pipeline/                     # 🆕 阶段5: Pipeline (流程总调度)
│   ├── report_generator.py      # 报告生成器（AI总结）
│   ├── pipeline_service.py      # 流程编排（5阶段串联）
│   ├── controller.py            # API控制器（5个接口）
│   └── __init__.py
├── backend_api_server.py         # 🆕 统一后端服务器
├── app/
│   ├── main.py                  # 主流程
│   ├── api_server.py            # FastAPI服务器
│   ├── agents/                  # AI Agent系统
│   ├── api_parser/              # API解析模块
│   ├── api_test_generator/      # API测试生成
│   ├── coverage_analyzer/       # 覆盖率分析
│   └── web/                     # Web可视化
├── config/
│   └── config.py                # 配置管理
├── ai/
│   ├── ai_client.py             # AI客户端
│   └── prompt_library.py        # Prompt库
├── test_design/
│   ├── module_splitter.py       # 模块拆分
│   ├── testpoint_generator.py   # 测试点生成
│   ├── scenario_matrix_generator.py # 场景矩阵
│   └── testcase_generator.py    # 测试用例生成
├── automation/
│   └── api_script_generator.py  # 自动化脚本生成
├── output/                      # 输出目录
│   ├── agent_logs/              # Agent日志
│   ├── strategy_logs/           # Strategy日志
│   ├── orchestrator_logs/       # Orchestrator日志
│   ├── healing_logs/            # Healing日志
│   ├── pipeline_logs/           # Pipeline日志
│   └── reports/                 # 测试报告
├── frontend/                    # 🆕 React前端
│   ├── src/
│   │   ├── pages/
│   │   │   ├── Dashboard.jsx    # 仪表盘
│   │   │   ├── TestAgent.jsx    # Test Agent页面
│   │   │   └── ...
│   │   └── components/
│   └── package.json
├── requirements.txt             # Python依赖
└── README.md                    # 项目文档
```

## 🚀 快速开始

### 方式一：一键自动测试（推荐）🆕

```bash
# 1. 启动后端服务
python backend_api_server.py

# 2. 一键执行测试
curl -X POST http://localhost:8000/api/pipeline/run \
  -H "Content-Type: application/json" \
  -d '{
    "requirement": "支付模块需要支持微信支付",
    "git_diff": "+def wechat_pay(): return process_payment()"
  }'

# 3. 查看API文档
# 访问 http://localhost:8000/docs
```

### 方式二：Python调用

```python
from pipeline.pipeline_service import get_pipeline_service

# 获取Pipeline服务
service = get_pipeline_service()

# 一键执行完整流程
result = service.run_pipeline({
    "requirement": "支付模块需要支持微信支付",
    "git_diff": "+def wechat_pay(): ...",
    "context": {"priority": "P0"}
})

# 查看结果
print(f"Trace ID: {result['trace_id']}")
print(f"最终状态: {result['report']['summary']['status']}")
print(f"总耗时: {result['total_duration']}s")
```

### 方式三：演示脚本

```bash
# 运行五阶段系统演示
python demo_pipeline.py

# 运行系统验证
python verify_five_stages.py
```

### 方式四：传统命令行模式

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env 文件，填入 API Key

# 3. 运行主流程
python app/main.py

# 4. 启动API服务
python app/api_server.py
```

### 方式五：Web可视化模式

```bash
# 启动前端界面
cd frontend
npm install
npm run dev

# 访问 http://localhost:5173
# 通过Web界面上传文档、生成测试、查看报告
```

## 📋 企业级功能特性

### 🔍 智能API解析
- ✅ 自动解析Swagger/OpenAPI 3.0文档
- ✅ 支持JSON和YAML格式
- ✅ 提取完整接口信息（路径、方法、参数、响应）
- ✅ 生成标准化接口数据结构

### 🤖 接口测试自动生成
- ✅ 根据API信息自动生成pytest测试脚本
- ✅ 包含正常请求、参数缺失、非法参数测试
- ✅ 自动生成权限测试和边界测试
- ✅ 支持数据驱动测试用例

### 🔧 Self Healing自修复
- ✅ pytest执行失败后自动分析错误
- ✅ AI智能生成修复代码
- ✅ 自动应用修复并重新执行
- ✅ 支持多次重试和修复历史记录

### 📊 测试覆盖率分析
- ✅ 需求覆盖率分析
- ✅ 测试点覆盖率统计
- ✅ 测试用例覆盖率计算
- ✅ 自动化覆盖率评估
- ✅ 智能改进建议生成

### 🤖 AI Agent协同系统
- ✅ RequirementAgent - 专业需求解析
- ✅ TestDesignAgent - 智能测试设计
- ✅ TestCaseAgent - 测试用例生成
- ✅ ApiTestAgent - API测试专家
- ✅ AutomationAgent - 自动化脚本生成
- ✅ BugAnalyzerAgent - Bug智能分析

### 🔄 完整自动化流水线
- ✅ 端到端流程编排
- ✅ 步骤依赖管理
- ✅ 错误处理和恢复
- ✅ 实时进度监控
- ✅ 并行任务执行

### 🌐 Web可视化平台
- ✅ 现代化响应式界面
- ✅ 文件拖拽上传
- ✅ 实时任务进度显示
- ✅ 在线报告查看
- ✅ RESTful API接口

## 🔧 配置说明

### 环境变量配置

复制 `.env.example` 为 `.env` 并配置以下参数：

```bash
# AI API 配置 (必须配置至少一个)
DEEPSEEK_API_KEY=sk-your-deepseek-api-key-here
OPENAI_API_KEY=sk-your-openai-api-key-here

# API 基础URL
DEEPSEEK_BASE_URL=https://api.deepseek.com
OPENAI_BASE_URL=https://api.openai.com/v1

# 默认AI模型
DEFAULT_AI_MODEL=deepseek-chat
DEFAULT_AI_PROVIDER=deepseek

# 测试配置
BASE_TEST_URL=http://localhost:8000
TEST_TIMEOUT=30
MAX_RETRIES=3

# 报告配置
REPORT_TITLE=AI Test Platform Report
COMPANY_NAME=Your Company Name
```

### 配置类说明

- **AIConfig**: AI模型相关配置
- **TestConfig**: 测试执行相关配置
- **PathConfig**: 文件路径配置
- **ReportConfig**: 报告生成配置

## 📖 使用文档

### 快速体验

```bash
# 运行完整演示
python demo_complete_platform.py
```

### 主要使用方式

#### 1. 命令行方式

```bash
# 运行完整工作流程
python app/main.py

# 启动Web API服务
python app/api_server.py
```

#### 2. 编程方式

```python
from app.main import AITestPlatform

# 创建平台实例
platform = AITestPlatform()

# 运行完整工作流程
result = platform.run_complete_workflow(
    requirement_file="data/requirement.txt",
    swagger_file="data/swagger.json"
)

if result['success']:
    print("工作流程执行成功！")
    print(f"生成测试用例: {result['summary']['testcases_count']} 个")
else:
    print(f"执行失败: {result['error']}")
```

#### 3. Web API方式

启动服务后访问 `http://localhost:8000/docs` 查看API文档。

主要接口：
- `POST /generate_testcases` - 生成测试用例
- `POST /generate_scripts` - 生成自动化脚本
- `POST /run_tests` - 执行测试
- `GET /report` - 获取测试报告

### 输入文件格式

#### 需求文档 (data/requirement.txt)

```text
用户管理系统需求

1. 用户注册功能
   - 支持邮箱注册
   - 支持手机号注册
   - 密码强度验证

2. 用户登录功能
   - 支持邮箱登录
   - 支持手机号登录
   - 支持记住登录状态

3. 用户信息管理
   - 查看个人信息
   - 修改个人信息
   - 修改密码
```

#### Swagger文档 (data/swagger.json)

```json
{
  "openapi": "3.0.0",
  "info": {
    "title": "用户管理API",
    "version": "1.0.0"
  },
  "paths": {
    "/api/register": {
      "post": {
        "summary": "用户注册",
        "requestBody": {
          "content": {
            "application/json": {
              "schema": {
                "type": "object",
                "properties": {
                  "email": {"type": "string"},
                  "password": {"type": "string"},
                  "phone": {"type": "string"}
                }
              }
            }
          }
        }
      }
    }
  }
}
```

### 输出文件说明

执行完成后，在 `output/` 目录下会生成以下文件：

- `test_strategy.md` - AI生成的测试策略
- `modules.json` - 功能模块拆分结果
- `testpoints.json` - 测试点生成结果
- `scenarios.json` - 测试场景矩阵
- `testcases.json` - 完整测试用例
- `testcases.xlsx` - Excel格式测试用例
- `tests/` - 自动化测试脚本目录
- `reports/` - 测试报告目录

## 🔍 核心模块说明

### AI客户端 (ai/ai_client.py)
- 支持DeepSeek和OpenAI模型
- 统一的AI调用接口
- 自动重试和错误处理

### Prompt库 (ai/prompt_library.py)
- 测试策略生成Prompt
- 模块拆分Prompt
- 测试用例生成Prompt
- Bug分析Prompt

### 测试设计模块
- **模块拆分器**: 将需求拆分为功能模块
- **测试点生成器**: 为每个模块生成测试点
- **场景矩阵生成器**: 生成测试场景组合
- **测试用例生成器**: 生成完整测试用例

### 自动化模块
- **API脚本生成器**: 生成pytest自动化脚本
- **测试执行器**: 执行pytest测试
- **日志解析器**: 解析测试结果
- **Bug分析器**: AI分析失败原因

## 🚨 注意事项

1. **API Key配置**: 必须配置至少一个AI API Key
2. **网络连接**: 需要稳定的网络连接访问AI服务
3. **Python版本**: 需要Python 3.11或更高版本
4. **依赖安装**: 确保所有依赖包正确安装
5. **文件权限**: 确保有写入output目录的权限

## 🐛 常见问题

### Q: AI API调用失败
A: 检查API Key是否正确配置，网络是否正常

### Q: 测试执行失败
A: 检查BASE_TEST_URL是否正确，目标服务是否启动

### Q: 文件生成失败
A: 检查output目录权限，确保有写入权限

### Q: 依赖安装失败
A: 使用虚拟环境，确保Python版本正确

## 📞 技术支持

如有问题，请查看：
1. 配置文件是否正确
2. 依赖是否完整安装
3. API Key是否有效
4. 网络连接是否正常

## 🔄 版本更新

### v1.0.0
- 完整的测试生命周期支持
- AI驱动的测试设计
- 自动化脚本生成
- 智能Bug分析
- 多格式报告输出


## 🎯 五阶段系统详细说明

### 快速使用

```bash
# 1. 启动后端
python backend_api_server.py

# 2. 一键执行测试
curl -X POST http://localhost:8000/api/pipeline/run \
  -d '{"requirement": "支付模块需要支持微信支付"}'

# 3. 查看结果
curl http://localhost:8000/api/pipeline/history
```

### API接口总览

五阶段系统提供18个HTTP接口：

**Test Agent (4个)**:
- POST /api/agent/analyze
- GET /api/agent/history
- GET /api/agent/statistics
- GET /api/agent/health

**Strategy Engine (1个)**:
- POST /api/strategy/generate

**Orchestrator (4个)**:
- POST /api/orchestrator/run
- GET /api/orchestrator/history
- GET /api/orchestrator/statistics
- GET /api/orchestrator/health

**Self-Healing (5个)**:
- POST /api/healing/fix
- GET /api/healing/history
- GET /api/healing/statistics
- GET /api/healing/suggestions/{error_type}
- GET /api/healing/health

**Pipeline (4个)**:
- POST /api/pipeline/run
- GET /api/pipeline/history
- GET /api/pipeline/statistics
- GET /api/pipeline/health
- GET /api/pipeline/trace/{trace_id}

### 性能指标

| 场景 | 耗时 | 说明 |
|------|------|------|
| 完整流程 | ~18s | Agent(18s) + 其他(<1s) |
| 跳过场景 | ~2s | 仅执行决策分析 |
| 并行加速 | 3-5x | Orchestrator并发执行 |

### 测试验证

```bash
# 系统验证（21个检查）
python verify_five_stages.py

# 单元测试
python test_pipeline.py          # 6/6
python test_orchestrator.py      # 6/6
python test_self_healing.py      # 6/6

# API测试
python test_pipeline_api.py      # 5/5
python test_orchestrator_api.py  # 5/5
python test_healing_api.py       # 7/7

# 演示脚本
python demo_pipeline.py          # 3个场景
```

### 详细文档

- **使用指南**: 五阶段系统使用指南.md
- **完成总结**: 五阶段系统完成总结.md
- **交付清单**: 五阶段完整交付清单.md
- **验收报告**: 第五阶段交付验收报告.md

## 🎉 系统状态

**版本**: v1.0.0  
**状态**: 🟢 生产就绪  
**测试覆盖**: 67+ 测试全部通过  
**代码质量**: 高内聚低耦合

**核心价值**:
- 🤖 AI驱动，智能决策
- ⚡ 全自动化，一键执行
- 🔧 失败自愈，无需人工
- 📊 全链路追踪，问题可溯源
