# AI Product Studio 演示脚本

## 1. 演示目标

演示从产品想法到正式测试用例和质量报告的完整闭环，展示 AI Product Studio 的端到端能力。

## 2. 演示前准备

1. **启动后端**：`python -m uvicorn backend.app:create_app --factory --port 8000`
2. **启动前端**：`cd frontend && npm run dev`（访问 http://localhost:5173）
3. **准备一个产品想法**：例如"AI 驱动的智能缺陷分析平台"
4. **准备已有真实项目数据**：可通过 Phase 4 验收脚本预生成
5. **确认 Phase 1-5 回归通过**：`python scripts/test_product_studio_quality_report.py http://127.0.0.1:8000`

## 3. 演示路径

### 步骤 1：进入 Product Studio 首页

- 导航到 `/product-studio`
- 展示想法列表（如果有历史数据会显示多条）
- 展示状态标签（created/in_progress 等）

### 步骤 2：创建 ProductIdea

- 点击"新建产品想法"
- 输入：
  - 产品名称：AI 智能缺陷分析平台
  - 产品方向：SaaS / 内部工具
  - 目标用户：测试工程师、QA Leader
  - 痛点：缺陷数据分散，难以识别系统性问题和趋势
  - 约束：需兼容现有测试平台数据模型
- 点击"保存并进入详情"

### 步骤 3：生成产品方案

- 点击"生成产品方案"按钮
- 等待 LLM 返回（约 15-30s）
- 展示生成的产品方案：产品定位、核心功能、技术方案、竞品分析等

### 步骤 4：生成 PRD

- 点击"生成 PRD"按钮
- 展示 PRD Artifact：功能需求列表、用户故事、优先级、非功能需求等
- 说明 Markdown 渲染增强效果（标题/表格/列表）

### 步骤 5：生成原型说明

- 点击"生成原型说明"按钮
- 展示页面清单、页面功能描述、交互流程、线框图说明

### 步骤 6：生成测试策略

- 点击"生成测试策略"按钮
- 展示测试范围、测试类型、风险评估、质量门禁标准

### 步骤 7：生成验收标准

- 点击"生成验收标准"按钮
- 展示可测试的验收条件表格、通过条件、测试方法

### 步骤 8：从 PRD 生成需求点

- 选中 PRD Artifact
- 点击"生成需求点"按钮
- 展示生成的 RequirementPoint 草稿列表
- 说明每个需求点通过 TraceLink 关联到来源 PRD

### 步骤 9：从验收标准生成测试用例

- 选中验收标准 Artifact
- 点击"生成测试用例草稿"按钮
- 展示生成的 TestCase 草稿列表
- 说明 case_type（functional/api/webui 等）

### 步骤 10：查看 TraceLink

- 展示 TraceLink 面板
- 说明来源 Artifact → target_type (requirement_point / test_case) → target_id
- 说明每条 link 的 status（draft → confirmed / rejected）

### 步骤 11：评分和查重

- 点击"批量评分"按钮
- 展示 quality_score（0~1）和 quality_reason
- 说明规则型评分逻辑（标题长度、内容结构、优先级等）
- 展示 duplicate_candidates（如果有重复）

### 步骤 12：确认 / 驳回

- 确认一条高质量 TraceLink，输入 review_reason
- 驳回一条低质量 TraceLink，输入 review_reason
- 展示状态变化：draft → confirmed / rejected
- 说明"全部确认"/"全部驳回"批量操作

### 步骤 13：Promote 正式 TestCase

- 在 TraceLink 面板中找到已确认的测试用例
- 点击"转正式"按钮
- 展示 promoted_target_id
- 切换到测试用例管理页面，搜索 source=ai_product_studio_promoted，展示正式 TestCase

### 步骤 14：查看 Quality Dashboard

- 返回详情页，查看 Dashboard 面板
- 展示 8 项指标：产物数、需求点数、TC 草稿数、TraceLink 数、已确认、已驳回、已转正、平均质量分
- 展示 risk_flags（如 LOW_CONFIRMATION_RATE）
- 展示 recommendations

### 步骤 15：生成 Quality Report

- 点击"📊 生成质量报告"按钮
- 自动跳转到报告 Artifact
- 展示 Markdown 报告内容：项目概况、质量统计、追溯链路、风险标记、建议、结论

## 4. 演示话术

### 步骤 1-2（开场，约 1 分钟）

> "这是我们 AI 测试平台的 Product Studio 模块。它的核心目标是把一个模糊的产品想法，通过 AI 转化为结构化的产品产物和可追溯的测试资产。我先创建一个新的产品想法。"

### 步骤 3-7（生成产物，约 2 分钟）

> "创建完想法后，我可以一键生成产品方案、PRD、原型说明、测试策略和验收标准。每次生成都会创建一条执行记录，包含 trace_id 和模型信息。可以看到，PRD 包含了功能需求列表和用户故事，测试策略包含了测试范围和风险评估。这些都是结构化的 Markdown 产物，可以编辑和导出。"

