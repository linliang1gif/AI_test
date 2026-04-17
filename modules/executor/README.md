# 测试执行引擎（无pytest版本）

## 🎯 核心特性

- ✅ **直接执行** - 不生成pytest脚本，直接执行TestCase
- ✅ **并发支持** - 使用ThreadPoolExecutor实现并行执行
- ✅ **可扩展** - 支持API/UI/Integration多种测试类型
- ✅ **统一结果** - 返回标准化的ExecutionResult
- ✅ **重试机制** - 支持失败自动重试
- ✅ **自定义Runner** - 可注册自定义测试执行器

## 📦 模块结构

```
modules/executor/
├── __init__.py                 # 模块入口
├── execution_engine.py         # 核心执行引擎
├── api_runner.py              # API测试执行器
├── ui_runner.py               # UI测试执行器
├── integration_runner.py      # 集成测试执行器
└── README.md                  # 本文档
```

## 🚀 快速开始

### 1. 基本使用

```python
from modules.executor import ExecutionEngine
from core.models import TestCase, TestType, Priority

# 创建测试用例
test_case = TestCase(
    id="TC_001",
    test_point_id="TP_001",
    title="验证用户登录接口",
    precondition="用户已注册",
    steps=["调用POST /api/login接口"],
    expected="返回200状态码",
    priority=Priority.P0,
    test_type=TestType.API,
    module="用户管理",
    execution_config={
        "method": "POST",
        "url": "/api/login",
        "body": {"username": "admin", "password": "123456"}
    },
    assertions=[
        {"type": "status_code", "expected": 200}
    ]
)

# 初始化执行引擎
config = {
    "base_url": "https://api.example.com",
    "timeout": 30
}
engine = ExecutionEngine(config)

# 执行测试
results = engine.execute([test_case])

# 查看结果
for result in results:
    print(f"测试用例: {result.test_case_id}")
    print(f"状态: {result.status}")
    print(f"耗时: {result.duration}s")
```

### 2. 并行执行

```python
# 批量执行（并行）
test_cases = [test_case1, test_case2, test_case3]

results = engine.execute(
    test_cases, 
    max_workers=5,      # 最大并发数
    parallel=True       # 启用并行
)
```

### 3. 启用重试机制

```python
config = {
    "base_url": "https://api.example.com",
    "retry_on_failure": True,   # 失败时重试
    "max_retries": 3,           # 最大重试次数
    "retry_delay": 2            # 重试延迟（秒）
}

engine = ExecutionEngine(config)
results = engine.execute(test_cases)

# 查看重试次数
for result in results:
    print(f"重试次数: {result.retry_count}")
```

### 4. 自定义Runner

```python
# 创建自定义Runner
class CustomRunner:
    def __init__(self, config):
        self.config = config
    
    def run(self, test_case):
        # 实现自定义测试逻辑
        return {
            "status": "passed",
            "actual_response": {...}
        }

# 注册自定义Runner
engine = ExecutionEngine()
engine.register_runner("custom", CustomRunner(config))

# 使用自定义Runner
test_case.test_type = TestType.CUSTOM
results = engine.execute([test_case])
```

## 📊 ExecutionResult 结构

```python
@dataclass
class ExecutionResult:
    test_case_id: str              # 测试用例ID
    status: str                    # 执行状态: passed/failed/error/skipped
    duration: float                # 执行耗时（秒）
    error_message: str             # 错误信息（如果失败）
    stack_trace: str               # 堆栈跟踪（如果异常）
    actual_response: Dict          # 实际响应数据
    assertion_results: List[Dict]  # 断言结果列表
    retry_count: int               # 重试次数
    metadata: Dict                 # 元数据
```

## 🔧 API Runner 断言类型

### 1. 状态码断言

```python
{
    "type": "status_code",
    "expected": 200
}
```

### 2. JSON路径断言

```python
{
    "type": "json_path",
    "field": "data.user.name",      # 支持嵌套路径
    "operator": "equals",            # equals/contains/not_equals/greater_than/less_than
    "expected": "admin"
}
```

### 3. 响应时间断言

```python
{
    "type": "response_time",
    "expected": 2.0  # 单位：秒
}
```

### 4. 响应头断言

```python
{
    "type": "header",
    "field": "Content-Type",
    "expected": "application/json"
}
```

### 5. JSON Schema断言

```python
{
    "type": "schema",
    "schema": {
        "type": "object",
        "properties": {
            "id": {"type": "integer"},
            "name": {"type": "string"}
        },
        "required": ["id", "name"]
    }
}
```

### 6. 包含断言

```python
{
    "type": "contains",
    "expected": "success"  # 响应中包含指定内容
}
```

