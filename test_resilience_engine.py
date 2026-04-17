#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 ResilienceEngine

演示：
1. 智能重试（指数退避）
2. 熔断机制
3. 限流
4. 错误分类
"""

import sys
import time
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from modules.resilience import ResilienceEngine, ResilienceConfig, ErrorCategory


# ==================== 模拟函数 ====================

class SimulatedAPI:
    """模拟 API（用于测试）"""
    
    def __init__(self):
        self.call_count = 0
        self.fail_until = 0  # 前N次调用失败
    
    def call(self):
        """模拟 API 调用"""
        self.call_count += 1
        
        if self.call_count <= self.fail_until:
            raise Exception("Connection timeout")
        
        return {"status": "success", "data": "ok"}
    
    def reset(self):
        """重置"""
        self.call_count = 0
        self.fail_until = 0


# ==================== 测试用例 ====================

def test_retry_with_exponential_backoff():
    """测试1: 智能重试（指数退避）"""
    print("=" * 80)
    print("🧪 测试1: 智能重试（指数退避）")
    print("=" * 80)
    
    # 创建引擎
    config = ResilienceConfig(
        max_retries=3,
        retry_delay=0.5,
        exponential_backoff=True,
        circuit_breaker_enabled=False,
        rate_limiter_enabled=False
    )
    engine = ResilienceEngine(config)
    
    # 模拟 API（前2次失败，第3次成功）
    api = SimulatedAPI()
    api.fail_until = 2
    
    print(f"\n场景: API 前2次失败（timeout），第3次成功")
    print(f"配置: max_retries=3, retry_delay=0.5s, exponential_backoff=True")
    
    try:
        start = time.time()
        result = engine.execute_with_resilience(
            func=api.call,
            api="/test/api"
        )
        duration = time.time() - start
        
        print(f"\n✅ 执行成功!")
        print(f"  结果: {result}")
        print(f"  总调用次数: {api.call_count}")
        print(f"  总耗时: {duration:.2f}s")
        print(f"  预期耗时: 0.5s + 1.0s = 1.5s (指数退避)")
        
    except Exception as e:
        print(f"\n❌ 执行失败: {e}")
    
    # 显示统计
    stats = engine.get_statistics()
    print(f"\n统计信息:")
    print(f"  总调用: {stats['resilience']['total_calls']}")
    print(f"  重试次数: {stats['resilience']['retried_calls']}")
    print(f"  成功: {stats['resilience']['successful_calls']}")
    print(f"  失败: {stats['resilience']['failed_calls']}")


def test_circuit_breaker():
    """测试2: 熔断机制"""
    print("\n" + "=" * 80)
    print("🧪 测试2: 熔断机制")
    print("=" * 80)
    
    # 创建引擎
    config = ResilienceConfig(
        max_retries=0,  # 不重试，直接失败
        circuit_breaker_enabled=True,
        failure_threshold=3,  # 连续3次失败后熔断
        recovery_timeout=2,   # 2秒后尝试恢复
        rate_limiter_enabled=False
    )
    engine = ResilienceEngine(config)
    
    # 模拟 API（一直失败）
    api = SimulatedAPI()
    api.fail_until = 100
    
    print(f"\n场景: API 一直失败，触发熔断")
    print(f"配置: failure_threshold=3, recovery_timeout=2s")
    
    # 第1-3次调用（触发熔断）
    print(f"\n第1-3次调用（触发熔断）:")
    for i in range(1, 4):
        try:
            engine.execute_with_resilience(api.call, api="/payment/create")
        except Exception as e:
            print(f"  第{i}次: ❌ {str(e)[:50]}")
    
    # 显示熔断器状态
    cb_stats = engine.circuit_breaker.get_statistics()
    print(f"\n熔断器状态:")
    print(f"  /payment/create: {cb_stats['circuits']['/payment/create']['state']}")
    
    # 第4次调用（熔断拒绝）
    print(f"\n第4次调用（熔断拒绝）:")
    try:
        engine.execute_with_resilience(api.call, api="/payment/create")
    except Exception as e:
        print(f"  ❌ {e}")
    
    # 等待恢复
    print(f"\n等待 {config.recovery_timeout}s 后尝试恢复...")
    time.sleep(config.recovery_timeout + 0.1)
    
    # 第5次调用（半开状态）
    print(f"\n第5次调用（半开状态）:")
    try:
        engine.execute_with_resilience(api.call, api="/payment/create")
    except Exception as e:
        print(f"  ❌ {str(e)[:50]}")
    
    # 显示最终状态
    cb_stats = engine.circuit_breaker.get_statistics()
    print(f"\n最终熔断器状态:")
    print(f"  /payment/create: {cb_stats['circuits']['/payment/create']['state']}")
    print(f"  失败次数: {cb_stats['circuits']['/payment/create']['failure_count']}")


def test_rate_limiter():
    """测试3: 限流"""
    print("\n" + "=" * 80)
    print("🧪 测试3: 限流")
    print("=" * 80)
    
    # 创建引擎
    config = ResilienceConfig(
        max_retries=0,
        circuit_breaker_enabled=False,
        rate_limiter_enabled=True,
        global_qps=10,
        api_qps=5
    )
    engine = ResilienceEngine(config)
    
    # 模拟 API（正常）
    api = SimulatedAPI()
    
    print(f"\n场景: 快速调用 API，触发限流")
    print(f"配置: global_qps=10, api_qps=5")
    
    # 快速调用10次
    print(f"\n快速调用 /order/query 10次:")
    success_count = 0
    rejected_count = 0
    
    for i in range(1, 11):
        try:
            engine.execute_with_resilience(api.call, api="/order/query")
            success_count += 1
            print(f"  第{i}次: ✅ 成功")
        except Exception as e:
            rejected_count += 1
            print(f"  第{i}次: ❌ {e}")
    
    print(f"\n结果:")
    print(f"  成功: {success_count}")
    print(f"  限流拒绝: {rejected_count}")
    
    # 显示限流统计
    rl_stats = engine.rate_limiter.get_statistics()
    print(f"\n限流统计:")
    print(f"  全局 QPS: {rl_stats['global_qps']}/{rl_stats['global_limit']}")
    print(f"  API QPS: {rl_stats['api_qps']}")


def test_error_classification():
    """测试4: 错误分类"""
    print("\n" + "=" * 80)
    print("🧪 测试4: 错误分类")
    print("=" * 80)
    
    engine = ResilienceEngine()
    
    print(f"\n测试错误分类:")
    
    # 可重试错误
    retryable_errors = [
        Exception("Connection timeout"),
        Exception("Network error"),
        Exception("500 Internal Server Error"),
        Exception("503 Service Unavailable"),
    ]
    
    print(f"\n可重试错误:")
    for error in retryable_errors:
        category = engine.classify_error(error)
        print(f"  {str(error):40s} → {category.value}")
    
    # 不可重试错误
    non_retryable_errors = [
        Exception("Assertion failed: expected 200, got 404"),
        Exception("400 Bad Request"),
        Exception("401 Unauthorized"),
        Exception("Validation error: invalid email"),
    ]
    
    print(f"\n不可重试错误:")
    for error in non_retryable_errors:
        category = engine.classify_error(error)
        print(f"  {str(error):40s} → {category.value}")


def test_integration_example():
    """测试5: 集成示例（完整流程）"""
    print("\n" + "=" * 80)
    print("🧪 测试5: 集成示例（完整流程）")
    print("=" * 80)
    
    # 创建引擎（启用所有功能）
    config = ResilienceConfig(
        max_retries=2,
        retry_delay=0.3,
        exponential_backoff=True,
        circuit_breaker_enabled=True,
        failure_threshold=3,
        rate_limiter_enabled=True,
        api_qps=5
    )
    engine = ResilienceEngine(config)
    
    print(f"\n场景: 模拟真实测试执行")
    print(f"配置: 重试+熔断+限流 全部启用")
    
    # 模拟多个 API
    apis = {
        "/user/login": SimulatedAPI(),
        "/order/create": SimulatedAPI(),
        "/payment/pay": SimulatedAPI()
    }
    
    # 设置失败场景
    apis["/user/login"].fail_until = 1  # 第1次失败，第2次成功
    apis["/order/create"].fail_until = 0  # 一直成功
    apis["/payment/pay"].fail_until = 5  # 前5次失败（触发熔断）
    
    # 执行测试
    results = []
    
    for api_path, api_obj in apis.items():
        print(f"\n测试 {api_path}:")
        try:
            result = engine.execute_with_resilience(
                func=api_obj.call,
                api=api_path
            )
            print(f"  ✅ 成功: {result}")
            results.append(("success", api_path))
        except Exception as e:
            print(f"  ❌ 失败: {str(e)[:60]}")
            results.append(("failed", api_path))
    
    # 显示统计
    print(f"\n" + "=" * 80)
    print(f"📊 统计信息")
    print(f"=" * 80)
    
    stats = engine.get_statistics()
    
    print(f"\n稳定性统计:")
    print(f"  总调用: {stats['resilience']['total_calls']}")
    print(f"  成功: {stats['resilience']['successful_calls']}")
    print(f"  失败: {stats['resilience']['failed_calls']}")
    print(f"  重试: {stats['resilience']['retried_calls']}")
    print(f"  熔断拒绝: {stats['resilience']['circuit_breaker_rejections']}")
    print(f"  限流拒绝: {stats['resilience']['rate_limiter_rejections']}")
    print(f"  成功率: {stats['resilience'].get('success_rate', 'N/A')}")
    
    print(f"\n熔断器统计:")
    cb_stats = stats['circuit_breaker']
    print(f"  总熔断器: {cb_stats['total_circuits']}")
    print(f"  打开: {cb_stats['open']}")
    print(f"  半开: {cb_stats['half_open']}")
    print(f"  关闭: {cb_stats['closed']}")
    
    print(f"\n限流统计:")
    rl_stats = stats['rate_limiter']
    print(f"  全局 QPS: {rl_stats['global_qps']}/{rl_stats['global_limit']}")


def main():
    """主函数"""
    print("=" * 80)
    print("🚀 ResilienceEngine 测试套件")
    print("=" * 80)
    
    # 测试1: 智能重试
    test_retry_with_exponential_backoff()
    
    # 测试2: 熔断机制
    test_circuit_breaker()
    
    # 测试3: 限流
    test_rate_limiter()
    
    # 测试4: 错误分类
    test_error_classification()
    
    # 测试5: 集成示例
    test_integration_example()
    
    print("\n" + "=" * 80)
    print("✅ 所有测试完成")
    print("=" * 80)


if __name__ == "__main__":
    main()
