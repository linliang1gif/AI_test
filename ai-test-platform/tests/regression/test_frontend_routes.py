"""测试前端路由是否正常"""
import requests

FRONTEND_URL = "http://localhost:5174"

routes = [
    "/",
    "/dashboard",
    "/projects-v2",
    "/test-cases",
    "/api-specs",
    "/test-runs-v2",
]

print("="*60)
print("前端路由测试")
print("="*60)

for route in routes:
    try:
        response = requests.get(f"{FRONTEND_URL}{route}", timeout=5)
        # 对于SPA，所有路由都应该返回200并返回HTML
        if response.status_code == 200 and 'html' in response.headers.get('content-type', '').lower():
            print(f"✅ {route:30} - 200 OK (HTML)")
        else:
            print(f"❌ {route:30} - {response.status_code} ({response.headers.get('content-type', 'unknown')})")
    except Exception as e:
        print(f"❌ {route:30} - 异常: {str(e)}")

print("\n" + "="*60)
print("说明: SPA应用所有路由都应返回200和HTML")
print("="*60)
