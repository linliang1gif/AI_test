import requests
import json

print("=" * 60)
print("检查AI测试平台数据状态")
print("=" * 60)

apis = {
    'projects': '/api/projects',
    'apis': '/api/apis',
    'test-cases': '/api/test-cases',
    'reports': '/api/reports',
    'scripts': '/api/automation/scripts'
}

for name, endpoint in apis.items():
    try:
        r = requests.get(f'http://127.0.0.1:8081{endpoint}')
        data = r.json()
        
        # 处理不同的响应格式
        if isinstance(data, dict):
            if 'projects' in data:
                count = len(data['projects'])
            elif 'testCases' in data:
                count = len(data['testCases'])
            elif 'scripts' in data:
                count = len(data['scripts'])
            elif 'apis' in data:
                count = len(data['apis'])
            elif 'reports' in data:
                count = len(data['reports'])
            else:
                count = len(data)
        elif isinstance(data, list):
            count = len(data)
        else:
            count = 1
            
        status = "✅ 已清空" if count == 0 else f"⚠️ 还有 {count} 条数据"
        print(f"{name:15} {status}")
        
    except Exception as e:
        print(f"{name:15} ❌ 错误: {e}")

print("=" * 60)
