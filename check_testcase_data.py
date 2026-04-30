"""检查测试用例数据一致性"""
import requests
import json

print("=" * 80)
print("🔍 检查测试用例数据")
print("=" * 80)

# 获取所有测试用例
response = requests.get("http://localhost:8000/api/test-cases")
data = response.json()
testcases = data.get('data', [])

print(f"\n总共 {len(testcases)} 个测试用例")

# 查找付款单相关的用例
payment_cases = [tc for tc in testcases if '付款' in tc.get('title', '') or '付款' in tc.get('module', '')]

print(f"\n付款单相关用例: {len(payment_cases)} 个")
print("\n最新的5个付款单用例:")

for i, tc in enumerate(payment_cases[:5], 1):
    print(f"\n{i}. ID: {tc.get('id')}")
    print(f"   标题: {tc.get('title')}")
    print(f"   模块: {tc.get('module')}")
    print(f"   优先级: {tc.get('priority')}")
    print(f"   来源: {tc.get('source')}")
    print(f"   创建时间: {tc.get('created_at', 'N/A')}")
    
    # 显示步骤
    steps = tc.get('steps', [])
    if steps:
        print(f"   步骤数: {len(steps)}")
        if len(steps) > 0:
            print(f"   第一步: {steps[0][:50]}...")

# 检查是否有重复ID
all_ids = [tc.get('id') for tc in testcases]
duplicate_ids = [id for id in set(all_ids) if all_ids.count(id) > 1]

if duplicate_ids:
    print(f"\n⚠️  发现重复ID: {len(duplicate_ids)} 个")
    for dup_id in duplicate_ids[:5]:
        print(f"   ID {dup_id} 出现 {all_ids.count(dup_id)} 次")
        # 显示这些重复的用例
        dup_cases = [tc for tc in testcases if tc.get('id') == dup_id]
        for tc in dup_cases:
            print(f"      - {tc.get('title')}")
else:
    print("\n✅ 没有重复ID")

print("\n" + "=" * 80)
