# 真实执行引擎 - 使用指南

## 概述

`ExecutionEngine` 是一个统一的测试执行引擎，替换所有mock和简单requests调用，提供企业级的执行能力。

## 核心特性

### ✅ 三种执行类型
- **API Test** - HTTP/HTTPS API测试
- **Script Test** - Python脚本执行
- **Command Test** - 系统命令执行

### ✅ 统一执行入口
```python
engine = ExecutionEngine()
result = engine.execute(test_case)
```

### ✅ 完整的错误处理
- Timeout（超时）
- Connection Error（连接错误）
- HTTP Error（HTTP错误）
- JSON Decode Error（JSON解析错误）
- Script Error（脚本错误）
- Command Error（命令错误）

### ✅ 可观测性
每次执行返回完整的观测数据：
- `trace_id` - 追踪ID
- `start_time` - 开始时间
- `end_time` - 结束时间
- `duration` - 执行时长

## 快速开始

### 1. API执行

```python
from modules.executor.real_execution_engine import execute_api_test

# 简单GET请求
result = execute_api_test(
    url='https://api.example.com/users/1',
    method='GET'
)

print(f"Status: {result.status}")
print(f"Status Code: {result.status_code}")
print(f"Response: {result.response}")
print(f"Duration: {result.duration}s")
```

### 2. POST请求with Body

```python
result = execute_api_test(
    url='https://api.example.com/users',
    method='POST',
    headers={'Content-Type': 'application/json'},
    body={'name': 'John', 'email': 'john@example.com'},
    timeout=30
)

if result.success:
    print("✅ 创建成功")
    print(f"Response: {result.response}")
else:
    print(f"❌ 创建失败: {result.error_message}")
```

### 3. 脚本执行

```python
from modules.executor.real_execution_engine import execute_script_test

script = """
import requests
response = requests.get('https://api.example.com/health')
print(f"Health check: {response.status_code}")
"""

result = execute_script_test(script, timeout=60)

print(f"Script output: {result.response['stdout']}")
print(f"Return code: {result.status_code}")
```

### 4. 命令执行

```python
from modules.executor.real_execution_engine import execute_command_test

result = execute_command_test(
    command='pytest tests/',
    cwd='/path/to/project',
    timeout=300
)

print(f"Tests output: {result.response['stdout']}")
print(f"Success: {result.success}")
```

## 使用ExecutionEngine类

### 基础用法

```python
from modules.executor.real_execution_engine import ExecutionEngine

engine = ExecutionEngine(default_timeout=30)

# 定义测试用例
test_case = {
    'id': 'TC_001',
    'name': '获取用户列表',
    'execution_type': 'api',
    'config': {
        'url': 'https://api.example.com/users',
        'method': 'GET',
        'headers': {'Authorization': 'Bearer token123'}
    },
    'timeout': 10
}

# 执行测试
result = engine.execute(test_case)

# 处理结果
if result.success:
    print(f"✅ 测试通过")
    print(f"Trace ID: {result.trace_id}")
    print(f"Duration: {result.duration}s")
else:
    print(f"❌ 测试失败")
    print(f"Error: {result.error_message}")
```

### 使用上下文管理器

```python
with ExecutionEngine() as engine:
    result = engine.execute(test_case)
    print(result.to_json())
```

### 单例模式

```python
from modules.executor.real_execution_engine import get_execution_engine

# 获取全局单例
engine = get_execution_engine()
result = engine.execute(test_case)
```

## ExecutionResult 数据结构

```python
@dataclass
class ExecutionResult:
    # 基础信息
    trace_id: str              # 追踪ID
    execution_type: str        # 执行类型 (api/script/command)
    status: str                # 状态 (success/failed/error/timeout)
    success: bool              # 是否成功
    
    # 时间信息
    start_time: str            # 开始时间 (ISO格式)
    end_time: str              # 结束时间 (ISO格式)
    duration: float            # 执行时长（秒）
    
    # 响应信息
    status_code: int           # HTTP状态码或返回码
    response: Any              # 响应数据
    response_headers: dict     # 响应头（仅API）
    
    # 错误信息
    error_type: str            # 错误类型
    error_message: str         # 错误消息
    error_details: str         # 错误详情
    
    # 额外信息
    metadata: dict             # 元数据
```

## API执行示例

### 成功案例

```python
result = execute_api_test(
    url='https://jsonplaceholder.typicode.com/posts/1',
    method='GET'
)

# 输出:
{
  "trace_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "execution_type": "api",
  "status": "success",
  "success": true,
  "start_time": "2026-04-16T21:00:00.123456",
  "end_time": "2026-04-16T21:00:00.456789",
  "duration": 0.333,
  "status_code": 200,
  "response": {
    "userId": 1,
    "id": 1,
    "title": "sunt aut facere...",
    "body": "quia et suscipit..."
  },
  "response_headers": {
    "content-type": "application/json; charset=utf-8",
    "content-length": "292"
  },
  "metadata": {
    "method": "GET",
    "url": "https://jsonplaceholder.typicode.com/posts/1",
    "request_headers": {},
    "request_body": {}
  }
}
```

### 错误案例 - 超时

```python
result = execute_api_test(
    url='https://httpbin.org/delay/10',
    method='GET',
    timeout=2
)

# 输出:
{
  "trace_id": "b2c3d4e5-f6g7-8901-bcde-fg2345678901",
  "execution_type": "api",
  "status": "error",
  "success": false,
  "start_time": "2026-04-16T21:00:00.123456",
  "end_time": "2026-04-16T21:00:02.123456",
  "duration": 2.0,
  "error_type": "timeout",
  "error_message": "请求超时（2秒）",
  "metadata": {
    "method": "GET",
    "url": "https://httpbin.org/delay/10"
  }
}
```

