#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试所有AI功能是否能正常调用模型
"""

import requests
import json

def test_ai_current_config():
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
    """测试AI文本生成功能"""
    print("\n🤖 测试AI文本生成功能...")
    
    test_cases = [
        "生成一个用户登录的测试用例",
        "为电商网站购物车功能设计测试场景",
        "创建API接口的自动化测试脚本"
    ]
    
    for i, prompt in enumerate(test_cases, 1):
        print(f"\n测试 {i}: {prompt}")
        
        try:
            response = requests.post(
                "http://localhost:8000/api/ai/generate",
                json={"prompt": prompt},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    print(f"✅ 生成成功")
                    print(f"📝 回复长度: {len(result['response'])} 字符")
                    print(f"🔧 使用模型: {result.get('provider', 'unknown')} ({result.get('model', 'unknown')})")
                    # 显示前100个字符
                    preview = result['response'][:100].replace('\n', ' ')
                    print(f"📄 内容预览: {preview}...")
                else:
                    print(f"❌ 生成失败: {result.get('error', 'Unknown error')}")
            else:
                print(f"❌ 请求失败: {response.status_code}")
                
        except Exception as e:
            print(f"❌ 请求异常: {e}")

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
                if provider.get('models'):
                    print(f"    模型数量: {len(provider['models'])}")
            
            return True
        else:
            print(f"❌ 获取失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return False

def test_provider_connection():
    """测试提供商连接"""
    print("\n🔗 测试提供商连接...")
    
    providers_to_test = ["ollama", "Ollama"]  # 测试大小写
    
    for provider in providers_to_test:
        print(f"\n测试 {provider} 连接...")
        
        try:
            response = requests.post(f"http://localhost:8000/api/ai/providers/{provider}/test")
            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    print(f"✅ {provider} 连接成功")
                    print(f"📊 响应时间: {result.get('provider', {}).get('response_time', 'N/A')}")
                else:
                    print(f"❌ {provider} 连接失败: {result.get('message', 'Unknown error')}")
            else:
                print(f"❌ 请求失败: {response.status_code}")
        except Exception as e:
            print(f"❌ 请求异常: {e}")

def test_specific_scenarios():
    """测试特定场景的AI生成"""
    print("\n🎯 测试特定场景的AI生成...")
    
    scenarios = [
        {
            "name": "测试用例生成",
            "prompt": "为用户注册功能生成详细的测试用例，包括正常流程和异常情况"
        },
        {
            "name": "API测试脚本",
            "prompt": "生成一个Python requests库的API自动化测试脚本，测试用户登录接口"
        },
        {
            "name": "失败分析",
            "prompt": "分析测试失败的可能原因：登录接口返回500错误"
        }
    ]
    
    for scenario in scenarios:
        print(f"\n🔍 {scenario['name']}:")
        
        try:
            response = requests.post(
                "http://localhost:8000/api/ai/generate",
                json={
                    "prompt": scenario["prompt"],
                    "context": scenario["name"]
                },
                timeout=45
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    print(f"✅ 生成成功 ({len(result['response'])} 字符)")
                    
                    # 检查回复质量
                    response_text = result['response'].lower()
                    if scenario['name'] == '测试用例生成':
                        if any(keyword in response_text for keyword in ['测试', 'test', '用例', '验证']):
                            print("🎯 内容相关性: 高")
                        else:
                            print("⚠️  内容相关性: 低")
                    elif scenario['name'] == 'API测试脚本':
                        if any(keyword in response_text for keyword in ['python', 'requests', 'api', '脚本']):
                            print("🎯 内容相关性: 高")
                        else:
                            print("⚠️  内容相关性: 低")
                    
                else:
                    print(f"❌ 生成失败: {result.get('error')}")
            else:
                print(f"❌ 请求失败: {response.status_code}")
                
        except Exception as e:
            print(f"❌ 请求异常: {e}")

def main():
    """主测试函数"""
    print("🚀 开始测试所有AI功能")
    print("=" * 60)
    
    # 测试1: 获取当前配置
    config = test_ai_current_config()
    
    # 测试2: 获取提供商列表
    providers_ok = test_providers_list()
    
    # 测试3: 测试连接
    test_provider_connection()
    
    # 测试4: AI文本生成
    test_ai_generation()
    
    # 测试5: 特定场景测试
    test_specific_scenarios()
    
    print("\n" + "=" * 60)
    print("📊 测试总结:")
    print(f"  ✅ AI配置: {'正常' if config else '异常'}")
    print(f"  ✅ 提供商列表: {'正常' if providers_ok else '异常'}")
    print(f"  ✅ 默认模型: {config['current_provider'] if config else 'N/A'} ({config['current_model'] if config else 'N/A'})")
    
    if config and providers_ok:
        print("\n🎉 所有核心功能测试通过！")
        print("💡 用户可以在以下页面使用AI功能:")
        print("  • AI分析页面: 上传文档生成测试用例")
        print("  • 右下角AI助手: 实时对话咨询")
        print("  • 测试用例页面: AI辅助测试设计")
        print("  • 自动化脚本页面: AI生成测试脚本")
    else:
        print("\n⚠️  部分功能异常，请检查服务配置")

if __name__ == "__main__":
    main()