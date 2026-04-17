#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Self-Healing 演示脚本
展示自动修复功能的完整流程
"""

import requests
import json
import time


BASE_URL = "http://localhost:8000/api"


def demo_healing_workflow():
    """演示完整的自动修复流程"""
    print("\n" + "="*70)
    print("🔧 Self-Healing 自动修复演示")
    print("="*70)
    
    # 场景1: 断言错误
    print("\n【场景1】断言错误 - 期望值不匹配")
    print("-" * 70)
    
    failure1 = {
        "module": "支付模块",
        "error": "AssertionError: expected status 200 but got 500",
        "test_type": "api"
    }
    
    print(f"❌ 测试失败:")
    print(f"   模块: {failure1['module']}")
    print(f"   错误: {failure1['error']}")
    
    response = requests.post(f"{BASE_URL}/healing/fix", json=failure1)
    result = response.json()
    
    print(f"\n🔧 自动修复:")
    print(f"   修复成功: {result['fixed']}")
    print(f"   修复策略: {result['fix_strategy']}")
    print(f"   置信度: {result['confidence']}")
    print(f"   重试结果: {result['retry_result']['status']}")
    print(f"   耗时: {result['retry_result']['duration']}s")
    
    # 场景2: 超时错误
    print("\n【场景2】超时错误 - 请求响应慢")
    print("-" * 70)
    
    failure2 = {
        "module": "订单查询",
        "error": "Timeout: Request timed out after 30 seconds",
        "test_type": "api"
    }
    
    print(f"❌ 测试失败:")
    print(f"   模块: {failure2['module']}")
    print(f"   错误: {failure2['error']}")
    
    response = requests.post(f"{BASE_URL}/healing/fix", json=failure2)
    result = response.json()
    
    print(f"\n🔧 自动修复:")
    print(f"   修复成功: {result['fixed']}")
    print(f"   修复策略: {result['fix_strategy']}")
    print(f"   置信度: {result['confidence']}")
    print(f"   重试结果: {result['retry_result']['status']}")
    
    # 场景3: 服务器错误
    print("\n【场景3】服务器错误 - 后端异常")
    print("-" * 70)
    
    failure3 = {
        "module": "用户登录",
        "error": "HTTP 500 Internal Server Error: Database connection failed",
        "test_type": "api"
    }
    
    print(f"❌ 测试失败:")
    print(f"   模块: {failure3['module']}")
    print(f"   错误: {failure3['error']}")
    
    response = requests.post(f"{BASE_URL}/healing/fix", json=failure3)
    result = response.json()
    
    print(f"\n🔧 自动修复:")
    print(f"   修复成功: {result['fixed']}")
    print(f"   修复策略: {result['fix_strategy']}")
    print(f"   错误严重程度: {result['error_analysis']['severity']}")
    print(f"   重试结果: {result['retry_result']['status']}")
    
    # 场景4: 404 错误
    print("\n【场景4】404 错误 - 资源不存在")
    print("-" * 70)
    
    failure4 = {
        "module": "商品详情",
        "error": "HTTP 404 Not Found: /api/v2/products/123",
        "test_type": "api"
    }
    
    print(f"❌ 测试失败:")
    print(f"   模块: {failure4['module']}")
    print(f"   错误: {failure4['error']}")
    
    response = requests.post(f"{BASE_URL}/healing/fix", json=failure4)
    result = response.json()
    
    print(f"\n🔧 自动修复:")
    print(f"   修复成功: {result['fixed']}")
    print(f"   修复策略: {result['fix_strategy']}")
    print(f"   重试结果: {result['retry_result']['status']}")


def demo_statistics():
    """演示统计信息"""
    print("\n" + "="*70)
    print("📊 修复统计信息")
    print("="*70)
    
    response = requests.get(f"{BASE_URL}/healing/statistics")
    data = response.json()
    stats = data['data']
    
    print(f"\n总修复次数: {stats['total_healings']}")
    print(f"成功修复: {stats['successful_fixes']}")
    print(f"失败修复: {stats['failed_fixes']}")
    print(f"成功率: {stats['success_rate']}%")
    print(f"平均置信度: {stats['avg_confidence']}")


def demo_suggestions():
    """演示修复建议"""
    print("\n" + "="*70)
    print("💡 修复建议查询")
    print("="*70)
    
    error_types = {
        'assertion': '断言错误',
        'timeout': '超时错误',
        'server_error': '服务器错误',
        'auth_error': '认证错误'
    }
    
    for error_type, name in error_types.items():
        response = requests.get(f"{BASE_URL}/healing/suggestions/{error_type}")
        data = response.json()
        
        print(f"\n【{name}】修复建议:")
        for i, suggestion in enumerate(data['suggestions'], 1):
            print(f"   {i}. {suggestion}")


def demo_history():
    """演示修复历史"""
    print("\n" + "="*70)
    print("📜 修复历史记录")
    print("="*70)
    
    response = requests.get(f"{BASE_URL}/healing/history?limit=3")
    data = response.json()
    
    print(f"\n最近 {data['count']} 次修复:")
    
    for i, record in enumerate(data['data'], 1):
        failure = record['failure_info']
        healing = record['healing_result']
        
        print(f"\n{i}. {record['timestamp']}")
        print(f"   模块: {failure['module']}")
        print(f"   错误: {failure['error'][:50]}...")
        print(f"   修复: {healing['fixed']}")
        print(f"   策略: {healing.get('fix_strategy', 'N/A')[:50]}...")


if __name__ == "__main__":
    try:
        print("\n" + "="*70)
        print("🚀 Self-Healing 自动修复系统演示")
        print("="*70)
        
        # 1. 演示修复流程
        demo_healing_workflow()
        
        # 2. 演示统计信息
        time.sleep(0.5)
        demo_statistics()
        
        # 3. 演示修复建议
        time.sleep(0.5)
        demo_suggestions()
        
        # 4. 演示历史记录
        time.sleep(0.5)
        demo_history()
        
        print("\n" + "="*70)
        print("✅ 演示完成！")
        print("="*70)
        print("\n💡 提示:")
        print("   - Self-Healing 可以自动分析 6 种错误类型")
        print("   - 支持自动修复并重试测试")
        print("   - 最多重试 1 次，防止死循环")
        print("   - 所有修复操作都会记录日志")
        
    except requests.exceptions.ConnectionError:
        print(f"\n❌ 连接失败: 请确保后端服务器运行在 {BASE_URL}")
    except Exception as e:
        print(f"\n❌ 演示异常: {e}")
        import traceback
        traceback.print_exc()
