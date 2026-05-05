#!/usr/bin/env python3
"""直接测试文件上传生成接口，查看AI原始响应"""
import sys, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.document_parser import parse_document_structured
from ai.ai_client import get_ai_client

# 用一个小的测试文本
TEST_TEXT = """
付款单功能：
1. 显示付款单数据，页签分全部、待审核、已审核
2. 主要功能有查询、新增、编辑、审核、删除
3. 新增付款单需选择供应商、输入金额、选择用途
4. 审核后不可编辑删除
"""

client = get_ai_client()
print(f"AI client: {type(client).__name__}")

prompt = f"""请为以下需求生成3个测试用例，返回JSON数组格式：

需求：
{TEST_TEXT}

模块：付款单

返回格式（必须是有效的JSON数组）：
[
  {{
    "title": "测试用例标题",
    "module": "付款单",
    "priority": "high/medium/low",
    "steps": ["步骤1", "步骤2", "步骤3"],
    "expected": "预期结果描述"
  }}
]

注意：只返回JSON数组，不要有其他文字。
"""

print("--- Calling AI ---")
response = client.generate_text(
    prompt=prompt,
    system_prompt="你是一个专业的测试工程师。",
    temperature=0.3,
    max_tokens=2000
)

print(f"--- AI Response (len={len(response)}) ---")
print(response[:2000])
print("--- End ---")

# Try parse
try:
    if '```json' in response:
        response = response.split('```json')[1].split('```')[0].strip()
    elif '```' in response:
        response = response.split('```')[1].split('```')[0].strip()
    start = response.find('[')
    end = response.rfind(']') + 1
    if start != -1 and end > 0:
        data = json.loads(response[start:end])
        print(f"\n✅ 解析成功: {len(data)} 条用例")
    else:
        print(f"\n❌ 未找到JSON数组")
except Exception as e:
    print(f"\n❌ 解析失败: {e}")
