"""
测试点生成器模块
根据需求文本生成结构化测试点列表
"""
from __future__ import annotations

import json
import re
import time
from typing import List, Optional

from openai import OpenAI

from app.config import Config

# 测试点生成的系统提示词
TESTPOINT_SYSTEM_PROMPT = """你是一位拥有 15 年经验的软件测试架构师和测试设计专家。
你的专长是从需求文档中提取和设计全面的测试点。

你的核心能力：
- 深度分析需求，识别所有可测试的功能点
- 从多个维度设计测试点：功能性、非功能性、边界条件、异常场景
- 确保测试点覆盖完整的业务流程和用户场景
- 识别隐含的测试需求和潜在风险点"""

# 测试点生成的提示词模板
TESTPOINT_PROMPT_TEMPLATE = """请根据以下需求文档内容，生成全面的测试点列表。

## 分析要求：
请从以下维度分析需求并生成测试点：

### 1. 功能测试点
- 核心业务功能验证
- 主流程和分支流程
- 用户交互功能
- 数据处理功能

### 2. 边界测试点  
- 输入数据的边界值
- 数量限制的边界
- 时间相关的边界
- 权限边界

### 3. 异常测试点
- 错误输入处理
- 网络异常场景
- 系统异常处理
- 并发冲突场景

### 4. 权限测试点
- 不同角色的权限验证
- 未授权访问控制
- 权限边界验证

### 5. 数据校验测试点
- 必填字段校验
- 数据格式校验
- 数据完整性校验
- 数据一致性校验

## 输出要求：
请严格按照以下 JSON 格式输出，不要输出任何其他内容：

```json
{{
  "analysis": "需求分析摘要（1-2句话概括主要功能和测试重点）",
  "test_points": [
    {{
      "category": "功能测试|边界测试|异常测试|权限测试|数据校验",
      "point": "具体的测试点描述（简洁明确，如：验证订单创建功能）",
      "priority": "高|中|低",
      "description": "测试点的详细说明（可选）"
    }}
  ]
}}
```

## 注意事项：
1. 测试点描述要简洁明确，便于后续生成测试用例
2. 确保覆盖所有5个测试维度
3. 优先级要合理分配：核心功能为高，边界异常为中低
4. 每个维度至少要有2-3个测试点

【需求文档内容】
{requirement}"""

# 带上下文的测试点生成提示词
TESTPOINT_PROMPT_WITH_CONTEXT = """请根据以下需求文档内容，生成测试点列表。

注意：这是同一份需求文档的第 {chunk_index} 部分（共 {total_chunks} 部分）。
{prev_context}

## 分析要求：
基于本段内容，补充生成新的测试点，重点关注：
- 本段特有的业务逻辑和功能
- 与前面部分的关联和集成点
- 避免与已生成测试点重复

请从功能测试、边界测试、异常测试、权限测试、数据校验五个维度分析。

## 输出格式：
请严格按照以下 JSON 格式输出：

```json
{{
  "analysis": "本段需求分析摘要",
  "test_points": [
    {{
      "category": "功能测试|边界测试|异常测试|权限测试|数据校验",
      "point": "具体的测试点描述",
      "priority": "高|中|低",
      "description": "测试点的详细说明（可选）"
    }}
  ]
}}
```

【需求文档内容（第 {chunk_index} 部分）】
{requirement}"""


