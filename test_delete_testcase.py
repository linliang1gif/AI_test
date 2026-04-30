#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试删除测试用例功能
"""

import requests

BASE_URL = "http://localhost:8000"

def test_delete():
    """测试删除功能"""
    print("="*60)
    print("  测试删除测试用例功能")
    print("="*60)
    
    # 1. 获取测试用例
    print("\n1. 获取测试用例...")
    r = requests.get(f"{BASE_URL}/api/test-cases")
    data = r.json()
    cases = data.get('data', [])
    
    print(f"   当前有 {len(cases)} 个测试用例")
    
    if len(cases) == 0:
        print("   ⚠️  没有测试用例可删除")
        return
    
    # 显示前5个
    print("\n   前5个测试用例:")
    for i, case in enumerate(cases[:5], 1):
        print(f"   {i}. ID={case.get('id')}: {case.get('title', 'N/A')[:50]}")
    
    # 2. 选择要删除的ID
    # 使用最后一个测试用例(避免删除重要数据)
    test_id = cases[-1]['id']
    test_title = cases[-1].get('title', 'N/A')
    
    print(f"\n2. 准备删除测试用例...")
    print(f"   ID: {test_id}")
    print(f"   标题: {test_title[:50]}")
    
    # 3. 调用删除API
    print(f"\n3. 调用删除API...")
    print(f"   POST {BASE_URL}/api/testcases/batch-delete")
    print(f"   请求体: {{'ids': [{test_id}]}}")
    
    try:
        r = requests.post(
            f"{BASE_URL}/api/testcases/batch-delete",
            json={"ids": [test_id]},
            timeout=10
        )
        
        print(f"\n   响应状态: {r.status_code}")
        result = r.json()
        
        if result.get('success'):
            print(f"   ✅ 删除成功")
            print(f"   删除数量: {result.get('deleted_count', 0)}")
            print(f"   消息: {result.get('message', '')}")
        else:
            print(f"   ❌ 删除失败")
            print(f"   错误: {result.get('error', '')}")
            print(f"   消息: {result.get('message', '')}")
        
    except Exception as e:
        print(f"   ❌ 请求失败: {e}")
        return
    
    # 4. 验证删除
    print(f"\n4. 验证删除结果...")
    r = requests.get(f"{BASE_URL}/api/test-cases")
    data = r.json()
    new_cases = data.get('data', [])
    
    print(f"   删除前: {len(cases)} 个")
    print(f"   删除后: {len(new_cases)} 个")
    
    if len(new_cases) == len(cases) - 1:
        print(f"   ✅ 删除验证成功")
    else:
        print(f"   ⚠️  数量不匹配")
    
    print("\n" + "="*60)

if __name__ == "__main__":
    test_delete()
