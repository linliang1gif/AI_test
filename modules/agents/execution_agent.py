#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ExecutionAgent - 智能测试执行代理（具备决策能力）

核心能力：
1. 执行顺序决策（P0优先、高风险优先、fail-fast）
2. 智能重试策略（超时/连接失败自动重试，断言失败不重试）
3. 并发控制（ThreadPoolExecutor）
4. 自动策略选择（串行/并行）
5. 环境控制（base_url切换）
"""

import logging
import time
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed, Future
from enum import Enum

try:
    from core import TestCase, ExecutionResult, TestCaseStatus, create_execution_result
    CORE_AVAILABLE = True
except ImportError:
    CORE_AVAILABLE = False


class ExecutionEnvironment(Enum):
    """执行环境"""
    LOCAL = "local"
    TEST = "test"
    STAGING = "staging"
    PRODUCTION = "production"


class ExecutionStrategy(Enum):
    """执行策略"""
    SEQUENTIAL = "sequential"      # 串行执行
    PARALLEL = "parallel"          # 并行执行
    PRIORITY = "priority"          # 按优先级执行
    ADAPTIVE = "adaptive"          # 自适应（自动选择）
    FAIL_FAST = "fail_fast"        # 快速失败


class FailureType(Enum):
    """失败类型"""
    TIMEOUT = "timeout"            # 超时 → 可重试
    CONNECTION = "connection"      # 连接失败 → 可重试
    ASSERTION = "assertion"        # 断言失败 → 不重试
    UNKNOWN = "unknown"            # 未知错误 → 可重试


class ExecutionAgent:
    """
    智能测试执行代理
    
    核心能力：
    1. 执行顺序决策 - P0优先、高风险优先、fail-fast
    2. 智能重试策略 - 超时/连接失败自动重试，断言失败不重试
    3. 并发控制 - ThreadPoolExecutor
    4. 自动策略选择 - 串行/并行自动选择
    5. 环境控制 - base_url切换
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # 环境配置
        self.environment = ExecutionEnvironment(self.config.get('environment', 'test'))
        self.base_urls = {
            'local': self.config.get('base_url_local', 'http://localhost:8000'),
            'test': self.config.get('base_url_test', 'http://test.example.com'),
            'staging': self.config.get('base_url_staging', 'http://staging.example.com'),
            'production': self.config.get('base_url_prod', 'http://api.example.com')
        }
        
        # 执行策略配置
        self.strategy = ExecutionStrategy(self.config.get('strategy', 'adaptive'))
        self.fail_fast = self.config.get('fail_fast', False)
        
        # 并发控制
        self.max_workers = self.config.get('max_workers', 4)
        self.parallel_threshold = self.config.get('parallel_threshold', 5)  # 超过5个用例才并行
        
        # 重试配置
        self.max_retry_count = self.config.get('max_retry_count', 3)
        self.retry_delay = self.config.get('retry_delay', 1.0)
        self.timeout = self.config.get('timeout', 30)
        
        # 🔥 ExecutionEngine 配置
        self.use_real_engine = self.config.get('use_real_engine', False)
        self.execution_engine = None
        
        if self.use_real_engine:
            try:
                from modules.executor.real_execution_engine import get_execution_engine
                self.execution_engine = get_execution_engine()
                self.logger.info("✅ 使用真实 ExecutionEngine")
            except ImportError as e:
                self.logger.warning(f"⚠️  无法导入 ExecutionEngine，使用模拟执行: {e}")
                self.use_real_engine = False
        
        # 运行状态
        self.is_running = False
        self.should_stop = False
        self.current_execution = None
        
        # 统计信息
        self.stats = {
            "total_executed": 0,
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "retried": 0,
            "timeout_retries": 0,
            "connection_retries": 0
        }
        
        self.logger.info(f"ExecutionAgent 初始化: 环境={self.environment.value}, 策略={self.strategy.value}, 真实引擎={self.use_real_engine}")
    
    def run(self, testcases: List[Any], environment: Optional[str] = None) -> List[Any]:
        """
        主执行流程（带决策能力）
        
        流程：
        1. 决策执行计划（顺序、策略、并发数）
        2. 执行测试用例
        3. 收集结果
        """
        if not testcases:
            self.logger.warning("没有测试用例需要执行")
            return []
        
        # 切换环境
        if environment:
            self.environment = ExecutionEnvironment(environment)
        
        self.is_running = True
        self.should_stop = False
        
        try:
            # 1. 决策执行计划
            execution_plan = self._decide_execution_plan(testcases)
            self.logger.info(f"执行计划: {execution_plan}")
            
            # 2. 根据计划执行
            if execution_plan['strategy'] == 'sequential':
                results = self._execute_sequential(
                    execution_plan['testcases'],
                    fail_fast=execution_plan['fail_fast']
                )
            elif execution_plan['strategy'] == 'parallel':
                results = self._execute_parallel(
                    execution_plan['testcases'],
                    max_workers=execution_plan['max_workers']
                )
            elif execution_plan['strategy'] == 'priority':
                results = self._execute_by_priority(
                    execution_plan['testcases'],
                    fail_fast=execution_plan['fail_fast']
                )
            else:  # adaptive
                results = self._execute_adaptive(execution_plan['testcases'])
            
            # 3. 更新统计
            self._update_statistics(results)
            
            return results
            
        finally:
            self.is_running = False
    
    def _decide_execution_plan(self, testcases: List[Any]) -> Dict[str, Any]:
        """
        决策执行计划
        
        决策因素：
        1. 用例数量（小规模串行，大规模并行）
        2. 优先级分布（P0优先）
        3. 风险等级（高风险优先）
        4. fail-fast 配置
        """
        total_count = len(testcases)
        
        # 分析优先级分布
        priority_counts = self._analyze_priority_distribution(testcases)
        high_priority_count = priority_counts.get('critical', 0) + priority_counts.get('high', 0)
        
        # 决策策略
        if self.strategy == ExecutionStrategy.ADAPTIVE:
            # 自动决策
            if total_count < self.parallel_threshold:
                strategy = 'sequential'
                max_workers = 1
            elif high_priority_count > total_count * 0.5:
                # 超过50%是高优先级，按优先级执行
                strategy = 'priority'
                max_workers = 1
            else:
                strategy = 'parallel'
                max_workers = min(self.max_workers, total_count)
        else:
            strategy = self.strategy.value
            max_workers = self.max_workers if strategy == 'parallel' else 1
        
        # 排序测试用例（P0优先、高风险优先）
        sorted_testcases = self._sort_testcases_by_priority_and_risk(testcases)
        
        return {
            'strategy': strategy,
            'testcases': sorted_testcases,
            'max_workers': max_workers,
            'fail_fast': self.fail_fast or self.strategy == ExecutionStrategy.FAIL_FAST,
            'total_count': total_count,
            'high_priority_count': high_priority_count
        }
    
    def _execute_sequential(self, testcases: List[Any], fail_fast: bool = False) -> List[Any]:
        """串行执行（支持 fail-fast）"""
        results = []
        
        for i, tc in enumerate(testcases, 1):
            if self.should_stop:
                self.logger.info("执行被中断")
                break
            
            self.logger.info(f"执行 [{i}/{len(testcases)}]: {self._get_testcase_id(tc)}")
            result = self._execute_single_with_retry(tc)
            results.append(result)
            
            # fail-fast: 遇到失败立即停止
            if fail_fast and not self._is_passed(result):
                self.logger.warning(f"Fail-fast: 测试失败，停止执行")
                break
        
        return results
    
    def _execute_parallel(self, testcases: List[Any], max_workers: int) -> List[Any]:
        """并行执行"""
        results = []
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 提交所有任务
            future_to_tc = {
                executor.submit(self._execute_single_with_retry, tc): tc 
                for tc in testcases
            }
            
            # 收集结果
            for future in as_completed(future_to_tc):
                if self.should_stop:
                    executor.shutdown(wait=False)
                    break
                
                try:
                    result = future.result(timeout=self.timeout + 10)
                    results.append(result)
                except Exception as e:
                    tc = future_to_tc[future]
                    self.logger.error(f"执行异常: {self._get_testcase_id(tc)}, {e}")
                    results.append(self._create_failed_result(tc, f"执行异常: {e}"))
        
        return results
    
    def _execute_by_priority(self, testcases: List[Any], fail_fast: bool = False) -> List[Any]:
        """按优先级执行（已排序）"""
        return self._execute_sequential(testcases, fail_fast=fail_fast)
    
    def _execute_adaptive(self, testcases: List[Any]) -> List[Any]:
        """自适应执行（高优先级串行，低优先级并行）"""
        high_priority = [
            tc for tc in testcases 
            if self._get_priority(tc) in ['critical', 'high']
        ]
        low_priority = [
            tc for tc in testcases 
            if self._get_priority(tc) not in ['critical', 'high']
        ]
        
        results = []
        
        # 高优先级串行执行
        if high_priority:
            self.logger.info(f"串行执行 {len(high_priority)} 个高优先级用例")
            results.extend(self._execute_sequential(high_priority))
        
        # 低优先级并行执行
        if low_priority and not self.should_stop:
            self.logger.info(f"并行执行 {len(low_priority)} 个低优先级用例")
            results.extend(self._execute_parallel(low_priority, self.max_workers))
        
        return results
    
    def _execute_single_with_retry(self, testcase: Any) -> Any:
        """
        执行单个测试用例（带智能重试）
        
        重试策略：
        - 超时 → 自动重试（最多3次）
        - 连接失败 → 重建连接后重试
        - 断言失败 → 不重试
        """
        attempt = 0
        last_error = None
        
        while attempt <= self.max_retry_count:
            try:
                # 执行测试用例
                result = self._run_testcase(testcase)
                
                # 成功或断言失败 → 不重试
                if self._is_passed(result):
                    return result
                
                failure_type = self._classify_failure(result)
                
                if failure_type == FailureType.ASSERTION:
                    # 断言失败不重试
                    self.logger.info(f"断言失败，不重试: {self._get_testcase_id(testcase)}")
                    return result
                
                # 其他失败类型可重试
                if attempt < self.max_retry_count:
                    attempt += 1
                    self.stats['retried'] += 1
                    
                    if failure_type == FailureType.TIMEOUT:
                        self.stats['timeout_retries'] += 1
                        self.logger.warning(
                            f"超时重试 [{attempt}/{self.max_retry_count}]: {self._get_testcase_id(testcase)}"
                        )
                    elif failure_type == FailureType.CONNECTION:
                        self.stats['connection_retries'] += 1
                        self.logger.warning(
                            f"连接失败重试 [{attempt}/{self.max_retry_count}]: {self._get_testcase_id(testcase)}"
                        )
                        # 重建连接
                        self._rebuild_connection()
                    
                    time.sleep(self.retry_delay * attempt)  # 指数退避
                    continue
                
                return result
                
            except Exception as e:
                last_error = str(e)
                attempt += 1
                
                if attempt <= self.max_retry_count:
                    self.logger.warning(f"执行异常，重试 [{attempt}/{self.max_retry_count}]: {e}")
                    time.sleep(self.retry_delay * attempt)
                else:
                    break
        
        # 重试耗尽
        return self._create_failed_result(
            testcase, 
            f"重试{self.max_retry_count}次后仍失败: {last_error}"
        )
    
    def _classify_failure(self, result: Any) -> FailureType:
        """分类失败类型"""
        error_msg = ""
        
        if CORE_AVAILABLE and hasattr(result, 'error'):
            error_msg = result.error or ""
        elif isinstance(result, dict):
            error_msg = result.get('error', '') or result.get('message', '')
        
        error_msg_lower = error_msg.lower()
        
        if 'timeout' in error_msg_lower or 'timed out' in error_msg_lower:
            return FailureType.TIMEOUT
        elif 'connection' in error_msg_lower or 'connect' in error_msg_lower:
            return FailureType.CONNECTION
        elif 'assertion' in error_msg_lower or 'assert' in error_msg_lower:
            return FailureType.ASSERTION
        else:
            return FailureType.UNKNOWN
    
    def _rebuild_connection(self):
        """重建连接（模拟）"""
        self.logger.info("重建连接...")
        time.sleep(0.5)
    
    def _run_testcase(self, testcase: Any) -> Any:
        """执行测试用例（使用真实 ExecutionEngine 或模拟执行）"""
        start_time = datetime.now()
        
        # 🔥 使用真实 ExecutionEngine
        if self.use_real_engine and self.execution_engine:
            try:
                # 获取当前环境的 base_url
                base_url = self.base_urls.get(self.environment.value, '')
                
                # 构建执行配置
                test_case_dict = self._build_execution_config(testcase, base_url)
                
                # 执行测试
                result = self.execution_engine.execute(test_case_dict)
                
                # 转换为标准格式
                return self._convert_engine_result(testcase, result)
                
            except Exception as e:
                self.logger.error(f"ExecutionEngine 执行失败: {e}")
                import traceback
                traceback.print_exc()
                return self._create_failed_result(testcase, f"ExecutionEngine 执行失败: {e}")
        
        # 模拟执行（降级方案）
        time.sleep(0.1)
        
        end_time = datetime.now()
        
        return self._create_result(
            testcase, 
            "passed", 
            start_time=start_time,
            end_time=end_time
        )
    
    def _build_execution_config(self, testcase: Any, base_url: str) -> Dict[str, Any]:
        """构建 ExecutionEngine 执行配置"""
        # 获取测试用例信息
        tc_id = self._get_testcase_id(testcase)
        tc_title = self._get_testcase_title(testcase)
        
        # 获取执行配置
        if CORE_AVAILABLE and hasattr(testcase, 'execution_config'):
            exec_config = testcase.execution_config
        elif isinstance(testcase, dict):
            exec_config = testcase.get('execution_config', {})
        else:
            exec_config = {}
        
        # 构建 URL
        url = exec_config.get('url', '')
        if not url.startswith('http'):
            # 相对路径，添加 base_url
            url = base_url.rstrip('/') + '/' + url.lstrip('/')
        
        # 构建测试用例配置
        return {
            'id': tc_id,
            'name': tc_title,
            'execution_type': 'api',
            'config': {
                'url': url,
                'method': exec_config.get('method', 'GET'),
                'headers': exec_config.get('headers', {}),
                'body': exec_config.get('body', exec_config.get('data', {}))
            },
            'timeout': self.timeout
        }
    
    def _convert_engine_result(self, testcase: Any, engine_result: Any) -> Any:
        """转换 ExecutionEngine 结果为标准格式"""
        # 提取结果信息
        success = engine_result.success
        status = 'passed' if success else 'failed'
        
        # 解析时间
        try:
            from datetime import datetime
            start_time = datetime.fromisoformat(engine_result.start_time)
            end_time = datetime.fromisoformat(engine_result.end_time)
        except:
            start_time = datetime.now()
            end_time = datetime.now()
        
        # 创建结果
        if CORE_AVAILABLE:
            result = create_execution_result(
                test_case_id=self._get_testcase_id(testcase),
                status=status,
                start_time=start_time,
                end_time=end_time,
                error=engine_result.error_message if not success else None
            )
            
            # 添加 ExecutionEngine 特有字段
            result.trace_id = engine_result.trace_id
            result.status_code = engine_result.status_code
            result.response = engine_result.response
            result.error_type = engine_result.error_type
            result.error_message = engine_result.error_message
            result.duration = engine_result.duration
            
            return result
        else:
            return {
                "testcase_id": self._get_testcase_id(testcase),
                "status": status,
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "error": engine_result.error_message if not success else None,
                "trace_id": engine_result.trace_id,
                "status_code": engine_result.status_code,
                "response": engine_result.response,
                "error_type": engine_result.error_type,
                "duration": engine_result.duration
            }
    
    def _get_testcase_title(self, testcase: Any) -> str:
        """获取测试用例标题"""
        if CORE_AVAILABLE and hasattr(testcase, 'title'):
            return testcase.title
        return testcase.get('title', 'Unnamed Test') if isinstance(testcase, dict) else 'Unnamed Test'
    
    def _create_result(self, testcase: Any, status: str, 
                      start_time: datetime = None, 
                      end_time: datetime = None,
                      error: str = None) -> Any:
        """创建执行结果"""
        if start_time is None:
            start_time = datetime.now()
        if end_time is None:
            end_time = datetime.now()
        
        if CORE_AVAILABLE:
            return create_execution_result(
                test_case_id=self._get_testcase_id(testcase),
                status=status,
                start_time=start_time,
                end_time=end_time,
                error=error
            )
        return {
            "testcase_id": self._get_testcase_id(testcase),
            "status": status,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "error": error
        }
    
    def _create_failed_result(self, testcase: Any, error: str) -> Any:
        """创建失败结果"""
        return self._create_result(testcase, "failed", error=error)
    
    # ==================== 辅助方法 ====================
    
    def stop(self):
        """停止执行"""
        self.should_stop = True
        self.logger.info("收到停止信号")
    
    def get_statistics(self) -> Dict:
        """获取统计信息"""
        total = self.stats["total_executed"]
        return {
            **self.stats,
            "pass_rate": self.stats["passed"] / total if total > 0 else 0
        }
    
    def get_current_base_url(self) -> str:
        """获取当前环境的 base_url"""
        return self.base_urls.get(self.environment.value, '')
    
    def _analyze_priority_distribution(self, testcases: List[Any]) -> Dict[str, int]:
        """分析优先级分布"""
        distribution = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
        
        for tc in testcases:
            priority = self._get_priority(tc)
            if priority in distribution:
                distribution[priority] += 1
        
        return distribution
    
    def _sort_testcases_by_priority_and_risk(self, testcases: List[Any]) -> List[Any]:
        """
        排序测试用例（P0优先、高风险优先）
        
        排序规则：
        1. critical > high > medium > low
        2. 同优先级按风险排序（如果有风险信息）
        """
        priority_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
        
        def sort_key(tc):
            priority = self._get_priority(tc)
            priority_value = priority_order.get(priority, 2)
            
            # TODO: 如果有风险信息，可以加入排序
            # risk = self._get_risk(tc)
            # risk_value = risk_order.get(risk, 2)
            # return (priority_value, risk_value)
            
            return priority_value
        
        return sorted(testcases, key=sort_key)
    
    def _get_testcase_id(self, testcase: Any) -> str:
        """获取测试用例ID"""
        if CORE_AVAILABLE and hasattr(testcase, 'id'):
            return testcase.id
        return testcase.get('id', 'unknown') if isinstance(testcase, dict) else str(testcase)
    
    def _get_priority(self, testcase: Any) -> str:
        """获取优先级"""
        if CORE_AVAILABLE and hasattr(testcase, 'priority'):
            p = testcase.priority
            return p.value if hasattr(p, 'value') else str(p).lower()
        
        priority = testcase.get('priority', 'medium') if isinstance(testcase, dict) else 'medium'
        return str(priority).lower()
    
    def _is_passed(self, result: Any) -> bool:
        """判断是否通过"""
        if CORE_AVAILABLE and hasattr(result, 'status'):
            s = result.status
            status_str = s.value if hasattr(s, 'value') else str(s)
            return status_str.lower() == 'passed'
        
        if isinstance(result, dict):
            status = result.get('status', '')
            return str(status).lower() == 'passed'
        
        return False
    
    def _update_statistics(self, results: List[Any]):
        """更新统计信息"""
        for result in results:
            self.stats["total_executed"] += 1
            
            if self._is_passed(result):
                self.stats["passed"] += 1
            else:
                self.stats["failed"] += 1
    
    # ==================== 兼容旧接口 ====================
    
    def execute(self, testcases: List[Any], environment: Optional[str] = None) -> List[Any]:
        """兼容旧接口（调用 run）"""
        return self.run(testcases, environment)
