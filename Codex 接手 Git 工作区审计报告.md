# Codex 接手 Git 工作区审计报告

审计时间：2026-04-28  
仓库路径：`G:\AI项目\ai测试`  
审计范围：只读检查分支、Git 状态、deleted/modified/untracked 文件和关键 diff。  
限制遵守：未修改代码、未删除文件、未提交、未执行 `git add .`、未开始 Phase 12。本文件是本阶段唯一新增产物。

## 1. 当前分支与 Git 状态

当前分支：`master`，跟踪 `origin/master`。

工作区状态摘要：

| 类型 | 数量 | 说明 |
| --- | ---: | --- |
| deleted | 454 | 主要是 `ai-test-platform/` 根目录历史文档、脚本、测试、Swagger 样例被删除 |
| modified | 21 | 后端入口、AI 配置、前端入口/API、执行/报告模块等 |
| untracked entries | 258 | `git status` 折叠目录后的条目数 |
| untracked files | 585 | `git ls-files --others --exclude-standard` 展开后的文件数 |

额外观察：

- `git` 多次提示无法访问 `C:\Users\lenovo/.config/git/ignore`，不影响本次审计，但说明全局 ignore 配置不可读。
- 多个已修改文件提示后续 Git 触碰时可能 LF 转 CRLF，涉及 `backend_api_server.py`、`App.jsx` 和部分前端页面。
- 当前工作区像是一次“大规模工程化重组 + Phase 1-11 功能接入 + 根目录清理”尚未整理成提交。

## 2. Deleted 文件分析

deleted 总计 454 个，按扩展名：

| 扩展名 | 数量 | 判断 |
| --- | ---: | --- |
| `.md` | 222 | 多为历史报告、完成报告、指南、交付清单，可归档 |
| `.py` | 203 | 多为脚本、测试、验证脚本，很多已有 untracked 新位置 |
| `.bat` | 15 | 启动/演示/检查脚本，很多已有 `scripts/batch/` 新位置 |
| `.json` | 7 | Swagger 样例、测试报告、mock 数据，不能直接丢失 |
| `.txt` | 4 | 测试输入/交付总结类文档 |
| `.docx` | 2 | 测试需求/上传样例 |
| `.sh` | 1 | Web 启动脚本 |

### 2.1 可归档或删除的历史报告/临时文档

有 221 个 deleted 文件没有同名 untracked 新位置，基本都是历史报告、完成说明、使用指南、交付清单。建议不要继续散落在 `ai-test-platform/` 根目录，可统一归档到 `docs/archive/legacy-reports/` 或从版本库删除，但删除需要单独提交并在提交说明中说明“文档归档/根目录清理”。

代表文件：

- `ai-test-platform/AI功能优化完成报告.md`
- `ai-test-platform/AI测试控制台完成报告.md`
- `ai-test-platform/Architecture_Upgrade_Complete_Summary.md`
- `ai-test-platform/FINAL_ARCHITECTURE.md`
- `ai-test-platform/FILES_INDEX.md`
- `ai-test-platform/PROJECT_SUMMARY.md`
- `ai-test-platform/QUICKSTART.md`
- `ai-test-platform/START_GUIDE.md`
- `ai-test-platform/Swagger导入使用说明.md`
- `ai-test-platform/系统架构最终版.md`
- `ai-test-platform/系统完整状态_2026-03-23.md`
- `ai-test-platform/项目使用指南.md`

建议：保留少量仍然有价值的入口文档，例如架构、启动、使用索引类文档；其他完成报告按日期/阶段归档。

### 2.2 不应该直接删除的核心脚本、Swagger、测试数据

有 233 个 deleted 文件与 untracked 文件同名匹配，疑似从根目录迁移到更合理目录。不能只提交删除，必须同时提交新位置或恢复旧位置。

迁移关系代表：

