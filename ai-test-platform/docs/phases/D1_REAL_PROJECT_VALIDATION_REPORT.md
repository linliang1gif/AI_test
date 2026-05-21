# D1 真实项目验证报告（客观证据版）

> **版本**：D1 阶段收尾报告
> **日期**：2026-05-07
> **分支**：`feature/tapd-integration-and-code-compare`
> **定位**：本报告只记录 D1.A~D1.D 已完成的机器可验证事实，不写人工准确率结论，不编造任何指标。

---

## 1. 验证结论

**D1.A~D1.D 已完成，平台已在真实项目数据上验证了 Code Compare v2 finding 产出、TAPD 字段回写和质量看板能力边界。由于本期未执行人工评审，D1 只能证明真实项目链路可运行，不能证明 finding 准确率和误报率。准确率评估延后到 D2 或后续人工复核阶段。**

---

## 2. 验证范围

本报告覆盖的内容：

- Code Compare v2 引擎在真实项目数据上的 finding 产出规模与类型分布
- Finding 向 TAPD 回写字段的完整性观察
- 质量看板相关 API 端点的可用性与能力边界观察
- D1 计划中 A / B / C / D 四个阶段的执行产物清单

本报告**不**覆盖的内容：

- Finding 内容的人工正确性评审
- Precision / Recall / False Positive Rate / False Negative Rate / Manual Review Pass Rate
- v2 引擎在其他项目上的表现
- 与 D2 阶段相关的回归测试、生产环境验证、多项目横向对比
- 业务代码修改、数据库结构变更、前端页面调整（本期严格不动）

---

## 3. 真实项目说明

| 项 | 值 |
|---|---|
| 项目名 | 蓝点 recycle-applet-feature-1.2.3（蓝点回收企业小程序） |
| 项目类型 | uni-app / Vue 小程序 |
| 选择理由 | 该项目已有 Axure 原型注释（需求侧）与 `subpackages/` 业务代码（实现侧），可作为"需求 vs 代码"对比的真实输入；历史上已在平台内完成一次 Code Compare v2 分析，产出报告 `rpt_ebc532452984` |
| 本期是否重新跑 analyze | **否**（严格复用历史报告，避免引入新 finding 噪音） |

---

## 4. 输入材料

| 材料 | 路径 / 编号 | 说明 |
|---|---|---|
| 历史 Code Compare v2 报告 | `data/code_compare/reports/rpt_ebc532452984.json` | 复用，未重跑 |
| Finding 评审抽样表 | `data/validation_samples/rpt_ebc532452984/findings_review.csv` | 30 条抽样，本期未填 |
| Finding 全量参考表 | `data/validation_samples/rpt_ebc532452984/findings_review_full.csv` | 167 条，仅参考 |
| Finding 评审说明 | `data/validation_samples/rpt_ebc532452984/findings_review.md` | 评审字段规范 |
| TAPD 回写观察结果 | `data/validation_samples/rpt_ebc532452984/tapd_observation.json` | 7 条 finding 的 TAPD 字段完整性快照 |
| 质量看板能力观察结果 | `data/validation_samples/rpt_ebc532452984/dashboard_observation.json` | 5 个看板相关端点的可用性快照 |

> 上述 `data/validation_samples/` 下的产物被 `.gitignore` 排除，不入仓，仅作为本地工件供复核使用。

---

## 5. D1.A~D1.D 完成情况

| 子阶段 | 状态 | 工件 | 备注 |
|---|---|---|---|
| **D1.A** 验证计划落盘 | ✅ 完成 | `docs/D1_REAL_PROJECT_VALIDATION_PLAN.md`（已 commit）| 含项目选择、抽样规则、指标定义、风险点 |
| **D1.B** 抽样 / 评分脚本 + 评审表导出 | ✅ 完成 | `scripts/validate_code_compare_v2_sample.py`（已 commit）+ `findings_review.csv` / `findings_review_full.csv`（本地产物）| 支持 `--export` / `--score` / `--observe-tapd` / `--observe-dashboard` |
| **D1.C** TAPD 回写字段观察 | ✅ 完成 | `tapd_observation.json` | 只读 GET，未触发任何 TAPD 写入 |
| **D1.D** 质量看板能力观察 | ✅ 完成 | `dashboard_observation.json` | 只读 GET，未触发任何数据库写入 |
| **D1.E** 人工评审 30 条 finding | ⏸ 本期不执行 | `findings_review.csv` 保留待补 | 用户明确选择不做 |
| **D1.F** `--score` 计算准确率指标 | ⏸ 本期不执行 | —— | 依赖 D1.E |
| **D1.G** 本客观证据版报告 | ✅ 完成 | `docs/D1_REAL_PROJECT_VALIDATION_REPORT.md`（本文件） | —— |

