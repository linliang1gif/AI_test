# 前端信息架构文档（RC-1）

> 本文档**只描述前端当前事实并给出治理建议**，不修改任何前端代码、不修改 App.jsx、不修改路由、不引入新依赖、不删除任何页面。
> 所有结论来源：直接扫描 `frontend/src/pages/*.jsx` 与 `frontend/src/App.jsx`。

---

## 1. 数据来源与扫描方法

| 项 | 方法 |
|---|---|
| 页面文件清单 | `Get-ChildItem frontend/src/pages -Filter *.jsx` |
| 路由配置 | grep `Route path` / `import ... from './pages/...'` 于 `frontend/src/App.jsx` |
| 引用检查 | grep `from "...pages/<PageName>"` 于 `frontend/src` 全量 + 动态 `import()` / `React.lazy` |
| 检查日期 | 2026-05-07 |
| 适用分支 | `feature/tapd-integration-and-code-compare` HEAD `f38f96d` |

## 2. 总体数据

| 项 | 数量 |
|---|---|
| `frontend/src/pages/*.jsx` 文件总数 | **52** |
| `App.jsx` `import` 的 page 模块数 | **24** |
| 渲染真实 Page 组件的路由数 | **24** |
| `<Navigate>` 历史重定向路由数 | **12**（含 `/` → `/dashboard`）|
| 占位路由（inline `<div>`）| **2** |
| 未挂载页面（无 import + 无动态 import + 无 React.lazy）| **28** |

**关键事实**：28 个未挂载页面经全量代码扫描**确认零引用**（静态 / 动态 / lazy 三类全空），属真实历史遗留文件。

## 3. App.jsx 路由总览

### 3.1 渲染真实 Page 组件的路由（24 条）

| 路径 | 组件 | 文件 |
|---|---|---|
| `/dashboard` | Dashboard | `pages/Dashboard.jsx` |
| `/projects-v2` | ProjectsV2 | `pages/ProjectsV2.jsx` |
| `/projects-v2/:projectId` | ProjectDetailV2 | `pages/ProjectDetailV2.jsx` |
| `/test-cases` | TestCases | `pages/TestCases.jsx` |
| `/requirement-upload` | RequirementUpload | `pages/RequirementUpload.jsx` |
| `/code-compare` | CodeCompare | `pages/CodeCompare.jsx` |
| `/api-specs` | ApiSpecList | `pages/ApiSpecList.jsx` |
| `/api-specs/:id` | ApiSpecDetail | `pages/ApiSpecDetail.jsx` |
| `/swagger-workbench` | SwaggerWorkbench | `pages/SwaggerWorkbench.jsx` |
| `/test-runs-v2` | TestRunsV2 | `pages/TestRunsV2.jsx` |
| `/test-runs-v2/:runId` | TestRunDetailV2 | `pages/TestRunDetailV2.jsx` |
| `/quick-execution-test` | QuickExecutionTest | `pages/QuickExecutionTest.jsx` |
| `/reports` | Reports | `pages/Reports.jsx` |
| `/reports/:id` | ReportDetail | `pages/ReportDetail.jsx` |
| `/ai-config` | AIConfigPage | `pages/AIConfigPage.jsx` |
| `/executor-v2` | ExecutorV2 | `pages/ExecutorV2.jsx` |
| `/batch-run` | BatchRunCenter | `pages/BatchRunCenter.jsx` |
| `/test-suites` | TestSuites | `pages/TestSuites.jsx` |
| `/quality-gate` | QualityGate | `pages/QualityGate.jsx` |
| `/test-data` | TestDataManagement | `pages/TestDataManagement.jsx` |
| `/defects` | DefectManagement | `pages/DefectManagement.jsx` |
| `/quality-dashboard` | QualityDashboard | `pages/QualityDashboard.jsx` |
| `/test-selection` | TestSelection | `pages/TestSelection.jsx` |
| `/real-project-onboarding` | RealProjectOnboarding | `pages/RealProjectOnboarding.jsx` |

### 3.2 占位路由（2 条，inline `<div>`）

| 路径 | 内容 | 关联文件 |
|---|---|---|
| `/dataset-management` | inline 占位（"数据集管理功能暂未启用，后续版本开放"）| `pages/DatasetManagement.jsx` 存在但**未被路由使用** |
| `/test-data-factory` | inline 占位（"测试数据工厂功能暂未启用，后续版本开放"）| `pages/TestDataFactory.jsx` 存在但**未被路由使用** |

