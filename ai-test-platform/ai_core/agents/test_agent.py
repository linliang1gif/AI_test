"""
TestAgent - 智能测试代理
负责理解测试需求、规划测试策略、调度测试执行
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

# 通过import调用已有模块，不修改原有代码
from ai.ai_client import AIClient
from ai.enhanced_ai_client import EnhancedAIClient
from parser.requirement_parser import RequirementParser
from test_design.testpoint_generator import TestPointGenerator
from test_design.testcase_generator import TestCaseGenerator


class TestAgent:
    """
    智能测试代理
    
    职责：
    1. 理解测试需求（自然语言/文档）
    2. 分析测试范围和优先级
    3. 规划测试策略
    4. 调度测试工作流
    5. 监控测试执行
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        初始化测试代理
        
        Args:
            config: 配置字典，包含AI模型、日志等配置
        """
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # 初始化AI客户端（调用已有模块）
        self.ai_client = AIClient()
        self.enhanced_ai = EnhancedAIClient()
        
        # 初始化解析器和生成器（调用已有模块）
        self.requirement_parser = RequirementParser()
        self.testpoint_generator = TestPointGenerator()
        self.testcase_generator = TestCaseGenerator()
        
        # 代理状态
        self.status = "idle"
        self.current_task = None
        self.task_history = []
        
        self.logger.info("TestAgent initialized")
    
    def understand_requirement(self, requirement: str, doc_path: Optional[str] = None) -> Dict:
        """
        理解测试需求
        
        Args:
            requirement: 需求描述文本
            doc_path: 需求文档路径（可选）
            
        Returns:
            需求分析结果
        """
        self.logger.info("Understanding requirement...")
        
        result = {
            "timestamp": datetime.now().isoformat(),
            "requirement": requirement,
            "doc_path": doc_path,
            "analysis": {}
        }
        
        try:
            # 如果有文档，使用已有的解析器
            if doc_path:
                parsed_data = self.requirement_parser.parse(doc_path)
                result["analysis"]["parsed_data"] = parsed_data
            
            # 使用AI理解需求意图
            ai_analysis = self.ai_client.analyze_requirement(requirement)
            result["analysis"]["ai_insights"] = ai_analysis
            
            # 提取关键信息
            result["analysis"]["key_points"] = self._extract_key_points(requirement, ai_analysis)
            result["status"] = "success"
            
        except Exception as e:
            self.logger.error(f"Error understanding requirement: {e}")
            result["status"] = "error"
            result["error"] = str(e)
        
        return result
    
    def plan_test_strategy(self, requirement_analysis: Dict) -> Dict:
        """
        规划测试策略
        
        Args:
            requirement_analysis: 需求分析结果
            
        Returns:
            测试策略计划
        """
        self.logger.info("Planning test strategy...")
        
        strategy = {
            "timestamp": datetime.now().isoformat(),
            "test_levels": [],
            "test_types": [],
            "priority": "medium",
            "estimated_effort": "unknown"
        }
        
        try:
            # 使用AI规划测试策略
            ai_strategy = self.enhanced_ai.plan_test_strategy(requirement_analysis)
            strategy.update(ai_strategy)
            
            # 确定测试级别
            strategy["test_levels"] = self._determine_test_levels(requirement_analysis)
            
            # 确定测试类型
            strategy["test_types"] = self._determine_test_types(requirement_analysis)
            
            strategy["status"] = "success"
            
        except Exception as e:
            self.logger.error(f"Error planning strategy: {e}")
            strategy["status"] = "error"
            strategy["error"] = str(e)
        
        return strategy
    
    def generate_test_artifacts(self, strategy: Dict) -> Dict:
        """
        生成测试制品（测试点、测试用例）
        
        Args:
            strategy: 测试策略
            
        Returns:
            生成的测试制品
        """
        self.logger.info("Generating test artifacts...")
        
        artifacts = {
            "timestamp": datetime.now().isoformat(),
            "testpoints": [],
            "testcases": []
        }
        
        try:
            # 生成测试点（调用已有模块）
            testpoints = self.testpoint_generator.generate(strategy)
            artifacts["testpoints"] = testpoints
            
            # 生成测试用例（调用已有模块）
            testcases = self.testcase_generator.generate(testpoints)
            artifacts["testcases"] = testcases
            
            artifacts["status"] = "success"
            artifacts["summary"] = {
                "testpoint_count": len(testpoints),
                "testcase_count": len(testcases)
            }
            
        except Exception as e:
            self.logger.error(f"Error generating artifacts: {e}")
            artifacts["status"] = "error"
            artifacts["error"] = str(e)
        
        return artifacts
    
    def execute_task(self, task: Dict) -> Dict:
        """
        执行测试任务
        
        Args:
            task: 任务定义
            
        Returns:
            执行结果
        """
        self.logger.info(f"Executing task: {task.get('name', 'unnamed')}")
        
        self.status = "running"
        self.current_task = task
        
        result = {
            "task_id": task.get("id"),
            "start_time": datetime.now().isoformat(),
            "status": "running"
        }
        
        try:
            # 1. 理解需求
            requirement_result = self.understand_requirement(
                task.get("requirement", ""),
                task.get("doc_path")
            )
            result["requirement_analysis"] = requirement_result
            
            # 2. 规划策略
            strategy = self.plan_test_strategy(requirement_result)
            result["strategy"] = strategy
            
            # 3. 生成制品
            artifacts = self.generate_test_artifacts(strategy)
            result["artifacts"] = artifacts
            
            result["status"] = "completed"
            result["end_time"] = datetime.now().isoformat()
            
        except Exception as e:
            self.logger.error(f"Error executing task: {e}")
            result["status"] = "failed"
            result["error"] = str(e)
            result["end_time"] = datetime.now().isoformat()
        
        finally:
            self.status = "idle"
            self.current_task = None
            self.task_history.append(result)
        
        return result
    
    def get_status(self) -> Dict:
        """获取代理状态"""
        return {
            "status": self.status,
            "current_task": self.current_task,
            "task_history_count": len(self.task_history)
        }
    
    def _extract_key_points(self, requirement: str, ai_analysis: Any) -> List[str]:
        """提取需求关键点"""
        # 简化实现，实际可以更复杂
        key_points = []
        
        if isinstance(ai_analysis, dict):
            key_points.extend(ai_analysis.get("key_features", []))
            key_points.extend(ai_analysis.get("test_focus", []))
        
        return key_points
    
    def _determine_test_levels(self, analysis: Dict) -> List[str]:
        """确定测试级别"""
        levels = ["unit", "integration"]
        
        # 根据分析结果动态调整
        if "api" in str(analysis).lower():
            levels.append("api")
        if "ui" in str(analysis).lower() or "界面" in str(analysis):
            levels.append("ui")
        
        return levels
    
    def _determine_test_types(self, analysis: Dict) -> List[str]:
        """确定测试类型"""
        types = ["functional"]
        
        # 根据分析结果动态调整
        if "性能" in str(analysis) or "performance" in str(analysis).lower():
            types.append("performance")
        if "安全" in str(analysis) or "security" in str(analysis).lower():
            types.append("security")
        
        return types
