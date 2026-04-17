#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
AI Test Platform - 测试场景矩阵生成器

根据测试点生成测试场景矩阵，覆盖各种测试维度的组合。
"""

import json
from typing import List, Dict, Any
from ai.ai_client import get_ai_client
from ai.prompt_library import PromptLibrary
from config.config import get_config

class ScenarioMatrixGenerator:
    """测试场景矩阵生成器"""
    
    def __init__(self):
        self.config = get_config()
        self.ai_client = get_ai_client()
        self.prompt_lib = PromptLibrary()
        
        # 测试维度定义
        self.test_dimensions = {
            'input_data': ['有效数据', '无效数据', '边界数据', '空数据', '特殊字符', '超长数据'],
            'user_state': ['已登录', '未登录', '权限不足', '账户锁定', '账户过期', '新用户'],
            'system_state': ['正常运行', '高负载', '维护模式', '异常状态', '资源不足', '服务降级'],
            'network': ['正常网络', '慢网络', '网络中断', '不稳定网络', '高延迟', '低带宽'],
            'device': ['Chrome浏览器', 'Firefox浏览器', 'Safari浏览器', 'Edge浏览器', '移动设备', 'IE浏览器'],
            'data_state': ['数据存在', '数据不存在', '数据过期', '数据损坏', '数据冲突', '数据同步中']
        }
    
    def generate_scenario_matrix(self, all_testpoints: Dict[str, List[Dict[str, Any]]]) -> Dict[str, List[Dict[str, Any]]]:
        """为所有测试点生成场景矩阵"""
        all_scenarios = {}
        
        for module_name, testpoints in all_testpoints.items():
            try:
                module_scenarios = self._generate_module_scenarios(module_name, testpoints)
                all_scenarios[module_name] = module_scenarios
            except Exception as e:
                print(f"为模块 {module_name} 生成场景矩阵失败: {str(e)}")
                # 使用默认场景
                all_scenarios[module_name] = self._get_default_scenarios(module_name, testpoints)
        
        return all_scenarios
    
    def _generate_module_scenarios(self, module_name: str, testpoints: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """为单个模块生成场景矩阵"""
        try:
            # 准备测试点信息
            testpoints_info = self._format_testpoints_info(testpoints)
            
            # 生成场景矩阵prompt
            prompt = self.prompt_lib.get_scenario_matrix_prompt(testpoints_info)
            system_prompt = self.prompt_lib.get_system_prompt()
            
            # 调用AI生成场景矩阵
            response = self.ai_client.generate_json(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=0.5
            )
            
            scenarios = response.get('scenarios', [])
            
            # 如果AI返回的场景为空或无效,使用默认场景
            if not scenarios or not isinstance(scenarios, list) or len(scenarios) == 0:
                print(f"  ⚠️  AI返回场景为空,使用默认场景")
                return self._get_default_scenarios(module_name, testpoints)
            
            # 验证和补充场景信息
            validated_scenarios = self._validate_scenarios(scenarios, module_name, testpoints)
            
            # 确保场景覆盖完整性
            complete_scenarios = self._ensure_scenario_coverage(validated_scenarios, module_name, testpoints)
            
            return complete_scenarios
            
        except Exception as e:
            print(f"  ⚠️  AI生成场景失败: {str(e)},使用默认场景")
            return self._get_default_scenarios(module_name, testpoints)
    
    def _format_testpoints_info(self, testpoints: List[Dict[str, Any]]) -> str:
        """格式化测试点信息"""
        info_lines = []
        
        for tp in testpoints:
            info_lines.append(f"测试点: {tp['name']}")
            info_lines.append(f"  类别: {tp['category']}")
            info_lines.append(f"  描述: {tp['description']}")
            info_lines.append(f"  优先级: {tp['priority']}")
            info_lines.append("")
        
        return "\n".join(info_lines)
    
    def _validate_scenarios(self, scenarios: List[Dict[str, Any]], module_name: str, testpoints: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """验证和补充场景信息"""
        validated_scenarios = []
        
        for i, scenario in enumerate(scenarios):
            validated_scenario = {
                'id': f"{module_name}_scenario_{i+1:03d}",
                'name': scenario.get('name', f'测试场景{i+1}'),
                'module_name': module_name,
                'testpoint_id': self._match_testpoint(scenario, testpoints),
                'input_data': scenario.get('input_data', '有效数据'),
                'user_state': scenario.get('user_state', '已登录'),
                'system_state': scenario.get('system_state', '正常运行'),
                'network': scenario.get('network', '正常网络'),
                'device': scenario.get('device', 'Chrome浏览器'),
                'data_state': scenario.get('data_state', '数据存在'),
                'expected_result': scenario.get('expected_result', '操作成功'),
                'priority': scenario.get('priority', '中'),
                'complexity': self._assess_scenario_complexity(scenario),
                'risk_level': self._assess_scenario_risk(scenario),
                'execution_time': self._estimate_execution_time(scenario)
            }
            
            # 验证场景名称
            if not validated_scenario['name'] or len(validated_scenario['name']) < 3:
                validated_scenario['name'] = f"{module_name}测试场景{i+1}"
            
            validated_scenarios.append(validated_scenario)
        
        return validated_scenarios
    
    def _match_testpoint(self, scenario: Dict[str, Any], testpoints: List[Dict[str, Any]]) -> str:
        """匹配对应的测试点"""
        scenario_name = scenario.get('name', '').lower()
        
        # 尝试根据名称匹配测试点
        for tp in testpoints:
            tp_name = tp['name'].lower()
            if any(word in scenario_name for word in tp_name.split()):
                return tp['id']
        
        # 如果没有匹配到，返回第一个测试点的ID
        return testpoints[0]['id'] if testpoints else ''
    
    def _assess_scenario_complexity(self, scenario: Dict[str, Any]) -> str:
        """评估场景复杂度"""
        complexity_score = 0
        
        # 检查各个维度的复杂性
        dimensions = ['input_data', 'user_state', 'system_state', 'network', 'device', 'data_state']
        
        for dim in dimensions:
            value = scenario.get(dim, '')
            
            # 复杂条件增加分数
            if any(keyword in value.lower() for keyword in ['异常', '错误', '中断', '损坏', '冲突']):
                complexity_score += 2
            elif any(keyword in value.lower() for keyword in ['边界', '特殊', '过期', '锁定']):
                complexity_score += 1
        
        # 确定复杂度等级
        if complexity_score >= 6:
            return '复杂'
        elif complexity_score >= 3:
            return '中等'
        else:
            return '简单'
    
    def _assess_scenario_risk(self, scenario: Dict[str, Any]) -> str:
        """评估场景风险等级"""
        risk_score = 0
        
        # 高风险条件
        high_risk_conditions = [
            '数据损坏', '数据冲突', '账户锁定', '权限不足', 
            '网络中断', '异常状态', '资源不足'
        ]
        
        # 中风险条件
        medium_risk_conditions = [
            '边界数据', '特殊字符', '慢网络', '高负载',
            '数据过期', '账户过期'
        ]
        
        # 检查所有维度
        scenario_text = ' '.join(str(v) for v in scenario.values())
        
        for condition in high_risk_conditions:
            if condition in scenario_text:
                risk_score += 3
        
        for condition in medium_risk_conditions:
            if condition in scenario_text:
                risk_score += 1
        
        # 确定风险等级
        if risk_score >= 6:
            return '高'
        elif risk_score >= 2:
            return '中'
        else:
            return '低'
    
    def _estimate_execution_time(self, scenario: Dict[str, Any]) -> int:
        """估算执行时间（分钟）"""
        base_time = 5  # 基础执行时间
        
        complexity = self._assess_scenario_complexity(scenario)
        complexity_multiplier = {
            '简单': 1.0,
            '中等': 1.5,
            '复杂': 2.0
        }
        
        return int(base_time * complexity_multiplier.get(complexity, 1.0))
    
    def _ensure_scenario_coverage(self, scenarios: List[Dict[str, Any]], module_name: str, testpoints: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """确保场景覆盖完整性"""
        # 检查关键场景组合
        critical_combinations = [
            {'input_data': '无效数据', 'user_state': '已登录'},
            {'input_data': '边界数据', 'system_state': '正常运行'},
            {'input_data': '有效数据', 'user_state': '未登录'},
            {'input_data': '空数据', 'user_state': '已登录'},
            {'input_data': '有效数据', 'network': '网络中断'}
        ]
        
        existing_combinations = []
        for scenario in scenarios:
            combo = {
                'input_data': scenario['input_data'],
                'user_state': scenario['user_state']
            }
            existing_combinations.append(combo)
        
        # 补充缺失的关键场景
        for i, combo in enumerate(critical_combinations):
            if not any(self._combinations_match(combo, existing) for existing in existing_combinations):
                additional_scenario = self._create_scenario_from_combination(
                    combo, module_name, testpoints, len(scenarios) + i
                )
                scenarios.append(additional_scenario)
        
        return scenarios
    
    def _combinations_match(self, combo1: Dict[str, str], combo2: Dict[str, str]) -> bool:
        """检查两个组合是否匹配"""
        for key, value in combo1.items():
            if combo2.get(key) != value:
                return False
        return True
    
    def _create_scenario_from_combination(self, combination: Dict[str, str], module_name: str, testpoints: List[Dict[str, Any]], index: int) -> Dict[str, Any]:
        """根据组合创建场景"""
        input_data = combination.get('input_data', '有效数据')
        user_state = combination.get('user_state', '已登录')
        scenario_name = f"{module_name}_{input_data}_{user_state}_场景"
        
        return {
            'id': f"{module_name}_scenario_{index+1:03d}",
            'name': scenario_name,
            'module_name': module_name,
            'testpoint_id': testpoints[0]['id'] if testpoints else '',
            'input_data': input_data,
            'user_state': user_state,
            'system_state': combination.get('system_state', '正常运行'),
            'network': combination.get('network', '正常网络'),
            'device': combination.get('device', 'Chrome浏览器'),
            'data_state': combination.get('data_state', '数据存在'),
            'expected_result': self._generate_expected_result(combination),
            'priority': '中',
            'complexity': '中等',
            'risk_level': '中',
            'execution_time': 5
        }
    
    def _generate_expected_result(self, combination: Dict[str, str]) -> str:
        """根据组合生成预期结果"""
        input_data = combination.get('input_data', '')
        user_state = combination.get('user_state', '')
        
        if '无效数据' in input_data:
            return '系统提示数据格式错误'
        elif '未登录' in user_state:
            return '系统提示需要登录'
        elif '边界数据' in input_data:
            return '系统正确处理边界情况'
        elif '空数据' in input_data:
            return '系统提示必填字段不能为空'
        else:
            return '操作成功完成'
    
    def _get_default_scenarios(self, module_name: str, testpoints: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """获取默认场景"""
        default_scenarios = []
        
        # 为每个测试点创建基本场景
        for i, tp in enumerate(testpoints):
            # 正常场景
            normal_scenario = {
                'id': f"{module_name}_scenario_{i*2+1:03d}",
                'name': f"{tp['name']}_正常场景",
                'module_name': module_name,
                'testpoint_id': tp['id'],
                'input_data': '有效数据',
                'user_state': '已登录',
                'system_state': '正常运行',
                'network': '正常网络',
                'device': 'Chrome浏览器',
                'data_state': '数据存在',
                'expected_result': '操作成功',
                'priority': tp['priority'],
                'complexity': '简单',
                'risk_level': '低',
                'execution_time': 3
            }
            
            # 异常场景
            exception_scenario = {
                'id': f"{module_name}_scenario_{i*2+2:03d}",
                'name': f"{tp['name']}_异常场景",
                'module_name': module_name,
                'testpoint_id': tp['id'],
                'input_data': '无效数据',
                'user_state': '已登录',
                'system_state': '正常运行',
                'network': '正常网络',
                'device': 'Chrome浏览器',
                'data_state': '数据存在',
                'expected_result': '系统提示错误信息',
                'priority': tp['priority'],
                'complexity': '中等',
                'risk_level': '中',
                'execution_time': 5
            }
            
            default_scenarios.extend([normal_scenario, exception_scenario])
        
        return default_scenarios
    
    def generate_scenario_summary(self, all_scenarios: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        """生成场景矩阵摘要"""
        total_scenarios = sum(len(scenarios) for scenarios in all_scenarios.values())
        
        # 统计各维度分布
        dimension_stats = {}
        for dimension in self.test_dimensions.keys():
            dimension_stats[dimension] = {}
        
        priority_stats = {'高': 0, '中': 0, '低': 0}
        complexity_stats = {'简单': 0, '中等': 0, '复杂': 0}
        risk_stats = {'高': 0, '中': 0, '低': 0}
        
        total_execution_time = 0
        
        for scenarios in all_scenarios.values():
            for scenario in scenarios:
                # 统计各维度
                for dimension in self.test_dimensions.keys():
                    value = scenario.get(dimension, '未知')
                    if value not in dimension_stats[dimension]:
                        dimension_stats[dimension][value] = 0
                    dimension_stats[dimension][value] += 1
                
                # 统计其他属性
                priority_stats[scenario.get('priority', '中')] += 1
                complexity_stats[scenario.get('complexity', '中等')] += 1
                risk_stats[scenario.get('risk_level', '中')] += 1
                total_execution_time += scenario.get('execution_time', 0)
        
        return {
            'total_modules': len(all_scenarios),
            'total_scenarios': total_scenarios,
            'average_scenarios_per_module': total_scenarios / max(len(all_scenarios), 1),
            'dimension_coverage': dimension_stats,
            'priority_distribution': priority_stats,
            'complexity_distribution': complexity_stats,
            'risk_distribution': risk_stats,
            'total_execution_time': total_execution_time,
            'average_execution_time': total_execution_time / max(total_scenarios, 1),
            'coverage_analysis': self._analyze_dimension_coverage(dimension_stats)
        }
    
    def _analyze_dimension_coverage(self, dimension_stats: Dict[str, Dict[str, int]]) -> Dict[str, Any]:
        """分析维度覆盖情况"""
        coverage_analysis = {
            'well_covered_dimensions': [],
            'poorly_covered_dimensions': [],
            'missing_values': {},
            'recommendations': []
        }
        
        for dimension, values in dimension_stats.items():
            expected_values = self.test_dimensions.get(dimension, [])
            covered_values = list(values.keys())
            
            coverage_rate = len(covered_values) / max(len(expected_values), 1)
            
            if coverage_rate >= 0.8:
                coverage_analysis['well_covered_dimensions'].append(dimension)
            elif coverage_rate < 0.5:
                coverage_analysis['poorly_covered_dimensions'].append(dimension)
            
            # 找出缺失的值
            missing = [v for v in expected_values if v not in covered_values]
            if missing:
                coverage_analysis['missing_values'][dimension] = missing
        
        # 生成建议
        if coverage_analysis['poorly_covered_dimensions']:
            coverage_analysis['recommendations'].append(
                f"以下维度覆盖不足，建议补充场景: {', '.join(coverage_analysis['poorly_covered_dimensions'])}"
            )
        
        if coverage_analysis['missing_values']:
            coverage_analysis['recommendations'].append(
                "建议补充缺失的测试条件以提高覆盖率"
            )
        
        return coverage_analysis
    
    def export_scenario_matrix(self, all_scenarios: Dict[str, List[Dict[str, Any]]]) -> str:
        """导出场景矩阵表格"""
        matrix_lines = []
        matrix_lines.append("# 测试场景矩阵")
        matrix_lines.append("")
        
        # 表头
        headers = [
            "场景ID", "场景名称", "模块", "输入数据", "用户状态", 
            "系统状态", "网络环境", "设备环境", "数据状态", "预期结果", "优先级"
        ]
        matrix_lines.append("| " + " | ".join(headers) + " |")
        matrix_lines.append("| " + " | ".join(["---"] * len(headers)) + " |")
        
        # 数据行
        for module_name, scenarios in all_scenarios.items():
            for scenario in scenarios:
                row = [
                    scenario['id'],
                    scenario['name'],
                    scenario['module_name'],
                    scenario['input_data'],
                    scenario['user_state'],
                    scenario['system_state'],
                    scenario['network'],
                    scenario['device'],
                    scenario['data_state'],
                    scenario['expected_result'],
                    scenario['priority']
                ]
                matrix_lines.append("| " + " | ".join(row) + " |")
        
        return "\n".join(matrix_lines)