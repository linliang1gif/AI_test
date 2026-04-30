#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试前端和后端集成
验证AI提供商功能是否正常工作
"""

import requests
import json
import time

def test_api_endpoints():
    """测试API端点"""
    
    base_url = "http://localhost:8000"
    
    print("🧪 前端后端集成测试")
    print("=" * 50)
    
    # 测试用例
    test_cases = [
        {
            "name": "AI提供商列表",
            "method": "GET",
            "url": f"{base_url}/api/ai/providers/list",
            "expected_keys": ["providers", "current"]
        },
        {
            "name": "仪表板统计",
            "method": "GET", 
            "url": f"{base_url}/api/dashboard/stats",
            "expected_keys": ["totalTests", "passed", "failed", "coverage"]
        },
        {
            "name": "Ollama状态检查",
            "method": "GET",
            "url": f"{base_url}/api/ai/providers/ollama/status",
            "expected_keys": ["provider"]
        }
    ]
    
    results = []
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. 测试 {test_case['name']}...")
        
        try:
            if test_case["method"] == "GET":
                response = requests.get(test_case["url"], timeout=5)
            else:
                response = requests.post(test_case["url"], timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                
                # 检查必需的键
                missing_keys = []
                for key in test_case["expected_keys"]:
                    if key not in data:
                        missing_keys.append(key)
                
                if not missing_keys:
                    print(f"  ✅ 成功 - 状态码: {response.status_code}")
                    print(f"  📊 数据键: {list(data.keys())}")
                    
                    # 显示特定数据
                    if "providers" in data:
                        providers = data["providers"]
                        print(f"  🤖 发现 {len(providers)} 个AI提供商")
                        for provider in providers:
                            status_icon = "✅" if provider["status"] == "available" else "❌"
                            print(f"    {status_icon} {provider['name']} ({provider['type']})")
                    
                    results.append(True)
                else:
                    print(f"  ❌ 缺少必需的键: {missing_keys}")
                    results.append(False)
            else:
                print(f"  ❌ HTTP错误: {response.status_code}")
                results.append(False)
                
        except Exception as e:
            print(f"  ❌ 请求失败: {e}")
            results.append(False)
    
    # 测试POST请求 - 选择提供商
    print(f"\n4. 测试提供商选择...")
    try:
        response = requests.post(
            f"{base_url}/api/ai/providers/select",
            json={"provider_id": "ollama"},
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                print(f"  ✅ 提供商选择成功")
                print(f"  📝 消息: {data.get('message', '')}")
                results.append(True)
            else:
                print(f"  ❌ 提供商选择失败: {data.get('error', '')}")
                results.append(False)
        else:
            print(f"  ❌ HTTP错误: {response.status_code}")
            results.append(False)
            
    except Exception as e:
        print(f"  ❌ 请求失败: {e}")
        results.append(False)
    
    # 总结
    print(f"\n📊 测试总结:")
    print(f"通过: {sum(results)}/{len(results)}")
    
    if all(results):
        print("\n🎉 所有API测试通过！")
        return True
    else:
        print(f"\n⚠️  {len(results) - sum(results)} 个测试失败")
        return False

def generate_frontend_instructions():
    """生成前端使用说明"""
    
    print("\n📋 前端集成说明:")
    print("=" * 50)
    
    instructions = """
1. 确保前端服务运行在 http://localhost:3000
2. 后端API服务运行在 http://localhost:8000
3. 在AI Insights页面点击 "AI Provider Settings" 按钮
4. 页面将显示可用的AI提供商卡片
5. 点击提供商卡片进行切换

前端API调用示例:
```javascript
// 获取提供商列表
const response = await fetch('/api/ai/providers/list');
const data = await response.json();

// 选择提供商
const selectResponse = await fetch('/api/ai/providers/select', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ provider_id: 'ollama' })
});
```

预期的提供商数据结构:
```json
{
  "providers": [
    {
      "id": "ollama",
      "name": "Ollama", 
      "description": "本地AI模型服务",
      "type": "local",
      "status": "available",
      "models": ["qwen2.5:1.5b", "qwen2.5-coder:latest"],
      "default_model": "qwen2.5:1.5b"
    }
  ],
  "current": "ollama"
}
```
"""
    
    print(instructions)

def main():
    """主函数"""
    
    # 测试API端点
    api_success = test_api_endpoints()
    
    # 生成前端说明
    generate_frontend_instructions()
    
    if api_success:
        print("\n🚀 系统就绪！")
        print("\n下一步操作:")
        print("1. 确保前端服务运行: cd frontend && npm run dev")
        print("2. 访问: http://localhost:3000")
        print("3. 进入 AI Insights 页面")
        print("4. 点击 'AI Provider Settings' 查看提供商")
        print("5. 选择 Ollama 提供商开始使用本地AI")
    else:
        print("\n⚠️  请检查API服务器配置")

if __name__ == "__main__":
    main()