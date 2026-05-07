# D1 真实项目验证计划

> 本计划仅描述 D1 阶段的执行步骤、抽样规则与指标定义。
> **不修改任何业务代码 / 路由 / 服务 / 数据库 / 前端 / App.jsx**。
> 最终验证报告（带真实指标值）参见 `docs/D1_REAL_PROJECT_VALIDATION_REPORT.md`，**仅在人工评审回填完成后产出**。

---

## 1. 当前分支状态

| 项 | 值 |
|---|---|
| 分支 | `feature/tapd-integration-and-code-compare` |
| HEAD | `f51e28b`（RC-1 工程证据基线最后一次落盘） |
| 工作区 | 仅 1 个 untracked 空文件 `ERP_ORDER_AGENT_PROJECT_ANALYSIS.md`（按指令 **excluded untracked**，不处理） |
| github | 同步到 `f51e28b` ✅ |
| origin (gitlab) | 落后 2 commit，VPN 不可用 — 待补推 |

## 2. 真实项目选择理由

**项目**：蓝点 `recycle-applet-feature-1.2.3`（uni-app + Vue 微信小程序前端）

| 选择理由 | 详情 |
|---|---|
| 已有完整对比报告 | `data/code_compare/reports/rpt_ebc532452984.json` 共 **167** 条 finding |
| 已有 TAPD 实推数据 | TAPD `1055833` ~ `1055839` 共 6 条 bug 推送到 workspace `50366622`，可直接验证字段回写 |
| 真实业务需求 | 蓝点付款单 / 采购订单等真实需求文档已在 `data/code_compare/req_cache/` |
| 避免重复消耗 | **本轮不重新跑 `analyze`**，复用现有 finding，节省 AI 调用且保证数据稳定 |
| 字段完整性 | API `GET /api/v2/code-compare/reports/{id}` 已合并 `tapd_*` 字段（`_TAPD_MERGE_FIELDS`） |

## 3. 输入材料清单

| 类型 | 路径 | 状态 |
|---|---|---|
| 代码对比报告 | `ai-test-platform/data/code_compare/reports/rpt_ebc532452984.json` | ✅ |
| 需求文档 cache | `ai-test-platform/data/code_compare/req_cache/req_*.json` | ✅ |
| 代码快照（report 内引用） | `code_snapshot_id` / `code_snapshot_name` 已记录 | ✅ |
| TAPD 配置 | `data/tapd_config/config.json`（workspace `50366622`，`api_password` 脱敏 OK） | ✅ |
| 已推送 TAPD bug | `1055833` ~ `1055839` 共 6 条（实例化）| ✅ |
| 后端服务 | `http://127.0.0.1:8001`，`app_mode=mock`，40/40 modules `true` | ✅ |
| 验收脚本基线 | `scripts/acceptance_rc1.py` FAIL=0 / EXIT_CODE=0 | ✅ |

**无需新输入**。本轮**不创建新数据**。

## 4. 验证步骤

### 4.1 D1.A — 落盘验证计划（本文档）

✅ 当前正在执行。

### 4.2 D1.B — 新增评审脚本 + 导出评审表

新增 `scripts/validate_code_compare_v2_sample.py`，仅用 Python stdlib，Windows 兼容，输出 `[OK]/[WARN]/[FAIL]/[SKIP]`。

模式：

| 模式 | 命令 | 用途 |
|---|---|---|
| `--export <report_id>` | `python scripts/validate_code_compare_v2_sample.py --export rpt_ebc532452984` | 导出 `findings_review.{md,csv}` + `findings_review_full.csv` |
| `--score <report_id>` | `python scripts/validate_code_compare_v2_sample.py --score rpt_ebc532452984` | 读人工填好 CSV，算 Precision/FP/Pass Rate，写 `score_summary.json` |

**抽样规则**（脚本内置）：
- finding ≤ `--sample-size`（默认 30）：全量
- finding > 30：分层抽样 30 条 + **强制纳入所有 `tapd_bug_id` 非空的 finding**

每条评审记录字段（与你指令完全一致）：
```
finding_id, type, severity, title, requirement_text, code_evidence, evidence_snippet,
engine_judgement, tapd_bug_id, tapd_url, tapd_status,
human_review_result, human_comment, should_convert_to_defect, should_push_tapd
```

