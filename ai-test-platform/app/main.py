#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
AI Test Platform - 主流程

实现完整的测试生命周期：
需求 → AI测试策略 → AI功能模块拆分 → AI生成测试点 → AI生成测试场景矩阵 → 
AI生成完整测试用例 → 解析接口文档 → 自动生成接口自动化脚本 → 执行pytest测试 → 
AI分析Bug → 生成测试报告
"""

import sys
import json
import time
from pathlib import Path
from typing import Dict, List, Any

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent.parent))

from config.config import get_config
from parser.requirement_parser import RequirementParser, create_sample_requirement
from parser.swagger_parser import SwaggerParser, create_sample_swagger
from test_design.module_splitter import ModuleSplitter
from test_design.testpoint_generator import TestPointGenerator
from test_design.scenario_matrix_generator import ScenarioMatrixGenerator
from test_design.testcase_generator import TestCaseGenerator
from automation.api_script_generator import ApiScriptGenerator
from executor.pytest_runner import PytestRunner
from analysis.log_parser import LogParser
from analysis.bug_reasoner import BugReasoner
from report.report_generator import ReportGenerator
from export.excel_exporter import ExcelExporter

class AITestPlatform:
    """AI测试平台主类"""
    
    def __init__(self):
        self.config = get_config()
        
        # 初始化各个组件
        self.requirement_parser = RequirementParser()
        self.swagger_parser = SwaggerParser()
        self.module_splitter = ModuleSplitter()
        self.testpoint_generator = TestPointGenerator()
        self.scenario_generator = ScenarioMatrixGenerator()
        self.testcase_generator = TestCaseGenerator()
        self.api_script_generator = ApiScriptGenerator()
        self.pytest_runner = PytestRunner()
        self.log_parser = LogParser()
        self.bug_reasoner = BugReasoner()
        self.report_generator = ReportGenerator()
        self.excel_exporter = ExcelExporter()
        
        # 存储中间结果
        self.results = {}
    
    def run_complete_workflow(self, requirement_file: str = None, swagger_file: str = None) -> Dict[str, Any]:
        """运行完整的测试工作流程"""
        print("🚀 启动 AI Test Platform 完整工作流程")
        print("=" * 60)
        
        try:
            # 步骤1: 读取需求
            print("\n📄 步骤1: 读取需求文档")
            requirement = self._load_requirement(requirement_file)
            self.results['requirement'] = requirement
            print(f"✅ 需求文档读取完成，长度: {len(requirement)} 字符")
            
            # 步骤2: AI生成测试策略
            print("\n🧠 步骤2: AI生成测试策略")
            test_strategy = self._generate_test_strategy(requirement)
            self.results['test_strategy'] = test_strategy
            print("✅ 测试策略生成完成")
            
            # 步骤3: AI功能模块拆分
            print("\n🔧 步骤3: AI功能模块拆分")
            modules = self._split_modules(requirement)
            self.results['modules'] = modules
            print(f"✅ 模块拆分完成，共识别 {len(modules)} 个模块")
            
            # 步骤4: AI生成测试点
            print("\n🎯 步骤4: AI生成测试点")
            testpoints = self._generate_testpoints(modules)
            self.results['testpoints'] = testpoints
            total_testpoints = sum(len(tp) for tp in testpoints.values())
            print(f"✅ 测试点生成完成，共生成 {total_testpoints} 个测试点")
            
            # 步骤5: AI生成测试场景矩阵
            print("\n📊 步骤5: AI生成测试场景矩阵")
            scenarios = self._generate_scenarios(testpoints)
            self.results['scenarios'] = scenarios
            total_scenarios = sum(len(sc) for sc in scenarios.values())
            print(f"✅ 测试场景矩阵生成完成，共生成 {total_scenarios} 个场景")
            
            # 步骤6: AI生成完整测试用例
            print("\n📝 步骤6: AI生成完整测试用例")
            testcases = self._generate_testcases(modules, scenarios)
            self.results['testcases'] = testcases
            total_testcases = sum(len(tc) for tc in testcases.values())
            print(f"✅ 测试用例生成完成，共生成 {total_testcases} 个测试用例")
            
            # 步骤7: 导出Excel测试用例
            print("\n📊 步骤7: 导出Excel测试用例")
            excel_file = self._export_testcases_excel(testcases)
            self.results['excel_file'] = excel_file
            print(f"✅ Excel测试用例导出完成: {excel_file}")
            
            # 步骤8: 解析接口文档
            print("\n🔍 步骤8: 解析接口文档")
            apis = self._parse_swagger(swagger_file)
            self.results['apis'] = apis
            print(f"✅ 接口文档解析完成，共解析 {len(apis)} 个接口")
            
            # 步骤9: 自动生成接口自动化脚本
            print("\n🤖 步骤9: 自动生成接口自动化脚本")
            scripts = self._generate_api_scripts(apis, testcases)
            self.results['scripts'] = scripts
            print(f"✅ 自动化脚本生成完成，共生成 {len(scripts)} 个脚本文件")
            
            # 步骤10: 执行pytest测试
            print("\n🧪 步骤10: 执行pytest测试")
            test_results = self._run_pytest_tests()
            self.results['test_results'] = test_results
            print(f"✅ pytest测试执行完成")
            
            # 步骤11: AI分析Bug
            print("\n🔍 步骤11: AI分析Bug")
            bug_analysis = self._analyze_bugs(test_results)
            self.results['bug_analysis'] = bug_analysis
            print(f"✅ Bug分析完成")
            
            # 步骤12: 生成测试报告
            print("\n📋 步骤12: 生成测试报告")
            report = self._generate_report()
            self.results['report'] = report
            print(f"✅ 测试报告生成完成: {report}")
            
            print("\n🎉 AI Test Platform 工作流程全部完成!")
            print("=" * 60)
            
            return {
                'success': True,
                'results': self.results,
                'summary': self._generate_workflow_summary()
            }
            
        except Exception as e:
            print(f"\n❌ 工作流程执行失败: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'results': self.results
            }
    
    def _load_requirement(self, requirement_file: str = None) -> str:
        """加载需求文档"""
        try:
            return self.requirement_parser.read_requirement_file(requirement_file)
        except FileNotFoundError:
            print("📝 需求文件不存在，创建示例需求文档...")
            create_sample_requirement()
            return self.requirement_parser.read_requirement_file()
    
    def _generate_test_strategy(self, requirement: str) -> str:
        """生成测试策略"""
        from ai.ai_client import get_ai_client
        from ai.prompt_library import PromptLibrary
        
        ai_client = get_ai_client()
        prompt_lib = PromptLibrary()
        
        prompt = prompt_lib.get_test_strategy_prompt(requirement)
        system_prompt = prompt_lib.get_system_prompt()
        
        strategy = ai_client.generate_text(prompt, system_prompt)
        
        # 保存测试策略
        strategy_file = self.config.paths.output_dir / "test_strategy.md"
        with open(strategy_file, 'w', encoding='utf-8') as f:
            f.write(strategy)
        
        return strategy
    
    def _split_modules(self, requirement: str) -> List[Dict[str, Any]]:
        """拆分功能模块"""
        modules = self.module_splitter.split_modules(requirement)
        
        # 保存模块信息
        modules_file = self.config.paths.output_dir / "modules.json"
        with open(modules_file, 'w', encoding='utf-8') as f:
            json.dump(modules, f, ensure_ascii=False, indent=2)
        
        return modules
    
    def _generate_testpoints(self, modules: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """生成测试点"""
        testpoints = self.testpoint_generator.generate_testpoints(modules)
        
        # 保存测试点
        testpoints_file = self.config.paths.output_dir / "testpoints.json"
        with open(testpoints_file, 'w', encoding='utf-8') as f:
            json.dump(testpoints, f, ensure_ascii=False, indent=2)
        
        return testpoints
    
    def _generate_scenarios(self, testpoints: Dict[str, List[Dict[str, Any]]]) -> Dict[str, List[Dict[str, Any]]]:
        """生成测试场景矩阵"""
        scenarios = self.scenario_generator.generate_scenario_matrix(testpoints)
        
        # 保存场景矩阵
        scenarios_file = self.config.paths.output_dir / "scenarios.json"
        with open(scenarios_file, 'w', encoding='utf-8') as f:
            json.dump(scenarios, f, ensure_ascii=False, indent=2)
        
        return scenarios
    
    def _generate_testcases(self, modules: List[Dict[str, Any]], scenarios: Dict[str, List[Dict[str, Any]]]) -> Dict[str, List[Dict[str, Any]]]:
        """生成测试用例"""
        testcases = self.testcase_generator.generate_testcases(modules, scenarios)
        
        # 保存测试用例
        testcases_file = self.config.paths.output_dir / "testcases.json"
        with open(testcases_file, 'w', encoding='utf-8') as f:
            json.dump(testcases, f, ensure_ascii=False, indent=2)
        
        return testcases
    
    def _export_testcases_excel(self, testcases: Dict[str, List[Dict[str, Any]]]) -> str:
        """导出测试用例到Excel"""
        excel_data = self.testcase_generator.export_testcases_excel_format(testcases)
        excel_file = self.excel_exporter.export_testcases(excel_data)
        return str(excel_file)
    
    def _parse_swagger(self, swagger_file: str = None) -> List[Dict[str, Any]]:
        """解析Swagger文档"""
        try:
            self.swagger_parser.load_swagger_file(swagger_file)
            return self.swagger_parser.parse_apis()
        except FileNotFoundError:
            print("📝 Swagger文件不存在，创建示例Swagger文档...")
            create_sample_swagger()
            self.swagger_parser.load_swagger_file()
            return self.swagger_parser.parse_apis()
    
    def _generate_api_scripts(self, apis: List[Dict[str, Any]], testcases: Dict[str, List[Dict[str, Any]]]) -> Dict[str, str]:
        """生成API自动化脚本"""
        # 将测试用例转换为API测试用例格式
        api_testcases = self._convert_to_api_testcases(testcases, apis)
        
        # 生成脚本
        scripts = self.api_script_generator.generate_api_scripts(api_testcases)
        
        return scripts
    
    def _convert_to_api_testcases(self, testcases: Dict[str, List[Dict[str, Any]]], apis: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """将测试用例转换为API测试用例格式"""
        api_testcases = []
        
        for module_name, module_testcases in testcases.items():
            for testcase in module_testcases:
                # 尝试匹配API
                matched_api = self._match_api_for_testcase(testcase, apis)
                
                if matched_api:
                    api_testcase = {
                        'id': testcase['id'],
                        'title': testcase['title'],
                        'api_name': matched_api['name'],
                        'method': matched_api['method'],
                        'url': matched_api['path'],
                        'headers': {'Content-Type': 'application/json'},
                        'request_data': self._generate_request_data(matched_api),
                        'expected_status': 200,
                        'expected_response': {'result': 'success'},
                        'test_type': testcase['type'],
                        'priority': testcase['priority']
                    }
                    api_testcases.append(api_testcase)
        
        return api_testcases
    
    def _match_api_for_testcase(self, testcase: Dict[str, Any], apis: List[Dict[str, Any]]) -> Dict[str, Any]:
        """为测试用例匹配对应的API"""
        testcase_title = testcase['title'].lower()
        
        # 关键词匹配
        keywords_mapping = {
            '登录': ['login'],
            '注册': ['register'],
            '查询': ['get', 'query', 'search'],
            '创建': ['post', 'create'],
            '更新': ['put', 'update'],
            '删除': ['delete']
        }
        
        for keyword, api_keywords in keywords_mapping.items():
            if keyword in testcase_title:
                for api in apis:
                    api_name = api['name'].lower()
                    api_path = api['path'].lower()
                    
                    if any(ak in api_name or ak in api_path for ak in api_keywords):
                        return api
        
        # 如果没有匹配到，返回第一个API
        return apis[0] if apis else None
    
    def _generate_request_data(self, api: Dict[str, Any]) -> Dict[str, Any]:
        """为API生成请求数据"""
        request_body = api.get('request_body', {})
        
        if request_body and 'example' in request_body:
            return request_body['example']
        
        # 根据API路径生成默认数据
        path = api['path'].lower()
        
        if 'login' in path:
            return {'username': 'testuser', 'password': 'password123'}
        elif 'register' in path:
            return {'email': 'test@example.com', 'password': 'password123', 'phone': '13800138000'}
        elif 'profile' in path:
            return {'nickname': 'Test User', 'phone': '13800138000'}
        else:
            return {'id': 1, 'name': 'test'}
    
    def _run_pytest_tests(self) -> Dict[str, Any]:
        """执行pytest测试"""
        return self.pytest_runner.run_tests()
    
    def _analyze_bugs(self, test_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """分析Bug"""
        if not test_results.get('failures'):
            return []
        
        bug_analyses = []
        for failure in test_results['failures']:
            analysis = self.bug_reasoner.analyze_bug(failure['error'], failure.get('context', ''))
            bug_analyses.append(analysis)
        
        return bug_analyses
    
    def _generate_report(self) -> str:
        """生成测试报告"""
        report_data = {
            'test_strategy': self.results.get('test_strategy', ''),
            'modules': self.results.get('modules', []),
            'testpoints': self.results.get('testpoints', {}),
            'scenarios': self.results.get('scenarios', {}),
            'testcases': self.results.get('testcases', {}),
            'test_results': self.results.get('test_results', {}),
            'bug_analysis': self.results.get('bug_analysis', [])
        }
        
        report_file = self.report_generator.generate_report(report_data)
        return str(report_file)
    
    def _generate_workflow_summary(self) -> Dict[str, Any]:
        """生成工作流程摘要"""
        modules = self.results.get('modules', [])
        testpoints = self.results.get('testpoints', {})
        scenarios = self.results.get('scenarios', {})
        testcases = self.results.get('testcases', {})
        test_results = self.results.get('test_results', {})
        
        return {
            'modules_count': len(modules),
            'testpoints_count': sum(len(tp) for tp in testpoints.values()),
            'scenarios_count': sum(len(sc) for sc in scenarios.values()),
            'testcases_count': sum(len(tc) for tc in testcases.values()),
            'test_execution': {
                'total': test_results.get('total', 0),
                'passed': test_results.get('passed', 0),
                'failed': test_results.get('failed', 0),
                'pass_rate': test_results.get('pass_rate', 0)
            },
            'files_generated': [
                'test_strategy.md',
                'modules.json',
                'testpoints.json',
                'scenarios.json',
                'testcases.json',
                'testcases.xlsx',
                'test_report.html'
            ]
        }

def main():
    """主函数"""
    print("🚀 AI Test Platform - 智能测试设计与自动化平台")
    print("版本: 1.0.0")
    print("=" * 60)
    
    # 验证配置
    config = get_config()
    if not config.validate():
        print("❌ 配置验证失败，请检查配置文件")
        return
    
    # 创建平台实例
    platform = AITestPlatform()
    
    # 运行完整工作流程
    result = platform.run_complete_workflow()
    
    if result['success']:
        print("\n📊 工作流程摘要:")
        summary = result['summary']
        print(f"  - 识别模块: {summary['modules_count']} 个")
        print(f"  - 生成测试点: {summary['testpoints_count']} 个")
        print(f"  - 生成测试场景: {summary['scenarios_count']} 个")
        print(f"  - 生成测试用例: {summary['testcases_count']} 个")
        print(f"  - 测试通过率: {summary['test_execution']['pass_rate']:.1f}%")
        print(f"  - 生成文件: {len(summary['files_generated'])} 个")
        
        print(f"\n📁 输出目录: {config.paths.output_dir}")
        print("🎉 所有任务已完成，请查看输出目录中的结果文件！")
    else:
        print(f"\n❌ 工作流程失败: {result['error']}")

if __name__ == "__main__":
    main()