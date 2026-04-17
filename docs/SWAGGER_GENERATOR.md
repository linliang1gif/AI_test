# Swagger测试用例生成器 - 企业级文档

## 🎯 核心特性

### 1. 自动生成高质量测试用例

从Swagger/OpenAPI规范自动生成测试用例，每个API生成5个用例：

- **1个正常流程用例** - 验证核心功能
- **2个边界用例** - 测试最小值/最大值
- **2个异常用例** - 测试错误处理

### 2. 严格遵守Swagger定义

- ✅ 所有URL来自Swagger定义
- ✅ 所有参数来自Swagger定义
- ✅ 不虚构任何接口
- ✅ 自动处理路径参数、查询参数、请求体

### 3. 完整的execution_config

生成的测试用例包含完整的执行配置：

```python
{
    "method": "POST",
    "url": "/api/users",
    "timeout": 30,
    "headers": {...},
    "params": {...},
    "body": {...}
}
```

### 4. 智能断言生成

自动生成合理的断言：

- 状态码断言
- JSON Path断言（字段存在性、类型）
- 响应时间断言

---

## 🚀 快速开始

### 1. 准备Swagger文件

支持Swagger 2.0和OpenAPI 3.0，支持JSON和YAML格式。

```json
{
  "swagger": "2.0",
  "info": {
    "title": "示例API",
    "version": "1.0.0"
  },
  "paths": {
    "/users": {
      "get": {
        "summary": "获取用户列表",
        "parameters": [...],
        "responses": {...}
      }
    }
  }
}
```

### 2. 生成测试用例

```python
from modules.swagger import SwaggerTestCaseGenerator

# 初始化生成器
generator = SwaggerTestCaseGenerator(
    swagger_file="swagger.json",
    business_context="用户管理系统"  # 可选
)

# 生成所有测试用例
test_cases = generator.generate_all_testcases()

print(f"生成了 {len(test_cases)} 个测试用例")
```

### 3. 查看生成的用例

```python
for tc in test_cases:
    print(f"ID: {tc.id}")
    print(f"标题: {tc.title}")
    print(f"方法: {tc.execution_config['method']}")
    print(f"URL: {tc.execution_config['url']}")
    print(f"断言: {tc.assertions}")
```

### 4. 导出为JSON

```python
# 导出为JSON格式
json_data = generator.export_to_json(test_cases)

# 保存到文件
import json
with open('testcases.json', 'w', encoding='utf-8') as f:
    json.dump(json_data, f, ensure_ascii=False, indent=2)
```

### 5. 与ExecutionEngine集成

```python
from modules.executor import ExecutionEngine

# 配置执行引擎
config = {
    "base_url": "https://api.example.com",
    "timeout": 30
}

engine = ExecutionEngine(config)

# 执行测试用例
results = engine.execute(test_cases)

# 查看结果
for result in results:
    print(f"{result.test_case_id}: {result.status}")
```

---

## 📖 详细功能

### 生成策略

#### 正常流程用例

- 使用示例值（example字段）
- 使用枚举值的第一个
- 使用合理的默认值

```python
# 示例：创建用户
{
    "method": "POST",
    "url": "/api/users",
    "body": {
        "name": "张三",
        "email": "zhangsan@example.com",
        "age": 25
    }
}
```

#### 边界用例 - 最小值

- 整数：使用minimum或0
- 字符串：使用minLength或空字符串
- 数组：空数组

```python
# 示例：最小值
{
    "method": "POST",
    "url": "/api/users",
    "body": {
        "name": "a",  # minLength=1
        "email": "a@b.c",
        "age": 0  # minimum=0
    }
}
```

#### 边界用例 - 最大值

- 整数：使用maximum或999999
- 字符串：使用maxLength或255个字符
- 数组：3个元素

```python
# 示例：最大值
{
    "method": "POST",
    "url": "/api/users",
    "body": {
        "name": "a" * 50,  # maxLength=50
        "email": "test@example.com",
        "age": 150  # maximum=150
    }
}
```

