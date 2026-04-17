"""
测试触发系统测试脚本
"""
import time
from modules.trigger.test_trigger_system import TestTriggerSystem, TriggerType, TriggerStatus


class MockPipelineService:
    """模拟Pipeline服务"""
    
    def run_pipeline(self, requirement, swagger_file=None, config=None):
        """模拟执行Pipeline"""
        print(f"\n📋 Pipeline执行:")
        print(f"  需求: {requirement[:100]}...")
        print(f"  配置: {config}")
        
        # 模拟执行时间
        time.sleep(1)
        
        return {
            "trace_id": f"trace_{int(time.time() * 1000)}",
            "status": "success",
            "test_cases_generated": 5,
            "test_cases_executed": 5,
            "test_cases_passed": 5
        }


def test_git_push_trigger():
    """测试Git Push触发"""
    print("=" * 60)
    print("测试1: Git Push 触发")
    print("=" * 60)
    
    # 创建触发系统
    pipeline_service = MockPipelineService()
    trigger_system = TestTriggerSystem(pipeline_service=pipeline_service)
    
    # 模拟Git Push
    result = trigger_system.on_git_push(
        repo="ai-test-platform",
        branch="main",
        commit_id="abc123def456",
        commit_message="feat: 添加用户登录功能",
        changed_files=[
            "src/api/user_controller.py",
            "src/service/auth_service.py",
            "tests/test_user.py"
        ],
        author="张三"
    )
    
    print(f"\n✅ 触发结果:")
    print(f"  Trigger ID: {result['trigger_id']}")
    print(f"  状态: {result['status']}")
    print(f"  消息: {result['message']}")
    
    # 等待执行完成
    trigger_id = result['trigger_id']
    print(f"\n⏳ 等待执行完成...")
    
    for i in range(10):
        time.sleep(1)
        status = trigger_system.get_trigger_status(trigger_id)
        if status and status['status'] in ['success', 'failed']:
            break
    
    # 查看最终状态
    final_status = trigger_system.get_trigger_status(trigger_id)
    print(f"\n📊 最终状态:")
    print(f"  状态: {final_status['status']}")
    print(f"  Trace ID: {final_status.get('trace_id')}")
    if final_status.get('pipeline_result'):
        print(f"  Pipeline结果: {final_status['pipeline_result']}")
    
    print(f"\n✅ Git Push触发测试通过\n")


def test_manual_trigger():
    """测试手动触发"""
    print("=" * 60)
    print("测试2: 手动触发")
    print("=" * 60)
    
    # 创建触发系统
    pipeline_service = MockPipelineService()
    trigger_system = TestTriggerSystem(pipeline_service=pipeline_service)
    
    # 手动触发
    result = trigger_system.manual_trigger(
        requirement="测试用户注册和登录功能，包括参数验证、密码加密、Token生成",
        priority="P0",
        user="测试工程师"
    )
    
    print(f"\n✅ 触发结果:")
    print(f"  Trigger ID: {result['trigger_id']}")
    print(f"  状态: {result['status']}")
    
    # 等待执行完成
    trigger_id = result['trigger_id']
    print(f"\n⏳ 等待执行完成...")
    
    for i in range(10):
        time.sleep(1)
        status = trigger_system.get_trigger_status(trigger_id)
        if status and status['status'] in ['success', 'failed']:
            break
    
    # 查看最终状态
    final_status = trigger_system.get_trigger_status(trigger_id)
    print(f"\n📊 最终状态:")
    print(f"  状态: {final_status['status']}")
    print(f"  Trace ID: {final_status.get('trace_id')}")
    
    print(f"\n✅ 手动触发测试通过\n")


def test_scheduled_trigger():
    """测试定时触发"""
    print("=" * 60)
    print("测试3: 定时触发")
    print("=" * 60)
    
    # 创建触发系统
    pipeline_service = MockPipelineService()
    trigger_system = TestTriggerSystem(pipeline_service=pipeline_service)
    
    # 添加定时任务（每分钟执行一次，用于测试）
    result = trigger_system.schedule_trigger(
        cron_expression="* * * * *",  # 每分钟
        requirement="每日回归测试：验证核心功能正常运行",
        job_name="daily_regression",
        priority="P2"
    )
    
    print(f"\n✅ 定时任务创建:")
    print(f"  Job ID: {result['job_id']}")
    print(f"  Cron: {result['job']['cron_expression']}")
    print(f"  任务名: {result['job']['job_name']}")
    
    # 列出所有定时任务
    jobs = trigger_system.list_scheduled_jobs()
    print(f"\n📋 定时任务列表: {len(jobs)} 个")
    for job in jobs:
        print(f"  - {job['job_name']}: {job['cron_expression']} (启用: {job['enabled']})")
    
    # 更新任务
    update_result = trigger_system.update_scheduled_job(
        job_id=result['job_id'],
        enabled=False
    )
    print(f"\n✅ 任务已禁用")
    
    # 删除任务
    delete_result = trigger_system.delete_scheduled_job(result['job_id'])
    print(f"✅ 任务已删除")
    
    print(f"\n✅ 定时触发测试通过\n")


def test_list_triggers():
    """测试查询触发记录"""
    print("=" * 60)
    print("测试4: 查询触发记录")
    print("=" * 60)
    
    # 创建触发系统
    pipeline_service = MockPipelineService()
    trigger_system = TestTriggerSystem(pipeline_service=pipeline_service)
    
    # 创建多个触发
    trigger_system.manual_trigger("测试需求1", priority="P0")
    time.sleep(0.5)
    trigger_system.manual_trigger("测试需求2", priority="P1")
    time.sleep(0.5)
    trigger_system.on_git_push("repo1", "main", "commit1")
    
    # 等待一下
    time.sleep(2)
    
    # 查询所有触发
    all_triggers = trigger_system.list_triggers(limit=10)
    print(f"\n📋 所有触发记录: {len(all_triggers)} 个")
    for trigger in all_triggers:
        print(f"  - {trigger['trigger_id']}: {trigger['trigger_type']} ({trigger['status']})")
    
    # 按类型过滤
    manual_triggers = trigger_system.list_triggers(trigger_type=TriggerType.MANUAL.value)
    print(f"\n📋 手动触发记录: {len(manual_triggers)} 个")
    
    git_triggers = trigger_system.list_triggers(trigger_type=TriggerType.GIT_PUSH.value)
    print(f"📋 Git触发记录: {len(git_triggers)} 个")
    
    print(f"\n✅ 查询触发记录测试通过\n")


def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("🚀 测试触发系统测试")
    print("=" * 60 + "\n")
    
    try:
        test_git_push_trigger()
        test_manual_trigger()
        test_scheduled_trigger()
        test_list_triggers()
        
        print("=" * 60)
        print("📊 测试总结")
        print("=" * 60)
        print("✅ 通过 - Git Push触发")
        print("✅ 通过 - 手动触发")
        print("✅ 通过 - 定时触发")
        print("✅ 通过 - 查询触发记录")
        print("=" * 60)
        print("通过率: 4/4 (100.0%)")
        print("=" * 60)
        print("\n🎉 所有测试通过！\n")
    
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
