"""
执行引擎单元测试
"""
import pytest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dataclasses import dataclass
from typing import List, Dict
from enum import Enum


# 模拟数据模型
class TestType(Enum):
    API = "api"
    UI = "ui"


class Priority(Enum):
    P0 = "P0"


@dataclass
class TestCase:
    id: str
    test_point_id: str
    title: str
    precondition: str
    steps: List[str]
    expected: str
    priority: Priority
    test_type: TestType
    module: str
    execution_config: Dict
    assertions: List[Dict]


class TestExecutionEngine:
    """测试执行引擎"""
    
    def test_basic_execution(self):
        """测试基本执行功能"""
        from modules.executor import ExecutionEngine
        
        test_case = TestCase(
            id="TC_001",
            test_point_id="TP_001",
            title="测试用例1",
            precondition="无",
            steps=["执行测试"],
            expected="成功",
            priority=Priority.P0,
            test_type=TestType.API,
            module="测试",
            execution_config={
                "method": "GET",
                "url": "https://jsonplaceholder.typicode.com/posts/1",
                "timeout": 10
            },
            assertions=[
                {"type": "status_code", "expected": 200}
            ]
        )
        
        engine = ExecutionEngine()
        results = engine.execute([test_case], parallel=False)
        
        assert len(results) == 1
        assert results[0].test_case_id == "TC_001"
        assert results[0].status in ["passed", "failed", "error"]
        assert results[0].duration > 0
    
    def test_parallel_execution(self):
        """测试并行执行"""
        from modules.executor import ExecutionEngine
        
        test_cases = [
            TestCase(
                id=f"TC_{i:03d}",
                test_point_id=f"TP_{i:03d}",
                title=f"测试用例{i}",
                precondition="无",
                steps=["执行测试"],
                expected="成功",
                priority=Priority.P0,
                test_type=TestType.API,
                module="测试",
                execution_config={
                    "method": "GET",
                    "url": f"https://jsonplaceholder.typicode.com/posts/{i}",
                    "timeout": 10
                },
                assertions=[
                    {"type": "status_code", "expected": 200}
                ]
            )
            for i in range(1, 4)
        ]
        
        engine = ExecutionEngine()
        results = engine.execute(test_cases, max_workers=3, parallel=True)
        
        assert len(results) == 3
        for result in results:
            assert result.status in ["passed", "failed", "error"]
    
    def test_statistics(self):
        """测试统计功能"""
        from modules.executor import ExecutionEngine, ExecutionResult
        
        results = [
            ExecutionResult(
                test_case_id="TC_001",
                status="passed",
                duration=1.0
            ),
            ExecutionResult(
                test_case_id="TC_002",
                status="failed",
                duration=2.0
            ),
            ExecutionResult(
                test_case_id="TC_003",
                status="passed",
                duration=1.5
            )
        ]
        
        engine = ExecutionEngine()
        stats = engine.get_statistics(results)
        
        assert stats['total'] == 3
        assert stats['passed'] == 2
        assert stats['failed'] == 1
        assert stats['pass_rate'] == "66.67%"
        assert stats['total_duration'] == 4.5
    
    def test_custom_runner(self):
        """测试自定义Runner"""
        from modules.executor import ExecutionEngine
        
        class MockRunner:
            def __init__(self, config):
                pass
            
            def run(self, test_case):
                return {
                    "status": "passed",
                    "message": "Mock execution"
                }
        
        engine = ExecutionEngine()
        engine.register_runner("mock", MockRunner({}))
        
        class MockTestType(Enum):
            MOCK = "mock"
        
        test_case = TestCase(
            id="TC_MOCK",
            test_point_id="TP_MOCK",
            title="Mock测试",
            precondition="无",
            steps=["执行"],
            expected="成功",
            priority=Priority.P0,
            test_type=MockTestType.MOCK,
            module="测试",
            execution_config={},
            assertions=[]
        )
        
        results = engine.execute([test_case], parallel=False)
        
        assert len(results) == 1
        assert results[0].status == "passed"


class TestApiRunner:
    """测试API Runner"""
    
    def test_status_code_assertion(self):
        """测试状态码断言"""
        from modules.executor import ApiRunner
        
        runner = ApiRunner({
            "base_url": "https://jsonplaceholder.typicode.com",
            "timeout": 10
        })
        
        test_case = TestCase(
            id="TC_API",
            test_point_id="TP_API",
            title="API测试",
            precondition="无",
            steps=["调用API"],
            expected="200",
            priority=Priority.P0,
            test_type=TestType.API,
            module="API",
            execution_config={
                "method": "GET",
                "url": "/posts/1"
            },
            assertions=[
                {"type": "status_code", "expected": 200}
            ]
        )
        
        result = runner.run(test_case)
        
        assert result['status'] == "passed"
        assert len(result['assertion_results']) == 1
        assert result['assertion_results'][0]['passed'] is True
    
    def test_json_path_assertion(self):
        """测试JSON路径断言"""
        from modules.executor import ApiRunner
        
        runner = ApiRunner({
            "base_url": "https://jsonplaceholder.typicode.com",
            "timeout": 10
        })
        
        test_case = TestCase(
            id="TC_JSON",
            test_point_id="TP_JSON",
            title="JSON测试",
            precondition="无",
            steps=["调用API"],
            expected="id=1",
            priority=Priority.P0,
            test_type=TestType.API,
            module="API",
            execution_config={
                "method": "GET",
                "url": "/posts/1"
            },
            assertions=[
                {
                    "type": "json_path",
                    "field": "id",
                    "operator": "equals",
                    "expected": 1
                }
            ]
        )
        
        result = runner.run(test_case)
        
        assert result['status'] == "passed"
        assert result['assertion_results'][0]['passed'] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
