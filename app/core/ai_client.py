from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass, field
from typing import List, Optional

from openai import OpenAI

from app.config import Config

SYSTEM_PROMPT = """你是一位拥有 10 年经验的 ERP/业务系统高级测试架构师。
你的工作方式：先深度分析需求，再系统性地生成测试用例。

你的核心能力：
- 识别隐含需求和边界条件
- 发现需求文档中未明确说明但实际存在的业务规则
- 从用户视角和系统视角双重审视功能
- 关注数据流转的完整性和一致性"""

PROMPT_TEMPLATE = """请根据以下需求文档内容，按两个阶段工作：

## 第一阶段：需求深度分析
请先分析以下维度（写在 analysis 字段中）：
1. 核心业务流程有哪些？主流程和分支流程分别是什么？
2. 关键状态流转：有哪些状态？状态之间的转换条件和约束？
3. 数据校验规则：必填字段、格式校验、范围校验、唯一性约束
4. 权限和角色：不同角色的操作权限差异
5. 异常场景：网络异常、并发冲突、数据不一致、批量操作边界
6. 业务规则：计算逻辑、关联影响、级联操作

## 第二阶段：系统性生成测试用例
基于分析结果，确保覆盖以下维度（每个维度至少 1-2 条）：
- 正向流程验证（主流程 + 分支流程）
- 必填字段校验（空值、空格、超长）
- 数据格式校验（类型错误、特殊字符、SQL注入）
- 边界值测试（最大值、最小值、临界值）
- 状态流转测试（正常流转 + 非法流转）
- 权限控制测试（有权限 + 无权限）
- 批量操作测试（空批量、单条、多条、超大批量）
- 关联数据一致性（修改/删除后关联数据的变化）
- 并发操作（同时编辑、重复提交）
- 回滚和撤销（操作失败后数据恢复）

【输出格式】
请严格按照以下 JSON 格式输出，不要输出任何其他内容：

```json
{{
  "analysis": "需求分析摘要（覆盖上述6个分析维度，每个维度1-2句话）",
  "coverage_dimensions": ["正向流程", "字段校验", "边界值", ...],
  "cases": [
    {{
      "function_point": "功能点名称（简短概括，如'订单创建-必填校验'）",
      "title": "用例标题（具体描述验证什么）",
      "precondition": "前置条件（具体到数据状态和用户角色）",
      "steps": "Step1. 具体操作（精确到按钮/字段/页面）\\nStep2. xxx\\nStep3. xxx",
      "expected": "预期结果（具体到提示信息内容、数据变化、页面跳转）",
      "priority": "高/中/低",
      "dimension": "覆盖维度"
    }}
  ]
}}
```

【需求文档内容】
{requirement}"""

PROMPT_TEMPLATE_WITH_CONTEXT = """请根据以下需求文档内容，按两个阶段工作。

注意：这是同一份需求文档的第 {chunk_index} 部分（共 {total_chunks} 部分）。
{prev_context}

## 第一阶段：需求深度分析
分析本段新增的业务逻辑、字段、状态、规则，重点关注与前面部分的关联关系。

## 第二阶段：补充测试用例
基于本段内容生成新的测试用例，注意：
- 不要重复前面已覆盖的用例
- 重点关注本段特有的业务逻辑
- 如果本段涉及与前面部分的交互，生成跨模块集成测试用例
- 确保覆盖维度的互补性（前面缺少的维度优先补充）

【输出格式】
请严格按照以下 JSON 格式输出，不要输出任何其他内容：

```json
{{
  "analysis": "本段需求分析摘要",
  "coverage_dimensions": ["本段覆盖的维度列表"],
  "cases": [
    {{
      "function_point": "功能点名称",
      "title": "用例标题",
      "precondition": "前置条件",
      "steps": "Step1. xxx\\nStep2. xxx",
      "expected": "预期结果",
      "priority": "高/中/低",
      "dimension": "覆盖维度"
    }}
  ]
}}
```

【需求文档内容（第 {chunk_index} 部分）】
{requirement}"""


