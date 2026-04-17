"""
测试结果智能分析器
提供失败原因分析、性能分析、覆盖率分析等功能
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
from collections import defaultdict, Counter
import re
from core import ExecutionResult, TestCaseStatus


class ResultAnalyzer:
    """测试结果智能分析器"""
    
    def __init__(self):
        """初始化分析器"""
        self.error_patterns = {
            'timeout': r'timeout|timed out|超时',
            'connection': r'connection|connect|连接',
            'auth': r'auth|unauthorized|forbidden|401|403|认证|授权',
            'not_found': r'not found|404|未找到',
            'server_error': r'500|502|503|server error|服务器错误',
            'validation': r'validation|invalid|格式|校验',
            'data': r'data|数据|null|empty',
            'assertion': r'assert|expected|actual|断言'
        }
    
    def analyze(self, results: List[ExecutionResult]) -> Dict[str, Any]:
        """
        综合分析测试结果
        
        Args:
            results: 测试结果列表
            
        Returns:
            分析报告字典
        """
        return {
            'basic_stats': self._analyze_basic_stats(results),
            'failure_analysis': self._analyze_failures(results),
            'performance_analysis': self._analyze_performance(results),
            'healing_analysis': self._analyze_healing(results),
            'recommendations': self._generate_recommendations(results)
        }
    
    def _analyze_basic_stats(self, results: List[ExecutionResult]) -> Dict[str, Any]:
        """基础统计分析"""
        total = len(results)
        if total == 0:
            return {
                'total': 0,
                'passed': 0,
                'failed': 0,
                'pass_rate': 0.0,
                'fail_rate': 0.0
            }
        
        passed = sum(1 for r in results if r.status == TestCaseStatus.PASSED)
        failed = sum(1 for r in results if r.status == TestCaseStatus.FAILED)
        
        return {
            'total': total,
            'passed': passed,
            'failed': failed,
            'pass_rate': round(passed / total * 100, 2),
            'fail_rate': round(failed / total * 100, 2),
            'total_duration': round(sum(r.duration for r in results), 2),
            'avg_duration': round(sum(r.duration for r in results) / total, 2)
        }
    
    def _analyze_failures(self, results: List[ExecutionResult]) -> Dict[str, Any]:
        """失败原因分析"""
        failures = [r for r in results if r.status == TestCaseStatus.FAILED]
        
        if not failures:
            return {
                'total_failures': 0,
                'error_categories': {},
                'top_errors': [],
                'failure_rate_by_category': {}
            }
        
        # 错误分类
        error_categories = defaultdict(list)
        for failure in failures:
            error_msg = failure.error or ''
            categorized = False
            
            for category, pattern in self.error_patterns.items():
                if re.search(pattern, error_msg, re.IGNORECASE):
                    error_categories[category].append({
                        'test_case_id': failure.test_case_id,
                        'error': error_msg
                    })
                    categorized = True
                    break
            
            if not categorized:
                error_categories['other'].append({
                    'test_case_id': failure.test_case_id,
                    'error': error_msg
                })
        
        # 统计每个分类的数量
        category_counts = {cat: len(errors) for cat, errors in error_categories.items()}
        
        # Top错误
        error_counter = Counter(f.error for f in failures if f.error)
        top_errors = [
            {'error': error, 'count': count}
            for error, count in error_counter.most_common(5)
        ]
        
        # 失败率按分类
        total_failures = len(failures)
        failure_rate_by_category = {
            cat: round(count / total_failures * 100, 2)
            for cat, count in category_counts.items()
        }
        
        return {
            'total_failures': total_failures,
            'error_categories': dict(error_categories),
            'category_counts': category_counts,
            'top_errors': top_errors,
            'failure_rate_by_category': failure_rate_by_category
        }
    
    def _analyze_performance(self, results: List[ExecutionResult]) -> Dict[str, Any]:
        """性能分析"""
        if not results:
            return {
                'avg_duration': 0,
                'min_duration': 0,
                'max_duration': 0,
                'slow_tests': [],
                'fast_tests': []
            }
        
        durations = [r.duration for r in results]
        avg_duration = sum(durations) / len(durations)
        
        # 慢测试（超过平均值2倍）
        slow_threshold = avg_duration * 2
        slow_tests = [
            {
                'test_case_id': r.test_case_id,
                'duration': round(r.duration, 2),
                'status': r.status.value
            }
            for r in results if r.duration > slow_threshold
        ]
        slow_tests.sort(key=lambda x: x['duration'], reverse=True)
        
        # 快测试（前5个最快的）
        fast_tests = sorted(
            [
                {
                    'test_case_id': r.test_case_id,
                    'duration': round(r.duration, 2),
                    'status': r.status.value
                }
                for r in results
            ],
            key=lambda x: x['duration']
        )[:5]
        
        return {
            'avg_duration': round(avg_duration, 2),
            'min_duration': round(min(durations), 2),
            'max_duration': round(max(durations), 2),
            'slow_tests': slow_tests[:10],  # 最慢的10个
            'fast_tests': fast_tests,
            'duration_distribution': self._calculate_duration_distribution(durations)
        }
    
    def _calculate_duration_distribution(self, durations: List[float]) -> Dict[str, int]:
        """计算耗时分布"""
        distribution = {
            '0-1s': 0,
            '1-2s': 0,
            '2-5s': 0,
            '5-10s': 0,
            '>10s': 0
        }
        
        for d in durations:
            if d < 1:
                distribution['0-1s'] += 1
            elif d < 2:
                distribution['1-2s'] += 1
            elif d < 5:
                distribution['2-5s'] += 1
            elif d < 10:
                distribution['5-10s'] += 1
            else:
                distribution['>10s'] += 1
        
        return distribution
    
    def _analyze_healing(self, results: List[ExecutionResult]) -> Dict[str, Any]:
        """修复分析"""
        healed = [r for r in results if r.healing_applied]
        
        if not healed:
            return {
                'total_healed': 0,
                'healing_success_rate': 0.0,
                'healing_by_level': {},
                'healing_effectiveness': {}
            }
        
        # 按级别统计
        healing_by_level = defaultdict(int)
        healing_success = defaultdict(int)
        
        for r in healed:
            level = r.healing_level.value if r.healing_level else 'unknown'
            healing_by_level[level] += 1
            
            if r.status == TestCaseStatus.PASSED:
                healing_success[level] += 1
        
        # 计算每个级别的成功率
        healing_effectiveness = {}
        for level, total in healing_by_level.items():
            success = healing_success.get(level, 0)
            healing_effectiveness[level] = {
                'total': total,
                'success': success,
                'success_rate': round(success / total * 100, 2) if total > 0 else 0
            }
        
        total_healed = len(healed)
        total_success = sum(1 for r in healed if r.status == TestCaseStatus.PASSED)
        
        return {
            'total_healed': total_healed,
            'healing_success_rate': round(total_success / total_healed * 100, 2),
            'healing_by_level': dict(healing_by_level),
            'healing_effectiveness': healing_effectiveness
        }
    
    def _generate_recommendations(self, results: List[ExecutionResult]) -> List[Dict[str, str]]:
        """生成优化建议"""
        recommendations = []
        
        # 分析失败率
        basic_stats = self._analyze_basic_stats(results)
        if basic_stats['fail_rate'] > 20:
            recommendations.append({
                'type': 'high_failure_rate',
                'severity': 'high',
                'message': f"失败率过高 ({basic_stats['fail_rate']}%)，建议检查测试环境和数据准备"
            })
        
        # 分析性能
        perf_analysis = self._analyze_performance(results)
        if len(perf_analysis['slow_tests']) > len(results) * 0.3:
            recommendations.append({
                'type': 'performance',
                'severity': 'medium',
                'message': f"有 {len(perf_analysis['slow_tests'])} 个慢测试，建议优化测试性能"
            })
        
        # 分析失败原因
        failure_analysis = self._analyze_failures(results)
        if failure_analysis.get('category_counts', {}).get('timeout', 0) > 3:
            recommendations.append({
                'type': 'timeout',
                'severity': 'high',
                'message': "多个超时失败，建议增加超时时间或优化接口性能"
            })
        
        if failure_analysis.get('category_counts', {}).get('connection', 0) > 3:
            recommendations.append({
                'type': 'connection',
                'severity': 'high',
                'message': "多个连接失败，建议检查网络和服务可用性"
            })
        
        # 分析修复效果
        healing_analysis = self._analyze_healing(results)
        if healing_analysis['total_healed'] > 0 and healing_analysis['healing_success_rate'] < 50:
            recommendations.append({
                'type': 'healing',
                'severity': 'medium',
                'message': f"修复成功率较低 ({healing_analysis['healing_success_rate']}%)，建议优化修复策略"
            })
        
        return recommendations
