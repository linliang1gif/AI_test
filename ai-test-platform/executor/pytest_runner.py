#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
AI Test Platform - pytest测试执行器

执行生成的pytest测试脚本并收集结果。
"""

import subprocess
import json
import time
from pathlib import Path
from typing import Dict, Any, List
from config.config import get_config

class PytestRunner:
    """pytest测试执行器"""
    
    def __init__(self):
        self.config = get_config()
    
    def run_tests(self, test_path: str = None, markers: str = None) -> Dict[str, Any]:
        """运行pytest测试"""
        if test_path is None:
            test_path = str(self.config.paths.tests_dir)
        
        # 构建pytest命令
        cmd = self._build_pytest_command(test_path, markers)
        
        print(f"🧪 执行pytest命令: {' '.join(cmd)}")
        
        try:
            # 执行pytest
            start_time = time.time()
            result = subprocess.run(
                cmd,
                cwd=self.config.paths.tests_dir.parent,
                capture_output=True,
                text=True,
                timeout=300  # 5分钟超时
            )
            end_time = time.time()
            
            # 解析结果
            test_results = self._parse_pytest_output(result, end_time - start_time)
            
            # 保存结果
            self._save_test_results(test_results)
            
            return test_results
            
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'error': '测试执行超时',
                'execution_time': 300
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'execution_time': 0
            }
    
    def _build_pytest_command(self, test_path: str, markers: str = None) -> List[str]:
        """构建pytest命令"""
        cmd = ['python', '-m', 'pytest']
        
        # 添加测试路径
        cmd.append(test_path)
        
        # 添加输出格式
        cmd.extend(['-v', '--tb=short'])
        
        # 添加JSON报告
        json_report = self.config.paths.reports_dir / 'pytest_report.json'
        cmd.extend(['--json-report', f'--json-report-file={json_report}'])
        
        # 添加HTML报告
        html_report = self.config.paths.reports_dir / 'pytest_report.html'
        cmd.extend(['--html', str(html_report), '--self-contained-html'])
        
        # 添加标记过滤
        if markers:
            cmd.extend(['-m', markers])
        
        # 添加其他选项
        cmd.extend([
            '--strict-markers',  # 严格标记模式
            '--disable-warnings',  # 禁用警告
            '-x'  # 遇到第一个失败就停止
        ])
        
        return cmd
    
    def _parse_pytest_output(self, result: subprocess.CompletedProcess, execution_time: float) -> Dict[str, Any]:
        """解析pytest输出"""
        test_results = {
            'success': result.returncode == 0,
            'execution_time': execution_time,
            'return_code': result.returncode,
            'stdout': result.stdout,
            'stderr': result.stderr,
            'summary': {},
            'failures': [],
            'errors': [],
            'passed_tests': [],
            'skipped_tests': []
        }
        
        # 尝试读取JSON报告
        json_report_path = self.config.paths.reports_dir / 'pytest_report.json'
        if json_report_path.exists():
            try:
                with open(json_report_path, 'r', encoding='utf-8') as f:
                    json_report = json.load(f)
                
                test_results.update(self._parse_json_report(json_report))
            except Exception as e:
                print(f"解析JSON报告失败: {str(e)}")
        
        # 解析文本输出
        if not test_results.get('summary'):
            test_results.update(self._parse_text_output(result.stdout))
        
        return test_results
    
    def _parse_json_report(self, json_report: Dict[str, Any]) -> Dict[str, Any]:
        """解析JSON报告"""
        summary = json_report.get('summary', {})
        tests = json_report.get('tests', [])
        
        parsed_results = {
            'summary': {
                'total': summary.get('total', 0),
                'passed': summary.get('passed', 0),
                'failed': summary.get('failed', 0),
                'error': summary.get('error', 0),
                'skipped': summary.get('skipped', 0),
                'pass_rate': 0
            },
            'failures': [],
            'errors': [],
            'passed_tests': [],
            'skipped_tests': []
        }
        
        # 计算通过率
        total = parsed_results['summary']['total']
        if total > 0:
            passed = parsed_results['summary']['passed']
            parsed_results['summary']['pass_rate'] = (passed / total) * 100
        
        # 解析测试详情
        for test in tests:
            test_info = {
                'nodeid': test.get('nodeid', ''),
                'outcome': test.get('outcome', ''),
                'duration': test.get('duration', 0),
                'setup_duration': test.get('setup', {}).get('duration', 0),
                'call_duration': test.get('call', {}).get('duration', 0),
                'teardown_duration': test.get('teardown', {}).get('duration', 0)
            }
            
            if test['outcome'] == 'passed':
                parsed_results['passed_tests'].append(test_info)
            elif test['outcome'] == 'failed':
                test_info['error'] = test.get('call', {}).get('longrepr', '')
                test_info['context'] = self._extract_test_context(test)
                parsed_results['failures'].append(test_info)
            elif test['outcome'] == 'error':
                test_info['error'] = test.get('setup', {}).get('longrepr', '') or test.get('call', {}).get('longrepr', '')
                parsed_results['errors'].append(test_info)
            elif test['outcome'] == 'skipped':
                test_info['reason'] = test.get('call', {}).get('longrepr', '')
                parsed_results['skipped_tests'].append(test_info)
        
        return parsed_results
    
    def _extract_test_context(self, test: Dict[str, Any]) -> str:
        """提取测试上下文信息"""
        context_parts = []
        
        # 测试文件和函数
        nodeid = test.get('nodeid', '')
        if '::' in nodeid:
            file_path, test_name = nodeid.split('::', 1)
            context_parts.append(f"测试文件: {file_path}")
            context_parts.append(f"测试函数: {test_name}")
        
        # 测试参数
        if 'keywords' in test:
            keywords = test['keywords']
            if keywords:
                context_parts.append(f"测试标记: {', '.join(keywords)}")
        
        return '\n'.join(context_parts)
    
    def _parse_text_output(self, stdout: str) -> Dict[str, Any]:
        """解析文本输出"""
        lines = stdout.split('\n')
        
        parsed_results = {
            'summary': {
                'total': 0,
                'passed': 0,
                'failed': 0,
                'error': 0,
                'skipped': 0,
                'pass_rate': 0
            },
            'failures': [],
            'errors': []
        }
        
        # 查找摘要行
        for line in lines:
            line = line.strip()
            
            # 解析pytest摘要行
            if 'passed' in line or 'failed' in line or 'error' in line:
                if '=' in line and ('passed' in line or 'failed' in line):
                    # 提取数字
                    import re
                    
                    passed_match = re.search(r'(\d+) passed', line)
                    failed_match = re.search(r'(\d+) failed', line)
                    error_match = re.search(r'(\d+) error', line)
                    skipped_match = re.search(r'(\d+) skipped', line)
                    
                    if passed_match:
                        parsed_results['summary']['passed'] = int(passed_match.group(1))
                    if failed_match:
                        parsed_results['summary']['failed'] = int(failed_match.group(1))
                    if error_match:
                        parsed_results['summary']['error'] = int(error_match.group(1))
                    if skipped_match:
                        parsed_results['summary']['skipped'] = int(skipped_match.group(1))
                    
                    # 计算总数和通过率
                    summary = parsed_results['summary']
                    summary['total'] = summary['passed'] + summary['failed'] + summary['error'] + summary['skipped']
                    
                    if summary['total'] > 0:
                        summary['pass_rate'] = (summary['passed'] / summary['total']) * 100
                    
                    break
        
        # 提取失败信息
        failure_section = False
        current_failure = {}
        
        for line in lines:
            if 'FAILURES' in line:
                failure_section = True
                continue
            
            if failure_section:
                if line.startswith('_'):  # 测试分隔符
                    if current_failure:
                        parsed_results['failures'].append(current_failure)
                        current_failure = {}
                elif '::' in line and 'FAILED' in line:
                    current_failure = {
                        'nodeid': line.split()[0],
                        'error': '',
                        'context': line
                    }
                elif current_failure and line.strip():
                    current_failure['error'] += line + '\n'
        
        # 添加最后一个失败
        if current_failure:
            parsed_results['failures'].append(current_failure)
        
        return parsed_results
    
    def _save_test_results(self, test_results: Dict[str, Any]) -> None:
        """保存测试结果"""
        results_file = self.config.paths.reports_dir / 'test_execution_results.json'
        
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(test_results, f, ensure_ascii=False, indent=2)
        
        print(f"📊 测试结果已保存: {results_file}")
    
    def run_specific_tests(self, test_files: List[str]) -> Dict[str, Any]:
        """运行指定的测试文件"""
        results = {}
        
        for test_file in test_files:
            test_path = self.config.paths.tests_dir / test_file
            if test_path.exists():
                print(f"🧪 运行测试文件: {test_file}")
                result = self.run_tests(str(test_path))
                results[test_file] = result
            else:
                print(f"❌ 测试文件不存在: {test_file}")
                results[test_file] = {
                    'success': False,
                    'error': f'文件不存在: {test_file}'
                }
        
        return results
    
    def run_smoke_tests(self) -> Dict[str, Any]:
        """运行冒烟测试"""
        print("🔥 运行冒烟测试...")
        return self.run_tests(markers='smoke')
    
    def run_regression_tests(self) -> Dict[str, Any]:
        """运行回归测试"""
        print("🔄 运行回归测试...")
        return self.run_tests(markers='regression')
    
    def generate_test_summary(self, test_results: Dict[str, Any]) -> str:
        """生成测试摘要"""
        if not test_results.get('success', False):
            return f"❌ 测试执行失败: {test_results.get('error', '未知错误')}"
        
        summary = test_results.get('summary', {})
        
        summary_text = f"""
