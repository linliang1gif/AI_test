# Worker 使用指南

## 概述

Worker 是任务执行线程，用于支持并发执行。

## 核心特性

1. **并发执行**: 支持多线程并发执行任务
2. **独立线程**: 每个 Worker 独立运行
3. **执行解耦**: 通过 Executor 分发，不依赖 Pipeline
4. **失败处理**: 自动重试 + 失败队列
5. **优先级调度**: 支持优先级队列
6. **统计信息**: 完整的执行统计

## 快速开始

### 基本使用

```python
from orchestrator.worker import WorkerPool
from orchestrator.task_queue import TaskQueue
from orchestrator.task import TaskFactory

# 1. 创建队列
task_queue = TaskQueue()
result_list = []
failure_queue = TaskQueue()

# 2. 创建任务
cases = [{"id": f"TC_{i}", "title": f"测试{i}"} for i in range(1, 11)]
tasks = TaskFactory.create_batch_from_cases(cases, "api", priority=3)
task_queue.add_tasks(tasks)

# 3. 创建 WorkerPool
pool = WorkerPool(
    num_workers=3,
    task_queue=task_queue,
    result_list=result_list,
    failure_queue=failure_queue
)

# 4. 启动线程池
pool.start()

# 5. 等待任务完成
pool.wait_completion(timeout=10)

# 6. 停止线程池
pool.stop()

# 7. 查看结果
print(f"成功: {len(result_list)}")
print(f"失败: {failure_queue.size()}")
```

## Worker 类

### 初始化

```python
from orchestrator.worker import Worker
import threading

stop_event = threading.Event()

worker = Worker(
    worker_id="worker_1",
    task_queue=task_queue,
    result_list=result_list,
    failure_queue=failure_queue,
    stop_event=stop_event
)
```

### 启动 Worker

```python
# 启动线程
worker.start()

# 等待任务完成
# ...

# 停止线程
stop_event.set()
worker.join(timeout=2)
```

### 获取统计信息

```python
stats = worker.get_statistics()

print(f"Worker ID: {stats['worker_id']}")
print(f"处理任务: {stats['tasks_processed']}")
print(f"成功任务: {stats['tasks_succeeded']}")
print(f"失败任务: {stats['tasks_failed']}")
```

## WorkerPool 类

### 初始化

```python
from orchestrator.worker import WorkerPool

pool = WorkerPool(
    num_workers=5,          # Worker 数量
    task_queue=task_queue,  # 任务队列
    result_list=result_list,  # 结果列表
    failure_queue=failure_queue  # 失败队列
)
```

### 启动线程池

```python
# 启动所有 Worker
pool.start()
```

### 等待任务完成

```python
# 等待所有任务完成（无超时）
pool.wait_completion()

# 等待所有任务完成（带超时）
pool.wait_completion(timeout=10)
```

### 停止线程池

```python
# 停止所有 Worker
pool.stop()
```

### 获取统计信息

```python
stats = pool.get_statistics()

print(f"Worker 数量: {stats['num_workers']}")
print(f"处理任务: {stats['total_processed']}")
print(f"成功任务: {stats['total_succeeded']}")
print(f"失败任务: {stats['total_failed']}")

# 各 Worker 统计
for worker_stat in stats['workers']:
    print(f"{worker_stat['name']}: {worker_stat['tasks_processed']} 个任务")
```

## 便捷函数

### create_worker_pool

```python
from orchestrator.worker import create_worker_pool

pool = create_worker_pool(
    num_workers=5,
    task_queue=task_queue,
    result_list=result_list,
    failure_queue=failure_queue
)
```

## 完整示例

### 示例1: 并发执行 API 测试