- `ai-test-platform/start_platform.py` -> `ai-test-platform/scripts/start_platform.py`
- `ai-test-platform/start_react_platform.py` -> `ai-test-platform/scripts/start_react_platform.py`
- `ai-test-platform/start_enhanced_platform.py` -> `ai-test-platform/scripts/start_enhanced_platform.py`
- `ai-test-platform/health_check.py` -> `ai-test-platform/scripts/health_check.py`
- `ai-test-platform/check_system.py` -> `ai-test-platform/scripts/check_system.py`
- `ai-test-platform/sample_swagger.json` -> `ai-test-platform/scripts/sample_swagger.json`
- `ai-test-platform/test-swagger-example.json` -> `ai-test-platform/scripts/test-swagger-example.json`
- `ai-test-platform/swaggerApi (1).json` -> `ai-test-platform/scripts/swaggerApi (1).json`
- `ai-test-platform/test_doc.docx` -> `ai-test-platform/scripts/test_doc.docx`
- `ai-test-platform/test_requirement.docx` -> `ai-test-platform/scripts/test_requirement.docx`
- `ai-test-platform/test_requirement.txt` -> `ai-test-platform/scripts/test_requirement.txt`
- `ai-test-platform/test_response.txt` -> `ai-test-platform/scripts/test_response.txt`
- `ai-test-platform/一键启动.bat` -> `ai-test-platform/scripts/batch/一键启动.bat`
- `ai-test-platform/启动Web平台.bat` -> `ai-test-platform/scripts/batch/启动Web平台.bat`
- `ai-test-platform/启动后端.bat` -> `ai-test-platform/scripts/batch/启动后端.bat`
- `ai-test-platform/test_*.py` -> `ai-test-platform/tests/legacy/test_*.py`
- `ai-test-platform/verify_*.py` -> `ai-test-platform/scripts/verify/verify_*.py`

建议：如果这是有意重组，应作为“脚本/测试归位”单独提交，不能和 Phase 12 混在一起。

### 2.3 删除可能影响系统启动或测试链路

如果 deleted 被提交而对应 untracked 新位置没有提交，下面链路会直接断：

- 启动链路：`start_platform.py`、`start_react_platform.py`、`start_enhanced_platform.py`、`启动Web平台.bat`、`启动后端.bat`、`一键启动.bat`。
- 健康检查/诊断链路：`health_check.py`、`check_system.py`、`diagnose_backend.py`、`diagnose_frontend` 类脚本。
- Swagger 导入/测试数据链路：`sample_swagger.json`、`test-swagger-example.json`、`swaggerApi (1).json`、`test_requirement.*`、`test_doc.docx`。
- 回归测试链路：所有根目录 `test_*.py` 与 `verify_*.py`，目前迁移到 `tests/legacy/` 或 `scripts/verify/`。

结论：当前 deleted 中没有明显“只有删除、没有任何替代”的核心代码文件；但所有非文档删除都必须随新位置一起提交，或在 Phase 12 前恢复。

## 3. Modified 文件分析

用户点名 8 个 modified 文件共计：1242 insertions，165 deletions。

| 文件 | 变更量 | 主要内容 | 风险/注意 |
| --- | ---: | --- | --- |
| `ai-test-platform/backend_api_server.py` | +632/-53 | 启动时数据库健康检查；注册项目配置、测试执行、可观测性、执行触发、Swagger、Executor V2 路由；新增 `/readiness`；增强 `/health`；批量删除 ID 支持字符串；增强 AI 生成；新增 `/api/v2/test/run-intelligent` | 依赖大量 untracked `database/`、`routes/`、`services/`、`schemas/`、`app/executor_v2/`。Pilot 后端被硬编码禁用，但前端 `api.js` 仍调用 `/api/pilot`。新增智能 Pipeline 中使用了未定义的 `test_cases`，应为 `test_cases_db`，且 `ExecutionEngine.execute(exec_case)` 传入单个 dict，疑似与执行引擎接口不匹配 |
| `ai-test-platform/orchestrator/base_runner.py` | +117/-25 | `ApiRunner` 接入 `ExecutionEngineV2`，支持真实 HTTP 执行，缺少 method/path 时返回 `skipped` | 强依赖 untracked `app/executor_v2/*`。旧 mock 通过率逻辑被移除，旧用例如果没有执行字段将从随机 passed 变为 skipped，测试统计语义会变 |
| `ai-test-platform/ai/ai_client.py` | +29/-7 | 增加模块级 AI 配置，OpenRouter 请求头，`get_ai_client(module=...)` | `get_ai_client` 先把 `provider` 置为默认值，可能导致模块 provider 不能完整覆盖 `self.provider`，特别是 Ollama/OpenRouter 鉴权逻辑需复核。Anthropic 配置日志会打印 key 前缀，建议脱敏 |
| `ai-test-platform/config/config.py` | +60/-8 | 新增模块级 AI env：`TESTCASE_GENERATION_AI_PROVIDER` 等；新增 `get_module_ai_config`、`get_all_module_configs`；OpenAI 可用模型改为 GLM 系列 | “openai” provider 实际被用于智谱兼容接口，命名需统一。`validate()` 仍只检查 DeepSeek/OpenAI key，没有覆盖 Anthropic、OpenRouter、模块配置 |
| `ai-test-platform/frontend/src/App.jsx` | +116/-58 | 前端入口切到 V2 导航；新增 `ToastProvider`；新增角色选择并写 `pilot_role`；默认 `/` 跳转 `/projects-v2`；移除旧 Dashboard/Automation 等入口 | 依赖大量 untracked V2 页面/组件。旧 `/api-explorer-old` 重定向到 `/api-explorer`，但当前没有 `/api-explorer` route，存在断路。角色选择与 `/api/pilot` 头配套，但后端 Pilot 当前禁用 |
| `ai-test-platform/frontend/src/services/api.js` | +271/-12 | 新增 `PILOT_API_BASE_URL=/api/pilot`；所有请求加 `X-User-Role`；新增大量 `/api/v2/*` API；项目/运行/报告旧 API 指向 pilot | 后端 `backend_api_server.py` 当前没有加载 `/api/pilot`，所以 `api.projects/getAll`、`api.testRuns`、`api.reports` 会 404。V2 API 与 Pilot API 并存，提交前必须统一前端使用哪条链路 |
| `modules/executor/execution_engine.py` | +16/-2 | `create_execution_result` 写入 `assertions_passed`、`assertions_failed` | 与 `core.models.ExecutionResult` 字段匹配，属于合理增强。需确认所有 runner 返回的 `assertion_results` 字段结构都含 `passed` |
| `modules/report/report_generator.py` | +1/-0 | summary 增加 `error: 0` | 兼容 HTML 模板的低风险修复 |

