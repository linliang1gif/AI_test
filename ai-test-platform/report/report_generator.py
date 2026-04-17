#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
AI Test Platform - 测试报告生成器

生成HTML格式的综合测试报告。
"""

import json
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime
from ai.ai_client import get_ai_client
from ai.prompt_library import PromptLibrary
from config.config import get_config

class ReportGenerator:
    """测试报告生成器"""
    
    def __init__(self):
        self.config = get_config()
        self.ai_client = get_ai_client()
        self.prompt_lib = PromptLibrary()
    
    def generate_report(self, report_data: Dict[str, Any]) -> str:
        """生成测试报告"""
        try:
            # 生成报告内容
            report_content = self._generate_report_content(report_data)
            
            # 生成HTML报告
            html_report = self._generate_html_report(report_content, report_data)
            
            # 保存报告
            report_file = self._save_report(html_report)
            
            return str(report_file)
            
        except Exception as e:
            print(f"报告生成失败: {str(e)}")
            # 生成基础报告
            return self._generate_basic_report(report_data)
    
    def _generate_report_content(self, report_data: Dict[str, Any]) -> str:
        """生成报告内容"""
        # 准备报告数据
        formatted_data = self._format_report_data(report_data)
        
        # 生成报告prompt
        prompt = self.prompt_lib.get_test_report_prompt(
            formatted_data['test_results'], 
            formatted_data['bug_analysis']
        )
        system_prompt = self.prompt_lib.get_system_prompt()
        
        # 调用AI生成报告内容
        report_content = self.ai_client.generate_text(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.3
        )
        
        return report_content
    
    def _format_report_data(self, report_data: Dict[str, Any]) -> Dict[str, str]:
        """格式化报告数据"""
        formatted_data = {}
        
        # 格式化测试结果
        test_results = report_data.get('test_results', {})
        formatted_data['test_results'] = json.dumps(test_results, ensure_ascii=False, indent=2)
        
        # 格式化Bug分析
        bug_analysis = report_data.get('bug_analysis', [])
        formatted_data['bug_analysis'] = json.dumps(bug_analysis, ensure_ascii=False, indent=2)
        
        return formatted_data
    
    def _generate_html_report(self, report_content: str, report_data: Dict[str, Any]) -> str:
        """生成HTML报告"""
        # 提取统计数据
        stats = self._extract_statistics(report_data)
        
        # HTML模板
        html_template = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{self.config.report.title}</title>
    <style>
        {self._get_css_styles()}
    </style>
</head>
<body>
    <div class="container">
        <header class="report-header">
            <h1>{self.config.report.title}</h1>
            <div class="report-info">
                <p>生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                <p>公司: {self.config.report.company_name}</p>
                <p>版本: {self.config.report.version}</p>
            </div>
        </header>
        
        <section class="summary-section">
            <h2>📊 测试摘要</h2>
            <div class="stats-grid">
                {self._generate_stats_cards(stats)}
            </div>
        </section>
        
        <section class="content-section">
            <h2>📋 详细报告</h2>
            <div class="report-content">
                {self._convert_markdown_to_html(report_content)}
            </div>
        </section>
        
        <section class="charts-section">
            <h2>📈 统计图表</h2>
            {self._generate_charts(stats)}
        </section>
        
        <footer class="report-footer">
            <p>报告由 AI Test Platform 自动生成</p>
        </footer>
    </div>
    
    <script>
        {self._get_javascript()}
    </script>
</body>
</html>
"""
        
        return html_template
    
    def _extract_statistics(self, report_data: Dict[str, Any]) -> Dict[str, Any]:
        """提取统计数据"""
        stats = {
            'modules_count': 0,
            'testpoints_count': 0,
            'scenarios_count': 0,
            'testcases_count': 0,
            'test_execution': {
                'total': 0,
                'passed': 0,
                'failed': 0,
                'pass_rate': 0
            },
            'bug_analysis': {
                'total_bugs': 0,
                'severity_distribution': {},
                'type_distribution': {}
            }
        }
        
        # 提取模块统计
        modules = report_data.get('modules', [])
        stats['modules_count'] = len(modules)
        
        # 提取测试点统计
        testpoints = report_data.get('testpoints', {})
        stats['testpoints_count'] = sum(len(tp) for tp in testpoints.values())
        
        # 提取场景统计
        scenarios = report_data.get('scenarios', {})
        stats['scenarios_count'] = sum(len(sc) for sc in scenarios.values())
        
        # 提取测试用例统计
        testcases = report_data.get('testcases', {})
        stats['testcases_count'] = sum(len(tc) for tc in testcases.values())
        
        # 提取测试执行统计
        test_results = report_data.get('test_results', {})
        if 'summary' in test_results:
            summary = test_results['summary']
            stats['test_execution'] = {
                'total': summary.get('total', 0),
                'passed': summary.get('passed', 0),
                'failed': summary.get('failed', 0),
                'pass_rate': summary.get('pass_rate', 0)
            }
        
        # 提取Bug分析统计
        bug_analysis = report_data.get('bug_analysis', [])
        if bug_analysis:
            stats['bug_analysis']['total_bugs'] = len(bug_analysis)
            
            # 统计严重程度分布
            severity_dist = {}
            type_dist = {}
            
            for bug in bug_analysis:
                severity = bug.get('severity', '一般')
                bug_type = bug.get('bug_type', '未知')
                
                severity_dist[severity] = severity_dist.get(severity, 0) + 1
                type_dist[bug_type] = type_dist.get(bug_type, 0) + 1
            
            stats['bug_analysis']['severity_distribution'] = severity_dist
            stats['bug_analysis']['type_distribution'] = type_dist
        
        return stats
    
    def _get_css_styles(self) -> str:
        """获取CSS样式"""
        return """
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #333; background-color: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
        .report-header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 10px; margin-bottom: 30px; }
        .report-header h1 { font-size: 2.5em; margin-bottom: 10px; }
        .report-info { display: flex; gap: 30px; font-size: 1.1em; }
        .summary-section, .content-section, .charts-section { background: white; padding: 30px; border-radius: 10px; margin-bottom: 30px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-top: 20px; }
        .stat-card { background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); color: white; padding: 20px; border-radius: 10px; text-align: center; }
        .stat-card h3 { font-size: 2em; margin-bottom: 10px; }
        .stat-card p { font-size: 1.1em; }
        .report-content { line-height: 1.8; }
        .report-content h2 { color: #667eea; margin: 20px 0 10px 0; }
        .report-content h3 { color: #764ba2; margin: 15px 0 8px 0; }
        .chart-container { margin: 20px 0; padding: 20px; background: #f8f9fa; border-radius: 8px; }
        .report-footer { text-align: center; padding: 20px; color: #666; }
        """
    
    def _generate_stats_cards(self, stats: Dict[str, Any]) -> str:
        """生成统计卡片"""
        cards = []
        
        # 模块数量卡片
        cards.append(f"""
        <div class="stat-card">
            <h3>{stats['modules_count']}</h3>
            <p>功能模块</p>
        </div>
        """)
        
        # 测试用例数量卡片
        cards.append(f"""
        <div class="stat-card">
            <h3>{stats['testcases_count']}</h3>
            <p>测试用例</p>
        </div>
        """)
        
        # 通过率卡片
        pass_rate = stats['test_execution']['pass_rate']
        cards.append(f"""
        <div class="stat-card">
            <h3>{pass_rate:.1f}%</h3>
            <p>测试通过率</p>
        </div>
        """)
        
        # Bug数量卡片
        bug_count = stats['bug_analysis']['total_bugs']
        cards.append(f"""
        <div class="stat-card">
            <h3>{bug_count}</h3>
            <p>发现Bug</p>
        </div>
        """)
        
        return ''.join(cards)
    
    def _convert_markdown_to_html(self, markdown_content: str) -> str:
        """将Markdown转换为HTML"""
        # 简单的Markdown到HTML转换
        html_content = markdown_content
        
        # 转换标题
        html_content = html_content.replace('# ', '<h1>').replace('\n', '</h1>\n', 1)
        html_content = html_content.replace('## ', '<h2>').replace('\n', '</h2>\n', 1)
        html_content = html_content.replace('### ', '<h3>').replace('\n', '</h3>\n', 1)
        
        # 转换列表
        lines = html_content.split('\n')
        in_list = False
        result_lines = []
        
        for line in lines:
            if line.strip().startswith('- '):
                if not in_list:
                    result_lines.append('<ul>')
                    in_list = True
                result_lines.append(f'<li>{line.strip()[2:]}</li>')
            else:
                if in_list:
                    result_lines.append('</ul>')
                    in_list = False
                result_lines.append(line)
        
        if in_list:
            result_lines.append('</ul>')
        
        # 转换段落
        html_content = '\n'.join(result_lines)
        paragraphs = html_content.split('\n\n')
        html_paragraphs = []
        
        for para in paragraphs:
            para = para.strip()
            if para and not para.startswith('<'):
                html_paragraphs.append(f'<p>{para}</p>')
            else:
                html_paragraphs.append(para)
        
        return '\n'.join(html_paragraphs)
    
    def _generate_charts(self, stats: Dict[str, Any]) -> str:
        """生成图表"""
        charts_html = ""
        
        # 测试执行结果饼图
        test_execution = stats['test_execution']
        if test_execution['total'] > 0:
            charts_html += f"""
            <div class="chart-container">
                <h3>测试执行结果分布</h3>
                <canvas id="testResultChart" width="400" height="200"></canvas>
            </div>
            """
        
        # Bug严重程度分布
        severity_dist = stats['bug_analysis']['severity_distribution']
        if severity_dist:
            charts_html += f"""
            <div class="chart-container">
                <h3>Bug严重程度分布</h3>
                <canvas id="bugSeverityChart" width="400" height="200"></canvas>
            </div>
            """
        
        return charts_html
    
    def _get_javascript(self) -> str:
        """获取JavaScript代码"""
        return """
        // 简单的图表绘制函数
        function drawPieChart(canvasId, data, labels) {
            const canvas = document.getElementById(canvasId);
            if (!canvas) return;
            
            const ctx = canvas.getContext('2d');
            const centerX = canvas.width / 2;
            const centerY = canvas.height / 2;
            const radius = Math.min(centerX, centerY) - 20;
            
            let total = data.reduce((sum, value) => sum + value, 0);
            let currentAngle = 0;
            
            const colors = ['#4CAF50', '#F44336', '#FF9800', '#2196F3', '#9C27B0'];
            
            data.forEach((value, index) => {
                const sliceAngle = (value / total) * 2 * Math.PI;
                
                ctx.beginPath();
                ctx.moveTo(centerX, centerY);
                ctx.arc(centerX, centerY, radius, currentAngle, currentAngle + sliceAngle);
                ctx.closePath();
                ctx.fillStyle = colors[index % colors.length];
                ctx.fill();
                
                // 绘制标签
                const labelAngle = currentAngle + sliceAngle / 2;
                const labelX = centerX + Math.cos(labelAngle) * (radius + 30);
                const labelY = centerY + Math.sin(labelAngle) * (radius + 30);
                
                ctx.fillStyle = '#333';
                ctx.font = '12px Arial';
                ctx.textAlign = 'center';
                ctx.fillText(labels[index] + ': ' + value, labelX, labelY);
                
                currentAngle += sliceAngle;
            });
        }
        
        // 页面加载完成后绘制图表
        window.onload = function() {
            // 测试结果图表
            const testResultCanvas = document.getElementById('testResultChart');
            if (testResultCanvas) {
                drawPieChart('testResultChart', 
                    [{{ test_passed }}, {{ test_failed }}], 
                    ['通过', '失败']);
            }
            
            // Bug严重程度图表
            const bugSeverityCanvas = document.getElementById('bugSeverityChart');
            if (bugSeverityCanvas) {
                drawPieChart('bugSeverityChart', 
                    [{{ bug_severe }}, {{ bug_normal }}, {{ bug_minor }}], 
                    ['严重', '一般', '轻微']);
            }
        };
        """
    
    def _save_report(self, html_content: str) -> Path:
        """保存报告"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = self.config.paths.reports_dir / f'test_report_{timestamp}.html'
        
        # 替换JavaScript中的占位符
        test_execution = self._extract_statistics({}).get('test_execution', {})
        html_content = html_content.replace('{{ test_passed }}', str(test_execution.get('passed', 0)))
        html_content = html_content.replace('{{ test_failed }}', str(test_execution.get('failed', 0)))
        html_content = html_content.replace('{{ bug_severe }}', '0')
        html_content = html_content.replace('{{ bug_normal }}', '0')
        html_content = html_content.replace('{{ bug_minor }}', '0')
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"📋 测试报告已生成: {report_file}")
        return report_file
    
    def _generate_basic_report(self, report_data: Dict[str, Any]) -> str:
        """生成基础报告"""
        stats = self._extract_statistics(report_data)
        
        basic_html = f"""
<!DOCTYPE html>
<html>
<head><title>测试报告</title></head>
<body>
<h1>AI Test Platform 测试报告</h1>
<h2>测试摘要</h2>
<p>模块数量: {stats['modules_count']}</p>
<p>测试用例数量: {stats['testcases_count']}</p>
<p>测试通过率: {stats['test_execution']['pass_rate']:.1f}%</p>
<p>发现Bug数量: {stats['bug_analysis']['total_bugs']}</p>
</body>
</html>
"""
        
        report_file = self.config.paths.reports_dir / 'basic_test_report.html'
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(basic_html)
        
        return str(report_file)