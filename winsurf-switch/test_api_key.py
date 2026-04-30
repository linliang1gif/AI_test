#!/usr/bin/env python3
"""
测试 API Key 是否可用
"""
import requests
import json

def test_api_key(api_key, base_url="https://api.openai.com/v1"):
    """
    测试 API Key 是否有效
    
    Args:
        api_key: 要测试的 API key
        base_url: API 基础 URL，默认为 OpenAI 官方地址
    """
    print(f"🔍 开始测试 API Key...")
    print(f"📍 Base URL: {base_url}")
    print(f"🔑 API Key: {api_key[:20]}...{api_key[-10:]}")
    print("-" * 60)
    
    # 测试 1: 获取模型列表
    print("\n📋 测试 1: 获取可用模型列表")
    try:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        response = requests.get(
            f"{base_url}/models",
            headers=headers,
            timeout=10
        )
        
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            models = response.json()
            print(f"✅ 成功! 找到 {len(models.get('data', []))} 个模型")
            if models.get('data'):
                print("\n可用模型:")
                for model in models['data'][:5]:  # 只显示前5个
                    print(f"  - {model.get('id', 'unknown')}")
                if len(models['data']) > 5:
                    print(f"  ... 还有 {len(models['data']) - 5} 个模型")
        else:
            print(f"❌ 失败: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 请求失败: {str(e)}")
        return False
    
    # 测试 2: 发送简单的聊天请求
    print("\n💬 测试 2: 发送聊天请求")
    try:
        chat_data = {
            "model": "gpt-3.5-turbo",
            "messages": [
                {"role": "user", "content": "Say 'API test successful' in Chinese"}
            ],
            "max_tokens": 50
        }
        
        response = requests.post(
            f"{base_url}/chat/completions",
            headers=headers,
            json=chat_data,
            timeout=30
        )
        
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            message = result['choices'][0]['message']['content']
            print(f"✅ 成功! 回复: {message}")
            print(f"📊 使用 tokens: {result.get('usage', {})}")
        else:
            print(f"❌ 失败: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 请求失败: {str(e)}")
        return False
    
    print("\n" + "=" * 60)
    print("🎉 所有测试通过! API Key 可用")
    print("=" * 60)
    return True


if __name__ == "__main__":
    # 你的 API Key
    API_KEY = "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"
    
    # 如果是第三方 API，修改这个 URL
    # 例如: BASE_URL = "https://api.your-provider.com/v1"
    BASE_URL = "https://api.openai.com/v1"
    
    # 如果 API key 以 nvapi- 开头，可能是 NVIDIA 的 API
    if API_KEY.startswith("nvapi-"):
        print("🔔 检测到 NVIDIA API Key，切换到 NVIDIA 端点")
        BASE_URL = "https://integrate.api.nvidia.com/v1"
    
    test_api_key(API_KEY, BASE_URL)
