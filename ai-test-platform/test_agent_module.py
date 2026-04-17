#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Agent 模块测试脚本
"""

import requests
import json


BASE_URL = "http://localhost:8000"


def test_analyze_api():
    """测试分析API"""
    print("=" * 60)
    print("🧪 测试 Test Agent 分析API")
    print("=" * 60)
    
    # 测试用例1: 核心功能变更
    print("\n【测试1】核心功能变更 - 订单支付")
    test_case_1 = {
        "requirement": "新增订单支付功能，支持微信支付和支付宝支付。用户下单后可以选择支付方式，完成支付后订单状态更新为已支付。",
        "git_diff": """
diff --git a/order/service.py b/order/service.py
+++ b/order/service.py
@@ -10,6 +10,15 @@ class OrderService:
+    def process_payment(self, order_id, payment_method):
+        # 处理支付逻辑
+        order = self.get_order(order_id)
+        if payment_method == 'wechat':
+            result = wechat_pay(order)
+        elif payment_method == 'alipay':
+            result = alipay_pay(order)
+        order.status = 'paid'
+        order.save()
"""
    }
    
    response = requests.post(f"{BASE_URL}/agent/analyze", json=test_case_1)
    print(f"状态码: {response.status_code}")
    result = response.json()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    
    # 测试用例2: 文档更新
    print("\n【测试2】文档更新 - 无需测试")
    test_case_2 = {
        "requirement": "更新README文档，添加安装说明和使用示例",
        "git_diff": """
diff --git a/README.md b/README.md
+++ b/README.md
@@ -1,3 +1,10 @@
 # 项目名称
+
+## 安装
+pip install -r requirements.txt
+
+## 使用
+python main.py
"""
    }
    
    response = requests.post(f"{BASE_URL}/agent/analyze", json=test_case_2)
    print(f"状态码: {response.status_code}")
    result = response.json()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    
    # 测试用例3: Bug修复
    print("\n【测试3】Bug修复 - 用户登录")
    test_case_3 = {
        "requirement": "修复用户登录时密码验证失败的bug",
        "git_diff": """
diff --git a/auth/service.py b/auth/service.py
+++ b/auth/service.py
@@ -5,7 +5,7 @@ def login(username, password):
     user = User.query.filter_by(username=username).first()
     if not user:
         return None
-    if user.password == password:
+    if check_password_hash(user.password, password):
         return user
"""
    }
    
    response = requests.post(f"{BASE_URL}/agent/analyze", json=test_case_3)
    print(f"状态码: {response.status_code}")
    result = response.json()
    print(json.dumps(result, ensure_ascii=False, indent=2))


def test_history_api():
    """测试历史记录API"""
    print("\n" + "=" * 60)
    print("🧪 测试决策历史API")
    print("=" * 60)
    
    response = requests.get(f"{BASE_URL}/agent/history?limit=5")
    print(f"状态码: {response.status_code}")
    result = response.json()
    print(f"历史记录数: {result['count']}")
    print(json.dumps(result, ensure_ascii=False, indent=2))


def test_statistics_api():
    """测试统计API"""
    print("\n" + "=" * 60)
    print("🧪 测试统计信息API")
    print("=" * 60)
    
    response = requests.get(f"{BASE_URL}/agent/statistics")
    print(f"状态码: {response.status_code}")
    result = response.json()
    print(json.dumps(result, ensure_ascii=False, indent=2))


def test_health_api():
    """测试健康检查API"""
    print("\n" + "=" * 60)
    print("🧪 测试健康检查API")
    print("=" * 60)
    
    response = requests.get(f"{BASE_URL}/agent/health")
    print(f"状态码: {response.status_code}")
    result = response.json()
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    print("🚀 Test Agent 模块测试")
    print("确保后端服务已启动: python backend_api_server.py")
    print()
    
    try:
        # 健康检查
        test_health_api()
        
        # 测试分析功能
        test_analyze_api()
        
        # 测试历史记录
        test_history_api()
        
        # 测试统计信息
        test_statistics_api()
        
        print("\n" + "=" * 60)
        print("✅ 所有测试完成!")
        print("=" * 60)
        
    except requests.exceptions.ConnectionError:
        print("\n❌ 连接失败! 请确保后端服务已启动:")
        print("   python backend_api_server.py")
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
