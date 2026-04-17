"""
测试用例生成器模块
根据测试点生成详细的测试用例
"""
from __future__ import annotations

import json
import re
import time
from typing import Dict, List, Optional

from openai import OpenAI

from app.config import Config

# 测试用例生成的系统提示词
TESTCASE_SYSTEM_PROMPT = """你是一位拥有 10 年经验的高级测试工程师和测试用例设计专家。
你的专长是根据测试点设计详细、可执行的测试用例。

你的核心能力：
- 将抽象的测试点转化为具体的测试步骤
- 设计清晰的前置条件和预期结果
- 确保测试用例的可执行性和可重现性
- 覆盖正常流程和异常场景"""

# 测试用例生成的提示词模板
TESTCASE_PROMPT_TEMPLATE = """请根据以下测试点列表，为每个测试点生成详细的测试用例。

## 测试用例设计要求：

### 1. 用例标题
- 简洁明确，体现测试目标
- 格式：验证/测试 + 具体功能/场景

### 2. 前置条件
- 明确测试执行前的系统状态
- 包括数据准备、用户权限、环境配置等

### 3. 操作步骤
- 详细的步骤描述，可重现
- 使用 Step1、Step2 格式
- 精确到具体的界面元素和操作

### 4. 预期结果
- 明确的验证点
- 包括界面反馈、数据变化、系统行为等

## 输出格式：
请严格按照以下 JSON 格式输出，不要输出任何其他内容：

```json
{{
  "test_cases": [
    {{
      "test_point": "对应的测试点",
      "title": "测试用例标题",
      "precondition": "前置条件",
      "steps": "Step1. 具体操作步骤\\nStep2. 下一步操作\\nStep3. 继续操作",
      "expected": "预期结果描述",
      "priority": "高|中|低"
    }}
  ]
}}
```

## 注意事项：
1. 每个测试点对应一个测试用例
2. 步骤要具体可执行，避免模糊描述
3. 预期结果要明确可验证
4. 优先级根据测试点的重要性确定

【测试点列表】
{test_points}"""

# 带上下文的测试用例生成提示词
TESTCASE_PROMPT_WITH_CONTEXT = """请根据以下测试点列表，生成对应的测试用例。

注意：这是第 {batch_index} 批测试点（共 {total_batches} 批）。
{prev_context}

## 设计要求：
- 基于当前批次的测试点生成用例
- 避免与之前批次的用例重复
- 保持用例编号的连续性

## 输出格式：
请严格按照以下 JSON 格式输出：

```json
{{
  "test_cases": [
    {{
      "test_point": "对应的测试点",
      "title": "测试用例标题",
      "precondition": "前置条件",
      "steps": "Step1. 具体操作步骤\\nStep2. 下一步操作",
      "expected": "预期结果描述",
      "priority": "高|中|低"
    }}
  ]
}}
```

【测试点列表（第 {batch_index} 批）】
{test_points}"""


