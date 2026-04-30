#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试测试用例显示问题
"""

import requests
import json

def test_backend_api():
    """测试后端API"""
    try:
        print("🔍 测试后端API...")
        response = requests.get('http://127.0.0.1:8081/api/test-cases')
        
        if response.status_code == 200:
            data = response.json()
            test_cases = data.get('testCases', [])
            
            print(f"✅ API调用成功")
            print(f"📊 总测试用例数量: {len(test_cases)}")
            
            # 统计AI生成的测试用例
            ai_cases = [tc for tc in test_cases if 'AI生成' in tc.get('title', '')]
            print(f"🤖 AI生成的测试用例数量: {len(ai_cases)}")
            
            print("\n📋 所有测试用例:")
            for i, tc in enumerate(test_cases, 1):
                title = tc.get('title', 'N/A')
                tc_id = tc.get('id', 'N/A')
                module = tc.get('module', 'N/A')
                status = tc.get('status', 'N/A')
                print(f"  {i:2d}. ID:{tc_id:2d} - {title} [{module}] ({status})")
            
            print(f"\n🎯 AI生成的测试用例详情:")
            for tc in ai_cases:
                print(f"  - ID:{tc['id']} - {tc['title']}")
                print(f"    模块: {tc.get('module', 'N/A')}")
                print(f"    状态: {tc.get('status', 'N/A')}")
                print(f"    步骤: {len(tc.get('steps', []))}个")
                print()
                
        else:
            print(f"❌ API调用失败: {response.status_code}")
            print(f"响应: {response.text}")
            
    except Exception as e:
        print(f"❌ 请求失败: {e}")

def trigger_ai_generation():
    """触发AI生成"""
    try:
        print("\n🚀 触发AI生成...")
        response = requests.post('http://127.0.0.1:8081/api/ai/generate', 
                               json={"type": "test_cases"})
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ AI生成任务启动成功")
            print(f"任务ID: {data.get('taskId')}")
            return data.get('taskId')
        else:
            print(f"❌ AI生成失败: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ AI生成请求失败: {e}")
        return None

def check_task_status(task_id):
    """检查任务状态"""
    try:
        print(f"\n📊 检查任务状态: {task_id}")
        response = requests.get(f'http://127.0.0.1:8081/api/tasks/{task_id}/status')
        
        if response.status_code == 200:
            data = response.json()
            print(f"状态: {data.get('status')}")
            print(f"进度: {data.get('progress', 0)}%")
            print(f"当前步骤: {data.get('current_step', 'N/A')}")
            return data.get('status')
        else:
            print(f"❌ 状态查询失败: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ 状态查询失败: {e}")
        return None

if __name__ == "__main__":
    print("🔧 AI测试平台 - 测试用例调试工具")
    print("=" * 50)
    
    # 1. 测试当前API状态
    test_backend_api()
    
    # 2. 触发新的AI生成
    task_id = trigger_ai_generation()
    
    if task_id:
        import time
        print("\n⏳ 等待AI生成完成...")
        
        for i in range(10):  # 最多等待20秒
            time.sleep(2)
            status = check_task_status(task_id)
            if status == 'completed':
                print("✅ AI生成完成!")
                break
            elif status == 'failed':
                print("❌ AI生成失败!")
                break
        
        # 3. 再次检查测试用例
        print("\n🔄 重新检查测试用例...")
        test_backend_api()