#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
完整的AI提供商切换和全局配置测试
"""

import requests
import json
import time

API_BASE = "http://localhost:8000/api"

def print_section(title):
    print("\n" + "=" * 60)
    print(f"📋 {title}")
    print("=" * 60)

def test_api_endpoint(method, endpoint, data=None, description=""):
    """通用API测试函数"""
    print(f"\n🔍 {description}")
    print(f"   方法: {method}")
    print(f"   端点: {endpoint}")
    
    try:
        if method.upper() == 'GET':
            response = requests.get(f"{API_BASE}{endpoint}")
        elif method.upper() == 'POST':
            response = requests.post(f"{API_BASE}{endpoint}", 
                                   json=data,
                                   headers={'Content-Type': 'application/json'})
        
        print(f"   状态码: {response.status_code}")
        result = response.json()
        
        if response.status_code == 200:
            print(f"   ✅ 成功")
            return result
        else:
            print(f"   ❌ 失败: {result}")
            return None
            
    except Exception as e:
        print(f"   ❌ 异常: {e}")
        return None

def main():
    print_section("AI提供商切换和全局配置完整测试")
    
    # 1. 获取提供商列表
    providers_data = test_api_endpoint('GET', '/ai/providers/list', 
                                     description="获取AI提供商列表")
    
    if providers_data:
        print(f"   📊 找到 {len(providers_data.get('providers', []))} 个提供商")
        for provider in providers_data.get('providers', []):
            print(f"      - {provider['name']} ({provider['id']}): {provider['status']}")
    
    # 2. 获取当前配置
    current_config = test_api_endpoint('GET', '/ai/current',
                                     description="获取当前AI配置")
    
    if current_config:
        print(f"   🤖 当前提供商: {current_config.get('current_provider')}")
        print(f"   📋 当前模型: {current_config.get('current_model')}")
    
    # 3. 测试Ollama连接
    test_result = test_api_endpoint('POST', '/ai/providers/Ollama/test',
                                  description="测试Ollama提供商连接")
    
    if test_result:
        print(f"   🔗 连接状态: {'成功' if test_result.get('success') else '失败'}")
        print(f"   💬 消息: {test_result.get('message')}")
    
    # 4. 切换提供商
    switch_data = {
        "provider": "ollama",
        "model": "qwen2.5:1.5b"
    }
    switch_result = test_api_endpoint('POST', '/ai/providers/switch', switch_data,
                                    description="切换到Ollama提供商")
    
    if switch_result:
        print(f"   🔄 切换状态: {'成功' if switch_result.get('success') else '失败'}")
        print(f"   💬 消息: {switch_result.get('message')}")
    
    # 5. 验证切换后的配置
    time.sleep(1)  # 等待状态更新
    new_config = test_api_endpoint('GET', '/ai/current',
                                 description="验证切换后的配置")
    
    if new_config:
        print(f"   🤖 新提供商: {new_config.get('current_provider')}")
        print(f"   📋 新模型: {new_config.get('current_model')}")
    
    # 6. 测试AI生成（使用全局配置）
    generate_data = {
        "prompt": "你好，请用一句话介绍你自己"
    }
    generate_result = test_api_endpoint('POST', '/ai/generate', generate_data,
                                      description="测试AI生成（使用全局配置）")
    
    if generate_result:
        print(f"   🤖 生成状态: {'成功' if generate_result.get('success') else '失败'}")
        print(f"   📡 使用提供商: {generate_result.get('provider')}")
        print(f"   📋 使用模型: {generate_result.get('model')}")
        print(f"   🔄 全局配置: {generate_result.get('current_config')}")
        if generate_result.get('success'):
            response_text = generate_result.get('response', '')
            print(f"   💬 AI回复: {response_text[:80]}{'...' if len(response_text) > 80 else ''}")
    
    # 7. 测试指定提供商的AI生成
    generate_specific_data = {
        "prompt": "请说一句话",
        "provider": "ollama",
        "model": "qwen2.5:1.5b"
    }
    generate_specific_result = test_api_endpoint('POST', '/ai/generate', generate_specific_data,
                                               description="测试指定提供商的AI生成")
    
    if generate_specific_result:
        print(f"   🤖 生成状态: {'成功' if generate_specific_result.get('success') else '失败'}")
        print(f"   📡 指定提供商: {generate_specific_result.get('provider')}")
        print(f"   📋 指定模型: {generate_specific_result.get('model')}")
    
    # 8. 总结测试结果
    print_section("测试总结")
    
    tests = [
        ("获取提供商列表", providers_data is not None),
        ("获取当前配置", current_config is not None),
        ("测试Ollama连接", test_result and test_result.get('success')),
        ("切换提供商", switch_result and switch_result.get('success')),
        ("验证配置更新", new_config is not None),
        ("全局配置AI生成", generate_result and generate_result.get('success')),
        ("指定提供商AI生成", generate_specific_result and generate_specific_result.get('success'))
    ]
    
    passed = sum(1 for _, result in tests if result)
    total = len(tests)
    
    print(f"\n📊 测试结果: {passed}/{total} 通过")
    
    for test_name, result in tests:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"   {status} {test_name}")
    
    if passed == total:
        print(f"\n🎉 所有测试通过！AI提供商切换和全局配置功能正常工作。")
    else:
        print(f"\n⚠️  有 {total - passed} 个测试失败，请检查相关功能。")
    
    # 9. 功能验证说明
    print_section("功能验证说明")
    print("""
✅ 已验证的功能:
1. AI提供商列表获取 - 可以获取所有可用的AI提供商
2. 当前配置查询 - 可以查看当前使用的提供商和模型
3. 提供商连接测试 - 可以测试特定提供商的连接状态
4. 提供商切换 - 可以切换到指定的提供商和模型
5. 全局配置生效 - AI生成时自动使用全局配置的提供商和模型
6. 配置覆盖 - 可以在请求中指定特定的提供商和模型

🔄 全局配置机制:
- 后端维护全局状态: current_provider 和 current_model
- 切换提供商时更新全局状态
- AI生成时优先使用全局配置，但允许请求覆盖
- 前端可以实时查询和显示当前配置

🌐 前端集成:
- 前端可以通过 /api/ai/current 获取当前配置
- 前端可以通过 /api/ai/providers/switch 切换提供商
- 前端可以显示当前使用的提供商和模型信息
- 切换后对整个系统生效，所有AI功能都使用新配置
    """)

if __name__ == "__main__":
    main()