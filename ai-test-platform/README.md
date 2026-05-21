# AI Test Platform

AI Test Platform 是一套基于 FastAPI + React 18 的 AI 测试平台，覆盖项目、环境、鉴权、接口/WEB UI 测试用例、执行记录、报告、缺陷、质量看板、Product Studio、Dev Studio 等核心能力。

## 唯一启动方式（治理基线）

```bash
uvicorn backend.app:create_app --factory --reload
```

后端启动只允许通过工厂入口 `backend.app:create_app`。仓库内任何其它启动脚本（含 `backend_api_server.py`、`app/api_server.py`、`simple_backend.py`、`enhanced_web_server.py`）均为 deprecated，仅保留向后兼容。完整治理规则见 [`docs/architecture/SYSTEM_MAINLINE.md`](docs/architecture/SYSTEM_MAINLINE.md)。

## 当前主线

当前主线是 V2 架构：

- 后端入口：`backend.app:create_app`
- 后端默认地址：`http://127.0.0.1:8001`
- 前端默认地址：`http://127.0.0.1:5173`
- 前端代理目标：`http://127.0.0.1:8001`
- 路由注册：`backend/router_registry.py`

`backend_api_server.py`、`app/api_server.py`、`simple_backend.py`、`enhanced_web_server.py` 属于历史入口，仅用于兼容或排查旧流程，不再作为新开发启动方式。

## 快速启动

### 推荐方式：一键启动

在仓库根目录运行：

```powershell
powershell -ExecutionPolicy Bypass -File G:\AI项目\ai测试\ai-test-platform\start-dev.ps1
```

只查看服务状态：

```powershell
powershell -ExecutionPolicy Bypass -File G:\AI项目\ai测试\ai-test-platform\start-dev.ps1 -StatusOnly
```

启动成功后访问：

- 前端：`http://127.0.0.1:5173/dashboard`
- 后端健康检查：`http://127.0.0.1:8001/health`
- 后端接口文档：`http://127.0.0.1:8001/docs`

### 手动启动后端

```powershell
cd G:\AI项目\ai测试\ai-test-platform
& "D:\python311\Scripts\uvicorn.exe" backend.app:create_app --factory --host 127.0.0.1 --port 8001
```

如果使用项目虚拟环境：

```powershell
cd G:\AI项目\ai测试\ai-test-platform
.\venv\Scripts\python.exe -m uvicorn backend.app:create_app --factory --host 127.0.0.1 --port 8001
```

### 手动启动前端

PowerShell 下优先使用 `npm.cmd`，避免 `npm.ps1` 执行策略问题：

```powershell
cd G:\AI项目\ai测试\ai-test-platform\frontend
& "C:\Program Files\nodejs\npm.cmd" install
& "C:\Program Files\nodejs\npm.cmd" run dev -- --host 127.0.0.1 --port 5173
```

注意：必须在 `frontend` 目录运行前端命令，因为 `package.json` 位于 `frontend/package.json`。

## 环境配置

首次运行可复制 `.env.example`：

```powershell
cd G:\AI项目\ai测试\ai-test-platform
Copy-Item .env.example .env
```

本地开发默认值：

```env
APP_MODE=mock
USE_MOCK_DATA=true
AI_PROVIDER=none
AI_ANALYSIS_MODE=rule
BACKEND_HOST=127.0.0.1
BACKEND_PORT=8001
FRONTEND_HOST=127.0.0.1
FRONTEND_PORT=5173
```

真实被测系统联调时，在 Web 页面中维护项目环境、鉴权配置和 Web UI 登录会话；不要把 token、cookie、authorization 等敏感值写进代码或提交到仓库。

## 常用命令

安装后端依赖：

```powershell
cd G:\AI项目\ai测试\ai-test-platform
pip install -r requirements.txt
```

安装前端依赖：

```powershell
cd G:\AI项目\ai测试\ai-test-platform\frontend
& "C:\Program Files\nodejs\npm.cmd" install
```

运行前端检查：

```powershell
cd G:\AI项目\ai测试\ai-test-platform\frontend
& "C:\Program Files\nodejs\npm.cmd" run lint
```

检查后端健康：

```powershell
Invoke-RestMethod http://127.0.0.1:8001/health
```

检查 Web UI 登录会话健康：

```powershell
Invoke-RestMethod http://127.0.0.1:8001/api/v2/ui/login-sessions/health
```

## 核心目录

```text
ai-test-platform/
├── backend/       # FastAPI app 工厂、配置、中间件、异常处理、启动生命周期
├── routes/        # HTTP 路由模块
├── services/      # 业务服务、执行引擎、状态机、脱敏等
├── database/      # SQLAlchemy 模型、session、repository
├── schemas/       # Pydantic 请求/响应模型
├── ai_core/       # 新 AI 客户端、工作流与编排能力
├── frontend/      # React 18 + Vite + Tailwind + antd
├── knowledge/     # RAG/知识库、接口样本
├── scripts/       # 本地脚本、验收脚本、批处理脚本
├── docs/          # 设计、验收、阶段报告和治理文档
└── tests/         # 测试代码
```

## 重要约定

- 新后端接口优先注册到 V2 路由体系，并保持标准错误结构：`{code, message, trace_id, details, detail}`。
- 新前端请求应复用 `frontend/src/services/api.js` 中已有封装；后续会按业务域拆分。
- Web UI 自动化依赖 Playwright 浏览器，如果执行时报 `headless_shell.exe` 不存在，需要在对应 Python 环境里执行 `python -m playwright install chromium`。
- 鉴权配置可能包含 token、cookie、authorization，写入和展示时都必须做脱敏。
- 被测系统源码副本不应继续放在本仓库根目录，清理计划见 `docs/REPO_CLEANUP_PLAN.md`。

## 常见问题

### 127.0.0.1:5173 打不开

先确认服务状态：

```powershell
powershell -ExecutionPolicy Bypass -File G:\AI项目\ai测试\ai-test-platform\start-dev.ps1 -StatusOnly
```

如果前端未启动，在 `frontend` 目录运行：

```powershell
cd G:\AI项目\ai测试\ai-test-platform\frontend
& "C:\Program Files\nodejs\npm.cmd" run dev -- --host 127.0.0.1 --port 5173
```

### 前端请求后端失败

确认后端运行在 8001：

```powershell
Invoke-RestMethod http://127.0.0.1:8001/health
```

确认 `frontend/vite.config.js` 的代理目标是 `http://127.0.0.1:8001`。

### Web UI 用例被重定向到 SSO 登录页

说明当前 Web UI 登录态失效或 token 被黑名单拦截。处理顺序：

1. 在项目环境里更新有效 `access_token`，不要填 `refresh_token`。
2. 重新保存 Web UI 登录会话。
3. 打开仪表盘查看登录态健康卡片，确认状态为有效。
4. 再执行 Web UI 用例。

### 创建缺陷提示 run_case_id 类型错误

接口要求 `run_case_id` 是字符串。前端或调用方传参时需要把数字 ID 转成字符串，例如 `"7282"`。

## 文档治理

历史阶段报告、验收报告和专项分析统一沉淀在 `docs/` 或 `docs/archive/`。根目录只保留面向新接手者的入口文档和必要启动脚本，避免搜索、构建、排查时被历史材料干扰。
