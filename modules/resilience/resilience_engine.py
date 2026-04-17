#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ResilienceEngine - 稳定性引擎

核心功能：
1. 智能重试（Retry）- 指数退避，仅对可重试错误
2. 熔断机制（Circuit Breaker）- 连续失败后熔断
3. 限流（Rate Limiter）- 全局和API级别限流
4. 错误分类 - RETRYABLE vs NON_RETRYABLE

目标：提高测试执行稳定性，避免因外部系统不稳定导致误判
"""

import time
import logging
import threading
from typing import Callable, Dict, Any, Optional
from datetime import datetime, timedelta
from enum import Enum
from collections import defaultdict


class ErrorCategory(Enum):
    """错误分类"""
    RETRYABLE = "retryable"           # 可重试（timeout/connection/5xx）
    NON_RETRYABLE = "non_retryable"   # 不可重试（4xx/assertion）


class CircuitState(Enum):
    """熔断器状态"""
    CLOSED = "closed"       # 关闭（正常）
    OPEN = "open"           # 打开（熔断）
    HALF_OPEN = "half_open" # 半开（恢复中）


class ResilienceConfig:
    """稳定性配置"""
    
    def __init__(
        self,
        # 重试配置
        max_retries: int = 3,
        retry_delay: float = 1.0,
        exponential_backoff: bool = True,
        
        # 熔断配置
        circuit_breaker_enabled: bool = True,
        failure_threshold: int = 5,
        recovery_timeout: int = 30,
        half_open_max_calls: int = 3,
        
        # 限流配置
        rate_limiter_enabled: bool = True,
        global_qps: int = 100,
        api_qps: int = 10
    ):
        # 重试
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.exponential_backoff = exponential_backoff
        
        # 熔断
        self.circuit_breaker_enabled = circuit_breaker_enabled
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_calls = half_open_max_calls
        
        # 限流
        self.rate_limiter_enabled = rate_limiter_enabled
        self.global_qps = global_qps
        self.api_qps = api_qps


class CircuitBreaker:
    """
    熔断器
    
    规则：
    - 连续失败 >= failure_threshold → 熔断（OPEN）
    - 熔断后 recovery_timeout 秒内不再请求
    - 半开状态：允许少量请求恢复
    """
    
    def __init__(self, config: ResilienceConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # API级别的熔断状态
        self.circuits: Dict[str, Dict] = defaultdict(lambda: {
            "state": CircuitState.CLOSED,
            "failure_count": 0,
            "last_failure_time": None,
            "half_open_calls": 0
        })
        
        self.lock = threading.Lock()
    
    def is_open(self, api: str) -> bool:
        """判断熔断器是否打开（熔断中）"""
        with self.lock:
            circuit = self.circuits[api]
            
            # 如果是 CLOSED，直接返回 False
            if circuit["state"] == CircuitState.CLOSED:
                return False
            
            # 如果是 OPEN，检查是否可以进入 HALF_OPEN
            if circuit["state"] == CircuitState.OPEN:
                if self._should_attempt_reset(circuit):
                    circuit["state"] = CircuitState.HALF_OPEN
                    circuit["half_open_calls"] = 0
                    self.logger.info(f"熔断器 {api} 进入半开状态")
                    return False
                return True
            
            # 如果是 HALF_OPEN，检查是否还能继续尝试
            if circuit["state"] == CircuitState.HALF_OPEN:
                if circuit["half_open_calls"] < self.config.half_open_max_calls:
                    return False
                return True
            
            return False
    
    def record_success(self, api: str):
        """记录成功"""
        with self.lock:
            circuit = self.circuits[api]
            
            if circuit["state"] == CircuitState.HALF_OPEN:
                # 半开状态下成功 → 关闭熔断器
                circuit["state"] = CircuitState.CLOSED
                circuit["failure_count"] = 0
                circuit["half_open_calls"] = 0
                self.logger.info(f"熔断器 {api} 恢复正常（CLOSED）")
            else:
                # 正常状态下成功 → 重置失败计数
                circuit["failure_count"] = 0
    
    def record_failure(self, api: str):
        """记录失败"""
        with self.lock:
            circuit = self.circuits[api]
            circuit["failure_count"] += 1
            circuit["last_failure_time"] = datetime.now()
            
            if circuit["state"] == CircuitState.HALF_OPEN:
                # 半开状态下失败 → 重新打开熔断器
                circuit["state"] = CircuitState.OPEN
                self.logger.warning(f"熔断器 {api} 重新打开（OPEN）")
            
            elif circuit["state"] == CircuitState.CLOSED:
                # 关闭状态下连续失败 → 打开熔断器
                if circuit["failure_count"] >= self.config.failure_threshold:
                    circuit["state"] = CircuitState.OPEN
                    self.logger.warning(
                        f"熔断器 {api} 打开（OPEN）- 连续失败 {circuit['failure_count']} 次"
                    )
            
            if circuit["state"] == CircuitState.HALF_OPEN:
                circuit["half_open_calls"] += 1
    
    def _should_attempt_reset(self, circuit: Dict) -> bool:
        """判断是否应该尝试重置（进入半开状态）"""
        if circuit["last_failure_time"] is None:
            return False
        
        elapsed = (datetime.now() - circuit["last_failure_time"]).total_seconds()
        return elapsed >= self.config.recovery_timeout
    
    def get_state(self, api: str) -> CircuitState:
        """获取熔断器状态"""
        with self.lock:
            return self.circuits[api]["state"]
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        with self.lock:
            stats = {
                "total_circuits": len(self.circuits),
                "open": 0,
                "half_open": 0,
                "closed": 0,
                "circuits": {}
            }
            
            for api, circuit in self.circuits.items():
                state = circuit["state"]
                stats["circuits"][api] = {
                    "state": state.value,
                    "failure_count": circuit["failure_count"]
                }
                
                if state == CircuitState.OPEN:
                    stats["open"] += 1
                elif state == CircuitState.HALF_OPEN:
                    stats["half_open"] += 1
                else:
                    stats["closed"] += 1
            
            return stats


class RateLimiter:
    """
    限流器
    
    支持：
    - 全局限流（QPS）
    - API级别限流
    """
    
    def __init__(self, config: ResilienceConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # 全局请求记录（时间戳列表）
        self.global_requests = []
        
        # API级别请求记录
        self.api_requests: Dict[str, list] = defaultdict(list)
        
        self.lock = threading.Lock()
    
    def acquire(self, api: str) -> bool:
        """
        获取许可（限流检查）
        
        Returns:
            True: 允许请求
            False: 超过限流，拒绝请求
        """
        with self.lock:
            now = time.time()
            
            # 清理过期记录（1秒前）
            self._cleanup_old_requests(now)
            
            # 检查全局限流
            if len(self.global_requests) >= self.config.global_qps:
                self.logger.warning(f"全局限流触发: {len(self.global_requests)}/{self.config.global_qps} QPS")
                return False
            
            # 检查 API 级别限流
            if len(self.api_requests[api]) >= self.config.api_qps:
                self.logger.warning(f"API 限流触发 {api}: {len(self.api_requests[api])}/{self.config.api_qps} QPS")
                return False
            
            # 记录请求
            self.global_requests.append(now)
            self.api_requests[api].append(now)
            
            return True
    
    def _cleanup_old_requests(self, now: float):
        """清理1秒前的请求记录"""
        cutoff = now - 1.0
        
        # 清理全局记录
        self.global_requests = [t for t in self.global_requests if t > cutoff]
        
        # 清理 API 记录
        for api in list(self.api_requests.keys()):
            self.api_requests[api] = [t for t in self.api_requests[api] if t > cutoff]
            
            # 删除空列表
            if not self.api_requests[api]:
                del self.api_requests[api]
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        with self.lock:
            now = time.time()
            self._cleanup_old_requests(now)
            
            return {
                "global_qps": len(self.global_requests),
                "global_limit": self.config.global_qps,
                "api_qps": {
                    api: len(requests)
                    for api, requests in self.api_requests.items()
                },
                "api_limit": self.config.api_qps
            }


class ResilienceEngine:
    """
    稳定性引擎
    
    核心功能：
    1. 智能重试（指数退避）
    2. 熔断机制
    3. 限流
    4. 错误分类
    """
    
    def __init__(self, config: Optional[ResilienceConfig] = None):
        """
        初始化稳定性引擎
        
        Args:
            config: 稳定性配置
        """
        self.config = config or ResilienceConfig()
        self.logger = logging.getLogger(__name__)
        
        # 熔断器
        self.circuit_breaker = CircuitBreaker(self.config)
        
        # 限流器
        self.rate_limiter = RateLimiter(self.config)
        
        # 统计信息
        self.stats = {
            "total_calls": 0,
            "retried_calls": 0,
            "circuit_breaker_rejections": 0,
            "rate_limiter_rejections": 0,
            "successful_calls": 0,
            "failed_calls": 0
        }
        
        self.logger.info(f"ResilienceEngine 初始化: max_retries={self.config.max_retries}, "
                        f"circuit_breaker={self.config.circuit_breaker_enabled}, "
                        f"rate_limiter={self.config.rate_limiter_enabled}")
    
    def execute_with_resilience(
        self,
        func: Callable,
        api: str = "default",
        config: Optional[Dict] = None
    ) -> Any:
        """
        包装执行（带重试+熔断+限流）
        
        Args:
            func: 要执行的函数
            api: API标识（用于熔断和限流）
            config: 执行配置（可选）
        
        Returns:
            函数执行结果
        
        Raises:
            Exception: 如果所有重试都失败
        """
        self.stats["total_calls"] += 1
        
        # 1. 熔断检查
        if self.config.circuit_breaker_enabled:
            if self.circuit_breaker.is_open(api):
                self.stats["circuit_breaker_rejections"] += 1
                raise Exception(f"Circuit breaker is OPEN for {api}")
        
        # 2. 限流检查
        if self.config.rate_limiter_enabled:
            if not self.rate_limiter.acquire(api):
                self.stats["rate_limiter_rejections"] += 1
                raise Exception(f"Rate limit exceeded for {api}")
        
        # 3. 执行（带重试）
        last_error = None
        
        for attempt in range(self.config.max_retries + 1):
            try:
                # 执行函数
                result = func()
                
                # 成功 → 记录成功
                self.stats["successful_calls"] += 1
                if self.config.circuit_breaker_enabled:
                    self.circuit_breaker.record_success(api)
                
                if attempt > 0:
                    self.logger.info(f"重试成功: {api} (第 {attempt} 次重试)")
                
                return result
                
            except Exception as e:
                last_error = e
                error_category = self.classify_error(e)
                
                # 记录失败
                self.stats["failed_calls"] += 1
                
                # 如果是不可重试的错误，直接抛出
                if error_category == ErrorCategory.NON_RETRYABLE:
                    self.logger.warning(f"不可重试错误: {api} - {str(e)}")
                    if self.config.circuit_breaker_enabled:
                        self.circuit_breaker.record_failure(api)
                    raise
                
                # 如果还有重试机会
                if attempt < self.config.max_retries:
                    self.stats["retried_calls"] += 1
                    
                    # 计算退避时间
                    if self.config.exponential_backoff:
                        delay = self.config.retry_delay * (2 ** attempt)
                    else:
                        delay = self.config.retry_delay
                    
                    self.logger.info(
                        f"重试 {api}: 第 {attempt + 1}/{self.config.max_retries} 次, "
                        f"等待 {delay}s - {str(e)}"
                    )
                    
                    time.sleep(delay)
                    continue
                
                # 所有重试都失败
                self.logger.error(f"所有重试失败: {api} - {str(e)}")
                if self.config.circuit_breaker_enabled:
                    self.circuit_breaker.record_failure(api)
                raise
        
        # 不应该到这里
        if last_error:
            raise last_error
    
    def should_retry(self, error: Exception) -> bool:
        """
        判断是否可重试
        
        Args:
            error: 异常对象
        
        Returns:
            True: 可重试
            False: 不可重试
        """
        return self.classify_error(error) == ErrorCategory.RETRYABLE
    
    def classify_error(self, error: Exception) -> ErrorCategory:
        """
        错误分类
        
        可重试错误：
        - TIMEOUT
        - CONNECTION
        - 5xx
        
        不可重试错误：
        - 4xx
        - ASSERTION
        - VALIDATION
        
        Args:
            error: 异常对象
        
        Returns:
            错误分类
        """
        error_str = str(error).lower()
        error_type = type(error).__name__.lower()
        
        # 可重试错误
        retryable_keywords = [
            'timeout', 'timed out',
            'connection', 'connect',
            'network',
            '500', '502', '503', '504',
            'internal server error',
            'bad gateway',
            'service unavailable',
            'gateway timeout'
        ]
        
        for keyword in retryable_keywords:
            if keyword in error_str or keyword in error_type:
                return ErrorCategory.RETRYABLE
        
        # 不可重试错误
        non_retryable_keywords = [
            'assertion', 'assert',
            'validation', 'invalid',
            '400', '401', '403', '404',
            'bad request',
            'unauthorized',
            'forbidden',
            'not found'
        ]
        
        for keyword in non_retryable_keywords:
            if keyword in error_str or keyword in error_type:
                return ErrorCategory.NON_RETRYABLE
        
        # 默认：可重试
        return ErrorCategory.RETRYABLE
    
    def circuit_break(self, api: str) -> bool:
        """
        熔断控制（检查是否熔断）
        
        Args:
            api: API标识
        
        Returns:
            True: 熔断中
            False: 正常
        """
        if not self.config.circuit_breaker_enabled:
            return False
        
        return self.circuit_breaker.is_open(api)
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        获取统计信息
        
        Returns:
            统计信息字典
        """
        stats = {
            "resilience": self.stats.copy(),
            "circuit_breaker": self.circuit_breaker.get_statistics(),
            "rate_limiter": self.rate_limiter.get_statistics()
        }
        
        # 计算成功率
        total = self.stats["total_calls"]
        if total > 0:
            stats["resilience"]["success_rate"] = f"{(self.stats['successful_calls'] / total * 100):.2f}%"
            stats["resilience"]["retry_rate"] = f"{(self.stats['retried_calls'] / total * 100):.2f}%"
        
        return stats
    
    def reset_statistics(self):
        """重置统计信息"""
        self.stats = {
            "total_calls": 0,
            "retried_calls": 0,
            "circuit_breaker_rejections": 0,
            "rate_limiter_rejections": 0,
            "successful_calls": 0,
            "failed_calls": 0
        }
