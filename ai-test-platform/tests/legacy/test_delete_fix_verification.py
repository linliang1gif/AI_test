"""
测试用例删除功能验证脚本
验证之前发现的所有删除bug是否已修复
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

def print_section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")

def test_backend_delete_api():
    """测试后端删除API是否正确返回deleted_count"""
    print_section("测试1: 后端API返回值验证")
    
    # 1. 获取当前测试用例
    print("📋 获取当前测试用例列表...")
    response = requests.get(f"{BASE_URL}/api/test-cases")
    test_cases = response.json().get('data', [])
    print(f"   当前共有 {len(test_cases)} 个测试用例")
    
    if len(test_cases) == 0:
        print("⚠️  没有测试用例可供测试,请先创建一些测试用例")
        return False
    
    # 2. 选择要删除的ID
    ids_to_delete = [tc['id'] for tc in test_cases[:2]]  # 删除前2个
    print(f"🎯 准备删除的ID: {ids_to_delete}")
    
    # 3. 调用删除API
    print("\n🗑️  调用批量删除API...")
    delete_response = requests.post(
        f"{BASE_URL}/api/testcases/batch-delete",
        headers={"Content-Type": "application/json"},
        json={"ids": ids_to_delete}
    )
    
    # 4. 检查响应
    result = delete_response.json()
    print(f"📦 响应数据: {json.dumps(result, indent=2, ensure_ascii=False)}")
    
    # 5. 验证关键字段
    checks = {
        "success字段存在": "success" in result,
        "success为True": result.get("success") == True,
        "deleted_count字段存在": "deleted_count" in result,
        "deleted_count不为0": result.get("deleted_count", 0) > 0,
        "deleted_count正确": result.get("deleted_count") == len(ids_to_delete),
        "message字段存在": "message" in result,
    }
    
    print("\n✅ 验证结果:")
    all_passed = True
    for check_name, check_result in checks.items():
        status = "✅" if check_result else "❌"
        print(f"   {status} {check_name}: {check_result}")
        if not check_result:
            all_passed = False
    
    # 6. 验证数据确实被删除
    print("\n🔍 验证数据是否真的被删除...")
    response = requests.get(f"{BASE_URL}/api/test-cases")
    remaining_cases = response.json().get('data', [])
    remaining_ids = [tc['id'] for tc in remaining_cases]
    
    deleted_successfully = all(id not in remaining_ids for id in ids_to_delete)
    print(f"   {'✅' if deleted_successfully else '❌'} 数据已从数据库删除: {deleted_successfully}")
    print(f"   剩余测试用例数: {len(remaining_cases)}")
    
    return all_passed and deleted_successfully

def test_mixed_id_types():
    """测试混合ID类型(整数和字符串)"""
    print_section("测试2: 混合ID类型支持")
    
    # 获取测试用例
    response = requests.get(f"{BASE_URL}/api/test-cases")
    test_cases = response.json().get('data', [])
    
    if len(test_cases) < 2:
        print("⚠️  测试用例不足,跳过此测试")
        return True
    
    # 混合使用整数和字符串ID
    mixed_ids = []
    for i, tc in enumerate(test_cases[:2]):
        if i == 0:
            # 第一个保持原样
            mixed_ids.append(tc['id'])
        else:
            # 第二个转换为字符串(如果是整数)或整数(如果是字符串)
            if isinstance(tc['id'], int):
                mixed_ids.append(str(tc['id']))
            else:
                try:
                    mixed_ids.append(int(tc['id']))
                except:
                    mixed_ids.append(tc['id'])
    
    print(f"🎯 测试混合ID类型: {mixed_ids}")
    print(f"   类型: {[type(id).__name__ for id in mixed_ids]}")
    
    # 调用删除API
    delete_response = requests.post(
        f"{BASE_URL}/api/testcases/batch-delete",
        headers={"Content-Type": "application/json"},
        json={"ids": mixed_ids}
    )
    
    result = delete_response.json()
    success = result.get("success") and result.get("deleted_count", 0) > 0
    
    print(f"   {'✅' if success else '❌'} 混合ID类型删除: {success}")
    print(f"   删除数量: {result.get('deleted_count', 0)}")
    
    return success

def test_empty_ids():
    """测试空ID列表"""
    print_section("测试3: 边界情况 - 空ID列表")
    
    delete_response = requests.post(
        f"{BASE_URL}/api/testcases/batch-delete",
        headers={"Content-Type": "application/json"},
        json={"ids": []}
    )
    
    result = delete_response.json()
    print(f"📦 响应: {json.dumps(result, indent=2, ensure_ascii=False)}")
    
    # 空列表应该返回success=True, deleted_count=0
    success = result.get("success") == True and result.get("deleted_count") == 0
    print(f"   {'✅' if success else '❌'} 空列表处理正确: {success}")
    
    return success

def test_nonexistent_ids():
    """测试不存在的ID"""
    print_section("测试4: 边界情况 - 不存在的ID")
    
    fake_ids = ["FAKE_ID_999", 999999, "TC_NONEXISTENT"]
    print(f"🎯 测试不存在的ID: {fake_ids}")
    
    delete_response = requests.post(
        f"{BASE_URL}/api/testcases/batch-delete",
        headers={"Content-Type": "application/json"},
        json={"ids": fake_ids}
    )
    
    result = delete_response.json()
    print(f"📦 响应: {json.dumps(result, indent=2, ensure_ascii=False)}")
    
    # 不存在的ID应该返回success=True, deleted_count=0
    success = result.get("success") == True and result.get("deleted_count") == 0
    print(f"   {'✅' if success else '❌'} 不存在ID处理正确: {success}")
    
    return success

def create_test_cases_for_testing():
    """创建一些测试用例用于测试"""
    print_section("准备: 创建测试数据")
    
    test_cases = [
        {
            "title": f"删除测试用例 {i+1}",
            "module": "删除功能测试",
            "priority": "medium",
            "status": "pending",
            "steps": ["步骤1", "步骤2"],
            "expected": "预期结果",
            "source": "manual"
        }
        for i in range(5)
    ]
    
    created_count = 0
    for tc in test_cases:
        try:
            response = requests.post(
                f"{BASE_URL}/api/test-cases",
                headers={"Content-Type": "application/json"},
                json=tc
            )
            if response.status_code == 200:
                created_count += 1
        except Exception as e:
            print(f"⚠️  创建测试用例失败: {e}")
    
    print(f"✅ 成功创建 {created_count} 个测试用例")
    return created_count > 0

def main():
    """主测试流程"""
    print("\n" + "="*60)
    print("  🧪 测试用例删除功能完整验证")
    print("="*60)
    
    # 检查后端是否运行
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=2)
        print("✅ 后端服务运行正常\n")
    except:
        print("❌ 后端服务未运行,请先启动: python backend_api_server.py")
        return
    
    # 创建测试数据
    if not create_test_cases_for_testing():
        print("❌ 无法创建测试数据,测试终止")
        return
    
    # 运行所有测试
    results = []
    
    # 测试1: 基本删除功能
    results.append(("后端API返回值", test_backend_delete_api()))
    time.sleep(0.5)
    
    # 测试2: 混合ID类型
    results.append(("混合ID类型", test_mixed_id_types()))
    time.sleep(0.5)
    
    # 测试3: 空ID列表
    results.append(("空ID列表", test_empty_ids()))
    time.sleep(0.5)
    
    # 测试4: 不存在的ID
    results.append(("不存在的ID", test_nonexistent_ids()))
    
    # 汇总结果
    print_section("📊 测试结果汇总")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"   {status} - {test_name}")
    
    print(f"\n总计: {passed}/{total} 测试通过")
    
    if passed == total:
        print("\n🎉 所有测试通过! 删除功能工作正常!")
        print("\n📝 前端使用建议:")
        print("   1. 清除浏览器缓存 (Ctrl+Shift+R)")
        print("   2. 检查前端是否正确读取 result.deleted_count")
        print("   3. 确保删除后调用 loadTestCases() 刷新列表")
    else:
        print("\n⚠️  部分测试失败,请检查后端实现")

if __name__ == "__main__":
    main()
