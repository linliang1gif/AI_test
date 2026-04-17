#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Mock AI客户端 - 用于测试和演示"""

import json
import os
import requests
from typing import Dict, Any, List

class MockAIClient:
    """Mock AI客户端"""

    def generate_text(self, prompt: str, system_prompt: str = None, **kwargs) -> str:
        """生成模拟文本响应"""
        if "测试策略" in prompt:
            return """
# 测试策略

## 1. 测试范围
- 功能测试
- 接口测试
- 性能测试

## 2. 测试方法
- 黑盒测试
- 自动化测试

## 3. 测试重点
- 核心业务流程
- 异常场景处理
"""
        elif "模块拆分" in prompt or "功能模块" in prompt:
            return json.dumps({
                "modules": [
                    {
                        "name": "用户管理模块",
                        "description": "负责用户注册、登录、信息管理等功能",
                        "functions": ["用户注册", "用户登录", "用户信息管理", "密码管理"],
                        "dependencies": [],
                        "priority": "高"
                    },
                    {
                        "name": "权限管理模块",
                        "description": "负责用户权限控制和访问管理",
                        "functions": ["角色管理", "权限分配", "访问控制"],
                        "dependencies": ["用户管理模块"],
                        "priority": "高"
                    },
                    {
                        "name": "数据管理模块",
                        "description": "负责数据的增删改查和数据处理",
                        "functions": ["数据录入", "数据查询", "数据导出", "数据统计"],
                        "dependencies": ["用户管理模块", "权限管理模块"],
                        "priority": "中"
                    }
                ]
            }, ensure_ascii=False)

        # 注意: 场景生成要在测试点之前判断,因为场景prompt中也包含"测试点"
        elif "测试场景" in prompt or "场景矩阵" in prompt:
            return json.dumps({
                "scenarios": [
                    {
                        "name": "正常用户注册场景",
                        "input_data": "有效数据",
                        "user_state": "未登录",
                        "system_state": "正常运行",
                        "network": "正常网络",
                        "device": "Chrome浏览器",
                        "data_state": "数据不存在",
                        "expected_result": "注册成功，返回用户信息",
                        "priority": "高"
                    },
                    {
                        "name": "重复注册场景",
                        "input_data": "已存在的邮箱",
                        "user_state": "未登录",
                        "system_state": "正常运行",
                        "network": "正常网络",
                        "device": "Chrome浏览器",
                        "data_state": "数据存在",
                        "expected_result": "提示邮箱已被注册",
                        "priority": "高"
                    },
                    {
                        "name": "无效数据注册场景",
                        "input_data": "无效数据",
                        "user_state": "未登录",
                        "system_state": "正常运行",
                        "network": "正常网络",
                        "device": "Chrome浏览器",
                        "data_state": "数据不存在",
                        "expected_result": "提示数据格式错误",
                        "priority": "中"
                    },
                    {
                        "name": "边界数据注册场景",
                        "input_data": "边界数据",
                        "user_state": "未登录",
                        "system_state": "正常运行",
                        "network": "正常网络",
                        "device": "Chrome浏览器",
                        "data_state": "数据不存在",
                        "expected_result": "系统正确处理边界情况",
                        "priority": "中"
                    },
                    {
                        "name": "网络异常注册场景",
                        "input_data": "有效数据",
                        "user_state": "未登录",
                        "system_state": "正常运行",
                        "network": "网络中断",
                        "device": "Chrome浏览器",
                        "data_state": "数据不存在",
                        "expected_result": "提示网络连接失败",
                        "priority": "中"
                    }
                ]
            }, ensure_ascii=False)

        elif "测试点" in prompt:
            return json.dumps({
                "testpoints": [
                    {
                        "category": "功能测试",
                        "name": "用户注册功能验证",
                        "description": "验证用户注册流程是否正常工作",
                        "priority": "高",
                        "complexity": "中等"
                    },
                    {
                        "category": "功能测试",
                        "name": "用户登录功能验证",
                        "description": "验证用户登录流程是否正常工作",
                        "priority": "高",
                        "complexity": "中等"
                    },
                    {
                        "category": "边界测试",
                        "name": "用户注册边界条件测试",
                        "description": "验证用户注册在边界条件下的行为",
                        "priority": "中",
                        "complexity": "中等"
                    },
                    {
                        "category": "异常测试",
                        "name": "用户注册异常处理测试",
                        "description": "验证用户注册的异常处理能力",
                        "priority": "中",
                        "complexity": "中等"
                    },
                    {
                        "category": "权限测试",
                        "name": "用户权限控制测试",
                        "description": "验证用户权限控制机制",
                        "priority": "高",
                        "complexity": "复杂"
                    }
                ]
            }, ensure_ascii=False)

        elif "测试场景" in prompt or "场景矩阵" in prompt:
            print(f"  [Mock] 匹配到场景生成,返回场景数据")
            return json.dumps({
                "scenarios": [
                    {
                        "name": "正常用户注册场景",
                        "input_data": "有效数据",
                        "user_state": "未登录",
                        "system_state": "正常运行",
                        "network": "正常网络",
                        "device": "Chrome浏览器",
                        "data_state": "数据不存在",
                        "expected_result": "注册成功，返回用户信息",
                        "priority": "高"
                    },
                    {
                        "name": "重复注册场景",
                        "input_data": "已存在的邮箱",
                        "user_state": "未登录",
                        "system_state": "正常运行",
                        "network": "正常网络",
                        "device": "Chrome浏览器",
                        "data_state": "数据存在",
                        "expected_result": "提示邮箱已被注册",
                        "priority": "高"
                    },
                    {
                        "name": "无效数据注册场景",
                        "input_data": "无效数据",
                        "user_state": "未登录",
                        "system_state": "正常运行",
                        "network": "正常网络",
                        "device": "Chrome浏览器",
                        "data_state": "数据不存在",
                        "expected_result": "提示数据格式错误",
                        "priority": "中"
                    },
                    {
                        "name": "边界数据注册场景",
                        "input_data": "边界数据",
                        "user_state": "未登录",
                        "system_state": "正常运行",
                        "network": "正常网络",
                        "device": "Chrome浏览器",
                        "data_state": "数据不存在",
                        "expected_result": "系统正确处理边界情况",
                        "priority": "中"
                    },
                    {
                        "name": "网络异常注册场景",
                        "input_data": "有效数据",
                        "user_state": "未登录",
                        "system_state": "正常运行",
                        "network": "网络中断",
                        "device": "Chrome浏览器",
                        "data_state": "数据不存在",
                        "expected_result": "提示网络连接失败",
                        "priority": "中"
                    }
                ]
            }, ensure_ascii=False)

        elif "测试用例" in prompt:
            return json.dumps({
                "testcases": [
                    {
                        "title": "验证用户注册功能正常工作",
                        "module": "用户管理模块",
                        "testpoint": "用户注册功能验证",
                        "precondition": "系统正常运行，用户未注册",
                        "steps": [
                            "步骤1: 打开用户注册页面",
                            "步骤2: 输入有效的用户信息（邮箱、密码、手机号）",
                            "步骤3: 点击注册按钮",
                            "步骤4: 验证注册结果"
                        ],
                        "test_data": "邮箱: test@example.com, 密码: Test123456, 手机: 13800138000",
                        "expected_result": "注册成功，返回用户ID和token，跳转到首页",
                        "priority": "高",
                        "type": "功能测试",
                        "complexity": "中等"
                    },
                    {
                        "title": "验证重复邮箱注册被拒绝",
                        "module": "用户管理模块",
                        "testpoint": "用户注册异常处理测试",
                        "precondition": "系统正常运行，邮箱已被注册",
                        "steps": [
                            "步骤1: 打开用户注册页面",
                            "步骤2: 输入已存在的邮箱地址",
                            "步骤3: 输入其他有效信息",
                            "步骤4: 点击注册按钮"
                        ],
                        "test_data": "邮箱: existing@example.com, 密码: Test123456",
                        "expected_result": "注册失败，提示'该邮箱已被注册'",
                        "priority": "高",
                        "type": "异常测试",
                        "complexity": "简单"
                    },
                    {
                        "title": "验证无效邮箱格式被拒绝",
                        "module": "用户管理模块",
                        "testpoint": "用户注册边界条件测试",
                        "precondition": "系统正常运行",
                        "steps": [
                            "步骤1: 打开用户注册页面",
                            "步骤2: 输入无效格式的邮箱",
                            "步骤3: 输入其他有效信息",
                            "步骤4: 点击注册按钮"
                        ],
                        "test_data": "邮箱: invalid-email, 密码: Test123456",
                        "expected_result": "注册失败，提示'邮箱格式不正确'",
                        "priority": "中",
                        "type": "边界测试",
                        "complexity": "简单"
                    },
                    {
                        "title": "验证密码强度要求",
                        "module": "用户管理模块",
                        "testpoint": "用户注册边界条件测试",
                        "precondition": "系统正常运行",
                        "steps": [
                            "步骤1: 打开用户注册页面",
                            "步骤2: 输入有效邮箱",
                            "步骤3: 输入弱密码（少于8位）",
                            "步骤4: 点击注册按钮"
                        ],
                        "test_data": "邮箱: test@example.com, 密码: 123",
                        "expected_result": "注册失败，提示'密码至少8位，需包含字母和数字'",
                        "priority": "中",
                        "type": "边界测试",
                        "complexity": "简单"
                    },
                    {
                        "title": "验证用户登录功能正常工作",
                        "module": "用户管理模块",
                        "testpoint": "用户登录功能验证",
                        "precondition": "系统正常运行，用户已注册",
                        "steps": [
                            "步骤1: 打开登录页面",
                            "步骤2: 输入正确的用户名和密码",
                            "步骤3: 点击登录按钮",
                            "步骤4: 验证登录结果"
                        ],
                        "test_data": "用户名: test@example.com, 密码: Test123456",
                        "expected_result": "登录成功，返回token，跳转到首页",
                        "priority": "高",
                        "type": "功能测试",
                        "complexity": "中等"
                    }
                ]
            }, ensure_ascii=False)

        elif "Bug分析" in prompt or "错误分析" in prompt:
            return """
## Bug分析

**问题原因**: 接口返回状态码500
**可能原因**:
1. 服务器内部错误
2. 数据库连接失败
3. 参数验证失败

**建议**: 检查服务器日志
"""

        return "这是一个模拟的AI响应"

    def generate_json(self, prompt: str, system_prompt: str = None, **kwargs) -> Dict[str, Any]:
        """生成JSON响应"""
        response = self.generate_text(prompt, system_prompt, **kwargs)
        
        try:
            # 如果response已经是JSON字符串,直接解析
            if isinstance(response, str):
                # 尝试找到JSON部分
                start = response.find('{')
                if start != -1:
                    end = response.rfind('}') + 1
                    if end > start:
                        json_str = response[start:end]
                        return json.loads(json_str)
                
                # 尝试直接解析
                return json.loads(response)
            
            # 如果已经是字典,直接返回
            return response
            
        except json.JSONDecodeError as e:
            print(f"⚠️  Mock JSON解析失败: {str(e)}")
            # 返回空结果
            return {"scenarios": [], "testpoints": [], "modules": [], "testcases": []}

    def generate_with_retry(self, prompt: str, system_prompt: str = None,
                          max_retries: int = 3, **kwargs) -> str:
        """带重试的生成"""
        return self.generate_text(prompt, system_prompt, **kwargs)

    def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """多轮对话"""
        last_message = messages[-1]["content"]
        return self.generate_text(last_message)


