"""
测试数据工厂快速验证
"""
import sys
sys.path.insert(0, 'test_data')

from data_factory import factory


def quick_test():
    """快速验证测试"""
    print("=" * 60)
    print("测试数据工厂快速验证")
    print("=" * 60)
    
    # 1. 基础数据
    print("\n1. 基础数据生成:")
    print(f"   邮箱: {factory.email()}")
    print(f"   手机: {factory.phone()}")
    print(f"   姓名: {factory.chinese_name()}")
    
    # 2. 业务对象
    print("\n2. 业务对象生成:")
    user = factory.user()
    print(f"   用户: {user['username']} - {user['email']}")
    
    product = factory.product()
    print(f"   产品: {product['name']} - ¥{product['price']}")
    
    # 3. Mock数据
    print("\n3. Mock数据生成:")
    response = factory.api_response(success=True, data={"test": "ok"})
    print(f"   API响应: code={response['code']}, message={response['message']}")
    
    token = factory.jwt_token(user_id="123")
    print(f"   JWT Token: {token[:50]}...")
    
    # 4. 批量生成
    print("\n4. 批量生成:")
    users = factory.batch("user", 3)
    print(f"   生成了 {len(users)} 个用户")
    
    # 5. 模板使用
    print("\n5. 模板使用:")
    templates = factory.list_templates()
    print(f"   可用模板: {', '.join(templates)}")
    
    login_data = factory.from_template("user_login", username="test", password="123")
    print(f"   登录数据: {login_data}")
    
    # 6. 依赖管理
    print("\n6. 依赖管理:")
    order = factory.with_dependencies("order")
    print(f"   订单(带依赖): order_id={order['order_id']}, total={order['total_amount']}")
    
    print("\n" + "=" * 60)
    print("✅ 所有功能验证通过!")
    print("=" * 60)


if __name__ == "__main__":
    try:
        quick_test()
    except Exception as e:
        print(f"\n❌ 验证失败: {e}")
        import traceback
        traceback.print_exc()
