#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试AI提供商切换API
"""

import requests
import json

API_BASE = "http://localhost:8000/api"

def test_current_config():
    """测试获取当前配置"""
    print("🔍 测试获取当前配置...")
    try:
        response = requests.get(f"{API_BASE}/ai/current")
        print(f"状态码: {response.status_code}")
        print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        return response.json()
    except Exception as e:
        print(f"❌ 错误: {e}")
        return None

def test_switch_provider():
    """测试切换提供商"""
    print("\n🔄 测试切换提供商...")
    try:
        data = {
            "provider": "ollama",
            "model": "qwen2.5:1.5b"
        }
        response = requests.post(f"{API_BASE}/ai/providers/switch", 
                               json=data,
                               headers={'Content-Type': 'application/json'})
        print(f"状态码: {response.status_code}")
        print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        return response.json()
    except Exception as e:
        print(f"❌ 错误: {e}")
        return None

def test_ai_generate():
    """测试AI生成（使用全局配置）"""
    print("\n🤖 测试AI生成...")
    try:
        data = {
            "prompt": "你好，请简单介绍一下你自己"
        }
        response = requests.post(f"{API_BASE}/ai/generate", 
                               json=data,
                               headers={'Content-Type': 'application/json'})
        print(f"状态码: {response.status_code}")
        result = response.json()
        print(f"成功: {result.get('success')}")
        print(f"使用提供商: {result.get('provider')}")
        print(f"使用模型: {result.get('model')}")
        print(f"全局配置: {result.get('current_config')}")
        if result.get('success'):
            print(f"AI回复: {result.get('response')[:100]}...")
        else:
            print(f"错误: {result.get('error')}")
        return result
    except Exception as e:
        print(f"❌ 错误: {e}")
        return None

def main():
    print("=" * 50)
    print("🧪 AI提供商切换功能测试")
    print("=" * 50)
    
    # 1. 获取当前配置
    current = test_current_config()
    
    # 2. 测试切换提供商
    switch_result = test_switch_provider()
    
    # 3. 再次获取配置验证切换
    print("\n🔍 验证切换后的配置...")
    current_after = test_current_config()
    
    # 4. 测试AI生成
    generate_result = test_ai_generate()
    
    print("\n" + "=" * 50)
    print("📊 测试总结")
    print("=" * 50)
    
    if current:
        print(f"✅ 获取当前配置: 成功")
    else:
        print(f"❌ 获取当前配置: 失败")
    
    if switch_result and switch_result.get('success'):
        print(f"✅ 切换提供商: 成功")
    else:
        print(f"❌ 切换提供商: 失败")
    
    if generate_result and generate_result.get('success'):
        print(f"✅ AI生成: 成功")
        print(f"   - 使用提供商: {generate_result.get('provider')}")
        print(f"   - 使用模型: {generate_result.get('model')}")
    else:
        print(f"❌ AI生成: 失败")

if __name__ == "__main__":
    main()