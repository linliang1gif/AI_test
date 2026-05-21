# P3-5 智能选测与风险推荐 实施报告

## 1. 概述

P3-5 实现智能选测 MVP，让平台可以根据历史失败、模块风险、缺陷、Flaky、性能/视觉退化等数据，推荐本次测试范围。纯规则引擎，不依赖 AI Provider。

---

## 2. 变更文件

| 文件 | 类型 | 说明 |
|------|------|------|
| `services/test_selection_service.py` | **新增** | 推荐引擎：case/suite/module 风险评分 + 推荐等级 + 理由生成 |
| `routes/test_selection_routes.py` | **新增** | POST /api/v2/test-selection/recommend |
| `frontend/src/pages/TestSelection.jsx` | **新增** | 智能选测前端页面 |
| `backend/router_registry.py` | 修改 | 注册智能选测路由 |
| `frontend/src/App.jsx` | 修改 | +导航项 +路由 |
| `scripts/test_p3_5_test_selection_recommendation.py` | **新增** | 104 项专项测试 |
| `scripts/run_regression_all.py` | 修改 | 注册 P3-5 测试脚本 |

---

## 3. 新增 API

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/v2/test-selection/recommend` | POST | 生成智能选测推荐 |

### 请求参数

| 字段 | 类型 | 默认 | 说明 |
|------|------|------|------|
| project_id | int | null | 项目过滤 |
| days | int | 14 | 分析窗口 (max 90) |
| target | string | null | 目标: smoke/regression/release |
| include_case_recommendations | bool | true | 是否包含用例推荐 |
| include_skip_candidates | bool | true | 是否包含可暂缓候选 |
| suite_type | string | null | 测试集类型过滤 |

### 返回结构

```json
{
  "summary": {
    "project_id": null,
    "days": 14,
    "target": "general",
    "total_candidates": 120,
    "must_run_count": 18,
    "should_run_count": 32,
    "optional_count": 40,
    "skip_candidate_count": 30,
    "high_risk_modules": ["付款单", "库存"],
    "suite_count": 5,
    "generated_at": "..."
  },
  "suite_recommendations": [...],
  "case_recommendations": [...],
  "module_recommendations": [...],
  "skip_candidates": [...]
}
```

---

## 4. 推荐输入数据

| 数据源 | 说明 |
|--------|------|
| test_runs | 历史执行状态 (最近 50 次) |
| run_cases | 用例级通过/失败/重试 |
| test_cases | priority / risk_level / module / case_type |
| test_suites + test_suite_cases | 测试集关联 |
| defects | 未关闭缺陷 / blocker / critical |
| summary.gate_status | 门禁失败记录 |
| summary.data_summary | 数据问题 |
| summary.performance_summary | 性能退化 |
| summary.visual_summary | 视觉失败 |

---

## 5. case_risk_score 公式

```
case_risk_score =
  history_failure_rate × 0.25
