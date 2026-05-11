#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
流水线编排器

实现完整的自动化测试流水线：
需求文档 → AI需求解析 → 模块拆分 → 测试点生成 → 测试用例生成 → 
Swagger接口解析 → 接口自动化生成 → pytest执行 → AI Bug分析 → 
Self Healing → 生成测试报告
"""

import time
import json
from typing import Dict, List, Any, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class PipelineOrchestrator:
    """流水线编排器"""
    
    def __init__(self):
        self.pipeline_steps = []
        self.execution_results = {}
        self.current_step = 0
        
        # 初始化各个组件
        self._initialize_components()
        
        # 定义流水线步骤
        self._define_pipeline_steps()
    
    def _initialize_components(self):
        """初始化所有组件"""
        try:
            # 导入所有必要的组件
            from ..agents.agent_coordinator import AgentCoordinator
            from ..api_parser.swagger_api_parser import SwaggerApiParser
            from ..api_test_generator.api_test_generator import ApiTestGenerator
            from ..self_healing.self_healing_engine import SelfHealingEngine
            from ..coverage_analyzer.coverage_analyzer import CoverageAnalyzer
            from ...report.report_generator import ReportGenerator
            
            self.agent_coordinator = AgentCoordinator()
            self.swagger_parser = SwaggerApiParser()
            self.api_test_generator = ApiTestGenerator()
            self.self_healing_engine = SelfHealingEngine()
            self.coverage_analyzer = CoverageAnalyzer()
            self.report_generator = ReportGenerator()
            
        except ImportError as e:
            logger.info(f"组件导入失败: {e}")
            # 使用兼容性导入
            self._initialize_components_fallback()
    
    def _initialize_components_fallback(self):
        """兼容性组件初始化"""
        # 这里可以添加兼容性处理逻辑
        pass
    
    def _define_pipeline_steps(self):
        """定义流水线步骤"""
        self.pipeline_steps = [
            {
                'name': 'requirement_analysis',
                'description': '需求文档解析',
                'function': self._step_requirement_analysis,
                'required_inputs': ['requirement_file'],
                'outputs': ['requirements', 'requirement_analysis']
            },
            {
                'name': 'module_splitting',
                'description': '功能模块拆分',
                'function': self._step_module_splitting,
                'required_inputs': ['requirements'],
                'outputs': ['modules']
            },
            {
                'name': 'test_point_generation',
                'description': '测试点生成',
                'function': self._step_test_point_generation,
                'required_inputs': ['modules'],
                'outputs': ['test_points']
            },
            {
                'name': 'test_case_generation',
                'description': '测试用例生成',
                'function': self._step_test_case_generation,
                'required_inputs': ['modules', 'test_points'],
                'outputs': ['test_cases']
            },
            {
                'name': 'swagger_parsing',
                'description': 'Swagger接口解析',
                'function': self._step_swagger_parsing,
                'required_inputs': ['swagger_file'],
                'outputs': ['apis', 'api_summary']
            },
            {
                'name': 'api_test_generation',
                'description': '接口自动化测试生成',
                'function': self._step_api_test_generation,
                'required_inputs': ['apis', 'test_cases'],
                'outputs': ['api_test_scripts']
            },
            {
                'name': 'test_execution',
                'description': 'pytest测试执行',
                'function': self._step_test_execution,
                'required_inputs': ['api_test_scripts'],
                'outputs': ['test_results']
            },
            {
                'name': 'self_healing',
                'description': '自动修复失败测试',
                'function': self._step_self_healing,
                'required_inputs': ['test_results', 'api_test_scripts'],
                'outputs': ['healing_results', 'final_test_results']
            },
            {
                'name': 'coverage_analysis',
                'description': '测试覆盖率分析',
                'function': self._step_coverage_analysis,
                'required_inputs': ['requirements', 'test_points', 'test_cases', 'api_test_scripts'],
                'outputs': ['coverage_analysis']
            },
            {
                'name': 'report_generation',
                'description': '生成测试报告',
                'function': self._step_report_generation,
                'required_inputs': ['final_test_results', 'coverage_analysis'],
                'outputs': ['test_report']
            }
        ]
    
    def execute_pipeline(self, input_config: Dict[str, Any]) -> Dict[str, Any]:
        """执行完整流水线"""
        pipeline_result = {
            'success': False,
            'start_time': time.time(),
            'end_time': None,
            'total_duration': 0,
            'steps_completed': 0,
            'steps_failed': 0,
            'step_results': {},
            'final_outputs': {},
            'error': None
        }
        
        logger.info("🚀 开始执行AI测试自动化流水线")
        logger.info("=" * 60)
        
        try:
            # 验证输入配置
            validation_result = self._validate_input_config(input_config)
            if not validation_result['valid']:
                raise ValueError(f"输入配置验证失败: {validation_result['error']}")
            
            # 初始化执行结果
            self.execution_results = input_config.copy()
            
            # 逐步执行流水线
            for i, step in enumerate(self.pipeline_steps):
                self.current_step = i
                step_result = self._execute_single_step(step, i + 1)
                
                pipeline_result['step_results'][step['name']] = step_result
                
                if step_result['success']:
                    pipeline_result['steps_completed'] += 1
                    # 将步骤输出添加到执行结果中
                    self.execution_results.update(step_result['outputs'])
                else:
                    pipeline_result['steps_failed'] += 1
                    
                    # 检查是否为关键步骤失败
                    if step['name'] in ['requirement_analysis', 'swagger_parsing']:
                        raise Exception(f"关键步骤失败: {step['name']} - {step_result['error']}")
                    
                    logger.info(f"⚠️  步骤失败但继续执行: {step['name']}")
            
            # 收集最终输出
            pipeline_result['final_outputs'] = self._collect_final_outputs()
            pipeline_result['success'] = True
            
            logger.info("\n🎉 流水线执行完成！")
            
        except Exception as e:
            pipeline_result['error'] = str(e)
            logger.info(f"\n❌ 流水线执行失败: {e}")
        
        finally:
            pipeline_result['end_time'] = time.time()
            pipeline_result['total_duration'] = pipeline_result['end_time'] - pipeline_result['start_time']
        
        return pipeline_result