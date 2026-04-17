"""
验证Swagger测试用例生成器功能
"""
import sys
import json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from modules.swagger import SwaggerTestCaseGenerator


def verify_basic_generation():
    """验证1: 基本生成功能"""
    print("=" * 60)
    print("验证1: 基本生成功能")
    print("=" * 60)
    
    try:
        swagger_file = Path(__file__).parent / "examples" / "sample_swagger.json"
        generator = SwaggerTestCaseGenerator(str(swagger_file))
        
        test_cases = generator.generate_all_testcases()
        
        if len(test_cases) > 0:
            print(f"✅ 基本生成功能正常")
            print(f"   生成了 {len(test_cases)} 个测试用例")
            return True
        else:
            print("❌ 未生成任何测试用例")
            return False
    except Exception as e:
        print(f"❌ 基本生成功能失败: {e}")
        return False


def verify_testcase_structure():
    """验证2: 测试用例结构"""
    print("\n" + "=" * 60)
    print("验证2: 测试用例结构")
    print("=" * 60)
    
    try:
        swagger_file = Path(__file__).parent / "examples" / "sample_swagger.json"
        generator = SwaggerTestCaseGenerator(str(swagger_file))
        
        test_cases = generator.generate_all_testcases()
        
        if not test_cases:
            print("❌ 没有测试用例")
            return False
        
        tc = test_cases[0]
        
        # 检查必需字段
        required_fields = ['id', 'title', 'module', 'execution_config', 'assertions']
        missing_fields = []
        
        for field in required_fields:
            if not hasattr(tc, field):
                missing_fields.append(field)
        
        if missing_fields:
            print(f"❌ 缺少字段: {missing_fields}")
            return False
        
        # 检查execution_config
        if 'method' not in tc.execution_config:
            print("❌ execution_config缺少method")
            return False
        
        if 'url' not in tc.execution_config:
            print("❌ execution_config缺少url")
            return False
        
        # 检查assertions
        if not tc.assertions:
            print("❌ 没有断言")
            return False
        
        print("✅ 测试用例结构正确")
        print(f"   ID: {tc.id}")
        print(f"   标题: {tc.title}")
        print(f"   方法: {tc.execution_config['method']}")
        print(f"   URL: {tc.execution_config['url']}")
        print(f"   断言数: {len(tc.assertions)}")
        return True
        
    except Exception as e:
        print(f"❌ 结构验证失败: {e}")
        return False


def verify_scenario_coverage():
    """验证3: 场景覆盖（正常/边界/异常）"""
    print("\n" + "=" * 60)
    print("验证3: 场景覆盖")
    print("=" * 60)
    
    try:
        swagger_file = Path(__file__).parent / "examples" / "sample_swagger.json"
        generator = SwaggerTestCaseGenerator(str(swagger_file))
        
        # 获取第一个API
        apis = generator.loader.get_all_apis()
        if not apis:
            print("❌ 没有API定义")
            return False
        
        api = apis[0]
        test_cases = generator.generate_testcases_for_api(api)
        
        # 检查是否包含不同场景
        titles = [tc.title for tc in test_cases]
        
        has_normal = any('正常' in title for title in titles)
        has_boundary = any('边界' in title for title in titles)
        has_error = any('异常' in title for title in titles)
        
        print(f"  正常用例: {'✅' if has_normal else '❌'}")
        print(f"  边界用例: {'✅' if has_boundary else '❌'}")
        print(f"  异常用例: {'✅' if has_error else '❌'}")
        
        if has_normal and has_boundary and has_error:
            print("\n✅ 场景覆盖完整")
            print(f"   共生成 {len(test_cases)} 个用例")
            return True
        else:
            print("\n❌ 场景覆盖不完整")
            return False
            
    except Exception as e:
        print(f"❌ 场景覆盖验证失败: {e}")
        return False


def verify_swagger_compliance():
    """验证4: Swagger规范遵守"""
    print("\n" + "=" * 60)
    print("验证4: Swagger规范遵守")
    print("=" * 60)
    
    try:
        swagger_file = Path(__file__).parent / "examples" / "sample_swagger.json"
        generator = SwaggerTestCaseGenerator(str(swagger_file))
        
        test_cases = generator.generate_all_testcases()
        apis = generator.loader.get_all_apis()
        
        # 检查URL是否来自Swagger
        swagger_paths = [api['path'] for api in apis]
        
        invalid_urls = []
        for tc in test_cases:
            url = tc.execution_config['url']
            # 移除路径参数的值，还原为模板
            url_template = url
            for api_path in swagger_paths:
                if api_path.replace('{', '').replace('}', '') in url.replace('/', ''):
                    url_template = api_path
                    break
            
            if url_template not in swagger_paths:
                # 检查是否是参数替换后的URL
                is_valid = False
                for path in swagger_paths:
                    if '{' in path:
                        # 简单检查路径结构
                        path_parts = path.split('/')
                        url_parts = url.split('/')
                        if len(path_parts) == len(url_parts):
                            is_valid = True
                            break
                
                if not is_valid:
                    invalid_urls.append(url)
        
        if invalid_urls:
            print(f"❌ 发现虚构的URL: {invalid_urls[:3]}")
            return False
        
        print("✅ 所有URL都来自Swagger定义")
        print(f"   Swagger定义的API: {len(swagger_paths)}")
        print(f"   生成的测试用例: {len(test_cases)}")
        return True
        
    except Exception as e:
        print(f"❌ Swagger规范验证失败: {e}")
        return False


