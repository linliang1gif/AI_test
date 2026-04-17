#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
直接测试 Ollama API
"""

import requests
import json

def test_ollama_api():
    """测试 Ollama API"""
    
    base_url = "http://localhost:11434"
    
    print("=" * 60)
    print("测试 Ollama API")
    print("=" * 60)
    
    # 测试 1: 获取模型列表
    print("\n测试 1: 获取模型列表")
    print("-" * 60)
    
    try:
        response = requests.get(f"{base_url}/api/tags")
        if response.status_code == 200:
            models = response.json()
            print(f"✅ 成功获取模型列表")
            print(f"📊 可用模型:")
            for model in models.get('models', []):
                print(f"  - {model['name']}")
        else:
            print(f"❌ 失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 异常: {e}")
        return False
    
    # 测试 2: 使用 /api/chat 端点
    print("\n\n测试 2: 使用 /api/chat 端点")
    print("-" * 60)
    
    try:
        payload = {
            "model": "qwen2.5-coder:latest",
            "messages": [
                {
                    "role": "user",
                    "content": "请用一句话介绍什么是软件测试"
                }
            ],
            "stream": False
        }
        
        print(f"🤖 使用模型: {payload['model']}")
        print(f"📝 提示词: {payload['messages'][0]['content']}")
        print(f"⏳ 正在调用 API...")
        
        response = requests.post(
            f"{base_url}/api/chat",
            json=payload,
            timeout=60
        )
        
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"\n✅ API 调用成功!")
            print(f"📄 完整响应:")
            print(json.dumps(result, indent=2, ensure_ascii=False))
            
            content = result.get('message', {}).get('content', '')
            print(f"\n📄 AI 响应:\n{content}")
            
            return True
        else:
            print(f"❌ API 调用失败: {response.status_code}")
            print(f"响应: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 测试 3: 使用 /api/generate 端点
    print("\n\n测试 3: 使用 /api/generate 端点")
    print("-" * 60)
    
    try:
        payload = {
            "model": "qwen2.5-coder:latest",
            "prompt": "请用一句话介绍什么是软件测试",
            "stream": False
        }
        
        print(f"🤖 使用模型: {payload['model']}")
        print(f"📝 提示词: {payload['prompt']}")
        print(f"⏳ 正在调用 API...")
        
        response = requests.post(
            f"{base_url}/api/generate",
            json=payload,
            timeout=60
        )
        
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"\n✅ API 调用成功!")
            print(f"📄 完整响应:")
            print(json.dumps(result, indent=2, ensure_ascii=False))
            
            content = result.get('response', '')
            print(f"\n📄 AI 响应:\n{content}")
            
            return True
        else:
            print(f"❌ API 调用失败: {response.status_code}")
            print(f"响应: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("\n🚀 Ollama API 测试\n")
    test_ollama_api()
