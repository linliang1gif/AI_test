# AI 测试平台 — 系统状态报告

**更新时间**: 2026-05-08
**系统版本**: v1.x → 接近 v2.0
**状态**: 🟢 核心功能可用，持续增强中
**当前分支**: `feature/tapd-integration-and-code-compare`

> 上一版（2026-03-23）已归档为 `SYSTEM_STATUS.2026-03.md`。本版基于 git 历史合并最近 1.5 个月（40+ commit）的进展。

---

## 1. 总体概览

平台从 **AI 测试控制台 + 五阶段系统**（v1.0）演进到包含完整 P1/P2/P3 阶段、缺陷生命周期、TAPD 集成、需求-代码对比 v2 的工程化版本。

### 1.1 两种工作模式（保留）

| 模式 | 入口 | 耗时 | 输出 | 适用场景 |
|------|------|------|------|---------|
| AI 控制台 | `/ai-test-console` | 10-20 秒 | 执行结果 + AI 报告 | 快速验证、回归测试 |
| 传统流程 | `/projects` | 数分钟 | 测试用例 + 自动化脚本 | 完整测试设计 |

### 1.2 服务端口

| 服务 | 端口 | 入口 |
|------|------|------|
| 后端 FastAPI | **8001** | http://localhost:8001/health, /docs |
| 前端 Vite | **5173** | http://localhost:5173/ |

> 注：旧版文档写的是 8000，已统一改为 8001（前端 `vite.config.js` 已对应修正）。

---

## 2. 完成的功能模块

### 2.1 早期里程碑（≤ 2026-03，已收录于旧版报告）

- ✅ AI 五阶段系统：Test Agent / Strategy / Orchestrator / Self-Healing / Pipeline
- ✅ AI 测试控制台
- ✅ 传统流程：需求解析 / Swagger / 用例生成 / 自动化脚本
- ✅ 测试数据工厂、断言引擎、知识库、AI 模型切换

### 2.2 P1 系列（2026-04-30 ~ 05-02）

| Code | 模块 | 状态 |
|---|---|---|
| P1-7D | 真实项目模式不安全方法保护 | ✅ |
| P1-7E/7F | 报告持久化 + Reports API + TestRunDetail 报告按钮 | ✅ |
| P1-8 | AI 用例评审 | ✅ |
| P1-9 | 统一用例模型 + L2 变异 + 脚本导出 | ✅ |
| P1-9.1 | 验收报告 | ✅ |

### 2.3 P2 系列（2026-05-02 ~ 05-04）

| Code | 模块 | 状态 |
|---|---|---|
| P2-1 | Docker CI/CD | ✅ |
| P2-2 / P2-2.1 | 后端重构 + 安全加固 | ✅ |
| P2-3 | Web UI 用例模型 | ✅ |
| P2-4 / P2-4.1 | Playwright 引擎 MVP + 回归修复 | ✅ |
| P2-5 | 视觉回归 MVP | ✅ |
| P2-6 ~ P2-6B.2 | Playwright 增强 + API 性能 | ✅ |
| P2-7 ~ P2-7.3 | Web UI 批量执行 + Trace + 信息架构 | ✅ |
| P2-8 | AI Web UI 失败归因 | ✅ |
| P2-9A / 9B / 9D | 用例组件拆分 + Web UI 稳定性 + 覆盖率 | ✅ |
| P2-10 / 10.1 | 测试套管理 MVP + 回归修复 | ✅ |

### 2.4 P3 系列（2026-05-04）

| Code | 模块 | 测试通过率 |
|---|---|---|
| P3-1 | CI/CD 质量门禁 MVP | ✅ |
| P3-3A | 测试数据增强与清理 | **44/44 PASS** |
| P3-4A | 质量看板分析 MVP | **76/76 PASS** |
| P3-4A.1 | 回归稳定性 + readiness check | FAIL=0 |
| P3-4B | 质量趋势 + 模块风险分析 | ✅ |
| P3-5 | 智能选测与风险推荐 MVP | **104/104 PASS, 回归 21/21** |
| P3-5.1 | 工程收口 + 性能治理 | ✅ |

