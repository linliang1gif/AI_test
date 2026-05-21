"""
AI Product Studio — Prompt 模板
5 个模板：product_solution / prd / prototype / test_strategy / acceptance_criteria
"""

# ── 每类 prompt 对应的 max_tokens ────────────────────────────────
MAX_TOKENS_MAP = {
    "product_solution": 8000,
    "prd": 12000,
    "prototype": 12000,
    "test_strategy": 10000,
    "acceptance_criteria": 8000,
}

ARTIFACT_TITLE_MAP = {
    "product_solution": "产品方案",
    "prd": "PRD 文档",
    "prototype": "原型设计说明",
    "test_strategy": "测试策略",
    "acceptance_criteria": "验收标准",
}


def _common_constraints() -> str:
    return """
## 约束条件
1. 不允许编造不存在的接口、数据、真实用户反馈。
2. 信息不足时必须标注「假设」。
3. 输出必须结构化 Markdown。
4. 输出适合研发、测试、产品协作阅读。
5. 必须给出风险、不做范围、验收标准。
6. 不要为了显得完整而虚构事实。
7. 敏感信息（API Key、Token、密码等）不允许出现在输出中。
"""


def build_product_solution_prompt(idea: dict) -> str:
    return f"""你是一位资深产品架构师，擅长从模糊想法中提炼产品方案。

## 输入信息

- 产品名称：{idea.get('title', '')}
- 产品方向：{idea.get('product_direction', '')}
- 目标用户：{idea.get('target_users', '')}
- 当前痛点：{idea.get('pain_points', '')}
- 已有基础：{idea.get('existing_assets', '')}
- 当前卡点：{idea.get('current_blockers', '')}
- 约束条件：{idea.get('constraints', '')}

## 输出要求

请按以下结构输出完整产品方案（Markdown 格式）：

# 产品方案

## 1. 结论

## 2. 问题重新定义

## 3. 目标用户

## 4. 核心场景

## 5. 用户痛点

## 6. AI 是否适合介入

## 7. 三个可行方案

### 方案 A：轻量 MVP

### 方案 B：标准产品版

### 方案 C：进阶平台版

## 8. 推荐方案

## 9. MVP 范围

## 10. 不做范围

## 11. 产品架构

## 12. 核心数据流

## 13. AI 工作流

## 14. 测试策略初稿

## 15. 风险与限制

## 16. 下一步建议
{_common_constraints()}
"""


def build_prd_prompt(idea: dict, solution_md: str = "") -> str:
    ctx = ""
    if solution_md:
        ctx = f"\n\n## 已有产品方案（供参考）\n\n{solution_md[:6000]}\n"
    return f"""你是一位资深产品经理，擅长撰写结构清晰、研发友好的 PRD 文档。

## 输入信息

- 产品名称：{idea.get('title', '')}
- 产品方向：{idea.get('product_direction', '')}
- 目标用户：{idea.get('target_users', '')}
- 当前痛点：{idea.get('pain_points', '')}
- 已有基础：{idea.get('existing_assets', '')}
- 当前卡点：{idea.get('current_blockers', '')}
- 约束条件：{idea.get('constraints', '')}
{ctx}
## 输出要求

请按以下结构输出完整 PRD（Markdown 格式）：

# PRD 文档

## 1. 产品背景

## 2. 目标用户

## 3. 用户痛点

## 4. 产品目标

## 5. 本期范围

## 6. 不做范围

## 7. 用户流程

## 8. 功能模块

每个功能模块必须包含：功能说明、输入、处理逻辑、输出、异常场景、验收标准。

## 9. 页面说明

## 10. AI 工作流

## 11. API 需求

## 12. 数据结构

## 13. 权限规则

## 14. 异常处理

## 15. 埋点需求

## 16. 验收标准

## 17. 风险与依赖
{_common_constraints()}
"""


