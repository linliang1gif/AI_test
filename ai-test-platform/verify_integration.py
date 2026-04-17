"""
验证前后端对接：检查测试用例是否包含 data_type 和 expected_behavior 字段
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def verify_api_response():
    """验证API返回的测试用例结构"""
    print("🔍 验证API响应结构...\n")
    
    try:
        # 获取测试用例列表
        response = requests.get(f"{BASE_URL}/api/testcases")
        
        if response.status_code != 200:
            print(f"❌ API请求失败: {response.status_code}")
            return False
        
        data = response.json()
        test_cases = data.get('data', [])
        
        if not test_cases:
            print("⚠️  没有测试用例数据")
            return False
        
        print(f"📊 找到 {len(test_cases)} 个测试用例\n")
        
        # 检查前3个用例
        success_count = 0
        missing_fields = []
        
        for i, tc in enumerate(test_cases[:3], 1):
            print(f"测试用例 {i}:")
            print(f"  ID: {tc.get('id')}")
            print(f"  标题: {tc.get('title', '')[:50]}")
            
            has_data_type = 'data_type' in tc
            has_expected_behavior = 'expected_behavior' in tc
            
            if has_data_type:
                print(f"  ✅ data_type: {tc['data_type']}")
            else:
                print(f"  ❌ data_type: 缺失")
                missing_fields.append(f"TC_{tc.get('id')} - data_type")
            
            if has_expected_behavior:
                print(f"  ✅ expected_behavior: {tc['expected_behavior']}")
            else:
                print(f"  ❌ expected_behavior: 缺失")
                missing_fields.append(f"TC_{tc.get('id')} - expected_behavior")
            
            if has_data_type and has_expected_behavior:
                success_count += 1
            
            print()
        
        # 统计所有用例
        total_with_fields = sum(
            1 for tc in test_cases 
            if 'data_type' in tc and 'expected_behavior' in tc
        )
        
        print(f"📊 统计结果:")
        print(f"   总用例数: {len(test_cases)}")
        print(f"   包含新字段: {total_with_fields}")
        print(f"   缺失字段: {len(test_cases) - total_with_fields}")
        
        if missing_fields:
            print(f"\n⚠️  缺失字段的用例:")
            for field in missing_fields[:5]:
                print(f"   - {field}")
        
        if total_with_fields == len(test_cases):
            print(f"\n🎉 验证通过！所有测试用例都包含新字段")
            return True
        elif total_with_fields > 0:
            print(f"\n⚠️  部分用例缺失字段，建议运行迁移脚本: py migrate_testcases.py")
            return False
        else:
            print(f"\n❌ 所有用例都缺失新字段，请检查后端代码")
            return False
        
    except requests.exceptions.ConnectionError:
        print(f"❌ 无法连接到后端服务器 ({BASE_URL})")
        print(f"   请确保后端服务器正在运行")
        return False
    except Exception as e:
        print(f"❌ 验证失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def verify_field_values():
    """验证字段值的正确性"""
    print("\n🔍 验证字段值的正确性...\n")
    
    try:
        response = requests.get(f"{BASE_URL}/api/testcases")
        data = response.json()
        test_cases = data.get('data', [])
        
        valid_data_types = ['valid', 'boundary', 'invalid']
        valid_behaviors = ['success', 'client_error', 'server_error']
        
        invalid_count = 0
        
        for tc in test_cases:
            if 'data_type' not in tc or 'expected_behavior' not in tc:
                continue
            
            data_type = tc['data_type']
            expected_behavior = tc['expected_behavior']
            
            if data_type not in valid_data_types:
                print(f"❌ 无效的 data_type: {data_type} (用例: {tc.get('id')})")
                invalid_count += 1
            
            if expected_behavior not in valid_behaviors:
                print(f"❌ 无效的 expected_behavior: {expected_behavior} (用例: {tc.get('id')})")
                invalid_count += 1
        
        if invalid_count == 0:
            print("✅ 所有字段值都有效")
            return True
        else:
            print(f"\n⚠️  发现 {invalid_count} 个无效字段值")
            return False
        
    except Exception as e:
        print(f"❌ 验证失败: {e}")
        return False

def show_statistics():
    """显示统计信息"""
    print("\n📊 字段分布统计...\n")
    
    try:
        response = requests.get(f"{BASE_URL}/api/testcases")
        data = response.json()
        test_cases = data.get('data', [])
        
        # 统计 data_type
        data_type_stats = {}
        for tc in test_cases:
            dt = tc.get('data_type', 'unknown')
            data_type_stats[dt] = data_type_stats.get(dt, 0) + 1
        
        print("数据类型分布:")
        for dt, count in sorted(data_type_stats.items()):
            print(f"  {dt}: {count}")
        
        # 统计 expected_behavior
        behavior_stats = {}
        for tc in test_cases:
            eb = tc.get('expected_behavior', 'unknown')
            behavior_stats[eb] = behavior_stats.get(eb, 0) + 1
        
        print("\n预期行为分布:")
        for eb, count in sorted(behavior_stats.items()):
            print(f"  {eb}: {count}")
        
    except Exception as e:
        print(f"❌ 统计失败: {e}")

if __name__ == "__main__":
    print("=" * 60)
    print("前后端对接验证")
    print("=" * 60)
    print()
    
    # 验证API响应
    api_ok = verify_api_response()
    
    if api_ok:
        # 验证字段值
        values_ok = verify_field_values()
        
        # 显示统计
        show_statistics()
        
        if values_ok:
            print("\n" + "=" * 60)
            print("🎉 验证完成！前后端对接正常")
            print("=" * 60)
        else:
            print("\n" + "=" * 60)
            print("⚠️  验证完成，但存在一些问题")
            print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("❌ 验证失败，请检查后端代码或运行迁移脚本")
        print("=" * 60)
        print("\n建议操作:")
        print("  1. 确保后端服务器正在运行: py backend_api_server.py")
        print("  2. 运行迁移脚本: py migrate_testcases.py")
        print("  3. 重新运行验证: py verify_integration.py")
