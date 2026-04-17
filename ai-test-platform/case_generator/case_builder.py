#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Case Builder - 用例构建器
基于场景生成详细的测试用例
"""

import sys
from typing import List, Dict, Any
from pathlib import Path
from utils.knowledge_prompt_helper import get_knowledge_helper

# V4增强：引入决策级RAG
try:
    from knowledge.decision_rag import get_decision_rag
    _decision_rag_available = True
except ImportError:
    _decision_rag_available = False
    print("⚠️  决策级RAG未找到，将不使用知识库增强")

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent.parent))

try:
    from test_design.testcase_generator import TestCaseGenerator
    _generator_available = True
except ImportError:
    _generator_available = False


class CaseBuilder:
    """用例构建器 - V4增强版（决策级RAG支持）"""
    
    def __init__(self):
        self.helper = get_knowledge_helper()
        if _generator_available:
            self.testcase_generator = TestCaseGenerator()
        else:
            self.testcase_generator = None
        
        # V4增强：初始化决策级RAG
        if _decision_rag_available:
            self.decision_rag = get_decision_rag()
            print("✅ 决策级RAG已加载到Case Builder")
        else:
            self.decision_rag = None
    
    def build_cases(
        self, 
        module_info: Dict[str, Any], 
        scenarios: List[Dict[str, Any]], 
        target_count: int,
        priority: str
    ) -> List[Dict[str, Any]]:
        """
        构建测试用例
        V4增强：使用决策级RAG基于真实API生成用例
        
        Args:
            module_info: 模块信息
            scenarios: 场景列表
            target_count: 目标用例数量
            priority: 优先级（P0/P1/P2）
            
        Returns:
            测试用例列表
        """
        module_name = module_info.get('name', '未知模块')
        
        # ==================== V4增强：使用决策级RAG ====================
        knowledge = None
        if self.decision_rag:
            try:
                print(f"🧠 V4增强：检索用例生成知识...")
                knowledge = self.decision_rag.retrieve_knowledge_v2(
                    query=module_name,
                    context_type="case_generation",
                    max_tokens=2000
                )
                print(f"✅ 知识检索完成:")
                print(f"   - APIs: {len(knowledge.get('apis', []))}")
                print(f"   - 模块: {knowledge.get('modules', [])}")
                print(f"   - 优先级: {knowledge.get('priority')}")
                print(f"   - 风险: {knowledge.get('risk_level')}")
            except Exception as e:
                print(f"⚠️  知识检索失败: {e}，使用简化模式")
                knowledge = None
        
        # 基于知识库生成用例
        if knowledge and not knowledge.get('fallback', False):
            testcases = self._build_knowledge_enhanced_cases(
                module_info, scenarios, target_count, priority, knowledge
            )
            print(f"✅ 基于知识库生成了{len(testcases)}个用例")
        else:
            # 降级：使用简化模式
            testcases = self._build_simple_cases(module_info, scenarios, target_count, priority)
            print(f"⚠️  使用简化模式生成了{len(testcases)}个用例")
        
        return testcases
    
    def _build_knowledge_enhanced_cases(
        self,
        module_info: Dict[str, Any],
        scenarios: List[Dict[str, Any]],
        target_count: int,
        priority: str,
        knowledge: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        基于知识库生成增强的测试用例
        
        Args:
            module_info: 模块信息
            scenarios: 场景列表
            target_count: 目标用例数量
            priority: 优先级
            knowledge: 知识库检索结果
            
        Returns:
            测试用例列表
        """
        module_name = module_info.get('name', '未知模块')
        apis = knowledge.get('apis', [])
        kb_priority = knowledge.get('priority', priority)
        kb_risk = knowledge.get('risk_level', 'low')
        
        # 风险等级映射
        risk_map = {'high': '高', 'medium': '中', 'low': '低'}
        risk_level = risk_map.get(kb_risk, '中')
        
        testcases = []
        
        # 为每个API生成测试用例
        for i, api in enumerate(apis[:target_count], 1):
            method = api.get('method', 'GET')
            path = api.get('path', '/unknown')
            summary = api.get('summary', path)
            
            # 根据优先级决定用例类型
            case_types = self._get_case_types_by_priority(kb_priority)
            
            for type_idx, case_type in enumerate(case_types):
                if len(testcases) >= target_count:
                    break
                
                testcase = {
                    'id': f"TC_{module_name}_{i:03d}_{type_idx+1}",
                    'title': f"测试{summary}_{case_type}",
                    'module': module_name,
                    'testpoint': f"{summary}测试点",
                    'scenario_id': scenarios[0]['id'] if scenarios else '',
                    'api': {
                        'method': method,
                        'path': path,
                        'summary': summary
                    },
                    'precondition': f"系统正常运行，用户已登录，{method} {path}接口可用",
                    'steps': [
                        f"步骤1: 准备{case_type}测试数据",
                        f"步骤2: 调用接口 {method} {path}",
                        f"步骤3: 验证HTTP状态码",
                        f"步骤4: 验证返回数据格式",
                        f"步骤5: 验证业务逻辑正确性",
                        "步骤6: 清理测试数据"
                    ],
                    'test_data': self._generate_api_test_data(method, case_type),
                    'expected_result': self._generate_api_expected_result(method, case_type),
                    'priority': self._map_priority(kb_priority),
                    'type': self._map_case_type(case_type),
                    'complexity': '中等',
                    'estimated_time': 5,
                    'automation_feasible': {'feasibility': '高', 'score': 1, 'recommendation': '建议自动化'},
                    'risk_level': risk_level,
                    'tags': [module_name, case_type, kb_priority, method],
                    'knowledge_enhanced': True,  # 标记为知识库增强
                    'knowledge_info': {
                        'api_similarity': api.get('similarity', 0),
                        'kb_priority': kb_priority,
                        'kb_risk': kb_risk
                    }
                }
                
                testcases.append(testcase)
            
            if len(testcases) >= target_count:
                break
        
        return testcases
    
    def _generate_api_test_data(self, method: str, case_type: str) -> str:
        """生成API测试数据"""
        if case_type == '正常':
            if method in ['POST', 'PUT', 'PATCH']:
                return '有效的JSON请求体，包含所有必需字段'
            elif method == 'GET':
                return '有效的查询参数'
            elif method == 'DELETE':
                return '有效的资源ID'
        elif case_type == '异常':
            if method in ['POST', 'PUT', 'PATCH']:
                return '无效的JSON请求体，缺少必需字段或字段类型错误'
            elif method == 'GET':
                return '无效的查询参数'
            elif method == 'DELETE':
                return '不存在的资源ID'
        elif case_type == '边界':
            return '边界值数据：空值、最大值、最小值、特殊字符'
        
        return '测试数据'
    
    def _generate_api_expected_result(self, method: str, case_type: str) -> str:
        """生成API预期结果"""
        if case_type == '正常':
            if method in ['POST', 'PUT', 'PATCH']:
                return 'HTTP 200/201，返回成功消息和数据'
            elif method == 'GET':
                return 'HTTP 200，返回正确的数据列表或详情'
            elif method == 'DELETE':
                return 'HTTP 200/204，资源删除成功'
        elif case_type == '异常':
            return 'HTTP 400/404/500，返回错误消息'
        elif case_type == '边界':
            return '系统正确处理边界情况，返回合理的响应'
        
        return '符合预期'
    
    def _filter_by_priority(self, testcases: List[Dict[str, Any]], priority: str) -> List[Dict[str, Any]]:
        """
        根据优先级过滤用例
        
        规则：
        - P0: 正常 + 异常 + 边界
        - P1: 正常 + 异常
        - P2: 只正常
        """
        if priority == "P0":
            # 保留所有类型
            return testcases
        elif priority == "P1":
            # 保留正常和异常
            return [tc for tc in testcases if tc.get('type', '') in ['功能测试', '异常测试', '接口测试']]
        else:  # P2
            # 只保留正常功能测试
            return [tc for tc in testcases if tc.get('type', '') == '功能测试']
    
    def _trim_to_target(self, testcases: List[Dict[str, Any]], target_count: int) -> List[Dict[str, Any]]:
        """裁剪到目标数量"""
        if len(testcases) <= target_count:
            return testcases
        
        # 按优先级和风险排序
        sorted_cases = sorted(
            testcases,
            key=lambda tc: (
                {'高': 0, '中': 1, '低': 2}.get(tc.get('priority', '中'), 1),
                {'高': 0, '中': 1, '低': 2}.get(tc.get('risk_level', '中'), 1)
            )
        )
        
        return sorted_cases[:target_count]
    
    def _build_simple_cases(
        self, 
        module_info: Dict[str, Any], 
        scenarios: List[Dict[str, Any]], 
        target_count: int,
        priority: str
    ) -> List[Dict[str, Any]]:
        """简化的用例构建（降级方案）"""
        module_name = module_info.get('name', '未知模块')
        functions = module_info.get('functions', ['基础功能'])
        
        testcases = []
        
        # 根据优先级决定用例类型
        case_types = self._get_case_types_by_priority(priority)
        
        # 为每个功能生成用例
        for func_idx, func in enumerate(functions):
            for type_idx, case_type in enumerate(case_types):
                if len(testcases) >= target_count:
                    break
                
                testcase = {
                    'id': f"TC_{func_idx+1:02d}_{type_idx+1:02d}",
                    'title': f"验证{func}_{case_type}",
                    'module': module_name,
                    'testpoint': f"{func}测试点",
                    'scenario_id': scenarios[0]['id'] if scenarios else '',
                    'precondition': f"系统正常运行，用户已登录",
                    'steps': [
                        f"步骤1: 准备{case_type}测试数据",
                        f"步骤2: 执行{func}操作",
                        f"步骤3: 验证结果",
                        "步骤4: 清理测试数据"
                    ],
                    'test_data': self._generate_test_data(case_type),
                    'expected_result': self._generate_expected_result(case_type),
                    'priority': self._map_priority(priority),
                    'type': self._map_case_type(case_type),
                    'complexity': '中等',
                    'estimated_time': 5,
                    'automation_feasible': {'feasibility': '高', 'score': 1, 'recommendation': '建议自动化'},
                    'risk_level': '中',
                    'tags': [module_name, case_type, priority]
                }
                
                testcases.append(testcase)
            
            if len(testcases) >= target_count:
                break
        
        return testcases
    
    def _get_case_types_by_priority(self, priority: str) -> List[str]:
        """根据优先级获取用例类型"""
        if priority == "P0":
            return ['正常', '异常', '边界']
        elif priority == "P1":
            return ['正常', '异常']
        else:  # P2
            return ['正常']
    
    def _generate_test_data(self, case_type: str) -> str:
        """生成测试数据"""
        if case_type == '正常':
            return '有效的测试数据'
        elif case_type == '异常':
            return '无效的测试数据'
        elif case_type == '边界':
            return '边界值测试数据'
        else:
            return '测试数据'
    
    def _generate_expected_result(self, case_type: str) -> str:
        """生成预期结果"""
        if case_type == '正常':
            return '操作成功，返回正确结果'
        elif case_type == '异常':
            return '系统提示错误信息，操作失败'
        elif case_type == '边界':
            return '系统正确处理边界情况'
        else:
            return '符合预期'
    
    def _map_priority(self, priority: str) -> str:
        """映射优先级"""
        mapping = {
            'P0': '高',
            'P1': '中',
            'P2': '低'
        }
        return mapping.get(priority, '中')
    
    def _map_case_type(self, case_type: str) -> str:
        """映射用例类型"""
        mapping = {
            '正常': '功能测试',
            '异常': '异常测试',
            '边界': '边界测试'
        }
        return mapping.get(case_type, '功能测试')
