#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试用例显示和导出功能测试
验证:
1. 上传需求文档生成测试用例
2. 测试用例是否显示完整标题和内容
3. Excel导出功能是否正常
"""

import requests
import json
import os
from pathlib import Path

BASE_URL = "http://127.0.0.1:8081"

def test_upload_and_generate():
    """测试上传需求文档并生成测试用例"""
    print("\n" + "="*60)
    print("测试1: 上传需求文档生成测试用例")
    print("="*60)
    
    # 创建测试文档
    test_doc_path = Path("test_requirement.txt")
    test_content = """
用户登录功能需求
1. 用户可以使用用户名和密码登录系统
2. 登录成功后跳转到首页
3. 登录失败显示错误提示
4. 支持记住密码功能
5. 支持找回密码功能

订单管理功能需求
1. 用户可以创建新订单
2. 用户可以查看订单列表
3. 用户可以取消订单
4. 管理员可以审核订单
5. 系统自动计算订单金额
"""
    
    with open(test_doc_path, "w", encoding="utf-8") as f:
        f.write(test_content)
    
    try:
        # 上传文档
        with open(test_doc_path, "rb") as f:
            files = {"file": ("test_requirement.txt", f, "text/plain")}
            response = requests.post(f"{BASE_URL}/api/testcases/generate", files=files)
        
        print(f"状态码: {response.status_code}")
        result = response.json()
        print(f"响应: {json.dumps(result, ensure_ascii=False, indent=2)}")
        
        if result.get("success"):
            print(f"✅ 成功生成 {result.get('count')} 个测试用例")
            
            # 检查测试用例内容
            test_cases = result.get("testCases", [])
            if test_cases:
                print("\n生成的测试用例详情:")
                for i, tc in enumerate(test_cases[:3], 1):  # 只显示前3个
                    print(f"\n测试用例 {i}:")
                    print(f"  标题: {tc.get('title')}")
                    print(f"  模块: {tc.get('module')}")
                    print(f"  优先级: {tc.get('priority')}")
                    print(f"  测试步骤: {tc.get('steps')}")
                    print(f"  预期结果: {tc.get('expected')}")
                    
                    # 验证标题不是占位符
                    if "AI生成测试用例" in tc.get('title', ''):
                        print("  ⚠️  警告: 标题仍然是占位符!")
                    else:
                        print("  ✅ 标题正常")
            
            return True
        else:
            print(f"❌ 生成失败: {result.get('error')}")
            return False
            
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        return False
    finally:
        # 清理测试文件
        if test_doc_path.exists():
            test_doc_path.unlink()


def test_export_excel():
    """测试导出Excel功能"""
    print("\n" + "="*60)
    print("测试2: 导出测试用例为Excel")
    print("="*60)
    
    try:
        response = requests.get(f"{BASE_URL}/api/test-cases/export")
        
        print(f"状态码: {response.status_code}")
        print(f"Content-Type: {response.headers.get('content-type')}")
        
        if response.status_code == 200:
            # 保存Excel文件
            output_dir = Path("output")
            output_dir.mkdir(exist_ok=True)
            
            excel_path = output_dir / "测试导出.xlsx"
            with open(excel_path, "wb") as f:
                f.write(response.content)
            
            file_size = excel_path.stat().st_size
            print(f"✅ Excel文件已保存: {excel_path}")
            print(f"   文件大小: {file_size} 字节")
            
            if file_size > 0:
                print("✅ 导出功能正常")
                return True
            else:
                print("❌ 文件为空")
                return False
        else:
            print(f"❌ 导出失败: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        return False


def test_get_test_cases():
    """测试获取测试用例列表"""
    print("\n" + "="*60)
    print("测试3: 获取测试用例列表")
    print("="*60)
    
    try:
        response = requests.get(f"{BASE_URL}/api/test-cases")
        
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            test_cases = response.json()
            print(f"✅ 获取到 {len(test_cases)} 个测试用例")
            
            if test_cases:
                print("\n前3个测试用例:")
                for i, tc in enumerate(test_cases[:3], 1):
                    print(f"\n{i}. {tc.get('title')}")
                    print(f"   模块: {tc.get('module', '-')}")
                    print(f"   优先级: {tc.get('priority')}")
                    print(f"   状态: {tc.get('status')}")
            
            return True
        else:
            print(f"❌ 获取失败: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        return False


def main():
    print("\n" + "="*60)
    print("测试用例显示和导出功能完整测试")
    print("="*60)
    
    results = []
    
    # 测试1: 上传生成
    results.append(("上传生成测试用例", test_upload_and_generate()))
    
    # 测试2: 获取列表
    results.append(("获取测试用例列表", test_get_test_cases()))
    
    # 测试3: 导出Excel
    results.append(("导出Excel", test_export_excel()))
    
    # 汇总结果
    print("\n" + "="*60)
    print("测试结果汇总")
    print("="*60)
    
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{name}: {status}")
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    print(f"\n总计: {passed}/{total} 通过")
    
    if passed == total:
        print("\n🎉 所有测试通过!")
    else:
        print("\n⚠️  部分测试失败,请检查")


if __name__ == "__main__":
    main()