其他 modified 文件也需要在 Phase 12 前一起处理：

- `ai-test-platform/routes/ai_routes.py`：新增 SVN 文档生成测试用例、AI 配置查询/热更新接口；该接口会写 `.env`，需要权限和审计保护。
- `ai-test-platform/requirements.txt`：固定 `anyio==3.7.1`、`starlette==0.27.0`。
- `ai-test-platform/utils/data_manager.py`：Windows 原子写入兼容。
- `core/enums.py`：新增 `RunStatus`。
- `ai-test-platform/frontend/src/main.jsx`、多个旧页面、`tailwind.config.js`：前端 V2/样式适配。
- `quick_start_guide.md`：大幅文档调整。

## 4. Untracked 文件分析

untracked 展开后 585 个文件。按扩展名：`.py` 361、`.md` 129、`.jsx` 42、`.bat` 25、`.json` 15、`.txt` 5、`.docx` 2、`.ps1` 1、`.code-workspace` 1、`.sh` 1、`.js` 1、`.css` 1、`.bluedot` 1。

### 4.1 Phase 1-11 新增核心代码，建议保留并进入核心提交

后端核心：

```text
ai-test-platform/app/executor_v2/
ai-test-platform/config/svn_config.py
ai-test-platform/database/
ai-test-platform/routes/execution_trigger_routes.py
ai-test-platform/routes/executor_v2_routes.py
ai-test-platform/routes/observability_routes.py
ai-test-platform/routes/project_config_routes.py
ai-test-platform/routes/swagger_routes.py
ai-test-platform/routes/test_run_routes.py
ai-test-platform/schemas/
ai-test-platform/services/
ai-test-platform/utils/auth_crypto.py
ai-test-platform/utils/document_parser.py
ai-test-platform/utils/svn_utils.py
```

前端核心：

