# Backend API Server 重构方案

## 当前状态分析

`ai-test-platform/backend_api_server.py` 是一个大型文件（1000+行），包含：
- 测试数据工厂 API
- 数据集管理 API  
- 测试用例 API
- 测试执行 API
- 报告 API
- AI API
- 自动化脚本 API

## 重构策略

由于文件过大，采用**渐进式重构**策略：

### 阶段1：添加 modules 导入（不破坏现有功能）

在文件顶部添加 modules 和 core 导入：

```python
# 🔧 导入 modules SDK（核心能力层）
import sys
from pathlib import Path

# 添加 modules 到路径
modules_path = Path(__file__).parent.parent / 'modules'
core_path = Path(__file__).parent.parent / 'core'
sys.path.insert(0, str(modules_path))
sys.path.insert(0, str(core_path))

# 导入 modules
from modules.swagger import SwaggerTestCaseGenerator
from modules.executor import ExecutionEngine
from modules.healing import HealingEngine
from modules.report import ReportGenerator
from modules.data import TestDataManager

# 导入 core
from core import (
    TestCase,
    ExecutionResult,
    TestCaseStatus,
    TestCasePriority,
    DataType,
    ExpectedBehavior,
    create_test_case,
    create_execution_result
)
```

### 阶段2：创建辅助函数（转换层）

创建数据转换函数，在 core 模型和 API 响应之间转换：

```python
def testcase_to_dict(tc: TestCase) -> Dict[str, Any]:
    """将 TestCase 对象转换为 API 响应格式"""
    return {
        "id": tc.id,
        "title": tc.title,
        "module": tc.module,
        "priority": tc.priority.value,  # 枚举转字符串
        "status": tc.status.value,
        "steps": tc.steps,
        "expected": tc.expected,
        "data_type": tc.data_type.value,  # 🆕 新字段
        "expected_behavior": tc.expected_behavior.value,  # 🆕 新字段
        "execution_config": tc.execution_config,
        "assertions": tc.assertions,
        "tags": tc.tags,
        "created_at": tc.created_at.isoformat() if tc.created_at else None,
        "test_point_id": tc.test_point_id
    }

def execution_result_to_dict(result: ExecutionResult) -> Dict[str, Any]:
    """将 ExecutionResult 对象转换为 API 响应格式"""
    return {
        "test_case_id": result.test_case_id,
        "status": result.status.value,
        "duration": result.duration,
        "start_time": result.start_time.isoformat(),
        "end_time": result.end_time.isoformat(),
        "error": result.error,
        "response": result.response,
        "assertions_passed": result.assertions_passed,
        "assertions_failed": result.assertions_failed,
        "assertion_details": result.assertion_details,
        "healing_applied": result.healing_applied,  # 🆕 修复信息
        "healing_level": result.healing_level.value if result.healing_level else None,
        "healing_details": result.healing_details
    }
```

### 阶段3：逐步替换 API 端点

#### 3.1 Swagger 解析 API

```python
@app.post("/api/swagger/parse")
async def parse_swagger(data: Dict[str, str]):
    """解析Swagger URL（使用 modules SDK）"""
    try:
        url = data.get('url')
        if not url:
            return {"success": False, "message": "缺少URL参数"}
        
        # 🔧 使用 modules SDK
        generator = SwaggerTestCaseGenerator(url)
        test_cases = generator.generate_all_testcases()
        
        # 转换为 API 响应格式
        apis = generator.export_to_json(test_cases)
        
        return {
            "success": True,
            "message": f"成功解析 {len(apis)} 个API",
            "count": len(apis),
            "apis": apis
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"解析失败: {str(e)}"
        }
```

#### 3.2 测试用例生成 API

```python
@app.post("/api/testcases/generate-from-swagger")
async def generate_testcases_from_swagger(file: UploadFile = File(...)):
    """从 Swagger 生成测试用例（使用 modules SDK）"""
    try:
        # 保存上传的文件
        temp_file = f"/tmp/{file.filename}"
        with open(temp_file, "wb") as f:
            f.write(await file.read())
        
        # 🔧 使用 modules SDK
        generator = SwaggerTestCaseGenerator(temp_file)
        test_cases = generator.generate_all_testcases()
        
        # 转换为 API 响应格式
        result = []
        for tc in test_cases:
            result.append(testcase_to_dict(tc))
        
        # 保存到数据库
        test_cases_db.extend(result)
        data_manager.set_data("test_cases", test_cases_db, save=True)
        
        return {
            "success": True,
            "count": len(result),
            "testCases": result,
            "message": f"成功生成 {len(result)} 个测试用例"
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"生成失败: {str(e)}"
        }
```

