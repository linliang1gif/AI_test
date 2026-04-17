#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
断言知识库集成 - 将断言结果存入知识库,支持学习和优化
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from assertion.assertion_engine import AssertionResult
from assertion.assertion_types import AssertionConfig


class AssertionKnowledgeIntegration:
    """断言知识库集成"""
    
    def __init__(self, knowledge_manager=None):
        """
        初始化
        
        Args:
            knowledge_manager: 知识管理器实例
        """
        self.knowledge_manager = knowledge_manager
        self.assertion_history: List[Dict] = []
    
    def record_assertion_result(self, config: AssertionConfig,
                               result: AssertionResult,
                               context: Dict) -> str:
        """
        记录断言结果到知识库
        
        Args:
            config: 断言配置
            result: 断言结果
            context: 上下文信息 {
                'test_case_id': '...',
                'api_endpoint': '...',
                'request_data': {...},
                'response_data': {...}
            }
        
        Returns:
            记录ID
        """
        record = {
            'record_id': self._generate_id(),
            'timestamp': datetime.now().isoformat(),
            'assertion_config': config.to_dict(),
            'assertion_result': result.to_dict(),
            'context': context,
            'passed': result.passed
        }
        
        # 添加到历史
        self.assertion_history.append(record)
        
        # 存入知识库
        if self.knowledge_manager:
            try:
                self.knowledge_manager.add_assertion_result(record)
            except Exception as e:
                print(f"存入知识库失败: {e}")
        
        return record['record_id']
    
    def record_assertion_failure(self, config: AssertionConfig,
                                 result: AssertionResult,
                                 context: Dict) -> str:
        """
        记录断言失败(重点关注)
        
        Args:
            config: 断言配置
            result: 断言结果
            context: 上下文信息
        
        Returns:
            失败记录ID
        """
        if result.passed:
            return ""
        
        failure_record = {
            'failure_id': self._generate_id(),
            'timestamp': datetime.now().isoformat(),
            'assertion_name': config.name,
            'assertion_description': config.description,
            'expected': result.expected,
            'actual': result.actual,
            'severity': config.severity.value,
            'error_message': result.message,
            'context': context,
            'tags': config.tags
        }
        
        # 存入知识库
        if self.knowledge_manager:
            try:
                self.knowledge_manager.add_assertion_failure(failure_record)
            except Exception as e:
                print(f"记录断言失败失败: {e}")
        
        return failure_record['failure_id']
    
    def find_similar_assertion_failures(self, config: AssertionConfig,
                                       limit: int = 5) -> List[Dict]:
        """
        查找相似的断言失败
        
        Args:
            config: 断言配置
            limit: 返回数量限制
        
        Returns:
            相似失败列表
        """
        if not self.knowledge_manager:
            return []
        
        try:
            query = f"{config.name} {config.description}"
            similar = self.knowledge_manager.find_similar_assertion_failures(
                query, limit=limit
            )
            return similar
        except Exception as e:
            print(f"查找相似失败失败: {e}")
            return []
    
    def get_assertion_success_rate(self, assertion_name: str) -> float:
        """
        获取断言的历史成功率
        
        Args:
            assertion_name: 断言名称
        
        Returns:
            成功率 (0.0-1.0)
        """
        matching_records = [
            r for r in self.assertion_history
            if r['assertion_config']['name'] == assertion_name
        ]
        
        if not matching_records:
            return 1.0  # 没有历史记录,默认100%
        
        passed_count = sum(1 for r in matching_records if r['passed'])
        return passed_count / len(matching_records)
    
    def get_assertion_statistics(self) -> Dict:
        """
        获取断言统计信息
        
        Returns:
            统计信息
        """
        total = len(self.assertion_history)
        if total == 0:
            return {
                'total': 0,
                'passed': 0,
                'failed': 0,
                'pass_rate': 0.0
            }
        
        passed = sum(1 for r in self.assertion_history if r['passed'])
        failed = total - passed
        
        # 按断言类型统计
        by_type = {}
        for record in self.assertion_history:
            assertion_name = record['assertion_config']['name']
            if assertion_name not in by_type:
                by_type[assertion_name] = {'total': 0, 'passed': 0, 'failed': 0}
            
            by_type[assertion_name]['total'] += 1
            if record['passed']:
                by_type[assertion_name]['passed'] += 1
            else:
                by_type[assertion_name]['failed'] += 1
        
        # 计算每个断言的成功率
        for name, stats in by_type.items():
            stats['pass_rate'] = stats['passed'] / stats['total']
        
        return {
            'total': total,
            'passed': passed,
            'failed': failed,
            'pass_rate': passed / total,
            'by_assertion': by_type
        }
    
    def suggest_assertion_improvements(self, config: AssertionConfig) -> List[str]:
        """
        建议断言改进
        
        Args:
            config: 断言配置
        
        Returns:
            改进建议列表
        """
        suggestions = []
        
        # 检查成功率
        success_rate = self.get_assertion_success_rate(config.name)
        if success_rate < 0.5:
            suggestions.append(
                f"断言 '{config.name}' 成功率较低({success_rate:.1%}), "
                f"建议检查期望值是否合理"
            )
        
        # 检查严重程度
        if config.severity.value == 'trivial' and success_rate < 0.8:
            suggestions.append(
                f"断言 '{config.name}' 虽然是轻微级,但失败率较高, "
                f"建议提升严重程度或调整断言条件"
            )
        
        # 查找相似失败
        similar_failures = self.find_similar_assertion_failures(config)
        if similar_failures:
            suggestions.append(
                f"发现 {len(similar_failures)} 个相似的断言失败, "
                f"建议参考历史失败原因"
            )
        
        return suggestions
    
    def export_assertion_knowledge(self, output_file: str):
        """
        导出断言知识
        
        Args:
            output_file: 输出文件路径
        """
        knowledge = {
            'export_time': datetime.now().isoformat(),
            'statistics': self.get_assertion_statistics(),
            'history': self.assertion_history
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(knowledge, f, ensure_ascii=False, indent=2)
        
        print(f"断言知识已导出到: {output_file}")
    
    def import_assertion_knowledge(self, input_file: str):
        """
        导入断言知识
        
        Args:
            input_file: 输入文件路径
        """
        with open(input_file, 'r', encoding='utf-8') as f:
            knowledge = json.load(f)
        
        self.assertion_history.extend(knowledge.get('history', []))
        print(f"已导入 {len(knowledge.get('history', []))} 条断言记录")
    
    def _generate_id(self) -> str:
        """生成唯一ID"""
        import uuid
        return str(uuid.uuid4())[:8]


# 使用示例
if __name__ == "__main__":
    from assertion.assertion_builder import AssertionBuilder
    from assertion.assertion_validator import AssertionValidator
    from assertion.assertion_engine import AssertionResult, AssertionType
    
    # 创建集成实例
    integration = AssertionKnowledgeIntegration()
    
    # 创建断言配置
    builder = AssertionBuilder()
    configs = (builder
               .new_assertion("状态码200").equals(200).at_path("status_code").blocker()
               .new_assertion("返回码为0").equals(0).at_path("body.code").critical()
               .build())
    
    # 模拟测试执行
    print("模拟测试执行...")
    
    # 第1次执行 - 成功
    response_data_1 = {
        'status_code': 200,
        'body': {'code': 0, 'data': {}}
    }
    
    validator = AssertionValidator()
    results_1 = validator.validate_all(configs, response_data_1)
    
    for config, result in zip(configs, results_1):
        record_id = integration.record_assertion_result(
            config, result,
            context={
                'test_case_id': 'TC001',
                'api_endpoint': '/api/test',
                'response_data': response_data_1
            }
        )
        print(f"记录断言结果: {record_id} - {result.passed}")
    
    # 第2次执行 - 失败
    response_data_2 = {
        'status_code': 500,
        'body': {'code': -1, 'error': 'Internal Error'}
    }
    
    validator2 = AssertionValidator()
    results_2 = validator2.validate_all(configs, response_data_2)
    
    for config, result in zip(configs, results_2):
        record_id = integration.record_assertion_result(
            config, result,
            context={
                'test_case_id': 'TC001',
                'api_endpoint': '/api/test',
                'response_data': response_data_2
            }
        )
        print(f"记录断言结果: {record_id} - {result.passed}")
        
        if not result.passed:
            failure_id = integration.record_assertion_failure(
                config, result,
                context={'test_case_id': 'TC001'}
            )
            print(f"  记录失败: {failure_id}")
    
    # 获取统计信息
    print("\n断言统计:")
    stats = integration.get_assertion_statistics()
    print(f"总计: {stats['total']}")
    print(f"通过: {stats['passed']}")
    print(f"失败: {stats['failed']}")
    print(f"通过率: {stats['pass_rate']:.1%}")
    
    print("\n按断言统计:")
    for name, assertion_stats in stats['by_assertion'].items():
        print(f"  {name}:")
        print(f"    通过率: {assertion_stats['pass_rate']:.1%}")
        print(f"    总计: {assertion_stats['total']}")
    
    # 获取改进建议
    print("\n改进建议:")
    for config in configs:
        suggestions = integration.suggest_assertion_improvements(config)
        if suggestions:
            print(f"\n{config.name}:")
            for suggestion in suggestions:
                print(f"  - {suggestion}")
    
    # 导出知识
    output_file = "assertion_knowledge.json"
    integration.export_assertion_knowledge(output_file)
    print(f"\n知识已导出到: {output_file}")
