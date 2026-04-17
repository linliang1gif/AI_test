"""
TestWorkflow - 测试工作流
定义和执行端到端测试流程
"""

import logging
from typing import Dict, List, Optional, Callable
from datetime import datetime
from enum import Enum

# 调用已有模块
from parser.requirement_parser import RequirementParser
from test_design.testpoint_generator import TestPointGenerator
from test_design.testcase_generator import TestCaseGenerator
from automation.api_script_generator import APIScriptGenerator
from executor.pytest_runner import PytestRunner
from report.report_generator import ReportGenerator


class WorkflowStage(Enum):
    """工作流阶段"""
    PARSE = "parse"
    DESIGN = "design"
    GENERATE = "generate"
    EXECUTE = "execute"
    REPORT = "report"


class TestWorkflow:
    """
    测试工作流
    
    定义完整的测试流程：
    需求解析 -> 测试设计 -> 脚本生成 -> 执行测试 -> 生成报告
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        初始化工作流
        
        Args:
            config: 工作流配置
        """
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # 初始化各阶段处理器（调用已有模块）
        self.requirement_parser = RequirementParser()
        self.testpoint_generator = TestPointGenerator()
        self.testcase_generator = TestCaseGenerator()
        self.script_generator = APIScriptGenerator()
        self.test_runner = PytestRunner()
        self.report_generator = ReportGenerator()
        
        # 工作流状态
        self.current_stage = None
        self.stages_completed = []
        self.workflow_data = {}
        
        # 钩子函数
        self.hooks = {
            "before_stage": {},
            "after_stage": {}
        }
        
        self.logger.info("TestWorkflow initialized")
    
    def run(self, input_data: Dict) -> Dict:
        """
        运行完整工作流
        
        Args:
            input_data: 输入数据，包含需求文档路径等
            
        Returns:
            工作流执行结果
        """
        self.logger.info("Starting test workflow...")
        
        result = {
            "workflow_id": self._generate_workflow_id(),
            "start_time": datetime.now().isoformat(),
            "stages": {},
            "status": "running"
        }
        
        try:
            # 阶段1: 解析需求
            parse_result = self._run_stage(
                WorkflowStage.PARSE,
                self._parse_requirement,
                input_data
            )
            result["stages"]["parse"] = parse_result
            
            # 阶段2: 测试设计
            design_result = self._run_stage(
                WorkflowStage.DESIGN,
                self._design_tests,
                parse_result
            )
            result["stages"]["design"] = design_result
            
            # 阶段3: 生成脚本
            generate_result = self._run_stage(
                WorkflowStage.GENERATE,
                self._generate_scripts,
                design_result
            )
            result["stages"]["generate"] = generate_result
            
            # 阶段4: 执行测试
            execute_result = self._run_stage(
                WorkflowStage.EXECUTE,
                self._execute_tests,
                generate_result
            )
            result["stages"]["execute"] = execute_result
            
            # 阶段5: 生成报告
            report_result = self._run_stage(
                WorkflowStage.REPORT,
                self._generate_report,
                execute_result
            )
            result["stages"]["report"] = report_result
            
            result["status"] = "completed"
            result["end_time"] = datetime.now().isoformat()
            
        except Exception as e:
            self.logger.error(f"Workflow failed: {e}")
            result["status"] = "failed"
            result["error"] = str(e)
            result["end_time"] = datetime.now().isoformat()
        
        return result
    
    def run_partial(self, stages: List[WorkflowStage], input_data: Dict) -> Dict:
        """
        运行部分工作流阶段
        
        Args:
            stages: 要运行的阶段列表
            input_data: 输入数据
            
        Returns:
            执行结果
        """
        self.logger.info(f"Running partial workflow: {[s.value for s in stages]}")
        
        result = {
            "workflow_id": self._generate_workflow_id(),
            "start_time": datetime.now().isoformat(),
            "stages": {},
            "status": "running"
        }
        
        try:
            stage_data = input_data
            
            for stage in stages:
                stage_func = self._get_stage_function(stage)
                stage_result = self._run_stage(stage, stage_func, stage_data)
                result["stages"][stage.value] = stage_result
                stage_data = stage_result
            
            result["status"] = "completed"
            result["end_time"] = datetime.now().isoformat()
            
        except Exception as e:
            self.logger.error(f"Partial workflow failed: {e}")
            result["status"] = "failed"
            result["error"] = str(e)
            result["end_time"] = datetime.now().isoformat()
        
        return result
    
    def register_hook(self, hook_type: str, stage: WorkflowStage, callback: Callable):
        """
        注册工作流钩子
        
        Args:
            hook_type: "before_stage" 或 "after_stage"
            stage: 工作流阶段
            callback: 回调函数
        """
        if hook_type not in self.hooks:
            raise ValueError(f"Invalid hook type: {hook_type}")
        
        self.hooks[hook_type][stage] = callback
        self.logger.info(f"Registered {hook_type} hook for {stage.value}")
    
    def _run_stage(self, stage: WorkflowStage, func: Callable, input_data: Dict) -> Dict:
        """运行单个阶段"""
        self.logger.info(f"Running stage: {stage.value}")
        self.current_stage = stage
        
        # 执行before钩子
        if stage in self.hooks["before_stage"]:
            self.hooks["before_stage"][stage](input_data)
        
        # 执行阶段
        result = func(input_data)
        
        # 执行after钩子
        if stage in self.hooks["after_stage"]:
            self.hooks["after_stage"][stage](result)
        
        self.stages_completed.append(stage)
        return result
    
    def _parse_requirement(self, input_data: Dict) -> Dict:
        """解析需求阶段"""
        doc_path = input_data.get("doc_path")
        parsed_data = self.requirement_parser.parse(doc_path)
        return {
            "stage": "parse",
            "parsed_data": parsed_data,
            "status": "success"
        }
    
    def _design_tests(self, input_data: Dict) -> Dict:
        """测试设计阶段"""
        parsed_data = input_data.get("parsed_data", {})
        
        # 生成测试点
        testpoints = self.testpoint_generator.generate(parsed_data)
        
        # 生成测试用例
        testcases = self.testcase_generator.generate(testpoints)
        
        return {
            "stage": "design",
            "testpoints": testpoints,
            "testcases": testcases,
            "status": "success"
        }
    
    def _generate_scripts(self, input_data: Dict) -> Dict:
        """生成脚本阶段"""
        testcases = input_data.get("testcases", [])
        
        # 生成API测试脚本
        scripts = self.script_generator.generate(testcases)
        
        return {
            "stage": "generate",
            "scripts": scripts,
            "status": "success"
        }
    
    def _execute_tests(self, input_data: Dict) -> Dict:
        """执行测试阶段"""
        scripts = input_data.get("scripts", [])
        
        # 执行测试
        execution_result = self.test_runner.run(scripts)
        
        return {
            "stage": "execute",
            "execution_result": execution_result,
            "status": "success"
        }
    
    def _generate_report(self, input_data: Dict) -> Dict:
        """生成报告阶段"""
        execution_result = input_data.get("execution_result", {})
        
        # 生成测试报告
        report = self.report_generator.generate(execution_result)
        
        return {
            "stage": "report",
            "report": report,
            "status": "success"
        }
    
    def _get_stage_function(self, stage: WorkflowStage) -> Callable:
        """获取阶段对应的函数"""
        stage_map = {
            WorkflowStage.PARSE: self._parse_requirement,
            WorkflowStage.DESIGN: self._design_tests,
            WorkflowStage.GENERATE: self._generate_scripts,
            WorkflowStage.EXECUTE: self._execute_tests,
            WorkflowStage.REPORT: self._generate_report
        }
        return stage_map[stage]
    
    def _generate_workflow_id(self) -> str:
        """生成工作流ID"""
        return f"workflow_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    def get_status(self) -> Dict:
        """获取工作流状态"""
        return {
            "current_stage": self.current_stage.value if self.current_stage else None,
            "stages_completed": [s.value for s in self.stages_completed],
            "total_stages": len(WorkflowStage)
        }
