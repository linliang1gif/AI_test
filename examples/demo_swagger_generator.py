"""
Swagger测试用例生成器演示
展示如何从Swagger自动生成高质量测试用例
"""
import sys
import json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.swagger import SwaggerTestCaseGenerator


def demo_basic_generation():
    """演示1: 基本生成"""
    print("=" * 80)
    print("演示1: 从Swagger生成测试用例")
    print("=" * 80)
    
    # 初始化生成器
    swagger_file = Path(__file__).parent / "sample_swagger.json"
    generator = SwaggerTestCaseGenerator(
        swagger_file=str(swagger_file),
        business_context="用户和订单管理系统"
    )
    
    # 生成所有测试用例
    print("\n🚀 开始生成测试用例...")
    test_cases = generator.generate_all_testcases()
    
    print(f"\n✅ 生成完成！共生成 {len(test_cases)} 个测试用例\n")
    
    # 显示统计信息
    stats = generator.get_statistics(test_cases)
    print("📊 统计信息:")
    print(f"  总用例数: {stats['total']}")
    print(f"  覆盖API数: {stats['apis_covered']}")
    print(f"  按优先级:")
    for priority, count in stats['by_priority'].items():
        print(f"    {priority}: {count}")
    print(f"  按模块:")
    for module, count in stats['by_module'].items():
        print(f"    {module}: {count}")
    
    return test_cases


def demo_testcase_details(test_cases):
    """演示2: 查看测试用例详情"""
    print("\n" + "=" * 80)
    print("演示2: 测试用例详情")
    print("=" * 80)
    
    # 显示前3个测试用例
    for i, tc in enumerate(test_cases[:3], 1):
        print(f"\n📝 测试用例 {i}:")
        print(f"  ID: {tc.id}")
        print(f"  标题: {tc.title}")
        print(f"  模块: {tc.module}")
        print(f"  优先级: {tc.priority.value}")
        print(f"  前置条件: {tc.precondition}")
        print(f"  步骤: {tc.steps}")
        print(f"  预期结果: {tc.expected}")
        print(f"\n  执行配置:")
        print(f"    方法: {tc.execution_config['method']}")
        print(f"    URL: {tc.execution_config['url']}")
        if 'body' in tc.execution_config:
            print(f"    请求体: {json.dumps(tc.execution_config['body'], ensure_ascii=False, indent=6)}")
        if 'params' in tc.execution_config:
            print(f"    查询参数: {tc.execution_config['params']}")
        
        print(f"\n  断言:")
        for assertion in tc.assertions:
            print(f"    - {assertion}")


def demo_normal_vs_boundary_vs_error():
    """演示3: 正常/边界/异常用例对比"""
    print("\n" + "=" * 80)
    print("演示3: 正常/边界/异常用例对比")
    print("=" * 80)
    
    swagger_file = Path(__file__).parent / "sample_swagger.json"
    generator = SwaggerTestCaseGenerator(str(swagger_file))
    
    # 获取所有API
    apis = generator.loader.get_all_apis()
    
    # 选择第一个POST接口
    post_api = next((api for api in apis if api['method'] == 'POST'), None)
    
    if post_api:
        print(f"\n🎯 API: {post_api['method']} {post_api['path']}")
        print(f"   描述: {post_api['summary']}")
        
        # 生成测试用例
        test_cases = generator.generate_testcases_for_api(post_api)
        
        print(f"\n📋 生成了 {len(test_cases)} 个测试用例:")
        
        for tc in test_cases:
            print(f"\n  {tc.id} - {tc.title}")
            print(f"    优先级: {tc.priority.value}")
            print(f"    请求体: {json.dumps(tc.execution_config.get('body', {}), ensure_ascii=False)}")
            print(f"    断言: {[a['type'] for a in tc.assertions]}")


