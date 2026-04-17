# 🚀 重构后架构快速上手指南

## 1. 验证安装

```bash
# 测试 core 和 modules 是否正常
py test_refactoring.py

# 查看完整演示
py demo_refactored_architecture.py
```

## 2. 基础使用

### 2.1 创建测试用例

```python
from core import create_test_case

# 创建一个测试用例
test_case = create_test_case(
    id="TC_001",
    title="用户登录 - 正常流程",
    module="用户管理",
    priority="high",              # critical/high/medium/low
    data_type="valid",            # valid/boundary/invalid
    expected_behavior="success",  # success/client_error/server_error
    steps=["1. 输入用户名", "2. 输入密码", "3. 点击登录"],
    expected="登录成功，跳转到首页"
)

print(f"创建测试用例: {test_case.title}")
print(f"数据类型: {test_case.data_type.value}")
print(f"预期行为: {test_case.expected_behavior.value}")
```

### 2.2 从 Swagger 生成测试用例

```python
from modules.swagger import SwaggerTestCaseGenerator

# 从 Swagger 文件生成
generator = SwaggerTestCaseGenerator("swagger.json")
test_cases = generator.generate_all_testcases()

# 获取统计信息
stats = generator.get_statistics(test_cases)
print(f"生成了 {stats['total']} 个测试用例")
print(f"按数据类型: {stats['by_data_type']}")
print(f"按预期行为: {stats['by_expected_behavior']}")

# 导出为 JSON
json_data = generator.export_to_json(test_cases)
```

### 2.3 生成测试数据

```python
from modules.data import TestDataManager

data_manager = TestDataManager()

# 定义数据 schema
schema = {
    "username": {"type": "string", "minLength": 3, "maxLength": 20},
    "password": {"type": "string", "minLength": 6, "maxLength": 20},
    "age": {"type": "integer", "minimum": 18, "maximum": 100}
}

# 生成不同类型的数据
valid_data = data_manager.generate_data(schema, "valid")
boundary_data = data_manager.generate_data(schema, "boundary")
invalid_data = data_manager.generate_data(schema, "invalid")

print(f"正常数据: {valid_data}")
print(f"边界数据: {boundary_data}")
print(f"异常数据: {invalid_data}")
```

### 2.4 执行测试

```python
from modules.executor import ExecutionEngine

# 配置执行引擎
config = {
    "base_url": "http://localhost:8080",
    "timeout": 30,
    "retry_on_failure": True,
    "max_retries": 3
}

engine = ExecutionEngine(config)

# 执行测试用例
results = engine.execute(test_cases, parallel=True, max_workers=5)

# 查看结果
for result in results:
    print(f"{result.test_case_id}: {result.status.value}")
```

### 2.5 应用 Self-Healing

```python
from modules.healing import HealingEngine

# 创建修复引擎
healing_engine = HealingEngine({
    "enable_l1": True,  # 环境问题（重试）
    "enable_l2": True,  # 数据问题（重建数据）
    "enable_l3": True,  # 不稳定（容错）
    "enable_l4": True   # 断言失败（人工审查）
})

# 应用修复
healed_results = healing_engine.heal(results)

# 查看修复信息
for result in healed_results:
    if result.healing_applied:
        print(f"{result.test_case_id}:")
        print(f"  修复级别: {result.healing_level.value}")
        print(f"  修复详情: {result.healing_details}")

# 获取修复报告
healing_report = healing_engine.get_healing_report()
print(f"修复率: {healing_report['healing_rate']}")
```

### 2.6 生成测试报告

```python
from modules.report import ReportGenerator

# 创建报告生成器
report_generator = ReportGenerator({
    "slow_threshold": 2.0,
    "include_response": False
})

# 生成报告
report = report_generator.generate(healed_results)

print(f"总用例数: {report['summary']['total']}")
print(f"通过: {report['summary']['passed']}")
print(f"失败: {report['summary']['failed']}")
print(f"通过率: {report['summary']['pass_rate']}")

# 生成文本报告
text_report = report_generator.generate_text_report(healed_results)
print(text_report)

# 生成 HTML 报告
html_report = report_generator.generate_html_report(healed_results)
with open("report.html", "w", encoding="utf-8") as f:
    f.write(html_report)
```

