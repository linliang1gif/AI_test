"""
测试执行引擎 V2 - Intelligence Agent 完全接管版本
强制要求使用 execution_plan，禁止直接执行 test_cases
"""
import time
import traceback
import warnings
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Optional, Any
from datetime import datetime

# 🔧 使用 core 层的统一模型
from core import (
    ExecutionResult,
    TestCaseStatus,
    TestType,
    create_execution_result
)

# 🛡️ 稳定性引擎
from modules.resilience import ResilienceEngine, ResilienceConfig

# 🧠 Intelligence Agent
from modules.agents import TestIntelligenceAgent, TestCase


class ExecutionEngine:
    """
    测试执行引擎 V2 - Intelligence Agent 完全接管版本
    
    ⚠️ 重要变更:
    - execute() 方法只接受 execution_plan (不再接受 test_cases)
    - 必须通过 TestIntelligenceAgent 生成 execution_plan
    - execute_legacy() 提供向后兼容,但内部强制走 Intelligence
    
    特性：
    - 智能测试选择（基于风险评分）
    - 智能执行顺序（高风险优先）
    - 智能并发策略（按模块分组）
    - 支持API/UI/Integration扩展
    - 统一返回ExecutionResult
    """
    
    def __init__(self, config: Optional[Dict] = None, intelligence_agent: Optional[TestIntelligenceAgent] = None):
        """
        初始化执行引擎
        
        Args:
            config: 配置字典
                - base_url: API基础URL
                - timeout: 默认超时时间
                - retry_on_failure: 失败时是否重试
                - max_retries: 最大重试次数
                - resilience_enabled: 是否启用稳定性引擎（默认True）
            intelligence_agent: TestIntelligenceAgent实例（可选，如果不提供会自动创建）
        """
        self.config = config or {}
        self.runners = {}
        
        # 🧠 创建或使用提供的 Intelligence Agent
        self.intelligence_agent = intelligence_agent or TestIntelligenceAgent()
        
        # 🛡️ 创建 ResilienceEngine
        if self.config.get('resilience_enabled', True):
            resilience_config = ResilienceConfig(
                max_retries=self.config.get('max_retries', 3),
                retry_delay=self.config.get('retry_delay', 1.0),
                exponential_backoff=True,
                circuit_breaker_enabled=self.config.get('circuit_breaker_enabled', True),
                failure_threshold=self.config.get('failure_threshold', 5),
                rate_limiter_enabled=self.config.get('rate_limiter_enabled', True),
                global_qps=self.config.get('global_qps', 100),
                api_qps=self.config.get('api_qps', 10)
            )
            self.resilience = ResilienceEngine(resilience_config)
        else:
            self.resilience = None
        
        self._register_default_runners()
    
    def _register_default_runners(self):
        """注册默认的Runner"""
        from .api_runner import ApiRunner
        from .ui_runner import UiRunner
        from .integration_runner import IntegrationRunner
        
        self.runners["api"] = ApiRunner(self.config)
        self.runners["ui"] = UiRunner(self.config)
        self.runners["integration"] = IntegrationRunner(self.config)
    
    def register_runner(self, test_type: str, runner):
        """
        注册自定义Runner
        
        Args:
            test_type: 测试类型（如 "api", "ui"）
            runner: Runner实例，必须实现run(test_case)方法
        """
        self.runners[test_type] = runner
    
    # ========================================
    # 🔥 修改点1: 新的execute方法 - 只接受execution_plan
    # ========================================
    def execute(self, execution_plan: Dict[str, Any], 
                test_cases_map: Dict[str, Any],
                max_workers: int = 5) -> List[ExecutionResult]:
        """
        执行测试用例（V2版本 - 只接受execution_plan）
        
        ⚠️ 重要: 此方法只接受 execution_plan，不再接受 test_cases 列表
        
        Args:
            execution_plan: 由 TestIntelligenceAgent 生成的执行计划
                必须包含: selected_tests, execution_order, parallel_groups
            test_cases_map: TestCase对象映射 {test_case_id: TestCase对象}
            max_workers: 最大并发数
            
        Returns:
            ExecutionResult列表
            
        Raises:
            TypeError: 如果传入的不是execution_plan
            ValueError: 如果execution_plan格式不正确
        """
        # 🔥 修改点1.1: 严格类型检查
        if not isinstance(execution_plan, dict):
            raise TypeError(
                "ExecutionEngine V2 only accepts execution_plan (dict). "
                "Use TestIntelligenceAgent.optimize_execution_plan() to generate it. "
                "For legacy code, use execute_legacy() instead."
            )
        
        # 🔥 修改点1.2: 验证execution_plan结构
        required_keys = ['selected_tests', 'execution_order', 'parallel_groups']
        missing_keys = [key for key in required_keys if key not in execution_plan]
        if missing_keys:
            raise ValueError(
                f"Invalid execution_plan: missing required keys {missing_keys}. "
                f"Use TestIntelligenceAgent.optimize_execution_plan() to generate valid plan."
            )
        
        # 🔥 修改点1.3: 只执行selected_tests
        selected_test_ids = execution_plan['selected_tests']
        if not selected_test_ids:
            print("⚠️  No tests selected by Intelligence Agent. All tests skipped.")
            return []
        
        print(f"🧠 Intelligence Agent selected {len(selected_test_ids)} tests to execute")
        print(f"⏭️  Skipped {len(execution_plan.get('skipped_tests', []))} low-risk tests")
        
        # 🔥 修改点1.4: 按execution_order排序
        execution_order = execution_plan['execution_order']
        ordered_test_cases = []
        for test_id in execution_order:
            if test_id in test_cases_map:
                ordered_test_cases.append(test_cases_map[test_id])
            else:
                print(f"⚠️  Warning: test_case_id '{test_id}' not found in test_cases_map")
        
        # 🔥 修改点1.5: 使用parallel_groups进行智能并发
        parallel_groups = execution_plan['parallel_groups']
        
        if len(parallel_groups) > 1:
            # 多个模块，可以并发执行
            return self._execute_with_parallel_groups(
                ordered_test_cases, 
                parallel_groups, 
                test_cases_map,
                max_workers
            )
        else:
            # 单个模块，顺序执行
            return self._execute_sequential(ordered_test_cases)
    
    # ========================================
    # 🔥 修改点2: 新增execute_legacy方法 - 向后兼容
    # ========================================
    def execute_legacy(self, test_cases: List, max_workers: int = 5, 
                      parallel: bool = True) -> List[ExecutionResult]:
        """
        执行测试用例（Legacy版本 - 向后兼容）
        
        ⚠️ 已废弃: 此方法仅用于向后兼容，内部会自动调用 Intelligence Agent
        
        建议迁移到新接口:
        ```python
        # 旧代码
        results = engine.execute_legacy(test_cases)
        
        # 新代码
        plan = intelligence_agent.optimize_execution_plan(test_cases)
        test_cases_map = {tc.test_case_id: tc for tc in test_cases}
        results = engine.execute(plan, test_cases_map)
        ```
        
        Args:
            test_cases: TestCase列表
            max_workers: 最大并发数
            parallel: 是否并行执行（已忽略，由Intelligence Agent决定）
            
        Returns:
            ExecutionResult列表
        """
        # 🔥 修改点2.1: 发出废弃警告
        warnings.warn(
            "execute_legacy() is deprecated and will be removed in future versions. "
            "Use execute() with execution_plan instead.",
            DeprecationWarning,
            stacklevel=2
        )
        
        if not test_cases:
            return []
        
        print("🔄 Legacy mode: Auto-generating execution_plan via Intelligence Agent...")
        
        # 🔥 修改点2.2: 转换为TestCase对象（如果需要）
        intelligence_test_cases = []
        test_cases_map = {}
        
        for tc in test_cases:
            # 如果已经是TestCase对象，直接使用
            if isinstance(tc, TestCase):
                intelligence_test_cases.append(tc)
                test_cases_map[tc.test_case_id] = tc
            else:
                # 否则转换
                test_case_obj = TestCase(
                    test_case_id=getattr(tc, 'id', str(id(tc))),
                    api=getattr(tc, 'api', '/unknown'),
                    module=getattr(tc, 'module', 'default'),
                    priority=getattr(tc, 'priority', 'P2')
                )
                intelligence_test_cases.append(test_case_obj)
                test_cases_map[test_case_obj.test_case_id] = tc  # 保存原始对象
        
        # 🔥 修改点2.3: 使用Intelligence Agent生成执行计划
        execution_plan = self.intelligence_agent.optimize_execution_plan(intelligence_test_cases)
        
        print(f"✅ Execution plan generated:")
        print(f"   Selected: {len(execution_plan['selected_tests'])} tests")
        print(f"   Skipped: {len(execution_plan['skipped_tests'])} tests")
        print(f"   Parallel groups: {len(execution_plan['parallel_groups'])}")
        
        # 🔥 修改点2.4: 调用新的execute方法
        return self.execute(execution_plan, test_cases_map, max_workers)
    
    # ========================================
    # 🔥 修改点3: 新增智能并发执行方法
    # ========================================
    def _execute_with_parallel_groups(self, test_cases: List, 
                                     parallel_groups: Dict[str, List[str]],
                                     test_cases_map: Dict[str, Any],
                                     max_workers: int) -> List[ExecutionResult]:
        """
        使用parallel_groups进行智能并发执行
        
        Args:
            test_cases: 排序后的TestCase列表
            parallel_groups: 并发分组 {module: [test_case_ids]}
            test_cases_map: TestCase映射
            max_workers: 最大并发数
            
        Returns:
            ExecutionResult列表
        """
        print(f"🔀 Executing with {len(parallel_groups)} parallel groups...")
        
        results = []
        
        # 按模块分组执行
        for module, test_ids in parallel_groups.items():
            print(f"📦 Executing module: {module} ({len(test_ids)} tests)")
            
            # 获取该模块的测试用例
            module_test_cases = [tc for tc in test_cases if self._get_test_id(tc) in test_ids]
            
            # 并发执行该模块的测试
            module_results = self._execute_parallel(module_test_cases, max_workers)
            results.extend(module_results)
        
        return results
    
    def _get_test_id(self, test_case) -> str:
        """获取测试用例ID"""
        if isinstance(test_case, TestCase):
            return test_case.test_case_id
        return getattr(test_case, 'id', str(id(test_case)))
    
    def _execute_parallel(self, test_cases: List, max_workers: int) -> List[ExecutionResult]:
        """并行执行"""
        results = []
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 提交所有任务
            future_to_case = {
                executor.submit(self._run_single, case): case
                for case in test_cases
            }
            
            # 收集结果（按完成顺序）
            for future in as_completed(future_to_case):
                test_case = future_to_case[future]
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    # 如果执行过程中出现异常，创建错误结果
                    now = datetime.now()
                    test_id = self._get_test_id(test_case)
                    results.append(create_execution_result(
                        test_case_id=test_id,
                        status="failed",
                        start_time=now,
                        end_time=now,
                        error=f"Execution failed: {str(e)}",
                        stack_trace=traceback.format_exc()
                    ))
        
        return results
    
    def _execute_sequential(self, test_cases: List) -> List[ExecutionResult]:
        """顺序执行"""
        results = []
        for case in test_cases:
            result = self._run_single(case)
            results.append(result)
        return results
    
    def _run_single(self, test_case) -> ExecutionResult:
        """
        执行单个测试用例
        
        Args:
            test_case: TestCase对象
            
        Returns:
            ExecutionResult
        """
        start_time_dt = datetime.now()
        
        # 🛡️ 使用 ResilienceEngine 包装执行
        if self.resilience:
            try:
                result = self.resilience.execute_with_resilience(
                    func=lambda: self._execute_test(test_case),
                    api=self._get_test_id(test_case)
                )
                return result
            except Exception as e:
                # ResilienceEngine 所有重试都失败
                end_time_dt = datetime.now()
                test_id = self._get_test_id(test_case)
                return create_execution_result(
                    test_case_id=test_id,
                    status="failed",
                    start_time=start_time_dt,
                    end_time=end_time_dt,
                    error=str(e),
                    stack_trace=traceback.format_exc(),
                    error_type=type(e).__name__
                )
        else:
            # 不使用 ResilienceEngine（原有逻辑）
            return self._execute_test_with_retry(test_case, start_time_dt)
    
    def _execute_test(self, test_case) -> ExecutionResult:
        """
        执行测试（核心逻辑）
        
        Args:
            test_case: TestCase对象
            
        Returns:
            ExecutionResult
        """
        start_time_ts = time.time()
        start_time_dt = datetime.now()
        
        # 1. 获取对应的Runner
        runner = self._get_runner(test_case)
        
        # 2. 执行测试
        runner_result = runner.run(test_case)
        
        # 3. 构建ExecutionResult
        end_time_dt = datetime.now()
        duration = time.time() - start_time_ts
        
        # 转换状态字符串为枚举
        status_str = runner_result.get("status", "failed")
        
        test_id = self._get_test_id(test_case)
        result = create_execution_result(
            test_case_id=test_id,
            status=status_str,
            start_time=start_time_dt,
            end_time=end_time_dt,
            error=runner_result.get("error_message"),
            stack_trace=runner_result.get("stack_trace"),
            response=runner_result.get("actual_response"),
            assertion_details=runner_result.get("assertion_results", [])
        )
        
        return result
    
    def _execute_test_with_retry(self, test_case, start_time_dt) -> ExecutionResult:
        """
        执行测试（带重试，原有逻辑）
        
        Args:
            test_case: TestCase对象
            start_time_dt: 开始时间
            
        Returns:
            ExecutionResult
        """
        start_time_ts = time.time()
        retry_count = 0
        max_retries = self.config.get('max_retries', 0)
        
        test_id = self._get_test_id(test_case)
        
        while retry_count <= max_retries:
            try:
                # 1. 获取对应的Runner
                runner = self._get_runner(test_case)
                
                # 2. 执行测试
                runner_result = runner.run(test_case)
                
                # 3. 构建ExecutionResult
                end_time_dt = datetime.now()
                duration = time.time() - start_time_ts
                
                # 转换状态字符串为枚举
                status_str = runner_result.get("status", "failed")
                
                result = create_execution_result(
                    test_case_id=test_id,
                    status=status_str,
                    start_time=start_time_dt,
                    end_time=end_time_dt,
                    error=runner_result.get("error_message"),
                    stack_trace=runner_result.get("stack_trace"),
                    response=runner_result.get("actual_response"),
                    assertion_details=runner_result.get("assertion_results", [])
                )
                
                # 添加重试信息
                result.retry_count = retry_count
                
                # 4. 如果成功或不需要重试，直接返回
                if result.status == TestCaseStatus.PASSED:
                    return result
                
                if not self.config.get('retry_on_failure', False):
                    return result
                
                # 5. 失败且需要重试
                retry_count += 1
                if retry_count <= max_retries:
                    time.sleep(self.config.get('retry_delay', 1))
                    continue
                else:
                    return result
                    
            except Exception as e:
                duration = time.time() - start_time_ts
                retry_count += 1
                end_time_dt = datetime.now()
                
                if retry_count > max_retries:
                    return create_execution_result(
                        test_case_id=test_id,
                        status="failed",
                        start_time=start_time_dt,
                        end_time=end_time_dt,
                        error=str(e),
                        stack_trace=traceback.format_exc(),
                        error_type=type(e).__name__
                    )
                
                # 重试前等待
                time.sleep(self.config.get('retry_delay', 1))
        
        # 不应该到这里，但为了安全返回错误结果
        end_time_dt = datetime.now()
        return create_execution_result(
            test_case_id=test_id,
            status="failed",
            start_time=start_time_dt,
            end_time=end_time_dt,
            error="Max retries exceeded"
        )
    
    def _get_runner(self, test_case):
        """获取对应的Runner"""
        # 默认使用 api runner
        test_type = "api"
        
        if test_type not in self.runners:
            raise ValueError(f"No runner registered for test type: {test_type}")
        
        return self.runners[test_type]
    
    def get_statistics(self, results: List[ExecutionResult]) -> Dict:
        """
        统计执行结果
        
        Args:
            results: ExecutionResult列表
            
        Returns:
            统计信息字典
        """
        total = len(results)
        passed = sum(1 for r in results if r.status == TestCaseStatus.PASSED)
        failed = sum(1 for r in results if r.status == TestCaseStatus.FAILED)
        skipped = sum(1 for r in results if r.status == TestCaseStatus.SKIPPED)
        
        total_duration = sum(r.duration for r in results)
        avg_duration = total_duration / total if total > 0 else 0
        
        stats = {
            "total": total,
            "passed": passed,
            "failed": failed,
            "skipped": skipped,
            "pass_rate": f"{(passed / total * 100):.2f}%" if total > 0 else "0%",
            "total_duration": round(total_duration, 2),
            "avg_duration": round(avg_duration, 2)
        }
        
        # 🛡️ 添加 ResilienceEngine 统计
        if self.resilience:
            stats["resilience"] = self.resilience.get_statistics()
        
        return stats
