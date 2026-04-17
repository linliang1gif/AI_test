"""
高级测试Pipeline（支持真实执行、Test Discovery、Self-Healing）
"""
import sys
import json
from pathlib import Path
from typing import List, Dict, Optional

from modules.swagger import SwaggerTestCaseGenerator, ApiSpecLoader
from modules.executor import ExecutionEngine
from modules.data import TestDataManager
from modules.discovery import TestDiscoveryAgent
from modules.report import ReportGenerator
from modules.healing import HealingEngine


def run_advanced_pipeline(
    swagger_file: str,
    base_url: str = "https://api.example.com",
    output_dir: str = "output",
    old_swagger: Optional[str] = None,
    enable_discovery: bool = False,
    real_execution: bool = False,
    auth_token: Optional[str] = None
):
    """
    运行高级测试Pipeline
    
    Args:
        swagger_file: Swagger文件路径
        base_url: API基础URL
        output_dir: 输出目录
        old_swagger: 旧版Swagger文件（用于Test Discovery）
        enable_discovery: 是否启用Test Discovery
        real_execution: 是否真实执行（否则模拟）
        auth_token: 认证Token
    """
    print("=" * 80)
    print("🚀 开始执行高级测试Pipeline")
    print("=" * 80)
    
    all_test_cases = []
    discovered_points = []
    
    # ========== 可选: Test Discovery ==========
    if enable_discovery and old_swagger:
        print("\n[0/6] 🔍 Test Discovery - 发现高风险测试点...")
        try:
            agent = TestDiscoveryAgent()
            discovered_points = agent.discover_from_swagger_changes(
                old_swagger,
                swagger_file
            )
            
            print(f"  ✅ 发现了 {len(discovered_points)} 个测试点")
            
            # 显示高风险测试点
            critical_points = [tp for tp in discovered_points if tp.risk_level == "critical"]
            if critical_points:
                print(f"  🔴 严重风险测试点: {len(critical_points)}")
                for tp in critical_points[:3]:
                    print(f"     - {tp.test_point}")
        
        except Exception as e:
            print(f"  ⚠️  Test Discovery失败: {e}")
    
    # ========== 步骤1: 解析Swagger ==========
    print("\n[1/6] 📄 解析Swagger...")
    try:
        loader = ApiSpecLoader(swagger_file)
        spec_info = loader.get_spec_info()
        apis = loader.get_all_apis()
        
        print(f"  ✅ Swagger解析成功")
        print(f"     标题: {spec_info['title']}")
        print(f"     版本: {spec_info['api_version']}")
        print(f"     API数量: {len(apis)}")
    
    except Exception as e:
        print(f"  ❌ Swagger解析失败: {e}")
        return None
    
    # ========== 步骤2: 生成测试用例 ==========
    print(f"\n[2/6] 🔧 生成测试用例...")
    try:
        generator = SwaggerTestCaseGenerator(swagger_file)
        test_cases = generator.generate_all_testcases()
        
        stats = generator.get_statistics(test_cases)
        
        print(f"  ✅ 测试用例生成成功")
        print(f"     总用例数: {stats['total']}")
        print(f"     覆盖API数: {stats['apis_covered']}")
        
        all_test_cases.extend(test_cases)
    
    except Exception as e:
        print(f"  ❌ 测试用例生成失败: {e}")
        return None
    
    # ========== 步骤3: 配置执行引擎 ==========
    print(f"\n[3/6] ⚙️  配置执行引擎...")
    try:
        config = {
            "base_url": base_url,
            "timeout": 30,
            "retry_on_failure": True,
            "max_retries": 2,
            "retry_delay": 1
        }
        
        # 添加认证配置
        if auth_token:
            config["auth_config"] = {
                "type": "bearer",
                "token": auth_token
            }
        
        engine = ExecutionEngine(config)
        
        print(f"  ✅ 执行引擎配置完成")
        print(f"     基础URL: {config['base_url']}")
        print(f"     超时时间: {config['timeout']}s")
        print(f"     重试次数: {config['max_retries']}")
        if auth_token:
            print(f"     认证: Bearer Token")
    
    except Exception as e:
        print(f"  ❌ 执行引擎配置失败: {e}")
        return None
    
    # ========== 步骤4: 执行测试 ==========
    print(f"\n[4/7] 🧪 执行测试...")
    print(f"  ⏳ 正在执行 {len(all_test_cases)} 个测试用例...")
    
    try:
        if real_execution:
            print(f"  🔴 真实执行模式")
            results = engine.execute(all_test_cases, parallel=False)
        else:
            print(f"  🟡 模拟执行模式")
            results = _simulate_execution(all_test_cases)
        
        print(f"  ✅ 测试执行完成")
    
    except Exception as e:
        print(f"  ❌ 测试执行失败: {e}")
        import traceback
        traceback.print_exc()
        return None
    
    # ========== 步骤5: Self-Healing 自动修复 ==========
    print(f"\n[5/7] 🔧 Self-Healing 自动修复...")
    
    try:
        healing_engine = HealingEngine()
        healed_results = healing_engine.heal(results)
        
        # 获取修复报告
        healing_report = healing_engine.get_healing_report()
        
        print(f"  ✅ 修复完成")
        print(f"     总用例: {healing_report['total_cases']}")
        print(f"     修复用例: {healing_report['healed_cases']}")
        print(f"     修复率: {healing_report['healing_rate']}")
        
        # 显示修复统计
        if healing_report['healed_cases'] > 0:
            print(f"\n  修复统计:")
            for level, info in healing_report['by_level'].items():
                if info['count'] > 0:
                    print(f"     {level}: {info['count']}个 - {info['description']}")
        
        # 显示需要人工审查的用例
        manual_cases = healing_engine.get_manual_review_cases(healed_results)
        if manual_cases:
            print(f"\n  ⚠️  需要人工审查: {len(manual_cases)}个用例")
    
    except Exception as e:
        print(f"  ⚠️  修复失败: {e}")
        healed_results = results  # 使用原始结果
        healing_report = {'total_cases': 0, 'healed_cases': 0, 'healing_rate': '0%', 'by_level': {}}
    
    # ========== 步骤6: 生成报告 ==========
    print(f"\n[6/7] 📊 生成报告...")
    
    # 使用ReportGenerator生成报告
    report_generator = ReportGenerator()
    report = report_generator.generate(healed_results)
    
    # 显示报告摘要
    summary = report["summary"]
    
    print(f"\n  {'='*60}")
    print(f"  📈 测试报告摘要")
    print(f"  {'='*60}")
    print(f"  总用例: {summary['total']}")
    print(f"  ✅ 通过: {summary['passed']}")
    print(f"  ❌ 失败: {summary['failed']}")
    print(f"  ⚠️  错误: {summary['error']}")
    print(f"  通过率: {summary['pass_rate']}")
    print(f"  ⏱️  总耗时: {summary['total_duration']}s")
    print(f"  ⏱️  平均耗时: {summary['avg_duration']}s")
    print(f"  {'='*60}")
    
    # 显示失败用例
    if report["failures"]:
        print(f"\n  ❌ 失败用例:")
        for f in report["failures"][:5]:  # 只显示前5个
            print(f"     - {f['test_case_id']} | {f['error'][:80]}")
        if len(report["failures"]) > 5:
            print(f"     ... 还有 {len(report['failures']) - 5} 个失败用例")
    
    # 显示错误用例
    if report["errors"]:
        print(f"\n  ⚠️  错误用例:")
        for e in report["errors"][:5]:  # 只显示前5个
            print(f"     - {e['test_case_id']} | {e['error'][:80]}")
        if len(report["errors"]) > 5:
            print(f"     ... 还有 {len(report['errors']) - 5} 个错误用例")
    
    # 显示慢测试
    if report["slow_tests"]:
        print(f"\n  🐌 慢测试 (>2.0s):")
        for s in report["slow_tests"][:5]:  # 只显示前5个
            print(f"     - {s['test_case_id']} | {s['duration']}s ({s['status']})")
        if len(report["slow_tests"]) > 5:
            print(f"     ... 还有 {len(report['slow_tests']) - 5} 个慢测试")
    
    # 显示重试测试
    if report["retried_tests"]:
        print(f"\n  🔄 重试测试:")
        for r in report["retried_tests"][:5]:  # 只显示前5个
            print(f"     - {r['test_case_id']} | 重试{r['retry_count']}次 ({r['status']})")
        if len(report["retried_tests"]) > 5:
            print(f"     ... 还有 {len(report['retried_tests']) - 5} 个重试测试")
    
    # ========== 步骤7: 保存结果 ==========
    print(f"\n[7/7] 💾 保存结果...")
    try:
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        # 保存测试用例
        testcases_file = output_path / "testcases.json"
        with open(testcases_file, 'w', encoding='utf-8') as f:
            json.dump(generator.export_to_json(all_test_cases), f, ensure_ascii=False, indent=2)
        
        # 使用ReportGenerator生成报告
        report_generator = ReportGenerator()
        
        # 保存JSON报告
        report_json_file = output_path / "report.json"
        report_generator.save_report(healed_results, str(report_json_file), format="json")
        
        # 保存文本报告
        report_txt_file = output_path / "report.txt"
        report_generator.save_report(healed_results, str(report_txt_file), format="text")
        
        # 保存HTML报告
        report_html_file = output_path / "report.html"
        report_generator.save_report(healed_results, str(report_html_file), format="html")
        
        # 保存Test Discovery结果
        if discovered_points:
            discovery_file = output_path / "discovered_points.json"
            agent = TestDiscoveryAgent()
            agent.discovered_points = discovered_points
            with open(discovery_file, 'w', encoding='utf-8') as f:
                json.dump(agent.export_to_json(), f, ensure_ascii=False, indent=2)
        
        # 保存Healing报告
        healing_report_file = output_path / "healing_report.json"
        with open(healing_report_file, 'w', encoding='utf-8') as f:
            json.dump(healing_report, f, ensure_ascii=False, indent=2)
        
        print(f"  ✅ 结果已保存")
        print(f"     测试用例: {testcases_file}")
        print(f"     JSON报告: {report_json_file}")
        print(f"     文本报告: {report_txt_file}")
        print(f"     HTML报告: {report_html_file}")
        print(f"     修复报告: {healing_report_file}")
        if discovered_points:
            print(f"     发现的测试点: {discovery_file}")
    
    except Exception as e:
        print(f"  ⚠️  保存结果失败: {e}")
    
    # ========== 完成 ==========
    print(f"\n{'='*80}")
    pass_rate_value = float(report['summary']['pass_rate'].rstrip('%'))
    if pass_rate_value >= 80:
        print(f"✅ Pipeline执行成功！通过率: {report['summary']['pass_rate']}")
    else:
        print(f"⚠️  Pipeline执行完成，但通过率较低: {report['summary']['pass_rate']}")
    
    # 显示修复信息
    if healing_report['healed_cases'] > 0:
        print(f"🔧 Self-Healing: 修复了 {healing_report['healed_cases']} 个用例 ({healing_report['healing_rate']})")
    
    print(f"{'='*80}\n")
    
    return healed_results


