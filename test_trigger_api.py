"""
测试触发系统API
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_manual_trigger():
    """测试手动触发"""
    print("=" * 60)
    print("测试手动触发API")
    print("=" * 60)
    
    url = f"{BASE_URL}/api/trigger/manual"
    data = {
        "requirement": "测试用户登录功能",
        "priority": "P1",
        "user": "测试用户"
    }
    
    try:
        response = requests.post(url, json=data, timeout=10)
        print(f"状态码: {response.status_code}")
        print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        return response.json()
    except Exception as e:
        print(f"❌ 错误: {e}")
        return None

def test_list_triggers():
    """测试查询触发记录"""
    print("\n" + "=" * 60)
    print("测试查询触发记录")
    print("=" * 60)
    
    url = f"{BASE_URL}/api/trigger/list"
    
    try:
        response = requests.get(url, timeout=10)
        print(f"状态码: {response.status_code}")
        result = response.json()
        print(f"触发记录数: {result.get('total', 0)}")
        
        if result.get('triggers'):
            print("\n最近的触发记录:")
            for trigger in result['triggers'][:3]:
                print(f"  - {trigger['trigger_id']}: {trigger['status']}")
        
        return result
    except Exception as e:
        print(f"❌ 错误: {e}")
        return None

def test_git_push_trigger():
    """测试Git Push触发"""
    print("\n" + "=" * 60)
    print("测试Git Push触发")
    print("=" * 60)
    
    url = f"{BASE_URL}/api/trigger/git-push"
    data = {
        "repo": "test-repo",
        "branch": "main",
        "commit_id": "abc123",
        "commit_message": "fix: 修复登录bug",
        "changed_files": ["src/auth/login.py", "tests/test_login.py"],
        "author": "developer"
    }
    
    try:
        response = requests.post(url, json=data, timeout=10)
        print(f"状态码: {response.status_code}")
        print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        return response.json()
    except Exception as e:
        print(f"❌ 错误: {e}")
        return None

def test_scheduled_trigger():
    """测试定时触发"""
    print("\n" + "=" * 60)
    print("测试定时触发")
    print("=" * 60)
    
    url = f"{BASE_URL}/api/trigger/scheduled"
    data = {
        "cron_expression": "0 2 * * *",  # 每天凌晨2点
        "requirement": "每日回归测试",
        "job_name": "daily_regression",
        "priority": "P2"
    }
    
    try:
        response = requests.post(url, json=data, timeout=10)
        print(f"状态码: {response.status_code}")
        print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        return response.json()
    except Exception as e:
        print(f"❌ 错误: {e}")
        return None

def main():
    print("🚀 触发系统API测试")
    print("=" * 60)
    
    # 测试手动触发
    manual_result = test_manual_trigger()
    
    # 测试Git Push触发
    git_result = test_git_push_trigger()
    
    # 测试定时触发
    scheduled_result = test_scheduled_trigger()
    
    # 查询触发记录
    import time
    time.sleep(2)  # 等待触发执行
    test_list_triggers()
    
    print("\n" + "=" * 60)
    print("✅ 测试完成")
    print("=" * 60)

if __name__ == "__main__":
    main()
