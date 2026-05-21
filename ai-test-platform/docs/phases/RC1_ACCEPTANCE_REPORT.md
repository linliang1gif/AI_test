# AI 测试平台 RC-1 验收报告

> 本报告仅基于客观事实，不写"生产就绪"、"v2.0 完成"、"企业级完全可用"等主观结论。
> 所有结论来源：git 状态、第一阶段 `acceptance_rc1.py` 真实输出、模块代码盘点、当前接口实际返回。

---

## 1. 验收结论

**RC-1 候选版本核心接口验收通过，FAIL=0，EXIT_CODE=0；当前允许进入真实项目验证、TAPD 风险收敛和代码对比 v2 质量评估阶段。**

| 维度 | 结果 |
|---|---|
| 第一阶段验收脚本 | TOTAL=15 / PASS=14 / FAIL=0 / WARN=1 / SKIP=0 / EXIT_CODE=0 |
| 核心接口 | 13 项全部 200 |
| 模块健康 | 40/40 modules `true` |
| TAPD 敏感字段脱敏 | `api_password='******'` ✅ |
| 错误结构化 | 4xx + `detail` 字段 ✅ |
| 明文敏感值泄露扫描 | 未命中 JWT/Bearer/Basic/bcrypt/AWS/PEM/PAT/Slack/OpenAI key ✅ |
| 唯一 WARN | Demo 数据未初始化（按规则不阻塞）|

**不写**：生产就绪、正式发布、v2.0 完成。

## 2. 验收范围

### 纳入

- 后端 29 个路由模块的可用性（通过 `/health.modules`）
- 13 个核心 HTTP 接口的可达性与状态码
- TAPD 集成的关键安全特性（密码脱敏、错误结构化）
- 敏感信息明文泄露扫描（基于 value pattern，非字段名）

### 不纳入

参见 §12。

## 3. 分支与代码状态

```
当前分支       feature/tapd-integration-and-code-compare
HEAD           e7d6bf7
工作区         clean（无未提交）
ahead/behind   0/0（与 origin 完全同步）
远端           origin (gitlab.szhibu.com)、github 均已同步
```

最近 5 条提交：

```
e7d6bf7 fix(tapd): 重构 finding 推 TAPD 的标题/描述/严重程度生成
3943c0d test(e2e): 端到端闭环脚本 finding -> 缺陷 -> TAPD -> 同步状态
79b403f fix(ai_routes): 解决长 AI 调用阻塞 + count=100 截断问题
b50c076 feat(tapd): TAPD 反向状态联动 - 自动推动本地缺陷状态机
1d3beeb docs: update SYSTEM_STATUS.md to 2026-05-07
```

## 4. 后端模块健康状态

来源：`GET /health` 响应中 `modules` 字段。

| 项 | 值 |
|---|---|
| 总模块数 | 40 |
| `true` 数 | 40 |
| `false` 数 | 0 |
| `database.connected` | `true` |
| `tables_ready` | `true` |
| `missing_tables` | `[]` |
| `app_mode` | `mock`（符合 RC-1 不依赖外网约束） |

按代码盘点：路由文件 29 个 `routes/*_routes.py`，全部 prefix 为 `/api/v2/...`（仅 `mock_routes.py` 为 `/api/mock`）。

## 5. 核心接口验收结果

来源：`scripts/acceptance_rc1.py` 第一阶段实际输出。

| # | check | 结果 | 备注 |
|---|---|---|---|
| 01 | `GET /health` | OK | `status=healthy`，`db.connected=true` |
| 02 | health.modules | OK | 全部 40 个模块 `true` |
| 03 | `GET /api/v2/projects` | OK | 200 |
| 04 | `GET /api/v2/test-cases?limit=5` | OK | 200，`total=4729` |
| 05 | `GET /api/v2/test-runs` | OK | 200 |
| 06 | `GET /api/v2/defects` | OK | 200 |
| 07 | `GET /api/v2/dashboard/summary` | OK | 200 |
| 08 | `GET /api/v2/analytics/overview` | OK | 200 |
| 09 | `GET /api/v2/code-compare/reports` | OK | 200 |
| 10 | `GET /api/v2/code-compare/tapd/config` | OK | api_password=`******` |
| 11 | `GET /api/v2/demo/status` | WARN | `initialized=false`（不阻塞）|
| 12 | `POST /api/v2/test-selection/recommend` | OK | 200（空 body 通过）|
| 13 | `GET /api/v2/quality-gates/default-config` | OK | 200 |
| 14 | 错误结构（不存在的 report_id）| OK | 404，含 `detail` |
| 15 | 敏感信息泄露扫描 | OK | 未命中任何明文敏感模式 |