### 2.5 缺陷生命周期（2026-05-04）

- ✅ Defect 状态机：open / confirmed / fixed / verified / closed / rejected / reopened
- ✅ 失败归因 → 缺陷自动建
- ✅ 缺陷管理前端页面 + 缺陷详情 Modal + 事件历史

### 2.6 Phase C2 安全加固（2026-05-05）

- ✅ 安全硬化（SSRF 白名单、敏感信息脱敏）
- ✅ 验证脚本稳定化
- ✅ Phase D 路线图（待执行）

### 2.7 当前分支：TAPD + 代码对比（2026-05-05 ~ 05-07）

- ✅ TAPD 缺陷推送集成（基础）
- ✅ 需求解析增强 + AI 路由 + 代码分析
- ✅ 代码对比 quality baseline 测试
- ✅ **代码对比 v2 引擎重写**（2026-05-06）
  - 扩展代码清单：components / functions / conditions / api_calls / data_fields / template_conditions
  - 倒排索引召回（中文 2/3-gram + 英文 token + 路径分段）
  - 四态判断 prompt：implemented / inconsistent / partial / missing
  - 源码片段证据（±8 行 + 敏感信息脱敏）
  - 低置信度 / partial / inconsistent finding 二次复核
- ✅ **TAPD 推送增强**（2026-05-06）
  - 批量推送 finding → TAPD
  - 单条 / 整报告状态同步
  - 缺陷管理列表"推 TAPD"一键按钮（未推送显示按钮 / 已推送显示 TAPD #ID 链接）
- ✅ 前端 inconsistent UI：粉色徽章、不一致表格（方面/需求/代码）、源码片段代码块
- ✅ **中文标签桥接修复**（2026-05-08，commit `0f31082`）
  - 根因：中文需求（"供应商"、"财务应付单号"）vs 英文代码变量名（`supplier`、`paymentNo`）→ 倒排索引交集 = 0 → 全部需求判 missing、全部代码判"超范围"
  - `code_analyzer.py`：提取 Java `@ApiModelProperty` 中文标签 + Vue 模板中文文本（label/placeholder/title 属性 + 标签内纯文本）
  - `req_code_diff.py`：`_extract_code_items` 为 `java_field` / `template_label` 类型创建带中文名的 code_item；`extra_code` 只报告 `api_route`，不再报内部函数/组件
  - `code_analysis_routes.py`：传 `code_dir` 给 `run_req_code_diff`
  - 匹配率：0% → 78%（蓝点 23 个 Vue 文件，173 个唯一中文标签）
  - 超范围误报：80 → ~0
  - ⏳ **待处理**：复合需求（如"支持筛选"）置信度仍偏低

---

## 3. 测试覆盖

| 类型 | 数量 | 备注 |
|---|---|---|
| 单元测试 | 31+ | 五阶段每模块 ~6 个 |
| 集成测试 | 49+ | 三/四/五阶段流程 |
| P3 验收 | **224 个 PASS** | P3-3A 44 + P3-4A 76 + P3-5 104 |
| 回归 | 21 / 21 PASS（P3-5）| 多次维持 |
| 冒烟 | + `tests/smoke_req_code_diff.py` | 代码对比引擎 |

---

## 4. 模块完成度（粗估）

| 模块 | 完成度 | 备注 |
|---|---|---|
| 基础测试 / 用例管理 | 95% | P1-9 完成统一模型 |
| AI 用例生成 / 评审 | 90% | P1-8 完成评审 |
| Web UI 自动化 (Playwright) | 90% | P2-4~9 系列完成 |
| API / 性能 / 视觉测试 | 85% | P2-5 / P2-6B 完成 |
| 测试数据管理 | 85% | P3-3A 完成 |
| 测试套 / 批量执行 | 90% | P2-7 / P2-10 完成 |
| 缺陷管理 + TAPD 集成 | 80% | 含批量 / 状态同步 / 列表一键推 |
| 需求-代码对比 | 82% | v2 + 中文标签桥接（匹配率 78%），待复合需求优化 |
| 质量门禁 + Dashboard | 80% | P3-1 / P3-4A 完成 |
| 智能选测 | 70% | P3-5 MVP 完成 |
| **整体平均** | **84%** | 已超过 v1.0 的"生产就绪"线 |

