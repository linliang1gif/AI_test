#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试报告生成功能
"""

import requests
import json

BASE_URL = "http://127.0.0.1:8081"

def test_report_generation():
    """测试报告生成功能"""
    print("=" * 60)
    print("测试报告生成功能")
    print("=" * 60)
    
    # 1. 获取测试运行列表
    print("\n1️⃣  获取测试运行列表...")
    response = requests.get(f"{BASE_URL}/api/test-runs")
    if response.status_code == 200:
        test_runs = response.json().get("test_runs", [])
        print(f"✅ 找到 {len(test_runs)} 个测试运行")
        
        if test_runs:
            # 使用第一个测试运行
            test_run = test_runs[0]
            print(f"   使用测试运行: {test_run['name']} (ID: {test_run['id']})")
            
            # 2. 生成报告
            print("\n2️⃣  生成测试报告...")
            response = requests.post(
                f"{BASE_URL}/api/reports/generate",
                json={
                    "test_run_id": test_run["id"],
                    "type": "comprehensive"
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                report = result.get("report", {})
                print(f"✅ 报告生成成功!")
                print(f"   报告ID: {report['id']}")
                print(f"   报告名称: {report['name']}")
                print(f"   通过率: {report['passRate']}%")
                print(f"   总测试数: {report['totalTests']}")
                print(f"   通过: {report['passed']}")
                print(f"   失败: {report['failed']}")
                
                # 3. 获取报告列表
                print("\n3️⃣  获取报告列表...")
                response = requests.get(f"{BASE_URL}/api/reports")
                if response.status_code == 200:
                    reports = response.json().get("reports", [])
                    print(f"✅ 找到 {len(reports)} 个报告")
                    for r in reports:
                        print(f"   - {r['name']} (ID: {r['id']}, 通过率: {r['passRate']}%)")
                
                # 4. 获取HTML报告
                print("\n4️⃣  获取HTML报告...")
                html_url = f"{BASE_URL}/api/reports/{report['id']}/html"
                response = requests.get(html_url)
                if response.status_code == 200:
                    print(f"✅ HTML报告生成成功!")
                    print(f"   报告大小: {len(response.text)} 字符")
                    print(f"   访问地址: {html_url}")
                else:
                    print(f"❌ 获取HTML报告失败: {response.status_code}")
                
                # 5. 测试删除报告
                print("\n5️⃣  测试删除报告...")
                response = requests.delete(f"{BASE_URL}/api/reports/{report['id']}")
                if response.status_code == 200:
                    print(f"✅ 报告删除成功!")
                else:
                    print(f"❌ 删除报告失败: {response.status_code}")
                
            else:
                print(f"❌ 生成报告失败: {response.status_code}")
                print(f"   错误: {response.text}")
        else:
            print("⚠️  没有找到测试运行，请先运行一些测试")
    else:
        print(f"❌ 获取测试运行失败: {response.status_code}")
    
    print("\n" + "=" * 60)
    print("测试完成!")
    print("=" * 60)

if __name__ == "__main__":
    test_report_generation()
