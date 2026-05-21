# 项目快照分析 — 渐进式重构基线

## 1. 核心代码目录

| 目录 | 作用 | 保留 |
|------|------|------|
| `agent/` | LLM 调用 + AI 决策（Pipeline Stage 1） | ✅ |
| `ai/` | AI 客户端统一层（传统流程用） | ✅ |
| `strategy/` | 测试策略生成（Pipeline Stage 2） | ✅ |
| `case_generator/` | 用例生成服务 | ✅ |
| `orchestrator/` | 测试编排 + **Mock Runner**（重写目标） | ⚠️ 重写 Runner |
| `self_healing/` | 自愈修复（含 Mock 重试） | ⚠️ 后续升级 |
| `pipeline/` | Pipeline 调度链 | ✅ |
| `executor/` | 旧版执行器（半成品） | ⚠️ 保留参考 |
| `config/` | 配置管理 | ✅ |
| `common/` | TestContext 等公共类 | ✅ |
| `database/` | SQLAlchemy 数据库 | ✅ |
| `routes/` | FastAPI 路由模块 | ✅ |
| `services/` | 业务服务层 | ✅ |
| `schemas/` | Pydantic 模型 | ✅ |
| `frontend/` | React + Ant Design 前端 | ✅ |
| `automation/` | API 脚本生成器 | ✅ |
| `assertion/` | 断言引擎（已有基础） | ✅ 升级 |
| `knowledge/` | 知识库（ChromaDB） | ✅ |
| `parser/` | 需求解析器 | ✅ |
| `report/` | 报告生成 | ✅ |
| `templates/` | 报告模板 | ✅ |
| `test_design/` | 传统测试设计流程 | ✅ |

## 2. Mock / Random 代码位置（必须替换）

| 文件 | 行号 | 问题 |
|------|------|------|
| `orchestrator/base_runner.py` | 149-153 | ApiRunner: `random.random() > 0.1` 模拟 90% 通过 |
| `orchestrator/base_runner.py` | 210-213 | UiRunner: `random.random() > 0.15` 模拟通过 |
| `orchestrator/base_runner.py` | 272-275 | IntegrationRunner: `random.random() > 0.2` 模拟通过 |
| `self_healing/healing_service.py` | 131-133 | 重试: `random.random() < 0.7` 模拟 70% 修复成功 |
| `self_healing/healing_worker.py` | 186-188 | Worker: `random.random() > 0.5` 模拟 50% 成功 |
| `executor/real_test_executor.py` | 434-436 | "真实"执行器: `random.random() > 0.1` 仍是假的 |

## 3. 后端执行相关路由

| 路由 | 方法 | 文件 | 作用 |
|------|------|------|------|
| `/api/execute-api` | POST | `backend_api_server.py:1224` | 执行单个 API 测试 |
| `/api/testcases/{id}/execute` | POST | `backend_api_server.py:2872` | 执行测试用例 |
| `/api/automation/scripts/{id}/execute` | POST | `backend_api_server.py:2775` | 执行脚本 |
| `/api/test-runs/start` | POST | `backend_api_server.py:2164` | 启动测试运行（V3 内存版） |
| `/api/test-runs/{id}/status` | GET | `backend_api_server.py:2199` | 获取运行状态 |
| `/api/v2/test-runs` | POST | `routes/test_run_routes.py` | 创建测试运行（数据库版） |
| `/api/pipeline/run` | POST | `pipeline/controller.py` | Pipeline 全流程 |

## 4. 前端执行相关页面

| 页面 | 文件 | 作用 |
|------|------|------|
| `ExecutionDetail.jsx` | 测试运行详情页 | **改造目标**：展示请求/响应/断言 |
| `TestRunDetailV2.jsx` | V2 运行详情页 | 可观测性详情 |
| `TestRuns.jsx` | 测试运行列表 | 运行列表页 |
| `TestRunsV2.jsx` | V2 运行列表 | V2 运行列表 |
| `TestRunsList.jsx` | 运行列表 | 简化版列表 |
| `QuickExecutionTest.jsx` | 快速执行测试 | 快速执行入口 |
| `AiTestConsole.jsx` | AI 控制台 | AI 一键测试 |

## 5. 前端 API 调用（执行相关）

| 前端调用 | 后端路由 |
|----------|----------|
| `api.apis.execute(data)` | `/api/execute-api` |
| `api.testCases.execute(id)` | `/api/testcases/{id}/execute` |
| `api.automation.executeScript(id)` | `/api/automation/scripts/{id}/execute` |
| `api.testRuns.start(data)` | `/api/pilot/test-runs` |
| `api.v2.testRuns.create(data)` | `/api/v2/test-runs` |
| `api.pipeline.run(data)` | `/api/pipeline/run` |

## 6. 需要清理的根目录文件分类

- **历史报告 .md**: ~150+ 个 → 移到 `docs/reports/old/`
- **demo_*.py**: ~10 个 → 移到 `scripts/demo/`
- **verify_*.py**: ~15 个 → 移到 `scripts/verify/`
- **test_*.py**: ~120 个 → 移到 `tests/`
- **临时 .html**: ~5 个 → 移到 `frontend/debug/`
- **临时 .bat/.sh**: ~15 个 → 移到 `scripts/`
