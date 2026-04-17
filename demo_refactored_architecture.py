#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
重构后架构演示
展示完整的测试流程：Swagger → 测试用例 → 执行 → 修复 → 报告
"""

import json
from pathlib import Path

print("=" * 80)
print("重构后架构完整流程演示")
print("=" * 80)

# ==================== 步骤1：导入模块 ====================
print("\n[步骤1] 导入 Core 和 Modules...")

from core import (
    TestCase,
    ExecutionResult,
    TestCaseStatus,
    DataType,
    ExpectedBehavior,
    create_test_case
)

from modules.swagger import SwaggerTestCaseGenerator
from modules.executor import ExecutionEngine
from modules.healing import HealingEngine
from modules.report import ReportGenerator
from modules.data import TestDataManager

print("✅ 模块导入成功")

# ==================== 步骤2：从 Swagger 生成测试用例 ====================
print("\n[步骤2] 从 Swagger 生成测试用例...")

swagger_file = "examples/sample_swagger.json"

if not Path(swagger_file).exists():
    print(f"⚠️  Swagger 文件不存在: {swagger_file}")
    print("使用手动创建的测试用例...")
    
    # 手动创建测试用例
    test_cases = [
        create_test_case(
            id="TC_001",
            title="用户登录 - 正常流程",
            module="用户管理",
            priority="high",
            status="pending",
            steps=[
                "1. 调用 POST /api/login",
                "2. 传入正确的用户名和密码",
                "3. 验证返回 token"
            ],
            expected="返回 200 状态码，包含有效的 JWT token",
            data_type="valid",
            expected_behavior="success",
            execution_config={
                "method": "POST",
                "url": "/api/login",
                "body": {
                    "username": "test_user",
                    "password": "test_pass"
                }
            },
            assertions=[
                {
                    "type": "status_code",
                    "operator": "equals",
                    "expected": 200
                },
                {
                    "type": "json_path",
                    "field": "token",
                    "operator": "exists",
                    "expected": True
                }
            ]
        ),
        create_test_case(
            id="TC_002",
            title="用户登录 - 参数校验",
            module="用户管理",
            priority="high",
            status="pending",
            steps=[
                "1. 调用 POST /api/login",
                "2. 传入空的用户名或密码",
                "3. 验证返回错误提示"
            ],
            expected="返回 400 状态码，提示参数错误",
            data_type="invalid",
            expected_behavior="client_error",
            execution_config={
                "method": "POST",
                "url": "/api/login",
                "body": {
                    "username": "",
                    "password": ""
                }
            },
            assertions=[
                {
                    "type": "status_code",
                    "operator": "in",
                    "expected": [400, 422]
                }
            ]
        ),
        create_test_case(
            id="TC_003",
            title="获取用户信息 - 正常流程",
            module="用户管理",
            priority="medium",
            status="pending",
            steps=[
                "1. 调用 GET /api/user/info",
                "2. 传入有效的 token",
                "3. 验证返回用户信息"
            ],
            expected="返回 200 状态码，包含用户详细信息",
            data_type="valid",
            expected_behavior="success",
            execution_config={
                "method": "GET",
                "url": "/api/user/info",
                "headers": {
                    "Authorization": "Bearer test_token"
                }
            },
            assertions=[
                {
                    "type": "status_code",
                    "expected": 200
                },
                {
                    "type": "json_path",
                    "field": "username",
                    "operator": "exists",
                    "expected": True
                }
            ]
        )
    ]
else:
    # 从 Swagger 生成
    generator = SwaggerTestCaseGenerator(swagger_file)
    test_cases = generator.generate_all_testcases()
    
    # 获取统计信息
    stats = generator.get_statistics(test_cases)
    print(f"✅ 从 Swagger 生成了 {stats['total']} 个测试用例")
    print(f"   - 按优先级: {stats['by_priority']}")
    print(f"   - 按数据类型: {stats['by_data_type']}")
    print(f"   - 按预期行为: {stats['by_expected_behavior']}")

print(f"\n生成的测试用例：")
for tc in test_cases[:3]:  # 只显示前3个
    print(f"  - {tc.id}: {tc.title}")
    print(f"    数据类型: {tc.data_type.value}, 预期行为: {tc.expected_behavior.value}")

# ==================== 步骤3：生成测试数据 ====================
print("\n[步骤3] 生成测试数据...")

data_manager = TestDataManager()

# 为第一个测试用例生成数据
if test_cases:
    tc = test_cases[0]
    if tc.execution_config and tc.execution_config.get('body'):
        print(f"\n为 {tc.id} 生成测试数据...")
        
        # 定义数据 schema
        schema = {
            "username": {"type": "string", "minLength": 3, "maxLength": 20},
            "password": {"type": "string", "minLength": 6, "maxLength": 20}
        }
        
        # 生成不同类型的数据
        valid_data = data_manager.generate_data(schema, "valid", tc.id)
        boundary_data = data_manager.generate_data(schema, "boundary", f"{tc.id}_boundary")
        invalid_data = data_manager.generate_data(schema, "invalid", f"{tc.id}_invalid")
        
        print(f"  ✅ 正常数据: {valid_data}")
        print(f"  ✅ 边界数据: {boundary_data}")
        print(f"  ✅ 异常数据: {invalid_data}")

# ==================== 步骤4：执行测试（模拟） ====================
print("\n[步骤4] 执行测试用例（模拟）...")

# 注意：这里是模拟执行，实际执行需要真实的 API 服务
# 创建模拟的执行结果
from datetime import datetime

mock_results = []
for i, tc in enumerate(test_cases[:3]):
    now = datetime.now()
    
    # 模拟不同的执行结果
    if i == 0:
        # 第一个用例：成功
        from core import create_execution_result
        result = create_execution_result(
            test_case_id=tc.id,
            status="passed",
            start_time=now,
            end_time=now,
            error=None
        )
        result.assertions_passed = 2
        result.assertions_failed = 0
    elif i == 1:
        # 第二个用例：失败（连接超时）
        result = create_execution_result(
            test_case_id=tc.id,
            status="failed",
            start_time=now,
            end_time=now,
            error="Connection timeout after 30s"
        )
        result.assertions_passed = 0
        result.assertions_failed = 1
    else:
        # 第三个用例：成功
        result = create_execution_result(
            test_case_id=tc.id,
            status="passed",
            start_time=now,
            end_time=now,
            error=None
        )
        result.assertions_passed = 2
        result.assertions_failed = 0
    
    mock_results.append(result)

print(f"✅ 执行了 {len(mock_results)} 个测试用例")
for result in mock_results:
    status_icon = "✅" if result.status == TestCaseStatus.PASSED else "❌"
    print(f"  {status_icon} {result.test_case_id}: {result.status.value}")

# ==================== 步骤5：Self-Healing 修复 ====================
print("\n[步骤5] 应用 Self-Healing 修复...")

healing_engine = HealingEngine({
    "enable_l1": True,
    "enable_l2": True,
    "enable_l3": True,
    "enable_l4": True,
    "max_retry": 3
})

healed_results = healing_engine.heal(mock_results)

print(f"✅ Self-Healing 分析完成")
for result in healed_results:
    if result.healing_applied:
        print(f"  🔧 {result.test_case_id}:")
        print(f"     修复级别: {result.healing_level.value}")
        print(f"     修复详情: {result.healing_details}")

# 获取修复报告
healing_report = healing_engine.get_healing_report()
print(f"\n修复统计:")
print(f"  - 总用例数: {healing_report['total_cases']}")
print(f"  - 修复用例数: {healing_report['healed_cases']}")
print(f"  - 修复率: {healing_report['healing_rate']}")

# ==================== 步骤6：生成测试报告 ====================
print("\n[步骤6] 生成测试报告...")

report_generator = ReportGenerator({
    "slow_threshold": 2.0,
    "include_response": False
})

report = report_generator.generate(healed_results)

print(f"\n✅ 测试报告生成成功")
print(f"\n📊 测试摘要:")
print(f"  - 总用例数: {report['summary']['total']}")
print(f"  - ✅ 通过: {report['summary']['passed']}")
print(f"  - ❌ 失败: {report['summary']['failed']}")
print(f"  - 通过率: {report['summary']['pass_rate']}")
print(f"  - 总耗时: {report['summary']['total_duration']}s")

if report['healing_summary']['total_healed'] > 0:
    print(f"\n🔧 Self-Healing 修复:")
    print(f"  - L1-重试: {report['healing_summary']['retry']}")
    print(f"  - L2-重建数据: {report['healing_summary']['regenerate_data']}")
    print(f"  - L3-容错: {report['healing_summary']['flaky']}")
    print(f"  - L4-人工审查: {report['healing_summary']['manual']}")

# 生成文本报告
text_report = report_generator.generate_text_report(healed_results)
print(f"\n📄 文本报告:")
print(text_report)

# ==================== 步骤7：数据转换（API 响应格式） ====================
print("\n[步骤7] 数据转换为 API 响应格式...")

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / 'ai-test-platform'))

from utils.model_converter import (
    testcase_to_dict,
    execution_result_to_dict,
    testcases_to_list,
    execution_results_to_list
)

# 转换测试用例
api_testcases = testcases_to_list(test_cases[:3])
print(f"✅ 转换了 {len(api_testcases)} 个测试用例为 API 格式")

# 转换执行结果
api_results = execution_results_to_list(healed_results)
print(f"✅ 转换了 {len(api_results)} 个执行结果为 API 格式")

# 示例：第一个测试用例的 API 格式
print(f"\n示例 - 测试用例 API 格式:")
print(json.dumps(api_testcases[0], indent=2, ensure_ascii=False))

# ==================== 总结 ====================
print("\n" + "=" * 80)
print("✅ 完整流程演示成功！")
print("=" * 80)

print("\n流程总结:")
print("  1. ✅ 从 Swagger 生成测试用例（或手动创建）")
print("  2. ✅ 使用 TestDataManager 生成测试数据")
print("  3. ✅ 执行测试用例（模拟）")
print("  4. ✅ 应用 Self-Healing 修复")
print("  5. ✅ 生成测试报告")
print("  6. ✅ 转换为 API 响应格式")

print("\n架构优势:")
print("  ✅ 数据模型统一（core 层）")
print("  ✅ 类型安全（枚举）")
print("  ✅ 功能模块化（modules 层）")
print("  ✅ 易于集成（转换器）")
print("  ✅ 自动修复（Self-Healing）")

print("\n下一步:")
print("  1. 集成到 backend_api_server.py")
print("  2. 连接真实的 API 服务")
print("  3. 更新前端组件")

print("=" * 80)