---

## 6. Code Compare v2 真实项目 finding 产出情况

| 指标 | 值 |
|---|---|
| 原始 finding 总数 | **167** |
| 复用报告 ID | `rpt_ebc532452984` |
| 是否重新跑 analyze | **否** |
| 是否修改 v2 引擎业务代码 | **否** |

### Finding type 分布（抽样评审 CSV 的 30 条分布）

| Type | 条数 | 占抽样比例 |
|---|---|---|
| missing（需求声明但代码未实现） | 22 | 73.3% |
| inconsistent（需求与代码实现不一致） | 5 | 16.7% |
| risk（代码中潜在风险点） | 3 | 10.0% |
| **合计** | **30** | 100.0% |

> **说明**：上述分布为抽样 CSV 的 type 组成，不是全量 167 条的 type 组成。全量 type 组成可从 `findings_review_full.csv` 重新聚合获得，本期未计算。观察到抽样中**不含** `implemented` / `uncertain` / `extra` 三种 type，这一现象值得在 D2 阶段结合全量数据进一步审视。

---

## 7. Finding 抽样评审状态

| 项 | 值 |
|---|---|
| 评审 CSV 已导出 | ✅ 是（30 条） |
| 全量 CSV 已导出 | ✅ 是（167 条，仅作参考） |
| 强制纳入 TAPD 已推送 finding | ✅ 是（7 条全部纳入抽样） |
| 抽样是否分层 | ✅ 是（按 finding type 分层 + 随机补足到 30） |
| **人工评审是否执行** | **❌ 否（本期不执行）** |
| `human_review_result` 列填写率 | 0 / 30 |
| `human_comment` 列填写率 | 0 / 30 |
| `should_convert_to_defect` 列填写率 | 0 / 30 |
| `should_push_tapd` 列填写率 | 0 / 30 |

**因此本期不评估**：

- Precision（精准率）
- False Positive Rate（误报率）
- Manual Review Pass Rate（人工复核通过率）

**Recall（召回率）当前无法可靠计算**，需要一份"项目完整需求-代码映射真值集"作为分母，该真值集当前不存在。

---

## 8. TAPD 回写观察结果

### 8.1 总体

| 项 | 值 |
|---|---|
| 全部 finding | 167 |
| 已推送到 TAPD 的 finding | **7** |
| TAPD bug id 回写完整性 | 7 / 7 |

### 8.2 TAPD 字段完整性（基于 `tapd_observation.json`）

| TAPD 字段 | 完整性 |
|---|---|
| `tapd_bug_id` | **7 / 7** |
| `tapd_url` | **7 / 7** |
| `tapd_pushed_at` | **7 / 7** |
| `tapd_status` | **7 / 7** |
| `tapd_status_name` | **7 / 7** |
| `tapd_last_sync_at` | **7 / 7** |
| `tapd_modified` | **7 / 7** |

### 8.3 状态分布

| TAPD status_name | 条数 |
|---|---|
| 新建 | 7 |
| 其他 | 0 |

### 8.4 本阶段是否触发 TAPD 写入

| 动作 | 是否触发 |
|---|---|
| 调用 TAPD push 接口新建 bug | ❌ 否 |
| 调用 sync-tapd-status 同步状态 | ❌ 否 |
| 修改 TAPD 侧数据 | ❌ 否 |
| 本期仅做的 TAPD 侧动作 | 只读 GET 既有 finding 的 TAPD 字段 |

### 8.5 可证明的结论

- Finding → TAPD bug 的字段回写链路在真实项目上**字段完整**（7 条样本中每条 7 个 TAPD 字段均非空）。
- 7 条 TAPD bug 状态均为 `新建`，**未被 TAPD 端处理过**，也**未在 D1 阶段人为修改**。

### 8.6 不能证明的结论

- 无法证明 TAPD bug 的**内容质量**（标题是否合理、描述是否精确、严重程度是否恰当），这需要人工查看 TAPD 侧单子。
- 无法证明 `sync-tapd-status` 在状态发生变化时仍能正确回写（7 条全部保持在"新建"，未构造状态变更样本）。