最后 4 列留空，**等你回填**。

### 4.3 D1.C — TAPD 回写观察（只读，不创建新 bug）

调用：

```
GET /api/v2/code-compare/reports/rpt_ebc532452984
```

观察项：

| 字段 | 期望 |
|---|---|
| `finding.tapd_bug_id` | 已推 finding 非空 |
| `finding.tapd_url` | 非空、含 `tapd.cn` |
| `finding.tapd_pushed_at` | ISO 时间 |
| `finding.tapd_status` / `tapd_status_name` | 非 null（首次推送时可能为 null）|
| `finding.tapd_last_sync_at` | 时间戳 |

**可选**调用（仅观察）：
```
POST /api/v2/code-compare/reports/rpt_ebc532452984/sync-tapd-status
```

如 `api.tapd.cn` 不可达 → 记录为 `external_dependency_blocked`，**不算 D1 失败**，**不重试过多次**。

产出：`data/validation_samples/rpt_ebc532452984/tapd_observation.json`

### 4.4 D1.D — 质量看板观察

调用：

| 接口 | 观察 |
|---|---|
| `GET /api/v2/dashboard/summary` | 缺陷总数 / 项目 / 用例量 |
| `GET /api/v2/analytics/overview` | 总体质量 |
| `GET /api/v2/dashboard/defect-summary` | 是否能反映 6 条 TAPD 关联缺陷 |

记录能联动的部分 + 当前能力边界。**不联动不算失败**。

产出：`data/validation_samples/rpt_ebc532452984/dashboard_observation.json`

### 4.5 D1.E — 人工回填评审表（**需你参与**）

打开 `data/validation_samples/rpt_ebc532452984/findings_review.csv`（建议 Excel），填以下 4 列：

| 列 | 取值 | 说明 |
|---|---|---|
| `human_review_result` | `valid` / `false_positive` / `uncertain` | 必填 |
| `human_comment` | 1-2 句话 | 必填（哪怕"-"也写）|
| `should_convert_to_defect` | `yes` / `no` | 必填 |
| `should_push_tapd` | `yes` / `no` | 必填 |

### 4.6 D1.F — 跑评分（你回填后）

```
python scripts/validate_code_compare_v2_sample.py --score rpt_ebc532452984
```

输出：`data/validation_samples/rpt_ebc532452984/score_summary.json`，含真实 Precision / FP / Pass Rate。

### 4.7 D1.G — 撰写最终报告

`docs/D1_REAL_PROJECT_VALIDATION_REPORT.md`，按 §四 19 章结构填写，**所有指标值来自 D1.F 的 score_summary.json，不编造**。

## 5. 抽样规则

| finding 数 | 规则 | 本次实际 |
|---|---|---|
| ≤ `--sample-size`（默认 30）| 全量 | 不适用 |
| > 30 | 分层抽样 30 条 + 强制纳入所有 `tapd_bug_id` 非空的 finding | **finding=167，按此规则抽样** |

**分层维度**（脚本实现）：
- 按 `type` 分层：`risk` / `inconsistent` / `missing` / `uncertain` / `implemented` / `extra`
- 类型权重：`risk`=3, `inconsistent`=3, `missing`=2，其他 1
- **强制纳入**：所有 `tapd_bug_id` 非空的 finding（确保 TAPD 闭环全覆盖）
- 随机种子固定 `seed=42`（可复现）

**全量保留**：`findings_review_full.csv`（167 条）始终生成，作为参考与可追溯档案；评审表 `findings_review.csv` 仅含抽样后条目（约 30~36 条，含强制纳入）。

## 6. 指标计算方法

> 严格按你 §六的定义。

```
reviewed_total            = valid + false_positive + uncertain
Precision                 = valid / reviewed_total
False_Positive_Rate       = false_positive / reviewed_total
Manual_Review_Pass_Rate   = (valid + uncertain_acceptable) / reviewed_total

uncertain_acceptable 定义：
  human_review_result = uncertain  AND  should_convert_to_defect = yes

Recall                    = "N/A：当前无完整人工标注的需求-代码映射基准集"
```

