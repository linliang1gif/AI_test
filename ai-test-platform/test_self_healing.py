#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Self-Healing Module 单元测试
测试错误分析、修复策略和重试逻辑
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from self_healing.analyzer import analyze_error, extract_error_context, calculate_fix_confidence
from self_healing.fixer import apply_fix, get_fix_strategy
from self_healing.healing_service import get_healing_service


def test_assertion_error():
    """测试断言错误分析和修复"""
    print("\n" + "="*60)
    print("测试1: 断言错误")
    print("="*60)
    
    error = "AssertionError: expected 200 but got 500"
    
    # 分析错误
    analysis = analyze_error(error, "支付模块", "api")
    print(f"✅ 错误分析:")
    print(f"   类型: {analysis['type']}")
    print(f"   严重程度: {analysis['severity']}")
    print(f"   可修复: {analysis['fixable']}")
    print(f"   详情: {analysis['details']}")
    
    assert analysis['type'] == 'assertion', "错误类型应为 assertion"
    assert analysis['fixable'] == True, "断言错误应该可修复"
    
    # 提取上下文
    context = extract_error_context(error)
    print(f"\n✅ 错误上下文:")
    print(f"   期望值: {context['expected_value']}")
    print(f"   实际值: {context['actual_value']}")
    
    # 应用修复
    fix_result = apply_fix(analysis['type'], "支付模块", context)
    print(f"\n✅ 修复策略:")
    print(f"   修复描述: {fix_result['fix_applied']}")
    print(f"   是否重试: {fix_result['retry']}")
    print(f"   修改内容: {fix_result['modifications']}")
    
    assert fix_result['retry'] == True, "应该触发重试"
    
    # 计算置信度
    confidence = calculate_fix_confidence(analysis['type'], analysis['severity'])
    print(f"\n✅ 修复置信度: {confidence}")
    
    assert confidence > 0.5, "断言错误修复置信度应该较高"
    
    print("\n✅ 测试1通过: 断言错误分析和修复正常")


def test_timeout_error():
    """测试超时错误分析和修复"""
    print("\n" + "="*60)
    print("测试2: 超时错误")
    print("="*60)
    
    error = "Timeout: Request timed out after 30 seconds"
    
    # 分析错误
    analysis = analyze_error(error, "订单模块", "api")
    print(f"✅ 错误分析:")
    print(f"   类型: {analysis['type']}")
    print(f"   严重程度: {analysis['severity']}")
    print(f"   可修复: {analysis['fixable']}")
    
    assert analysis['type'] == 'timeout', "错误类型应为 timeout"
    assert analysis['fixable'] == True, "超时错误应该可修复"
    
    # 应用修复
    context = extract_error_context(error)
    fix_result = apply_fix(analysis['type'], "订单模块", context)
    print(f"\n✅ 修复策略:")
    print(f"   修复描述: {fix_result['fix_applied']}")
    print(f"   修改内容: {fix_result['modifications']}")
    
    assert 'timeout' in fix_result['modifications'], "应该包含超时时间调整"
    assert fix_result['modifications']['timeout'] > 30, "超时时间应该增加"
    
    print("\n✅ 测试2通过: 超时错误分析和修复正常")


def test_server_error():
    """测试服务器错误分析和修复"""
    print("\n" + "="*60)
    print("测试3: 服务器错误")
    print("="*60)
    
    error = "HTTP 500 Internal Server Error: Database connection failed"
    
    # 分析错误
    analysis = analyze_error(error, "用户模块", "api")
    print(f"✅ 错误分析:")
    print(f"   类型: {analysis['type']}")
    print(f"   严重程度: {analysis['severity']}")
    print(f"   可修复: {analysis['fixable']}")
    
    assert analysis['type'] == 'server_error', "错误类型应为 server_error"
    assert analysis['severity'] == 'high', "服务器错误严重程度应为 high"
    
    # 应用修复
    context = extract_error_context(error)
    fix_result = apply_fix(analysis['type'], "用户模块", context)
    print(f"\n✅ 修复策略:")
    print(f"   修复描述: {fix_result['fix_applied']}")
    print(f"   修改内容: {fix_result['modifications']}")
    
    assert 'retry_count' in fix_result['modifications'], "应该包含重试次数"
    
    print("\n✅ 测试3通过: 服务器错误分析和修复正常")