def build_prototype_prompt(idea: dict, prd_md: str = "") -> str:
    ctx = ""
    if prd_md:
        ctx = f"\n\n## 已有 PRD（供参考）\n\n{prd_md[:6000]}\n"
    return f"""你是一位资深交互设计师，擅长将 PRD 转化为低保真原型说明。

## 输入信息

- 产品名称：{idea.get('title', '')}
- 产品方向：{idea.get('product_direction', '')}
- 目标用户：{idea.get('target_users', '')}
{ctx}
## 输出要求

请按以下结构输出原型设计说明（Markdown 格式）：

# 原型设计说明

## 1. 页面总览

用表格列出：页面名称 | 页面目标 | 路由建议 | 主要用户动作 | 优先级

## 2. 页面详情

每个页面必须包含：
- 页面名称、页面目标、页面布局
- 核心组件、字段说明、按钮动作
- 页面状态（empty / loading / normal / error）
- 异常提示、验收标准

## 3. 低保真 Wireframe

使用文本线框图，例如：

```
+------------------------------------------------+
| 页面标题                                       |
+------------------------------------------------+
| 筛选区 / 表单区                                |
+------------------------------------------------+
| 内容卡片 / 表格 / 结果区                       |
+------------------------------------------------+
| 操作按钮区                                     |
+------------------------------------------------+
```

## 4. 用户流程图

使用 Mermaid flowchart 输出。

## 5. 页面数据流

说明用户输入、前端状态、后端接口、AI 调用、结果展示之间的关系。
{_common_constraints()}
"""


def build_test_strategy_prompt(idea: dict, prd_md: str = "", prototype_md: str = "") -> str:
    ctx = ""
    if prd_md:
        ctx += f"\n\n## 已有 PRD（供参考）\n\n{prd_md[:4000]}\n"
    if prototype_md:
        ctx += f"\n\n## 已有原型说明（供参考）\n\n{prototype_md[:4000]}\n"
    return f"""你是一位资深测试架构师，擅长制定全面的测试策略。

## 输入信息

- 产品名称：{idea.get('title', '')}
- 产品方向：{idea.get('product_direction', '')}
- 目标用户：{idea.get('target_users', '')}
{ctx}
## 输出要求

请按以下结构输出测试策略（Markdown 格式）：

# 测试策略

## 1. 测试目标

## 2. 测试范围

## 3. 不测范围

## 4. 测试类型

必须包含：功能测试、接口测试、数据测试、权限测试、异常测试、AI 输出质量测试、回归测试、上线验证。

## 5. 核心测试点

## 6. 测试数据设计

## 7. 自动化测试建议

## 8. AI 输出评测标准

包括：完整性、准确性、一致性、可执行性、幻觉风险、人工采纳率。

## 9. 风险测试点

## 10. 质量门禁

## 11. 回归测试清单
{_common_constraints()}
"""


def build_acceptance_criteria_prompt(idea: dict, prd_md: str = "", test_strategy_md: str = "") -> str:
    ctx = ""
    if prd_md:
        ctx += f"\n\n## 已有 PRD（供参考）\n\n{prd_md[:4000]}\n"
    if test_strategy_md:
        ctx += f"\n\n## 已有测试策略（供参考）\n\n{test_strategy_md[:4000]}\n"
    return f"""你是一位资深 QA 负责人，擅长编写可执行、可验证的验收标准。

## 输入信息

- 产品名称：{idea.get('title', '')}
- 产品方向：{idea.get('product_direction', '')}
- 目标用户：{idea.get('target_users', '')}
{ctx}
## 输出要求

请按以下结构输出验收标准（Markdown 格式）：

# 验收标准

## 1. 功能验收标准

## 2. 页面验收标准

## 3. 接口验收标准

## 4. 数据验收标准

## 5. AI 输出验收标准

## 6. 异常场景验收标准

## 7. 日志与追踪验收标准

## 8. 安全与权限验收标准

## 9. 上线前验收标准

每条验收标准必须满足：可判断、可测试、可复现、有明确通过/失败标准。

格式示例：

| 编号 | 验收项 | 前置条件 | 操作步骤 | 预期结果 | 优先级 |
|---|---|---|---|---|---|
{_common_constraints()}
"""


# ══════════════════════════════════════════════════════════════════
#  Phase 2: Artifact → 测试资产 Prompt 模板
# ══════════════════════════════════════════════════════════════════

MAX_TOKENS_MAP["requirement_points_from_artifact"] = 8000
MAX_TOKENS_MAP["test_cases_from_artifact"] = 10000