**严禁编造**。任何指标必须由 `--score` 模式从 CSV 真实回填中计算。

## 7. 风险点

| # | 风险 | 影响 | 处置 |
|---|---|---|---|
| Q1 | TAPD 反向同步可能不可达（与 GitLab 同样的内网/VPN 依赖） | 步骤 D1.C 部分内容阻塞 | 记 `external_dependency_blocked`，**不算 D1 失败** |
| Q2 | 人工评审依赖你 / 蓝点同事 | D1.E 阻塞 | 计划只到 D1.D；D1.F 在你回填后启动 |
| Q3 | 现有 167 条 finding 中可能有 `code_evidence` 为空或 `evidence_snippet` 缺失 | 评审表字段稀疏 | 脚本兼容 dict / list / null，不报错；评审者凭 `requirement` + `analysis` 仍可判断 |
| Q4 | Recall 无法计算 | 已是公认限制 | 报告中显式声明 |
| Q5 | 质量看板对"finding-derived defect"可能未分桶 | D1.D 看板能力有限 | 记录现状，**不要求**联动 |
| Q6 | 167 条中可能存在内容近似的 finding（命中 R1 风险）| 抽样可能有冗余 | `--score` 输出含 `tapd_pushed_in_sample`；人工评审可标 `false_positive` |
| Q7 | 后端 8001 跑在 mock 模式 | DB 中 defect 数据可能不全 | 当前 `/api/v2/defects` 返回 14 条已实在；`/dashboard/defect-summary` 视后端实现 |

## 8. 需要新增的脚本

✅ **1 个，全程仅 stdlib**：

| 脚本 | 路径 |
|---|---|
| `validate_code_compare_v2_sample.py` | `scripts/` |

不引入新依赖。

## 9. 不修改代码声明

| 类型 | 状态 |
|---|---|
| 业务代码 / `services/` | ❌ 不修改 |
| `routes/` | ❌ 不修改 |
| 数据库 schema | ❌ 不修改 |
| 前端页面 / `App.jsx` | ❌ 不修改 |
| 新依赖 | ❌ 不引入 |
| 创建新 TAPD bug | ❌ 不创建 |
| 重新跑 `analyze` | ❌ 不重跑 |
| TAPD 风险 R1/R2/R3 | ❌ 不修复（仅观察） |

✅ **仅新增**：

| 类型 | 文件 |
|---|---|
| 计划文档（本文）| `docs/D1_REAL_PROJECT_VALIDATION_PLAN.md` |
| 评审脚本 | `scripts/validate_code_compare_v2_sample.py` |
| 评审表 / 全量 CSV / MD 说明 | `data/validation_samples/rpt_ebc532452984/findings_review.{md,csv}` + `findings_review_full.csv` |
| TAPD 观察记录 | `data/validation_samples/rpt_ebc532452984/tapd_observation.json` |
| 看板观察记录 | `data/validation_samples/rpt_ebc532452984/dashboard_observation.json` |

## 10. D1 子阶段节奏

| 子阶段 | 负责 | 产出 | 状态 |
|---|---|---|---|
| **D1.A** 落盘计划 | 我 | `docs/D1_REAL_PROJECT_VALIDATION_PLAN.md` | 进行中 |
| **D1.B** 写评审脚本 + `--export` | 我 | `validate_code_compare_v2_sample.py` + `findings_review.{md,csv,_full.csv}` | 进行中 |
| **D1.C** TAPD 回写观察 | 我 | `tapd_observation.json` | 进行中 |
| **D1.D** 质量看板观察 | 我 | `dashboard_observation.json` | 进行中 |
| **D1.E** 人工回填评审表 | **你** | 填好 4 列的 `findings_review.csv` | 待你回填 |
| **D1.F** 跑 `--score` | 我 | `score_summary.json` | 待 D1.E 完成 |
| **D1.G** 撰写最终报告 | 我 | `docs/D1_REAL_PROJECT_VALIDATION_REPORT.md` | 待 D1.F 完成 |

---

*文档生成日期：2026-05-07；适用分支：`feature/tapd-integration-and-code-compare`；HEAD：`f51e28b`*
