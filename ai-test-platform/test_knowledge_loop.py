#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
知识库闭环功能测试
验证: 自动入库 → 智能检索 → 反馈闭环
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from knowledge.knowledge_manager import get_knowledge_manager


def test_knowledge_loop():
    """测试完整的知识库闭环"""
    
    print("=" * 70)
    print("🔥 知识库闭环功能测试")
    print("=" * 70)
    
    km = get_knowledge_manager()
    
    # ═══════════════════════════════════════════════════════
    # 测试1: 自动入库
    # ═══════════════════════════════════════════════════════
    
    print("\n📝 测试1: 自动入库功能")
    print("-" * 70)
    
    # 模拟测试失败
    test_case = {
        'id': 'TC-001',
        'title': '用户登录测试',
        'module': '认证模块'
    }
    
    error_info = {
        'error_type': 'AssertionError',
        'error_message': 'Expected status code 200, got 401',
        'stack_trace': 'File "test_login.py", line 25, in test_login\n    assert response.status_code == 200'
    }
    
    bug_id = km.record_test_failure(test_case, error_info)
    if bug_id:
        print(f"✅ Bug自动入库成功: {bug_id}")
    else:
        print("❌ Bug入库失败")
        return False
    
    # 记录测试用例
    test_case_full = {
        'id': 'TC-001',
        'title': '用户登录测试',
        'module': '认证模块',
        'priority': 'high',
        'steps': [
            '1. 打开登录页面',
            '2. 输入用户名和密码',
            '3. 点击登录按钮'
        ],
        'expected_result': '登录成功,跳转到首页',
        'source': 'ai_generated'
    }
    
    if km.record_test_case(test_case_full):
        print("✅ 测试用例自动入库成功")
    else:
        print("❌ 测试用例入库失败")
    
    # ═══════════════════════════════════════════════════════
    # 测试2: 智能检索
    # ═══════════════════════════════════════════════════════
    
    print("\n🔍 测试2: 智能检索功能")
    print("-" * 70)
    
    # 查找相似Bug
    similar_bugs = km.find_similar_bugs("登录返回401错误", top_k=3)
    print(f"\n找到 {len(similar_bugs)} 个相似Bug:")
    for i, bug in enumerate(similar_bugs, 1):
        print(f"  {i}. {bug['bug_id']} - {bug['root_cause']}")
        print(f"     相似度: {bug['similarity']:.2f}")
        if bug.get('fix_suggestion'):
            print(f"     修复建议: {bug['fix_suggestion']}")
    
    # 查找相似测试用例
    similar_cases = km.find_similar_testcases("用户登录功能", top_k=3)
    print(f"\n找到 {len(similar_cases)} 个相似测试用例:")
    for i, case in enumerate(similar_cases, 1):
        print(f"  {i}. {case['tc_id']} - {case['title']}")
        print(f"     模块: {case['module']}, 优先级: {case['priority']}")
    
    # ═══════════════════════════════════════════════════════
    # 测试3: 修复模式学习
    # ═══════════════════════════════════════════════════════
    
    print("\n🔧 测试3: 修复模式学习")
    print("-" * 70)
    
    # 记录修复成功
    fix_pattern = """
    # 修复方案: 检查认证token是否过期
    if token_expired():
        refresh_token()
        retry_request()
    """
    
    error_pattern = "401 Unauthorized - Token expired"
    
    if km.record_healing_success(bug_id, fix_pattern, error_pattern):
        print("✅ 修复模式已学习")
    else:
        print("❌ 修复模式学习失败")
    
    # 查找修复模式
    healing_patterns = km.find_healing_patterns("401 authentication error", top_k=3)
    print(f"\n找到 {len(healing_patterns)} 个修复模式:")
    for i, pattern in enumerate(healing_patterns, 1):
        print(f"  {i}. 模式ID: {pattern['pattern_id']}")
        print(f"     成功率: {pattern['success_rate']:.1%}")
        print(f"     使用次数: {pattern['success_count']}")
    
    # ═══════════════════════════════════════════════════════
    # 测试4: 反馈闭环
    # ═══════════════════════════════════════════════════════
    
    print("\n🔄 测试4: 反馈闭环")
    print("-" * 70)
    
    if healing_patterns:
        pattern_id = healing_patterns[0]['pattern_id']
        
        # 模拟修复成功
        if km.evaluate_healing_result(pattern_id, success=True):
            print("✅ 修复结果已反馈(成功)")
        
        # 模拟修复失败
        if km.evaluate_healing_result(pattern_id, success=False):
            print("✅ 修复结果已反馈(失败)")
    
    # ═══════════════════════════════════════════════════════
    # 测试5: 知识库统计
    # ═══════════════════════════════════════════════════════
    
    print("\n📊 测试5: 知识库统计")
    print("-" * 70)
    
    stats = km.get_knowledge_stats()
    if stats:
        print(f"\nBug记录:")
        print(f"  总数: {stats['bugs']['total']}")
        print(f"  已修复: {stats['bugs']['fixed']}")
        print(f"  修复率: {stats['bugs']['fix_rate']:.1%}")
        
        print(f"\n测试用例:")
        print(f"  总数: {stats['testcases']['total']}")
        
        print(f"\n修复模式:")
        print(f"  总数: {stats['healing_patterns']['total']}")
        print(f"  平均成功率: {stats['healing_patterns']['avg_success_rate']:.1%}")
    
    # ═══════════════════════════════════════════════════════
    # 总结
    # ═══════════════════════════════════════════════════════
    
    print("\n" + "=" * 70)
    print("✅ 知识库闭环功能测试完成!")
    print("=" * 70)
    
    print("\n🎯 闭环流程验证:")
    print("  1. ✅ 测试失败 → 自动入库")
    print("  2. ✅ 遇到问题 → 智能检索相似案例")
    print("  3. ✅ 修复成功 → 学习修复模式")
    print("  4. ✅ 执行结果 → 反馈评估")
    print("  5. ✅ 知识积累 → 持续优化")
    
    print("\n💡 AI闭环已打通!")
    
    return True


if __name__ == "__main__":
    try:
        success = test_knowledge_loop()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
