#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
端到端测试 - 验证完整 Pipeline

测试流程：
Discovery → Design → Optimization → Execution → Healing → Report

使用真实 API：JSONPlaceholder (https://jsonplaceholder.typicode.com)
"""

import sys
import json
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from pipeline_v2 import run_pipeline_v2


def test_e2e_with_requirement():
    """测试1: 从需求生成测试（端到端）"""
    print("=" * 80)
    print("🧪 测试1: 从需求生成测试（端到端）")
    print("=" * 80)
    
    print("\n场景: 测试用户管理功能")
    print("API: JSONPlaceholder (https://jsonplaceholder.typicode.com)")
    
    # 运行 Pipeline
    results = run_pipeline_v2(
        requirement="测试用户管理功能：查询用户列表、获取单个用户信息、创建用户",
        base_url="https://jsonplaceholder.typicode.com",
        environment="test",
        output_dir="output/e2e_test1"
    )
    
    # 验证结果
    print("\n" + "=" * 80)
    print("📊 验证结果")
    print("=" * 80)
    
    if results is not None:
        print(f"✅ Pipeline 执行成功")
        print(f"  执行结果数: {len(results)}")
        
        # 统计
        passed = sum(1 for r in results if hasattr(r, 'status') and 
                    str(r.status).upper() == 'PASSED')
        failed = len(results) - passed
        
        print(f"  通过: {passed}")
        print(f"  失败: {failed}")
        print(f"  通过率: {(passed / len(results) * 100):.1f}%")
        
        return True
    else:
        print(f"❌ Pipeline 执行失败")
        return False


def test_e2e_with_swagger():
    """测试2: 从 Swagger 生成测试（端到端）"""
    print("\n" + "=" * 80)
    print("🧪 测试2: 从 Swagger 生成测试（端到端）")
    print("=" * 80)
    
    # 检查 Swagger 文件是否存在
    swagger_file = Path("examples/sample_swagger.json")
    
    if not swagger_file.exists():
        print(f"⚠️  Swagger 文件不存在: {swagger_file}")
        print(f"  跳过此测试")
        return True
    
    print(f"\n场景: 从 Swagger 生成测试")
    print(f"Swagger: {swagger_file}")
    
    # 运行 Pipeline
    try:
        results = run_pipeline_v2(
            new_swagger=str(swagger_file),
            base_url="https://api.example.com",
            environment="test",
            output_dir="output/e2e_test2"
        )
        
        # 验证结果
        print("\n" + "=" * 80)
        print("📊 验证结果")
        print("=" * 80)
        
        if results is not None:
            print(f"✅ Pipeline 执行成功")
            print(f"  执行结果数: {len(results)}")
            return True
        else:
            print(f"❌ Pipeline 执行失败")
            return False
            
    except Exception as e:
        print(f"⚠️  执行出错: {e}")
        return False


def test_e2e_components():
    """测试3: 验证各组件协同工作"""
    print("\n" + "=" * 80)
    print("🧪 测试3: 验证各组件协同工作")
    print("=" * 80)
    
    print("\n验证点:")
    print("  1. DesignAgent - 生成测试用例")
    print("  2. OptimizationAgent - 优化测试用例")
    print("  3. ExecutionAgent - 执行测试")
    print("  4. ResilienceEngine - 提供稳定性保障")
    print("  5. HealingAgent - 智能修复")
    print("  6. LearningAgent - 学习反馈")
    print("  7. ReportGenerator - 生成报告")
    
    # 运行 Pipeline
    results = run_pipeline_v2(
        requirement="测试文章管理：获取文章列表、获取单篇文章、创建文章",
        base_url="https://jsonplaceholder.typicode.com",
        environment="test",
        output_dir="output/e2e_test3"
    )
    
    # 验证输出文件
    print("\n验证输出文件:")
    output_dir = Path("output/e2e_test3")
    
    expected_files = [
        "testcases_v2.json",
        "report_v2.json",
        "report_v2.html",
        "pipeline_summary_v2.json"
    ]
    
    all_exist = True
    for filename in expected_files:
        file_path = output_dir / filename
        if file_path.exists():
            print(f"  ✅ {filename}")
        else:
            print(f"  ❌ {filename} (不存在)")
            all_exist = False
    
    if all_exist and results is not None:
        print(f"\n✅ 所有组件协同工作正常")
        return True
    else:
        print(f"\n⚠️  部分组件可能存在问题")
        return False


def test_e2e_resilience():
    """测试4: 验证 ResilienceEngine 生效"""
    print("\n" + "=" * 80)
    print("🧪 测试4: 验证 ResilienceEngine 生效")
    print("=" * 80)
    
    print("\n场景: 执行测试并验证稳定性保障")
    
    # 运行 Pipeline
    results = run_pipeline_v2(
        requirement="测试评论功能：获取评论列表",
        base_url="https://jsonplaceholder.typicode.com",
        environment="test",
        output_dir="output/e2e_test4"
    )
    
    # 检查 pipeline_summary 中的 ResilienceEngine 统计
    summary_file = Path("output/e2e_test4/pipeline_summary_v2.json")
    
    if summary_file.exists():
        with open(summary_file, 'r', encoding='utf-8') as f:
            summary = json.load(f)
        
        # 检查是否有 ResilienceEngine 统计
        exec_stats = summary.get('stages', {}).get('execution', {}).get('statistics', {})
        
        if 'resilience' in exec_stats:
            print(f"\n✅ ResilienceEngine 已生效")
            res_stats = exec_stats['resilience']['resilience']
            print(f"  总调用: {res_stats['total_calls']}")
            print(f"  成功: {res_stats['successful_calls']}")
            print(f"  重试: {res_stats['retried_calls']}")
            return True
        else:
            print(f"\n⚠️  未找到 ResilienceEngine 统计")
            return False
    else:
        print(f"\n⚠️  未找到 pipeline_summary 文件")
        return False


def main():
    """主函数"""
    print("=" * 80)
    print("🚀 端到端测试套件")
    print("=" * 80)
    
    results = []
    
    # 测试1: 从需求生成测试
    results.append(("从需求生成测试", test_e2e_with_requirement()))
    
    # 测试2: 从 Swagger 生成测试
    results.append(("从 Swagger 生成测试", test_e2e_with_swagger()))
    
    # 测试3: 验证各组件协同
    results.append(("验证各组件协同", test_e2e_components()))
    
    # 测试4: 验证 ResilienceEngine
    results.append(("验证 ResilienceEngine", test_e2e_resilience()))
    
    # 汇总结果
    print("\n" + "=" * 80)
    print("📊 测试汇总")
    print("=" * 80)
    
    for name, passed in results:
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"  {name:30s} {status}")
    
    total = len(results)
    passed_count = sum(1 for _, p in results if p)
    
    print(f"\n总计: {passed_count}/{total} 通过")
    
    if passed_count == total:
        print("\n🎉 所有端到端测试通过！")
        return 0
    else:
        print(f"\n⚠️  {total - passed_count} 个测试失败")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
