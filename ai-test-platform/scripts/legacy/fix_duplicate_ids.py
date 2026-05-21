"""
修复数据库中的重复ID问题
"""

import json
from pathlib import Path
from collections import Counter
import time

def fix_duplicate_ids():
    """修复重复的测试用例ID"""
    data_file = Path("data/platform_data.json")
    
    if not data_file.exists():
        print("❌ 数据文件不存在")
        return
    
    # 读取数据
    with open(data_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    test_cases = data.get('test_cases', [])
    print(f"📊 当前测试用例数: {len(test_cases)}")
    
    # 检查重复ID
    ids = [tc.get('id') for tc in test_cases if 'id' in tc]
    id_counts = Counter(ids)
    duplicates = {id: count for id, count in id_counts.items() if count > 1}
    
    if not duplicates:
        print("✅ 没有发现重复ID")
        return
    
    print(f"\n⚠️  发现 {len(duplicates)} 个重复ID:")
    for id, count in duplicates.items():
        print(f"   ID {id}: 出现 {count} 次")
    
    # 修复重复ID
    print("\n🔧 开始修复...")
    seen_ids = set()
    fixed_count = 0
    
    for tc in test_cases:
        if 'id' not in tc:
            # 没有ID,生成新ID
            new_id = int(time.time() * 1000)
            tc['id'] = new_id
            seen_ids.add(new_id)
            fixed_count += 1
            print(f"   ✓ 为测试用例生成新ID: {new_id}")
            time.sleep(0.001)  # 确保ID唯一
        elif tc['id'] in seen_ids:
            # ID重复,生成新ID
            old_id = tc['id']
            new_id = int(time.time() * 1000)
            tc['id'] = new_id
            seen_ids.add(new_id)
            fixed_count += 1
            print(f"   ✓ 替换重复ID: {old_id} → {new_id}")
            time.sleep(0.001)  # 确保ID唯一
        else:
            # ID唯一,记录
            seen_ids.add(tc['id'])
    
    # 保存修复后的数据
    if fixed_count > 0:
        # 备份原文件
        backup_file = data_file.with_suffix('.backup.json')
        with open(backup_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"\n💾 原数据已备份到: {backup_file}")
        
        # 保存修复后的数据
        data['test_cases'] = test_cases
        with open(data_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 修复完成! 共修复 {fixed_count} 个重复ID")
        print(f"📊 修复后测试用例数: {len(test_cases)}")
        
        # 验证
        new_ids = [tc.get('id') for tc in test_cases]
        new_id_counts = Counter(new_ids)
        new_duplicates = {id: count for id, count in new_id_counts.items() if count > 1}
        
        if new_duplicates:
            print(f"\n⚠️  警告: 仍有 {len(new_duplicates)} 个重复ID")
        else:
            print("\n✅ 验证通过: 所有ID现在都是唯一的")
    else:
        print("\n✅ 没有需要修复的ID")

if __name__ == "__main__":
    print("="*60)
    print("  🔧 修复重复ID工具")
    print("="*60)
    print()
    
    fix_duplicate_ids()
    
    print("\n" + "="*60)
    print("  完成!")
    print("="*60)
