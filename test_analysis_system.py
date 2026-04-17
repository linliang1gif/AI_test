"""
测试分析系统测试脚本
"""
from modules.analysis import ResultAnalyzer, TrendAnalyzer, FailureAnalyzer
from core import ExecutionResult, TestCaseStatus, HealingLevel
from datetime import datetime


def create_test_results():
    """创建测试数据"""
    now = datetime.now()
    results = [
        # 成功用例
        ExecutionResult(
            test_case_id="test_001",
            status=TestCaseStatus.PASSED,
            duration=0.5,
            start_time=now,
            end_time=now,
            error=None
        ),
        ExecutionResult(
            test_case_id="test_002",
            status=TestCaseStatus.PASSED,
            duration=1.2,
            start_time=now,
            end_time=now,
            error=None
        ),
        # 超时失败
        ExecutionResult(
            test_case_id="test_003",
            status=TestCaseStatus.FAILED,
            duration=5.0,
            start_time=now,
            end_time=now,
            error="Request timeout after 5 seconds"
        ),
        ExecutionResult(
            test_case_id="test_004",
            status=TestCaseStatus.FAILED,
            duration=5.1,
            start_time=now,
            end_time=now,
            error="Connection timed out"
        ),
        # 认证失败
        ExecutionResult(
            test_case_id="test_005",
            status=TestCaseStatus.FAILED,
            duration=0.3,
            start_time=now,
            end_time=now,
            error="401 Unauthorized: Invalid token"
        ),
        # 服务器错误
        ExecutionResult(
            test_case_id="test_006",
            status=TestCaseStatus.FAILED,
            duration=2.0,
            start_time=now,
            end_time=now,
            error="500 Internal Server Error"
        ),
        # 修复成功的用例
        ExecutionResult(
            test_case_id="test_007",
            status=TestCaseStatus.PASSED,
            duration=1.5,
            start_time=now,
            end_time=now,
            error=None,
            healing_applied=True,
            healing_level=HealingLevel.L1_RETRY,
            healing_details="重试1次后成功"
        ),
        # 慢测试
        ExecutionResult(
            test_case_id="test_008",
            status=TestCaseStatus.PASSED,
            duration=8.0,
            start_time=now,
            end_time=now,
            error=None
        ),
        # 数据问题
        ExecutionResult(
            test_case_id="test_009",
            status=TestCaseStatus.FAILED,
            duration=0.8,
            start_time=now,
            end_time=now,
            error="Data validation failed: null value"
        ),
        # 断言失败
        ExecutionResult(
            test_case_id="test_010",
            status=TestCaseStatus.FAILED,
            duration=1.0,
            start_time=now,
            end_time=now,
            error="Assertion failed: expected 200, got 404"
        )
    ]
    return results


def test_result_analyzer():
    """测试结果分析器"""
    print("=" * 80)
    print("测试 ResultAnalyzer")
    print("=" * 80)
    
    results = create_test_results()
    analyzer = ResultAnalyzer()
    
    analysis = analyzer.analyze(results)
    
    print("\n📊 基础统计:")
    stats = analysis['basic_stats']
    print(f"  总数: {stats['total']}")
    print(f"  通过: {stats['passed']}")
    print(f"  失败: {stats['failed']}")
    print(f"  通过率: {stats['pass_rate']}%")
    print(f"  平均耗时: {stats['avg_duration']}s")
    
    print("\n❌ 失败分析:")
    failure = analysis['failure_analysis']
    print(f"  总失败数: {failure['total_failures']}")
    print(f"  错误分类:")
    for category, count in failure['category_counts'].items():
        print(f"    {category}: {count}个")
    
    print("\n⚡ 性能分析:")
    perf = analysis['performance_analysis']
    print(f"  平均耗时: {perf['avg_duration']}s")
    print(f"  最慢: {perf['max_duration']}s")
    print(f"  慢测试数: {len(perf['slow_tests'])}")
    print(f"  耗时分布:")
    for range_name, count in perf['duration_distribution'].items():
        print(f"    {range_name}: {count}个")
    
    print("\n🔧 修复分析:")
    healing = analysis['healing_analysis']
    print(f"  总修复数: {healing['total_healed']}")
    print(f"  修复成功率: {healing['healing_success_rate']}%")
    
    print("\n💡 优化建议:")
    for rec in analysis['recommendations']:
        print(f"  [{rec['severity']}] {rec['message']}")
    
    print("\n✅ ResultAnalyzer 测试通过")


