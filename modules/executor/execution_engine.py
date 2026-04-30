"""
测试执行引擎 - 无pytest版本
🔥 架构升级: Test Intelligence Agent 完全接管执行层
- ExecutionEngine 只能执行 execution_plan (禁止直接执行 test_cases)
- 引入 test_cases_map 解决 TestCase 查找问题
- 保留 execute_legacy 兼容旧代码 (但内部强制走 Intelligence)
- 所有执行路径统一
"""
import time
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Optional
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


class ExecutionEngine:
    """
    测试执行引擎 (Intelligence Agent 接管版)
    
    🔥 新架构特性:
    - 只能执行 execution_plan (由 Intelligence Agent 生成)
    - 引入 test_cases_map 解决 TestCase 查找问题
    - 保留 execute_legacy 兼容旧代码 (但内部强制走 Intelligence)
    - 支持并发执行
    - 支持API/UI/Integration扩展
    - 统一返回ExecutionResult
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        初始化执行引擎
        
        Args:
            config: 配置字典
                - base_url: API基础URL
                - timeout: 默认超时时间
                - retry_on_failure: 失败时是否重试
                - max_retries: 最大重试次数
                - resilience_enabled: 是否启用稳定性引擎(默认True)
        """
        self.config = config or {}
        self.runners = {}
        
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
            test_type: 测试类型(如 "api", "ui")
            runner: Runner实例,必须实现run(test_case)方法
        """
        self.runners[test_type] = runner
    
    # ==================== 🔥 新架构: 只能执行 execution_plan ====================
    
    def execute_plan(self, execution_plan: Dict, test_cases_map: Dict) -> List[ExecutionResult]:
        """
        🔥 新架构: 执行 execution_plan (由 Intelligence Agent 生成)
        
        Args:
            execution_plan: 执行计划 (由 TestIntelligenceAgent.optimize_execution_plan 生成)
                - selected_tests: 选中的测试用例ID列表
                - execution_order: 执行顺序 (按风险评分排序)
                - parallel_groups: 并发分组 (按module分组)
                - risk_scores: 风险评分列表
                - statistics: 统计信息
            test_cases_map: TestCase映射 {test_case_id: TestCase对象}
            
        Returns:
            ExecutionResult列表
        """
        if not execution_plan or not test_cases_map:
            return []
        
        # 1. 获取执行顺序
        execution_order = execution_plan.get('execution_order', [])
        parallel_groups = execution_plan.get('parallel_groups', {})
        
        print(f"  🎯 执行计划:")
        print(f"     总用例: {len(test_cases_map)}")
        print(f"     选中: {len(execution_order)}")
        print(f"     跳过: {len(test_cases_map) - len(execution_order)}")
        print(f"     并发组: {len(parallel_groups)}")
        
        # 2. 按执行顺序构建 TestCase 列表
        ordered_test_cases = []
        for test_id in execution_order:
            test_case = test_cases_map.get(test_id)
            if test_case:
                ordered_test_cases.append(test_case)
            else:
                print(f"  ⚠️  警告: 找不到测试用例 {test_id}")
        
        # 3. 执行测试 (使用并发分组)
        results = self._execute_with_groups(ordered_test_cases, parallel_groups)
        
        return results
    
    def _execute_with_groups(self, test_cases: List, parallel_groups: Dict) -> List[ExecutionResult]:
        """
        按并发分组执行测试
        
        Args:
            test_cases: TestCase列表 (已排序)
            parallel_groups: 并发分组 {module: [test_case_id, ...]}
            
        Returns:
            ExecutionResult列表
        """
        # 如果没有分组信息,使用默认并发执行
        if not parallel_groups:
            return self._execute_parallel(test_cases, max_workers=5)
        
        # 按分组执行
        all_results = []
        
        for module, test_ids in parallel_groups.items():
            # 获取该组的测试用例
            group_cases = [tc for tc in test_cases if tc.id in test_ids]
            
            if not group_cases:
                continue
            
            print(f"  📦 执行分组: {module} ({len(group_cases)} 个用例)")
            
            # 并发执行该组
            group_results = self._execute_parallel(group_cases, max_workers=5)
            all_results.extend(group_results)
        
        return all_results
    
    # ==================== 🔥 兼容层: execute_legacy ====================
    
    def execute_legacy(self, test_cases: List, max_workers: int = 5, 
                      parallel: bool = True) -> List[ExecutionResult]:
        """
        🔥 兼容旧代码: 但内部强制走 Intelligence Agent
        
        Args:
            test_cases: TestCase列表
            max_workers: 最大并发数
            parallel: 是否并行执行
            
        Returns:
            ExecutionResult列表
        """
        print(f"  ⚠️  警告: 使用 execute_legacy (兼容模式)")
        print(f"  💡 建议: 使用 execute_plan + TestIntelligenceAgent")
        
        # 🔥 强制走 Intelligence Agent
        from modules.agents import TestIntelligenceAgent, TestCase as IntelligenceTestCase
        
        # 1. 转换为 Intelligence TestCase
        intelligence_cases = []
        for tc in test_cases:
            intelligence_cases.append(IntelligenceTestCase(
                test_case_id=tc.id,
                api=getattr(tc, 'api_id', tc.id),
                module=tc.module,
                priority=tc.priority.value if hasattr(tc.priority, 'value') else str(tc.priority),
                tags=getattr(tc, 'tags', [])
            ))
        
        # 2. 使用 Intelligence Agent 生成执行计划
        intelligence_agent = TestIntelligenceAgent()
        execution_plan = intelligence_agent.optimize_execution_plan(intelligence_cases)
        
        # 3. 构建 test_cases_map
        test_cases_map = {tc.id: tc for tc in test_cases}
        
        # 4. 执行计划
        return self.execute_plan(execution_plan, test_cases_map)
    
    def execute(self, test_cases: List, max_workers: int = 5, 
                parallel: bool = True) -> List[ExecutionResult]:
        """
        🔥 已废弃: 请使用 execute_plan 或 execute_legacy
        
        为了向后兼容,暂时保留,但会打印警告
        """
        print(f"  ⚠️  警告: execute() 已废弃,请使用 execute_plan() 或 execute_legacy()")
        return self.execute_legacy(test_cases, max_workers, parallel)
    
    # ==================== 内部执行方法 ====================
    
    def _execute_parallel(self, test_cases: List, max_workers: int) -> List[ExecutionResult]:
        """并行执行"""
        results = []
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 提交所有任务
            future_to_case = {
                executor.submit(self._run_single, case): case
                for case in test_cases
            }
            
            # 收集结果(按完成顺序)
            for future in as_completed(future_to_case):
                test_case = future_to_case[future]
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    # 如果执行过程中出现异常,创建错误结果
                    now = datetime.now()
                    results.append(create_execution_result(
                        test_case_id=test_case.id,
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
                    api=getattr(test_case, 'id', 'unknown')
                )
                return result
            except Exception as e:
                # ResilienceEngine 所有重试都失败
                end_time_dt = datetime.now()
                return create_execution_result(
                    test_case_id=test_case.id,
                    status="failed",
                    start_time=start_time_dt,
                    end_time=end_time_dt,
                    error=str(e),
                    stack_trace=traceback.format_exc(),
                    error_type=type(e).__name__
                )
        else:
            # 不使用 ResilienceEngine(原有逻辑)
            return self._execute_test_with_retry(test_case, start_time_dt)
    
    def _execute_test(self, test_case) -> ExecutionResult:
        """
        执行测试(核心逻辑)
        
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
        
        # 统计断言结果
        assertion_details = runner_result.get("assertion_results", [])
        assertions_passed = sum(1 for a in assertion_details if a.get('passed', False))
        assertions_failed = sum(1 for a in assertion_details if not a.get('passed', True))
        
        result = create_execution_result(
            test_case_id=test_case.id,
            status=status_str,
            start_time=start_time_dt,
            end_time=end_time_dt,
            error=runner_result.get("error_message"),
            stack_trace=runner_result.get("stack_trace"),
            response=runner_result.get("actual_response"),
            assertion_details=assertion_details,
            assertions_passed=assertions_passed,
            assertions_failed=assertions_failed
        )
        
        return result
    
    def _execute_test_with_retry(self, test_case, start_time_dt) -> ExecutionResult:
        """
        执行测试(带重试,原有逻辑)
        
        Args:
            test_case: TestCase对象
            start_time_dt: 开始时间
            
        Returns:
            ExecutionResult
        """
        start_time_ts = time.time()
        retry_count = 0
        max_retries = self.config.get('max_retries', 0)
        
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
                
                # 统计断言结果
                assertion_details = runner_result.get("assertion_results", [])
                assertions_passed = sum(1 for a in assertion_details if a.get('passed', False))
                assertions_failed = sum(1 for a in assertion_details if not a.get('passed', True))
                
                result = create_execution_result(
                    test_case_id=test_case.id,
                    status=status_str,
                    start_time=start_time_dt,
                    end_time=end_time_dt,
                    error=runner_result.get("error_message"),
                    stack_trace=runner_result.get("stack_trace"),
                    response=runner_result.get("actual_response"),
                    assertion_details=assertion_details,
                    assertions_passed=assertions_passed,
                    assertions_failed=assertions_failed
                )
                
                # 添加重试信息(通过直接赋值,因为dataclass允许)
                result.retry_count = retry_count
                
                # 4. 如果成功或不需要重试,直接返回
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
                        test_case_id=test_case.id,
                        status="failed",
                        start_time=start_time_dt,
                        end_time=end_time_dt,
                        error=str(e),
                        stack_trace=traceback.format_exc(),
                        error_type=type(e).__name__
                    )
                
                # 重试前等待
                time.sleep(self.config.get('retry_delay', 1))
        
        # 不应该到这里,但为了安全返回错误结果
        end_time_dt = datetime.now()
        return create_execution_result(
            test_case_id=test_case.id,
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
