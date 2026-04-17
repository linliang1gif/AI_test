#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
AI Test Platform - 测试点生成器

根据功能模块信息，使用AI生成全面的测试点。
"""

import json
from typing import List, Dict, Any
from ai.ai_client import get_ai_client
from ai.prompt_library import PromptLibrary
from config.config import get_config

class TestPointGenerator:
    """测试点生成器"""
    
    def __init__(self):
        self.config = get_config()
        self.ai_client = get_ai_client()
        self.prompt_lib = PromptLibrary()
    
    def generate_testpoints(self, modules: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """为所有模块生成测试点"""
        all_testpoints = {}
        
        for module in modules:
            try:
                module_testpoints = self._generate_module_testpoints(module)
                all_testpoints[module['name']] = module_testpoints
            except Exception as e:
                print(f"为模块 {module['name']} 生成测试点失败: {str(e)}")
                # 使用默认测试点
                all_testpoints[module['name']] = self._get_default_testpoints(module)
        
        return all_testpoints
    
    def _generate_module_testpoints(self, module: Dict[str, Any]) -> List[Dict[str, Any]]:
        """为单个模块生成测试点"""
        # 准备模块信息
        module_info = self._format_module_info(module)
        
        # 生成测试点prompt
        prompt = self.prompt_lib.get_testpoint_generation_prompt(module_info)
        system_prompt = self.prompt_lib.get_system_prompt()
        
        # 调用AI生成测试点
        response = self.ai_client.generate_json(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.4
        )
        
        testpoints = response.get('testpoints', [])
        
        # 验证和补充测试点信息
        validated_testpoints = self._validate_testpoints(testpoints, module)
        
        # 确保测试覆盖完整性
        complete_testpoints = self._ensure_test_coverage(validated_testpoints, module)
        
        return complete_testpoints
    
    def _format_module_info(self, module: Dict[str, Any]) -> str:
        """格式化模块信息"""
        info_lines = []
        info_lines.append(f"模块名称: {module['name']}")
        info_lines.append(f"模块描述: {module['description']}")
        info_lines.append(f"优先级: {module['priority']}")
        info_lines.append(f"复杂度: {module['complexity']}")
        
        if module.get('functions'):
            info_lines.append("主要功能:")
            for func in module['functions']:
                info_lines.append(f"  - {func}")
        
        if module.get('dependencies'):
            info_lines.append("依赖模块:")
            for dep in module['dependencies']:
                info_lines.append(f"  - {dep}")
        
        return "\n".join(info_lines)
    
    def _validate_testpoints(self, testpoints: List[Dict[str, Any]], module: Dict[str, Any]) -> List[Dict[str, Any]]:
        """验证和补充测试点信息"""
        validated_testpoints = []
        
        for i, testpoint in enumerate(testpoints):
            validated_testpoint = {
                'id': f"{module['id']}_tp_{i+1:03d}",
                'module_name': module['name'],
                'category': testpoint.get('category', '功能测试'),
                'name': testpoint.get('name', f'测试点{i+1}'),
                'description': testpoint.get('description', ''),
                'priority': testpoint.get('priority', '中'),
                'complexity': testpoint.get('complexity', '中等'),
                'test_type': self._determine_test_type(testpoint),
                'estimated_cases': self._estimate_test_cases(testpoint),
                'risk_level': self._assess_risk_level(testpoint, module)
            }
            
            # 验证测试点名称
            if not validated_testpoint['name'] or len(validated_testpoint['name']) < 3:
                validated_testpoint['name'] = f"{validated_testpoint['category']}测试点{i+1}"
            
            validated_testpoints.append(validated_testpoint)
        
        return validated_testpoints
    
    def _determine_test_type(self, testpoint: Dict[str, Any]) -> List[str]:
        """确定测试类型"""
        category = testpoint.get('category', '').lower()
        name = testpoint.get('name', '').lower()
        description = testpoint.get('description', '').lower()
        
        test_types = []
        
        # 基于类别确定测试类型
        if '功能' in category or 'function' in category:
            test_types.append('功能测试')
        
        if '性能' in category or 'performance' in category:
            test_types.append('性能测试')
        
        if '安全' in category or 'security' in category:
            test_types.append('安全测试')
        
        if '边界' in category or 'boundary' in category:
            test_types.append('边界测试')
        
        if '异常' in category or 'exception' in category:
            test_types.append('异常测试')
        
        if '权限' in category or 'permission' in category:
            test_types.append('权限测试')
        
        # 基于名称和描述补充测试类型
        text = f"{name} {description}"
        
        if any(keyword in text for keyword in ['登录', '注册', '验证', 'login', 'register']):
            test_types.append('身份验证测试')
        
        if any(keyword in text for keyword in ['接口', 'api', 'rest']):
            test_types.append('接口测试')
        
        if any(keyword in text for keyword in ['数据库', 'database', 'sql']):
            test_types.append('数据测试')
        
        if any(keyword in text for keyword in ['并发', 'concurrent', '负载', 'load']):
            test_types.append('并发测试')
        
        # 如果没有确定类型，默认为功能测试
        if not test_types:
            test_types.append('功能测试')
        
        return list(set(test_types))
    
    def _estimate_test_cases(self, testpoint: Dict[str, Any]) -> int:
        """估算测试用例数量"""
        complexity = testpoint.get('complexity', '中等')
        category = testpoint.get('category', '')
        
        # 基础用例数量
        base_cases = {
            '简单': 3,
            '中等': 5,
            '复杂': 8
        }
        
        case_count = base_cases.get(complexity, 5)
        
        # 根据测试类别调整
        if '安全' in category or '权限' in category:
            case_count += 2  # 安全测试需要更多用例
        
        if '边界' in category or '异常' in category:
            case_count += 3  # 边界和异常测试需要更多用例
        
        if '性能' in category:
            case_count += 1  # 性能测试相对较少但重要
        
        return max(case_count, 2)  # 至少2个用例
    
    def _assess_risk_level(self, testpoint: Dict[str, Any], module: Dict[str, Any]) -> str:
        """评估风险等级"""
        priority = testpoint.get('priority', '中')
        complexity = testpoint.get('complexity', '中等')
        module_priority = module.get('priority', '中')
        category = testpoint.get('category', '')
        
        # 风险评分
        risk_score = 0
        
        # 优先级影响
        priority_scores = {'高': 3, '中': 2, '低': 1}
        risk_score += priority_scores.get(priority, 2)
        risk_score += priority_scores.get(module_priority, 2)
        
        # 复杂度影响
        complexity_scores = {'复杂': 3, '中等': 2, '简单': 1}
        risk_score += complexity_scores.get(complexity, 2)
        
        # 测试类别影响
        high_risk_categories = ['安全', '权限', '数据', 'security', 'permission']
        if any(keyword in category.lower() for keyword in high_risk_categories):
            risk_score += 2
        
        # 确定风险等级
        if risk_score >= 8:
            return '高'
        elif risk_score >= 5:
            return '中'
        else:
            return '低'
    
    def _ensure_test_coverage(self, testpoints: List[Dict[str, Any]], module: Dict[str, Any]) -> List[Dict[str, Any]]:
        """确保测试覆盖完整性"""
        # 检查必要的测试类别
        required_categories = [
            '功能测试',
            '边界测试', 
            '异常测试',
            '权限测试'
        ]
        
        existing_categories = [tp['category'] for tp in testpoints]
        
        # 补充缺失的测试类别
        for category in required_categories:
            if category not in existing_categories:
                additional_testpoint = self._create_default_testpoint(category, module, len(testpoints))
                testpoints.append(additional_testpoint)
        
        return testpoints
    
    def _create_default_testpoint(self, category: str, module: Dict[str, Any], index: int) -> Dict[str, Any]:
        """创建默认测试点"""
        category_templates = {
            '功能测试': {
                'name': f"{module['name']}核心功能验证",
                'description': f"验证{module['name']}的核心功能是否正常工作"
            },
            '边界测试': {
                'name': f"{module['name']}边界条件测试",
                'description': f"验证{module['name']}在边界条件下的行为"
            },
            '异常测试': {
                'name': f"{module['name']}异常处理测试",
                'description': f"验证{module['name']}的异常处理能力"
            },
            '权限测试': {
                'name': f"{module['name']}权限控制测试",
                'description': f"验证{module['name']}的权限控制机制"
            }
        }
        
        template = category_templates.get(category, {
            'name': f"{module['name']}{category}",
            'description': f"{module['name']}的{category}"
        })
        
        return {
            'id': f"{module['id']}_tp_{index+1:03d}",
            'module_name': module['name'],
            'category': category,
            'name': template['name'],
            'description': template['description'],
            'priority': '中',
            'complexity': '中等',
            'test_type': [category],
            'estimated_cases': 3,
            'risk_level': '中'
        }
    
    def _get_default_testpoints(self, module: Dict[str, Any]) -> List[Dict[str, Any]]:
        """获取默认测试点"""
        default_categories = [
            '功能测试',
            '边界测试',
            '异常测试',
            '权限测试',
            '性能测试'
        ]
        
        testpoints = []
        for i, category in enumerate(default_categories):
            testpoint = self._create_default_testpoint(category, module, i)
            testpoints.append(testpoint)
        
        return testpoints
    
    def generate_testpoint_summary(self, all_testpoints: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        """生成测试点摘要"""
        total_testpoints = sum(len(testpoints) for testpoints in all_testpoints.values())
        
        # 统计各种分布
        category_stats = {}
        priority_stats = {'高': 0, '中': 0, '低': 0}
        risk_stats = {'高': 0, '中': 0, '低': 0}
        complexity_stats = {'简单': 0, '中等': 0, '复杂': 0}
        
        total_estimated_cases = 0
        
        for module_name, testpoints in all_testpoints.items():
            for tp in testpoints:
                # 统计类别
                category = tp.get('category', '其他')
                category_stats[category] = category_stats.get(category, 0) + 1
                
                # 统计优先级
                priority_stats[tp.get('priority', '中')] += 1
                
                # 统计风险等级
                risk_stats[tp.get('risk_level', '中')] += 1
                
                # 统计复杂度
                complexity_stats[tp.get('complexity', '中等')] += 1
                
                # 累计预估用例数
                total_estimated_cases += tp.get('estimated_cases', 0)
        
        return {
            'total_modules': len(all_testpoints),
            'total_testpoints': total_testpoints,
            'total_estimated_cases': total_estimated_cases,
            'average_testpoints_per_module': total_testpoints / max(len(all_testpoints), 1),
            'category_distribution': category_stats,
            'priority_distribution': priority_stats,
            'risk_distribution': risk_stats,
            'complexity_distribution': complexity_stats,
            'coverage_analysis': self._analyze_coverage(all_testpoints)
        }
    
    def _analyze_coverage(self, all_testpoints: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        """分析测试覆盖情况"""
        required_categories = [
            '功能测试', '边界测试', '异常测试', '权限测试', '性能测试', '安全测试'
        ]
        
        coverage_analysis = {
            'covered_categories': set(),
            'missing_categories': [],
            'coverage_percentage': 0,
            'recommendations': []
        }
        
        # 收集所有已覆盖的类别
        for testpoints in all_testpoints.values():
            for tp in testpoints:
                coverage_analysis['covered_categories'].add(tp.get('category', ''))
        
        # 计算覆盖率
        covered_required = len([cat for cat in required_categories 
                              if cat in coverage_analysis['covered_categories']])
        coverage_analysis['coverage_percentage'] = (covered_required / len(required_categories)) * 100
        
        # 找出缺失的类别
        coverage_analysis['missing_categories'] = [
            cat for cat in required_categories 
            if cat not in coverage_analysis['covered_categories']
        ]
        
        # 生成建议
        if coverage_analysis['missing_categories']:
            coverage_analysis['recommendations'].append(
                f"建议补充以下测试类别: {', '.join(coverage_analysis['missing_categories'])}"
            )
        
        if coverage_analysis['coverage_percentage'] < 80:
            coverage_analysis['recommendations'].append("测试覆盖率偏低，建议增加测试点")
        
        # 转换set为list以便JSON序列化
        coverage_analysis['covered_categories'] = list(coverage_analysis['covered_categories'])
        
        return coverage_analysis
    
    def export_testpoints_report(self, all_testpoints: Dict[str, List[Dict[str, Any]]]) -> str:
        """导出测试点报告"""
        report_lines = []
        report_lines.append("# 测试点分析报告")
        report_lines.append("")
        
        # 摘要信息
        summary = self.generate_testpoint_summary(all_testpoints)
        report_lines.append("## 摘要信息")
        report_lines.append(f"- 模块总数: {summary['total_modules']}")
        report_lines.append(f"- 测试点总数: {summary['total_testpoints']}")
        report_lines.append(f"- 预估用例总数: {summary['total_estimated_cases']}")
        report_lines.append(f"- 平均每模块测试点: {summary['average_testpoints_per_module']:.1f}")
        report_lines.append("")
        
        # 各模块测试点详情
        report_lines.append("## 各模块测试点详情")
        for module_name, testpoints in all_testpoints.items():
            report_lines.append(f"### {module_name}")
            report_lines.append(f"测试点数量: {len(testpoints)}")
            report_lines.append("")
            
            for tp in testpoints:
                report_lines.append(f"**{tp['name']}**")
                report_lines.append(f"- 类别: {tp['category']}")
                report_lines.append(f"- 优先级: {tp['priority']}")
                report_lines.append(f"- 复杂度: {tp['complexity']}")
                report_lines.append(f"- 风险等级: {tp['risk_level']}")
                report_lines.append(f"- 预估用例数: {tp['estimated_cases']}")
                report_lines.append(f"- 描述: {tp['description']}")
                report_lines.append("")
        
        return "\n".join(report_lines)