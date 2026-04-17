#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Self-Healing API 测试
测试 HTTP 接口功能
"""

import requests
import json


BASE_URL = "http://localhost:8000/api"


def test_fix_endpoint():
    """测试修复接口"""
    print("\n" + "="*60)
    print("测试1: POST /healing/fix")
    print("="*60)
    
    # 测试断言错误修复
    payload = {
        "module": "支付模块",
        "error": "AssertionError: expected 200 but got 500",
        "test_type": "api"
    }
    
    response = requests.post(f"{BASE_URL}/healing/fix", json=payload)
    print(f"状态码: {response.status_code}")
    
    assert response.status_code == 200, f"应该返回200，实际: {response.status_code}"
    
    data = response.json()
    print(f"响应数据: {json.dumps(data, indent=2, ensure_ascii=False)}")
    
    assert data['fixed'] == True, "应该成功修复"
    assert 'error_analysis' in data, "应该包含错误分析"
    assert 'retry_result' in data, "应该包含重试结果"
    assert data['confidence'] > 0, "置信度应该大于0"
    
    print("✅ 测试1通过: 修复接口正常")


def test_timeout_fix():
    """测试超时错误修复"""
    print("\n" + "="*60)
    print("测试2: 超时错误修复")
    print("="*60)
    
    payload = {
        "module": "订单模块",
        "error": "Timeout: Request timed out after 30 seconds",
        "test_type": "api"
    }
    
    response = requests.post(f"{BASE_URL}/healing/fix", json=payload)
    data = response.json()
    
    print(f"修复结果: {data['fixed']}")
    print(f"修复策略: {data.get('fix_strategy', 'N/A')}")
    
    assert data['fixed'] == True, "超时错误应该可修复"
    # 检查修复策略中是否包含超时相关内容
    fix_strategy = data.get('fix_strategy', '')
    assert 'timeout' in fix_strategy.lower() or '超时' in fix_strategy, "修复策略应该包含超时调整"
    
    print("✅ 测试2通过: 超时错误修复正常")


def test_server_error_fix():
    """测试服务器错误修复"""
    print("\n" + "="*60)
    print("测试3: 服务器错误修复")
    print("="*60)
    
    payload = {
        "module": "用户模块",
        "error": "HTTP 500 Internal Server Error",
        "test_type": "api"
    }
    
    response = requests.post(f"{BASE_URL}/healing/fix", json=payload)
    data = response.json()
    
    print(f"修复结果: {data['fixed']}")
    print(f"错误类型: {data['error_analysis']['type']}")
    
    assert data['fixed'] == True, "服务器错误应该可修复"
    assert data['error_analysis']['type'] == 'server_error', "错误类型应为 server_error"
    
    print("✅ 测试3通过: 服务器错误修复正常")


def test_history_endpoint():
    """测试历史记录接口"""
    print("\n" + "="*60)
    print("测试4: GET /healing/history")
    print("="*60)
    
    response = requests.get(f"{BASE_URL}/healing/history?limit=5")
    print(f"状态码: {response.status_code}")
    
    assert response.status_code == 200, "应该返回200"
    
    data = response.json()
    print(f"历史记录数: {data['count']}")
    
    assert data['success'] == True, "应该成功"
    assert 'data' in data, "应该包含数据"
    
    print("✅ 测试4通过: 历史记录接口正常")


def test_statistics_endpoint():
    """测试统计信息接口"""
    print("\n" + "="*60)
    print("测试5: GET /healing/statistics")
    print("="*60)
    
    response = requests.get(f"{BASE_URL}/healing/statistics")
    print(f"状态码: {response.status_code}")
    
    assert response.status_code == 200, "应该返回200"
    
    data = response.json()
    stats = data['data']
    
    print(f"统计信息:")
    print(f"   总修复次数: {stats['total_healings']}")
    print(f"   成功修复: {stats['successful_fixes']}")
    print(f"   失败修复: {stats['failed_fixes']}")
    print(f"   成功率: {stats['success_rate']}%")
    print(f"   平均置信度: {stats['avg_confidence']}")
    
    assert 'total_healings' in stats, "应该包含总修复次数"
    assert 'success_rate' in stats, "应该包含成功率"
    
    print("✅ 测试5通过: 统计信息接口正常")


def test_suggestions_endpoint():
    """测试修复建议接口"""
    print("\n" + "="*60)
    print("测试6: GET /healing/suggestions/{error_type}")
    print("="*60)
    
    error_types = ['assertion', 'timeout', 'server_error']
    
    for error_type in error_types:
        response = requests.get(f"{BASE_URL}/healing/suggestions/{error_type}")
        data = response.json()
        
        print(f"\n{error_type} 建议:")
        for suggestion in data['suggestions']:
            print(f"   - {suggestion}")
        
        assert data['success'] == True, "应该成功"
        assert len(data['suggestions']) > 0, f"{error_type} 应该有建议"
    
    print("\n✅ 测试6通过: 修复建议接口正常")


def test_health_endpoint():
    """测试健康检查接口"""
    print("\n" + "="*60)
    print("测试7: GET /healing/health")
    print("="*60)
    
    response = requests.get(f"{BASE_URL}/healing/health")
    print(f"状态码: {response.status_code}")
    
    assert response.status_code == 200, "应该返回200"
    
    data = response.json()
    print(f"健康状态: {data['status']}")
    print(f"修复记录数: {data['healings_count']}")
    
    assert data['status'] == 'healthy', "状态应该为 healthy"
    
    print("✅ 测试7通过: 健康检查接口正常")


def run_all_tests():
    """运行所有API测试"""
    print("\n" + "="*60)
    print("🧪 Self-Healing API 测试")
    print("="*60)
    
    try:
        test_fix_endpoint()
        test_timeout_fix()
        test_server_error_fix()
        test_history_endpoint()
        test_statistics_endpoint()
        test_suggestions_endpoint()
        test_health_endpoint()
        
        print("\n" + "="*60)
        print("✅ 所有API测试通过！(7/7)")
        print("="*60)
        
        return True
        
    except AssertionError as e:
        print(f"\n❌ 测试失败: {e}")
        return False
    except requests.exceptions.ConnectionError:
        print(f"\n❌ 连接失败: 请确保后端服务器运行在 {BASE_URL}")
        return False
    except Exception as e:
        print(f"\n❌ 测试异常: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    import sys
    success = run_all_tests()
    sys.exit(0 if success else 1)
