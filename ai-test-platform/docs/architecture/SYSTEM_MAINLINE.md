# SYSTEM MAINLINE

> 平台治理与主线收敛阶段的唯一权威声明。任何与本文档冲突的旧文档（含 `docs/archive/*`、`backend_api_server.py` 顶部说明、各模块 README）一律以本文档为准。

## 1. 主线对照表

| 模块 | 唯一主线 | 备注 |
| --- | --- | --- |
| Backend Entry | `backend.app:create_app` | FastAPI 工厂；通过 `backend/router_registry.py` 集中注册路由 |
| API Prefix | `/api/v2` | 所有新接口必须以 `/api/v2/...` 暴露；`/api/*` 为 V1 兼容层，禁止扩张 |
| AI Core | `ai_core/` | 所有 AI 能力的入口；`ai/`、`agent/` 仅作为兼容 shim 存在 |
| Executor | `app/executor_v2/` | 用例执行的唯一引擎；`executor/` 为 V1，禁止新增逻辑 |
| Frontend Pages | `frontend/src/pages/*V2.jsx` 及无版本后缀的 V2 主线页面 | 非 V2 命名页面（`*-Simple.jsx`、`*-Pro.jsx`、`*List.jsx` 等）若仍存在仅供参考，禁止扩展 |
| Workflow | `ai_core/workflow/` | 编排/Pipeline/Skills 的唯一调度入口 |

## 2. 启动方式（唯一）

```bash
uvicorn backend.app:create_app --factory --reload
```

生产/开发任何环境都只允许通过工厂入口启动。`backend_api_server.py`、`app/api_server.py`、`simple_backend.py`、`enhanced_web_server.py` 已 deprecated，仅保留向后兼容的 import path，不再作为启动入口。

## 3. 治理硬约束

1. **legacy 目录禁止新增代码**
   - `tests/legacy/`（已迁出至 `archive/tests_legacy/`）、`archive/**`、`docs/archive/**` 仅作历史归档使用。
   - 仓库根下未列入主线对照表的旧模块（`ai/`、`agent/`、`executor/`、`pipeline/`、`pilot/`、`orchestrator/`、`case_generator/`、`assertion/`、`automation/`、`parser/`、`self_healing/`、`strategy/`、`test_design/`、`report/`、`export/`、`schemas/`、`config/`、`configs/`、`common/`、`knowledge/`、`utils/` 等）只允许 bug fix 和必要 shim，不允许扩张功能。
2. **所有新功能只能进入主线**
   - 新接口 → `routes/*` 并由 `backend/router_registry.py` 注册到 `/api/v2`。
   - 新 AI 能力 → `ai_core/`（agents / orchestration / skills / workflow）。
   - 新执行能力 → `app/executor_v2/`。
   - 新页面 → `frontend/src/pages/` 下 V2 主线命名。
3. **deprecated 模块仅允许 shim**
   - 旧入口（`backend_api_server.py` 等）只能保留 re-export 与 `DeprecationWarning`，不得新增业务逻辑。
   - 旧路由前缀 `/api/*` 不得新增 endpoint；现有 endpoint 仅做兼容，迁移目标全部指向 `/api/v2`。
4. **禁止继续双轨开发**
   - 同一能力不允许同时存在 V1 / V2 两份实现。新需求落地后，对应 V1 必须在同一 PR 内打 deprecate 标记或迁出 legacy。
   - 严禁出现 `xxx_v3.py`、`xxx_pro.py`、`xxx_simple.py`、`xxx_new.py` 这类并行实现。

## 4. 仓库布局红线

仓库根目录只允许以下条目（其余必须归位到 `docs/`、`docs/archive/`、`docs/frontend/`、`scripts/`、`frontend/scripts/`、`frontend/demo/`、`archive/` 等子目录）：

```
README.md
CHANGELOG.md
requirements.txt
pytest.ini
docker-compose.yml
Dockerfile.backend
Dockerfile.frontend
.gitignore  .cursorignore  .copilotignore  .codeiumignore  .dockerignore  .env.example
start-dev.ps1  start_all.ps1
backend/
frontend/
docs/
scripts/
database/
routes/
services/
ai_core/
app/              ← 仅保留 executor_v2/，FROZEN
utils/            ← FROZEN
ai/               ← FROZEN
schemas/          ← FROZEN
config/           ← FROZEN
agent/            ← FROZEN
knowledge/        ← FROZEN
tests/
```

以下 6 个根级模块为活跃依赖，标记 FROZEN（仅允许 bug fix 和必要 shim）：

```
utils/       — code_analyzer, document_parser, req_code_diff 等工具函数
ai/          — ai_client, mock_ai_client
schemas/     — project_schemas, swagger_schemas, test_run_schemas
config/      — get_config / reload_config
agent/       — llm_client
knowledge/   — manual_retriever, decision_rag
```

其余旧根级模块已在 P1 阶段归档至 `archive/legacy_modules/`，不再被 git 跟踪。

## 5. 评审 / CI 默认规则

- pytest 默认从仓库根扫描 `tests/`、`scripts/`，自动忽略 `archive/`、`docs/`、`recycle-*/`、`蓝点/`。
- CI（`.github/workflows/ci.yml`）只跑 `scripts/run_regression_all.py` + 前端构建 + Docker compose 健康检查，不再扫描 `tests/legacy/`。
- 任何 PR 引入 V1 路由前缀 / legacy 模块新逻辑 / 双轨实现，CR 必须 reject。

## 6. 变更历史

- 2026-05 P0：建立本文档，配套完成根目录文档归档、自嵌套副本清理、ignore 收敛、tests/legacy 隔离、`backend_api_server.py` 加 `DeprecationWarning`、`pytest.ini` 收敛扫描范围。
- 2026-05 P1：根目录旧模块收敛——21 个孤立模块 git rm 归档至 `archive/legacy_modules/`；`app/` 拆分仅保留 `executor_v2/`；根目录散落 .py 迁入 `scripts/` 或归档；6 个活跃模块（utils/ai/schemas/config/agent/knowledge）标记 FROZEN；根 `__init__.py` 删除。
- 2026-05 P2：app/ 物理残留清理至 `archive/legacy_modules/app_legacy/`；白名单同步更新。