+ recent_failure_weight × 0.20    # min(failure_rate × 1.5, 1.0)
+ priority_weight × 0.15           # max(priority_map, risk_level_map)
+ module_risk × 0.15               # 模块失败率
+ defect_weight × 0.10             # min(open_defects / 5, 1.0)
+ flaky_weight × 0.05              # 0.8 if both pass & fail in period
+ data_issue_weight × 0.05         # 0.5 if in data_issue run
+ gate_failure_weight × 0.05       # 0.8 if in gate_failed run
```

取值范围 0~1。

| risk_level | 条件 |
|------------|------|
| high | score >= 0.75 |
| medium | score >= 0.45 |
| low | score < 0.45 |

---

## 6. 用例推荐规则

### must_run 条件
- priority == critical
- blocker_defects > 0
- risk_score >= 0.75
- failure_rate > 0.5

### skip_candidate 条件
- pass_streak >= 5
- risk_level == low
- open_defects == 0
- priority not in (critical, high)
- is_flaky == false

### recommendation_level
| 等级 | 条件 |
|------|------|
| must_run | 见上 |
| should_run | score >= 0.45 |
| optional | score >= 0.2 |
| skip_candidate | 见上 |

---

## 7. 测试集推荐规则

suite_risk_score 综合以下因子：
- 用例平均风险分 × 0.30
- 用例最大风险分 × 0.20
- must_run 用例比例 × 0.15
- high risk 用例比例 × 0.10
- 包含 blocker 缺陷 → +0.15
- suite_type 优先级 (release=3, smoke=2, regression=1) × 0.05
- 门禁失败 → +0.10

| recommendation_level | 条件 |
|---------------------|------|
| must_run | score >= 0.6 或 release/smoke 类型 或 has_blocker |
| should_run | score >= 0.35 |
| optional | score >= 0.15 |
| skip_candidate | score < 0.15 |

---

## 8. 前端页面

`TestSelection.jsx` 功能：
- 时间范围选择：7 / 14 / 30 天
- 目标类型过滤：smoke / regression / release
- 套件类型过滤
- "生成推荐" 按钮
- 推荐摘要卡片 (候选/必执行/建议/可选/可暂缓/测试集)
- 高风险模块告警条
- 测试集推荐表 (名称/类型/推荐等级/风险分/用例数/原因)
- 高风险模块表 (模块/风险分/等级/用例数/失败率/缺陷/Flaky/原因)
- 用例推荐表 (用例/类型/模块/优先级/推荐等级/风险分/上次状态/原因)
- 可暂缓候选表 (用例/类型/模块/连续通过/风险分/原因 + 免责声明)

**不自动执行推荐结果，必须用户确认。**

---

## 9. 安全与可解释性

| 要求 | 状态 |
|------|------|
| 推荐必须有 reasons | ✅ 每条推荐附带理由列表 |
| 不返回敏感数据 | ✅ 无 password/token/trace_path/screenshot_path |
| 不依赖 AI Provider | ✅ AI_PROVIDER=none 正常工作 |
| 不自动跳过高风险用例 | ✅ skip_candidate 仅建议 |
| 不自动执行推荐结果 | ✅ 前端无自动执行按钮 |
| counts 一致性 | ✅ summary counts 与实际列表一致 |

---

## 10. 测试结果

### P3-5 专项测试
```
P3-5 测试汇总: 104 PASS / 0 FAIL / 104 TOTAL
```

覆盖：
- recommend API 正常返回 + summary 字段完整
- suite/case/module/skip 推荐返回 + 字段校验
- must_run 逻辑 (critical → must_run)
- skip_candidate 逻辑 (低风险 + 连续通过)
- blocker 影响 (blocker → must_run)
- reasons 可解释性
- days 参数 (7/30/91/100)
- project_id / suite_type 过滤
- include flags (case=false, skip=false)
- 无数据不 500
- 敏感字段检查 (5 键)
- counts 一致性
- 主链路回归 (7 端点)
- 风险评分合理性 (0~1, level threshold)

### 全量回归
```
总计: 24  ✅ PASS: 21  ❌ FAIL: 0  ⚠️ XFAIL: 1  ⏭️ SKIP: 2
核心通过率: 21/21 = 100.0%
```

| 脚本 | 结果 | 耗时 |
|------|------|------|
| P0-7 Smoke | PASS | 18.3s |
| API Contract | PASS | 3.2s |
| P1-7A Import Pipeline | PASS | 89.5s |
| P1-7D Real Mode Safety | PASS | 80.7s |
| P1-7E Report Persistence | PASS | 34.6s |
| Phase 18 | XFAIL | 51.1s |
| P2-3 Web UI Case Model | PASS | 45.9s |
| P2-4 Playwright Engine | PASS | 56.4s |
| P2-5 Visual Regression | PASS | 44.8s |
| P2-6 Playwright Enhanced | PASS | 118.2s |
| P2-6B API Performance | PASS | 75.2s |
| P2-7 Web UI Batch/Trace | PASS | 73.7s |
| P2-8 AI UI Failure Analysis | PASS | 40.4s |
| P2-9B Web UI Stability | PASS | 45.6s |
| P2-10 Test Suite Management | PASS | 66.9s |
| P3-1 CI Quality Gate | PASS | 113.6s |
| P3-2 Test Data Management | PASS | 101.9s |
| P3-3A Test Data Enhancement | PASS | 91.1s |
| P3-3B Defect Management | PASS | 78.9s |
| P3-4A Quality Dashboard | PASS | 75.2s |
| P3-4B Quality Trends Risk | PASS | 99.2s |
| P3-5 Test Selection | PASS | 52.3s |
| P1-8A AI Heal Guard | SKIP | - |
| P1-8 AI Case Review | SKIP | - |

### 前端构建
```
✓ built in 1m — dist/assets/index-be1ff06b.js 1,119.35 kB
```

---

## 11. P3-6 准备度

| 准备项 | 状态 |
|--------|------|
| 智能选测推荐引擎 | ✅ 纯规则，不依赖 LLM |
| case_risk_score 公式 | ✅ 8 因子加权 |
| suite 推荐规则 | ✅ 7 因子 + type 优先 |
| skip_candidate 规则 | ✅ 连续通过 + 低风险 |
| 推荐理由 | ✅ 每条附带 reasons |
| 前端展示 | ✅ 4 区块 + 空状态 |
| 回归稳定性 | ✅ FAIL=0 |
| 数据安全 | ✅ 敏感字段屏蔽 |

**结论：P3-5 完成，FAIL=0，可以进入 P3-6 AI 生成质量闭环。**