```python
from orchestrator.worker import create_worker_pool
from orchestrator.task_queue import TaskQueue
from orchestrator.task import TaskFactory

# 创建队列
task_queue = TaskQueue()
result_list = []
failure_queue = TaskQueue()

# 创建任务
cases = [
    {"id": "TC_001", "title": "登录测试"},
    {"id": "TC_002", "title": "查询测试"},
    {"id": "TC_003", "title": "创建测试"},
    {"id": "TC_004", "title": "更新测试"},
    {"id": "TC_005", "title": "删除测试"}
]
tasks = TaskFactory.create_batch_from_cases(cases, "api", priority=3)
task_queue.add_tasks(tasks)

# 创建线程池（3个 Worker）
pool = create_worker_pool(
    num_workers=3,
    task_queue=task_queue,
    result_list=result_list,
    failure_queue=failure_queue
)

# 启动
pool.start()

# 等待完成
pool.wait_completion(timeout=30)

# 停止
pool.stop()

# 查看结果
print(f"成功: {len(result_list)}")
print(f"失败: {failure_queue.size()}")

# 统计信息
stats = pool.get_statistics()
print(f"处理任务: {stats['total_processed']}")
```

### 示例2: 优先级调度

```python
# 创建不同优先级的任务
high_priority_cases = [
    {"id": "URGENT_001", "title": "紧急测试1"},
    {"id": "URGENT_002", "title": "紧急测试2"}
]
normal_cases = [
    {"id": "NORMAL_001", "title": "普通测试1"},
    {"id": "NORMAL_002", "title": "普通测试2"}
]

# 高优先级任务
high_tasks = TaskFactory.create_batch_from_cases(
    high_priority_cases, "api", priority=5
)

# 普通优先级任务
normal_tasks = TaskFactory.create_batch_from_cases(
    normal_cases, "api", priority=3
)

# 添加到队列（先添加普通任务）
task_queue.add_tasks(normal_tasks)
task_queue.add_tasks(high_tasks)

# 执行（高优先级任务会先执行）
pool.start()
pool.wait_completion()
pool.stop()
```

### 示例3: 失败处理

```python
# 创建任务
cases = [{"id": f"TC_{i}", "title": f"测试{i}"} for i in range(1, 11)]
tasks = TaskFactory.create_batch_from_cases(cases, "api", priority=3)

# 设置最大重试次数
for task in tasks:
    task.max_retries = 2

task_queue.add_tasks(tasks)

# 执行
pool.start()
pool.wait_completion()
pool.stop()

# 查看失败任务
print(f"失败任务数: {failure_queue.size()}")

failed_tasks = failure_queue.get_all_tasks()
for task in failed_tasks:
    print(f"任务 {task.id} 失败: {task.error}")
    print(f"重试次数: {task.retry_count}")
```

### 示例4: 混合测试类型

```python
# 创建不同类型的任务
api_cases = [{"id": f"API_{i}", "title": f"API测试{i}"} for i in range(1, 6)]
ui_cases = [{"id": f"UI_{i}", "title": f"UI测试{i}"} for i in range(1, 4)]
integration_cases = [{"id": f"INT_{i}", "title": f"集成测试{i}"} for i in range(1, 3)]

# 创建任务
api_tasks = TaskFactory.create_batch_from_cases(api_cases, "api", priority=3)
ui_tasks = TaskFactory.create_batch_from_cases(ui_cases, "ui", priority=2)
integration_tasks = TaskFactory.create_batch_from_cases(
    integration_cases, "integration", priority=1
)

# 添加到队列
task_queue.add_tasks(api_tasks)
task_queue.add_tasks(ui_tasks)
task_queue.add_tasks(integration_tasks)

# 执行（按优先级：api > ui > integration）
pool.start()
pool.wait_completion()
pool.stop()
```

## 设计原则

### 1. 独立线程

每个 Worker 是独立的线程，不阻塞主线程：

```python
class Worker(threading.Thread):
    def run(self):
        while not self.stop_event.is_set():
            task = self.queue.get_task()
            self._execute_task(task)
```

### 2. 执行解耦

Worker 通过 Executor 分发，不直接依赖 Pipeline：

```python
# Worker 调用 Executor
result = self.executor.execute_task(task)

# Executor 分发到 Runner
if task.task_type == "api":
    return self.api_runner.run_cases([task.case])
```

### 3. 失败处理

自动重试 + 失败队列：

```python
if task.can_retry():
    # 重试
    task.retry()
    self.queue.add_task(task)
else:
    # 放入失败队列
    self.failure_queue.add_task(task)
```

