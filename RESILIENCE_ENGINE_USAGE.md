# ResilienceEngine 使用指南

## 📖 概述

ResilienceEngine 是一个稳定性引擎，提供智能重试、熔断、限流等功能，提高测试执行的稳定性。

## 🎯 核心功能

1. **智能重试** - 指数退避，仅对可重试错误
2. **熔断机制** - 连续失败后自动熔断
3. **限流** - 全局和API级别限流
4. **错误分类** - 自动识别可重试错误

## 🚀 快速开始

### 1. 基本使用

```python
from modules.resilience import ResilienceEngine, ResilienceConfig

# 创建引擎
resilience = ResilienceEngine()

# 包装执行
result = resilience.execute_with_resilience(
    func=lambda: your_function(),
    api="/your/api"
)
```

### 2. 自定义配置

```python
# 创建配置
config = ResilienceConfig(
    max_retries=3,              # 最大重试3次
    retry_delay=1.0,            # 基础延迟1秒
    exponential_backoff=True,   # 启用指数退避
    circuit_breaker_enabled=True,
    rate_limiter_enabled=True
)

# 创建引擎
resilience = ResilienceEngine(config)
```

## 🔧 配置参数

### 重试配置

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `max_retries` | int | 3 | 最大重试次数 |
| `retry_delay` | float | 1.0 | 基础延迟（秒） |
| `exponential_backoff` | bool | True | 是否启用指数退避 |

### 熔断配置

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `circuit_breaker_enabled` | bool | True | 是否启用熔断 |
| `failure_threshold` | int | 5 | 失败阈值 |
| `recovery_timeout` | int | 30 | 恢复超时（秒） |
| `half_open_max_calls` | int | 3 | 半开最大调用数 |

### 限流配置

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `rate_limiter_enabled` | bool | True | 是否启用限流 |
| `global_qps` | int | 100 | 全局QPS限制 |
| `api_qps` | int | 10 | 单API QPS限制 |

## 📊 功能详解

### 1. 智能重试

**指数退避策略：**
```
第1次失败 → 等待 1s → 重试
第2次失败 → 等待 2s → 重试
第3次失败 → 等待 4s → 重试
```

**仅对可重试错误重试：**
- ✅ Timeout
- ✅ Connection Error
- ✅ 5xx Server Error
- ❌ Assertion Error
- ❌ 4xx Client Error

**示例：**
```python
config = ResilienceConfig(
    max_retries=3,
    retry_delay=1.0,
    exponential_backoff=True
)
resilience = ResilienceEngine(config)

# 自动重试（最多3次）
result = resilience.execute_with_resilience(
    func=lambda: api_call(),
    api="/payment/create"
)
```

### 2. 熔断机制

**状态转换：**
```
CLOSED (正常)
    ↓ 连续失败 >= 5次
OPEN (熔断)
    ↓ 等待 30s
HALF_OPEN (半开)
    ↓ 成功 → CLOSED
    ↓ 失败 → OPEN
```

**示例：**
```python
config = ResilienceConfig(
    circuit_breaker_enabled=True,
    failure_threshold=5,        # 连续5次失败后熔断
    recovery_timeout=30         # 30秒后尝试恢复
)
resilience = ResilienceEngine(config)

# 自动熔断保护
try:
    result = resilience.execute_with_resilience(
        func=lambda: api_call(),
        api="/payment/create"
    )
except Exception as e:
    if "Circuit breaker is OPEN" in str(e):
        print("API已熔断，请稍后重试")
```

**检查熔断状态：**
```python
# 检查是否熔断
is_open = resilience.circuit_break("/payment/create")
if is_open:
    print("API已熔断")

# 获取熔断器状态
state = resilience.circuit_breaker.get_state("/payment/create")
print(f"熔断器状态: {state.value}")
```

### 3. 限流

**两级限流：**
- 全局限流：所有API总QPS
- API限流：单个API的QPS

**示例：**
```python
config = ResilienceConfig(
    rate_limiter_enabled=True,
    global_qps=100,             # 全局每秒100个请求
    api_qps=10                  # 每个API每秒10个请求
)
resilience = ResilienceEngine(config)

# 自动限流
try:
    result = resilience.execute_with_resilience(
        func=lambda: api_call(),
        api="/order/query"
    )
except Exception as e:
    if "Rate limit exceeded" in str(e):
        print("请求过快，请稍后重试")
```

### 4. 错误分类

**可重试错误（RETRYABLE）：**
```python
errors = [
    "Connection timeout",
    "Network error",
    "500 Internal Server Error",
    "503 Service Unavailable"
]

for error in errors:
    category = resilience.classify_error(Exception(error))
    print(f"{error} → {category.value}")
    # 输出: retryable
```

**不可重试错误（NON_RETRYABLE）：**
```python
errors = [
    "Assertion failed",
    "400 Bad Request",
    "401 Unauthorized",
    "Validation error"
]

for error in errors:
    category = resilience.classify_error(Exception(error))
    print(f"{error} → {category.value}")
    # 输出: non_retryable
```

## 🔄 集成方式

### 方式1: 集成到 ExecutionEngine

```python
from modules.resilience import ResilienceEngine, ResilienceConfig

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
            api=test_case.api_path or test_case.id
        )
        return result
    
    def _execute_test(self, test_case):
        # 原有的执行逻辑
        runner = self._get_runner(test_case)
        return runner.run(test_case)
```

