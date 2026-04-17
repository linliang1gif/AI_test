#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Agent 完整演示
展示AI测试决策中心的实际应用场景
"""

import requests
import json
import time


BASE_URL = "http://localhost:8000"


def print_section(title):
    """打印分节标题"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def print_result(result):
    """格式化打印结果"""
    print(f"\n📊 决策结果:")
    print(f"  需要测试: {'✅ 是' if result['need_test'] else '❌ 否'}")
    print(f"  影响模块: {', '.join(result['modules'])}")
    print(f"  优先级: {result['priority']}")
    print(f"  风险等级: {result['risk_level']}")
    print(f"  预估工作量: {result['estimated_effort']}")
    print(f"  测试类型: {', '.join(result['test_types'])}")
    print(f"  决策理由: {result['reason']}")
    print(f"  分析耗时: {result['duration']}")
    print(f"  使用模型: {result['provider']} - {result['model']}")


def scenario_1_payment_feature():
    """场景1: 新增支付功能"""
    print_section("场景1: 新增核心功能 - 订单支付")
    
    request_data = {
        "requirement": """
需求：新增订单支付功能

功能描述：
1. 用户下单后可以选择支付方式（微信支付、支付宝支付）
2. 点击支付按钮后跳转到支付页面
3. 支付成功后订单状态更新为"已支付"
4. 支付失败显示错误提示
5. 支持支付超时自动取消

技术实现：
- 集成微信支付SDK
- 集成支付宝SDK
- 添加支付回调接口
- 更新订单状态机
        """,
        "git_diff": """
diff --git a/order/service.py b/order/service.py
+++ b/order/service.py
@@ -10,6 +10,25 @@ class OrderService:
+    def process_payment(self, order_id, payment_method):
+        '''处理支付逻辑'''
+        order = self.get_order(order_id)
+        if not order:
+            raise OrderNotFound()
+        
+        if payment_method == 'wechat':
+            result = wechat_pay_service.create_payment(order)
+        elif payment_method == 'alipay':
+            result = alipay_service.create_payment(order)
+        else:
+            raise InvalidPaymentMethod()
+        
+        if result.success:
+            order.status = 'paid'
+            order.paid_at = datetime.now()
+            order.save()
+        
+        return result
        """
    }
    
    print("\n📝 需求内容:")
    print(request_data["requirement"].strip())
    
    print("\n🔍 代码变更:")
    print(request_data["git_diff"].strip()[:300] + "...")
    
    print("\n⏳ AI正在分析...")
    response = requests.post(f"{BASE_URL}/agent/analyze", json=request_data)
    result = response.json()
    
    print_result(result)


def scenario_2_bug_fix():
    """场景2: Bug修复"""
    print_section("场景2: Bug修复 - 库存计算错误")
    
    request_data = {
        "requirement": "修复库存计算bug：当用户退货时，库存数量没有正确增加",
        "git_diff": """
diff --git a/inventory/service.py b/inventory/service.py
+++ b/inventory/service.py
@@ -15,7 +15,7 @@ def handle_return(product_id, quantity):
     inventory = Inventory.get(product_id)
-    inventory.quantity -= quantity  # Bug: 应该是增加
+    inventory.quantity += quantity  # 修复: 退货应该增加库存
     inventory.save()
        """
    }
    
    print("\n📝 需求: " + request_data["requirement"])
    print("\n⏳ AI正在分析...")
    
    response = requests.post(f"{BASE_URL}/agent/analyze", json=request_data)
    result = response.json()
    
    print_result(result)


def scenario_3_doc_update():
    """场景3: 文档更新"""
    print_section("场景3: 文档更新 - 无需测试")
    
    request_data = {
        "requirement": "更新项目README文档，添加贡献指南和许可证说明",
        "git_diff": """
diff --git a/README.md b/README.md
+++ b/README.md
@@ -50,3 +50,20 @@
+## 贡献指南
+
+欢迎贡献代码！请遵循以下步骤：
+1. Fork本项目
+2. 创建特性分支
+3. 提交代码
+4. 发起Pull Request
+
+## 许可证
+
+MIT License
        """
    }
    
    print("\n📝 需求: " + request_data["requirement"])
    print("\n⏳ AI正在分析...")
    
    response = requests.post(f"{BASE_URL}/agent/analyze", json=request_data)
    result = response.json()
    
    print_result(result)