---

## 9. 质量看板观察结果

### 9.1 端点可用性（基于 `dashboard_observation.json`）

| 端点 | HTTP 状态 | 能力 |
|---|---|---|
| `/api/v2/dashboard/summary` | **200** | 可用 |
| `/api/v2/analytics/overview` | **200** | 可用 |
| `/api/v2/dashboard/defect-summary` | **404** | 未实现 |
| `/api/v2/defects/summary/for-gate` | **200** | 可用（质量门禁专用） |
| `/api/v2/code-compare/reports` | **200** | 可用 |

### 9.2 能力标签

| 能力 | 当前支持 |
|---|---|
| 展示项目数 | ✅ 是 |
| 展示测试用例数 | ✅ 是 |
| 展示通过率（run_pass_rate） | ✅ 是 |
| 展示用例通过率（case_pass_rate） | ✅ 是 |
| 展示缺陷总数 | ❌ 否（默认 summary 不含） |
| `dashboard/defect-summary` 端点 | ❌ 否（404） |
| `defects/summary/for-gate` 端点 | ✅ 是 |
| 展示 finding-derived defect / TAPD-linked defect | ❌ 否（无专用聚合端点） |

### 9.3 可证明的结论

- 当前看板可展示**项目数 / 测试用例数 / 运行通过率 / 用例通过率**等通用质量数据。
- `defects/summary/for-gate` 端点可用，能够支撑"质量门禁"相关的缺陷聚合。
- `code-compare/reports` 端点可用，能够列出历史 code compare 报告。

### 9.4 不能证明的结论

- 当前看板**不能**专门展示 finding-derived defect / TAPD-linked defect（无专用聚合端点）。
- 未评估看板的 UI 展示一致性（本期仅做 API 观察，未做前端页面截图比对）。

---

## 10. 当前可证明的结论

1. **真实项目链路可运行**：Code Compare v2 能在真实项目数据上产出 167 条 finding（静态复用历史报告）。
2. **TAPD 字段回写链路完整**：7 条已推送 finding 的 7 个 TAPD 字段**全部 100% 非空**。
3. **TAPD 推送对数据库状态一致**：7 条 bug 的 `tapd_status_name` 均为 `新建`，与"本期未发起任何 TAPD 写入"一致。
4. **质量看板关键端点可用**：4 / 5 个端点返回 200，足以支撑基础项目/用例/通过率展示。
5. **抽样与评审工具已落地**：`scripts/validate_code_compare_v2_sample.py` 支持 `--export` / `--score` / `--observe-tapd` / `--observe-dashboard`，后续复现可机器化。
6. **D1 阶段未引入任何破坏性操作**：未改业务代码、未改数据库、未改前端、未新建 TAPD bug、未重跑 analyze。

---

## 11. 当前不能证明的结论

1. **不能证明** v2 引擎的**准确率（Precision）**——未做人工评审。
2. **不能证明** v2 引擎的**误报率（False Positive Rate）**——未做人工评审。
3. **不能证明** v2 引擎的**人工复核通过率（Manual Review Pass Rate）**——未做人工评审。
4. **不能可靠计算 Recall（召回率）**——需要一份项目完整的"需求-代码映射真值集"，当前不存在。
5. **不能证明** v2 引擎在**其他项目**上的表现——仅在蓝点 1 个项目上做了一次观察。
6. **不能证明** TAPD bug 的**内容质量**（标题 / 描述 / 严重度是否合理）——未做人工查看 TAPD 侧。
7. **不能证明** 状态同步链路（`sync-tapd-status`）在**状态发生变化时**仍能正确回写——7 条全部保持"新建"，未构造变更场景。

---

## 12. 已知能力边界