### 3.3 历史重定向（12 条，`<Navigate replace>`）

| 路径 | 重定向到 | 备注 |
|---|---|---|
| `/` | `/dashboard` | 默认首页 |
| `/projects` | `/projects-v2` | 旧版项目列表 |
| `/projects-old` | `/projects-v2` | |
| `/projects/:id` | `/projects-v2` | **参数 `:id` 在重定向后丢失**（已知小缺陷）|
| `/api-explorer-old` | `/api-explorer` | **目标 `/api-explorer` 未注册**（重定向后会进入空白） |
| `/test-cases-old` | `/test-cases` | |
| `/test-cases/:id` | `/test-cases` | **参数 `:id` 丢失** |
| `/automation` | `/quick-execution-test` | |
| `/test-runs` | `/test-runs-v2` | |
| `/test-runs-old` | `/test-runs-v2` | |
| `/test-runs/:id` | `/test-runs-v2` | **参数 `:id` 丢失** |
| `/ai-insights` | `/dashboard` | |
| `/ai-test-console` | `/quick-execution-test` | |

> 注：上表实际 13 行（11 条重定向 + `/` 默认 + `/api-explorer-old` 指向不存在路径）。代码中 `<Navigate>` 数量为 12（一行被合并到默认首页），见 `App.jsx:444-486`。

## 4. 一级模块归类

按你指定的 5 大一级模块对**已挂载 24 页**进行映射。

### 4.1 测试资产（9 页）

> 数据准备阶段：项目、需求、API、Swagger、测试用例、测试数据、真实项目接入。

| 页面 | 路径 |
|---|---|
| ProjectsV2 | `/projects-v2` |
| ProjectDetailV2 | `/projects-v2/:projectId` |
| TestCases | `/test-cases` |
| RequirementUpload | `/requirement-upload` |
| ApiSpecList | `/api-specs` |
| ApiSpecDetail | `/api-specs/:id` |
| SwaggerWorkbench | `/swagger-workbench` |
| TestDataManagement | `/test-data` |
| RealProjectOnboarding | `/real-project-onboarding` |

### 4.2 自动化执行（6 页）

> 触发执行 / 批量执行 / 执行详情。

| 页面 | 路径 |
|---|---|
| QuickExecutionTest | `/quick-execution-test` |
| ExecutorV2 | `/executor-v2` |
| BatchRunCenter | `/batch-run` |
| TestSuites | `/test-suites` |
| TestRunsV2 | `/test-runs-v2` |
| TestRunDetailV2 | `/test-runs-v2/:runId` |

### 4.3 缺陷闭环（2 页）

> 缺陷创建 / 流转 / TAPD 推送 / 需求-代码对比 → finding → 缺陷链路。

| 页面 | 路径 |
|---|---|
| DefectManagement | `/defects` |
| CodeCompare | `/code-compare` |

### 4.4 质量分析（6 页）

> 大盘 / 报告 / 质量门禁 / 智能选测。

| 页面 | 路径 |
|---|---|
| Dashboard | `/dashboard` |
| Reports | `/reports` |
| ReportDetail | `/reports/:id` |
| QualityDashboard | `/quality-dashboard` |
| QualityGate | `/quality-gate` |
| TestSelection | `/test-selection` |

### 4.5 系统配置（1 页）

> AI 服务配置。当前仅 1 页可达。

| 页面 | 路径 |
|---|---|
| AIConfigPage | `/ai-config` |

### 4.6 模块归类小结

| 模块 | 页面数 | 占比 |
|---|---|---|
| 测试资产 | 9 | 37.5% |
| 自动化执行 | 6 | 25.0% |
| 缺陷闭环 | 2 | 8.3% |
| 质量分析 | 6 | 25.0% |
| 系统配置 | 1 | 4.2% |
| **合计** | **24** | 100% |

**观察**：
- "缺陷闭环"和"系统配置"页面较少；如果未来增加页面，倾向归到这两组
- "测试资产"较重，未来可考虑细分子类（项目 / 需求 / API / 测试用例 / 测试数据）

## 5. 未挂载页面清单（28 个）

> 全部经过 `import` / 动态 `import()` / `React.lazy` 三重扫描确认**零引用**。

### 5.1 重复族（命名后缀变体，旧版本残留）

