from __future__ import annotations

import time
from typing import List

from openai import OpenAI

from app.config import Config

PROMPT_TEMPLATE = """你是一位拥有 10 年经验的 ERP 测试负责人，目前负责“蓝点新生”系统中相关模块的质量保障。
请先阅读需求内容，进行多维度分析，再输出高质量测试用例。务必体现真实工程师的思考过程，而非模板化套用。

【步骤 1：分析说明】
- 先写“测试点分析：”开头的段落，用列表列出关键需求点、潜在风险（排序、状态流转、消息同步、权限、边界、批量、异常、接口/数据库一致性等）。
- 分析要说明为什么该点需要用例覆盖，可包含数据构造、并发、刷新、跨端同步等角度。

【步骤 2：测试用例清单】
- 逐条输出测试用例，结构固定：用例编号、功能点、用例标题、前置条件、测试步骤（Step1/Step2…）、预期结果、优先级。
- 功能点：用一句话概括该用例验证的核心功能（例如："字段默认值验证"、"自动创建产品"、"权限控制"），应比用例标题更简洁，用于分类统计。
- 用例标题：详细描述测试目标（例如："验证通过'废品回收接单'生成采购订单时，字段默认值及状态正确"）。
- 步骤必须具体到界面/接口/数据操作；预期结果需要描述界面、接口、消息或数据库的校验方法，不能为空。
- 必须覆盖正常、异常、边界、批量、权限、排序/状态规则及需求提到的所有业务流程，如涉及外部系统需说明同步验证方式。
- 如发现需求隐含风险点（例如批量操作失败回滚、多角色并发、禁用/启用排序异常等），应主动补充用例。
- 用例数量不少于 12 条，如需求复杂需更多。

【写作要求】
1. 语言自然，像真人写的测试用例；可在步骤或预期中加入必要的说明（例如“通过 SQL 校验”、“查看消息中心”）。
2. 不得省略字段；如无前置条件请写“无”。
3. 如果需求有排序或启/禁规则，需写出数据准备及对比方法，确保能验证准确性。
4. 输出必须按照上述固定结构，方便程序解析。

【需求文档内容】
{requirement}
"""


class AIClient:
    """Wrapper around the OpenAI-compatible SDK with retry logic."""

    def __init__(self, config: Config) -> None:
        self.config = config
        self._client = OpenAI(api_key=config.api_key, base_url=config.base_url)

    def generate(self, text: str, retries: int = 3, delay: float = 3.0) -> str:
        prompt = PROMPT_TEMPLATE.format(requirement=text)
        last_error: Exception | None = None

        for _ in range(retries):
            try:
                response = self._client.chat.completions.create(
                    model=self.config.model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=self.config.temperature,
                )
                return response.choices[0].message.content
            except Exception as exc:  # pragma: no cover - network dependent
                last_error = exc
                time.sleep(delay)
        raise RuntimeError(f"AI 接口调用失败: {last_error}")

    def generate_chunks(self, chunks: List[str]) -> List[str]:
        """Generate responses for multiple chunks."""
        results: List[str] = []
        for part in chunks:
            results.append(self.generate(part))
        return results


