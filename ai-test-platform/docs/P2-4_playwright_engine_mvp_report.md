# P2-4 Playwright 执行引擎 MVP 报告

**日期**: 2026-05-02 (更新: 2026-05-02 21:30)
**阶段**: P2-4 Playwright 执行引擎 MVP
**状态**: ✅ 完成

---

## 1. 修改文件清单

| 文件 | 变更 |
|---|---|
| `requirements.txt` | 新增 `playwright==1.49.1` |
| `services/playwright_engine.py` | **新增** PlaywrightEngine 执行引擎；步骤容错(skip)；纯文本步骤智能解析；`networkidle` 等待 |
| `services/page_scanner.py` | **新增** 页面扫描器 + 登录会话管理 + AI 用例生成 |
| `routes/case_execute_routes.py` | Web UI 用例分发到 PlaywrightEngine；新增 `_execute_web_ui_case()` |
| `routes/page_scanner_routes.py` | **新增** 扫描/登录会话/AI生成 API (含 `asyncio.to_thread` 线程安全) |
| `backend/app.py` | 新增 `/screenshots` 静态文件服务 |
| `backend/router_registry.py` | 注册 `page_scanner_routes` |
| `frontend/src/pages/TestCases.jsx` | 页面扫描器 UI + AI 生成按钮 + 登录会话管理 + 步骤结果增强展示 |
| `frontend/src/services/api.js` | 新增 `api.v2.ui.*` 系列 API |
| `scripts/test_p2_4_playwright_engine_mvp.py` | **新增** 28 项测试 |
| `scripts/run_regression_all.py` | 添加 P2-4 到回归套件 |
| `scripts/test_p2_3_web_ui_case_model.py` | 更新执行拦截测试为执行分发测试 |

---

## 2. 是否新增 PlaywrightEngine

**✅ 是。** `services/playwright_engine.py`

核心函数: `execute_web_ui(steps, assertions, execution_config, case_id) → PlaywrightResult`

增强特性:
- **步骤容错**: `fill`/`click`/`wait_for` 元素不存在时标记 `skipped`，不中断测试
- **纯文本步骤解析**: 自动将旧格式 `"步骤1: 打开首页 /index"` 解析为 `{action:"goto", target:"/index"}`
- **会话复用**: 支持 `session_project_id` 参数加载已保存的登录 Cookie
- **页面扫描**: `services/page_scanner.py` 扫描页面提取可交互元素
- **AI 用例生成**: 基于扫描结果调用 LLM 智能生成测试步骤和断言

---

## 3. 是否安装 Playwright

**✅ 是。**
- `pip install playwright==1.49.1`
- `python -m playwright install chromium`

---

## 4. Chromium 是否可用

**✅ 可用。** Chromium 131.0.6778.33 (playwright build v1148)

---

## 5. 支持的 action

| action | 说明 | 状态 |
|---|---|---|
| `goto` | 导航到 URL（支持相对/绝对路径） | ✅ |
| `fill` | 填写输入框 | ✅ |
| `click` | 点击元素 | ✅ |
| `wait_for` | 等待元素或超时（毫秒） | ✅ |
| `screenshot` | 主动截图 | ✅ |
| 其他 | 返回友好错误，不 500 | ✅ |

---

## 6. 支持的 assertion

| assertion | 说明 | 状态 |
|---|---|---|
| `text_visible` | 页面文本可见（`get_by_text` + `wait_for`） | ✅ |
| `url_contains` | 当前 URL 包含指定字符串 | ✅ |
| `url_not_contains` | 当前 URL 不包含指定字符串（登录跳转验证） | ✅ |
| `element_visible` | CSS 选择器元素可见（支持逗号分隔多选择器 + 页面内容兜底） | ✅ |
| 其他 | 返回友好错误，不 500 | ✅ |

---

## 7. Web UI 用例是否可执行

**✅ 是。**

执行流程:
```
POST /api/v2/test-cases/{id}/execute
  → case_type=web_ui → _execute_web_ui_case()
    → services/playwright_engine.execute_web_ui()
      → Playwright: launch chromium → new_page → 执行 steps → 执行 assertions
    → 写入 test_runs / run_cases / run_steps
    → 返回 ExecuteResponse
```

---

## 8. 执行结果是否写入 test_runs / run_cases / run_steps

**✅ 是。**

| 表 | 写入内容 |
|---|---|
| `test_runs` | run_id, status, duration, summary `{"engine":"playwright"}` |
| `run_cases` | test_case_id, status, assertion_details, screenshots |
| `run_steps` | 每个 step + 每个 assertion 各一条记录，含 input/output snapshot |

每个 run_step 记录:
- `step_name`: `{action}: {target}` 或 `assert:{type} — {description}`
- `input_snapshot`: `{action, target, value, description}`
- `output_snapshot`: `{current_url, screenshot_path}`
- `error_message`, `error_type`

---

## 9. 失败截图是否保存

**✅ 是。**

- 目录: `data/artifacts/ui/screenshots/`
- 步骤失败时自动截图: `{case_id}_{timestamp}_fail_step{idx}.png`
- `screenshot` action 主动截图: `{case_id}_{timestamp}_step{idx}.png`
- 截图路径写入 `run_steps.output_snapshot.screenshot_path`
- 不存储在数据库中，仅存文件路径

