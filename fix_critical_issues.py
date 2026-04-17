"""自动修复AI测试平台的关键问题"""
import sys
from pathlib import Path

print("=" * 80)
print("AI测试平台 - 自动修复工具")
print("=" * 80)
print()

fixes_applied = []
fixes_failed = []

# 优先级1：检查并修复后端路由配置
print("优先级1：检查后端路由配置...")
print("-" * 80)

backend_file = Path("ai-test-platform/backend_api_server.py")
if backend_file.exists():
    content = backend_file.read_text(encoding='utf-8')
    
    # 检查关键路由是否存在
    routes_to_check = [
        ("/api/execute-api", "API执行"),
        ("/api/save-api-as-testcase", "保存测试用例"),
        ("/api/test-cases", "测试用例管理"),
        ("/api/automation/scripts/generate", "脚本生成"),
        ("/api/automation/scripts/<int:script_id>/download", "脚本下载"),
        ("/api/automation/scripts/<int:script_id>/execute", "脚本执行"),
    ]
    
    missing_routes = []
    for route, name in routes_to_check:
        # 简化检查：只看路由字符串是否存在
        route_simple = route.replace("<int:script_id>", "").replace("/", "")
        if route_simple not in content:
            missing_routes.append((route, name))
            print(f"⚠️  缺少路由: {name} ({route})")
        else:
            print(f"✅ 路由存在: {name}")
    
    if missing_routes:
        print(f"\n发现 {len(missing_routes)} 个缺失的路由")
        fixes_failed.append(f"后端缺少 {len(missing_routes)} 个路由")
    else:
        print("\n✅ 所有关键路由都存在")
        fixes_applied.append("后端路由检查通过")
else:
    print("❌ 后端文件不存在")
    fixes_failed.append("后端文件不存在")

print()

# 优先级2：创建缺失的前端页面
print("优先级2：创建缺失的前端页面...")
print("-" * 80)

test_data_page = Path("ai-test-platform/frontend/src/pages/TestData.jsx")
if not test_data_page.exists():
    print("创建测试数据页面...")
    
    test_data_content = '''import React, { useState, useEffect } from 'react'
import { testDataAPI } from '../services/api'

export default function TestData() {
  const [datasets, setDatasets] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadDatasets()
  }, [])

  const loadDatasets = async () => {
    try {
      const response = await testDataAPI.getDatasets()
      setDatasets(response.datasets || [])
    } catch (error) {
      console.error('加载数据集失败:', error)
    } finally {
      setLoading(false)
    }
  }

  const generateTestData = async (dataType) => {
    try {
      const response = await testDataAPI.generate({
        data_type: dataType,
        count: 1
      })
      alert(`生成成功:\\n${JSON.stringify(response.data, null, 2)}`)
    } catch (error) {
      alert(`生成失败: ${error.message}`)
    }
  }

  if (loading) {
    return <div className="p-6">加载中...</div>
  }

  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold mb-2">测试数据管理</h1>
        <p className="text-gray-600">生成和管理测试数据</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <button
          onClick={() => generateTestData('user')}
          className="p-4 bg-blue-500 text-white rounded hover:bg-blue-600"
        >
          生成用户数据
        </button>
        <button
          onClick={() => generateTestData('order')}
          className="p-4 bg-green-500 text-white rounded hover:bg-green-600"
        >
          生成订单数据
        </button>
        <button
          onClick={() => generateTestData('product')}
          className="p-4 bg-purple-500 text-white rounded hover:bg-purple-600"
        >
          生成商品数据
        </button>
      </div>

      <div className="bg-white rounded-lg shadow">
        <div className="p-4 border-b">
          <h2 className="text-lg font-semibold">数据集列表</h2>
        </div>
        <div className="p-4">
          {datasets.length === 0 ? (
            <p className="text-gray-500 text-center py-8">暂无数据集</p>
          ) : (
            <div className="space-y-2">
              {datasets.map((dataset) => (
                <div key={dataset.id} className="p-3 border rounded hover:bg-gray-50">
                  <div className="font-medium">{dataset.name}</div>
                  <div className="text-sm text-gray-600">{dataset.description}</div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
'''
    
    try:
        test_data_page.parent.mkdir(parents=True, exist_ok=True)
        test_data_page.write_text(test_data_content, encoding='utf-8')
        print("✅ 测试数据页面创建成功")
        fixes_applied.append("创建测试数据页面")
    except Exception as e:
        print(f"❌ 创建失败: {e}")
        fixes_failed.append(f"创建测试数据页面失败: {e}")
