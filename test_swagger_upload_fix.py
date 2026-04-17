"""
测试Swagger上传修复
验证不同场景下的错误处理
"""
import json
import tempfile
from pathlib import Path
from modules.swagger.swagger_testcase_generator import SwaggerTestCaseGenerator
from modules.swagger.api_spec_loader import ApiSpecLoader


def test_valid_swagger_2():
    """测试有效的Swagger 2.0文件"""
    print("\n=== 测试1: 有效的Swagger 2.0 ===")
    
    swagger_doc = {
        "swagger": "2.0",
        "info": {"title": "Test API", "version": "1.0.0"},
        "paths": {
            "/users": {
                "get": {
                    "summary": "Get users",
                    "responses": {"200": {"description": "Success"}}
                }
            }
        }
    }
    
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
        json.dump(swagger_doc, f)
        temp_path = f.name
    
    try:
        generator = SwaggerTestCaseGenerator(temp_path)
        test_cases = generator.generate_all_testcases()
        print(f"✅ 成功: 生成了 {len(test_cases)} 个测试用例")
        return True
    except Exception as e:
        print(f"❌ 失败: {e}")
        return False
    finally:
        Path(temp_path).unlink()


def test_valid_openapi_3():
    """测试有效的OpenAPI 3.0文件"""
    print("\n=== 测试2: 有效的OpenAPI 3.0 ===")
    
    openapi_doc = {
        "openapi": "3.0.0",
        "info": {"title": "Test API", "version": "1.0.0"},
        "paths": {
            "/users": {
                "get": {
                    "summary": "Get users",
                    "responses": {"200": {"description": "Success"}}
                }
            }
        }
    }
    
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
        json.dump(openapi_doc, f)
        temp_path = f.name
    
    try:
        generator = SwaggerTestCaseGenerator(temp_path)
        test_cases = generator.generate_all_testcases()
        print(f"✅ 成功: 生成了 {len(test_cases)} 个测试用例")
        return True
    except Exception as e:
        print(f"❌ 失败: {e}")
        return False
    finally:
        Path(temp_path).unlink()


def test_missing_version_key():
    """测试缺少版本键的文件"""
    print("\n=== 测试3: 缺少版本键 ===")
    
    invalid_doc = {
        "info": {"title": "Test API", "version": "1.0.0"},
        "paths": {
            "/users": {
                "get": {
                    "summary": "Get users",
                    "responses": {"200": {"description": "Success"}}
                }
            }
        }
    }
    
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
        json.dump(invalid_doc, f)
        temp_path = f.name
    
    try:
        generator = SwaggerTestCaseGenerator(temp_path)
        print(f"❌ 应该抛出错误但没有")
        return False
    except ValueError as e:
        error_msg = str(e)
        if "Unknown spec version" in error_msg and "Available keys" in error_msg:
            print(f"✅ 正确捕获错误: {error_msg}")
            return True
        else:
            print(f"❌ 错误信息不够详细: {error_msg}")
            return False
    except Exception as e:
        print(f"❌ 意外错误: {e}")
        return False
    finally:
        Path(temp_path).unlink()


def test_empty_file():
    """测试空文件"""
    print("\n=== 测试4: 空文件 ===")
    
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
        f.write("")
        temp_path = f.name
    
    try:
        generator = SwaggerTestCaseGenerator(temp_path)
        print(f"❌ 应该抛出错误但没有")
        return False
    except ValueError as e:
        error_msg = str(e)
        if "empty" in error_msg.lower():
            print(f"✅ 正确捕获错误: {error_msg}")
            return True
        else:
            print(f"⚠️ 捕获了错误但信息不够明确: {error_msg}")
            return True
    except Exception as e:
        print(f"❌ 意外错误: {e}")
        return False
    finally:
        Path(temp_path).unlink()


def test_invalid_json():
    """测试无效的JSON"""
    print("\n=== 测试5: 无效的JSON ===")
    
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
        f.write("{invalid json content")
        temp_path = f.name
    
    try:
        generator = SwaggerTestCaseGenerator(temp_path)
        print(f"❌ 应该抛出错误但没有")
        return False
    except ValueError as e:
        error_msg = str(e)
        if "JSON" in error_msg or "YAML" in error_msg:
            print(f"✅ 正确捕获错误: {error_msg[:100]}...")
            return True
        else:
            print(f"⚠️ 捕获了错误: {error_msg[:100]}...")
            return True
    except Exception as e:
        print(f"❌ 意外错误: {e}")
        return False
    finally:
        Path(temp_path).unlink()


def test_non_dict_content():
    """测试非字典内容"""
    print("\n=== 测试6: 非字典内容 ===")
    
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
        json.dump(["array", "content"], f)
        temp_path = f.name
    
    try:
        generator = SwaggerTestCaseGenerator(temp_path)
        print(f"❌ 应该抛出错误但没有")
        return False
    except ValueError as e:
        error_msg = str(e)
        if "dictionary" in error_msg.lower() or "object" in error_msg.lower():
            print(f"✅ 正确捕获错误: {error_msg}")
            return True
        else:
            print(f"⚠️ 捕获了错误: {error_msg}")
            return True
    except Exception as e:
        print(f"❌ 意外错误: {e}")
        return False
    finally:
        Path(temp_path).unlink()


if __name__ == "__main__":
    print("=" * 60)
    print("Swagger上传修复测试")
    print("=" * 60)
    
    results = []
    
    # 运行所有测试
    results.append(("有效Swagger 2.0", test_valid_swagger_2()))
    results.append(("有效OpenAPI 3.0", test_valid_openapi_3()))
    results.append(("缺少版本键", test_missing_version_key()))
    results.append(("空文件", test_empty_file()))
    results.append(("无效JSON", test_invalid_json()))
    results.append(("非字典内容", test_non_dict_content()))
    
    # 统计结果
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {name}")
    
    print(f"\n总计: {passed}/{total} 通过")
    
    if passed == total:
        print("\n🎉 所有测试通过!")
    else:
        print(f"\n⚠️ {total - passed} 个测试失败")
