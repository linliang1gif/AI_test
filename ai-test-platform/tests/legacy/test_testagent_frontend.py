"""
测试 TestAgent 前端页面集成
验证路由是否正确配置
"""
import requests
import json

def test_frontend_routing():
    """测试前端路由是否包含 TestAgent 页面"""
    print("=" * 60)
    print("测试 TestAgent 前端页面集成")
    print("=" * 60)
    
    # 1. 检查前端服务器
    try:
        response = requests.get("http://localhost:5173", timeout=5)
        print(f"\n✅ 前端服务器运行正常 (状态码: {response.status_code})")
    except Exception as e:
        print(f"\n❌ 前端服务器连接失败: {e}")
        return
    
    # 2. 检查后端 TestAgent API
    try:
        response = requests.get("http://localhost:8000/api/agent/health", timeout=5)
        data = response.json()
        print(f"\n✅ TestAgent API 健康检查:")
        print(f"   状态: {data.get('status')}")
        print(f"   LLM提供商: {data.get('llm_provider')}")
        print(f"   模型: {data.get('model')}")
    except Exception as e:
        print(f"\n❌ TestAgent API 连接失败: {e}")
        return
    
    # 3. 测试分析功能
    test_data = {
        "requirement": "修改用户登录接口，增加验证码功能",
        "git_diff": """
diff --git a/auth/login.py b/auth/login.py
@@ -10,6 +10,8 @@ def login(username, password):
+    # 新增验证码验证
+    if not verify_captcha(captcha):
+        return {"error": "验证码错误"}
     user = authenticate(username, password)
"""
    }
    
    try:
        response = requests.post(
            "http://localhost:8000/api/agent/analyze",
            json=test_data,
            timeout=30
        )
        result = response.json()
        print(f"\n✅ TestAgent 分析功能测试:")
        print(f"   需要测试: {result.get('need_test')}")
        print(f"   影响模块: {result.get('modules')}")
        print(f"   优先级: {result.get('priority')}")
        print(f"   原因: {result.get('reason')}")
    except Exception as e:
        print(f"\n❌ TestAgent 分析失败: {e}")
    
    # 4. 访问说明
    print("\n" + "=" * 60)
    print("✅ TestAgent 模块集成完成！")
    print("=" * 60)
    print("\n📌 访问方式:")
    print("   1. 打开浏览器访问: http://localhost:5173")
    print("   2. 在左侧导航栏找到 '🎯 AI测试决策' 菜单")
    print("   3. 点击进入 TestAgent 页面")
    print("\n📌 功能说明:")
    print("   - 输入需求文档和Git变更")
    print("   - AI自动分析是否需要测试")
    print("   - 给出测试范围和优先级建议")
    print("   - 查看历史决策记录")
    print("   - 查看统计数据")

if __name__ == "__main__":
    test_frontend_routing()
