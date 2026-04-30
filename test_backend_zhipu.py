"""测试后端API使用智谱AI生成测试用例"""
import requests
import json
import io

def test_backend_testcase_generation():
    """测试后端测试用例生成"""
    print("=" * 60)
    print("🧪 测试后端API - 测试用例生成 (智谱AI)")
    print("=" * 60)
    
    url = "http://localhost:8000/api/testcases/generate"
    
    # 创建测试需求文档
    requirement_text = """
用户登录功能需求说明

1. 功能描述
用户可以通过用户名和密码登录系统

2. 详细需求
- 用户在登录页面输入用户名和密码
- 点击登录按钮
- 系统验证用户信息
- 验证成功后跳转到首页
- 验证失败显示错误提示

3. 验证规则
- 用户名不能为空
- 密码不能为空
- 密码长度至少6位
"""
    
    # 创建文件对象
    files = {
        'file': ('requirement.txt', io.BytesIO(requirement_text.encode('utf-8')), 'text/plain')
    }
    
    print(f"📤 发送请求到: {url}")
    print(f"📝 需求文档: requirement.txt")
    print()
    
    try:
        response = requests.post(url, files=files, timeout=60)
        
        print(f"📥 响应状态码: {response.status_code}")
        print()
        
        if response.status_code == 200:
            result = response.json()
            print("✅ 测试用例生成成功!")
            print()
            print(f"📊 生成了 {len(result.get('testcases', []))} 个测试用例")
            print()
            
            # 显示生成的测试用例
            for i, tc in enumerate(result.get('testcases', [])[:3], 1):
                print(f"测试用例 {i}:")
                print(f"  标题: {tc.get('title', 'N/A')}")
                print(f"  优先级: {tc.get('priority', 'N/A')}")
                print(f"  类型: {tc.get('type', 'N/A')}")
                if 'steps' in tc and tc['steps']:
                    print(f"  步骤数: {len(tc['steps'])}")
                print()
            
            return True
        else:
            print("❌ 请求失败!")
            print(f"错误: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ 请求超时")
        return False
    except Exception as e:
        print(f"❌ 发生错误: {e}")
        return False

if __name__ == "__main__":
    success = test_backend_testcase_generation()
    print("=" * 60)
    if success:
        print("✅ 后端API测试通过 - 智谱AI工作正常")
    else:
        print("❌ 后端API测试失败")
    print("=" * 60)
