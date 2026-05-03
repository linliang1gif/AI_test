# P2-7 Web UI 批量执行 / Trace / Console / Network 增强报告

**日期**: 2026-05-03  
**状态**: ✅ 通过

---

## 1. 目标

为 Web UI 测试提供完整的批量执行能力，并增强执行证据链：
- 批量执行多条 Web UI 用例，单条失败不中断
- 每条用例生成 Playwright trace.zip
- 捕获 console.error / console.warning
- 捕获 network requestfailed / 4xx/5xx
- 敏感信息（Authorization, Cookie, Token）自动脱敏
- 前端展示证据摘要与下载

---

## 2. 交付物

### 2.1 后端

| 文件 | 说明 |
|------|------|
| `services/sanitize.py` | 敏感数据脱敏工具（URL参数/Headers/文本） |
| `services/playwright_engine.py` | 增强: trace录制、console/network捕获 |
| `routes/web_ui_batch_routes.py` | `POST /api/v2/web-ui/batch-run` 批量执行 |
| `routes/web_ui_batch_routes.py` | `GET /api/v2/web-ui/traces/{filename}` trace下载 |
| `routes/case_execute_routes.py` | 单条执行响应增加 trace/console/network 字段 |
| `backend/router_registry.py` | 注册 Web UI 批量路由 |
| `backend/app.py` | 挂载 `/traces` 静态文件服务 |

### 2.2 前端

| 文件 | 说明 |
|------|------|
| `frontend/src/services/api.js` | 新增 `v2.webUiBatch.run()` API |
| `frontend/src/pages/TestCases.jsx` | "Web UI 批量" 按钮 + 执行结果明细表 |
| `frontend/src/pages/TestRunDetailV2.jsx` | Trace下载 / Console日志 / Network错误 展示块 |
| `frontend/src/pages/ReportDetail.jsx` | Web UI 证据摘要卡片 |

### 2.3 测试

| 文件 | 说明 |
|------|------|
| `scripts/test_p2_7_web_ui_batch_trace.py` | 44 项测试，全部通过 |
| `scripts/run_regression_all.py` | 已注册 P2-7 测试脚本（browser 依赖标记） |

---

## 3. API 设计

### POST /api/v2/web-ui/batch-run

**请求体**:
```json
{
  "case_ids": ["TC_001", "TC_002"],
  "execution_config": {
    "browser": "chromium",
    "headless": true,
    "enable_trace": true,
    "capture_console": true,
    "capture_network": true
  }
}
```

**响应**:
```json
{
  "success": true,
  "run_id": "RUN_20260503...",
  "total_cases": 2,
  "passed_cases": 2,
  "failed_cases": 0,
  "trace_count": 2,
  "console_error_count": 4,
  "network_error_count": 0,
  "case_results": [
    {
      "case_id": "TC_001",
      "status": "passed",
      "duration_ms": 3200,
      "trace_path": "data/artifacts/ui/traces/RUN_xxx_TC_001_xxx.zip",
      "console_error_count": 2,
      "network_error_count": 0
    }
  ]
}
```

### GET /api/v2/web-ui/traces/{filename}

直接下载 trace.zip 文件。

---

## 4. 安全: 敏感数据脱敏

`services/sanitize.py` 处理以下场景:

| 类型 | 脱敏规则 |
|------|---------|
| URL 参数 | `token`, `access_token`, `api_key`, `password`, `secret` → `[REDACTED]` |
| Headers | `Authorization`, `Cookie`, `Set-Cookie`, `X-Api-Key` 等 → `[REDACTED]` |
| 文本内容 | `Bearer xxx`, `token=xxx` 等模式 → `[REDACTED]` |

脱敏在数据写入 DB 之前执行，确保 response_snapshot 和前端展示均不含敏感信息。

---

## 5. 数据流

```
用户选择 Web UI 用例 → 前端 POST /api/v2/web-ui/batch-run
  → 后端创建 TestRun (trigger_type=web_ui_batch)
  → 逐条执行 Playwright (trace + console + network)
  → 写入 RunCase + RunSteps (含脱敏数据)
  → 返回聚合结果
```

**Trace 文件存储**: `data/artifacts/ui/traces/{run_id}_{case_id}_{timestamp}.zip`

---

## 6. 前端展示

### TestCases 页面
- 工具栏新增紫色 **"Web UI 批量"** 按钮
- 自动过滤非 web_ui 用例并提示
- 执行完成后弹出结果对话框，显示:
  - Trace/Console/Network 统计卡片
  - 用例明细表（含状态、耗时、Trace下载链接）

### TestRunDetailV2 页面
- RunCase 详情新增:
  - **Playwright Trace** 下载链接
  - **Console 日志** 列表（error/warning 分色）
  - **Network 错误** 列表（method/url/status/failure_text）

### ReportDetail 页面
- `trigger_type=web_ui_batch` 的报告显示紫色证据摘要卡片
- 展示总用例数、Trace文件数、Console错误数、Network错误数

---

## 7. 测试结果

```
P2-7: PASS=44 FAIL=0 SKIP=0 TOTAL=44
```

| 类别 | 测试项 | 数量 | 状态 |
|------|--------|------|------|
| sanitize 模块 | URL/Headers/Text/Entry 脱敏 | 9 | ✅ |
| PlaywrightResult | 新字段默认值 | 3 | ✅ |
| Playwright 可用性 | Chromium 启动 | 1 | ✅ |
| 用例创建 | Web UI 用例 A/B | 2 | ✅ |
| 非 web_ui 拒绝 | API 用例被拒 | 1 | ✅ |
| 批量执行 | 2条用例执行 + 结果验证 | 12 | ✅ |
| TestRun 写入 | DB 记录验证 | 2 | ✅ |
| RunCase/RunStep | response_snapshot + steps | 5 | ✅ |
| 单条失败不中断 | 混合批量 | 4 | ✅ |
| Trace 下载 | API 下载 + 文件大小 | 2 | ✅ |
| 路由注册 | OpenAPI 检查 | 1 | ✅ |

**前端 build**: ✅ 成功 (28s, 1006KB gzipped 297KB)

---

## 8. 范围外（不在 P2-7）

- ❌ 录制/回放
- ❌ 元素自愈
- ❌ AI UI 失败归因
- ❌ 多浏览器矩阵
- ❌ App/小程序
- ❌ 性能测试增强
- ❌ 数据库 schema 变更

---

## 9. 结论

P2-7 所有功能已实现并通过验证:
- **批量执行**: 支持多条 Web UI 用例并行执行，单条失败不中断
- **Trace 增强**: 每条用例生成 trace.zip，可通过 API 或静态路径下载
- **Console 捕获**: error/warning 级别日志自动记录
- **Network 捕获**: requestfailed 和 4xx/5xx 响应自动记录
- **安全脱敏**: Authorization/Cookie/Token 等敏感信息自动脱敏
- **前端集成**: TestCases/TestRunDetail/ReportDetail 三处 UI 已更新
- **测试覆盖**: 44 项测试全部通过