📊 测试执行摘要
{'='*50}
总用例数: {summary.get('total', 0)}
通过数: {summary.get('passed', 0)}
失败数: {summary.get('failed', 0)}
错误数: {summary.get('error', 0)}
跳过数: {summary.get('skipped', 0)}
通过率: {summary.get('pass_rate', 0):.1f}%
执行时间: {test_results.get('execution_time', 0):.2f}秒
"""
        
        # 添加失败详情
        failures = test_results.get('failures', [])
        if failures:
            summary_text += f"\n❌ 失败用例 ({len(failures)}个):\n"
            for i, failure in enumerate(failures[:5], 1):  # 只显示前5个
                summary_text += f"  {i}. {failure.get('nodeid', '未知测试')}\n"
            
            if len(failures) > 5:
                summary_text += f"  ... 还有 {len(failures) - 5} 个失败用例\n"
        
        return summary_text
    
    def check_test_environment(self) -> Dict[str, Any]:
        """检查测试环境"""
        env_check = {
            'pytest_available': False,
            'test_files_exist': False,
            'dependencies_installed': False,
            'issues': []
        }
        
        # 检查pytest是否可用
        try:
            result = subprocess.run(['python', '-m', 'pytest', '--version'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                env_check['pytest_available'] = True
            else:
                env_check['issues'].append('pytest未安装或不可用')
        except Exception:
            env_check['issues'].append('无法执行pytest命令')
        
        # 检查测试文件是否存在
        tests_dir = self.config.paths.tests_dir
        if tests_dir.exists():
            test_files = list(tests_dir.glob('test_*.py'))
            if test_files:
                env_check['test_files_exist'] = True
            else:
                env_check['issues'].append('未找到测试文件')
        else:
            env_check['issues'].append('测试目录不存在')
        
        # 检查依赖是否安装
        try:
            import requests
            env_check['dependencies_installed'] = True
        except ImportError:
            env_check['issues'].append('requests库未安装')
        
        return env_check