#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试AI生成流程修复
验证Mock AI客户端是否正确返回数据
"""

import sys
import json
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from ai.mock_ai_client import MockAIClient
from test_design.module_splitter import ModuleSplitter
from test_design.testpoint_generator import TestPointGenerator
from test_design.scenario_matrix_generator import ScenarioMatrixGenerator
from test_design.testcase_generator import TestCaseGenerator

def test_mock_ai_client():
    """测试Mock AI客户端"""
    print("=" * 60)
    print("测试 Mock AI 客户端")
    print("=" * 60)
    
    client = MockAIClient()
    
    # 测试模块拆分
    print("\n1. 测试模块拆分响应...")
    module_response = client.generate_json("请进行模块拆分")
    print(f"   返回类型: {type(module_response)}")
    print(f"   包含 'modules' 键: {'modules' in module_response}")
    if 'modules' in module_response:
        print(f"   模块数量: {len(module_response['modules'])}")
        for i, mod in enumerate(module_response['modules'][:2], 1):
            print(f"   模块{i}: {mod.get('name', 'N/A')}")
    
    # 测试测试点生成
    print("\n2. 测试测试点生成响应...")
    testpoint_response = client.generate_json("请生成测试点")
    print(f"   返回类型: {type(testpoint_response)}")
    print(f"   包含 'testpoints' 键: {'testpoints' in testpoint_response}")
    if 'testpoints' in testpoint_response:
        print(f"   测试点数量: {len(testpoint_response['testpoints'])}")
    
    # 测试场景生成
    print("\n3. 测试场景矩阵生成响应...")
    scenario_response = client.generate_json("请生成测试场景矩阵")
    print(f"   返回类型: {type(scenario_response)}")
    print(f"   包含 'scenarios' 键: {'scenarios' in scenario_response}")
    if 'scenarios' in scenario_response:
        print(f"   场景数量: {len(scenario_response['scenarios'])}")
    
    # 测试用例生成
    print("\n4. 测试测试用例生成响应...")
    testcase_response = client.generate_json("请生成测试用例")
    print(f"   返回类型: {type(testcase_response)}")
    print(f"   包含 'testcases' 键: {'testcases' in testcase_response}")
    if 'testcases' in testcase_response:
        print(f"   测试用例数量: {len(testcase_response['testcases'])}")
        for i, tc in enumerate(testcase_response['testcases'][:2], 1):
            print(f"   用例{i}: {tc.get('title', 'N/A')}")
    
    print("\n✅ Mock AI 客户端测试完成")
    return True

def test_complete_workflow():
    """测试完整的AI生成工作流"""
    print("\n" + "=" * 60)
    print("测试完整 AI 生成工作流")
    print("=" * 60)
    
    # 示例需求文档
    requirement = """
# 用户管理系统需求文档

## 功能需求

### 用户注册
- 用户可以通过邮箱注册
- 密码需要满足安全要求

### 用户登录
- 支持邮箱登录
- 支持记住登录状态

### 用户信息管理
- 用户可以查看和编辑个人信息
- 支持头像上传
"""
    
    try:
        # 步骤1: 拆分模块
        print("\n步骤1: 拆分功能模块...")
        splitter = ModuleSplitter()
        modules = splitter.split_modules(requirement)
        print(f"   ✅ 识别到 {len(modules)} 个功能模块")
        for mod in modules:
            print(f"      - {mod['name']}")
        
        if len(modules) == 0:
            print("   ❌ 错误: 未识别到任何模块!")
            return False
        
        # 步骤2: 生成测试点
        print("\n步骤2: 生成测试点...")
        testpoint_gen = TestPointGenerator()
        all_testpoints = testpoint_gen.generate_testpoints(modules)
        total_testpoints = sum(len(points) for points in all_testpoints.values())
        print(f"   ✅ 生成 {total_testpoints} 个测试点")
        
        if total_testpoints == 0:
            print("   ❌ 错误: 未生成任何测试点!")
            return False
        
        # 步骤3: 生成场景矩阵
        print("\n步骤3: 生成测试场景...")
        scenario_gen = ScenarioMatrixGenerator()
        all_scenarios = scenario_gen.generate_scenario_matrix(all_testpoints)
        total_scenarios = sum(len(scenarios) for scenarios in all_scenarios.values())
        print(f"   ✅ 生成 {total_scenarios} 个测试场景")
        
        if total_scenarios == 0:
            print("   ❌ 错误: 未生成任何场景!")
            return False
        
        # 步骤4: 生成测试用例
        print("\n步骤4: 生成测试用例...")
        testcase_gen = TestCaseGenerator()
        all_testcases = testcase_gen.generate_testcases(modules, all_scenarios)
        total_testcases = sum(len(cases) for cases in all_testcases.values())
        print(f"   ✅ 生成 {total_testcases} 个测试用例")
        
        if total_testcases == 0:
            print("   ❌ 错误: 未生成任何测试用例!")
            return False
        
        # 显示摘要
        print("\n" + "=" * 60)
        print("生成摘要:")
        print(f"  - 功能模块: {len(modules)} 个")
        print(f"  - 测试点: {total_testpoints} 个")
        print(f"  - 测试场景: {total_scenarios} 个")
        print(f"  - 测试用例: {total_testcases} 个")
        print("=" * 60)
        
        print("\n✅ 完整工作流测试成功!")
        return True
        
    except Exception as e:
        print(f"\n❌ 工作流测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    print("🚀 AI生成流程修复验证")
    print("=" * 60)
    
    # 测试Mock AI客户端
    if not test_mock_ai_client():
        print("\n❌ Mock AI客户端测试失败")
        return
    
    # 测试完整工作流
    if not test_complete_workflow():
        print("\n❌ 完整工作流测试失败")
        return
    
    print("\n" + "=" * 60)
    print("🎉 所有测试通过! AI生成流程已修复")
    print("=" * 60)
    print("\n现在你可以:")
    print("  1. 启动后端服务: python backend_api_server.py")
    print("  2. 上传需求文档进行AI生成")
    print("  3. 查看生成的测试用例")

if __name__ == "__main__":
    main()