### 4. 并发安全

- TaskQueue 线程安全
- result_list 使用 append（线程安全）
- failure_queue 线程安全

## 最佳实践

### 1. Worker 数量选择

```python
# CPU 密集型任务
num_workers = os.cpu_count()

# IO 密集型任务
num_workers = os.cpu_count() * 2

# 混合任务
num_workers = os.cpu_count() + 2
```

### 2. 超时设置

```python
# 设置合理的超时时间
pool.wait_completion(timeout=60)  # 60秒超时
```

### 3. 优雅停止

```python
try:
    pool.start()
    pool.wait_completion()
finally:
    pool.stop()  # 确保停止
```

### 4. 错误处理

```python
# 检查失败任务
if failure_queue.size() > 0:
    print(f"有 {failure_queue.size()} 个任务失败")
    
    # 获取失败任务
    failed_tasks = failure_queue.get_all_tasks()
    
    # 分析失败原因
    for task in failed_tasks:
        print(f"任务 {task.id}: {task.error}")
```

### 5. 监控执行

```python
import time

pool.start()

# 定期检查进度
while not task_queue.is_empty():
    stats = pool.get_statistics()
    print(f"进度: {stats['total_processed']}/{total_tasks}")
    time.sleep(1)

pool.stop()
```

## 性能优化

### 1. 调整 Worker 数量

```python
# 根据任务类型调整
if task_type == "api":
    num_workers = 10  # API 测试可以更多
elif task_type == "ui":
    num_workers = 3   # UI 测试较少
```

### 2. 批量添加任务

```python
# 一次性添加所有任务
task_queue.add_tasks(all_tasks)

# 而不是逐个添加
for task in all_tasks:
    task_queue.add_task(task)
```

### 3. 合理设置重试次数

```python
# 根据任务类型设置
for task in tasks:
    if task.task_type == "api":
        task.max_retries = 3  # API 可以多重试
    elif task.task_type == "ui":
        task.max_retries = 1  # UI 少重试
```

## 常见问题

### Q1: Worker 数量如何选择？

A: 根据任务类型：
- CPU 密集型：cpu_count()
- IO 密集型：cpu_count() * 2
- 混合型：cpu_count() + 2

### Q2: 如何处理失败任务？

A: 两种方式：
1. 自动重试（设置 max_retries）
2. 失败队列（手动处理）

### Q3: 如何优雅停止？

A: 使用 try-finally：
```python
try:
    pool.start()
    pool.wait_completion()
finally:
    pool.stop()
```

### Q4: 如何监控执行进度？

A: 使用统计信息：
```python
stats = pool.get_statistics()
progress = stats['total_processed'] / total_tasks
```

### Q5: 如何处理超时？

A: 设置超时时间：
```python
pool.wait_completion(timeout=60)
```

## API 参考

### Worker

```python
Worker(
    worker_id: str,
    task_queue: TaskQueue,
    result_list: List[Task],
    failure_queue: TaskQueue,
    stop_event: Optional[threading.Event] = None
)
```

**方法**:
- `start()`: 启动线程
- `stop()`: 停止线程
- `get_statistics()`: 获取统计信息

### WorkerPool

```python
WorkerPool(
    num_workers: int,
    task_queue: TaskQueue,
    result_list: List[Task],
    failure_queue: TaskQueue
)
```

**方法**:
- `start()`: 启动线程池
- `stop()`: 停止线程池
- `wait_completion(timeout=None)`: 等待任务完成
- `get_statistics()`: 获取统计信息

### create_worker_pool

```python
create_worker_pool(
    num_workers: int,
    task_queue: TaskQueue,
    result_list: List[Task],
    failure_queue: TaskQueue
) -> WorkerPool
```

## 总结

Worker 提供了强大的并发执行能力：

1. ✅ 独立线程运行
2. ✅ 执行逻辑可扩展
3. ✅ 自动失败处理
4. ✅ 优先级调度
5. ✅ 完整统计信息
6. ✅ 优雅启动/停止

使用 Worker 可以显著提升测试执行效率！