---

## 5. 技术栈（更新）

### 后端
- Python 3.11+
- FastAPI（33 个路由模块在 `routes/` 下）
- SQLAlchemy + SQLite（缺陷生命周期 / 报告持久化 / TAPD 状态）
- Pydantic
- Ollama / DeepSeek / OpenAI / Mock 多 AI 提供商

### 前端
- React 18 + Vite + Ant Design
- React Router
- Tailwind CSS
- 代理 `/api/`、`/health`、`/screenshots`、`/visual` → 后端 8001

### 集成
- Playwright（Web UI 引擎）
- TAPD API（缺陷推送 + 状态同步）
- GitLab API（私有仓库克隆）

---

## 6. 项目规模

| 指标 | 当前 | vs 3 月 |
|---|---|---|
| Python 模块 | 100+ 文件 | ↑ 50+ |
| 路由模块（routes/） | 30+ | ↑ 大量 |
| React 页面 | 30+ | ↑ |
| API 端点 | 100+ 实际可用 | ↑ |
| 数据库表 | 缺陷 / 事件 / 报告 / 测试数据 / TAPD 状态 等多张 | ↑ |
| 测试脚本 | 60+ | ↑ |

---

## 7. 短期 TODO

1. ⏳ 推 GitHub（网络好后或推 origin gitlab）
2. ✅ ~~实测 v2 对比引擎~~（蓝点 recycle-applet，2026-05-08 完成中文标签桥接）
3. ⏳ 复合需求匹配优化（如"支持筛选"置信度偏低）
4. ⏳ 7 列统计卡布局微调（栅格 24 / 7 ≈ 3.43，目前会换行）
5. ⏳ Phase D 安全 + 工程化路线图

---

## 8. 启动 / 健康检查

### 启动后端

```bash
cd ai-test-platform
python app/main.py
# 监听 http://0.0.0.0:8001
```

### 启动前端

```bash
cd ai-test-platform/frontend
npm run dev
# 监听 http://0.0.0.0:5173
```

### 健康检查

```bash
curl http://127.0.0.1:8001/health
# 返回 {"status":"healthy", "modules": { ... 33 个模块均为 true }}
```

---

## 9. 文档索引（最新）

### 阶段验收报告（docs/）
- P1-9 系列：unified testcase plan / acceptance / unified import / l2 mutation / script export
- P2 系列：docker_cicd / backend_refactor / web_ui_case_model / playwright / visual_regression / api_performance / web_ui_batch / ai_ui_failure_analysis / web_ui_stability / coverage
- P3 系列：ci_quality_gate / smart_test_selection（含 P3-5）

### 路线图
- `docs/phase_d_*` — 安全与工程化下一阶段（待执行）

### 知识库
- `docs/蓝点后端知识库.md` — 蓝点回收系统接口约定

---

## 10. 已知问题 / 注意事项

- **360 文档卫士**：开发期间会随机加密某些 .py / .jsx 文件，导致 `edit` 工具报 "null bytes"。需要手动从 360 文档卫士里移出保护。
- **GitHub 推送**：国内网络偶发 HTTP/2 framing layer / Connection reset，建议优先推 origin（公司内网 gitlab）。
- **vite 多实例**：开发时容易同时跑 5173 + 5174，要保证只开一个并访问正确端口。

---

**最近 commit**：

```
0f31082  fix(diff): extract Chinese labels from Java/Vue for keyword matching
d402fe8  feat(tapd): TAPD 推送增强 - 批量推送/状态同步/缺陷列表一键推
65ca124  feat(code-compare): 重写需求-代码对比引擎，支持四态判断 + 代码片段证据
70c78bf  test: add code compare quality baseline
295f286  docs: add Phase D security and engineering roadmap
```
