# P2-3 Web UI 用例模型报告

**日期**: 2026-05-02
**阶段**: P2-3 Web UI 用例模型
**状态**: ✅ 完成

---

## 1. 当前 test_cases 模型审计结果

| 字段 | 类型 | 说明 |
|---|---|---|
| id | String(100) PK | TC_001 格式 |
| title | String(500) | 用例标题 |
| module | String(200) | 模块 |
| priority | String(50) | critical/high/medium/low |
| status | String(50) | pending/passed/failed/skipped/deleted |
| steps | JSON | 步骤列表 |
| expected | Text | 预期结果 |
| data_type | String(50) | valid/invalid/boundary/edge/manual |
| expected_behavior | String(50) | success/client_error/server_error |
| execution_config | JSON | 执行配置 |
| assertions | JSON | 断言列表 |
| tags | JSON | 标签数组 |
| source | String(100) | swagger/manual/ai_generated |
| **case_type** | **String(50)** | **P2-3 新增: api/functional/web_ui** |
| created_at | DateTime | 创建时间 |
| updated_at | DateTime | 更新时间 |
| created_by | String(100) | 创建者 |
| ... | ... | Phase 16 治理字段 (risk_level, api_pattern, etc.) |

### 审计结论

- **之前无 `case_type` 字段**，仅通过 `source` 区分来源（swagger/manual/ai_generated），无法区分用例类型
- `steps` 字段为 JSON，之前存储简单字符串数组（功能用例）或空（API 用例依赖 execution_config）
- `assertions` 字段为 JSON，已存在但主要用于 API 断言
- `execution_config` 字段为 JSON，已存在，主要存储 `{method, url, headers, body}`
- `tags` 字段为 JSON 数组，已存在

---

## 2. 是否新增或复用 case_type

**新增 `case_type` 列。** 数据库 ALTER TABLE 迁移，默认值 `'api'` 保证向后兼容。

| case_type | 说明 |
|---|---|
| `api` | 接口测试用例（默认，旧数据兼容） |
| `functional` | 功能测试用例（手动创建默认） |
| `web_ui` | Web UI 测试用例（P2-3 新增） |

迁移方式: `backend/startup.py` → `_run_migrations()` 中自动检测并添加。

---

## 3. Web UI steps 模型

每个 step 为 JSON 对象：

```json
{
  "action": "click",
  "target": "button[type=submit]",
  "value": "",
  "description": "点击登录按钮"
}
```

支持的 action 类型：

| action | 说明 |
|---|---|
| goto | 导航到 URL |
| click | 点击元素 |
| fill | 填写输入框 |
| select | 选择下拉框 |
| hover | 悬停 |
| wait_for | 等待元素 |
| upload | 上传文件 |
| screenshot | 截图（预留） |
| custom | 自定义操作 |

---

## 4. Web UI assertions 模型

```json
{
  "type": "text_visible",
  "target": "",
  "value": "登录成功",
  "description": "页面展示登录成功提示"
}
```

支持的 assertion 类型：

| type | 说明 |
|---|---|
| url_contains | URL 包含指定文本 |
| text_visible | 页面可见文本 |
| element_visible | 元素可见 |
| element_hidden | 元素隐藏 |
| title_contains | 标题包含 |
| screenshot_match | 截图对比（预留） |
| custom | 自定义断言 |

---

## 5. execution_config 结构

```json
{
  "engine": "playwright",
  "browser": "chromium",
  "base_url": "http://localhost:3000",
  "viewport": {"width": 1366, "height": 768},
  "headless": true
}
```

---

## 6. 是否支持创建 Web UI 用例

**✅ 是。**

- 后端: `POST /api/v2/test-cases` 支持 `case_type=web_ui`，保存 steps/assertions/execution_config
- 前端: 手动创建 Tab 新增用例类型选择器（功能用例/API用例/Web UI用例）
- 选择 Web UI 后显示专用表单：步骤编辑器、断言编辑器、浏览器选择、基础 URL

---

## 7. 是否支持编辑 Web UI 用例

**✅ 是。**

- `PUT /api/v2/test-cases/{case_id}` 支持更新 steps/assertions/execution_config/case_type
- `TestCaseUpdateRequest` 已添加 `execution_config` 和 `case_type` 字段

---

## 8. 是否支持 case_type 筛选

**✅ 是。**

- 后端: `GET /api/v2/test-cases?case_type=web_ui` 新增 `case_type` 查询参数
- 前端: 列表 Tab 新增 "Web UI" 筛选标签
- `TestCaseService.get_test_cases()` 已支持 `case_type` 过滤

---

## 9. 是否阻止 Web UI 用例误走 API 执行

**✅ 是。**

| 场景 | 行为 |
|---|---|
| 单个执行 `POST /api/v2/test-cases/{id}/execute` | 返回 400: "Web UI 用例暂不支持执行，Playwright 执行引擎将在 P2-4 支持" |
| 批量执行中包含 web_ui 用例 | 自动过滤掉 web_ui 用例；若全部为 web_ui 则返回 400 |
| 前端列表操作按钮 | Web UI 用例显示"🌐 待接入"灰色按钮，点击提示 P2-4 |

