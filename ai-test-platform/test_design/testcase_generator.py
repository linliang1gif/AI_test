#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
AI Test Platform - 测试用例生成器

根据测试场景矩阵生成详细的测试用例。
"""

import json
from typing import List, Dict, Any
from ai.ai_client import get_ai_client
from ai.prompt_library import PromptLibrary
from config.config import get_config

# 知识库（懒加载）
try:
    from knowledge.testcase_knowledge import TestCaseKnowledge
    _tc_knowledge = TestCaseKnowledge()
except Exception:
    _tc_knowledge = None

class TestCaseGenerator:
    """测试用例生成器"""

    def __init__(self):
        self.config = get_config()
        self.ai_client = get_ai_client()
        self.prompt_lib = PromptLibrary()
    
    def generate_testcases(self, modules: List[Dict[str, Any]], 
                          all_scenarios: Dict[str, List[Dict[str, Any]]]) -> Dict[str, List[Dict[str, Any]]]:
        """为所有模块生成测试用例"""
        all_testcases = {}
        
        for module in modules:
            module_name = module['name']
            scenarios = all_scenarios.get(module_name, [])
            
            try:
                module_testcases = self._generate_module_testcases(module, scenarios)
                all_testcases[module_name] = module_testcases
            except Exception as e:
                print(f"为模块 {module_name} 生成测试用例失败: {str(e)}")
                # 使用默认测试用例
                all_testcases[module_name] = self._get_default_testcases(module, scenarios)
        
        return all_testcases
    
    def _generate_module_testcases(self, module: Dict[str, Any], scenarios: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """为单个模块生成测试用例（RAG增强版）"""
        module_info = self._format_module_info(module)
        scenario_matrix = self._format_scenario_matrix(scenarios)

        # 1. 检索历史相似用例
        similar_cases = []
        if _tc_knowledge:
            try:
                similar_cases = _tc_knowledge.search_similar_cases(module['name'], top_k=5)
            except Exception as e:
                print(f"  ⚠️  知识库检索失败: {str(e)}")
                pass

        # 2. 将历史用例注入 prompt
        prompt = self.prompt_lib.get_testcase_generation_prompt(
            scenario_matrix, module_info, similar_cases=similar_cases
        )
        system_prompt = self.prompt_lib.get_system_prompt()

        response = self.ai_client.generate_json(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.3
        )

        testcases = response.get('testcases', [])
        validated_testcases = self._validate_testcases(testcases, module, scenarios)
        complete_testcases = self._ensure_testcase_quantity(validated_testcases, module, scenarios)

        # 3. 去重 + 入库
        if _tc_knowledge:
            try:
                unique_cases, dup_cases = _tc_knowledge.deduplicate(complete_testcases)
                _tc_knowledge.batch_save(unique_cases, source='ai_generated')
                print(f"  ✅ 知识库已保存 {len(unique_cases)} 个用例，去重 {len(dup_cases)} 个")
                return unique_cases
            except Exception as e:
                print(f"  ⚠️  知识库保存失败: {str(e)}")
                pass

        return complete_testcases
    
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
        
        return "\n".join(info_lines)
    
    def _format_scenario_matrix(self, scenarios: List[Dict[str, Any]]) -> str:
        """格式化场景矩阵信息"""
        if not scenarios:
            return "暂无测试场景"
        
        matrix_lines = []
        matrix_lines.append("测试场景矩阵:")
        
        for scenario in scenarios:
            matrix_lines.append(f"\n场景: {scenario['name']}")
            matrix_lines.append(f"  输入数据: {scenario['input_data']}")
            matrix_lines.append(f"  用户状态: {scenario['user_state']}")
            matrix_lines.append(f"  系统状态: {scenario['system_state']}")
            matrix_lines.append(f"  网络环境: {scenario['network']}")
            matrix_lines.append(f"  设备环境: {scenario['device']}")
            matrix_lines.append(f"  数据状态: {scenario['data_state']}")
            matrix_lines.append(f"  预期结果: {scenario['expected_result']}")
        
        return "\n".join(matrix_lines)
    
    def _validate_testcases(self, testcases: List[Dict[str, Any]], module: Dict[str, Any], scenarios: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """验证和补充测试用例信息"""
        validated_testcases = []
        
        for i, testcase in enumerate(testcases):
            validated_testcase = {
                'id': testcase.get('id', f"TC_{module['id']}_{i+1:03d}"),
                'title': testcase.get('title', f'测试用例{i+1}'),
                'module': module['name'],
                'testpoint': testcase.get('testpoint', ''),
                'scenario_id': self._match_scenario(testcase, scenarios),
                'precondition': testcase.get('precondition', '系统正常运行'),
                'steps': self._validate_steps(testcase.get('steps', [])),
                'test_data': testcase.get('test_data', ''),
                'expected_result': testcase.get('expected_result', '操作成功'),
                'priority': testcase.get('priority', '中'),
                'type': testcase.get('type', '功能测试'),
                'complexity': testcase.get('complexity', '中等'),
                'estimated_time': self._estimate_execution_time(testcase),
                'automation_feasible': self._assess_automation_feasibility(testcase),
                'risk_level': self._assess_testcase_risk(testcase),
                'tags': self._generate_tags(testcase, module)
            }
            
            # 验证标题
            if not validated_testcase['title'] or len(validated_testcase['title']) < 5:
                validated_testcase['title'] = f"验证{module['name']}功能{i+1}"
            
            # 验证步骤
            if not validated_testcase['steps']:
                validated_testcase['steps'] = [
                    "步骤1: 准备测试环境",
                    "步骤2: 执行测试操作", 
                    "步骤3: 验证测试结果"
                ]
            
            validated_testcases.append(validated_testcase)
        
        return validated_testcases
    
    def _validate_steps(self, steps: List[str]) -> List[str]:
        """验证测试步骤"""
        if not steps:
            return []
        
        validated_steps = []
        for i, step in enumerate(steps):
            if isinstance(step, str) and step.strip():
                # 确保步骤有编号
                step = step.strip()
                if not step.startswith(('步骤', 'Step', f'{i+1}.')):
                    step = f"步骤{i+1}: {step}"
                validated_steps.append(step)
        
        return validated_steps
    
    def _match_scenario(self, testcase: Dict[str, Any], scenarios: List[Dict[str, Any]]) -> str:
        """匹配对应的测试场景"""
        testcase_title = testcase.get('title', '').lower()
        
        # 尝试根据标题匹配场景
        for scenario in scenarios:
            scenario_name = scenario['name'].lower()
            if any(word in testcase_title for word in scenario_name.split()):
                return scenario['id']
        
        # 如果没有匹配到，返回第一个场景的ID
        return scenarios[0]['id'] if scenarios else ''
    
    def _estimate_execution_time(self, testcase: Dict[str, Any]) -> int:
        """估算执行时间（分钟）"""
        base_time = 5
        
        # 根据复杂度调整
        complexity = testcase.get('complexity', '中等')
        complexity_multiplier = {
            '简单': 0.8,
            '中等': 1.0,
            '复杂': 1.5
        }
        
        # 根据步骤数量调整
        steps = testcase.get('steps', [])
        step_multiplier = max(len(steps) / 3, 1.0)
        
        return int(base_time * complexity_multiplier.get(complexity, 1.0) * step_multiplier)
    
    def _assess_automation_feasibility(self, testcase: Dict[str, Any]) -> Dict[str, Any]:
        """评估自动化可行性"""
        title = testcase.get('title', '').lower()
        steps = ' '.join(testcase.get('steps', [])).lower()
        test_type = testcase.get('type', '').lower()
        
        # 自动化友好的特征
        automation_friendly = [
            'api', '接口', 'login', '登录', 'register', '注册',
            'create', '创建', 'update', '更新', 'delete', '删除',
            'query', '查询', 'search', '搜索'
        ]
        
        # 自动化困难的特征
        automation_difficult = [
            'ui', '界面', 'visual', '视觉', 'manual', '手动',
            'user experience', '用户体验', 'usability', '易用性'
        ]
        
        text = f"{title} {steps} {test_type}"
        
        friendly_score = sum(1 for keyword in automation_friendly if keyword in text)
        difficult_score = sum(1 for keyword in automation_difficult if keyword in text)
        
        if friendly_score > difficult_score and '接口' in text:
            feasibility = '高'
            recommendation = '建议优先自动化'
        elif friendly_score > 0:
            feasibility = '中'
            recommendation = '可以考虑自动化'
        else:
            feasibility = '低'
            recommendation = '建议手动测试'
        
        return {
            'feasibility': feasibility,
            'score': friendly_score - difficult_score,
            'recommendation': recommendation
        }
    
    def _assess_testcase_risk(self, testcase: Dict[str, Any]) -> str:
        """评估测试用例风险等级"""
        priority = testcase.get('priority', '中')
        complexity = testcase.get('complexity', '中等')
        test_type = testcase.get('type', '').lower()
        
        risk_score = 0
        
        # 优先级影响
        priority_scores = {'高': 3, '中': 2, '低': 1}
        risk_score += priority_scores.get(priority, 2)
        
        # 复杂度影响
        complexity_scores = {'复杂': 3, '中等': 2, '简单': 1}
        risk_score += complexity_scores.get(complexity, 2)
        
        # 测试类型影响
        high_risk_types = ['安全', '性能', '集成', 'security', 'performance', 'integration']
        if any(risk_type in test_type for risk_type in high_risk_types):
            risk_score += 2
        
        # 确定风险等级
        if risk_score >= 7:
            return '高'
        elif risk_score >= 4:
            return '中'
        else:
            return '低'
    
    def _generate_tags(self, testcase: Dict[str, Any], module: Dict[str, Any]) -> List[str]:
        """生成测试用例标签"""
        tags = []
        
        # 模块标签
        tags.append(module['name'])
        
        # 优先级标签
        priority = testcase.get('priority', '中')
        priority_num = {'高': '1', '中': '2', '低': '3'}.get(priority, '2')
        tags.append(f"P{priority_num}")
        
        # 类型标签
        test_type = testcase.get('type', '功能测试')
        tags.append(test_type)
        
        # 自动化标签
        automation = self._assess_automation_feasibility(testcase)
        if automation['feasibility'] == '高':
            tags.append('可自动化')
        
        # 风险标签
        risk = self._assess_testcase_risk(testcase)
        if risk == '高':
            tags.append('高风险')
        
        return tags
    
    def _ensure_testcase_quantity(self, testcases: List[Dict[str, Any]], module: Dict[str, Any], scenarios: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """确保测试用例数量充足"""
        target_count = max(100, len(scenarios) * 5)  # 每个模块至少100个用例，每个场景至少5个用例

        if len(testcases) >= target_count:
            return testcases

        # 补充测试用例
        additional_count = target_count - len(testcases)
        additional_testcases = self._generate_additional_testcases(
            module, scenarios, additional_count, len(testcases)
        )

        return testcases + additional_testcases
    
    def _generate_additional_testcases(self, module: Dict[str, Any], scenarios: List[Dict[str, Any]], count: int, start_index: int) -> List[Dict[str, Any]]:
        """生成额外的测试用例"""
        additional_testcases = []
        
        # 测试用例模板
        testcase_templates = [
            {
                'title_template': '验证{module}的{function}功能正常工作',
                'type': '功能测试',
                'priority': '高'
            },
            {
                'title_template': '验证{module}的{function}边界条件处理',
                'type': '边界测试',
                'priority': '中'
            },
            {
                'title_template': '验证{module}的{function}异常处理',
                'type': '异常测试',
                'priority': '中'
            },
            {
                'title_template': '验证{module}的{function}权限控制',
                'type': '权限测试',
                'priority': '高'
            },
            {
                'title_template': '验证{module}的{function}性能表现',
                'type': '性能测试',
                'priority': '低'
            }
        ]
        
        functions = module.get('functions', [module['name']])
        
        for i in range(count):
            template = testcase_templates[i % len(testcase_templates)]
            function = functions[i % len(functions)]
            
            testcase = {
                'id': f"TC_{module['id']}_{start_index + i + 1:03d}",
                'title': template['title_template'].format(
                    module=module['name'], 
                    function=function
                ),
                'module': module['name'],
                'testpoint': f"{function}测试点",
                'scenario_id': scenarios[i % len(scenarios)]['id'] if scenarios else '',
                'precondition': f"系统正常运行，用户已登录，{function}功能可用",
                'steps': [
                    f"步骤1: 准备{function}测试数据",
                    f"步骤2: 执行{function}操作",
                    f"步骤3: 验证{function}结果",
                    "步骤4: 清理测试数据"
                ],
                'test_data': f"{function}相关的测试数据",
                'expected_result': f"{function}操作成功完成，结果符合预期",
                'priority': template['priority'],
                'type': template['type'],
                'complexity': '中等',
                'estimated_time': 5,
                'automation_feasible': {'feasibility': '中', 'score': 0, 'recommendation': '可以考虑自动化'},
                'risk_level': '中',
                'tags': [module['name'], template['type'], "P" + {'高': '1', '中': '2', '低': '3'}.get(template['priority'], '2')]
            }
            
            additional_testcases.append(testcase)
        
        return additional_testcases
    
    def _get_default_testcases(self, module: Dict[str, Any], scenarios: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """获取默认测试用例"""
        return self._generate_additional_testcases(module, scenarios, 100, 0)
    
    def generate_testcase_summary(self, all_testcases: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        """生成测试用例摘要"""
        total_testcases = sum(len(testcases) for testcases in all_testcases.values())
        
        # 统计分布
        type_stats = {}
        priority_stats = {'高': 0, '中': 0, '低': 0}
        complexity_stats = {'简单': 0, '中等': 0, '复杂': 0}
        risk_stats = {'高': 0, '中': 0, '低': 0}
        automation_stats = {'高': 0, '中': 0, '低': 0}
        
        total_execution_time = 0
        
        for testcases in all_testcases.values():
            for tc in testcases:
                # 统计类型
                test_type = tc.get('type', '其他')
                type_stats[test_type] = type_stats.get(test_type, 0) + 1
                
                # 统计其他属性
                priority_stats[tc.get('priority', '中')] += 1
                complexity_stats[tc.get('complexity', '中等')] += 1
                risk_stats[tc.get('risk_level', '中')] += 1
                
                automation = tc.get('automation_feasible', {})
                automation_stats[automation.get('feasibility', '中')] += 1
                
                total_execution_time += tc.get('estimated_time', 0)
        
        return {
            'total_modules': len(all_testcases),
            'total_testcases': total_testcases,
            'average_testcases_per_module': total_testcases / max(len(all_testcases), 1),
            'type_distribution': type_stats,
            'priority_distribution': priority_stats,
            'complexity_distribution': complexity_stats,
            'risk_distribution': risk_stats,
            'automation_distribution': automation_stats,
            'total_execution_time': total_execution_time,
            'average_execution_time': total_execution_time / max(total_testcases, 1),
            'automation_rate': (automation_stats.get('高', 0) + automation_stats.get('中', 0)) / max(total_testcases, 1) * 100
        }
    
    def export_testcases_excel_format(self, all_testcases: Dict[str, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """导出Excel格式的测试用例"""
        excel_testcases = []
        
        for module_name, testcases in all_testcases.items():
            for tc in testcases:
                excel_testcase = {
                    '序号': tc['id'],
                    '模块名称': tc['module'],
                    '测试点': tc['testpoint'],
                    '用例标题': tc['title'],
                    '前置条件': tc['precondition'],
                    '测试步骤': '\n'.join(tc['steps']),
                    '测试数据': tc['test_data'],
                    '预期结果': tc['expected_result'],
                    '优先级': tc['priority'],
                    '测试类型': tc['type'],
                    '复杂度': tc['complexity'],
                    '预估时间': f"{tc['estimated_time']}分钟",
                    '自动化可行性': tc['automation_feasible']['feasibility'],
                    '风险等级': tc['risk_level'],
                    '标签': ', '.join(tc['tags'])
                }
                excel_testcases.append(excel_testcase)
        
        return excel_testcases