#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
AI Test Platform - 增强AI客户端模块

支持多种AI提供商：DeepSeek、OpenAI、Ollama本地模型
集成智能模型选择器，自动选择最适合的模型
"""

import json
import time
import requests
from typing import Dict, Any, Optional, List
from config.config import get_config
from model_selector import ModelSelector
from utils.logger import get_logger

logger = get_logger("ai_client")

class OllamaClient:
    """Ollama本地模型客户端"""
    
    def __init__(self, base_url: str, model: str = None, timeout: int = 60):
        self.base_url = base_url.rstrip('/')
        self.model = model
        self.timeout = timeout
        self.model_selector = ModelSelector(base_url)
    
    def generate(self, prompt: str, system_prompt: str = None, task_type: str = None, 
                prefer_speed: bool = False, **kwargs) -> str:
        """生成文本 - 支持智能模型选择"""
        start_time = time.time()
        
        try:
            # 如果没有指定模型，使用智能选择器
            if not self.model:
                logger.info(f"使用智能模型选择器 - 任务类型: {task_type}")
                result = self.model_selector.generate_with_auto_selection(
                    prompt=prompt,
                    task_type=task_type,
                    prefer_speed=prefer_speed,
                    system_prompt=system_prompt,
                    **kwargs
                )
                
                duration = time.time() - start_time
                if result["success"]:
                    logger.log_api_call("ollama", "auto_select", len(prompt), 
                                      len(result["content"]), duration, True)
                    return result["content"]
                else:
                    logger.log_api_call("ollama", "auto_select", len(prompt), 
                                      0, duration, False, result['error'])
                    raise Exception(f"生成失败: {result['error']}")
            
            # 使用指定模型 - 修复为chat API格式
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            payload = {
                "model": self.model,
                "messages": messages,
                "stream": False,
                "options": {
                    "temperature": kwargs.get("temperature", 0.2),
                    "num_predict": kwargs.get("max_tokens", 4000)
                }
            }
            
            logger.debug(f"发送Ollama请求 - 模型: {self.model}, 消息数: {len(messages)}")
            
            response = requests.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            result = response.json()
            content = result.get("message", {}).get("content", "")
            
            duration = time.time() - start_time
            logger.log_api_call("ollama", self.model, len(prompt), len(content), duration, True)
            
            return content
            
        except requests.exceptions.RequestException as e:
            duration = time.time() - start_time
            logger.log_api_call("ollama", self.model or "unknown", len(prompt), 
                              0, duration, False, str(e))
            raise Exception(f"Ollama API请求失败: {str(e)}")
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"Ollama生成文本失败", e, {
                'model': self.model,
                'prompt_length': len(prompt),
                'duration': duration
            })
            raise
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"Ollama API请求失败: {str(e)}")
    
    def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """多轮对话"""
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": kwargs.get("temperature", 0.2),
                "num_predict": kwargs.get("max_tokens", 4000)
            }
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            result = response.json()
            return result.get("message", {}).get("content", "")
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Ollama Chat API请求失败", e, {
                'model': self.model,
                'messages_count': len(messages)
            })
            raise Exception(f"Ollama Chat API请求失败: {str(e)}")
        except Exception as e:
            logger.error(f"Ollama多轮对话失败", e, {'model': self.model})
            raise
    
    def list_models(self) -> List[str]:
        """获取可用模型列表"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=10)
            response.raise_for_status()
            
            result = response.json()
            return [model["name"] for model in result.get("models", [])]
            
        except requests.exceptions.RequestException:
            return []
    
    def is_available(self) -> bool:
        """检查Ollama服务是否可用"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            available = response.status_code == 200
            logger.debug(f"Ollama服务可用性检查: {available}")
            return available
        except Exception as e:
            logger.warning(f"Ollama服务不可用", extra={'error': str(e)})
            return False

class EnhancedAIClient:
    """增强的AI客户端，支持多种提供商"""
    
    def __init__(self, provider: str = None):
        self.config = get_config()
        self.provider = provider or self.config.ai.default_provider
        self.ai_config = self.config.get_ai_config_for_provider(self.provider)
        
        # 初始化对应的客户端
        if self.provider == "ollama":
            self.client = OllamaClient(
                self.ai_config["base_url"],
                self.ai_config["model"],
                self.ai_config["timeout"]
            )
        else:
            # 使用原有的API客户端
            self.client = None
    
    def _make_api_request(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """发送API请求（DeepSeek/OpenAI）"""
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.ai_config['api_key']}"
        }
        
        payload = {
            "model": self.ai_config["model"],
            "messages": messages,
            "temperature": kwargs.get("temperature", self.ai_config["temperature"]),
            "max_tokens": kwargs.get("max_tokens", self.ai_config["max_tokens"])
        }
        
        try:
            response = requests.post(
                f"{self.ai_config['base_url']}/chat/completions",
                headers=headers,
                json=payload,
                timeout=self.ai_config["timeout"]
            )
            response.raise_for_status()
            
            result = response.json()
            return result["choices"][0]["message"]["content"]
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"AI API请求失败: {str(e)}")
        except KeyError as e:
            raise Exception(f"AI API响应格式错误: {str(e)}")
    
    def generate_text(self, prompt: str, system_prompt: str = None, **kwargs) -> str:
        """生成文本"""
        if self.provider == "ollama":
            return self.client.generate(prompt, system_prompt, **kwargs)
        else:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            return self._make_api_request(messages, **kwargs)
    
    def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """多轮对话"""
        if self.provider == "ollama":
            return self.client.chat(messages, **kwargs)
        else:
            return self._make_api_request(messages, **kwargs)
    
    def generate_with_retry(self, prompt: str, system_prompt: str = None, 
                          max_retries: int = 3, **kwargs) -> str:
        """带重试的生成"""
        for attempt in range(max_retries):
            try:
                return self.generate_text(prompt, system_prompt, **kwargs)
            except Exception as e:
                if attempt == max_retries - 1:
                    raise e
                print(f"AI请求失败，正在重试 ({attempt + 1}/{max_retries}): {str(e)}")
                time.sleep(2 ** attempt)
        
        raise Exception("AI请求重试次数已用完")
    
    def generate_json(self, prompt: str, system_prompt: str = None, **kwargs) -> Dict[str, Any]:
        """生成JSON格式的响应"""
        json_prompt = f"{prompt}\n\n请以JSON格式返回结果，确保格式正确。"
        
        response = self.generate_with_retry(json_prompt, system_prompt, **kwargs)
        
        try:
            # 尝试提取JSON部分
            start_idx = response.find('{')
            end_idx = response.rfind('}') + 1
            
            if start_idx != -1 and end_idx != 0:
                json_str = response[start_idx:end_idx]
                return json.loads(json_str)
            else:
                return json.loads(response)
                
        except json.JSONDecodeError as e:
            raise Exception(f"AI返回的不是有效的JSON格式: {str(e)}\n原始响应: {response}")
    
    def is_available(self) -> bool:
        """检查AI服务是否可用"""
        if self.provider == "ollama":
            return self.client.is_available()
        else:
            try:
                # 发送一个简单的测试请求
                self.generate_text("Hello", max_tokens=10)
                return True
            except:
                return False
    
    def get_available_models(self) -> List[str]:
        """获取可用模型列表"""
        if self.provider == "ollama":
            return self.client.list_models()
        else:
            return self.config.get_available_models(self.provider)
    
    def switch_provider(self, provider: str, model: str = None):
        """切换AI提供商"""
        self.provider = provider
        self.ai_config = self.config.get_ai_config_for_provider(provider)
        
        if model:
            self.ai_config["model"] = model
        
        if provider == "ollama":
            self.client = OllamaClient(
                self.ai_config["base_url"],
                self.ai_config["model"],
                self.ai_config["timeout"]
            )
        else:
            self.client = None

# 全局增强AI客户端实例
_enhanced_ai_client = None

def get_enhanced_ai_client(provider: str = None) -> EnhancedAIClient:
    """获取增强AI客户端实例"""
    global _enhanced_ai_client
    if _enhanced_ai_client is None or (provider and _enhanced_ai_client.provider != provider):
        _enhanced_ai_client = EnhancedAIClient(provider)
    return _enhanced_ai_client

# 向后兼容
def get_ai_client(provider: str = None):
    """向后兼容的AI客户端获取函数"""
    return get_enhanced_ai_client(provider)