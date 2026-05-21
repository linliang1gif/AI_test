# AI Product Studio 项目总结

## 1. 项目定位

AI Product Studio 是 AI 测试平台中的产品设计与测试资产治理模块，用于把模糊产品想法转化为 PRD、原型说明、测试策略、验收标准，并进一步生成可追溯、可评分、可评审、可转正式的测试资产。

它不只是一个文档生成工具，而是一个从需求到测试资产的质量治理闭环。

## 2. 解决的问题

1. **需求不清晰**：产品想法往往只有口头描述，缺少结构化的 PRD 和验收标准。Product Studio 通过 LLM 生成结构化产物，降低需求梳理门槛。
2. **PRD 与测试资产断层**：传统流程中，PRD 写完后测试人员需要手动拆解需求点和测试用例，效率低且容易遗漏。Product Studio 自动从 PRD 提取需求点和生成测试用例草稿。
3. **测试用例生成缺少追溯**：AI 生成的用例不知道来源是什么。Product Studio 通过 TraceLink 建立 Artifact→RP/TC 的追溯关系。
4. **AI 生成内容质量不可控**：直接使用 LLM 输出的内容可能存在低质量或重复。Product Studio 提供质量评分和重复检测机制。
5. **草稿用例无法治理**：AI 生成的用例如果直接进入正式库，会污染测试数据。Product Studio 要求人工确认后才能 promote。
6. **缺少质量报告**：缺少项目级的质量汇总和风险可视化。Product Studio 提供 Dashboard 和 Markdown 质量报告。

## 3. 核心价值

1. **提升需求到测试的转化效率**：一键从产品想法生成 PRD → 测试策略 → 验收标准 → 测试用例
2. **建立产品产物和测试资产之间的 TraceLink**：每一条测试用例都可追溯到来源 Artifact
3. **提供质量评分和重复检测**：规则型评分 + 标题相似度查重，辅助人工决策
4. **支持人工确认/驳回**：AI 生成默认草稿，必须经过人工评审才能进入正式流程
5. **支持草稿转正式测试用例**：promote 机制将高质量草稿转为正式 TestCase
6. **支持质量 Dashboard 和质量报告**：项目级统计 + 风险标记 + 建议 + Markdown 报告

## 4. 产品闭环

```
用户输入产品想法
    │
    ├─→ 生成产品方案（product_solution）
    ├─→ 生成 PRD（prd）
    ├─→ 生成原型说明（prototype）
    ├─→ 生成测试策略（test_strategy）
    └─→ 生成验收标准（acceptance_criteria）
            │
            ├─→ 从 PRD 提取需求点（RequirementPoint）
            └─→ 从 PRD/测试策略/验收标准 生成测试用例草稿（TestCase）
                    │
                    └─→ 建立 TraceLink（Artifact ↔ RP/TC）
                            │
                            ├─→ 质量评分（quality_score）
                            ├─→ 重复检测（duplicate_candidates）
                            ├─→ 人工确认 / 驳回（confirmed / rejected）
                            └─→ Promote 正式 TestCase
                                    │
                                    ├─→ 正式用例查询
                                    ├─→ 质量 Dashboard
                                    └─→ 质量报告
```

## 5. 技术架构

| 层 | 技术 |
|----|------|
| 前端 | React + Vite + TailwindCSS |
| 后端 | FastAPI + SQLAlchemy |
| 数据库 | SQLite（开发环境），可切换 PostgreSQL |
| LLM | 复用现有 LLMClient（支持 DeepSeek / OpenAI / Ollama / Mock） |
| 追踪 | run_id / trace_id（每次 LLM 调用独立标识） |
| 产物存储 | ProductArtifact（content_markdown 字段） |
| 追溯 | ProductArtifactTraceLink（连接 Artifact 与 RP/TC） |

## 6. 数据流

```
用户输入 ProductIdea（标题/方向/用户/痛点/约束）
    ↓
调用 LLM 生成 Artifact
  → 创建 ProductStudioRun（记录执行状态/模型/trace_id）
  → 创建 ProductArtifact（保存 Markdown 内容）
    ↓
Artifact 生成 RequirementPoint / TestCase
  → 调用 LLM 解析 Artifact 内容
  → 创建 RP/TC 记录
  → 创建 ProductArtifactTraceLink（连接 Artifact 与 RP/TC）
    ↓
评分 / 查重
  → 规则型评分写入 quality_score / quality_reason
  → 标题相似度写入 duplicate_candidates
    ↓
人工评审
  → 确认/驳回 → 更新 TraceLink status + review_reason
    ↓
Promote
  → 更新 TC.status=pending, TC.source=ai_product_studio_promoted
  → 记录 promoted_at / promoted_target_id
    ↓
Dashboard / Report
  → 聚合所有 Artifact/TraceLink 统计
  → 生成 risk_flags + recommendations
  → 生成 Markdown 质量报告 Artifact
```