#### 3.3 测试执行 API

```python
@app.post("/api/testcases/execute")
async def execute_testcases(request: Dict[str, Any]):
    """执行测试用例（使用 modules SDK）"""
    try:
        testcase_ids = request.get("testcase_ids", [])
        
        # 查找测试用例
        test_cases_to_run = [
            tc for tc in test_cases_db 
            if tc["id"] in testcase_ids
        ]
        
        if not test_cases_to_run:
            return {
                "success": False,
                "message": "未找到要执行的测试用例"
            }
        
        # 🔧 转换为 core TestCase 对象
        core_test_cases = []
        for tc in test_cases_to_run:
            core_tc = create_test_case(
                id=str(tc["id"]),
                title=tc["title"],
                module=tc["module"],
                priority=tc["priority"],
                status=tc.get("status", "pending"),
                steps=tc.get("steps", []),
                expected=tc.get("expected", ""),
                data_type=tc.get("data_type", "valid"),
                expected_behavior=tc.get("expected_behavior", "success"),
                execution_config=tc.get("execution_config", {}),
                assertions=tc.get("assertions", [])
            )
            core_test_cases.append(core_tc)
        
        # 🔧 使用 modules SDK 执行
        config = {
            "base_url": request.get("base_url", "http://localhost:8080"),
            "timeout": request.get("timeout", 30),
            "retry_on_failure": request.get("retry_on_failure", False),
            "max_retries": request.get("max_retries", 0)
        }
        
        engine = ExecutionEngine(config)
        results = engine.execute(core_test_cases, parallel=True)
        
        # 🔧 应用 Self-Healing
        healing_engine = HealingEngine()
        healed_results = healing_engine.heal(results)
        
        # 🔧 生成报告
        report_generator = ReportGenerator()
        report = report_generator.generate(healed_results)
        
        # 转换为 API 响应格式
        results_dict = [execution_result_to_dict(r) for r in healed_results]
        
        return {
            "success": True,
            "results": results_dict,
            "report": report,
            "message": f"执行完成: {report['summary']['passed']}/{report['summary']['total']} 通过"
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "message": f"执行失败: {str(e)}"
        }
```

### 阶段4：删除重复模块

删除 ai-test-platform 中的重复实现：
- `ai-test-platform/parser/` ❌
- `ai-test-platform/executor/` ❌
- `ai-test-platform/report/` ❌
- `ai-test-platform/test_data/` ❌
- `ai-test-platform/test_design/` ❌
- `ai-test-platform/automation/` ❌
- `ai-test-platform/case_generator/` ❌
- `ai-test-platform/assertion/` ❌
- `ai-test-platform/analysis/` ❌
- `ai-test-platform/self_healing/` ❌

## 实施步骤

1. ✅ 创建 core 层（已完成）
2. ✅ 更新 modules 使用 core（已完成）
3. 🔄 在 backend_api_server.py 顶部添加 modules 导入
4. 🔄 创建数据转换辅助函数
5. 🔄 逐个替换 API 端点（从最简单的开始）
6. 🔄 测试每个替换的端点
7. 🔄 删除重复模块
8. 🔄 更新前端组件

## 注意事项

1. **保持向后兼容** - API 响应格式不变
2. **渐进式替换** - 一次替换一个端点，测试通过后再继续
3. **错误处理** - 确保异常被正确捕获和转换
4. **数据转换** - 枚举值必须转 `.value`
5. **持久化** - 继续使用 data_manager 保存数据

## 优先级

高优先级（核心功能）：
1. Swagger 解析和测试用例生成
2. 测试用例执行
3. Self-Healing
4. 报告生成

中优先级：
5. 测试数据管理
6. 数据集管理

低优先级：
7. AI 生成（已有独立实现）
8. 自动化脚本生成
