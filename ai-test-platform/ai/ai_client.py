#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
AI Test Platform - AI客户端模块

负责与各种AI模型进行交互，支持DeepSeek、OpenAI等多种AI提供商。
"""

import json
import time
from typing import Dict, Any, Optional, List
import requests
from config.config import get_config

class AIClient:
    """AI客户端类"""
    
    def __init__(self, provider: str = None, module: str = None):
        self.config = get_config()
        self.module = module
        self.provider = provider or self.config.ai.default_provider
        
        # 如果指定了模块，使用模块配置
        if module:
            module_config = self.config.get_module_ai_config(module)
            self.provider = provider or module_config["provider"]
            self.model_override = module_config["model"]
        else:
            self.model_override = None
        
        self.ai_config = self.config.get_ai_config_for_provider(self.provider, module)
        
    def _make_request(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """发送AI请求"""
        headers = {
            "Content-Type": "application/json",
        }
        
        # Ollama 不需要 Authorization header
        if self.provider != "ollama":
            headers["Authorization"] = f"Bearer {self.ai_config['api_key']}"
        
        # OpenRouter 需要额外的请求头
        if "openrouter.ai" in self.ai_config.get('base_url', ''):
            headers["HTTP-Referer"] = "http://localhost:8000"
            headers["X-Title"] = "AI Test Platform"
        
        payload = {
            "model": kwargs.get("model", self.ai_config["model"]),  # 支持动态指定模型
            "messages": messages,
            "temperature": kwargs.get("temperature", self.ai_config["temperature"]),
        }
        
        # Ollama 不支持 max_tokens，其他提供商支持
        if self.provider != "ollama":
            payload["max_tokens"] = kwargs.get("max_tokens", self.ai_config["max_tokens"])
        
        # Ollama 需要 stream 参数
        if self.provider == "ollama":
            payload["stream"] = kwargs.get("stream", False)
        
        # 添加其他参数
        if "stream" in kwargs and self.provider != "ollama":
            payload["stream"] = kwargs["stream"]
        
        try:
            # 创建session以复用连接,并配置重试策略
            session = requests.Session()
            
            # 配置适配器和重试策略
            from requests.adapters import HTTPAdapter
            from urllib3.util.retry import Retry
            
            retry_strategy = Retry(
                total=3,
                backoff_factor=1,
                status_forcelist=[429, 500, 502, 503, 504],
                allowed_methods=["POST"]
            )
            adapter = HTTPAdapter(max_retries=retry_strategy)
            session.mount("http://", adapter)
            session.mount("https://", adapter)
            
            # 发送请求,增加超时时间并禁用SSL验证(如果需要)
            # Ollama 使用 /api/chat，其他使用 /chat/completions
            if self.provider == "ollama":
                endpoint = "/api/chat"
            else:
                endpoint = "/chat/completions"
            
            response = session.post(
                f"{self.ai_config['base_url']}{endpoint}",
                headers=headers,
                json=payload,
                timeout=(10, 120),  # (连接超时, 读取超时)
                verify=True  # 保持SSL验证
            )
            response.raise_for_status()
            
            result = response.json()
            
            # Ollama 的响应格式不同
            if self.provider == "ollama":
                return result.get("message", {}).get("content", "")
            else:
                return result["choices"][0]["message"]["content"]
            
        except requests.exceptions.SSLError as e:
            raise Exception(f"SSL连接错误: {str(e)}. 可能是网络问题或证书问题,请检查网络连接")
        except requests.exceptions.Timeout as e:
            raise Exception(f"请求超时: {str(e)}. DeepSeek API响应时间过长,请稍后重试")
        except requests.exceptions.ConnectionError as e:
            raise Exception(f"连接错误: {str(e)}. 无法连接到DeepSeek API,请检查网络")
        except requests.exceptions.RequestException as e:
            raise Exception(f"AI API请求失败: {str(e)}")
        except KeyError as e:
            raise Exception(f"AI API响应格式错误: {str(e)}")
    
    def generate_text(self, prompt: str, system_prompt: str = None, **kwargs) -> str:
        """生成文本"""
        messages = []
        
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        messages.append({"role": "user", "content": prompt})
        
        return self._make_request(messages, **kwargs)
    
    def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """多轮对话"""
        return self._make_request(messages, **kwargs)
    
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
                time.sleep(2 ** attempt)  # 指数退避
        
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
                
                # 尝试修复常见的JSON错误
                json_str = self._fix_common_json_errors(json_str)
                
                return json.loads(json_str)
            else:
                # 如果没找到JSON,尝试解析整个响应
                return json.loads(response)
                
        except json.JSONDecodeError as e:
            # JSON解析失败,尝试更激进的修复
            try:
                fixed_response = self._aggressive_json_fix(response)
                return json.loads(fixed_response)
            except:
                # 如果还是失败,返回一个包含原始响应的字典
                print(f"⚠️  JSON解析失败,返回空结果: {str(e)}")
                return {"error": "JSON解析失败", "raw_response": response[:200], "scenarios": []}
    
    def _fix_common_json_errors(self, json_str: str) -> str:
        """修复常见的JSON错误"""
        # 移除注释
        import re
        json_str = re.sub(r'//.*?\n', '\n', json_str)
        json_str = re.sub(r'/\*.*?\*/', '', json_str, flags=re.DOTALL)
        
        # 修复单引号
        json_str = json_str.replace("'", '"')
        
        # 修复尾部逗号
        json_str = re.sub(r',(\s*[}\]])', r'\1', json_str)
        
        # 修复缺少引号的键
        json_str = re.sub(r'(\w+):', r'"\1":', json_str)
        
        return json_str
    
    def _aggressive_json_fix(self, response: str) -> str:
        """更激进的JSON修复"""
        import re
        
        # 尝试找到最外层的{}或[]
        brace_start = response.find('{')
        bracket_start = response.find('[')
        
        if brace_start == -1 and bracket_start == -1:
            return '{"scenarios": []}'
        
        # 选择最早出现的
        if brace_start != -1 and (bracket_start == -1 or brace_start < bracket_start):
            start = brace_start
            end = response.rfind('}') + 1
        else:
            start = bracket_start
            end = response.rfind(']') + 1
        
        if end <= start:
            return '{"scenarios": []}'
        
        json_str = response[start:end]
        
        # 应用所有修复
        json_str = self._fix_common_json_errors(json_str)
        
        return json_str
    
    def generate_list(self, prompt: str, system_prompt: str = None, **kwargs) -> List[str]:
        """生成列表格式的响应"""
        list_prompt = f"{prompt}\n\n请以列表格式返回结果，每行一个项目。"
        
        response = self.generate_with_retry(list_prompt, system_prompt, **kwargs)
        
        # 解析列表
        lines = response.strip().split('\n')
        result = []
        
        for line in lines:
            line = line.strip()
            # 移除列表标记
            if line.startswith('- '):
                line = line[2:]
            elif line.startswith('* '):
                line = line[2:]
            elif '. ' in line and line.split('.')[0].isdigit():
                line = line.split('. ', 1)[1]
            
            if line:
                result.append(line)
        
        return result
    
    def validate_response(self, response: str, expected_format: str = "text") -> bool:
        """验证AI响应格式"""
        if expected_format == "json":
            try:
                json.loads(response)
                return True
            except json.JSONDecodeError:
                return False
        elif expected_format == "list":
            return '\n' in response or '- ' in response or '* ' in response
        else:
            return len(response.strip()) > 0

# 全局AI客户端实例
_ai_client = None

def get_ai_client(provider: str = None, module: str = None, use_mock: bool = None, use_ollama: bool = None) -> AIClient:
    """获取AI客户端实例
    
    Args:
        provider: AI提供商
        module: 模块名称（testcase_generation, script_generation, swagger_analysis, test_optimization）
        use_mock: 是否使用 Mock 客户端
        use_ollama: 是否使用 Ollama
    """
    global _ai_client
    
    # 检查环境变量和配置
    import os
    config = get_config()
    
    # 确定使用哪个提供商
    if provider is None:
        provider = config.ai.default_provider
    
    # 如果明确指定使用 Anthropic 或配置为 Anthropic
    if provider == 'anthropic':
        from ai.mock_ai_client import AnthropicAIClient
        # 优先使用ANTHROPIC_API_KEY,如果没有则使用ANTHROPIC_AUTH_TOKEN
        anthropic_key = os.getenv('ANTHROPIC_API_KEY') or os.getenv('ANTHROPIC_AUTH_TOKEN')
        # 从环境变量读取BASE_URL
        anthropic_base = os.getenv('ANTHROPIC_BASE_URL', 'https://api.anthropic.com')
        anthropic_model = os.getenv('DEFAULT_AI_MODEL', 'claude-sonnet-4-5-20250929')
        
        print(f"🔧 Anthropic配置: base_url={anthropic_base}, model={anthropic_model}, api_key={anthropic_key[:20]}...")
        
        return AnthropicAIClient(
            base_url=anthropic_base,
            model=anthropic_model,
            api_key=anthropic_key
        )
    
    # 如果明确指定使用 Ollama 或配置为 Ollama
    if use_ollama or provider == 'ollama':
        from ai.mock_ai_client import OllamaAIClient
        return OllamaAIClient(
            base_url=config.ai.ollama_base_url,
            model=config.ai.default_model
        )

    # 检查是否配置为使用mock
    if provider == 'mock':
        from ai.mock_ai_client import MockAIClient
        return MockAIClient()

    # 自动检测是否使用mock（没有API Key时）
    if use_mock is None:
        use_mock = not config.ai.deepseek_api_key and not config.ai.openai_api_key

    if use_mock:
        from ai.mock_ai_client import MockAIClient
        return MockAIClient()

    # 使用真实的AI客户端(DeepSeek/OpenAI)，支持模块配置
    if _ai_client is None or (provider and _ai_client.provider != provider) or (module and getattr(_ai_client, 'module', None) != module):
        _ai_client = AIClient(provider, module)
    return _ai_client