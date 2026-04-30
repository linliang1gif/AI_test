#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 Case Generator API
验证用例生成 API 端点
"""

import requests
import json

BASE_URL = "http://localhost:8000/api"


def test_case_generator_api():
    """测试 Case Generator API"""
    
    print("=" * 60)
    print("测试 Case Generator API")
    print("=" * 60)
    
    # 准备测试策略
    test_strategy = {
        "strategy": [
            {
                "module": {
                    "name": "支付模块",
                    "impact": "high"
                },
                "priority": "P0",
                "test_types": ["api", "integration"],
                "case_count": 8,
                "execution_order": 1,
                "risk_level": "高",
                "execution_hint": {
                    "parallel": True,
                    "timeout": 60
                }
            },
            {
                "module": {
                    "name": "订单模块",
                    "impact": "medium"
                },
                "priority": "P1",
                "test_types": ["api"],
                "case_count": 5,
                "execution_order": 2,
                "risk_level": "中",
                "execution_hint": {
                    "parallel": True,
                    "timeout": 90
                }
            }
        ],
        "total_modules": 2,
        "total_cases": 13,
        "generated_at": "2024-03-21T10:00:00"
    }
    
    # 测试1: 健康检查
    print("\n【测试1】健康检查")
    print("-" * 60)
    
    try:
        response = requests.get(f"{BASE_URL}/case/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 健康检查通过: {data['status']}")
        else:
            print(f"❌ 健康检查失败: {response.status_code}")
    except Exception as e:
        print(f"❌ 健康检查异常: {e}")
    
    # 测试2: 生成用例
    print("\n【测试2】生成测试用例")
    print("-" * 60)
    
    try:
        response = requests.post(
            f"{BASE_URL}/case/generate",
            json={"strategy": test_strategy},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 用例生成成功:")
            print(f"   - 模块数: {len(data['cases'])}")
            print(f"   - 总用例数: {data['total_cases']}")
            
            for module_cases in data['cases']:
                module_name = module_cases['module']
                cases = module_cases['cases']
                print(f"\n   📦 {module_name}: {len(cases)} 个用例")
                
                # 显示前2个用例
                for i, case in enumerate(cases[:2], 1):
                    print(f"      {i}. {case['title']}")
                    print(f"         类型: {case['type']}, 优先级: {case['priority']}")
        else:
            print(f"❌ 用例生成失败: {response.status_code}")
            print(f"   响应: {response.text}")
    except Exception as e:
        print(f"❌ 用例生成异常: {e}")
    
    # 测试3: 获取历史
    print("\n【测试3】获取用例历史")
    print("-" * 60)
    
    try:
        response = requests.get(f"{BASE_URL}/case/history?limit=5", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 历史记录数: {data['total']}")
        else:
            print(f"❌ 获取历史失败: {response.status_code}")
    except Exception as e:
        print(f"❌ 获取历史异常: {e}")
    
    # 测试4: 获取统计
    print("\n【测试4】获取统计信息")
    print("-" * 60)
    
    try:
        response = requests.get(f"{BASE_URL}/case/statistics", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 统计信息:")
            print(f"   - 总生成次数: {data['total_generations']}")
            print(f"   - 总用例数: {data['total_cases']}")
            print(f"   - 平均每次: {data['avg_cases_per_generation']}")
        else:
            print(f"❌ 获取统计失败: {response.status_code}")
    except Exception as e:
        print(f"❌ 获取统计异常: {e}")
    
    print("\n" + "=" * 60)
    print("✅ Case Generator API 测试完成")
    print("=" * 60)


if __name__ == "__main__":
    test_case_generator_api()
