#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""测试上传功能修复"""

import requests
import json
from pathlib import Path

print("=" * 60)
print("🧪 测试上传功能修复")
print("=" * 60)

BASE_URL = "http://localhost:8000"

# 1. 测试Swagger上传 - 空文件
print("\n1️⃣ 测试空文件上传:")
try:
    files = {'file': ('empty.json', b'', 'application/json')}
    response = requests.post(f"{BASE_URL}/api/swagger/upload", files=files)
    print(f"   状态码: {response.status_code}")
    print(f"   响应头: {response.headers.get('content-type')}")
    
    try:
        data = response.json()
        print(f"   ✅ JSON解析成功: {data}")
    except Exception as e:
        print(f"   ❌ JSON解析失败: {e}")
        print(f"   原始响应: {response.text[:200]}")
except Exception as e:
    print(f"   ❌ 请求失败: {e}")

# 2. 测试Swagger上传 - 无效JSON
print("\n2️⃣ 测试无效JSON上传:")
try:
    files = {'file': ('invalid.json', b'{invalid json}', 'application/json')}
    response = requests.post(f"{BASE_URL}/api/swagger/upload", files=files)
    print(f"   状态码: {response.status_code}")
    
    try:
        data = response.json()
        print(f"   ✅ JSON解析成功: {data}")
    except Exception as e:
        print(f"   ❌ JSON解析失败: {e}")
        print(f"   原始响应: {response.text[:200]}")
except Exception as e:
    print(f"   ❌ 请求失败: {e}")

# 3. 测试Swagger上传 - 有效但无paths的JSON
print("\n3️⃣ 测试无paths的Swagger文档:")
try:
    swagger_doc = {
        "openapi": "3.0.0",
        "info": {"title": "Test API", "version": "1.0.0"}
    }
    files = {'file': ('no-paths.json', json.dumps(swagger_doc).encode(), 'application/json')}
    response = requests.post(f"{BASE_URL}/api/swagger/upload", files=files)
    print(f"   状态码: {response.status_code}")
    
    try:
        data = response.json()
        print(f"   ✅ JSON解析成功: {data}")
    except Exception as e:
        print(f"   ❌ JSON解析失败: {e}")
        print(f"   原始响应: {response.text[:200]}")
except Exception as e:
    print(f"   ❌ 请求失败: {e}")

# 4. 测试Swagger上传 - 有效的Swagger文档
print("\n4️⃣ 测试有效的Swagger文档:")
try:
    swagger_doc = {
        "openapi": "3.0.0",
        "info": {"title": "Test API", "version": "1.0.0"},
        "paths": {
            "/api/users": {
                "get": {
                    "summary": "获取用户列表",
                    "description": "返回所有用户",
                    "tags": ["用户管理"]
                },
                "post": {
                    "summary": "创建用户",
                    "description": "创建新用户",
                    "tags": ["用户管理"]
                }
            },
            "/api/users/{id}": {
                "get": {
                    "summary": "获取用户详情",
                    "description": "根据ID获取用户",
                    "tags": ["用户管理"]
                }
            }
        }
    }
    files = {'file': ('valid-swagger.json', json.dumps(swagger_doc).encode(), 'application/json')}
    response = requests.post(f"{BASE_URL}/api/swagger/upload", files=files)
    print(f"   状态码: {response.status_code}")
    
    try:
        data = response.json()
        print(f"   ✅ JSON解析成功")
        print(f"   成功: {data.get('success')}")
        print(f"   消息: {data.get('message')}")
        print(f"   API数量: {data.get('count')}")
    except Exception as e:
        print(f"   ❌ JSON解析失败: {e}")
        print(f"   原始响应: {response.text[:200]}")
except Exception as e:
    print(f"   ❌ 请求失败: {e}")

# 5. 测试获取API列表
print("\n5️⃣ 测试获取API列表:")
try:
    response = requests.get(f"{BASE_URL}/api/apis")
    print(f"   状态码: {response.status_code}")
    
    try:
        data = response.json()
        print(f"   ✅ JSON解析成功")
        print(f"   API数量: {len(data)}")
        if data:
            print(f"   第一个API: {data[0].get('method')} {data[0].get('path')}")
    except Exception as e:
        print(f"   ❌ JSON解析失败: {e}")
except Exception as e:
    print(f"   ❌ 请求失败: {e}")

print("\n" + "=" * 60)
print("✅ 测试完成")
print("=" * 60)