```text
ai-test-platform/frontend/src/components/ApiCard.jsx
ai-test-platform/frontend/src/components/AuthProfileForm.jsx
ai-test-platform/frontend/src/components/DetailCard.jsx
ai-test-platform/frontend/src/components/EmptyState.jsx
ai-test-platform/frontend/src/components/EnvironmentForm.jsx
ai-test-platform/frontend/src/components/EnvironmentManager.jsx
ai-test-platform/frontend/src/components/ExecutionCard.jsx
ai-test-platform/frontend/src/components/ExecutionTriggerDialog.jsx
ai-test-platform/frontend/src/components/FilterPanel.jsx
ai-test-platform/frontend/src/components/MetaInfo.jsx
ai-test-platform/frontend/src/components/PageHeader.jsx
ai-test-platform/frontend/src/components/ProjectCard.jsx
ai-test-platform/frontend/src/components/StatusBadge.jsx
ai-test-platform/frontend/src/components/SVNInput.jsx
ai-test-platform/frontend/src/components/TestCaseCard.jsx
ai-test-platform/frontend/src/components/ui/ConfirmDialog.jsx
ai-test-platform/frontend/src/components/ui/PageTransition.jsx
ai-test-platform/frontend/src/components/ui/Skeleton.jsx
ai-test-platform/frontend/src/components/ui/Toast.jsx
ai-test-platform/frontend/src/pages/AIConfigPage.jsx
ai-test-platform/frontend/src/pages/AISettings.jsx
ai-test-platform/frontend/src/pages/ApiDetail.jsx
ai-test-platform/frontend/src/pages/ApiExplorerPro.jsx
ai-test-platform/frontend/src/pages/ApiList.jsx
ai-test-platform/frontend/src/pages/ApiSpecDetail.jsx
ai-test-platform/frontend/src/pages/ApiSpecList.jsx
ai-test-platform/frontend/src/pages/ExecutionDetail.jsx
ai-test-platform/frontend/src/pages/ExecutorV2.jsx
ai-test-platform/frontend/src/pages/ProjectDetail.jsx
ai-test-platform/frontend/src/pages/ProjectDetailV2.jsx
ai-test-platform/frontend/src/pages/ProjectsList.jsx
ai-test-platform/frontend/src/pages/ProjectsV2.jsx
ai-test-platform/frontend/src/pages/QuickExecutionTest.jsx
ai-test-platform/frontend/src/pages/ReportDetail.jsx
ai-test-platform/frontend/src/pages/SwaggerWorkbench.jsx
ai-test-platform/frontend/src/pages/TestCaseDetail.jsx
ai-test-platform/frontend/src/pages/TestCasesList.jsx
ai-test-platform/frontend/src/pages/TestCasesPro.jsx
ai-test-platform/frontend/src/pages/TestRunDetailV2.jsx
ai-test-platform/frontend/src/pages/TestRunsList.jsx
ai-test-platform/frontend/src/pages/TestRunsV2.jsx
ai-test-platform/frontend/src/styles/enterprise.css
```

测试/迁移/验证核心：

```text
ai-test-platform/tests/legacy/
ai-test-platform/scripts/init_db.py
ai-test-platform/scripts/migrate_json_to_db.py
ai-test-platform/scripts/check_and_start_backend.py
ai-test-platform/scripts/quick_import_swagger.py
ai-test-platform/scripts/verify/verify_database.py
ai-test-platform/scripts/verify/verify_observability.py
ai-test-platform/scripts/verify/verify_run_steps.py
ai-test-platform/scripts/verify_executor_v2.py
ai-test-platform/scripts/_integration_verify.py
ai-test-platform/scripts/_p11_frontend_verify.py
ai-test-platform/scripts/_p11_test_guard.py
```

需要单独决策的核心/准核心：

- `ai-test-platform/pilot/`：提供 `/api/pilot`，但当前 `backend_api_server.py` 已禁用 Pilot。若前端继续使用 `/api/pilot`，必须解决模型冲突并加载；若改用 `/api/v2`，则前端 `api.js` 应移除 Pilot 依赖。
- `ai-test-platform/knowledge/landian_apis.json`、Postman JSON、`蓝点/bluedot_openapi.json`：对蓝点/蓝点知识库试点有用，但包含内部接口信息，应按敏感资料处理。
- `ai-test-platform/scripts/`：包含大量从根目录迁移来的旧脚本。建议分为 `scripts/dev/`、`scripts/verify/`、`scripts/demo/`、`scripts/batch/`，不要把一次性临时脚本混入核心目录。

### 4.2 报告文档

untracked 文档集中在仓库根目录和前端目录，例如：

- `P0-3_STATE_MACHINE_COMPLETE.md`
- `P0-4_OBSERVABILITY_COMPLETE.md`
- `P0-5.1_EXECUTION_TRIGGER_COMPLETE.md`
- `P0-7_COMPLETE_REPORT.md`
- `P0-8.1_环境管理完成报告.md`
- `PIPELINE_V2_INDEX.md`
- `PIPELINE_V2_SUMMARY.md`
- `POST_PILOT_HARDENING_REPORT.md`
- `REAL_PILOT_REPORT.md`
- `ai-test-platform/Phase1-10_联调验收报告.md`
- `ai-test-platform/Phase11_前端验收与业务断言修正报告.md`
- `ai-test-platform/frontend/FRONTEND_OPTIMIZATION_FINAL_REPORT.md`
- `ai-test-platform/frontend/PHASE_5_EXECUTION_OPTIMIZATION_COMPLETE.md`

