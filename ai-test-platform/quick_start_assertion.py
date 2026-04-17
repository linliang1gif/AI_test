#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
断言系统快速启动演示
展示断言系统的核心功能
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from assertion import (
    AssertionBuilder,
    AssertionValidator,
    AIAssertionGenerator,
    AssertionKnowledgeIntegration,
    quick_assertions
)


def demo_quick_start():
    """演示1: 快速开始"""
    print("\n" + "=" * 70)
    print("演示1: 快速开始 - 使用快捷断言")
    print("=" * 70)
    
    # 创建标准断言
    configs = quick_assertions().build()
    print(f"\n✅ 创建了 {len(configs)} 个标准断言")
    
    # 模拟API响应
    response_data = {
        'status_code': 200,
        'response_time': 0.5,
        'body': {
            'code': 0,
            'message': 'success',
            'data': {
                'user_id': 12345,
                'username': 'test_user',
                'email': 'test@example.com'
            }
        }
    }
    
    # 验证
    validator = AssertionValidator()
    results = validator.validate_all(configs, response_data)
    
    # 打印结果
    print("\n验证结果:")
    for result in results:
        status = "✅" if result.passed else "❌"
        print(f"  {status} {result.message}")
    
    summary = validator.get_summary()
    print(f"\n通过率: {summary['pass_rate']:.1%}")


def demo_custom_assertions():
    """演示2: 自定义断言"""
    print("\n" + "=" * 70)
    print("演示2: 自定义断言 - 流式API")
    print("=" * 70)
    
    # 使用流式API构建断言
    builder = AssertionBuilder()
    configs = (builder
        .new_assertion("状态码200")
        .equals(200)
        .at_path("status_code")
        .blocker()
        
        .new_assertion("响应时间<1秒")
        .less_than(1.0)
        .at_path("response_time")
        .major()
        
        .new_assertion("用户ID>0")
        .greater_than(0)
        .at_path("body.data.user_id")
        .critical()
        
        .new_assertion("邮箱格式正确")
        .matches(r'^[\w\.-]+@[\w\.-]+\.\w+$')
        .at_path("body.data.email")
        .major()
        
        .build())
    
    print(f"\n✅ 构建了 {len(configs)} 个自定义断言:")
    for config in configs:
        print(f"  - {config.name} [{config.severity.value}]")
    
    # 验证
    response_data = {
        'status_code': 200,
        'response_time': 0.3,
        'body': {
            'data': {
                'user_id': 12345,
                'email': 'test@example.com'
            }
        }
    }
    
    validator = AssertionValidator()
    results = validator.validate_all(configs, response_data)
    
    print("\n验证结果:")
    for result in results:
        status = "✅" if result.passed else "❌"
        print(f"  {status} {result.message}")


def demo_ai_generation():
    """演示3: AI生成断言"""
    print("\n" + "=" * 70)
    print("演示3: AI生成断言")
    print("=" * 70)
    
    generator = AIAssertionGenerator()
    
    # 从API规范生成
    api_spec = {
        'endpoint': '/api/login',
        'method': 'POST',
        'description': '用户登录接口',
        'response_schema': {
            'properties': {
                'code': {'type': 'number'},
                'data': {
                    'properties': {
                        'token': {'type': 'string'},
                        'user_id': {'type': 'number'}
                    },
                    'required': ['token', 'user_id']
                }
            }
        }
    }
    
    assertions = generator.generate_from_api_spec(api_spec)
    
    print(f"\n✅ 从API规范生成了 {len(assertions)} 个断言:")
    for assertion in assertions:
        print(f"  - {assertion.name}")
    
    # 验证
    response_data = {
        'status_code': 200,
        'response_time': 0.2,
        'body': {
            'code': 0,
            'data': {
                'token': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...',
                'user_id': 12345
            }
        }
    }
    
    validator = AssertionValidator()
    results = validator.validate_all(assertions, response_data)
    
    summary = validator.get_summary()
    print(f"\n验证完成: {summary['passed']}/{summary['total']} 通过")


