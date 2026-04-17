# 统一执行调度器使用指南

## 概述

UnifiedExecutionScheduler 是一个分布式系统级别的测试执行调度器，解决了并发混乱、执行无序、无优先级控制、无限流、失败扩散等问题。

## 核心能力

### 1. 优先级队列
- P0 (最高优先级) > P1 (中优先级) > P2 (低优先级) > P3 (最低优先级)
- 高优先级任务优先执行

### 2. 并发控制
- 可配置最大并发数 (默认: 5)
- 防止资源耗尽

### 3. 限流控制
- 令牌桶算法实现
- 可配置 QPS (默认: 10)
- 平滑流量控制

### 4. 失败隔离
- 单个任务失败不影响其他任务
- 支持自动重试 (最多3次)
- 详细错误信息记录

### 5. 任务状态管理
- pending: 等待执行
- running: 正在执行
- success: 执行成功
- failed: 执行失败
- cancelled: 已取消

## 调度流程图

```
┌─────────────┐
│  提交任务    │
│  submit()   │
└──────┬──────┘
       │
       ▼
┌─────────────────┐
│  优先级队列      │
│  P0 > P1 > P2   │
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│  并发控制        │
│  max_workers=5  │
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│  限流控制        │
│  rate_limit=10  │
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│  执行引擎        │
│ ExecutionEngine │
└──────┬──────────┘
       │
       ├─ 成功 ──► success
       │
       └─ 失败 ──► 重试(最多3次) ──► failed
```

## 快速开始

### 基本使用

```python
from modules.scheduler.unified_execution_scheduler import UnifiedExecutionScheduler, Priority

# 创建调度器
scheduler = UnifiedExecutionScheduler(
    max_workers=5,    # 最大并发数
    rate_limit=10     # 每秒最多10个请求
)

# 提交任务
task_id = scheduler.submit(
    test_case_id="tc_001",
    title="用户登录测试",
    method="POST",
    url="https://api.example.com/login",
    priority=Priority.P0
)

# 启动调度器
scheduler.run()

# 等待完成
await scheduler.wait_all()

# 查看统计
stats = scheduler.get_statistics()
print(f"成功: {stats.total_success}, 失败: {stats.total_failed}")

# 停止调度器
scheduler.stop()
```

### 设置优先级

```python
# 提交时设置
scheduler.submit(..., priority=Priority.P0)

# 动态调整
scheduler.set_priority("tc_001", Priority.P1)
```

### 查看任务状态

```python
status = scheduler.get_task_status("tc_001")
print(f"状态: {status.status.value}")
print(f"Trace ID: {status.trace_id}")
```

## API 参考

### UnifiedExecutionScheduler

#### 初始化参数
- `max_workers`: 最大并发数 (默认: 5)
- `rate_limit`: 每秒最多请求数 (默认: 10)

#### 方法

##### submit()
提交测试任务

参数:
- `test_case_id`: 测试用例ID
- `title`: 测试标题
- `method`: HTTP方法
- `url`: 请求URL
- `headers`: 请求头 (可选)
- `body`: 请求体 (可选)
- `priority`: 优先级 (默认: P2)

返回: 任务ID

##### set_priority()
设置任务优先级

参数:
- `test_case_id`: 测试用例ID
- `priority`: 新优先级

##### run()
启动调度器 (非阻塞)

##### stop()
停止调度器

##### wait_all()
等待所有任务完成 (异步)

##### get_task_status()
获取任务状态

参数:
- `test_case_id`: 测试用例ID

返回: TaskStatus 对象

##### get_statistics()
获取统计信息

返回: SchedulerStatistics 对象

## 最佳实践

### 1. 合理设置并发数
```python
# 根据服务器性能调整
scheduler = UnifiedExecutionScheduler(max_workers=10)
```

### 2. 使用优先级
```python
# 关键业务用 P0
scheduler.submit(..., priority=Priority.P0)

# 普通测试用 P1
scheduler.submit(..., priority=Priority.P1)

# 批量测试用 P2
scheduler.submit(..., priority=Priority.P2)
```

### 3. 监控统计信息
```python
stats = scheduler.get_statistics()
if stats.total_failed > 0:
    print(f"⚠️  有 {stats.total_failed} 个任务失败")
```

### 4. 优雅关闭
```python
try:
    await scheduler.wait_all()
finally:
    scheduler.stop()
```

## 与 ExecutionEngine 集成

调度器内部使用 ExecutionEngine 执行真实 HTTP 请求:

```python
# 调度器自动调用
engine = get_execution_engine()
result = await engine.execute_api(config)
```

所有执行结果包含:
- `trace_id`: 追踪ID
- `status`: 执行状态
- `response`: 响应数据
- `error`: 错误信息 (如果失败)

## 运行示例

```bash
# 运行测试
py test_unified_scheduler.py

# 运行演示
py demo_unified_scheduler.py
```

## 测试结果

所有测试通过 (100%):
- ✅ 基本调度功能
- ✅ 优先级调度
- ✅ 限流功能
- ✅ 失败隔离
