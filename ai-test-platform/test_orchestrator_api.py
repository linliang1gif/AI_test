"""
测试 Orchestrator API 接口
验证 HTTP 接口是否正常工作
"""
import requests
import json


BASE_URL = "http://localhost:8000/api"


def test_orchestrator_run_api():
    """测试1：执行测试 API"""
    print("\n" + "="*60)
    print("测试1：POST /orchestrator/run")
    print("="*60)
    
    # 准备策略数据
    strategy = {
        "strategy": [
            {
                "module": {"name": "支付模块", "impact": "high"},
                "priority": "P0",
                "test_types": ["api", "ui"],
                "case_count": 30,
                "execution_order": 1,
                "risk_level": "高",
                "execution_hint": {"parallel": True, "timeout": 60}
            },
            {
                "module": {"name": "订单模块", "impact": "medium"},
                "priority": "P1",
                "test_types": ["api"],
                "case_count": 20,
                "execution_order": 2,
                "risk_level": "中",
                "execution_hint": {"parallel": True, "timeout": 90}
            }
        ],
        "summary": {
            "total_modules": 2,
            "estimated_total_cases": 50,
            "risk_level": "高"
        }
    }
    
    # 发送请求
    response = requests.post(
        f"{BASE_URL}/orchestrator/run",
        json={"strategy": strategy},
        timeout=30
    )
    
    print(f"状态码: {response.status_code}")
    
    if response.status_code != 200:
        print(f"❌ 请求失败: {response.text}")
        return False
    
    result = response.json()
    
    # 验证响应结构
    assert "results" in result, "❌ 缺少 results"
    assert "summary" in result, "❌ 缺少 summary"
    assert "executed_at" in result, "❌ 缺少 executed_at"
    
    # 验证结果
    assert len(result["results"]) == 2, f"❌ 应该有2个结果，实际{len(result['results'])}"
    
    summary = result["summary"]
    assert summary["total"] == 2, f"❌ total 应为2，实际{summary['total']}"
    
    print(f"✅ API 调用成功:")
    print(f"   - 执行模块: {summary['total']}")
    print(f"   - 通过: {summary['passed']}")
    print(f"   - 失败: {summary['failed']}")
    print(f"   - 通过率: {summary['pass_rate']}%")
    print(f"   - 耗时: {summary['duration']}s")
    
    print(f"\n   执行详情:")
    for r in result["results"]:
        status_icon = "✅" if r['status'] == 'passed' else "❌"
        print(f"   {status_icon} {r['module']}: {r['status']} ({r['duration']}s)")
    
    return True


def test_orchestrator_health_api():
    """测试2：健康检查 API"""
    print("\n" + "="*60)
    print("测试2：GET /orchestrator/health")
    print("="*60)
    
    response = requests.get(f"{BASE_URL}/orchestrator/health", timeout=10)
    
    print(f"状态码: {response.status_code}")
    
    if response.status_code != 200:
        print(f"❌ 请求失败: {response.text}")
        return False
    
    result = response.json()
    
    assert "status" in result, "❌ 缺少 status"
    assert result["status"] == "healthy", f"❌ 状态应为 healthy，实际{result['status']}"
    
    print(f"✅ 健康检查通过:")
    print(f"   - 状态: {result['status']}")
    print(f"   - 执行次数: {result.get('executions_count', 0)}")
    
    return True


def test_orchestrator_history_api():
    """测试3：历史记录 API"""
    print("\n" + "="*60)
    print("测试3：GET /orchestrator/history")
    print("="*60)
    
    response = requests.get(f"{BASE_URL}/orchestrator/history?limit=5", timeout=10)
    
    print(f"状态码: {response.status_code}")
    
    if response.status_code != 200:
        print(f"❌ 请求失败: {response.text}")
        return False
    
    result = response.json()
    
    assert "success" in result, "❌ 缺少 success"
    assert "data" in result, "❌ 缺少 data"
    assert "count" in result, "❌ 缺少 count"
    
    print(f"✅ 历史记录获取成功:")
    print(f"   - 记录数: {result['count']}")
    
    if result['count'] > 0:
        print(f"   - 最新记录时间: {result['data'][0].get('timestamp', 'N/A')}")
    
    return True


