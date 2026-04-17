"""
测试ReportGenerator与Pipeline的集成
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from modules.report import ReportGenerator
from modules.executor.execution_engine import ExecutionResult


def test_integration():
    """测试集成"""
    print("=" * 80)
    print("测试ReportGenerator与Pipeline集成")
    print("=" * 80)
    
    # 模拟执行结果
    results = [
        ExecutionResult("TC_001", "passed", 0.5, None, retry_count=0),
        ExecutionResult("TC_002", "passed", 1.2, None, retry_count=0),
        ExecutionResult("TC_003", "failed", 0.8, "Assertion failed: status_code expected 200, got 404", retry_count=2),
        ExecutionResult("TC_004", "error", 0.3, "Connection timeout", retry_count=0),
        ExecutionResult("TC_005", "passed", 3.5, None, retry_count=0),
        ExecutionResult("TC_006", "passed", 0.7, None, retry_count=1),
        ExecutionResult("TC_007", "failed", 1.1, "Assertion failed: json_path data.id not found", retry_count=3),
        ExecutionResult("TC_008", "passed", 2.8, None, retry_count=0),
    ]
    
    # 创建输出目录
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    
    # 使用ReportGenerator生成报告
    report_generator = ReportGenerator()
    
    print("\n生成报告...")
    
    # 保存JSON报告
    report_json_file = output_dir / "test_report.json"
    report_generator.save_report(results, str(report_json_file), format="json")
    print(f"✅ JSON报告: {report_json_file}")
    
    # 保存文本报告
    report_txt_file = output_dir / "test_report.txt"
    report_generator.save_report(results, str(report_txt_file), format="text")
    print(f"✅ 文本报告: {report_txt_file}")
    
    # 保存HTML报告
    report_html_file = output_dir / "test_report.html"
    report_generator.save_report(results, str(report_html_file), format="html")
    print(f"✅ HTML报告: {report_html_file}")
    
    # 显示报告摘要
    report = report_generator.generate(results)
    print(f"\n📊 报告摘要:")
    print(f"   总用例: {report['summary']['total']}")
    print(f"   通过: {report['summary']['passed']}")
    print(f"   失败: {report['summary']['failed']}")
    print(f"   错误: {report['summary']['error']}")
    print(f"   通过率: {report['summary']['pass_rate']}")
    print(f"   总耗时: {report['summary']['total_duration']}s")
    print(f"   慢测试: {len(report['slow_tests'])}个")
    print(f"   重试测试: {len(report['retried_tests'])}个")
    
    print("\n" + "=" * 80)
    print("🎉 集成测试完成！")
    print("=" * 80)


if __name__ == "__main__":
    test_integration()
