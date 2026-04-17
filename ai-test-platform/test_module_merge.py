#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试模块合并功能
验证AI测试控制台的两种执行模式
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_decision_only_mode():
    """测试仅决策模式"""
    print("\n" + "="*60)
    print("测试1: 仅决策分析模式")
    print("="*60)
    
    # 调用Agent API
    response = requests.post(
        f"{BASE_URL}/api/agent/analyze",
        json={
            "requirement": "支付模块需要支持微信支付",
            "git_diff": "+def wechat_pay():\n+    return process_payment('wechat')"
        }
    )
    
    if response.status_code == 200:
        result = response.json()
        print("✅ 仅决策模式测试通过")
        print(f"   需要测试: {result.get('need_test')}")
        print(f"   优先级: {result.get('priority')}")
        print(f"   风险等级: {result.get('risk_level')}")
        print(f"   置信度: {result.get('confidence', 0)*100:.0f}%")
        return True
    else:
        print(f"❌ 仅决策模式测试失败: {response.status_code}")
        return False

def test_full_pipeline_mode():
    """测试完整流程模式"""
    print("\n" + "="*60)
    print("测试2: 完整流程模式")
    print("="*60)
    
    # 调用Pipeline API
    response = requests.post(
        f"{BASE_URL}/api/pipeline/run",
        json={
            "requirement": "用户登录功能需要添加验证码",
            "git_diff": "",
            "context": {"priority": "P1"}
        }
    )
    
    if response.status_code == 200:
        result = response.json()
        print("✅ 完整流程模式测试通过")
        print(f"   Trace ID: {result.get('trace_id')}")
        print(f"   总耗时: {result.get('total_duration')}s")
        
        if 'decision' in result:
            print(f"   决策: {result['decision'].get('need_test')}")
        if 'report' in result:
            print(f"   状态: {result['report']['summary'].get('status')}")
        
        return True
    else:
        print(f"❌ 完整流程模式测试失败: {response.status_code}")
        return False

def test_frontend_routes():
    """测试前端路由"""
    print("\n" + "="*60)
    print("测试3: 前端路由检查")
    print("="*60)
    
    # 检查前端是否运行
    try:
        response = requests.get("http://localhost:5173")
        if response.status_code == 200:
            print("✅ 前端服务正常运行")
            
            # 检查是否还有test-agent路由
            if 'test-agent' in response.text:
                print("⚠️  警告: 前端代码中可能还有test-agent引用")
                return False
            else:
                print("✅ test-agent路由已移除")
                return True
        else:
            print("⚠️  前端服务未运行")
            return False
    except:
        print("⚠️  无法连接到前端服务")
        return False

def main():
    """主测试函数"""
    print("\n🚀 开始测试模块合并功能")
    print("="*60)
    
    results = []
    
    # 测试1: 仅决策模式
    results.append(("仅决策模式", test_decision_only_mode()))
    
    # 测试2: 完整流程模式
    results.append(("完整流程模式", test_full_pipeline_mode()))
    
    # 测试3: 前端路由
    results.append(("前端路由", test_frontend_routes()))
    
    # 汇总结果
    print("\n" + "="*60)
    print("测试结果汇总")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{status} - {name}")
    
    print(f"\n通过率: {passed}/{total} ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("\n🎉 所有测试通过!模块合并成功!")
    else:
        print(f"\n⚠️  有 {total-passed} 个测试失败,请检查")

if __name__ == "__main__":
    main()
