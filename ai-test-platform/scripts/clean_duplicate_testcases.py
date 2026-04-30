"""清理重复的测试用例"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from utils.data_manager import get_data_manager
import uuid

print("=" * 60)
print("🧹 清理重复测试用例")
print("=" * 60)

dm = get_data_manager()
testcases = dm.get_data("test_cases", [])

print(f"\n当前测试用例总数: {len(testcases)}")

# 找出重复ID
id_count = {}
for tc in testcases:
    tc_id = tc.get('id')
    if tc_id:
        id_count[tc_id] = id_count.get(tc_id, 0) + 1

duplicate_ids = [id for id, count in id_count.items() if count > 1]
print(f"发现重复ID: {len(duplicate_ids)} 个")

if not duplicate_ids:
    print("✅ 没有重复数据")
    sys.exit(0)

# 为重复的ID重新分配唯一ID
cleaned_cases = []
seen_ids = set()

for tc in testcases:
    tc_id = tc.get('id')
    
    if tc_id in seen_ids:
        # 这是重复的,生成新ID
        new_id = f"TC_{int(__import__('time').time() * 1000)}_{uuid.uuid4().hex[:8]}"
        print(f"  重复ID {tc_id} -> 新ID {new_id}")
        tc['id'] = new_id
        seen_ids.add(new_id)
    else:
        seen_ids.add(tc_id)
    
    cleaned_cases.append(tc)

print(f"\n清理后测试用例总数: {len(cleaned_cases)}")
print(f"唯一ID数量: {len(seen_ids)}")

# 保存清理后的数据
dm.set_data("test_cases", cleaned_cases, save=True)
print("\n✅ 数据已清理并保存")

print("=" * 60)
