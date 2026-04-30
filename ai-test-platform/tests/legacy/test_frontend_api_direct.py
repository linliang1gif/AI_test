#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
直接模拟前端API调用
"""

import requests
import json

def test_frontend_api_calls():
    """模拟前端的API调用"""
    
    print("🔍 模拟前端API调用...")
    
    # 1. 获取提供商列表（模拟前端调用）
    try:
        print("\n1. 获取提供商列表...")
        response = requests.get("http://127.0.0.1:8000/api/ai/providers/list")
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            providers = data.get('providers', [])
            print(f"提供商数量: {len(providers)}")
            
            # 找到Ollama提供商
            ollama_provider = None
            for provider in providers:
                print(f"  - ID: {provider['id']}, Name: {provider['name']}, Status: {provider['status']}")
                if provider['id'] == 'ollama':
                    ollama_provider = provider
            
            if ollama_provider:
                print(f"\n找到Ollama提供商: {ollama_provider}")
                
                # 2. 测试Ollama连接（使用正确的ID）
                print(f"\n2. 测试Ollama连接 (ID: {ollama_provider['id']})...")
                test_url = f"http://127.0.0.1:8000/api/ai/providers/{ollama_provider['id']}/test"
                print(f"请求URL: {test_url}")
                
                response = requests.post(test_url, headers={'Content-Type': 'application/json'})
                print(f"状态码: {response.status_code}")
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"测试结果: {json.dumps(result, indent=2, ensure_ascii=False)}")
                    
                    if result.get('success'):
                        print("✅ 前端API调用成功")
                    else:
                        print(f"❌ 连接失败: {result.get('message')}")
                else:
                    print(f"❌ HTTP错误: {response.text}")
            else:
                print("❌ 未找到Ollama提供商")
        else:
            print(f"❌ 获取提供商列表失败: {response.text}")
            
    except Exception as e:
        print(f"❌ 请求异常: {e}")

if __name__ == "__main__":
    test_frontend_api_calls()