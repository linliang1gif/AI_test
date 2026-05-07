# 需求-代码对比 v2 质量评估文档

> 本文档定义 v2 引擎的质量评估方法、抽样标准与指标体系。
> **当前指标先留占位**，必须等真实项目抽样跑出后再填写，**不编造数值**。

---

## 1. v2 引擎定位

需求-代码对比 v2 引擎用于：

> 在不运行代码的前提下，将需求文档中的"需求点 (requirement point)"与代码实现做静态对比，输出"四态主结论 + 两态辅助"的 finding，并支持人工确认与导入 TAPD。

**它不是**：
- 不是动态测试引擎，不会调用真实 API / 跑真实 UI
- 不是单元测试覆盖率工具
- 不是 lint / 静态语法检查工具

**它是**：
- 静态语义对比（需求文本 ↔ 代码摘要的 AI 推理对比）
- 配合二次复核机制降低单次 AI 推断的随机性
- 输出结构化 finding 供人工评审与缺陷转化

## 2. 当前能力范围

代码事实（来自 `routes/code_compare_routes.py`、`utils/code_analyzer.py`、`knowledge/code_indexer.py`、`services/code_compare_storage_service.py`）：

| 能力 | 实现位置 | 备注 |
|---|---|---|
| 上传 ZIP 代码快照（含安全加固）| `routes/code_compare_routes.py::upload_code_snapshot` | 限制大小、校验后缀 |
| 从 Git 仓库克隆代码 | `routes/code_compare_routes.py::clone_repo` | 支持私有仓库 token，token 在日志中脱敏（`_sanitize_git_url_for_log`）|
| 多语言代码扫描 | `utils/code_analyzer.py::scan_code_directory` | 支持 Vue / JS / TS / Python / Java |
| Vue SFC 解析 | `utils/code_analyzer.py::_parse_vue_file` | 提取组件名、props、methods、template |
| 需求文档解析 + 缓存 | `routes/code_compare_routes.py::cache_requirement` | `data/code_compare/req_cache/` |
| 对比分析 | `routes/code_compare_routes.py::analyze_requirement_code` | 内部走 AI prompt（fallback 模式可用）|
| Finding 持久化 | `services/code_compare_storage_service.py` | DB + 文件双存储 |
| 人工确认 | `routes/code_compare_routes.py::confirm_finding` | 7 种 manual_status |
| Finding 转缺陷 / 用例 / 待确认 / 误报 | `convert-to-defect/case/question` + `mark-false-positive` | 4 个动作 |
| 标题/描述生成 | `services/tapd_service.py::finding_to_tapd_bug` | 8/8 单元测试 |

## 3. 检索召回机制

### 3.1 代码侧检索

来源：`utils/code_analyzer.py::scan_code_directory` + `knowledge/code_indexer.py`。

| 步骤 | 实现 | 输入 | 输出 |
|---|---|---|---|
| 文件遍历 | `scan_code_directory` | 项目目录 | 按语言分桶的文件清单 |
| 单文件解析 | `_parse_vue_file` / `_parse_js_file` / `_parse_python_file` / `_parse_java_file` | 文件内容 + 相对路径 | 组件 / 函数 / 类 / 方法的结构化条目 |
| 摘要 | `summarize_code_analysis` | 全量解析结果 | 给 AI prompt 的代码摘要文本 |

### 3.2 需求侧检索

需求文档解析后切分为 "requirement points"（需求点），每个点带 `req_id`、`requirement` 文本，进入对比循环。

### 3.3 召回粒度

| 粒度 | 当前实现 | 备注 |
|---|---|---|
| 项目级摘要 | ✅ | `summarize_code_analysis` 一次性提供 |
| 文件级匹配 | ✅ | finding.code_evidence.file 指向具体 .vue / .js / .py |
| 函数 / 组件级 | ✅ | finding.code_evidence.code_item 指向 `purchaseOrderAdd` 等具体符号 |
| 行级定位 | 部分 | `code_evidence.line` 字段存在但常为 0（**精度受限**，非 RC-1 阻塞）|
| 跨文件依赖 | 暂无 | 调用图 / 引用图 暂未实现 |

## 4. 四态判断规则

代码事实（来自 `routes/code_compare_routes.py::_diff_to_findings`）：

实际有 **6 种 type**（4 主 + 2 辅）：

| type | 判定来源 | 主/辅 | 含义 |
|---|---|---|---|
| `implemented` | matched + confidence > 0.5 | 主 | 已实现 |
| `inconsistent` | matched + status="部分实现/partial" 或 inconsistent 列表 | 主 | 实现与需求不一致 |
| `missing` | unimplemented 列表 | 主 | 需求未实现 |
| `risk` | bugs 列表 | 主 | 实现存在风险 |
| `uncertain` | matched + confidence <= 0.5 | 辅 | 实现存疑（低置信）|
| `extra` | extra 列表 | 辅 | 多余代码（无对应需求）|

**四态主结论 = `implemented` / `inconsistent` / `missing` / `risk`**，进入推 TAPD / 转缺陷 / 转用例的核心判定。

