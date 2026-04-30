#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
P0-4 成功路径验证
使用httpbin.org公开API验证passed链路
"""

import sys
from pathlib import Path
from datetime import datetime

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core import TestCase, create_test_case
from database import get_db
from services.execution_orchestrator import ExecutionOrchestrator
from modules.executor import ExecutionEngine


def create_httpbin_test_cases():
    """创建使用httpbin.org的测试用例"""
    test_cases = []
    
    # 成功用例1: GET请求
    tc1 = create_test_case(
        id="TC_HTTPBIN_GET_001",
        title="httpbin GET请求测试",
        module="httpbin",
        priority="high",
        steps=[
            {"action": "发送GET请求", "endpoint": "/get", "method": "GET"}
        ],
        expected="返回200状态码",
        data_type="valid",
        expected_behavior="success",
        execution_config={
            "method": "GET",
            "url": "https://httpbin.org/get",
            "headers": {"User-Agent": "AI-Test-Platform/1.0"},
            "params": {"test": "success"}
        },
        assertions=[
            {"type": "status_code", "expected": 200}
        ]
    )
    test_cases.append(tc1)
    
    # 成功用例2: POST请求
    tc2 = create_test_case(
        id="TC_HTTPBIN_POST_001",
        title="httpbin POST请求测试",
        module="httpbin",
        priority="high",
        steps=[
            {"action": "发送POST请求", "endpoint": "/post", "method": "POST"}
        ],
        expected="返回200状态码",
        data_type="valid",
        expected_behavior="success",
        execution_config={
            "method": "POST",
            "url": "https://httpbin.org/post",
            "headers": {"Content-Type": "application/json"},
            "json": {"name": "test", "value": "success"}
        },
        assertions=[
            {"type": "status_code", "expected": 200}
        ]
    )
    test_cases.append(tc2)
    
    # 失败用例: 404错误
    tc3 = create_test_case(
        id="TC_HTTPBIN_404_001",
        title="httpbin 404错误测试",
        module="httpbin",
        priority="medium",
        steps=[
            {"action": "访问不存在的路径", "endpoint": "/status/404", "method": "GET"}
        ],
        expected="返回404状态码",
        data_type="invalid",
        expected_behavior="client_error",
        execution_config={
            "method": "GET",
            "url": "https://httpbin.org/status/404"
        },
        assertions=[
            {"type": "status_code", "expected": 404}
        ]
    )
    test_cases.append(tc3)
    
    # 失败用例2: 期望200但实际404
    tc4 = create_test_case(
        id="TC_HTTPBIN_FAIL_001",
        title="httpbin 失败测试 - 期望200实际404",
        module="httpbin",
        priority="medium",
        steps=[
            {"action": "访问不存在的路径但期望200", "endpoint": "/status/404", "method": "GET"}
        ],
        expected="返回200状态码(但实际会404)",
        data_type="invalid",
        expected_behavior="success",
        execution_config={
            "method": "GET",
            "url": "https://httpbin.org/status/404"
        },
        assertions=[
            {"type": "status_code", "expected": 200}  # 期望200但实际404,会失败
        ]
    )
    test_cases.append(tc4)
    
    return test_cases


def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("P0-4 成功路径验证")
    print("=" * 60 + "\n")
    
    # 1. 创建测试用例
    print("📝 [1/4] 创建测试用例...")
    test_cases = create_httpbin_test_cases()
    print(f"✅ 创建了 {len(test_cases)} 个测试用例")
    for tc in test_cases:
        print(f"  - {tc.id}: {tc.title}")
    print()
    
    # 2. 初始化数据库
    print("📊 [2/4] 初始化数据库...")
    db = next(get_db())
    print("✅ 数据库连接成功")
    print()
    
    # 3. 执行测试
    print("🚀 [3/4] 执行测试...")
    try:
        execution_engine = ExecutionEngine()
        orchestrator = ExecutionOrchestrator(db, execution_engine)
        
        result = orchestrator.execute_test_cases(
            test_cases=test_cases,
            project_id=1,
            environment_id=1,
            trigger_type='manual',
            created_by='test_user',
            max_workers=1,
            parallel=False
        )
        
        print(f"\n✅ 执行完成")
        print(f"  Run ID: {result['run_id']}")
        print(f"  Trace ID: {result.get('trace_id', 'N/A')}")
        print(f"  最终状态: {result['status']}")
        print(f"  统计: {result['statistics']}")
        print()
        
        # 4. 验证结果
        print("🔍 [4/4] 验证结果...")
        stats = result['statistics']
        
        # 验证成功路径
        if stats['passed'] > 0:
            print(f"✅ 成功路径验证通过: {stats['passed']}个用例passed")
        else:
            print(f"❌ 成功路径验证失败: 0个用例passed")
            return False
        
        # 验证失败路径
        if stats['failed'] > 0:
            print(f"✅ 失败路径验证通过: {stats['failed']}个用例failed")
        else:
            print(f"⚠️  失败路径未验证: 0个用例failed")
        
        # 验证总数
        if stats['total'] == len(test_cases):
            print(f"✅ 总数验证通过: {stats['total']}/{len(test_cases)}")
        else:
            print(f"❌ 总数验证失败: {stats['total']}/{len(test_cases)}")
            return False
        
        print()
        print("=" * 60)
        print("🎉 P0-4 成功路径验证完成")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ 执行失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