def demo_knowledge_integration():
    """演示4: 知识库集成"""
    print("\n" + "=" * 70)
    print("演示4: 知识库集成")
    print("=" * 70)
    
    integration = AssertionKnowledgeIntegration()
    
    # 创建断言
    configs = quick_assertions().build()
    
    # 模拟多次测试
    test_scenarios = [
        {
            'name': '成功场景1',
            'data': {
                'status_code': 200,
                'response_time': 0.3,
                'body': {'code': 0, 'data': {'user_id': 123}}
            }
        },
        {
            'name': '成功场景2',
            'data': {
                'status_code': 200,
                'response_time': 0.5,
                'body': {'code': 0, 'data': {'user_id': 456}}
            }
        },
        {
            'name': '失败场景',
            'data': {
                'status_code': 500,
                'response_time': 2.0,
                'body': {'code': -1, 'error': 'Server Error'}
            }
        }
    ]
    
    print("\n执行测试并记录到知识库...")
    for scenario in test_scenarios:
        validator = AssertionValidator()
        results = validator.validate_all(configs, scenario['data'])
        
        for config, result in zip(configs, results):
            integration.record_assertion_result(
                config, result,
                context={'scenario': scenario['name']}
            )
    
    # 获取统计
    stats = integration.get_assertion_statistics()
    print(f"\n✅ 知识库统计:")
    print(f"  总计: {stats['total']}")
    print(f"  通过: {stats['passed']}")
    print(f"  失败: {stats['failed']}")
    print(f"  通过率: {stats['pass_rate']:.1%}")
    
    print(f"\n按断言统计:")
    for name, assertion_stats in list(stats['by_assertion'].items())[:3]:
        print(f"  {name}:")
        print(f"    通过率: {assertion_stats['pass_rate']:.1%}")


def demo_complete_workflow():
    """演示5: 完整工作流"""
    print("\n" + "=" * 70)
    print("演示5: 完整工作流")
    print("=" * 70)
    
    print("\n步骤1: AI生成断言")
    generator = AIAssertionGenerator()
    api_spec = {
        'endpoint': '/api/users',
        'method': 'GET',
        'description': '获取用户列表'
    }
    configs = generator.generate_from_api_spec(api_spec)
    print(f"  ✅ 生成了 {len(configs)} 个断言")
    
    print("\n步骤2: 执行验证")
    response_data = {
        'status_code': 200,
        'response_time': 0.4,
        'body': {
            'code': 0,
            'data': [
                {'id': 1, 'name': 'User1'},
                {'id': 2, 'name': 'User2'}
            ]
        }
    }
    
    validator = AssertionValidator()
    results = validator.validate_all(configs, response_data)
    summary = validator.get_summary()
    print(f"  ✅ 验证完成: {summary['passed']}/{summary['total']} 通过")
    
    print("\n步骤3: 记录到知识库")
    integration = AssertionKnowledgeIntegration()
    for config, result in zip(configs, results):
        integration.record_assertion_result(
            config, result,
            context={'api': '/api/users'}
        )
    print(f"  ✅ 已记录 {len(results)} 条结果")
    
    print("\n步骤4: 获取统计")
    stats = integration.get_assertion_statistics()
    print(f"  ✅ 通过率: {stats['pass_rate']:.1%}")
    
    print("\n✅ 完整工作流演示完成!")


def main():
    """主函数"""
    print("\n" + "=" * 70)
    print("断言系统快速启动演示")
    print("=" * 70)
    
    try:
        # 运行所有演示
        demo_quick_start()
        demo_custom_assertions()
        demo_ai_generation()
        demo_knowledge_integration()
        demo_complete_workflow()
        
        # 总结
        print("\n" + "=" * 70)
        print("演示总结")
        print("=" * 70)
        print("\n✅ 所有演示完成!")
        print("\n核心功能:")
        print("  1. ✅ 快捷断言 - 一行代码创建标准断言")
        print("  2. ✅ 自定义断言 - 流式API灵活构建")
        print("  3. ✅ AI生成 - 智能生成断言")
        print("  4. ✅ 知识库集成 - 自动学习和统计")
        print("  5. ✅ 完整工作流 - 端到端支持")
        
        print("\n下一步:")
        print("  - 查看使用指南: assertion/使用指南.md")
        print("  - 运行完整测试: py test_enhanced_assertion_system.py")
        print("  - 查看完成报告: P1.1_断言引擎增强完成报告.md")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ 演示执行出错: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
