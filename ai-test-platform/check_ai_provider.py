#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
检查当前AI提供商配置
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from config.config import get_config
from ai.ai_client import get_ai_client

def check_ai_provider():
    """检查AI提供商配置"""
    print("=" * 60)
    print("🔍 AI提供商配置检查")
    print("=" * 60)
    
    # 检查环境变量
    print("\n📋 环境变量:")
    print(f"  USE_OLLAMA: {os.environ.get('USE_OLLAMA', '未设置')}")
    print(f"  AI_PROVIDER: {os.environ.get('AI_PROVIDER', '未设置')}")
    
    # 检查配置文件
    config = get_config()
    print("\n⚙️  配置文件 (.env):")
    print(f"  DEFAULT_AI_PROVIDER: {config.ai.default_provider}")
    print(f"  DEFAULT_AI_MODEL: {config.ai.default_model}")
    print(f"  DEEPSEEK_API_KEY: {'已配置' if config.ai.deepseek_api_key else '未配置'}")
    print(f"  DEEPSEEK_BASE_URL: {config.ai.deepseek_base_url}")
    print(f"  OPENAI_API_KEY: {'已配置' if config.ai.openai_api_key else '未配置'}")
    print(f"  OLLAMA_BASE_URL: {config.ai.ollama_base_url}")
    
    # 获取AI客户端
    print("\n🤖 实际使用的AI客户端:")
    try:
        ai_client = get_ai_client()
        client_type = type(ai_client).__name__
        print(f"  客户端类型: {client_type}")
        
        if hasattr(ai_client, 'provider'):
            print(f"  提供商: {ai_client.provider}")
        
        if hasattr(ai_client, 'ai_config'):
            print(f"  模型: {ai_client.ai_config.get('model', 'N/A')}")
            print(f"  Base URL: {ai_client.ai_config.get('base_url', 'N/A')}")
            print(f"  API Key: {'已配置' if ai_client.ai_config.get('api_key') else '未配置'}")
        
        # 测试AI调用
        print("\n🧪 测试AI调用:")
        try:
            response = ai_client.generate_text("请回复'测试成功'", max_tokens=50)
            print(f"  ✅ AI响应: {response[:100]}")
        except Exception as e:
            print(f"  ❌ AI调用失败: {str(e)}")
            
    except Exception as e:
        print(f"  ❌ 获取AI客户端失败: {str(e)}")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    check_ai_provider()