class TestPointGenerator:
    """测试点生成器"""
    
    def __init__(self, config: Config) -> None:
        self.config = config
        self._client = OpenAI(api_key=config.api_key, base_url=config.base_url)
    
    def generate_test_points(self, requirement_text: str, retries: int = 3, delay: float = 3.0) -> List[str]:
        """
        根据需求文本生成测试点列表
        
        Args:
            requirement_text: 需求文档文本
            retries: 重试次数
            delay: 重试延迟
            
        Returns:
            测试点列表，格式为 ["测试点1", "测试点2", ...]
        """
        prompt = TESTPOINT_PROMPT_TEMPLATE.format(requirement=requirement_text)
        response = self._call_api(prompt, retries, delay)
        return self._parse_test_points(response)
    
    def generate_test_points_with_context(
        self, 
        requirement_text: str, 
        chunk_index: int, 
        total_chunks: int,
        prev_points: Optional[List[str]] = None,
        retries: int = 3, 
        delay: float = 3.0
    ) -> List[str]:
        """
        带上下文生成测试点（用于分块处理）
        
        Args:
            requirement_text: 当前块的需求文本
            chunk_index: 当前块索引
            total_chunks: 总块数
            prev_points: 之前已生成的测试点
            retries: 重试次数
            delay: 重试延迟
            
        Returns:
            测试点列表
        """
        prev_context = ""
        if prev_points:
            prev_context = f"前面部分已生成的测试点：{'、'.join(prev_points[:20])}"
        
        prompt = TESTPOINT_PROMPT_WITH_CONTEXT.format(
            requirement=requirement_text,
            chunk_index=chunk_index,
            total_chunks=total_chunks,
            prev_context=prev_context
        )
        response = self._call_api(prompt, retries, delay)
        return self._parse_test_points(response)
    
    def generate_test_points_for_chunks(self, chunks: List[str]) -> List[str]:
        """
        为多个文本块生成测试点
        
        Args:
            chunks: 文本块列表
            
        Returns:
            合并后的测试点列表
        """
        all_points: List[str] = []
        
        for idx, chunk in enumerate(chunks, 1):
            if len(chunks) == 1:
                points = self.generate_test_points(chunk)
            else:
                points = self.generate_test_points_with_context(
                    chunk, idx, len(chunks), all_points
                )
            all_points.extend(points)
        
        # 去重处理
        return self._deduplicate_points(all_points)
    
    def _call_api(self, prompt: str, retries: int, delay: float) -> str:
        """调用AI API"""
        last_error: Exception | None = None
        
        for attempt in range(retries):
            try:
                response = self._client.chat.completions.create(
                    model=self.config.model,
                    messages=[
                        {"role": "system", "content": TESTPOINT_SYSTEM_PROMPT},
                        {"role": "user", "content": prompt},
                    ],
                    temperature=self.config.temperature,
                )
                return response.choices[0].message.content
            except Exception as exc:
                last_error = exc
                time.sleep(delay * (attempt + 1))
        
        raise RuntimeError(f"测试点生成失败（已重试 {retries} 次）: {last_error}")
    
    def _parse_test_points(self, ai_output: str) -> List[str]:
        """解析AI输出，提取测试点列表"""
        try:
            # 尝试提取JSON
            data = self._extract_json(ai_output)
            if data and "test_points" in data:
                points = []
                for item in data["test_points"]:
                    point = item.get("point", "").strip()
                    if point:
                        points.append(point)
                return points
        except Exception:
            pass
        
        # 如果JSON解析失败，尝试文本解析
        return self._parse_text_points(ai_output)
    
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
        match = re.search(r"\{[\s\S]*\"test_points\"[\s\S]*\}", text)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                pass
        
        return None
    
    def _parse_text_points(self, text: str) -> List[str]:
        """从纯文本中解析测试点"""
        points = []
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            # 查找类似 "验证xxx功能" 的模式
            if any(keyword in line for keyword in ["验证", "测试", "检查", "确认"]):
                # 清理格式
                line = re.sub(r'^[-•\d\.]+\s*', '', line)  # 移除列表标记
                line = re.sub(r'^[：:]\s*', '', line)      # 移除冒号
                if len(line) > 5 and len(line) < 100:     # 合理长度
                    points.append(line)
        
        return points[:20]  # 限制数量
    
    def _deduplicate_points(self, points: List[str]) -> List[str]:
        """测试点去重"""
        unique_points = []
        seen = set()
        
        for point in points:
            # 简单的相似度检查
            normalized = re.sub(r'[^\w\u4e00-\u9fff]', '', point.lower())
            if normalized not in seen and len(normalized) > 3:
                unique_points.append(point)
                seen.add(normalized)
        
        return unique_points