## 3. API 集成（Backend）

### 3.1 在 backend_api_server.py 中使用

```python
# 在文件顶部添加导入
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.swagger import SwaggerTestCaseGenerator
from modules.executor import ExecutionEngine
from modules.healing import HealingEngine
from modules.report import ReportGenerator
from utils.model_converter import testcase_to_dict, execution_result_to_dict

# 或者直接导入集成函数
from backend_api_modules_integration import (
    parse_swagger_with_modules,
    execute_testcases_with_modules,
    generate_test_data_with_modules
)

# 替换现有 API 端点
@app.post("/api/swagger/parse")
async def parse_swagger(data: Dict[str, str]):
    return await parse_swagger_with_modules(data)

@app.post("/api/testcases/execute")
async def execute_testcases(request: Dict[str, Any]):
    return await execute_testcases_with_modules(request, test_cases_db)
```

### 3.2 数据转换

```python
from utils.model_converter import (
    testcase_to_dict,
    dict_to_testcase,
    execution_result_to_dict,
    enrich_testcase_dict
)

# TestCase 对象 → API 响应
api_response = testcase_to_dict(test_case)

# API 请求 → TestCase 对象
test_case = dict_to_testcase(api_request_data)

# 为旧格式添加新字段（向后兼容）
enriched_tc = enrich_testcase_dict(old_format_tc)
```

## 4. 前端集成

### 4.1 使用 TypeScript 类型

```typescript
import { TestCase, ExecutionResult } from '../types/core';
import { getEnumLabel, getEnumColor } from '../types/enums';
import { DataTypeTag } from '../components/DataTypeTag';

// 使用类型
const testCase: TestCase = {
  id: "TC_001",
  title: "用户登录",
  priority: "high",
  data_type: "valid",
  expected_behavior: "success",
  // ...
};

// 显示枚举标签
<span>{getEnumLabel('TestCasePriority', testCase.priority)}</span>

// 显示数据类型标签
<DataTypeTag dataType={testCase.data_type} />

// 显示修复信息
{result.healing_applied && (
  <div>
    <span>修复级别: {result.healing_level}</span>
    <span>修复详情: {result.healing_details}</span>
  </div>
)}
```

## 5. 完整流程示例

```python
#!/usr/bin/env python3
"""完整的测试流程"""

from core import create_test_case
from modules.swagger import SwaggerTestCaseGenerator
from modules.executor import ExecutionEngine
from modules.healing import HealingEngine
from modules.report import ReportGenerator

# 1. 生成测试用例
generator = SwaggerTestCaseGenerator("swagger.json")
test_cases = generator.generate_all_testcases()
print(f"✅ 生成了 {len(test_cases)} 个测试用例")

# 2. 执行测试
config = {"base_url": "http://localhost:8080", "timeout": 30}
engine = ExecutionEngine(config)
results = engine.execute(test_cases, parallel=True)
print(f"✅ 执行完成")

# 3. 应用修复
healing_engine = HealingEngine()
healed_results = healing_engine.heal(results)
print(f"✅ 修复完成")

# 4. 生成报告
report_generator = ReportGenerator()
report = report_generator.generate(healed_results)
print(f"✅ 报告生成完成")

# 5. 保存报告
report_generator.save_report(healed_results, "report.html", format="html")
print(f"✅ 报告已保存")

# 6. 显示摘要
print(f"\n📊 测试摘要:")
print(f"  总用例数: {report['summary']['total']}")
print(f"  通过: {report['summary']['passed']}")
print(f"  失败: {report['summary']['failed']}")
print(f"  通过率: {report['summary']['pass_rate']}")
```