## 5. finding 证据结构

代码事实（来自 `routes/code_compare_routes.py::_new_finding`）：

```python
{
  "finding_id": "f_<12hex>",          # 唯一 ID
  "type": "missing|inconsistent|risk|implemented|uncertain|extra",
  "requirement": "<需求点原文>",
  "req_id": "<需求点 ID>",
  "confidence": 0.0~1.0,
  "risk_level": "high|medium|low",
  "analysis": "<AI 给出的分析说明（可能含 [复核] 前缀）>",
  "code_evidence": {                  # 单条 dict 或 list
    "file": "...vue|.js|.py",
    "line": 0,
    "code_item": "<组件/函数/类名>",
    "match_reason": "<匹配理由>"
  },
  "evidence_snippet": "<代码片段>",
  "inconsistencies": [                # 维度化的不一致点
    {"aspect": "...", "expected": "...", "actual": "..."}
  ],
  "test_suggestion": {                # 测试建议
    "title": "...",
    "priority": "high|medium|low",
    "test_points": ["验证 X", "验证 Y", ...]
  },
  "manual_status": "未审核|confirmed_implemented|confirmed_missing|false_positive|need_discussion|converted_to_bug|converted_to_case|need_product_confirm",
  "tapd_bug_id": null,                # 推 TAPD 后回填
  "tapd_url": null,
  "tapd_pushed_at": null,
  "tapd_status": null,
  "tapd_status_name": null,
  "tapd_last_sync_at": null
}
```

**关键证据字段**：

| 字段 | 角色 |
|---|---|
| `analysis` | AI 给出的判定理由 |
| `code_evidence.file/line/code_item` | 代码定位 |
| `evidence_snippet` | 代码原文片段 |
| `inconsistencies[]` | 不一致的具体维度 + 需求要求 + 代码实际 |
| `confidence` | 单次 AI 推断的置信度 |

## 6. 二次复核机制

代码事实（来自 `services/tapd_service.py::_BUG_TONE_REPLACEMENTS`）：

`finding.analysis` 中可能出现 `[复核]` 前缀，表明该 finding 经过了二次 AI 复核。

| 触发条件 | 当前依据代码 |
|---|---|
| 何时触发复核 | `routes/code_compare_routes.py` 内部对部分高风险/低置信 finding 触发二次 AI 调用 |
| 复核结果如何融合 | analysis 字段加 `[复核]` 前缀，最终 finding 仅保留一条 |
| 是否影响 type | 复核可改变 type（例如 risk → inconsistent）|
| 是否影响 confidence | 复核会调整 confidence 值 |

**未在本次 RC-1 评估范围内**：复核覆盖率、复核前后 type 翻转率、复核额外耗时（需要在抽样阶段量化）。

## 7. 当前已验证事实

| 事实 | 数据 | 来源 |
|---|---|---|
| 已生成报告数 | `data/code_compare/reports/` 共 12 个 `rpt_*.json` | 文件系统 |
| 已生成需求 cache | `data/code_compare/req_cache/` 共 16 个 `req_*.json` | 文件系统 |
| 蓝点项目实测样本 | `rpt_ebc532452984` 共 10 个 findings | 单一报告 |
| TAPD 实推 bug | 1055833~1055839 共 6 条（其中 1055833 已删）| TAPD 项目 50366622 |
| 标题/描述生成单元测试 | 8/8 PASS | `scripts/test_finding_to_tapd_bug.py` |
| 标题/描述生成回归 | 修复语气 / 模板后再跑 8/8 PASS | 同上 |

## 8. 未验证风险

### 8.1 项目维度

| 风险 | 状态 |
|---|---|
| 跨项目泛化 | 未验证（仅蓝点 1 个项目，且仅前端 .vue + uni-app）|
| 跨语言 | 未验证（实际跑过的仅 Vue + 少量 JS）|
| 大型代码库 | 未验证（蓝点中等规模；10w+ 行项目未测）|
| 多需求文档格式 | 未验证（需求当前来自单一渠道）|

### 8.2 finding 质量维度

| 风险 | 状态 |
|---|---|
| 假阳性率（FP）| 未量化 |
| 假阴性率（FN）| 未量化 |
| 同质 finding 重复率 | 未量化 |
| 复核覆盖率与翻转率 | 未量化 |
| 标题字段抽取准确率 | 未量化（已通过单元测试覆盖典型 case）|

### 8.3 数据维度

| 风险 | 状态 |
|---|---|
| 需求与代码版本错位 | 未量化（实际工程中需求与代码可能不同步）|
| 代码注释 / 死代码干扰 | 未量化 |

## 9. 人工抽样评估方法

### 9.1 抽样原则

- **按 type 分层抽样**：4 个主态各抽 N 条，2 个辅态各抽 N/2 条
- **按 confidence 分桶抽样**：[0, 0.5] / [0.5, 0.7] / [0.7, 0.9] / [0.9, 1.0] 各桶不少于 5 条
- **按项目分层**：每个项目至少 30 条样本
- **盲评**：评审人员看不到 confidence / risk_level，仅看 finding.requirement / analysis / code_evidence / inconsistencies

