"""
ReportGenerator演示脚本
展示如何使用报告生成器
"""
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.report import ReportGenerator
from modules.executor.execution_engine import ExecutionResult


def demo_basic_report():
    """演示1: 基本报告生成"""
    print("=" * 80)
    print("演示1: 基本报告生成")
    print("=" * 80)
    
    # 模拟执行结果
    results = [
        ExecutionResult(
            test_case_id="TC_001",
            status="passed",
            duration=0.5,
            error_message=None
        ),
        ExecutionResult(
            test_case_id="TC_002",
            status="passed",
            duration=1.2,
            error_message=None
        ),
        ExecutionResult(
            test_case_id="TC_003",
            status="failed",
            duration=0.8,
            error_message="Assertion failed: status_code expected 200, got 404"
        ),
        ExecutionResult(
            test_case_id="TC_004",
            status="error",
            duration=0.3,
            error_message="Connection timeout"
        ),
        ExecutionResult(
            test_case_id="TC_005",
            status="passed",
            duration=3.5,  # 慢测试
            error_message=None
        ),
    ]
    
    # 生成报告
    generator = ReportGenerator()
    report = generator.generate(results)
    
    print("\n📊 报告内容:")
    print(f"总用例: {report['summary']['total']}")
    print(f"通过: {report['summary']['passed']}")
    print(f"失败: {report['summary']['failed']}")
    print(f"错误: {report['summary']['error']}")
    print(f"通过率: {report['summary']['pass_rate']}")
    print(f"总耗时: {report['summary']['total_duration']}s")
    
    print(f"\n失败用例数: {len(report['failures'])}")
    print(f"错误用例数: {len(report['errors'])}")
    print(f"慢测试数: {len(report['slow_tests'])}")
    
    print("\n✅ 演示完成\n")


def demo_text_report():
    """演示2: 文本格式报告"""
    print("=" * 80)
    print("演示2: 文本格式报告")
    print("=" * 80)
    
    # 模拟执行结果
    results = [
        ExecutionResult("TC_001", "passed", 0.5, None),
        ExecutionResult("TC_002", "passed", 1.2, None),
        ExecutionResult("TC_003", "failed", 0.8, "Assertion failed: status_code expected 200, got 404"),
        ExecutionResult("TC_004", "error", 0.3, "Connection timeout"),
        ExecutionResult("TC_005", "passed", 3.5, None),
    ]
    
    # 生成文本报告
    generator = ReportGenerator()
    text_report = generator.generate_text_report(results)
    
    print("\n" + text_report)
    
    print("✅ 演示完成\n")


def demo_json_report():
    """演示3: JSON格式报告"""
    print("=" * 80)
    print("演示3: JSON格式报告")
    print("=" * 80)
    
    # 模拟执行结果
    results = [
        ExecutionResult("TC_001", "passed", 0.5, None),
        ExecutionResult("TC_002", "failed", 0.8, "Assertion failed"),
        ExecutionResult("TC_003", "passed", 2.5, None),
    ]
    
    # 生成JSON报告
    generator = ReportGenerator()
    json_report = generator.generate_json_report(results)
    
    print("\n📄 JSON报告:")
    print(json_report)
    
    print("\n✅ 演示完成\n")


def demo_html_report():
    """演示4: HTML格式报告"""
    print("=" * 80)
    print("演示4: HTML格式报告")
    print("=" * 80)
    
    # 模拟执行结果
    results = [
        ExecutionResult("TC_001", "passed", 0.5, None),
        ExecutionResult("TC_002", "passed", 1.2, None),
        ExecutionResult("TC_003", "failed", 0.8, "Assertion failed: status_code expected 200, got 404"),
        ExecutionResult("TC_004", "error", 0.3, "Connection timeout"),
        ExecutionResult("TC_005", "passed", 3.5, None),
        ExecutionResult("TC_006", "passed", 0.7, None),
        ExecutionResult("TC_007", "failed", 1.1, "Assertion failed: json_path data.id not found"),
        ExecutionResult("TC_008", "passed", 2.8, None),
    ]
    
    # 生成HTML报告
    generator = ReportGenerator()
    html_report = generator.generate_html_report(results)
    
    # 保存到文件
    output_path = Path("output/demo_report.html")
    output_path.parent.mkdir(exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_report)
    
    print(f"\n✅ HTML报告已保存到: {output_path}")
    print(f"   文件大小: {len(html_report)} 字节")
    print(f"   请在浏览器中打开查看")
    
    print("\n✅ 演示完成\n")


