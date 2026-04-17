"""
快速测试Swagger生成器
"""
import sys
import json
from pathlib import Path

print("🚀 快速测试Swagger生成器\n")

try:
    # 1. 导入模块
    print("1️⃣ 导入模块...")
    from modules.swagger import SwaggerTestCaseGenerator
    print("   ✅ 模块导入成功")
    
    # 2. 加载Swagger文件
    print("\n2️⃣ 加载Swagger文件...")
    swagger_file = Path(__file__).parent / "examples" / "sample_swagger.json"
    
    if not swagger_file.exists():
        print(f"   ❌ Swagger文件不存在: {swagger_file}")
        sys.exit(1)
    
    print(f"   ✅ Swagger文件存在: {swagger_file}")
    
    # 3. 初始化生成器
    print("\n3️⃣ 初始化生成器...")
    generator = SwaggerTestCaseGenerator(str(swagger_file))
    print("   ✅ 生成器初始化成功")
    
    # 4. 获取API信息
    print("\n4️⃣ 获取API信息...")
    spec_info = generator.loader.get_spec_info()
    print(f"   API标题: {spec_info['title']}")
    print(f"   API版本: {spec_info['api_version']}")
    print(f"   API总数: {spec_info['total_apis']}")
    
    # 5. 生成测试用例
    print("\n5️⃣ 生成测试用例...")
    test_cases = generator.generate_all_testcases()
    print(f"   ✅ 生成了 {len(test_cases)} 个测试用例")
    
    # 6. 显示统计信息
    print("\n6️⃣ 统计信息:")
    stats = generator.get_statistics(test_cases)
    print(f"   总用例数: {stats['total']}")
    print(f"   覆盖API数: {stats['apis_covered']}")
    print(f"   按优先级: {stats['by_priority']}")
    print(f"   按模块: {stats['by_module']}")
    
    # 7. 显示第一个测试用例
    print("\n7️⃣ 第一个测试用例示例:")
    if test_cases:
        tc = test_cases[0]
        print(f"   ID: {tc.id}")
        print(f"   标题: {tc.title}")
        print(f"   模块: {tc.module}")
        print(f"   优先级: {tc.priority.value}")
        print(f"   方法: {tc.execution_config['method']}")
        print(f"   URL: {tc.execution_config['url']}")
        print(f"   断言数: {len(tc.assertions)}")
    
    # 8. 导出为JSON
    print("\n8️⃣ 导出为JSON...")
    json_data = generator.export_to_json(test_cases[:3])
    print(f"   ✅ 导出了前3个用例")
    print(f"   JSON示例（第1个用例）:")
    print(json.dumps(json_data[0], ensure_ascii=False, indent=2)[:500] + "...")
    
    # 9. 验证用例结构
    print("\n9️⃣ 验证用例结构...")
    required_fields = ['id', 'title', 'module', 'execution_config', 'assertions']
    tc = test_cases[0]
    
    all_present = all(hasattr(tc, field) for field in required_fields)
    has_method = 'method' in tc.execution_config
    has_url = 'url' in tc.execution_config
    has_assertions = len(tc.assertions) > 0
    
    if all_present and has_method and has_url and has_assertions:
        print("   ✅ 用例结构完整")
    else:
        print("   ❌ 用例结构不完整")
        sys.exit(1)
    
    # 10. 验证场景覆盖
    print("\n🔟 验证场景覆盖...")
    titles = [tc.title for tc in test_cases]
    has_normal = any('正常' in title for title in titles)
    has_boundary = any('边界' in title for title in titles)
    has_error = any('异常' in title for title in titles)
    
    print(f"   正常用例: {'✅' if has_normal else '❌'}")
    print(f"   边界用例: {'✅' if has_boundary else '❌'}")
    print(f"   异常用例: {'✅' if has_error else '❌'}")
    
    if has_normal and has_boundary and has_error:
        print("\n🎉 所有测试通过！Swagger生成器工作正常！")
        sys.exit(0)
    else:
        print("\n⚠️ 场景覆盖不完整")
        sys.exit(1)
        
except Exception as e:
    print(f"\n❌ 测试失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
