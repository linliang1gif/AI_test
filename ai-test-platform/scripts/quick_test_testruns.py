#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""快速测试TestRuns API"""

import requests
import time

BASE_URL = "http://127.0.0.1:8081"

print("测试TestRuns API...")
print("=" * 50)

# 1. 启动测试运行
print("\n1. 启动测试运行...")
response = requests.post(f"{BASE_URL}/api/test-runs", json={"environment": "staging"})
print(f"状态码: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    run = data.get("testRun", {})
    print(f"✅ 测试运行ID: {run.get('id')}")
    print(f"   名称: {run.get('name')}")
    print(f"   状态: {run.get('status')}")
    print(f"   总测试数: {run.get('totalTests')}")
    
    run_id = run.get('id')
    
    # 2. 等待并查询状态
    print(f"\n2. 查询状态 (等待5秒)...")
    time.sleep(5)
    
    response = requests.get(f"{BASE_URL}/api/test-runs/{run_id}/status")
    if response.status_code == 200:
        data = response.json()
        run = data.get("testRun", {})
        print(f"✅ 状态: {run.get('status')}")
        print(f"   进度: {run.get('progress')}%")
        print(f"   通过: {run.get('passed')}")
        print(f"   失败: {run.get('failed')}")
        print(f"   日志数: {len(run.get('logs', []))}")
        
        if run.get('logs'):
            print("\n   最新日志:")
            for log in run.get('logs', [])[-3:]:
                print(f"     [{log.get('level')}] {log.get('message')}")
    else:
        print(f"❌ 查询失败: {response.text}")
else:
    print(f"❌ 启动失败: {response.text}")

print("\n" + "=" * 50)
print("测试完成")
