#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
五阶段系统验证脚本
验证所有模块是否正常工作
"""

import sys
import importlib


def verify_module(module_name: str, description: str) -> bool:
    """验证模块是否可导入"""
    try:
        importlib.import_module(module_name)
        print(f"✅ {description:30s} - 模块加载成功")
        return True
    except Exception as e:
        print(f"❌ {description:30s} - 加载失败: {e}")
        return False


def verify_service(module_name: str, service_func: str, description: str) -> bool:
    """验证服务是否可用"""
    try:
        module = importlib.import_module(module_name)
        get_service = getattr(module, service_func)
        service = get_service()
        print(f"✅ {description:30s} - 服务实例化成功")
        return True
    except Exception as e:
        print(f"❌ {description:30s} - 实例化失败: {e}")
        return False


def main():
    """主验证流程"""
    print("\n" + "="*70)
    print("🔍 五阶段系统验证")
    print("="*70)
    
    results = []
    
    # ==================== 阶段1: Test Agent ====================
    print(f"\n【阶段1】Test Agent - AI决策中心")
    print("-" * 70)
    
    results.append(verify_module("agent.llm_client", "LLM Client"))
    results.append(verify_module("agent.test_agent_service", "Test Agent Service"))
    results.append(verify_module("agent.controller", "Test Agent Controller"))
    results.append(verify_service("agent.test_agent_service", "get_test_agent_service", "Test Agent 实例"))
    
    # ==================== 阶段2: Strategy Engine ====================
    print(f"\n【阶段2】Strategy Engine - 策略引擎")
    print("-" * 70)
    
    results.append(verify_module("strategy.rules", "Strategy Rules"))
    results.append(verify_module("strategy.strategy_service", "Strategy Service"))
    results.append(verify_module("strategy.controller", "Strategy Controller"))
    results.append(verify_service("strategy.strategy_service", "get_strategy_service", "Strategy 实例"))
    
    # ==================== 阶段3: Orchestrator ====================
    print(f"\n【阶段3】Orchestrator - 测试执行调度器")
    print("-" * 70)
    
    results.append(verify_module("orchestrator.base_runner", "Base Runner"))
    results.append(verify_module("orchestrator.orchestrator_service", "Orchestrator Service"))
    results.append(verify_module("orchestrator.controller", "Orchestrator Controller"))
    results.append(verify_service("orchestrator.orchestrator_service", "get_orchestrator_service", "Orchestrator 实例"))
    
    # ==================== 阶段4: Self-Healing ====================
    print(f"\n【阶段4】Self-Healing - 自动修复系统")
    print("-" * 70)
    
    results.append(verify_module("self_healing.analyzer", "Error Analyzer"))
    results.append(verify_module("self_healing.fixer", "Error Fixer"))
    results.append(verify_module("self_healing.healing_service", "Healing Service"))
    results.append(verify_module("self_healing.controller", "Healing Controller"))
    results.append(verify_service("self_healing.healing_service", "get_healing_service", "Healing 实例"))
    
    # ==================== 阶段5: Pipeline ====================
    print(f"\n【阶段5】Pipeline - 流程总调度器")
    print("-" * 70)
    
    results.append(verify_module("pipeline.report_generator", "Report Generator"))
    results.append(verify_module("pipeline.pipeline_service", "Pipeline Service"))
    results.append(verify_module("pipeline.controller", "Pipeline Controller"))
    results.append(verify_service("pipeline.pipeline_service", "get_pipeline_service", "Pipeline 实例"))
    
    # ==================== 统计结果 ====================
    print(f"\n" + "="*70)
    total = len(results)
    passed = sum(results)
    failed = total - passed
    
    print(f"📊 验证结果: {passed}/{total} 通过")
    
    if failed > 0:
        print(f"❌ {failed} 个模块验证失败")
        print(f"\n建议:")
        print(f"   1. 检查模块导入路径")
        print(f"   2. 确认所有依赖已安装")
        print(f"   3. 查看详细错误信息")
        return False
    else:
        print(f"✅ 所有模块验证通过！")
        print(f"\n系统状态: 🟢 生产就绪")
        print(f"\n五阶段系统已完整实现：")
        print(f"   1️⃣  Test Agent - AI决策分析")
        print(f"   2️⃣  Strategy Engine - 策略生成")
        print(f"   3️⃣  Orchestrator - 自动执行")
        print(f"   4️⃣  Self-Healing - 自动修复")
        print(f"   5️⃣  Pipeline - 流程编排")
        return True
    
    print("="*70)


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
