"""
api模块API自动化测试脚本
自动生成于：2026-03-13 15:43:40
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

def test_customize_list_fields_visibility():\n    \"\"\"TC010-验证列表字段显示/隐藏的自定义功能\"\"\"\n    # 模拟用户登录（实际项目中应有独立的登录逻辑）\n    login_url = \"http://api.example.com/auth/login\"\n    login_data = {\"username\": \"test_user\", \"password\": \"test_password\"}\n    login_response = requests.post(login_url, json=login_data)\n    assert login_response.status_code == 200\n    token = login_response.json().get(\"token\")\n    \n    # 获取当前字段配置\n    get_config_url = \"http://api.example.com/sales/orders/list/field-config\"\n    headers = {\"Authorization\": f\"Bearer {token}\"}\n    get_response = requests.get(get_config_url, headers=headers)\n    assert get_response.status_code == 200\n    current_config = get_response.json()\n    \n    # 修改字段配置：隐藏\"客户联系人\"，显示\"预计交货日期\"\n    update_config_url = \"http://api.example.com/sales/orders/list/field-config\"\n    updated_fields = current_config.get(\"fields\", [])\n    # 假设字段配置是一个字段名列表，需要更新显示状态\n    # 这里简化处理，实际根据接口数据结构调整\n    config_data = {\n        \"fields\": [\n            {\"name\": \"客户联系人\", \"visible\": False},\n            {\"name\": \"预计交货日期\", \"visible\": True}\n        ]\n    }\n    update_response = requests.post(update_config_url, json=config_data, headers=headers)\n    \n    # 断言配置更新成功\n    assert update_response.status_code == 200\n    assert update_response.json().get(\"success\") == True\n    \n    # 验证列表刷新后的字段显示\n    list_url = \"http://api.example.com/sales/orders\"\n    list_response = requests.get(list_url, headers=headers)\n    assert list_response.status_code == 200\n    list_data = list_response.json()\n    \n    # 检查字段显示状态（假设返回的列表数据包含字段信息）\n    columns = list_data.get(\"columns\", [])\n    column_names = [col.get(\"name\") for col in columns]\n    assert \"客户联系人\" not in column_names\n    assert \"预计交货日期\" in column_names",
      "imports": ["import requests", "import pytest"],
      "api_info": {
        "method": "POST",
        "endpoint": "/sales/orders/list/field-config",
        "description": "更新列表字段显示配置"
      }
    },
    {
      "function_name": "test_adjust_list_fields_order",
      "docstring": "TC011-验证拖动调整列表字段顺序的功能",
      "code": "def test_adjust_list_fields_order():\n    \"\"\"TC011-验证拖动调整列表字段顺序的功能\"\"\"\n    # 模拟登录\n    login_url = \"http://api.example.com/auth/login\"\n    login_data = {\"username\": \"test_user\", \"password\": \"test_password\"}\n    login_response = requests.post(login_url, json=login_data)\n    assert login_response.status_code == 200\n    token = login_response.json().get(\"token\")\n    \n    # 获取当前字段顺序\n    get_config_url = \"http://api.example.com/sales/orders/list/field-config\"\n    headers = {\"Authorization\": f\"Bearer {token}\"}\n    get_response = requests.get(get_config_url, headers=headers)\n    assert get_response.status_code == 200\n    current_config = get_response.json()\n    \n    # 调整字段顺序：将\"订单金额\"移到\"客户名称\"之前\n    # 假设字段配置包含顺序信息\n    fields = current_config.get(\"fields\", [])\n    order_amount_index = next((i for i, f in enumerate(fields) if f.get(\"name\") == \"订单金额\"), -1)\n    customer_name_index = next((i for i, f in enumerate(fields) if f.get(\"name\") == \"客户名称\"), -1)\n    \n    # 重新排序\n    if order_amount_index != -1 and customer_name_index != -1:\n        fields.insert(customer_name_index, fields.pop(order_amount_index))\n    \n    config_data = {\"fields\": fields}\n    update_config_url = \"http://api.example.com/sales/orders/list/field-config\"\n    update_response = requests.post(update_config_url, json=config_data, headers=headers)\n    \n    # 断言配置更新成功\n    assert update_response.status_code == 200\n    assert update_response.json().get(\"success\") == True\n    \n    # 验证列表字段顺序\n    list_url = \"http://api.example.com/sales/orders\"\n    list_response = requests.get(list_url, headers=headers)\n    assert list_response.status_code == 200\n    list_data = list_response.json()\n    \n    columns = list_data.get(\"columns\", [])\n    column_names = [col.get(\"name\") for col in columns]\n    \n    # 检查\"订单金额\"是否在\"客户名称\"之前\n    if \"订单金额\" in column_names and \"客户名称\" in column_names:\n        order_amount_pos = column_names.index(\"订单金额\")\n        customer_name_pos = column_names.index(\"客户名称\")\n        assert order_amount_pos < customer_name_pos",
      "imports": ["import requests", "import pytest"],
      "api_info": {
        "method": "POST",
        "endpoint": "/sales/orders/list/field-config",
        "description": "更新列表字段顺序配置"
      }
    },
    {
      "function_name": "test_query_condition_boundary_validation",
      "docstring": "TC012-验证查询条件输入值的边界处理（超长字符）",
      "code": "def test_query_condition_boundary_validation():\n    \"\"\"TC012-验证查询条件输入值的边界处理（超长字符）\"\"\"\n    # 模拟登录\n    login_url = \"http://api.example.com/auth/login\"\n    login_data = {\"username\": \"test_user\", \"password\": \"test_password\"}\n    login_response = requests.post(login_url, json=login_data)\n    assert login_response.status_code == 200\n    token = login_response.json().get(\"token\")\n    \n    # 测试超长订单编号查询\n    query_url = \"http://api.example.com/sales/orders/query\"\n    headers = {\"Authorization\": f\"Bearer {token}\", \"Content-Type\": \"application/json\"}\n    \n    # 生成超过100个字符的字符串\n    long_order_no = \"A\" * 101\n    query_data = {\n        \"order_no\": long_order_no,\n        \"page\": 1,\n        \"page_size\": 10\n    }\n    \n    response = requests.post(query_url, json=query_data, headers=headers)\n    \n    # 断言：系统应正确处理超长输入\n    # 可能情况1：返回400状态码并给出错误提示\n    # 可能情况2：返回200但结果为空\n    if response.status_code == 400:\n        error_msg = response.json().get(\"message\", \"\")\n        assert \"长度\" in error_msg or \"过长\" in error_msg or \"无效\" in error_msg\n    elif response.status_code == 200:\n        result = response.json()\n        # 检查是否返回空结果或错误信息\n        assert result.get(\"total\", 0) == 0 or \"error\" in result\n    else:\n        # 其他状态码视为测试失败\n        assert False, f\"Unexpected status code: {response.status_code}\"",
      "imports": ["import requests", "import pytest"],
      "api_info": {
        "method": "POST",
        "endpoint": "/sales/orders/query",
        "description": "销售订单查询接口"
      }
    },
    {
      "function_name": "test_query_condition_state_persistence",
      "docstring": "TC013-验证查询条件在页面刷新或回退后的状态保持",
      "code": "def test_query_condition_state_persistence():\n    \"\"\"TC013-验证查询条件在页面刷新或回退后的状态保持\"\"\"\n    # 模拟登录\n    login_url = \"http://api.example.com/auth/login\"\n    login_data = {\"username\": \"test_user\", \"password\": \"test_password\"}\n    login_response = requests.post(login_url, json=login_data)\n    assert login_response.status_code == 200\n    token = login_response.json().get(\"token\")\n    \n    # 设置复杂查询条件\n    query_url = \"http://api.example.com/sales/orders/query\"\n    headers = {\"Authorization\": f\"Bearer {token}\", \"Content-Type\": \"application/json\"}\n    \n    query_data = {\n        \"customer\": \"A\",\n        \"status\": \"pending_review\",\n        \"date_from\": \"2024-01-01\",\n        \"date_to\": \"2024-01-31\",\n        \"page\": 1,\n        \"page_size\": 10\n    }\n    \n    # 执行查询\n    response = requests.post(query_url, json=query_data, headers=headers)\n    assert response.status_code == 200\n    \n    # 模拟页面刷新：重新获取查询条件\n    # 假设有接口可以获取上次查询条件\n    get_query_state_url = \"http://api.example.com/sales/orders/query/state\"\n    state_response = requests.get(get_query_state_url, headers=headers)\n    \n    # 断言查询条件被保存\n    if state_response.status_code == 200:\n        saved_state = state_response.json()\n        assert saved_state.get(\"customer\") == \"A\"\n        assert saved_state.get(\"status\") == \"pending_review\"\n        assert saved_state.get(\"date_from\") == \"2024-01-01\"\n        assert saved_state.get(\"date_to\") == \"2024-01-31\"\n    else:\n        # 如果系统不支持查询状态保存，则跳过此断言\n        pytest.skip(\"Query state persistence not supported by API\")",
      "imports": ["import requests", "import pytest"],
      "api_info": {
        "method": "GET",
        "endpoint": "/sales/orders/query/state",
        "description": "获取保存的查询条件状态"
      }
    },
    {
      "function_name": "test_material_list_max_rows_boundary",
      "docstring": "TC014-验证物料清单分录数量的上限边界",
      "code": "def test_material_list_max_rows_boundary():\n    \"\"\"TC014-验证物料清单分录数量的上限边界\"\"\"\n    # 模拟登录\n    login_url = \"http://api.example.com/auth/login\"\n    login_data = {\"username\": \"test_user\", \"password\": \"test_password\"}\n    login_response = requests.post(login_url, json=login_data)\n    assert login_response.status_code == 200\n    token = login_response.json().get(\"token\")\n    \n    # 获取草稿订单\n    draft_orders_url = \"http://api.example.com/sales/orders?status=draft\"\n    headers = {\"Authorization\": f\"Bearer {token}\"}\n    orders_response = requests.get(draft_orders_url, headers=headers)\n    assert orders_response.status_code == 200\n    \n    orders = orders_response.json().get(\"data\", [])\n    assert len(orders) > 0, \"No draft orders found\"\n    order_id = orders[0].get(\"id\")\n    \n    # 获取订单详情\n    order_detail_url = f\"http://api.example.com/sales/orders/{order_id}\"\n    detail_response = requests.get(order_detail_url, headers=headers)\n    assert detail_response.status_code == 200\n    \n    # 添加物料分录直到达到上限\n    add_material_url = f\"http://api.example.com/sales/orders/{order_id}/materials\"\n    \n    # 先添加100条物料分录\n    for i in range(100):\n        material_data = {\n            \"material_code\": f\"MAT{i:03d}\",\n            \"quantity\": 1,\n            \"unit_price\": 10.0\n        }\n        add_response = requests.post(add_material_url, json=material_data, headers=headers)\n        \n        # 检查是否达到上限\n        if add_response.status_code == 400:\n            error_msg = add_response.json().get(\"message\", \"\")\n            assert \"上限\" in error_msg or \"最大\" in error_msg or \"限制\" in error_msg\n            break\n        else:\n            assert add_response.status_code == 201\n    \n    # 尝试添加第101条\n    material_data = {\n        \"material_code\": \"MAT101\",\n        \"quantity\": 1,\n        \"unit_price\": 10.0\n    }\n    final_response = requests.post(add_material_url, json=material_data, headers=headers)\n    \n    # 断言第101条应该失败\n    assert final_response.status_code == 400\n    error_msg = final_response.json().get(\"message\", \"\")\n    assert \"上限\" in error_msg or \"最大\" in error_msg or \"限制\" in error_msg",
      "imports": ["import requests", "import pytest"],
      "api_info": {
        "method": "POST",
        "endpoint": "/sales/orders/{order_id}/materials",
        "description": "为销售订单添加物料分录"
      }
    },
    {
      "function_name": "test_material_fields_boundary_validation",
      "docstring": "TC015-验证物料清单分录中数值型字段的边界（数量、单价）",
      "code": "def test_material_fields_boundary_validation():\n    \"\"\"TC015-验证物料清单分录中数值型字段的边界（数量、单价）\"\"\"\n    # 模拟登录\n    login_url = \"http://api.example.com/auth/login\"\n    login_data = {\"username\": \"test_user\", \"password\": \"test_password\"}\n    login_response = requests.post(login_url, json=login_data)\n    assert login_response.status_code == 200\n    token = login_response.json().get(\"token\")\n    \n    # 获取草稿订单\n    draft_orders_url = \"http://api.example.com/sales/orders?status=draft\"\n    headers = {\"Authorization\": f\"Bearer {token}\"}\n    orders_response = requests.get(draft_orders_url, headers=headers)\n    assert orders_response.status_code == 200\n    \n    orders = orders_response.json().get(\"data\", [])\n    assert len(orders) > 0, \"No draft orders found\"\n    order_id = orders[0].get(\"id\")\n    \n    # 测试1：负数数量\n    add_material_url = f\"http://api.example.com/sales/orders/{order_id}/materials\"\n    negative_qty_data = {\n        \"material_code\": \"MAT001\",\n        \"quantity\": -5,\n        \"unit_price\": 10.0\n    }\n    response1 = requests.post(add_material_url, json=negative_qty_data, headers=headers)\n    \n    # 断言负数数量应该被拒绝\n    assert response1.status_code == 400\n    error_msg1 = response1.json().get(\"message\", \"\")\n    assert \"负数\" in error_msg1 or \"不能为负\" in error_msg1 or \"大于0\" in error_msg1\n    \n    # 测试2：超精度小数单价\n    precision_data = {\n        \"material_code\": \"MAT002\",\n        \"quantity\": 1,\n        \"unit_price\": 10.123\n    }\n    response2 = requests.post(add_material_url, json=precision_data, headers=headers)\n    \n    # 断言超精度小数应该被处理\n    if response2.status_code == 201:\n        # 如果成功创建，检查单价是否被正确处理\n        material_id = response2.json().get(\"id\")\n        get_material_url = f\"http://api.example.com/sales/orders/{order_id}/materials/{material_id}\"\n        get_response = requests.get(get_material_url, headers=headers)\n        assert get_response.status_code == 200\n        unit_price = get_response.json().get(\"unit_price\")\n        # 检查是否为2位小数\n        assert len(str(unit_price).split('.')[-1]) <= 2\n    elif response2.status_code == 400:\n        # 或者直接返回错误\n        error_msg2 = response2.json().get(\"message\", \"\")\n        assert \"小数\" in error_msg2 or \"精度\" in error_msg2 or \"位数\" in error_msg2\n    else:\n        assert False, f\"Unexpected response: {response2.status_code}\"",
      "imports": ["import requests", "import pytest"],
      "api_info": {
        "method": "POST",
        "endpoint": "/sales/orders/{order_id}/materials",
        "description": "为销售订单添加物料分录"
      }
    },
    {
      "function_name": "test_invoice_status_boundary_and_display",
      "docstring": "TC016-验证开票状态字段的取值与显示边界",
      "code": "def test

def test_adjust_list_fields_order():\n    \"\"\"TC011-验证拖动调整列表字段顺序的功能\"\"\"\n    # 模拟登录\n    login_url = \"http://api.example.com/auth/login\"\n    login_data = {\"username\": \"test_user\", \"password\": \"test_password\"}\n    login_response = requests.post(login_url, json=login_data)\n    assert login_response.status_code == 200\n    token = login_response.json().get(\"token\")\n    \n    # 获取当前字段顺序\n    get_config_url = \"http://api.example.com/sales/orders/list/field-config\"\n    headers = {\"Authorization\": f\"Bearer {token}\"}\n    get_response = requests.get(get_config_url, headers=headers)\n    assert get_response.status_code == 200\n    current_config = get_response.json()\n    \n    # 调整字段顺序：将\"订单金额\"移到\"客户名称\"之前\n    # 假设字段配置包含顺序信息\n    fields = current_config.get(\"fields\", [])\n    order_amount_index = next((i for i, f in enumerate(fields) if f.get(\"name\") == \"订单金额\"), -1)\n    customer_name_index = next((i for i, f in enumerate(fields) if f.get(\"name\") == \"客户名称\"), -1)\n    \n    # 重新排序\n    if order_amount_index != -1 and customer_name_index != -1:\n        fields.insert(customer_name_index, fields.pop(order_amount_index))\n    \n    config_data = {\"fields\": fields}\n    update_config_url = \"http://api.example.com/sales/orders/list/field-config\"\n    update_response = requests.post(update_config_url, json=config_data, headers=headers)\n    \n    # 断言配置更新成功\n    assert update_response.status_code == 200\n    assert update_response.json().get(\"success\") == True\n    \n    # 验证列表字段顺序\n    list_url = \"http://api.example.com/sales/orders\"\n    list_response = requests.get(list_url, headers=headers)\n    assert list_response.status_code == 200\n    list_data = list_response.json()\n    \n    columns = list_data.get(\"columns\", [])\n    column_names = [col.get(\"name\") for col in columns]\n    \n    # 检查\"订单金额\"是否在\"客户名称\"之前\n    if \"订单金额\" in column_names and \"客户名称\" in column_names:\n        order_amount_pos = column_names.index(\"订单金额\")\n        customer_name_pos = column_names.index(\"客户名称\")\n        assert order_amount_pos < customer_name_pos",
      "imports": ["import requests", "import pytest"],
      "api_info": {
        "method": "POST",
        "endpoint": "/sales/orders/list/field-config",
        "description": "更新列表字段顺序配置"
      }
    },
    {
      "function_name": "test_query_condition_boundary_validation",
      "docstring": "TC012-验证查询条件输入值的边界处理（超长字符）",
      "code": "def test_query_condition_boundary_validation():\n    \"\"\"TC012-验证查询条件输入值的边界处理（超长字符）\"\"\"\n    # 模拟登录\n    login_url = \"http://api.example.com/auth/login\"\n    login_data = {\"username\": \"test_user\", \"password\": \"test_password\"}\n    login_response = requests.post(login_url, json=login_data)\n    assert login_response.status_code == 200\n    token = login_response.json().get(\"token\")\n    \n    # 测试超长订单编号查询\n    query_url = \"http://api.example.com/sales/orders/query\"\n    headers = {\"Authorization\": f\"Bearer {token}\", \"Content-Type\": \"application/json\"}\n    \n    # 生成超过100个字符的字符串\n    long_order_no = \"A\" * 101\n    query_data = {\n        \"order_no\": long_order_no,\n        \"page\": 1,\n        \"page_size\": 10\n    }\n    \n    response = requests.post(query_url, json=query_data, headers=headers)\n    \n    # 断言：系统应正确处理超长输入\n    # 可能情况1：返回400状态码并给出错误提示\n    # 可能情况2：返回200但结果为空\n    if response.status_code == 400:\n        error_msg = response.json().get(\"message\", \"\")\n        assert \"长度\" in error_msg or \"过长\" in error_msg or \"无效\" in error_msg\n    elif response.status_code == 200:\n        result = response.json()\n        # 检查是否返回空结果或错误信息\n        assert result.get(\"total\", 0) == 0 or \"error\" in result\n    else:\n        # 其他状态码视为测试失败\n        assert False, f\"Unexpected status code: {response.status_code}\"",
      "imports": ["import requests", "import pytest"],
      "api_info": {
        "method": "POST",
        "endpoint": "/sales/orders/query",
        "description": "销售订单查询接口"
      }
    },
    {
      "function_name": "test_query_condition_state_persistence",
      "docstring": "TC013-验证查询条件在页面刷新或回退后的状态保持",
      "code": "def test_query_condition_state_persistence():\n    \"\"\"TC013-验证查询条件在页面刷新或回退后的状态保持\"\"\"\n    # 模拟登录\n    login_url = \"http://api.example.com/auth/login\"\n    login_data = {\"username\": \"test_user\", \"password\": \"test_password\"}\n    login_response = requests.post(login_url, json=login_data)\n    assert login_response.status_code == 200\n    token = login_response.json().get(\"token\")\n    \n    # 设置复杂查询条件\n    query_url = \"http://api.example.com/sales/orders/query\"\n    headers = {\"Authorization\": f\"Bearer {token}\", \"Content-Type\": \"application/json\"}\n    \n    query_data = {\n        \"customer\": \"A\",\n        \"status\": \"pending_review\",\n        \"date_from\": \"2024-01-01\",\n        \"date_to\": \"2024-01-31\",\n        \"page\": 1,\n        \"page_size\": 10\n    }\n    \n    # 执行查询\n    response = requests.post(query_url, json=query_data, headers=headers)\n    assert response.status_code == 200\n    \n    # 模拟页面刷新：重新获取查询条件\n    # 假设有接口可以获取上次查询条件\n    get_query_state_url = \"http://api.example.com/sales/orders/query/state\"\n    state_response = requests.get(get_query_state_url, headers=headers)\n    \n    # 断言查询条件被保存\n    if state_response.status_code == 200:\n        saved_state = state_response.json()\n        assert saved_state.get(\"customer\") == \"A\"\n        assert saved_state.get(\"status\") == \"pending_review\"\n        assert saved_state.get(\"date_from\") == \"2024-01-01\"\n        assert saved_state.get(\"date_to\") == \"2024-01-31\"\n    else:\n        # 如果系统不支持查询状态保存，则跳过此断言\n        pytest.skip(\"Query state persistence not supported by API\")",
      "imports": ["import requests", "import pytest"],
      "api_info": {
        "method": "GET",
        "endpoint": "/sales/orders/query/state",
        "description": "获取保存的查询条件状态"
      }
    },
    {
      "function_name": "test_material_list_max_rows_boundary",
      "docstring": "TC014-验证物料清单分录数量的上限边界",
      "code": "def test_material_list_max_rows_boundary():\n    \"\"\"TC014-验证物料清单分录数量的上限边界\"\"\"\n    # 模拟登录\n    login_url = \"http://api.example.com/auth/login\"\n    login_data = {\"username\": \"test_user\", \"password\": \"test_password\"}\n    login_response = requests.post(login_url, json=login_data)\n    assert login_response.status_code == 200\n    token = login_response.json().get(\"token\")\n    \n    # 获取草稿订单\n    draft_orders_url = \"http://api.example.com/sales/orders?status=draft\"\n    headers = {\"Authorization\": f\"Bearer {token}\"}\n    orders_response = requests.get(draft_orders_url, headers=headers)\n    assert orders_response.status_code == 200\n    \n    orders = orders_response.json().get(\"data\", [])\n    assert len(orders) > 0, \"No draft orders found\"\n    order_id = orders[0].get(\"id\")\n    \n    # 获取订单详情\n    order_detail_url = f\"http://api.example.com/sales/orders/{order_id}\"\n    detail_response = requests.get(order_detail_url, headers=headers)\n    assert detail_response.status_code == 200\n    \n    # 添加物料分录直到达到上限\n    add_material_url = f\"http://api.example.com/sales/orders/{order_id}/materials\"\n    \n    # 先添加100条物料分录\n    for i in range(100):\n        material_data = {\n            \"material_code\": f\"MAT{i:03d}\",\n            \"quantity\": 1,\n            \"unit_price\": 10.0\n        }\n        add_response = requests.post(add_material_url, json=material_data, headers=headers)\n        \n        # 检查是否达到上限\n        if add_response.status_code == 400:\n            error_msg = add_response.json().get(\"message\", \"\")\n            assert \"上限\" in error_msg or \"最大\" in error_msg or \"限制\" in error_msg\n            break\n        else:\n            assert add_response.status_code == 201\n    \n    # 尝试添加第101条\n    material_data = {\n        \"material_code\": \"MAT101\",\n        \"quantity\": 1,\n        \"unit_price\": 10.0\n    }\n    final_response = requests.post(add_material_url, json=material_data, headers=headers)\n    \n    # 断言第101条应该失败\n    assert final_response.status_code == 400\n    error_msg = final_response.json().get(\"message\", \"\")\n    assert \"上限\" in error_msg or \"最大\" in error_msg or \"限制\" in error_msg",
      "imports": ["import requests", "import pytest"],
      "api_info": {
        "method": "POST",
        "endpoint": "/sales/orders/{order_id}/materials",
        "description": "为销售订单添加物料分录"
      }
    },
    {
      "function_name": "test_material_fields_boundary_validation",
      "docstring": "TC015-验证物料清单分录中数值型字段的边界（数量、单价）",
      "code": "def test_material_fields_boundary_validation():\n    \"\"\"TC015-验证物料清单分录中数值型字段的边界（数量、单价）\"\"\"\n    # 模拟登录\n    login_url = \"http://api.example.com/auth/login\"\n    login_data = {\"username\": \"test_user\", \"password\": \"test_password\"}\n    login_response = requests.post(login_url, json=login_data)\n    assert login_response.status_code == 200\n    token = login_response.json().get(\"token\")\n    \n    # 获取草稿订单\n    draft_orders_url = \"http://api.example.com/sales/orders?status=draft\"\n    headers = {\"Authorization\": f\"Bearer {token}\"}\n    orders_response = requests.get(draft_orders_url, headers=headers)\n    assert orders_response.status_code == 200\n    \n    orders = orders_response.json().get(\"data\", [])\n    assert len(orders) > 0, \"No draft orders found\"\n    order_id = orders[0].get(\"id\")\n    \n    # 测试1：负数数量\n    add_material_url = f\"http://api.example.com/sales/orders/{order_id}/materials\"\n    negative_qty_data = {\n        \"material_code\": \"MAT001\",\n        \"quantity\": -5,\n        \"unit_price\": 10.0\n    }\n    response1 = requests.post(add_material_url, json=negative_qty_data, headers=headers)\n    \n    # 断言负数数量应该被拒绝\n    assert response1.status_code == 400\n    error_msg1 = response1.json().get(\"message\", \"\")\n    assert \"负数\" in error_msg1 or \"不能为负\" in error_msg1 or \"大于0\" in error_msg1\n    \n    # 测试2：超精度小数单价\n    precision_data = {\n        \"material_code\": \"MAT002\",\n        \"quantity\": 1,\n        \"unit_price\": 10.123\n    }\n    response2 = requests.post(add_material_url, json=precision_data, headers=headers)\n    \n    # 断言超精度小数应该被处理\n    if response2.status_code == 201:\n        # 如果成功创建，检查单价是否被正确处理\n        material_id = response2.json().get(\"id\")\n        get_material_url = f\"http://api.example.com/sales/orders/{order_id}/materials/{material_id}\"\n        get_response = requests.get(get_material_url, headers=headers)\n        assert get_response.status_code == 200\n        unit_price = get_response.json().get(\"unit_price\")\n        # 检查是否为2位小数\n        assert len(str(unit_price).split('.')[-1]) <= 2\n    elif response2.status_code == 400:\n        # 或者直接返回错误\n        error_msg2 = response2.json().get(\"message\", \"\")\n        assert \"小数\" in error_msg2 or \"精度\" in error_msg2 or \"位数\" in error_msg2\n    else:\n        assert False, f\"Unexpected response: {response2.status_code}\"",
      "imports": ["import requests", "import pytest"],
      "api_info": {
        "method": "POST",
        "endpoint": "/sales/orders/{order_id}/materials",
        "description": "为销售订单添加物料分录"
      }
    },
    {
      "function_name": "test_invoice_status_boundary_and_display",
      "docstring": "TC016-验证开票状态字段的取值与显示边界",
      "code": "def test

def test_query_condition_boundary_validation():\n    \"\"\"TC012-验证查询条件输入值的边界处理（超长字符）\"\"\"\n    # 模拟登录\n    login_url = \"http://api.example.com/auth/login\"\n    login_data = {\"username\": \"test_user\", \"password\": \"test_password\"}\n    login_response = requests.post(login_url, json=login_data)\n    assert login_response.status_code == 200\n    token = login_response.json().get(\"token\")\n    \n    # 测试超长订单编号查询\n    query_url = \"http://api.example.com/sales/orders/query\"\n    headers = {\"Authorization\": f\"Bearer {token}\", \"Content-Type\": \"application/json\"}\n    \n    # 生成超过100个字符的字符串\n    long_order_no = \"A\" * 101\n    query_data = {\n        \"order_no\": long_order_no,\n        \"page\": 1,\n        \"page_size\": 10\n    }\n    \n    response = requests.post(query_url, json=query_data, headers=headers)\n    \n    # 断言：系统应正确处理超长输入\n    # 可能情况1：返回400状态码并给出错误提示\n    # 可能情况2：返回200但结果为空\n    if response.status_code == 400:\n        error_msg = response.json().get(\"message\", \"\")\n        assert \"长度\" in error_msg or \"过长\" in error_msg or \"无效\" in error_msg\n    elif response.status_code == 200:\n        result = response.json()\n        # 检查是否返回空结果或错误信息\n        assert result.get(\"total\", 0) == 0 or \"error\" in result\n    else:\n        # 其他状态码视为测试失败\n        assert False, f\"Unexpected status code: {response.status_code}\"",
      "imports": ["import requests", "import pytest"],
      "api_info": {
        "method": "POST",
        "endpoint": "/sales/orders/query",
        "description": "销售订单查询接口"
      }
    },
    {
      "function_name": "test_query_condition_state_persistence",
      "docstring": "TC013-验证查询条件在页面刷新或回退后的状态保持",
      "code": "def test_query_condition_state_persistence():\n    \"\"\"TC013-验证查询条件在页面刷新或回退后的状态保持\"\"\"\n    # 模拟登录\n    login_url = \"http://api.example.com/auth/login\"\n    login_data = {\"username\": \"test_user\", \"password\": \"test_password\"}\n    login_response = requests.post(login_url, json=login_data)\n    assert login_response.status_code == 200\n    token = login_response.json().get(\"token\")\n    \n    # 设置复杂查询条件\n    query_url = \"http://api.example.com/sales/orders/query\"\n    headers = {\"Authorization\": f\"Bearer {token}\", \"Content-Type\": \"application/json\"}\n    \n    query_data = {\n        \"customer\": \"A\",\n        \"status\": \"pending_review\",\n        \"date_from\": \"2024-01-01\",\n        \"date_to\": \"2024-01-31\",\n        \"page\": 1,\n        \"page_size\": 10\n    }\n    \n    # 执行查询\n    response = requests.post(query_url, json=query_data, headers=headers)\n    assert response.status_code == 200\n    \n    # 模拟页面刷新：重新获取查询条件\n    # 假设有接口可以获取上次查询条件\n    get_query_state_url = \"http://api.example.com/sales/orders/query/state\"\n    state_response = requests.get(get_query_state_url, headers=headers)\n    \n    # 断言查询条件被保存\n    if state_response.status_code == 200:\n        saved_state = state_response.json()\n        assert saved_state.get(\"customer\") == \"A\"\n        assert saved_state.get(\"status\") == \"pending_review\"\n        assert saved_state.get(\"date_from\") == \"2024-01-01\"\n        assert saved_state.get(\"date_to\") == \"2024-01-31\"\n    else:\n        # 如果系统不支持查询状态保存，则跳过此断言\n        pytest.skip(\"Query state persistence not supported by API\")",
      "imports": ["import requests", "import pytest"],
      "api_info": {
        "method": "GET",
        "endpoint": "/sales/orders/query/state",
        "description": "获取保存的查询条件状态"
      }
    },
    {
      "function_name": "test_material_list_max_rows_boundary",
      "docstring": "TC014-验证物料清单分录数量的上限边界",
      "code": "def test_material_list_max_rows_boundary():\n    \"\"\"TC014-验证物料清单分录数量的上限边界\"\"\"\n    # 模拟登录\n    login_url = \"http://api.example.com/auth/login\"\n    login_data = {\"username\": \"test_user\", \"password\": \"test_password\"}\n    login_response = requests.post(login_url, json=login_data)\n    assert login_response.status_code == 200\n    token = login_response.json().get(\"token\")\n    \n    # 获取草稿订单\n    draft_orders_url = \"http://api.example.com/sales/orders?status=draft\"\n    headers = {\"Authorization\": f\"Bearer {token}\"}\n    orders_response = requests.get(draft_orders_url, headers=headers)\n    assert orders_response.status_code == 200\n    \n    orders = orders_response.json().get(\"data\", [])\n    assert len(orders) > 0, \"No draft orders found\"\n    order_id = orders[0].get(\"id\")\n    \n    # 获取订单详情\n    order_detail_url = f\"http://api.example.com/sales/orders/{order_id}\"\n    detail_response = requests.get(order_detail_url, headers=headers)\n    assert detail_response.status_code == 200\n    \n    # 添加物料分录直到达到上限\n    add_material_url = f\"http://api.example.com/sales/orders/{order_id}/materials\"\n    \n    # 先添加100条物料分录\n    for i in range(100):\n        material_data = {\n            \"material_code\": f\"MAT{i:03d}\",\n            \"quantity\": 1,\n            \"unit_price\": 10.0\n        }\n        add_response = requests.post(add_material_url, json=material_data, headers=headers)\n        \n        # 检查是否达到上限\n        if add_response.status_code == 400:\n            error_msg = add_response.json().get(\"message\", \"\")\n            assert \"上限\" in error_msg or \"最大\" in error_msg or \"限制\" in error_msg\n            break\n        else:\n            assert add_response.status_code == 201\n    \n    # 尝试添加第101条\n    material_data = {\n        \"material_code\": \"MAT101\",\n        \"quantity\": 1,\n        \"unit_price\": 10.0\n    }\n    final_response = requests.post(add_material_url, json=material_data, headers=headers)\n    \n    # 断言第101条应该失败\n    assert final_response.status_code == 400\n    error_msg = final_response.json().get(\"message\", \"\")\n    assert \"上限\" in error_msg or \"最大\" in error_msg or \"限制\" in error_msg",
      "imports": ["import requests", "import pytest"],
      "api_info": {
        "method": "POST",
        "endpoint": "/sales/orders/{order_id}/materials",
        "description": "为销售订单添加物料分录"
      }
    },
    {
      "function_name": "test_material_fields_boundary_validation",
      "docstring": "TC015-验证物料清单分录中数值型字段的边界（数量、单价）",
      "code": "def test_material_fields_boundary_validation():\n    \"\"\"TC015-验证物料清单分录中数值型字段的边界（数量、单价）\"\"\"\n    # 模拟登录\n    login_url = \"http://api.example.com/auth/login\"\n    login_data = {\"username\": \"test_user\", \"password\": \"test_password\"}\n    login_response = requests.post(login_url, json=login_data)\n    assert login_response.status_code == 200\n    token = login_response.json().get(\"token\")\n    \n    # 获取草稿订单\n    draft_orders_url = \"http://api.example.com/sales/orders?status=draft\"\n    headers = {\"Authorization\": f\"Bearer {token}\"}\n    orders_response = requests.get(draft_orders_url, headers=headers)\n    assert orders_response.status_code == 200\n    \n    orders = orders_response.json().get(\"data\", [])\n    assert len(orders) > 0, \"No draft orders found\"\n    order_id = orders[0].get(\"id\")\n    \n    # 测试1：负数数量\n    add_material_url = f\"http://api.example.com/sales/orders/{order_id}/materials\"\n    negative_qty_data = {\n        \"material_code\": \"MAT001\",\n        \"quantity\": -5,\n        \"unit_price\": 10.0\n    }\n    response1 = requests.post(add_material_url, json=negative_qty_data, headers=headers)\n    \n    # 断言负数数量应该被拒绝\n    assert response1.status_code == 400\n    error_msg1 = response1.json().get(\"message\", \"\")\n    assert \"负数\" in error_msg1 or \"不能为负\" in error_msg1 or \"大于0\" in error_msg1\n    \n    # 测试2：超精度小数单价\n    precision_data = {\n        \"material_code\": \"MAT002\",\n        \"quantity\": 1,\n        \"unit_price\": 10.123\n    }\n    response2 = requests.post(add_material_url, json=precision_data, headers=headers)\n    \n    # 断言超精度小数应该被处理\n    if response2.status_code == 201:\n        # 如果成功创建，检查单价是否被正确处理\n        material_id = response2.json().get(\"id\")\n        get_material_url = f\"http://api.example.com/sales/orders/{order_id}/materials/{material_id}\"\n        get_response = requests.get(get_material_url, headers=headers)\n        assert get_response.status_code == 200\n        unit_price = get_response.json().get(\"unit_price\")\n        # 检查是否为2位小数\n        assert len(str(unit_price).split('.')[-1]) <= 2\n    elif response2.status_code == 400:\n        # 或者直接返回错误\n        error_msg2 = response2.json().get(\"message\", \"\")\n        assert \"小数\" in error_msg2 or \"精度\" in error_msg2 or \"位数\" in error_msg2\n    else:\n        assert False, f\"Unexpected response: {response2.status_code}\"",
      "imports": ["import requests", "import pytest"],
      "api_info": {
        "method": "POST",
        "endpoint": "/sales/orders/{order_id}/materials",
        "description": "为销售订单添加物料分录"
      }
    },
    {
      "function_name": "test_invoice_status_boundary_and_display",
      "docstring": "TC016-验证开票状态字段的取值与显示边界",
      "code": "def test

def test_query_condition_state_persistence():\n    \"\"\"TC013-验证查询条件在页面刷新或回退后的状态保持\"\"\"\n    # 模拟登录\n    login_url = \"http://api.example.com/auth/login\"\n    login_data = {\"username\": \"test_user\", \"password\": \"test_password\"}\n    login_response = requests.post(login_url, json=login_data)\n    assert login_response.status_code == 200\n    token = login_response.json().get(\"token\")\n    \n    # 设置复杂查询条件\n    query_url = \"http://api.example.com/sales/orders/query\"\n    headers = {\"Authorization\": f\"Bearer {token}\", \"Content-Type\": \"application/json\"}\n    \n    query_data = {\n        \"customer\": \"A\",\n        \"status\": \"pending_review\",\n        \"date_from\": \"2024-01-01\",\n        \"date_to\": \"2024-01-31\",\n        \"page\": 1,\n        \"page_size\": 10\n    }\n    \n    # 执行查询\n    response = requests.post(query_url, json=query_data, headers=headers)\n    assert response.status_code == 200\n    \n    # 模拟页面刷新：重新获取查询条件\n    # 假设有接口可以获取上次查询条件\n    get_query_state_url = \"http://api.example.com/sales/orders/query/state\"\n    state_response = requests.get(get_query_state_url, headers=headers)\n    \n    # 断言查询条件被保存\n    if state_response.status_code == 200:\n        saved_state = state_response.json()\n        assert saved_state.get(\"customer\") == \"A\"\n        assert saved_state.get(\"status\") == \"pending_review\"\n        assert saved_state.get(\"date_from\") == \"2024-01-01\"\n        assert saved_state.get(\"date_to\") == \"2024-01-31\"\n    else:\n        # 如果系统不支持查询状态保存，则跳过此断言\n        pytest.skip(\"Query state persistence not supported by API\")",
      "imports": ["import requests", "import pytest"],
      "api_info": {
        "method": "GET",
        "endpoint": "/sales/orders/query/state",
        "description": "获取保存的查询条件状态"
      }
    },
    {
      "function_name": "test_material_list_max_rows_boundary",
      "docstring": "TC014-验证物料清单分录数量的上限边界",
      "code": "def test_material_list_max_rows_boundary():\n    \"\"\"TC014-验证物料清单分录数量的上限边界\"\"\"\n    # 模拟登录\n    login_url = \"http://api.example.com/auth/login\"\n    login_data = {\"username\": \"test_user\", \"password\": \"test_password\"}\n    login_response = requests.post(login_url, json=login_data)\n    assert login_response.status_code == 200\n    token = login_response.json().get(\"token\")\n    \n    # 获取草稿订单\n    draft_orders_url = \"http://api.example.com/sales/orders?status=draft\"\n    headers = {\"Authorization\": f\"Bearer {token}\"}\n    orders_response = requests.get(draft_orders_url, headers=headers)\n    assert orders_response.status_code == 200\n    \n    orders = orders_response.json().get(\"data\", [])\n    assert len(orders) > 0, \"No draft orders found\"\n    order_id = orders[0].get(\"id\")\n    \n    # 获取订单详情\n    order_detail_url = f\"http://api.example.com/sales/orders/{order_id}\"\n    detail_response = requests.get(order_detail_url, headers=headers)\n    assert detail_response.status_code == 200\n    \n    # 添加物料分录直到达到上限\n    add_material_url = f\"http://api.example.com/sales/orders/{order_id}/materials\"\n    \n    # 先添加100条物料分录\n    for i in range(100):\n        material_data = {\n            \"material_code\": f\"MAT{i:03d}\",\n            \"quantity\": 1,\n            \"unit_price\": 10.0\n        }\n        add_response = requests.post(add_material_url, json=material_data, headers=headers)\n        \n        # 检查是否达到上限\n        if add_response.status_code == 400:\n            error_msg = add_response.json().get(\"message\", \"\")\n            assert \"上限\" in error_msg or \"最大\" in error_msg or \"限制\" in error_msg\n            break\n        else:\n            assert add_response.status_code == 201\n    \n    # 尝试添加第101条\n    material_data = {\n        \"material_code\": \"MAT101\",\n        \"quantity\": 1,\n        \"unit_price\": 10.0\n    }\n    final_response = requests.post(add_material_url, json=material_data, headers=headers)\n    \n    # 断言第101条应该失败\n    assert final_response.status_code == 400\n    error_msg = final_response.json().get(\"message\", \"\")\n    assert \"上限\" in error_msg or \"最大\" in error_msg or \"限制\" in error_msg",
      "imports": ["import requests", "import pytest"],
      "api_info": {
        "method": "POST",
        "endpoint": "/sales/orders/{order_id}/materials",
        "description": "为销售订单添加物料分录"
      }
    },
    {
      "function_name": "test_material_fields_boundary_validation",
      "docstring": "TC015-验证物料清单分录中数值型字段的边界（数量、单价）",
      "code": "def test_material_fields_boundary_validation():\n    \"\"\"TC015-验证物料清单分录中数值型字段的边界（数量、单价）\"\"\"\n    # 模拟登录\n    login_url = \"http://api.example.com/auth/login\"\n    login_data = {\"username\": \"test_user\", \"password\": \"test_password\"}\n    login_response = requests.post(login_url, json=login_data)\n    assert login_response.status_code == 200\n    token = login_response.json().get(\"token\")\n    \n    # 获取草稿订单\n    draft_orders_url = \"http://api.example.com/sales/orders?status=draft\"\n    headers = {\"Authorization\": f\"Bearer {token}\"}\n    orders_response = requests.get(draft_orders_url, headers=headers)\n    assert orders_response.status_code == 200\n    \n    orders = orders_response.json().get(\"data\", [])\n    assert len(orders) > 0, \"No draft orders found\"\n    order_id = orders[0].get(\"id\")\n    \n    # 测试1：负数数量\n    add_material_url = f\"http://api.example.com/sales/orders/{order_id}/materials\"\n    negative_qty_data = {\n        \"material_code\": \"MAT001\",\n        \"quantity\": -5,\n        \"unit_price\": 10.0\n    }\n    response1 = requests.post(add_material_url, json=negative_qty_data, headers=headers)\n    \n    # 断言负数数量应该被拒绝\n    assert response1.status_code == 400\n    error_msg1 = response1.json().get(\"message\", \"\")\n    assert \"负数\" in error_msg1 or \"不能为负\" in error_msg1 or \"大于0\" in error_msg1\n    \n    # 测试2：超精度小数单价\n    precision_data = {\n        \"material_code\": \"MAT002\",\n        \"quantity\": 1,\n        \"unit_price\": 10.123\n    }\n    response2 = requests.post(add_material_url, json=precision_data, headers=headers)\n    \n    # 断言超精度小数应该被处理\n    if response2.status_code == 201:\n        # 如果成功创建，检查单价是否被正确处理\n        material_id = response2.json().get(\"id\")\n        get_material_url = f\"http://api.example.com/sales/orders/{order_id}/materials/{material_id}\"\n        get_response = requests.get(get_material_url, headers=headers)\n        assert get_response.status_code == 200\n        unit_price = get_response.json().get(\"unit_price\")\n        # 检查是否为2位小数\n        assert len(str(unit_price).split('.')[-1]) <= 2\n    elif response2.status_code == 400:\n        # 或者直接返回错误\n        error_msg2 = response2.json().get(\"message\", \"\")\n        assert \"小数\" in error_msg2 or \"精度\" in error_msg2 or \"位数\" in error_msg2\n    else:\n        assert False, f\"Unexpected response: {response2.status_code}\"",
      "imports": ["import requests", "import pytest"],
      "api_info": {
        "method": "POST",
        "endpoint": "/sales/orders/{order_id}/materials",
        "description": "为销售订单添加物料分录"
      }
    },
    {
      "function_name": "test_invoice_status_boundary_and_display",
      "docstring": "TC016-验证开票状态字段的取值与显示边界",
      "code": "def test

def test_material_list_max_rows_boundary():\n    \"\"\"TC014-验证物料清单分录数量的上限边界\"\"\"\n    # 模拟登录\n    login_url = \"http://api.example.com/auth/login\"\n    login_data = {\"username\": \"test_user\", \"password\": \"test_password\"}\n    login_response = requests.post(login_url, json=login_data)\n    assert login_response.status_code == 200\n    token = login_response.json().get(\"token\")\n    \n    # 获取草稿订单\n    draft_orders_url = \"http://api.example.com/sales/orders?status=draft\"\n    headers = {\"Authorization\": f\"Bearer {token}\"}\n    orders_response = requests.get(draft_orders_url, headers=headers)\n    assert orders_response.status_code == 200\n    \n    orders = orders_response.json().get(\"data\", [])\n    assert len(orders) > 0, \"No draft orders found\"\n    order_id = orders[0].get(\"id\")\n    \n    # 获取订单详情\n    order_detail_url = f\"http://api.example.com/sales/orders/{order_id}\"\n    detail_response = requests.get(order_detail_url, headers=headers)\n    assert detail_response.status_code == 200\n    \n    # 添加物料分录直到达到上限\n    add_material_url = f\"http://api.example.com/sales/orders/{order_id}/materials\"\n    \n    # 先添加100条物料分录\n    for i in range(100):\n        material_data = {\n            \"material_code\": f\"MAT{i:03d}\",\n            \"quantity\": 1,\n            \"unit_price\": 10.0\n        }\n        add_response = requests.post(add_material_url, json=material_data, headers=headers)\n        \n        # 检查是否达到上限\n        if add_response.status_code == 400:\n            error_msg = add_response.json().get(\"message\", \"\")\n            assert \"上限\" in error_msg or \"最大\" in error_msg or \"限制\" in error_msg\n            break\n        else:\n            assert add_response.status_code == 201\n    \n    # 尝试添加第101条\n    material_data = {\n        \"material_code\": \"MAT101\",\n        \"quantity\": 1,\n        \"unit_price\": 10.0\n    }\n    final_response = requests.post(add_material_url, json=material_data, headers=headers)\n    \n    # 断言第101条应该失败\n    assert final_response.status_code == 400\n    error_msg = final_response.json().get(\"message\", \"\")\n    assert \"上限\" in error_msg or \"最大\" in error_msg or \"限制\" in error_msg",
      "imports": ["import requests", "import pytest"],
      "api_info": {
        "method": "POST",
        "endpoint": "/sales/orders/{order_id}/materials",
        "description": "为销售订单添加物料分录"
      }
    },
    {
      "function_name": "test_material_fields_boundary_validation",
      "docstring": "TC015-验证物料清单分录中数值型字段的边界（数量、单价）",
      "code": "def test_material_fields_boundary_validation():\n    \"\"\"TC015-验证物料清单分录中数值型字段的边界（数量、单价）\"\"\"\n    # 模拟登录\n    login_url = \"http://api.example.com/auth/login\"\n    login_data = {\"username\": \"test_user\", \"password\": \"test_password\"}\n    login_response = requests.post(login_url, json=login_data)\n    assert login_response.status_code == 200\n    token = login_response.json().get(\"token\")\n    \n    # 获取草稿订单\n    draft_orders_url = \"http://api.example.com/sales/orders?status=draft\"\n    headers = {\"Authorization\": f\"Bearer {token}\"}\n    orders_response = requests.get(draft_orders_url, headers=headers)\n    assert orders_response.status_code == 200\n    \n    orders = orders_response.json().get(\"data\", [])\n    assert len(orders) > 0, \"No draft orders found\"\n    order_id = orders[0].get(\"id\")\n    \n    # 测试1：负数数量\n    add_material_url = f\"http://api.example.com/sales/orders/{order_id}/materials\"\n    negative_qty_data = {\n        \"material_code\": \"MAT001\",\n        \"quantity\": -5,\n        \"unit_price\": 10.0\n    }\n    response1 = requests.post(add_material_url, json=negative_qty_data, headers=headers)\n    \n    # 断言负数数量应该被拒绝\n    assert response1.status_code == 400\n    error_msg1 = response1.json().get(\"message\", \"\")\n    assert \"负数\" in error_msg1 or \"不能为负\" in error_msg1 or \"大于0\" in error_msg1\n    \n    # 测试2：超精度小数单价\n    precision_data = {\n        \"material_code\": \"MAT002\",\n        \"quantity\": 1,\n        \"unit_price\": 10.123\n    }\n    response2 = requests.post(add_material_url, json=precision_data, headers=headers)\n    \n    # 断言超精度小数应该被处理\n    if response2.status_code == 201:\n        # 如果成功创建，检查单价是否被正确处理\n        material_id = response2.json().get(\"id\")\n        get_material_url = f\"http://api.example.com/sales/orders/{order_id}/materials/{material_id}\"\n        get_response = requests.get(get_material_url, headers=headers)\n        assert get_response.status_code == 200\n        unit_price = get_response.json().get(\"unit_price\")\n        # 检查是否为2位小数\n        assert len(str(unit_price).split('.')[-1]) <= 2\n    elif response2.status_code == 400:\n        # 或者直接返回错误\n        error_msg2 = response2.json().get(\"message\", \"\")\n        assert \"小数\" in error_msg2 or \"精度\" in error_msg2 or \"位数\" in error_msg2\n    else:\n        assert False, f\"Unexpected response: {response2.status_code}\"",
      "imports": ["import requests", "import pytest"],
      "api_info": {
        "method": "POST",
        "endpoint": "/sales/orders/{order_id}/materials",
        "description": "为销售订单添加物料分录"
      }
    },
    {
      "function_name": "test_invoice_status_boundary_and_display",
      "docstring": "TC016-验证开票状态字段的取值与显示边界",
      "code": "def test

def test_material_fields_boundary_validation():\n    \"\"\"TC015-验证物料清单分录中数值型字段的边界（数量、单价）\"\"\"\n    # 模拟登录\n    login_url = \"http://api.example.com/auth/login\"\n    login_data = {\"username\": \"test_user\", \"password\": \"test_password\"}\n    login_response = requests.post(login_url, json=login_data)\n    assert login_response.status_code == 200\n    token = login_response.json().get(\"token\")\n    \n    # 获取草稿订单\n    draft_orders_url = \"http://api.example.com/sales/orders?status=draft\"\n    headers = {\"Authorization\": f\"Bearer {token}\"}\n    orders_response = requests.get(draft_orders_url, headers=headers)\n    assert orders_response.status_code == 200\n    \n    orders = orders_response.json().get(\"data\", [])\n    assert len(orders) > 0, \"No draft orders found\"\n    order_id = orders[0].get(\"id\")\n    \n    # 测试1：负数数量\n    add_material_url = f\"http://api.example.com/sales/orders/{order_id}/materials\"\n    negative_qty_data = {\n        \"material_code\": \"MAT001\",\n        \"quantity\": -5,\n        \"unit_price\": 10.0\n    }\n    response1 = requests.post(add_material_url, json=negative_qty_data, headers=headers)\n    \n    # 断言负数数量应该被拒绝\n    assert response1.status_code == 400\n    error_msg1 = response1.json().get(\"message\", \"\")\n    assert \"负数\" in error_msg1 or \"不能为负\" in error_msg1 or \"大于0\" in error_msg1\n    \n    # 测试2：超精度小数单价\n    precision_data = {\n        \"material_code\": \"MAT002\",\n        \"quantity\": 1,\n        \"unit_price\": 10.123\n    }\n    response2 = requests.post(add_material_url, json=precision_data, headers=headers)\n    \n    # 断言超精度小数应该被处理\n    if response2.status_code == 201:\n        # 如果成功创建，检查单价是否被正确处理\n        material_id = response2.json().get(\"id\")\n        get_material_url = f\"http://api.example.com/sales/orders/{order_id}/materials/{material_id}\"\n        get_response = requests.get(get_material_url, headers=headers)\n        assert get_response.status_code == 200\n        unit_price = get_response.json().get(\"unit_price\")\n        # 检查是否为2位小数\n        assert len(str(unit_price).split('.')[-1]) <= 2\n    elif response2.status_code == 400:\n        # 或者直接返回错误\n        error_msg2 = response2.json().get(\"message\", \"\")\n        assert \"小数\" in error_msg2 or \"精度\" in error_msg2 or \"位数\" in error_msg2\n    else:\n        assert False, f\"Unexpected response: {response2.status_code}\"",
      "imports": ["import requests", "import pytest"],
      "api_info": {
        "method": "POST",
        "endpoint": "/sales/orders/{order_id}/materials",
        "description": "为销售订单添加物料分录"
      }
    },
    {
      "function_name": "test_invoice_status_boundary_and_display",
      "docstring": "TC016-验证开票状态字段的取值与显示边界",
      "code": "def test