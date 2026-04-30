"""
AI智能生成器测试
"""
import sys
sys.path.insert(0, 'test_data')

from data_factory import factory


def test_smart_generation():
    """测试智能生成"""
    print("\n========== AI智能生成测试 ==========")
    
    # 智能生成单个字段
    print("\n1. 智能生成单个字段:")
    email = factory.smart_generate('user_email', {'username': 'testuser'})
    print(f"   邮箱: {email}")
    
    phone = factory.smart_generate('contact_phone', {'country': 'CN'})
    print(f"   手机: {phone}")
    
    age = factory.smart_generate('user_age', {'role': 'adult'})
    print(f"   年龄: {age}")
    
    price = factory.smart_generate('product_price', {'category': '电子产品'})
    print(f"   价格: {price}")


def test_smart_object():
    """测试智能对象生成"""
    print("\n========== AI智能对象生成测试 ==========")
    
    # 定义schema
    user_schema = {
        'user_id': 'string',
        'username': 'string',
        'email': 'string',
        'phone': 'string',
        'age': 'integer',
        'status': 'string'
    }
    
    # 智能生成用户对象
    user = factory.smart_object(user_schema, {'role': 'adult', 'country': 'CN'})
    print("\n智能生成的用户对象:")
    for key, value in user.items():
        print(f"   {key}: {value}")


def test_field_analysis():
    """测试字段分析"""
    print("\n========== 字段分析测试 ==========")
    
    fields = ['user_email', 'product_price', 'order_status', 'created_at']
    
    for field in fields:
        analysis = factory.analyze_field(field)
        print(f"\n字段: {field}")
        print(f"   类型: {analysis['field_type']}")
        print(f"   数据类型: {analysis['data_type']}")
        print(f"   建议: {analysis['suggestions'][:2]}")


def test_schema_analysis():
    """测试schema分析"""
    print("\n========== Schema分析测试 ==========")
    
    order_schema = {
        'order_id': 'string',
        'user_id': 'string',
        'product_id': 'string',
        'quantity': 'integer',
        'price': 'float',
        'total_amount': 'float',
        'status': 'string',
        'created_at': 'datetime'
    }
    
    analysis = factory.analyze_schema(order_schema)
    print(f"\n实体类型: {analysis['entity_type']}")
    print(f"字段数量: {len(analysis['fields'])}")
    print(f"关系建议: {len(analysis['relationships'])}个")
    print(f"优化建议: {analysis['recommendations']}")


def test_scenario_suggestion():
    """测试场景建议"""
    print("\n========== 测试场景建议 ==========")
    
    entity_types = ['user', 'order', 'product']
    
    for entity_type in entity_types:
        scenarios = factory.suggest_scenarios(entity_type)
        print(f"\n{entity_type}实体的测试场景:")
        for scenario in scenarios[:3]:
            print(f"   - {scenario['name']} ({scenario['type']}, 优先级:{scenario['priority']})")


def test_quality_evaluation():
    """测试质量评估"""
    print("\n========== 数据质量评估测试 ==========")
    
    # 生成测试数据
    good_data = {
        'user_id': 'USR12345',
        'username': 'testuser',
        'email': 'test@example.com',
        'phone': '13800138000',
        'age': 25,
        'status': 'active',
        'created_at': '2024-01-01 10:00:00',
        'updated_at': '2024-01-02 10:00:00'
    }
    
    bad_data = {
        'user_id': '',
        'username': 'test',
        'email': 'invalid-email',
        'phone': '123',
        'age': 200,
        'status': 'unknown'
    }
    
    print("\n1. 优质数据评估:")
    result = factory.evaluate_quality(good_data)
    print(f"   总分: {result['total_score']}")
    print(f"   等级: {result['level']}")
    print(f"   完整性: {result['dimensions']['completeness']:.1f}")
    print(f"   有效性: {result['dimensions']['validity']:.1f}")
    print(f"   一致性: {result['dimensions']['consistency']:.1f}")
    print(f"   合理性: {result['dimensions']['reasonableness']:.1f}")
    
    print("\n2. 低质数据评估:")
    result = factory.evaluate_quality(bad_data)
    print(f"   总分: {result['total_score']}")
    print(f"   等级: {result['level']}")
    print(f"   问题: {len(result['issues'])}个")
    print(f"   建议: {result['suggestions'][:2]}")


def test_batch_evaluation():
    """测试批量评估"""
    print("\n========== 批量质量评估测试 ==========")
    
    # 生成批量数据
    data_list = [factory.user() for _ in range(5)]
    
    result = factory.batch_evaluate(data_list)
    print(f"\n评估数量: {result['count']}")
    print(f"平均分: {result['average_score']}")
    print(f"最高分: {result['max_score']}")
    print(f"最低分: {result['min_score']}")
    print(f"质量分布: {result['quality_distribution']}")


def test_generation_stats():
    """测试生成统计"""
    print("\n========== 生成统计测试 ==========")
    
    # 生成一些数据
    for _ in range(5):
        factory.smart_generate('user_email')
        factory.smart_generate('user_phone')
        factory.smart_generate('product_price')
    
    stats = factory.generation_stats()
    print(f"\n总生成次数: {stats['total']}")
    print(f"字段统计: {stats['fields']}")


def run_all_tests():
    """运行所有测试"""
    print("=" * 60)
    print("AI智能生成器完整测试")
    print("=" * 60)
    
    test_smart_generation()
    test_smart_object()
    test_field_analysis()
    test_schema_analysis()
    test_scenario_suggestion()
    test_quality_evaluation()
    test_batch_evaluation()
    test_generation_stats()
    
    print("\n" + "=" * 60)
    print("✅ 所有测试完成!")
    print("=" * 60)


if __name__ == "__main__":
    try:
        run_all_tests()
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
