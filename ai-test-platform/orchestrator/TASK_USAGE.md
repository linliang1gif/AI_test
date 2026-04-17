# Task 数据模型使用指南

## 概述

Task 是统一执行最小单元，所有测试执行都必须转换为 Task。

## 核心特性

1. **统一执行单元**: 所有执行单元必须转成 Task
2. **状态管理**: pending / running / success / failed
3. **优先级支持**: 1-10，数字越大优先级越高
4. **重试机制**: 支持失败重试
5. **时间追踪**: 记录创建、开始、结束时间

## 快速开始

### 1. 创建 Task

```python
from orchestrator.task import Task

# 方式1: 直接创建
case = {"id": "TC_001", "title": "登录测试"}
task = Task("task_001", case, "api", priority=5)

# 方式2: 从用例创建
task = Task.from_case(case, "api", priority=5)
```

### 2. 状态转换

```python
# 开始执行
task.start()
print(task.status)  # "running"

# 执行成功
result = {"status": "passed", "response_time": 0.5}
task.succeed(result)
print(task.status)  # "success"

# 执行失败
task.fail("Connection timeout")
print(task.status)  # "failed"
```

### 3. 重试机制

```python
# 检查是否可以重试
if task.can_retry():
    task.retry()
    print(task.retry_count)  # 1
```

### 4. 使用 TaskFactory

```python
from orchestrator.task import TaskFactory

# 从单个用例创建
case = {"id": "TC_001", "title": "测试"}
task = TaskFactory.create_from_case(case, "api", priority=3)

# 批量创建
cases = [
    {"id": "TC_001", "title": "测试1"},
    {"id": "TC_002", "title": "测试2"}
]
tasks = TaskFactory.create_batch_from_cases(cases, "ui", priority=2)

# 从策略创建
strategy = {
    "strategy": [
        {
            "module": {"name": "支付模块"},
            "test_types": ["api", "ui"]
        }
    ]
}
tasks = TaskFactory.create_from_strategy(strategy)
```

## 优先级规则

默认优先级映射：
- API 测试: priority=3
- UI 测试: priority=2
- 集成测试: priority=1

优先级越高，越先执行。

## 状态流转

```
pending → running → success
                 → failed → (retry) → pending
```

## 完整示例

```python
from orchestrator.task import Task, TaskFactory

# 创建任务
case = {
    "id": "TC_LOGIN_001",
    "title": "用户登录测试",
    "module": "用户模块"
}

task = Task.from_case(case, "api", priority=5)

# 执行任务
task.start()

try:
    # 模拟执行
    result = {"status": "passed", "response_time": 0.3}
    task.succeed(result)
    
except Exception as e:
    task.fail(str(e))
    
    # 重试
    if task.can_retry():
        task.retry()
        # 再次执行...

# 获取结果
print(f"任务状态: {task.status}")
print(f"执行时长: {task.duration}s")
print(f"重试次数: {task.retry_count}")

# 序列化
task_dict = task.to_dict()
```

## 与 Orchestrator 集成

Task 将在 Orchestrator V3 中使用：

```python
# Orchestrator V3 伪代码
class OrchestratorService:
    def run(self, strategy, cases=None):
        # 1. 转换为 Task
        if cases:
            tasks = self._convert_cases_to_tasks(cases)
        else:
            tasks = TaskFactory.create_from_strategy(strategy)
        
        # 2. 按优先级排序
        tasks = sorted(tasks)
        
        # 3. 执行 Task
        for task in tasks:
            self._execute_task(task)
        
        return results
```

## 最佳实践

1. **统一转换**: 所有执行单元都转换为 Task
2. **优先级设置**: 根据业务重要性设置优先级
3. **状态检查**: 执行前检查 Task 状态
4. **错误处理**: 失败后检查是否可以重试
5. **结果记录**: 使用 to_dict() 序列化结果

## 下一步

Task 模型已完成，接下来将实现：
- TaskQueue: 任务队列管理
- Orchestrator V3: 基于 Task 的执行调度

---

**版本**: V1
**状态**: ✅ 已完成
**测试**: 8/8 通过