## 📈 统计信息

```python
# 获取统计信息
stats = engine.get_statistics(results)

print(stats)
# {
#     "total": 10,
#     "passed": 8,
#     "failed": 2,
#     "error": 0,
#     "skipped": 0,
#     "pass_rate": "80.00%",
#     "total_duration": 15.5,
#     "avg_duration": 1.55
# }
```

## 🎨 完整示例

```python
from modules.executor import ExecutionEngine
from core.models import TestCase, TestType, Priority

# 1. 定义测试用例
test_cases = [
    TestCase(
        id="TC_001",
        test_point_id="TP_001",
        title="创建订单",
        precondition="用户已登录",
        steps=["调用POST /api/orders接口"],
        expected="返回订单ID",
        priority=Priority.P0,
        test_type=TestType.API,
        module="订单管理",
        execution_config={
            "method": "POST",
            "url": "/api/orders",
            "body": {
                "product_id": 123,
                "quantity": 2
            },
            "headers": {
                "Authorization": "Bearer token123"
            }
        },
        assertions=[
            {"type": "status_code", "expected": 201},
            {"type": "json_path", "field": "order_id", "operator": "greater_than", "expected": 0},
            {"type": "response_time", "expected": 3.0}
        ]
    ),
    TestCase(
        id="TC_002",
        test_point_id="TP_002",
        title="查询订单",
        precondition="订单已创建",
        steps=["调用GET /api/orders/{id}接口"],
        expected="返回订单详情",
        priority=Priority.P1,
        test_type=TestType.API,
        module="订单管理",
        execution_config={
            "method": "GET",
            "url": "/api/orders/123"
        },
        assertions=[
            {"type": "status_code", "expected": 200},
            {"type": "json_path", "field": "status", "operator": "equals", "expected": "pending"}
        ]
    )
]

# 2. 配置执行引擎
config = {
    "base_url": "https://api.example.com",
    "timeout": 30,
    "retry_on_failure": True,
    "max_retries": 2,
    "retry_delay": 1,
    "default_headers": {
        "Content-Type": "application/json"
    }
}

engine = ExecutionEngine(config)

# 3. 执行测试（并行）
print("开始执行测试...")
results = engine.execute(test_cases, max_workers=5, parallel=True)

# 4. 处理结果
for result in results:
    print(f"\n测试用例: {result.test_case_id}")
    print(f"状态: {result.status}")
    print(f"耗时: {result.duration:.2f}s")
    
    if result.assertion_results:
        print("断言结果:")
        for assertion in result.assertion_results:
            status = "✅" if assertion['passed'] else "❌"
            print(f"  {status} {assertion['type']}: {assertion.get('expected')} vs {assertion.get('actual')}")
    
    if result.error_message:
        print(f"错误: {result.error_message}")

# 5. 统计信息
stats = engine.get_statistics(results)
print(f"\n统计信息:")
print(f"总计: {stats['total']}")
print(f"通过: {stats['passed']}")
print(f"失败: {stats['failed']}")
print(f"通过率: {stats['pass_rate']}")
print(f"总耗时: {stats['total_duration']}s")
```

## 🔄 与pytest的对比

| 特性 | ExecutionEngine | pytest |
|------|----------------|--------|
| 执行方式 | 直接执行TestCase对象 | 需要生成.py脚本文件 |
| 启动速度 | 快（无文件IO） | 慢（需要加载脚本） |
| 并发控制 | 精确控制（ThreadPoolExecutor） | 依赖pytest-xdist |
| 结果格式 | 统一的ExecutionResult | 需要解析pytest输出 |
| 可扩展性 | 高（自定义Runner） | 中（fixture机制） |
| 适用场景 | AI驱动的动态测试 | 传统脚本化测试 |

## ⚠️ 注意事项

1. **线程安全**: 确保自定义Runner是线程安全的
2. **资源管理**: UI Runner需要正确清理浏览器资源
3. **超时控制**: 设置合理的timeout避免长时间阻塞
4. **错误处理**: Runner应该捕获异常并返回错误信息
5. **并发数**: max_workers不宜过大，建议5-10

## 🧪 运行测试

```bash
# 运行单元测试
pytest tests/test_execution_engine.py -v

# 运行演示
python examples/demo_execution_engine.py
```

## 📚 扩展阅读

- [API Runner详细文档](./api_runner.py)
- [UI Runner详细文档](./ui_runner.py)
- [Integration Runner详细文档](./integration_runner.py)
- [核心数据模型](../../core/models.py)

## 🤝 贡献

欢迎提交Issue和Pull Request！

## 📄 许可证

MIT License
