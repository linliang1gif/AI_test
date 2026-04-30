"""
测试 Pipeline V3 集成（接入新调度系统）

验证目标：
1. Pipeline 正确接入 Orchestrator V3
2. Pipeline 正确接入 Healing Worker
3. 完整流程可以正常运行
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from pipeline.pipeline_service import get_pipeline_service
from common.context import TestContext


def test_pipeline_v3_with_orchestrator():
    """测试 Pipeline V3 接入 Orchestrator V3"""
    print("\n" + "="*70)
    print("测试1: Pipeline V3 接入 Orchestrator V3")
    print("="*70)
    
    pipeline = get_pipeline_service()
    
    # 准备输入
    input_data = {
        "requirement": "测试支付模块的退款功能",
        "git_diff": "修改了 payment_service.py 的 refund() 方法",
        "priority": "P1",
        "use_case_generator": False  # 不使用 Case Generator，直接测试 Orchestrator
    }
    
    # 运行 Pipeline
    result = pipeline.run_pipeline(input_data)
    
    # 验证结果
    assert result is not None, "Pipeline 返回结果不能为空"
    assert "execution" in result, "结果中必须包含 execution"
    
    execution = result["execution"]
    assert execution is not None, "execution 不能为空"
    assert "mode" in execution, "execution 必须包含 mode"
    assert execution["mode"] == "v3_scheduler", f"执行模式应该是 v3_scheduler，实际是 {execution['mode']}"
    
    print(f"\n✅ 测试通过")
    print(f"   执行模式: {execution['mode']}")
    print(f"   执行结果: {execution.get('summary', {})}")
    
    return result


def test_pipeline_v3_with_healing():
    """测试 Pipeline V3 接入 Healing Worker"""
    print("\n" + "="*70)
    print("测试2: Pipeline V3 接入 Healing Worker")
    print("="*70)
    
    pipeline = get_pipeline_service()
    
    # 准备输入（模拟会有失败的场景）
    input_data = {
        "requirement": "测试订单模块的创建和查询功能",
        "git_diff": "修改了 order_service.py",
        "priority": "P1",
        "use_case_generator": False
    }
    
    # 运行 Pipeline
    result = pipeline.run_pipeline(input_data)
    
    # 验证结果
    assert result is not None, "Pipeline 返回结果不能为空"
    
    # 检查是否有失败任务
    execution = result.get("execution", {})
    failed_count = execution.get("summary", {}).get("failed", 0)
    
    print(f"\n   失败任务数: {failed_count}")
    
    if failed_count > 0:
        # 应该有 healing 结果
        assert "healing" in result, "有失败任务时，结果中必须包含 healing"
        healing = result["healing"]
        assert healing is not None, "healing 不能为空"
        assert "summary" in healing, "healing 必须包含 summary"
        
        print(f"   修复结果: {healing.get('summary', {})}")
        print(f"✅ Healing Worker 正常工作")
    else:
        print(f"   没有失败任务，跳过修复")
        print(f"✅ 测试通过（无需修复）")
    
    return result


def test_pipeline_v3_complete_flow():
    """测试 Pipeline V3 完整流程"""
    print("\n" + "="*70)
    print("测试3: Pipeline V3 完整流程")
    print("="*70)
    
    pipeline = get_pipeline_service()
    
    # 准备输入
    input_data = {
        "requirement": "测试用户模块的注册、登录、修改密码功能",
        "git_diff": "新增了 user_service.py",
        "priority": "P0",
        "use_case_generator": True  # 使用完整流程
    }
    
    # 运行 Pipeline
    result = pipeline.run_pipeline(input_data)
    
    # 验证完整流程
    assert result is not None, "Pipeline 返回结果不能为空"
    
    # 验证各阶段
    stages = ["decision", "strategy", "execution", "report"]
    for stage in stages:
        assert stage in result, f"结果中必须包含 {stage}"
        assert result[stage] is not None, f"{stage} 不能为空"
    
    # 验证 timeline
    assert "timeline" in result, "结果中必须包含 timeline"
    timeline = result["timeline"]
    assert len(timeline) > 0, "timeline 不能为空"
    
    print(f"\n✅ 完整流程测试通过")
    print(f"   阶段数: {len(timeline)}")
    print(f"   总耗时: {sum(e.get('duration', 0) for e in timeline):.2f}s")
    
    # 打印各阶段耗时
    print(f"\n   各阶段耗时:")
    for event in timeline:
        stage = event.get('stage', 'unknown')
        duration = event.get('duration', 0)
        status = event.get('status', 'unknown')
        print(f"      {stage}: {duration:.2f}s ({status})")
    
    return result


def test_context_flow():
    """测试 TestContext 数据流"""
    print("\n" + "="*70)
    print("测试4: TestContext 数据流")
    print("="*70)
    
    # 创建 TestContext
    context = TestContext(
        requirement="测试商品模块",
        git_diff="修改了 product_service.py",
        priority="P1"
    )
    
    print(f"   初始 Context: {context}")
    
    # 模拟各阶段写入数据
    context.decision = {"need_test": True, "action": "test"}
    context.add_timeline_event("agent", "completed", 1.5)
    
    context.strategy = {"strategy": [], "total_cases": 10}
    context.add_timeline_event("strategy", "completed", 2.0)
    
    context.execution = {
        "results": [],
        "failures": [],
        "summary": {"total": 10, "passed": 8, "failed": 2}
    }
    context.add_timeline_event("orchestrator", "completed", 5.0)
    
    # 验证数据流
    assert context.decision is not None, "decision 应该被写入"
    assert context.strategy is not None, "strategy 应该被写入"
    assert context.execution is not None, "execution 应该被写入"
    assert len(context.timeline) == 3, "timeline 应该有3个事件"
    
    # 验证辅助方法
    assert context.should_heal() == True, "有失败任务时应该返回 True"
    assert context.is_skip() == False, "action 不是 skip 时应该返回 False"
    
    total_duration = context.get_total_duration()
    assert total_duration == 8.5, f"总耗时应该是 8.5s，实际是 {total_duration}s"
    
    print(f"✅ TestContext 数据流测试通过")
    print(f"   总耗时: {total_duration}s")
    print(f"   需要修复: {context.should_heal()}")
    
    return context


def test_extract_cases_logic():
    """测试用例提取逻辑"""
    print("\n" + "="*70)
    print("测试5: 用例提取逻辑")
    print("="*70)
    
    from pipeline.pipeline_service import PipelineService
    
    pipeline = PipelineService()
    
    # 场景1: 有 cases（Case Generator 生成）
    context1 = TestContext()
    context1.cases = {
        "cases": [
            {
                "module": "支付模块",
                "cases": [
                    {"name": "测试支付", "type": "api"}
                ]
            }
        ]
    }
    
    extracted1 = pipeline._extract_cases_for_orchestrator(context1)
    assert len(extracted1) == 1, "应该提取到1个模块"
    assert extracted1[0]["module"] == "支付模块", "模块名应该是'支付模块'"
    print(f"   场景1（有cases）: 提取到 {len(extracted1)} 个模块 ✅")
    
    # 场景2: 只有 strategy（没有 Case Generator）
    context2 = TestContext()
    context2.strategy = {
        "strategy": [
            {
                "module": "订单模块",
                "test_points": [
                    {"name": "测试创建订单", "type": "功能测试", "priority": "P1"}
                ]
            }
        ]
    }
    
    extracted2 = pipeline._extract_cases_for_orchestrator(context2)
    assert len(extracted2) == 1, "应该提取到1个模块"
    assert extracted2[0]["module"] == "订单模块", "模块名应该是'订单模块'"
    assert len(extracted2[0]["cases"]) == 1, "应该有1个用例"
    print(f"   场景2（只有strategy）: 提取到 {len(extracted2)} 个模块 ✅")
    
    # 场景3: 都没有
    context3 = TestContext()
    extracted3 = pipeline._extract_cases_for_orchestrator(context3)
    assert len(extracted3) == 0, "应该返回空列表"
    print(f"   场景3（都没有）: 返回空列表 ✅")
    
    print(f"\n✅ 用例提取逻辑测试通过")


def main():
    """运行所有测试"""
    print("\n" + "="*70)
    print("Pipeline V3 集成测试")
    print("="*70)
    
    try:
        # 测试1: Orchestrator V3 集成
        test_pipeline_v3_with_orchestrator()
        
        # 测试2: Healing Worker 集成
        test_pipeline_v3_with_healing()
        
        # 测试3: 完整流程
        test_pipeline_v3_complete_flow()
        
        # 测试4: TestContext 数据流
        test_context_flow()
        
        # 测试5: 用例提取逻辑
        test_extract_cases_logic()
        
        print("\n" + "="*70)
        print("✅ 所有测试通过")
        print("="*70)
        
    except AssertionError as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
    except Exception as e:
        print(f"\n❌ 测试异常: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