def demo_custom_config():
    """演示5: 自定义配置"""
    print("=" * 80)
    print("演示5: 自定义配置")
    print("=" * 80)
    
    # 模拟执行结果
    results = [
        ExecutionResult("TC_001", "passed", 0.5, None),
        ExecutionResult("TC_002", "passed", 1.5, None),  # 超过1秒
        ExecutionResult("TC_003", "passed", 2.5, None),  # 超过1秒
    ]
    
    # 自定义配置：慢测试阈值为1秒
    config = {
        'slow_threshold': 1.0,
        'include_response': True
    }
    
    generator = ReportGenerator(config)
    report = generator.generate(results)
    
    print(f"\n慢测试阈值: {generator.slow_threshold}s")
    print(f"慢测试数量: {len(report['slow_tests'])}")
    
    for slow in report['slow_tests']:
        print(f"  - {slow['test_case_id']}: {slow['duration']}s")
    
    print("\n✅ 演示完成\n")


def demo_save_reports():
    """演示6: 保存多种格式报告"""
    print("=" * 80)
    print("演示6: 保存多种格式报告")
    print("=" * 80)
    
    # 模拟执行结果
    results = [
        ExecutionResult("TC_001", "passed", 0.5, None),
        ExecutionResult("TC_002", "passed", 1.2, None),
        ExecutionResult("TC_003", "failed", 0.8, "Assertion failed"),
        ExecutionResult("TC_004", "error", 0.3, "Connection timeout"),
        ExecutionResult("TC_005", "passed", 3.5, None),
    ]
    
    generator = ReportGenerator()
    
    # 创建输出目录
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    
    # 保存JSON格式
    json_path = output_dir / "report.json"
    generator.save_report(results, str(json_path), format="json")
    print(f"✅ JSON报告已保存: {json_path}")
    
    # 保存文本格式
    text_path = output_dir / "report.txt"
    generator.save_report(results, str(text_path), format="text")
    print(f"✅ 文本报告已保存: {text_path}")
    
    # 保存HTML格式
    html_path = output_dir / "report.html"
    generator.save_report(results, str(html_path), format="html")
    print(f"✅ HTML报告已保存: {html_path}")
    
    print("\n✅ 演示完成\n")


def demo_with_retry():
    """演示7: 包含重试信息的报告"""
    print("=" * 80)
    print("演示7: 包含重试信息的报告")
    print("=" * 80)
    
    # 模拟执行结果（包含重试）
    results = [
        ExecutionResult("TC_001", "passed", 0.5, None, retry_count=0),
        ExecutionResult("TC_002", "passed", 1.2, None, retry_count=2),  # 重试2次后通过
        ExecutionResult("TC_003", "failed", 0.8, "Assertion failed", retry_count=3),  # 重试3次仍失败
        ExecutionResult("TC_004", "passed", 0.6, None, retry_count=1),  # 重试1次后通过
    ]
    
    generator = ReportGenerator()
    report = generator.generate(results)
    
    print(f"\n重试测试数量: {len(report['retried_tests'])}")
    
    for retry in report['retried_tests']:
        print(f"  - {retry['test_case_id']}: 重试{retry['retry_count']}次, 最终{retry['status']}")
    
    print("\n✅ 演示完成\n")


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("ReportGenerator 完整演示")
    print("=" * 80 + "\n")
    
    demo_basic_report()
    demo_text_report()
    demo_json_report()
    demo_html_report()
    demo_custom_config()
    demo_save_reports()
    demo_with_retry()
    
    print("=" * 80)
    print("🎉 所有演示完成！")
    print("=" * 80)
