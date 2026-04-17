#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""测试批量删除API"""

import requests

def test_batch_delete():
    """测试批量删除"""
    base_url = "http://localhost:8000"
    
    # 1. 获取当前测试用例
    print("📋 获取当前测试用例...")
    response = requests.get(f"{base_url}/api/test-cases")
    result = response.json()
    print(f"当前有 {result['count']} 个测试用例")
    
    if result['count'] > 0:
        # 获取前2个ID
        ids_to_delete = [tc['id'] for tc in result['data'][:2]]
        print(f"\n🗑️  准备删除ID: {ids_to_delete}")
        
        # 2. 测试批量删除
        delete_response = requests.post(
            f"{base_url}/api/testcases/batch-delete",
            json={"ids": ids_to_delete}
        )
        
        print(f"状态码: {delete_response.status_code}")
        delete_result = delete_response.json()
        print(f"删除结果: {delete_result}")
        
        # 3. 再次获取测试用例
        print("\n📋 删除后的测试用例...")
        response = requests.get(f"{base_url}/api/test-cases")
        result = response.json()
        print(f"剩余 {result['count']} 个测试用例")
        
        print("\n✅ 批量删除测试完成!")
    else:
        print("⚠️  没有测试用例可删除")

if __name__ == "__main__":
    test_batch_delete()
