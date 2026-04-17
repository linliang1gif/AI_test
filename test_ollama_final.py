#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
最终测试 Ollama 集成
"""

import sys
import os
from pathlib import Path

# 清除环境变量缓存
if 'OLLAMA_MODELS' in os.environ:
    del os.environ['OLLAMA_MODELS']

# 重新加载环境变量
from dotenv import load_dotenv
load_dotenv(override=True)  # 强制覆盖

# 添加路径
sys.path.insert(0, str(Path(__file__).parent / 'ai-test-platform'))

def test_ollama():
    """测试 Ollama 集成"""
    print("=" * 60)
    print("测试 Ollama 集成")
    print("=" * 60)
    
    # 检查环境变量
    print("\n1. 环境变量检查:")
    print(f"  OLLAMA_MODELS: {os.getenv('OLLAMA_MODELS')}")
    print(f"  DEFAULT_AI_MODEL: {os.getenv('DEFAULT_AI_MODEL')}")
    print(f"  DEFAULT_AI_PROVIDER: {os.getenv('DEFAULT_AI_PROVIDER')}")
    
    # 检查配置
    print("\n2. 配置检查:")
    from config.config import get_config
    config = get_config()
    print(f"  Provider: {config.ai.default_provider}")
    print(f"  Model: {config.ai.default_model}")
    print(f"  Ollama models: {config.ai.ollama_models}")
    
    ollama_config = config.get_ai_config_for_provider('ollama')
    print(f"  Ollama config model: {ollama_config['model']}")
    
    # 测试 AI 客户端
    print("\n3. AI 客户端测试:")
    from ai.ai_client import AIClient
    
    client = AIClient(provider="ollama")
    print(f"  ✅ 客户端创建成功")
    print(f"  Provider: {client.provider}")
    print(f"  Model: {client.ai_config['model']}")
    
    # 测试生成
    print("\n4. 文本生成测试:")
    try:
        response = client.generate_text(
            prompt="请用一句话介绍什么是软件测试",
            system_prompt="你是一个专业的软件测试工程师",
            temperature=0.2
        )
        
        print(f"  ✅ 生成成功!")
        print(f"  响应: {response}")
        return True
        
    except Exception as e:
        print(f"  ❌ 生成失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("\n🚀 Ollama 集成最终测试\n")
    
    success = test_ollama()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 测试通过！Ollama 集成正常工作！")
    else:
        print("❌ 测试失败")
    print("=" * 60)
