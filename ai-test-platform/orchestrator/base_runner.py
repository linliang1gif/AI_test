"""
Base Runner - 测试执行器基类
定义统一的 Runner 接口
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List
import time
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent.parent))

try:
    from automation.api_script_generator import ApiScriptGenerator
    _script_generator_available = True
except ImportError:
    _script_generator_available = False


class BaseRunner(ABC):
    """测试执行器基类"""
    
    @abstractmethod
    def run(self, module: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行测试（基于策略）
        
        Args:
            module: 模块策略信息
            
        Returns:
            执行结果 {
                "status": "passed/failed",
                "duration": float,
                "details": str
            }
        """
        pass
    
    @abstractmethod
    def run_cases(self, cases: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        执行测试（基于用例列表）
        
        Args:
            cases: 测试用例列表
            
        Returns:
            执行结果 {
                "status": "passed/failed",
                "duration": float,
                "details": str,
                "case_results": [...]
            }
        """
        pass
    
    def _create_result(self, status: str, duration: float, details: str, case_results: List[Dict] = None) -> Dict[str, Any]:
        """创建标准结果格式"""
        result = {
            "status": status,
            "duration": round(duration, 2),
            "details": details
        }
        
        if case_results is not None:
            result["case_results"] = case_results
        
        return result


class ApiRunner(BaseRunner):
    """API 测试执行器"""
    
    def __init__(self):
        self.script_generator = ApiScriptGenerator() if _script_generator_available else None
    
    def run(self, module: Dict[str, Any]) -> Dict[str, Any]:
        """执行 API 测试（基于策略）"""
        start = time.time()
        
        try:
            module_name = module.get("module", {}).get("name", "未知模块")
            case_count = module.get("case_count", 0)
            
            # Mock: 模拟 API 测试执行
            time.sleep(0.1)
            
            details = f"API测试完成: {module_name}, 执行{case_count}个用例"
            duration = time.time() - start
            
            return self._create_result("passed", duration, details)
            
        except Exception as e:
            duration = time.time() - start
            return self._create_result("failed", duration, f"API测试失败: {str(e)}")
    
    def run_cases(self, cases: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        执行 API 测试（基于用例列表）
        
        流程:
        1. 调用 ApiScriptGenerator 生成脚本
        2. 执行 pytest
        3. 返回结果
        """
        start = time.time()
        
        try:
            print(f"    🔧 API Runner: 执行 {len(cases)} 个用例")
            
            case_results = []
            
            # 为每个用例生成并执行
            for case in cases:
                case_result = self._execute_single_case(case)
                case_results.append(case_result)
            
            # 统计结果
            passed = sum(1 for r in case_results if r['status'] == 'passed')
            failed = len(case_results) - passed
            
            duration = time.time() - start
            details = f"API测试: {passed}/{len(cases)} 通过"
            status = "passed" if failed == 0 else "failed"
            
            return self._create_result(status, duration, details, case_results)
            
        except Exception as e:
            duration = time.time() - start
            return self._create_result("failed", duration, f"API测试异常: {str(e)}")
    
    def _execute_single_case(self, case: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行单个测试用例
        
        流程:
        1. 生成脚本（如果有 ApiScriptGenerator）
        2. 执行测试
        3. 返回结果
        """
        case_id = case.get('id', 'unknown')
        case_title = case.get('title', '未知用例')
        
        try:
            # Mock: 模拟测试执行
            # 实际应该: 生成脚本 → 执行 pytest → 解析结果
            time.sleep(0.05)
            
            # 90% 通过率
            import random
            passed = random.random() > 0.1
            
            return {
                "case_id": case_id,
                "title": case_title,
                "status": "passed" if passed else "failed",
                "duration": 0.05,
                "message": "测试通过" if passed else "断言失败"
            }
            
        except Exception as e:
            return {
                "case_id": case_id,
                "title": case_title,
                "status": "failed",
                "duration": 0.0,
                "message": f"执行异常: {str(e)}"
            }


class UiRunner(BaseRunner):
    """UI 测试执行器"""
    
    def run(self, module: Dict[str, Any]) -> Dict[str, Any]:
        """执行 UI 测试（基于策略）"""
        start = time.time()
        
        try:
            module_name = module.get("module", {}).get("name", "未知模块")
            case_count = module.get("case_count", 0)
            
            # Mock: 模拟 UI 测试执行
            time.sleep(0.15)
            
            details = f"UI测试完成: {module_name}, 执行{case_count}个用例"
            duration = time.time() - start
            
            return self._create_result("passed", duration, details)
            
        except Exception as e:
            duration = time.time() - start
            return self._create_result("failed", duration, f"UI测试失败: {str(e)}")
    
    def run_cases(self, cases: List[Dict[str, Any]]) -> Dict[str, Any]:
        """执行 UI 测试（基于用例列表）"""
        start = time.time()
        
        try:
            print(f"    🔧 UI Runner: 执行 {len(cases)} 个用例")
            
            case_results = []
            
            for case in cases:
                case_id = case.get('id', 'unknown')
                case_title = case.get('title', '未知用例')
                
                # Mock: 模拟 UI 测试
                time.sleep(0.1)
                
                import random
                passed = random.random() > 0.15
                
                case_results.append({
                    "case_id": case_id,
                    "title": case_title,
                    "status": "passed" if passed else "failed",
                    "duration": 0.1,
                    "message": "UI测试通过" if passed else "UI元素未找到"
                })
            
            passed = sum(1 for r in case_results if r['status'] == 'passed')
            duration = time.time() - start
            details = f"UI测试: {passed}/{len(cases)} 通过"
            status = "passed" if passed == len(cases) else "failed"
            
            return self._create_result(status, duration, details, case_results)
            
        except Exception as e:
            duration = time.time() - start
            return self._create_result("failed", duration, f"UI测试异常: {str(e)}")


class IntegrationRunner(BaseRunner):
    """集成测试执行器"""
    
    def run(self, module: Dict[str, Any]) -> Dict[str, Any]:
        """执行集成测试（基于策略）"""
        start = time.time()
        
        try:
            module_name = module.get("module", {}).get("name", "未知模块")
            case_count = module.get("case_count", 0)
            
            # Mock: 模拟集成测试执行
            time.sleep(0.2)
            
            details = f"集成测试完成: {module_name}, 执行{case_count}个用例"
            duration = time.time() - start
            
            return self._create_result("passed", duration, details)
            
        except Exception as e:
            duration = time.time() - start
            return self._create_result("failed", duration, f"集成测试失败: {str(e)}")
    
    def run_cases(self, cases: List[Dict[str, Any]]) -> Dict[str, Any]:
        """执行集成测试（基于用例列表）"""
        start = time.time()
        
        try:
            print(f"    🔧 Integration Runner: 执行 {len(cases)} 个用例")
            
            case_results = []
            
            for case in cases:
                case_id = case.get('id', 'unknown')
                case_title = case.get('title', '未知用例')
                
                # Mock: 模拟集成测试
                time.sleep(0.15)
                
                import random
                passed = random.random() > 0.2
                
                case_results.append({
                    "case_id": case_id,
                    "title": case_title,
                    "status": "passed" if passed else "failed",
                    "duration": 0.15,
                    "message": "集成测试通过" if passed else "服务调用失败"
                })
            
            passed = sum(1 for r in case_results if r['status'] == 'passed')
            duration = time.time() - start
            details = f"集成测试: {passed}/{len(cases)} 通过"
            status = "passed" if passed == len(cases) else "failed"
            
            return self._create_result(status, duration, details, case_results)
            
        except Exception as e:
            duration = time.time() - start
            return self._create_result("failed", duration, f"集成测试异常: {str(e)}")


def get_runner(test_type: str) -> BaseRunner:
    """
    根据测试类型获取对应的 Runner
    
    Args:
        test_type: 测试类型 (api/ui/integration)
        
    Returns:
        对应的 Runner 实例
    """
    runners = {
        "api": ApiRunner(),
        "ui": UiRunner(),
        "integration": IntegrationRunner()
    }
    
    return runners.get(test_type, ApiRunner())
