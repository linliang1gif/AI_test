"""
product模块API自动化测试脚本
自动生成于：2026-03-13 13:50:14
"""
import pytest
import requests


# 测试配置
BASE_URL = "http://localhost:8080"  # 请根据实际情况修改
DEFAULT_HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json"
}

def get_full_url(endpoint: str) -> str:
    """获取完整的API URL"""
    return f"{BASE_URL.rstrip('/')}{endpoint}"

def test_query_product_by_id():
    """测试根据ID查询商品详情"""
    # 测试数据准备
    base_url = "http://api.example.com"
    endpoint = "/api/products"
    product_id = 123  # 假设存在的商品ID
    url = f"{base_url}{endpoint}/{product_id}"
    
    # 发送GET请求
    response = requests.get(url)
    
    # 断言验证
    # 1. 验证状态码为200
    assert response.status_code == 200, f"Expected status code 200, but got {response.status_code}"
    
    # 2. 验证响应包含商品信息
    response_data = response.json()
    assert "id" in response_data, "Response should contain 'id' field"
    assert response_data["id"] == product_id, f"Expected product id {product_id}, but got {response_data.get('id')}"
    
    # 3. 验证关键业务字段存在
    required_fields = ["name", "price", "stock"]
    for field in required_fields:
        assert field in response_data, f"Response should contain '{field}' field"
    
    # 4. 验证字段类型和格式
    assert isinstance(response_data["name"], str), "Product name should be a string"
    assert isinstance(response_data["price"], (int, float)), "Product price should be a number"
    assert isinstance(response_data["stock"], int), "Product stock should be an integer"
    
    # 5. 验证价格和库存非负
    assert response_data["price"] >= 0, "Product price should be non-negative"
    assert response_data["stock"] >= 0, "Product stock should be non-negative"