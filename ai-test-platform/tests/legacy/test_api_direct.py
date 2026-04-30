#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
直接测试API端点
"""

import requests
import time
import subprocess
import sys

print("=" * 60)
print("直接测试后端API")
print("=" * 60)

# 测试API是否可访问
api_url = "http://localhost:8000/api/v2/projects"

print(f"\n测试URL: {api_url}")

try:
    response = requests.get(api_url, timeout=5)
    print(f"状态码: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ API调用成功")
        print(f"响应数据: {data}")
    else:
        print(f"❌ API返回错误: {response.status_code}")
        print(f"错误详情: {response.text}")
        
except requests.exceptions.ConnectionError:
    print("❌ 无法连接到后端服务器")
    print("请确保后端服务器正在运行: py backend_api_server.py")
except Exception as e:
    print(f"❌ 请求失败: {e}")

print("\n" + "=" * 60)
