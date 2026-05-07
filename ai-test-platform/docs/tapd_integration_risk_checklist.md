# TAPD 集成风险清单（RC-1）

> 本文档**仅登记风险与最小修复方案**，不修改代码。
> 所有结论基于 `services/tapd_service.py`、`routes/code_compare_routes.py`、`routes/defect_routes.py` 当前代码事实。

---

## 1. TAPD 集成当前能力

### 1.1 配置与凭据

| 能力 | 入口 | 实现位置 |
|---|---|---|
| 配置加载 / 保存 | `GET/POST /api/v2/code-compare/tapd/config` | `services/tapd_service.py::load_tapd_config` / `save_tapd_config` |
| 连接测试 | `POST /api/v2/code-compare/tapd/test` | `services/tapd_service.py::test_tapd_connection` |
| 凭据脱敏（读路径） | `GET /api/v2/code-compare/tapd/config` 返回 `api_password='******'` | `routes/code_compare_routes.py::get_tapd_config` |

### 1.2 推送（缺陷 / Finding）

| 能力 | 入口 | 实现位置 |
|---|---|---|
| 单条 Finding 推 TAPD | `POST /api/v2/code-compare/findings/{finding_id}/push-to-tapd` | `routes/code_compare_routes.py::push_finding_to_tapd` |
| 批量 Finding 推 TAPD | `POST /api/v2/code-compare/findings/batch-push-to-tapd` | `routes/code_compare_routes.py::batch_push_findings_to_tapd` |
| Defect → TAPD 推送 | `POST /api/v2/defects/{defect_id}/push-to-tapd` | `routes/defect_routes.py::api_push_defect_to_tapd` |
| 标题/描述/严重程度生成 | `services/tapd_service.py::finding_to_tapd_bug` | 单元测试 8/8 (`scripts/test_finding_to_tapd_bug.py`) |
| 实际推送 | `services/tapd_service.py::push_bug_to_tapd` | `requests.post("https://api.tapd.cn/bugs", timeout=15)` |

### 1.3 状态同步

| 能力 | 入口 | 实现位置 |
|---|---|---|
| 拉取 TAPD Bug 状态 | `services/tapd_service.py::fetch_tapd_bug_status` | `requests.get("https://api.tapd.cn/bugs", timeout=15)` |
| 单条 Finding 同步 | `POST /api/v2/code-compare/findings/{finding_id}/sync-tapd-status` | `routes/code_compare_routes.py::sync_finding_tapd_status` |
| 报告下批量同步 | `POST /api/v2/code-compare/reports/{report_id}/sync-tapd-status` | `routes/code_compare_routes.py::sync_report_tapd_status` |
| Defect 单条同步 | `POST /api/v2/defects/{defect_id}/sync-tapd-status` | `routes/defect_routes.py::api_sync_defect_tapd_status` |
| Defect 批量同步 | `POST /api/v2/defects/sync-tapd-status-batch` | `routes/defect_routes.py::api_sync_defects_tapd_status_batch` |

## 2. 已通过的检查项

| 检查项 | 现状 | 证据 |
|---|---|---|
| C1：TAPD 凭据读路径脱敏 | ✅ | `api_password='******'`，acceptance_rc1.py 第 10 项 OK |
| C2：单条 Finding 重复推送保护 | ✅ | `target_finding.get("tapd_bug_id")` 命中即返回 `already_pushed=True` |
| C3：批量推送已推送跳过 | ✅ | `BatchPushToTapdRequest.skip_already_pushed=True` 默认；命中后状态为 `already_pushed` |
| C4：批量推送部分成功处理 | ✅ | 返回 `{total, pushed, skipped, failed, not_found, results[]}` |
| C5：报告级 TAPD 状态展示 | ✅ | `_TAPD_MERGE_FIELDS = (tapd_bug_id, tapd_url, tapd_pushed_at, tapd_status, tapd_status_name, tapd_last_sync_at, tapd_modified)` 在报告 GET 接口合并 |
| C6：错误响应结构化 | ✅ | acceptance_rc1.py 第 14 项 OK |
| C7：服务层日志不暴露密码 | ✅ | `services/tapd_service.py::fetch_tapd_bug_status` 注释明确"不要把 api_password / token 暴露到日志或返回" |

## 3. 当前非阻塞风险

### R1：finding 内容指纹去重缺失

| 项 | 内容 |
|---|---|
| 现状 | 当前只通过 `finding.tapd_bug_id` 字段判定"是否已推送"。即"同一份 finding 重新推 TAPD 会被拦截"。**但是不同 finding（不同 finding_id）即使内容近乎一致，也会重复创建 TAPD bug**。 |
| 触发场景 | 同一份需求多次跑 v2 对比生成不同 `finding_id` 的同质 finding；批量 push 时 TAPD 上出现大量内容相似的 bug |
| 影响等级 | **中**：会污染 TAPD bug 库；不影响推送链路稳定性 |
| 是否阻塞 RC-1 | 否（属于质量优化项） |
| 已知规避 | 在 `acceptance_rc1.py` 验收无关；运行时通过人工标记 `false_positive` 处理 |

### R2：TAPD 推送失败无重试

| 项 | 内容 |
|---|---|
| 现状 | `services/tapd_service.py::push_bug_to_tapd` 与 `fetch_tapd_bug_status` 均使用 `requests.{post|get}(..., timeout=15)` 单次调用，无重试封装 |
| 触发场景 | TAPD 网络抖动 / 5xx / 408 / 短暂的 connection reset 时，**单次调用失败即视为最终失败**，需要用户重新触发 |
| 影响等级 | **中**：批量推送在弱网环境下成功率下降 |
| 是否阻塞 RC-1 | 否（业务可手动重试） |
| 已知规避 | 用户层手动重试 / 批量推送 `failed` 列表逐条复推 |

