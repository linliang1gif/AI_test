"""
测试 Task 数据模型

验证点：
1. Task 基本功能
2. 状态转换
3. 优先级支持
4. TaskFactory 工厂方法
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from orchestrator.task import Task, TaskFactory, TaskStatus, TaskType


def test_task_basic():
    """测试 Task 基本功能"""
    print("\n【测试1】Task 基本功能")
    print("-" * 70)
    
    case = {
        "id": "TC_001",
        "title": "登录测试",
        "module": "用户模块"
    }
    
    task = Task("task_001", case, "api", priority=5)
    
    assert task.id == "task_001"
    assert task.case == case
    assert task.task_type == "api"
    assert task.priority == 5
    assert task.status == TaskStatus.PENDING.value
    assert task.result is None
    assert task.error is None
    
    print(f"✅ Task 创建成功: {task}")
    print(f"   状态: {task.status}")
    print(f"   优先级: {task.priority}")


def test_task_status_transition():
    """测试 Task 状态转换"""
    print("\n【测试2】Task 状态转换")
    print("-" * 70)
    
    case = {"id": "TC_002", "title": "支付测试"}
    task = Task("task_002", case, "api")
    
    # pending -> running
    task.start()
    assert task.status == TaskStatus.RUNNING.value
    assert task.started_at is not None
    print(f"✅ 状态转换: pending -> running")
    
    # running -> success
    result = {"status": "passed", "response_time": 0.5}
    task.succeed(result)
    assert task.status == TaskStatus.SUCCESS.value
    assert task.result == result
    assert task.finished_at is not None
    print(f"✅ 状态转换: running -> success")
    print(f"   执行时长: {task.duration}s")


def test_task_failure_and_retry():
    """测试 Task 失败和重试"""
    print("\n【测试3】Task 失败和重试")
    print("-" * 70)
    
    case = {"id": "TC_003", "title": "订单测试"}
    task = Task("task_003", case, "api")
    task.max_retries = 2
    
    # 第一次失败
    task.start()
    task.fail("Connection timeout")
    assert task.status == TaskStatus.FAILED.value
    assert task.error == "Connection timeout"
    assert task.can_retry() is True
    print(f"✅ 第1次失败: {task.error}")
    
    # 重试
    task.retry()
    assert task.status == TaskStatus.PENDING.value
    assert task.retry_count == 1
    print(f"✅ 重试次数: {task.retry_count}")
    
    # 第二次失败
    task.start()
    task.fail("Server error")
    assert task.can_retry() is True
    print(f"✅ 第2次失败: {task.error}")
    
    # 再次重试
    task.retry()
    assert task.retry_count == 2
    
    # 第三次失败（达到最大重试次数）
    task.start()
    task.fail("Network error")
    assert task.can_retry() is False
    print(f"✅ 达到最大重试次数: {task.retry_count}/{task.max_retries}")


def test_task_priority():
    """测试 Task 优先级"""
    print("\n【测试4】Task 优先级")
    print("-" * 70)
    
    task1 = Task("task_1", {"id": "TC_1"}, "api", priority=1)
    task2 = Task("task_2", {"id": "TC_2"}, "api", priority=5)
    task3 = Task("task_3", {"id": "TC_3"}, "api", priority=3)
    
    # 优先级排序（高优先级在前）
    tasks = [task1, task2, task3]
    sorted_tasks = sorted(tasks)
    
    assert sorted_tasks[0].priority == 5
    assert sorted_tasks[1].priority == 3
    assert sorted_tasks[2].priority == 1
    
    print(f"✅ 优先级排序:")
    for i, task in enumerate(sorted_tasks, 1):
        print(f"   {i}. {task.id} (priority={task.priority})")


def test_task_factory_from_case():
    """测试 TaskFactory.create_from_case"""
    print("\n【测试5】TaskFactory.create_from_case")
    print("-" * 70)
    
    case = {"id": "TC_004", "title": "库存测试"}
    task = TaskFactory.create_from_case(case, "api", priority=3)
    
    assert task.case == case
    assert task.task_type == "api"
    assert task.priority == 3
    
    print(f"✅ 从用例创建 Task: {task}")


def test_task_factory_batch():
    """测试 TaskFactory.create_batch_from_cases"""
    print("\n【测试6】TaskFactory.create_batch_from_cases")
    print("-" * 70)
    
    cases = [
        {"id": "TC_005", "title": "测试1"},
        {"id": "TC_006", "title": "测试2"},
        {"id": "TC_007", "title": "测试3"}
    ]
    
    tasks = TaskFactory.create_batch_from_cases(cases, "ui", priority=2)
    
    assert len(tasks) == 3
    assert all(t.task_type == "ui" for t in tasks)
    assert all(t.priority == 2 for t in tasks)
    
    print(f"✅ 批量创建 Task: {len(tasks)} 个")
    for task in tasks:
        print(f"   - {task}")


def test_task_factory_from_strategy():
    """测试 TaskFactory.create_from_strategy"""
    print("\n【测试7】TaskFactory.create_from_strategy")
    print("-" * 70)
    
    strategy = {
        "strategy": [
            {
                "module": {"name": "支付模块"},
                "test_types": ["api", "ui"]
            },
            {
                "module": {"name": "订单模块"},
                "test_types": ["api", "integration"]
            }
        ]
    }
    
    tasks = TaskFactory.create_from_strategy(strategy)
    
    assert len(tasks) == 4  # 2个模块 * 2个测试类型 = 4个任务
    
    # 验证优先级
    api_tasks = [t for t in tasks if t.task_type == "api"]
    ui_tasks = [t for t in tasks if t.task_type == "ui"]
    integration_tasks = [t for t in tasks if t.task_type == "integration"]
    
    assert all(t.priority == 3 for t in api_tasks)
    assert all(t.priority == 2 for t in ui_tasks)
    assert all(t.priority == 1 for t in integration_tasks)
    
    print(f"✅ 从策略创建 Task: {len(tasks)} 个")
    for task in sorted(tasks):
        print(f"   - {task}")


def test_task_to_dict():
    """测试 Task.to_dict"""
    print("\n【测试8】Task.to_dict")
    print("-" * 70)
    
    case = {"id": "TC_008", "title": "序列化测试"}
    task = Task("task_008", case, "api", priority=4)
    
    task.start()
    task.succeed({"status": "passed"})
    
    task_dict = task.to_dict()
    
    assert task_dict["id"] == "task_008"
    assert task_dict["status"] == TaskStatus.SUCCESS.value
    assert task_dict["priority"] == 4
    assert task_dict["result"] == {"status": "passed"}
    
    print(f"✅ Task 序列化成功")
    print(f"   字段数: {len(task_dict)}")


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("Task 数据模型测试")
    print("=" * 70)
    
    try:
        test_task_basic()
        test_task_status_transition()
        test_task_failure_and_retry()
        test_task_priority()
        test_task_factory_from_case()
        test_task_factory_batch()
        test_task_factory_from_strategy()
        test_task_to_dict()
        
        print("\n" + "=" * 70)
        print("✅ 所有测试通过 (8/8)")
        print("=" * 70)
        
    except AssertionError as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
    except Exception as e:
        print(f"\n❌ 测试异常: {e}")
        import traceback
        traceback.print_exc()