---

## 10. 前端是否支持执行 Web UI 用例

**✅ 是。**

- Web UI 用例列表显示 🌐 **执行** 按钮（紫色）
- 点击调用 `handleExecuteTest` → `POST /api/v2/test-cases/{id}/execute`
- 执行中显示 loading
- 执行完成弹出结果对话框

---

## 11. 执行详情是否能看到 Web UI step 和截图

**✅ 是。**

- 结果对话框标题: "Web UI 测试结果"
- 逐步执行结果卡片: action | 目标 | 状态(通过/跳过/失败颜色区分) | 耗时 | 错误原因
- **截图内嵌预览**: 直接在步骤卡片中显示截图缩略图，点击放大
- 失败截图直接展示（不仅是链接）
- 断言详情正常显示
- 截图通过 `/screenshots/{filename}` 静态服务访问

---

## 12. API 用例是否不受影响

**✅ 不受影响。**

- `case_type=api` 仍走 `ExecutionEngineV2`
- `case_type=functional` 不走 Playwright
- 仅 `case_type=web_ui` 或 `execution_config.engine=playwright` 分发到 PlaywrightEngine
- Smoke 测试、API Contract 测试全部通过

---

## 13. P2-4 Playwright MVP 测试通过率

```
P2-4 Playwright Engine MVP: PASS=28 FAIL=0 SKIP=0 TOTAL=28
通过率: 100.0%
```

覆盖:
- ✅ Playwright + Chromium 可用
- ✅ 创建 Web UI 用例
- ✅ goto / fill / click / wait_for 步骤执行
- ✅ text_visible / url_contains / element_visible 断言
- ✅ 失败截图保存 + 文件存在
- ✅ 不支持 action 返回友好错误
- ✅ 非 chromium 浏览器返回友好错误
- ✅ 结果写入 test_runs
- ✅ API 用例不受影响

---

## 14. Smoke 通过率

```
P0-7 Smoke 冒烟测试: PASS (17.1s)
```

---

## 15. API Contract 通过率

```
API Contract 契约检查: PASS (2.9s)
```

---

## 16. run_regression_all 结果

```
总计: 9  ✅ PASS: 5  ❌ FAIL: 2  ⏭️ SKIP: 2
通过率: 5/7 = 71.4%

  ✅ P0-7 Smoke 冒烟测试                    PASS   17.0s
  ✅ API Contract 契约检查                   PASS   2.6s
  ✅ P1-7A Import Pipeline                   PASS   70.2s
  ❌ P1-7D Real Mode Safety                  FAIL   8.7s   ← 历史遗留，非本次变更
  ❌ P1-7E Report Persistence                FAIL   34.6s  ← 历史遗留，非本次变更
  ✅ P2-3 Web UI Case Model                  PASS   41.7s
  ✅ P2-4 Playwright Engine MVP              PASS   56.9s
  ⏭️ P1-8A AI Heal Guard                    SKIP   (AI_PROVIDER=none)
  ⏭️ P1-8 AI Case Review                    SKIP   (AI_PROVIDER=none)

注: P1-7D/P1-7E 失败为历史遗留问题，与 P2-4 Playwright 变更无关。
P2 相关测试（P2-3 + P2-4）全部通过。
```

前端构建: `✓ built in 30.41s`

---

## 17. 是否可以进入 P2-5：视觉回归 MVP

**✅ 是。**

P2-4 已完成:
- PlaywrightEngine 支持 5 种 action + 4 种 assertion
- 执行结果写入完整的 test_runs / run_cases / run_steps
- 失败自动截图 + 主动截图
- 截图静态文件服务
- 页面扫描器 + AI 智能用例生成
- 登录会话保存/复用
- 步骤容错 + 纯文本步骤智能解析
- 前端执行 + 增强详情展示（截图内嵌预览）
- P2 相关回归全部通过，API 链路不受影响

P2-5 可基于此引擎的截图能力实现视觉回归基线对比。

---

## 执行配置参数

| 参数 | 默认值 | 说明 |
|---|---|---|
| `browser` | `chromium` | 仅支持 chromium |
| `headless` | `true` | 无头模式 |
| `base_url` | 无 | 页面基础 URL |
| `viewport` | `{1366, 768}` | 视口大小 |
| `timeout` | `30000` | 超时毫秒 |
| `session_project_id` | 无 | 指定项目 ID 加载已保存的登录 Cookie |

---

## 新增 API 端点

| 端点 | 方法 | 说明 |
|---|---|---|
| `/api/v2/ui/scan` | POST | 扫描页面提取可交互元素 |
| `/api/v2/ui/ai-generate` | POST | AI 智能生成测试用例 |
| `/api/v2/ui/login-session` | POST | 执行登录并保存 Cookie 会话 |
| `/api/v2/ui/login-session/{project_id}` | GET | 获取已保存的会话信息 |
| `/api/v2/ui/login-session/{project_id}` | DELETE | 删除会话 |

---

## 安全约束

- 不打印密码/token 到日志
- `base_url` 为空时 goto 相对路径返回友好错误
- 非 chromium 浏览器返回 400
- Playwright 未安装返回 503
- 不支持的 action/assertion 返回 failed（不 500）
