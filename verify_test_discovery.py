"""
验证Test Discovery Agent功能
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from modules.discovery import TestDiscoveryAgent, RiskLevel


def verify_swagger_discovery():
    """验证Swagger变更发现"""
    print("=" * 60)
    print("验证1: Swagger变更发现")
    print("=" * 60)
    
    try:
        agent = TestDiscoveryAgent()
        
        old_swagger = Path(__file__).parent / "examples" / "old_swagger.json"
        new_swagger = Path(__file__).parent / "examples" / "new_swagger.json"
        
        test_points = agent.discover_from_swagger_changes(
            str(old_swagger),
            str(new_swagger)
        )
        
        if len(test_points) > 0:
            print(f"✅ Swagger变更发现功能正常")
            print(f"   发现了 {len(test_points)} 个测试点")
            return True
        else:
            print("❌ 未发现任何测试点")
            return False
    except Exception as e:
        print(f"❌ Swagger变更发现失败: {e}")
        return False


def verify_test_point_structure():
    """验证测试点结构"""
    print("\n" + "=" * 60)
    print("验证2: 测试点结构")
    print("=" * 60)
    
    try:
        agent = TestDiscoveryAgent()
        
        old_swagger = Path(__file__).parent / "examples" / "old_swagger.json"
        new_swagger = Path(__file__).parent / "examples" / "new_swagger.json"
        
        test_points = agent.discover_from_swagger_changes(
            str(old_swagger),
            str(new_swagger)
        )
        
        if not test_points:
            print("❌ 没有测试点")
            return False
        
        tp = test_points[0]
        
        # 检查必需字段
        required_fields = ['test_point', 'reason', 'risk_level', 'suggested_test_type']
        missing_fields = []
        
        for field in required_fields:
            if not hasattr(tp, field) or getattr(tp, field) is None:
                missing_fields.append(field)
        
        if missing_fields:
            print(f"❌ 缺少字段: {missing_fields}")
            return False
        
        print("✅ 测试点结构正确")
        print(f"   描述: {tp.test_point[:50]}...")
        print(f"   风险: {tp.risk_level}")
        print(f"   类型: {tp.suggested_test_type}")
        return True
        
    except Exception as e:
        print(f"❌ 结构验证失败: {e}")
        return False


def verify_risk_detection():
    """验证风险识别"""
    print("\n" + "=" * 60)
    print("验证3: 风险识别")
    print("=" * 60)
    
    try:
        agent = TestDiscoveryAgent()
        
        old_swagger = Path(__file__).parent / "examples" / "old_swagger.json"
        new_swagger = Path(__file__).parent / "examples" / "new_swagger.json"
        
        test_points = agent.discover_from_swagger_changes(
            str(old_swagger),
            str(new_swagger)
        )
        
        # 检查是否识别出高风险测试点
        has_critical = any(tp.risk_level == RiskLevel.CRITICAL.value for tp in test_points)
        has_high = any(tp.risk_level == RiskLevel.HIGH.value for tp in test_points)
        
        print(f"  严重风险: {'✅' if has_critical else '❌'}")
        print(f"  高风险: {'✅' if has_high else '❌'}")
        
        if has_critical or has_high:
            print("\n✅ 风险识别功能正常")
            return True
        else:
            print("\n❌ 未识别出高风险测试点")
            return False
            
    except Exception as e:
        print(f"❌ 风险识别验证失败: {e}")
        return False


def verify_export_functionality():
    """验证导出功能"""
    print("\n" + "=" * 60)
    print("验证4: 导出功能")
    print("=" * 60)
    
    try:
        agent = TestDiscoveryAgent()
        
        old_swagger = Path(__file__).parent / "examples" / "old_swagger.json"
        new_swagger = Path(__file__).parent / "examples" / "new_swagger.json"
        
        test_points = agent.discover_from_swagger_changes(
            str(old_swagger),
            str(new_swagger)
        )
        
        # 导出为JSON
        json_data = agent.export_to_json()
        
        # 验证JSON格式
        if not isinstance(json_data, list):
            print("❌ 导出格式不是列表")
            return False
        
        if len(json_data) != len(test_points):
            print("❌ 导出数量不匹配")
            return False
        
        # 验证JSON可序列化
        import json
        json_str = json.dumps(json_data, ensure_ascii=False)
        
        print("✅ 导出功能正常")
        print(f"   导出了 {len(json_data)} 个测试点")
        return True
        
    except Exception as e:
        print(f"❌ 导出功能失败: {e}")
        return False


def main():
    """运行所有验证"""
    print("\n🚀 开始验证Test Discovery Agent\n")
    
    results = []
    
    try:
        results.append(("Swagger发现", verify_swagger_discovery()))
    except Exception as e:
        print(f"❌ Swagger发现验证异常: {e}")
        results.append(("Swagger发现", False))
    
    try:
        results.append(("测试点结构", verify_test_point_structure()))
    except Exception as e:
        print(f"❌ 测试点结构验证异常: {e}")
        results.append(("测试点结构", False))
    
    try:
        results.append(("风险识别", verify_risk_detection()))
    except Exception as e:
        print(f"❌ 风险识别验证异常: {e}")
        results.append(("风险识别", False))
    
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
        print("\n🎉 所有验证通过！Test Discovery Agent工作正常！")
        return 0
    else:
        print(f"\n⚠️ {total - passed} 个验证失败，请检查")
        return 1


if __name__ == "__main__":
    exit(main())
