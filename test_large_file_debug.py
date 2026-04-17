"""
调试大文件上传
"""
from modules.swagger.swagger_testcase_generator import SwaggerTestCaseGenerator
import traceback


file_path = r"ai-test-platform\swaggerApi (1).json"

print("=" * 60)
print("调试大文件上传")
print("=" * 60)
print(f"\n文件: {file_path}")

try:
    print("\n正在加载Swagger文件...")
    generator = SwaggerTestCaseGenerator(file_path)
    
    print("✅ 文件加载成功")
    print(f"API数量: {len(generator.loader.get_all_apis())}")
    
    print("\n正在生成测试用例...")
    test_cases = generator.generate_all_testcases()
    
    print(f"✅ 生成成功: {len(test_cases)} 个测试用例")
    
except Exception as e:
    print(f"\n❌ 错误: {e}")
    print(f"\n完整错误信息:")
    traceback.print_exc()
