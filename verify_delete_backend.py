"""
验证删除功能后端是否正常
用户可以运行这个脚本来确认后端工作正常
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def print_section(title):
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)

def print_result(success, message):
    icon = "✅" if success else "❌"
    print(f"{icon} {message}")

print_section("删除功能后端验证")

# 1. 检查后端是否运行
print("\n1. 检查后端服务...")
try:
    response = requests.get(f"{BASE_URL}/health", timeout=3)
    if response.status_code == 200:
        print_result(True, "后端服务正常运行")
    else:
        print_result(False, f"后端服务异常: {response.status_code}")
        exit(1)
except Exception as e:
    print_result(False, f"无法连接到后端: {e}")
    print("\n请确保后端服务正在运行:")
    print("  cd ai-test-platform")
    print("  py backend_api_server.py")
    exit(1)

# 2. 检查批量删除API是否存在
print("\n2. 检查批量删除API...")
try:
    response = requests.post(
        f"{BASE_URL}/api/testcases/batch-delete",
        json={"ids": [999999]},  # 使用不存在的ID
        headers={"Content-Type": "application/json"},
        timeout=3
    )
    
    if response.status_code == 200:
        result = response.json()
        if result.get('success'):
            print_result(True, "批量删除API存在且正常")
            print(f"   响应: {result}")
        else:
            print_result(False, f"API返回失败: {result}")
    elif response.status_code == 404:
        print_result(False, "批量删除API不存在")
        print("   需要在backend_api_server.py中实现该API")
        exit(1)
    else:
        print_result(False, f"API返回异常状态码: {response.status_code}")
        print(f"   响应: {response.text}")
except Exception as e:
    print_result(False, f"API调用失败: {e}")
    exit(1)

# 3. 获取测试用例数量
print("\n3. 检查测试用例数据...")
try:
    response = requests.get(f"{BASE_URL}/api/test-cases", timeout=3)
    if response.status_code == 200:
        data = response.json()
        test_cases = data.get('data', [])
        count = len(test_cases)
        print_result(True, f"共有 {count} 个测试用例")
        
        if count == 0:
            print("   ⚠️ 没有测试用例,无法测试删除功能")
            print("   建议先生成一些测试用例")
        else:
            # 显示ID类型
            if test_cases:
                sample_id = test_cases[0].get('id')
                id_type = type(sample_id).__name__
                print(f"   ID类型: {id_type}")
                print(f"   示例ID: {sample_id}")
    else:
        print_result(False, f"获取测试用例失败: {response.status_code}")
except Exception as e:
    print_result(False, f"获取测试用例失败: {e}")

# 4. 测试实际删除(如果有测试用例)
print("\n4. 测试实际删除功能...")
try:
    response = requests.get(f"{BASE_URL}/api/test-cases", timeout=3)
    test_cases = response.json().get('data', [])
    
    if len(test_cases) == 0:
        print("   ⚠️ 跳过删除测试(没有测试用例)")
    else:
        # 选择最后一个测试用例
        test_case = test_cases[-1]
        test_id = test_case['id']
        test_title = test_case.get('title', 'N/A')[:40]
        
        print(f"   准备删除: ID={test_id}, 标题={test_title}")
        
        # 执行删除
        response = requests.post(
            f"{BASE_URL}/api/testcases/batch-delete",
            json={"ids": [test_id]},
            headers={"Content-Type": "application/json"},
            timeout=3
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                deleted_count = result.get('deleted_count', 0)
                if deleted_count > 0:
                    print_result(True, f"删除成功! 删除了 {deleted_count} 个测试用例")
                    
                    # 验证是否真的删除了
                    response = requests.get(f"{BASE_URL}/api/test-cases", timeout=3)
                    new_test_cases = response.json().get('data', [])
                    new_count = len(new_test_cases)
                    
                    if new_count < len(test_cases):
                        print_result(True, f"验证成功! 测试用例数量从 {len(test_cases)} 减少到 {new_count}")
                    else:
                        print_result(False, "验证失败! 测试用例数量没有变化")
                else:
                    print_result(False, "删除失败! deleted_count为0")
                    print("   这可能是后端逻辑问题")
            else:
                print_result(False, f"删除失败: {result.get('message', 'Unknown error')}")
        else:
            print_result(False, f"删除请求失败: {response.status_code}")
            print(f"   响应: {response.text}")
            
except Exception as e:
    print_result(False, f"删除测试失败: {e}")

# 总结
print_section("验证总结")

print("""
如果以上所有检查都通过(✅),说明:
1. 后端服务正常运行
2. 批量删除API存在且工作正常
3. 删除功能可以正确删除数据

如果前端删除功能还是不正常,问题在于:
❌ 浏览器缓存了旧的JavaScript代码

解决方案:
1. 按 Ctrl + Shift + R 硬刷新浏览器
2. 或者 F12 → Network → Disable cache

如果有任何检查失败(❌),请查看上面的错误信息。
""")

print("=" * 60)
print("验证完成")
print("=" * 60)