## 6. 常见问题

### Q1: 如何添加自定义字段？

在 `core/models.py` 中的 `TestCase` 类添加字段：

```python
@dataclass
class TestCase:
    # ... 现有字段
    custom_field: Optional[str] = None  # 新字段
```

### Q2: 如何添加新的枚举值？

在 `core/enums.py` 中添加：

```python
class TestCasePriority(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    TRIVIAL = "trivial"  # 新增
```

### Q3: 如何自定义 Self-Healing 策略？

```python
from modules.healing import HealingEngine

class CustomHealingEngine(HealingEngine):
    def _analyze_error(self, error_message: str):
        # 自定义错误分析逻辑
        if "custom_error" in error_message:
            return HealingLevel.L1_RETRY
        return super()._analyze_error(error_message)
```

### Q4: 如何扩展数据生成器？

```python
from modules.data import TestDataManager

class CustomDataManager(TestDataManager):
    def _generate_string_value(self, schema, scenario):
        # 自定义字符串生成逻辑
        if scenario == "custom":
            return "custom_value"
        return super()._generate_string_value(schema, scenario)
```

## 7. 最佳实践

### 7.1 使用工厂函数

✅ 推荐：
```python
from core import create_test_case
test_case = create_test_case(id="TC_001", title="测试", ...)
```

❌ 不推荐：
```python
from core import TestCase
test_case = TestCase(id="TC_001", title="测试", ...)
```

### 7.2 枚举值转换

✅ 推荐：
```python
# 枚举 → 字符串
priority_str = test_case.priority.value

# 字符串 → 枚举（通过工厂函数）
test_case = create_test_case(priority="high", ...)
```

❌ 不推荐：
```python
# 直接使用字符串
test_case.priority = "high"  # 类型错误
```

### 7.3 数据转换

✅ 推荐：
```python
from utils.model_converter import testcase_to_dict
api_response = testcase_to_dict(test_case)
```

❌ 不推荐：
```python
# 手动构建字典
api_response = {
    "id": test_case.id,
    "priority": test_case.priority.value,
    # ... 容易遗漏字段
}
```

## 8. 性能优化

### 8.1 并行执行

```python
# 使用并行执行提升速度
results = engine.execute(test_cases, parallel=True, max_workers=10)
```

### 8.2 数据缓存

```python
# TestDataManager 自动缓存数据
data = data_manager.generate_data(schema, "valid", case_id="TC_001")
# 再次调用会返回缓存的数据
data = data_manager.generate_data(schema, "valid", case_id="TC_001")
```

### 8.3 批量操作

```python
# 批量转换
from utils.model_converter import testcases_to_list
api_responses = testcases_to_list(test_cases)
```

## 9. 调试技巧

### 9.1 查看枚举值

```python
print(f"Priority: {test_case.priority}")        # TestCasePriority.HIGH
print(f"Priority value: {test_case.priority.value}")  # "high"
```

### 9.2 查看修复信息

```python
if result.healing_applied:
    print(f"修复级别: {result.healing_level.value}")
    print(f"修复详情: {result.healing_details}")
```

### 9.3 查看报告详情

```python
report = report_generator.generate(results)
print(json.dumps(report, indent=2, ensure_ascii=False))
```

## 10. 资源链接

- **验证脚本**: `py test_refactoring.py`
- **完整演示**: `py demo_refactored_architecture.py`
- **API 集成示例**: `ai-test-platform/backend_api_modules_integration.py`
- **数据转换器**: `ai-test-platform/utils/model_converter.py`
- **详细文档**: `重构完成.md`, `架构重构完成总结.md`

---

**开始使用：**
```bash
py test_refactoring.py          # 验证安装
py demo_refactored_architecture.py  # 查看演示
```

**获取帮助：**
- 查看文档目录中的详细文档
- 运行示例脚本了解用法
- 参考 `backend_api_modules_integration.py` 了解集成方式