class AnthropicAIClient:
    """Anthropic Claude客户端"""

    def __init__(self, base_url="https://api.anthropic.com", model="claude-sonnet-4-5-20250929", api_key=None):
        self.base_url = base_url.rstrip('/')
        self.model = model
        self.api_key = api_key or os.getenv('ANTHROPIC_API_KEY')

    def generate_text(self, prompt: str, system_prompt: str = None, **kwargs) -> str:
        """生成文本"""
        headers = {
            "Content-Type": "application/json",
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01"
        }
        
        messages = [{"role": "user", "content": prompt}]
        
        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": kwargs.get("max_tokens", 4000),
            "temperature": kwargs.get("temperature", 0.2)
        }
        
        if system_prompt:
            payload["system"] = system_prompt

        try:
            response = requests.post(
                f"{self.base_url}/v1/messages",
                headers=headers,
                json=payload,
                timeout=120
            )
            response.raise_for_status()
            result = response.json()
            return result.get("content", [{}])[0].get("text", "")
        except Exception as e:
            return f"Anthropic错误: {str(e)}"

    def generate_json(self, prompt: str, system_prompt: str = None, **kwargs) -> Dict[str, Any]:
        """生成JSON"""
        json_prompt = f"{prompt}\n\n请严格按照JSON格式返回,不要包含任何其他文字。"
        response = self.generate_text(json_prompt, system_prompt, **kwargs)
        
        try:
            start = response.find('{')
            end = response.rfind('}') + 1
            
            if start != -1 and end != 0:
                json_str = response[start:end]
                
                import re
                json_str = re.sub(r'//.*?\n', '\n', json_str)
                json_str = re.sub(r'/\*.*?\*/', '', json_str, flags=re.DOTALL)
                json_str = json_str.replace("'", '"')
                json_str = re.sub(r',(\s*[}\]])', r'\1', json_str)
                
                return json.loads(json_str)
            
            return json.loads(response)
            
        except json.JSONDecodeError as e:
            print(f"⚠️  Anthropic JSON解析失败: {str(e)}")
            print(f"原始响应: {response[:200]}...")
            return {"scenarios": [], "error": "JSON解析失败"}

    def generate_with_retry(self, prompt: str, system_prompt: str = None,
                          max_retries: int = 3, **kwargs) -> str:
        """带重试"""
        return self.generate_text(prompt, system_prompt, **kwargs)

    def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """多轮对话"""
        headers = {
            "Content-Type": "application/json",
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01"
        }
        
        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": kwargs.get("max_tokens", 4000),
            "temperature": kwargs.get("temperature", 0.2)
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/v1/messages",
                headers=headers,
                json=payload,
                timeout=120
            )
            response.raise_for_status()
            result = response.json()
            return result.get("content", [{}])[0].get("text", "")
        except Exception as e:
            return f"Anthropic错误: {str(e)}"


