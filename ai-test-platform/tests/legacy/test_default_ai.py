#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试默认AI配置功能
"""

import requests
import json

def test_current_config():
    """测试获取当前AI配置"""
    print("🔍 测试获取当前AI配置...")
    
    try:
        response = requests.get("http://localhost:8000/api/ai/current")
        if response.status_code == 200:
            config = response.json()
            print(f"✅ 当前配置: {config['current_provider']} ({config['current_model']})")
            return config
        else:
            print(f"❌ 获取配置失败: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return None

def test_ai_generation():
    """测试AI文本生成（使用默认配置）"""
    print("\n🤖 测试AI文本生成...")
    
    test_prompt = "你好，请简单介绍一下你自己"
    
    try:
        response = requests.post(
            "http://localhost:8000/api/ai/generate",
            json={"prompt": test_prompt},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                print(f"✅ AI生成成功")
                print(f"📝 提示: {test_prompt}")
                print(f"🤖 回复: {result['response'][:100]}...")
                print(f"🔧 使用模型: {result.get('provider', 'unknown')} ({result.get('model', 'unknown')})")
                return True
            else:
                print(f"❌ AI生成失败: {result.get('error', 'Unknown error')}")
                return False
        else:
            print(f"❌ 请求失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 请求异常: {e}")
        return False

def test_providers_list():
    """测试获取提供商列表"""
    print("\n📋 测试获取提供商列表...")
    
    try:
        response = requests.get("http://localhost:8000/api/ai/providers/list")
        if response.status_code == 200:
            data = response.json()
            providers = data.get("providers", [])
            current = data.get("current", "unknown")
            
            print(f"✅ 获取到 {len(providers)} 个提供商")
            print(f"🎯 当前默认: {current}")
            
            for provider in providers:
                status_icon = "✅" if provider["status"] == "available" else "❌"
                print(f"  {status_icon} {provider['name']} ({provider['id']}) - {provider['status']}")
            
            return True
        else:
            print(f"❌ 获取失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🚀 开始测试默认AI配置功能")
    print("=" * 50)
    
    # 测试1: 获取当前配置
    config = test_current_config()
    
    # 测试2: 获取提供商列表
    providers_ok = test_providers_list()
    
    # 测试3: AI文本生成
    generation_ok = test_ai_generation()
    
    print("\n" + "=" * 50)
    print("📊 测试结果汇总:")
    print(f"  配置获取: {'✅' if config else '❌'}")
    print(f"  提供商列表: {'✅' if providers_ok else '❌'}")
    print(f"  AI文本生成: {'✅' if generation_ok else '❌'}")
    
    if config and providers_ok and generation_ok:
        print("\n🎉 所有测试通过！默认AI配置功能正常工作")
        print(f"🎯 默认使用: {config['current_provider']} ({config['current_model']})")
        print("💡 用户无需手动切换，直接使用AI功能即可")
    else:
        print("\n⚠️  部分测试失败，请检查服务配置")

if __name__ == "__main__":
    main()