def verify_assertions_quality():
    """验证5: 断言质量"""
    print("\n" + "=" * 60)
    print("验证5: 断言质量")
    print("=" * 60)
    
    try:
        swagger_file = Path(__file__).parent / "examples" / "sample_swagger.json"
        generator = SwaggerTestCaseGenerator(str(swagger_file))
        
        test_cases = generator.generate_all_testcases()
        
        # 检查断言
        total_assertions = 0
        has_status_code = 0
        has_json_path = 0
        
        for tc in test_cases:
            total_assertions += len(tc.assertions)
            
            for assertion in tc.assertions:
                if assertion['type'] == 'status_code':
                    has_status_code += 1
                elif assertion['type'] == 'json_path':
                    has_json_path += 1
        
        print(f"  总断言数: {total_assertions}")
        print(f"  状态码断言: {has_status_code}")
        print(f"  JSON Path断言: {has_json_path}")
        
        # 每个用例至少应该有1个断言
        min_assertions = min(len(tc.assertions) for tc in test_cases)
        
        if min_assertions >= 1 and has_status_code > 0:
            print("\n✅ 断言质量合格")
            print(f"   每个用例至少 {min_assertions} 个断言")
            return True
        else:
            print("\n❌ 断言质量不足")
            return False
            
    except Exception as e:
        print(f"❌ 断言质量验证失败: {e}")
        return False


def verify_export_functionality():
    """验证6: 导出功能"""
    print("\n" + "=" * 60)
    print("验证6: 导出功能")
    print("=" * 60)
    
    try:
        swagger_file = Path(__file__).parent / "examples" / "sample_swagger.json"
        generator = SwaggerTestCaseGenerator(str(swagger_file))
        
        test_cases = generator.generate_all_testcases()
        
        # 导出为JSON
        json_data = generator.export_to_json(test_cases)
        
        # 验证JSON格式
        if not isinstance(json_data, list):
            print("❌ 导出格式不是列表")
            return False
        
        if len(json_data) != len(test_cases):
            print("❌ 导出数量不匹配")
            return False
        
        # 验证JSON可序列化
        json_str = json.dumps(json_data, ensure_ascii=False)
        
        print("✅ 导出功能正常")
        print(f"   导出了 {len(json_data)} 个用例")
        print(f"   JSON大小: {len(json_str)} 字节")
        return True
        
    except Exception as e:
        print(f"❌ 导出功能失败: {e}")
        return False


def main():
    """运行所有验证"""
    print("\n🚀 开始验证Swagger测试用例生成器\n")
    
    results = []
    
    try:
        results.append(("基本生成", verify_basic_generation()))
    except Exception as e:
        print(f"❌ 基本生成验证异常: {e}")
        results.append(("基本生成", False))
    
    try:
        results.append(("用例结构", verify_testcase_structure()))
    except Exception as e:
        print(f"❌ 用例结构验证异常: {e}")
        results.append(("用例结构", False))
    
    try:
        results.append(("场景覆盖", verify_scenario_coverage()))
    except Exception as e:
        print(f"❌ 场景覆盖验证异常: {e}")
        results.append(("场景覆盖", False))
    
    try:
        results.append(("Swagger规范", verify_swagger_compliance()))
    except Exception as e:
        print(f"❌ Swagger规范验证异常: {e}")
        results.append(("Swagger规范", False))
    
    try:
        results.append(("断言质量", verify_assertions_quality()))
    except Exception as e:
        print(f"❌ 断言质量验证异常: {e}")
        results.append(("断言质量", False))
    
    try:
        results.append(("导出功能", verify_export_functionality()))
    except Exception as e:
        print(f"❌ 导出功能验证异常: {e}")
        results.append(("导出功能", False))
    
    # 汇总结果
    print("\n" + "=" * 60)
    print("验证结果汇总")
    print("=" * 60)
    
    for name, passed in results:
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"{status} - {name}")
    
    total = len(results)
    passed = sum(1 for _, p in results if p)
    
    print(f"\n总计: {total}, 通过: {passed}, 失败: {total - passed}")
    print(f"通过率: {passed/total*100:.1f}%")
    
    if passed == total:
        print("\n🎉 所有验证通过！Swagger生成器工作正常！")
        return 0
    else:
        print(f"\n⚠️ {total - passed} 个验证失败，请检查")
        return 1


if __name__ == "__main__":
    exit(main())
