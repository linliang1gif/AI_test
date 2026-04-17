#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
断言引擎测试 - 验证所有断言类型
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from assertion.assertion_engine import AssertionEngine, AssertionType


def test_basic_assertions():
    """测试基础断言"""
    print("\n" + "=" * 70)
    print("1. 测试基础断言")
    print("=" * 70)
    
    engine = AssertionEngine()
    
    # 状态码断言
    engine.assert_status_code(200, 200)
    engine.assert_status_code(404, 200)
    engine.assert_status_code_in(200, [200, 201, 204])
    
    # 响应时间断言
    engine.assert_response_time(0.5, 1.0)
    engine.assert_response_time(2.0, 1.0)
    
    # 响应头断言
    headers = {"Content-Type": "application/json", "Authorization": "Bearer xxx"}
    engine.assert_header_exists(headers, "Content-Type")
    engine.assert_header_exists(headers, "X-Custom-Header")
    engine.assert_header_value(headers, "Content-Type", "application/json")
    
    engine.print_results()
    summary = engine.get_summary()
    
    print(f"\n✅ 基础断言测试完成")
    print(f"   通过: {summary['passed']}/{summary['total']}")
    
    return summary['passed'] >= 5


def test_response_body_assertions():
    """测试响应体断言"""
    print("\n" + "=" * 70)
    print("2. 测试响应体断言")
    print("=" * 70)
    
    engine = AssertionEngine()
    
    response_body = """
    {
        "code": 200,
        "message": "success",
        "data": {
            "user_id": 12345,
            "username": "test_user",
            "email": "test@example.com"
        }
    }
    """
    
    # 包含文本断言
    engine.assert_body_contains(response_body, "success")
    engine.assert_body_contains(response_body, "error")
    engine.assert_body_not_contains(response_body, "error")
    
    # 正则匹配断言
    engine.assert_body_matches_regex(response_body, r'"user_id":\s*\d+')
    engine.assert_body_matches_regex(response_body, r'"email":\s*"[^"]+@[^"]+"')
    
    engine.print_results()
    summary = engine.get_summary()
    
    print(f"\n✅ 响应体断言测试完成")
    print(f"   通过: {summary['passed']}/{summary['total']}")
    
    return summary['passed'] >= 3


def test_json_assertions():
    """测试JSON断言"""
    print("\n" + "=" * 70)
    print("3. 测试JSON断言")
    print("=" * 70)
    
    engine = AssertionEngine()
    
    json_data = {
        "code": 200,
        "message": "success",
        "data": {
            "user_id": 12345,
            "username": "test_user",
            "email": "test@example.com",
            "profile": {
                "age": 25,
                "city": "Beijing"
            }
        }
    }
    
    # JSON路径断言
    engine.assert_json_path_exists(json_data, "code")
    engine.assert_json_path_exists(json_data, "data.user_id")
    engine.assert_json_path_exists(json_data, "data.profile.city")
    engine.assert_json_path_exists(json_data, "data.nonexistent")
    
    # JSON路径值断言
    engine.assert_json_path_equals(json_data, "code", 200)
    engine.assert_json_path_equals(json_data, "data.username", "test_user")
    engine.assert_json_path_equals(json_data, "data.profile.age", 25)
    
    # JSON Schema断言
    schema = {
        "code": "number",
        "message": "string",
        "data": "object"
    }
    engine.assert_json_schema(json_data, schema)
    
    engine.print_results()
    summary = engine.get_summary()
    
    print(f"\n✅ JSON断言测试完成")
    print(f"   通过: {summary['passed']}/{summary['total']}")
    
    return summary['passed'] >= 6


def test_business_rule_assertions():
    """测试业务规则断言"""
    print("\n" + "=" * 70)
    print("4. 测试业务规则断言")
    print("=" * 70)
    
    engine = AssertionEngine()
    
    # 测试默认规则
    engine.assert_business_rule('valid_user_id', {'user_id': 12345})
    engine.assert_business_rule('valid_user_id', {'user_id': -1})
    engine.assert_business_rule('valid_user_id', {'user_id': 'abc'})
    
    engine.assert_business_rule('valid_order_amount', {'amount': 99.99})
    engine.assert_business_rule('valid_order_amount', {'amount': 0})
    
    engine.assert_business_rule('valid_email', {'email': 'test@example.com'})
    engine.assert_business_rule('valid_email', {'email': 'invalid-email'})
    
    # 注册自定义规则
    def rule_valid_age(data):
        age = data.get('age')
        if age is None:
            return False, "age不存在"
        if not isinstance(age, int) or age < 0 or age > 150:
            return False, f"age必须在0-150之间, 实际: {age}"
        return True, f"age有效: {age}"
    
    engine.register_business_rule('valid_age', rule_valid_age)
    engine.assert_business_rule('valid_age', {'age': 25})
    engine.assert_business_rule('valid_age', {'age': 200})
    
    engine.print_results()
    summary = engine.get_summary()
    
    print(f"\n✅ 业务规则断言测试完成")
    print(f"   通过: {summary['passed']}/{summary['total']}")
    
    return summary['passed'] >= 4