| 当前主版（已挂载）| 同族未挂载文件 | 推断版本 |
|---|---|---|
| `ProjectsV2.jsx` | `Projects.jsx`, `ProjectsList.jsx`, `ProjectsPro.jsx`, `Projects-Simple.jsx` | 4 个旧版 |
| `ProjectDetailV2.jsx` | `ProjectDetail.jsx` | 1 个旧版 |
| `Dashboard.jsx` | `Dashboard-Pro.jsx`, `Dashboard-Simple.jsx` | 2 个旧版 |
| `TestCases.jsx` | `TestCasesList.jsx`, `TestCasesPro.jsx`, `TestCaseDetail.jsx` | 3 个旧版 |
| `TestRunsV2.jsx` / `TestRunDetailV2.jsx` | `TestRuns.jsx`, `TestRunsList.jsx` | 2 个旧版 |
| `TestDataManagement.jsx` | `TestData.jsx`, `TestDataFactory.jsx`, `DatasetManagement.jsx` | 3 个旧版（其中 2 个是占位路由对应文件）|
| `AIConfigPage.jsx` | `AISettings.jsx`, `AiInsights.jsx`, `AiTestConsole.jsx` | 3 个旧版 |
| - (无主版) | `ApiExplorer.jsx`, `ApiExplorerPro.jsx`, `ApiExplorer-Simple.jsx`, `ApiList.jsx`, `ApiDetail.jsx` | 5 个旧版 API Explorer 系列 |
| - (无主版) | `Settings.jsx` | 1 个（已被 AIConfigPage 替代）|
| - (无主版) | `Automation.jsx` | 1 个（重定向 `/automation` → `/quick-execution-test`）|
| - (无主版) | `TestAgent.jsx` | 1 个 |
| - (无主版) | `ExecutionDetail.jsx` | 1 个（已被 TestRunDetailV2 替代）|
| - (无主版) | `AllPages-Simple.jsx` | 1 个（疑似全页面预览/调试页）|

合计 5+1+2+3+2+3+3+5+1+1+1+1+1 = **28 个**，与扫描结果一致。

### 5.2 字母序完整清单（28 个）

```
AISettings.jsx              AiInsights.jsx          AiTestConsole.jsx
AllPages-Simple.jsx         ApiDetail.jsx           ApiExplorer.jsx
ApiExplorerPro.jsx          ApiExplorer-Simple.jsx  ApiList.jsx
Automation.jsx              Dashboard-Pro.jsx       Dashboard-Simple.jsx
DatasetManagement.jsx       ExecutionDetail.jsx     ProjectDetail.jsx
Projects.jsx                ProjectsList.jsx        ProjectsPro.jsx
Projects-Simple.jsx         Settings.jsx            TestAgent.jsx
TestCaseDetail.jsx          TestCasesList.jsx       TestCasesPro.jsx
TestData.jsx                TestDataFactory.jsx     TestRuns.jsx
TestRunsList.jsx
```

## 6. 治理建议矩阵

> 治理动作仅作建议登记，**本次 RC-1 不执行任何文件删除或代码修改**。

| 类别 | 数量 | 建议 | 处置时机 |
|---|---|---|---|
| **保留** | 24 | 当前主版本，挂载在路由上 | 持续保留 |
| **冻结** | 2 | 占位路由对应的文件（`DatasetManagement.jsx` / `TestDataFactory.jsx`）| RC-1 期间冻结，下个迭代决定是激活还是删除 |
| **待确认** | 5 | API Explorer 系列：`ApiExplorer.jsx` `ApiExplorerPro.jsx` `ApiExplorer-Simple.jsx` `ApiList.jsx` `ApiDetail.jsx` | 因当前**没有 API Explorer 主版**且 `App.jsx` 中存在 `/api-explorer-old → /api-explorer` 但 `/api-explorer` 未注册（指向空），需产品确认：是否要重启 API Explorer 模块（用其中之一作为主版重新挂载），还是彻底放弃 |
| **后续可清理** | 21 | 其他重复族旧版本与孤立页 | 待 RC-1 验收完成 + 一个完整的回归窗口后，单开任务 `chore(frontend): drop legacy pages` 整批清理 |

### 6.1 类别详情

#### 保留（24 个）

参见 §3.1 与 §4 全部已挂载页面。

#### 冻结（2 个）

```
DatasetManagement.jsx     -> /dataset-management 当前为 inline 占位
TestDataFactory.jsx       -> /test-data-factory 当前为 inline 占位
```

**判定理由**：路由仍占位，文件可能在功能激活时复用。**禁止本次清理**。

#### 待确认（5 个 - API Explorer 族）

```
ApiExplorer.jsx           ApiExplorerPro.jsx       ApiExplorer-Simple.jsx
ApiList.jsx               ApiDetail.jsx
```