#### 异常用例 - 缺少必填参数

- 跳过required字段
- 期望返回400/422

```python
# 示例：缺少必填字段
{
    "method": "POST",
    "url": "/api/users",
    "body": {
        # 缺少name（required）
        "email": "test@example.com"
    }
}
```

#### 异常用例 - 无效类型

- 整数字段传字符串
- 字符串字段传数字
- 期望返回400/422

```python
# 示例：无效类型
{
    "method": "POST",
    "url": "/api/users",
    "body": {
        "name": 12345,  # 应该是string
        "email": "test@example.com",
        "age": "not_a_number"  # 应该是integer
    }
}
```

---

## 🎨 支持的Swagger特性

### 参数类型

| 类型 | 支持 | 说明 |
|------|------|------|
| path | ✅ | 路径参数（如/users/{id}） |
| query | ✅ | 查询参数（如?page=1） |
| header | ✅ | 请求头参数 |
| body | ✅ | 请求体（JSON） |
| formData | ⚠️ | 部分支持 |

### 数据类型

| 类型 | 支持 | 边界值生成 |
|------|------|-----------|
| integer | ✅ | minimum/maximum |
| number | ✅ | minimum/maximum |
| string | ✅ | minLength/maxLength |
| boolean | ✅ | true/false |
| array | ✅ | 空数组/多元素 |
| object | ✅ | 嵌套对象 |

### 约束条件

| 约束 | 支持 | 说明 |
|------|------|------|
| required | ✅ | 必填字段 |
| minimum | ✅ | 最小值 |
| maximum | ✅ | 最大值 |
| minLength | ✅ | 最小长度 |
| maxLength | ✅ | 最大长度 |
| pattern | ✅ | 正则模式（智能识别） |
| enum | ✅ | 枚举值 |
| example | ✅ | 示例值 |

---

## 📊 生成的测试用例结构

```python
TestCase(
    id="TC_001",                    # 测试用例ID
    test_point_id="TP_001",         # 测试点ID
    title="创建用户 - 正常流程",     # 标题
    precondition="无",              # 前置条件
    steps=["调用 POST /api/users"], # 步骤
    expected="返回201状态码，创建成功", # 预期结果
    priority=Priority.P0,           # 优先级
    test_type=TestType.API,         # 测试类型
    module="用户管理",              # 模块
    execution_config={              # 执行配置
        "method": "POST",
        "url": "/api/users",
        "timeout": 30,
        "body": {
            "name": "张三",
            "email": "zhangsan@example.com"
        }
    },
    assertions=[                    # 断言
        {
            "type": "status_code",
            "expected": 201
        },
        {
            "type": "json_path",
            "field": "id",
            "operator": "exists",
            "expected": True
        }
    ]
)
```

---

## 🔧 高级用法

### 1. 为特定API生成用例

```python
# 获取所有API
apis = generator.loader.get_all_apis()

# 选择特定API
user_api = next(api for api in apis if api['path'] == '/users')

# 只为这个API生成用例
test_cases = generator.generate_testcases_for_api(user_api)
```

### 2. 按模块生成

```python
# 获取特定标签的API
user_apis = generator.loader.get_apis_by_tag('用户管理')

# 为这些API生成用例
test_cases = []
for api in user_apis:
    test_cases.extend(generator.generate_testcases_for_api(api))
```

### 3. 自定义业务上下文

```python
generator = SwaggerTestCaseGenerator(
    swagger_file="swagger.json",
    business_context="""
    这是一个电商系统的用户管理模块。
    用户注册后需要邮箱验证。
    用户可以修改个人信息。
    """
)
```

### 4. 获取统计信息

```python
stats = generator.get_statistics(test_cases)

print(f"总用例数: {stats['total']}")
print(f"覆盖API数: {stats['apis_covered']}")
print(f"按优先级: {stats['by_priority']}")
print(f"按模块: {stats['by_module']}")
```

---

## 📈 最佳实践

### 1. Swagger文件质量

确保Swagger文件包含：