def test_orchestrator_statistics_api():
    """测试4：统计信息 API"""
    print("\n" + "="*60)
    print("测试4：GET /orchestrator/statistics")
    print("="*60)
    
    response = requests.get(f"{BASE_URL}/orchestrator/statistics", timeout=10)
    
    print(f"状态码: {response.status_code}")
    
    if response.status_code != 200:
        print(f"❌ 请求失败: {response.text}")
        return False
    
    result = response.json()
    
    assert "success" in result, "❌ 缺少 success"
    assert "data" in result, "❌ 缺少 data"
    
    stats = result["data"]
    assert "total_executions" in stats, "❌ 缺少 total_executions"
    assert "total_tests" in stats, "❌ 缺少 total_tests"
    assert "avg_pass_rate" in stats, "❌ 缺少 avg_pass_rate"
    
    print(f"✅ 统计信息获取成功:")
    print(f"   - 总执行次数: {stats['total_executions']}")
    print(f"   - 总测试数: {stats['total_tests']}")
    print(f"   - 平均通过率: {stats['avg_pass_rate']}%")
    
    return True


def test_full_api_pipeline():
    """测试5：完整 API 流程"""
    print("\n" + "="*60)
    print("测试5：完整 API 流程 (Agent → Strategy → Orchestrator)")
    print("="*60)
    
    # 步骤1: Agent 分析
    print("\n  步骤1: Agent 分析")
    agent_response = requests.post(
        f"{BASE_URL}/agent/analyze",
        json={
            "requirement": "新增用户注册功能",
            "git_diff": "diff --git a/user/register.py"
        },
        timeout=30
    )
    
    if agent_response.status_code != 200:
        print(f"  ❌ Agent 失败: {agent_response.text}")
        return False
    
    agent_result = agent_response.json()
    print(f"  ✅ Agent: action={agent_result['action']}, modules={len(agent_result['modules'])}")
    
    # 步骤2: Strategy 生成
    print("\n  步骤2: Strategy 生成")
    strategy_response = requests.post(
        f"{BASE_URL}/strategy/generate",
        json={"agent_decision": agent_result},
        timeout=30
    )
    
    if strategy_response.status_code != 200:
        print(f"  ❌ Strategy 失败: {strategy_response.text}")
        return False
    
    strategy_result = strategy_response.json()
    print(f"  ✅ Strategy: modules={strategy_result['summary']['total_modules']}, cases={strategy_result['summary']['estimated_total_cases']}")
    
    # 步骤3: Orchestrator 执行
    print("\n  步骤3: Orchestrator 执行")
    orchestrator_response = requests.post(
        f"{BASE_URL}/orchestrator/run",
        json={"strategy": strategy_result},
        timeout=30
    )
    
    if orchestrator_response.status_code != 200:
        print(f"  ❌ Orchestrator 失败: {orchestrator_response.text}")
        return False
    
    execution_result = orchestrator_response.json()
    print(f"  ✅ Orchestrator: passed={execution_result['summary']['passed']}/{execution_result['summary']['total']}")
    
    print(f"\n✅ 完整 API 流程成功:")
    print(f"   - Agent → Strategy → Orchestrator")
    print(f"   - 最终通过率: {execution_result['summary']['pass_rate']}%")
    
    return True


def main():
    """运行所有 API 测试"""
    print("\n" + "🌐 " + "="*58)
    print("🌐  Orchestrator API 接口测试")
    print("🌐 " + "="*58)
    print("\n⚠️  请确保后端服务已启动: http://localhost:8000")
    
    tests = [
        ("执行测试 API", test_orchestrator_run_api),
        ("健康检查 API", test_orchestrator_health_api),
        ("历史记录 API", test_orchestrator_history_api),
        ("统计信息 API", test_orchestrator_statistics_api),
        ("完整 API 流程", test_full_api_pipeline)
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            if test_func():
                passed += 1
        except AssertionError as e:
            print(f"\n❌ 测试失败: {name}")
            print(f"   错误: {e}")
            failed += 1
        except requests.exceptions.ConnectionError:
            print(f"\n❌ 连接失败: {name}")
            print(f"   请确保后端服务已启动")
            failed += 1
        except Exception as e:
            print(f"\n❌ 测试异常: {name}")
            print(f"   错误: {e}")
            failed += 1
    
    # 总结
    print("\n" + "="*60)
    print("📊 API 测试总结")
    print("="*60)
    print(f"✅ 通过: {passed}/{len(tests)}")
    print(f"❌ 失败: {failed}/{len(tests)}")
    
    if failed == 0:
        print("\n🎉 所有 Orchestrator API 测试通过！")
        return True
    else:
        print(f"\n⚠️  有 {failed} 个测试失败")
        return False


if __name__ == "__main__":
    import sys
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ API 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
