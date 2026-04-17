#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试后端API接口
验证所有测试数据工厂API是否正常工作
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_health():
    """测试健康检查"""
    print("\n" + "="*60)
    print("测试: 健康检查")
    print("="*60)
    
    response = requests.get(f"{BASE_URL}/health")
    print(f"状态码: {response.status_code}")
    print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
    print("✅ 健康检查通过")

def test_generate_user():
    """测试生成用户数据"""
    print("\n" + "="*60)
    print("测试: 生成用户数据")
    print("="*60)
    
    data = {
        "data_type": "user",
        "count": 1
    }
    
    response = requests.post(f"{BASE_URL}/api/test-data/generate", json=data)
    print(f"状态码: {response.status_code}")
    result = response.json()
    print(f"响应: {json.dumps(result, indent=2, ensure_ascii=False)}")
    assert response.status_code == 200
    assert result["success"] == True
    assert "data" in result
    print("✅ 用户数据生成成功")

def test_batch_generate():
    """测试批量生成"""
    print("\n" + "="*60)
    print("测试: 批量生成产品数据")
    print("="*60)
    
    data = {
        "data_type": "product",
        "count": 3
    }
    
    response = requests.post(f"{BASE_URL}/api/test-data/generate", json=data)
    print(f"状态码: {response.status_code}")
    result = response.json()
    print(f"响应: {json.dumps(result, indent=2, ensure_ascii=False)}")
    assert response.status_code == 200
    assert result["success"] == True
    assert result["count"] == 3
    print("✅ 批量生成成功")

def test_smart_generate():
    """测试AI智能生成"""
    print("\n" + "="*60)
    print("测试: AI智能生成字段")
    print("="*60)
    
    data = {
        "field_name": "user_email",
        "context": {"domain": "test.com"}
    }
    
    response = requests.post(f"{BASE_URL}/api/test-data/smart-generate", json=data)
    print(f"状态码: {response.status_code}")
    result = response.json()
    print(f"响应: {json.dumps(result, indent=2, ensure_ascii=False)}")
    assert response.status_code == 200
    assert result["success"] == True
    print("✅ AI智能生成成功")

def test_scenarios():
    """测试获取测试场景"""
    print("\n" + "="*60)
    print("测试: 获取测试场景")
    print("="*60)
    
    response = requests.get(f"{BASE_URL}/api/test-data/scenarios/user")
    print(f"状态码: {response.status_code}")
    result = response.json()
    print(f"响应: {json.dumps(result, indent=2, ensure_ascii=False)}")
    assert response.status_code == 200
    assert result["success"] == True
    assert "scenarios" in result
    print("✅ 测试场景获取成功")

def test_stats():
    """测试获取统计信息"""
    print("\n" + "="*60)
    print("测试: 获取统计信息")
    print("="*60)
    
    response = requests.get(f"{BASE_URL}/api/test-data/stats")
    print(f"状态码: {response.status_code}")
    result = response.json()
    print(f"响应: {json.dumps(result, indent=2, ensure_ascii=False)}")
    assert response.status_code == 200
    assert result["success"] == True
    print("✅ 统计信息获取成功")

def test_boundary_values():
    """测试获取边界值"""
    print("\n" + "="*60)
    print("测试: 获取边界值")
    print("="*60)
    
    response = requests.get(f"{BASE_URL}/api/test-data/boundary-values/integer?min_value=0&max_value=100")
    print(f"状态码: {response.status_code}")
    result = response.json()
    print(f"响应: {json.dumps(result, indent=2, ensure_ascii=False)}")
    assert response.status_code == 200
    assert result["success"] == True
    print("✅ 边界值获取成功")

def test_invalid_values():
    """测试获取非法值"""
    print("\n" + "="*60)
    print("测试: 获取非法值")
    print("="*60)
    
    response = requests.get(f"{BASE_URL}/api/test-data/invalid-values/email")
    print(f"状态码: {response.status_code}")
    result = response.json()
    print(f"响应: {json.dumps(result, indent=2, ensure_ascii=False)}")
    assert response.status_code == 200
    assert result["success"] == True
    print("✅ 非法值获取成功")

def test_quality_evaluation():
    """测试数据质量评估"""
    print("\n" + "="*60)
    print("测试: 数据质量评估")
    print("="*60)
    
    data = {
        "data": {
            "user_id": "12345",
            "email": "test@example.com",
            "age": 25
        }
    }
    
    response = requests.post(f"{BASE_URL}/api/test-data/evaluate", json=data)
    print(f"状态码: {response.status_code}")
    result = response.json()
    print(f"响应: {json.dumps(result, indent=2, ensure_ascii=False)}")
    assert response.status_code == 200
    assert result["success"] == True
    print("✅ 质量评估成功")

def run_all_tests():
    """运行所有测试"""
    print("\n" + "🚀 " + "="*58)
    print("开始测试后端API接口")
    print("="*60)
    
    tests = [
        ("健康检查", test_health),
        ("生成用户数据", test_generate_user),
        ("批量生成", test_batch_generate),
        ("AI智能生成", test_smart_generate),
        ("获取测试场景", test_scenarios),
        ("获取统计信息", test_stats),
        ("获取边界值", test_boundary_values),
        ("获取非法值", test_invalid_values),
        ("数据质量评估", test_quality_evaluation),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            test_func()
            passed += 1
        except Exception as e:
            print(f"❌ {name} 失败: {e}")
            failed += 1
    
    print("\n" + "="*60)
    print("测试结果汇总")
    print("="*60)
    print(f"✅ 通过: {passed}")
    print(f"❌ 失败: {failed}")
    print(f"📊 总计: {passed + failed}")
    print(f"🎯 成功率: {passed / (passed + failed) * 100:.1f}%")
    print("="*60)
    
    if failed == 0:
        print("\n🎉 所有测试通过!")
    else:
        print(f"\n⚠️  有 {failed} 个测试失败")

if __name__ == "__main__":
    try:
        run_all_tests()
    except requests.exceptions.ConnectionError:
        print("\n❌ 无法连接到后端服务器")
        print("请确保后端服务器正在运行: py backend_api_server.py")
    except KeyboardInterrupt:
        print("\n\n⚠️  测试被用户中断")