建议：报告文档单独归档提交，不要和核心代码同提交。可保留 `Phase1-10`、`Phase11`、`P0_*` 汇总索引，其余完成报告移入 `docs/archive/phase-reports/`。

### 4.3 临时脚本和试点脚本

根目录出现大量临时脚本，建议不要直接提交：

- `check_*.py`
- `debug_*.py`
- `diagnose_*.py`
- `fix_*.py`
- `test_*.py`
- `verify_*.py`
- `pilot_bluedot*.py`
- `zhipu_integration_test.py`
- `retry_bluedot_pilot.bat`
- `start_p0_7_demo.bat`
- `demo/`
- `ai测试/`
- `蓝点/`

处理建议：有复用价值的脚本迁入 `ai-test-platform/scripts/dev/` 或 `scripts/verify/`，一次性脚本归档或忽略；根目录不应继续堆放临时脚本。

### 4.4 敏感信息

发现以下敏感风险，报告中不记录任何密钥明文：

- `.env.bluedot` 包含 `BLUEDOT_TOKEN`、`BLUEDOT_CLIENT_SECRET`、`BLUEDOT_USERNAME`、`BLUEDOT_PASSWORD` 等。必须加入 `.gitignore`，不得提交。
- `test_openrouter_key.py` 含硬编码 OpenRouter API Key。必须删除或改为读取环境变量，并轮换已暴露密钥。
- `test_zhipu_key.py` 含硬编码智谱 Key。必须删除或改为读取环境变量，并轮换已暴露密钥。
- `pilot_bluedot_with_token.py` 含硬编码 JWT Token。必须删除或改为读取环境变量，并轮换 Token。
- `debug_env.py` 会读取并打印蓝点环境变量信息，应作为本地诊断脚本，不应提交。
- `蓝点/bluedot_openapi.json` 约 10.7 MB，包含内部 OpenAPI 资料。除非已脱敏且确认可以进入仓库，否则不应提交。
- `data/platform_data.json` 含生成的测试用例/运行数据，属于运行数据或样例数据，建议不要作为核心代码提交。

## 5. 明确建议清单

### 5.1 应该保留的文件

必须保留并在 Phase 12 前整理提交：

- 8 个用户点名 modified 文件。
- 其他核心 modified：`routes/ai_routes.py`、`requirements.txt`、`utils/data_manager.py`、`core/enums.py`、前端相关 modified。
- `ai-test-platform/database/`
- `ai-test-platform/services/`
- `ai-test-platform/schemas/`
- `ai-test-platform/routes/*_routes.py`
- `ai-test-platform/app/executor_v2/`
- `ai-test-platform/frontend/src/components/`
- `ai-test-platform/frontend/src/pages/*V2.jsx`
- `ai-test-platform/frontend/src/pages/SwaggerWorkbench.jsx`
- `ai-test-platform/frontend/src/pages/ExecutorV2.jsx`
- `ai-test-platform/frontend/src/pages/AIConfigPage.jsx`
- `ai-test-platform/frontend/src/styles/enterprise.css`
- `ai-test-platform/tests/legacy/`，直到新测试目录策略确定。
- 迁移后的启动/验证/样例脚本：`ai-test-platform/scripts/` 中可复用部分。

条件保留：

- `ai-test-platform/pilot/`：只有在继续支持 `/api/pilot` 时保留并修复加载冲突。
- `ai-test-platform/knowledge/*.json`、`蓝点/bluedot_openapi.json`：只有在确认脱敏和授权后保留。

### 5.2 应该加入 `.gitignore` 的文件或模式

建议先做 `.gitignore` 提交，再整理代码提交：

```gitignore
.env.*
*.bluedot
*.code-workspace
data/
bluedot_pilot_result.json
landian_project_config.json
test_openrouter_key.py
test_zhipu_key.py
test_credentials.py
pilot_bluedot_with_token.py
debug_env.py
retry_bluedot_pilot.bat
蓝点/bluedot_openapi.json
```

可选，取决于团队是否允许根目录临时脚本：

```gitignore
/debug_*.py
/diagnose_*.py
/fix_*.py
/check_*.py
/verify_*.py
/pilot_bluedot*.py
/zhipu_integration_test.py
```

注意：不要粗暴忽略所有 `test_*.py`，否则可能屏蔽真正回归测试。应优先迁移到 `tests/`。

### 5.3 应该恢复的误删文件

严格说，本次未发现“核心代码只被删除且没有替代位置”的文件；非文档删除大多已有同名 untracked 迁移版本。