class TestCaseGenerator:
    """测试用例生成器"""
    
    def __init__(self, config: Config) -> None:
        self.config = config
        self._client = OpenAI(api_key=config.api_key, base_url=config.base_url)
    
    def generate_test_cases(self, test_points: List[str], retries: int = 3, delay: float = 3.0) -> List[Dict[str, str]]:
        """
        根据测试点列表生成测试用例
        
        Args:
            test_points: 测试点列表
            retries: 重试次数
            delay: 重试延迟
            
        Returns:
            测试用例列表，每个用例包含：test_point, title, precondition, steps, expected, priority
        """
        if not test_points:
            return []
        
        # 如果测试点太多，分批处理
        if len(test_points) > 10:
            return self._generate_cases_in_batches(test_points, retries, delay)
        
        points_text = '\n'.join(f"{i+1}. {point}" for i, point in enumerate(test_points))
        prompt = TESTCASE_PROMPT_TEMPLATE.format(test_points=points_text)
        response = self._call_api(prompt, retries, delay)
        return self._parse_test_cases(response)
    
    def _generate_cases_in_batches(self, test_points: List[str], retries: int, delay: float) -> List[Dict[str, str]]:
        """分批生成测试用例"""
        batch_size = 8
        all_cases: List[Dict[str, str]] = []
        batches = [test_points[i:i + batch_size] for i in range(0, len(test_points), batch_size)]
        
        for batch_idx, batch_points in enumerate(batches, 1):
            prev_context = ""
            if all_cases:
                prev_titles = [case.get("title", "") for case in all_cases[-5:]]  # 最近5个用例标题
                prev_context = f"前面批次已生成的用例标题：{'、'.join(prev_titles)}"
            
            points_text = '\n'.join(f"{i+1}. {point}" for i, point in enumerate(batch_points))
            prompt = TESTCASE_PROMPT_WITH_CONTEXT.format(
                test_points=points_text,
                batch_index=batch_idx,
                total_batches=len(batches),
                prev_context=prev_context
            )
            
            try:
                response = self._call_api(prompt, retries, delay)
                batch_cases = self._parse_test_cases(response)
                all_cases.extend(batch_cases)
            except Exception as e:
                # 如果某批次失败，记录错误但继续处理其他批次
                print(f"批次 {batch_idx} 生成失败: {e}")
                continue
        
        return all_cases
    
    def _call_api(self, prompt: str, retries: int, delay: float) -> str:
        """调用AI API"""
        last_error: Exception | None = None
        
        for attempt in range(retries):
            try:
                response = self._client.chat.completions.create(
                    model=self.config.model,
                    messages=[
                        {"role": "system", "content": TESTCASE_SYSTEM_PROMPT},
                        {"role": "user", "content": prompt},
                    ],
                    temperature=self.config.temperature,
                )
                return response.choices[0].message.content
            except Exception as exc:
                last_error = exc
                time.sleep(delay * (attempt + 1))
        
        raise RuntimeError(f"测试用例生成失败（已重试 {retries} 次）: {last_error}")
    
    def _parse_test_cases(self, ai_output: str) -> List[Dict[str, str]]:
        """解析AI输出，提取测试用例列表"""
        try:
            # 尝试提取JSON
            data = self._extract_json(ai_output)
            if data and "test_cases" in data:
                cases = []
                for item in data["test_cases"]:
                    case = {
                        "test_point": str(item.get("test_point", "")).strip(),
                        "title": str(item.get("title", "")).strip(),
                        "precondition": str(item.get("precondition", "无")).strip(),
                        "steps": str(item.get("steps", "")).strip(),
                        "expected": str(item.get("expected", "")).strip(),
                        "priority": str(item.get("priority", "中")).strip()
                    }
                    # 只保留有效的用例
                    if case["title"] and case["steps"]:
                        cases.append(case)
                return cases
        except Exception:
            pass
        
        # 如果JSON解析失败，尝试文本解析
        return self._parse_text_cases(ai_output)
    
    def _extract_json(self, text: str) -> Optional[dict]:
        """从文本中提取JSON"""
        # 尝试代码块
        match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1).strip())
            except json.JSONDecodeError:
                pass
        
        # 尝试整个文本
        try:
            return json.loads(text.strip())
        except json.JSONDecodeError:
            pass
        
        # 尝试查找JSON对象
        match = re.search(r"\{[\s\S]*\"test_cases\"[\s\S]*\}", text)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                pass
        
        return None
    
    def _parse_text_cases(self, text: str) -> List[Dict[str, str]]:
        """从纯文本中解析测试用例（备用方案）"""
        cases = []
        lines = text.split('\n')
        current_case = {}
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # 检测各个字段
            if line.startswith(('用例标题', '标题', 'Title')):
                if current_case and current_case.get('title'):
                    cases.append(current_case)
                    current_case = {}
                current_case['title'] = line.split(':', 1)[-1].strip()
            elif line.startswith(('前置条件', 'Precondition')):
                current_case['precondition'] = line.split(':', 1)[-1].strip()
            elif line.startswith(('操作步骤', '测试步骤', 'Steps')):
                current_case['steps'] = line.split(':', 1)[-1].strip()
            elif line.startswith(('预期结果', 'Expected')):
                current_case['expected'] = line.split(':', 1)[-1].strip()
            elif line.startswith(('优先级', 'Priority')):
                current_case['priority'] = line.split(':', 1)[-1].strip()
            elif line.startswith('Step'):
                # 步骤内容
                if 'steps' in current_case:
                    current_case['steps'] += '\n' + line
                else:
                    current_case['steps'] = line
        
        # 添加最后一个用例
        if current_case and current_case.get('title'):
            cases.append(current_case)
        
        # 标准化字段
        for case in cases:
            case.setdefault('test_point', case.get('title', ''))
            case.setdefault('precondition', '无')
            case.setdefault('priority', '中')
        
        return cases