def test_unknown_error():
    """测试未知错误（不可修复）"""
    print("\n" + "="*60)
    print("测试4: 未知错误")
    print("="*60)
    
    error = "Something went wrong in the system"
    
    # 分析错误
    analysis = analyze_error(error, "未知模块", "api")
    print(f"✅ 错误分析:")
    print(f"   类型: {analysis['type']}")
    print(f"   可修复: {analysis['fixable']}")
    
    assert analysis['type'] == 'unknown', "错误类型应为 unknown"
    assert analysis['fixable'] == False, "未知错误不应该可修复"
    
    print("\n✅ 测试4通过: 未知错误正确识别为不可修复")


def test_healing_service():
    """测试完整的修复服务流程"""
    print("\n" + "="*60)
    print("测试5: 完整修复服务流程")
    print("="*60)
    
    service = get_healing_service()
    
    # 测试修复流程
    failure_info = {
        "module": "支付模块",
        "error": "AssertionError: expected 200 but got 500",
        "test_type": "api"
    }
    
    result = service.fix_and_retry(failure_info)
    
    print(f"\n✅ 修复结果:")
    print(f"   是否修复: {result['fixed']}")
    print(f"   修复原因: {result['reason']}")
    print(f"   置信度: {result['confidence']}")
    
    assert result['fixed'] == True, "应该成功修复"
    assert 'error_analysis' in result, "应该包含错误分析"
    assert 'retry_result' in result, "应该包含重试结果"
    
    # 测试历史记录
    history = service.get_healing_history(limit=5)
    print(f"\n✅ 修复历史: {len(history)} 条记录")
    assert len(history) > 0, "应该有历史记录"
    
    # 测试统计信息
    stats = service.get_statistics()
    print(f"\n✅ 统计信息:")
    print(f"   总修复次数: {stats['total_healings']}")
    print(f"   成功修复: {stats['successful_fixes']}")
    print(f"   失败修复: {stats['failed_fixes']}")
    print(f"   成功率: {stats['success_rate']}%")
    print(f"   平均置信度: {stats['avg_confidence']}")
    
    assert stats['total_healings'] > 0, "应该有修复记录"
    
    print("\n✅ 测试5通过: 完整修复服务流程正常")


def test_fix_suggestions():
    """测试修复建议"""
    print("\n" + "="*60)
    print("测试6: 修复建议")
    print("="*60)
    
    service = get_healing_service()
    
    error_types = ['assertion', 'timeout', 'server_error', 'unknown']
    
    for error_type in error_types:
        suggestions = service.get_fix_suggestions(error_type)
        print(f"\n✅ {error_type} 修复建议:")
        for i, suggestion in enumerate(suggestions, 1):
            print(f"   {i}. {suggestion}")
        
        assert len(suggestions) > 0, f"{error_type} 应该有修复建议"
    
    print("\n✅ 测试6通过: 修复建议功能正常")


def run_all_tests():
    """运行所有测试"""
    print("\n" + "="*60)
    print("🧪 Self-Healing Module 单元测试")
    print("="*60)
    
    try:
        test_assertion_error()
        test_timeout_error()
        test_server_error()
        test_unknown_error()
        test_healing_service()
        test_fix_suggestions()
        
        print("\n" + "="*60)
        print("✅ 所有测试通过！(6/6)")
        print("="*60)
        
        return True
        
    except AssertionError as e:
        print(f"\n❌ 测试失败: {e}")
        return False
    except Exception as e:
        print(f"\n❌ 测试异常: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
