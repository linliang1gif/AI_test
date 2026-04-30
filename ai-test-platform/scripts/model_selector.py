#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
智能模型选择器
根据任务类型自动选择最适合的Ollama模型
"""

import requests
import time
from typing import Dict, Any, Optional

class ModelSelector:
    """智能模型选择器"""
    
    def __init__(self, ollama_base_url: str = "http://localhost:11434"):
        self.ollama_base_url = ollama_base_url.rstrip('/')
        
        # 模型配置
        self.models = {
            "qwen2.5:1.5b": {
                "size": "small",
                "speed": "fast",
                "best_for": ["simple_tasks", "quick_responses", "basic_analysis"],
                "timeout": 30,
                "description": "轻量级模型，适合快速响应的简单任务"
            },
            "qwen2.5-coder:latest": {
                "size": "large", 
                "speed": "slow",
                "best_for": ["code_generation", "complex_analysis", "detailed_responses"],
                "timeout": 60,
                "description": "代码专用模型，适合复杂的代码生成和分析"
            }
        }
        
        # 任务类型映射
        self.task_mapping = {
            # 快速任务 - 使用轻量级模型
            "test_case_generation": "qwen2.5:1.5b",
            "simple_analysis": "qwen2.5:1.5b", 
            "quick_summary": "qwen2.5:1.5b",
            "basic_questions": "qwen2.5:1.5b",
            
            # 复杂任务 - 使用代码专用模型
            "code_generation": "qwen2.5-coder:latest",
            "api_script_generation": "qwen2.5-coder:latest",
            "complex_debugging": "qwen2.5-coder:latest",
            "detailed_code_review": "qwen2.5-coder:latest"
        }
    
    def select_model(self, task_type: str = None, prompt: str = None, prefer_speed: bool = False) -> Dict[str, Any]:
        """
        选择最适合的模型
        
        Args:
            task_type: 任务类型
            prompt: 提示文本（用于智能判断）
            prefer_speed: 是否优先考虑速度
            
        Returns:
            包含模型名称和配置的字典
        """
        
        # 如果指定了任务类型，直接使用映射
        if task_type and task_type in self.task_mapping:
            model_name = self.task_mapping[task_type]
            return {
                "model": model_name,
                "config": self.models[model_name],
                "reason": f"任务类型 '{task_type}' 映射到模型 '{model_name}'"
            }
        
        # 如果优先考虑速度，使用轻量级模型
        if prefer_speed:
            model_name = "qwen2.5:1.5b"
            return {
                "model": model_name,
                "config": self.models[model_name],
                "reason": "优先考虑响应速度"
            }
        
        # 基于提示内容智能判断
        if prompt:
            prompt_lower = prompt.lower()
            
            # 代码相关关键词
            code_keywords = [
                "代码", "code", "function", "class", "python", "java", "javascript",
                "api", "script", "编程", "开发", "debug", "测试脚本", "自动化"
            ]
            
            # 简单任务关键词
            simple_keywords = [
                "简单", "快速", "概述", "总结", "列表", "简要", "basic", "simple", "quick"
            ]
            
            # 检查是否包含代码相关关键词
            if any(keyword in prompt_lower for keyword in code_keywords):
                model_name = "qwen2.5-coder:latest"
                return {
                    "model": model_name,
                    "config": self.models[model_name],
                    "reason": "检测到代码相关任务"
                }
            
            # 检查是否包含简单任务关键词
            if any(keyword in prompt_lower for keyword in simple_keywords):
                model_name = "qwen2.5:1.5b"
                return {
                    "model": model_name,
                    "config": self.models[model_name],
                    "reason": "检测到简单快速任务"
                }
        
        # 默认使用轻量级模型（平衡速度和功能）
        model_name = "qwen2.5:1.5b"
        return {
            "model": model_name,
            "config": self.models[model_name],
            "reason": "默认选择（平衡速度和功能）"
        }
    
    def generate_with_auto_selection(self, prompt: str, task_type: str = None, 
                                   prefer_speed: bool = False, **kwargs) -> Dict[str, Any]:
        """
        自动选择模型并生成内容
        
        Args:
            prompt: 提示文本
            task_type: 任务类型
            prefer_speed: 是否优先考虑速度
            **kwargs: 其他生成参数
            
        Returns:
            包含生成结果和元信息的字典
        """
        
        # 选择模型
        selection = self.select_model(task_type, prompt, prefer_speed)
        model_name = selection["model"]
        model_config = selection["config"]
        
        print(f"🤖 选择模型: {model_name}")
        print(f"📝 选择原因: {selection['reason']}")
        
        # 准备请求参数
        payload = {
            "model": model_name,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": kwargs.get("temperature", 0.2),
                "num_predict": kwargs.get("max_tokens", 2000)
            }
        }
        
        if kwargs.get("system_prompt"):
            payload["system"] = kwargs["system_prompt"]
        
        # 发送请求
        start_time = time.time()
        
        try:
            response = requests.post(
                f"{self.ollama_base_url}/api/chat",
                json={
                    "model": model_name,
                    "messages": [{"role": "user", "content": prompt}],
                    "stream": False,
                    "options": model_config.get("options", {})
                },
                timeout=model_config["timeout"]
            )
            response.raise_for_status()

            result = response.json()
            generated_text = result.get("response", "")

            end_time = time.time()
            duration = end_time - start_time
            end_time = time.time()
            duration = end_time - start_time

            return {
                "success": True,
                "content": generated_text,
                "model_used": model_name,
                "selection_reason": selection["reason"],
                "duration": duration,
                "model_config": model_config
            }

        except requests.exceptions.Timeout:
            # 如果大模型超时，自动回退到小模型
            if model_name == "qwen2.5-coder:latest":
                print("⚠️ 大模型超时，自动回退到轻量级模型")
                return self.generate_with_auto_selection(
                    prompt, task_type="simple_analysis", prefer_speed=True, **kwargs
                )
            else:
                return {
                    "success": False,
                    "error": "请求超时",
                    "model_used": model_name,
                    "duration": time.time() - start_time
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "model_used": model_name,
                "duration": time.time() - start_time
            }
    
    def get_available_models(self) -> Dict[str, Any]:
        """获取可用模型列表"""
        try:
            response = requests.get(f"{self.ollama_base_url}/api/tags")
            if response.status_code == 200:
                ollama_models = response.json().get("models", [])
                available_models = {}
                
                for model_info in ollama_models:
                    model_name = model_info["name"]
                    if model_name in self.models:
                        available_models[model_name] = {
                            **self.models[model_name],
                            "size_bytes": model_info.get("size", 0),
                            "modified": model_info.get("modified_at", "")
                        }
                
                return available_models
            else:
                return {}
        except Exception as e:
            print(f"获取模型列表失败: {e}")
            return {}

def demo():
    """演示模型选择器功能"""
    selector = ModelSelector()
    
    # 测试用例
    test_cases = [
        {
            "prompt": "请生成一个用户登录的API测试用例",
            "task_type": "test_case_generation",
            "description": "测试用例生成"
        },
        {
            "prompt": "请用Python写一个HTTP客户端函数",
            "task_type": "code_generation", 
            "description": "代码生成"
        },
        {
            "prompt": "简单总结一下这个错误的原因",
            "prefer_speed": True,
            "description": "快速分析"
        }
    ]
    
    print("🚀 模型选择器演示\n")
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"--- 测试 {i}: {test_case['description']} ---")
        
        result = selector.generate_with_auto_selection(
            prompt=test_case["prompt"],
            task_type=test_case.get("task_type"),
            prefer_speed=test_case.get("prefer_speed", False)
        )
        
        if result["success"]:
            print(f"✅ 生成成功 (耗时: {result['duration']:.2f}秒)")
            print(f"📄 内容预览: {result['content'][:100]}...")
        else:
            print(f"❌ 生成失败: {result['error']}")
        
        print()

if __name__ == "__main__":
    demo()