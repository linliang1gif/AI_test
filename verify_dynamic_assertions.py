"""
验证动态断言生成功能
"""
from modules.swagger import SwaggerTestCaseGenerator
import json


def verify_dynamic_assertions():
    """验证动态断言生成"""
    print("\n🔍 验证动态断言生成功能\n")
    print("=" * 60)
    
    # 生成测试用例
    generator = SwaggerTestCaseGenerator("examples/sample_swagger.json")
    test_cases = generator.generate_all_testcases()
    
    # 按数据类型分组
    by_data_type = {}
    by_expected_behavior = {}
    
    for tc in test_cases:
        # 按数据类型分组
        data_type = tc.data_type
        if data_type not in by_data_type:
            by_data_type[data_type] = []
        by_data_type[data_type].append(tc)
        
        # 按预期行为分组
        expected_behavior = tc.expected_behavior
        if expected_behavior not in by_expected_behavior:
            by_expected_behavior[expected_behavior] = []
        by_expected_behavior[expected_behavior].append(tc)
    
    # 验证1: 数据类型分布
    print("\n📊 验证1: 数据类型分布")
    print("-" * 60)
    for data_type, cases in by_data_type.items():
        print(f"  {data_type}: {len(cases)} 个用例")
    
    # 验证2: 预期行为分布
    print("\n📊 验证2: 预期行为分布")
    print("-" * 60)
    for behavior, cases in by_expected_behavior.items():
        print(f"  {behavior}: {len(cases)} 个用例")
    
    # 验证3: 检查每种组合的断言
    print("\n🔍 验证3: 断言内容检查")
    print("-" * 60)
    
    # 检查 valid + success
    print("\n1️⃣ valid + success 用例:")
    valid_success = [tc for tc in test_cases if tc.data_type == "valid" and tc.expected_behavior == "success"]
    if valid_success:
        tc = valid_success[0]
        print(f"   用例: {tc.id} - {tc.title}")
        print(f"   data_type: {tc.data_type}")
        print(f"   expected_behavior: {tc.expected_behavior}")
        print(f"   断言:")
        for assertion in tc.assertions:
            print(f"     - type: {assertion['type']}")
            if 'operator' in assertion:
                print(f"       operator: {assertion['operator']}")
            print(f"       expected: {assertion['expected']}")
    
    # 检查 boundary + success
    print("\n2️⃣ boundary + success 用例:")
    boundary_success = [tc for tc in test_cases if tc.data_type == "boundary" and tc.expected_behavior == "success"]
    if boundary_success:
        tc = boundary_success[0]
        print(f"   用例: {tc.id} - {tc.title}")
        print(f"   data_type: {tc.data_type}")
        print(f"   expected_behavior: {tc.expected_behavior}")
        print(f"   断言:")
        for assertion in tc.assertions:
            print(f"     - type: {assertion['type']}")
            if 'operator' in assertion:
                print(f"       operator: {assertion['operator']}")
            print(f"       expected: {assertion['expected']}")
    
    # 检查 invalid + client_error
    print("\n3️⃣ invalid + client_error 用例:")
    invalid_error = [tc for tc in test_cases if tc.data_type == "invalid" and tc.expected_behavior == "client_error"]
    if invalid_error:
        tc = invalid_error[0]
        print(f"   用例: {tc.id} - {tc.title}")
        print(f"   data_type: {tc.data_type}")
        print(f"   expected_behavior: {tc.expected_behavior}")
        print(f"   断言:")
        for assertion in tc.assertions:
            print(f"     - type: {assertion['type']}")
            if 'operator' in assertion:
                print(f"       operator: {assertion['operator']}")
            print(f"       expected: {assertion['expected']}")
    
    # 验证4: 断言逻辑正确性
    print("\n✅ 验证4: 断言逻辑正确性")
    print("-" * 60)
    
    errors = []
    
    for tc in test_cases:
        status_assertions = [a for a in tc.assertions if a['type'] == 'status_code']
        
        if not status_assertions:
            errors.append(f"{tc.id}: 缺少状态码断言")
            continue
        
        status_assertion = status_assertions[0]
        
        # 检查 success 场景
        if tc.expected_behavior == "success":
            if status_assertion.get('operator') != 'in':
                errors.append(f"{tc.id}: success场景应该使用'in'操作符")
            expected = status_assertion.get('expected', [])
            if not any(code in [200, 201, 204] for code in expected):
                errors.append(f"{tc.id}: success场景应该包含2xx状态码")
        
        # 检查 client_error 场景
        elif tc.expected_behavior == "client_error":
            if status_assertion.get('operator') != 'in':
                errors.append(f"{tc.id}: client_error场景应该使用'in'操作符")
            expected = status_assertion.get('expected', [])
            if not any(code in [400, 422, 404, 403] for code in expected):
                errors.append(f"{tc.id}: client_error场景应该包含4xx状态码")
        
        # 检查 server_error 场景
        elif tc.expected_behavior == "server_error":
            if status_assertion.get('operator') != 'greater_than_or_equal':
                errors.append(f"{tc.id}: server_error场景应该使用'greater_than_or_equal'操作符")
            if status_assertion.get('expected') != 500:
                errors.append(f"{tc.id}: server_error场景应该期望>=500")
    
    if errors:
        print("❌ 发现错误:")
        for error in errors:
            print(f"   - {error}")
    else:
        print("✅ 所有断言逻辑正确")
    
    # 验证5: 导出JSON检查
    print("\n📄 验证5: 导出JSON检查")
    print("-" * 60)
    
    json_data = generator.export_to_json(test_cases)
    
    # 检查字段完整性
    required_fields = ['id', 'title', 'data_type', 'expected_behavior', 'assertions', 'execution_config']
    missing_fields = []
    
    for tc_json in json_data:
        for field in required_fields:
            if field not in tc_json:
                missing_fields.append(f"{tc_json.get('id', 'unknown')}: 缺少字段 {field}")
    
    if missing_fields:
        print("❌ 发现缺失字段:")
        for error in missing_fields:
            print(f"   - {error}")
    else:
        print("✅ 所有必需字段完整")
    
    # 保存示例
    sample_cases = json_data[:3]
    with open("dynamic_assertions_sample.json", "w", encoding="utf-8") as f:
        json.dump(sample_cases, f, indent=2, ensure_ascii=False)
    print(f"✅ 已保存示例到 dynamic_assertions_sample.json")
    
    # 统计信息
    print("\n📊 统计信息")
    print("-" * 60)
    stats = generator.get_statistics(test_cases)
    print(f"  总用例数: {stats['total']}")
    print(f"  数据类型分布: {stats['by_data_type']}")
    print(f"  预期行为分布: {stats['by_expected_behavior']}")
    
    # 最终结果
    print("\n" + "=" * 60)
    if not errors and not missing_fields:
        print("🎉 动态断言生成功能验证通过！")
        return True
    else:
        print("❌ 动态断言生成功能存在问题")
        return False


if __name__ == "__main__":
    verify_dynamic_assertions()