### R3：TAPD 状态同步失败未持久化日志

| 项 | 内容 |
|---|---|
| 现状 | `sync_finding_tapd_status` / `api_sync_defect_tapd_status` 失败时返回 HTTP 错误，**未写入持久化日志表 / 文件**，运行后无法复盘 |
| 触发场景 | TAPD bug 被删除 / 权限变更 / 网络异常时，同步接口返回错误，平台没有失败痕迹 |
| 影响等级 | **低**：影响事后排障，不影响业务流转 |
| 是否阻塞 RC-1 | 否（运维需求，非功能缺陷） |
| 已知规避 | 后端控制台 stdout 日志可看到；不持久化 |

## 4. 风险等级

| 风险编号 | 等级 | 阻塞 RC-1 | 阻塞下一阶段（真实项目验证） |
|---|---|---|---|
| R1 | 中 | 否 | 否（先在 v2 质量评估中观察 finding 重复率，再决定是否治理） |
| R2 | 中 | 否 | 否（弱网下成功率监测可量化）|
| R3 | 低 | 否 | 否（事后排障可用 stdout）|

## 5. 最小修复方案

> 以下方案**仅作设计登记**，本次 RC-1 不实施。每个方案标注代码改动面、是否需要 schema 变更、是否引入新依赖。

### 5.1 R1 修复方案：finding 内容指纹去重

| 项 | 内容 |
|---|---|
| 思路 | 基于 finding 的内容字段（`requirement_id` + `type` + `inconsistencies` 维度键）生成稳定 hash 作为指纹。推送前查同项目下最近 N 天是否有同指纹的已推送 finding；命中则视为 `already_pushed_by_fingerprint`。 |
| 改动面 | `services/tapd_service.py` 增加 `_finding_fingerprint(finding) -> str`；`routes/code_compare_routes.py::push_finding_to_tapd` 增加 fingerprint 索引查询 |
| Schema 变更 | 否（指纹可放在 finding 字段 `fingerprint` 内存里；持久化时存到现有 `defects.dedup_key` 字段或 `findings.fingerprint` JSON 内字段）|
| 新依赖 | 否（用 `hashlib.sha1`） |
| 单元测试 | 在 `scripts/test_finding_to_tapd_bug.py` 中加 1~2 个 case 验证 fingerprint 稳定性 |
| 估时 | 0.5 天 |

### 5.2 R2 修复方案：TAPD 推送失败重试

| 项 | 内容 |
|---|---|
| 思路 | 在 `push_bug_to_tapd` / `fetch_tapd_bug_status` 外包一层指数退避重试（最多 3 次：1s / 2s / 4s）；只对网络异常和 5xx / 429 重试，4xx 直接失败。 |
| 改动面 | `services/tapd_service.py` 顶部新增 `_retry_request(callable, attempts=3, backoff=2)` 工具；`push_bug_to_tapd` / `fetch_tapd_bug_status` 内部用包一下 |
| Schema 变更 | 否 |
| 新依赖 | 否（用 `time.sleep` + 标准库） |
| 单元测试 | 加 mock 断言重试次数和退避时序 |
| 估时 | 0.5 天 |

### 5.3 R3 修复方案：状态同步失败持久化日志

| 项 | 内容 |
|---|---|
| 思路 | 沿用现有 `defect_events` 表（`database/models.py` 中已存在），在 `sync_finding_tapd_status` / `api_sync_defect_tapd_status` 失败分支写入 `defect_events.event_type='tapd_sync_failed'`，附 `payload={error, code, request_url, finding_id}`。**不需要新表**。 |
| 改动面 | `routes/code_compare_routes.py::sync_finding_tapd_status` 失败分支；`routes/defect_routes.py::api_sync_defect_tapd_status` 失败分支 |
| Schema 变更 | 否（`defect_events` 表已支持任意 event_type） |
| 新依赖 | 否 |
| 单元测试 | 不必需；建议加一条集成测试 |
| 估时 | 0.5 天 |

## 6. 后续验收标准

### 6.1 R1 验收

- 单元测试：相同 `requirement_id` 与 `inconsistencies` 维度的两个 finding 生成同一 fingerprint，不同 inconsistencies 生成不同 fingerprint
- 集成测试：在测试 TAPD 项目上跑两次推同份 finding（不同 finding_id），第二次返回 `already_pushed_by_fingerprint=True`
- 不破坏现有 `tapd_bug_id` 已推保护

### 6.2 R2 验收

- 单元测试：模拟 5xx 三次后回退、4xx 立即失败、网络超时按指数退避
- 集成测试：弱网模拟下 100 次推送的成功率从基线 X% 提升到 ≥ 95%（基线在第二阶段实测）
- 重试不导致 TAPD 创建重复 bug（依赖 R1 的 fingerprint 双重保护）

### 6.3 R3 验收

- `defect_events` 表中能查到 `event_type='tapd_sync_failed'` 的记录
- 错误 payload 不泄露 `api_password` 等敏感字段（用 `_sanitize_content`）
- 失败日志保留窗口与现有 `defect_events` 一致

---

*文档生成日期：2026-05-07；适用分支：`feature/tapd-integration-and-code-compare`；HEAD：`e7d6bf7`*
