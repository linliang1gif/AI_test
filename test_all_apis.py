#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试所有关键API接口
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_api(name, method, endpoint, data=None, expected_status=200):
    """测试API接口"""
    url = f"{BASE_URL}{endpoint}"
    print(f"\n{'='*60}")
    print(f"测试: {name}")
    print(f"方法: {method} {endpoint}")
    
    try:
        if method == "GET":
            response = requests.get(url, timeout=5)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=5)
        elif method == "PUT":
            response = requests.put(url, json=data, timeout=5)
        elif method == "DELETE":
            response = requests.delete(url, timeout=5)
        else:
            print(f"❌ 不支持的方法: {method}")
            return False
        
        print(f"状态码: {response.status_code}")
        
        if response.status_code == expected_status:
            print(f"✅ 测试通过")
            try:
                result = response.json()
                print(f"响应: {json.dumps(result, ensure_ascii=False, indent=2)[:200]}...")
                return True, result
            except:
                print(f"响应: {response.text[:200]}...")
                return True, response.text
        else:
            print(f"❌ 测试失败 - 期望状态码 {expected_status}")
            print(f"响应: {response.text[:200]}")
            return False, None
            
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return False, None

def main():
    print("="*60)
    print("AI测试平台 - API接口测试")
    print("="*60)
    
    results = []
    
    # 1. 测试健康检查
    success, _ = test_api("健康检查", "GET", "/health")
    results.append(("健康检查", success))
    
    # 2. 测试获取测试用例
    success, data = test_api("获取测试用例", "GET", "/api/test-cases")
    results.append(("获取测试用例", success))
    test_cases = data.get('data', []) if data else []
    print(f"   测试用例数量: {len(test_cases)}")
    
    # 3. 测试执行API
    success, result = test_api(
        "执行API",
        "POST",
        "/api/execute-api",
        {
            "method": "GET",
            "url": "https://jsonplaceholder.typicode.com/posts/1",
            "base_url": "https://jsonplaceholder.typicode.com",
            "path": "/posts/1"
        }
    )
    results.append(("执行API", success))
    
    # 4. 测试保存为测试用例
    if result and result.get('success'):
        success, saved = test_api(
            "保存为测试用例",
            "POST",
            "/api/save-api-as-testcase",
            {
                "api_info": {
                    "name": "测试API",
                    "method": "GET",
                    "path": "/posts/1",
                    "tags": ["测试"]
                },
                "execution_result": result,
                "request_data": {}
            }
        )
        results.append(("保存为测试用例", success))
        
        if saved and saved.get('success'):
            test_case_id = saved.get('test_case_id')
            print(f"   生成的测试用例ID: {test_case_id}")
            
            # 5. 测试生成脚本
            success, script_result = test_api(
                "生成自动化脚本",
                "POST",
                "/api/automation/scripts/generate",
                {"test_case_id": test_case_id}
            )
            results.append(("生成自动化脚本", success))
            
            if script_result and script_result.get('success'):
                script_id = script_result.get('script_id')
                print(f"   生成的脚本ID: {script_id}")
                
                # 6. 测试下载脚本
                success, _ = test_api(
                    "下载脚本",
                    "GET",
                    f"/api/automation/scripts/{script_id}/download"
                )
                results.append(("下载脚本", success))
                
                # 7. 测试执行脚本
                success, exec_result = test_api(
                    "执行脚本",
                    "POST",
                    f"/api/automation/scripts/{script_id}/execute"
                )
                results.append(("执行脚本", success))
    
    # 8. 测试获取自动化脚本列表
    success, scripts = test_api("获取脚本列表", "GET", "/api/automation/scripts")
    results.append(("获取脚本列表", success))
    if scripts:
        script_list = scripts.get('scripts', []) or scripts.get('data', [])
        print(f"   脚本数量: {len(script_list)}")
    
    # 9. 测试获取测试运行
    success, runs = test_api("获取测试运行", "GET", "/api/test-runs")
    results.append(("获取测试运行", success))
    if runs:
        run_list = runs.get('test_runs', []) or runs.get('data', [])
        print(f"   测试运行数量: {len(run_list)}")
    
    # 总结
    print("\n" + "="*60)
    print("测试总结")
    print("="*60)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for name, success in results:
        status = "✅" if success else "❌"
        print(f"{status} {name}")
    
    print(f"\n通过率: {passed}/{total} ({passed*100//total}%)")
    
    if passed == total:
        print("\n🎉 所有测试通过！")
    else:
        print(f"\n⚠️  有 {total - passed} 个测试失败")

if __name__ == "__main__":
    main()
