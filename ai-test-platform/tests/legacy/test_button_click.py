#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试自动化脚本按钮功能

模拟前端点击按钮的操作
"""

import requests
import time

BASE_URL = "http://127.0.0.1:8081"

def test_run_button():
    """测试运行按钮"""
    print("\n" + "="*60)
    print("测试: 点击运行按钮")
    print("="*60)
    
    script_id = 1
    
    print(f"\n模拟点击脚本 #{script_id} 的运行按钮...")
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/automation/scripts/{script_id}/execute",
            headers={"Content-Type": "application/json"}
        )
        
        print(f"响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 运行成功!")
            print(f"  任务ID: {data.get('taskId')}")
            print(f"  消息: {data.get('message')}")
            
            # 等待并查询任务状态
            task_id = data.get('taskId')
            if task_id:
                print(f"\n等待任务执行...")
                time.sleep(3)
                
                status_response = requests.get(f"{BASE_URL}/api/tasks/{task_id}/status")
                if status_response.status_code == 200:
                    status_data = status_response.json()
                    print(f"\n任务状态:")
                    print(f"  状态: {status_data.get('status')}")
                    print(f"  进度: {status_data.get('progress')}%")
                    print(f"  当前步骤: {status_data.get('current_step')}")
                    
                    if status_data.get('result'):
                        print(f"\n执行结果:")
                        result = status_data['result']
                        for key, value in result.items():
                            print(f"  {key}: {value}")
        else:
            print(f"❌ 运行失败: HTTP {response.status_code}")
            print(f"响应内容: {response.text}")
            
    except Exception as e:
        print(f"❌ 请求异常: {e}")

def test_download_button():
    """测试下载按钮"""
    print("\n" + "="*60)
    print("测试: 点击下载按钮")
    print("="*60)
    
    script_id = 1
    
    print(f"\n模拟点击脚本 #{script_id} 的下载按钮...")
    
    try:
        response = requests.get(f"{BASE_URL}/api/automation/scripts/{script_id}/download")
        
        print(f"响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            print(f"✅ 下载成功!")
            print(f"  内容长度: {len(response.text)} 字符")
            print(f"\n脚本预览 (前20行):")
            print("-" * 60)
            lines = response.text.split('\n')[:20]
            for line in lines:
                print(line)
            print("-" * 60)
        else:
            print(f"❌ 下载失败: HTTP {response.status_code}")
            
    except Exception as e:
        print(f"❌ 请求异常: {e}")

def test_generate_button():
    """测试生成按钮"""
    print("\n" + "="*60)
    print("测试: 点击生成新脚本按钮")
    print("="*60)
    
    print(f"\n模拟点击生成新脚本按钮...")
    print(f"  框架: pytest")
    print(f"  语言: Python")
    print(f"  类型: Unit Tests")
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/ai/generate",
            headers={"Content-Type": "application/json"},
            json={
                "type": "automation_script",
                "framework": "pytest",
                "language": "Python",
                "test_type": "Unit Tests"
            }
        )
        
        print(f"响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 生成任务已启动!")
            print(f"  任务ID: {data.get('taskId')}")
            print(f"  消息: {data.get('message')}")
            
            # 等待并查询任务状态
            task_id = data.get('taskId')
            if task_id:
                print(f"\n等待生成完成...")
                for i in range(5):
                    time.sleep(1)
                    status_response = requests.get(f"{BASE_URL}/api/tasks/{task_id}/status")
                    if status_response.status_code == 200:
                        status_data = status_response.json()
                        print(f"  进度: {status_data.get('progress')}% - {status_data.get('current_step')}")
                        
                        if status_data.get('status') == 'completed':
                            print(f"\n✅ 生成完成!")
                            if status_data.get('result'):
                                result = status_data['result']
                                print(f"  脚本ID: {result.get('script_id')}")
                                print(f"  脚本名: {result.get('script_name')}")
                            break
        else:
            print(f"❌ 生成失败: HTTP {response.status_code}")
            
    except Exception as e:
        print(f"❌ 请求异常: {e}")

def test_refresh_list():
    """测试刷新脚本列表"""
    print("\n" + "="*60)
    print("测试: 刷新脚本列表")
    print("="*60)
    
    print(f"\n获取最新脚本列表...")
    
    try:
        response = requests.get(f"{BASE_URL}/api/automation/scripts")
        
        if response.status_code == 200:
            data = response.json()
            scripts = data.get('scripts', [])
            print(f"✅ 成功获取 {len(scripts)} 个脚本")
            
            print(f"\n脚本列表:")
            for script in scripts:
                print(f"  #{script['id']}: {script['name']}")
                print(f"    框架: {script['framework']} | 测试数: {script['testCount']} | 状态: {script['status']}")
        else:
            print(f"❌ 获取失败: HTTP {response.status_code}")
            
    except Exception as e:
        print(f"❌ 请求异常: {e}")

def main():
    """主测试流程"""
    print("\n" + "="*60)
    print("自动化脚本按钮功能测试")
    print("="*60)
    
    # 测试1: 刷新列表
    test_refresh_list()
    
    # 测试2: 运行按钮
    test_run_button()
    
    # 测试3: 下载按钮
    test_download_button()
    
    # 测试4: 生成按钮
    test_generate_button()
    
    # 测试5: 再次刷新列表
    test_refresh_list()
    
    print("\n" + "="*60)
    print("✅ 所有按钮功能测试完成!")
    print("="*60)
    print("\n如果后端测试都通过,但前端按钮没反应,可能的原因:")
    print("1. 浏览器控制台有JavaScript错误")
    print("2. 前端代码没有正确绑定事件处理器")
    print("3. 需要刷新浏览器页面")
    print("4. 浏览器缓存问题")
    print("\n建议:")
    print("- 打开浏览器开发者工具 (F12)")
    print("- 查看Console标签页的错误信息")
    print("- 查看Network标签页的网络请求")
    print("- 尝试硬刷新页面 (Ctrl+Shift+R)")

if __name__ == "__main__":
    main()
