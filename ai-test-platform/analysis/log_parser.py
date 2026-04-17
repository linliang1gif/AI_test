#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
AI Test Platform - 日志解析器

解析pytest测试日志，提取错误信息和失败详情。
"""

import re
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from config.config import get_config

class LogParser:
    """测试日志解析器"""
    
    def __init__(self):
        self.config = get_config()
    
    def parse_pytest_log(self, log_content: str) -> Dict[str, Any]:
        """解析pytest日志"""
        parsed_log = {
            'test_summary': self._extract_test_summary(log_content),
            'failed_tests': self._extract_failed_tests(log_content),
            'error_tests': self._extract_error_tests(log_content),
            'passed_tests': self._extract_passed_tests(log_content),
            'skipped_tests': self._extract_skipped_tests(log_content),
            'warnings': self._extract_warnings(log_content),
            'execution_info': self._extract_execution_info(log_content)
        }
        
        return parsed_log
    
    def _extract_test_summary(self, log_content: str) -> Dict[str, Any]:
        """提取测试摘要信息"""
        summary = {
            'total': 0,
            'passed': 0,
            'failed': 0,
            'error': 0,
            'skipped': 0,
            'warnings': 0,
            'duration': 0.0,
            'pass_rate': 0.0
        }
        
        # 查找摘要行
        summary_patterns = [
            r'(\d+) passed',
            r'(\d+) failed',
            r'(\d+) error',
            r'(\d+) skipped',
            r'(\d+) warnings?'
        ]
        
        for pattern in summary_patterns:
            matches = re.findall(pattern, log_content, re.IGNORECASE)
            if matches:
                count = int(matches[-1])  # 取最后一个匹配
                if 'passed' in pattern:
                    summary['passed'] = count
                elif 'failed' in pattern:
                    summary['failed'] = count
                elif 'error' in pattern:
                    summary['error'] = count
                elif 'skipped' in pattern:
                    summary['skipped'] = count
                elif 'warning' in pattern:
                    summary['warnings'] = count
        
        # 计算总数
        summary['total'] = summary['passed'] + summary['failed'] + summary['error'] + summary['skipped']
        
        # 计算通过率
        if summary['total'] > 0:
            summary['pass_rate'] = (summary['passed'] / summary['total']) * 100
        
        # 提取执行时间
        duration_match = re.search(r'in ([\d.]+)s', log_content)
        if duration_match:
            summary['duration'] = float(duration_match.group(1))
        
        return summary
    
    def _extract_failed_tests(self, log_content: str) -> List[Dict[str, Any]]:
        """提取失败的测试"""
        failed_tests = []
        
        # 查找FAILURES部分
        failures_match = re.search(r'FAILURES.*?(?=\n=|$)', log_content, re.DOTALL)
        if not failures_match:
            return failed_tests
        
        failures_section = failures_match.group(0)
        
        # 分割每个失败的测试
        test_blocks = re.split(r'_{20,}', failures_section)
        
        for block in test_blocks:
            if not block.strip():
                continue
            
            failed_test = self._parse_failure_block(block)
            if failed_test:
                failed_tests.append(failed_test)
        
        return failed_tests
    
    def _parse_failure_block(self, block: str) -> Optional[Dict[str, Any]]:
        """解析单个失败测试块"""
        lines = block.strip().split('\n')
        if not lines:
            return None
        
        failed_test = {
            'test_name': '',
            'file_path': '',
            'line_number': 0,
            'error_type': '',
            'error_message': '',
            'traceback': '',
            'assertion_error': '',
            'context': {}
        }
        
        # 提取测试名称
        for line in lines:
            if '::' in line and ('FAILED' in line or 'ERROR' in line):
                parts = line.split()
                if parts:
                    test_path = parts[0]
                    if '::' in test_path:
                        file_path, test_name = test_path.split('::', 1)
                        failed_test['test_name'] = test_name
                        failed_test['file_path'] = file_path
                break
        
        # 提取错误信息
        in_traceback = False
        traceback_lines = []
        
        for line in lines:
            line = line.strip()
            
            # 检测traceback开始
            if line.startswith('Traceback') or 'File "' in line:
                in_traceback = True
            
            if in_traceback:
                traceback_lines.append(line)
                
                # 提取文件和行号
                file_match = re.search(r'File "([^"]+)", line (\d+)', line)
                if file_match and not failed_test['line_number']:
                    failed_test['line_number'] = int(file_match.group(2))
                
                # 提取错误类型
                error_type_match = re.search(r'^(\w+Error|AssertionError|Exception):', line)
                if error_type_match:
                    failed_test['error_type'] = error_type_match.group(1)
                    failed_test['error_message'] = line
            
            # 提取断言错误
            if line.startswith('assert ') or 'AssertionError' in line:
                failed_test['assertion_error'] = line
        
        failed_test['traceback'] = '\n'.join(traceback_lines)
        
        return failed_test if failed_test['test_name'] else None
    
    def _extract_error_tests(self, log_content: str) -> List[Dict[str, Any]]:
        """提取错误的测试"""
        error_tests = []
        
        # 查找ERRORS部分
        errors_match = re.search(r'ERRORS.*?(?=\n=|$)', log_content, re.DOTALL)
        if not errors_match:
            return error_tests
        
        errors_section = errors_match.group(0)
        
        # 分割每个错误的测试
        test_blocks = re.split(r'_{20,}', errors_section)
        
        for block in test_blocks:
            if not block.strip():
                continue
            
            error_test = self._parse_error_block(block)
            if error_test:
                error_tests.append(error_test)
        
        return error_tests
    
    def _parse_error_block(self, block: str) -> Optional[Dict[str, Any]]:
        """解析单个错误测试块"""
        # 类似于失败测试的解析，但专注于setup/teardown错误
        return self._parse_failure_block(block)
    
    def _extract_passed_tests(self, log_content: str) -> List[Dict[str, str]]:
        """提取通过的测试"""
        passed_tests = []
        
        # 查找PASSED标记的行
        passed_pattern = r'([^\s]+::[^\s]+)\s+PASSED'
        matches = re.findall(passed_pattern, log_content)
        
        for match in matches:
            if '::' in match:
                file_path, test_name = match.split('::', 1)
                passed_tests.append({
                    'test_name': test_name,
                    'file_path': file_path,
                    'full_path': match
                })
        
        return passed_tests
    
    def _extract_skipped_tests(self, log_content: str) -> List[Dict[str, str]]:
        """提取跳过的测试"""
        skipped_tests = []
        
        # 查找SKIPPED标记的行
        skipped_pattern = r'([^\s]+::[^\s]+)\s+SKIPPED'
        matches = re.findall(skipped_pattern, log_content)
        
        for match in matches:
            if '::' in match:
                file_path, test_name = match.split('::', 1)
                skipped_tests.append({
                    'test_name': test_name,
                    'file_path': file_path,
                    'full_path': match
                })
        
        return skipped_tests
    
    def _extract_warnings(self, log_content: str) -> List[Dict[str, str]]:
        """提取警告信息"""
        warnings = []
        
        # 查找警告部分
        warnings_match = re.search(r'warnings summary.*?(?=\n=|$)', log_content, re.DOTALL | re.IGNORECASE)
        if not warnings_match:
            return warnings
        
        warnings_section = warnings_match.group(0)
        lines = warnings_section.split('\n')
        
        current_warning = {}
        for line in lines:
            line = line.strip()
            
            # 检测文件路径
            if line and not line.startswith('--') and ':' in line and '/' in line:
                if current_warning:
                    warnings.append(current_warning)
                
                current_warning = {
                    'file': line,
                    'message': '',
                    'category': ''
                }
            elif current_warning and line:
                if 'Warning' in line:
                    current_warning['category'] = line
                else:
                    current_warning['message'] += line + ' '
        
        if current_warning:
            warnings.append(current_warning)
        
        return warnings
    
    def _extract_execution_info(self, log_content: str) -> Dict[str, Any]:
        """提取执行信息"""
        execution_info = {
            'start_time': '',
            'end_time': '',
            'platform': '',
            'python_version': '',
            'pytest_version': '',
            'plugins': []
        }
        
        # 提取平台信息
        platform_match = re.search(r'platform (.+?) --', log_content)
        if platform_match:
            execution_info['platform'] = platform_match.group(1)
        
        # 提取Python版本
        python_match = re.search(r'Python ([\d.]+)', log_content)
        if python_match:
            execution_info['python_version'] = python_match.group(1)
        
        # 提取pytest版本
        pytest_match = re.search(r'pytest-([\d.]+)', log_content)
        if pytest_match:
            execution_info['pytest_version'] = pytest_match.group(1)
        
        # 提取插件信息
        plugins_match = re.search(r'plugins: (.+)', log_content)
        if plugins_match:
            plugins_str = plugins_match.group(1)
            execution_info['plugins'] = [p.strip() for p in plugins_str.split(',')]
        
        return execution_info
    
    def parse_log_file(self, log_file_path: str) -> Dict[str, Any]:
        """解析日志文件"""
        log_path = Path(log_file_path)
        
        if not log_path.exists():
            raise FileNotFoundError(f"日志文件不存在: {log_file_path}")
        
        try:
            with open(log_path, 'r', encoding='utf-8') as f:
                log_content = f.read()
            
            return self.parse_pytest_log(log_content)
            
        except UnicodeDecodeError:
            # 尝试其他编码
            with open(log_path, 'r', encoding='gbk') as f:
                log_content = f.read()
            
            return self.parse_pytest_log(log_content)
    
    def extract_error_patterns(self, failed_tests: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """提取错误模式"""
        error_patterns = {
            'assertion_errors': [],
            'connection_errors': [],
            'timeout_errors': [],
            'import_errors': [],
            'attribute_errors': [],
            'other_errors': []
        }
        
        for test in failed_tests:
            error_message = test.get('error_message', '').lower()
            error_type = test.get('error_type', '')
            
            if 'assertion' in error_type.lower():
                error_patterns['assertion_errors'].append(test['test_name'])
            elif 'connection' in error_message or 'network' in error_message:
                error_patterns['connection_errors'].append(test['test_name'])
            elif 'timeout' in error_message:
                error_patterns['timeout_errors'].append(test['test_name'])
            elif 'import' in error_type.lower():
                error_patterns['import_errors'].append(test['test_name'])
            elif 'attribute' in error_type.lower():
                error_patterns['attribute_errors'].append(test['test_name'])
            else:
                error_patterns['other_errors'].append(test['test_name'])
        
        return error_patterns
    
    def generate_log_summary(self, parsed_log: Dict[str, Any]) -> str:
        """生成日志摘要"""
        summary = parsed_log.get('test_summary', {})
        failed_tests = parsed_log.get('failed_tests', [])
        error_tests = parsed_log.get('error_tests', [])
        
        summary_text = f"""
📊 测试日志分析摘要
{'='*50}
总测试数: {summary.get('total', 0)}
通过: {summary.get('passed', 0)}
失败: {summary.get('failed', 0)}
错误: {summary.get('error', 0)}
跳过: {summary.get('skipped', 0)}
通过率: {summary.get('pass_rate', 0):.1f}%
执行时间: {summary.get('duration', 0):.2f}秒
"""
        
        if failed_tests:
            summary_text += f"\n❌ 失败测试详情:\n"
            for test in failed_tests[:5]:  # 只显示前5个
                summary_text += f"  - {test.get('test_name', '未知')}: {test.get('error_type', '未知错误')}\n"
        
        if error_tests:
            summary_text += f"\n🚫 错误测试详情:\n"
            for test in error_tests[:3]:  # 只显示前3个
                summary_text += f"  - {test.get('test_name', '未知')}: {test.get('error_type', '未知错误')}\n"
        
        return summary_text
    
    def save_parsed_log(self, parsed_log: Dict[str, Any], output_file: str = None) -> str:
        """保存解析后的日志"""
        if output_file is None:
            output_file = self.config.paths.reports_dir / 'parsed_test_log.json'
        
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(parsed_log, f, ensure_ascii=False, indent=2)
        
        return str(output_path)