"""
AI Dev Studio — Prompt 模板
5 个模板：dev_plan / api_design / db_design / file_impact / test_plan
"""

# ── 每类 prompt 对应的 max_tokens ────────────────────────────────
MAX_TOKENS_MAP = {
    "dev_plan": 10000,
    "api_design": 10000,
    "db_design": 8000,
    "file_impact": 8000,
    "test_plan": 10000,
    "patch_draft": 12000,
    "patch_review": 12000,
}

ARTIFACT_TITLE_MAP = {
    "dev_plan": "开发计划",
    "api_design": "API 设计",
    "db_design": "数据库设计",
    "file_impact": "影响文件分析",
    "test_plan": "测试计划",
    "patch_draft": '补丁草稿',
    "patch_review": '补丁评审',
}

RUN_TYPES = list(MAX_TOKENS_MAP.keys())


def _common_constraints() -> str:
    return """
## 共同约束
1. 不允许编造当前项目不存在的文件。
2. 如果无法确认文件路径，必须标注"需人工确认"。
3. 不允许输出自动执行 git / 删除 / 覆盖文件的命令。
4. 不允许要求自动合并代码。
5. 输出必须适合研发评审。
6. 输出必须包含测试策略和验收标准。
7. 必须区分 P0 / P1 / P2 优先级。
8. 必须标注风险和回滚思路。
9. 不允许输出 API Key、Token、Cookie、密码等敏感信息。
"""


def build_dev_plan_prompt(context: str, task_title: str) -> str:
    return f"""你是一位资深全栈工程师兼技术负责人，擅长将产品需求转化为可执行的开发计划。

## 任务
基于以下需求上下文，生成完整的开发计划。

## 任务标题
{task_title}

## 需求上下文
{context[:8000]}

## 输出要求

请按以下结构输出完整开发计划（Markdown 格式）：

# 开发计划

## 1. 结论

## 2. 需求来源

## 3. 目标

## 4. 本期范围

## 5. 不做范围

## 6. 总体技术方案

## 7. 模块拆分

## 8. 开发任务拆解

| 优先级 | 任务 | 说明 | 预估复杂度 | 依赖 | 验收标准 |
|---|---|---|---|---|---|

## 9. API 设计概览

## 10. 数据库设计概览

## 11. 前端改造概览

## 12. 后端改造概览

## 13. 测试计划

## 14. 风险与回滚

## 15. 下一步建议
{_common_constraints()}
"""


def build_api_design_prompt(context: str, task_title: str) -> str:
    return f"""你是一位资深后端架构师，擅长设计 RESTful API。

## 任务
基于以下需求上下文，生成详细的 API 设计文档。

## 任务标题
{task_title}

## 需求上下文
{context[:8000]}

## 输出要求

请按以下结构输出 API 设计（Markdown 格式）：

# API 设计

## 1. 接口总览

| 方法 | 路径 | 用途 | 权限 | 状态 |
|---|---|---|---|---|

## 2. 接口详情

每个接口包含：
- 方法
- 路径
- 请求参数（含示例）
- 返回结构（含示例）
- 错误码
- 权限要求
- 幂等性
- 日志字段
- 验收标准

## 3. 异常处理

## 4. 安全要求

## 5. 测试点
{_common_constraints()}
"""


def build_db_design_prompt(context: str, task_title: str) -> str:
    return f"""你是一位资深数据库架构师，擅长数据库建模和迁移方案设计。

## 任务
基于以下需求上下文，生成数据库设计文档。

## 任务标题
{task_title}

## 需求上下文
{context[:8000]}

## 输出要求

请按以下结构输出数据库设计（Markdown 格式）：

# 数据库设计

## 1. 新增表

## 2. 修改表

## 3. 字段说明

## 4. 索引建议

## 5. 兼容迁移方案

## 6. 数据风险

## 7. 回滚方案

## 8. 验收标准
{_common_constraints()}
"""


def build_file_impact_prompt(context: str, task_title: str) -> str:
    return f"""你是一位资深全栈工程师，擅长代码影响分析和变更风险评估。

## 任务
基于以下需求上下文，分析可能影响的文件和变更范围。

## 任务标题
{task_title}

## 需求上下文
{context[:8000]}

## 输出要求

请按以下结构输出影响文件分析（Markdown 格式）：

# 影响文件分析

## 1. 结论

## 2. 可能新增文件

| 文件 | 作用 | 是否必须 | 风险 |
|---|---|---|---|

## 3. 可能修改文件

| 文件 | 修改点 | 影响范围 | 风险 | 是否需人工确认 |
|---|---|---|---|---|

## 4. 不建议修改的文件

## 5. 依赖关系

## 6. 风险点

## 7. 验收建议

注意：基于项目约定推断，需人工确认实际文件路径。
{_common_constraints()}
"""


def build_test_plan_prompt(context: str, task_title: str) -> str:
    return f"""你是一位资深测试架构师，擅长制定全面的测试计划和验收方案。

## 任务
基于以下需求上下文，生成详细的开发验收测试计划。

## 任务标题
{task_title}

## 需求上下文
{context[:8000]}

## 输出要求

请按以下结构输出测试计划（Markdown 格式）：

# 开发验收测试计划

## 1. 测试目标

## 2. 测试范围

## 3. 不测范围

## 4. 功能测试

## 5. 接口测试

## 6. 数据库测试

## 7. 异常测试

## 8. 回归测试

## 9. 自动化测试建议

## 10. 验收脚本建议

## 11. 上线前检查

## 12. 回滚验证
{_common_constraints()}
"""