- ✅ 完整的参数定义（type, required）
- ✅ 合理的约束条件（minimum, maximum）
- ✅ 示例值（example）
- ✅ 响应schema定义
- ✅ 清晰的tags分类

### 2. 生成后的处理

```python
# 生成测试用例
test_cases = generator.generate_all_testcases()

# 按优先级排序
test_cases.sort(key=lambda tc: tc.priority.value)

# 按模块分组
from collections import defaultdict
by_module = defaultdict(list)
for tc in test_cases:
    by_module[tc.module].append(tc)

# 导出
for module, cases in by_module.items():
    filename = f"testcases_{module}.json"
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(generator.export_to_json(cases), f, ensure_ascii=False, indent=2)
```

### 3. 与CI/CD集成

```python
# 生成测试用例
test_cases = generator.generate_all_testcases()

# 执行测试
engine = ExecutionEngine(config)
results = engine.execute(test_cases)

# 生成报告
stats = engine.get_statistics(results)

# 判断是否通过
if stats['pass_rate'] < 0.95:
    sys.exit(1)  # 失败
```

---

## 🎯 实际案例

### 案例1: 用户管理API

```python
# Swagger定义
{
    "paths": {
        "/users": {
            "post": {
                "summary": "创建用户",
                "parameters": [{
                    "name": "body",
                    "in": "body",
                    "schema": {
                        "type": "object",
                        "required": ["name", "email"],
                        "properties": {
                            "name": {"type": "string", "minLength": 1, "maxLength": 50},
                            "email": {"type": "string", "pattern": "email"},
                            "age": {"type": "integer", "minimum": 0, "maximum": 150}
                        }
                    }
                }]
            }
        }
    }
}

# 生成的测试用例
TC_001: 创建用户 - 正常流程
  body: {"name": "张三", "email": "test@example.com", "age": 25}
  assertions: [status_code=201, id.exists=True]

TC_002: 创建用户 - 边界测试(最小值)
  body: {"name": "a", "email": "a@b.c", "age": 0}
  assertions: [status_code=201]

TC_003: 创建用户 - 边界测试(最大值)
  body: {"name": "a"*50, "email": "test@example.com", "age": 150}
  assertions: [status_code=201]

TC_004: 创建用户 - 异常测试(缺少必填参数)
  body: {"email": "test@example.com"}  # 缺少name
  assertions: [status_code in [400, 422]]

TC_005: 创建用户 - 异常测试(无效参数类型)
  body: {"name": 12345, "email": "test@example.com", "age": "not_a_number"}
  assertions: [status_code in [400, 422]]
```

---

## 🔍 常见问题

### Q1: 生成的用例数量太多？

可以按模块或优先级筛选：

```python
# 只生成P0用例
p0_cases = [tc for tc in test_cases if tc.priority == Priority.P0]

# 只生成特定模块
user_cases = [tc for tc in test_cases if tc.module == '用户管理']
```

### Q2: 如何自定义生成策略？

可以继承SwaggerTestCaseGenerator并重写方法：

```python
class CustomGenerator(SwaggerTestCaseGenerator):
    def _generate_string_value(self, schema, scenario):
        # 自定义字符串生成逻辑
        return "custom_value"
```

### Q3: 支持OpenAPI 3.0吗？

完全支持！自动检测版本。

### Q4: 如何处理认证？

在ExecutionEngine配置中添加认证信息：

```python
config = {
    "base_url": "https://api.example.com",
    "auth_config": {
        "type": "bearer",
        "token": "your_token"
    }
}
```

---

## 📚 相关文档

- [API Spec Loader文档](../modules/swagger/api_spec_loader.py)
- [ExecutionEngine文档](../modules/executor/README.md)
- [企业级ApiRunner文档](./ENTERPRISE_API_RUNNER.md)

---

## 🎉 快速体验

```bash
# 运行演示
python examples/demo_swagger_generator.py

# 运行验证
python verify_swagger_generator.py
```

---

**版本:** v1.0.0  
**状态:** 🟢 生产就绪  
**更新日期:** 2024-03-23
