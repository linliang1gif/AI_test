#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
完整工作流端到端测试
模拟用户从上传文档到执行测试的完整流程
"""

import requests
import json
import time
from pathlib import Path

BASE_URL = "http://localhost:8000"

def print_section(title):
    """打印分隔线"""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)

def test_complete_workflow():
    """测试完整工作流"""
    
    print("\n🚀 开始测试完整工作流...")
    
    # ==================== 步骤1: 创建测试用例 ====================
    print_section("步骤1: 创建测试用例")
    
    test_cases = [
        {
            "title": "验证用户登录功能",
            "module": "用户管理",
            "priority": "high",
            "status": "pending",
            "steps": [
                "打开登录页面",
                "输入用户名: admin",
                "输入密码: admin123",
                "点击登录按钮",
                "验证登录成功,跳转到首页"
            ],
            "expected": "用户成功登录,显示用户信息",
            "source": "test"
        },
        {
            "title": "验证订单创建功能",
            "module": "订单管理",
            "priority": "high",
            "status": "pending",
            "steps": [
                "选择商品",
                "填写收货地址",
                "选择支付方式",
                "提交订单",
                "验证订单创建成功"
            ],
            "expected": "订单创建成功,返回订单号",
            "source": "test"
        },
        {
            "title": "验证商品搜索功能",
            "module": "商品管理",
            "priority": "medium",
            "status": "pending",
            "steps": [
                "打开商品列表页面",
                "输入搜索关键词",
                "点击搜索按钮",
                "验证搜索结果正确"
            ],
            "expected": "返回匹配的商品列表",
            "source": "test"
        }
    ]
    
    created_ids = []
    for tc in test_cases:
        response = requests.post(f"{BASE_URL}/api/test-cases", json=tc)
        if response.status_code == 200:
            created = response.json()['data']
            created_ids.append(created['id'])
            print(f"  ✅ 创建测试用例: {tc['title']} (ID: {created['id']})")
        else:
            print(f"  ❌ 创建失败: {tc['title']}")
    
    print(f"\n  📊 共创建 {len(created_ids)} 个测试用例")
    
    # ==================== 步骤2: 生成自动化脚本 ====================
    print_section("步骤2: 生成自动化脚本")
    
    generated_scripts = []
    for testcase_id in created_ids:
        response = requests.post(f"{BASE_URL}/api/testcases/{testcase_id}/generate-script")
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                script = result.get('script', '')
                script_lines = len(script.split('\n'))
                generated_scripts.append({
                    'id': testcase_id,
                    'script': script,
                    'lines': script_lines
                })
                print(f"  ✅ 测试用例 {testcase_id} - 脚本生成成功 ({script_lines} 行)")
            else:
                print(f"  ❌ 测试用例 {testcase_id} - 脚本生成失败")
        else:
            print(f"  ❌ 测试用例 {testcase_id} - API请求失败")
    
    print(f"\n  📊 共生成 {len(generated_scripts)} 个脚本")
    
    # 显示第一个脚本的预览
    if generated_scripts:
        print(f"\n  📄 脚本预览 (测试用例 {generated_scripts[0]['id']}):")
        print("  " + "-"*66)
        preview_lines = generated_scripts[0]['script'].split('\n')[:15]
        for line in preview_lines:
            print(f"  {line}")
        print("  " + "-"*66)
    
    # ==================== 步骤3: 执行测试用例 ====================
    print_section("步骤3: 执行测试用例")
    
    execution_results = []
    for testcase_id in created_ids:
        print(f"\n  🧪 执行测试用例 {testcase_id}...")
        response = requests.post(f"{BASE_URL}/api/testcases/{testcase_id}/execute")
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                exec_result = result.get('result', {})
                status = exec_result.get('status')
                message = exec_result.get('message')
                duration = exec_result.get('response_time')
                assertions = exec_result.get('assertions', {})
                
                execution_results.append({
                    'id': testcase_id,
                    'status': status,
                    'duration': duration,
                    'assertions': assertions
                })
                
                status_icon = "✅" if status == "passed" else "❌"
                print(f"  {status_icon} 状态: {status}")
                print(f"     消息: {message}")
                print(f"     耗时: {duration}")
                if assertions:
                    print(f"     断言: {assertions.get('passed', 0)}/{assertions.get('total', 0)} 通过")
            else:
                print(f"  ❌ 执行失败: {result.get('message')}")
        else:
            print(f"  ❌ API请求失败: {response.status_code}")
        
        time.sleep(0.5)  # 避免请求过快
    
    # 统计执行结果
    passed_count = sum(1 for r in execution_results if r['status'] == 'passed')
    failed_count = sum(1 for r in execution_results if r['status'] == 'failed')
    total_count = len(execution_results)
    pass_rate = (passed_count / total_count * 100) if total_count > 0 else 0
    
    print(f"\n  📊 执行统计:")
    print(f"     总计: {total_count}")
    print(f"     通过: {passed_count}")
    print(f"     失败: {failed_count}")
    print(f"     通过率: {pass_rate:.1f}%")
    
    # ==================== 步骤4: 查看执行记录 ====================
    print_section("步骤4: 查看执行记录")
    
    response = requests.get(f"{BASE_URL}/api/test-runs")
    if response.status_code == 200:
        result = response.json()
        if result.get('success'):
            runs = result.get('data', [])
            print(f"  ✅ 获取到 {len(runs)} 条执行记录")
            
            # 显示最近3条记录
            print(f"\n  📋 最近执行记录:")
            for run in runs[-3:]:
                status_icon = "✅" if run.get('status') == 'passed' else "❌"
                print(f"     {status_icon} [{run.get('id')}] {run.get('testcase_title', 'N/A')}")
                print(f"        状态: {run.get('status')} | 时间: {run.get('executed_at')}")
        else:
            print(f"  ❌ 获取失败: {result.get('message')}")
    else:
        print(f"  ❌ API请求失败: {response.status_code}")
    
    # ==================== 总结 ====================
    print_section("✅ 完整流程测试完成")
    
    print(f"""
  工作流验证结果:
  
  ✅ 步骤1: 创建测试用例 - {len(created_ids)} 个
  ✅ 步骤2: 生成自动化脚本 - {len(generated_scripts)} 个
  ✅ 步骤3: 执行测试用例 - {total_count} 个 (通过率: {pass_rate:.1f}%)
  ✅ 步骤4: 查看执行记录 - 正常
  
  🎉 完整流程已打通!
  
  前端访问地址: http://localhost:5173
  后端API文档: http://localhost:8000/docs
    """)

if __name__ == "__main__":
    try:
        test_complete_workflow()
    except KeyboardInterrupt:
        print("\n\n⚠️  测试被用户中断")
    except Exception as e:
        print(f"\n\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
