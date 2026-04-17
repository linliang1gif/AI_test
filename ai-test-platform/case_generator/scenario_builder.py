#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Scenario Builder - 场景构建器
基于测试点生成测试场景
"""

import sys
from typing import List, Dict, Any
from pathlib import Path
from utils.knowledge_prompt_helper import get_knowledge_helper

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent.parent))

try:
    from test_design.testpoint_generator import TestPointGenerator
    from test_design.scenario_matrix_generator import ScenarioMatrixGenerator
    _generators_available = True
except ImportError:
    _generators_available = False


class ScenarioBuilder:
    """场景构建器"""
    
    def __init__(self):
        self.helper = get_knowledge_helper()
        if _generators_available:
            self.testpoint_generator = TestPointGenerator()
            self.scenario_generator = ScenarioMatrixGenerator()
        else:
            self.testpoint_generator = None
            self.scenario_generator = None
    
    def build_scenarios(self, module_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        为模块构建测试场景
        
        Args:
            module_info: 模块信息（来自 Agent 的 parsed_modules）
            
        Returns:
            {
                "testpoints": [测试点列表],
                "scenarios": [场景列表]
            }
        """
        # 直接使用简化模式,避免调用传统组件的 AI（会很慢）
        return self._build_simple_scenarios(module_info)
    
    def _generate_testpoints(self, module_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """生成测试点"""
        # 调用传统流程的测试点生成器
        all_testpoints = self.testpoint_generator.generate_testpoints([module_info])
        
        # 提取当前模块的测试点
        module_name = module_info['name']
        return all_testpoints.get(module_name, [])
    
    def _generate_scenarios(self, module_name: str, testpoints: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """生成场景矩阵"""
        # 调用传统流程的场景矩阵生成器
        all_scenarios = self.scenario_generator.generate_scenario_matrix({
            module_name: testpoints
        })
        
        # 提取当前模块的场景
        return all_scenarios.get(module_name, [])
    
    def _build_simple_scenarios(self, module_info: Dict[str, Any]) -> Dict[str, Any]:
        """简化的场景构建（降级方案）"""
        module_name = module_info.get('name', '未知模块')
        functions = module_info.get('functions', ['基础功能'])
        
        testpoints = []
        scenarios = []
        
        # 为每个功能创建测试点和场景
        for i, func in enumerate(functions):
            # 测试点
            testpoint = {
                'id': f"tp_{i+1:03d}",
                'module_name': module_name,
                'category': '功能测试',
                'name': f"{func}测试",
                'description': f"验证{func}功能",
                'priority': '中',
                'complexity': '中等',
                'test_type': ['功能测试'],
                'estimated_cases': 3,
                'risk_level': '中'
            }
            testpoints.append(testpoint)
            
            # 正常场景
            scenarios.append({
                'id': f"sc_{i*2+1:03d}",
                'name': f"{func}_正常场景",
                'module_name': module_name,
                'testpoint_id': testpoint['id'],
                'input_data': '有效数据',
                'user_state': '已登录',
                'system_state': '正常运行',
                'network': '正常网络',
                'device': 'Chrome浏览器',
                'data_state': '数据存在',
                'expected_result': '操作成功',
                'priority': '中',
                'complexity': '简单',
                'risk_level': '低',
                'execution_time': 3
            })
            
            # 异常场景
            scenarios.append({
                'id': f"sc_{i*2+2:03d}",
                'name': f"{func}_异常场景",
                'module_name': module_name,
                'testpoint_id': testpoint['id'],
                'input_data': '无效数据',
                'user_state': '已登录',
                'system_state': '正常运行',
                'network': '正常网络',
                'device': 'Chrome浏览器',
                'data_state': '数据存在',
                'expected_result': '系统提示错误',
                'priority': '中',
                'complexity': '中等',
                'risk_level': '中',
                'execution_time': 5
            })
        
        return {
            "testpoints": testpoints,
            "scenarios": scenarios
        }
