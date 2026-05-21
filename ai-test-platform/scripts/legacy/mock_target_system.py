#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
模拟被测系统 - 用于演示真实测试执行

这是一个简单的Flask应用，模拟被测试的系统
"""

from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
import time
import uuid

app = Flask(__name__)
CORS(app)

# 模拟用户数据
users = {
    "test_user": {
        "password": "test_password",
        "user_id": "U001",
        "email": "test@example.com"
    }
}

# 模拟商品数据
products = [
    {"id": "P001", "name": "测试商品1", "price": 99.99, "category": "电子产品"},
    {"id": "P002", "name": "测试商品2", "price": 199.99, "category": "服装"},
    {"id": "P003", "name": "测试商品3", "price": 299.99, "category": "家居"}
]

# 模拟购物车数据
carts = {}

# 模拟仓储数据
inventory = {
    "P001": {"quantity": 1000, "warehouse": "W001"},
    "P002": {"quantity": 500, "warehouse": "W001"},
    "P003": {"quantity": 200, "warehouse": "W001"}
}

@app.route('/')
def home():
    return """
    <h1>模拟被测系统</h1>
    <p>这是一个用于测试的模拟系统</p>
    <ul>
        <li><a href="/login">登录页面</a></li>
        <li><a href="/register">注册页面</a></li>
        <li><a href="/api/products">商品API</a></li>
    </ul>
    """

@app.route('/login')
def login_page():
    return """
    <h2>登录页面</h2>
    <form>
        <input type="text" placeholder="用户名" name="username"><br><br>
        <input type="password" placeholder="密码" name="password"><br><br>
        <button type="button">登录</button>
    </form>
    """

@app.route('/register')
def register_page():
    return """
    <h2>注册页面</h2>
    <form>
        <input type="text" placeholder="用户名" name="username"><br><br>
        <input type="email" placeholder="邮箱" name="email"><br><br>
        <input type="password" placeholder="密码" name="password"><br><br>
        <button type="button">注册</button>
    </form>
    """

@app.route('/api/auth/login', methods=['POST'])
def api_login():
    """登录API"""
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    # 模拟处理时间
    time.sleep(0.1)
    
    if username in users and users[username]['password'] == password:
        token = str(uuid.uuid4())
        return jsonify({
            "success": True,
            "token": token,
            "user_id": users[username]['user_id'],
            "expires_at": int(time.time()) + 3600
        }), 200
    else:
        return jsonify({
            "success": False,
            "error": "用户名或密码错误"
        }), 401

@app.route('/api/auth/register', methods=['POST'])
def api_register():
    """注册API"""
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    
    time.sleep(0.2)
    
    if username in users:
        return jsonify({
            "success": False,
            "error": "用户名已存在"
        }), 400
    
    # 创建新用户
    user_id = f"U{len(users) + 1:03d}"
    users[username] = {
        "password": password,
        "user_id": user_id,
        "email": email
    }
    
    return jsonify({
        "success": True,
        "user_id": user_id,
        "message": "注册成功"
    }), 201

@app.route('/api/products')
def api_products():
    """商品列表API"""
    time.sleep(0.05)
    return jsonify({
        "success": True,
        "products": products,
        "total_count": len(products)
    })

@app.route('/api/products/search')
def api_product_search():
    """商品搜索API"""
    keyword = request.args.get('keyword', '')
    category = request.args.get('category', 'all')
    
    time.sleep(0.1)
    
    filtered_products = products
    if keyword:
        filtered_products = [p for p in filtered_products if keyword in p['name']]
    if category != 'all':
        filtered_products = [p for p in filtered_products if p['category'] == category]
    
    return jsonify({
        "success": True,
        "products": filtered_products,
        "total_count": len(filtered_products),
        "keyword": keyword,
        "category": category
    })

@app.route('/api/cart/add', methods=['POST'])
def api_cart_add():
    """添加到购物车API"""
    data = request.get_json()
    product_id = data.get('product_id')
    quantity = data.get('quantity', 1)
    user_id = data.get('user_id')
    
    time.sleep(0.1)
    
    if user_id not in carts:
        carts[user_id] = []
    
    # 检查商品是否存在
    product = next((p for p in products if p['id'] == product_id), None)
    if not product:
        return jsonify({
            "success": False,
            "error": "商品不存在"
        }), 404
    
    # 添加到购物车
    cart_item = {
        "product_id": product_id,
        "product_name": product['name'],
        "price": product['price'],
        "quantity": quantity
    }
    carts[user_id].append(cart_item)
    
    return jsonify({
        "success": True,
        "message": "商品已添加到购物车",
        "cart_item": cart_item
    }), 201

@app.route('/api/cart/<user_id>')
def api_cart_view(user_id):
    """查看购物车API"""
    time.sleep(0.05)
    
    user_cart = carts.get(user_id, [])
    total_amount = sum(item['price'] * item['quantity'] for item in user_cart)
    
    return jsonify({
        "success": True,
        "items": user_cart,
        "total_amount": total_amount,
        "item_count": len(user_cart)
    })

@app.route('/api/warehouse/inbound', methods=['POST'])
def api_warehouse_inbound():
    """入库API"""
    data = request.get_json()
    product_id = data.get('product_id')
    quantity = data.get('quantity')
    warehouse_id = data.get('warehouse_id')
    supplier_id = data.get('supplier_id')
    
    time.sleep(0.2)
    
    if product_id not in inventory:
        inventory[product_id] = {"quantity": 0, "warehouse": warehouse_id}
    
    inventory[product_id]["quantity"] += quantity
    
    return jsonify({
        "success": True,
        "message": f"商品 {product_id} 入库成功",
        "product_id": product_id,
        "quantity": quantity,
        "new_stock": inventory[product_id]["quantity"],
        "warehouse_id": warehouse_id,
        "supplier_id": supplier_id
    }), 201

@app.route('/api/warehouse/inventory')
def api_warehouse_inventory():
    """库存查询API"""
    time.sleep(0.1)
    return jsonify({
        "success": True,
        "inventory": inventory
    })

@app.route('/health')
def health_check():
    """健康检查"""
    return jsonify({
        "status": "healthy",
        "timestamp": int(time.time()),
        "version": "1.0.0"
    })

if __name__ == '__main__':
    print("🚀 启动模拟被测系统")
    print("📍 地址: http://localhost:8080")
    print("🔗 健康检查: http://localhost:8080/health")
    print("=" * 50)
    app.run(host='0.0.0.0', port=8080, debug=True)