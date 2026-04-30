#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""测试Ollama API"""

import requests
import json

def test_ollama_generate():
    """测试/api/generate端点"""
    print("测试 /api/generate 端点...")
    
    url = "http://localhost:11434/api/generate"
    payload = {
        "model": "qwen2.5:1.5b",
        "prompt": "生成一个用户登录功能的测试用例,包含标题、测试步骤和预期结果",
        "stream": False,
        "options": {
            "temperature": 0.2,
            "num_predict": 500
        }
    }
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 成功!")
            print(f"响应内容: {result.get('response', '')[:200]}...")
            return True
        else:
            print(f"❌ 失败: {response.text}")
            return False
    except Exception as e:
        print(f"❌ 异常: {e}")
        return False

def test_ollama_chat():
    """测试/api/chat端点"""
    print("\n测试 /api/chat 端点...")
    
    url = "http://localhost:11434/api/chat"
    payload = {
        "model": "qwen2.5:1.5b",
        "messages": [
            {
                "role": "user",
                "content": "生成一个用户登录功能的测试用例,包含标题、测试步骤和预期结果"
            }
        ],
        "stream": False,
        "options": {
            "temperature": 0.2,
            "num_predict": 500
        }
    }
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 成功!")
            content = result.get('message', {}).get('content', '')
            print(f"响应内容: {content[:200]}...")
            return True
        else:
            print(f"❌ 失败: {response.text}")
            return False
    except Exception as e:
        print(f"❌ 异常: {e}")
        return False

if __name__ == "__main__":
    print("🔍 测试Ollama API端点\n")
    
    # 测试两个端点
    generate_ok = test_ollama_generate()
    chat_ok = test_ollama_chat()
    
    print("\n" + "="*50)
    print("测试结果:")
    print(f"/api/generate: {'✅ 可用' if generate_ok else '❌ 不可用'}")
    print(f"/api/chat: {'✅ 可用' if chat_ok else '❌ 不可用'}")
