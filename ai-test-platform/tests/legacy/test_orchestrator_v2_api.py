#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 Orchestrator V2 API
验证 API 端点支持 cases 参数
"""

import requests
import json

BASE_URL = "http://localhost:8000/api"


def test_orchestrator_v2_api():
    """测试 Orchestrator V2 API"""
    
    print("=" * 80)
    print("测试 Orchestrator V2 API")
    print("=" * 80)
    
    # 测试1: 基于策略执行（原模式）
    print("\n【测试1】基于策略执行（原模式）")
    print("-" * 80)
    
    strategy_payload = {
        "strategy": {
            "strategy": [
                {
                    "module": {"name": "测试模块A", "impact": "high"},
                    "priority": "P0",
                    "test_types": ["api"],
                    "case_count": 5,
                    "execution_order": 1,
                    "execution_hint": {"parallel": False, "timeout": 60}
                }
            ],
            "total_modules": 1,
            "total_cases": 5
        }
    }
    
    response = requests.post(f"{BASE_URL}/orchestrator/run", json=strategy_payload)
    
    print(f"   状态码: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"   ✅ 执行成功:")
        print(f"      - 模式: {result.get('mode', 'unknown')}")
        print(f"      - 通过: {result['summary']['passed']}/{result['summary']['total']}")
    else:
        print(f"   ❌ 执行失败: {response.text}")
    
    # 测试2: 基于用例执行（新模式）
    print("\n【测试2】基于用例执行（新模式）")
    print("-" * 80)
    
    cases_payload = {
        "strategy": {
            "strategy": [],
            "total_modules": 0
        },
        "cases": {
            "cases": [
                {
                    "module": "支付模块",
                    "cases": [
                        {
                            "id": "TC_01_01",
                            "title": "验证支付功能",
                            "type": "功能测试",
                            "priority": "高",
                            "steps": ["步骤1"],
                            "expected_result": "支付成功"
                        },
                        {
                            "id": "TC_01_02",
                            "title": "验证支付UI",
                            "type": "UI测试",
                            "priority": "中",
                            "steps": ["步骤1"],
                            "expected_result": "界面正常"
                        }
                    ]
                }
            ],
            "total_cases": 2
        }
    }
    
    response = requests.post(f"{BASE_URL}/orchestrator/run", json=cases_payload)
    
    print(f"   状态码: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"   ✅ 执行成功:")
        print(f"      - 模式: {result.get('mode', 'unknown')}")
        print(f"      - 模块数: {len(result['results'])}")
        print(f"      - 通过: {result['summary']['passed']}/{result['summary']['total']}")
        
        # 显示用例级别结果
        for module_result in result['results']:
            case_results = module_result.get('case_results', [])
            if case_results:
                print(f"      - {module_result['module']}: {len(case_results)}个用例执行")
    else:
        print(f"   ❌ 执行失败: {response.text}")
    
    # 测试3: 健康检查
    print("\n【测试3】健康检查")
    print("-" * 80)
    
    response = requests.get(f"{BASE_URL}/orchestrator/health")
    
    if response.status_code == 200:
        health = response.json()
        print(f"   ✅ 健康状态: {health['status']}")
        print(f"      - 执行次数: {health['executions_count']}")
    else:
        print(f"   ❌ 健康检查失败")
    
    print("\n" + "=" * 80)
    print("✅ Orchestrator V2 API 测试完成")
    print("=" * 80)


if __name__ == "__main__":
    try:
        test_orchestrator_v2_api()
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到后端服务器")
        print("   请确保后端服务器正在运行: python backend_api_server.py")
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
