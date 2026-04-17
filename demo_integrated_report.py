"""
集成报告系统演示
"""
from modules.analysis import IntegratedReportSystem
from core import ExecutionResult, TestCaseStatus, HealingLevel
from datetime import datetime


def create_demo_results():
    """创建演示数据"""
    now = datetime.now()
    results = []
    
    # 创建20个测试用例
    for i in range(20):
        if i < 12:  # 12个成功
            result = ExecutionResult(
                test_case_id=f"test_{i+1:03d}",
                status=TestCaseStatus.PASSED,
                duration=0.5 + i * 0.1,
                start_time=now,
                end_time=now,
                error=None
            )
        elif i < 15:  # 3个超时失败
            result = ExecutionResult(
                test_case_id=f"test_{i+1:03d}",
                status=TestCaseStatus.FAILED,
                duration=5.0,
                start_time=now,
                end_time=now,
                error=f"Request timeout after 5 seconds"
            )
        elif i < 17:  # 2个认证失败
            result = ExecutionResult(
                test_case_id=f"test_{i+1:03d}",
                status=TestCaseStatus.FAILED,
                duration=0.3,
                start_time=now,
                end_time=now,
                error="401 Unauthorized: Invalid token"
            )
        else:  # 3个其他失败
            errors = [
                "500 Internal Server Error",
                "Data validation failed: null value",
                "Assertion failed: expected 200, got 404"
            ]
            result = ExecutionResult(
                test_case_id=f"test_{i+1:03d}",
                status=TestCaseStatus.FAILED,
                duration=1.0,
                start_time=now,
                end_time=now,
                error=errors[i-17]
            )
        
        results.append(result)
    
    # 添加一个修复成功的用例
    results.append(ExecutionResult(
        test_case_id="test_021",
        status=TestCaseStatus.PASSED,
        duration=1.5,
        start_time=now,
        end_time=now,
        error=None,
        healing_applied=True,
        healing_level=HealingLevel.L1_RETRY,
        healing_details="重试1次后成功"
    ))
    
    return results


def main():
    """主演示函数"""
    print("🚀 集成报告系统演示")
    print("=" * 80)
    
    # 创建报告系统
    report_system = IntegratedReportSystem()
    
    # 创建测试数据
    print("\n📝 创建测试数据...")
    results = create_demo_results()
    print(f"  创建了 {len(results)} 个测试结果")
    
    # 生成综合报告
    print("\n📊 生成综合报告...")
    execution_id = f"demo_exec_{int(datetime.now().timestamp())}"
    metadata = {
        'trigger': 'manual',
        'branch': 'main',
        'commit': 'abc123',
        'author': 'demo_user'
    }
    
    report = report_system.generate_comprehensive_report(
        execution_id=execution_id,
        results=results,
        metadata=metadata
    )
    
    # 显示摘要
    print("\n✅ 报告生成成功!")
    print("\n📈 执行摘要:")
    summary = report['summary']
    print(f"  总用例数: {summary['total']}")
    print(f"  通过: {summary['passed']}")
    print(f"  失败: {summary['failed']}")
    print(f"  通过率: {summary['pass_rate']}")
    print(f"  总耗时: {summary['total_duration']}s")
    
    # 显示失败分析
    failure_analysis = report['failure_analysis']
    if failure_analysis['total_failures'] > 0:
        print(f"\n❌ 失败分析:")
        print(f"  总失败数: {failure_analysis['total_failures']}")
        for cause in failure_analysis['root_causes'][:3]:
            print(f"    {cause['category']}: {cause['failure_count']}个 ({cause['percentage']}%)")
    
    # 显示优化建议
    if report['recommendations']:
        print(f"\n💡 优化建议 (前5条):")
        for rec in report['recommendations'][:5]:
            print(f"  [{rec['severity']}] {rec['message']}")
    
    # 保存报告
    print("\n💾 保存报告...")
    file_paths = report_system.save_report(
        execution_id=execution_id,
        results=results,
        metadata=metadata,
        output_dir="demo_reports",
        formats=['json', 'html', 'text']
    )
    
    print("\n📁 报告已保存:")
    for format_type, path in file_paths.items():
        print(f"  {format_type.upper()}: {path}")
    
    print("\n" + "=" * 80)
    print("✅ 演示完成!")
    print("=" * 80)


if __name__ == "__main__":
    main()