## 6. TAPD 配置脱敏验证

| 项 | 现状 |
|---|---|
| 接口 | `GET /api/v2/code-compare/tapd/config` |
| 实际返回 | `config.api_password = "******"` |
| 实现位置 | `routes/code_compare_routes.py` 中 `get_tapd_config()` 显式将 `api_password` 替换为 `"******"` |
| 服务层 | `services/tapd_service.py::fetch_tapd_bug_status` 注释明确："不要把 api_password 暴露到日志或返回" |
| 写接口 | `POST /api/v2/code-compare/tapd/config` 接受 `api_password` 但写入文件后不回显（参见 `save_tapd_config_endpoint`） |

**结论**：TAPD 凭据在读路径上已脱敏，写路径不回显。

## 7. 错误结构化验证

| 项 | 现状 |
|---|---|
| 探测请求 | `GET /api/v2/code-compare/reports/__nonexistent_rc1__` |
| 实际响应 | HTTP 404，JSON 含 `detail` 字段 |
| 结构 | 符合 FastAPI 默认 `HTTPException` 响应模型 |

**结论**：错误响应结构化，未返回 HTML 或空响应。

## 8. 敏感信息泄露扫描

扫描范围：`/health`、`/api/v2/projects`、`/api/v2/code-compare/tapd/config`。

扫描方法：基于 value 内容的 pattern 匹配，**不命中字段名**：

| 模式 | 含义 |
|---|---|
| `eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+` | JWT |
| `Bearer\s+[A-Za-z0-9_\-\.~+/=]{16,}` | Bearer token |
| `Basic\s+[A-Za-z0-9+/]{20,}={0,2}` | Basic auth |
| `\$2[aby]\$\d{2}\$[A-Za-z0-9./]{53}` | bcrypt hash |
| `(AKIA\|ASIA)[A-Z0-9]{16}` | AWS access key |
| `-----BEGIN [A-Z ]*PRIVATE KEY-----` | PEM 私钥 |
| `xox[baprs]-[A-Za-z0-9-]{10,}` | Slack token |
| `ghp_[A-Za-z0-9]{30,}` | GitHub PAT |
| `sk-[A-Za-z0-9]{20,}` | OpenAI key |

白名单：纯 `*` 串、`<redacted>`、`REDACTED`、`masked` 等已脱敏占位。

**结论**：扫描三个端点未命中任何明文敏感模式。

## 9. Demo 状态 WARN 说明

| 项 | 内容 |
|---|---|
| 接口 | `GET /api/v2/demo/status` |
| 实际响应 | `{"data":{"initialized":false}}` |
| 影响 | Dashboard 等部分页面看到的样本数据较少；不影响核心接口可用性 |
| 处置规则 | 按用户指令：**不为消除 WARN 而初始化 demo 数据**。Demo 初始化属于写操作，会写入数据库；当前 RC-1 维持只读探测 |
| 后续动作 | 第二阶段（真实项目接入）时，由用户决定是否调用 `POST /api/v2/demo/init` |

## 10. 前端路由与页面盘点摘要

来源：扫描 `frontend/src/pages/*.jsx` 与 `frontend/src/App.jsx`。

| 项 | 数量 |
|---|---|
| `frontend/src/pages/*.jsx` 文件总数 | 52 |
| `App.jsx` 实际有效路由 | 23 |
| 历史路径重定向（`<Navigate>`）| 11 |
| 占位页（"暂未启用"）| 2（`/dataset-management`、`/test-data-factory`）|
| 文件存在但无路由（疑似死代码 / 历史版本）| 约 25 个 |

代表性历史版本（仍存在文件但未在 `App.jsx` 注册）：

```
AISettings.jsx              AiInsights.jsx          AiTestConsole.jsx
AllPages-Simple.jsx         ApiDetail.jsx           ApiExplorer-Simple.jsx
ApiExplorer.jsx             ApiExplorerPro.jsx      ApiList.jsx
Automation.jsx              Dashboard-Pro.jsx       Dashboard-Simple.jsx
DatasetManagement.jsx       ExecutionDetail.jsx     ProjectDetail.jsx
Projects-Simple.jsx         Projects.jsx            ProjectsList.jsx
ProjectsPro.jsx             Settings.jsx            TestAgent.jsx
TestCaseDetail.jsx          TestCasesList.jsx       TestCasesPro.jsx
TestData.jsx                TestDataFactory.jsx     TestRuns.jsx
TestRunsList.jsx
```

