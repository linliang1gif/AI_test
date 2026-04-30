#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试Ollama连接API
"""

import requests
import json

def test_ollama_api():
    """测试后端Ollama连接API"""
    
    print("🔍 测试Ollama连接API...")
    
    # 1. 测试获取提供商列表
    try:
        print("\n1. 测试获取提供商列表...")
        response = requests.get("http://localhost:8000/api/ai/providers/list")
        print(f"状态码: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"提供商数量: {len(data.get('providers', []))}")
            for provider in data.get('providers', []):
                print(f"  - {provider['name']}: {provider['status']}")
        else:
            print(f"错误: {response.text}")
    except Exception as e:
        print(f"请求失败: {e}")
    
    # 2. 测试Ollama连接
    try:
        print("\n2. 测试Ollama连接...")
        response = requests.post("http://localhost:8000/api/ai/providers/ollama/test")
        print(f"状态码: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"连接结果: {data}")
            if data.get('success'):
                print("✅ Ollama连接成功")
            else:
                print(f"❌ Ollama连接失败: {data.get('message')}")
        else:
            print(f"错误: {response.text}")
    except Exception as e:
        print(f"请求失败: {e}")
    
    # 3. 直接测试Ollama服务
    try:
        print("\n3. 直接测试Ollama服务...")
        response = requests.get("http://localhost:11434/api/tags", timeout=3)
        print(f"状态码: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            models = [model["name"] for model in data.get("models", [])]
            print(f"✅ Ollama服务正常，可用模型: {models}")
        else:
            print(f"❌ Ollama服务异常: {response.text}")
    except Exception as e:
        print(f"❌ Ollama服务连接失败: {e}")

if __name__ == "__main__":
    test_ollama_api()