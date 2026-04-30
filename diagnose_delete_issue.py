#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
诊断删除问题
"""

import requests
import json

BASE_URL = "http://localhost:8000"

print("="*60)
print("  诊断删除问题")
print("="*60)

# 1. 获取测试用例
print("\n1. 获取测试用例...")
r = requests.get(f"{BASE_URL}/api/test-cases")
cases = r.json()['data']

print(f"   总数: {len(cases)}")

# 显示前3个的ID和类型
print("\n   前3个测试用例的ID:")
for i, case in enumerate(cases[:3], 1):
    case_id = case.get('id')
    print(f"   {i}. ID={case_id}, 类型={type(case_id).__name__}, 值={repr(case_id)}")

# 2. 尝试删除第一个
test_id = cases[0]['id']
print(f"\n2. 尝试删除 ID={test_id} (类型={type(test_id).__name__})")

# 发送删除请求
payload = {"ids": [test_id]}
print(f"   请求体: {json.dumps(payload)}")

r = requests.post(
    f"{BASE_URL}/api/testcases/batch-delete",
    json=payload,
    timeout=10
)

print(f"\n   响应状态: {r.status_code}")
result = r.json()
print(f"   响应内容: {json.dumps(result, indent=2, ensure_ascii=False)}")

# 3. 检查是否真的删除了
print(f"\n3. 验证删除结果...")
r = requests.get(f"{BASE_URL}/api/test-cases")
new_cases = r.json()['data']

print(f"   删除前: {len(cases)} 个")
print(f"   删除后: {len(new_cases)} 个")
print(f"   实际删除: {len(cases) - len(new_cases)} 个")

if len(cases) == len(new_cases):
    print("\n   ❌ 删除失败! 数据没有变化")
    print("\n   可能原因:")
    print("   1. ID类型不匹配 (前端发送的ID类型和后端存储的不一致)")
    print("   2. ID值不匹配")
    print("   3. 后端过滤逻辑有问题")
    
    # 检查ID是否在列表中
    print(f"\n   检查: ID {test_id} 是否在列表中?")
    found = any(tc['id'] == test_id for tc in cases)
    print(f"   结果: {'找到' if found else '未找到'}")
    
    # 检查类型转换
    print(f"\n   尝试类型转换:")
    if isinstance(test_id, int):
        print(f"   str({test_id}) = {str(test_id)}")
        found_str = any(tc['id'] == str(test_id) for tc in cases)
        print(f"   字符串匹配: {'找到' if found_str else '未找到'}")
    elif isinstance(test_id, str):
        try:
            int_id = int(test_id)
            print(f"   int({test_id}) = {int_id}")
            found_int = any(tc['id'] == int_id for tc in cases)
            print(f"   整数匹配: {'找到' if found_int else '未找到'}")
        except:
            print(f"   无法转换为整数")
else:
    print(f"\n   ✅ 删除成功!")

print("\n" + "="*60)