但在进入 Phase 12 前，下面三类必须二选一处理：

1. 提交迁移后的新位置：`scripts/`、`scripts/batch/`、`scripts/verify/`、`tests/legacy/`、`scripts/*.json/*.docx/*.txt`。
2. 如果短期不提交迁移，则恢复旧位置的启动脚本、测试脚本、Swagger 样例和测试需求文件。
3. 如果提交迁移，则同步更新 README、启动说明、CI/pytest 配置和脚本路径引用。

建议条件性恢复或保留入口包装的文件：

- `ai-test-platform/启动后端.bat`
- `ai-test-platform/启动Web平台.bat`
- `ai-test-platform/一键启动.bat`
- `ai-test-platform/start_platform.py`
- `ai-test-platform/start_react_platform.py`
- `ai-test-platform/sample_swagger.json`
- `ai-test-platform/test-swagger-example.json`
- `ai-test-platform/test_requirement.txt`

文档类不建议简单恢复到根目录，建议归档：

- `ai-test-platform/QUICKSTART.md`
- `ai-test-platform/START_GUIDE.md`
- `ai-test-platform/FILES_INDEX.md`
- `ai-test-platform/FINAL_ARCHITECTURE.md`
- `ai-test-platform/PROJECT_SUMMARY.md`
- `ai-test-platform/系统架构最终版.md`
- `ai-test-platform/使用手册索引.md`

### 5.4 可以归档的文档和 demo

可归档到 `docs/archive/legacy-reports/`：

- `ai-test-platform/*完成报告.md`
- `ai-test-platform/*完成总结.md`
- `ai-test-platform/*交付清单.md`
- `ai-test-platform/*使用指南.md`
- 根目录 `P0-*`、`P0_*`、`PIPELINE_V2_*`、`*_COMPLETE.md`
- `ai-test-platform/frontend/*COMPLETE.md`
- `ai-test-platform/frontend/*GUIDE.md`

可归档到 `demo/legacy/` 或 `scripts/demo/legacy/`：

- `demo/`
- `ai-test-platform/scripts/demo/`
- `start_p0_7_demo.bat`
- `DEMO_GUIDE.md`
- `DEMO_PIPELINE_COMPLETE.md`
- `INTELLIGENT_RUN_DEMO.md`

### 5.5 进入 Phase 12 前必须先提交的核心改动

建议按以下顺序拆提交，严禁 `git add .`：

1. 安全与 ignore 提交：加入 `.env.*`、`*.bluedot`、敏感脚本和本地数据 ignore；确认不提交 `.env.bluedot`、硬编码 key/token 脚本；轮换已暴露凭据。
2. 后端核心提交：`database/`、`services/`、`schemas/`、`routes/`、`app/executor_v2/`、`config/svn_config.py`、`utils/*`、`backend_api_server.py`、`requirements.txt`、`core/enums.py`、`modules/executor/*`、`modules/report/*`。
3. 前端核心提交：`frontend/src/App.jsx`、`frontend/src/services/api.js`、V2 页面、共享组件、Toast/Skeleton/Dialog、`enterprise.css`、相关 modified 页面。
4. 脚本和测试迁移提交：把 root deleted 的脚本/测试/样例文件与 `scripts/`、`tests/legacy/` 新位置一起提交，并更新路径引用。
5. 文档归档提交：把历史报告、完成文档、demo 文档归档或删除，避免和代码变更混在一起。
6. 冲突修复提交：在 Phase 12 前修复 `/api/pilot` 与 `/api/v2` 取舍、`backend_api_server.py` 中 `test_cases` 未定义、智能 Pipeline 执行接口不匹配、前端 `/api-explorer` 断路。

## 6. Phase 12 前阻塞项

必须先解决：

- 敏感文件和硬编码凭据不能提交，且已出现的 key/token 应轮换。
- `backend_api_server.py` 禁用 Pilot，但 `api.js` 把项目/运行/报告指向 `/api/pilot`，前后端不一致。
- untracked 核心代码未提交，当前 modified 文件依赖这些模块，不能单独提交。
- deleted 的脚本/测试/样例文件必须与新位置一起提交或恢复旧位置。
- `backend_api_server.py` 新增智能 Pipeline 中存在明显变量/接口风险。
- 前端旧路由重定向存在断路：`/api-explorer-old` -> `/api-explorer`，当前未注册 `/api-explorer`。

建议在上述提交完成并至少做一次后端 import 检查、前端 build、基础 API smoke test 后，再开始 Phase 12。
