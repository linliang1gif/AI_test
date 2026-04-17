#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 TestContext 统一数据模型
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from common.context import TestContext


def test_context_creation():
    """测试 Context 创建"""
    
    print("=" * 80)
    print("测试 TestContext 创建")
    print("=" * 80)
    
    # 创建 context
    context = TestContext(
        requirement="测试需求",
        git_diff="+ def test(): pass",
        priority="P0"
    )
    
    print(f"\n✅ Context 创建成功:")
    print(f"   - Trace ID: {context.trace_id}")
    print(f"   - Requirement: {context.requirement}")
    print(f"   - Priority: {context.priority}")
    print(f"   - Created At: {context.created_at}")
    
    # 验证
    assert context.requirement == "测试需求"
    assert context.priority == "P0"
    assert len(context.trace_id) == 8
    
    print("\n" + "=" * 80)


def test_context_stage_operations():
    """测试 Context 阶段操作"""
    
    print("\n" + "=" * 80)
    print("测试 TestContext 阶段操作")
    print("=" * 80)
    
    context = TestContext(requirement="测试")
    
    # 写入 decision
    context.set_stage_data("decision", {
        "need_test": True,
        "risk_level": "高"
    })
    
    print(f"\n✅ 写入 decision:")
    print(f"   {context.decision}")
    
    # 读取 decision
    decision = context.get_stage_data("agent")
    print(f"\n✅ 读取 decision (通过 'agent' 别名):")
    print(f"   {decision}")
    
    # 写入 strategy
    context.set_stage_data("strategy", {
        "strategy": [{"module": "测试模块"}],
        "total_cases": 10
    })
    
    print(f"\n✅ 写入 strategy:")
    print(f"   {context.strategy}")
    
    # 验证
    assert context.decision is not None
    assert context.strategy is not None
    assert context.decision['need_test'] == True
    assert context.strategy['total_cases'] == 10
    
    print("\n" + "=" * 80)


def test_context_timeline():
    """测试 Context 时间线"""
    
    print("\n" + "=" * 80)
    print("测试 TestContext 时间线")
    print("=" * 80)
    
    context = TestContext(requirement="测试")
    
    # 添加时间线事件
    context.add_timeline_event("agent", "completed", 1.5, "AI 决策完成")
    context.add_timeline_event("strategy", "completed", 0.3, "策略生成完成")
    context.add_timeline_event("orchestrator", "completed", 2.1, "执行完成")
    
    print(f"\n✅ 时间线事件: {len(context.timeline)} 个")
    
    for event in context.timeline:
        print(f"   📍 {event['stage']}: {event['status']} ({event['duration']}s)")
    
    # 计算总耗时
    total_duration = context.get_total_duration()
    print(f"\n✅ 总耗时: {total_duration}s")
    
    # 验证
    assert len(context.timeline) == 3
    assert abs(total_duration - 3.9) < 0.01  # 浮点数比较
    
    print("\n" + "=" * 80)


def test_context_helper_methods():
    """测试 Context 辅助方法"""
    
    print("\n" + "=" * 80)
    print("测试 TestContext 辅助方法")
    print("=" * 80)
    
    # 测试 is_skip()
    context1 = TestContext(requirement="测试")
    context1.decision = {"action": "skip", "reason": "低风险"}
    
    print(f"\n✅ is_skip() 测试:")
    print(f"   - Decision action: {context1.decision['action']}")
    print(f"   - is_skip(): {context1.is_skip()}")
    
    assert context1.is_skip() == True
    
    # 测试 should_heal()
    context2 = TestContext(requirement="测试")
    context2.execution = {
        "summary": {"total": 5, "passed": 3, "failed": 2}
    }
    
    print(f"\n✅ should_heal() 测试:")
    print(f"   - Failed: {context2.execution['summary']['failed']}")
    print(f"   - should_heal(): {context2.should_heal()}")
    
    assert context2.should_heal() == True
    
    # 测试无失败的情况
    context3 = TestContext(requirement="测试")
    context3.execution = {
        "summary": {"total": 5, "passed": 5, "failed": 0}
    }
    
    print(f"\n✅ should_heal() 测试 (无失败):")
    print(f"   - Failed: {context3.execution['summary']['failed']}")
    print(f"   - should_heal(): {context3.should_heal()}")
    
    assert context3.should_heal() == False
    
    print("\n" + "=" * 80)


def test_context_serialization():
    """测试 Context 序列化"""
    
    print("\n" + "=" * 80)
    print("测试 TestContext 序列化")
    print("=" * 80)
    
    # 创建 context
    context = TestContext(
        requirement="测试需求",
        priority="P0",
        use_case_generator=True
    )
    
    context.decision = {"need_test": True}
    context.strategy = {"total_cases": 10}
    
    # 转换为字典
    context_dict = context.to_dict()
    
    print(f"\n✅ 转换为字典:")
    print(f"   - Keys: {list(context_dict.keys())}")
    print(f"   - Requirement: {context_dict['requirement']}")
    print(f"   - Decision: {context_dict['decision']}")
    
    # 从字典恢复
    context2 = TestContext.from_dict(context_dict)
    
    print(f"\n✅ 从字典恢复:")
    print(f"   - Requirement: {context2.requirement}")
    print(f"   - Decision: {context2.decision}")
    print(f"   - Trace ID: {context2.trace_id}")
    
    # 验证
    assert context2.requirement == "测试需求"
    assert context2.decision == {"need_test": True}
    assert context2.trace_id == context.trace_id
    
    print("\n" + "=" * 80)


def test_context_repr():
    """测试 Context 字符串表示"""
    
    print("\n" + "=" * 80)
    print("测试 TestContext 字符串表示")
    print("=" * 80)
    
    context = TestContext(requirement="测试")
    context.decision = {"need_test": True}
    context.strategy = {"total_cases": 10}
    context.execution = {"summary": {}}
    
    print(f"\n✅ Context 表示:")
    print(f"   {context}")
    
    # 验证包含关键信息
    repr_str = repr(context)
    assert "TestContext" in repr_str
    assert "trace_id" in repr_str
    assert "stages=3" in repr_str  # decision, strategy, execution
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    print("\n🚀 开始测试 TestContext\n")
    
    # 测试1: 创建
    test_context_creation()
    
    # 测试2: 阶段操作
    test_context_stage_operations()
    
    # 测试3: 时间线
    test_context_timeline()
    
    # 测试4: 辅助方法
    test_context_helper_methods()
    
    # 测试5: 序列化
    test_context_serialization()
    
    # 测试6: 字符串表示
    test_context_repr()
    
    print("\n🎉 所有测试完成！TestContext 已就绪\n")