def demo_export_to_json(test_cases):
    """演示4: 导出为JSON"""
    print("\n" + "=" * 80)
    print("演示4: 导出为JSON格式")
    print("=" * 80)
    
    swagger_file = Path(__file__).parent / "sample_swagger.json"
    generator = SwaggerTestCaseGenerator(str(swagger_file))
    
    # 导出为JSON
    json_data = generator.export_to_json(test_cases[:2])
    
    print("\n📄 JSON格式（前2个用例）:")
    print(json.dumps(json_data, ensure_ascii=False, indent=2))
    
    # 保存到文件
    output_file = Path(__file__).parent.parent / "output" / "generated_testcases.json"
    output_file.parent.mkdir(exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(generator.export_to_json(test_cases), f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ 已保存到: {output_file}")


def demo_integration_with_execution_engine(test_cases):
    """演示5: 与ExecutionEngine集成"""
    print("\n" + "=" * 80)
    print("演示5: 与ExecutionEngine集成执行")
    print("=" * 80)
    
    from modules.executor import ExecutionEngine
    
    # 配置执行引擎
    config = {
        "base_url": "https://api.example.com",
        "timeout": 30,
        "retry_on_failure": True,
        "max_retries": 2
    }
    
    engine = ExecutionEngine(config)
    
    print("\n🚀 执行测试用例（模拟）...")
    print(f"  基础URL: {config['base_url']}")
    print(f"  超时时间: {config['timeout']}s")
    print(f"  重试次数: {config['max_retries']}")
    
    # 选择前3个用例执行（实际环境中会真正执行）
    print(f"\n📋 准备执行 {min(3, len(test_cases))} 个测试用例:")
    for tc in test_cases[:3]:
        print(f"  - {tc.id}: {tc.title}")
    
    print("\n💡 提示: 在真实环境中，这些用例会被ExecutionEngine执行")
    print("   执行结果会包含:")
    print("   - 状态（passed/failed）")
    print("   - 响应数据")
    print("   - 断言结果")
    print("   - 执行时间")


def demo_api_coverage():
    """演示6: API覆盖率分析"""
    print("\n" + "=" * 80)
    print("演示6: API覆盖率分析")
    print("=" * 80)
    
    swagger_file = Path(__file__).parent / "sample_swagger.json"
    generator = SwaggerTestCaseGenerator(str(swagger_file))
    
    # 获取API信息
    spec_info = generator.loader.get_spec_info()
    apis = generator.loader.get_all_apis()
    
    print(f"\n📚 Swagger规范信息:")
    print(f"  标题: {spec_info['title']}")
    print(f"  版本: {spec_info['api_version']}")
    print(f"  基础路径: {spec_info['base_path']}")
    print(f"  API总数: {spec_info['total_apis']}")
    
    print(f"\n🔍 API列表:")
    for api in apis:
        print(f"  {api['method']:6} {api['path']:30} - {api['summary']}")
    
    # 生成测试用例
    test_cases = generator.generate_all_testcases()
    
    print(f"\n✅ 覆盖率:")
    print(f"  API数量: {len(apis)}")
    print(f"  测试用例数: {len(test_cases)}")
    print(f"  平均每个API: {len(test_cases) / len(apis):.1f} 个用例")


if __name__ == "__main__":
    print("\n🎉 Swagger测试用例生成器演示\n")
    
    # 演示1: 基本生成
    test_cases = demo_basic_generation()
    
    # 演示2: 查看详情
    demo_testcase_details(test_cases)
    
    # 演示3: 对比不同类型用例
    demo_normal_vs_boundary_vs_error()
    
    # 演示4: 导出JSON
    demo_export_to_json(test_cases)
    
    # 演示5: 集成执行
    demo_integration_with_execution_engine(test_cases)
    
    # 演示6: 覆盖率分析
    demo_api_coverage()
    
    print("\n" + "=" * 80)
    print("✅ 所有演示完成！")
    print("=" * 80)
    print("\n💡 下一步:")
    print("  1. 查看生成的测试用例: output/generated_testcases.json")
    print("  2. 使用ExecutionEngine执行测试用例")
    print("  3. 查看执行结果和报告")
    print()
