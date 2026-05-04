# P3-4B 质量趋势与风险模块 实施报告

## 1. 概述

P3-4B 在 P3-4A 质量驾驶舱 MVP 基础上，新增 **6 类趋势分析**、**模块风险评分** 和 **质量退化检测** 三大能力，使质量驾驶舱从"静态快照"升级为"动态趋势 + 智能预警"。

---

## 2. 变更文件

| 文件 | 类型 | 说明 |
|------|------|------|
| `services/analytics_service.py` | 修改 | +8 个聚合函数 (case/defect/data-issue/flaky/performance/visual trend + module-risk + quality-regression) |
| `routes/analytics_routes.py` | 修改 | +8 个 GET API 端点 |
| `frontend/src/pages/QualityDashboard.jsx` | 修改 | +模块风险Top5 +质量退化提醒 +缺陷趋势 +Flaky趋势 +性能趋势 +视觉趋势 |
| `scripts/test_p3_4b_quality_trends_risk.py` | 新增 | 111 项专项测试 |
| `scripts/run_regression_all.py` | 修改 | 注册 P3-4B 测试脚本 |

---

## 3. 新增 API (8 个)

| 端点 | 方法 | 说明 | 参数 |
|------|------|------|------|
| `/api/v2/analytics/case-trend` | GET | 用例通过率按天趋势 | project_id, days(14) |
| `/api/v2/analytics/defect-trend` | GET | 缺陷新增/关闭/reopened/未关闭趋势 | project_id, days(14) |
| `/api/v2/analytics/data-issue-trend` | GET | 数据问题按天趋势 | project_id, days(14) |
| `/api/v2/analytics/flaky-trend` | GET | Flaky候选/重试/恢复趋势 | project_id, days(14) |
| `/api/v2/analytics/performance-trend` | GET | 性能P95/错误率/阈值失败趋势 | project_id, days(14) |
| `/api/v2/analytics/visual-trend` | GET | 视觉失败/最大Diff趋势 | project_id, days(14) |
| `/api/v2/analytics/module-risk` | GET | 模块风险评分(Top N) | project_id, days(14), module |
| `/api/v2/analytics/quality-regression` | GET | 质量退化检测(6指标) | project_id, days(7) |

所有端点 `days` 参数最大 90，超出返回 400。

---

## 4. 模块风险评分公式

```
risk_score = failure_rate × 0.30
           + recent_failure_weight × 0.20
           + open_defect_weight × 0.20
           + blocker_weight × 0.15
           + data_issue_weight × 0.10
           + flaky_weight × 0.05
```

| 权重因子 | 归一化方式 | 说明 |
|----------|-----------|------|
| failure_rate | 直接使用 (0~1) | 近 N 天失败率 |
| recent_failure_weight | min(failure_rate × 1.5, 1.0) | 放大近期失败影响 |
| open_defect_weight | min(open_defects / 10, 1.0) | 未关闭缺陷数 |
| blocker_weight | min(blocker_count / 3, 1.0) | blocker/critical 缺陷 |
| data_issue_weight | 0 (当前无模块级数据) | 预留扩展 |
| flaky_weight | min(flaky_count / 5, 1.0) | Flaky 候选用例数 |

**风险等级：**
- **high**: risk_score ≥ 0.7
- **medium**: risk_score ≥ 0.4
- **low**: risk_score < 0.4

每个模块附带 `risk_reasons` 列表，说明风险来源。

---

## 5. 质量退化检测规则

对比 **最近 N 天** vs **前 N 天** (默认 N=7)，检测 6 项指标：

| 指标 | 方向 | 退化判定 | 严重度 |
|------|------|---------|--------|
| 用例通过率 | 越高越好 | 下降 >2% | high: Δ<-10%, medium: Δ<-5%, low: else |
| 门禁通过率 | 越高越好 | 下降 >2% | 同上 |
| 新增缺陷 | 越少越好 | 增长 >10% 或绝对增量>0 | high: >50%↑, medium: >20%↑, low: else |
| 性能 P95 | 越低越好 | 增长 >10% | 同上 |
| 视觉失败 | 越少越好 | 增长 >10% | 同上 |
| 数据问题 | 越少越好 | 增长 >10% | 同上 |