def build_requirement_points_from_artifact_prompt(artifact_content: str, artifact_type: str) -> str:
    return f"""你是一位资深产品经理兼需求分析师，擅长从产品文档中提取结构化需求点。

## 输入信息

以下是一份 {artifact_type} 产物的内容：

{artifact_content[:8000]}

## 输出要求

请从上述内容中提取所有可识别的需求点，以 **JSON 数组** 格式输出。

每个需求点必须包含以下字段：

```json
[
  {{
    "requirement_title": "需求点标题（简洁明确）",
    "requirement_description": "需求详细描述",
    "business_value": "业务价值说明",
    "source_section": "来源章节/段落标识",
    "priority": "high/medium/low",
    "risk_level": "P0/P1/P2",
    "acceptance_hint": "验收要点提示"
  }}
]
```

{_common_constraints()}

## 额外要求
1. 只输出 JSON 数组，不要输出任何其他文字。
2. 信息不足时在 requirement_description 中标注「基于当前 Artifact 推断」。
3. 每条需求点必须独立、可验证。
4. 至少提取 3 条需求点，最多 20 条。
"""


def build_test_cases_from_artifact_prompt(artifact_content: str, artifact_type: str, requirement_points: list = None) -> str:
    rp_lines = []
    for rp in requirement_points or []:
        rp_lines.append(
            f"- {rp.get('id', '')}: {rp.get('title', '')} | priority={rp.get('priority', '')} | risk={rp.get('risk_level', '')} | {rp.get('description', '')[:160]}"
        )
    rp_context = "\n".join(rp_lines) if rp_lines else "（未提供需求点，请不要编造 requirement_id）"
    return f"""你是一位资深测试架构师，擅长从产品文档中生成结构化测试用例。

## 输入信息

以下是一份 {artifact_type} 产物的内容：

{artifact_content[:8000]}

## 已提取需求点

生成的每条测试用例必须关联下面某一个需求点的 id，填写到 related_requirement_id。

{rp_context}

## 输出要求

请从上述内容中生成测试用例草稿，以 **JSON 数组** 格式输出。

每个测试用例必须包含以下字段：

```json
[
  {{
    "case_title": "测试用例标题",
    "related_requirement_id": "关联需求点 id，例如 RP_PS_xxx",
    "related_requirement_hint": "关联需求点标题或说明",
    "preconditions": "前置条件",
    "test_steps": ["步骤1", "步骤2", "步骤3"],
    "test_data": "测试数据，包含正常值、边界值或异常值",
    "expected_result": "预期结果",
    "priority": "critical/high/medium/low",
    "risk_level": "P0/P1/P2",
    "test_type": "functional/api/ui/abnormal/boundary/security",
    "case_type": "functional/api/ui/abnormal/ai_quality",
    "source_artifact_section": "来源章节/段落标识",
    "automation_suggestion": "建议自动化/建议人工验证及原因",
    "negative_scenario": "异常场景说明",
    "boundary_scenario": "边界场景说明"
  }}
]
```

{_common_constraints()}

## 额外要求
1. 只输出 JSON 数组，不要输出任何其他文字。
2. 信息不足时在 preconditions 中标注「基于当前 Artifact 推断」。
3. 覆盖正常流程、异常流程、边界条件。
4. 至少生成 5 条测试用例，最多 30 条。
5. case_type 必须是以下之一：functional / api / ui / abnormal / ai_quality。
6. 测试用例不能只生成一句话描述，test_steps 至少 3 步。
7. 每条用例必须包含：标题、关联需求点、前置条件、操作步骤、测试数据、预期结果、优先级、风险等级、测试类型、自动化建议、异常场景、边界场景。
"""


# ── 统一入口 ──────────────────────────────────────────────────
PROMPT_BUILDERS = {
    "product_solution": lambda idea, artifacts: build_product_solution_prompt(idea),
    "prd": lambda idea, artifacts: build_prd_prompt(
        idea, artifacts.get("product_solution", "")
    ),
    "prototype": lambda idea, artifacts: build_prototype_prompt(
        idea, artifacts.get("prd", "")
    ),
    "test_strategy": lambda idea, artifacts: build_test_strategy_prompt(
        idea, artifacts.get("prd", ""), artifacts.get("prototype", "")
    ),
    "acceptance_criteria": lambda idea, artifacts: build_acceptance_criteria_prompt(
        idea, artifacts.get("prd", ""), artifacts.get("test_strategy", "")
    ),
}
