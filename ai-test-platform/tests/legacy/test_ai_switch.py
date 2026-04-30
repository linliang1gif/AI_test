#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试AI模型切换功能
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_get_current_config():
    """测试获取当前配置"""
    print("=" * 60)
    print("1. 测试获取当前AI配置")
    print("=" * 60)
    
    response = requests.get(f"{BASE_URL}/api/ai/current")
    data = response.json()
    
    if data['success']:
        print(f"✅ 当前提供商: {data['provider']}")
        print(f"✅ 当前模型: {data['model']}")
        print(f"\n可用提供商:")
        for provider_id, provider_info in data['providers'].items():
            api_key_status = "✅" if provider_info['api_key_configured'] else "❌"
            print(f"  {api_key_status} {provider_info['name']} ({provider_id})")
            print(f"     模型: {', '.join(provider_info['models'])}")
    else:
        print(f"❌ 失败: {data.get('error')}")
    
    return data

def test_switch_provider(provider, model):
    """测试切换提供商"""
    print("\n" + "=" * 60)
    print(f"2. 测试切换到 {provider} - {model}")
    print("=" * 60)
    
    response = requests.post(
        f"{BASE_URL}/api/ai/providers/switch",
        json={"provider": provider, "model": model}
    )
    data = response.json()
    
    if data['success']:
        print(f"✅ {data['message']}")
    else:
        print(f"❌ 失败: {data.get('error')}")
    
    return data

def test_verify_switch():
    """验证切换是否生效"""
    print("\n" + "=" * 60)
    print("3. 验证切换是否生效")
    print("=" * 60)
    
    response = requests.get(f"{BASE_URL}/api/ai/current")
    data = response.json()
    
    if data['success']:
        print(f"✅ 当前提供商: {data['provider']}")
        print(f"✅ 当前模型: {data['model']}")
    else:
        print(f"❌ 失败: {data.get('error')}")
    
    return data

if __name__ == "__main__":
    print("\n🧪 AI模型切换功能测试\n")
    
    # 1. 获取当前配置
    current = test_get_current_config()
    
    # 2. 切换到不同的提供商
    if current['success']:
        current_provider = current['provider']
        
        # 如果当前是deepseek,切换到mock测试
        if current_provider == 'deepseek':
            test_switch_provider('mock', 'mock-model')
            test_verify_switch()
            # 切换回deepseek
            test_switch_provider('deepseek', 'deepseek-chat')
            test_verify_switch()
        else:
            # 切换到deepseek
            test_switch_provider('deepseek', 'deepseek-chat')
            test_verify_switch()
    
    print("\n" + "=" * 60)
    print("✅ 测试完成!")
    print("=" * 60)
