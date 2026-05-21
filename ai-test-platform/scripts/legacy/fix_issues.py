#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复两个问题:
1. Ollama超时从60秒增加到180秒
2. 测试批量删除功能
"""

import requests
import json

def test_batch_delete():
    """测试批量删除功能"""
    base_url = "http://localhost:8000"
    
    print("=" * 60)
    print("测试批量删除功能")
    print("=" * 60)
    
    # 1. 获取当前测试用例
    print("\n1. 获取当前测试用例...")
    response = requests.get(f"{base_url}/api/test-cases")
    result = response.json()
    test_cases = result.get('data', [])
    print(f"   当前有 {len(test_cases)} 个测试用例")
    
    if len(test_cases) < 2:
        print("   ⚠️  测试用例数量不足，无法测试批量删除")
        return
    
    # 2. 选择前2个测试用例进行删除
    ids_to_delete = [test_cases[0]['id'], test_cases[1]['id']]
    print(f"\n2. 准备删除测试用例 ID: {ids_to_delete}")
    
    # 3. 调用批量删除API
    print("\n3. 调用批量删除API...")
    delete_response = requests.post(
        f"{base_url}/api/testcases/batch-delete",
        headers={"Content-Type": "application/json"},
        json={"ids": ids_to_delete}
    )
    
    print(f"   响应状态码: {delete_response.status_code}")
    delete_result = delete_response.json()
    print(f"   响应内容: {json.dumps(delete_result, ensure_ascii=False, indent=2)}")
    
    if delete_result.get('success'):
        print(f"   ✅ 删除成功! 删除了 {delete_result.get('deleted_count')} 个测试用例")
    else:
        print(f"   ❌ 删除失败: {delete_result.get('error')}")
    
    # 4. 验证删除结果
    print("\n4. 验证删除结果...")
    response = requests.get(f"{base_url}/api/test-cases")
    result = response.json()
    remaining_cases = result.get('data', [])
    print(f"   剩余 {len(remaining_cases)} 个测试用例")
    
    # 检查被删除的ID是否还存在
    remaining_ids = [tc['id'] for tc in remaining_cases]
    deleted_ids = [id for id in ids_to_delete if id not in remaining_ids]
    print(f"   实际删除的ID: {deleted_ids}")
    
    if len(deleted_ids) == len(ids_to_delete):
        print("   ✅ 批量删除功能正常!")
    else:
        print("   ❌ 批量删除功能异常!")

if __name__ == "__main__":
    test_batch_delete()
