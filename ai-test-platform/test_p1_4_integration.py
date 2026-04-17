#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
P1.4 测试数据工厂集成测试
验证所有集成功能是否正常工作
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_api_explorer_integration():
    """测试1: API Explorer + 测试数据工厂集成"""
    print("\n" + "="*60)
    print("测试1: API Explorer + 测试数据工厂集成")
    print("="*60)
    
    # 模拟API参数schema
    api_schema = {
        "user_name": "string",
        "user_email": "string",
        "user_age": "integer",
        "user_phone": "string"
    }
    
    # 调用智能对象生成
    response = requests.post(
        f"{BASE_URL}/api/test-data/smart-object",
        json={
            "data_schema": api_schema,
            "context": {
                "api_path": "/api/users",
                "api_method": "POST"
            }
        }
    )
    
    print(f"状态码: {response.status_code}")
    result = response.json()
    print(f"响应: {json.dumps(result, indent=2, ensure_ascii=False)}")
    
    if result.get('success'):
        print("✅ API Explorer集成测试通过")
        print(f"生成的数据: {json.dumps(result['data'], indent=2, ensure_ascii=False)}")
        return True
    else:
        print("❌ API Explorer集成测试失败")
        return False

def test_batch_data_generation():
    """测试2: 批量数据生成"""
    print("\n" + "="*60)
    print("测试2: 批量数据生成")
    print("="*60)
    
    # 批量生成用户数据
    response = requests.post(
        f"{BASE_URL}/api/test-data/generate",
        json={
            "data_type": "user",
            "count": 5
        }
    )
    
    print(f"状态码: {response.status_code}")
    result = response.json()
    
    if result.get('success'):
        print(f"✅ 成功生成 {result['count']} 条数据")
        print(f"数据示例: {json.dumps(result['data'][0], indent=2, ensure_ascii=False)}")
        return True
    else:
        print("❌ 批量数据生成失败")
        return False

def test_scenario_suggestions():
    """测试3: 测试场景建议"""
    print("\n" + "="*60)
    print("测试3: 测试场景建议")
    print("="*60)
    
    # 获取用户相关的测试场景
    response = requests.get(f"{BASE_URL}/api/test-data/scenarios/user")
    
    print(f"状态码: {response.status_code}")
    result = response.json()
    
    if result.get('success'):
        print(f"✅ 获取到 {result['count']} 个测试场景")
        for scenario in result['scenarios'][:3]:
            print(f"  - {scenario['name']} ({scenario['type']}, {scenario['priority']})")
        return True
    else:
        print("❌ 测试场景获取失败")
        return False

def test_quality_evaluation():
    """测试4: 数据质量评估"""
    print("\n" + "="*60)
    print("测试4: 数据质量评估")
    print("="*60)
    
    # 评估数据质量
    test_data = {
        "user_id": "12345",
        "email": "test@example.com",
        "age": 25,
        "phone": "13800138000"
    }
    
    response = requests.post(
        f"{BASE_URL}/api/test-data/evaluate",
        json={"data": test_data}
    )
    
    print(f"状态码: {response.status_code}")
    result = response.json()
    
    if result.get('success'):
        evaluation = result['evaluation']
        print(f"✅ 数据质量评估完成")
        print(f"  总分: {evaluation['overall_score']}")
        print(f"  等级: {evaluation['grade']}")
        print(f"  完整性: {evaluation['completeness']}")
        print(f"  有效性: {evaluation['validity']}")
        return True
    else:
        print("❌ 数据质量评估失败")
        return False

def test_boundary_values():
    """测试5: 边界值生成"""
    print("\n" + "="*60)
    print("测试5: 边界值生成")
    print("="*60)
    
    # 获取整数边界值
    response = requests.get(
        f"{BASE_URL}/api/test-data/boundary-values/integer",
        params={"min_value": 0, "max_value": 100}
    )
    
    print(f"状态码: {response.status_code}")
    result = response.json()
    
    if result.get('success'):
        print(f"✅ 生成 {result['count']} 个边界值")
        print(f"  边界值: {result['values']}")
        return True
    else:
        print("❌ 边界值生成失败")
        return False

def test_invalid_values():
    """测试6: 非法值生成"""
    print("\n" + "="*60)
    print("测试6: 非法值生成")
    print("="*60)
    
    # 获取邮箱非法值
    response = requests.get(f"{BASE_URL}/api/test-data/invalid-values/email")
    
    print(f"状态码: {response.status_code}")
    result = response.json()
    
    if result.get('success'):
        print(f"✅ 生成 {result['count']} 个非法值")
        print(f"  非法值示例: {result['values'][:5]}")
        return True
    else:
        print("❌ 非法值生成失败")
        return False

def main():
    """运行所有集成测试"""
    print("=" * 60)
    print("🧪 P1.4 测试数据工厂集成测试")
    print("=" * 60)
    print(f"后端地址: {BASE_URL}")
    print()
    
    tests = [
        ("API Explorer集成", test_api_explorer_integration),
        ("批量数据生成", test_batch_data_generation),
        ("测试场景建议", test_scenario_suggestions),
        ("数据质量评估", test_quality_evaluation),
        ("边界值生成", test_boundary_values),
        ("非法值生成", test_invalid_values),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"❌ {name} 测试异常: {e}")
            results.append((name, False))
    
    # 统计结果
    print("\n" + "=" * 60)
    print("📊 测试结果汇总")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{status} - {name}")
    
    print("\n" + "=" * 60)
    print(f"总计: {passed}/{total} 通过 ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 所有测试通过!")
    else:
        print(f"⚠️  {total - passed} 个测试失败")
    
    print("=" * 60)

if __name__ == "__main__":
    main()
