#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试AI提供商API功能
"""

import requests
import json
import time

def test_ai_providers_api():
    """测试AI提供商API"""
    
    # 模拟AI提供商数据
    providers_data = {
        "providers": [
            {
                "id": "ollama",
                "name": "Ollama",
                "description": "本地AI模型服务",
                "type": "local",
                "status": "available",
                "models": ["qwen2.5:1.5b", "qwen2.5-coder:latest"],
                "default_model": "qwen2.5:1.5b",
                "config": {
                    "base_url": "http://localhost:11434",
                    "timeout": 60
                }
            },
            {
                "id": "deepseek",
                "name": "DeepSeek",
                "description": "DeepSeek AI API服务",
                "type": "cloud",
                "status": "available",
                "models": ["deepseek-chat", "deepseek-coder"],
                "default_model": "deepseek-chat",
                "config": {
                    "base_url": "https://api.deepseek.com",
                    "api_key": "sk-***"
                }
            },
            {
                "id": "openai",
                "name": "OpenAI",
                "description": "OpenAI GPT API服务",
                "type": "cloud",
                "status": "unavailable",
                "models": ["gpt-3.5-turbo", "gpt-4"],
                "default_model": "gpt-3.5-turbo",
                "config": {
                    "base_url": "https://api.openai.com/v1",
                    "api_key": ""
                }
            }
        ],
        "current": "ollama"
    }
    
    print("🧪 AI提供商API测试")
    print("=" * 50)
    
    # 检查Ollama服务状态
    print("\n1. 检查Ollama服务状态...")
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            models_data = response.json()
            models = [model["name"] for model in models_data.get("models", [])]
            print(f"✅ Ollama服务正常，发现模型: {models}")
            
            # 更新提供商数据中的模型列表
            for provider in providers_data["providers"]:
                if provider["id"] == "ollama":
                    provider["models"] = models
                    provider["status"] = "available"
                    break
        else:
            print(f"❌ Ollama服务异常: {response.status_code}")
            # 更新状态为不可用
            for provider in providers_data["providers"]:
                if provider["id"] == "ollama":
                    provider["status"] = "unavailable"
                    break
    except Exception as e:
        print(f"❌ 无法连接Ollama服务: {e}")
        for provider in providers_data["providers"]:
            if provider["id"] == "ollama":
                provider["status"] = "unavailable"
                break
    
    # 显示提供商信息
    print("\n2. 可用的AI提供商:")
    for provider in providers_data["providers"]:
        status_icon = "✅" if provider["status"] == "available" else "❌"
        type_label = "本地" if provider["type"] == "local" else "云端"
        print(f"  {status_icon} {provider['name']} ({type_label})")
        print(f"     描述: {provider['description']}")
        print(f"     状态: {provider['status']}")
        print(f"     模型: {len(provider['models'])} 个")
        if provider["models"]:
            print(f"     默认模型: {provider['default_model']}")
        print()
    
    # 测试模型选择逻辑
    print("3. 测试智能模型选择...")
    
    # 导入模型选择器
    try:
        from model_selector import ModelSelector
        
        selector = ModelSelector()
        
        test_cases = [
            {
                "prompt": "生成一个简单的API测试用例",
                "expected": "qwen2.5:1.5b"
            },
            {
                "prompt": "请用Python写一个复杂的API客户端",
                "expected": "qwen2.5-coder:latest"
            },
            {
                "prompt": "快速分析这个错误",
                "expected": "qwen2.5:1.5b"
            }
        ]
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"  测试 {i}: {test_case['prompt'][:30]}...")
            
            selection = selector.select_model(prompt=test_case["prompt"])
            selected_model = selection["model"]
            
            if selected_model == test_case["expected"]:
                print(f"    ✅ 选择正确: {selected_model}")
            else:
                print(f"    ⚠️  选择: {selected_model} (期望: {test_case['expected']})")
            
            print(f"    📝 原因: {selection['reason']}")
        
        print("\n✅ 模型选择器测试完成")
        
    except ImportError as e:
        print(f"⚠️  无法导入模型选择器: {e}")
    
    # 生成前端可用的API响应格式
    print("\n4. 生成前端API响应格式...")
    
    api_response = {
        "success": True,
        "data": providers_data,
        "timestamp": int(time.time())
    }
    
    print("API响应格式:")
    print(json.dumps(api_response, indent=2, ensure_ascii=False))
    
    # 保存到文件供前端测试使用
    with open("ai_providers_mock_data.json", "w", encoding="utf-8") as f:
        json.dump(api_response, f, indent=2, ensure_ascii=False)
    
    print(f"\n📁 模拟数据已保存到: ai_providers_mock_data.json")
    
    print("\n🎉 AI提供商API测试完成！")
    print("\n📋 前端集成建议:")
    print("1. 在前端页面加载时调用 /api/ai/providers/list")
    print("2. 显示提供商卡片，标识状态和类型")
    print("3. 允许用户点击切换提供商")
    print("4. 调用 /api/ai/providers/select 切换提供商")
    print("5. 实时检查提供商状态")

if __name__ == "__main__":
    test_ai_providers_api()