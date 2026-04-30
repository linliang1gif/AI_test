#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
AI测试平台 - 完整演示流程 (Full Pipeline)
集成 Intelligence Agent → ExecutionEngine → Self-Healing → Report
"""

import sys
import os
from pathlib import Path
import time
from datetime import datetime

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

print("AI测试平台 - 完整演示流程")
print("="*60)
print("演示: 用户系统API测试")
print("API: https://jsonplaceholder.typicode.com")
print("流程: Intelligence → Execution → Healing → Report")
print("="*60)

# 导入核心模块
try:
    from core import TestCase, TestCaseStatus, TestCasePriority, create_test_case
    from modules.agents.execution_agent import ExecutionAgent
    from modules.healing.healing_engine import HealingEngine
    from modules.report.report_generator import ReportGenerator
    MODULES_AVAILABLE = True
    print("✅ 核心模块加载成功")
except ImportError as e:
    print(f"❌ 模块导入失败: {e}")
    print("提示: 请确保在项目根目录运行")
    sys.exit(1)

def print_section(title):
    """打印分节标题"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def step1_create_testcases():
    """步骤1: 创建测试用例"""
    print_section("步骤1: Intelligence Agent - 生成测试用例")
    
    # 模拟从Swagger生成测试用例
    test_cases = [
        create_test_case(
            id='TC_001',
            title='获取用户列表',
            module='用户管理',
            priority=TestCasePriority.HIGH,
            steps=['发送GET请求到/users', '验证返回状态码为200', '验证返回用户列表'],
            expected='返回用户列表,状态码200',
            execution_config={
                'url': 'https://jsonplaceholder.typicode.com/users',
                'method': 'GET',
                'expected_status': 200
            }
        ),
        create_test_case(
            id='TC_002',
            title='获取单个用户',
            module='用户管理',
            priority=TestCasePriority.HIGH,
            steps=['发送GET请求到/users/1', '验证返回状态码为200', '验证返回用户详情'],
            expected='返回用户详情,状态码200',
            execution_config={
                'url': 'https://jsonplaceholder.typicode.com/users/1',
                'method': 'GET',
                'expected_status': 200
            }
        ),
        create_test_case(
            id='TC_003',
            title='创建用户',
            module='用户管理',
            priority=TestCasePriority.MEDIUM,
            steps=['发送POST请求到/users', '传入用户数据', '验证返回状态码为201'],
            expected='创建成功,状态码201',
            execution_config={
                'url': 'https://jsonplaceholder.typicode.com/users',
                'method': 'POST',
                'data': {
                    'name': 'Test User',
                    'email': 'test@example.com'
                },
                'expected_status': 201
            }
        ),
        create_test_case(
            id='TC_004',
            title='获取不存在的用户',
            module='用户管理',
            priority=TestCasePriority.LOW,
            steps=['发送GET请求到/users/999', '验证返回状态码为404'],
            expected='返回404错误',
            execution_config={
                'url': 'https://jsonplaceholder.typicode.com/users/999',
                'method': 'GET',
                'expected_status': 404
            }
        )
    ]
    
    print(f"✅ 生成了 {len(test_cases)} 个测试用例")
    for tc in test_cases:
        priority_emoji = "🔴" if tc.priority == TestCasePriority.HIGH else "🟡" if tc.priority == TestCasePriority.MEDIUM else "🟢"
        print(f"   {priority_emoji} {tc.id}: {tc.title} (优先级: {tc.priority.value})")
    
    return test_cases

def step2_generate_execution_plan(test_cases):
    """步骤2: Intelligence Agent - 生成执行计划"""
    print_section("步骤2: Intelligence Agent - 生成执行计划")
    
    # 分析测试用例
    high_priority = [tc for tc in test_cases if tc.priority == TestCasePriority.HIGH]
    medium_priority = [tc for tc in test_cases if tc.priority == TestCasePriority.MEDIUM]
    low_priority = [tc for tc in test_cases if tc.priority == TestCasePriority.LOW]
    
    print(f"📊 测试用例分析:")
    print(f"   高优先级: {len(high_priority)}个")
    print(f"   中优先级: {len(medium_priority)}个")
    print(f"   低优先级: {len(low_priority)}个")
    
    print(f"\n🎯 执行策略:")
    print(f"   策略: 自适应执行 (高优先级串行,低优先级并行)")
    print(f"   并发数: 2")
    print(f"   超时: 30秒")
    print(f"   重试: 最多3次")
    
    execution_plan = {
        'strategy': 'adaptive',
        'max_workers': 2,
        'timeout': 30,
        'max_retry': 3
    }
    
    return execution_plan

def step3_execute_tests(test_cases, execution_plan):
    """步骤3: ExecutionEngine - 执行测试"""
    print_section("步骤3: ExecutionEngine - 执行测试")
    
    # 创建执行代理
    agent = ExecutionAgent(config={
        'strategy': execution_plan['strategy'],
        'max_workers': execution_plan['max_workers'],
        'timeout': execution_plan['timeout'],
        'max_retry_count': execution_plan['max_retry'],
        'use_real_engine': False  # 使用模拟执行(更稳定)
    })
    
    print(f"🚀 开始执行测试...")
    start_time = time.time()
    
    # 执行测试
    results = agent.run(test_cases)
    
    duration = time.time() - start_time
    
    # 统计结果
    passed = sum(1 for r in results if r.status == TestCaseStatus.PASSED)
    failed = sum(1 for r in results if r.status == TestCaseStatus.FAILED)
    
    print(f"\n✅ 执行完成 (耗时: {duration:.2f}秒)")
    print(f"   通过: {passed}/{len(results)}")
    print(f"   失败: {failed}/{len(results)}")
    
    # 显示执行详情
    for r in results:
        status_emoji = "✅" if r.status == TestCaseStatus.PASSED else "❌"
        print(f"   {status_emoji} {r.test_case_id}: {r.status.value} ({r.duration:.2f}s)")
    
    return results

