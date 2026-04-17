"""
ReportGenerator验证脚本
验证报告生成器的功能
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from modules.report import ReportGenerator
from modules.executor.execution_engine import ExecutionResult


def verify_basic_generation():
    """验证1: 基本报告生成"""
    print("=" * 80)
    print("验证1: 基本报告生成")
    print("=" * 80)
    
    results = [
        ExecutionResult("TC_001", "passed", 0.5, None),
        ExecutionResult("TC_002", "passed", 1.2, None),
        ExecutionResult("TC_003", "failed", 0.8, "Assertion failed"),
        ExecutionResult("TC_004", "error", 0.3, "Connection timeout"),
        ExecutionResult("TC_005", "passed", 3.5, None),
    ]
    
    generator = ReportGenerator()
    report = generator.generate(results)
    
    # 验证摘要
    assert report['summary']['total'] == 5, "总数应为5"
    assert report['summary']['passed'] == 3, "通过数应为3"
    assert report['summary']['failed'] == 1, "失败数应为1"
    assert report['summary']['error'] == 1, "错误数应为1"
    assert report['summary']['pass_rate'] == "60.0%", "通过率应为60.0%"
    
    # 验证失败列表
    assert len(report['failures']) == 1, "应有1个失败用例"
    assert report['failures'][0]['test_case_id'] == "TC_003"
    
    # 验证错误列表
    assert len(report['errors']) == 1, "应有1个错误用例"
    assert report['errors'][0]['test_case_id'] == "TC_004"
    
    # 验证慢测试
    assert len(report['slow_tests']) == 1, "应有1个慢测试"
    assert report['slow_tests'][0]['test_case_id'] == "TC_005"
    
    print("✅ 基本报告生成正常")
    print(f"   总数: {report['summary']['total']}")
    print(f"   通过: {report['summary']['passed']}")
    print(f"   失败: {report['summary']['failed']}")
    print(f"   错误: {report['summary']['error']}")
    print(f"   通过率: {report['summary']['pass_rate']}")
    print()
    
    return True


def verify_text_format():
    """验证2: 文本格式生成"""
    print("=" * 80)
    print("验证2: 文本格式生成")
    print("=" * 80)
    
    results = [
        ExecutionResult("TC_001", "passed", 0.5, None),
        ExecutionResult("TC_002", "failed", 0.8, "Assertion failed"),
    ]
    
    generator = ReportGenerator()
    text_report = generator.generate_text_report(results)
    
    # 验证文本内容
    assert "测试执行报告" in text_report, "应包含标题"
    assert "测试摘要" in text_report, "应包含摘要"
    assert "总用例数: 2" in text_report, "应包含总数"
    assert "通过: 1" in text_report, "应包含通过数"
    assert "失败: 1" in text_report, "应包含失败数"
    assert "TC_002" in text_report, "应包含失败用例ID"
    
    print("✅ 文本格式生成正常")
    print(f"   文本长度: {len(text_report)} 字符")
    print()
    
    return True


def verify_json_format():
    """验证3: JSON格式生成"""
    print("=" * 80)
    print("验证3: JSON格式生成")
    print("=" * 80)
    
    results = [
        ExecutionResult("TC_001", "passed", 0.5, None),
        ExecutionResult("TC_002", "failed", 0.8, "Assertion failed"),
    ]
    
    generator = ReportGenerator()
    json_report = generator.generate_json_report(results)
    
    # 验证JSON格式
    import json
    report_dict = json.loads(json_report)
    
    assert 'summary' in report_dict, "应包含summary"
    assert 'failures' in report_dict, "应包含failures"
    assert report_dict['summary']['total'] == 2, "总数应为2"
    
    print("✅ JSON格式生成正常")
    print(f"   JSON长度: {len(json_report)} 字符")
    print(f"   可正确解析为字典")
    print()
    
    return True


def verify_html_format():
    """验证4: HTML格式生成"""
    print("=" * 80)
    print("验证4: HTML格式生成")
    print("=" * 80)
    
    results = [
        ExecutionResult("TC_001", "passed", 0.5, None),
        ExecutionResult("TC_002", "failed", 0.8, "Assertion failed"),
        ExecutionResult("TC_003", "passed", 3.5, None),
    ]
    
    generator = ReportGenerator()
    html_report = generator.generate_html_report(results)
    
    # 验证HTML内容
    assert "<!DOCTYPE html>" in html_report, "应包含HTML声明"
    assert "<html>" in html_report, "应包含html标签"
    assert "测试执行报告" in html_report, "应包含标题"
    assert "TC_002" in html_report, "应包含失败用例"
    assert "<table>" in html_report, "应包含表格"
    
    print("✅ HTML格式生成正常")
    print(f"   HTML长度: {len(html_report)} 字符")
    print(f"   包含完整HTML结构")
    print()
    
    return True


def verify_custom_config():
    """验证5: 自定义配置"""
    print("=" * 80)
    print("验证5: 自定义配置")
    print("=" * 80)
    
    results = [
        ExecutionResult("TC_001", "passed", 0.5, None),
        ExecutionResult("TC_002", "passed", 1.5, None),
        ExecutionResult("TC_003", "passed", 2.5, None),
    ]
    
    # 默认配置（阈值2.0秒）
    generator1 = ReportGenerator()
    report1 = generator1.generate(results)
    
    # 自定义配置（阈值1.0秒）
    generator2 = ReportGenerator({'slow_threshold': 1.0})
    report2 = generator2.generate(results)
    
    assert len(report1['slow_tests']) == 1, "默认配置应有1个慢测试"
    assert len(report2['slow_tests']) == 2, "自定义配置应有2个慢测试"
    
    print("✅ 自定义配置正常")
    print(f"   默认阈值(2.0s): {len(report1['slow_tests'])}个慢测试")
    print(f"   自定义阈值(1.0s): {len(report2['slow_tests'])}个慢测试")
    print()
    
    return True


def verify_save_report():
    """验证6: 保存报告"""
    print("=" * 80)
    print("验证6: 保存报告")
    print("=" * 80)
    
    results = [
        ExecutionResult("TC_001", "passed", 0.5, None),
        ExecutionResult("TC_002", "failed", 0.8, "Assertion failed"),
    ]
    
    generator = ReportGenerator()
    
    # 创建输出目录
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    
    # 保存JSON
    json_path = output_dir / "test_report.json"
    generator.save_report(results, str(json_path), format="json")
    assert json_path.exists(), "JSON文件应存在"
    
    # 保存文本
    text_path = output_dir / "test_report.txt"
    generator.save_report(results, str(text_path), format="text")
    assert text_path.exists(), "文本文件应存在"
    
    # 保存HTML
    html_path = output_dir / "test_report.html"
    generator.save_report(results, str(html_path), format="html")
    assert html_path.exists(), "HTML文件应存在"
    
    print("✅ 保存报告正常")
    print(f"   JSON: {json_path} ({json_path.stat().st_size} 字节)")
    print(f"   文本: {text_path} ({text_path.stat().st_size} 字节)")
    print(f"   HTML: {html_path} ({html_path.stat().st_size} 字节)")
    print()
    
    return True


def verify_retry_info():
    """验证7: 重试信息"""
    print("=" * 80)
    print("验证7: 重试信息")
    print("=" * 80)
    
    results = [
        ExecutionResult("TC_001", "passed", 0.5, None, retry_count=0),
        ExecutionResult("TC_002", "passed", 1.2, None, retry_count=2),
        ExecutionResult("TC_003", "failed", 0.8, "Assertion failed", retry_count=3),
    ]
    
    generator = ReportGenerator()
    report = generator.generate(results)
    
    assert len(report['retried_tests']) == 2, "应有2个重试测试"
    assert report['retried_tests'][0]['retry_count'] == 2
    assert report['retried_tests'][1]['retry_count'] == 3
    
    print("✅ 重试信息正常")
    print(f"   重试测试数: {len(report['retried_tests'])}")
    for r in report['retried_tests']:
        print(f"   - {r['test_case_id']}: 重试{r['retry_count']}次")
    print()
    
    return True


def main():
    """运行所有验证"""
    print("\n" + "=" * 80)
    print("🚀 开始验证ReportGenerator")
    print("=" * 80 + "\n")
    
    results = []
    
    try:
        results.append(("基本生成", verify_basic_generation()))
    except Exception as e:
        print(f"❌ 基本生成验证失败: {e}\n")
        results.append(("基本生成", False))
    
    try:
        results.append(("文本格式", verify_text_format()))
    except Exception as e:
        print(f"❌ 文本格式验证失败: {e}\n")
        results.append(("文本格式", False))
    
    try:
        results.append(("JSON格式", verify_json_format()))
    except Exception as e:
        print(f"❌ JSON格式验证失败: {e}\n")
        results.append(("JSON格式", False))
    
    try:
        results.append(("HTML格式", verify_html_format()))
    except Exception as e:
        print(f"❌ HTML格式验证失败: {e}\n")
        results.append(("HTML格式", False))
    
    try:
        results.append(("自定义配置", verify_custom_config()))
    except Exception as e:
        print(f"❌ 自定义配置验证失败: {e}\n")
        results.append(("自定义配置", False))
    
    try:
        results.append(("保存报告", verify_save_report()))
    except Exception as e:
        print(f"❌ 保存报告验证失败: {e}\n")
        results.append(("保存报告", False))
    
    try:
        results.append(("重试信息", verify_retry_info()))
    except Exception as e:
        print(f"❌ 重试信息验证失败: {e}\n")
        results.append(("重试信息", False))
    
    # 汇总结果
    print("=" * 80)
    print("验证结果汇总")
    print("=" * 80)
    
    for name, passed in results:
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"{status} - {name}")
    
    total = len(results)
    passed_count = sum(1 for _, p in results if p)
    failed_count = total - passed_count
    pass_rate = (passed_count / total * 100) if total > 0 else 0
    
    print(f"\n总计: {total}, 通过: {passed_count}, 失败: {failed_count}")
    print(f"通过率: {pass_rate:.1f}%")
    
    if passed_count == total:
        print("\n🎉 所有验证通过！ReportGenerator工作正常！")
        return 0
    else:
        print(f"\n⚠️  有 {failed_count} 个验证失败")
        return 1


if __name__ == "__main__":
    sys.exit(main())