### 方式2: 集成到 ApiRunner

```python
from modules.resilience import ResilienceEngine
import requests

class ApiRunner:
    def __init__(self, config):
        self.config = config
        self.resilience = ResilienceEngine()
    
    def run(self, test_case):
        # 包装 HTTP 请求
        response = self.resilience.execute_with_resilience(
            func=lambda: self._make_request(test_case),
            api=test_case.url
        )
        return response
    
    def _make_request(self, test_case):
        return requests.request(
            method=test_case.method,
            url=test_case.url,
            headers=test_case.headers,
            json=test_case.body,
            timeout=test_case.timeout
        )
```

### 方式3: 集成到 ExecutionAgent

```python
from modules.resilience import ResilienceEngine, ResilienceConfig

class ExecutionAgent:
    def __init__(self, config):
        self.config = config
        
        # 创建 ResilienceEngine
        self.resilience = ResilienceEngine(ResilienceConfig(
            max_retries=config.get('max_retry_count', 3),
            circuit_breaker_enabled=True,
            rate_limiter_enabled=True
        ))
    
    def run(self, test_cases, environment="test"):
        results = []
        
        for tc in test_cases:
            # 使用 ResilienceEngine 包装执行
            try:
                result = self.resilience.execute_with_resilience(
                    func=lambda: self._execute_single(tc),
                    api=self._get_api_key(tc)
                )
                results.append(result)
            except Exception as e:
                # 处理失败
                results.append(self._create_error_result(tc, e))
        
        return results
```

## 📊 统计信息

### 获取统计

```python
stats = resilience.get_statistics()

print(f"总调用: {stats['resilience']['total_calls']}")
print(f"成功: {stats['resilience']['successful_calls']}")
print(f"失败: {stats['resilience']['failed_calls']}")
print(f"重试: {stats['resilience']['retried_calls']}")
print(f"成功率: {stats['resilience']['success_rate']}")
```

### 完整统计信息

```python
{
    "resilience": {
        "total_calls": 100,
        "successful_calls": 85,
        "failed_calls": 15,
        "retried_calls": 30,
        "circuit_breaker_rejections": 5,
        "rate_limiter_rejections": 10,
        "success_rate": "85.00%",
        "retry_rate": "30.00%"
    },
    "circuit_breaker": {
        "total_circuits": 5,
        "open": 1,
        "half_open": 0,
        "closed": 4,
        "circuits": {
            "/payment/create": {
                "state": "open",
                "failure_count": 5
            }
        }
    },
    "rate_limiter": {
        "global_qps": 50,
        "global_limit": 100,
        "api_qps": {
            "/order/query": 8
        },
        "api_limit": 10
    }
}
```

## 💡 最佳实践

### 1. 根据环境配置

**开发环境：**
```python
config = ResilienceConfig(
    max_retries=1,
    circuit_breaker_enabled=False,
    rate_limiter_enabled=False
)
```

**测试环境：**
```python
config = ResilienceConfig(
    max_retries=3,
    circuit_breaker_enabled=True,
    failure_threshold=5,
    rate_limiter_enabled=True,
    api_qps=10
)
```

**生产环境：**
```python
config = ResilienceConfig(
    max_retries=5,
    exponential_backoff=True,
    circuit_breaker_enabled=True,
    failure_threshold=10,
    recovery_timeout=60,
    rate_limiter_enabled=True,
    global_qps=1000,
    api_qps=50
)
```

### 2. 监控统计信息

```python
# 定期检查统计
stats = resilience.get_statistics()

# 告警条件
if stats['resilience']['retry_rate'] > 0.5:
    print("⚠️  重试率过高，检查外部系统")

if stats['circuit_breaker']['open'] > 0:
    print("⚠️  有API被熔断，检查服务状态")
```

### 3. 自定义错误分类

```python
# 如果需要自定义错误分类
class CustomResilienceEngine(ResilienceEngine):
    def classify_error(self, error):
        # 自定义逻辑
        if "custom_error" in str(error):
            return ErrorCategory.NON_RETRYABLE
        
        # 调用父类方法
        return super().classify_error(error)
```

## 🧪 测试

### 运行测试

```bash
# 完整测试套件
py test_resilience_engine.py

# 集成示例
py examples/demo_resilience_integration.py
```

### 测试覆盖

- ✅ 智能重试（指数退避）
- ✅ 熔断机制（状态转换）
- ✅ 限流（全局+API级别）
- ✅ 错误分类
- ✅ 集成示例

## ⚠️ 注意事项

1. **API标识** - 确保传入正确的API标识，用于熔断和限流
2. **重试幂等性** - 确保被重试的操作是幂等的
3. **超时设置** - 重试会增加总耗时，注意设置合理的超时
4. **熔断恢复** - 熔断后需要等待恢复时间
5. **限流影响** - 限流可能影响测试执行速度

## 🔗 相关文档

- `RESILIENCE_ENGINE_COMPLETE.md` - 实现完成报告
- `test_resilience_engine.py` - 测试文件
- `examples/demo_resilience_integration.py` - 集成示例

## ✅ 总结

ResilienceEngine 提供了完整的稳定性保障：

- **智能重试** - 自动处理临时故障
- **熔断机制** - 保护系统避免雪崩
- **限流** - 控制请求速率
- **错误分类** - 区分真实失败和临时故障

可以无缝集成到现有系统，提高测试执行的稳定性。
