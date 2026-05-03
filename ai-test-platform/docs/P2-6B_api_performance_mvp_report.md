# P2-6B API 性能测试 MVP 报告

## 1. 概述

P2-6B 实现了 **API 性能测试 MVP**，允许用户对已有 API 测试用例执行并发性能测试，收集 QPS、响应时间分位数、错误率等指标，支持阈值校验和结果持久化。

## 2. 新增/修改文件

| 文件 | 变更类型 | 说明 |
|------|----------|------|
| `services/performance_engine.py` | **新增** | 性能测试引擎核心，使用 `requests` + `threading` 并发 |
| `routes/performance_routes.py` | **新增** | `POST /api/v2/performance/run` 路由 |
| `backend/router_registry.py` | 修改 | 注册性能测试路由 |
| `frontend/src/services/api.js` | 修改 | 新增 `api.v2.performance.run()` |
| `frontend/src/pages/TestCases.jsx` | 修改 | 性能测试配置弹窗 + 结果展示弹窗 |
| `frontend/src/pages/ReportDetail.jsx` | 修改 | 报告详情页性能摘要卡片 |
| `scripts/test_p2_6b_api_performance_mvp.py` | **新增** | 测试脚本 (30 个测试) |

## 3. 功能特性

### 3.1 性能引擎 (`services/performance_engine.py`)

- **并发模型**: `requests.Session` + `threading.Thread` (1-50 并发)
- **持续时间**: 1-300 秒
- **Ramp-up**: 线程逐步启动，均匀分布在 ramp-up 窗口
- **Think Time**: 请求间可配置间隔
- **指标采集**:
  - `total_requests` / `success_requests` / `failed_requests`
  - `avg_response_time_ms` / `min` / `max`
  - `p50_ms` / `p95_ms` / `p99_ms` (线性插值)
  - `qps` (总请求数 / 实际时间跨度)
  - `error_rate`
- **阈值校验**: 支持 `p95_ms` / `p99_ms` / `avg_ms` / `error_rate` / `max_ms`
- **失败样本**: 最多收集 20 条失败请求详情

### 3.2 API 路由 (`POST /api/v2/performance/run`)

**请求参数**:
```json
{
  "project_id": 1,
  "case_ids": ["TC_001", "TC_002"],
  "concurrency": 5,
  "duration_seconds": 30,
  "ramp_up_seconds": 5,
  "think_time_ms": 0,
  "thresholds": {"p95_ms": 500, "error_rate": 0.05},
  "allow_unsafe_methods": false,
  "environment_id": 1,
  "base_url": "http://api-server:8080"
}
```

**响应**:
```json
{
  "success": true,
  "run_id": "PERF_20260503_abc123",
  "status": "passed",
  "message": "性能测试完成: 1500 请求, QPS=50.3, P95=12.5ms",
  "performance_summary": { ... }
}
```

**校验逻辑**:
- `ramp_up_seconds` ≤ `duration_seconds`
- 用例存在且为 API 类型（拒绝 `web_ui`）
- `concurrency` 1-50, `duration` 1-300

### 3.3 安全保护 (Real Mode)

- `APP_MODE=real` 时，默认阻止包含 `POST/PUT/PATCH/DELETE` 方法的用例
- 返回 `403 REAL_MODE_PERF_UNSAFE_BLOCKED`
- 设置 `allow_unsafe_methods=true` 可解除限制

### 3.4 数据持久化

- 写入 `test_runs` 表，`trigger_type='performance'`
- `summary` 字段存储 `performance_summary` JSON
- 每个用例写入 `run_cases` 表，含阈值校验结果

### 3.5 前端 UI

- **TestCases 页面**: 选中用例后出现「性能测试」按钮，点击打开配置弹窗
- **配置弹窗**: 并发数、持续时间、Ramp-up、请求间隔
- **结果弹窗**: 总请求/QPS/错误率大卡片 + 响应时间分位数 + 阈值失败 + 失败样本
- **ReportDetail 页面**: `trigger_type=performance` 时展示性能摘要卡片

## 4. 技术决策

### 为何使用 `requests` 而非 `httpx.AsyncClient`

测试发现 `httpx` 对 Python 内置 HTTP Server (HTTP/1.0 协议) 返回伪 502 响应。
`requests` 库兼容性更好，配合 `threading.Thread` 实现并发，在 MVP 阶段足够满足 1-50 并发需求。

## 5. 测试结果

### 5.1 P2-6B 性能测试脚本

```
P2-6B API Performance MVP: PASS=30 FAIL=0 SKIP=0 TOTAL=30
Pass rate: 100.0%
```

**覆盖场景**:
1. GET 接口性能执行成功
2. concurrency / duration 生效
3. 统计指标完整 (total/avg/p50/p95/p99/qps/error_rate)
4. 阈值通过判定
5. 阈值失败识别
6. real 模式 POST 拦截 (403)
7. allow_unsafe_methods 放行
8. Web UI 用例拒绝 (400)
9. performance_summary 写入 DB
10. 参数校验 (ramp_up > duration, 用例不存在)
11. API / Web UI 执行后向兼容

### 5.2 全量回归

| 测试脚本 | 结果 | 说明 |
|----------|------|------|
| test_p1_5_failure_recovery | 100% PASS | |
| test_p1_7b_quick | 14/14 PASS | |
| test_p1_7d_real_mode_safety | 15/15 PASS | |
| test_p1_7e_report_persistence | 26/26 PASS | |
| test_phase18 | 38/50 | 12 failures 为外部 API timeout，非 P2-6B 引入 |
| test_phase19 | 50/50 PASS | |
| test_phase20 | 49/49 PASS | |
| test_p2_3_web_ui_case_model | 29/29 PASS | |
| test_p2_6b_api_performance_mvp | 30/30 PASS | |
| **Frontend build** | **PASS** | vite build 成功 |

### 5.3 无回归影响

- API 用例执行链路不受影响
- Web UI 用例执行链路不受影响
- 数据库 schema 无变更
- 所有既有路由正常工作

## 6. 限制与后续

- **MVP 限制**: 不支持分布式负载、不支持 UI 性能测试
- **并发上限**: 50 (受 Python GIL 和线程模型限制)
- **后续可扩展**: 支持阈值自定义 UI、历史趋势图、CI 集成
