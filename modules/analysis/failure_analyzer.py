"""
失败分析器
深度分析失败原因并提供修复建议
"""
from typing import List, Dict, Any, Optional
from collections import defaultdict
import re
from core import ExecutionResult, TestCaseStatus


class FailureAnalyzer:
    """失败分析器"""
    
    def __init__(self):
        """初始化失败分析器"""
        # 失败模式定义
        self.failure_patterns = {
            'timeout': {
                'pattern': r'timeout|timed out|超时',
                'category': '超时',
                'suggestions': [
                    '增加请求超时时间',
                    '检查接口性能',
                    '优化数据库查询',
                    '检查网络延迟'
                ]
            },
            'connection': {
                'pattern': r'connection|connect|连接|refused|reset',
                'category': '连接失败',
                'suggestions': [
                    '检查服务是否启动',
                    '验证网络连接',
                    '检查防火墙设置',
                    '确认服务地址正确'
                ]
            },
            'auth': {
                'pattern': r'auth|unauthorized|forbidden|401|403|认证|授权|token',
                'category': '认证/授权',
                'suggestions': [
                    '检查认证token是否有效',
                    '验证用户权限',
                    '更新过期的凭证',
                    '检查认证配置'
                ]
            },
            'not_found': {
                'pattern': r'not found|404|未找到',
                'category': '资源未找到',
                'suggestions': [
                    '检查请求路径是否正确',
                    '验证资源是否存在',
                    '检查路由配置',
                    '确认API版本'
                ]
            },
            'server_error': {
                'pattern': r'500|502|503|504|server error|服务器错误|internal error',
                'category': '服务器错误',
                'suggestions': [
                    '查看服务器日志',
                    '检查服务健康状态',
                    '验证数据库连接',
                    '检查依赖服务'
                ]
            },
            'validation': {
                'pattern': r'validation|invalid|格式|校验|required|missing',
                'category': '数据校验',
                'suggestions': [
                    '检查请求参数格式',
                    '验证必填字段',
                    '确认数据类型正确',
                    '检查数据约束'
                ]
            },
            'data': {
                'pattern': r'null|empty|数据|none|undefined',
                'category': '数据问题',
                'suggestions': [
                    '检查测试数据准备',
                    '验证数据依赖',
                    '确认数据库状态',
                    '检查数据清理逻辑'
                ]
            },
            'assertion': {
                'pattern': r'assert|expected|actual|断言|不匹配',
                'category': '断言失败',
                'suggestions': [
                    '检查预期结果是否正确',
                    '验证实际返回值',
                    '更新断言逻辑',
                    '检查业务逻辑变更'
                ]
            }
        }
    
    def analyze_failures(self, results: List[ExecutionResult]) -> Dict[str, Any]:
        """
        分析失败用例
        
        Args:
            results: 测试结果列表
            
        Returns:
            失败分析报告
        """
        failures = [r for r in results if r.status == TestCaseStatus.FAILED]
        
        if not failures:
            return {
                'total_failures': 0,
                'categorized_failures': {},
                'root_causes': [],
                'fix_suggestions': []
            }
        
        # 分类失败
        categorized = self._categorize_failures(failures)
        
        # 分析根因
        root_causes = self._analyze_root_causes(categorized)
        
        # 生成修复建议
        fix_suggestions = self._generate_fix_suggestions(categorized, root_causes)
        
        return {
            'total_failures': len(failures),
            'categorized_failures': categorized,
            'root_causes': root_causes,
            'fix_suggestions': fix_suggestions,
            'priority_fixes': self._prioritize_fixes(categorized, root_causes)
        }
    
    def _categorize_failures(self, failures: List[ExecutionResult]) -> Dict[str, List[Dict]]:
        """分类失败用例"""
        categorized = defaultdict(list)
        
        for failure in failures:
            error_msg = failure.error or ''
            matched = False
            
            for pattern_name, pattern_info in self.failure_patterns.items():
                if re.search(pattern_info['pattern'], error_msg, re.IGNORECASE):
                    categorized[pattern_info['category']].append({
                        'test_case_id': failure.test_case_id,
                        'error': error_msg,
                        'duration': failure.duration,
                        'pattern': pattern_name
                    })
                    matched = True
                    break
            
            if not matched:
                categorized['其他'].append({
                    'test_case_id': failure.test_case_id,
                    'error': error_msg,
                    'duration': failure.duration,
                    'pattern': 'unknown'
                })
        
        return dict(categorized)
    
    def _analyze_root_causes(self, categorized: Dict[str, List[Dict]]) -> List[Dict[str, Any]]:
        """分析根本原因"""
        root_causes = []
        
        for category, failures in categorized.items():
            if len(failures) == 0:
                continue
            
            # 统计该分类的失败数量
            count = len(failures)
            
            # 提取共同特征
            common_errors = self._find_common_patterns(failures)
            
            root_cause = {
                'category': category,
                'failure_count': count,
                'percentage': 0,  # 将在外部计算
                'common_patterns': common_errors,
                'affected_tests': [f['test_case_id'] for f in failures[:5]]  # 最多显示5个
            }
            
            root_causes.append(root_cause)
        
        # 计算百分比
        total_failures = sum(len(failures) for failures in categorized.values())
        for cause in root_causes:
            cause['percentage'] = round(cause['failure_count'] / total_failures * 100, 2)
        
        # 按失败数量排序
        root_causes.sort(key=lambda x: x['failure_count'], reverse=True)
        
        return root_causes
    
    def _find_common_patterns(self, failures: List[Dict]) -> List[str]:
        """查找共同模式"""
        if not failures:
            return []
        
        # 提取所有错误消息中的关键词
        all_words = []
        for failure in failures:
            error = failure['error'].lower()
            # 提取有意义的词（长度>3）
            words = re.findall(r'\b\w{4,}\b', error)
            all_words.extend(words)
        
        # 统计词频
        from collections import Counter
        word_counts = Counter(all_words)
        
        # 返回最常见的3个词
        common = [word for word, count in word_counts.most_common(3) if count > 1]
        return common
    
    def _generate_fix_suggestions(self, categorized: Dict[str, List[Dict]], 
                                  root_causes: List[Dict]) -> List[Dict[str, Any]]:
        """生成修复建议"""
        suggestions = []
        
        for cause in root_causes:
            category = cause['category']
            
            # 查找对应的模式
            pattern_info = None
            for pattern_name, info in self.failure_patterns.items():
                if info['category'] == category:
                    pattern_info = info
                    break
            
            if pattern_info:
                suggestion = {
                    'category': category,
                    'failure_count': cause['failure_count'],
                    'severity': self._calculate_severity(cause['failure_count'], cause['percentage']),
                    'suggestions': pattern_info['suggestions'],
                    'affected_tests': cause['affected_tests']
                }
                suggestions.append(suggestion)
        
        return suggestions
    
    def _calculate_severity(self, count: int, percentage: float) -> str:
        """计算严重程度"""
        if percentage > 50 or count > 10:
            return 'critical'
        elif percentage > 20 or count > 5:
            return 'high'
        elif percentage > 10 or count > 2:
            return 'medium'
        else:
            return 'low'
    
    def _prioritize_fixes(self, categorized: Dict[str, List[Dict]], 
                         root_causes: List[Dict]) -> List[Dict[str, Any]]:
        """优先级排序修复建议"""
        priority_fixes = []
        
        for cause in root_causes[:3]:  # 只取前3个最严重的
            category = cause['category']
            failures = categorized.get(category, [])
            
            # 查找对应的模式
            pattern_info = None
            for pattern_name, info in self.failure_patterns.items():
                if info['category'] == category:
                    pattern_info = info
                    break
            
            if pattern_info and failures:
                priority_fix = {
                    'priority': len(priority_fixes) + 1,
                    'category': category,
                    'failure_count': len(failures),
                    'impact': 'high' if len(failures) > 5 else 'medium',
                    'recommended_action': pattern_info['suggestions'][0],  # 第一个建议
                    'all_suggestions': pattern_info['suggestions'],
                    'example_error': failures[0]['error'][:200]  # 示例错误（截断）
                }
                priority_fixes.append(priority_fix)
        
        return priority_fixes
    
    def generate_failure_report(self, results: List[ExecutionResult]) -> str:
        """
        生成失败分析文本报告
        
        Args:
            results: 测试结果列表
            
        Returns:
            文本格式的失败分析报告
        """
        analysis = self.analyze_failures(results)
        
        lines = []
        lines.append("=" * 80)
        lines.append("失败分析报告")
        lines.append("=" * 80)
        lines.append("")
        
        lines.append(f"📊 总失败数: {analysis['total_failures']}")
        lines.append("")
        
        # 根本原因
        if analysis['root_causes']:
            lines.append("🔍 根本原因分析")
            lines.append("-" * 80)
            for cause in analysis['root_causes']:
                lines.append(f"\n{cause['category']}: {cause['failure_count']}个 ({cause['percentage']}%)")
                if cause['common_patterns']:
                    lines.append(f"  共同特征: {', '.join(cause['common_patterns'])}")
                lines.append(f"  影响用例: {', '.join(cause['affected_tests'][:3])}")
            lines.append("")
        
        # 优先修复建议
        if analysis['priority_fixes']:
            lines.append("🎯 优先修复建议")
            lines.append("-" * 80)
            for fix in analysis['priority_fixes']:
                lines.append(f"\n优先级 {fix['priority']}: {fix['category']}")
                lines.append(f"  失败数: {fix['failure_count']}")
                lines.append(f"  影响: {fix['impact']}")
                lines.append(f"  建议: {fix['recommended_action']}")
                lines.append(f"  示例: {fix['example_error']}")
            lines.append("")
        
        # 详细修复建议
        if analysis['fix_suggestions']:
            lines.append("💡 详细修复建议")
            lines.append("-" * 80)
            for suggestion in analysis['fix_suggestions']:
                lines.append(f"\n{suggestion['category']} ({suggestion['severity']})")
                for i, sug in enumerate(suggestion['suggestions'], 1):
                    lines.append(f"  {i}. {sug}")
            lines.append("")
        
        lines.append("=" * 80)
        
        return "\n".join(lines)
