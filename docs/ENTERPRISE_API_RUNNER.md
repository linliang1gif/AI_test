# 企业级 ApiRunner 文档

## 🎯 核心特性

### 1. 动态参数替换 ⚡

支持在URL、请求头、请求体中使用变量：

```python
# 支持的变量格式
${var_name}           # 从上下文获取
${env.VAR_NAME}       # 从环境变量获取
${response.field}     # 从上一个响应获取
${random.uuid}        # 生成随机UUID
${random.int}         # 生成随机整数
${timestamp}          # 当前时间戳
```

**示例：**
```python
execution_config = {
    "method": "GET",
    "url": "/users/${user_id}/posts/${post_id}",
    "headers": {
        "X-Request-ID": "${random.uuid}",
        "X-Timestamp": "${timestamp}"
    },
    "body": {
        "token": "${env.API_TOKEN}",
        "previous_id": "${response.id}"
    }
}
```

### 2. 智能Token注入 🔐

支持多种认证方式：

#### Bearer Token
```python
config = {
    "auth_config": {
        "type": "bearer",
        "token": "your_token_here"
    }
}
# 自动添加: Authorization: Bearer your_token_here
```

#### Basic Auth
```python
config = {
    "auth_config": {
        "type": "basic",
        "username": "admin",
        "password": "password123"
    }
}
# 自动添加: Authorization: Basic YWRtaW46cGFzc3dvcmQxMjM=
```

#### API Key
```python
config = {
    "auth_config": {
        "type": "api_key",
        "key_name": "X-API-Key",
        "key_value": "your_api_key"
    }
}
# 自动添加: X-API-Key: your_api_key
```

#### Custom Headers
```python
config = {
    "auth_config": {
        "type": "custom",
        "headers": {
            "X-Custom-Auth": "custom_value",
            "X-Tenant-ID": "tenant_123"
        }
    }
}
```

### 3. 增强的JSON Path断言 🎯

#### 支持的操作符

| 操作符 | 说明 | 示例 |
|--------|------|------|
| equals | 相等 | `{"operator": "equals", "expected": 1}` |
| contains | 包含 | `{"operator": "contains", "expected": "test"}` |
| not_equals | 不等于 | `{"operator": "not_equals", "expected": 0}` |
| greater_than | 大于 | `{"operator": "greater_than", "expected": 0}` |
| less_than | 小于 | `{"operator": "less_than", "expected": 100}` |
| greater_than_or_equal | 大于等于 | `{"operator": "greater_than_or_equal", "expected": 1}` |
| less_than_or_equal | 小于等于 | `{"operator": "less_than_or_equal", "expected": 10}` |
| regex | 正则匹配 | `{"operator": "regex", "expected": "^test.*"}` |
| exists | 存在 | `{"operator": "exists", "expected": True}` |
| not_exists | 不存在 | `{"operator": "not_exists", "expected": True}` |
| type | 类型检查 | `{"operator": "type", "expected": "int"}` |
| length | 长度 | `{"operator": "length", "expected": 5}` |
| length_greater_than | 长度大于 | `{"operator": "length_greater_than", "expected": 0}` |
| length_less_than | 长度小于 | `{"operator": "length_less_than", "expected": 100}` |

#### 支持的路径格式

```python
# 简单路径
"user.name"

# 嵌套路径
"data.user.profile.name"

# 数组索引
"users[0].name"

# 负数索引
"users[-1].name"

# 数组切片
"users[0:2]"

# 通配符（返回列表）
"users.*.name"
```

#### 示例

```python
assertions = [
    # 基本断言
    {
        "type": "json_path",
        "field": "id",
        "operator": "equals",
        "expected": 1
    },
    
    # 嵌套路径
    {
        "type": "json_path",
        "field": "data.user.name",
        "operator": "contains",
        "expected": "admin"
    },
    
    # 数组断言
    {
        "type": "json_path",
        "field": "users[0].age",
        "operator": "greater_than",
        "expected": 18
    },
    
    # 存在性断言
    {
        "type": "json_path",
        "field": "token",
        "operator": "exists",
        "expected": True
    },
    
    # 类型断言
    {
        "type": "json_path",
        "field": "count",
        "operator": "type",
        "expected": "int"
    },
    
    # 长度断言
    {
        "type": "json_path",
        "field": "items",
        "operator": "length_greater_than",
        "expected": 0
    },
    
    # 正则断言
    {
        "type": "json_path",
        "field": "email",
        "operator": "regex",
        "expected": "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$"
    }
]
```

### 4. 智能重试机制 🔄

#### 配置选项

```python
config = {
    "retry_config": {
        "max_retries": 3,              # 最大重试次数
        "backoff_factor": 2,           # 退避因子（指数退避）
        "retry_on_status": [500, 502, 503, 504],  # 重试的状态码
        "retry_on_timeout": True       # 超时时是否重试
    }
}
```

#### 重试策略

- **指数退避**: 第1次重试等待2秒，第2次等待4秒，第3次等待8秒
- **条件重试**: 只在特定状态码或超时时重试
- **重试记录**: 记录重试次数和原因

#### 重试信息