def test_ai_assertions():
    """测试AI智能断言"""
    print("\n" + "=" * 70)
    print("5. 测试AI智能断言")
    print("=" * 70)
    
    engine = AssertionEngine()
    
    # 成功响应
    success_response = {
        "code": 200,
        "message": "success",
        "data": {"result": "ok"}
    }
    engine.assert_with_ai(success_response, "返回成功状态")
    
    # 错误响应
    error_response = {
        "code": 500,
        "message": "error",
        "error": "Internal Server Error"
    }
    engine.assert_with_ai(error_response, "返回错误状态")
    
    engine.print_results()
    summary = engine.get_summary()
    
    print(f"\n✅ AI断言测试完成")
    print(f"   通过: {summary['passed']}/{summary['total']}")
    
    return summary['passed'] >= 1


def test_custom_assertions():
    """测试自定义断言"""
    print("\n" + "=" * 70)
    print("6. 测试自定义断言")
    print("=" * 70)
    
    engine = AssertionEngine()
    
    # 自定义条件
    user_age = 25
    engine.assert_custom(user_age >= 18, f"用户年龄 {user_age} 必须 >= 18")
    engine.assert_custom(user_age < 18, f"用户年龄 {user_age} 必须 < 18")
    
    # 复杂条件
    response_time = 0.5
    max_time = 1.0
    engine.assert_custom(
        response_time <= max_time,
        f"响应时间 {response_time}s 必须 <= {max_time}s"
    )
    
    engine.print_results()
    summary = engine.get_summary()
    
    print(f"\n✅ 自定义断言测试完成")
    print(f"   通过: {summary['passed']}/{summary['total']}")
    
    return summary['passed'] >= 2


def test_real_api_scenario():
    """测试真实API场景"""
    print("\n" + "=" * 70)
    print("7. 测试真实API场景")
    print("=" * 70)
    
    engine = AssertionEngine()
    
    # 模拟API响应
    api_response = {
        "status_code": 200,
        "headers": {
            "Content-Type": "application/json",
            "X-Request-ID": "abc123"
        },
        "body": {
            "code": 0,
            "message": "success",
            "data": {
                "order_id": "ORD-2024-001",
                "user_id": 12345,
                "amount": 299.99,
                "status": "paid",
                "created_at": "2024-01-01T10:00:00Z"
            }
        },
        "response_time": 0.35
    }
    
    # 综合断言
    engine.assert_status_code(api_response['status_code'], 200)
    engine.assert_response_time(api_response['response_time'], 1.0)
    engine.assert_header_exists(api_response['headers'], "Content-Type")
    
    body = api_response['body']
    engine.assert_json_path_equals(body, "code", 0)
    engine.assert_json_path_equals(body, "data.status", "paid")
    engine.assert_business_rule('valid_user_id', body['data'])
    engine.assert_business_rule('valid_order_amount', body['data'])
    
    engine.print_results()
    summary = engine.get_summary()
    
    print(f"\n✅ 真实API场景测试完成")
    print(f"   通过: {summary['passed']}/{summary['total']}")
    
    return summary['all_passed']


def main():
    """主测试函数"""
    print("\n" + "=" * 70)
    print("断言引擎完整测试")
    print("=" * 70)
    
    results = []
    
    # 运行所有测试
    results.append(("基础断言", test_basic_assertions()))
    results.append(("响应体断言", test_response_body_assertions()))
    results.append(("JSON断言", test_json_assertions()))
    results.append(("业务规则断言", test_business_rule_assertions()))
    results.append(("AI断言", test_ai_assertions()))
    results.append(("自定义断言", test_custom_assertions()))
    results.append(("真实API场景", test_real_api_scenario()))
    
    # 汇总结果
    print("\n" + "=" * 70)
    print("测试汇总")
    print("=" * 70)
    
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {name}")
    
    total = len(results)
    passed = sum(1 for _, p in results if p)
    
    print("\n" + "-" * 70)
    print(f"总计: {total}")
    print(f"通过: {passed} ✅")
    print(f"失败: {total - passed} ❌")
    print(f"通过率: {passed / total:.1%}")
    print("=" * 70)
    
    if passed == total:
        print("\n🎉 所有测试通过! 断言引擎工作正常!")
        return 0
    else:
        print(f"\n⚠️ {total - passed} 个测试失败,请检查!")
        return 1


if __name__ == "__main__":
    exit(main())
