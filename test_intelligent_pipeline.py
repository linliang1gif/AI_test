#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试智能执行Pipeline API
验证 Intelligence → Execution → Healing → Report 完整链路
"""

import requests
import json
import time

# API配置
BASE_URL = "http://localhost:8000"
API_ENDPOINT = f"{BASE_URL}/api/v2/test/run-intelligent"

def test_intelligent_pipeline():
    """测试智能执行Pipeline"""
    
    print("\n" + "="*60)
    print("🧪 测试智能执行Pipeline API")
    print("="*60)
    
    # 准备测试数据
    test_request = {
        "test_case_ids": ["TC_001", "TC_002", "TC_003"],
        "environment": "test",
        "base_url": "https://jsonplaceholder.typicode.com"
    }
    
    print(f"\n📤 发送请求:")
    print(json.dumps(test_request, indent=2, ensure_ascii=False))
    
    # 发送请求
    try:
        print(f"\n🔄 调用API: {API_ENDPOINT}")
        start_time = time.time()
        
        response = requests.post(
            API_ENDPOINT,
            json=test_request,
            headers={"Content-Type": "application/json"},
            timeout=120  # 2分钟超时
        )
        
        duration = time.time() - start_time
        
        print(f"⏱️  请求耗时: {duration:.2f}秒")
        print(f"📊 状态码: {response.status_code}")
        
        # 解析响应
        if response.status_code == 200:
            result = response.json()
            
            print(f"\n✅ 请求成功!")
            print(f"\n{'='*60}")
            print(f"📋 执行结果摘要")
            print(f"{'='*60}")
            
            # 1. 执行计划
            if 'execution_plan' in result:
                plan = result['execution_plan']
                print(f"\n🧠 执行计划:")
                print(f"   - 选中测试: {len(plan.get('selected_tests', []))}")
                print(f"   - 跳过测试: {len(plan.get('skipped_tests', []))}")
                print(f"   - 并发分组: {len(plan.get('parallel_groups', {}))}")
            
            # 2. 执行结果
            if 'results' in result:
                results = result['results']
                print(f"\n⚙️  执行结果:")
                print(f"   - 总计: {len(results)}")
                passed = sum(1 for r in results if r.get('status') == 'passed')
                failed = sum(1 for r in results if r.get('status') == 'failed')
                print(f"   - 通过: {passed}")
                print(f"   - 失败: {failed}")
            
            # 3. 修复报告
            if 'healing' in result:
                healing = result['healing']
                print(f"\n🔧 修复报告:")
                print(f"   - 总用例: {healing.get('total_cases', 0)}")
                print(f"   - 已修复: {healing.get('healed_cases', 0)}")
                print(f"   - 修复率: {healing.get('healing_rate', '0%')}")
                
                if 'by_level' in healing:
                    print(f"   - 修复明细:")
                    for level, info in healing['by_level'].items():
                        if info['count'] > 0:
                            print(f"     • {level}: {info['count']} ({info['description']})")
            
            # 4. 测试报告
            if 'report' in result:
                report = result['report']
                if 'summary' in report:
                    summary = report['summary']
                    print(f"\n📊 测试报告:")
                    print(f"   - 通过率: {summary.get('pass_rate', '0%')}")
                    print(f"   - 通过: {summary.get('passed', 0)}")
                    print(f"   - 失败: {summary.get('failed', 0)}")
                    print(f"   - 总耗时: {summary.get('total_duration', 0):.2f}秒")
            
            # 5. 统计信息
            if 'statistics' in result:
                stats = result['statistics']
                print(f"\n📈 统计信息:")
                print(f"   - 总测试数: {stats.get('total_tests', 0)}")
                print(f"   - 已执行: {stats.get('executed_tests', 0)}")
                print(f"   - 通过率: {stats.get('pass_rate', '0%')}")
            
            # 保存完整结果
            output_file = "intelligent_pipeline_result.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            print(f"\n💾 完整结果已保存到: {output_file}")
            
            print(f"\n{'='*60}")
            print(f"✅ 测试完成!")
            print(f"{'='*60}\n")
            
            return True
            
        else:
            print(f"\n❌ 请求失败!")
            print(f"状态码: {response.status_code}")
            print(f"响应: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print(f"\n❌ 请求超时!")
        return False
    except requests.exceptions.ConnectionError:
        print(f"\n❌ 连接失败! 请确保后端服务已启动: {BASE_URL}")
        return False
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_with_mock_data():
    """使用模拟数据测试"""
    
    print("\n" + "="*60)
    print("🧪 使用模拟数据测试Pipeline")
    print("="*60)
    
    # 先创建一些测试用例
    create_url = f"{BASE_URL}/api/test-cases"
    
    mock_test_cases = [
        {
            "id": "TC_001",
            "title": "获取用户列表",
            "method": "GET",
            "path": "/users",
            "priority": "P0",
            "module": "user",
            "expected_status": 200
        },
        {
            "id": "TC_002",
            "title": "获取单个用户",
            "method": "GET",
            "path": "/users/1",
            "priority": "P1",
            "module": "user",
            "expected_status": 200
        },
        {
            "id": "TC_003",
            "title": "创建用户",
            "method": "POST",
            "path": "/users",
            "priority": "P0",
            "module": "user",
            "body": {
                "name": "Test User",
                "email": "test@example.com"
            },
            "expected_status": 201
        }
    ]
    
    print(f"\n📝 创建测试用例...")
    for tc in mock_test_cases:
        try:
            response = requests.post(create_url, json=tc)
            if response.status_code == 200:
                print(f"   ✅ {tc['id']}: {tc['title']}")
            else:
                print(f"   ⚠️  {tc['id']}: 创建失败 (可能已存在)")
        except Exception as e:
            print(f"   ❌ {tc['id']}: {e}")
    
    # 执行Pipeline测试
    time.sleep(1)  # 等待数据同步
    return test_intelligent_pipeline()


if __name__ == "__main__":
    print("\n" + "="*60)
    print("🚀 智能执行Pipeline API 测试工具")
    print("="*60)
    print(f"📍 后端地址: {BASE_URL}")
    print(f"🔗 API端点: {API_ENDPOINT}")
    print("="*60)
    
    # 选择测试模式
    print("\n请选择测试模式:")
    print("1. 直接测试 (使用现有测试用例)")
    print("2. 使用模拟数据测试 (先创建测试用例)")
    
    choice = input("\n请输入选项 (1/2, 默认2): ").strip() or "2"
    
    if choice == "1":
        success = test_intelligent_pipeline()
    else:
        success = test_with_mock_data()
    
    # 退出码
    exit(0 if success else 1)
