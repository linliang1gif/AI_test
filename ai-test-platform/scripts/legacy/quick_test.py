"""
一键快速测试 - AI测试控制台
最快速度验证系统是否正常
"""
import requests
import sys


def quick_test():
    """快速测试"""
    print("\n🚀 AI测试控制台 - 快速测试\n")
    
    # 1. 检查后端
    print("1️⃣ 检查后端服务...", end=" ")
    try:
        r = requests.get("http://localhost:8000/api/pipeline/health", timeout=3)
        if r.json().get('status') == 'healthy':
            print("✅")
        else:
            print("❌")
            return False
    except:
        print("❌ (未运行)")
        print("\n请先启动后端: python backend_api_server.py")
        return False
    
    # 2. 检查前端
    print("2️⃣ 检查前端服务...", end=" ")
    try:
        r = requests.get("http://localhost:5173", timeout=3)
        if r.status_code == 200:
            print("✅")
        else:
            print("❌")
            return False
    except:
        print("❌ (未运行)")
        print("\n请先启动前端: cd frontend && npm run dev")
        return False
    
    # 3. 测试API
    print("3️⃣ 测试Pipeline API...", end=" ")
    try:
        r = requests.post(
            "http://localhost:8000/api/pipeline/run",
            json={
                "requirement": "测试功能",
                "context": {"priority": "P1"}
            },
            timeout=25
        )
        if r.status_code == 200:
            result = r.json()
            trace_id = result.get('trace_id')
            print(f"✅ (Trace: {trace_id})")
        else:
            print("❌")
            return False
    except Exception as e:
        print(f"❌ ({str(e)})")
        return False
    
    # 成功
    print("\n" + "="*50)
    print("🎉 系统正常！可以使用了")
    print("="*50)
    print("\n📍 访问地址:")
    print("   http://localhost:5173/ai-test-console")
    print("\n💡 快速使用:")
    print("   1. 输入需求描述")
    print("   2. 选择优先级")
    print("   3. 点击 Run AI Test")
    print("   4. 查看结果（10-20秒）\n")
    
    return True


if __name__ == "__main__":
    success = quick_test()
    sys.exit(0 if success else 1)
