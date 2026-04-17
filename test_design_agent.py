#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 DesignAgent - 不依赖 ExecutionAgent
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from modules.agents import DesignAgent


def test_design_agent():
    """测试 DesignAgent"""
    print("=" * 80)
    print("DesignAgent 功能测试")
    print("=" * 80)
    
    # 创建 DesignAgent
    design_agent = DesignAgent(config={
        'max_testcases_per_api': 3,
        'include_edge_cases': True,
        'include_error_cases': True
    })
    
    print("\n✅ DesignAgent 已创建")
    
    # 测试 1: 从需求设计
    print("\n" + "-" * 80)
    print("测试 1: 从需求文档设计测试用例")
    print("-" * 80)
    
    requirement = """
    用户登录功能需求：
    1. 用户可以使用用户名和密码登录
    2. 登录成功后返回 JWT token
    3. 登录失败返回错误信息
    """
    
    testcases = design_agent.design_from_requirement(requirement)
    print(f"\n✅ 生成了 {len(testcases)} 个测试用例")
    
    for i, tc in enumerate(testcases, 1):
        title = tc.get('title') if isinstance(tc, dict) else getattr(tc, 'title', 'Unknown')
        print(f"   {i}. {title}")
    
    # 测试 2: 从 Discovery 结果设计
    print("\n" + "-" * 80)
    print("测试 2: 从 Discovery 结果设计测试用例")
    print("-" * 80)
    
    discovery_results = [
        {
            "path": "/api/users",
            "method": "POST",
            "change_type": "new_endpoint",
            "risk_level": "high"
        },
        {
            "path": "/api/users/{id}",
            "method": "DELETE",
            "change_type": "modified",
            "risk_level": "critical"
        }
    ]
    
    testcases = design_agent.design_from_discovery(discovery_results)
    print(f"\n✅ 生成了 {len(testcases)} 个测试用例")
    
    # 测试 3: 优化测试用例
    print("\n" + "-" * 80)
    print("测试 3: 优化测试用例")
    print("-" * 80)
    
    all_testcases = testcases + testcases[:2]
    print(f"原始: {len(all_testcases)} 个")
    
    optimized = design_agent.optimize_testcases(all_testcases, max_count=10)
    print(f"优化后: {len(optimized)} 个")
    
    # 测试 4: 统计信息
    print("\n" + "-" * 80)
    print("测试 4: 设计统计信息")
    print("-" * 80)
    
    stats = design_agent.get_design_statistics()
    print(f"\n总设计次数: {stats['total_designs']}")
    print(f"总测试用例数: {stats['total_testcases']}")
    print(f"平均每次: {stats['avg_testcases_per_design']:.1f} 个")
    
    print("\n" + "=" * 80)
    print("✅ DesignAgent 测试完成！")
    print("=" * 80)


if __name__ == "__main__":
    test_design_agent()
