"""
集成报告系统
整合结果分析、趋势分析和失败分析,生成综合报告
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
import json
import os
from core import ExecutionResult
from .result_analyzer import ResultAnalyzer
from .trend_analyzer import TrendAnalyzer
from .failure_analyzer import FailureAnalyzer
from modules.report.report_generator import ReportGenerator


class IntegratedReportSystem:
    """集成报告系统"""
    
    def __init__(self, config: Optional[Dict] = None):
        """
        初始化集成报告系统
        
        Args:
            config: 配置项
        """
        self.config = config or {}
        self.result_analyzer = ResultAnalyzer()
        self.trend_analyzer = TrendAnalyzer(
            storage_path=self.config.get('history_path', 'test_history')
        )
        self.failure_analyzer = FailureAnalyzer()
        self.report_generator = ReportGenerator(config)
    
    def generate_comprehensive_report(self, 
                                     execution_id: str,
                                     results: List[ExecutionResult],
                                     metadata: Optional[Dict] = None) -> Dict[str, Any]:
        """
        生成综合报告
        
        Args:
            execution_id: 执行ID
            results: 测试结果列表
            metadata: 元数据
            
        Returns:
            综合报告字典
        """
        # 保存执行记录（用于趋势分析）
        self.trend_analyzer.save_execution_record(execution_id, results, metadata)
        
        # 生成各类分析
        result_analysis = self.result_analyzer.analyze(results)
        failure_analysis = self.failure_analyzer.analyze_failures(results)
        trend_analysis = self.trend_analyzer.analyze_trend(days=7)
        basic_report = self.report_generator.generate(results)
        
        # 整合报告
        comprehensive_report = {
            'execution_id': execution_id,
            'timestamp': datetime.now().isoformat(),
            'metadata': metadata or {},
            'summary': basic_report['summary'],
            'result_analysis': result_analysis,
            'failure_analysis': failure_analysis,
            'trend_analysis': trend_analysis,
            'healing_summary': basic_report['healing_summary'],
            'recommendations': self._merge_recommendations(
                result_analysis.get('recommendations', []),
                failure_analysis.get('priority_fixes', [])
            )
        }
        
        return comprehensive_report
    
    def _merge_recommendations(self, 
                              result_recommendations: List[Dict],
                              failure_fixes: List[Dict]) -> List[Dict[str, Any]]:
        """合并优化建议"""
        recommendations = []
        
        # 添加结果分析的建议
        for rec in result_recommendations:
            recommendations.append({
                'source': 'result_analysis',
                'type': rec['type'],
                'severity': rec['severity'],
                'message': rec['message']
            })
        
        # 添加失败分析的建议
        for fix in failure_fixes:
            recommendations.append({
                'source': 'failure_analysis',
                'type': 'failure_fix',
                'severity': 'high' if fix['failure_count'] > 3 else 'medium',
                'category': fix['category'],
                'message': f"{fix['category']}: {fix['recommended_action']}",
                'details': fix
            })
        
        # 按严重程度排序
        severity_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
        recommendations.sort(key=lambda x: severity_order.get(x['severity'], 4))
        
        return recommendations
    
    def generate_html_report(self, 
                            execution_id: str,
                            results: List[ExecutionResult],
                            metadata: Optional[Dict] = None,
                            output_path: Optional[str] = None) -> str:
        """
        生成HTML综合报告
        
        Args:
            execution_id: 执行ID
            results: 测试结果列表
            metadata: 元数据
            output_path: 输出路径（可选）
            
        Returns:
            HTML内容
        """
        report = self.generate_comprehensive_report(execution_id, results, metadata)
        
        html = self._generate_html_content(report)
        
        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html)
        
        return html
    
    def _generate_html_content(self, report: Dict[str, Any]) -> str:
        """生成HTML内容"""
        summary = report['summary']
        result_analysis = report['result_analysis']
        failure_analysis = report['failure_analysis']
        trend_analysis = report['trend_analysis']
        
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>综合测试报告 - {report['execution_id']}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}
        .header h1 {{ font-size: 32px; margin-bottom: 10px; }}
        .header .meta {{ opacity: 0.9; font-size: 14px; }}
        .content {{ padding: 30px; }}
        .section {{
            margin-bottom: 40px;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 8px;
        }}
        .section h2 {{
            color: #333;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 3px solid #667eea;
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }}
        .stat-card {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            text-align: center;
        }}
        .stat-card.success {{ border-left: 4px solid #28a745; }}
        .stat-card.danger {{ border-left: 4px solid #dc3545; }}
        .stat-card.warning {{ border-left: 4px solid #ffc107; }}
        .stat-card.info {{ border-left: 4px solid #17a2b8; }}
        .stat-value {{
            font-size: 36px;
            font-weight: bold;
            margin: 10px 0;
        }}
        .stat-label {{
            color: #666;
            font-size: 14px;
        }}
        .recommendation {{
            padding: 15px;
            margin: 10px 0;
            border-radius: 6px;
            border-left: 4px solid;
        }}
        .recommendation.critical {{ background: #fff5f5; border-color: #dc3545; }}
        .recommendation.high {{ background: #fff8e1; border-color: #ff9800; }}
        .recommendation.medium {{ background: #e3f2fd; border-color: #2196f3; }}
        .recommendation.low {{ background: #f1f8e9; border-color: #8bc34a; }}
        .chart-container {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            background: white;
            border-radius: 8px;
            overflow: hidden;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background: #667eea;
            color: white;
            font-weight: 600;
        }}
        tr:hover {{ background: #f5f5f5; }}
        .badge {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: 600;
        }}
        .badge.success {{ background: #d4edda; color: #155724; }}
        .badge.danger {{ background: #f8d7da; color: #721c24; }}
        .badge.warning {{ background: #fff3cd; color: #856404; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🧪 综合测试报告</h1>
            <div class="meta">
                <div>执行ID: {report['execution_id']}</div>
                <div>生成时间: {report['timestamp']}</div>
            </div>
        </div>
        
        <div class="content">
            <!-- 执行摘要 -->
            <div class="section">
                <h2>📊 执行摘要</h2>
                <div class="stats-grid">
                    <div class="stat-card info">
                        <div class="stat-label">总用例数</div>
                        <div class="stat-value">{summary['total']}</div>
                    </div>
                    <div class="stat-card success">
                        <div class="stat-label">✅ 通过</div>
                        <div class="stat-value">{summary['passed']}</div>
                    </div>
                    <div class="stat-card danger">
                        <div class="stat-label">❌ 失败</div>
                        <div class="stat-value">{summary['failed']}</div>
                    </div>
                    <div class="stat-card warning">
                        <div class="stat-label">通过率</div>
                        <div class="stat-value">{summary['pass_rate']}</div>
                    </div>
                    <div class="stat-card info">
                        <div class="stat-label">总耗时</div>
                        <div class="stat-value">{summary['total_duration']}s</div>
                    </div>
                    <div class="stat-card info">
                        <div class="stat-label">平均耗时</div>
                        <div class="stat-value">{summary['avg_duration']}s</div>
                    </div>
                </div>
            </div>
            
            <!-- 失败分析 -->
"""
        
        if failure_analysis['total_failures'] > 0:
            html += f"""
            <div class="section">
                <h2>❌ 失败分析</h2>
                <div class="stats-grid">
                    <div class="stat-card danger">
                        <div class="stat-label">总失败数</div>
                        <div class="stat-value">{failure_analysis['total_failures']}</div>
                    </div>
"""
            
            for cause in failure_analysis['root_causes'][:3]:
                html += f"""
                    <div class="stat-card warning">
                        <div class="stat-label">{cause['category']}</div>
                        <div class="stat-value">{cause['failure_count']}</div>
                        <div class="stat-label">{cause['percentage']}%</div>
                    </div>
"""
            
            html += """
                </div>
            </div>
"""
        
        # 优化建议
        if report['recommendations']:
            html += """
            <div class="section">
                <h2>💡 优化建议</h2>
"""
            for rec in report['recommendations'][:10]:
                severity_class = rec.get('severity', 'medium')
                html += f"""
                <div class="recommendation {severity_class}">
                    <strong>[{severity_class.upper()}]</strong> {rec['message']}
                </div>
"""
            html += """
            </div>
"""
        
        # 趋势分析
        if trend_analysis['total_executions'] > 0:
            html += f"""
            <div class="section">
                <h2>📈 趋势分析 ({trend_analysis['period']})</h2>
                <div class="stats-grid">
                    <div class="stat-card info">
                        <div class="stat-label">总执行次数</div>
                        <div class="stat-value">{trend_analysis['total_executions']}</div>
                    </div>
"""
            
            if 'summary' in trend_analysis and trend_analysis['summary']:
                ts = trend_analysis['summary']
                html += f"""
                    <div class="stat-card success">
                        <div class="stat-label">平均通过率</div>
                        <div class="stat-value">{ts['avg_pass_rate']}%</div>
                    </div>
                    <div class="stat-card info">
                        <div class="stat-label">总测试数</div>
                        <div class="stat-value">{ts['total_tests']}</div>
                    </div>
"""
            
            html += """
                </div>
"""
            
            if trend_analysis.get('insights'):
                html += "<h3>💡 趋势洞察</h3>"
                for insight in trend_analysis['insights']:
                    html += f"<div class='recommendation medium'>{insight['message']}</div>"
            
            html += """
            </div>
"""
        
        html += """
        </div>
    </div>
</body>
</html>
"""
        
        return html
    
    def save_report(self, 
                   execution_id: str,
                   results: List[ExecutionResult],
                   metadata: Optional[Dict] = None,
                   output_dir: str = "reports",
                   formats: List[str] = None) -> Dict[str, str]:
        """
        保存报告到文件
        
        Args:
            execution_id: 执行ID
            results: 测试结果列表
            metadata: 元数据
            output_dir: 输出目录
            formats: 报告格式列表 ['json', 'html', 'text']
            
        Returns:
            生成的文件路径字典
        """
        if formats is None:
            formats = ['json', 'html']
        
        os.makedirs(output_dir, exist_ok=True)
        
        report = self.generate_comprehensive_report(execution_id, results, metadata)
        file_paths = {}
        
        # JSON格式
        if 'json' in formats:
            json_path = os.path.join(output_dir, f"{execution_id}_report.json")
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            file_paths['json'] = json_path
        
        # HTML格式
        if 'html' in formats:
            html_path = os.path.join(output_dir, f"{execution_id}_report.html")
            html_content = self._generate_html_content(report)
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            file_paths['html'] = html_path
        
        # 文本格式
        if 'text' in formats:
            text_path = os.path.join(output_dir, f"{execution_id}_report.txt")
            text_content = self._generate_text_report(report)
            with open(text_path, 'w', encoding='utf-8') as f:
                f.write(text_content)
            file_paths['text'] = text_path
        
        return file_paths
    
    def _generate_text_report(self, report: Dict[str, Any]) -> str:
        """生成文本报告"""
        lines = []
        lines.append("=" * 80)
        lines.append("综合测试报告")
        lines.append("=" * 80)
        lines.append(f"执行ID: {report['execution_id']}")
        lines.append(f"生成时间: {report['timestamp']}")
        lines.append("")
        
        # 摘要
        summary = report['summary']
        lines.append("📊 执行摘要")
        lines.append("-" * 80)
        lines.append(f"总用例数: {summary['total']}")
        lines.append(f"通过: {summary['passed']}")
        lines.append(f"失败: {summary['failed']}")
        lines.append(f"通过率: {summary['pass_rate']}")
        lines.append(f"总耗时: {summary['total_duration']}s")
        lines.append("")
        
        # 失败分析
        failure_analysis = report['failure_analysis']
        if failure_analysis['total_failures'] > 0:
            lines.append("❌ 失败分析")
            lines.append("-" * 80)
            lines.append(f"总失败数: {failure_analysis['total_failures']}")
            for cause in failure_analysis['root_causes']:
                lines.append(f"  {cause['category']}: {cause['failure_count']}个 ({cause['percentage']}%)")
            lines.append("")
        
        # 优化建议
        if report['recommendations']:
            lines.append("💡 优化建议")
            lines.append("-" * 80)
            for rec in report['recommendations'][:10]:
                lines.append(f"  [{rec['severity']}] {rec['message']}")
            lines.append("")
        
        lines.append("=" * 80)
        
        return "\n".join(lines)