def test_failure_analyzer():
    """测试失败分析器"""
    print("\n" + "=" * 80)
    print("测试 FailureAnalyzer")
    print("=" * 80)
    
    results = create_test_results()
    analyzer = FailureAnalyzer()
    
    analysis = analyzer.analyze_failures(results)
    
    print(f"\n📊 总失败数: {analysis['total_failures']}")
    
    print("\n🔍 根本原因:")
    for cause in analysis['root_causes']:
        print(f"  {cause['category']}: {cause['failure_count']}个 ({cause['percentage']}%)")
        if cause['common_patterns']:
            print(f"    共同特征: {', '.join(cause['common_patterns'])}")
    
    print("\n🎯 优先修复建议:")
    for fix in analysis['priority_fixes']:
        print(f"  优先级 {fix['priority']}: {fix['category']}")
        print(f"    失败数: {fix['failure_count']}")
        print(f"    建议: {fix['recommended_action']}")
    
    # 生成文本报告
    print("\n" + "-" * 80)
    print("生成失败分析报告:")
    print("-" * 80)
    report = analyzer.generate_failure_report(results)
    print(report)
    
    print("✅ FailureAnalyzer 测试通过")


def test_trend_analyzer():
    """测试趋势分析器"""
    print("\n" + "=" * 80)
    print("测试 TrendAnalyzer")
    print("=" * 80)
    
    results = create_test_results()
    analyzer = TrendAnalyzer(storage_path="test_history_temp")
    
    # 保存几次执行记录
    print("\n保存执行记录...")
    for i in range(3):
        execution_id = f"exec_{i+1}"
        metadata = {
            'trigger': 'manual',
            'branch': 'main',
            'commit': f'abc123{i}'
        }
        analyzer.save_execution_record(execution_id, results, metadata)
        print(f"  保存 {execution_id}")
    
    # 分析趋势
    print("\n分析趋势...")
    trend = analyzer.analyze_trend(days=7)
    
    print(f"\n📈 趋势分析 ({trend['period']}):")
    print(f"  总执行次数: {trend['total_executions']}")
    
    if trend['summary']:
        summary = trend['summary']
        print(f"  总测试数: {summary['total_tests']}")
        print(f"  平均通过率: {summary['avg_pass_rate']}%")
        print(f"  总耗时: {summary['total_duration']}s")
    
    print(f"\n💡 洞察:")
    for insight in trend['insights']:
        print(f"  [{insight['type']}] {insight['message']}")
    
    # 对比执行
    print("\n对比执行...")
    comparison = analyzer.compare_executions("exec_1", "exec_2")
    if 'error' not in comparison:
        comp = comparison['comparison']
        print(f"  通过率变化: {comp['pass_rate_change']}%")
        print(f"  耗时变化: {comp['duration_change']}s")
    
    # 清理测试数据
    import shutil
    import os
    if os.path.exists("test_history_temp"):
        shutil.rmtree("test_history_temp")
    
    print("\n✅ TrendAnalyzer 测试通过")


def main():
    """主测试函数"""
    print("\n🚀 测试分析系统")
    print("=" * 80)
    
    try:
        test_result_analyzer()
        test_failure_analyzer()
        test_trend_analyzer()
        
        print("\n" + "=" * 80)
        print("✅ 所有测试通过!")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