def scenario_4_refactoring():
    """场景4: 代码重构"""
    print_section("场景4: 代码重构 - 提取公共方法")
    
    request_data = {
        "requirement": "重构用户服务代码，提取公共的参数验证方法，提高代码复用性",
        "git_diff": """
diff --git a/user/service.py b/user/service.py
+++ b/user/service.py
@@ -5,15 +5,20 @@
+def validate_user_params(username, email):
+    '''验证用户参数'''
+    if not username or len(username) < 3:
+        raise ValueError("用户名长度不能少于3")
+    if not email or '@' not in email:
+        raise ValueError("邮箱格式不正确")
+
 def create_user(username, email):
-    if not username or len(username) < 3:
-        raise ValueError("用户名长度不能少于3")
-    if not email or '@' not in email:
-        raise ValueError("邮箱格式不正确")
+    validate_user_params(username, email)
     # 创建用户逻辑...
        """
    }
    
    print("\n📝 需求: " + request_data["requirement"])
    print("\n⏳ AI正在分析...")
    
    response = requests.post(f"{BASE_URL}/agent/analyze", json=request_data)
    result = response.json()
    
    print_result(result)


def scenario_5_performance():
    """场景5: 性能优化"""
    print_section("场景5: 性能优化 - 数据库查询优化")
    
    request_data = {
        "requirement": "优化订单列表查询性能，添加索引，减少N+1查询问题",
        "git_diff": """
diff --git a/order/models.py b/order/models.py
+++ b/order/models.py
@@ -10,6 +10,7 @@ class Order(Model):
     user_id = IntegerField()
     status = CharField()
+    created_at = DateTimeField(index=True)  # 添加索引
     
diff --git a/order/service.py b/order/service.py
+++ b/order/service.py
@@ -20,7 +20,8 @@ def get_user_orders(user_id):
-    orders = Order.query.filter_by(user_id=user_id).all()
+    # 优化: 使用join避免N+1查询
+    orders = Order.query.filter_by(user_id=user_id).join(User).all()
        """
    }
    
    print("\n📝 需求: " + request_data["requirement"])
    print("\n⏳ AI正在分析...")
    
    response = requests.post(f"{BASE_URL}/agent/analyze", json=request_data)
    result = response.json()
    
    print_result(result)


def show_statistics():
    """显示统计信息"""
    print_section("📊 Test Agent 统计信息")
    
    response = requests.get(f"{BASE_URL}/agent/statistics")
    stats = response.json()['data']
    
    print(f"\n总决策次数: {stats['total_decisions']}")
    print(f"需要测试: {stats['need_test_count']} ({stats['need_test_rate']})")
    print(f"无需测试: {stats['no_test_count']}")
    print(f"\n优先级分布:")
    for priority, count in stats['priority_distribution'].items():
        print(f"  {priority}: {count}次")


def demo_ci_cd_integration():
    """演示CI/CD集成场景"""
    print_section("🔄 CI/CD集成演示")
    
    print("""
在CI/CD流程中，每次代码提交时自动调用Test Agent分析：

1. 开发者提交代码
2. CI触发构建
3. 调用Test Agent分析变更
4. 根据决策结果：
   - need_test=true → 执行测试流程
   - need_test=false → 跳过测试，直接部署
5. 节省测试资源和时间

示例代码：
""")
    
    print("""
# .github/workflows/ci.yml
- name: Analyze Test Need
  run: |
    RESULT=$(curl -X POST http://test-agent:8000/agent/analyze \\
      -H "Content-Type: application/json" \\
      -d '{"requirement": "${{ github.event.head_commit.message }}", 
           "git_diff": "$(git diff HEAD~1)"}')
    
    NEED_TEST=$(echo $RESULT | jq -r '.need_test')
    
    if [ "$NEED_TEST" = "true" ]; then
      echo "需要执行测试"
      npm run test
    else
      echo "无需测试，跳过"
    fi
    """)


if __name__ == "__main__":
    print("🚀 Test Agent 完整演示")
    print("=" * 70)
    print("展示AI测试决策中心在实际场景中的应用")
    print()
    
    try:
        # 场景演示
        scenario_1_payment_feature()
        time.sleep(1)
        
        scenario_2_bug_fix()
        time.sleep(1)
        
        scenario_3_doc_update()
        time.sleep(1)
        
        scenario_4_refactoring()
        time.sleep(1)
        
        scenario_5_performance()
        time.sleep(1)
        
        # 统计信息
        show_statistics()
        
        # CI/CD集成演示
        demo_ci_cd_integration()
        
        print("\n" + "=" * 70)
        print("✅ 演示完成!")
        print("=" * 70)
        print("\n💡 Test Agent 可以帮助你：")
        print("  1. 自动判断是否需要测试")
        print("  2. 识别影响范围和优先级")
        print("  3. 节省测试资源和时间")
        print("  4. 集成到CI/CD流程")
        print("\n📚 查看完整文档: agent/README.md")
        print("🌐 API文档: http://localhost:8000/docs")
        
    except requests.exceptions.ConnectionError:
        print("\n❌ 连接失败! 请确保后端服务已启动:")
        print("   py backend_api_server.py")
    except Exception as e:
        print(f"\n❌ 演示失败: {e}")
        import traceback
        traceback.print_exc()
