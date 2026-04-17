"""
测试报告生成器
从ExecutionEngine的结果生成结构化报告
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
import json

# 🔧 使用 core 层的统一模型
from core import ExecutionResult, TestCaseStatus


class ReportGenerator:
    """测试报告生成器"""
    
    def __init__(self, config: Optional[Dict] = None):
        """
        初始化报告生成器
        
        Args:
            config: 配置项
                - slow_threshold: 慢测试阈值（秒），默认2.0
                - include_response: 是否包含响应详情，默认False
        """
        self.config = config or {}
        self.slow_threshold = self.config.get('slow_threshold', 2.0)
        self.include_response = self.config.get('include_response', False)
    
    def generate(self, results: List[Any]) -> Dict[str, Any]:
        """
        生成测试报告
        
        Args:
            results: ExecutionResult对象列表
        
        Returns:
            报告字典，包含summary、failures、slow_tests等
        """
        # 统计信息
        total = len(results)
        passed = sum(1 for r in results if r.status == TestCaseStatus.PASSED)
        failed = sum(1 for r in results if r.status == TestCaseStatus.FAILED)
        
        # 计算通过率
        pass_rate = f"{(passed/total)*100:.1f}%" if total > 0 else "0%"
        
        # 计算总耗时
        total_duration = sum(r.duration for r in results)
        avg_duration = total_duration / total if total > 0 else 0
        
        # 统计修复信息
        healing_summary = {
            "retry": 0,
            "regenerate_data": 0,
            "flaky": 0,
            "manual": 0,
            "total_healed": 0
        }
        
        for r in results:
            if r.healing_applied:
                level_value = r.healing_level.value if r.healing_level else ""
                if level_value == 'L1':
                    healing_summary['retry'] += 1
                    healing_summary['total_healed'] += 1
                elif level_value == 'L2':
                    healing_summary['regenerate_data'] += 1
                    healing_summary['total_healed'] += 1
                elif level_value == 'L3':
                    healing_summary['flaky'] += 1
                    healing_summary['total_healed'] += 1
                elif level_value == 'L4':
                    healing_summary['manual'] += 1
                    healing_summary['total_healed'] += 1
        
        # 构建报告
        report = {
            "summary": {
                "total": total,
                "passed": passed,
                "failed": failed,
                "pass_rate": pass_rate,
                "total_duration": round(total_duration, 2),
                "avg_duration": round(avg_duration, 2),
                "generated_at": datetime.now().isoformat()
            },
            "healing_summary": healing_summary,
            "failures": [],
            "slow_tests": [],
            "healed_cases": []
        }
        
        # 收集失败、慢测试、修复信息
        for r in results:
            # 失败用例
            if r.status == TestCaseStatus.FAILED:
                failure_info = {
                    "test_case_id": r.test_case_id,
                    "error": r.error,
                    "duration": round(r.duration, 2)
                }
                if self.include_response and r.response:
                    failure_info["response"] = r.response
                
                # 添加修复信息
                if r.healing_applied:
                    failure_info["healing"] = {
                        "level": r.healing_level.value if r.healing_level else None,
                        "details": r.healing_details
                    }
                
                report["failures"].append(failure_info)
            
            # 慢测试
            if r.duration > self.slow_threshold:
                report["slow_tests"].append({
                    "test_case_id": r.test_case_id,
                    "duration": round(r.duration, 2),
                    "status": r.status.value
                })
            
            # 修复过的用例
            if r.healing_applied:
                healed_info = {
                    "test_case_id": r.test_case_id,
                    "current_status": r.status.value,
                    "healing_level": r.healing_level.value if r.healing_level else None,
                    "healing_details": r.healing_details
                }
                report["healed_cases"].append(healed_info)
        
        return report
    
    def generate_text_report(self, results: List[Any]) -> str:
        """
        生成文本格式报告
        
        Args:
            results: ExecutionResult对象列表
        
        Returns:
            文本格式的报告
        """
        report = self.generate(results)
        
        lines = []
        lines.append("=" * 80)
        lines.append("测试执行报告")
        lines.append("=" * 80)
        lines.append("")
        
        # 摘要
        summary = report["summary"]
        lines.append("📊 测试摘要")
        lines.append("-" * 80)
        lines.append(f"总用例数: {summary['total']}")
        lines.append(f"✅ 通过: {summary['passed']}")
        lines.append(f"❌ 失败: {summary['failed']}")
        lines.append(f"通过率: {summary['pass_rate']}")
        lines.append(f"总耗时: {summary['total_duration']}s")
        lines.append(f"平均耗时: {summary['avg_duration']}s")
        lines.append(f"生成时间: {summary['generated_at']}")
        lines.append("")
        
        # 修复摘要
        healing = report["healing_summary"]
        if healing['total_healed'] > 0:
            lines.append("🔧 Self-Healing 修复摘要")
            lines.append("-" * 80)
            lines.append(f"总修复数: {healing['total_healed']}")
            if healing['retry'] > 0:
                lines.append(f"  L1-重试: {healing['retry']}个")
            if healing['regenerate_data'] > 0:
                lines.append(f"  L2-重建数据: {healing['regenerate_data']}个")
            if healing['flaky'] > 0:
                lines.append(f"  L3-容错: {healing['flaky']}个")
            if healing['manual'] > 0:
                lines.append(f"  L4-人工审查: {healing['manual']}个")
            lines.append("")
        
        # 失败用例
        if report["failures"]:
            lines.append("❌ 失败用例")
            lines.append("-" * 80)
            for f in report["failures"]:
                lines.append(f"  [{f['test_case_id']}] {f['error']}")
                lines.append(f"    耗时: {f['duration']}s")
            lines.append("")
        
        # 慢测试
        if report["slow_tests"]:
            lines.append(f"🐌 慢测试 (>{self.slow_threshold}s)")
            lines.append("-" * 80)
            for s in report["slow_tests"]:
                lines.append(f"  [{s['test_case_id']}] {s['duration']}s ({s['status']})")
            lines.append("")
        
        # 修复用例
        if report["healed_cases"]:
            lines.append("🔧 修复用例详情")
            lines.append("-" * 80)
            for h in report["healed_cases"]:
                lines.append(f"  [{h['test_case_id']}]")
                lines.append(f"    当前状态: {h['current_status']}")
                lines.append(f"    修复级别: {h['healing_level']}")
                lines.append(f"    修复详情: {h['healing_details']}")
            lines.append("")
        
        lines.append("=" * 80)
        
        return "\n".join(lines)
    
    def generate_json_report(self, results: List[Any]) -> str:
        """
        生成JSON格式报告
        
        Args:
            results: ExecutionResult对象列表
        
        Returns:
            JSON格式的报告字符串
        """
        report = self.generate(results)
        return json.dumps(report, ensure_ascii=False, indent=2)
    
    def generate_html_report(self, results: List[Any]) -> str:
        """
        生成HTML格式报告
        
        Args:
            results: ExecutionResult对象列表
        
        Returns:
            HTML格式的报告
        """
        report = self.generate(results)
        summary = report["summary"]
        
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>测试报告</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #333;
            border-bottom: 3px solid #4CAF50;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #555;
            margin-top: 30px;
            border-bottom: 2px solid #ddd;
            padding-bottom: 8px;
        }}
        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }}
        .stat-card {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
        }}
        .stat-card.passed {{
            background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
        }}
        .stat-card.failed {{
            background: linear-gradient(135deg, #eb3349 0%, #f45c43 100%);
        }}
        .stat-card.error {{
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        }}
        .stat-value {{
            font-size: 36px;
            font-weight: bold;
            margin: 10px 0;
        }}
        .stat-label {{
            font-size: 14px;
            opacity: 0.9;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 12px;
            text-align: left;
        }}
        th {{
            background-color: #4CAF50;
            color: white;
            font-weight: bold;
        }}
        tr:nth-child(even) {{
            background-color: #f9f9f9;
        }}
        tr:hover {{
            background-color: #f5f5f5;
        }}
        .status-passed {{
            color: #28a745;
            font-weight: bold;
        }}
        .status-failed {{
            color: #dc3545;
            font-weight: bold;
        }}
        .status-error {{
            color: #ffc107;
            font-weight: bold;
        }}
        .error-message {{
            color: #666;
            font-size: 0.9em;
            max-width: 400px;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }}
        .footer {{
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            text-align: center;
            color: #999;
            font-size: 0.9em;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🧪 测试执行报告</h1>
        
        <div class="summary">
            <div class="stat-card">
                <div class="stat-label">总用例数</div>
                <div class="stat-value">{summary['total']}</div>
            </div>
            <div class="stat-card passed">
                <div class="stat-label">✅ 通过</div>
                <div class="stat-value">{summary['passed']}</div>
            </div>
            <div class="stat-card failed">
                <div class="stat-label">❌ 失败</div>
                <div class="stat-value">{summary['failed']}</div>
            </div>
            <div class="stat-card error">
                <div class="stat-label">⚠️ 错误</div>
                <div class="stat-value">{summary['error']}</div>
            </div>
        </div>
        
        <div class="summary">
            <div class="stat-card">
                <div class="stat-label">通过率</div>
                <div class="stat-value">{summary['pass_rate']}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">总耗时</div>
                <div class="stat-value">{summary['total_duration']}s</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">平均耗时</div>
                <div class="stat-value">{summary['avg_duration']}s</div>
            </div>
        </div>
"""
        
        # 修复摘要
        healing = report["healing_summary"]
        if healing['total_healed'] > 0:
            html += f"""
        <h2>🔧 Self-Healing 修复摘要</h2>
        <div class="summary">
            <div class="stat-card">
                <div class="stat-label">总修复数</div>
                <div class="stat-value">{healing['total_healed']}</div>
            </div>
"""
            if healing['retry'] > 0:
                html += f"""
            <div class="stat-card">
                <div class="stat-label">L1-重试</div>
                <div class="stat-value">{healing['retry']}</div>
            </div>
"""
            if healing['regenerate_data'] > 0:
                html += f"""
            <div class="stat-card">
                <div class="stat-label">L2-重建数据</div>
                <div class="stat-value">{healing['regenerate_data']}</div>
            </div>
"""
            if healing['flaky'] > 0:
                html += f"""
            <div class="stat-card">
                <div class="stat-label">L3-容错</div>
                <div class="stat-value">{healing['flaky']}</div>
            </div>
"""
            if healing['manual'] > 0:
                html += f"""
            <div class="stat-card error">
                <div class="stat-label">L4-人工审查</div>
                <div class="stat-value">{healing['manual']}</div>
            </div>
"""
            html += """
        </div>
"""
        
        # 失败用例表格
        if report["failures"]:
            html += """
        <h2>❌ 失败用例</h2>
        <table>
            <tr>
                <th>用例ID</th>
                <th>错误信息</th>
                <th>耗时</th>
            </tr>
"""
            for f in report["failures"]:
                html += f"""
            <tr>
                <td>{f['test_case_id']}</td>
                <td class="error-message" title="{f['error']}">{f['error']}</td>
                <td>{f['duration']}s</td>
            </tr>
"""
            html += """
        </table>
"""
        
        # 慢测试表格
        if report["slow_tests"]:
            html += f"""
        <h2>🐌 慢测试 (>{self.slow_threshold}s)</h2>
        <table>
            <tr>
                <th>用例ID</th>
                <th>耗时</th>
                <th>状态</th>
            </tr>
"""
            for s in report["slow_tests"]:
                status_class = f"status-{s['status']}"
                html += f"""
            <tr>
                <td>{s['test_case_id']}</td>
                <td>{s['duration']}s</td>
                <td class="{status_class}">{s['status']}</td>
            </tr>
"""
            html += """
        </table>
"""
        
        # 修复用例表格
        if report["healed_cases"]:
            html += """
        <h2>🔧 修复用例详情</h2>
        <table>
            <tr>
                <th>用例ID</th>
                <th>当前状态</th>
                <th>修复级别</th>
                <th>修复详情</th>
            </tr>
"""
            for h in report["healed_cases"]:
                curr_status_class = f"status-{h['current_status']}" if h['current_status'] else ""
                html += f"""
            <tr>
                <td>{h['test_case_id']}</td>
                <td class="{curr_status_class}">{h['current_status']}</td>
                <td>{h['healing_level']}</td>
                <td class="error-message" title="{h['healing_details']}">{h['healing_details']}</td>
            </tr>
"""
            html += """
        </table>
"""
        
        html += f"""
        <div class="footer">
            生成时间: {summary['generated_at']}
        </div>
    </div>
</body>
</html>
"""
        
        return html
    
    def save_report(self, results: List[Any], output_path: str, format: str = "json"):
        """
        保存报告到文件
        
        Args:
            results: ExecutionResult对象列表
            output_path: 输出文件路径
            format: 报告格式 (json/text/html)
        """
        if format == "json":
            content = self.generate_json_report(results)
        elif format == "text":
            content = self.generate_text_report(results)
        elif format == "html":
            content = self.generate_html_report(results)
        else:
            raise ValueError(f"不支持的格式: {format}")
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
