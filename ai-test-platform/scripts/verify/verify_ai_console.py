"""
AI测试控制台验收测试
完整验证前端页面、后端API、数据流转
"""
import requests
import json
import time
from datetime import datetime


class Colors:
    """终端颜色"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'


def print_section(title):
    """打印章节标题"""
    print(f"\n{'='*70}")
    print(f"{Colors.BLUE}{title}{Colors.RESET}")
    print('='*70)


def print_success(msg):
    """打印成功消息"""
    print(f"{Colors.GREEN}✅ {msg}{Colors.RESET}")


def print_error(msg):
    """打印错误消息"""
    print(f"{Colors.RED}❌ {msg}{Colors.RESET}")


def print_info(msg):
    """打印信息"""
    print(f"{Colors.YELLOW}ℹ️  {msg}{Colors.RESET}")


def test_1_backend_health():
    """测试1: 后端服务健康检查"""
    print_section("测试 1: 后端服务健康检查")
    
    modules = ['agent', 'strategy', 'orchestrator', 'healing', 'pipeline']
    all_healthy = True
    
    for module in modules:
        url = f"http://localhost:8000/api/{module}/health"
        try:
            response = requests.get(url, timeout=3)
            data = response.json()
            
            if data.get('status') == 'healthy':
                print_success(f"{module.upper()}: 健康")
            else:
                print_error(f"{module.upper()}: {data.get('status', 'unknown')}")
                all_healthy = False
                
        except Exception as e:
            print_error(f"{module.upper()}: 无法访问 - {str(e)}")
            all_healthy = False
    
    return all_healthy


def test_2_frontend_access():
    """测试2: 前端服务访问"""
    print_section("测试 2: 前端服务访问")
    
    try:
        response = requests.get("http://localhost:5173", timeout=5)
        
        if response.status_code == 200:
            print_success("前端服务正常运行")
            print_info("访问地址: http://localhost:5173")
            print_info("控制台页面: http://localhost:5173/ai-test-console")
            return True
        else:
            print_error(f"前端访问失败: {response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"前端访问失败: {str(e)}")
        return False


def test_3_pipeline_skip_scenario():
    """测试3: 跳过场景（文档修改）"""
    print_section("测试 3: 跳过场景 - 文档修改")
    
    data = {
        "requirement": "更新README文档，添加安装说明",
        "git_diff": "+## 安装\n+npm install",
        "context": {"priority": "P2"}
    }
    
    print_info(f"需求: {data['requirement']}")
    print_info("预期: AI判断跳过测试")
    
    try:
        response = requests.post(
            "http://localhost:8000/api/pipeline/run",
            json=data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            decision = result.get('decision', {})
            
            need_test = decision.get('need_test', True)
            
            if not need_test:
                print_success("AI正确判断：跳过测试")
                print_info(f"原因: {decision.get('reason', 'N/A')}")
                return True
            else:
                print_error("AI判断错误：不应该执行测试")
                return False
        else:
            print_error(f"API调用失败: {response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"测试失败: {str(e)}")
        return False


def test_4_pipeline_p0_scenario():
    """测试4: P0核心功能场景"""
    print_section("测试 4: P0核心功能 - 支付模块")
    
    data = {
        "requirement": "支付模块新增微信支付和支付宝支付功能",
        "git_diff": "+def wechat_pay(): pass\n+def alipay_pay(): pass",
        "context": {"priority": "P0"}
    }
    
    print_info(f"需求: {data['requirement']}")
    print_info("预期: 需要测试，高风险，全面覆盖")
    
    try:
        start_time = time.time()
        response = requests.post(
            "http://localhost:8000/api/pipeline/run",
            json=data,
            timeout=30
        )
        duration = time.time() - start_time
        
        if response.status_code == 200:
            result = response.json()
            
            # 验证决策
            decision = result.get('decision', {})
            if not decision.get('need_test'):
                print_error("AI判断错误：应该执行测试")
                return False
            
            print_success(f"AI决策正确: 需要测试")
            print_info(f"优先级: {decision.get('priority')}")
            print_info(f"风险等级: {decision.get('risk_level')}")
            print_info(f"置信度: {decision.get('confidence', 0)*100:.0f}%")
            
            # 验证策略
            strategy = result.get('strategy')
            if strategy:
                strategy_list = strategy.get('strategy', [])
                print_success(f"生成策略: {len(strategy_list)} 个模块")
                
                # 检查是否包含多种测试类型
                all_types = set()
                for module in strategy_list:
                    all_types.update(module.get('test_types', []))
                
                if len(all_types) >= 2:
                    print_success(f"测试类型: {', '.join(all_types)}")
                else:
                    print_error(f"测试类型不足: {', '.join(all_types)}")
            
            # 验证执行
            execution = result.get('execution')
            if execution:
                summary = execution.get('summary', {})
                print_success(f"执行完成: {summary.get('passed')}/{summary.get('total')}")
            
            # 验证报告
            report = result.get('report', {})
            if report:
                print_success(f"生成报告: {report.get('summary', {}).get('status')}")
            
            print_info(f"总耗时: {duration:.2f}秒")
            print_info(f"Trace ID: {result.get('trace_id')}")
            
            return True
            
        else:
            print_error(f"API调用失败: {response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"测试失败: {str(e)}")
        return False


def test_5_pipeline_p2_scenario():
    """测试5: P2一般功能场景"""
    print_section("测试 5: P2一般功能 - 日志查询")
    
    data = {
        "requirement": "添加系统日志查询功能",
        "git_diff": "+def query_logs(): pass",
        "context": {"priority": "P2"}
    }
    
    print_info(f"需求: {data['requirement']}")
    print_info("预期: 需要测试，低风险，仅API测试")
    
    try:
        response = requests.post(
            "http://localhost:8000/api/pipeline/run",
            json=data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            decision = result.get('decision', {})
            
            if decision.get('need_test'):
                print_success("AI决策正确: 需要测试")
                
                # 验证风险等级
                risk = decision.get('risk_level', '')
                if risk in ['低', '中']:
                    print_success(f"风险评估正确: {risk}")
                else:
                    print_error(f"风险评估异常: {risk}")
                
                # 验证策略
                strategy = result.get('strategy')
                if strategy:
                    strategy_list = strategy.get('strategy', [])
                    all_types = set()
                    for module in strategy_list:
                        all_types.update(module.get('test_types', []))
                    
                    print_info(f"测试类型: {', '.join(all_types)}")
                
                return True
            else:
                print_error("AI判断错误：应该执行测试")
                return False
        else:
            print_error(f"API调用失败: {response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"测试失败: {str(e)}")
        return False


def test_6_trace_query():
    """测试6: Trace ID查询"""
    print_section("测试 6: Trace ID查询功能")
    
    # 先执行一次获取trace_id
    data = {
        "requirement": "测试Trace查询功能",
        "context": {"priority": "P1"}
    }
    
    try:
        response = requests.post(
            "http://localhost:8000/api/pipeline/run",
            json=data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            trace_id = result.get('trace_id')
            
            print_info(f"生成 Trace ID: {trace_id}")
            
            # 查询这个trace_id
            query_url = f"http://localhost:8000/api/pipeline/trace/{trace_id}"
            query_response = requests.get(query_url, timeout=5)
            
            if query_response.status_code == 200:
                query_data = query_response.json()
                
                if query_data.get('success') and query_data.get('data'):
                    print_success("Trace查询成功")
                    print_info(f"查询到的Trace ID: {query_data['data'].get('trace_id')}")
                    return True
                else:
                    print_error("Trace查询返回数据异常")
                    return False
            else:
                print_error(f"Trace查询失败: {query_response.status_code}")
                return False
        else:
            print_error("无法生成Trace ID")
            return False
            
    except Exception as e:
        print_error(f"测试失败: {str(e)}")
        return False


def test_7_statistics():
    """测试7: 统计信息查询"""
    print_section("测试 7: 统计信息查询")
    
    try:
        response = requests.get("http://localhost:8000/api/pipeline/statistics", timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get('success'):
                stats = data.get('data', {})
                print_success("统计信息查询成功")
                print_info(f"总执行次数: {stats.get('total_runs', 0)}")
                print_info(f"跳过次数: {stats.get('skipped_runs', 0)}")
                print_info(f"平均耗时: {stats.get('avg_duration', 0):.2f}秒")
                return True
            else:
                print_error("统计信息返回失败")
                return False
        else:
            print_error(f"API调用失败: {response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"测试失败: {str(e)}")
        return False


def test_8_history():
    """测试8: 历史记录查询"""
    print_section("测试 8: 历史记录查询")
    
    try:
        response = requests.get("http://localhost:8000/api/pipeline/history?limit=5", timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get('success'):
                history = data.get('data', [])
                count = data.get('count', 0)
                
                print_success(f"历史记录查询成功: {count} 条记录")
                
                if count > 0:
                    latest = history[0]
                    print_info(f"最新记录 Trace ID: {latest.get('trace_id')}")
                    print_info(f"状态: {latest.get('report', {}).get('summary', {}).get('status')}")
                
                return True
            else:
                print_error("历史记录返回失败")
                return False
        else:
            print_error(f"API调用失败: {response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"测试失败: {str(e)}")
        return False


def main():
    """主验收流程"""
    print("\n" + "="*70)
    print(f"{Colors.BLUE}🚀 AI测试控制台验收测试{Colors.RESET}")
    print("="*70)
    print(f"\n开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 执行所有测试
    tests = [
        ("后端服务健康检查", test_1_backend_health),
        ("前端服务访问", test_2_frontend_access),
        ("跳过场景测试", test_3_pipeline_skip_scenario),
        ("P0核心功能测试", test_4_pipeline_p0_scenario),
        ("P2一般功能测试", test_5_pipeline_p2_scenario),
        ("Trace查询功能", test_6_trace_query),
        ("统计信息查询", test_7_statistics),
        ("历史记录查询", test_8_history),
    ]
    
    results = []
    
    for name, test_func in tests:
        try:
            passed = test_func()
            results.append((name, passed))
        except Exception as e:
            print_error(f"测试异常: {str(e)}")
            results.append((name, False))
    
    # 汇总结果
    print_section("📊 验收结果汇总")
    
    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)
    pass_rate = (passed_count / total_count * 100) if total_count > 0 else 0
    
    for name, passed in results:
        if passed:
            print_success(f"{name}")
        else:
            print_error(f"{name}")
    
    print(f"\n{'='*70}")
    print(f"通过率: {passed_count}/{total_count} ({pass_rate:.1f}%)")
    print('='*70)
    
    if passed_count == total_count:
        print(f"\n{Colors.GREEN}🎉 验收通过！AI测试控制台已就绪{Colors.RESET}")
        print("\n" + "="*70)
        print("📍 快速访问")
        print("="*70)
        print("\n1. 前端控制台:")
        print("   http://localhost:5173/ai-test-console")
        print("\n2. 后端API文档:")
        print("   http://localhost:8000/docs")
        print("\n3. 快速测试页面:")
        print("   打开 frontend/test_ai_console.html")
        
        print("\n" + "="*70)
        print("💡 使用建议")
        print("="*70)
        print("\n【快速验证场景】")
        print("  • 代码提交前验证")
        print("  • 功能变更影响分析")
        print("  • 回归测试执行")
        print("  • Bug修复验证")
        
        print("\n【完整测试场景】")
        print("  • 新功能开发")
        print("  • 需要测试文档")
        print("  • 复杂业务逻辑")
        print("  • 使用传统流程（/projects页面）")
        
        print("\n" + "="*70)
        print("🔄 两种模式互补使用")
        print("="*70)
        print("\n  AI控制台（快）: 10-20秒，快速验证")
        print("  传统流程（全）: 数分钟，完整文档")
        
    else:
        print(f"\n{Colors.RED}⚠️ 验收未通过: {total_count - passed_count} 项测试失败{Colors.RESET}")
        print("\n请检查:")
        print("  1. 后端服务是否正常运行 (python backend_api_server.py)")
        print("  2. 前端服务是否正常运行 (npm run dev)")
        print("  3. Ollama服务是否启动")
    
    print(f"\n结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    return passed_count == total_count


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
