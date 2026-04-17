"""
Test Intelligence Agent - 测试智能决策引擎
在执行前动态决定测试用例的选择、优先级和并发策略
"""
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum
from collections import defaultdict
import json


class ExecutionDecision(Enum):
    """执行决策"""
    MUST_RUN = "must_run"      # 必须执行
    OPTIONAL = "optional"       # 可选执行
    SKIP = "skip"              # 跳过


class Priority(Enum):
    """优先级"""
    P0 = "P0"  # 最高优先级
    P1 = "P1"  # 高优先级
    P2 = "P2"  # 中优先级
    P3 = "P3"  # 低优先级


@dataclass
class TestCase:
    """测试用例"""
    test_case_id: str
    api: str
    module: str = "default"
    priority: str = "P2"
    tags: List[str] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []


@dataclass
class RiskScore:
    """风险评分"""
    test_case_id: str
    total_score: float
    failure_rate: float
    change_frequency: float
    priority_weight: float
    coverage_gap: float
    decision: ExecutionDecision


class TestIntelligenceAgent:
    """测试智能决策引擎"""
    
    def __init__(self, learning_agent=None):
        """
        初始化测试智能决策引擎
        
        Args:
            learning_agent: LearningAgent实例,用于获取历史数据
        """
        self.learning_agent = learning_agent
        
        # 优先级权重映射
        self.priority_weights = {
            'P0': 1.0,
            'P1': 0.7,
            'P2': 0.4,
            'P3': 0.2
        }
        
        # 风险阈值
        self.risk_thresholds = {
            'must_run': 0.6,    # > 0.6 必须执行
            'optional': 0.3     # 0.3~0.6 可选执行, < 0.3 跳过
        }
    
    def select_tests(self, test_cases: List[TestCase]) -> Dict[str, Any]:
        """
        选择需要执行的测试用例
        
        Args:
            test_cases: 测试用例列表
            
        Returns:
            选择结果字典
        """
        selected_tests = []
        skipped_tests = []
        priority_order = []
        
        # 计算每个测试用例的风险评分
        risk_scores = []
        for tc in test_cases:
            risk_score = self.calculate_risk_score(tc)
            risk_scores.append(risk_score)
            
            # 根据风险评分决策
            if risk_score.decision == ExecutionDecision.MUST_RUN:
                selected_tests.append(tc.test_case_id)
            elif risk_score.decision == ExecutionDecision.OPTIONAL:
                selected_tests.append(tc.test_case_id)
            else:  # SKIP
                skipped_tests.append(tc.test_case_id)
        
        # 按风险评分排序,高风险优先
        risk_scores.sort(key=lambda x: x.total_score, reverse=True)
        priority_order = [rs.test_case_id for rs in risk_scores if rs.decision != ExecutionDecision.SKIP]
        
        return {
            'selected_tests': selected_tests,
            'skipped_tests': skipped_tests,
            'priority_order': priority_order,
            'risk_scores': [self._risk_score_to_dict(rs) for rs in risk_scores]
        }
    
    def calculate_risk_score(self, test_case: TestCase) -> RiskScore:
        """
        计算测试用例的风险评分
        
        风险评分模型:
        risk_score = 0.4 * failure_rate + 0.2 * change_frequency + 
                     0.2 * priority_weight + 0.2 * coverage_gap
        
        Args:
            test_case: 测试用例
            
        Returns:
            风险评分对象
        """
        # 1. 获取历史失败率 (0~1)
        failure_rate = self._get_failure_rate(test_case)
        
        # 2. 获取变更频率 (0~1)
        change_frequency = self._get_change_frequency(test_case)
        
        # 3. 优先级权重 (0~1)
        priority_weight = self.priority_weights.get(test_case.priority, 0.4)
        
        # 4. 覆盖率缺口 (0~1)
        coverage_gap = self._get_coverage_gap(test_case)
        
        # 计算总风险评分
        total_score = (
            0.4 * failure_rate +
            0.2 * change_frequency +
            0.2 * priority_weight +
            0.2 * coverage_gap
        )
        
        # 决策
        if total_score > self.risk_thresholds['must_run']:
            decision = ExecutionDecision.MUST_RUN
        elif total_score >= self.risk_thresholds['optional']:
            decision = ExecutionDecision.OPTIONAL
        else:
            decision = ExecutionDecision.SKIP
        
        return RiskScore(
            test_case_id=test_case.test_case_id,
            total_score=round(total_score, 3),
            failure_rate=round(failure_rate, 3),
            change_frequency=round(change_frequency, 3),
            priority_weight=round(priority_weight, 3),
            coverage_gap=round(coverage_gap, 3),
            decision=decision
        )
    
    def optimize_execution_plan(self, test_cases: List[TestCase]) -> Dict[str, Any]:
        """
        优化执行计划,包括选择、排序和并发策略
        
        Args:
            test_cases: 测试用例列表
            
        Returns:
            完整执行计划
        """
        # 1. 选择测试用例
        selection_result = self.select_tests(test_cases)
        
        # 2. 获取选中的测试用例
        selected_test_ids = set(selection_result['selected_tests'])
        selected_test_cases = [tc for tc in test_cases if tc.test_case_id in selected_test_ids]
        
        # 3. 按优先级排序
        execution_order = selection_result['priority_order']
        
        # 4. 生成并发分组
        parallel_groups = self._generate_parallel_groups(selected_test_cases)
        
        # 5. 生成执行统计
        statistics = self._generate_statistics(test_cases, selection_result)
        
        return {
            'selected_tests': selection_result['selected_tests'],
            'skipped_tests': selection_result['skipped_tests'],
            'execution_order': execution_order,
            'parallel_groups': parallel_groups,
            'risk_scores': selection_result['risk_scores'],
            'statistics': statistics
        }
    
    def _get_failure_rate(self, test_case: TestCase) -> float:
        """
        获取历史失败率
        
        Args:
            test_case: 测试用例
            
        Returns:
            失败率 (0~1)
        """
        if not self.learning_agent:
            return 0.1  # 默认值
        
        try:
            # 从LearningAgent获取API统计
            high_risk_apis = self.learning_agent.get_high_risk_apis(top_n=100)
            
            for api_stat in high_risk_apis:
                if api_stat['api'] == test_case.api:
                    return min(api_stat['failure_rate'], 1.0)
            
            return 0.1  # 未找到数据,使用默认值
        except Exception:
            return 0.1
    
    def _get_change_frequency(self, test_case: TestCase) -> float:
        """
        获取API变更频率
        
        Args:
            test_case: 测试用例
            
        Returns:
            变更频率 (0~1)
        """
        # TODO: 从版本控制系统或变更记录获取
        # 目前返回默认值
        return 0.1
    
    def _get_coverage_gap(self, test_case: TestCase) -> float:
        """
        获取覆盖率缺口
        
        Args:
            test_case: 测试用例
            
        Returns:
            覆盖率缺口 (0~1)
        """
        if not self.learning_agent:
            return 0.2  # 默认值
        
        try:
            # 从LearningAgent获取覆盖率缺口
            coverage_gaps = self.learning_agent.get_coverage_gaps()
            
            for gap in coverage_gaps:
                if gap['api'] == test_case.api:
                    # 缺口越大,返回值越高
                    return min(gap.get('gap_score', 0.2), 1.0)
            
            return 0.2  # 未找到数据,使用默认值
        except Exception:
            return 0.2
    
    def _generate_parallel_groups(self, test_cases: List[TestCase]) -> Dict[str, List[str]]:
        """
        生成并发执行分组
        按module分组,同一module的测试用例可以并发执行
        
        Args:
            test_cases: 测试用例列表
            
        Returns:
            并发分组字典
        """
        parallel_groups = defaultdict(list)
        
        for tc in test_cases:
            module = tc.module or 'default'
            parallel_groups[module].append(tc.test_case_id)
        
        return dict(parallel_groups)
    
    def _generate_statistics(self, all_test_cases: List[TestCase], 
                            selection_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        生成执行统计
        
        Args:
            all_test_cases: 所有测试用例
            selection_result: 选择结果
            
        Returns:
            统计信息
        """
        total = len(all_test_cases)
        selected = len(selection_result['selected_tests'])
        skipped = len(selection_result['skipped_tests'])
        
        # 按决策类型统计
        decision_counts = defaultdict(int)
        for risk_score in selection_result['risk_scores']:
            decision_counts[risk_score['decision']] += 1
        
        # 按优先级统计
        priority_counts = defaultdict(int)
        for tc in all_test_cases:
            priority_counts[tc.priority] += 1
        
        return {
            'total_tests': total,
            'selected_tests': selected,
            'skipped_tests': skipped,
            'selection_rate': round(selected / total * 100, 2) if total > 0 else 0,
            'decision_breakdown': dict(decision_counts),
            'priority_breakdown': dict(priority_counts)
        }
    
    def _risk_score_to_dict(self, risk_score: RiskScore) -> Dict[str, Any]:
        """将RiskScore对象转换为字典"""
        return {
            'test_case_id': risk_score.test_case_id,
            'total_score': risk_score.total_score,
            'failure_rate': risk_score.failure_rate,
            'change_frequency': risk_score.change_frequency,
            'priority_weight': risk_score.priority_weight,
            'coverage_gap': risk_score.coverage_gap,
            'decision': risk_score.decision.value
        }
    
    def explain_decision(self, test_case: TestCase) -> str:
        """
        解释决策原因
        
        Args:
            test_case: 测试用例
            
        Returns:
            决策解释文本
        """
        risk_score = self.calculate_risk_score(test_case)
        
        lines = []
        lines.append(f"测试用例: {test_case.test_case_id}")
        lines.append(f"总风险评分: {risk_score.total_score:.3f}")
        lines.append(f"决策: {risk_score.decision.value}")
        lines.append("")
        lines.append("评分明细:")
        lines.append(f"  - 历史失败率 (40%): {risk_score.failure_rate:.3f}")
        lines.append(f"  - 变更频率 (20%): {risk_score.change_frequency:.3f}")
        lines.append(f"  - 优先级权重 (20%): {risk_score.priority_weight:.3f}")
        lines.append(f"  - 覆盖率缺口 (20%): {risk_score.coverage_gap:.3f}")
        lines.append("")
        
        # 决策原因
        if risk_score.decision == ExecutionDecision.MUST_RUN:
            lines.append(f"原因: 风险评分 > {self.risk_thresholds['must_run']},必须执行")
        elif risk_score.decision == ExecutionDecision.OPTIONAL:
            lines.append(f"原因: 风险评分在 {self.risk_thresholds['optional']}~{self.risk_thresholds['must_run']} 之间,可选执行")
        else:
            lines.append(f"原因: 风险评分 < {self.risk_thresholds['optional']},可以跳过")
        
        return "\n".join(lines)
    
    def save_execution_plan(self, execution_plan: Dict[str, Any], output_path: str):
        """
        保存执行计划到文件
        
        Args:
            execution_plan: 执行计划
            output_path: 输出文件路径
        """
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(execution_plan, f, ensure_ascii=False, indent=2)
    
    def load_execution_plan(self, input_path: str) -> Dict[str, Any]:
        """
        从文件加载执行计划
        
        Args:
            input_path: 输入文件路径
            
        Returns:
            执行计划
        """
        with open(input_path, 'r', encoding='utf-8') as f:
            return json.load(f)
