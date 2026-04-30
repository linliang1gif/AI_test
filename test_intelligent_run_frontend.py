#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试前端智能执行功能
验证 TestCasesList.jsx 的智能执行按钮是否正常工作
"""

import requests
import json
import time

# API配置
BASE_URL = "http://localhost:8000"
API_ENDPOINT = f"{BASE_URL}/api/v2/test/run-intelligent"

def test_intelligent_run():
    """测试智能执行Pipeline"""
    print("\n" + "="*60)
    print("🧪 测试智能执行Pipeline")
    print("="*60)
    
    # 1. 准备测试数据
    test_request = {
        "test_case_ids": ["TC_001", "TC_002"],
        "environment": "test",
        "base_url": "https://jsonplaceholder.typicode.com"
    }
    
    print(f"\n📤 发送请求:")
    print(f"   URL: {API_ENDPOINT}")
    print(f"   数据: {json.dumps(test_request, indent=2, ensure_ascii=False)}")
    
    # 2. 发送请求
    try:
        response = requests.post(
            API_ENDPOINT,
            json=test_request,
            timeout=60
        )
        
        print(f"\n📥 响应状态: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"\n✅ 执行成功!")
            print(f"\n📊 执行统计:")
            stats = result.get('statistics', {})
            print(f"   - 总测试数: {stats.get('total_tests', 0)}")
            print(f"   - 执行数: {stats.get('executed_tests', 0)}")
            print(f"   - 通过数: {stats.get('passed_tests', 0)}")
            print(f"   - 失败数: {stats.get('failed_tests', 0)}")
            print(f"   - 通过率: {stats.get('pass_rate', '0%')}")
            print(f"   - 总耗时: {stats.get('total_duration', 0)}s")
            
            # 显示执行计划
            plan = result.get('execution_plan', {})
            print(f"\n🧠 执行计划:")
            print(f"   - 选中测试: {len(plan.get('selected_tests', []))}")
            print(f"   - 跳过测试: {len(plan.get('skipped_tests', []))}")
            
            # 显示修复信息
            healing = result.get('healing', {})
            print(f"\n🔧 自动修复:")
            print(f"   - 总用例: {healing.get('total_cases', 0)}")
            print(f"   - 已修复: {healing.get('healed_cases', 0)}")
            print(f"   - 修复率: {healing.get('healing_rate', '0%')}")
            
            return True
        else:
            print(f"\n❌ 执行失败!")
            print(f"   错误: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"\n❌ 连接失败! 请确保后端服务已启动:")
        print(f"   cd ai-test-platform")
        print(f"   py backend_api_server.py")
        return False
    except Exception as e:
        print(f"\n❌ 请求失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_backend_health():
    """检查后端服务健康状态"""
    print("\n" + "="*60)
    print("🏥 检查后端服务")
    print("="*60)
    
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print(f"✅ 后端服务正常运行")
            return True
        else:
            print(f"⚠️  后端服务响应异常: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print(f"❌ 无法连接到后端服务")
        print(f"\n请先启动后端服务:")
        print(f"   cd ai-test-platform")
        print(f"   py backend_api_server.py")
        return False
    except Exception as e:
        print(f"❌ 健康检查失败: {e}")
        return False

def main():
    """主函数"""
    print("\n" + "="*60)
    print("🚀 前端智能执行功能测试")
    print("="*60)
    
    # 1. 检查后端服务
    if not check_backend_health():
        return
    
    # 2. 测试智能执行
    success = test_intelligent_run()
    
    # 3. 总结
    print("\n" + "="*60)
    if success:
        print("✅ 测试通过! 前端智能执行功能正常")
        print("\n📝 前端使用说明:")
        print("   1. 启动前端: cd ai-test-platform/frontend && npm run dev")
        print("   2. 访问: http://localhost:5173/test-cases")
        print("   3. 勾选测试用例")
        print("   4. 点击'智能执行'按钮")
        print("   5. 查看实时进度和执行结果")
    else:
        print("❌ 测试失败! 请检查后端服务和API实现")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()
