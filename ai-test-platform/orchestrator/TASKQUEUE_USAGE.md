# TaskQueue 使用指南

## 概述

TaskQueue 是任务队列，用于解耦任务生产与执行。

## 核心特性

1. **优先级调度**: 优先级高的任务先执行
2. **并发安全**: 线程安全，支持多生产者/多消费者
3. **职责单一**: 只负责队列管理，不执行任务
4. **状态追踪**: 支持任务状态查询和统计

## 快速开始

### 1. 创建队列

```python
from orchestrator.task_queue import TaskQueue

# 创建无限容量队列
queue = TaskQueue()

# 创建有限容量队列
queue = TaskQueue(max_size=100)
```

### 2. 添加任务

```python
from orchestrator.task import Task

# 单个添加
task = Task("task_1", {"id": "TC_1"}, "api", priority=5)
queue.add_task(task)

# 批量添加
tasks = [
    Task("task_1", {"id": "TC_1"}, "api", priority=5),
    Task("task_2", {"id": "TC_2"}, "ui", priority=3)
]
success_count = queue.add_tasks(tasks)
```

### 3. 获取任务

```python
# 阻塞获取（等待直到有任务）
task = queue.get_task(block=True)

# 非阻塞获取（立即返回）
task = queue.get_task(block=False)

# 超时获取（等待最多3秒）
task = queue.get_task(block=True, timeout=3)
```

### 4. 队列状态

```python
# 队列大小
size = queue.size()

# 是否为空
is_empty = queue.is_empty()

# 是否已满
is_full = queue.is_full()

# 查看队列头部（不出队）
task = queue.peek()
```

### 5. 任务查询

```python
# 获取所有任务
all_tasks = queue.get_all_tasks()

# 按状态查询
pending_tasks = queue.get_tasks_by_status("pending")
running_tasks = queue.get_tasks_by_status("running")
success_tasks = queue.get_tasks_by_status("success")
failed_tasks = queue.get_tasks_by_status("failed")

# 按ID查询
task = queue.get_task_by_id("task_1")
```

### 6. 统计信息

```python
stats = queue.get_statistics()

print(f"队列大小: {stats['queue_size']}")
print(f"总任务数: {stats['total_tasks']}")
print(f"待执行: {stats['pending']}")
print(f"执行中: {stats['running']}")
print(f"成功: {stats['success']}")
print(f"失败: {stats['failed']}")
```

## 优先级调度

TaskQueue 使用优先级队列，优先级高的任务先出队。

```python
# 添加不同优先级的任务
queue.add_task(Task("task_1", {...}, "api", priority=1))
queue.add_task(Task("task_2", {...}, "api", priority=5))
queue.add_task(Task("task_3", {...}, "api", priority=3))

# 出队顺序：task_2 (5) -> task_3 (3) -> task_1 (1)
task1 = queue.get_task()  # task_2
task2 = queue.get_task()  # task_3
task3 = queue.get_task()  # task_1
```

## 并发安全

TaskQueue 是线程安全的，支持多生产者/多消费者模式。

```python
import threading

queue = TaskQueue()

# 生产者线程
def producer():
    for i in range(10):
        task = Task(f"task_{i}", {...}, "api")
        queue.add_task(task)

# 消费者线程
def consumer():
    while True:
        task = queue.get_task(block=True, timeout=1)
        if task:
            # 执行任务
            execute_task(task)

# 启动多个生产者和消费者
producers = [threading.Thread(target=producer) for _ in range(3)]
consumers = [threading.Thread(target=consumer) for _ in range(5)]

for t in producers + consumers:
    t.start()
```

## 完整示例

```python
from orchestrator.task_queue import TaskQueue
from orchestrator.task import Task, TaskFactory

# 1. 创建队列
queue = TaskQueue()

# 2. 从策略创建任务
strategy = {
    "strategy": [
        {
            "module": {"name": "支付模块"},
            "test_types": ["api", "ui"]
        }
    ]
}

tasks = TaskFactory.create_from_strategy(strategy)

# 3. 添加到队列
queue.add_tasks(tasks)

# 4. 消费任务
while not queue.is_empty():
    task = queue.get_task(block=False)
    
    if task:
        # 执行任务
        task.start()
        
        try:
            # 模拟执行
            result = execute_test(task)
            task.succeed(result)
        except Exception as e:
            task.fail(str(e))
        
        # 标记完成
        queue.mark_task_completed(task.id)

# 5. 查看统计
stats = queue.get_statistics()
print(f"完成: {stats['total_completed']}/{stats['total_added']}")
```

## 与 Orchestrator 集成

TaskQueue 将在 Orchestrator V3 中使用：

```python
# Orchestrator V3 伪代码
class OrchestratorService:
    def __init__(self):
        self.task_queue = TaskQueue()
    
    def run(self, strategy, cases=None):
        # 1. 创建任务
        if cases:
            tasks = self._convert_cases_to_tasks(cases)
        else:
            tasks = TaskFactory.create_from_strategy(strategy)
        
        # 2. 添加到队列
        self.task_queue.add_tasks(tasks)
        
        # 3. 执行任务
        while not self.task_queue.is_empty():
            task = self.task_queue.get_task()
            self._execute_task(task)
        
        return results
```

## 设计原则

### 1. 职责单一
- TaskQueue 只负责队列管理
- 不负责任务执行
- 不负责任务创建

### 2. 解耦
- 生产者和消费者解耦
- 任务创建和执行解耦

### 3. 线程安全
- 使用 PriorityQueue（线程安全）
- 使用 Lock 保护索引

### 4. 可观测
- 提供丰富的查询接口
- 提供统计信息

## 最佳实践

1. **优先级设置**: 根据业务重要性设置优先级
2. **容量限制**: 生产环境建议设置 max_size
3. **超时处理**: 使用 timeout 避免永久阻塞
4. **状态追踪**: 定期查询统计信息
5. **清理队列**: 任务完成后及时清理

## API 参考

### TaskQueue

#### 构造函数
- `__init__(max_size=0)`: 创建队列

#### 任务管理
- `add_task(task)`: 添加任务
- `add_tasks(tasks)`: 批量添加
- `get_task(block=True, timeout=None)`: 获取任务

#### 状态查询
- `size()`: 队列大小
- `is_empty()`: 是否为空
- `is_full()`: 是否已满
- `peek()`: 查看队列头部

#### 任务查询
- `get_all_tasks()`: 获取所有任务
- `get_tasks_by_status(status)`: 按状态查询
- `get_task_by_id(task_id)`: 按ID查询

#### 统计信息
- `get_statistics()`: 获取统计信息
- `mark_task_completed(task_id)`: 标记完成

#### 其他
- `clear()`: 清空队列

---

**版本**: V1
**状态**: ✅ 已完成
**测试**: 9/9 通过
