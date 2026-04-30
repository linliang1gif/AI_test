#!/usr/bin/env python3
"""
测试创建项目 - 调试版本
"""

import requests
import json
from pathlib import Path
from dotenv import load_dotenv

# 加载环境变量
env_file = Path(__file__).parent / ".env.bluedot"
if env_file.exists():
    load_dotenv(env_file)
    print(f"✓ 已加载环境变量: {env_file}")

# 配置
BACKEND_URL = "http://localhost:8000"

print("\n" + "="*60)
print("测试创建项目")
print("="*60)

# 测试数据
data = {
    "name": "蓝点回收系统",
    "description": "蓝点新生废品回收B2B平台 v1.2.2",
    "version": "1.2.2"
}

print(f"\n请求URL: {BACKEND_URL}/api/v2/projects")
print(f"请求数据: {json.dumps(data, ensure_ascii=False, indent=2)}")

try:
    response = requests.post(
        f"{BACKEND_URL}/api/v2/projects",
        json=data,
        timeout=30
    )
    
    print(f"\n响应状态码: {response.status_code}")
    print(f"响应头: {dict(response.headers)}")
    
    try:
        result = response.json()
        print(f"\n响应内容:")
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except:
        print(f"\n响应文本:")
        print(response.text)
    
    if response.status_code in [200, 201]:
        print("\n✓ 项目创建成功")
        if 'id' in result:
            print(f"  项目ID: {result['id']}")
    else:
        print("\n✗ 项目创建失败")
        
except Exception as e:
    print(f"\n✗ 请求异常: {type(e).__name__}: {str(e)}")
    import traceback
    traceback.print_exc()