## 7. 测试与验收

| Phase | 脚本 | 项数 | 结果 |
|-------|------|------|------|
| Phase 1 | `test_product_studio_mvp.py` | 52 | ✅ PASS |
| Phase 2 | `test_product_studio_traceability.py` | 38 | ✅ PASS |
| Phase 3 | `test_product_studio_quality_governance.py` | 59 | ✅ PASS |
| Phase 4 | `test_product_studio_real_project_validation.py` | 55 | ✅ PASS |
| Phase 5 | `test_product_studio_quality_report.py` | 58 | ✅ PASS |
| **总计** | | **262** | **✅ ALL PASS** |

## 8. 当前边界

### 已做
- 5 种 Artifact 类型生成
- RequirementPoint / TestCase 草稿生成
- TraceLink 追溯 + 确认/驳回
- 规则型质量评分 + 重复检测
- Promote 正式 TestCase（幂等）
- 质量 Dashboard + 质量报告
- 前端完整交互

### 未做（合理决策）
- Skill 商店 / 第三方 Skill 导入
- Figma 集成 / 高保真原型
- 复杂 Artifact 版本 Diff
- PDF 导出
- 多人审批流 / 复杂权限
- 自动开发代码 / GitHub PR
- LLM Judge 评分（当前为规则型）

## 9. 项目亮点

1. **不只是生成文档**：形成了从产品想法到正式测试资产的完整闭环，而非仅输出 Markdown
2. **不只是生成用例**：每条用例都有 TraceLink 追溯到来源 Artifact，支持质量审计
3. **不只是 AI 输出**：有人工评审环节（确认/驳回 + review_reason），AI 不直接决定
4. **不只是草稿**：高质量草稿可以 promote 到正式 TestCase 表，融入测试平台主流程
5. **不只是功能结果**：有 Dashboard 和质量报告，支持项目汇报和风险预警
6. **符合测试架构和质量工程思路**：追溯、评分、评审、治理，遵循质量工程最佳实践

## 10. 面试 / 汇报表达

### 1 分钟版本

> "我负责设计和开发了 AI Product Studio 模块，这是 AI 测试平台中的产品设计与测试资产治理引擎。它能把一个模糊的产品想法，自动生成 PRD、测试策略、验收标准等结构化产物，然后从这些产物中提取需求点和测试用例草稿，建立追溯链路。每条草稿都经过质量评分和人工评审，高质量的草稿可以转为正式测试用例，最终输出项目级质量 Dashboard 和质量报告。整个模块覆盖了 5 个 Phase，262 项自动化验收全部通过。"

### 3 分钟版本

> "我负责设计和实现了 AI Product Studio，这是我们 AI 测试平台的产品设计与测试资产治理模块。
>
> **背景**：在传统测试流程中，需求文档和测试用例之间存在断层——PRD 写完后测试人员需要手动拆解需求、编写用例，效率低且容易遗漏，更缺少追溯关系。
>
> **我做了什么**：我设计了一个从产品想法到正式测试资产的端到端闭环。用户输入产品想法后，系统通过 LLM 自动生成 PRD、测试策略、验收标准等 5 种结构化产物，然后从这些产物中提取需求点和测试用例草稿，并建立 TraceLink 追溯链路——每条用例都知道它是从哪个文档的哪个部分生成的。
>
> **质量治理**：AI 生成的内容不直接进入正式库。我设计了规则型质量评分、重复检测、人工确认/驳回机制。只有经过评审且质量分达标的草稿，才能 promote 为正式测试用例。
>
> **可度量**：项目级质量 Dashboard 展示确认率、驳回率、平均质量分、风险标记等指标，并支持生成 Markdown 质量报告。
>
> **技术栈**：前端 React + TailwindCSS，后端 FastAPI + SQLAlchemy，LLM 层复用统一客户端支持 DeepSeek/OpenAI/Ollama。
>
> **验收**：5 个 Phase 共 262 项自动化验收全部通过，包括 3 个真实业务场景的全链路验证。
>
> **核心价值**：这个模块的核心不是'AI 能生成文档'，而是'AI 生成的内容可以经过治理流程，安全地融入正式测试体系'。这符合质量工程的思路——追溯、评分、评审、治理。"
