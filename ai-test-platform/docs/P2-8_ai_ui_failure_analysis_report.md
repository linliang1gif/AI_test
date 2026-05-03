# P2-8: AI UI 失败归因 — 完成报告

## 1. 目标

基于 Web UI 执行失败证据（error_message、console_logs、network_errors、visual_results、assertion_details），实现规则引擎 + 可选 AI 增强的失败归因分析，输出结构化归因结果并在前端展示。

## 2. 实现清单

| 组件 | 文件 | 说明 |
|------|------|------|
| 归因服务 | `services/failure_analysis.py` | 规则引擎 + AI fallback，证据构建、脱敏、归因、汇总 |
| API 路由 | `routes/web_ui_batch_routes.py` | POST/GET `/api/v2/web-ui/runs/{run_id}/failure-analysis` |
| 前端详情 | `frontend/src/pages/TestRunDetailV2.jsx` | 归因按钮、归因结果 Tab、归因卡片 |
| 前端报告 | `frontend/src/pages/ReportDetail.jsx` | 归因摘要区域（从 run.summary 读取） |
| 测试脚本 | `scripts/test_p2_8_ai_ui_failure_analysis.py` | 53 项测试用例 |
| 回归注册 | `scripts/run_regression_all.py` | P2-8 已注册 |

## 3. 失败归因分类

| 分类 | 触发条件 | 建议动作 |
|------|----------|----------|
| `selector_not_found` | error 含 selector/locator 关键词 | 更新 Selector |
| `page_timeout` | error 含 timeout/timed out 关键词 | 重试 |
| `element_not_visible` | error 含 not visible/hidden/obscured | 更新 Selector |
| `network_error` | network_errors 含 status=0 或 net::ERR | 重试 |
| `app_bug_suspected` | network_errors 含 5xx 状态码 | 提 Bug |
| `auth_or_permission` | network_errors 含 401/403 | 检查权限配置 |
| `visual_diff` | visual_results 有 failed 条目 | 更新 Baseline |
| `assertion_failed` | assertion_details 有 passed=false | 检查断言或应用逻辑 |
| `console_error` | console_logs 含 error 类型条目 | 检查前端代码 |
| `unknown` | 以上均不匹配 | 人工排查 |

## 4. 安全保障

- 所有 error_message 经 `sanitize_text()` 脱敏（Bearer/token/authorization → `[REDACTED]`）
- network_errors URL 经 `sanitize_url()` 脱敏（query 参数中的 token/key/secret）
- console_logs 经 `sanitize_text()` 脱敏
- 不传 trace.zip、完整 HTML、截图到 AI
- AI 请求不含 Cookie/Authorization header
- 测试脚本验证输出无敏感信息泄露

## 5. API 接口

### POST `/api/v2/web-ui/runs/{run_id}/failure-analysis`
- 触发归因分析，返回 `{ analyses: [...], summary: {...} }`
- 结果持久化到 `RunCase.response_snapshot.failure_analysis` 和 `TestRun.summary.failure_analysis_summary`

### GET `/api/v2/web-ui/runs/{run_id}/failure-analysis`
- 查询已有归因结果
- 无结果时返回空 analyses

## 6. 前端集成

### TestRunDetailV2
- **归因按钮**: 页面顶部 "失败归因分析" 按钮（amber 色），点击触发 POST 分析
- **归因结果 Tab**: 分析完成后自动切换到 "归因结果" Tab
- **归因汇总卡片**: 6 项统计（分析总数、高置信度、建议提 Bug、建议重试、更新 Selector、更新 Baseline）+ 分类分布
- **归因详情卡片**: 每条分析结果显示分类标签、置信度、分析模式（规则/AI）、根因摘要、证据列表、建议动作、操作标签
- **页面加载自动查询**: GET 已有归因结果

### ReportDetail
- **归因摘要区域**: 从 `run.summary.failure_analysis_summary` 读取，显示汇总统计 + 分类分布 + 归因条目列表

## 7. 测试结果

### P2-8 单测: 53 PASS / 0 FAIL / 0 SKIP

覆盖内容:
- 9 种失败分类规则匹配
- 脱敏验证（Bearer/Token/Cookie 全部 REDACTED）
- 汇总构建验证
- POST/GET API 端到端（含真实 batch-run 失败用例）
- 归因结果字段完整性（14 项字段）
- 幂等重复 POST
- 不存在 run 404
- 无失败 run 空结果
- 路由注册验证
- 主链路完整性

### 全量回归: 13/13 PASS, 0 FAIL, 2 SKIP

```
✅ P0-7 Smoke 冒烟测试                          PASS   17.5s
✅ API Contract 契约检查                         PASS   2.7s
✅ P1-7A Import Pipeline                         PASS   79.8s
✅ P1-7D Real Mode Safety                        PASS   84.7s
✅ P1-7E Report Persistence                      PASS   34.5s
✅ Phase 18 执行稳定性                           PASS   151.0s
✅ P2-3 Web UI Case Model                        PASS   42.2s
✅ P2-4 Playwright Engine MVP                    PASS   53.3s
✅ P2-5 Visual Regression MVP                    PASS   42.1s
✅ P2-6 Playwright Enhanced                      PASS   102.7s
✅ P2-6B API Performance MVP                     PASS   72.4s
✅ P2-7 Web UI Batch/Trace                       PASS   74.9s
✅ P2-8 AI UI Failure Analysis                   PASS   36.6s
⏭️ P1-8A AI Heal Guard                          SKIP (AI_PROVIDER=none)
⏭️ P1-8 AI Case Review                          SKIP (AI_PROVIDER=none)
```

### 前端构建: 通过 (42.80s)

## 8. 禁止项确认

| 禁止项 | 状态 |
|--------|------|
| 不自动修改测试用例/选择器 | ✅ 遵守 |
| 不自动更新 baseline | ✅ 遵守 |
| 不自动元素自愈 | ✅ 遵守 |
| 不向 AI 发送 trace.zip 内容 | ✅ 遵守 |
| 不在分析结果中暴露敏感 header | ✅ 遵守（脱敏验证通过） |
| 不向 AI 上传完整 HTML/截图 | ✅ 遵守 |
| 不修改数据库结构 | ✅ 遵守（使用现有 JSON 字段） |
| 不破坏现有 API/UI/Visual/Performance 链路 | ✅ 遵守（全量回归 100%） |

## 9. 结论

P2-8 AI UI 失败归因功能完整实现，规则引擎覆盖 10 种失败分类，证据脱敏严格，前端展示完整，全量回归零失败。