def build_patch_draft_prompt(context: str, task_title: str, candidate_files: str = "") -> str:
    return f"""你是一位资深全栈工程师，擅长基于需求和影响分析生成精确的代码补丁草稿。

## 重要声明
- 这是 **补丁草稿**，仅供人工审查参考
- **不会自动应用**，不会修改任何代码文件
- **必须由人工确认后手动实施**
- 所有修改建议需人工评估风险后决定是否采纳

## 任务标题
{task_title}

## 需求上下文
{context[:6000]}

## 候选影响文件
{candidate_files}

## 输出要求

请按以下结构输出（Markdown 格式）：

# Patch Draft 草稿

## 1. 声明

> **重要提示**：本补丁草稿由 AI 生成，不会自动应用任何修改。
> 所有代码变更必须由开发者人工审查、确认并手动实施。
> AI 可能产生不准确或不完整的代码，请务必仔细验证。

## 2. 需求来源

- 任务: {task_title}
- 来源产物类型
- 影响文件来源

## 3. 候选文件总览

| # | 文件路径 | 修改意图 | 风险等级 | 需人工确认 |
|---|---|---|---|---|
| 1 | path/to/file | 修改原因 | 高/中/低 | 是/否 |

## 4. 补丁草稿

按文件逐个输出 unified diff 格式的补丁草稿：

### 文件: path/to/file.py

**修改意图**: xxx
**风险等级**: 中
**置信度**: 高/中/低

```diff
--- a/path/to/file.py
+++ b/path/to/file.py
@@ -line,count +line,count @@
 context line
-old line
+new line
 context line
```

**修改说明**: 具体说明这段改动的作用

## 5. 新增文件建议

如果需要新增文件，列出建议的文件路径、职责和完整内容框架。

## 6. 风险评估

- 总体风险等级
- 高风险改动数量
- 建议测试重点
- 回滚策略

## 7. 实施建议

- 建议的实施顺序
- 依赖关系
- 验证步骤

## 8. 注意事项

- 列出实施时需特别注意的事项
- 可能的副作用
- 需要额外验证的点

{_common_constraints()}
"""


def build_patch_review_prompt(patch_content: str, task_title: str,
                              file_impact_ctx: str = "", test_plan_ctx: str = "",
                              strict_mode: bool = True,
                              include_test_mapping: bool = True,
                              include_security_check: bool = True) -> str:
    strict_note = "\n- **严格模式已开启**：任何阻塞问题必须导致 should_apply=false" if strict_mode else ""
    security_section = """
## 6. 安全检查

必须检查：
- 是否包含 API Key / Token / Cookie / Authorization
- 是否涉及 .env / secret / password 文件
- 是否包含 rm / del / format / drop table 等危险操作
- 是否包含 git apply / git commit / git push 等自动执行命令
- 是否涉及权限绕过
- 是否输出敏感日志
""" if include_security_check else ""
    test_section = """
## 7. 测试映射

| 修改点 | 建议测试 | 测试类型 | 是否必须 |
|---|---|---|---|

测试类型：unit / api / ui / integration / regression / security / db_migration
""" if include_test_mapping else ""
    fi_block = f"\n## 关联影响文件分析\n{file_impact_ctx[:2000]}" if file_impact_ctx else ""
    tp_block = f"\n## 关联测试计划\n{test_plan_ctx[:2000]}" if test_plan_ctx else ""

    return f"""你是一位资深代码评审专家，擅长识别代码补丁中的风险、安全问题和质量缺陷。

## 重要声明
- 这是对 Patch Draft 的评审，不是自动应用
- 评审结果仅供人工参考{strict_note}

## 任务标题
{task_title}

## Patch Draft 内容
{patch_content[:8000]}
{fi_block}
{tp_block}

## 输出要求

请按以下结构输出（Markdown 格式）：

# Patch Draft 评审报告

## 1. 结论

必须包含：
- **是否建议人工应用该 Patch**: true/false
- **风险等级**: low / medium / high
- **评审分数**: 0.0 ~ 1.0
- **是否存在阻塞问题**: 是/否
- **下一步建议**

同时请在评审报告末尾输出以下 JSON 块（用于结构化解析）：

```json
{{
  "risk_level": "low|medium|high",
  "review_score": 0.0,
  "should_apply": true,
  "blocking_issues": [],
  "warnings": [],
  "test_suggestions": [],
  "manual_checklist": []
}}
```

## 2. Patch 来源

- 任务: {task_title}
- 关联产物

## 3. 主要修改点识别

| 文件 | 修改意图 | 风险等级 | 是否需人工确认 |
|---|---|---|---|

## 4. 阻塞问题

| 编号 | 问题 | 严重级别 | 原因 | 建议 |
|---|---|---|---|---|

## 5. 警告项

| 编号 | 警告 | 风险 | 建议 |
|---|---|---|---|
{security_section}
{test_section}

## 8. 应用前人工确认清单

- [ ] 确认修改文件路径正确
- [ ] 确认 Patch 内容可人工理解
- [ ] 确认没有敏感信息
- [ ] 确认没有危险命令
- [ ] 确认数据库修改有迁移和回滚方案
- [ ] 确认接口修改有兼容性说明
- [ ] 确认测试计划覆盖核心风险
- [ ] 确认由开发人员手工应用，不自动执行

## 9. 建议执行的测试

只允许输出建议，不允许执行命令。

{_common_constraints()}
"""


# ── 统一入口 ────────────────────────────────────────────────────
PROMPT_BUILDERS = {
    "dev_plan": build_dev_plan_prompt,
    "api_design": build_api_design_prompt,
    "db_design": build_db_design_prompt,
    "file_impact": build_file_impact_prompt,
    "test_plan": build_test_plan_prompt,
    "patch_draft": build_patch_draft_prompt,
    "patch_review": build_patch_review_prompt,
}
