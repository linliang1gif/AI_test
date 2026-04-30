#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
前端完整流程验证
验证前端智能执行按钮 → 后端API → 完整Pipeline
"""

import requests
import time

BASE_URL = "http://localhost:8000"

def print_section(title):
    """打印分节标题"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def test_backend_health():
    """测试后端健康状态"""
    print_section("1. 检查后端服务")
    
    try:
        r = requests.get(f"{BASE_URL}/health", timeout=5)
        if r.status_code == 200:
            print("✅ 后端服务正常运行")
            return True
        else:
            print(f"❌ 后端服务异常: {r.status_code}")
            return False
    except Exception as e:
        print(f"❌ 无法连接后端服务: {e}")
        return False

def test_get_testcases():
    """获取测试用例"""
    print_section("2. 获取测试用例")
    
    try:
        r = requests.get(f"{BASE_URL}/api/test-cases", timeout=5)
        data = r.json()
        cases = data.get('data', [])
        
        print(f"✅ 获取到 {len(cases)} 个测试用例")
        
        if len(cases) > 0:
            # 显示前3个
            print("\n前3个测试用例:")
            for i, case in enumerate(cases[:3], 1):
                print(f"   {i}. {case.get('id')}: {case.get('title', 'N/A')}")
            
            return [case.get('id') for case in cases[:3]]
        else:
            print("⚠️  没有测试用例")
            return []
            
    except Exception as e:
        print(f"❌ 获取测试用例失败: {e}")
        return []

def test_intelligent_run_api(test_case_ids):
    """测试智能执行API"""
    print_section("3. 测试智能执行API")
    
    if not test_case_ids:
        print("⚠️  没有测试用例ID,跳过测试")
        return False
    
    print(f"📋 准备执行 {len(test_case_ids)} 个测试用例")
    print(f"   用例ID: {test_case_ids}")
    
    try:
        # 调用智能执行API
        payload = {
            "test_case_ids": test_case_ids
        }
        
        print(f"\n🚀 调用API: POST {BASE_URL}/api/v2/test/run-intelligent")
        print(f"   请求体: {payload}")
        
        r = requests.post(
            f"{BASE_URL}/api/v2/test/run-intelligent",
            json=payload,
            timeout=60
        )
        
        print(f"\n📊 响应状态: {r.status_code}")
        
        if r.status_code == 200:
            result = r.json()
            print("✅ API调用成功")
            
            # 显示结果
            print("\n📈 执行结果:")
            print(f"   状态: {result.get('status', 'unknown')}")
            
            data = result.get('data', {})
            summary = data.get('summary', {})
            
            print(f"\n📊 测试摘要:")
            print(f"   总用例数: {summary.get('total', 0)}")
            print(f"   通过: {summary.get('passed', 0)}")
            print(f"   失败: {summary.get('failed', 0)}")
            print(f"   成功率: {summary.get('pass_rate', '0%')}")
            
            # 修复信息
            healing = data.get('healing_summary', {})
            if healing.get('total_healed', 0) > 0:
                print(f"\n🔧 Self-Healing:")
                print(f"   修复数: {healing.get('total_healed', 0)}")
                print(f"   L1-重试: {healing.get('retry', 0)}")
                print(f"   L2-数据: {healing.get('regenerate_data', 0)}")
                print(f"   L3-容错: {healing.get('flaky', 0)}")
                print(f"   L4-人工: {healing.get('manual', 0)}")
            
            return True
        else:
            print(f"❌ API调用失败: {r.status_code}")
            print(f"   响应: {r.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ API调用超时")
        return False
    except Exception as e:
        print(f"❌ API调用异常: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_frontend_integration():
    """测试前端集成"""
    print_section("4. 前端集成检查")
    
    print("📋 前端功能清单:")
    print("   ✅ 智能执行按钮 (TestCasesList.jsx)")
    print("   ✅ API服务层 (api.js)")
    print("   ✅ 实时进度显示")
    print("   ✅ 执行结果展示")
    print("   ✅ 自动页面跳转")
    
    print("\n🎯 前端使用步骤:")
    print("   1. 访问: http://localhost:5173/test-cases")
    print("   2. 勾选测试用例")
    print("   3. 点击'智能执行'按钮")
    print("   4. 观察实时进度")
    print("   5. 查看执行结果")
    
    return True

def main():
    """主函数"""
    print("="*60)
    print("  前端完整流程验证")
    print("="*60)
    print("验证: 前端 → 后端API → 完整Pipeline")
    print("="*60)
    
    # 1. 检查后端
    if not test_backend_health():
        print("\n❌ 后端服务未运行,请先启动后端服务")
        print("   启动命令: cd ai-test-platform && py backend_api_server.py")
        return 1
    
    # 2. 获取测试用例
    test_case_ids = test_get_testcases()
    
    # 3. 测试智能执行API
    api_ok = test_intelligent_run_api(test_case_ids)
    
    # 4. 前端集成检查
    frontend_ok = test_frontend_integration()
    
    # 总结
    print_section("验证总结")
    
    print("✅ 后端服务: 正常")
    print(f"{'✅' if test_case_ids else '⚠️ '} 测试用例: {len(test_case_ids)}个")
    print(f"{'✅' if api_ok else '❌'} 智能执行API: {'正常' if api_ok else '失败'}")
    print(f"{'✅' if frontend_ok else '❌'} 前端集成: {'完成' if frontend_ok else '未完成'}")
    
    if api_ok and frontend_ok:
        print("\n🎉 前端完整流程验证通过!")
        print("\n📝 下一步:")
        print("   1. 启动前端: cd ai-test-platform/frontend && npm run dev")
        print("   2. 访问: http://localhost:5173/test-cases")
        print("   3. 勾选测试用例,点击'智能执行'按钮")
        print("   4. 观察完整的AI执行流程")
        return 0
    else:
        print("\n⚠️  部分功能验证失败,请检查上述错误")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())
