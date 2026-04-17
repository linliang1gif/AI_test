#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""诊断上传错误"""

import requests
import json
from pathlib import Path

print("=" * 60)
print("🔍 诊断上传错误")
print("=" * 60)

BASE_URL = "http://localhost:8000"

# 1. 检查后端服务器是否运行
print("\n1️⃣ 检查后端服务器:")
try:
    response = requests.get(f"{BASE_URL}/health", timeout=2)
    print(f"   ✅ 后端服务器运行正常")
    print(f"   状态码: {response.status_code}")
except requests.exceptions.ConnectionError:
    print(f"   ❌ 无法连接到后端服务器 {BASE_URL}")
    print(f"   请先启动后端: py backend_api_server.py")
    exit(1)
except Exception as e:
    print(f"   ⚠️  连接异常: {e}")

# 2. 测试Swagger上传端点
print("\n2️⃣ 测试Swagger上传端点:")
try:
    # 创建一个简单的Swagger文档
    swagger_doc = {
        "openapi": "3.0.0",
        "info": {"title": "Test", "version": "1.0.0"},
        "paths": {
            "/test": {
                "get": {"summary": "测试接口"}
            }
        }
    }
    
    files = {'file': ('test.json', json.dumps(swagger_doc).encode(), 'application/json')}
    
    print(f"   发送请求到: {BASE_URL}/api/swagger/upload")
    response = requests.post(f"{BASE_URL}/api/swagger/upload", files=files, timeout=10)
    
    print(f"   状态码: {response.status_code}")
    print(f"   Content-Type: {response.headers.get('content-type')}")
    print(f"   响应长度: {len(response.content)} bytes")
    
    # 尝试解析响应
    try:
        data = response.json()
        print(f"   ✅ JSON解析成功")
        print(f"   响应内容: {json.dumps(data, ensure_ascii=False, indent=2)}")
    except json.JSONDecodeError as e:
        print(f"   ❌ JSON解析失败: {e}")
        print(f"   原始响应文本:")
        print(f"   {response.text[:500]}")
        
except Exception as e:
    print(f"   ❌ 请求失败: {e}")
    import traceback
    traceback.print_exc()

# 3. 检查CORS配置
print("\n3️⃣ 检查CORS配置:")
try:
    headers = {
        'Origin': 'http://localhost:5173',
        'Access-Control-Request-Method': 'POST',
        'Access-Control-Request-Headers': 'content-type'
    }
    response = requests.options(f"{BASE_URL}/api/swagger/upload", headers=headers, timeout=2)
    print(f"   状态码: {response.status_code}")
    print(f"   CORS Headers:")
    for key, value in response.headers.items():
        if 'access-control' in key.lower():
            print(f"     {key}: {value}")
except Exception as e:
    print(f"   ⚠️  CORS检查失败: {e}")

# 4. 测试空文件上传
print("\n4️⃣ 测试空文件上传:")
try:
    files = {'file': ('empty.json', b'', 'application/json')}
    response = requests.post(f"{BASE_URL}/api/swagger/upload", files=files, timeout=10)
    print(f"   状态码: {response.status_code}")
    try:
        data = response.json()
        print(f"   响应: {json.dumps(data, ensure_ascii=False)}")
    except:
        print(f"   原始响应: {response.text[:200]}")
except Exception as e:
    print(f"   ❌ 请求失败: {e}")

# 5. 测试无效JSON上传
print("\n5️⃣ 测试无效JSON上传:")
try:
    files = {'file': ('invalid.json', b'{invalid}', 'application/json')}
    response = requests.post(f"{BASE_URL}/api/swagger/upload", files=files, timeout=10)
    print(f"   状态码: {response.status_code}")
    try:
        data = response.json()
        print(f"   响应: {json.dumps(data, ensure_ascii=False)}")
    except:
        print(f"   原始响应: {response.text[:200]}")
except Exception as e:
    print(f"   ❌ 请求失败: {e}")

print("\n" + "=" * 60)
print("📋 诊断建议:")
print("=" * 60)

print("""
如果看到"JSON解析失败",可能的原因:

1. 后端返回了HTML错误页面而不是JSON
   - 检查后端控制台的错误日志
   - 确认路由配置正确

2. 后端返回了空响应
   - 检查是否有未捕获的异常
   - 确认所有代码路径都返回JSONResponse

3. CORS问题
   - 确认后端CORS配置允许前端域名
   - 检查是否允许文件上传

4. 网络问题
   - 确认前端代理配置正确
   - 检查防火墙设置

下一步:
1. 查看后端控制台输出
2. 打开浏览器开发者工具 -> Network标签
3. 尝试上传文件,查看实际的HTTP请求和响应
4. 检查Response标签中的原始响应内容
""")
