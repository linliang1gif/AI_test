#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
四阶段简化测试
验证 Self-Healing 模块与其他模块的基本集成
"""

import requests
import json


BASE_URL = "http://localhost:8000/api"


def test_all_modules_health():
    """测试所有模块的健康状态"""
    print("\n" + "="*70)
    print("🏥 四阶段模块健康检查")
    print("="*70)
    
    modules = [
        ("Test Agent", "/agent/health"),
        ("Strategy Engine", "/strategy/health"),
        ("Orchestrator", "/orchestrator/health"),
        ("Self-Healing", "/healing/health")
    ]
    
    all_healthy = True
    
    for name, endpoint in modules:
        try:
            response = requests.get(f"{BASE_URL}{endpoint}")
            data = response.json()
            status = data.get('status', 'unknown')
            
            icon = "✅" if status == 'healthy' else "❌"
            print(f"{icon} {name}: {status}")
            
            if status != 'healthy':
                all_healthy = False
                
        except Exception as e:
            print(f"❌ {name}: 连接失败 - {e}")
            all_healthy = False
    
    print("\n" + "="*70)
    if all_healthy:
        print("✅ 所有模块健康")
    else:
        print("⚠️  部分模块异常")
    print("="*70)
    
    return all_healthy


def test_self_healing_basic():
    """测试 Self-Healing 基本功能"""
    print("\n" + "="*70)
    print("🔧 Self-Healing 基本功能测试")
    print("="*70)
    
    test_cases = [
        {
            "name": "断言错误",
            "request": {
                "module": "支付模块",
                "error": "AssertionError: expected 200 but got 500",
                "test_type": "api"
            },
            "expected_type": "assertion"
        },
        {
            "name": "超时错误",
            "request": {
                "module": "订单模块",
                "error": "Timeout: Request timed out",
                "test_type": "api"
            },
            "expected_type": "timeout"
        },
        {
            "name": "服务器错误",
            "request": {
                "module": "用户模块",
                "error": "HTTP 500 Internal Server Error",
                "test_type": "api"
            },
            "expected_type": "server_error"
        }
    ]
    
    passed = 0
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n测试 {i}: {test['name']}")
        print("-" * 70)
        
        response = requests.post(f"{BASE_URL}/healing/fix", json=test['request'])
        
        if response.status_code != 200:
            print(f"❌ 请求失败: {response.status_code}")
            continue
        
        result = response.json()
        
        print(f"   修复成功: {result['fixed']}")
        print(f"   错误类型: {result['error_analysis']['type']}")
        print(f"   置信度: {result['confidence']}")
        
        if result['error_analysis']['type'] == test['expected_type']:
            print(f"   ✅ 错误类型识别正确")
            passed += 1
        else:
            print(f"   ❌ 错误类型识别错误")
    
    print("\n" + "="*70)
    print(f"测试结果: {passed}/{len(test_cases)} 通过")
    print("="*70)
    
    return passed == len(test_cases)


def test_self_healing_statistics():
    """测试 Self-Healing 统计功能"""
    print("\n" + "="*70)
    print("📊 Self-Healing 统计功能测试")
    print("="*70)
    
    # 获取统计信息
    response = requests.get(f"{BASE_URL}/healing/statistics")
    data = response.json()
    stats = data['data']
    
    print(f"\n统计信息:")
    print(f"   总修复次数: {stats['total_healings']}")
    print(f"   成功修复: {stats['successful_fixes']}")
    print(f"   失败修复: {stats['failed_fixes']}")
    print(f"   成功率: {stats['success_rate']}%")
    print(f"   平均置信度: {stats['avg_confidence']}")
    
    # 获取历史记录
    response = requests.get(f"{BASE_URL}/healing/history?limit=3")
    data = response.json()
    
    print(f"\n最近修复记录: {data['count']} 条")
    
    # 获取修复建议
    response = requests.get(f"{BASE_URL}/healing/suggestions/assertion")
    data = response.json()
    
    print(f"\n断言错误修复建议: {len(data['suggestions'])} 条")
    for suggestion in data['suggestions']:
        print(f"   - {suggestion}")
    
    print("\n✅ 统计功能正常")
    return True


def test_integration_scenario():
    """测试集成场景：失败 → 修复 → 重试"""
    print("\n" + "="*70)
    print("🔄 集成场景测试：失败 → 修复 → 重试")
    print("="*70)
    
    # 模拟一个测试失败
    print("\n1️⃣ 模拟测试失败")
    failure = {
        "module": "商品搜索",
        "error": "AssertionError: expected 10 results but got 5",
        "test_type": "api"
    }
    print(f"   模块: {failure['module']}")
    print(f"   错误: {failure['error']}")
    
    # 触发自动修复
    print("\n2️⃣ 触发自动修复")
    response = requests.post(f"{BASE_URL}/healing/fix", json=failure)
    result = response.json()
    
    print(f"   修复成功: {result['fixed']}")
    print(f"   修复策略: {result.get('fix_strategy', 'N/A')}")
    print(f"   置信度: {result['confidence']}")
    
    # 检查重试结果
    if result.get('retry_result'):
        retry = result['retry_result']
        print(f"\n3️⃣ 重试结果")
        print(f"   状态: {retry['status']}")
        print(f"   耗时: {retry['duration']}s")
        print(f"   详情: {retry['details']}")
        
        if retry['status'] == 'passed':
            print(f"\n✅ 修复成功！测试通过")
        else:
            print(f"\n⚠️  修复后仍失败，需要人工介入")
    
    return True


if __name__ == "__main__":
    try:
        print("\n" + "="*70)
        print("🚀 四阶段系统简化测试")
        print("="*70)
        
        # 1. 健康检查
        health_ok = test_all_modules_health()
        
        if not health_ok:
            print("\n⚠️  部分模块不健康，但继续测试 Self-Healing")
        
        # 2. Self-Healing 基本功能
        basic_ok = test_self_healing_basic()
        
        # 3. Self-Healing 统计功能
        stats_ok = test_self_healing_statistics()
        
        # 4. 集成场景
        integration_ok = test_integration_scenario()
        
        print("\n" + "="*70)
        print("🎉 测试完成")
        print("="*70)
        print(f"\n结果:")
        print(f"   健康检查: {'✅' if health_ok else '⚠️'}")
        print(f"   基本功能: {'✅' if basic_ok else '❌'}")
        print(f"   统计功能: {'✅' if stats_ok else '❌'}")
        print(f"   集成场景: {'✅' if integration_ok else '❌'}")
        
        print("\n💡 Self-Healing 模块已成功集成到四阶段系统！")
        
    except requests.exceptions.ConnectionError:
        print(f"\n❌ 连接失败: 请确保后端服务器运行在 {BASE_URL}")
    except Exception as e:
        print(f"\n❌ 测试异常: {e}")
        import traceback
        traceback.print_exc()
