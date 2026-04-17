"""
统一执行调度器使用示例
演示如何使用 UnifiedExecutionScheduler 管理测试执行
"""
from modules.scheduler.unified_execution_scheduler import UnifiedExecutionScheduler, TaskPriority

def main():
    print("=" * 60)
    print("🚀 统一执行调度器使用示例")
    print("=" * 60)
    
    # 1. 创建调度器实例
    scheduler = UnifiedExecutionScheduler(config={
        'max_workers': 3,      # 最大并发数
        'rate_limit': 5        # 每秒最多5个请求
    })
    
    # 2. 准备测试用例（符合ExecutionEngine格式）
    test_cases = [
        {
            "id": "tc_001",
            "name": "用户登录测试",
            "execution_type": "api",
            "config": {
                "url": "https://httpbin.org/post",  # 必须有url字段
                "method": "POST",
                "headers": {"Content-Type": "application/json"},
                "body": {"username": "test", "password": "123456"}
            },
            "timeout": 10,
            "priority": TaskPriority.P0  # 高优先级
        },
        {
            "id": "tc_002",
            "name": "获取用户信息",
            "execution_type": "api",
            "config": {
                "url": "https://httpbin.org/get",  # 必须有url字段
                "method": "GET",
                "headers": {"Content-Type": "application/json"}
            },
            "timeout": 10,
            "priority": TaskPriority.P1  # 中优先级
        },
        {
            "id": "tc_003",
            "name": "更新用户资料",
            "execution_type": "api",
            "config": {
                "url": "https://httpbin.org/put",  # 必须有url字段
                "method": "PUT",
                "headers": {"Content-Type": "application/json"},
                "body": {"name": "张三", "age": 25}
            },
            "timeout": 10,
            "priority": TaskPriority.P2  # 低优先级
        }
    ]
    
    # 3. 提交任务
    print("\n📝 提交测试任务...")
    for tc in test_cases:
        task_id = scheduler.submit(
            test_case=tc,
            priority=tc["priority"].name
        )
        print(f"  ✅ {tc['name']} (ID: {task_id}, 优先级: {tc['priority'].name})")
    
    # 4. 启动调度器（非阻塞模式）
    print("\n⚙️  启动调度器...")
    scheduler.run(blocking=False)
    
    # 5. 等待所有任务完成
    print("\n⏳ 等待任务执行...")
    scheduler.wait_all()
    
    # 6. 查看统计信息
    print("\n" + "=" * 60)
    print("📊 执行统计")
    print("=" * 60)
    stats = scheduler.get_statistics()
    print(f"  总提交: {stats['total_submitted']}")
    print(f"  总执行: {stats['total_executed']}")
    print(f"  成功: {stats['total_success']}")
    print(f"  失败: {stats['total_failed']}")
    print(f"  平均等待时间: {stats['avg_wait_time']}")
    print(f"  平均执行时间: {stats['avg_execution_time']}")
    
    # 7. 查看任务状态
    print("\n" + "=" * 60)
    print("📋 任务状态")
    print("=" * 60)
    for tc in test_cases:
        status = scheduler.get_task_status(tc["id"])
        if status:
            print(f"  {tc['name']}: {status['status']}")
            if status.get('trace_id'):
                print(f"    Trace ID: {status['trace_id']}")
    
    # 8. 停止调度器
    scheduler.stop()
    print("\n✅ 调度器已停止")

if __name__ == "__main__":
    main()
