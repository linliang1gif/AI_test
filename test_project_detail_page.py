"""测试项目详情页是否可以正常访问"""
import requests

def test_project_detail():
    """测试项目详情页相关的API"""
    base_url = "http://localhost:8000"
    
    print("=" * 60)
    print("测试项目详情页 API")
    print("=" * 60)
    
    # 1. 获取项目列表
    print("\n1. 获取项目列表...")
    try:
        response = requests.get(f"{base_url}/api/v2/projects")
        print(f"   状态码: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            projects = data.get('projects', [])
            print(f"   项目数量: {len(projects)}")
            if projects:
                project_id = projects[0]['id']
                print(f"   第一个项目ID: {project_id}")
                print(f"   第一个项目名称: {projects[0]['name']}")
                
                # 2. 获取项目详情
                print(f"\n2. 获取项目详情 (ID: {project_id})...")
                response = requests.get(f"{base_url}/api/v2/projects/{project_id}")
                print(f"   状态码: {response.status_code}")
                if response.status_code == 200:
                    project = response.json()
                    print(f"   项目名称: {project.get('name', 'N/A')}")
                    print(f"   ✅ 项目详情 API 正常")
                else:
                    print(f"   ❌ 项目详情 API 失败: {response.text}")
                
                # 3. 获取项目环境列表
                print(f"\n3. 获取项目环境列表 (项目ID: {project_id})...")
                response = requests.get(f"{base_url}/api/v2/projects/{project_id}/environments")
                print(f"   状态码: {response.status_code}")
                if response.status_code == 200:
                    environments = response.json()  # 后端直接返回数组
                    print(f"   环境数量: {len(environments) if isinstance(environments, list) else 0}")
                    if isinstance(environments, list) and environments:
                        for env in environments:
                            print(f"   - {env['name']}: {env['base_url']}")
                    print(f"   ✅ 环境列表 API 正常")
                else:
                    print(f"   ❌ 环境列表 API 失败: {response.text}")
            else:
                print("   ⚠️  没有项目，请先创建项目")
        else:
            print(f"   ❌ 获取项目列表失败: {response.text}")
    except Exception as e:
        print(f"   ❌ 请求失败: {e}")
    
    # 4. 测试前端是否可访问
    print("\n4. 测试前端是否可访问...")
    try:
        response = requests.get("http://localhost:5173", timeout=5)
        print(f"   状态码: {response.status_code}")
        if response.status_code == 200:
            print(f"   ✅ 前端正常运行")
        else:
            print(f"   ❌ 前端返回异常状态码")
    except Exception as e:
        print(f"   ❌ 前端无法访问: {e}")
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)
    print("\n访问地址:")
    print("- 项目列表: http://localhost:5173/projects-v2")
    if 'project_id' in locals():
        print(f"- 项目详情: http://localhost:5173/projects-v2/{project_id}")
    print("\n如果页面打不开，请检查:")
    print("1. 浏览器控制台是否有JavaScript错误")
    print("2. 浏览器网络面板是否有API请求失败")
    print("3. 前端终端是否有编译错误")

if __name__ == "__main__":
    test_project_detail()
