#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TestOptimizationAgent - 测试优化代理

核心能力：
1. 测试去重 - 合并冗余测试，保留关键用例
2. 执行优先级排序 - 结合优先级和风险评分
3. 覆盖率优化 - 识别重复覆盖和未覆盖路径
4. 执行计划生成 - 输出优化后的执行计划

目标：减少冗余测试，提高执行效率，优化测试覆盖质量
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from collections import defaultdict


class TestOptimizationAgent:
    """
    测试优化代理 - 优化测试用例和执行策略
    
    核心功能：
    1. 测试去重（相同API+参数结构合并）
    2. 执行优先级排序（P0 + 高风险优先）
    3. 覆盖率优化（识别重复和缺口）
    4. 执行计划生成（优化后的执行方案）
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        初始化优化代理
        
        Args:
            config: 配置字典
                - dedup_threshold: 去重相似度阈值（默认0.9）
                - keep_boundary: 保留边界测试（默认True）
                - keep_negative: 保留异常测试（默认True）
                - keep_high_priority: 保留高优先级（默认True）
        """
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # 配置参数
        self.dedup_threshold = self.config.get('dedup_threshold', 0.9)
        self.keep_boundary = self.config.get('keep_boundary', True)
        self.keep_negative = self.config.get('keep_negative', True)
        self.keep_high_priority = self.config.get('keep_high_priority', True)
        
        # 优化历史
        self.optimization_history = []
        
        self.logger.info(f"TestOptimizationAgent 初始化: {self.config}")
    
    def optimize(
        self,
        test_cases: List[Any],
        learning_agent: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        优化测试用例（主入口）
        
        Args:
            test_cases: 原始测试用例列表
            learning_agent: LearningAgent 实例（用于获取高风险API）
        
        Returns:
            优化结果字典：
            {
                "optimized_cases": List[TestCase],  # 优化后的用例
                "dropped_cases": List[TestCase],    # 被移除的用例
                "execution_plan": Dict,             # 执行计划
                "coverage_report": Dict,            # 覆盖率报告
                "statistics": Dict                  # 统计信息
            }
        """
        self.logger.info(f"开始优化 {len(test_cases)} 个测试用例")
        start_time = datetime.now()
        
        # 1. 测试去重
        self.logger.info("[1/4] 执行测试去重...")
        deduplicated, dropped_by_dedup = self._deduplicate(test_cases)
        self.logger.info(f"  去重后: {len(deduplicated)} 个用例 (移除 {len(dropped_by_dedup)} 个)")
        
        # 2. 执行优先级排序
        self.logger.info("[2/4] 执行优先级排序...")
        prioritized = self._prioritize(deduplicated, learning_agent)
        self.logger.info(f"  排序完成: {len(prioritized)} 个用例")
        
        # 3. 覆盖率优化
        self.logger.info("[3/4] 分析覆盖率...")
        coverage_report = self._analyze_coverage(prioritized)
        self.logger.info(f"  覆盖率分析完成")
        
        # 4. 生成执行计划
        self.logger.info("[4/4] 生成执行计划...")
        execution_plan = self._generate_execution_plan(
            prioritized,
            len(test_cases),
            len(dropped_by_dedup)
        )
        
        # 计算优化统计
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        statistics = {
            "original_count": len(test_cases),
            "optimized_count": len(prioritized),
            "dropped_count": len(dropped_by_dedup),
            "reduction_rate": len(dropped_by_dedup) / len(test_cases) if test_cases else 0,
            "optimization_duration": duration,
            "timestamp": datetime.now().isoformat()
        }
        
        # 记录优化历史
        self._record_optimization(statistics)
        
        self.logger.info(f"优化完成: {len(test_cases)} → {len(prioritized)} 用例 "
                        f"(减少 {statistics['reduction_rate']:.1%})")
        
        return {
            "optimized_cases": prioritized,
            "dropped_cases": dropped_by_dedup,
            "execution_plan": execution_plan,
            "coverage_report": coverage_report,
            "statistics": statistics
        }
    
    # ==================== 1. 测试去重 ====================
    
    def _deduplicate(self, test_cases: List[Any]) -> Tuple[List[Any], List[Any]]:
        """
        测试去重
        
        逻辑：
        - 相同API + 相同参数结构 → 合并
        - 保留：边界测试、异常测试、高优先级测试
        
        Args:
            test_cases: 原始测试用例列表
        
        Returns:
            (去重后的用例列表, 被移除的用例列表)
        """
        if not test_cases:
            return [], []
        
        # 按 API 分组
        api_groups = defaultdict(list)
        
        for tc in test_cases:
            api_key = self._get_api_key(tc)
            api_groups[api_key].append(tc)
        
        deduplicated = []
        dropped = []
        
        # 对每个 API 组进行去重
        for api_key, group in api_groups.items():
            if len(group) == 1:
                # 只有一个用例，直接保留
                deduplicated.append(group[0])
                continue
            
            # 多个用例，需要去重
            kept, removed = self._deduplicate_group(group)
            deduplicated.extend(kept)
            dropped.extend(removed)
        
        return deduplicated, dropped
    
    def _deduplicate_group(self, group: List[Any]) -> Tuple[List[Any], List[Any]]:
        """
        对同一 API 的用例组进行去重
        
        策略：
        1. 保留所有边界测试
        2. 保留所有异常测试
        3. 保留所有高优先级测试
        4. 对于普通测试，只保留一个
        """
        kept = []
        removed = []
        
        # 分类用例
        boundary_cases = []
        negative_cases = []
        high_priority_cases = []
        normal_cases = []
        
        for tc in group:
            test_type = self._get_test_type(tc)
            priority = self._get_priority(tc)
            
            if test_type == 'boundary' and self.keep_boundary:
                boundary_cases.append(tc)
            elif test_type == 'negative' and self.keep_negative:
                negative_cases.append(tc)
            elif priority in ['critical', 'high'] and self.keep_high_priority:
                high_priority_cases.append(tc)
            else:
                normal_cases.append(tc)
        
        # 保留策略
        kept.extend(boundary_cases)
        kept.extend(negative_cases)
        kept.extend(high_priority_cases)
        
        # 普通用例只保留一个（优先级最高的）
        if normal_cases:
            normal_cases.sort(key=lambda tc: self._get_priority_score(tc), reverse=True)
            kept.append(normal_cases[0])
            removed.extend(normal_cases[1:])
        
        return kept, removed
    
    # ==================== 2. 执行优先级排序 ====================
    
    def _prioritize(
        self,
        test_cases: List[Any],
        learning_agent: Optional[Any]
    ) -> List[Any]:
        """
        执行优先级排序
        
        结合：
        - test_case.priority
        - LearningAgent.get_high_risk_apis()
        
        规则：P0 + 高频失败 → 最优先执行
        
        Args:
            test_cases: 测试用例列表
            learning_agent: LearningAgent 实例
        
        Returns:
            排序后的测试用例列表
        """
        if not test_cases:
            return []
        
        # 获取高风险 API
        high_risk_apis = {}
        if learning_agent:
            try:
                risk_list = learning_agent.get_high_risk_apis(top_n=50)
                high_risk_apis = {
                    item['api']: item['risk_score']
                    for item in risk_list
                }
                self.logger.info(f"  获取了 {len(high_risk_apis)} 个高风险 API")
            except Exception as e:
                self.logger.warning(f"  获取高风险 API 失败: {e}")
        
        # 计算每个用例的综合优先级分数
        scored_cases = []
        
        for tc in test_cases:
            # 基础优先级分数
            priority_score = self._get_priority_score(tc)
            
            # 风险分数
            api_key = self._get_api_key(tc)
            risk_score = high_risk_apis.get(api_key, 0.0)
            
            # 综合分数 = 优先级分数 * 0.6 + 风险分数 * 0.4
            total_score = priority_score * 0.6 + risk_score * 0.4
            
            scored_cases.append((total_score, tc))
        
        # 按综合分数降序排序
        scored_cases.sort(key=lambda x: x[0], reverse=True)
        
        return [tc for score, tc in scored_cases]
    
    def _get_priority_score(self, test_case: Any) -> float:
        """
        获取优先级分数
        
        critical: 1.0
        high: 0.7
        medium: 0.4
        low: 0.1
        """
        priority = self._get_priority(test_case)
        
        score_map = {
            'critical': 1.0,
            'high': 0.7,
            'medium': 0.4,
            'low': 0.1
        }
        
        return score_map.get(priority, 0.4)
    
    # ==================== 3. 覆盖率优化 ====================
    
    def _analyze_coverage(self, test_cases: List[Any]) -> Dict[str, Any]:
        """
        覆盖率优化
        
        识别：
        - 覆盖重复的测试
        - 未覆盖的重要路径
        
        Returns:
            覆盖率报告
        """
        if not test_cases:
            return {
                "total_apis": 0,
                "covered_apis": [],
                "duplicate_coverage": [],
                "coverage_gaps": []
            }
        
        # 统计 API 覆盖
        api_coverage = defaultdict(list)
        
        for tc in test_cases:
            api_key = self._get_api_key(tc)
            api_coverage[api_key].append(tc)
        
        # 识别重复覆盖（同一 API 有多个测试）
        duplicate_coverage = []
        for api_key, cases in api_coverage.items():
            if len(cases) > 3:  # 超过3个测试认为可能重复
                duplicate_coverage.append({
                    "api": api_key,
                    "test_count": len(cases),
                    "suggestion": "考虑减少测试数量"
                })
        
        # 覆盖缺口（这里简化处理，实际需要结合 Swagger 或需求）
        coverage_gaps = []
        
        avg_tests = sum(len(cases) for cases in api_coverage.values()) / len(api_coverage) if api_coverage else 0
        
        return {
            "total_apis": len(api_coverage),
            "covered_apis": list(api_coverage.keys()),
            "duplicate_coverage": duplicate_coverage,
            "coverage_gaps": coverage_gaps,
            "avg_tests_per_api": avg_tests
        }
    
    # ==================== 4. 执行计划生成 ====================
    
    def _generate_execution_plan(
        self,
        optimized_cases: List[Any],
        original_count: int,
        dropped_count: int
    ) -> Dict[str, Any]:
        """
        执行计划生成
        
        Returns:
            执行计划字典
        """
        # 估算执行时间（假设每个用例平均 2 秒）
        estimated_time = len(optimized_cases) * 2
        
        # 生成执行顺序（已经排序好了）
        execution_order = []
        for i, tc in enumerate(optimized_cases, 1):
            execution_order.append({
                "sequence": i,
                "test_case_id": self._get_testcase_id(tc),
                "title": self._get_title(tc),
                "priority": self._get_priority(tc),
                "api": self._get_api_key(tc)
            })
        
        return {
            "total_cases": original_count,
            "optimized_cases": len(optimized_cases),
            "dropped_cases": dropped_count,
            "reduction_rate": f"{(dropped_count / original_count * 100):.1f}%" if original_count > 0 else "0%",
            "execution_order": execution_order[:10],  # 只显示前10个
            "estimated_time": f"{estimated_time}s",
            "estimated_time_saved": f"{dropped_count * 2}s"
        }
    
    # ==================== 辅助方法 ====================
    
    def _get_api_key(self, test_case: Any) -> str:
        """
        获取 API 键（用于分组）
        
        格式：METHOD /path
        """
        # 尝试从 testcase_id 提取
        testcase_id = self._get_testcase_id(test_case)
        
        # 简单提取：假设 testcase_id 包含 API 信息
        # 例如：tc_payment_create_001 → POST /payment/create
        if '_' in testcase_id:
            parts = testcase_id.split('_')
            if len(parts) >= 3:
                return f"POST /{parts[1]}/{parts[2]}"
        
        # 尝试从 title 提取
        title = self._get_title(test_case)
        if ' ' in title:
            parts = title.split(' ')
            if len(parts) >= 2:
                return f"{parts[0]} {parts[1]}"
        
        return "/unknown"
    
    def _get_test_type(self, test_case: Any) -> str:
        """获取测试类型"""
        # 从 title 推断
        title = self._get_title(test_case).lower()
        
        if '边界' in title or 'boundary' in title:
            return 'boundary'
        elif '异常' in title or 'negative' in title or '错误' in title:
            return 'negative'
        else:
            return 'functional'
    
    def _get_priority(self, test_case: Any) -> str:
        """获取优先级"""
        if hasattr(test_case, 'priority'):
            p = test_case.priority
            if hasattr(p, 'value'):
                return p.value
            return str(p)
        elif isinstance(test_case, dict):
            return test_case.get('priority', 'medium')
        return 'medium'
    
    def _get_testcase_id(self, test_case: Any) -> str:
        """获取测试用例 ID"""
        if hasattr(test_case, 'id'):
            return test_case.id
        elif isinstance(test_case, dict):
            return test_case.get('id', 'unknown')
        return 'unknown'
    
    def _get_title(self, test_case: Any) -> str:
        """获取测试用例标题"""
        if hasattr(test_case, 'title'):
            return test_case.title
        elif isinstance(test_case, dict):
            return test_case.get('title', 'Untitled')
        return 'Untitled'
    
    def _record_optimization(self, statistics: Dict):
        """记录优化历史"""
        self.optimization_history.append(statistics)
    
    def get_optimization_statistics(self) -> Dict[str, Any]:
        """
        获取优化统计信息
        
        Returns:
            统计信息字典
        """
        if not self.optimization_history:
            return {
                "total_optimizations": 0,
                "total_original_cases": 0,
                "total_optimized_cases": 0,
                "total_dropped_cases": 0,
                "avg_reduction_rate": 0.0
            }
        
        total_original = sum(h['original_count'] for h in self.optimization_history)
        total_optimized = sum(h['optimized_count'] for h in self.optimization_history)
        total_dropped = sum(h['dropped_count'] for h in self.optimization_history)
        avg_reduction = sum(h['reduction_rate'] for h in self.optimization_history) / len(self.optimization_history)
        
        return {
            "total_optimizations": len(self.optimization_history),
            "total_original_cases": total_original,
            "total_optimized_cases": total_optimized,
            "total_dropped_cases": total_dropped,
            "avg_reduction_rate": avg_reduction
        }
