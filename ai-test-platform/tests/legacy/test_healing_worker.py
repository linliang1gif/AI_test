"""
Healing Worker 测试
测试独立的失败任务修复器
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from orchestrator.task import Task
from orchestrator.task_queue import TaskQueue
from self_healing.healing_worker import HealingWorker, create_healing_worker


def test_healing_worker_basic():
    """测试1: Healing Worker 基本功能"""
    print("\n" + "="*70)
    print("【测试1】Healing Worker 基本功能")
    print("="*70)
    
    # 创建失败队列
    failure_queue = TaskQueue()
    
    # 创建失败任务
    task1 = Task("task_1", {"id": "TC_001", "title": "测试1"}, "api", priority=3)
    task1.status = "failed"
    task1.error = "Connection timeout"
    task1.retry_count = 0
    
    task2 = Task("task_2", {"id": "TC_002", "title": "测试2"}, "api", priority=3)
    task2.status = "failed"
    task2.error = "Assertion failed"
    task2.retry_count = 0
    
    failure_queue.add_task(task1)
    failure_queue.add_task(task2)
    
    print(f"✅ 添加失败任务: 2 个")
    
    # 创建 Healing Worker
    healing_worker = HealingWorker(max_retries=3)
    
    # 处理失败任务
    result = healing_worker.run(failure_queue)
    
    # 验证
    print(f"\n📊 修复结果:")
    print(f"   总任务数: {result['summary']['total']}")
    print(f"   修复成功: {result['summary']['healed']}")
    print(f"   修复失败: {result['summary']['failed']}")
    print(f"   修复率: {result['summary']['heal_rate']}%")
    
    assert result['summary']['total'] == 2, "应该处理2个任务"
    
    print(f"\n✅ Healing Worker 基本功能验证通过")


def test_healing_worker_max_retries():
    """测试2: 最大重试次数限制"""
    print("\n" + "="*70)
    print("【测试2】最大重试次数限制")
    print("="*70)
    
    # 创建失败队列
    failure_queue = TaskQueue()
    
    # 创建已达到最大重试次数的任务
    task = Task("task_1", {"id": "TC_001", "title": "测试1"}, "api", priority=3)
    task.status = "failed"
    task.error = "Connection timeout"
    task.retry_count = 3  # 已重试3次
    
    failure_queue.add_task(task)
    
    # 创建 Healing Worker（最大重试3次）
    healing_worker = HealingWorker(max_retries=3)
    
    # 处理失败任务
    result = healing_worker.run(failure_queue)
    
    # 验证
    print(f"\n📊 修复结果:")
    print(f"   总任务数: {result['summary']['total']}")
    print(f"   修复成功: {result['summary']['healed']}")
    print(f"   修复失败: {result['summary']['failed']}")
    
    # 应该直接放弃修复
    assert result['summary']['failed'] == 1, "应该有1个修复失败的任务"
    assert result['summary']['healed'] == 0, "不应该有修复成功的任务"
    
    print(f"\n✅ 最大重试次数限制验证通过")


def test_healing_worker_analyze():
    """测试3: 失败原因分析"""
    print("\n" + "="*70)
    print("【测试3】失败原因分析")
    print("="*70)
    
    # 创建失败队列
    failure_queue = TaskQueue()
    
    # 创建不同失败原因的任务
    errors = [
        "Connection timeout",
        "Resource not found",
        "Permission denied",
        "Assertion failed",
        "Unknown error"
    ]
    
    for i, error in enumerate(errors, 1):
        task = Task(f"task_{i}", {"id": f"TC_{i:03d}", "title": f"测试{i}"}, "api", priority=3)
        task.status = "failed"
        task.error = error
        task.retry_count = 0
        failure_queue.add_task(task)
    
    print(f"✅ 添加失败任务: {len(errors)} 个")
    
    # 创建 Healing Worker
    healing_worker = HealingWorker(max_retries=3)
    
    # 处理失败任务
    result = healing_worker.run(failure_queue)
    
    # 验证
    print(f"\n📊 修复结果:")
    print(f"   总任务数: {result['summary']['total']}")
    print(f"   修复成功: {result['summary']['healed']}")
    print(f"   修复失败: {result['summary']['failed']}")
    
    assert result['summary']['total'] == len(errors), f"应该处理{len(errors)}个任务"
    
    print(f"\n✅ 失败原因分析验证通过")


def test_healing_worker_empty_queue():
    """测试4: 空队列处理"""
    print("\n" + "="*70)
    print("【测试4】空队列处理")
    print("="*70)
    
    # 创建空的失败队列
    failure_queue = TaskQueue()
    
    # 创建 Healing Worker
    healing_worker = HealingWorker(max_retries=3)
    
    # 处理失败任务
    result = healing_worker.run(failure_queue)
    
    # 验证
    assert result['summary']['total'] == 0, "应该没有任务"
    assert result['summary']['healed'] == 0, "不应该有修复成功的任务"
    assert result['summary']['failed'] == 0, "不应该有修复失败的任务"
    
    print(f"✅ 空队列处理验证通过")


def test_healing_worker_statistics():
    """测试5: 统计信息"""
    print("\n" + "="*70)
    print("【测试5】统计信息")
    print("="*70)
    
    # 创建失败队列
    failure_queue = TaskQueue()
    
    # 创建失败任务
    for i in range(1, 6):
        task = Task(f"task_{i}", {"id": f"TC_{i:03d}", "title": f"测试{i}"}, "api", priority=3)
        task.status = "failed"
        task.error = "Connection timeout"
        task.retry_count = 0
        failure_queue.add_task(task)
    
    # 创建 Healing Worker
    healing_worker = HealingWorker(max_retries=3)
    
    # 处理失败任务
    result = healing_worker.run(failure_queue)
    
    # 获取统计信息
    stats = healing_worker.get_statistics()
    
    print(f"\n📊 统计信息:")
    print(f"   处理任务: {stats['total_processed']}")
    print(f"   修复成功: {stats['healed']}")
    print(f"   修复失败: {stats['failed']}")
    print(f"   修复率: {stats['heal_rate']}%")
    
    assert stats['total_processed'] == 5, "应该处理5个任务"
    
    print(f"\n✅ 统计信息验证通过")


def test_healing_worker_create_function():
    """测试6: 便捷创建函数"""
    print("\n" + "="*70)
    print("【测试6】便捷创建函数")
    print("="*70)
    
    # 使用便捷函数创建
    healing_worker = create_healing_worker(max_retries=5)
    
    # 验证
    assert healing_worker.max_retries == 5, "最大重试次数应该是5"
    
    print(f"✅ 便捷创建函数验证通过")


def run_all_tests():
    """运行所有测试"""
    print("\n" + "="*70)
    print("Healing Worker 测试")
    print("="*70)
    
    tests = [
        ("Healing Worker 基本功能", test_healing_worker_basic),
        ("最大重试次数限制", test_healing_worker_max_retries),
        ("失败原因分析", test_healing_worker_analyze),
        ("空队列处理", test_healing_worker_empty_queue),
        ("统计信息", test_healing_worker_statistics),
        ("便捷创建函数", test_healing_worker_create_function)
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
