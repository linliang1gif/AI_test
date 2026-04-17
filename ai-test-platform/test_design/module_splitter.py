#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
AI Test Platform - 模块拆分器

根据需求文档，使用AI智能拆分系统功能模块。
"""

import json
from typing import List, Dict, Any
from ai.ai_client import get_ai_client
from ai.prompt_library import PromptLibrary
from config.config import get_config

class ModuleSplitter:
    """功能模块拆分器"""
    
    def __init__(self):
        self.config = get_config()
        self.ai_client = get_ai_client()
        self.prompt_lib = PromptLibrary()
    
    def split_modules(self, requirement: str) -> List[Dict[str, Any]]:
        """拆分功能模块"""
        try:
            # 生成模块拆分prompt
            prompt = self.prompt_lib.get_module_split_prompt(requirement)
            system_prompt = self.prompt_lib.get_system_prompt()
            
            # 调用AI生成模块拆分
            response = self.ai_client.generate_json(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=0.3
            )
            
            modules = response.get('modules', [])
            
            # 验证和补充模块信息
            validated_modules = self._validate_modules(modules)
            
            # 分析模块依赖关系
            modules_with_deps = self._analyze_dependencies(validated_modules)
            
            return modules_with_deps
            
        except Exception as e:
            print(f"模块拆分失败: {str(e)}")
            # 返回默认模块结构
            return self._get_default_modules()
    
    def _validate_modules(self, modules: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """验证和补充模块信息"""
        validated_modules = []
        
        for i, module in enumerate(modules):
            # 确保必要字段存在
            validated_module = {
                'id': f"module_{i+1:03d}",
                'name': module.get('name', f'模块{i+1}'),
                'description': module.get('description', ''),
                'functions': module.get('functions', []),
                'dependencies': module.get('dependencies', []),
                'priority': module.get('priority', '中'),
                'complexity': self._assess_complexity(module),
                'test_priority': self._assess_test_priority(module),
                'estimated_effort': self._estimate_effort(module)
            }
            
            # 验证模块名称
            if not validated_module['name'] or len(validated_module['name']) < 2:
                validated_module['name'] = f'功能模块{i+1}'
            
            # 验证功能列表
            if not validated_module['functions']:
                validated_module['functions'] = [f"{validated_module['name']}基础功能"]
            
            validated_modules.append(validated_module)
        
        return validated_modules
    
    def _assess_complexity(self, module: Dict[str, Any]) -> str:
        """评估模块复杂度"""
        functions = module.get('functions', [])
        dependencies = module.get('dependencies', [])
        
        # 基于功能数量和依赖关系评估复杂度
        function_count = len(functions)
        dependency_count = len(dependencies)
        
        if function_count <= 2 and dependency_count <= 1:
            return '简单'
        elif function_count <= 5 and dependency_count <= 3:
            return '中等'
        else:
            return '复杂'
    
    def _assess_test_priority(self, module: Dict[str, Any]) -> str:
        """评估测试优先级"""
        priority = module.get('priority', '中')
        complexity = self._assess_complexity(module)
        
        # 综合业务优先级和复杂度确定测试优先级
        if priority == '高' or complexity == '复杂':
            return '高'
        elif priority == '低' and complexity == '简单':
            return '低'
        else:
            return '中'
    
    def _estimate_effort(self, module: Dict[str, Any]) -> Dict[str, int]:
        """估算工作量"""
        functions = module.get('functions', [])
        complexity = self._assess_complexity(module)
        
        # 基础工作量
        base_effort = len(functions) * 2
        
        # 复杂度调整
        complexity_multiplier = {
            '简单': 1.0,
            '中等': 1.5,
            '复杂': 2.0
        }
        
        multiplier = complexity_multiplier.get(complexity, 1.0)
        
        return {
            'design_hours': int(base_effort * multiplier),
            'development_hours': int(base_effort * multiplier * 3),
            'testing_hours': int(base_effort * multiplier * 2)
        }
    
    def _analyze_dependencies(self, modules: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """分析模块依赖关系"""
        module_names = [module['name'] for module in modules]
        
        for module in modules:
            # 清理依赖关系，确保依赖的模块存在
            valid_dependencies = []
            for dep in module.get('dependencies', []):
                if dep in module_names and dep != module['name']:
                    valid_dependencies.append(dep)
            
            module['dependencies'] = valid_dependencies
            
            # 添加被依赖信息
            module['dependents'] = []
            for other_module in modules:
                if module['name'] in other_module.get('dependencies', []):
                    module['dependents'].append(other_module['name'])
        
        return modules
    
    def _get_default_modules(self) -> List[Dict[str, Any]]:
        """获取默认模块结构"""
        return [
            {
                'id': 'module_001',
                'name': '用户管理模块',
                'description': '负责用户注册、登录、信息管理等功能',
                'functions': ['用户注册', '用户登录', '用户信息管理', '密码管理'],
                'dependencies': [],
                'priority': '高',
                'complexity': '中等',
                'test_priority': '高',
                'estimated_effort': {
                    'design_hours': 12,
                    'development_hours': 36,
                    'testing_hours': 24
                },
                'dependents': []
            },
            {
                'id': 'module_002',
                'name': '权限管理模块',
                'description': '负责用户权限控制和访问管理',
                'functions': ['角色管理', '权限分配', '访问控制'],
                'dependencies': ['用户管理模块'],
                'priority': '高',
                'complexity': '复杂',
                'test_priority': '高',
                'estimated_effort': {
                    'design_hours': 16,
                    'development_hours': 48,
                    'testing_hours': 32
                },
                'dependents': []
            },
            {
                'id': 'module_003',
                'name': '数据管理模块',
                'description': '负责数据的增删改查和数据处理',
                'functions': ['数据录入', '数据查询', '数据导出', '数据统计'],
                'dependencies': ['用户管理模块', '权限管理模块'],
                'priority': '中',
                'complexity': '中等',
                'test_priority': '中',
                'estimated_effort': {
                    'design_hours': 10,
                    'development_hours': 30,
                    'testing_hours': 20
                },
                'dependents': []
            }
        ]
    
    def generate_module_summary(self, modules: List[Dict[str, Any]]) -> Dict[str, Any]:
        """生成模块摘要信息"""
        total_modules = len(modules)
        
        # 统计优先级分布
        priority_stats = {'高': 0, '中': 0, '低': 0}
        complexity_stats = {'简单': 0, '中等': 0, '复杂': 0}
        
        total_effort = {
            'design_hours': 0,
            'development_hours': 0,
            'testing_hours': 0
        }
        
        for module in modules:
            priority_stats[module.get('priority', '中')] += 1
            complexity_stats[module.get('complexity', '中等')] += 1
            
            effort = module.get('estimated_effort', {})
            for key in total_effort:
                total_effort[key] += effort.get(key, 0)
        
        return {
            'total_modules': total_modules,
            'priority_distribution': priority_stats,
            'complexity_distribution': complexity_stats,
            'total_estimated_effort': total_effort,
            'average_functions_per_module': sum(len(m.get('functions', [])) for m in modules) / max(total_modules, 1),
            'modules_with_dependencies': sum(1 for m in modules if m.get('dependencies')),
            'dependency_complexity': self._calculate_dependency_complexity(modules)
        }
    
    def _calculate_dependency_complexity(self, modules: List[Dict[str, Any]]) -> str:
        """计算依赖复杂度"""
        total_dependencies = sum(len(m.get('dependencies', [])) for m in modules)
        
        if total_dependencies == 0:
            return '无依赖'
        elif total_dependencies <= len(modules):
            return '简单'
        elif total_dependencies <= len(modules) * 2:
            return '中等'
        else:
            return '复杂'
    
    def export_module_diagram(self, modules: List[Dict[str, Any]]) -> str:
        """导出模块关系图（文本格式）"""
        diagram_lines = []
        diagram_lines.append("# 系统模块关系图")
        diagram_lines.append("")
        
        # 模块列表
        diagram_lines.append("## 模块列表")
        for module in modules:
            diagram_lines.append(f"- **{module['name']}** ({module['priority']}优先级, {module['complexity']}复杂度)")
            diagram_lines.append(f"  - 功能: {', '.join(module.get('functions', []))}")
            if module.get('dependencies'):
                diagram_lines.append(f"  - 依赖: {', '.join(module['dependencies'])}")
            diagram_lines.append("")
        
        # 依赖关系
        diagram_lines.append("## 依赖关系")
        for module in modules:
            if module.get('dependencies'):
                for dep in module['dependencies']:
                    diagram_lines.append(f"{dep} --> {module['name']}")
        
        return "\n".join(diagram_lines)
    
    def validate_module_structure(self, modules: List[Dict[str, Any]]) -> Dict[str, Any]:
        """验证模块结构的合理性"""
        validation_result = {
            'is_valid': True,
            'warnings': [],
            'suggestions': []
        }
        
        # 检查模块数量
        if len(modules) < 2:
            validation_result['warnings'].append("模块数量过少，建议至少拆分为2个模块")
        elif len(modules) > 10:
            validation_result['warnings'].append("模块数量过多，可能导致管理复杂")
        
        # 检查循环依赖
        circular_deps = self._detect_circular_dependencies(modules)
        if circular_deps:
            validation_result['warnings'].append(f"检测到循环依赖: {circular_deps}")
        
        # 检查孤立模块
        isolated_modules = [m['name'] for m in modules 
                          if not m.get('dependencies') and not m.get('dependents')]
        if len(isolated_modules) > len(modules) * 0.5:
            validation_result['suggestions'].append("存在较多孤立模块，建议检查模块间的关联性")
        
        return validation_result
    
    def _detect_circular_dependencies(self, modules: List[Dict[str, Any]]) -> List[str]:
        """检测循环依赖"""
        # 简单的循环依赖检测
        module_deps = {m['name']: m.get('dependencies', []) for m in modules}
        
        def has_path(start, end, visited=None):
            if visited is None:
                visited = set()
            
            if start == end:
                return True
            
            if start in visited:
                return False
            
            visited.add(start)
            
            for dep in module_deps.get(start, []):
                if has_path(dep, end, visited.copy()):
                    return True
            
            return False
        
        circular_deps = []
        for module_name in module_deps:
            for dep in module_deps.get(module_name, []):
                if has_path(dep, module_name):
                    circular_deps.append(f"{module_name} <-> {dep}")
        
        return list(set(circular_deps))