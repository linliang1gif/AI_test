#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI 路由模块 - 提供 AI 生成测试用例和脚本的接口
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import json

from ai.ai_client import get_ai_client

router = APIRouter()


class TestCaseGenerate(BaseModel):
    """测试用例生成请求"""
    requirement: str
    module: Optional[str] = "默认模块"
    count: Optional[int] = 5
    provider: Optional[str] = None


class TestCase(BaseModel):
    """测试用例"""
    title: str
    module: Optional[str] = None
    priority: Optional[str] = None
    steps: List[str]
    expected: str


class ScriptGenerate(BaseModel):
    """测试脚本生成请求"""
    testcase: TestCase
    framework: Optional[str] = "pytest"
    provider: Optional[str] = None


@router.post("/ai/generate-testcases")
async def generate_testcases(request: TestCaseGenerate):
    """
    AI 生成测试用例
    
    根据需求文档使用 AI 生成测试用例
    """
    try:
        # 获取 AI 客户端
        use_ollama = request.provider == "ollama" if request.provider else None
        use_mock = request.provider == "mock" if request.provider else None
        
        client = get_ai_client(use_ollama=use_ollama, use_mock=use_mock)
        
        # 构建提示词
        prompt = f"""请为以下需求生成{request.count}个测试用例，返回JSON数组格式：

需求：
{request.requirement}

模块：{request.module}

返回格式（必须是有效的JSON数组）：
[
  {{
    "title": "测试用例标题",
    "module": "{request.module}",
    "priority": "high/medium/low",
    "steps": ["步骤1", "步骤2", "步骤3"],
    "expected": "预期结果描述"
  }}
]

注意：
1. 只返回JSON数组，不要有其他文字
2. 确保JSON格式正确
3. 每个测试用例都要有完整的字段
"""
        
        system_prompt = "你是一个专业的测试工程师，擅长根据需求生成高质量的测试用例。"
        
        # 调用 AI
        response = client.generate_text(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.3,
            max_tokens=2000
        )
        
        # 解析响应
        try:
            # 提取 JSON 部分
            if '```json' in response:
                response = response.split('```json')[1].split('```')[0].strip()
            elif '```' in response:
                response = response.split('```')[1].split('```')[0].strip()
            
            # 查找 JSON 数组
            start = response.find('[')
            end = response.rfind(']') + 1
            
            if start != -1 and end > 0:
                json_str = response[start:end]
                testcases = json.loads(json_str)
            else:
                # 如果没有找到数组，尝试直接解析
                testcases = json.loads(response)
            
            # 确保是列表
            if not isinstance(testcases, list):
                testcases = [testcases]
            
            return {
                "success": True,
                "testcases": testcases,
                "count": len(testcases)
            }
            
        except json.JSONDecodeError as e:
            # JSON 解析失败，返回默认测试用例
            print(f"JSON 解析失败: {e}")
            print(f"原始响应: {response[:500]}")
            
            return {
                "success": True,
                "testcases": [
                    {
                        "title": "基本功能测试",
                        "module": request.module,
                        "priority": "high",
                        "steps": ["执行基本操作", "验证结果"],
                        "expected": "功能正常"
                    }
                ],
                "count": 1,
                "warning": "AI 响应格式不正确，返回默认测试用例"
            }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成测试用例失败: {str(e)}")


@router.post("/ai/generate-script")
async def generate_script(request: ScriptGenerate):
    """
    AI 生成测试脚本
    
    根据测试用例使用 AI 生成自动化测试脚本
    """
    try:
        # 获取 AI 客户端
        use_ollama = request.provider == "ollama" if request.provider else None
        use_mock = request.provider == "mock" if request.provider else None
        
        client = get_ai_client(use_ollama=use_ollama, use_mock=use_mock)
        
        # 构建提示词
        steps_text = "\n".join([f"{i+1}. {step}" for i, step in enumerate(request.testcase.steps)])
        
        prompt = f"""请为以下测试用例生成{request.framework}自动化测试脚本：

测试用例：
标题：{request.testcase.title}
模块：{request.testcase.module}
优先级：{request.testcase.priority}

测试步骤：
{steps_text}

预期结果：
{request.testcase.expected}

要求：
1. 使用{request.framework}框架
2. 包含必要的导入语句
3. 包含测试类和测试方法
4. 添加适当的断言
5. 添加注释说明
6. 代码要完整可运行

请直接返回Python代码，不要有其他说明文字。
"""
        
        system_prompt = f"你是一个专业的测试开发工程师，擅长编写{request.framework}自动化测试脚本。"
        
        # 调用 AI
        response = client.generate_text(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.2,
            max_tokens=1500
        )
        
        # 提取代码部分
        if '```python' in response:
            script = response.split('```python')[1].split('```')[0].strip()
        elif '```' in response:
            script = response.split('```')[1].split('```')[0].strip()
        else:
            script = response.strip()
        
        return {
            "success": True,
            "script": script,
            "framework": request.framework
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成测试脚本失败: {str(e)}")


@router.get("/ai/providers")
async def get_ai_providers():
    """
    获取可用的 AI 提供商列表
    """
    from config.config import get_config
    
    config = get_config()
    
    providers = [
        {
            "id": "ollama",
            "name": "Ollama (本地)",
            "status": "available",
            "model": config.ai.default_model if config.ai.default_provider == "ollama" else "qwen2.5-coder:latest"
        },
        {
            "id": "deepseek",
            "name": "DeepSeek",
            "status": "available" if config.ai.deepseek_api_key else "unavailable",
            "model": "deepseek-chat"
        },
        {
            "id": "openai",
            "name": "OpenAI",
            "status": "available" if config.ai.openai_api_key else "unavailable",
            "model": "gpt-3.5-turbo"
        },
        {
            "id": "mock",
            "name": "Mock (测试)",
            "status": "available",
            "model": "mock"
        }
    ]
    
    return {
        "providers": providers,
        "default": config.ai.default_provider
    }