前端显示：
- 有退化 → 红色警告框，列出退化指标、delta、严重度
- 无退化 → 绿色提示"所有指标稳定"

---

## 6. 前端新增展示

| 区域 | 说明 |
|------|------|
| 质量退化提醒 | 红色/绿色横幅，位于页面顶部 |
| 模块风险 Top 5 | 表格：模块、风险分、等级、失败率、缺陷、Blocker、Flaky、原因 |
| 缺陷趋势 | 日期表：新增/关闭/Reopen/未关闭 |
| Flaky 趋势 | 日期表：Flaky候选/重试/重试恢复 |
| 性能趋势摘要 | 日期表：P95、错误率、阈值失败 |
| 视觉趋势摘要 | 日期表：视觉失败、最大Diff |

所有区域在无数据时显示空状态提示。

---

## 7. 数据安全

- API 不返回 `password`、`token`、`authorization`、`trace_path`、`screenshot_path` 等敏感键
- `analytics_service.py` import 时不执行任何 DB 查询
- 所有查询通过 SQLAlchemy ORM，无原始 SQL 注入风险
- days 参数限制 1~90，防止大范围扫描

---

## 8. 测试结果

### P3-4B 专项测试
```
P3-4B 测试汇总: 111 PASS / 0 FAIL / 111 TOTAL
```

覆盖：
- 8 个新 API 正常返回 + 字段校验
- days 参数边界 (7/30/100)
- project_id / module 过滤
- 无数据不 500 (8 端点 × project_id=99999)
- 敏感字段检查 (5 键 × 4 端点)
- import 安全性 (AST 扫描)
- 主链路回归 (10 端点)

### 全量回归
```
总计: 23  ✅ PASS: 20  ❌ FAIL: 0  ⚠️ XFAIL: 1  ⏭️ SKIP: 2
核心通过率: 20/20 = 100.0%
```

| 脚本 | 结果 | 耗时 |
|------|------|------|
| P0-7 Smoke | PASS | 18.3s |
| API Contract | PASS | 3.2s |
| P1-7A Import Pipeline | PASS | 89.4s |
| P1-7D Real Mode Safety | PASS | 80.3s |
| P1-7E Report Persistence | PASS | 34.3s |
| Phase 18 | XFAIL | 46.2s |
| P2-3 Web UI Case Model | PASS | 45.8s |
| P2-4 Playwright Engine | PASS | 57.3s |
| P2-5 Visual Regression | PASS | 39.6s |
| P2-6 Playwright Enhanced | PASS | 99.4s |
| P2-6B API Performance | PASS | 72.4s |
| P2-7 Web UI Batch/Trace | PASS | 73.8s |
| P2-8 AI UI Failure Analysis | PASS | 39.8s |
| P2-9B Web UI Stability | PASS | 41.5s |
| P2-10 Test Suite Management | PASS | 66.7s |
| P3-1 CI Quality Gate | PASS | 113.4s |
| P3-2 Test Data Management | PASS | 102.9s |
| P3-3A Test Data Enhancement | PASS | 91.9s |
| P3-3B Defect Management | PASS | 78.7s |
| P3-4A Quality Dashboard | PASS | 73.8s |
| P3-4B Quality Trends Risk | PASS | 97.1s |
| P1-8A AI Heal Guard | SKIP | - |
| P1-8 AI Case Review | SKIP | - |

### 前端构建
```
✓ built in 41.21s — dist/assets/index-fa7d1eaf.js 1,107.69 kB
```

---

## 9. P3-5 准备度

| 准备项 | 状态 |
|--------|------|
| 趋势数据管道 (6 类) | ✅ 已就绪 |
| 模块风险评分模型 | ✅ 已实现，支持公式扩展 |
| 质量退化检测 | ✅ 6 指标自动比较 |
| 前端展示 | ✅ 表格+告警+空状态 |
| 回归稳定性 | ✅ FAIL=0 |
| 数据安全 | ✅ 敏感字段屏蔽 |

**结论：P3-4B 完成，FAIL=0，可以进入 P3-5 智能选测/风险推荐。**
