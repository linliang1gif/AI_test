#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试所有API端点的连通性
"""

import requests
import json

def test_api_endpoint(url, method='GET', data=None):
    """测试API端点"""
    try:
        if method == 'GET':
            response = requests.get(url, timeout=5)
        elif method == 'POST':
            response = requests.post(url, json=data, timeout=5)
        
        print(f"✅ {method} {url} - Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"   Response: {json.dumps(result, ensure_ascii=False, indent=2)[:200]}...")
        return True
    except Exception as e:
        print(f"❌ {method} {url} - Error: {e}")
        return False

def main():
    """测试所有API端点"""
    base_url = "http://localhost:8000/api"
    
    print("🔍 测试AI提供商API端点...")
    print("=" * 50)
    
    # 测试提供商列表
    test_api_endpoint(f"{base_url}/ai/providers/list")
    
    # 测试Ollama状态
    test_api_endpoint(f"{base_url}/ai/providers/ollama/status")
    
    # 测试DeepSeek状态
    test_api_endpoint(f"{base_url}/ai/providers/deepseek/status")
    
    # 测试OpenAI状态
    test_api_endpoint(f"{base_url}/ai/providers/openai/status")
    
    # 测试选择提供商
    test_api_endpoint(f"{base_url}/ai/providers/select", 'POST', {'provider_id': 'ollama'})
    
    # 测试仪表板
    test_api_endpoint(f"{base_url}/dashboard/stats")
    
    print("\n🔍 测试Ollama直接连接...")
    print("=" * 50)
    
    # 直接测试Ollama
    test_api_endpoint("http://localhost:11434/api/tags")
    
    print("\n✅ 测试完成!")

if __name__ == "__main__":
    main()