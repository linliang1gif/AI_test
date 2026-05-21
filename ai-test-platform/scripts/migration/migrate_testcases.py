"""
数据迁移脚本：为已有测试用例添加 data_type 和 expected_behavior 字段
"""
from utils.data_manager import get_data_manager

def migrate_testcases():
    """为已有测试用例添加新字段"""
    print("🔄 开始迁移测试用例数据...\n")
    
    data_manager = get_data_manager()
    test_cases = data_manager.get_data("test_cases", [])
    
    print(f"📊 总测试用例数: {len(test_cases)}")
    
    updated_count = 0
    skipped_count = 0
    
    for tc in test_cases:
        # 如果已有这些字段，跳过
        if 'data_type' in tc and 'expected_behavior' in tc:
            skipped_count += 1
            continue
        
        # 根据测试类型和标题推断
        test_type = tc.get('type', '功能测试')
        title = tc.get('title', '')
        
        # 推断 data_type
        if '异常' in test_type or '参数校验' in title or '非法' in title or '错误' in title:
            tc['data_type'] = 'invalid'
        elif '边界' in test_type or '边界' in title or '临界' in title or '最大' in title or '最小' in title:
            tc['data_type'] = 'boundary'
        else:
            tc['data_type'] = 'valid'
        
        # 推断 expected_behavior
        if tc['data_type'] == 'invalid':
            tc['expected_behavior'] = 'client_error'
        else:
            tc['expected_behavior'] = 'success'
        
        updated_count += 1
        
        # 打印前5个更新的用例
        if updated_count <= 5:
            print(f"  ✅ {tc['id']}: {tc['title'][:50]}")
            print(f"     data_type: {tc['data_type']}, expected_behavior: {tc['expected_behavior']}")
    
    # 保存更新
    if updated_count > 0:
        data_manager.set_data("test_cases", test_cases, save=True)
        print(f"\n💾 已保存更新到持久化存储")
    
    print(f"\n📊 迁移统计:")
    print(f"   更新: {updated_count} 个")
    print(f"   跳过: {skipped_count} 个")
    print(f"   总计: {len(test_cases)} 个")
    
    print(f"\n🎉 迁移完成！")

if __name__ == "__main__":
    try:
        migrate_testcases()
    except Exception as e:
        print(f"\n❌ 迁移失败: {e}")
        import traceback
        traceback.print_exc()
