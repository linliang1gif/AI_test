#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
核心接口定义
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any
from core.models import TestCase, ExecutionResult, TestReport, HealingRecord

class ITestCaseGenerator(ABC):
    """测试用例生成器接口"""
    
    @abstractmethod
    def generate_testcases(self, spec: Any) -> List[TestCase]:
        """生成测试用例"""
        pass

class IExecutor(ABC):
    """执行器接口"""
    
    @abstractmethod
    def execute(self, test_case: TestCase) -> ExecutionResult:
        """执行单个测试用例"""
        pass
    
    @abstractmethod
    def execute_batch(self, test_cases: List[TestCase]) -> List[ExecutionResult]:
        """批量执行测试用例"""
        pass

class IHealingEngine(ABC):
    """修复引擎接口"""
    
    @abstractmethod
    def heal(self, result: ExecutionResult) -> HealingRecord:
        """修复失败的测试"""
        pass

class IReportGenerator(ABC):
    """报告生成器接口"""
    
    @abstractmethod
    def generate(self, results: List[ExecutionResult], format: str = "json") -> TestReport:
        """生成测试报告"""
        pass

class IDataManager(ABC):
    """数据管理器接口"""
    
    @abstractmethod
    def generate_data(self, schema: Dict[str, Any], data_type: str) -> Dict[str, Any]:
        """生成测试数据"""
        pass