class OllamaAIClient:
    """Ollama本地模型客户端"""

    def __init__(self, base_url="http://localhost:11434", model="qwen2.5:1.5b"):
        self.base_url = base_url.rstrip('/')
        self.model = model

    def generate_text(self, prompt: str, system_prompt: str = None, **kwargs) -> str:
        """生成文本"""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False
        }

        try:
            response = requests.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=180  # 增加到3分钟
            )
            response.raise_for_status()
            result = response.json()
            return result.get("message", {}).get("content", "")
        except Exception as e:
            return f"Ollama错误: {str(e)}"

    def generate_json(self, prompt: str, system_prompt: str = None, **kwargs) -> Dict[str, Any]:
        """生成JSON"""
        json_prompt = f"{prompt}\n\n请严格按照JSON格式返回,不要包含任何其他文字。"
        response = self.generate_text(json_prompt, system_prompt, **kwargs)
        
        try:
            # 尝试提取JSON部分
            start = response.find('{')
            end = response.rfind('}') + 1
            
            if start != -1 and end != 0:
                json_str = response[start:end]
                
                # 修复常见JSON错误
                import re
                # 移除注释
                json_str = re.sub(r'//.*?\n', '\n', json_str)
                json_str = re.sub(r'/\*.*?\*/', '', json_str, flags=re.DOTALL)
                # 修复单引号
                json_str = json_str.replace("'", '"')
                # 修复尾部逗号
                json_str = re.sub(r',(\s*[}\]])', r'\1', json_str)
                
                return json.loads(json_str)
            
            return json.loads(response)
            
        except json.JSONDecodeError as e:
            print(f"⚠️  Ollama JSON解析失败: {str(e)}")
            print(f"原始响应: {response[:200]}...")
            # 返回空结果而不是抛出异常
            return {"scenarios": [], "error": "JSON解析失败"}

    def generate_with_retry(self, prompt: str, system_prompt: str = None,
                          max_retries: int = 3, **kwargs) -> str:
        """带重试"""
        return self.generate_text(prompt, system_prompt, **kwargs)

    def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """多轮对话"""
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False
        }
        try:
            response = requests.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=180  # 增加到180秒
            )
            response.raise_for_status()
            result = response.json()
            return result.get("message", {}).get("content", "")
        except Exception as e:
            return f"Ollama错误: {str(e)}"
