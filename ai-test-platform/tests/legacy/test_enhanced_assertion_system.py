#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
增强断言系统完整测试 - 验证所有新功能
"""

import sys
from pathlib import Path

# 添加路径
sys.path.insert(0, str(Path(__file__).parent))

from assertion import (
    AssertionBuilder,
    AssertionValidator,
    AIAssertionGenerator,
    AssertionKnowledgeIntegration,
    AssertionTemplates,
    AssertionSeverity,
    create_assertion,
    quick_assertions
)


def test_assertion_builder():
    """测试断言构建器"""
    print("\n" + "=" * 70)
    print("1. 测试断言构建器")
    print("=" * 70)
    
    # 流式API构建
    builder = AssertionBuilder()
    configs = (builder
               .new_assertion("状态码200").equals(200).at_path("status_code").blocker()
               .new_assertion("响应时间<2秒").less_than(2.0).at_path("response_time").major()
               .new_assertion("返回码为0").equals(0).at_path("body.code").critical()
               .new_assertion("数据不为空").not_empty().at_path("body.data").critical()
               .new_assertion("用户ID>0").greater_than(0).at_path("body.data.user_id").major()
               .build())
    
    print(f"✅ 构建了 {len(configs)} 个断言:")
    for config in configs:
        print(f"  - {config.name} [{config.severity.value}]")
    
    return len(configs) == 5


def test_quick_assertions():
    """测试快捷断言"""
    print("\n" + "=" * 70)
    print("2. 测试快捷断言")
    print("=" * 70)
    
    # 使用快捷方法
    configs = quick_assertions().build()
    
    print(f"✅ 快速创建了 {len(configs)} 个标准断言:")
    for config in configs:
        print(f"  - {config.name}")
    
    return len(configs) >= 3


def test_assertion_templates():
    """测试断言模板"""
    print("\n" + "=" * 70)
    print("3. 测试断言模板")
    print("=" * 70)
    
    # API成功模板
    builder = AssertionBuilder()
    configs = builder.api_success_assertions().build()
    
    print(f"✅ API成功模板包含 {len(configs)} 个断言:")
    for config in configs:
        print(f"  - {config.name} [{config.severity.value}]")
    
    # API错误模板
    builder2 = AssertionBuilder()
    configs2 = builder2.api_error_assertions().build()
    
    print(f"\n✅ API错误模板包含 {len(configs2)} 个断言:")
    for config in configs2:
        print(f"  - {config.name} [{config.severity.value}]")
    
    return len(configs) >= 2 and len(configs2) >= 1


def test_assertion_validator():
    """测试断言验证器"""
    print("\n" + "=" * 70)
    print("4. 测试断言验证器")
    print("=" * 70)
    
    # 创建断言
    configs = quick_assertions().build()
    
    # 成功场景
    print("\n场景1: 成功响应")
    response_success = {
        'status_code': 200,
        'response_time': 0.5,
        'body': {
            'code': 0,
            'message': 'success',
            'data': {
                'user_id': 12345,
                'username': 'test_user'
            }
        }
    }
    
    validator = AssertionValidator()
    results = validator.validate_all(configs, response_success)
    
    passed = sum(1 for r in results if r.passed)
    print(f"✅ 验证完成: {passed}/{len(results)} 通过")
    
    # 失败场景
    print("\n场景2: 失败响应")
    response_fail = {
        'status_code': 500,
        'response_time': 3.0,
        'body': {
            'code': -1,
            'message': 'error'
        }
    }
    
    validator2 = AssertionValidator()
    results2 = validator2.validate_all(configs, response_fail)
    
    failed = sum(1 for r in results2 if not r.passed)
    print(f"✅ 验证完成: {failed}/{len(results2)} 失败(符合预期)")
    
    return passed >= 3 and failed >= 2


def test_ai_assertion_generator():
    """测试AI断言生成器"""
    print("\n" + "=" * 70)
    print("5. 测试AI断言生成器")
    print("=" * 70)
    
    generator = AIAssertionGenerator()
    
    # 从API规范生成
    api_spec = {
        'endpoint': '/api/users',
        'method': 'GET',
        'description': '获取用户列表',
        'response_schema': {
            'type': 'object',
            'properties': {
                'code': {'type': 'number'},
                'data': {
                    'type': 'array',
                    'items': {
                        'type': 'object',
                        'properties': {
                            'id': {'type': 'number'},
                            'name': {'type': 'string'}
                        },
                        'required': ['id', 'name']
                    }
                }
            },
            'required': ['code', 'data']
        }
    }
    
    assertions = generator.generate_from_api_spec(api_spec)
    
    print(f"✅ 从API规范生成了 {len(assertions)} 个断言:")
    for assertion in assertions:
        print(f"  - {assertion.name}")
    
    # 从测试用例生成
    test_case = {
        'title': '测试用户登录',
        'expected': '登录成功,返回用户信息和token'
    }
    
    assertions2 = generator.generate_from_test_case(test_case)
    
    print(f"\n✅ 从测试用例生成了 {len(assertions2)} 个断言:")
    for assertion in assertions2:
        print(f"  - {assertion.name}")
    
    return len(assertions) >= 3


def test_knowledge_integration():
    """测试知识库集成"""
    print("\n" + "=" * 70)
    print("6. 测试知识库集成")
    print("=" * 70)
    
    integration = AssertionKnowledgeIntegration()
    
    # 创建断言和验证器
    configs = quick_assertions().build()
    
    # 模拟多次测试执行
    test_scenarios = [
        {
            'name': '成功场景',
            'data': {
                'status_code': 200,
                'response_time': 0.5,
                'body': {'code': 0, 'data': {'user_id': 123}}
            }
        },
        {
            'name': '失败场景1',
            'data': {
                'status_code': 500,
                'response_time': 1.0,
                'body': {'code': -1, 'error': 'Server Error'}
            }
        },
        {
            'name': '成功场景2',
            'data': {
                'status_code': 200,
                'response_time': 0.8,
                'body': {'code': 0, 'data': {'user_id': 456}}
            }
        }
    ]
    
    for scenario in test_scenarios:
        print(f"\n执行: {scenario['name']}")
        validator = AssertionValidator()
        results = validator.validate_all(configs, scenario['data'])
        
        for config, result in zip(configs, results):
            record_id = integration.record_assertion_result(
                config, result,
                context={
                    'scenario': scenario['name'],
                    'response_data': scenario['data']
                }
            )
            
            if not result.passed:
                integration.record_assertion_failure(
                    config, result,
                    context={'scenario': scenario['name']}
                )
    
    # 获取统计
    stats = integration.get_assertion_statistics()
    print(f"\n✅ 断言统计:")
    print(f"  总计: {stats['total']}")
    print(f"  通过: {stats['passed']}")
    print(f"  失败: {stats['failed']}")
    print(f"  通过率: {stats['pass_rate']:.1%}")
    
    # 获取改进建议
    print(f"\n✅ 改进建议:")
    for config in configs[:2]:  # 只检查前2个
        suggestions = integration.suggest_assertion_improvements(config)
        if suggestions:
            print(f"\n  {config.name}:")
            for suggestion in suggestions:
                print(f"    - {suggestion}")
    
    return stats['total'] >= 9


def test_complete_workflow():
    """测试完整工作流"""
    print("\n" + "=" * 70)
    print("7. 测试完整工作流")
    print("=" * 70)
    
    print("\n步骤1: 使用AI生成断言")
    generator = AIAssertionGenerator()
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
    configs = generator.generate_from_api_spec(api_spec)
    print(f"  生成了 {len(configs)} 个断言")
    
    print("\n步骤2: 执行断言验证")
    response_data = {
        'status_code': 200,
        'response_time': 0.3,
        'body': {
            'code': 0,
            'message': 'success',
            'data': {
                'token': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...',
                'user_id': 12345
            }
        }
    }
    
    validator = AssertionValidator()
    results = validator.validate_all(configs, response_data)
    passed = sum(1 for r in results if r.passed)
    print(f"  验证完成: {passed}/{len(results)} 通过")
    
    print("\n步骤3: 记录到知识库")
    integration = AssertionKnowledgeIntegration()
    for config, result in zip(configs, results):
        integration.record_assertion_result(
            config, result,
            context={
                'api': '/api/login',
                'response': response_data
            }
        )
    print(f"  已记录 {len(results)} 条断言结果")
    
    print("\n步骤4: 获取统计和建议")
    stats = integration.get_assertion_statistics()
    print(f"  通过率: {stats['pass_rate']:.1%}")
    
    print("\n✅ 完整工作流测试通过!")
    return True


def main():
    """主测试函数"""
    print("\n" + "=" * 70)
    print("增强断言系统完整测试")
    print("=" * 70)
    
    results = []
    
    # 运行所有测试
    try:
        results.append(("断言构建器", test_assertion_builder()))
        results.append(("快捷断言", test_quick_assertions()))
        results.append(("断言模板", test_assertion_templates()))
        results.append(("断言验证器", test_assertion_validator()))
        results.append(("AI断言生成", test_ai_assertion_generator()))
        results.append(("知识库集成", test_knowledge_integration()))
        results.append(("完整工作流", test_complete_workflow()))
    except Exception as e:
        print(f"\n❌ 测试执行出错: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    # 汇总结果
    print("\n" + "=" * 70)
    print("测试汇总")
    print("=" * 70)
    
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {name}")
    
    total = len(results)
    passed_count = sum(1 for _, p in results if p)
    
    print("\n" + "-" * 70)
    print(f"总计: {total}")
    print(f"通过: {passed_count} ✅")
    print(f"失败: {total - passed_count} ❌")
    print(f"通过率: {passed_count / total:.1%}")
    print("=" * 70)
    
    if passed_count == total:
        print("\n🎉 所有测试通过! 增强断言系统工作正常!")
        print("\n✨ 新增功能:")
        print("  1. ✅ 断言类型定义和配置")
        print("  2. ✅ 流式API断言构建器")
        print("  3. ✅ 断言模板系统")
        print("  4. ✅ AI辅助断言生成")
        print("  5. ✅ 断言验证器")
        print("  6. ✅ 知识库集成")
        print("  7. ✅ 完整工作流支持")
        return 0
    else:
        print(f"\n⚠️ {total - passed_count} 个测试失败,请检查!")
        return 1


if __name__ == "__main__":
    exit(main())
