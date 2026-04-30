#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""测试 OpenRouter API Key"""

import requests
import json

# 你的 API Key
API_KEY = "sk-rUFvwaIZ7RJIB9cVRteHR4aI1P7xT8570VhMF5NFpRr77KMz"
BASE_URL = "https://openrouter.ai/api/v1"

def test_openrouter():
    """测试 OpenRouter API"""
    
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "HTTP-Referer": "http://localhost:8000",
        "X-Title": "AI Test Platform",
        "Content-Type": "application/json"
    }
    
    # 尝试不同的模型
    models_to_try = [
        "openai/gpt-3.5-turbo",
        "google/gemini-flash-1.5",
        "meta-llama/llama-3.2-3b-instruct:free"
    ]
    
    for model in models_to_try:
        payload = {
            "model": model,
            "messages": [
                {"role": "user", "content": "Hello, please respond with 'Test successful'"}
            ]
        }
        
        print(f"\n🧪 测试模型: {model}")
        print(f"API Key: {API_KEY[:20]}...")
        print(f"URL: {BASE_URL}/chat/completions")
        print()
        
        try:
            response = requests.post(
                f"{BASE_URL}/chat/completions",
                headers=headers,
                json=payload,
                timeout=30
            )
            
            print(f"状态码: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print("✅ API 调用成功!")
                print(f"响应: {json.dumps(result, indent=2, ensure_ascii=False)[:500]}")
                return True
            else:
                print(f"❌ API 调用失败!")
                print(f"错误信息: {response.text}")
                
        except Exception as e:
            print(f"❌ 请求异常: {e}")
    
    return False

if __name__ == "__main__":
    test_openrouter()
