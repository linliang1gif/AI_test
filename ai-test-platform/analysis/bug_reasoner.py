#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
AI Test Platform - Bug分析推理器

使用AI分析测试失败原因，提供Bug分析和修复建议。
"""

import json
from typing import Dict, Any, List
from ai.ai_client import get_ai_client
from ai.prompt_library import PromptLibrary
from config.config import get_config

# 知识库（懒加载，失败不影响主流程）
try:
    from knowledge.bug_knowledge import BugKnowledge, THRESHOLD_HIT, THRESHOLD_HINT
    _bug_knowledge = BugKnowledge()
except Exception:
    _bug_knowledge = None
    THRESHOLD_HIT = 0.85
    THRESHOLD_HINT = 0.60

class BugReasoner:
    """Bug分析推理器"""

    def __init__(self):
        self.config = get_config()
        self.ai_client = get_ai_client()
        self.prompt_lib = PromptLibrary()

    def analyze_bug(self, error_log: str, test_context: str = "") -> Dict[str, Any]:
        """分析单个Bug（RAG增强版）"""
        # 1. 检索历史相似 Bug
        similar_bugs = []
        if _bug_knowledge:
            try:
                similar_bugs = _bug_knowledge.search_similar_bugs(error_log, top_k=3)
            except Exception:
                pass

        # 2. 高相似度直接命中，跳过 AI
        if similar_bugs and similar_bugs[0]["similarity"] >= THRESHOLD_HIT:
            best = similar_bugs[0]
            print(f"✅ 命中历史Bug（相似度 {best['similarity']:.2f}），跳过AI调用")
            result = {
                "bug_type": best["bug_type"],
                "root_cause": best["root_cause"],
                "fix_suggestion": best["fix_suggestion"],
                "severity": best["severity"],
                "from_knowledge_base": True,
                "kb_similarity": best["similarity"],
                "reproduce_steps": self._generate_basic_reproduce_steps(error_log),
                "prevention": "参考历史修复方案",
                "test_recommendation": "复用历史测试用例",
                "confidence_score": best["similarity"],
                "error_pattern": self._identify_error_pattern(error_log),
                "related_tests": [],
                "fix_priority": self._calculate_fix_priority(best),
                "impact_assessment": {"user_impact": "低", "business_impact": "低",
                                      "system_stability": "稳定", "data_integrity": "安全"}
            }
            import datetime
            result["analysis_timestamp"] = datetime.datetime.now().isoformat()
            return result

        try:
            # 3. 中等相似度：注入历史方案辅助 AI
            hint_bugs = [b for b in similar_bugs if b["similarity"] >= THRESHOLD_HINT]
            if hint_bugs:
                prompt = self._build_rag_enhanced_prompt(error_log, hint_bugs)
            else:
                prompt = self.prompt_lib.get_bug_analysis_prompt(error_log, test_context)

            system_prompt = self.prompt_lib.get_system_prompt()

            response = self.ai_client.generate_json(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=0.3
            )

            bug_analysis = response.get('bug_analysis', {})
            validated_analysis = self._validate_bug_analysis(bug_analysis, error_log)
            enhanced_analysis = self._enhance_bug_analysis(validated_analysis, error_log, test_context)

            # 4. AI 分析完成后入库
            if _bug_knowledge:
                try:
                    _bug_knowledge.save_bug(error_log, enhanced_analysis)
                except Exception:
                    pass

            return enhanced_analysis

        except Exception as e:
            print(f"Bug分析失败: {str(e)}")
            return self._get_basic_bug_analysis(error_log, test_context)

    def _build_rag_enhanced_prompt(self, error_log: str, similar_bugs: List[Dict[str, Any]]) -> str:
        """构建 RAG 增强的 Bug 分析 prompt"""
        hints = "\n".join(
            f"- 相似度 {b['similarity']:.2f}：{b['bug_type']} | 根因：{b['root_cause']} | 修复：{b['fix_suggestion']}"
            for b in similar_bugs
        )
        base_prompt = self.prompt_lib.get_bug_analysis_prompt(error_log, "")
        return f"{base_prompt}\n\n以下是历史相似Bug的分析结果，供参考：\n{hints}"
    
    def _validate_bug_analysis(self, bug_analysis: Dict[str, Any], error_log: str) -> Dict[str, Any]:
        """验证和补充Bug分析结果"""
        validated_analysis = {
            'bug_type': bug_analysis.get('bug_type', self._classify_bug_type(error_log)),
            'root_cause': bug_analysis.get('root_cause', '未知原因'),
            'impact_scope': bug_analysis.get('impact_scope', '局部影响'),
            'severity': bug_analysis.get('severity', self._assess_severity(error_log)),
            'reproduce_steps': bug_analysis.get('reproduce_steps', []),
            'fix_suggestion': bug_analysis.get('fix_suggestion', '需要进一步调查'),
            'prevention': bug_analysis.get('prevention', '加强测试覆盖'),
            'test_recommendation': bug_analysis.get('test_recommendation', '补充相关测试用例'),
            'confidence_score': self._calculate_confidence_score(bug_analysis, error_log)
        }
        
        # 验证复现步骤
        if not validated_analysis['reproduce_steps']:
            validated_analysis['reproduce_steps'] = self._generate_basic_reproduce_steps(error_log)
        
        return validated_analysis
    
    def _classify_bug_type(self, error_log: str) -> str:
        """分类Bug类型"""
        error_log_lower = error_log.lower()
        
        # 常见错误类型映射
        error_type_mapping = {
            'assertionerror': '功能缺陷',
            'connectionerror': '网络问题',
            'timeout': '性能问题',
            'importerror': '环境问题',
            'attributeerror': '代码缺陷',
            'keyerror': '数据问题',
            'valueerror': '参数问题',
            'typeerror': '类型错误',
            'indexerror': '边界问题',
            'filenotfounderror': '配置问题',
            'permissionerror': '权限问题',
            'syntaxerror': '语法错误'
        }
        
        for error_keyword, bug_type in error_type_mapping.items():
            if error_keyword in error_log_lower:
                return bug_type
        
        return '未知类型'
    
    def _assess_severity(self, error_log: str) -> str:
        """评估严重程度"""
        error_log_lower = error_log.lower()
        
        # 高严重性关键词
        high_severity_keywords = [
            'crash', 'fatal', 'critical', 'security', 'data loss',
            '崩溃', '致命', '严重', '安全', '数据丢失'
        ]
        
        # 中等严重性关键词
        medium_severity_keywords = [
            'error', 'exception', 'fail', 'timeout',
            '错误', '异常', '失败', '超时'
        ]
        
        # 低严重性关键词
        low_severity_keywords = [
            'warning', 'deprecated', 'minor',
            '警告', '弃用', '轻微'
        ]
        
        for keyword in high_severity_keywords:
            if keyword in error_log_lower:
                return '严重'
        
        for keyword in medium_severity_keywords:
            if keyword in error_log_lower:
                return '一般'
        
        for keyword in low_severity_keywords:
            if keyword in error_log_lower:
                return '轻微'
        
        return '一般'
    
    def _generate_basic_reproduce_steps(self, error_log: str) -> List[str]:
        """生成基础复现步骤"""
        steps = [
            "步骤1: 准备测试环境",
            "步骤2: 执行失败的测试用例",
            "步骤3: 观察错误现象"
        ]
        
        # 根据错误类型添加特定步骤
        error_log_lower = error_log.lower()
        
        if 'connection' in error_log_lower:
            steps.insert(1, "步骤1.5: 检查网络连接状态")
        elif 'timeout' in error_log_lower:
            steps.insert(1, "步骤1.5: 设置较长的超时时间")
        elif 'import' in error_log_lower:
            steps.insert(1, "步骤1.5: 检查依赖包安装情况")
        
        return steps
    
    def _calculate_confidence_score(self, bug_analysis: Dict[str, Any], error_log: str) -> float:
        """计算分析置信度"""
        confidence = 0.5  # 基础置信度
        
        # 根据分析完整性调整置信度
        if bug_analysis.get('root_cause') and len(bug_analysis['root_cause']) > 10:
            confidence += 0.2
        
        if bug_analysis.get('fix_suggestion') and len(bug_analysis['fix_suggestion']) > 20:
            confidence += 0.2
        
        if bug_analysis.get('reproduce_steps') and len(bug_analysis['reproduce_steps']) >= 3:
            confidence += 0.1
        
        # 根据错误日志清晰度调整
        if len(error_log) > 100 and 'traceback' in error_log.lower():
            confidence += 0.1
        
        return min(confidence, 1.0)
    
    def _enhance_bug_analysis(self, analysis: Dict[str, Any], error_log: str, test_context: str) -> Dict[str, Any]:
        """增强Bug分析"""
        enhanced_analysis = analysis.copy()
        
        # 添加错误模式识别
        enhanced_analysis['error_pattern'] = self._identify_error_pattern(error_log)
        
        # 添加相关测试建议
        enhanced_analysis['related_tests'] = self._suggest_related_tests(analysis, test_context)
        
        # 添加修复优先级
        enhanced_analysis['fix_priority'] = self._calculate_fix_priority(analysis)
        
        # 添加影响评估
        enhanced_analysis['impact_assessment'] = self._assess_impact(analysis, test_context)
        
        # 添加时间戳
        import datetime
        enhanced_analysis['analysis_timestamp'] = datetime.datetime.now().isoformat()
        
        return enhanced_analysis
    
    def _identify_error_pattern(self, error_log: str) -> Dict[str, Any]:
        """识别错误模式"""
        pattern = {
            'pattern_type': '未知模式',
            'frequency': '偶发',
            'environment_related': False,
            'data_related': False,
            'timing_related': False
        }
        
        error_log_lower = error_log.lower()
        
        # 识别模式类型
        if 'connection' in error_log_lower or 'network' in error_log_lower:
            pattern['pattern_type'] = '网络相关'
            pattern['environment_related'] = True
        elif 'timeout' in error_log_lower:
            pattern['pattern_type'] = '超时相关'
            pattern['timing_related'] = True
        elif 'data' in error_log_lower or 'key' in error_log_lower:
            pattern['pattern_type'] = '数据相关'
            pattern['data_related'] = True
        elif 'assert' in error_log_lower:
            pattern['pattern_type'] = '断言失败'
        
        # 评估频率
        if 'intermittent' in error_log_lower or 'random' in error_log_lower:
            pattern['frequency'] = '间歇性'
        elif 'always' in error_log_lower or 'consistent' in error_log_lower:
            pattern['frequency'] = '持续性'
        
        return pattern
    
    def _suggest_related_tests(self, analysis: Dict[str, Any], test_context: str) -> List[str]:
        """建议相关测试"""
        suggestions = []
        
        bug_type = analysis.get('bug_type', '')
        
        if '功能缺陷' in bug_type:
            suggestions.extend([
                '增加边界值测试',
                '补充异常输入测试',
                '添加集成测试'
            ])
        elif '性能问题' in bug_type:
            suggestions.extend([
                '添加性能基准测试',
                '增加负载测试',
                '补充并发测试'
            ])
        elif '网络问题' in bug_type:
            suggestions.extend([
                '添加网络异常测试',
                '增加重试机制测试',
                '补充超时处理测试'
            ])
        elif '数据问题' in bug_type:
            suggestions.extend([
                '增加数据验证测试',
                '补充数据格式测试',
                '添加数据边界测试'
            ])
        
        return suggestions
    
    def _calculate_fix_priority(self, analysis: Dict[str, Any]) -> str:
        """计算修复优先级"""
        severity = analysis.get('severity', '一般')
        impact_scope = analysis.get('impact_scope', '局部影响')
        
        # 优先级矩阵
        if severity == '严重':
            if '全局' in impact_scope or '系统' in impact_scope:
                return 'P0 - 紧急'
            else:
                return 'P1 - 高'
        elif severity == '一般':
            if '全局' in impact_scope:
                return 'P1 - 高'
            else:
                return 'P2 - 中'
        else:  # 轻微
            return 'P3 - 低'
    
    def _assess_impact(self, analysis: Dict[str, Any], test_context: str) -> Dict[str, Any]:
        """评估影响"""
        impact = {
            'user_impact': '低',
            'business_impact': '低',
            'system_stability': '稳定',
            'data_integrity': '安全'
        }
        
        severity = analysis.get('severity', '一般')
        bug_type = analysis.get('bug_type', '')
        
        if severity == '严重':
            impact['user_impact'] = '高'
            impact['business_impact'] = '高'
            
            if '崩溃' in analysis.get('root_cause', ''):
                impact['system_stability'] = '不稳定'
        
        if '数据' in bug_type or '安全' in bug_type:
            impact['data_integrity'] = '风险'
        
        return impact
    
    def _get_basic_bug_analysis(self, error_log: str, test_context: str) -> Dict[str, Any]:
        """获取基础Bug分析"""
        return {
            'bug_type': self._classify_bug_type(error_log),
            'root_cause': '需要进一步分析错误日志',
            'impact_scope': '局部影响',
            'severity': self._assess_severity(error_log),
            'reproduce_steps': self._generate_basic_reproduce_steps(error_log),
            'fix_suggestion': '请检查错误日志并联系开发团队',
            'prevention': '加强代码审查和测试覆盖',
            'test_recommendation': '补充相关的自动化测试用例',
            'confidence_score': 0.3,
            'error_pattern': self._identify_error_pattern(error_log),
            'related_tests': ['基础功能测试', '异常处理测试'],
            'fix_priority': 'P2 - 中',
            'impact_assessment': {
                'user_impact': '低',
                'business_impact': '低',
                'system_stability': '稳定',
                'data_integrity': '安全'
            }
        }
    
    def analyze_multiple_bugs(self, bug_reports: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析多个Bug"""
        if not bug_reports:
            return {'total_bugs': 0, 'analysis': []}
        
        analyses = []
        for bug_report in bug_reports:
            error_log = bug_report.get('error', '')
            context = bug_report.get('context', '')
            
            analysis = self.analyze_bug(error_log, context)
            analysis['original_report'] = bug_report
            analyses.append(analysis)
        
        # 生成汇总分析
        summary = self._generate_bug_summary(analyses)
        
        return {
            'total_bugs': len(analyses),
            'analyses': analyses,
            'summary': summary
        }
    
    def _generate_bug_summary(self, analyses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """生成Bug汇总分析"""
        summary = {
            'bug_type_distribution': {},
            'severity_distribution': {},
            'priority_distribution': {},
            'common_patterns': [],
            'fix_recommendations': [],
            'overall_assessment': ''
        }
        
        # 统计分布
        for analysis in analyses:
            bug_type = analysis.get('bug_type', '未知')
            severity = analysis.get('severity', '一般')
            priority = analysis.get('fix_priority', 'P2 - 中')
            
            summary['bug_type_distribution'][bug_type] = summary['bug_type_distribution'].get(bug_type, 0) + 1
            summary['severity_distribution'][severity] = summary['severity_distribution'].get(severity, 0) + 1
            summary['priority_distribution'][priority] = summary['priority_distribution'].get(priority, 0) + 1
        
        # 识别常见模式
        pattern_counts = {}
        for analysis in analyses:
            pattern = analysis.get('error_pattern', {}).get('pattern_type', '未知')
            pattern_counts[pattern] = pattern_counts.get(pattern, 0) + 1
        
        # 取前3个最常见的模式
        summary['common_patterns'] = sorted(pattern_counts.items(), key=lambda x: x[1], reverse=True)[:3]
        
        # 生成修复建议
        high_priority_bugs = [a for a in analyses if 'P0' in a.get('fix_priority', '') or 'P1' in a.get('fix_priority', '')]
        
        if high_priority_bugs:
            summary['fix_recommendations'].append('优先修复高优先级Bug')
        
        if len(analyses) > 5:
            summary['fix_recommendations'].append('建立Bug修复流程和跟踪机制')
        
        # 整体评估
        severe_count = len([a for a in analyses if a.get('severity') == '严重'])
        if severe_count > 0:
            summary['overall_assessment'] = f'发现{severe_count}个严重Bug，需要立即处理'
        elif len(analyses) > 10:
            summary['overall_assessment'] = 'Bug数量较多，建议系统性排查和修复'
        else:
            summary['overall_assessment'] = 'Bug数量在可控范围内，按优先级逐步修复'
        
        return summary
    
    def export_bug_report(self, bug_analysis: Dict[str, Any], output_file: str = None) -> str:
        """导出Bug分析报告"""
        if output_file is None:
            output_file = self.config.paths.reports_dir / 'bug_analysis_report.json'
        
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(bug_analysis, f, ensure_ascii=False, indent=2)
        
        return str(output_path)