def _simulate_execution(test_cases):
    """模拟执行"""
    from modules.executor.execution_engine import ExecutionResult
    import random
    
    results = []
    for tc in test_cases:
        rand = random.random()
        
        if rand < 0.80:
            status = "passed"
            error_message = None
        elif rand < 0.95:
            status = "failed"
            error_message = "Assertion failed: status_code expected 200, got 404"
        else:
            status = "error"
            error_message = "Connection timeout"
        
        result = ExecutionResult(
            test_case_id=tc.id,
            status=status,
            duration=random.uniform(0.1, 2.0),
            error_message=error_message,
            retry_count=0
        )
        
        results.append(result)
    
    return results


def _classify_error(error_message: str) -> str:
    """分类错误类型"""
    if not error_message:
        return "未知错误"
    
    error_lower = error_message.lower()
    
    if "timeout" in error_lower:
        return "超时错误"
    elif "connection" in error_lower:
        return "连接错误"
    elif "404" in error_lower:
        return "接口不存在"
    elif "500" in error_lower:
        return "服务器错误"
    elif "assertion" in error_lower:
        return "断言失败"
    else:
        return "其他错误"


def _generate_html_report(output_file: Path, data: Dict):
    """生成HTML报告"""
    html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>测试报告</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        h1 {{ color: #333; }}
        .summary {{ background: #f5f5f5; padding: 20px; border-radius: 5px; }}
        .stat {{ display: inline-block; margin: 10px 20px; }}
        .passed {{ color: #28a745; }}
        .failed {{ color: #dc3545; }}
        .error {{ color: #ffc107; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #4CAF50; color: white; }}
    </style>
</head>
<body>
    <h1>🧪 测试执行报告</h1>
    
    <div class="summary">
        <h2>📊 统计信息</h2>
        <div class="stat">总用例: <strong>{data['total']}</strong></div>
        <div class="stat passed">✅ 通过: <strong>{data['passed']}</strong></div>
        <div class="stat failed">❌ 失败: <strong>{data['failed']}</strong></div>
        <div class="stat error">⚠️ 错误: <strong>{data['error']}</strong></div>
        <div class="stat">通过率: <strong>{data['pass_rate']:.1f}%</strong></div>
        <div class="stat">总耗时: <strong>{data['total_duration']:.2f}s</strong></div>
    </div>
    
    <h2>📋 测试结果</h2>
    <table>
        <tr>
            <th>用例ID</th>
            <th>状态</th>
            <th>耗时</th>
            <th>错误信息</th>
        </tr>
"""
    
    for r in data['results']:
        status_class = r.status
        status_icon = "✅" if r.status == "passed" else "❌" if r.status == "failed" else "⚠️"
        error_msg = r.error_message or "-"
        
        html += f"""
        <tr>
            <td>{r.test_case_id}</td>
            <td class="{status_class}">{status_icon} {r.status}</td>
            <td>{r.duration:.2f}s</td>
            <td>{error_msg[:100]}</td>
        </tr>
"""
    
    html += """
    </table>
</body>
</html>
"""
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='运行高级测试Pipeline')
    parser.add_argument('swagger_file', help='Swagger文件路径')
    parser.add_argument('--base-url', default='https://api.example.com', help='API基础URL')
    parser.add_argument('--output', default='output', help='输出目录')
    parser.add_argument('--old-swagger', help='旧版Swagger文件（用于Test Discovery）')
    parser.add_argument('--discovery', action='store_true', help='启用Test Discovery')
    parser.add_argument('--real', action='store_true', help='真实执行（不模拟）')
    parser.add_argument('--token', help='认证Token')
    
    args = parser.parse_args()
    
    # 检查文件
    if not Path(args.swagger_file).exists():
        print(f"❌ 错误: Swagger文件不存在: {args.swagger_file}")
        sys.exit(1)
    
    # 运行Pipeline
    results = run_advanced_pipeline(
        swagger_file=args.swagger_file,
        base_url=args.base_url,
        output_dir=args.output,
        old_swagger=args.old_swagger,
        enable_discovery=args.discovery,
        real_execution=args.real,
        auth_token=args.token
    )
    
    if results is None:
        sys.exit(1)
    
    # 根据通过率决定退出码
    passed = sum(1 for r in results if r.status == "passed")
    pass_rate = (passed / len(results) * 100) if results else 0
    
    sys.exit(0 if pass_rate >= 80 else 1)


if __name__ == "__main__":
    if len(sys.argv) == 1:
        print("💡 使用示例Swagger文件运行高级Pipeline\n")
        results = run_advanced_pipeline(
            swagger_file="examples/sample_swagger.json",
            base_url="https://jsonplaceholder.typicode.com",
            output_dir="output",
            old_swagger="examples/old_swagger.json",
            enable_discovery=True,
            real_execution=False
        )
    else:
        main()
