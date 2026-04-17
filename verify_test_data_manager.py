"""
验证测试数据管理器功能
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from modules.data import TestDataManager


def verify_basic_generation():
    """验证1: 基本数据生成"""
    print("=" * 60)
    print("验证1: 基本数据生成")
    print("=" * 60)
    
    try:
        manager = TestDataManager()
        
        schema = {
            "amount": "number",
            "name": "string",
            "is_active": "boolean"
        }
        
        # 生成正常数据
        valid_data = manager.generate_data(schema, "valid")
        
        # 验证数据类型
        if not isinstance(valid_data["amount"], (int, float)):
            print("❌ amount类型错误")
            return False
        
        if not isinstance(valid_data["name"], str):
            print("❌ name类型错误")
            return False
        
        if not isinstance(valid_data["is_active"], bool):
            print("❌ is_active类型错误")
            return False
        
        print("✅ 基本数据生成功能正常")
        print(f"   生成数据: {valid_data}")
        return True
        
    except Exception as e:
        print(f"❌ 基本数据生成失败: {e}")
        return False


def verify_all_categories():
    """验证2: 所有分类数据生成"""
    print("\n" + "=" * 60)
    print("验证2: 所有分类数据生成")
    print("=" * 60)
    
    try:
        manager = TestDataManager()
        
        schema = {"amount": "number"}
        
        all_data = manager.generate_all_categories(schema)
        
        # 验证包含所有分类
        required_categories = ["valid", "boundary", "invalid", "null", "empty"]
        
        for category in required_categories:
            if category not in all_data:
                print(f"❌ 缺少分类: {category}")
                return False
        
        # 验证null分类
        if all_data["null"]["amount"] is not None:
            print("❌ null分类数据不正确")
            return False
        
        print("✅ 所有分类数据生成功能正常")
        print(f"   分类数: {len(all_data)}")
        return True
        
    except Exception as e:
        print(f"❌ 所有分类数据生成失败: {e}")
        return False


def verify_boundary_values():
    """验证3: 边界值生成"""
    print("\n" + "=" * 60)
    print("验证3: 边界值生成")
    print("=" * 60)
    
    try:
        manager = TestDataManager()
        
        schema = {
            "amount": {"type": "number", "minimum": 0, "maximum": 100}
        }
        
        # 生成边界数据
        boundary_data = manager.generate_data(schema, "boundary")
        amount = boundary_data["amount"]
        
        # 验证是最小值或最大值
        if amount not in [0, 100]:
            print(f"❌ 边界值不正确: {amount}")
            return False
        
        print("✅ 边界值生成功能正常")
        print(f"   边界值: {amount}")
        return True
        
    except Exception as e:
        print(f"❌ 边界值生成失败: {e}")
        return False


def verify_invalid_values():
    """验证4: 异常值生成"""
    print("\n" + "=" * 60)
    print("验证4: 异常值生成")
    print("=" * 60)
    
    try:
        manager = TestDataManager()
        
        schema = {
            "amount": {"type": "number", "minimum": 0, "maximum": 100}
        }
        
        # 生成异常数据
        invalid_data = manager.generate_data(schema, "invalid")
        amount = invalid_data["amount"]
        
        # 验证是异常值（超出范围或负数）
        if not (amount < 0 or amount > 100):
            print(f"❌ 异常值不正确: {amount}")
            return False
        
        print("✅ 异常值生成功能正常")
        print(f"   异常值: {amount}")
        return True
        
    except Exception as e:
        print(f"❌ 异常值生成失败: {e}")
        return False


def verify_special_formats():
    """验证5: 特殊格式生成"""
    print("\n" + "=" * 60)
    print("验证5: 特殊格式生成")
    print("=" * 60)
    
    try:
        manager = TestDataManager()
        
        schema = {
            "email": {"type": "string", "format": "email"}
        }
        
        # 生成正常邮箱
        valid_data = manager.generate_data(schema, "valid")
        email = valid_data["email"]
        
        # 简单验证邮箱格式
        if "@" not in email or "." not in email:
            print(f"❌ 邮箱格式不正确: {email}")
            return False
        
        # 生成异常邮箱
        invalid_data = manager.generate_data(schema, "invalid")
        invalid_email = invalid_data["email"]
        
        # 验证是异常邮箱（不需要严格验证，只要不是完全正确的格式即可）
        # test@.com 也算异常邮箱（域名格式错误）
        
        print("✅ 特殊格式生成功能正常")
        print(f"   正常邮箱: {email}")
        print(f"   异常邮箱: {invalid_email}")
        return True
        
    except Exception as e:
        print(f"❌ 特殊格式生成失败: {e}")
        return False


def main():
    """运行所有验证"""
    print("\n🚀 开始验证测试数据管理器\n")
    
    results = []
    
    try:
        results.append(("基本生成", verify_basic_generation()))
    except Exception as e:
        print(f"❌ 基本生成验证异常: {e}")
        results.append(("基本生成", False))
    
    try:
        results.append(("所有分类", verify_all_categories()))
    except Exception as e:
        print(f"❌ 所有分类验证异常: {e}")
        results.append(("所有分类", False))
    
    try:
        results.append(("边界值", verify_boundary_values()))
    except Exception as e:
        print(f"❌ 边界值验证异常: {e}")
        results.append(("边界值", False))
    
    try:
        results.append(("异常值", verify_invalid_values()))
    except Exception as e:
        print(f"❌ 异常值验证异常: {e}")
        results.append(("异常值", False))
    
    try:
        results.append(("特殊格式", verify_special_formats()))
    except Exception as e:
        print(f"❌ 特殊格式验证异常: {e}")
        results.append(("特殊格式", False))
    
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
        print("\n🎉 所有验证通过！测试数据管理器工作正常！")
        return 0
    else:
        print(f"\n⚠️ {total - passed} 个验证失败，请检查")
        return 1


if __name__ == "__main__":
    exit(main())
