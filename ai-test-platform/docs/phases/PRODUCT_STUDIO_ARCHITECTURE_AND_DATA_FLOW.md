# AI Product Studio 架构与数据流

## 1. 模块架构

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend                              │
│                                                              │
│  ProductStudio.jsx          ProductStudioDetail.jsx          │
│  ├─ 想法列表                ├─ 想法详情                      │
│  ├─ 状态标签                ├─ 生成按钮组                    │
│  └─ 创建入口                ├─ Artifact/Run 列表             │
│                             ├─ Artifact 预览/编辑             │
│                             ├─ TraceLink 面板                │
│                             ├─ Quality Dashboard             │
│                             ├─ Quality Report 展示           │
│                             ├─ Markdown 渲染器               │
│                             └─ 批量 Promote 操作             │
└──────────────────────┬──────────────────────────────────────┘
                       │ HTTP /api/v2/product-studio/*
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                        Backend                               │
│                                                              │
│  product_studio_routes.py     product_studio_service.py      │
│  ├─ Idea CRUD                 ├─ generate()                  │
│  ├─ Artifact 生成/查询/更新   ├─ generate_requirement_points()│
│  ├─ TraceLink 查询/确认/驳回  ├─ generate_test_cases()       │
│  ├─ 评分/批量评分             ├─ score_trace_link()          │
│  ├─ Promote                   ├─ get_quality_dashboard()     │
│  ├─ Dashboard                 ├─ generate_quality_report()   │
│  └─ Quality Report            └─ batch_promote_test_cases()  │
│                                                              │
│  product_studio_prompts.py                                   │
│  └─ 各类型 Prompt 模板 + max_tokens 配置                    │
└──────────────────────┬──────────────────────────────────────┘
                       │
          ┌────────────┼────────────┐
          ▼            ▼            ▼
┌──────────────┐ ┌──────────┐ ┌──────────────────┐
│ Data Models  │ │ LLMClient│ │ Existing Modules │
│              │ │          │ │                  │
│ ProductIdea  │ │ DeepSeek │ │ TestCase 模块    │
│ ProductStudio│ │ OpenAI   │ │ (正式用例表)     │
│   Run        │ │ Ollama   │ │                  │
│ ProductArti- │ │ Mock     │ │ RequirementPoint │
│   fact       │ │          │ │ 模块             │
│ ProductArti- │ └──────────┘ │                  │
│   factTrace- │              └──────────────────┘
│   Link       │
└──────────────┘
```

## 2. 核心数据流

### 2.1 ProductIdea 创建流

```
用户提交表单
  → POST /api/v2/product-studio/ideas
  → 创建 ProductIdea 记录 (status=created)
  → 返回 idea_id
```

### 2.2 Artifact 生成流

```
用户点击"生成 PRD"
  → POST /ideas/{idea_id}/generate-prd
  → 创建 ProductStudioRun (status=running)
  → 调用 LLMClient.generate(prompt, max_tokens)
  → LLM 返回 Markdown 文本
  → 创建 ProductArtifact (type=prd, content_markdown=...)
  → 更新 Run (status=succeeded, artifact_id=...)
  → 返回 artifact_id + run_id + trace_id
```

### 2.3 RequirementPoint 生成流

```
用户选中 PRD Artifact → 点击"生成需求点"
  → POST /artifacts/{artifact_id}/generate-requirement-points
  → 校验 artifact_type ∈ {prd, product_solution}
  → 调用 LLM 解析 Artifact.content_markdown → JSON 数组
  → 遍历 JSON 数组:
      → 创建 RequirementPoint 记录
      → 创建 ProductArtifactTraceLink (target_type=requirement_point)
  → 返回 generated_count + requirement_points + trace_links
```

### 2.4 TestCase 生成流

```
用户选中 Artifact → 点击"生成测试用例草稿"
  → POST /artifacts/{artifact_id}/generate-test-cases
  → 校验 artifact_type ∈ {prd, test_strategy, acceptance_criteria}
  → 调用 LLM 解析 Artifact.content_markdown → JSON 数组
  → 遍历 JSON 数组:
      → 创建 TestCase 记录 (status=draft, source=ai_product_studio)
      → 创建 ProductArtifactTraceLink (target_type=test_case)
  → 返回 generated_count + test_cases + trace_links
```

### 2.5 TraceLink 生成流（自动）

```
TraceLink 在 RP/TC 生成时自动创建:
  → artifact_id = 来源 Artifact
  → target_type = requirement_point / test_case
  → target_id = RP/TC 的 ID
  → status = draft
  → quality_score = null (待评分)
```

### 2.6 质量评分流

```
用户点击"批量评分"
  → POST /artifacts/{artifact_id}/score-trace-links
  → 遍历该 Artifact 下所有 TraceLink:
      → 根据目标类型查询 RP/TC
      → 规则评分:
          - 标题长度 (>10 字 → +0.2)
          - 内容/步骤存在 → +0.2
          - 优先级存在 → +0.2
          - case_type 存在 → +0.2
          - 基础分 +0.2
      → 重复检测 (标题相似度 > 0.8 → duplicate)
      → 写入 quality_score / quality_reason / duplicate_candidates
  → 返回 scored_count + average_quality_score
```

### 2.7 Promote 流

```
用户点击"转正式" / "批量转正式"
  → POST /trace-links/{link_id}/promote-to-test-case
  → 校验 target_type = test_case
  → 校验 promoted_at 为空 (幂等)
  → 更新 TestCase: status=pending, source=ai_product_studio_promoted
  → 更新 TraceLink: promoted_at=now, promoted_target_id=tc.id
  → 返回 promoted_target_id

批量 promote:
  → POST /ideas/{idea_id}/batch-promote-test-cases
  → 查询 idea 下所有 test_case 类型 TraceLink
  → 过滤: only_confirmed + min_quality_score + max_count
  → 逐条 promote (跳过已 promoted)
  → 返回 promoted_count + skipped_count + skipped_reasons
```

### 2.8 Quality Report 流

```
用户点击"生成质量报告"
  → POST /ideas/{idea_id}/generate-quality-report
  → 调用 _collect_idea_stats(idea_id) 聚合统计
  → 构建 Markdown 报告 (项目概况/质量统计/追溯链路/风险/建议/结论)
  → 创建 ProductArtifact (type=quality_report, content_markdown=...)
  → 返回 artifact_id + summary
```

## 3. 状态流转

### ProductArtifact.status

```
draft ──→ confirmed ──→ archived
  │                       ↑
  └───────────────────────┘
```

- `draft`: 默认状态，LLM 生成后
- `confirmed`: 人工确认
- `archived`: 归档

### ProductArtifactTraceLink.status

```
draft ──→ confirmed
  │
  └──→ rejected
```

- `draft`: 默认状态，自动生成后
- `confirmed`: 人工确认，可 promote
- `rejected`: 人工驳回

### ProductStudioRun.status

```
created ──→ running ──→ succeeded
                │
                └──→ failed
```

## 4. 追溯关系

```
ProductArtifact (来源)
    │
    │  artifact_id
    ▼
ProductArtifactTraceLink (桥梁)
    │
    │  target_id + target_type
    ▼
RequirementPoint / TestCase (目标)
    │
    │  promoted_target_id (promote 后)
    ▼
TestCase (正式用例, source=ai_product_studio_promoted)
```

**关键字段说明**：

| 字段 | 位置 | 说明 |
|------|------|------|
| `artifact_id` | TraceLink | 来源 Artifact ID |
| `target_type` | TraceLink | `requirement_point` 或 `test_case` |
| `target_id` | TraceLink | RP 或 TC 的 ID |
| `quality_score` | TraceLink | 规则评分 (0~1) |
| `quality_reason` | TraceLink | 评分原因文本 |
| `duplicate_candidates` | TraceLink | 重复候选 JSON |
| `review_reason` | TraceLink | 人工评审原因 |
| `promoted_at` | TraceLink | promote 时间（幂等标记） |
| `promoted_target_id` | TraceLink | 正式 TestCase ID |

## 5. 安全与治理

1. **错误脱敏**：`sanitize_text()` 截断和清理 LLM 错误信息，防止敏感内容泄露
2. **trace_id**：每次 LLM 调用生成唯一 trace_id，支持问题追踪
3. **mock/fallback 标识**：LLM 使用 mock provider 时在响应中标记 `is_mock=true`
4. **LLM 失败不崩溃**：LLM 调用失败时 Run 记录 error_message，不影响其他功能
5. **promote 幂等**：`promoted_at` 非空时跳过，不重复创建正式 TestCase
6. **batch promote 过滤**：默认 `only_confirmed=true` + `min_quality_score=0.8` + `max_count=20`
7. **AI 结果默认草稿**：所有 AI 生成的 RP/TC 默认 status=draft，不直接进入正式资产，必须经过人工评审
8. **Markdown 渲染 XSS 防护**：`renderMarkdown()` 对输入做 HTML 实体转义（`& < >`），仅适用于可信 LLM 输出