### 步骤 8-10（追溯，约 1.5 分钟）

> "接下来是核心环节——从 PRD 提取需求点，从验收标准生成测试用例草稿。注意，每条需求点和测试用例都通过 TraceLink 关联到来源 Artifact。这意味着我们可以回溯'这条测试用例是从哪个文档的哪个部分生成的'。这是 AI 生成和传统手写用例的关键区别。"

### 步骤 11-12（质量治理，约 1.5 分钟）

> "AI 生成的内容不是直接可用的。我们有质量评分机制，每条 TraceLink 都有 quality_score 和评分原因。同时有重复检测，防止冗余用例。人工评审是必须的——确认高质量的，驳回低质量的，并记录评审原因。AI 默认输出的都是草稿状态。"

### 步骤 13（Promote，约 1 分钟）

> "经过评审的高质量测试用例，可以 promote 为正式 TestCase，进入测试平台的正式用例库。promote 是幂等的，不会重复创建。正式用例可以在用例管理模块中查到，标记为 ai_product_studio_promoted。"

### 步骤 14-15（Dashboard 和报告，约 1.5 分钟）

> "最后是项目级的质量 Dashboard 和质量报告。Dashboard 展示了确认率、驳回率、平均质量分、风险标记等指标。如果有问题，会给出具体建议。质量报告是一个完整的 Markdown 文档，可以用于汇报和存档。"

### 收尾（约 30 秒）

> "总结一下：Product Studio 不只是让 AI 生成文档，而是建立了一个从需求到测试资产的质量治理闭环——追溯、评分、评审、转正式、报告。5 个 Phase，262 项自动化验收全部通过。"

## 5. 亮点总结

1. **需求到测试资产全链路**：产品想法 → PRD → 测试用例 → 正式 TestCase，一站式完成
2. **TraceLink 可追溯**：每条用例都有来源，支持质量审计和需求覆盖分析
3. **AI 生成质量可治理**：质量评分 + 重复检测，不是盲目信任 AI 输出
4. **人工评审可控**：确认/驳回 + review_reason，AI 辅助但人工决策
5. **正式测试资产可落库**：promote 后进入 TestCase 主表，融入测试平台主流程
6. **质量报告可汇报**：Dashboard + Markdown 报告，支持项目级质量度量

## 6. 常见问题回答

### Q1: 这和普通 AI 生成测试用例有什么区别？

> 普通 AI 生成用例只是"给一段需求，输出一堆用例"，没有追溯、没有评分、没有评审、没有治理流程。Product Studio 的区别在于：每条用例有来源追溯（TraceLink），有质量评分，有人工评审环节，有 promote 正式流程，有 Dashboard 和质量报告。它是一个质量治理闭环，不是一个简单的生成工具。

### Q2: AI 生成不准怎么办？

> AI 生成的内容默认是草稿状态，不会直接进入正式库。我们有三道防线：(1) 质量评分机制自动标记低质量内容；(2) 重复检测防止冗余；(3) 人工评审是必须环节，只有确认后才能 promote。如果生成质量差，可以驳回并重新生成。

### Q3: 如何防止垃圾用例进入正式库？

> promote 有三重保障：(1) 只有 confirmed 状态的 TraceLink 可以 promote；(2) 批量 promote 有 min_quality_score 过滤（默认 >= 0.8）；(3) 已 promoted 的不会重复创建（幂等）。此外，Dashboard 的 risk_flags 会预警异常情况。

### Q4: 如何证明生成内容有价值？

> Phase 4 用 3 个真实业务场景做了全链路验证：生成了 268 条 TraceLink，平均质量分 0.82，高分准确率 100%，需求点可用率 100%，promoted TestCase 查询率 100%。这些都是自动化验证的结果。

### Q5: 为什么没做 Figma / 高保真原型？

> 当前主线是从产品想法到测试资产的治理闭环，Figma 集成需要第三方 API 对接，高保真原型需要额外的渲染引擎。当前阶段以文本原型说明为主，已经足够验证流程闭环。后续有需求时可以扩展。

### Q6: 为什么没做 Skill 商店？

> Skill 商店是一个独立的功能模块，需要 Skill 定义规范、第三方导入机制、Skill 编排引擎等基础设施。当前 Product Studio 的 5 种 Artifact 类型（产品方案/PRD/原型/测试策略/验收标准）已经覆盖了核心场景。Skill 商店属于后续扩展项。

### Q7: 下一步准备做什么？

> 下一步是 Phase 6：AI Dev Studio DevPlan MVP。目标是将 Product Studio 生成的 PRD 和验收标准，进一步转化为开发计划——包括接口设计、数据库设计、影响文件分析、任务拆解。形成需求→设计→开发→测试的完整闭环。
