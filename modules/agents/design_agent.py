#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DesignAgent - 测试设计代理

职责：
- 生成测试点
- 生成测试用例
- 决定测试范围（哪些接口要测）
- 决定测试类型（API/UI/边界/异常）
- 控制测试用例数量（避免全量生成）

输入：
- Swagger / 需求文档 / Discovery结果

输出：
- List[TestCase]
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path

# 导入核心模型
try:
    from core import TestCase, TestCasePriority, create_test_case
    CORE_AVAILABLE = True
except ImportError:
    CORE_AVAILABLE = False
    logging.warning("Core models not available, using dict format")


class DesignAgent:
    """
    测试设计代理
    
    专注于测试用例的设计和生成，不涉及执行逻辑
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        初始化设计代理
        
        Args:
            config: 配置字典
                - max_testcases_per_api: 每个API最大测试用例数（默认5）
                - include_edge_cases: 是否包含边界测试（默认True）
                - include_error_cases: 是否包含异常测试（默认True）
                - priority_threshold: 优先级阈值（默认medium）
        """
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # 配置参数
        self.max_testcases_per_api = self.config.get('max_testcases_per_api', 5)
        self.include_edge_cases = self.config.get('include_edge_cases', True)
        self.include_error_cases = self.config.get('include_error_cases', True)
        self.priority_threshold = self.config.get('priority_threshold', 'medium')
        
        # 设计历史
        self.design_history = []
        
        self.logger.info(f"DesignAgent initialized with config: {self.config}")
    
    def design_from_swagger(
        self,
        swagger_file: str,
        filters: Optional[Dict] = None
    ) -> List[Any]:
        """
        从 Swagger 文件设计测试用例
        
        Args:
            swagger_file: Swagger 文件路径
            filters: 过滤条件
                - paths: 只测试指定的路径列表
                - methods: 只测试指定的方法列表
                - tags: 只测试指定的标签列表
                
        Returns:
            测试用例列表
        """
        self.logger.info(f"Designing tests from Swagger: {swagger_file}")
        
        filters = filters or {}
        testcases = []
        
        try:
            # 1. 解析 Swagger
            swagger_data = self._parse_swagger(swagger_file)
            
            # 2. 确定测试范围
            apis_to_test = self._determine_test_scope(swagger_data, filters)
            self.logger.info(f"Selected {len(apis_to_test)} APIs to test")
            
            # 3. 为每个 API 生成测试用例
            for api in apis_to_test:
                api_testcases = self._design_api_testcases(api)
                testcases.extend(api_testcases)
            
            # 4. 记录设计历史
            self._record_design({
                "source": "swagger",
                "file": swagger_file,
                "filters": filters,
                "testcase_count": len(testcases),
                "timestamp": datetime.now().isoformat()
            })
            
            self.logger.info(f"Generated {len(testcases)} test cases")
            return testcases
            
        except Exception as e:
            self.logger.error(f"Error designing from Swagger: {e}")
            raise
    
    def design_from_requirement(
        self,
        requirement: str,
        doc_path: Optional[str] = None
    ) -> List[Any]:
        """
        从需求文档设计测试用例
        
        Args:
            requirement: 需求描述文本
            doc_path: 需求文档路径（可选）
            
        Returns:
            测试用例列表
        """
        self.logger.info("Designing tests from requirement")
        
        testcases = []
        
        try:
            # 1. 分析需求
            analysis = self._analyze_requirement(requirement, doc_path)
            
            # 2. 提取测试点
            test_points = self._extract_test_points(analysis)
            self.logger.info(f"Extracted {len(test_points)} test points")
            
            # 3. 为每个测试点生成用例
            for point in test_points:
                point_testcases = self._design_testcases_for_point(point)
                testcases.extend(point_testcases)
            
            # 4. 记录设计历史
            self._record_design({
                "source": "requirement",
                "requirement": requirement[:100],
                "doc_path": doc_path,
                "testcase_count": len(testcases),
                "timestamp": datetime.now().isoformat()
            })
            
            self.logger.info(f"Generated {len(testcases)} test cases")
            return testcases
            
        except Exception as e:
            self.logger.error(f"Error designing from requirement: {e}")
            raise
    
    def design_from_discovery(
        self,
        discovery_results: List[Dict]
    ) -> List[Any]:
        """
        从 Discovery 结果设计测试用例
        
        Args:
            discovery_results: Test Discovery Agent 的输出
            
        Returns:
            测试用例列表
        """
        self.logger.info(f"Designing tests from {len(discovery_results)} discovery points")
        
        testcases = []
        
        try:
            # 1. 按风险等级排序
            sorted_points = self._sort_by_risk(discovery_results)
            
            # 2. 为高风险点生成更多测试用例
            for point in sorted_points:
                risk_level = point.get('risk_level', 'medium')
                
                # 根据风险等级决定用例数量
                if risk_level == 'critical':
                    count = self.max_testcases_per_api * 2
                elif risk_level == 'high':
                    count = self.max_testcases_per_api
                else:
                    count = max(2, self.max_testcases_per_api // 2)
                
                point_testcases = self._design_testcases_for_discovery_point(
                    point,
                    count=count
                )
                testcases.extend(point_testcases)
            
            # 3. 记录设计历史
            self._record_design({
                "source": "discovery",
                "discovery_point_count": len(discovery_results),
                "testcase_count": len(testcases),
                "timestamp": datetime.now().isoformat()
            })
            
            self.logger.info(f"Generated {len(testcases)} test cases")
            return testcases
            
        except Exception as e:
            self.logger.error(f"Error designing from discovery: {e}")
            raise
    
    def optimize_testcases(
        self,
        testcases: List[Any],
        max_count: Optional[int] = None
    ) -> List[Any]:
        """
        优化测试用例集合
        
        - 去重
        - 按优先级排序
        - 限制数量
        
        Args:
            testcases: 原始测试用例列表
            max_count: 最大保留数量
            
        Returns:
            优化后的测试用例列表
        """
        self.logger.info(f"Optimizing {len(testcases)} test cases")
        
        # 1. 去重
        unique_testcases = self._deduplicate_testcases(testcases)
        self.logger.info(f"After deduplication: {len(unique_testcases)} test cases")
        
        # 2. 按优先级排序
        sorted_testcases = self._sort_by_priority(unique_testcases)
        
        # 3. 限制数量
        if max_count and len(sorted_testcases) > max_count:
            sorted_testcases = sorted_testcases[:max_count]
            self.logger.info(f"Limited to {max_count} test cases")
        
        return sorted_testcases
    
    def get_design_statistics(self) -> Dict:
        """
        获取设计统计信息
        
        Returns:
            统计信息字典
        """
        total_designs = len(self.design_history)
        total_testcases = sum(d.get('testcase_count', 0) for d in self.design_history)
        
        sources = {}
        for design in self.design_history:
            source = design.get('source', 'unknown')
            sources[source] = sources.get(source, 0) + 1
        
        return {
            "total_designs": total_designs,
            "total_testcases": total_testcases,
            "sources": sources,
            "avg_testcases_per_design": total_testcases / total_designs if total_designs > 0 else 0
        }
    
    # ==================== 私有方法 ====================
    
    def _parse_swagger(self, swagger_file: str) -> Dict:
        """解析 Swagger 文件"""
        import json
        
        with open(swagger_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _determine_test_scope(
        self,
        swagger_data: Dict,
        filters: Dict
    ) -> List[Dict]:
        """
        确定测试范围
        
        根据过滤条件决定哪些 API 需要测试
        """
        apis = []
        paths = swagger_data.get('paths', {})
        
        filter_paths = filters.get('paths', [])
        filter_methods = filters.get('methods', [])
        filter_tags = filters.get('tags', [])
        
        for path, methods in paths.items():
            # 路径过滤
            if filter_paths and path not in filter_paths:
                continue
            
            for method, spec in methods.items():
                # 方法过滤
                if filter_methods and method.lower() not in [m.lower() for m in filter_methods]:
                    continue
                
                # 标签过滤
                if filter_tags:
                    tags = spec.get('tags', [])
                    if not any(tag in filter_tags for tag in tags):
                        continue
                
                apis.append({
                    "path": path,
                    "method": method.upper(),
                    "spec": spec
                })
        
        return apis
    
    def _design_api_testcases(self, api: Dict) -> List[Any]:
        """为单个 API 设计测试用例"""
        testcases = []
        path = api['path']
        method = api['method']
        spec = api['spec']
        
        # 1. 正常场景
        testcases.append(self._create_testcase(
            title=f"{method} {path} - 正常场景",
            path=path,
            method=method,
            priority="high",
            test_type="functional"
        ))
        
        # 2. 边界测试
        if self.include_edge_cases:
            testcases.append(self._create_testcase(
                title=f"{method} {path} - 边界值测试",
                path=path,
                method=method,
                priority="medium",
                test_type="boundary"
            ))
        
        # 3. 异常测试
        if self.include_error_cases:
            testcases.append(self._create_testcase(
                title=f"{method} {path} - 异常场景",
                path=path,
                method=method,
                priority="medium",
                test_type="negative"
            ))
        
        # 限制数量
        return testcases[:self.max_testcases_per_api]
    
    def _analyze_requirement(
        self,
        requirement: str,
        doc_path: Optional[str]
    ) -> Dict:
        """分析需求"""
        analysis = {
            "requirement": requirement,
            "doc_path": doc_path,
            "features": [],
            "test_focus": []
        }
        
        # 简单的关键词提取
        keywords = ["登录", "注册", "查询", "创建", "删除", "更新", "支付"]
        for keyword in keywords:
            if keyword in requirement:
                analysis["features"].append(keyword)
        
        return analysis
    
    def _extract_test_points(self, analysis: Dict) -> List[Dict]:
        """从需求分析中提取测试点"""
        test_points = []
        
        for feature in analysis.get("features", []):
            test_points.append({
                "feature": feature,
                "description": f"测试{feature}功能",
                "priority": "high"
            })
        
        return test_points
    
    def _design_testcases_for_point(self, point: Dict) -> List[Any]:
        """为测试点设计用例"""
        testcases = []
        feature = point.get('feature', 'unknown')
        
        testcases.append(self._create_testcase(
            title=f"{feature} - 正常场景",
            priority=point.get('priority', 'medium'),
            test_type="functional"
        ))
        
        if self.include_error_cases:
            testcases.append(self._create_testcase(
                title=f"{feature} - 异常场景",
                priority="medium",
                test_type="negative"
            ))
        
        return testcases
    
    def _sort_by_risk(self, discovery_results: List[Dict]) -> List[Dict]:
        """按风险等级排序"""
        risk_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
        
        return sorted(
            discovery_results,
            key=lambda x: risk_order.get(x.get('risk_level', 'medium'), 2)
        )
    
    def _design_testcases_for_discovery_point(
        self,
        point: Dict,
        count: int
    ) -> List[Any]:
        """为 Discovery 点设计用例"""
        testcases = []
        change_type = point.get('change_type', 'unknown')
        path = point.get('path', 'unknown')
        
        for i in range(count):
            test_type = ["functional", "boundary", "negative"][i % 3]
            testcases.append(self._create_testcase(
                title=f"{change_type} - {path} - 测试{i+1}",
                priority=self._map_risk_to_priority(point.get('risk_level', 'medium')),
                test_type=test_type
            ))
        
        return testcases
    
    def _create_testcase(self, **kwargs) -> Any:
        """创建测试用例对象"""
        if CORE_AVAILABLE:
            # 使用核心模型
            import uuid
            return create_test_case(
                id=kwargs.get('id', f"TC_{uuid.uuid4().hex[:8]}"),
                title=kwargs.get('title', 'Untitled'),
                module=kwargs.get('module', 'default'),
                priority=kwargs.get('priority', 'medium')
            )
        else:
            # 使用字典格式
            return {
                "id": f"TC_{datetime.now().timestamp()}",
                "title": kwargs.get('title', 'Untitled'),
                "module": kwargs.get('module', 'default'),
                "priority": kwargs.get('priority', 'medium'),
                "test_type": kwargs.get('test_type', 'functional'),
                "path": kwargs.get('path'),
                "method": kwargs.get('method'),
                "steps": [],
                "expected": "",
                "created_at": datetime.now().isoformat()
            }
    
    def _deduplicate_testcases(self, testcases: List[Any]) -> List[Any]:
        """去重测试用例"""
        seen = set()
        unique = []
        
        for tc in testcases:
            # 使用 title 作为去重键
            if CORE_AVAILABLE and hasattr(tc, 'title'):
                key = tc.title
            else:
                key = tc.get('title', '')
            
            if key not in seen:
                seen.add(key)
                unique.append(tc)
        
        return unique
    
    def _sort_by_priority(self, testcases: List[Any]) -> List[Any]:
        """按优先级排序"""
        priority_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
        
        def get_priority(tc):
            if CORE_AVAILABLE and hasattr(tc, 'priority'):
                return priority_order.get(tc.priority.value if hasattr(tc.priority, 'value') else str(tc.priority), 2)
            else:
                return priority_order.get(tc.get('priority', 'medium'), 2)
        
        return sorted(testcases, key=get_priority)
    
    def _map_risk_to_priority(self, risk_level: str) -> str:
        """将风险等级映射到优先级"""
        mapping = {
            'critical': 'critical',
            'high': 'high',
            'medium': 'medium',
            'low': 'low'
        }
        return mapping.get(risk_level, 'medium')
    
    def _record_design(self, design_info: Dict):
        """记录设计历史"""
        self.design_history.append(design_info)
