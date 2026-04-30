#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试Ollama集成的脚本

用于验证Ollama本地模型是否正确集成到AI测试平台中
"""

import asyncio
import sys
from pathlib import Path

# 添加项目路径
sys.path.append(str(Path(__file__).parent))

from ai.enhanced_ai_client import get_enhanced_ai_client
from ai.provider_manager import get_provider_manager
from config.config import get_config

async def test_ollama_integration():
    """测试Ollama集成"""
    print("🧪 开始测试Ollama集成...")
    print("=" * 60)
    
    # 1. 测试配置加载
    print("\n1️⃣ 测试配置加载...")
    try:
        config = get_config()
        print(f"✅ 配置加载成功")
        print(f"   - Ollama Base URL: {config.ai.ollama_base_url}")
        print(f"   - 可用模型: {config.ai.ollama_models}")
        print(f"   - 默认提供商: {config.ai.default_provider}")
    except Exception as e:
        print(f"❌ 配置加载失败: {e}")
        return False
    
    # 2. 测试Ollama连接
    print("\n2️⃣ 测试Ollama连接...")
    try:
        ollama_client = get_enhanced_ai_client("ollama")
        is_available = ollama_client.is_available()
        
        if is_available:
            print("✅ Ollama服务连接成功")
            
            # 获取可用模型
            models = ollama_client.get_available_models()
            print(f"   - 可用模型: {models}")
        else:
            print("❌ Ollama服务不可用")
            print("   请确保Ollama服务正在运行: ollama serve")
            return False
            
    except Exception as e:
        print(f"❌ Ollama连接失败: {e}")
        return False
    
    # 3. 测试AI提供商管理器
    print("\n3️⃣ 测试AI提供商管理器...")
    try:
        provider_manager = get_provider_manager()
        
        # 检查所有提供商状态
        for provider_name in ["deepseek", "ollama", "openai"]:
            status = provider_manager.check_provider_status(provider_name)
            print(f"   - {provider_name}: {status.value}")
        
        # 获取统计信息
        stats = provider_manager.get_provider_stats()
        print(f"✅ 提供商管理器工作正常")
        
    except Exception as e:
        print(f"❌ 提供商管理器测试失败: {e}")
        return False
    
    # 4. 测试文本生成
    print("\n4️⃣ 测试文本生成...")
    try:
        # 测试简单的文本生成
        test_prompt = "请简单介绍一下软件测试的重要性，用一句话回答。"
        
        print(f"   提示词: {test_prompt}")
        print("   正在生成...")
        
        response = ollama_client.generate_text(
            test_prompt,
            system_prompt="你是一个专业的软件测试工程师。",
            max_tokens=100
        )
        
        print(f"✅ 文本生成成功")
        print(f"   响应: {response[:100]}...")
        
    except Exception as e:
        print(f"❌ 文本生成失败: {e}")
        return False
    
    # 5. 测试fallback机制
    print("\n5️⃣ 测试fallback机制...")
    try:
        provider_manager = get_provider_manager()
        
        # 测试优先使用本地模型
        response, used_provider = provider_manager.generate_with_fallback(
            "Hello, this is a test.",
            prefer_local=True,
            max_tokens=20
        )
        
        print(f"✅ Fallback机制工作正常")
        print(f"   使用的提供商: {used_provider}")
        print(f"   响应: {response[:50]}...")
        
    except Exception as e:
        print(f"❌ Fallback机制测试失败: {e}")
        return False
    
    # 6. 测试测试用例生成
    print("\n6️⃣ 测试测试用例生成...")
    try:
        test_prompt = """
基于以下需求，生成一个测试用例，以JSON格式返回：
需求：用户登录功能

请返回格式：
{
  "title": "测试用例标题",
  "steps": ["步骤1", "步骤2"],
  "expected": "预期结果"
}
"""
        
        response = ollama_client.generate_text(
            test_prompt,
            system_prompt="你是一个专业的测试工程师，擅长生成测试用例。",
            max_tokens=200
        )
        
        print(f"✅ 测试用例生成成功")
        print(f"   响应: {response[:200]}...")
        
    except Exception as e:
        print(f"❌ 测试用例生成失败: {e}")
        return False
    
    print("\n" + "=" * 60)
    print("🎉 Ollama集成测试完成！所有测试都通过了。")
    print("\n📋 测试总结:")
    print("✅ 配置加载正常")
    print("✅ Ollama服务连接成功")
    print("✅ 提供商管理器工作正常")
    print("✅ 文本生成功能正常")
    print("✅ Fallback机制正常")
    print("✅ 测试用例生成功能正常")
    
    print("\n🚀 现在可以在AI测试平台中使用Ollama了！")
    print("   1. 启动后端服务: python backend_api_server.py")
    print("   2. 启动前端服务: cd frontend && npm run dev")
    print("   3. 在AI分析页面中切换到Ollama提供商")
    
    return True

def check_ollama_service():
    """检查Ollama服务状态"""
    import requests
    
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get("models", [])
            return True, models
        else:
            return False, []
    except:
        return False, []

def main():
    """主函数"""
    print("🔍 检查Ollama服务状态...")
    
    is_running, models = check_ollama_service()
    
    if not is_running:
        print("❌ Ollama服务未运行")
        print("\n📝 请按以下步骤启动Ollama:")
        print("1. 安装Ollama: 访问 https://ollama.ai")
        print("2. 启动服务: ollama serve")
        print("3. 下载模型: ollama pull deepseek-coder")
        print("4. 重新运行此测试脚本")
        return
    
    print(f"✅ Ollama服务正在运行")
    print(f"   已安装模型: {[model['name'] for model in models]}")
    
    if not models:
        print("\n⚠️  未发现已安装的模型")
        print("请先下载模型:")
        print("   ollama pull deepseek-coder")
        print("   ollama pull qwen2.5")
        return
    
    # 运行集成测试
    try:
        asyncio.run(test_ollama_integration())
    except KeyboardInterrupt:
        print("\n\n⏹️  测试被用户中断")
    except Exception as e:
        print(f"\n\n❌ 测试过程中发生错误: {e}")

if __name__ == "__main__":
    main()