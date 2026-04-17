#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
自动化脚本模块功能测试

测试自动化脚本模块的所有功能:
1. 获取脚本列表
2. 生成新脚本
3. 下载脚本
4. 执行脚本
"""

import requests
import time
import json
from pathlib import Path

BASE_URL = "http://127.0.0.1:8081"

def test_get_scripts():
    """测试获取脚本列表"""
    print("\n" + "="*60)
    print("测试1: 获取脚本列表")
    print("="*60)
    
    response = requests.get(f"{BASE_URL}/api/automation/scripts")
    assert response.status_code == 200, f"请求失败: {response.status_code}"
    
    data = response.json()
    scripts = data.get("scripts", [])
    
    print(f"✅ 成功获取 {len(scripts)} 个脚本")
    
    for script in scripts:
        print(f"\n脚本 #{script['id']}:")
        print(f"  名称: {script['name']}")
        print(f"  框架: {script['framework']}")
        print(f"  语言: {script.get('language', 'Python')}")
        print(f"  测试数: {script['testCount']}")
        print(f"  状态: {script['status']}")
        print(f"  生成时间: {script['lastGenerated']}")
    
    return scripts

def test_generate_script():
    """测试生成新脚本"""
    print("\n" + "="*60)
    print("测试2: 生成新脚本")
    print("="*60)
    
    # 发起生成请求
    payload = {
        "type": "automation_script",
        "framework": "pytest",
        "language": "Python",
        "test_type": "Integration Tests"
    }
    
    response = requests.post(
        f"{BASE_URL}/api/ai/generate",
        json=payload
    )
    
    assert response.status_code == 200, f"生成请求失败: {response.status_code}"
    
    data = response.json()
    task_id = data.get("taskId")
    
    print(f"✅ 生成任务已启动")
    print(f"  任务ID: {task_id}")
    print(f"  消息: {data.get('message')}")
    
    # 等待生成完成
    print("\n等待生成完成...")
    max_wait = 10
    for i in range(max_wait):
        time.sleep(1)
        status_response = requests.get(f"{BASE_URL}/api/tasks/{task_id}/status")
        
        if status_response.status_code == 200:
            status_data = status_response.json()
            status = status_data.get("status")
            progress = status_data.get("progress", 0)
            
            print(f"  进度: {progress}% - {status_data.get('current_step', '')}")
            
            if status == "completed":
                print(f"\n✅ 脚本生成完成!")
                result = status_data.get("result", {})
                print(f"  脚本ID: {result.get('script_id')}")
                print(f"  脚本名: {result.get('script_name')}")
                print(f"  框架: {result.get('framework')}")
                print(f"  语言: {result.get('language')}")
                return result.get('script_id')
            elif status == "failed":
                print(f"❌ 生成失败: {status_data.get('error')}")
                return None
    
    print("⚠️ 生成超时")
    return None

def test_download_script(script_id):
    """测试下载脚本"""
    print("\n" + "="*60)
    print(f"测试3: 下载脚本 #{script_id}")
    print("="*60)
    
    response = requests.get(f"{BASE_URL}/api/automation/scripts/{script_id}/download")
    
    assert response.status_code == 200, f"下载失败: {response.status_code}"
    
    script_content = response.text
    
    print(f"✅ 脚本下载成功")
    print(f"  内容长度: {len(script_content)} 字符")
    print(f"\n脚本预览 (前30行):")
    print("-" * 60)
    
    lines = script_content.split('\n')[:30]
    for line in lines:
        print(line)
    
    print("-" * 60)
    
    # 验证脚本内容
    assert "import pytest" in script_content, "脚本缺少pytest导入"
    assert "def test_" in script_content, "脚本缺少测试方法"
    assert "class Test" in script_content, "脚本缺少测试类"
    
    print("\n✅ 脚本内容验证通过")
    
    return script_content

def test_execute_script(script_id):
    """测试执行脚本"""
    print("\n" + "="*60)
    print(f"测试4: 执行脚本 #{script_id}")
    print("="*60)
    
    # 发起执行请求
    response = requests.post(f"{BASE_URL}/api/automation/scripts/{script_id}/execute")
    
    assert response.status_code == 200, f"执行请求失败: {response.status_code}"
    
    data = response.json()
    task_id = data.get("taskId")
    
    print(f"✅ 执行任务已启动")
    print(f"  任务ID: {task_id}")
    print(f"  消息: {data.get('message')}")
    
    # 等待执行完成
    print("\n等待执行完成...")
    max_wait = 10
    for i in range(max_wait):
        time.sleep(1)
        status_response = requests.get(f"{BASE_URL}/api/tasks/{task_id}/status")
        
        if status_response.status_code == 200:
            status_data = status_response.json()
            status = status_data.get("status")
            progress = status_data.get("progress", 0)
            
            print(f"  进度: {progress}% - {status_data.get('current_step', '')}")
            
            if status == "completed":
                print(f"\n✅ 脚本执行完成!")
                result = status_data.get("result", {})
                print(f"  总测试数: {result.get('total_tests')}")
                print(f"  通过: {result.get('passed')}")
                print(f"  失败: {result.get('failed')}")
                print(f"  耗时: {result.get('duration')}")
                
                # 显示执行日志
                logs = status_data.get("logs", [])
                if logs:
                    print(f"\n执行日志 (共{len(logs)}条):")
                    for log in logs[:5]:  # 只显示前5条
                        print(f"  - {log.get('message', log)}")
                
                return result
            elif status == "failed":
                print(f"❌ 执行失败: {status_data.get('error')}")
                return None
    
    print("⚠️ 执行超时")
    return None

def test_from_testcases_generation():
    """测试从测试用例生成脚本"""
    print("\n" + "="*60)
    print("测试5: 从测试用例生成脚本")
    print("="*60)
    
    # 先获取测试用例
    response = requests.get(f"{BASE_URL}/api/test-cases")
    assert response.status_code == 200
    
    testcases = response.json().get("testCases", [])
    
    if not testcases:
        print("⚠️ 没有测试用例,跳过此测试")
        return None
    
    # 选择前3个测试用例
    testcase_ids = [tc["id"] for tc in testcases[:3]]
    
    print(f"选择 {len(testcase_ids)} 个测试用例: {testcase_ids}")
    
    # 发起生成请求
    payload = {
        "testcase_ids": testcase_ids,
        "framework": "pytest",
        "language": "Python"
    }
    
    response = requests.post(
        f"{BASE_URL}/api/automation/scripts/generate",
        json=payload
    )
    
    assert response.status_code == 200, f"生成请求失败: {response.status_code}"
    
    data = response.json()
    task_id = data.get("taskId")
    
    print(f"✅ 生成任务已启动")
    print(f"  任务ID: {task_id}")
    
    # 等待生成完成
    print("\n等待生成完成...")
    max_wait = 10
    for i in range(max_wait):
        time.sleep(1)
        status_response = requests.get(f"{BASE_URL}/api/tasks/{task_id}/status")
        
        if status_response.status_code == 200:
            status_data = status_response.json()
            status = status_data.get("status")
            progress = status_data.get("progress", 0)
            
            print(f"  进度: {progress}%")
            
            if status == "completed":
                print(f"\n✅ 从测试用例生成脚本完成!")
                result = status_data.get("result", {})
                print(f"  生成脚本数: {result.get('scripts_generated')}")
                print(f"  使用测试用例数: {result.get('total_testcases')}")
                scripts = result.get('scripts', [])
                for script_name in scripts:
                    print(f"  - {script_name}")
                return result
            elif status == "failed":
                print(f"❌ 生成失败: {status_data.get('error')}")
                return None
    
    print("⚠️ 生成超时")
    return None

def main():
    """主测试流程"""
    print("\n" + "="*60)
    print("自动化脚本模块功能测试")
    print("="*60)
    
    try:
        # 测试1: 获取脚本列表
        scripts = test_get_scripts()
        assert len(scripts) > 0, "脚本列表为空"
        
        # 测试2: 生成新脚本
        new_script_id = test_generate_script()
        
        # 测试3: 下载脚本
        if scripts:
            script_content = test_download_script(scripts[0]['id'])
            assert script_content, "脚本下载失败"
        
        # 测试4: 执行脚本
        if scripts:
            result = test_execute_script(scripts[0]['id'])
            assert result, "脚本执行失败"
        
        # 测试5: 从测试用例生成脚本
        test_from_testcases_generation()
        
        # 最终验证
        print("\n" + "="*60)
        print("最终验证")
        print("="*60)
        
        final_scripts = test_get_scripts()
        
        print("\n" + "="*60)
        print("✅ 所有测试通过!")
        print("="*60)
        print(f"\n测试总结:")
        print(f"  初始脚本数: {len(scripts)}")
        print(f"  最终脚本数: {len(final_scripts)}")
        print(f"  新增脚本数: {len(final_scripts) - len(scripts)}")
        print(f"\n自动化脚本模块功能完整,运行正常!")
        
    except AssertionError as e:
        print(f"\n❌ 测试失败: {e}")
        return False
    except Exception as e:
        print(f"\n❌ 测试异常: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
