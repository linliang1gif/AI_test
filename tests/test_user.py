"""
user模块API自动化测试脚本
自动生成于：2026-03-13 15:45:24
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

def test_concurrent_order_modification():
    """TC019-验证两个用户同时修改同一订单基本信息时的并发控制"""
    # 测试数据准备
    base_url = "http://api.example.com"
    order_id = "test_order_123"  # 假设的测试订单ID
    
    # 用户A的请求数据 - 修改客户名称
    user_a_token = "token_user_a"
    user_a_headers = {
        "Authorization": f"Bearer {user_a_token}",
        "Content-Type": "application/json"
    }
    user_a_data = {
        "order_id": order_id,
        "customer_name": "客户A",
        "version": 1  # 假设使用乐观锁，需要版本号
    }
    
    # 用户B的请求数据 - 修改联系电话
    user_b_token = "token_user_b"
    user_b_headers = {
        "Authorization": f"Bearer {user_b_token}",
        "Content-Type": "application/json"
    }
    user_b_data = {
        "order_id": order_id,
        "phone": "13800138000",
        "version": 1  # 初始版本号，可能与用户A的请求冲突
    }
    
    # 步骤1: 用户A修改订单
    url = f"{base_url}/api/orders/{order_id}"
    response_a = requests.put(url, json=user_a_data, headers=user_a_headers)
    
    # 断言用户A的保存操作应成功
    assert response_a.status_code == 200, f"用户A保存失败: {response_a.status_code}"
    assert response_a.json().get("success") == True, "用户A保存未返回成功状态"
    
    # 步骤2: 用户B尝试修改订单（模拟并发操作）
    response_b = requests.put(url, json=user_b_data, headers=user_b_headers)
    
    # 验证并发控制 - 两种情况都可能发生
    if response_b.status_code == 409:  # 乐观锁冲突
        # 情况a: 系统提示数据已被修改
        error_message = response_b.json().get("message", "")
        assert "数据已被他人修改" in error_message or "请刷新后重试" in error_message, \
            f"未返回预期的并发控制提示: {error_message}"
        print("并发控制生效: 用户B的修改被阻止")
        
        # 步骤3: 验证最终数据一致性
        get_response = requests.get(url, headers=user_a_headers)
        final_data = get_response.json()
        assert final_data.get("customer_name") == "客户A", "用户A的修改未生效"
        assert final_data.get("phone") != "13800138000", "用户B的修改不应生效"
        
    elif response_b.status_code == 200:  # 合并保存成功
        # 情况b: 系统成功合并修改
        assert response_b.json().get("success") == True, "用户B保存未返回成功状态"
        print("并发控制: 修改被成功合并")
        
        # 验证合并后的数据
        get_response = requests.get(url, headers=user_a_headers)
        final_data = get_response.json()
        assert final_data.get("customer_name") == "客户A", "用户A的客户名称修改未保留"
        assert final_data.get("phone") == "13800138000", "用户B的电话修改未生效"
        
    else:
        # 其他状态码表示测试失败
        pytest.fail(f"用户B保存返回了意外的状态码: {response_b.status_code}")
    
    # 最终验证：两个用户获取的数据应该一致
    response_a_view = requests.get(url, headers=user_a_headers)
    response_b_view = requests.get(url, headers=user_b_headers)
    
    assert response_a_view.status_code == 200, "用户A无法查看订单"
    assert response_b_view.status_code == 200, "用户B无法查看订单"
    
    data_a = response_a_view.json()
    data_b = response_b_view.json()
    
    # 验证数据一致性
    assert data_a == data_b, "两个用户看到的订单数据不一致"

def test_role_based_order_access_permissions():
    """TC020-验证不同角色用户对订单详情页的访问与操作权限差异"""
    # 测试数据准备
    base_url = "http://api.example.com"
    order_id = "test_order_123"
    
    # 定义不同角色的测试账号
    roles = [
        {
            "name": "viewer",
            "token": "token_viewer",
            "description": "查看人员"
        },
        {
            "name": "editor",
            "token": "token_editor",
            "description": "编辑人员"
        },
        {
            "name": "admin",
            "token": "token_admin",
            "description": "管理员"
        }
    ]
    
    # 测试每个角色的权限
    for role in roles:
        print(f"\n测试角色: {role['description']}")
        
        # 准备请求头
        headers = {
            "Authorization": f"Bearer {role['token']}",
            "Content-Type": "application/json"
        }
        
        # Step1 & Step2: 访问订单详情页
        url = f"{base_url}/api/orders/{order_id}/detail"
        response = requests.get(url, headers=headers)
        
        # 预期结果1: 所有角色均应能成功访问订单详情页面
        assert response.status_code == 200, \
            f"{role['description']}无法访问订单详情页: {response.status_code}"
        
        order_data = response.json()
        
        # Step3 & Step4: 检查页面元素和操作权限
        page_info = order_data.get("page_info", {})
        buttons = page_info.get("available_buttons", [])
        editable_fields = page_info.get("editable_fields", [])
        
        # 根据角色验证权限
        if role["name"] == "viewer":
            # 预期结果2: 查看人员应为纯只读状态
            assert len(editable_fields) == 0, "查看人员不应有可编辑字段"
            
            # 验证不应出现的按钮
            forbidden_buttons = ["edit", "delete", "submit_review"]
            for button in forbidden_buttons:
                assert button not in buttons, f"查看人员不应有'{button}'按钮"
            
            # 尝试编辑操作（应被拒绝）
            edit_url = f"{base_url}/api/orders/{order_id}"
            edit_data = {"customer_name": "测试修改"}
            edit_response = requests.put(edit_url, json=edit_data, headers=headers)
            
            # 预期结果5: 无权限的操作会失败
            assert edit_response.status_code in [403, 401], \
                f"查看人员不应能编辑订单，但返回了: {edit_response.status_code}"
            
        elif role["name"] == "editor":
            # 预期结果3: 编辑人员应有部分编辑权限
            expected_editable = ["customer_name", "phone", "address", "items"]
            for field in expected_editable:
                assert field in editable_fields, f"编辑人员应能编辑'{field}'字段"
            
            # 应有保存按钮，但可能没有删除按钮
            assert "save" in buttons, "编辑人员应有保存按钮"
            assert "delete" not in buttons, "编辑人员不应有删除按钮"
            
            # 测试编辑操作（应成功）
            edit_url = f"{base_url}/api/orders/{order_id}"
            edit_data = {"customer_name": "编辑人员修改"}
            edit_response = requests.put(edit_url, json=edit_data, headers=headers)
            
            assert edit_response.status_code == 200, \
                f"编辑人员编辑失败: {edit_response.status_code}"
            
        elif role["name"] == "admin":
            # 预期结果4: 管理员应有全部权限
            expected_buttons = ["save", "delete", "submit_review", "approve", "reject"]
            for button in expected_buttons:
                assert button in buttons, f"管理员应有'{button}'按钮"
            
            # 所有字段都应可编辑
            expected_fields = ["customer_name", "phone", "address", "items", "status", "priority"]
            for field in expected_fields:
                assert field in editable_fields, f"管理员应能编辑'{field}'字段"
            
            # 测试删除操作（应成功）
            delete_url = f"{base_url}/api/orders/{order_id}"
            delete_response = requests.delete(delete_url, headers=headers)
            
            # 注意：实际测试中可能需要恢复测试数据
            if delete_response.status_code == 200:
                print("管理员成功删除订单（测试环境）")
                # 在实际测试中，这里可能需要重新创建测试订单
            else:
                # 在某些系统中，删除可能需要额外确认
                assert delete_response.status_code in [200, 202, 204], \
                    f"管理员删除失败: {delete_response.status_code}"
        
        print(f"{role['description']}权限验证通过")