@dataclass
class TokenUsage:
    """Track token usage across API calls."""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    api_calls: int = 0
    total_time: float = 0.0

    def add(self, prompt: int, completion: int, elapsed: float) -> None:
        self.prompt_tokens += prompt
        self.completion_tokens += completion
        self.total_tokens += prompt + completion
        self.api_calls += 1
        self.total_time += elapsed

    def summary(self) -> str:
        avg = self.total_time / self.api_calls if self.api_calls else 0
        return (f"API调用 {self.api_calls} 次，"
                f"Token: {self.total_tokens}（输入 {self.prompt_tokens} + 输出 {self.completion_tokens}），"
                f"耗时 {self.total_time:.1f}s（平均 {avg:.1f}s/次）")


class AIClient:
    """Wrapper around the OpenAI-compatible SDK with retry, context awareness, and token tracking."""

    def __init__(self, config: Config) -> None:
        self.config = config
        self._client = OpenAI(api_key=config.api_key, base_url=config.base_url)
        self.usage = TokenUsage()

    def generate(self, text: str, retries: int = 3, delay: float = 3.0) -> str:
        prompt = PROMPT_TEMPLATE.format(requirement=text)
        return self._call_api(prompt, retries, delay)

    def generate_with_context(self, text: str, chunk_index: int, total_chunks: int,
                              prev_titles: Optional[List[str]] = None,
                              prev_dimensions: Optional[List[str]] = None,
                              retries: int = 3, delay: float = 3.0) -> str:
        prev_parts = []
        if prev_titles:
            prev_parts.append(f"前面部分已生成的用例标题：{'、'.join(prev_titles[:30])}")
        if prev_dimensions:
            prev_parts.append(f"前面已覆盖的维度：{'、'.join(sorted(set(prev_dimensions)))}")
        prompt = PROMPT_TEMPLATE_WITH_CONTEXT.format(
            requirement=text, chunk_index=chunk_index,
            total_chunks=total_chunks, prev_context="\n".join(prev_parts))
        return self._call_api(prompt, retries, delay)

    def _call_api(self, prompt: str, retries: int, delay: float) -> str:
        last_error: Exception | None = None
        for attempt in range(retries):
            try:
                t0 = time.time()
                response = self._client.chat.completions.create(
                    model=self.config.model,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": prompt},
                    ],
                    temperature=self.config.temperature,
                )
                elapsed = time.time() - t0
                # Track token usage
                if response.usage:
                    self.usage.add(
                        response.usage.prompt_tokens or 0,
                        response.usage.completion_tokens or 0,
                        elapsed)
                else:
                    self.usage.add(0, 0, elapsed)
                return response.choices[0].message.content
            except Exception as exc:
                last_error = exc
                time.sleep(delay * (attempt + 1))
        raise RuntimeError(f"AI 接口调用失败（已重试 {retries} 次）: {last_error}")

    def generate_chunks(self, chunks: List[str]) -> List[str]:
        results: List[str] = []
        prev_titles: List[str] = []
        prev_dimensions: List[str] = []
        for idx, part in enumerate(chunks, 1):
            if len(chunks) == 1:
                result = self.generate(part)
            else:
                result = self.generate_with_context(
                    part, idx, len(chunks), prev_titles, prev_dimensions)
            results.append(result)
            try:
                titles, dims = _extract_context(result)
                prev_titles.extend(titles)
                prev_dimensions.extend(dims)
            except Exception:
                pass
        return results


def _extract_context(ai_output: str) -> tuple[List[str], List[str]]:
    titles, dimensions = [], []
    data = _extract_json(ai_output)
    if data:
        for case in data.get("cases", []):
            t = case.get("title", "")
            if t:
                titles.append(t)
            d = case.get("dimension", "")
            if d:
                dimensions.append(d)
        dimensions.extend(data.get("coverage_dimensions", []))
    return titles, dimensions


def _extract_json(text: str) -> Optional[dict]:
    m = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(1).strip())
        except json.JSONDecodeError:
            pass
    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        pass
    m = re.search(r"\{[\s\S]*\"cases\"[\s\S]*\}", text)
    if m:
        try:
            return json.loads(m.group(0))
        except json.JSONDecodeError:
            pass
    return None
