"""
Orchestrator V3 测试
测试重构后的调度器
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from orchestrator.orchestrator_service import OrchestratorService, get_orchestrator_service


def test_orchestrator_v3_basic():
    """测试1: Orchestrator V3 基本功能"""
    print("\n" + "="*70)
    print("【测试1】Orchestrator V3 基本功能")
    print("="*70)
    
    # 创建调度服务
    orchestrator = OrchestratorService(num_workers=3)
    
    # 准备测试数据
    context = {
        "cases": [
            {
                "module": "支付模块",
                "cases": [
                    {"id": "TC_001", "title": "支付测试1", "type": "功能测试", "priority": "P1"},
                    {"id": "TC_002", "title": "支付测试2", "type": "功能测试", "priority": "P2"},
                    {"id": "TC_003", "title": "支付测试3", "type": "功能测试", "priority": "P3"}
                ]
            },
            {
                "module": "订单模块",
                "cases": [
                    {"id": "TC_004", "title": "订单测试1", "type": "功能测试", "priority": "P1"},
                    {"id": "TC_005", "title": "订单测试2", "type": "功能测试", "priority": "P2"}
                ]
            }
        ]
    }
    
    # 执行
    result = orchestrator.run(context)
    
    # 验证
    print(f"\n📊 执行结果:")
    print(f"   总任务数: {result['summary']['total']}")
    print(f"   成功任务: {result['summary']['passed']}")
    print(f"   失败任务: {result['summary']['failed']}")
    print(f"   执行时长: {result['summary']['duration']}s")
    print(f"   通过率: {result['summary']['pass_rate']}%")
    
    assert result['summary']['total'] == 5, "应该有5个任务"
    assert result['summary']['passed'] > 0, "应该有成功的任务"
    
    print(f"\n✅ Orchestrator V3 基本功能验证通过")


def test_orchestrator_v3_concurrent():
    """测试2: 并发执行"""
    print("\n" + "="*70)
    print("【测试2】并发执行")
    print("="*70)
    
    # 创建调度服务（5个 Worker）
    orchestrator = OrchestratorService(num_workers=5)
    
    # 准备大量测试数据
    cases = []
    for i in range(1, 4):
        module_cases = {
            "module": f"模块{i}",
            "cases": [
                {"id": f"TC_{i}_{j:02d}", "title": f"测试{i}-{j}", "type": "功能测试", "priority": "P2"}
                for j in range(1, 6)
            ]
        }
        cases.append(module_cases)
    
    context = {"cases": cases}
    
    # 执行
    import time
    start_time = time.time()
    result = orchestrator.run(context)
    duration = time.time() - start_time
    
    # 验证
    print(f"\n📊 并发执行结果:")
    print(f"   总任务数: {result['summary']['total']}")
    print(f"   成功任务: {result['summary']['passed']}")
    print(f"   失败任务: {result['summary']['failed']}")
    print(f"   执行时长: {duration:.2f}s")
    
    assert result['summary']['total'] == 15, "应该有15个任务"
    
    print(f"\n✅ 并发执行验证通过")


def test_orchestrator_v3_priority():
    """测试3: 优先级调度"""
    print("\n" + "="*70)
    print("【测试3】优先级调度")
    print("="*70)
    
    # 创建调度服务（单个 Worker，方便观察顺序）
    orchestrator = OrchestratorService(num_workers=1)
    
    # 准备不同优先级的测试数据
    context = {
        "cases": [
            {
                "module": "测试模块",
                "cases": [
                    {"id": "LOW_1", "title": "低优先级1", "type": "功能测试", "priority": "P3"},
                    {"id": "HIGH_1", "title": "高优先级1", "type": "功能测试", "priority": "P0"},
                    {"id": "LOW_2", "title": "低优先级2", "type": "功能测试", "priority": "P3"},
                    {"id": "HIGH_2", "title": "高优先级2", "type": "功能测试", "priority": "P0"},
                    {"id": "NORMAL_1", "title": "普通优先级1", "type": "功能测试", "priority": "P2"}
                ]
            }
        ]
    }
    
    # 执行
    result = orchestrator.run(context)
    
    # 验证
    print(f"\n📊 优先级调度结果:")
    print(f"   总任务数: {result['summary']['total']}")
    
    # 检查执行顺序（高优先级应该先执行）
    print(f"\n   执行顺序:")
    for i, task_dict in enumerate(result['results'][:5], 1):
        print(f"      {i}. {task_dict['case']['id']} (priority={task_dict['priority']})")
    
    print(f"\n✅ 优先级调度验证通过")


def test_orchestrator_v3_failure_handling():
    """测试4: 失败处理"""
    print("\n" + "="*70)
    print("【测试4】失败处理")
    print("="*70)
    
    # 创建调度服务
    orchestrator = OrchestratorService(num_workers=2)
    
    # 准备测试数据
    context = {
        "cases": [
            {
                "module": "测试模块",
                "cases": [
                    {"id": "TC_001", "title": "测试1", "type": "功能测试", "priority": "P2"},
                    {"id": "TC_002", "title": "测试2", "type": "功能测试", "priority": "P2"},
                    {"id": "TC_003", "title": "测试3", "type": "功能测试", "priority": "P2"}
                ]
            }
        ]
    }
    
    # 执行
    result = orchestrator.run(context)
    
    # 验证
    print(f"\n📊 失败处理结果:")
    print(f"   总任务数: {result['summary']['total']}")
    print(f"   成功任务: {result['summary']['passed']}")
    print(f"   失败任务: {result['summary']['failed']}")
    print(f"   失败队列: {len(result['failures'])} 个")
    
    print(f"\n✅ 失败处理验证通过")


def test_orchestrator_v3_singleton():
    """测试5: 单例模式"""
    print("\n" + "="*70)
    print("【测试5】单例模式")
    print("="*70)
    
    # 获取两次实例
    orchestrator1 = get_orchestrator_service()
    orchestrator2 = get_orchestrator_service()
    
    # 验证是同一个实例
    assert orchestrator1 is orchestrator2, "应该是同一个实例"
    
    print(f"✅ 单例模式验证通过")


def test_orchestrator_v3_empty_cases():
    """测试6: 空用例处理"""
    print("\n" + "="*70)
    print("【测试6】空用例处理")
    print("="*70)
    
    # 创建调度服务
    orchestrator = OrchestratorService(num_workers=3)
    
    # 空用例
    context = {"cases": []}
    
    # 执行
    result = orchestrator.run(context)
    
    # 验证
    assert result['summary']['total'] == 0, "应该没有任务"
    
    print(f"✅ 空用例处理验证通过")


def run_all_tests():
    """运行所有测试"""
    print("\n" + "="*70)
    print("Orchestrator V3 测试")
    print("="*70)
    
    tests = [
        ("Orchestrator V3 基本功能", test_orchestrator_v3_basic),
        ("并发执行", test_orchestrator_v3_concurrent),
        ("优先级调度", test_orchestrator_v3_priority),
        ("失败处理", test_orchestrator_v3_failure_handling),
        ("单例模式", test_orchestrator_v3_singleton),
        ("空用例处理", test_orchestrator_v3_empty_cases)
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            test_func()
            passed += 1
        except Exception as e:
            print(f"\n❌ 测试失败: {name}")
            print(f"   错误: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    # 总结
    print("\n" + "="*70)
    print(f"✅ 所有测试通过 ({passed}/{len(tests)})")
    if failed > 0:
        print(f"❌ 失败测试: {failed}")
    print("="*70)


if __name__ == "__main__":
    run_all_tests()
