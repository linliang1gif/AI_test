"""
测试实际删除功能
"""
import requests
import json

BASE_URL = "http://localhost:8000"

print("=" * 60)
print("测试实际删除功能")
print("=" * 60)

# 1. 获取当前测试用例
print("\n1. 获取当前测试用例...")
response = requests.get(f"{BASE_URL}/api/test-cases")
test_cases = response.json().get('data', [])
print(f"   当前共有 {len(test_cases)} 个测试用例")

if len(test_cases) == 0:
    print("   ❌ 没有测试用例可以删除")
    exit(0)

# 选择最后一个测试用例进行删除
test_case_to_delete = test_cases[-1]
delete_id = test_case_to_delete['id']
print(f"\n2. 准备删除测试用例:")
print(f"   ID: {delete_id} ({type(delete_id).__name__})")
print(f"   标题: {test_case_to_delete.get('title', 'N/A')[:50]}")

# 3. 执行删除
print(f"\n3. 执行删除...")
response = requests.post(
    f"{BASE_URL}/api/testcases/batch-delete",
    json={"ids": [delete_id]},
    headers={"Content-Type": "application/json"}
)

print(f"   状态码: {response.status_code}")
print(f"   响应: {response.json()}")

result = response.json()
if result.get('success'):
    deleted_count = result.get('deleted_count', 0)
    print(f"\n   ✅ 删除成功!")
    print(f"   删除数量: {deleted_count}")
    
    if deleted_count == 0:
        print("   ⚠️ 警告: deleted_count为0,但success为True")
        print("   这可能是后端逻辑问题")
else:
    print(f"   ❌ 删除失败: {result.get('message', 'Unknown error')}")

# 4. 验证删除结果
print(f"\n4. 验证删除结果...")
response = requests.get(f"{BASE_URL}/api/test-cases")
new_test_cases = response.json().get('data', [])
print(f"   现在共有 {len(new_test_cases)} 个测试用例")

if len(new_test_cases) < len(test_cases):
    print(f"   ✅ 确认删除成功! (减少了 {len(test_cases) - len(new_test_cases)} 个)")
else:
    print(f"   ❌ 删除失败! 数量没有变化")
    print(f"   检查ID {delete_id} 是否还存在...")
    still_exists = any(tc['id'] == delete_id for tc in new_test_cases)
    if still_exists:
        print(f"   ❌ ID {delete_id} 仍然存在")
    else:
        print(f"   ⚠️ ID {delete_id} 不存在,但总数没变化")

print("\n" + "=" * 60)
print("结论")
print("=" * 60)

if result.get('success') and deleted_count > 0 and len(new_test_cases) < len(test_cases):
    print("✅ 后端删除功能完全正常")
    print("   问题在前端:")
    print("   1. 浏览器缓存了旧代码")
    print("   2. 需要清除缓存: Ctrl + Shift + R")
elif result.get('success') and deleted_count == 0:
    print("⚠️ 后端返回success但deleted_count为0")
    print("   可能的原因:")
    print("   1. 后端删除逻辑有问题")
    print("   2. 前端读取了错误的字段")
else:
    print("❌ 后端删除功能有问题")
    print("   需要检查后端代码")
