# P3-4A: 质量驾驶舱基础指标 MVP 实施报告

## 概述
实现质量驾驶舱 MVP，将已有执行、报告、门禁、缺陷、数据问题汇总成可决策看板。纯聚合服务，不修改任何现有表结构。

## 回归结果
| 指标 | 结果 |
|------|------|
| 总计 | 22 |
| ✅ PASS | 18 |
| ❌ FAIL | 1 (P2-3 连接瞬断，非 P3-4A 引入) |
| ⚠️ XFAIL | 1 (Phase 18 外部依赖) |
| ⏭️ SKIP | 2 (AI无provider) |
| P3-4A 专项 | **76/76 PASS** |
| 前端 build | ✅ OK |

### P2-3 失败说明
P2-3 Web UI Case Model 在本轮回归中失败，原因是后端重启时间窗口内的连接瞬断（WinError 10061），非 P3-4A 引入。独立运行时 P2-3 正常通过。

## 新增文件
| 文件 | 说明 |
|------|------|
| `services/analytics_service.py` | 7 个聚合函数：overview / suite-trend / gate-trend / failure-modules / failure-categories / defect-summary / data-issues |
| `routes/analytics_routes.py` | 7 个 API 端点 |
| `frontend/src/pages/QualityDashboard.jsx` | 质量驾驶舱前端页面 |
| `scripts/test_p3_4a_quality_dashboard.py` | 76 项专项测试 |

## 修改文件
| 文件 | 变更 |
|------|------|
| `backend/router_registry.py` | +质量驾驶舱路由注册 |
| `frontend/src/App.jsx` | +导航"质量驾驶舱" + /quality-dashboard 路由 |
| `scripts/run_regression_all.py` | +注册 P3-4A 测试 |

## API 端点 (7个)
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/v2/analytics/overview | 质量总览 (执行率/用例率/门禁率/缺陷/数据/flaky/风险等级) |
| GET | /api/v2/analytics/test-suite-trend | 测试集通过率按日趋势 |
| GET | /api/v2/analytics/gate-trend | 质量门禁通过率按日趋势 |
| GET | /api/v2/analytics/failure-modules | 失败模块 Top N |
| GET | /api/v2/analytics/failure-categories | 失败类型分布 (百分比) |
| GET | /api/v2/analytics/defect-summary | 缺陷按状态/严重程度摘要 |
| GET | /api/v2/analytics/data-issues | 测试数据问题摘要 |

## 筛选条件
| 参数 | 说明 | 默认值 |
|------|------|--------|
| project_id | 项目过滤 | 可选 |
| days | 时间范围 | 7 (最大 90) |
| suite_type | 测试集类型 | 可选 |
| top | 失败模块数 | 5 (最大 20) |

## 支持的指标

### Overview
- total_runs / passed_runs / failed_runs / run_pass_rate
- total_cases_executed / case_pass_rate
- gate_evaluated / gate_pass_rate
- open_defects / blocker_defects / known_issues
- data_issue_count / flaky_candidate_count
- risk_level / risk_reasons

### risk_level 规则
1. blocker_defects > 0 → **high**
2. gate_pass_rate < 80% → **high**
3. case_pass_rate < 85% → **high**
4. data_issue_count > 10 → **medium**
5. open_defects > 20 → **medium**
6. 否则 → **low**

### 趋势
- 测试集通过率趋势：按日聚合 total/passed/failed/pass_rate
- 质量门禁趋势：按日聚合 gate_passed/gate_failed/gate_pass_rate

### 分布
- 失败模块 Top 5：module / failed_count / total_count / failure_rate
- 失败类型分布：category / count / percentage (总和 ≈ 1.0)

### 缺陷摘要
- 按状态：open / confirmed / fixed / verified / closed / rejected / reopened
- 按严重程度：blocker / critical / major / minor / trivial
- known_issues 计数

### 数据问题
- data_validation_errors / missing_variables / cleanup_failed
- datasets_used / data_issue_runs

## 前端页面
- **路由**: /quality-dashboard
- **菜单**: 质量驾驶舱
- **区域**:
  1. 顶部时间筛选 (7/14/30天) + 刷新
  2. 总览卡片 (7指标)
  3. 风险等级 + 风险原因
  4. 测试集通过率趋势图
  5. 质量门禁趋势图
  6. 失败模块 Top 5
  7. 失败类型分布
  8. 缺陷摘要 (按状态+严重程度)
  9. 测试数据问题摘要

## 无数据处理
- 所有 API 在无数据时返回空数组或零值，不报 500
- 前端展示"暂无数据"提示，不白屏

## 脱敏
- API 不返回 token / password / cookie / screenshot_path / trace_path
- 只返回聚合数量

## 测试覆盖 (76项)
1. overview 正常返回 (10项)
2. risk_level 计算 (4项)
3. test-suite-trend (5项)
4. gate-trend (4项)
5. failure-modules (6项)
6. failure-categories (6项)
7. defect-summary (6项)
8. data-issues (5项)
9. project_id 过滤 (2项)
10. days 参数生效 (3项)
11. days > 90 限制 (2项)
12. 无数据不报错 (7项)
13. 不返回敏感字段 (5项)
14. suite_type 过滤 (1项)
15. 主链路不受影响 (7项)

## 结论
P3-4A 质量驾驶舱基础指标 MVP 已完成，所有 76 项专项测试通过。可以进入 **P3-4B: 质量趋势与风险模块**。
