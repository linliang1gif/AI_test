#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
架构重构验证脚本
测试 core + modules 集成是否正常工作
"""

print("=" * 60)
print("架构重构验证测试")
print("=" * 60)

# 测试1：Core 导入
print("\n[测试1] Core 模块导入...")
try:
    from core import (
        TestCase,
        ExecutionResult,
        TestCaseStatus,
        TestCasePriority,
        DataType,
        ExpectedBehavior,
        HealingLevel,
        create_test_case,
        create_execution_result
    )
    print("✅ Core 模块导入成功")
except Exception as e:
    print(f"❌ Core 模块导入失败: {e}")
    exit(1)

# 测试2：Modules 导入
print("\n[测试2] Modules 模块导入...")
try:
    from modules.swagger import SwaggerTestCaseGenerator
    from modules.executor import ExecutionEngine
    from modules.healing import HealingEngine
    from modules.report import ReportGenerator
    from modules.data import TestDataManager
    print("✅ Modules 模块导入成功")
except Exception as e:
    print(f"❌ Modules 模块导入失败: {e}")
    exit(1)

# 测试3：创建 TestCase
print("\n[测试3] 创建 TestCase 对象...")
try:
    test_case = create_test_case(
        id="TC_001",
        title="用户登录 - 正常流程",
        module="用户管理",
        priority="high",
        status="pending",
        steps=["1. 输入用户名", "2. 输入密码", "3. 点击登录"],
        expected="登录成功，跳转到首页",
        data_type="valid",
        expected_behavior="success"
    )
    print(f"✅ TestCase 创建成功: {test_case.title}")
    print(f"   - ID: {test_case.id}")
    print(f"   - Priority: {test_case.priority.value}")
    print(f"   - Data Type: {test_case.data_type.value}")
    print(f"   - Expected Behavior: {test_case.expected_behavior.value}")
except Exception as e:
    print(f"❌ TestCase 创建失败: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# 测试4：枚举转换
print("\n[测试4] 枚举值转换...")
try:
    assert test_case.priority.value == "high"
    assert test_case.status.value == "pending"
    assert test_case.data_type.value == "valid"
    assert test_case.expected_behavior.value == "success"
    print("✅ 枚举值转换正确")
except AssertionError as e:
    print(f"❌ 枚举值转换失败: {e}")
    exit(1)

# 测试5：TestDataManager
print("\n[测试5] TestDataManager 生成数据...")
try:
    data_manager = TestDataManager()
    schema = {
        "username": {"type": "string", "minLength": 3, "maxLength": 20},
        "password": {"type": "string", "minLength": 6, "maxLength": 20},
        "age": {"type": "integer", "minimum": 18, "maximum": 100}
    }
    
    # 生成正常数据
    valid_data = data_manager.generate_data(schema, "valid", "TC_001")
    print(f"✅ 正常数据生成成功: {valid_data}")
    
    # 生成边界数据
    boundary_data = data_manager.generate_data(schema, "boundary", "TC_002")
    print(f"✅ 边界数据生成成功: {boundary_data}")
    
    # 生成异常数据
    invalid_data = data_manager.generate_data(schema, "invalid", "TC_003")
    print(f"✅ 异常数据生成成功: {invalid_data}")
except Exception as e:
    print(f"❌ TestDataManager 测试失败: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# 测试6：ExecutionResult
print("\n[测试6] 创建 ExecutionResult...")
try:
    from datetime import datetime
    
    now = datetime.now()
    result = create_execution_result(
        test_case_id="TC_001",
        status="passed",
        start_time=now,
        end_time=now,
        error=None
    )
    print(f"✅ ExecutionResult 创建成功")
    print(f"   - Test Case ID: {result.test_case_id}")
    print(f"   - Status: {result.status.value}")
    print(f"   - Duration: {result.duration}s")
except Exception as e:
    print(f"❌ ExecutionResult 创建失败: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# 测试7：HealingEngine
print("\n[测试7] HealingEngine 修复测试...")
try:
    healing_engine = HealingEngine()
    
    # 创建一个失败的结果
    failed_result = create_execution_result(
        test_case_id="TC_002",
        status="failed",
        start_time=now,
        end_time=now,
        error="Connection timeout"
    )
    
    # 应用修复
    healed_results = healing_engine.heal([failed_result])
    
    print(f"✅ HealingEngine 测试成功")
    print(f"   - 修复应用: {healed_results[0].healing_applied}")
    if healed_results[0].healing_applied:
        print(f"   - 修复级别: {healed_results[0].healing_level.value}")
        print(f"   - 修复详情: {healed_results[0].healing_details}")
except Exception as e:
    print(f"❌ HealingEngine 测试失败: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# 测试8：ReportGenerator
print("\n[测试8] ReportGenerator 生成报告...")
try:
    report_generator = ReportGenerator()
    
    # 创建一些测试结果
    results = [
        create_execution_result("TC_001", "passed", now, now),
        create_execution_result("TC_002", "failed", now, now, error="Test failed"),
        create_execution_result("TC_003", "passed", now, now)
    ]
    
    # 生成报告
    report = report_generator.generate(results)
    
    print(f"✅ ReportGenerator 测试成功")
    print(f"   - 总用例数: {report['summary']['total']}")
    print(f"   - 通过: {report['summary']['passed']}")
    print(f"   - 失败: {report['summary']['failed']}")
    print(f"   - 通过率: {report['summary']['pass_rate']}")
except Exception as e:
    print(f"❌ ReportGenerator 测试失败: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# 测试9：数据转换器
print("\n[测试9] 数据转换器测试...")
try:
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent / 'ai-test-platform'))
    
    from utils.model_converter import testcase_to_dict, dict_to_testcase
    
    # TestCase → Dict
    tc_dict = testcase_to_dict(test_case)
    print(f"✅ TestCase → Dict 转换成功")
    print(f"   - ID: {tc_dict['id']}")
    print(f"   - Priority: {tc_dict['priority']}")
    print(f"   - Data Type: {tc_dict['data_type']}")
    
    # Dict → TestCase
    tc_obj = dict_to_testcase(tc_dict)
    print(f"✅ Dict → TestCase 转换成功")
    print(f"   - ID: {tc_obj.id}")
    print(f"   - Priority: {tc_obj.priority.value}")
    print(f"   - Data Type: {tc_obj.data_type.value}")
except Exception as e:
    print(f"❌ 数据转换器测试失败: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# 总结
print("\n" + "=" * 60)
print("✅ 所有测试通过！架构重构成功！")
print("=" * 60)
print("\n重构效果：")
print("  ✅ Core 层正常工作")
print("  ✅ Modules 层正常工作")
print("  ✅ 数据模型统一")
print("  ✅ 枚举类型安全")
print("  ✅ 数据转换正常")
print("  ✅ Self-Healing 正常")
print("  ✅ 报告生成正常")
print("\n下一步：")
print("  1. 集成到 backend_api_server.py")
print("  2. 更新前端组件")
print("  3. 删除重复模块")
print("=" * 60)
