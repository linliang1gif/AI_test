#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试覆盖率分析器

分析测试覆盖率：
- 需求覆盖率
- 测试点覆盖率  
- 测试用例覆盖率
- 自动化覆盖率
"""

import json
from typing import Dict, List, Any, Optional
from pathlib import Path
from collections import defaultdict

class CoverageAnalyzer:
    """测试覆盖率分析器"""
    
    def __init__(self):
        self.coverage_data = {}
        self.analysis_results = {}
    
    def analyze_coverage(self, 
                        requirements: List[Dict[str, Any]],
                        test_points: Dict[str, List[Dict[str, Any]]],
                        test_cases: Dict[str, List[Dict[str, Any]]],
                        automation_scripts: Dict[str, str]) -> Dict[str, Any]:
        """分析完整测试覆盖率"""
        
        coverage_analysis = {
            'timestamp': self._get_timestamp(),
            'summary': {},
            'module_coverage': {},
            'detailed_analysis': {},
            'recommendations': []
        }
        
        # 按模块分析覆盖率
        modules = self._extract_modules(requirements, test_points, test_cases)
        
        total_coverage_data = {
            'requirement_count': 0,
            'test_point_count': 0,
            'test_case_count': 0,
            'automation_count': 0
        }
        
        for module_name in modules:
            module_coverage = self._analyze_module_coverage(
                module_name, requirements, test_points, test_cases, automation_scripts
            )
            
            coverage_analysis['module_coverage'][module_name] = module_coverage
            
            # 累计总数
            for key in total_coverage_data:
                total_coverage_data[key] += module_coverage.get(key, 0)
        
        # 计算总体覆盖率
        coverage_analysis['summary'] = self._calculate_summary_coverage(total_coverage_data)
        
        # 生成详细分析
        coverage_analysis['detailed_analysis'] = self._generate_detailed_analysis(
            coverage_analysis['module_coverage']
        )
        
        # 生成改进建议
        coverage_analysis['recommendations'] = self._generate_recommendations(
            coverage_analysis['module_coverage']
        )
        
        self.analysis_results = coverage_analysis
        return coverage_analysis
    
    def _extract_modules(self, requirements: List[Dict[str, Any]], 
                        test_points: Dict[str, List[Dict[str, Any]]],
                        test_cases: Dict[str, List[Dict[str, Any]]]) -> List[str]:
        """提取所有模块名称"""
        modules = set()
        
        # 从需求中提取
        for req in requirements:
            if 'module' in req:
                modules.add(req['module'])
        
        # 从测试点中提取
        modules.update(test_points.keys())
        
        # 从测试用例中提取
        modules.update(test_cases.keys())
        
        return list(modules)
    
    def _analyze_module_coverage(self, 
                                module_name: str,
                                requirements: List[Dict[str, Any]],
                                test_points: Dict[str, List[Dict[str, Any]]],
                                test_cases: Dict[str, List[Dict[str, Any]]],
                                automation_scripts: Dict[str, str]) -> Dict[str, Any]:
        """分析单个模块的覆盖率"""
        
        # 统计各项数量
        requirement_count = len([req for req in requirements if req.get('module') == module_name])
        test_point_count = len(test_points.get(module_name, []))
        test_case_count = len(test_cases.get(module_name, []))
        
        # 统计自动化脚本数量
        automation_count = 0
        for script_path in automation_scripts.keys():
            if module_name.lower() in script_path.lower():
                automation_count += 1
        
        # 计算覆盖率
        test_point_coverage = (test_point_count / requirement_count * 100) if requirement_count > 0 else 0
        test_case_coverage = (test_case_count / test_point_count * 100) if test_point_count > 0 else 0
        automation_coverage = (automation_count / test_case_count * 100) if test_case_count > 0 else 0
        
        # 计算综合覆盖率
        overall_coverage = (automation_count / requirement_count * 100) if requirement_count > 0 else 0
        
        return {
            'module': module_name,
            'requirement_count': requirement_count,
            'test_point_count': test_point_count,
            'test_case_count': test_case_count,
            'automation_count': automation_count,
            'test_point_coverage': round(test_point_coverage, 2),
            'test_case_coverage': round(test_case_coverage, 2),
            'automation_coverage': round(automation_coverage, 2),
            'overall_coverage': round(overall_coverage, 2),
            'coverage_level': self._get_coverage_level(overall_coverage)
        }
    
    def _calculate_summary_coverage(self, total_data: Dict[str, int]) -> Dict[str, Any]:
        """计算总体覆盖率摘要"""
        req_count = total_data['requirement_count']
        tp_count = total_data['test_point_count']
        tc_count = total_data['test_case_count']
        auto_count = total_data['automation_count']
        
        return {
            'total_requirements': req_count,
            'total_test_points': tp_count,
            'total_test_cases': tc_count,
            'total_automation': auto_count,
            'test_point_coverage_rate': round((tp_count / req_count * 100) if req_count > 0 else 0, 2),
            'test_case_coverage_rate': round((tc_count / tp_count * 100) if tp_count > 0 else 0, 2),
            'automation_coverage_rate': round((auto_count / tc_count * 100) if tc_count > 0 else 0, 2),
            'overall_coverage_rate': round((auto_count / req_count * 100) if req_count > 0 else 0, 2)
        }
    
    def _generate_detailed_analysis(self, module_coverage: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """生成详细分析"""
        analysis = {
            'high_coverage_modules': [],
            'medium_coverage_modules': [],
            'low_coverage_modules': [],
            'coverage_gaps': [],
            'strengths': [],
            'weaknesses': []
        }
        
        for module_name, coverage in module_coverage.items():
            coverage_rate = coverage['overall_coverage']
            
            if coverage_rate >= 80:
                analysis['high_coverage_modules'].append({
                    'module': module_name,
                    'coverage': coverage_rate
                })
            elif coverage_rate >= 50:
                analysis['medium_coverage_modules'].append({
                    'module': module_name,
                    'coverage': coverage_rate
                })
            else:
                analysis['low_coverage_modules'].append({
                    'module': module_name,
                    'coverage': coverage_rate
                })
            
            # 识别覆盖率缺口
            if coverage['test_point_coverage'] < 80:
                analysis['coverage_gaps'].append({
                    'module': module_name,
                    'gap_type': 'test_points',
                    'current': coverage['test_point_coverage'],
                    'target': 80
                })
            
            if coverage['automation_coverage'] < 60:
                analysis['coverage_gaps'].append({
                    'module': module_name,
                    'gap_type': 'automation',
                    'current': coverage['automation_coverage'],
                    'target': 60
                })
        
        # 识别优势和劣势
        if analysis['high_coverage_modules']:
            analysis['strengths'].append(f"有 {len(analysis['high_coverage_modules'])} 个模块达到高覆盖率")
        
        if analysis['low_coverage_modules']:
            analysis['weaknesses'].append(f"有 {len(analysis['low_coverage_modules'])} 个模块覆盖率偏低")
        
        if len(analysis['coverage_gaps']) > 0:
            analysis['weaknesses'].append(f"发现 {len(analysis['coverage_gaps'])} 个覆盖率缺口")
        
        return analysis
    
    def _generate_recommendations(self, module_coverage: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
        """生成改进建议"""
        recommendations = []
        
        for module_name, coverage in module_coverage.items():
            # 测试点覆盖率建议
            if coverage['test_point_coverage'] < 80:
                recommendations.append({
                    'type': 'test_points',
                    'priority': 'high' if coverage['test_point_coverage'] < 50 else 'medium',
                    'module': module_name,
                    'current_coverage': coverage['test_point_coverage'],
                    'recommendation': f"为{module_name}模块补充测试点设计，当前覆盖率{coverage['test_point_coverage']:.1f}%，建议提升至80%以上",
                    'action_items': [
                        "分析需求细节，识别遗漏的测试场景",
                        "补充边界值和异常情况的测试点",
                        "增加用户体验相关的测试点"
                    ]
                })
            
            # 测试用例覆盖率建议
            if coverage['test_case_coverage'] < 90:
                recommendations.append({
                    'type': 'test_cases',
                    'priority': 'medium',
                    'module': module_name,
                    'current_coverage': coverage['test_case_coverage'],
                    'recommendation': f"为{module_name}模块补充测试用例，当前覆盖率{coverage['test_case_coverage']:.1f}%",
                    'action_items': [
                        "为每个测试点设计详细的测试用例",
                        "确保测试用例包含完整的前置条件和预期结果",
                        "添加数据驱动的测试用例"
                    ]
                })
            
            # 自动化覆盖率建议
            if coverage['automation_coverage'] < 60:
                recommendations.append({
                    'type': 'automation',
                    'priority': 'high' if coverage['automation_coverage'] < 30 else 'medium',
                    'module': module_name,
                    'current_coverage': coverage['automation_coverage'],
                    'recommendation': f"提升{module_name}模块自动化覆盖率，当前{coverage['automation_coverage']:.1f}%",
                    'action_items': [
                        "优先自动化核心功能和回归测试用例",
                        "为API接口编写自动化测试脚本",
                        "建立持续集成的自动化测试流程"
                    ]
                })
        
        # 按优先级排序
        priority_order = {'high': 0, 'medium': 1, 'low': 2}
        recommendations.sort(key=lambda x: priority_order.get(x['priority'], 3))
        
        return recommendations
    
    def _get_coverage_level(self, coverage_rate: float) -> str:
        """获取覆盖率等级"""
        if coverage_rate >= 80:
            return 'excellent'
        elif coverage_rate >= 60:
            return 'good'
        elif coverage_rate >= 40:
            return 'fair'
        else:
            return 'poor'
    
    def _get_timestamp(self) -> str:
        """获取时间戳"""
        import datetime
        return datetime.datetime.now().isoformat()
    
    def export_coverage_report(self, output_path: str) -> str:
        """导出覆盖率报告"""
        if not self.analysis_results:
            raise ValueError("请先执行覆盖率分析")
        
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.analysis_results, f, ensure_ascii=False, indent=2)
        
        return str(output_file)
    
    def get_coverage_summary_text(self) -> str:
        """获取覆盖率摘要文本"""
        if not self.analysis_results:
            return "未进行覆盖率分析"
        
        summary = self.analysis_results['summary']
        
        text = f"""
测试覆盖率分析摘要
==================

总体统计：
- 需求总数：{summary['total_requirements']}
- 测试点总数：{summary['total_test_points']}
- 测试用例总数：{summary['total_test_cases']}
- 自动化脚本总数：{summary['total_automation']}

覆盖率指标：
- 测试点覆盖率：{summary['test_point_coverage_rate']}%
- 测试用例覆盖率：{summary['test_case_coverage_rate']}%
- 自动化覆盖率：{summary['automation_coverage_rate']}%
- 综合覆盖率：{summary['overall_coverage_rate']}%

改进建议数量：{len(self.analysis_results['recommendations'])}
"""
        
        return text.strip()