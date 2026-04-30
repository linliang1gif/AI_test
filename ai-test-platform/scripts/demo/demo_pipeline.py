#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pipeline 演示脚本
展示一键自动测试系统的完整流程
"""

import requests
import json
import time


BASE_URL = "http://localhost:8000/api"


def demo_scenario_1():
    """场景1: 核心功能变更 - 完整执行"""
    print("\n" + "="*70)
    print("📋 场景1: 支付功能变更（核心功能）")
    print("="*70)
    
    payload = {
        "requirement": "支付模块需要支持微信支付和支付宝支付",
        "git_diff": """
+def wechat_pay(order_id, amount):
+    # 调用微信支付API
+    return process_payment('wechat', order_id, amount)
+
+def alipay(order_id, amount):
+    # 调用支付宝API
+    return process_payment('alipay', order_id, amount)
""",
        "context": {"priority": "P0", "module": "payment"}
    }
    
    print(f"\n📤 发送请求...")
    response = requests.post(f"{BASE_URL}/pipeline/run", json=payload)
    
    if response.status_code == 200:
        data = response.json()
        print_pipeline_result(data)
    else:
        print(f"❌ 请求失败: {response.status_code}")
        print(response.text)


def demo_scenario_2():
    """场景2: 文档变更 - 跳过执行"""
    print("\n" + "="*70)
    print("📋 场景2: README文档更新（低风险）")
    print("="*70)
    
    payload = {
        "requirement": "更新README文档，添加安装说明",
        "git_diff": """
+## 安装说明
+
+1. 克隆仓库
+2. 安装依赖: pip install -r requirements.txt
+3. 运行: python main.py
""",
        "context": {"priority": "P2"}
    }
    
    print(f"\n📤 发送请求...")
    response = requests.post(f"{BASE_URL}/pipeline/run", json=payload)
    
    if response.status_code == 200:
        data = response.json()
        print_pipeline_result(data)
    else:
        print(f"❌ 请求失败: {response.status_code}")


def demo_scenario_3():
    """场景3: 查询历史和统计"""
    print("\n" + "="*70)
    print("📋 场景3: 查询历史记录和统计信息")
    print("="*70)
    
    # 查询历史
    print(f"\n📊 查询历史记录...")
    response = requests.get(f"{BASE_URL}/pipeline/history?limit=5")
    
    if response.status_code == 200:
        data = response.json()
        print(f"   历史记录数: {data['count']}")
        
        for i, record in enumerate(data['data'], 1):
            result = record['result']
            print(f"\n   [{i}] Trace: {result['trace_id']}")
            print(f"       状态: {result['report']['summary']['status']}")
            print(f"       耗时: {result['total_duration']}s")
    
    # 查询统计
    print(f"\n📈 查询统计信息...")
    response = requests.get(f"{BASE_URL}/pipeline/statistics")
    
    if response.status_code == 200:
        data = response.json()
        stats = data['data']
        
        print(f"\n   统计信息:")
        print(f"      总 Pipeline 数: {stats['total_pipelines']}")
        print(f"      跳过执行: {stats['skipped']}")
        print(f"      实际执行: {stats['executed']}")
        print(f"      平均耗时: {stats['avg_duration']}s")
        print(f"      成功率: {stats['success_rate']}%")


def print_pipeline_result(data: dict):
    """打印Pipeline结果"""
    print(f"\n✅ Pipeline 完成 [Trace: {data['trace_id']}]")
    print(f"   总耗时: {data['total_duration']}s")
    
    # 决策
    decision = data['decision']
    print(f"\n   【决策】")
    print(f"      需要测试: {decision['need_test']}")
    print(f"      动作: {decision['action']}")
    print(f"      风险等级: {decision['risk_level']}")
    print(f"      优先级: {decision['priority']}")
    
    # 策略
    if data.get('strategy'):
        strategy = data['strategy']
        print(f"\n   【策略】")
        print(f"      模块数: {len(strategy.get('strategy', []))}")
        
        for module in strategy.get('strategy', []):
            print(f"         - {module['module']}: {', '.join(module['test_types'])}")
    
    # 执行
    if data.get('execution'):
        execution = data['execution']
        summary = execution['summary']
        print(f"\n   【执行】")
        print(f"      总数: {summary['total']}")
        print(f"      通过: {summary['passed']}")
        print(f"      失败: {summary['failed']}")
    
    # 修复
    if data.get('healing'):
        healing = data['healing']
        stats = healing['statistics']
        print(f"\n   【修复】")
        print(f"      修复次数: {stats['total_healings']}")
        print(f"      成功修复: {stats['successful_fixes']}")
    
    # 报告
    report = data['report']
    summary = report['summary']
    print(f"\n   【报告】")
    print(f"      最终状态: {summary['status']}")
    print(f"      AI分析: {report['ai_analysis'][:100]}...")
    
    # Timeline
    print(f"\n   【时间线】")
    for step in data['timeline']:
        print(f"      {step['stage']:15s} - {step['duration']}s")


def main():
    """主函数"""
    print("\n" + "="*70)
    print("🚀 AI Test Pipeline 演示")
    print("="*70)
    print("\n本演示展示一键自动测试系统的完整流程：")
    print("   Agent → Strategy → Orchestrator → Self-Healing → Report")
    
    try:
        # 场景1: 核心功能变更
        demo_scenario_1()
        time.sleep(2)
        
        # 场景2: 文档变更
        demo_scenario_2()
        time.sleep(2)
        
        # 场景3: 查询历史和统计
        demo_scenario_3()
        
        print("\n" + "="*70)
        print("✅ 演示完成！")
        print("="*70)
        
    except requests.exceptions.ConnectionError:
        print(f"\n❌ 连接失败: 请确保后端服务器运行在 {BASE_URL}")
    except Exception as e:
        print(f"\n❌ 演示异常: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
