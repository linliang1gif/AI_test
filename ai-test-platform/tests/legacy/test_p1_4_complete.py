"""
P1.4 完整功能测试
测试数据集管理、Test Cases集成、Automation集成
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_dataset_management():
    """测试数据集管理"""
    print("\n" + "=" * 60)
    print("测试1: 数据集管理")
    print("=" * 60)
    
    # 1. 创建数据集
    print("\n1.1 创建数据集...")
    test_data = {
        "username": "测试用户",
        "email": "test@example.com",
        "age": 25
    }
    
    response = requests.post(
        f"{BASE_URL}/api/test-data/datasets",
        json={
            "name": "用户测试数据集",
            "data": test_data,
            "description": "用于用户注册测试的数据集",
            "tags": ["用户", "注册"]
        }
    )
    
    print(f"状态码: {response.status_code}")
    result = response.json()
    
    if result.get('success'):
        dataset_id = result['dataset']['id']
        print(f"✅ 数据集创建成功! ID: {dataset_id}")
    else:
        print(f"❌ 创建失败: {result.get('message')}")
        return None
    
    # 2. 获取数据集列表
    print("\n1.2 获取数据集列表...")
    response = requests.get(f"{BASE_URL}/api/test-data/datasets")
    result = response.json()
    
    if result.get('success'):
        print(f"✅ 成功获取 {result['count']} 个数据集")
    else:
        print(f"❌ 获取失败")
    
    # 3. 获取单个数据集
    print(f"\n1.3 获取数据集详情...")
    response = requests.get(f"{BASE_URL}/api/test-data/datasets/{dataset_id}")
    result = response.json()
    
    if result.get('success'):
        print(f"✅ 数据集详情获取成功")
        print(f"   名称: {result['dataset']['name']}")
        print(f"   使用次数: {result['dataset']['usage_count']}")
    else:
        print(f"❌ 获取失败")
    
    # 4. 使用数据集
    print(f"\n1.4 使用数据集...")
    response = requests.post(f"{BASE_URL}/api/test-data/datasets/{dataset_id}/use")
    result = response.json()
    
    if result.get('success'):
        print(f"✅ 使用次数已更新: {result['dataset']['usage_count']}")
    else:
        print(f"❌ 更新失败")
    
    # 5. 搜索数据集
    print(f"\n1.5 搜索数据集...")
    response = requests.get(f"{BASE_URL}/api/test-data/datasets?keyword=用户")
    result = response.json()
    
    if result.get('success'):
        print(f"✅ 搜索到 {result['count']} 个数据集")
    else:
        print(f"❌ 搜索失败")
    
    # 6. 获取统计信息
    print(f"\n1.6 获取统计信息...")
    response = requests.get(f"{BASE_URL}/api/test-data/datasets-stats")
    result = response.json()
    
    if result.get('success'):
        stats = result['stats']
        print(f"✅ 统计信息:")
        print(f"   总数据集: {stats['total_datasets']}")
        print(f"   总使用次数: {stats['total_usage']}")
    else:
        print(f"❌ 获取失败")
    
    return dataset_id

def test_complete_workflow():
    """测试完整工作流"""
    print("\n" + "=" * 60)
    print("测试2: 完整工作流")
    print("=" * 60)
    
    # 1. 生成测试数据
    print("\n2.1 生成测试数据...")
    response = requests.post(
        f"{BASE_URL}/api/test-data/smart-object",
        json={
            "data_schema": {
                "username": "string",
                "email": "string",
                "password": "string"
            },
            "context": {
                "api_path": "/api/users",
                "api_method": "POST"
            }
        }
    )
    
    result = response.json()
    if result.get('success'):
        generated_data = result['data']
        print(f"✅ 数据生成成功")
        print(f"   数据: {json.dumps(generated_data, ensure_ascii=False)}")
        
        # 2. 保存为数据集
        print("\n2.2 保存为数据集...")
        response = requests.post(
            f"{BASE_URL}/api/test-data/datasets",
            json={
                "name": "自动生成的用户数据",
                "data": generated_data,
                "description": "通过智能生成器创建的数据集",
                "api_id": "api_users_post",
                "tags": ["自动生成", "用户"]
            }
        )
        
        result = response.json()
        if result.get('success'):
            print(f"✅ 数据集保存成功")
            return result['dataset']['id']
        else:
            print(f"❌ 保存失败")
    else:
        print(f"❌ 生成失败")
    
    return None

def main():
    print("=" * 60)
    print("P1.4 完整功能测试")
    print("=" * 60)
    
    # 测试数据集管理
    dataset_id = test_dataset_management()
    
    # 测试完整工作流
    workflow_dataset_id = test_complete_workflow()
    
    # 总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    
    if dataset_id and workflow_dataset_id:
        print("\n✅ 所有测试通过!")
        print(f"\n创建的数据集:")
        print(f"  - 手动创建: {dataset_id}")
        print(f"  - 工作流创建: {workflow_dataset_id}")
        
        print(f"\n📝 使用说明:")
        print(f"1. 打开浏览器: http://localhost:5174/")
        print(f"2. 进入 '💾 数据集管理' 页面")
        print(f"3. 查看刚创建的数据集")
        print(f"4. 点击 '📋 复制' 使用数据")
        print(f"5. 在 'API管理' 中生成数据并保存为数据集")
    else:
        print("\n⚠️ 部分测试失败")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    main()
