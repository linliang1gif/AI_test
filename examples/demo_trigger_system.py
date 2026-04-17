"""
触发系统使用示例
演示如何使用TestTriggerSystem
"""
import time
from modules.trigger.test_trigger_system import TestTriggerSystem


class SimplePipelineService:
    """简单的Pipeline服务"""
    
    def run_pipeline(self, requirement, swagger_file=None, config=None):
        """执行Pipeline"""
        print(f"\n🔄 执行Pipeline...")
        print(f"  需求: {requirement[:80]}...")
        print(f"  触发类型: {config.get('trigger_type')}")
        
        # 模拟执行
        time.sleep(1)
        
        return {
            "trace_id": f"trace_{int(time.time())}",
            "status": "success",
            "summary": "测试执行完成"
        }


def main():
    print("=" * 60)
    print("🚀 测试触发系统使用示例")
    print("=" * 60)
    
    # 1. 创建触发系统
    pipeline_service = SimplePipelineService()
    trigger_system = TestTriggerSystem(pipeline_service=pipeline_service)
    
    # 2. Git Push 触发示例
    print("\n" + "=" * 60)
    print("示例1: Git Push 触发")
    print("=" * 60)
    
    git_result = trigger_system.on_git_push(
        repo="my-project",
        branch="feature/user-auth",
        commit_id="a1b2c3d4e5f6",
        commit_message="feat: 实现用户认证功能",
        changed_files=[
            "src/auth/login.py",
            "src/auth/register.py",
            "tests/test_auth.py"
        ],
        author="开发者A"
    )
    
    print(f"\n✅ Git触发成功:")
    print(f"  Trigger ID: {git_result['trigger_id']}")
    print(f"  状态: {git_result['status']}")
    
    # 等待执行
    time.sleep(2)
    status = trigger_system.get_trigger_status(git_result['trigger_id'])
    print(f"\n📊 执行状态: {status['status']}")
    if status.get('trace_id'):
        print(f"  Trace ID: {status['trace_id']}")
    
    # 3. 手动触发示例
    print("\n" + "=" * 60)
    print("示例2: 手动触发")
    print("=" * 60)
    
    manual_result = trigger_system.manual_trigger(
        requirement="""
        测试需求：用户管理模块
        1. 用户注册功能
        2. 用户登录功能
        3. 密码重置功能
        """,
        priority="P0",
        user="测试工程师"
    )
    
    print(f"\n✅ 手动触发成功:")
    print(f"  Trigger ID: {manual_result['trigger_id']}")
    
    # 等待执行
    time.sleep(2)
    status = trigger_system.get_trigger_status(manual_result['trigger_id'])
    print(f"\n📊 执行状态: {status['status']}")
    
    # 4. 定时触发示例
    print("\n" + "=" * 60)
    print("示例3: 定时触发")
    print("=" * 60)
    
    # 添加每日回归测试
    schedule_result = trigger_system.schedule_trigger(
        cron_expression="0 2 * * *",  # 每天凌晨2点
        requirement="每日回归测试：验证核心功能",
        job_name="daily_regression",
        priority="P2"
    )
    
    print(f"\n✅ 定时任务创建成功:")
    print(f"  Job ID: {schedule_result['job_id']}")
    print(f"  Cron: 每天凌晨2点执行")
    
    # 添加每周全量测试
    schedule_result2 = trigger_system.schedule_trigger(
        cron_expression="0 3 * * 0",  # 每周日凌晨3点
        requirement="每周全量测试：完整功能验证",
        job_name="weekly_full_test",
        priority="P1"
    )
    
    print(f"\n✅ 定时任务创建成功:")
    print(f"  Job ID: {schedule_result2['job_id']}")
    print(f"  Cron: 每周日凌晨3点执行")
    
    # 列出所有定时任务
    jobs = trigger_system.list_scheduled_jobs()
    print(f"\n📋 定时任务列表:")
    for job in jobs:
        print(f"  - {job['job_name']}")
        print(f"    Cron: {job['cron_expression']}")
        print(f"    优先级: {job['priority']}")
        print(f"    状态: {'启用' if job['enabled'] else '禁用'}")
    
    # 5. 查询触发历史
    print("\n" + "=" * 60)
    print("示例4: 查询触发历史")
    print("=" * 60)
    
    all_triggers = trigger_system.list_triggers(limit=10)
    print(f"\n📋 最近的触发记录 ({len(all_triggers)} 个):")
    for trigger in all_triggers:
        print(f"\n  Trigger ID: {trigger['trigger_id']}")
        print(f"  类型: {trigger['trigger_type']}")
        print(f"  状态: {trigger['status']}")
        print(f"  创建时间: {trigger['created_at']}")
        if trigger.get('trace_id'):
            print(f"  Trace ID: {trigger['trace_id']}")
    
    # 6. 清理
    print("\n" + "=" * 60)
    print("清理资源")
    print("=" * 60)
    
    # 删除定时任务
    for job in jobs:
        trigger_system.delete_scheduled_job(job['job_id'])
        print(f"✅ 已删除定时任务: {job['job_name']}")
    
    # 停止调度器
    trigger_system.stop_scheduler()
    print(f"✅ 调度器已停止")
    
    print("\n" + "=" * 60)
    print("✅ 示例演示完成")
    print("=" * 60)


if __name__ == "__main__":
    main()