### 9.2 评审标准

每条 finding 由人工评审打 1 个标签：

| 标签 | 含义 |
|---|---|
| TP（True Positive）| 引擎判 missing/inconsistent/risk，人工复核确认确实存在该问题 |
| FP（False Positive）| 引擎判有问题，人工复核为误报（代码已实现 / 与需求一致）|
| FN（False Negative）| 引擎判 implemented，人工复核发现存在 missing/inconsistent |
| TN（True Negative）| 引擎判 implemented，人工复核确认无问题 |
| 不可判定 | 评审人员凭现有 finding 信息无法判定（需更多上下文）|

### 9.3 推荐样本量

| 评估范围 | 样本量 |
|---|---|
| 单项目 RC | 不少于 100 条 |
| 跨项目泛化 | 至少 3 个项目，每项目不少于 50 条 |
| 单 type 显著性 | 每 type 不少于 30 条 |

## 10. 质量指标定义

| 指标 | 公式 | 含义 |
|---|---|---|
| **Precision（准确率）** | TP / (TP + FP) | 引擎说有问题的 finding 中，确实有问题的比例 |
| **Recall（召回率）** | TP / (TP + FN) | 实际有问题的需求点中，被引擎找出来的比例 |
| **False Positive 率（FP rate）** | FP / (TP + FP) | 引擎给出的 finding 中误报的比例（= 1 - Precision）|
| **False Negative 率（FN rate）** | FN / (TP + FN) | 实际有问题但引擎漏掉的比例（= 1 - Recall）|
| **Manual Review Pass Rate（人工复核通过率）** | (TP 中被评 "可入 TAPD") / TP | 人工复核认可入库的 finding 占 TP 的比例（衡量 finding 描述质量与可执行性）|
| **Duplicate Rate（重复率）** | (内容指纹相同的 finding 数 - 1) / 总 finding 数 | 同质 finding 重复推送概率 |

## 11. 真实项目验证计划

### 11.1 第一轮：蓝点项目（已部分覆盖）

| 项 | 状态 |
|---|---|
| 已生成报告 | rpt_ebc532452984 等 12 个 |
| 已实推 TAPD | 6 条 bug（实例化数据）|
| 抽样人工评审 | **未开展** |
| 输出 | 第一份 precision / recall / FP / FN 数据 |

### 11.2 第二轮：跨项目泛化（待选）

候选：从平台已接入的项目中选 2 个不同语言 / 业务领域的项目。

需求：
- 每项目至少 1 份完整需求文档
- 配套代码快照
- 1 名熟悉项目的评审人

### 11.3 第三轮：动态验证组合（参考方向）

参见 `docs/RC1_ACCEPTANCE_REPORT.md` §12："真实项目动态 API 验证（白盒+黑盒）" 单开任务。

## 12. 指标占位表

> 以下数值**当前留空，等真实抽样跑出后填充**。**严禁编造**。

### 12.1 单项目（蓝点）

| 指标 | 值 | 样本量 | 评审日期 | 备注 |
|---|---|---|---|---|
| Precision | <待填> | 待填 | 待填 | |
| Recall | <待填> | 待填 | 待填 | |
| FP rate | <待填> | 待填 | 待填 | |
| FN rate | <待填> | 待填 | 待填 | |
| Manual Review Pass Rate | <待填> | 待填 | 待填 | |
| Duplicate Rate | <待填> | 待填 | 待填 | |

### 12.2 按 type 分层

| type | Precision | Recall | FP | FN | 样本量 |
|---|---|---|---|---|---|
| implemented | 待填 | 待填 | 待填 | 待填 | 待填 |
| inconsistent | 待填 | 待填 | 待填 | 待填 | 待填 |
| missing | 待填 | 待填 | 待填 | 待填 | 待填 |
| risk | 待填 | 待填 | 待填 | 待填 | 待填 |
| uncertain | 待填 | 待填 | 待填 | 待填 | 待填 |
| extra | 待填 | 待填 | 待填 | 待填 | 待填 |

### 12.3 按 confidence 分桶

| confidence 区间 | Precision | 样本量 |
|---|---|---|
| [0.0, 0.5] | 待填 | 待填 |
| (0.5, 0.7] | 待填 | 待填 |
| (0.7, 0.9] | 待填 | 待填 |
| (0.9, 1.0] | 待填 | 待填 |

### 12.4 推 TAPD 后的人工反馈（实际工作中收集）

| 指标 | 值 | 备注 |
|---|---|---|
| 推送后被开发标记"无效缺陷"率 | 待填 | 来自 TAPD 反向同步的状态变更 |
| 推送后被合并 / 关闭"重复"的比例 | 待填 | 用于校准 R1 风险（指纹去重）|
| 推送后真实修复的比例 | 待填 | 衡量 finding 实际价值 |

---

*文档生成日期：2026-05-07；适用分支：`feature/tapd-integration-and-code-compare`；HEAD：`e7d6bf7`*