else:
    print("✅ 测试数据页面已存在")

print()

# 优先级3：检查API服务配置
print("优先级3：检查前端API服务配置...")
print("-" * 80)

api_service = Path("ai-test-platform/frontend/src/services/api.js")
if api_service.exists():
    content = api_service.read_text(encoding='utf-8')
    
    # 检查testDataAPI是否存在
    if 'testDataAPI' not in content or 'getDatasets' not in content:
        print("⚠️  testDataAPI配置不完整，需要添加")
        
        # 添加testDataAPI配置
        test_data_api_code = '''
// Test Data API
export const testDataAPI = {
  generate: (data) => request('/test-data/generate', {
    method: 'POST',
    body: JSON.stringify(data),
  }),
  getDatasets: () => request('/test-data/datasets'),
  createDataset: (data) => request('/test-data/datasets', {
    method: 'POST',
    body: JSON.stringify(data),
  }),
}
'''
        
        # 在export default之前插入
        if 'export default {' in content:
            parts = content.split('export default {')
            new_content = parts[0] + test_data_api_code + '\nexport default {'
            if len(parts) > 1:
                new_content += parts[1]
            
            # 在export default中添加testData
            new_content = new_content.replace(
                'export default {',
                'export default {\n  testData: testDataAPI,'
            )
            
            try:
                api_service.write_text(new_content, encoding='utf-8')
                print("✅ testDataAPI配置已添加")
                fixes_applied.append("添加testDataAPI配置")
            except Exception as e:
                print(f"❌ 添加失败: {e}")
                fixes_failed.append(f"添加testDataAPI失败: {e}")
    else:
        print("✅ testDataAPI配置已存在")
else:
    print("❌ API服务文件不存在")
    fixes_failed.append("API服务文件不存在")

print()

# 优先级4：检查路由配置
print("优先级4：检查前端路由配置...")
print("-" * 80)

# 查找路由配置文件
route_files = [
    Path("ai-test-platform/frontend/src/App.jsx"),
    Path("ai-test-platform/frontend/src/App.tsx"),
    Path("ai-test-platform/frontend/src/router/index.jsx"),
]

route_file = None
for f in route_files:
    if f.exists():
        route_file = f
        break

if route_file:
    content = route_file.read_text(encoding='utf-8')
    
    if 'TestData' not in content or '/test-data' not in content:
        print("⚠️  测试数据路由未配置")
        print("   需要手动添加路由:")
        print("   import TestData from './pages/TestData'")
        print("   <Route path='/test-data' element={<TestData />} />")
        fixes_failed.append("测试数据路由需要手动配置")
    else:
        print("✅ 测试数据路由已配置")
        fixes_applied.append("测试数据路由检查通过")
else:
    print("⚠️  未找到路由配置文件")
    fixes_failed.append("未找到路由配置文件")

print()

# 总结
print("=" * 80)
print("修复总结")
print("=" * 80)
print()

if fixes_applied:
    print(f"✅ 成功修复 {len(fixes_applied)} 项:")
    for fix in fixes_applied:
        print(f"   - {fix}")
    print()

if fixes_failed:
    print(f"⚠️  需要手动处理 {len(fixes_failed)} 项:")
    for fix in fixes_failed:
        print(f"   - {fix}")
    print()

print("下一步操作:")
print()
print("1. 重启后端服务:")
print("   cd ai-test-platform")
print("   py backend_api_server.py")
print()
print("2. 重启前端服务:")
print("   cd ai-test-platform/frontend")
print("   npm run dev")
print()
print("3. 硬刷新浏览器:")
print("   按 Ctrl+Shift+R")
print()
print("4. 重新检查功能:")
print("   py check_all_features.py")