```python
result = runner.run(test_case)

retry_info = result['retry_info']
print(f"总尝试次数: {retry_info['total_attempts']}")
print(f"重试次数: {retry_info['retry_count']}")
print(f"重试原因: {retry_info['retry_reasons']}")
```

### 5. 上下文链式调用 🔗

#### 保存响应到上下文

```python
test_case = TestCase(
    # ... 其他配置 ...
    save_to_context={
        "user_id": "id",           # 保存响应中的id字段到user_id
        "token": "access_token",   # 保存响应中的access_token到token
        "email": "user.email"      # 保存嵌套字段
    }
)
```

#### 在后续请求中使用

```python
# 第一个请求保存了user_id
runner.run(test_case_1)

# 第二个请求使用user_id
test_case_2 = TestCase(
    execution_config={
        "method": "GET",
        "url": "/users/${user_id}/profile",  # 使用上下文变量
    }
)
```

#### 手动操作上下文

```python
# 设置上下文
runner.set_context("api_key", "your_api_key")

# 获取上下文
api_key = runner.get_context("api_key")

# 上下文会自动保存last_response
last_response = runner.get_context("last_response")
```

### 6. 请求/响应拦截器 🎣

#### 添加拦截器

```python
# 请求拦截器
def request_logger(config):
    print(f"发送请求: {config['method']} {config['url']}")
    return config

# 响应拦截器
def response_logger(response):
    print(f"收到响应: {response.status_code}")
    return response

runner.add_request_interceptor(request_logger)
runner.add_response_interceptor(response_logger)
```

#### 使用场景

- **日志记录**: 记录所有请求和响应
- **性能监控**: 统计响应时间
- **数据脱敏**: 隐藏敏感信息
- **请求修改**: 动态修改请求参数
- **响应处理**: 统一处理响应数据

### 7. 连接池复用 🏊

```python
config = {
    "pool_connections": 10,  # 连接池大小
    "pool_maxsize": 10       # 最大连接数
}
```

**优势：**
- 复用TCP连接
- 减少握手开销
- 提升并发性能

---

## 📖 完整示例

### 场景：用户注册 → 登录 → 获取信息

```python
from modules.executor.api_runner import ApiRunner

# 初始化Runner
config = {
    "base_url": "https://api.example.com",
    "timeout": 30,
    "auth_config": {
        "type": "bearer"
    },
    "retry_config": {
        "max_retries": 3,
        "backoff_factor": 2
    }
}

runner = ApiRunner(config)

# 步骤1: 注册用户
register_case = TestCase(
    id="TC_001",
    execution_config={
        "method": "POST",
        "url": "/api/register",
        "body": {
            "username": "test_${random.int}",
            "email": "test_${random.uuid}@example.com",
            "password": "password123"
        }
    },
    assertions=[
        {"type": "status_code", "expected": 201},
        {"type": "json_path", "field": "user_id", "operator": "exists", "expected": True}
    ],
    save_to_context={
        "user_id": "user_id",
        "username": "username"
    }
)

result1 = runner.run(register_case)
print(f"注册成功，用户ID: {runner.get_context('user_id')}")

# 步骤2: 登录
login_case = TestCase(
    id="TC_002",
    execution_config={
        "method": "POST",
        "url": "/api/login",
        "body": {
            "username": "${username}",  # 使用上一步的username
            "password": "password123"
        }
    },
    assertions=[
        {"type": "status_code", "expected": 200},
        {"type": "json_path", "field": "access_token", "operator": "exists", "expected": True}
    ],
    save_to_context={
        "access_token": "access_token"
    }
)

result2 = runner.run(login_case)
print(f"登录成功，Token: {runner.get_context('access_token')[:20]}...")

# 步骤3: 获取用户信息（自动注入Token）
get_user_case = TestCase(
    id="TC_003",
    execution_config={
        "method": "GET",
        "url": "/api/users/${user_id}"  # 使用第一步的user_id
    },
    assertions=[
        {"type": "status_code", "expected": 200},
        {"type": "json_path", "field": "username", "operator": "equals", "expected": runner.get_context('username')}
    ]
)

result3 = runner.run(get_user_case)
print(f"获取用户信息成功")
```

---

## 🆚 对比标准版

| 特性 | 标准版 | 企业级 |
|------|--------|--------|
| 动态参数 | ❌ | ✅ 支持8种变量类型 |
| Token注入 | ❌ | ✅ 支持4种认证方式 |
| JSON Path | ✅ 基础 | ✅ 增强（14种操作符） |
| 重试机制 | ❌ | ✅ 智能重试（指数退避） |
| 上下文管理 | ❌ | ✅ 完整的上下文系统 |
| 拦截器 | ❌ | ✅ 请求/响应拦截器 |
| 连接池 | ❌ | ✅ 连接池复用 |
| 错误信息 | ✅ 基础 | ✅ 详细（含重试信息） |

---

## 🚀 快速开始

```bash
# 运行演示
python examples/demo_enterprise_api_runner.py
```

---

## 📚 相关文档

- [ExecutionEngine文档](../modules/executor/README.md)
- [使用示例](../examples/demo_enterprise_api_runner.py)
- [快速参考](../EXECUTION_ENGINE_QUICK_REF.md)
