"""测试后端API并查看详细日志"""
import requests
import io
import time

def test_backend():
    """测试后端测试用例生成"""
    print("=" * 60)
    print("🧪 测试后端API - 查看详细日志")
    print("=" * 60)
    
    url = "http://localhost:8000/api/testcases/generate"
    
    # 创建简单的测试需求
    requirement_text = """
用户注册功能

1. 用户填写注册信息(用户名、邮箱、密码)
2. 点击注册按钮
3. 系统验证信息格式
4. 创建用户账号
5. 发送验证邮件
"""
    
    files = {
        'file': ('register_requirement.txt', io.BytesIO(requirement_text.encode('utf-8')), 'text/plain')
    }
    
    print(f"📤 发送请求到: {url}")
    print(f"📝 需求: 用户注册功能")
    print()
    print("⏳ 等待AI生成(可能需要10-30秒)...")
    print()
    
    try:
        start_time = time.time()
        response = requests.post(url, files=files, timeout=120)
        elapsed = time.time() - start_time
        
        print(f"📥 响应状态码: {response.status_code}")
        print(f"⏱️  耗时: {elapsed:.2f}秒")
        print()
        
        if response.status_code == 200:
            result = response.json()
            
            if result.get('success'):
                testcases = result.get('testCases', [])
                print(f"✅ 成功生成 {len(testcases)} 个测试用例")
                print()
                
                # 显示前3个测试用例
                for i, tc in enumerate(testcases[:3], 1):
                    print(f"测试用例 {i}:")
                    print(f"  ID: {tc.get('id')}")
                    print(f"  标题: {tc.get('title')}")
                    print(f"  模块: {tc.get('module')}")
                    print(f"  优先级: {tc.get('priority')}")
                    print(f"  类型: {tc.get('type')}")
                    print(f"  来源: {tc.get('source')}")
                    
                    steps = tc.get('steps', [])
                    if steps:
                        print(f"  步骤数: {len(steps)}")
                        if len(steps) > 0:
                            print(f"    第一步: {steps[0]}")
                    print()
                
                # 检查来源
                sources = set(tc.get('source', 'unknown') for tc in testcases)
                print(f"📊 测试用例来源: {', '.join(sources)}")
                
                if 'ai_generated' in sources:
                    print("✅ 使用了AI生成")
                elif 'smart_generated' in sources:
                    print("⚠️  使用了快速生成(AI可能失败)")
                
                return True
            else:
                print(f"❌ 生成失败: {result.get('error')}")
                return False
        else:
            print(f"❌ 请求失败")
            print(f"错误: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ 请求超时(超过120秒)")
        return False
    except Exception as e:
        print(f"❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("\n提示: 请同时查看后端终端的日志输出\n")
    success = test_backend()
    print()
    print("=" * 60)
    if success:
        print("✅ 测试完成")
    else:
        print("❌ 测试失败")
    print("=" * 60)