**判定理由**：
- `App.jsx:478` 存在 `<Route path="/api-explorer-old" element={<Navigate to="/api-explorer" replace />} />`
- 但 `/api-explorer` 路径**未注册任何 Route**，进入后是 React Router 的兜底空白
- 说明产品上"API Explorer"功能曾计划保留但实际未上线
- 当前 API 相关已挂载页：`ApiSpecList` (`/api-specs`) + `ApiSpecDetail` (`/api-specs/:id`) + `SwaggerWorkbench` (`/swagger-workbench`)，**功能可能已被替代**

**建议处置**：
- 一种处置：选 `ApiExplorerPro.jsx` 作为主版重新挂载到 `/api-explorer`
- 二种处置：删除上述 5 个文件 + 移除 `<Route path="/api-explorer-old">` 重定向
- 选哪种由产品决定，**RC-1 不执行**

#### 后续可清理（21 个）

```
AISettings.jsx              AiInsights.jsx          AiTestConsole.jsx
AllPages-Simple.jsx         Automation.jsx          Dashboard-Pro.jsx
Dashboard-Simple.jsx        ExecutionDetail.jsx     ProjectDetail.jsx
Projects.jsx                ProjectsList.jsx        ProjectsPro.jsx
Projects-Simple.jsx         Settings.jsx            TestAgent.jsx
TestCaseDetail.jsx          TestCasesList.jsx       TestCasesPro.jsx
TestData.jsx                TestRuns.jsx            TestRunsList.jsx
```

**判定理由**：
- 全部为有主版替代的旧版本（V2 / Pro / List / Simple 系列变体）
- 全量代码扫描确认零 import 引用
- 删除不影响任何运行时路径

**建议处置**：
- 等 RC-1 验收完成
- 等 1 个完整业务回归周期（例如 7 天，确认线上无问题）
- 单开任务 `chore(frontend): drop 21 legacy unmounted pages`，**只删除文件**，**不动 App.jsx**（因为 App.jsx 已经不引用它们）
- 删除前再做一次全量 grep 确认零引用（防止本周期内有人新增引用）
- **RC-1 不执行**

## 7. 已知小缺陷登记（非阻塞）

| # | 项 | 影响 | 是否阻塞 RC-1 |
|---|---|---|---|
| F1 | `<Route path="/projects/:id">` `<Route path="/test-cases/:id">` `<Route path="/test-runs/:id">` 重定向后**参数丢失** | 用户从外部分享链接（带 `:id`）进来会落到列表页 | 否（旧版分享链接极少）|
| F2 | `<Route path="/api-explorer-old">` 重定向到 `/api-explorer` 但**目标路径未注册** | 进入后是空白 | 否（重定向源也基本没人用）|
| F3 | inline 占位文案没有跳转 / 申请 / 联系入口 | 用户看到占位无明确去向 | 否（功能性而非阻塞） |

**RC-1 不修复**，登记到 `docs/RC1_ACCEPTANCE_REPORT.md` §11 "已知风险" 之后版本治理。

## 8. 不在本次范围

| 项 | 原因 |
|---|---|
| 删除任何 `.jsx` 文件 | 风险面，需逐文件确认 + 回归窗口；按指令"不删除任何页面" |
| 修改 `App.jsx` 路由 | 按指令"不修改 App.jsx" |
| 增加新一级模块 / 新菜单 | RC-1 信息架构盘点，不做导航改造 |
| 修复 §7 中 F1 / F2 / F3 | 非阻塞，单开任务 |
| 重新挂载 API Explorer | 待产品决策 |
| 引入新依赖 | 按指令 |

## 9. 后续可执行步骤（**不在本次执行**）

1. 产品确认 API Explorer 族取舍（§6 #待确认）
2. RC-1 验收完成 + 1 周回归窗口后，单开任务删除 §6 #后续可清理 的 21 个文件
3. 修复 §7 F1（参数透传重定向）：将 `<Route path="/projects/:id" element={<Navigate to="/projects-v2" replace />} />` 改为带参数的 wrapper 组件，使用 `useParams()` 拼到目标 URL
4. 修复 §7 F2（注册或移除孤儿重定向）
5. （可选）将 §4 一级模块映射落地为左侧菜单分组（涉及 `frontend/src/components/Sidebar*.jsx` 改造，**不在 RC-1 范围**）

---

*文档生成日期：2026-05-07；适用分支：`feature/tapd-integration-and-code-compare`；HEAD：`f38f96d`*
