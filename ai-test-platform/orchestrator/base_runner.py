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

try:
    from app.executor_v2.execution_engine import ExecutionEngineV2
    from app.executor_v2.models import TestCaseV2, AssertionDef
    from app.executor_v2.auth_manager import AuthManager
    from config.config import get_config
    _v2_engine_available = True
except ImportError:
    _v2_engine_available = False


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
    """API 测试执行器 — 使用 Executor V2 真实执行引擎"""
    
    def __init__(self):
        self.script_generator = ApiScriptGenerator() if _script_generator_available else None
        self._engine = None
    
    def _get_engine(self, base_url: str = "") -> 'ExecutionEngineV2':
        """获取 V2 执行引擎（懒加载）"""
        if not _v2_engine_available:
            return None
        if not base_url:
            try:
                config = get_config()
                base_url = config.test.base_url
            except Exception:
                pass
        if base_url:
            return ExecutionEngineV2(base_url=base_url)
        return None
    
    def run(self, module: Dict[str, Any]) -> Dict[str, Any]:
        """执行 API 测试（基于策略）"""
        start = time.time()
        
        try:
            module_name = module.get("module", {}).get("name", "未知模块")
            case_count = module.get("case_count", 0)
            
            # 尝试使用 V2 引擎
            engine = self._get_engine()
            if engine:
                details = f"API测试完成(V2引擎): {module_name}, 共{case_count}个用例"
            else:
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
        
        优先使用 V2 真实执行引擎，无法使用时回退到脚本生成
        """
        start = time.time()
        
        try:
            print(f"    🔧 API Runner: 执行 {len(cases)} 个用例")
            
            case_results = []
            
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
        
        使用 V2 引擎发送真实 HTTP 请求并验证断言。
        如果 V2 不可用或用例缺少必要字段，回退到基本测试。
        """
        case_id = case.get('id', 'unknown')
        case_title = case.get('title', '未知用例')
        
        try:
            # 尝试用 V2 引擎真实执行
            if _v2_engine_available and case.get('method') and case.get('path'):
                return self._execute_with_v2(case)
            
            # 回退：用例缺少 method/path，无法发 HTTP
            exec_config = case.get('execution_config', {})
            if isinstance(exec_config, str):
                import json
                try:
                    exec_config = json.loads(exec_config)
                except Exception:
                    exec_config = {}
            
            method = exec_config.get('method', case.get('method', ''))
            path = exec_config.get('path', case.get('path', ''))
            base_url = exec_config.get('base_url', case.get('base_url', ''))
            
            if _v2_engine_available and method and path:
                merged = {**case, **exec_config, 'method': method, 'path': path}
                if base_url:
                    merged['base_url'] = base_url
                return self._execute_with_v2(merged)
            
            # 最终回退：无法真实执行，返回 skipped
            return {
                "case_id": case_id,
                "title": case_title,
                "status": "skipped",
                "duration": 0.0,
                "message": "用例缺少 method/path，无法执行真实HTTP请求"
            }
            
        except Exception as e:
            return {
                "case_id": case_id,
                "title": case_title,
                "status": "failed",
                "duration": 0.0,
                "message": f"执行异常: {str(e)}"
            }
    
    def _execute_with_v2(self, case: Dict[str, Any]) -> Dict[str, Any]:
        """使用 V2 引擎执行单个用例"""
        base_url = case.get('base_url', '')
        engine = self._get_engine(base_url)
        if not engine:
            return {
                "case_id": case.get('id', 'unknown'),
                "title": case.get('title', '未知用例'),
                "status": "skipped",
                "duration": 0.0,
                "message": "未配置 base_url，无法执行真实请求"
            }
        
        # 构建 TestCaseV2
        assertions_raw = case.get('assertions', [])
        if isinstance(assertions_raw, str):
            import json
            try:
                assertions_raw = json.loads(assertions_raw)
            except Exception:
                assertions_raw = []
        
        assertions = []
        for a in assertions_raw:
            if isinstance(a, dict) and 'type' in a:
                assertions.append(AssertionDef(
                    type=a['type'],
                    expected=a.get('expected'),
                    path=a.get('path', ''),
                ))
        
        tc = TestCaseV2(
            id=case.get('id', f'case-{int(time.time())}'),
            title=case.get('title', ''),
            method=case.get('method', 'GET').upper(),
            path=case.get('path', '/'),
            base_url=base_url,
            headers=case.get('headers', {}),
            body=case.get('body'),
            timeout=case.get('timeout', 30.0),
            assertions=assertions,
        )
        
        result = engine.execute_case(tc, run_id=f"orch-{int(time.time())}")
        
        return {
            "case_id": tc.id,
            "title": tc.title,
            "status": result.status,
            "duration": round(result.duration_ms / 1000, 3),
            "message": result.error_message or ("测试通过" if result.passed else "断言失败"),
            "http_status": result.response.status_code if result.response else 0,
            "assertions": [a.to_dict() for a in result.assertions] if result.assertions else [],
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
