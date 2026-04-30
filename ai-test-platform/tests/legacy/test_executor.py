"""
测试 Executor 执行分发器

验证点：
1. 分发逻辑（api/ui/integration）
2. 任务状态更新
3. 执行结果返回
4. 异常处理
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from orchestrator.executor import TaskExecutor, execute_task, get_executor
from orchestrator.task import Task, TaskStatus


def test_executor_api():
    """测试 API 任务执行"""
    print("\n【测试1】API 任务执行")
    print("-" * 70)
    
    executor = TaskExecutor()
    
    # 创建 API 任务
    case = {"id": "TC_API_001", "title": "API登录测试"}
    task = Task("task_api_1", case, "api", priority=5)
    
    # 执行任务
    result = executor.execute_task(task)
    
    # 验证任务状态
    assert task.status == TaskStatus.SUCCESS.value
    assert task.result is not None
    
    # 验证执行结果
    assert result["status"] in ["passed", "failed"]
    assert "duration" in result
    assert "details" in result
    
    print(f"✅ API 任务执行成功")
    print(f"   任务状态: {task.status}")
    print(f"   执行结果: {result['status']}")
    print(f"   执行时长: {result['duration']}s")


def test_executor_ui():
    """测试 UI 任务执行"""
    print("\n【测试2】UI 任务执行")
    print("-" * 70)
    
    executor = TaskExecutor()
    
    # 创建 UI 任务
    case = {"id": "TC_UI_001", "title": "UI按钮点击测试"}
    task = Task("task_ui_1", case, "ui", priority=3)
    
    # 执行任务
    result = executor.execute_task(task)
    
    # 验证
    assert task.status == TaskStatus.SUCCESS.value
    assert result["status"] in ["passed", "failed"]
    
    print(f"✅ UI 任务执行成功")
    print(f"   任务状态: {task.status}")
    print(f"   执行结果: {result['status']}")


def test_executor_integration():
    """测试集成任务执行"""
    print("\n【测试3】集成任务执行")
    print("-" * 70)
    
    executor = TaskExecutor()
    
    # 创建集成任务
    case = {"id": "TC_INT_001", "title": "订单流程集成测试"}
    task = Task("task_int_1", case, "integration", priority=1)
    
    # 执行任务
    result = executor.execute_task(task)
    
    # 验证
    assert task.status == TaskStatus.SUCCESS.value
    assert result["status"] in ["passed", "failed"]
    
    print(f"✅ 集成任务执行成功")
    print(f"   任务状态: {task.status}")
    print(f"   执行结果: {result['status']}")


def test_executor_dispatch():
    """测试分发逻辑"""
    print("\n【测试4】分发逻辑")
    print("-" * 70)
    
    executor = TaskExecutor()
    
    # 测试不同类型的任务
    task_types = ["api", "ui", "integration"]
    
    for task_type in task_types:
        case = {"id": f"TC_{task_type.upper()}_001", "title": f"{task_type}测试"}
        task = Task(f"task_{task_type}_1", case, task_type)
        
        result = executor.execute_task(task)
        
        assert task.status == TaskStatus.SUCCESS.value
        print(f"   ✅ {task_type} 分发成功")
    
    print(f"✅ 分发逻辑验证通过")


def test_executor_error_handling():
    """测试异常处理"""
    print("\n【测试5】异常处理")
    print("-" * 70)
    
    executor = TaskExecutor()
    
    # 创建不支持的任务类型
    case = {"id": "TC_ERR_001", "title": "错误测试"}
    task = Task("task_err_1", case, "unknown_type")
    
    # 执行任务（应该失败）
    result = executor.execute_task(task)
    
    # 验证任务状态为失败
    assert task.status == TaskStatus.FAILED.value
    assert task.error is not None
    assert "不支持的任务类型" in task.error
    
    # 验证执行结果
    assert result["status"] == "failed"
    
    print(f"✅ 异常处理正确")
    print(f"   任务状态: {task.status}")
    print(f"   错误信息: {task.error}")


def test_executor_singleton():
    """测试单例模式"""
    print("\n【测试6】单例模式")
    print("-" * 70)
    
    executor1 = get_executor()
    executor2 = get_executor()
    
    assert executor1 is executor2
    
    print(f"✅ 单例模式验证通过")
    print(f"   executor1 id: {id(executor1)}")
    print(f"   executor2 id: {id(executor2)}")


def test_execute_task_function():
    """测试便捷函数"""
    print("\n【测试7】便捷函数")
    print("-" * 70)
    
    # 使用便捷函数
    case = {"id": "TC_FUNC_001", "title": "便捷函数测试"}
    task = Task("task_func_1", case, "api")
    
    result = execute_task(task)
    
    assert task.status == TaskStatus.SUCCESS.value
    assert result["status"] in ["passed", "failed"]
    
    print(f"✅ 便捷函数验证通过")
    print(f"   任务状态: {task.status}")


def test_task_state_transition():
    """测试任务状态转换"""
    print("\n【测试8】任务状态转换")
    print("-" * 70)
    
    executor = TaskExecutor()
    
    case = {"id": "TC_STATE_001", "title": "状态转换测试"}
    task = Task("task_state_1", case, "api")
    
    # 初始状态
    assert task.status == TaskStatus.PENDING.value
    print(f"   初始状态: {task.status}")
    
    # 执行任务
    result = executor.execute_task(task)
    
    # 最终状态
    assert task.status in [TaskStatus.SUCCESS.value, TaskStatus.FAILED.value]
    print(f"   最终状态: {task.status}")
    
    # 验证时间戳
    assert task.started_at is not None
    assert task.finished_at is not None
    assert task.duration > 0
    
    print(f"✅ 状态转换正确")
    print(f"   执行时长: {task.duration}s")


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("Executor 执行分发器测试")
    print("=" * 70)
    
    try:
        test_executor_api()
        test_executor_ui()
        test_executor_integration()
        test_executor_dispatch()
        test_executor_error_handling()
        test_executor_singleton()
        test_execute_task_function()
        test_task_state_transition()
        
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
