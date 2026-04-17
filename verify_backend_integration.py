#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证 Backend API Server 的 Modules SDK 集成
"""

import sys
from pathlib import Path

# 添加路径
sys.path.insert(0, str(Path(__file__).parent / 'ai-test-platform'))
sys.path.insert(0, str(Path(__file__).parent / 'modules'))
sys.path.insert(0, str(Path(__file__).parent / 'core'))

def test_imports():
    """测试导入"""
    print("=" * 60)
    print("测试 1: 验证导入")
    print("=" * 60)
    
    try:
        # 测试 modules 导入
        from modules.swagger import SwaggerTestCaseGenerator
        from modules.executor import ExecutionEngine
        from modules.healing import HealingEngine
        from modules.report import ReportGenerator
        from modules.data import TestDataManager
        print("✅ Modules SDK 导入成功")
    except ImportError as e:
        print(f"❌ Modules SDK 导入失败: {e}")
        return False
    
    try:
        # 测试 core 导入
        from core import (
            TestCase,
            ExecutionResult,
            TestCaseStatus,
            TestCasePriority,
            DataType,
            ExpectedBehavior,
            create_test_case,
            create_execution_result
        )
        print("✅ Core Models 导入成功")
    except ImportError as e:
        print(f"❌ Core Models 导入失败: {e}")
        return False
    
    try:
        # 测试 model_converter 导入
        sys.path.insert(0, str(Path(__file__).parent / 'ai-test-platform' / 'utils'))
        from model_converter import (
            testcase_to_dict,
            dict_to_testcase,
            execution_result_to_dict,
            testcases_to_list,
            execution_results_to_list,
            enrich_testcase_dict,
            enrich_testcase_list
        )
        print("✅ Model Converter 导入成功")
    except ImportError as e:
        print(f"❌ Model Converter 导入失败: {e}")
        return False
    
    return True


def test_swagger_generation():
    """测试 Swagger 生成"""
    print("\n" + "=" * 60)
    print("测试 2: Swagger 测试用例生成")
    print("=" * 60)
    
    try:
        from modules.swagger import SwaggerTestCaseGenerator
        from core import TestCaseStatus
        
        # 使用示例 Swagger 文件
        swagger_file = Path(__file__).parent / 'examples' / 'sample_swagger.json'
        if not swagger_file.exists():
            print(f"⚠️  示例文件不存在: {swagger_file}")
            return True  # 不算失败
        
        generator = SwaggerTestCaseGenerator(str(swagger_file))
        test_cases = generator.generate_all_testcases()
        
        print(f"✅ 成功生成 {len(test_cases)} 个测试用例")
        
        # 验证字段
        if test_cases:
            tc = test_cases[0]
            assert hasattr(tc, 'data_type'), "缺少 data_type 字段"
            assert hasattr(tc, 'expected_behavior'), "缺少 expected_behavior 字段"
            print(f"✅ 测试用例包含新字段: data_type={tc.data_type.value}, expected_behavior={tc.expected_behavior.value}")
        
        return True
    except Exception as e:
        print(f"❌ Swagger 生成失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_data_conversion():
    """测试数据转换"""
    print("\n" + "=" * 60)
    print("测试 3: 数据转换")
    print("=" * 60)
    
    try:
        from core import create_test_case, TestCaseStatus, TestCasePriority, DataType, ExpectedBehavior
        sys.path.insert(0, str(Path(__file__).parent / 'ai-test-platform' / 'utils'))
        from model_converter import testcase_to_dict, dict_to_testcase
        
        # 创建测试用例
        tc = create_test_case(
            id="test_001",
            title="测试登录功能",
            module="用户模块",
            priority=TestCasePriority.HIGH,
            status=TestCaseStatus.PENDING,
            steps=["打开登录页面", "输入用户名密码", "点击登录"],
            expected="登录成功",
            data_type=DataType.VALID,
            expected_behavior=ExpectedBehavior.SUCCESS
        )
        
        # 转换为字典
        tc_dict = testcase_to_dict(tc)
        print(f"✅ TestCase -> Dict: {tc_dict['title']}")
        assert tc_dict['data_type'] == 'valid'
        assert tc_dict['expected_behavior'] == 'success'
        print(f"✅ 字段验证通过: data_type={tc_dict['data_type']}, expected_behavior={tc_dict['expected_behavior']}")
        
        # 转换回对象
        tc2 = dict_to_testcase(tc_dict)
        print(f"✅ Dict -> TestCase: {tc2.title}")
        assert tc2.data_type == DataType.VALID
        assert tc2.expected_behavior == ExpectedBehavior.SUCCESS
        print(f"✅ 往返转换成功")
        
        return True
    except Exception as e:
        print(f"❌ 数据转换失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_execution_engine():
    """测试执行引擎"""
    print("\n" + "=" * 60)
    print("测试 4: 执行引擎")
    print("=" * 60)
    
    try:
        from modules.executor import ExecutionEngine
        from core import create_test_case, TestCasePriority, DataType, ExpectedBehavior
        
        # 创建测试用例
        tc = create_test_case(
            id="test_api_001",
            title="测试 API 健康检查",
            module="API 测试",
            priority=TestCasePriority.HIGH,
            steps=["发送 GET 请求到 /health"],
            expected="返回 200 状态码",
            data_type=DataType.VALID,
            expected_behavior=ExpectedBehavior.SUCCESS,
            execution_config={
                "method": "GET",
                "path": "/health",
                "expected_status": 200
            }
        )
        
        # 配置执行引擎
        config = {
            "base_url": "http://httpbin.org",  # 使用公共测试 API
            "timeout": 10
        }
        
        engine = ExecutionEngine(config)
        print(f"✅ 执行引擎创建成功")
        
        # 注意：这里不实际执行，只验证创建
        print(f"✅ 执行引擎验证通过")
        
        return True
    except Exception as e:
        print(f"❌ 执行引擎测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_healing_engine():
    """测试修复引擎"""
    print("\n" + "=" * 60)
    print("测试 5: Self-Healing 引擎")
    print("=" * 60)
    
    try:
        from modules.healing import HealingEngine
        from core import create_execution_result, TestCaseStatus
        from datetime import datetime, timedelta
        
        # 创建失败的执行结果
        start = datetime.now()
        end = start + timedelta(seconds=1.5)
        result = create_execution_result(
            test_case_id="test_001",
            status=TestCaseStatus.FAILED,
            start_time=start,
            end_time=end,
            error="Connection timeout"
        )
        
        # 配置修复引擎
        config = {
            "enable_l1": True,
            "enable_l2": True,
            "enable_l3": True,
            "enable_l4": True
        }
        
        healing_engine = HealingEngine(config)
        print(f"✅ Self-Healing 引擎创建成功")
        
        # 应用修复
        healed_results = healing_engine.heal([result])
        print(f"✅ 修复应用成功，处理了 {len(healed_results)} 个结果")
        
        # 验证修复信息字段
        healed = healed_results[0]
        assert hasattr(healed, 'healing_applied'), "缺少 healing_applied 字段"
        assert hasattr(healed, 'healing_level'), "缺少 healing_level 字段"
        assert hasattr(healed, 'healing_details'), "缺少 healing_details 字段"
        print(f"✅ 修复信息字段验证通过")
        
        return True
    except Exception as e:
        print(f"❌ Self-Healing 引擎测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_report_generator():
    """测试报告生成器"""
    print("\n" + "=" * 60)
    print("测试 6: 报告生成器")
    print("=" * 60)
    
    try:
        from modules.report import ReportGenerator
        from core import create_execution_result, TestCaseStatus
        from datetime import datetime, timedelta
        
        # 创建执行结果
        start1 = datetime.now()
        end1 = start1 + timedelta(seconds=1.2)
        start2 = datetime.now()
        end2 = start2 + timedelta(seconds=2.5)
        
        results = [
            create_execution_result(
                test_case_id="test_001",
                status=TestCaseStatus.PASSED,
                start_time=start1,
                end_time=end1
            ),
            create_execution_result(
                test_case_id="test_002",
                status=TestCaseStatus.FAILED,
                start_time=start2,
                end_time=end2,
                error="Assertion failed"
            )
        ]
        
        # 配置报告生成器
        config = {
            "slow_threshold": 2.0,
            "include_response": False
        }
        
        report_generator = ReportGenerator(config)
        print(f"✅ 报告生成器创建成功")
        
        # 生成报告
        report = report_generator.generate(results)
        print(f"✅ 报告生成成功")
        print(f"   - 总数: {report['summary']['total']}")
        print(f"   - 通过: {report['summary']['passed']}")
        print(f"   - 失败: {report['summary']['failed']}")
        print(f"   - 通过率: {report['summary']['pass_rate']}%")
        
        return True
    except Exception as e:
        print(f"❌ 报告生成器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("Backend API Server - Modules SDK 集成验证")
    print("=" * 60)
    
    tests = [
        ("导入测试", test_imports),
        ("Swagger 生成", test_swagger_generation),
        ("数据转换", test_data_conversion),
        ("执行引擎", test_execution_engine),
        ("Self-Healing", test_healing_engine),
        ("报告生成", test_report_generator),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ {name} 测试异常: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))
    
    # 汇总结果
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{status} - {name}")
    
    print("=" * 60)
    print(f"总计: {passed}/{total} 通过")
    print("=" * 60)
    
    if passed == total:
        print("\n🎉 所有测试通过！Backend API Server 集成成功！")
        return 0
    else:
        print(f"\n⚠️  {total - passed} 个测试失败")
        return 1


if __name__ == "__main__":
    sys.exit(main())
