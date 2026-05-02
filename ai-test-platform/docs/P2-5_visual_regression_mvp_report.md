# P2-5 视觉回归 MVP 报告

**日期**: 2026-05-02
**阶段**: P2-5 Visual Regression MVP
**状态**: ✅ 完成

---

## 1. 修改文件清单

| 文件 | 变更 |
|---|---|
| `backend/health.py` | X-Testing-Key 去除硬编码默认值; /health 返回 ai_provider |
| `backend/app.py` | 新增 /visual 静态文件服务 |
| `services/visual_diff.py` | **新增** 像素级视觉对比服务 |
| `services/playwright_engine.py` | 新增 screenshot_match 断言 + visual_results |
| `routes/case_execute_routes.py` | run_id 提前生成; response_snapshot 含 visual_results |
| `routes/report_routes.py` | 报告详情含 visual_summary |
| `frontend/src/pages/TestCases.jsx` | 视觉回归结果展示区块 |
| `scripts/test_p2_5_visual_regression_mvp.py` | **新增** 29 项测试 |
| `scripts/run_regression_all.py` | 加入 P2-5; TESTING_KEY env 传递 |
| `scripts/test_p1_7d_real_mode_safety.py` | 去除 TESTING_KEY 硬编码 |
| `scripts/test_p1_7e_report_persistence.py` | 去除 TESTING_KEY 硬编码 |

## 2. X-Testing-Key 是否非硬编码

**是。** `TESTING_KEY` 从 `os.getenv("TESTING_KEY", "")` 读取，空值时 X-Testing-Key 机制禁用。测试脚本同样从环境变量读取，无硬编码默认值。

## 3. 是否支持 screenshot_match

**是。** `assertions` 中 `type: "screenshot_match"` 由 PlaywrightEngine 处理。仅对 `case_type=web_ui` 生效，API 用例不处理。

## 4. 是否支持 baseline 创建

**是。** baseline 不存在时自动从当前截图创建。目录: `data/artifacts/visual/baselines/`

## 5. 首次运行是否标记 baseline_created

**是。** `visual_result.baseline_created=true`, `status="baseline_created"`。不算真正视觉对比通过。

## 6. 是否支持 current 截图

**是。** 每次执行生成当前截图。目录: `data/artifacts/visual/current/`。文件名含 case_id + run_id + name，不会覆盖。

## 7. 是否支持 diff 图生成

**是。** baseline 存在时使用 PIL/ImageChops 像素级对比生成 diff 图。目录: `data/artifacts/visual/diff/`

## 8. 是否输出 diff_ratio

**是。** `diff_ratio` = 变化像素数 / 总像素数，范围 0.0~1.0。

## 9. threshold 是否生效

**是。** `diff_ratio <= threshold` → passed; `diff_ratio > threshold` → failed。默认 0.05。

## 10. 执行记录是否保存 visual_result

**是。** 写入 `response_snapshot.visual_results[]`，包含:
- type, name, status, baseline_created
- baseline_path, current_path, diff_path
- diff_ratio, threshold, error_message, reason

## 11. 执行详情是否能查看视觉结果

**是。** 前端展示视觉回归对比区块:
- baseline_created 提示首次创建基准图
- passed 显示 diff_ratio 和阈值
- failed 突出显示差异超阈值
- 基准图/当前图/差异图可点击查看

## 12. 报告是否展示视觉摘要

**是。** `GET /api/v2/reports/{id}` 返回 `visual_summary`:
- total, passed, failed, baseline_created, max_diff_ratio
- 无视觉断言时 visual_summary=null

## 13. API 用例是否不受影响

**是。** API 用例 response_snapshot 无 visual_results 字段。测试验证通过。

## 14. Web UI 普通执行是否不受影响

**是。** 不含 screenshot_match 的 Web UI 用例 visual_results 为空数组。测试验证通过。

## 15. Visual Regression MVP 测试通过率

**29/29 = 100%**

## 16. smoke 通过率

**PASS** (17.8s)

## 17. API Contract 通过率

**PASS** (2.9s)

## 18. run_regression_all 结果

```
总计: 10  PASS: 8  FAIL: 0  SKIP: 2
通过率: 8/8 = 100.0%

  ✅ P0-7 Smoke 冒烟测试              PASS   17.8s
  ✅ API Contract 契约检查             PASS   2.9s
  ✅ P1-7A Import Pipeline             PASS   71.1s
  ✅ P1-7D Real Mode Safety            PASS   85.5s
  ✅ P1-7E Report Persistence          PASS   34.8s
  ✅ P2-3 Web UI Case Model            PASS   41.4s
  ✅ P2-4 Playwright Engine MVP        PASS   50.5s
  ✅ P2-5 Visual Regression MVP        PASS   42.0s
  ⏭️ P1-8A AI Heal Guard              SKIP   (AI_PROVIDER=none)
  ⏭️ P1-8 AI Case Review              SKIP   (AI_PROVIDER=none)
```

前端构建: built in 29.49s

## 19. 是否可以进入 P2-6：API 性能测试 MVP

**是。** 所有回归通过，视觉回归 MVP 完整交付，可进入 P2-6。