| 能力 | 当前状态 | 备注 |
|---|---|---|
| Code Compare v2 在真实项目上**产出 finding** | ✅ 可运行 | 167 条 |
| Finding **字段结构** | ✅ 完整 | 含 code_evidence / inconsistencies / test_suggestions 等 |
| Finding → TAPD **字段回写** | ✅ 100% 完整 | 7 条样本，7 字段全非空 |
| Finding **准确率量化** | ❌ 未量化 | 需人工评审 |
| Finding **召回率量化** | ❌ 不可量化 | 需真值集 |
| 抽样 type 分布 | 观察到 | missing(22) / inconsistent(5) / risk(3) |
| 抽样中 type 缺失项 | 观察到 | 未见 implemented / uncertain / extra |
| 质量看板**通用质量指标** | ✅ 支持 | 项目数 / 用例数 / 通过率 |
| 质量看板**缺陷总数聚合** | ❌ 默认不展示 | `dashboard/summary` 不含 |
| 质量看板**缺陷专用端点** | ⚠️ 部分 | `for-gate` 有，`defect-summary` 404 |
| 质量看板 **finding-derived defect 联动** | ❌ 无专用端点 | 登记为 D2+ 扩展候选 |
| origin remote push | ⚠️ 受 VPN 影响 | 仅 github 已同步 |

---

## 13. 后续待补事项

| 待办 | 触发条件 | 预计影响 |
|---|---|---|
| 人工填写 `findings_review.csv`（30 行） | 有评审人力 | 解锁 Precision / FP Rate / Manual Review Pass Rate 计算 |
| 跑 `python scripts\validate_code_compare_v2_sample.py --score rpt_ebc532452984` | D1.E 完成后 | 产出 `score_summary.json` |
| 补做 Recall 真值集构造 | D2 / D3 | 真值集是重劳作，可作为单独子项目规划 |
| 补做 `sync-tapd-status` 变更场景测试 | 有 TAPD 侧可控 bug | 需要能构造"bug 状态变化"的样本 |
| 扩展 `dashboard/defect-summary` 端点或明确作废 | 产品决策 | 当前 404，需决定是实现还是移除前端入口 |
| 补推 origin remote | VPN 恢复 | 当前领先 origin 若干 commit（以 `git log` 为准） |
| 引入第 2 个真实项目做横向对比 | D2+ | 避免"单项目过拟合"式结论 |

---

## 14. 是否建议进入下一阶段

**建议：可以进入 D2 规划，但 D2 必须包含"人工或半自动评审"这一块。**

理由：

- D1 的核心问题"平台在真实项目上能不能端到端跑起来"——已得到**肯定的客观证据**。
- D1 的次级问题"finding 准不准"——本期**主动跳过**，不编造结论。
- D2 阶段如果继续绕过评审，会让整条质量评估链路始终停留在"能跑"层级，无法给出"好不好用"的结论。

**不建议**的做法：

- 把 D1 当作"完全通过"并推向生产。
- 把"TAPD 字段回写 7/7"这一条直接等价于"v2 引擎质量达标"。
- 在没有真值集的情况下给出任何 Precision / Recall / FP Rate 的具体百分比数值。

---

## 15. 附录：关键数据摘要

```text
project            : 蓝点 recycle-applet-feature-1.2.3
report_id          : rpt_ebc532452984
analyze_rerun      : no
findings_total     : 167
review_sample      : 30
review_full_export : 167
sample_type_dist   : missing=22, inconsistent=5, risk=3
manual_review_done : no
tapd_pushed        : 7
tapd_field_complete: 7/7 for each of 7 fields
tapd_status_dist   : 新建=7
dashboard_endpoints: summary=200, overview=200, defect-summary=404,
                     for-gate=200, code-compare/reports=200
precision          : not_evaluated
false_positive_rate: not_evaluated
manual_pass_rate   : not_evaluated
recall             : not_computable_without_ground_truth
```

### 引用产物

- `docs/D1_REAL_PROJECT_VALIDATION_PLAN.md`（已入仓）
- `scripts/validate_code_compare_v2_sample.py`（已入仓）
- `data/validation_samples/rpt_ebc532452984/findings_review.csv`（本地产物，未入仓）
- `data/validation_samples/rpt_ebc532452984/findings_review_full.csv`（本地产物，未入仓）
- `data/validation_samples/rpt_ebc532452984/findings_review.md`（本地产物，未入仓）
- `data/validation_samples/rpt_ebc532452984/tapd_observation.json`（本地产物，未入仓）
- `data/validation_samples/rpt_ebc532452984/dashboard_observation.json`（本地产物，未入仓）

---

**本报告仅记录客观事实。任何 Precision / Recall / False Positive Rate / False Negative Rate / Manual Review Pass Rate 数值如在后续文档中出现，必须基于 `data/validation_samples/rpt_ebc532452984/findings_review.csv` 完整填写后由 `--score` 生成，严禁人工编造。**
