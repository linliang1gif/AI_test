#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LLM Client - 统一的LLM调用客户端
支持多种Provider: Ollama, OpenAI, DeepSeek, Mock
"""

import os
import json
import requests
from typing import Dict, Any, Optional
from pathlib import Path
import sys

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.config import get_config


class LLMClient:
    """统一的LLM调用客户端"""
    
    def __init__(self, provider: Optional[str] = None, model: Optional[str] = None):
        """
        初始化LLM客户端
        
        Args:
            provider: AI提供商 (ollama/openai/deepseek/mock)
            model: 模型名称
        """
        self.config = get_config()
        self.provider = provider or self.config.ai.default_provider
        self.model = model or self.config.ai.default_model
        
        # 根据provider设置配置
        if self.provider == 'ollama':
            self.base_url = self.config.ai.ollama_base_url
            self.api_key = None
        elif self.provider == 'deepseek':
            self.base_url = self.config.ai.deepseek_base_url
            self.api_key = self.config.ai.deepseek_api_key
        elif self.provider == 'openai':
            self.base_url = self.config.ai.openai_base_url
            self.api_key = self.config.ai.openai_api_key
        elif self.provider == 'anthropic':
            self.base_url = self.config.ai.anthropic_base_url
            self.api_key = self.config.ai.anthropic_api_key
        else:  # mock
            self.base_url = None
            self.api_key = None
    
    def generate(self, prompt: str, system_prompt: Optional[str] = None, 
                 temperature: float = 0.2, max_tokens: int = 4000) -> str:
        """
        生成文本
        
        Args:
            prompt: 用户提示词
            system_prompt: 系统提示词
            temperature: 温度参数
            max_tokens: 最大token数
            
        Returns:
            生成的文本内容
        """
        if self.provider == 'mock':
            return self._mock_generate(prompt)
        elif self.provider == 'ollama':
            return self._ollama_generate(prompt, system_prompt, temperature)
        else:  # openai/deepseek/anthropic - 都使用OpenAI兼容API
            return self._openai_compatible_generate(prompt, system_prompt, temperature, max_tokens)
    
    def generate_json(self, prompt: str, system_prompt: Optional[str] = None) -> Dict[str, Any]:
        """
        生成JSON格式的响应
        
        Args:
            prompt: 用户提示词
            system_prompt: 系统提示词
            
        Returns:
            解析后的JSON对象
        """
        try:
            # 在prompt中强调JSON格式
            json_prompt = f"{prompt}\n\n请以标准JSON格式返回结果，不要包含任何其他文本。"
            
            response_text = self.generate(json_prompt, system_prompt, temperature=0.1)
            
            # 检查响应是否为空
            if not response_text or not response_text.strip():
                print(f"⚠️  LLM返回空响应")
                return self._get_default_json_response("LLM返回空响应")
            
            # 尝试解析JSON
            try:
                # 提取JSON内容（可能包含在markdown代码块中）
                import re
                json_match = re.search(r'```json\s*(.*?)\s*```', response_text, re.DOTALL)
                if json_match:
                    response_text = json_match.group(1)
                
                # 移除可能的前后空白和非JSON字符
                response_text = response_text.strip()
                
                return json.loads(response_text)
            except json.JSONDecodeError as e:
                print(f"⚠️  JSON解析失败: {e}")
                print(f"原始响应: {response_text[:500]}")
                
                # 返回默认结构
                return self._get_default_json_response(f"JSON解析失败: {str(e)}")
                
        except Exception as e:
            print(f"❌ generate_json异常: {e}")
            return self._get_default_json_response(f"生成异常: {str(e)}")
    
    def _get_default_json_response(self, reason: str) -> Dict[str, Any]:
        """获取默认JSON响应"""
        return {
            "need_test": True,
            "modules": ["未知模块"],
            "priority": "P1",
            "reason": f"AI响应异常: {reason}，建议人工审核",
            "test_types": ["功能测试"],
            "estimated_effort": "未评估",
            "risk_level": "中"
        }
    
    def _mock_generate(self, prompt: str) -> str:
        """Mock模式生成"""
        # 分析prompt关键词，返回合理的mock响应
        if "是否需要测试" in prompt or "need_test" in prompt.lower():
            return json.dumps({
                "need_test": True,
                "modules": ["订单模块", "支付模块"],
                "priority": "P0",
                "reason": "核心交易逻辑变更，涉及订单和支付流程"
            }, ensure_ascii=False, indent=2)
        else:
            return "这是一个Mock响应，用于测试和开发。"
    
    def _ollama_generate(self, prompt: str, system_prompt: Optional[str], 
                        temperature: float) -> str:
        """Ollama生成"""
        try:
            url = f"{self.base_url}/api/chat"
            
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            payload = {
                "model": self.model,
                "messages": messages,
                "stream": False,
                "options": {
                    "temperature": temperature
                }
            }
            
            response = requests.post(url, json=payload, timeout=180)
            response.raise_for_status()
            
            result = response.json()
            return result.get('message', {}).get('content', '')
            
        except Exception as e:
            print(f"❌ Ollama调用失败: {e}")
            raise
    
    def _openai_compatible_generate(self, prompt: str, system_prompt: Optional[str],
                                    temperature: float, max_tokens: int) -> str:
        """OpenAI兼容API生成（支持OpenAI和DeepSeek）"""
        try:
            url = f"{self.base_url}/chat/completions"
            
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            
            payload = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens
            }
            
            response = requests.post(url, json=payload, headers=headers, timeout=120)
            response.raise_for_status()
            
            result = response.json()
            return result['choices'][0]['message']['content']
            
        except Exception as e:
            print(f"❌ {self.provider.upper()} API调用失败: {e}")
            raise


# 全局客户端实例
_llm_client = None

def get_llm_client(provider: Optional[str] = None, model: Optional[str] = None) -> LLMClient:
    """获取LLM客户端实例"""
    global _llm_client
    if _llm_client is None or provider or model:
        _llm_client = LLMClient(provider, model)
    return _llm_client
