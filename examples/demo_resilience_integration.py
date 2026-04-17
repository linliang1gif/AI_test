#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ResilienceEngine 集成示例

演示如何将 ResilienceEngine 集成到 ExecutionEngine
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from modules.resilience import ResilienceEngine, ResilienceConfig
from core import create_test_case


def simulate_api_call(test_case):
    """模拟 API 调用"""
    import random
    
    # 模拟随机失败
    if random.random() < 0.3:  # 30% 失败率
        raise Exception("Connection timeout")
    
    return {
        "status": "passed",
        "response": {"code": 200, "data": "success"}
    }


def execute_with_resilience_example():
    """示例：使用 ResilienceEngine 包装执行"""
    print("=" * 80)
    print("🔧 ResilienceEngine 集成示例")
    print("=" * 80)
    
    # 1. 创建 ResilienceEngine
    print("\n[1] 创建 ResilienceEngine...")
    config = ResilienceConfig(
        max_retries=3,
        retry_delay=0.5,
        exponential_backoff=True,
        circuit_breaker_enabled=True,
        failure_threshold=5,
        rate_limiter_enabled=True,
        api_qps=10
    )
    resilience = ResilienceEngine(config)
    print("  ✅ ResilienceEngine 已创建")
    
    # 2. 创建测试用例
    print("\n[2] 创建测试用例...")
    test_case = create_test_case(
        id="tc_payment_001",
        title="POST /payment/create - 正常场景",
        module="payment",
        priority="high"
    )
    print(f"  ✅ 测试用例: {test_case.id}")
    
    # 3. 使用 ResilienceEngine 包装执行
    print("\n[3] 执行测试（带稳定性保障）...")
    
    try:
        # 包装执行
        result = resilience.execute_with_resilience(
            func=lambda: simulate_api_call(test_case),
            api="/payment/create"
        )
        
        print(f"  ✅ 执行成功: {result}")
        
    except Exception as e:
        print(f"  ❌ 执行失败: {e}")
    
    # 4. 显示统计
    print("\n[4] 稳定性统计:")
    stats = resilience.get_statistics()
    
    print(f"  总调用: {stats['resilience']['total_calls']}")
    print(f"  成功: {stats['resilience']['successful_calls']}")
    print(f"  重试: {stats['resilience']['retried_calls']}")
    print(f"  熔断拒绝: {stats['resilience']['circuit_breaker_rejections']}")
    print(f"  限流拒绝: {stats['resilience']['rate_limiter_rejections']}")
    
    print("\n" + "=" * 80)
    print("✅ 集成示例完成")
    print("=" * 80)


def integration_pattern():
    """集成模式说明"""
    print("\n" + "=" * 80)
    print("📖 集成模式")
    print("=" * 80)
    
    print("""
在 ExecutionEngine 中集成 ResilienceEngine：

# 方式1: 在 ExecutionEngine 初始化时创建
class ExecutionEngine:
    def __init__(self, config):
        self.config = config
        
        # 创建 ResilienceEngine
        resilience_config = ResilienceConfig(
            max_retries=config.get('max_retries', 3),
            circuit_breaker_enabled=True,
            rate_limiter_enabled=True
        )
        self.resilience = ResilienceEngine(resilience_config)
    
    def _run_single(self, test_case):
        # 使用 ResilienceEngine 包装执行
        result = self.resilience.execute_with_resilience(
            func=lambda: self._execute_test(test_case),
            api=test_case.api_path
        )
        return result

# 方式2: 在 API Runner 中使用
class ApiRunner:
    def __init__(self, config):
        self.resilience = ResilienceEngine()
    
    def run(self, test_case):
        # 包装 HTTP 请求
        response = self.resilience.execute_with_resilience(
            func=lambda: requests.request(
                method=test_case.method,
                url=test_case.url,
                **test_case.params
            ),
            api=test_case.url
        )
        return response

优点：
1. 不改变现有执行逻辑
2. 仅包一层，透明集成
3. 自动处理重试、熔断、限流
4. 提高测试稳定性
""")


if __name__ == "__main__":
    # 示例1: 基本集成
    execute_with_resilience_example()
    
    # 示例2: 集成模式说明
    integration_pattern()