---

## 10. 是否提供 Web UI 用例模板

**✅ 是。** 3 个内置模板，点击即可填充：

| 模板 | steps | assertions |
|---|---|---|
| 登录流程 | goto → fill username → fill password → click submit | url_contains /dashboard, text_visible 首页 |
| 表单提交 | goto → fill 字段 → click 保存 | text_visible 保存成功 |
| 列表查询 | goto → fill 搜索 → click 查询 | element_visible table |

---

## 11. 是否没有安装/执行 Playwright

**✅ 确认没有。**

- 未安装 playwright 包
- 未新增浏览器执行逻辑
- 未新增截图逻辑
- 未新增视觉对比逻辑
- 仅做用例资产管理

---

## 12. 回归测试结果

### P2-3 Web UI Case Model 测试 (29/29)

```
  ✅ Backend healthy
  ✅ 创建 Web UI 用例 status=200
  ✅ 创建 Web UI 用例 success=true
  ✅ 返回 test_case_id
  ✅ 查询 Web UI 用例详情
  ✅ case_type=web_ui
  ✅ steps 保存 4 步
  ✅ step[0].action=goto
  ✅ assertions 保存 2 条
  ✅ assertion[0].type=url_contains
  ✅ execution_config.engine=playwright
  ✅ execution_config.browser=chromium
  ✅ execution_config.base_url 保存
  ✅ 列表查询成功
  ✅ 列表中能找到 Web UI 用例
  ✅ case_type=web_ui 筛选成功
  ✅ 筛选结果包含刚创建的用例
  ✅ 筛选结果全部为 web_ui
  ✅ 编辑 Web UI 用例成功
  ✅ 编辑后标题更新
  ✅ 编辑后 steps 变为 3 步
  ✅ deleted 用例查询返回 404
  ✅ 创建 API 用例成功
  ✅ API 用例 case_type 正确
  ✅ 创建 functional 用例成功
  ✅ functional 用例 case_type 正确
  ✅ Web UI 执行返回 400
  ✅ 返回友好提示含 P2-4
  ✅ 非法 case_type 返回 400

通过率: 100.0%
```

### run_regression_all 结果

```
总计: 8  ✅ PASS: 6  ❌ FAIL: 0  ⏭️ SKIP: 2
通过率: 6/6 = 100.0%

  ✅ P0-7 Smoke 冒烟测试                    PASS   18.4s
  ✅ API Contract 契约检查                   PASS   3.0s
  ✅ P1-7A Import Pipeline                   PASS   69.9s
  ✅ P1-7D Real Mode Safety                  PASS   70.1s
  ✅ P1-7E Report Persistence                PASS   27.2s
  ✅ P2-3 Web UI Case Model                  PASS   39.5s
  ⏭️ P1-8A AI Heal Guard                    SKIP   (AI_PROVIDER=none)
  ⏭️ P1-8 AI Case Review                    SKIP   (AI_PROVIDER=none)
```

### 前端构建

```
✓ 4383 modules transformed
✓ built in 29.50s
```

---

## 13-15. 通过率汇总

| # | 测试项 | 结果 | 耗时 |
|---|---|---|---|
| 12 | P2-3 Web UI Case Model | ✅ 29/29 PASS (100%) | 39.5s |
| 13 | P0-7 Smoke | ✅ PASS | 18.4s |
| 14 | API Contract | ✅ PASS | 3.0s |
| 15 | run_regression_all | ✅ 6/6 PASS, 2 SKIP | 228.1s |

---

## 16. 是否可以进入 P2-4：Playwright 执行引擎 MVP

**✅ 是。**

P2-3 已完成：
- Web UI 用例数据模型（case_type, steps, assertions, execution_config）
- 后端 CRUD 支持
- 前端创建/编辑/筛选/列表展示
- 3 个内置模板
- 执行拦截保护
- 全部回归通过
- 未安装 Playwright，仅做用例资产管理

P2-4 可基于此模型接入 Playwright 执行引擎。

---

## 修改文件清单

| 文件 | 变更 |
|---|---|
| `database/models.py` | 添加 `case_type` 列 |
| `backend/startup.py` | P2-3 迁移: ALTER TABLE 添加 case_type |
| `schemas/swagger_schemas.py` | TestCaseResponse 添加 case_type |
| `services/test_case_service.py` | get_test_cases 支持 case_type 过滤 |
| `routes/swagger_routes.py` | 创建接口支持 case_type; 列表接口支持 case_type 查询 |
| `routes/case_governance_routes.py` | 更新接口支持 case_type, execution_config |
| `routes/case_execute_routes.py` | 单个/批量执行拦截 web_ui 用例 |
| `frontend/src/pages/TestCases.jsx` | 用例类型选择器, Web UI 表单, 模板, 筛选 Tab, 列表标签, 执行拦截 |
| `scripts/test_p2_3_web_ui_case_model.py` | 新增 29 项测试 |
| `scripts/run_regression_all.py` | 添加 P2-3 到回归套件 |
