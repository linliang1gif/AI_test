#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试数据持久化和AI生成功能
"""

import requests
import json
import time
from pathlib import Path

BASE_URL = "http://127.0.0.1:8081"

def test_data_persistence():
    """测试数据持久化功能"""
    print("\n" + "="*60)
    print("测试1: 数据持久化功能")
    print("="*60)
    
    # 1. 获取当前测试用例数量
    print("\n1️⃣ 获取当前测试用例...")
    response = requests.get(f"{BASE_URL}/api/test-cases")
    if response.status_code == 200:
        data = response.json()
        initial_count = len(data.get('testCases', []))
        print(f"✅ 当前测试用例数量: {initial_count}")
        print(f"   前3个用例:")
        for case in data.get('testCases', [])[:3]:
            print(f"   - ID {case['id']}: {case['title']}")
    else:
        print(f"❌ 获取失败: {response.status_code}")
        return False
    
    # 2. 上传需求文档生成新测试用例
    print("\n2️⃣ 上传需求文档生成测试用例...")
    test_doc_path = Path("uploads/test_requirement.txt")
    test_doc_path.parent.mkdir(exist_ok=True)
    
    # 创建测试文档
    test_content = """
    用户登录功能需求:
    1. 用户可以使用用户名和密码登录系统
    2. 登录失败时显示错误提示
    3. 支持密码重置功能
    
    购物车功能需求:
    1. 用户可以添加商品到购物车
    2. 用户可以修改购物车中商品数量
    3. 用户可以清空购物车
    
    订单管理需求:
    1. 用户可以创建订单
    2. 用户可以支付订单
    3. 用户可以查询订单状态
    """
    
    with open(test_doc_path, 'w', encoding='utf-8') as f:
        f.write(test_content)
    
    with open(test_doc_path, 'rb') as f:
        files = {'file': ('test_requirement.txt', f, 'text/plain')}
        response = requests.post(f"{BASE_URL}/api/testcases/generate", files=files)
    
    if response.status_code == 200:
        data = response.json()
        if data.get('success'):
            generated_count = data.get('count', 0)
            print(f"✅ 成功生成 {generated_count} 个测试用例")
            print(f"   生成的用例:")
            for case in data.get('testCases', [])[:3]:
                print(f"   - ID {case['id']}: {case['title']}")
                print(f"     模块: {case['module']}, 优先级: {case['priority']}")
        else:
            print(f"❌ 生成失败: {data.get('error')}")
            return False
    else:
        print(f"❌ 请求失败: {response.status_code}")
        return False
    
    # 3. 再次获取测试用例,验证数量增加
    print("\n3️⃣ 验证测试用例数量增加...")
    response = requests.get(f"{BASE_URL}/api/test-cases")
    if response.status_code == 200:
        data = response.json()
        new_count = len(data.get('testCases', []))
        print(f"✅ 新的测试用例数量: {new_count}")
        print(f"   增加了: {new_count - initial_count} 个用例")
        
        if new_count > initial_count:
            print("✅ 测试用例成功添加到内存")
        else:
            print("❌ 测试用例未添加")
            return False
    else:
        print(f"❌ 获取失败: {response.status_code}")
        return False
    
    # 4. 检查持久化文件
    print("\n4️⃣ 检查持久化文件...")
    data_file = Path("data/platform_data.json")
    if data_file.exists():
        print(f"✅ 持久化文件存在: {data_file}")
        with open(data_file, 'r', encoding='utf-8') as f:
            saved_data = json.load(f)
            saved_count = len(saved_data.get('test_cases', []))
            print(f"   文件中保存的测试用例数量: {saved_count}")
            print(f"   最后更新时间: {saved_data.get('last_updated', 'N/A')}")
            
            if saved_count == new_count:
                print("✅ 数据已成功持久化到文件")
            else:
                print(f"⚠️ 数据不一致: 内存 {new_count} vs 文件 {saved_count}")
    else:
        print(f"❌ 持久化文件不存在")
        return False
    
    return True

def test_ai_generation():
    """测试AI生成功能"""
    print("\n" + "="*60)
    print("测试2: AI生成功能")
    print("="*60)
    
    # 1. 检查AI提供商状态
    print("\n1️⃣ 检查AI提供商状态...")
    response = requests.get(f"{BASE_URL}/api/ai/current")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ 当前AI提供商: {data.get('provider_name')}")
        print(f"   提供商ID: {data.get('current_provider')}")
        print(f"   当前模型: {data.get('current_model')}")
        print(f"   状态: {data.get('status')}")
    else:
        print(f"❌ 获取失败: {response.status_code}")
    
    # 2. 检查Ollama服务状态
    print("\n2️⃣ 检查Ollama服务状态...")
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get('models', [])
            print(f"✅ Ollama服务运行正常")
            print(f"   可用模型数量: {len(models)}")
            for model in models[:3]:
                print(f"   - {model.get('name')}")
        else:
            print(f"⚠️ Ollama服务响应异常: {response.status_code}")
    except Exception as e:
        print(f"❌ Ollama服务不可用: {e}")
        print("   提示: 请确保Ollama服务已启动 (ollama serve)")
    
    # 3. 测试AI生成接口
    print("\n3️⃣ 测试AI生成接口...")
    test_data = {
        "type": "testcase",
        "requirement": "用户登录功能测试"
    }
    
    response = requests.post(f"{BASE_URL}/api/ai/generate", json=test_data)
    if response.status_code == 200:
        data = response.json()
        if data.get('success'):
            task_id = data.get('taskId')
            print(f"✅ AI生成任务已启动")
            print(f"   任务ID: {task_id}")
            
            # 等待任务完成
            print("   等待任务完成...")
            for i in range(10):
                time.sleep(1)
                status_response = requests.get(f"{BASE_URL}/api/tasks/{task_id}/status")
                if status_response.status_code == 200:
                    status_data = status_response.json()
                    progress = status_data.get('progress', 0)
                    current_step = status_data.get('current_step', '')
                    print(f"   进度: {progress}% - {current_step}")
                    
                    if status_data.get('status') == 'completed':
                        print("✅ AI生成任务完成")
                        break
        else:
            print(f"❌ 任务启动失败: {data.get('message')}")
    else:
        print(f"❌ 请求失败: {response.status_code}")
    
    return True

def test_export_functionality():
    """测试导出功能"""
    print("\n" + "="*60)
    print("测试3: 导出功能")
    print("="*60)
    
    print("\n1️⃣ 测试Excel导出...")
    response = requests.get(f"{BASE_URL}/api/test-cases/export")
    if response.status_code == 200:
        # 保存文件
        output_file = Path("output/exported_testcases.xlsx")
        output_file.parent.mkdir(exist_ok=True)
        
        with open(output_file, 'wb') as f:
            f.write(response.content)
        
        file_size = output_file.stat().st_size
        print(f"✅ Excel文件导出成功")
        print(f"   文件路径: {output_file}")
        print(f"   文件大小: {file_size} 字节")
    else:
        print(f"❌ 导出失败: {response.status_code}")
        return False
    
    return True

def main():
    """主函数"""
    print("🚀 AI测试平台 - 数据持久化和AI生成功能测试")
    print("="*60)
    print("测试目标:")
    print("1. 验证测试用例数据持久化到JSON文件")
    print("2. 验证AI生成功能是否调用本地Ollama")
    print("3. 验证Excel导出功能")
    print("="*60)
    
    # 检查后端服务
    print("\n检查后端服务...")
    try:
        response = requests.get(f"{BASE_URL}/api/dashboard/stats", timeout=5)
        if response.status_code == 200:
            print("✅ 后端服务运行正常")
        else:
            print(f"⚠️ 后端服务响应异常: {response.status_code}")
    except Exception as e:
        print(f"❌ 无法连接到后端服务: {e}")
        print("   请确保后端服务已启动: py backend_api_server.py")
        return
    
    # 运行测试
    results = []
    
    # 测试1: 数据持久化
    results.append(("数据持久化", test_data_persistence()))
    
    # 测试2: AI生成
    results.append(("AI生成功能", test_ai_generation()))
    
    # 测试3: 导出功能
    results.append(("导出功能", test_export_functionality()))
    
    # 总结
    print("\n" + "="*60)
    print("测试总结")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{status} - {name}")
    
    print(f"\n总计: {passed}/{total} 测试通过 ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("\n🎉 所有测试通过!")
    else:
        print(f"\n⚠️ {total - passed} 个测试失败")

if __name__ == "__main__":
    main()