**不在本次 RC-1 范围内删除**（详见 §12）。

## 11. 已知风险

### 11.1 TAPD 集成（详见 `docs/tapd_integration_risk_checklist.md`）

| # | 风险 | 等级 |
|---|---|---|
| R1 | finding 内容指纹去重缺失（仅依赖 `tapd_bug_id` 字段判已推） | 中 |
| R2 | TAPD 推送失败无重试（`requests` 单次 timeout=15s）| 中 |
| R3 | TAPD 状态同步失败未持久化日志（仅运行时返回错误）| 低 |

### 11.2 代码对比 v2（详见 `docs/code_compare_v2_quality_evaluation.md`）

- 未在多项目、多语言、多团队样本上跑过；当前已验证仅蓝点小程序前端 1 个项目
- 质量指标（precision / recall / FP / FN / 人工复核通过率）尚未抽样，**先留占位**
- finding → 真实 bug 的转化率尚未对照人工评审基线

### 11.3 前端

- 死代码 / 历史版本 page 文件约 25 个，未删除
- 模块归类（测试资产 / 自动化执行 / 缺陷闭环 / 质量分析 / 系统配置）尚未在导航上落地

### 11.4 Demo 数据未初始化

参见 §9，按规则不阻塞。

## 12. 不纳入本次 RC-1 的内容

| 项 | 原因 |
|---|---|
| 删除前端历史 page 文件 | 风险面大，需要逐个验证无引用，单开任务 |
| 修复 TAPD 风险 R1/R2/R3 | 涉及 services/tapd_service.py 修改，本次 RC-1 仅风险登记 |
| 初始化 demo 数据 | 写操作，按用户指令保持只读探测 |
| 修改数据库结构 | 任何 schema 变更需独立兼容迁移方案 |
| 引入新依赖 | 不引入 |
| 真实项目动态 API 验证（白盒+黑盒） | 单开任务，详见 v2 质量评估文档 §11 |
| 微信小程序自动化（miniprogram-automator） | 不在 RC-1 |

## 13. 是否建议进入下一阶段

**建议**：当前允许进入下一阶段，目标范围：

1. 真实项目验证：在蓝点等真实项目上抽样人工复核 v2 finding 质量
2. TAPD 风险收敛：按 `docs/tapd_integration_risk_checklist.md` 提供的最小修复方案逐项收敛
3. 代码对比 v2 质量评估：按 `docs/code_compare_v2_quality_evaluation.md` 抽样后填充 precision / recall / FP / FN

**不进入**：v2.0 正式发布、生产部署、对外宣称完成。

## 14. 附录：acceptance_rc1.py 原始输出

```
======================================================================
RC-1 ACCEPTANCE  backend=http://127.0.0.1:8001  timeout=10.0s
======================================================================
[OK] 01_health - status=healthy, database.connected=true
[OK] 02_modules - 全部 40 个模块 true
[OK] 03_projects - GET /api/v2/projects -> 200
[OK] 04_test_cases - 200 OK total=4729
[OK] 05_test_runs - GET /api/v2/test-runs -> 200
[OK] 06_defects - GET /api/v2/defects -> 200
[OK] 07_dashboard_summary - GET /api/v2/dashboard/summary -> 200
[OK] 08_analytics_overview - GET /api/v2/analytics/overview -> 200
[OK] 09_code_compare_reports - GET /api/v2/code-compare/reports -> 200
[OK] 10_tapd_config - api_password 已脱敏 (value='******')
[WARN] 11_demo_status - Demo 未初始化（按 RC-1 规则不阻塞）
[OK] 12_test_selection - POST recommend -> 200
[OK] 13_quality_gate - GET /api/v2/quality-gates/default-config -> 200
[OK] 14_error_structure - 404 含字段 ['detail']
[OK] 15_sensitive_leak - 未发现疑似明文敏感值（JWT/Bearer/bcrypt/AWS/PEM/PAT/Slack 等）
======================================================================
SUMMARY
======================================================================
TOTAL:     15
PASS:      14
FAIL:      0
WARN:      1
SKIP:      0
EXIT_CODE: 0
```

复现命令：

```powershell
python scripts\acceptance_rc1.py
# 自定义后端地址：
$env:BACKEND_URL="http://127.0.0.1:8001"; python scripts\acceptance_rc1.py
```

---

*报告生成日期：2026-05-07；分支：`feature/tapd-integration-and-code-compare`；HEAD：`e7d6bf7`*
