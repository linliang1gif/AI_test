#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
AI Test Platform - AI提供商管理器

统一管理多个AI提供商，支持自动切换和负载均衡
"""

import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from .enhanced_ai_client import get_enhanced_ai_client, EnhancedAIClient

class ProviderStatus(Enum):
    """提供商状态"""
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    RATE_LIMITED = "rate_limited"
    ERROR = "error"

@dataclass
class ProviderInfo:
    """提供商信息"""
    name: str
    status: ProviderStatus
    last_check: float
    error_count: int = 0
    success_count: int = 0
    avg_response_time: float = 0.0
    cost_per_token: float = 0.0  # 每token成本

class AIProviderManager:
    """AI提供商管理器"""
    
    def __init__(self):
        self.providers: Dict[str, ProviderInfo] = {}
        self.current_provider = None
        self.fallback_order = ["deepseek", "ollama", "openai"]
        self.check_interval = 300  # 5分钟检查一次
        
        # 初始化提供商信息
        self._initialize_providers()
    
    def _initialize_providers(self):
        """初始化提供商信息"""
        provider_configs = {
            "deepseek": {"cost_per_token": 0.00014},  # 估算成本
            "ollama": {"cost_per_token": 0.0},        # 本地免费
            "openai": {"cost_per_token": 0.002}       # GPT-3.5成本
        }
        
        for name, config in provider_configs.items():
            self.providers[name] = ProviderInfo(
                name=name,
                status=ProviderStatus.UNAVAILABLE,
                last_check=0,
                cost_per_token=config["cost_per_token"]
            )
    
    def check_provider_status(self, provider_name: str) -> ProviderStatus:
        """检查提供商状态"""
        try:
            client = get_enhanced_ai_client(provider_name)
            
            # 记录开始时间
            start_time = time.time()
            
            # 检查可用性
            if client.is_available():
                # 更新响应时间
                response_time = time.time() - start_time
                provider_info = self.providers[provider_name]
                provider_info.avg_response_time = (
                    provider_info.avg_response_time + response_time
                ) / 2 if provider_info.avg_response_time > 0 else response_time
                
                provider_info.success_count += 1
                provider_info.status = ProviderStatus.AVAILABLE
                return ProviderStatus.AVAILABLE
            else:
                self.providers[provider_name].error_count += 1
                self.providers[provider_name].status = ProviderStatus.UNAVAILABLE
                return ProviderStatus.UNAVAILABLE
                
        except Exception as e:
            self.providers[provider_name].error_count += 1
            self.providers[provider_name].status = ProviderStatus.ERROR
            print(f"检查提供商 {provider_name} 状态失败: {str(e)}")
            return ProviderStatus.ERROR
        finally:
            self.providers[provider_name].last_check = time.time()
    
    def get_best_provider(self, prefer_local: bool = False, 
                         prefer_cost_effective: bool = False) -> Optional[str]:
        """获取最佳提供商"""
        available_providers = []
        
        # 检查所有提供商状态
        for provider_name in self.providers.keys():
            provider_info = self.providers[provider_name]
            
            # 如果超过检查间隔，重新检查状态
            if time.time() - provider_info.last_check > self.check_interval:
                self.check_provider_status(provider_name)
            
            if provider_info.status == ProviderStatus.AVAILABLE:
                available_providers.append((provider_name, provider_info))
        
        if not available_providers:
            return None
        
        # 根据偏好选择提供商
        if prefer_local:
            # 优先选择本地模型
            for name, info in available_providers:
                if name == "ollama":
                    return name
        
        if prefer_cost_effective:
            # 选择成本最低的
            available_providers.sort(key=lambda x: x[1].cost_per_token)
            return available_providers[0][0]
        
        # 默认按照fallback顺序选择
        for provider_name in self.fallback_order:
            if any(name == provider_name for name, _ in available_providers):
                return provider_name
        
        # 如果都不在fallback列表中，选择第一个可用的
        return available_providers[0][0]
    
    def get_client_with_fallback(self, prefer_local: bool = False) -> Tuple[EnhancedAIClient, str]:
        """获取客户端，支持自动fallback"""
        provider_name = self.get_best_provider(prefer_local=prefer_local)
        
        if not provider_name:
            raise Exception("没有可用的AI提供商")
        
        client = get_enhanced_ai_client(provider_name)
        return client, provider_name
    
    def generate_with_fallback(self, prompt: str, system_prompt: str = None, 
                             prefer_local: bool = False, **kwargs) -> Tuple[str, str]:
        """使用fallback机制生成文本"""
        last_error = None
        
        # 尝试所有可用的提供商
        for provider_name in self.fallback_order:
            if prefer_local and provider_name != "ollama":
                continue
                
            try:
                # 检查提供商状态
                if self.check_provider_status(provider_name) != ProviderStatus.AVAILABLE:
                    continue
                
                client = get_enhanced_ai_client(provider_name)
                result = client.generate_text(prompt, system_prompt, **kwargs)
                
                # 更新成功统计
                self.providers[provider_name].success_count += 1
                
                return result, provider_name
                
            except Exception as e:
                last_error = e
                self.providers[provider_name].error_count += 1
                self.providers[provider_name].status = ProviderStatus.ERROR
                print(f"提供商 {provider_name} 失败，尝试下一个: {str(e)}")
                continue
        
        # 所有提供商都失败了
        raise Exception(f"所有AI提供商都不可用。最后错误: {str(last_error)}")
    
    def get_provider_stats(self) -> Dict[str, Dict]:
        """获取提供商统计信息"""
        stats = {}
        
        for name, info in self.providers.items():
            total_requests = info.success_count + info.error_count
            success_rate = (info.success_count / total_requests * 100) if total_requests > 0 else 0
            
            stats[name] = {
                "status": info.status.value,
                "success_count": info.success_count,
                "error_count": info.error_count,
                "success_rate": round(success_rate, 2),
                "avg_response_time": round(info.avg_response_time, 3),
                "cost_per_token": info.cost_per_token,
                "last_check": info.last_check
            }
        
        return stats
    
    def reset_stats(self):
        """重置统计信息"""
        for provider_info in self.providers.values():
            provider_info.success_count = 0
            provider_info.error_count = 0
            provider_info.avg_response_time = 0.0

# 全局提供商管理器实例
_provider_manager = None

def get_provider_manager() -> AIProviderManager:
    """获取提供商管理器实例"""
    global _provider_manager
    if _provider_manager is None:
        _provider_manager = AIProviderManager()
    return _provider_manager