def step4_self_healing(results):
    """步骤4: Self-Healing - 自动修复"""
    print_section("步骤4: Self-Healing Engine - 自动修复")
    
    # 创建修复引擎
    healing_engine = HealingEngine(config={
        'enable_l1': True,
        'enable_l2': True,
        'enable_l3': True,
        'enable_l4': True,
        'max_retry': 3
    })
    
    print(f"🔧 开始分析失败用例...")
    
    # 执行修复
    healed_results = healing_engine.heal(results)
    
    # 获取修复报告
    healing_report = healing_engine.get_healing_report()
    
    print(f"\n✅ 修复分析完成")
    print(f"   总用例数: {healing_report['total_cases']}")
    print(f"   修复用例数: {healing_report['healed_cases']}")
    print(f"   修复率: {healing_report['healing_rate']}")
    
    # 显示修复详情
    by_level = healing_report['by_level']
    if by_level['L1_RETRY']['count'] > 0:
        print(f"   L1-重试: {by_level['L1_RETRY']['count']}个 ({by_level['L1_RETRY']['description']})")
    if by_level['L2_DATA']['count'] > 0:
        print(f"   L2-数据: {by_level['L2_DATA']['count']}个 ({by_level['L2_DATA']['description']})")
    if by_level['L3_TOLERANCE']['count'] > 0:
        print(f"   L3-容错: {by_level['L3_TOLERANCE']['count']}个 ({by_level['L3_TOLERANCE']['description']})")
    if by_level['L4_MANUAL']['count'] > 0:
        print(f"   L4-人工: {by_level['L4_MANUAL']['count']}个 ({by_level['L4_MANUAL']['description']})")
    
    return healed_results, healing_report

def step5_generate_report(results, healing_report):
    """步骤5: Report Generator - 生成报告"""
    print_section("步骤5: Report Generator - 生成报告")
    
    # 创建报告生成器
    report_gen = ReportGenerator(config={
        'slow_threshold': 2.0,
        'include_response': False
    })
    
    print(f"📝 生成测试报告...")
    
    # 生成报告
    report = report_gen.generate(results)
    
    # 打印控制台报告
    print(f"\n{'='*60}")
    print(f"  AI测试执行报告")
    print(f"{'='*60}")
    print(f"总用例数: {report['summary']['total']}")
    print(f"执行用例数: {report['summary']['total']}")
    print(f"跳过用例数: 0")
    print(f"成功率: {report['summary']['pass_rate']}")
    print(f"通过: {report['summary']['passed']}")
    print(f"失败: {report['summary']['failed']}")
    
    # 失败原因Top3
    if report['failures']:
        print(f"\n失败原因Top3:")
        for i, f in enumerate(report['failures'][:3], 1):
            print(f"   {i}. {f['test_case_id']}: {f['error'][:50]}...")
    else:
        print(f"\n失败原因Top3: 无")
    
    # 修复次数
    print(f"\n修复次数: {healing_report['healed_cases']}")
    
    # 优化建议
    if report['summary']['failed'] == 0:
        print(f"优化建议: 所有测试用例执行正常")
    else:
        print(f"优化建议: 有{report['summary']['failed']}个用例失败,建议检查失败原因")
    
    print(f"{'='*60}\n")
    
    return report

def step6_save_html_report(results):
    """步骤6: 生成HTML报告"""
    print_section("步骤6: 生成HTML报告")
    
    # 创建报告生成器
    report_gen = ReportGenerator(config={
        'slow_threshold': 2.0,
        'include_response': False
    })
    
    # 生成HTML报告
    output_dir = Path(__file__).parent / 'output'
    output_dir.mkdir(exist_ok=True)
    
    report_path = output_dir / 'demo_report_full.html'
    
    print(f"📄 生成HTML报告...")
    report_gen.save_report(results, str(report_path), format='html')
    
    print(f"✅ HTML报告已生成: {report_path}")
    print(f"   打开浏览器查看: file:///{report_path.absolute()}")
    
    return report_path

def main():
    """主函数"""
    start_time = time.time()
    
    print(f"\n开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    try:
        # 步骤1: 创建测试用例
        test_cases = step1_create_testcases()
        
        # 步骤2: 生成执行计划
        execution_plan = step2_generate_execution_plan(test_cases)
        
        # 步骤3: 执行测试
        results = step3_execute_tests(test_cases, execution_plan)
        
        # 步骤4: Self-Healing
        healed_results, healing_report = step4_self_healing(results)
        
        # 步骤5: 生成报告
        report = step5_generate_report(healed_results, healing_report)
        
        # 步骤6: 保存HTML报告
        html_path = step6_save_html_report(healed_results)
        
        # 总结
        duration = time.time() - start_time
        print(f"\n{'='*60}")
        print(f"✅ 完整演示流程执行成功!")
        print(f"{'='*60}")
        print(f"总耗时: {duration:.2f}秒")
        print(f"成功率: {report['summary']['pass_rate']}")
        print(f"HTML报告: {html_path}")
        print(f"{'='*60}\n")
        
        return 0
        
    except KeyboardInterrupt:
        print("\n\n⚠️  演示被用户中断")
        return 1
    except Exception as e:
        print(f"\n\n❌ 演示失败: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
