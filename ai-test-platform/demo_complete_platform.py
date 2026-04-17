#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
AI Test Platform - 完整平台演示

演示AI测试设计与自动化平台的完整功能。
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent))

from app.main import AITestPlatform
from parser.requirement_parser import create_sample_requirement
from parser.swagger_parser import create_sample_swagger
from config.config import get_config

def main():
    """主演示函数"""
    print("🚀 AI Test Platform - 完整功能演示")
    print("=" * 60)
    
    # 验证配置
    config = get_config()
    print(f"📁 配置验证: {'✅ 通过' if config.validate() else '❌ 失败'}")
    
    # 创建示例文件
    print("\n📝 创建示例文件...")
    requirement_file = create_sample_requirement()
    swagger_file = create_sample_swagger()
    print(f"✅ 需求文档: {requirement_file}")
    print(f"✅ Swagger文档: {swagger_file}")
    
    # 创建平台实例
    print("\n🔧 初始化AI测试平台...")
    platform = AITestPlatform()
    print("✅ 平台初始化完成")
    
    # 运行完整工作流程
    print("\n🚀 开始执行完整测试工作流程...")
    result = platform.run_complete_workflow()
    
    # 显示结果
    if result['success']:
        print("\n🎉 工作流程执行成功！")
        print("\n📊 执行摘要:")
        summary = result['summary']
        
        print(f"  🔧 识别模块: {summary['modules_count']} 个")
        print(f"  🎯 生成测试点: {summary['testpoints_count']} 个")
        print(f"  📊 生成测试场景: {summary['scenarios_count']} 个")
        print(f"  📝 生成测试用例: {summary['testcases_count']} 个")
        
        test_execution = summary['test_execution']
        print(f"  🧪 测试执行: {test_execution['total']} 个用例")
        print(f"  ✅ 通过: {test_execution['passed']} 个")
        print(f"  ❌ 失败: {test_execution['failed']} 个")
        print(f"  📈 通过率: {test_execution['pass_rate']:.1f}%")
        
        print(f"\n📁 生成文件:")
        for file_name in summary['files_generated']:
            print(f"  📄 {file_name}")
        
        print(f"\n📂 输出目录: {config.paths.output_dir}")
        print("🎯 请查看输出目录中的所有生成文件！")
        
        # 显示关键文件路径
        results = result['results']
        if 'excel_file' in results:
            print(f"\n📊 Excel测试用例: {results['excel_file']}")
        if 'report' in results:
            print(f"📋 测试报告: {results['report']}")
        
    else:
        print(f"\n❌ 工作流程执行失败: {result['error']}")
        print("请检查配置和依赖是否正确安装")
    
    print("\n" + "=" * 60)
    print("演示完成！")

if __name__ == "__main__":
    main()