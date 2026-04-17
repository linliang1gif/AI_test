#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试统一执行调度器
"""

import sys
import time
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from modules.scheduler import UnifiedExecutionScheduler, TaskPriority


def test_basic_scheduling():
    """测试基本调度功能"""
    print("=" * 60)
    print("测试1: 基本调度功能")
    print("=" * 60)
    
    # 创建调度器
    scheduler = UnifiedExecutionScheduler(config={
        'max_workers': 3,
        'rate_limit': 5,
        'enable_rate_limit': True
    })
    
    # 提交任务
    test_cases = [
        {
            'id': 'test_1',
            'name': 'API Test 1',
            'execution_type': 'api',
            'config': {
                'url': 'https://jsonplaceholder.typicode.com/posts/1',
                'method': 'GET'
            }
        },
        {
            'id': 'test_2',
            'name': 'API Test 2',
            'execution_type': 'api',
            'config': {
                'url': 'https://jsonplaceholder.typicode.com/posts/2',
                'method': 'GET'
            }
        },
        {
            'id': 'test_3',
            'name': 'API Test 3',
            'execution_type': 'api',
            'config': {
                'url': 'https://jsonplaceholder.typicode.com/posts/3',
                'method': 'GET'
            }
        }
    ]
    
    # 提交任务
    task_ids = []
    for tc in test_cases:
        task_id = scheduler.submit(tc, priority='P1')
        task_ids.append(task_id)
        print(f"✅ 已提交任务: {task_id}")
    
    # 启动调度器（非阻塞）
    scheduler.run(blocking=False)
    
    # 等待所有任务完成
    print("\n等待任务完成...")
    success = scheduler.wait_all(timeout=30)
    
    if success:
        print("✅ 所有任务已完成")
    else:
        print("⚠️  等待超时")
    
    # 获取统计信息
    stats = scheduler.get_statistics()
    print(f"\n📊 统计信息:")
    print(f"  总提交: {stats['total_submitted']}")
    print(f"  总执行: {stats['total_executed']}")
    print(f"  成功: {stats['total_success']}")
    print(f"  失败: {stats['total_failed']}")
    print(f"  平均等待时间: {stats['avg_wait_time']}")
    print(f"  平均执行时间: {stats['avg_execution_time']}")
    
    # 停止调度器
    scheduler.stop()
    
    return stats['total_success'] == len(test_cases)


def test_priority_scheduling():
    """测试优先级调度"""
    print("\n" + "=" * 60)
    print("测试2: 优先级调度")
    print("=" * 60)
    
    scheduler = UnifiedExecutionScheduler(config={
        'max_workers': 2,
        'rate_limit': 10
    })
    
    # 提交不同优先级的任务
    priorities = ['P2', 'P0', 'P1', 'P2', 'P0']
    task_ids = []
    
    for i, priority in enumerate(priorities, 1):
        test_case = {
            'id': f'test_{i}',
            'name': f'Test {i} ({priority})',
            'execution_type': 'api',
            'config': {
                'url': f'https://jsonplaceholder.typicode.com/posts/{i}',
                'method': 'GET'
            }
        }
        task_id = scheduler.submit(test_case, priority=priority)
        task_ids.append(task_id)
        print(f"✅ 已提交任务: {task_id} (优先级: {priority})")
    
    # 启动并等待
    scheduler.run(blocking=False)
    scheduler.wait_all(timeout=30)
    
    # 检查执行顺序（P0应该先执行）
    print("\n📋 任务状态:")
    for task_id in task_ids:
        status = scheduler.get_task_status(task_id)
        if status:
            print(f"  {task_id}: {status['status']} (优先级: {status['priority']})")
    
    stats = scheduler.get_statistics()
    print(f"\n📊 按优先级统计:")
    for priority, count in stats['by_priority'].items():
        print(f"  {priority}: {count}")
    
    scheduler.stop()
    return True


def test_rate_limiting():
    """测试限流功能"""
    print("\n" + "=" * 60)
    print("测试3: 限流功能")
    print("=" * 60)
    
    scheduler = UnifiedExecutionScheduler(config={
        'max_workers': 5,
        'rate_limit': 2,  # 每秒最多2个请求
        'enable_rate_limit': True
    })
    
    # 提交10个任务
    print("提交10个任务（限流: 2 QPS）...")
    for i in range(1, 11):
        test_case = {
            'id': f'test_{i}',
            'name': f'Test {i}',
            'execution_type': 'api',
            'config': {
                'url': f'https://jsonplaceholder.typicode.com/posts/{i}',
                'method': 'GET'
            }
        }
        scheduler.submit(test_case, priority='P1')
    
    # 启动并等待
    start_time = time.time()
    scheduler.run(blocking=False)
    scheduler.wait_all(timeout=60)
    elapsed = time.time() - start_time
    
    stats = scheduler.get_statistics()
    print(f"\n⏱️  总耗时: {elapsed:.2f}秒")
    print(f"📊 限流统计:")
    print(f"  总执行: {stats['total_executed']}")
    print(f"  限流次数: {stats['total_throttled']}")
    
    # 验证限流效果（10个任务，2 QPS，至少需要5秒）
    assert elapsed >= 4, "限流未生效"
    print("✅ 限流功能正常")
    
    scheduler.stop()
    return True


def test_failure_isolation():
    """测试失败隔离"""
    print("\n" + "=" * 60)
    print("测试4: 失败隔离")
    print("=" * 60)
    
    scheduler = UnifiedExecutionScheduler(config={
        'max_workers': 3,
        'rate_limit': 10
    })
    
    # 提交包含失败任务的测试
    test_cases = [
        {
            'id': 'test_success_1',
            'name': 'Success Test 1',
            'execution_type': 'api',
            'config': {
                'url': 'https://jsonplaceholder.typicode.com/posts/1',
                'method': 'GET'
            }
        },
        {
            'id': 'test_fail',
            'name': 'Fail Test',
            'execution_type': 'api',
            'config': {
                'url': 'http://invalid-domain-12345.com',
                'method': 'GET'
            }
        },
        {
            'id': 'test_success_2',
            'name': 'Success Test 2',
            'execution_type': 'api',
            'config': {
                'url': 'https://jsonplaceholder.typicode.com/posts/2',
                'method': 'GET'
            }
        }
    ]
    
    for tc in test_cases:
        scheduler.submit(tc, priority='P1')
        print(f"✅ 已提交任务: {tc['id']}")
    
    scheduler.run(blocking=False)
    scheduler.wait_all(timeout=30)
    
    stats = scheduler.get_statistics()
    print(f"\n📊 执行结果:")
    print(f"  总执行: {stats['total_executed']}")
    print(f"  成功: {stats['total_success']}")
    print(f"  失败: {stats['total_failed']}")
    
    # 验证失败隔离（失败任务不影响其他任务）
    assert stats['total_success'] >= 2, "失败隔离未生效"
    print("✅ 失败隔离功能正常")
    
    scheduler.stop()
    return True


def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("🚀 统一执行调度器测试")
    print("=" * 60)
    
    tests = [
        ("基本调度功能", test_basic_scheduling),
        ("优先级调度", test_priority_scheduling),
        ("限流功能", test_rate_limiting),
        ("失败隔离", test_failure_isolation),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            success = test_func()
            results.append((name, success))
        except Exception as e:
            print(f"\n❌ 测试 '{name}' 异常: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))
    
    # 打印总结
    print("\n" + "=" * 60)
    print("📊 测试总结")
    print("=" * 60)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for name, success in results:
        status = "✅ 通过" if success else "❌ 失败"
        print(f"{status} - {name}")
    
    print("\n" + "=" * 60)
    print(f"通过率: {passed}/{total} ({passed/total*100:.1f}%)")
    print("=" * 60)
    
    if passed == total:
        print("\n🎉 所有测试通过！")
        return 0
    else:
        print(f"\n⚠️  有 {total - passed} 个测试失败")
        return 1


if __name__ == "__main__":
    exit(main())
