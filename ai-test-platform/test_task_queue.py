"""
测试 TaskQueue 任务队列

验证点：
1. 基本功能（add/get）
2. 优先级调度
3. 并发安全
4. 队列状态查询
5. 任务查询
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

import time
import threading
from orchestrator.task_queue import TaskQueue, create_task_queue
from orchestrator.task import Task, TaskStatus


def test_queue_basic():
    """测试队列基本功能"""
    print("\n【测试1】队列基本功能")
    print("-" * 70)
    
    queue = TaskQueue()
    
    # 添加任务
    task1 = Task("task_1", {"id": "TC_1"}, "api", priority=3)
    task2 = Task("task_2", {"id": "TC_2"}, "ui", priority=2)
    
    assert queue.add_task(task1) is True
    assert queue.add_task(task2) is True
    
    print(f"✅ 添加任务: {queue.size()} 个")
    
    # 获取任务
    task = queue.get_task(block=False)
    assert task is not None
    assert task.id == "task_1"  # 优先级高的先出队
    
    print(f"✅ 获取任务: {task.id} (priority={task.priority})")
    
    # 队列大小
    assert queue.size() == 1
    print(f"✅ 队列大小: {queue.size()}")


def test_priority_scheduling():
    """测试优先级调度"""
    print("\n【测试2】优先级调度")
    print("-" * 70)
    
    queue = TaskQueue()
    
    # 添加不同优先级的任务
    tasks = [
        Task("task_1", {"id": "TC_1"}, "api", priority=1),
        Task("task_2", {"id": "TC_2"}, "api", priority=5),
        Task("task_3", {"id": "TC_3"}, "api", priority=3),
        Task("task_4", {"id": "TC_4"}, "api", priority=4),
    ]
    
    for task in tasks:
        queue.add_task(task)
    
    print(f"✅ 添加任务: {queue.size()} 个")
    
    # 按优先级出队
    priorities = []
    while not queue.is_empty():
        task = queue.get_task(block=False)
        if task:
            priorities.append(task.priority)
            print(f"   出队: {task.id} (priority={task.priority})")
    
    # 验证优先级顺序（从高到低）
    assert priorities == [5, 4, 3, 1]
    print(f"✅ 优先级顺序正确: {priorities}")


def test_batch_add():
    """测试批量添加"""
    print("\n【测试3】批量添加")
    print("-" * 70)
    
    queue = TaskQueue()
    
    tasks = [
        Task(f"task_{i}", {"id": f"TC_{i}"}, "api", priority=i)
        for i in range(1, 6)
    ]
    
    success_count = queue.add_tasks(tasks)
    
    assert success_count == 5
    assert queue.size() == 5
    
    print(f"✅ 批量添加: {success_count} 个任务")
    print(f"✅ 队列大小: {queue.size()}")


def test_queue_status():
    """测试队列状态查询"""
    print("\n【测试4】队列状态查询")
    print("-" * 70)
    
    queue = TaskQueue()
    
    # 空队列
    assert queue.is_empty() is True
    assert queue.size() == 0
    print(f"✅ 空队列检测")
    
    # 添加任务
    task = Task("task_1", {"id": "TC_1"}, "api")
    queue.add_task(task)
    
    assert queue.is_empty() is False
    assert queue.size() == 1
    print(f"✅ 非空队列检测")
    
    # Peek（查看但不出队）
    peeked_task = queue.peek()
    assert peeked_task is not None
    assert peeked_task.id == "task_1"
    assert queue.size() == 1  # 队列大小不变
    print(f"✅ Peek 功能: {peeked_task.id}")


def test_task_query():
    """测试任务查询"""
    print("\n【测试5】任务查询")
    print("-" * 70)
    
    queue = TaskQueue()
    
    # 添加不同状态的任务
    task1 = Task("task_1", {"id": "TC_1"}, "api")
    task2 = Task("task_2", {"id": "TC_2"}, "api")
    task3 = Task("task_3", {"id": "TC_3"}, "api")
    
    task1.start()
    task2.start()
    task2.succeed({"status": "passed"})
    
    queue.add_task(task1)
    queue.add_task(task2)
    queue.add_task(task3)
    
    # 获取所有任务
    all_tasks = queue.get_all_tasks()
    assert len(all_tasks) == 3
    print(f"✅ 获取所有任务: {len(all_tasks)} 个")
    
    # 按状态查询
    pending_tasks = queue.get_tasks_by_status(TaskStatus.PENDING.value)
    running_tasks = queue.get_tasks_by_status(TaskStatus.RUNNING.value)
    success_tasks = queue.get_tasks_by_status(TaskStatus.SUCCESS.value)
    
    assert len(pending_tasks) == 1
    assert len(running_tasks) == 1
    assert len(success_tasks) == 1
    
    print(f"✅ 按状态查询:")
    print(f"   pending: {len(pending_tasks)}")
    print(f"   running: {len(running_tasks)}")
    print(f"   success: {len(success_tasks)}")
    
    # 按ID查询
    task = queue.get_task_by_id("task_2")
    assert task is not None
    assert task.status == TaskStatus.SUCCESS.value
    print(f"✅ 按ID查询: {task.id}")


def test_statistics():
    """测试统计信息"""
    print("\n【测试6】统计信息")
    print("-" * 70)
    
    queue = TaskQueue()
    
    # 添加任务
    tasks = [
        Task(f"task_{i}", {"id": f"TC_{i}"}, "api")
        for i in range(1, 6)
    ]
    
    for task in tasks:
        queue.add_task(task)
    
    # 修改任务状态
    tasks[0].start()
    tasks[1].start()
    tasks[1].succeed({"status": "passed"})
    tasks[2].start()
    tasks[2].fail("Error")
    
    # 获取统计
    stats = queue.get_statistics()
    
    assert stats["total_tasks"] == 5
    assert stats["pending"] == 2
    assert stats["running"] == 1
    assert stats["success"] == 1
    assert stats["failed"] == 1
    
    print(f"✅ 统计信息:")
    print(f"   总任务数: {stats['total_tasks']}")
    print(f"   pending: {stats['pending']}")
    print(f"   running: {stats['running']}")
    print(f"   success: {stats['success']}")
    print(f"   failed: {stats['failed']}")


def test_concurrent_safety():
    """测试并发安全"""
    print("\n【测试7】并发安全")
    print("-" * 70)
    
    queue = TaskQueue()
    
    # 生产者线程
    def producer(start_id, count):
        for i in range(count):
            task = Task(f"task_{start_id + i}", {"id": f"TC_{start_id + i}"}, "api")
            queue.add_task(task)
            time.sleep(0.001)
    
    # 消费者线程
    def consumer(count):
        consumed = 0
        while consumed < count:
            task = queue.get_task(block=True, timeout=1)
            if task:
                consumed += 1
            time.sleep(0.001)
    
    # 启动多个生产者和消费者
    producers = [
        threading.Thread(target=producer, args=(i * 10, 10))
        for i in range(3)
    ]
    
    consumers = [
        threading.Thread(target=consumer, args=(10,))
        for _ in range(3)
    ]
    
    # 启动所有线程
    for t in producers + consumers:
        t.start()
    
    # 等待完成
    for t in producers + consumers:
        t.join()
    
    # 验证
    stats = queue.get_statistics()
    assert stats["total_added"] == 30
    
    print(f"✅ 并发测试完成")
    print(f"   生产者: 3 个线程")
    print(f"   消费者: 3 个线程")
    print(f"   总任务数: {stats['total_added']}")


def test_clear():
    """测试清空队列"""
    print("\n【测试8】清空队列")
    print("-" * 70)
    
    queue = TaskQueue()
    
    # 添加任务
    for i in range(5):
        task = Task(f"task_{i}", {"id": f"TC_{i}"}, "api")
        queue.add_task(task)
    
    assert queue.size() == 5
    print(f"✅ 添加任务: {queue.size()} 个")
    
    # 清空
    queue.clear()
    
    assert queue.size() == 0
    assert queue.is_empty() is True
    assert len(queue.get_all_tasks()) == 0
    
    print(f"✅ 清空队列成功")


def test_create_function():
    """测试便捷创建函数"""
    print("\n【测试9】便捷创建函数")
    print("-" * 70)
    
    queue = create_task_queue(max_size=10)
    
    assert queue is not None
    assert isinstance(queue, TaskQueue)
    
    print(f"✅ 创建队列: {queue}")


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("TaskQueue 任务队列测试")
    print("=" * 70)
    
    try:
        test_queue_basic()
        test_priority_scheduling()
        test_batch_add()
        test_queue_status()
        test_task_query()
        test_statistics()
        test_concurrent_safety()
        test_clear()
        test_create_function()
        
        print("\n" + "=" * 70)
        print("✅ 所有测试通过 (9/9)")
        print("=" * 70)
        
    except AssertionError as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
    except Exception as e:
        print(f"\n❌ 测试异常: {e}")
        import traceback
        traceback.print_exc()
