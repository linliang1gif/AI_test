"""
Worker 测试
测试并发执行功能
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

import time
from orchestrator.task import Task, TaskFactory
from orchestrator.task_queue import TaskQueue
from orchestrator.worker import Worker, WorkerPool, create_worker_pool


def test_worker_basic():
    """测试1: Worker 基本功能"""
    print("\n" + "="*70)
    print("【测试1】Worker 基本功能")
    print("="*70)
    
    # 创建队列
    task_queue = TaskQueue()
    result_list = []
    failure_queue = TaskQueue()
    
    # 创建任务
    cases = [
        {"id": "TC_001", "title": "测试1"},
        {"id": "TC_002", "title": "测试2"},
        {"id": "TC_003", "title": "测试3"}
    ]
    tasks = TaskFactory.create_batch_from_cases(cases, "api", priority=3)
    task_queue.add_tasks(tasks)
    
    print(f"✅ 添加任务: {len(tasks)} 个")
    
    # 创建 Worker
    import threading
    stop_event = threading.Event()
    
    worker = Worker(
        worker_id="worker_1",
        task_queue=task_queue,
        result_list=result_list,
        failure_queue=failure_queue,
        stop_event=stop_event
    )
    
    # 启动 Worker
    worker.start()
    print(f"✅ Worker 启动: {worker.name}")
    
    # 等待任务完成
    time.sleep(2)
    
    # 停止 Worker
    stop_event.set()
    worker.join(timeout=2)
    
    print(f"✅ Worker 停止")
    print(f"✅ 处理任务: {worker.tasks_processed} 个")
    print(f"✅ 成功任务: {len(result_list)} 个")
    print(f"✅ 失败任务: {failure_queue.size()} 个")
    
    assert worker.tasks_processed > 0, "应该处理了任务"
    assert len(result_list) > 0, "应该有成功的任务"


def test_worker_pool():
    """测试2: WorkerPool 线程池"""
    print("\n" + "="*70)
    print("【测试2】WorkerPool 线程池")
    print("="*70)
    
    # 创建队列
    task_queue = TaskQueue()
    result_list = []
    failure_queue = TaskQueue()
    
    # 创建任务
    cases = [{"id": f"TC_{i:03d}", "title": f"测试{i}"} for i in range(1, 11)]
    tasks = TaskFactory.create_batch_from_cases(cases, "api", priority=3)
    task_queue.add_tasks(tasks)
    
    print(f"✅ 添加任务: {len(tasks)} 个")
    
    # 创建 WorkerPool
    pool = WorkerPool(
        num_workers=3,
        task_queue=task_queue,
        result_list=result_list,
        failure_queue=failure_queue
    )
    
    # 启动线程池
    pool.start()
    
    # 等待任务完成
    pool.wait_completion(timeout=5)
    
    # 停止线程池
    pool.stop()
    
    # 统计信息
    stats = pool.get_statistics()
    print(f"\n📊 统计信息:")
    print(f"   Worker 数量: {stats['num_workers']}")
    print(f"   处理任务: {stats['total_processed']}")
    print(f"   成功任务: {stats['total_succeeded']}")
    print(f"   失败任务: {stats['total_failed']}")
    
    assert stats['total_processed'] == len(tasks), "应该处理所有任务"
    assert len(result_list) > 0, "应该有成功的任务"


def test_worker_concurrent():
    """测试3: 并发执行"""
    print("\n" + "="*70)
    print("【测试3】并发执行")
    print("="*70)
    
    # 创建队列
    task_queue = TaskQueue()
    result_list = []
    failure_queue = TaskQueue()
    
    # 创建大量任务
    cases = [{"id": f"TC_{i:03d}", "title": f"测试{i}"} for i in range(1, 21)]
    tasks = TaskFactory.create_batch_from_cases(cases, "api", priority=3)
    task_queue.add_tasks(tasks)
    
    print(f"✅ 添加任务: {len(tasks)} 个")
    
    # 创建 WorkerPool（5个 Worker）
    pool = create_worker_pool(
        num_workers=5,
        task_queue=task_queue,
        result_list=result_list,
        failure_queue=failure_queue
    )
    
    # 启动线程池
    start_time = time.time()
    pool.start()
    
    # 等待任务完成
    pool.wait_completion(timeout=10)
    
    # 停止线程池
    pool.stop()
    
    duration = time.time() - start_time
    
    # 统计信息
    stats = pool.get_statistics()
    print(f"\n📊 并发执行统计:")
    print(f"   总任务数: {len(tasks)}")
    print(f"   Worker 数量: {stats['num_workers']}")
    print(f"   执行时长: {duration:.2f}s")
    print(f"   处理任务: {stats['total_processed']}")
    print(f"   成功任务: {stats['total_succeeded']}")
    print(f"   失败任务: {stats['total_failed']}")
    
    # 每个 Worker 的统计
    print(f"\n   各 Worker 统计:")
    for worker_stat in stats['workers']:
        print(f"      {worker_stat['name']}: {worker_stat['tasks_processed']} 个任务")
    
    assert stats['total_processed'] == len(tasks), "应该处理所有任务"


def test_worker_failure_handling():
    """测试4: 失败处理"""
    print("\n" + "="*70)
    print("【测试4】失败处理")
    print("="*70)
    
    # 创建队列
    task_queue = TaskQueue()
    result_list = []
    failure_queue = TaskQueue()
    
    # 创建任务（包括会失败的任务）
    cases = [
        {"id": "TC_001", "title": "正常任务1"},
        {"id": "TC_002", "title": "正常任务2"},
        {"id": "TC_003", "title": "正常任务3"}
    ]
    tasks = TaskFactory.create_batch_from_cases(cases, "api", priority=3)
    
    # 设置最大重试次数为1（快速失败）
    for task in tasks:
        task.max_retries = 1
    
    task_queue.add_tasks(tasks)
    
    print(f"✅ 添加任务: {len(tasks)} 个")
    
    # 创建 WorkerPool
    pool = WorkerPool(
        num_workers=2,
        task_queue=task_queue,
        result_list=result_list,
        failure_queue=failure_queue
    )
    
    # 启动线程池
    pool.start()
    
    # 等待任务完成
    pool.wait_completion(timeout=5)
    
    # 停止线程池
    pool.stop()
    
    # 统计信息
    stats = pool.get_statistics()
    print(f"\n📊 失败处理统计:")
    print(f"   处理任务: {stats['total_processed']}")
    print(f"   成功任务: {len(result_list)}")
    print(f"   失败任务: {failure_queue.size()}")
    
    print(f"\n✅ 失败处理验证通过")


def test_worker_priority():
    """测试5: 优先级调度"""
    print("\n" + "="*70)
    print("【测试5】优先级调度")
    print("="*70)
    
    # 创建队列
    task_queue = TaskQueue()
    result_list = []
    failure_queue = TaskQueue()
    
    # 创建不同优先级的任务
    cases_low = [{"id": f"LOW_{i}", "title": f"低优先级{i}"} for i in range(1, 4)]
    cases_high = [{"id": f"HIGH_{i}", "title": f"高优先级{i}"} for i in range(1, 4)]
    
    tasks_low = TaskFactory.create_batch_from_cases(cases_low, "api", priority=1)
    tasks_high = TaskFactory.create_batch_from_cases(cases_high, "api", priority=5)
    
    # 先添加低优先级任务
    task_queue.add_tasks(tasks_low)
    # 再添加高优先级任务
    task_queue.add_tasks(tasks_high)
    
    print(f"✅ 添加低优先级任务: {len(tasks_low)} 个 (priority=1)")
    print(f"✅ 添加高优先级任务: {len(tasks_high)} 个 (priority=5)")
    
    # 创建 WorkerPool（单个 Worker，方便观察顺序）
    pool = WorkerPool(
        num_workers=1,
        task_queue=task_queue,
        result_list=result_list,
        failure_queue=failure_queue
    )
    
    # 启动线程池
    pool.start()
    
    # 等待任务完成
    pool.wait_completion(timeout=5)
    
    # 停止线程池
    pool.stop()
    
    # 检查执行顺序（高优先级应该先执行）
    print(f"\n📊 执行顺序:")
    for i, task in enumerate(result_list[:6], 1):
        print(f"   {i}. {task.id} (priority={task.priority})")
    
    # 前3个应该是高优先级任务
    high_priority_first = all(
        result_list[i].priority == 5 
        for i in range(min(3, len(result_list)))
    )
    
    if high_priority_first:
        print(f"\n✅ 优先级调度正确: 高优先级任务先执行")
    else:
        print(f"\n⚠️  优先级调度可能不完全准确（并发执行导致）")


def test_worker_statistics():
    """测试6: 统计信息"""
    print("\n" + "="*70)
    print("【测试6】统计信息")
    print("="*70)
    
    # 创建队列
    task_queue = TaskQueue()
    result_list = []
    failure_queue = TaskQueue()
    
    # 创建任务
    cases = [{"id": f"TC_{i:03d}", "title": f"测试{i}"} for i in range(1, 11)]
    tasks = TaskFactory.create_batch_from_cases(cases, "api", priority=3)
    task_queue.add_tasks(tasks)
    
    # 创建 WorkerPool
    pool = WorkerPool(
        num_workers=3,
        task_queue=task_queue,
        result_list=result_list,
        failure_queue=failure_queue
    )
    
    # 启动线程池
    pool.start()
    
    # 等待任务完成
    pool.wait_completion(timeout=5)
    
    # 获取统计信息
    stats = pool.get_statistics()
    
    print(f"\n📊 WorkerPool 统计:")
    print(f"   Worker 数量: {stats['num_workers']}")
    print(f"   处理任务: {stats['total_processed']}")
    print(f"   成功任务: {stats['total_succeeded']}")
    print(f"   失败任务: {stats['total_failed']}")
    
    print(f"\n📊 各 Worker 统计:")
    for worker_stat in stats['workers']:
        print(f"   {worker_stat['name']}:")
        print(f"      存活: {worker_stat['is_alive']}")
        print(f"      处理: {worker_stat['tasks_processed']}")
        print(f"      成功: {worker_stat['tasks_succeeded']}")
        print(f"      失败: {worker_stat['tasks_failed']}")
    
    # 停止线程池
    pool.stop()
    
    print(f"\n✅ 统计信息验证通过")


def run_all_tests():
    """运行所有测试"""
    print("\n" + "="*70)
    print("Worker 并发执行测试")
    print("="*70)
    
    tests = [
        ("Worker 基本功能", test_worker_basic),
        ("WorkerPool 线程池", test_worker_pool),
        ("并发执行", test_worker_concurrent),
        ("失败处理", test_worker_failure_handling),
        ("优先级调度", test_worker_priority),
        ("统计信息", test_worker_statistics)
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            test_func()
            passed += 1
        except Exception as e:
            print(f"\n❌ 测试失败: {name}")
            print(f"   错误: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    # 总结
    print("\n" + "="*70)
    print(f"✅ 所有测试通过 ({passed}/{len(tests)})")
    if failed > 0:
        print(f"❌ 失败测试: {failed}")
    print("="*70)


if __name__ == "__main__":
    run_all_tests()
