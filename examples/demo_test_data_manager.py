"""
测试数据管理器演示
展示如何智能生成测试数据
"""
import sys
import json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.data import TestDataManager


def demo_basic_generation():
    """演示1: 基本数据生成"""
    print("=" * 80)
    print("演示1: 基本数据生成")
    print("=" * 80)
    
    manager = TestDataManager()
    
    # 定义schema
    schema = {
        "amount": {"type": "number", "minimum": 0, "maximum": 10000},
        "name": {"type": "string", "minLength": 1, "maxLength": 50},
        "email": {"type": "string", "format": "email"},
        "age": {"type": "integer", "minimum": 0, "maximum": 150},
        "is_active": {"type": "boolean"}
    }
    
    print("\n📋 Schema:")
    print(json.dumps(schema, indent=2))
    
    # 生成正常数据
    print("\n✅ 正常数据:")
    valid_data = manager.generate_data(schema, "valid")
    print(json.dumps(valid_data, indent=2, ensure_ascii=False))
    
    # 生成边界数据
    print("\n⚠️ 边界数据:")
    boundary_data = manager.generate_data(schema, "boundary")
    print(json.dumps(boundary_data, indent=2, ensure_ascii=False))
    
    # 生成异常数据
    print("\n❌ 异常数据:")
    invalid_data = manager.generate_data(schema, "invalid")
    print(json.dumps(invalid_data, indent=2, ensure_ascii=False))


def demo_all_categories():
    """演示2: 生成所有分类数据"""
    print("\n" + "=" * 80)
    print("演示2: 生成所有分类数据")
    print("=" * 80)
    
    manager = TestDataManager()
    
    schema = {
        "amount": "number",
        "name": "string"
    }
    
    print("\n📋 简化Schema:")
    print(json.dumps(schema, indent=2))
    
    # 生成所有分类
    all_data = manager.generate_all_categories(schema)
    
    print("\n📦 所有分类数据:")
    for category, data in all_data.items():
        print(f"\n  {category}:")
        print(f"    {json.dumps(data, ensure_ascii=False)}")


def demo_special_formats():
    """演示3: 特殊格式数据"""
    print("\n" + "=" * 80)
    print("演示3: 特殊格式数据")
    print("=" * 80)
    
    manager = TestDataManager()
    
    schema = {
        "email": {"type": "string", "format": "email"},
        "phone": "string",  # 自动识别
        "url": {"type": "string", "format": "url"},
        "password": "string",  # 自动识别
        "created_at": {"type": "string", "format": "date-time"},
        "user_id": {"type": "string", "format": "uuid"}
    }
    
    print("\n📋 特殊格式Schema:")
    for field, config in schema.items():
        print(f"  {field}: {config}")
    
    print("\n✅ 正常数据:")
    valid_data = manager.generate_data(schema, "valid")
    for field, value in valid_data.items():
        print(f"  {field}: {value}")
    
    print("\n❌ 异常数据:")
    invalid_data = manager.generate_data(schema, "invalid")
    for field, value in invalid_data.items():
        print(f"  {field}: {value}")


def demo_array_and_object():
    """演示4: 数组和对象数据"""
    print("\n" + "=" * 80)
    print("演示4: 数组和对象数据")
    print("=" * 80)
    
    manager = TestDataManager()
    
    schema = {
        "items": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "product_id": {"type": "integer"},
                    "quantity": {"type": "integer", "minimum": 1}
                }
            },
            "minItems": 1,
            "maxItems": 10
        },
        "address": {
            "type": "object",
            "properties": {
                "city": {"type": "string"},
                "zipcode": {"type": "string"}
            }
        }
    }
    
    print("\n📋 复杂Schema:")
    print(json.dumps(schema, indent=2))
    
    print("\n✅ 正常数据:")
    valid_data = manager.generate_data(schema, "valid")
    print(json.dumps(valid_data, indent=2, ensure_ascii=False))
    
    print("\n⚠️ 边界数据（空数组）:")
    boundary_data = manager.generate_data(schema, "boundary")
    print(json.dumps(boundary_data, indent=2, ensure_ascii=False))


def demo_payment_scenario():
    """演示5: 支付场景数据"""
    print("\n" + "=" * 80)
    print("演示5: 支付场景数据生成")
    print("=" * 80)
    
    manager = TestDataManager()
    
    # 支付接口schema
    schema = {
        "order_id": {"type": "integer", "minimum": 1},
        "amount": {"type": "number", "minimum": 0.01, "maximum": 100000},
        "payment_method": {
            "type": "string",
            "enum": ["credit_card", "alipay", "wechat"]
        },
        "user_id": {"type": "integer", "minimum": 1}
    }
    
    print("\n💳 支付接口Schema:")
    print(json.dumps(schema, indent=2))
    
    # 生成不同场景的数据
    scenarios = {
        "正常支付": "valid",
        "最小金额": "boundary",
        "异常金额": "invalid",
        "空值测试": "null"
    }
    
    for scenario_name, category in scenarios.items():
        print(f"\n📌 {scenario_name}:")
        data = manager.generate_data(schema, category)
        print(f"  {json.dumps(data, ensure_ascii=False)}")


def demo_integration_with_swagger():
    """演示6: 与Swagger生成器集成"""
    print("\n" + "=" * 80)
    print("演示6: 与Swagger生成器集成")
    print("=" * 80)
    
    from modules.swagger import SwaggerTestCaseGenerator
    
    # 加载Swagger
    swagger_file = Path(__file__).parent / "sample_swagger.json"
    generator = SwaggerTestCaseGenerator(str(swagger_file))
    
    # 获取一个API
    apis = generator.loader.get_all_apis()
    post_api = next((api for api in apis if api['method'] == 'POST'), None)
    
    if post_api:
        print(f"\n🎯 API: {post_api['method']} {post_api['path']}")
        
        # 提取schema
        if post_api.get('request_body'):
            schema = post_api['request_body'].get('schema', {})
            properties = schema.get('properties', {})
            
            if properties:
                print(f"\n📋 请求体Schema:")
                print(json.dumps(properties, indent=2, ensure_ascii=False))
                
                # 使用TestDataManager生成数据
                manager = TestDataManager()
                
                print(f"\n✅ 生成的正常数据:")
                valid_data = manager.generate_data(properties, "valid")
                print(json.dumps(valid_data, indent=2, ensure_ascii=False))
                
                print(f"\n❌ 生成的异常数据:")
                invalid_data = manager.generate_data(properties, "invalid")
                print(json.dumps(invalid_data, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    print("\n🎉 测试数据管理器演示\n")
    
    # 演示1: 基本生成
    demo_basic_generation()
    
    # 演示2: 所有分类
    demo_all_categories()
    
    # 演示3: 特殊格式
    demo_special_formats()
    
    # 演示4: 数组和对象
    demo_array_and_object()
    
    # 演示5: 支付场景
    demo_payment_scenario()
    
    # 演示6: 集成
    demo_integration_with_swagger()
    
    print("\n" + "=" * 80)
    print("✅ 所有演示完成！")
    print("=" * 80)
    print("\n💡 下一步:")
    print("  1. 在测试用例中使用TestDataManager生成数据")
    print("  2. 结合Swagger Generator自动生成测试数据")
    print("  3. 在Self-Healing中使用regenerate_data修复数据问题")
    print()
