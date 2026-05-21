# P3-3B: 缺陷闭环 MVP 实施报告

## 概述
实现缺陷全生命周期管理（创建→确认→修复→验证→关闭），支持多来源创建、重复检测、证据脱敏、质量门禁联动。

## 回归结果
| 指标 | 结果 |
|------|------|
| 总计 | 21 |
| ✅ PASS | 19 |
| ❌ FAIL | 0 |
| ⏭️ SKIP | 2 (AI无provider) |
| 核心通过率 | **19/19 = 100.0%** |
| P3-3B 专项 | **64/64 PASS** |
| 前端 build | ✅ OK |

## 新增文件
| 文件 | 说明 |
|------|------|
| `services/defect_service.py` | 缺陷核心服务: CRUD、状态流转、duplicate_key、脱敏、门禁摘要 |
| `routes/defect_routes.py` | 10 个 API 端点 |
| `frontend/src/pages/DefectManagement.jsx` | 缺陷管理前端页面 |
| `scripts/test_p3_3b_defect_management.py` | 64 项专项测试 |

## 修改文件
| 文件 | 变更 |
|------|------|
| `database/models.py` | +Defect / +DefectEvent 模型 |
| `backend/startup.py` | +P3-3B defects/defect_events 建表迁移 |
| `backend/router_registry.py` | +缺陷管理路由注册 |
| `frontend/src/App.jsx` | +导航"缺陷管理" + /defects 路由 |
| `frontend/src/pages/TestRunDetailV2.jsx` | +失败用例"创建缺陷"按钮 |
| `frontend/src/pages/ReportDetail.jsx` | +DefectSummaryPanel 缺陷摘要 |
| `services/quality_gate_service.py` | +Rule 12 open_blocker_defects +Rule 13 known_issue |
| `scripts/run_regression_all.py` | +注册 P3-3B 测试 |

## 数据模型
### defects 表
- id, title, description, project_id, module
- severity (blocker/critical/major/minor/trivial)
- priority (P0/P1/P2/P3)
- status (open/confirmed/fixed/verified/closed/rejected/reopened)
- source (manual/run_failure/failure_analysis/quality_gate/visual_diff/performance_regression/data_issue)
- failure_category, case_id, run_id, run_case_id, report_id
- trace_path, screenshot_path, evidence_json
- duplicate_key, created_by, assigned_to
- created_at, updated_at, closed_at

### defect_events 表
- id, defect_id, event_type, from_status, to_status
- comment, evidence_json, created_by, created_at

## 状态流转
```
open → confirmed → fixed → verified → closed → reopened
open → rejected
reopened → confirmed / rejected
```

## API 端点 (10个)
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/v2/defects | 创建缺陷 |
| GET | /api/v2/defects | 查询列表 (支持 status/severity/source/keyword 过滤) |
| GET | /api/v2/defects/{id} | 缺陷详情 (含事件历史) |
| PUT | /api/v2/defects/{id} | 更新基础信息 |
| POST | /api/v2/defects/{id}/transition | 状态流转 |
| POST | /api/v2/defects/from-run-case | 从执行记录创建 |
| POST | /api/v2/defects/from-failure-analysis | 从失败归因创建 |
| GET | /api/v2/defects/duplicates/check | 重复检测 |
| POST | /api/v2/defects/{id}/link-run | 关联执行记录 |
| GET | /api/v2/defects/summary/for-gate | 质量门禁摘要 |

## 质量门禁新规则
| 规则 | 配置项 | 默认 | 说明 |
|------|--------|------|------|
| Rule 12: open_blocker_defects | open_blocker_defects_policy | fail | 存在未关闭 blocker 缺陷时阻断 |
| Rule 13: known_issue | known_issue_policy | warn | 存在已知问题时警告 |

## 前端功能
- **DefectManagement.jsx**: 缺陷列表/创建/详情/状态流转/事件历史/证据查看
- **TestRunDetailV2.jsx**: 失败用例右上角"创建缺陷"按钮，一键从 run_case 创建
- **ReportDetail.jsx**: DefectSummaryPanel 展示关联缺陷/未关闭/已知问题/blocker 统计

## 关键特性
1. **duplicate_key**: 基于 project_id + case_id + failure_category + 归一化错误信息 的 MD5
2. **evidence 脱敏**: 自动匹配 token/cookie/authorization/password/secret/api_key 并脱敏
3. **事件溯源**: 每次创建、更新、状态变更、关联操作均记录 DefectEvent

## 测试覆盖 (64项)
1. 创建人工缺陷 (5项)
2. 查询缺陷列表+过滤 (6项)
3. 缺陷详情+事件 (3项)
4. 更新缺陷 (3项)
5. 状态合法流转 (7项)
6. 状态非法流转 (2项)
7. 从 run_case 创建 (4项)
8. 从 failure_analysis 创建 (2项)
9. duplicate_key+重复检测 (4项)
10. 关联 run (2项)
11. 事件完整记录 (4项)
12. evidence 脱敏 (3项)
13. 质量门禁 blocker 规则 (4项)
14. known_issue 规则 (3项)
15. 缺陷摘要 API (4项)
16. 主链路不受影响 (6项)
17. 404 边界 (2项)

## 结论
P3-3B 缺陷闭环 MVP 已完成，所有功能验证通过。可以进入 **P3-4A: 质量驾驶舱 MVP**。
