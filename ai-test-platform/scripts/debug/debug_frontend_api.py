#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
调试前端API连接问题
"""

import requests
import json

def test_cors_and_api():
    """测试CORS和API连接"""
    
    print("🔍 调试前端API连接问题")
    print("=" * 50)
    
    # 测试API端点
    api_url = "http://localhost:8000/api/ai/providers/list"
    
    print(f"1. 测试API端点: {api_url}")
    
    try:
        # 模拟浏览器请求
        headers = {
            'Origin': 'http://localhost:3000',
            'Referer': 'http://localhost:3000/',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(api_url, headers=headers, timeout=5)
        
        print(f"   状态码: {response.status_code}")
        print(f"   响应头: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ API响应正常")
            print(f"   📊 提供商数量: {len(data.get('providers', []))}")
            
            # 显示提供商信息
            for provider in data.get('providers', []):
                status_icon = "✅" if provider['status'] == 'available' else "❌"
                print(f"     {status_icon} {provider['name']} ({provider['type']})")
        else:
            print(f"   ❌ API响应异常")
            
    except Exception as e:
        print(f"   ❌ 请求失败: {e}")
    
    # 测试CORS预检请求
    print(f"\n2. 测试CORS预检请求")
    
    try:
        response = requests.options(
            api_url,
            headers={
                'Origin': 'http://localhost:3000',
                'Access-Control-Request-Method': 'GET',
                'Access-Control-Request-Headers': 'Content-Type'
            },
            timeout=5
        )
        
        print(f"   OPTIONS状态码: {response.status_code}")
        print(f"   CORS头: {response.headers.get('Access-Control-Allow-Origin', '未设置')}")
        
        if response.status_code == 200:
            print(f"   ✅ CORS预检通过")
        else:
            print(f"   ❌ CORS预检失败")
            
    except Exception as e:
        print(f"   ❌ CORS测试失败: {e}")
    
    # 测试POST请求
    print(f"\n3. 测试POST请求 (选择提供商)")
    
    try:
        post_url = "http://localhost:8000/api/ai/providers/select"
        post_data = {"provider_id": "ollama"}
        
        response = requests.post(
            post_url,
            json=post_data,
            headers={
                'Origin': 'http://localhost:3000',
                'Content-Type': 'application/json'
            },
            timeout=5
        )
        
        print(f"   POST状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ POST请求成功")
            print(f"   📝 响应: {data.get('message', '')}")
        else:
            print(f"   ❌ POST请求失败")
            
    except Exception as e:
        print(f"   ❌ POST测试失败: {e}")
    
    # 生成前端调试建议
    print(f"\n📋 前端调试建议:")
    print("=" * 50)
    
    suggestions = [
        "1. 打开浏览器开发者工具 (F12)",
        "2. 进入 Network 标签页",
        "3. 访问 AI Insights 页面",
        "4. 点击 'AI Provider Settings' 按钮",
        "5. 查看是否有API请求发出",
        "6. 检查请求URL是否正确: http://localhost:8000/api/ai/providers/list",
        "7. 查看响应状态和数据",
        "8. 检查Console标签页是否有错误信息"
    ]
    
    for suggestion in suggestions:
        print(f"   {suggestion}")
    
    print(f"\n🔧 如果仍有问题，请检查:")
    print("   • 后端服务是否运行在端口8000")
    print("   • 前端服务是否运行在端口3000") 
    print("   • 浏览器是否阻止了跨域请求")
    print("   • API路径配置是否正确")

if __name__ == "__main__":
    test_cors_and_api()