### 错误案例 - 连接失败

```python
result = execute_api_test(
    url='http://invalid-domain.com',
    method='GET'
)

# 输出:
{
  "trace_id": "c3d4e5f6-g7h8-9012-cdef-gh3456789012",
  "execution_type": "api",
  "status": "error",
  "success": false,
  "start_time": "2026-04-16T21:00:00.123456",
  "end_time": "2026-04-16T21:00:00.234567",
  "duration": 0.111,
  "error_type": "connection_error",
  "error_message": "连接失败，请检查URL是否正确",
  "error_details": "HTTPConnectionPool(host='invalid-domain.com', port=80): Max retries exceeded...",
  "metadata": {
    "method": "GET",
    "url": "http://invalid-domain.com"
  }
}
```

### 错误案例 - HTTP 404

```python
result = execute_api_test(
    url='https://jsonplaceholder.typicode.com/posts/99999',
    method='GET'
)

# 输出:
{
  "trace_id": "d4e5f6g7-h8i9-0123-defg-hi4567890123",
  "execution_type": "api",
  "status": "failed",
  "success": false,
  "start_time": "2026-04-16T21:00:00.123456",
  "end_time": "2026-04-16T21:00:00.456789",
  "duration": 0.333,
  "status_code": 404,
  "response": {},
  "response_headers": {
    "content-type": "application/json; charset=utf-8"
  },
  "metadata": {
    "method": "GET",
    "url": "https://jsonplaceholder.typicode.com/posts/99999",
    "request_headers": {},
    "request_body": {}
  }
}
```

## 与现有系统集成

### 替换backend_api_server.py中的执行逻辑

```python
# 旧代码 ❌
@app.post("/api/testcases/{testcase_id}/execute")
async def execute_test_case(testcase_id: str):
    # 手动使用requests
    response = requests.get(url, timeout=30)
    # ...

# 新代码 ✅
from modules.executor.real_execution_engine import get_execution_engine

@app.post("/api/testcases/{testcase_id}/execute")
async def execute_test_case(testcase_id: str):
    engine = get_execution_engine()
    
    # 构建测试用例
    test_case = {
        'id': testcase_id,
        'name': testcase['title'],
        'execution_type': 'api',
        'config': testcase['execution_config']
    }
    
    # 执行测试
    result = engine.execute(test_case)
    
    # 返回结果
    return {
        "success": result.success,
        "result": {
            "status": result.status,
            "status_code": result.status_code,
            "response_time": int(result.duration * 1000),
            "message": result.error_message if not result.success else "测试通过"
        },
        "trace_id": result.trace_id
    }
```

### 替换ApiRunner

```python
# 旧代码 ❌
class ApiRunner:
    def run(self, test_case):
        # mock逻辑
        return {"status": "passed"}

# 新代码 ✅
from modules.executor.real_execution_engine import ExecutionEngine

class ApiRunner:
    def __init__(self):
        self.engine = ExecutionEngine()
    
    def run(self, test_case):
        result = self.engine.execute(test_case)
        return result.to_dict()
```

## 错误类型说明

| 错误类型 | 说明 | 示例 |
|---------|------|------|
| `timeout` | 请求超时 | 请求时间超过设定的timeout值 |
| `connection_error` | 连接失败 | 无法连接到目标服务器 |
| `http_error` | HTTP错误 | HTTP协议层面的错误 |
| `json_decode_error` | JSON解析错误 | 响应不是有效的JSON |
| `script_error` | 脚本错误 | Python脚本执行失败 |
| `command_error` | 命令错误 | 系统命令执行失败 |
| `validation_error` | 验证错误 | 参数验证失败 |
| `unknown_error` | 未知错误 | 其他未分类的错误 |

## 最佳实践

### 1. 使用单例模式

```python
from modules.executor.real_execution_engine import get_execution_engine

# 推荐：使用全局单例
engine = get_execution_engine()
```

### 2. 设置合理的超时时间

```python
# API测试：10-30秒
result = execute_api_test(url, timeout=30)

# 脚本执行：60-300秒
result = execute_script_test(script, timeout=120)

# 命令执行：根据实际情况
result = execute_command_test(command, timeout=600)
```

### 3. 检查执行结果

```python
result = engine.execute(test_case)

if result.success:
    # 处理成功情况
    print(f"✅ 测试通过: {result.response}")
else:
    # 处理失败情况
    print(f"❌ 测试失败: {result.error_message}")
    
    # 根据错误类型采取不同措施
    if result.error_type == 'timeout':
        print("建议：增加超时时间或检查网络")
    elif result.error_type == 'connection_error':
        print("建议：检查URL和网络连接")
```

### 4. 记录trace_id用于追踪

```python
result = engine.execute(test_case)

# 记录trace_id到日志
logger.info(f"Test executed: trace_id={result.trace_id}, success={result.success}")

# 保存到数据库
test_run = {
    "trace_id": result.trace_id,
    "test_case_id": test_case['id'],
    "status": result.status,
    "duration": result.duration
}
```

## 运行测试

```bash
# 运行完整测试
cd G:\AI项目\ai测试
py test_real_execution_engine.py
```

## 总结

`ExecutionEngine` 提供了：
- ✅ 统一的执行接口
- ✅ 完整的错误处理
- ✅ 丰富的观测数据
- ✅ 三种执行类型支持
- ✅ 企业级的可靠性

替换所有mock和简单requests调用，提供真实的测试执行能力！
