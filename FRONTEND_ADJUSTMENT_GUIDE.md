# 前端调整指南 - 支持动态断言字段

## 📋 概述

后端已新增 `data_type` 和 `expected_behavior` 字段到测试用例模型，前端需要相应调整以显示和利用这些字段。

---

## 🔍 需要调整的内容

### 1. 测试用例列表显示（TestCases.jsx）

#### 当前状态
前端目前显示的字段：
- 用例名称（title）
- 模块（module）
- 优先级（priority）
- 来源（source）
- 状态（status）
- 最后运行（lastRun）

#### 建议调整
**选项A：添加新列（推荐）**

在表格中添加两列：

```jsx
<th className="text-left py-3 px-4 text-gray-600 font-medium">数据类型</th>
<th className="text-left py-3 px-4 text-gray-600 font-medium">预期行为</th>
```

显示逻辑：

```jsx
// 数据类型映射
const dataTypeMap = {
  valid: { cls: 'bg-green-100 text-green-700', label: '正常' },
  boundary: { cls: 'bg-yellow-100 text-yellow-700', label: '边界' },
  invalid: { cls: 'bg-red-100 text-red-700', label: '异常' }
}

// 预期行为映射
const behaviorMap = {
  success: { cls: 'bg-green-100 text-green-700', label: '成功' },
  client_error: { cls: 'bg-orange-100 text-orange-700', label: '客户端错误' },
  server_error: { cls: 'bg-red-100 text-red-700', label: '服务器错误' }
}

// 在表格行中添加
<td className="py-4 px-4">
  <span className={`px-2 py-1 rounded text-sm ${dataTypeMap[tc.data_type]?.cls || 'bg-gray-100 text-gray-700'}`}>
    {dataTypeMap[tc.data_type]?.label || tc.data_type || '-'}
  </span>
</td>
<td className="py-4 px-4">
  <span className={`px-2 py-1 rounded text-sm ${behaviorMap[tc.expected_behavior]?.cls || 'bg-gray-100 text-gray-700'}`}>
    {behaviorMap[tc.expected_behavior]?.label || tc.expected_behavior || '-'}
  </span>
</td>
```

**选项B：在详情中显示（最小改动）**

如果不想增加列，可以只在详情对话框中显示：

```jsx
{/* 在测试用例详情对话框中添加 */}
<div className="grid grid-cols-2 gap-4">
  <div>
    <label className="block text-sm font-medium text-gray-700 mb-1">数据类型</label>
    <div className="p-3 bg-gray-50 rounded border">
      <span className={`px-2 py-1 rounded text-sm ${dataTypeMap[selectedTestCase.data_type]?.cls}`}>
        {dataTypeMap[selectedTestCase.data_type]?.label || '-'}
      </span>
    </div>
  </div>
  <div>
    <label className="block text-sm font-medium text-gray-700 mb-1">预期行为</label>
    <div className="p-3 bg-gray-50 rounded border">
      <span className={`px-2 py-1 rounded text-sm ${behaviorMap[selectedTestCase.expected_behavior]?.cls}`}>
        {behaviorMap[selectedTestCase.expected_behavior]?.label || '-'}
      </span>
    </div>
  </div>
</div>
```

---

### 2. 测试用例筛选功能（可选增强）

可以添加按数据类型和预期行为筛选的功能：

```jsx
const [filterDataType, setFilterDataType] = useState('all')
const [filterBehavior, setFilterBehavior] = useState('all')

// 筛选逻辑
const filteredTestCases = testCases.filter(tc => {
  const matchSearch = searchQuery 
    ? (tc.title || '').toLowerCase().includes(searchQuery.toLowerCase())
    : true
  
  const matchDataType = filterDataType === 'all' || tc.data_type === filterDataType
  const matchBehavior = filterBehavior === 'all' || tc.expected_behavior === filterBehavior
  
  return matchSearch && matchDataType && matchBehavior
})

// UI组件
<div className="flex space-x-4 mb-4">
  <select
    value={filterDataType}
    onChange={(e) => setFilterDataType(e.target.value)}
    className="px-3 py-2 border border-gray-300 rounded-lg"
  >
    <option value="all">全部数据类型</option>
    <option value="valid">正常</option>
    <option value="boundary">边界</option>
    <option value="invalid">异常</option>
  </select>
  
  <select
    value={filterBehavior}
    onChange={(e) => setFilterBehavior(e.target.value)}
    className="px-3 py-2 border border-gray-300 rounded-lg"
  >
    <option value="all">全部预期行为</option>
    <option value="success">成功</option>
    <option value="client_error">客户端错误</option>
    <option value="server_error">服务器错误</option>
  </select>
</div>
```

---

### 3. 测试报告显示（Reports.jsx）

在测试报告中显示这些字段可以帮助分析：

```jsx
// 统计信息
const stats = {
  byDataType: {
    valid: testCases.filter(tc => tc.data_type === 'valid').length,
    boundary: testCases.filter(tc => tc.data_type === 'boundary').length,
    invalid: testCases.filter(tc => tc.data_type === 'invalid').length
  },
  byBehavior: {
    success: testCases.filter(tc => tc.expected_behavior === 'success').length,
    client_error: testCases.filter(tc => tc.expected_behavior === 'client_error').length,
    server_error: testCases.filter(tc => tc.expected_behavior === 'server_error').length
  }
}

// 显示统计卡片
<div className="grid grid-cols-3 gap-4 mb-6">
  <div className="bg-white p-4 rounded-lg shadow">
    <h3 className="text-sm font-medium text-gray-600 mb-2">数据类型分布</h3>
    <div className="space-y-1">
      <div className="flex justify-between">
        <span className="text-sm">正常:</span>
        <span className="font-medium">{stats.byDataType.valid}</span>
      </div>
      <div className="flex justify-between">
        <span className="text-sm">边界:</span>
        <span className="font-medium">{stats.byDataType.boundary}</span>
      </div>
      <div className="flex justify-between">
        <span className="text-sm">异常:</span>
        <span className="font-medium">{stats.byDataType.invalid}</span>
      </div>
    </div>
  </div>
  
  <div className="bg-white p-4 rounded-lg shadow">
    <h3 className="text-sm font-medium text-gray-600 mb-2">预期行为分布</h3>
    <div className="space-y-1">
      <div className="flex justify-between">
        <span className="text-sm">成功:</span>
        <span className="font-medium">{stats.byBehavior.success}</span>
      </div>
      <div className="flex justify-between">
        <span className="text-sm">客户端错误:</span>
        <span className="font-medium">{stats.byBehavior.client_error}</span>
      </div>
      <div className="flex justify-between">
        <span className="text-sm">服务器错误:</span>
        <span className="font-medium">{stats.byBehavior.server_error}</span>
      </div>
    </div>
  </div>
</div>
```

---

### 4. 断言信息显示（可选）

在测试用例详情中显示断言信息，让用户了解动态断言：

```jsx
{/* 在详情对话框中添加 */}
<div>
  <label className="block text-sm font-medium text-gray-700 mb-1">断言规则</label>
  <div className="p-3 bg-gray-50 rounded border">
    {selectedTestCase.assertions && selectedTestCase.assertions.length > 0 ? (
      <div className="space-y-2">
        {selectedTestCase.assertions.map((assertion, index) => (
          <div key={index} className="text-sm">
            <span className="font-medium">{assertion.type}:</span>
            {assertion.operator && <span className="ml-2 text-gray-600">操作符: {assertion.operator}</span>}
            <span className="ml-2 text-gray-600">
              期望: {Array.isArray(assertion.expected) 
                ? assertion.expected.join(', ') 
                : assertion.expected}
            </span>
          </div>
        ))}
      </div>
    ) : (
      <span className="text-gray-500">无断言信息</span>
    )}
  </div>
</div>

{/* 添加说明提示 */}
{selectedTestCase.expected_behavior && (
  <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
    <div className="flex items-start space-x-2">
      <span className="text-blue-600">💡</span>
      <div className="text-sm text-blue-800">
        <p className="font-medium">动态断言说明:</p>
        <p className="mt-1">
          {selectedTestCase.expected_behavior === 'success' && 
            '此用例期望成功响应（状态码 200/201/204）'}
          {selectedTestCase.expected_behavior === 'client_error' && 
            '此用例期望客户端错误（状态码 400/422/404/403）'}
          {selectedTestCase.expected_behavior === 'server_error' && 
            '此用例期望服务器错误（状态码 >= 500）'}
        </p>
      </div>
    </div>
  </div>
)}
```

---

## 📊 推荐的调整优先级

### 必须调整（P0）
1. ✅ 确保后端API返回 `data_type` 和 `expected_behavior` 字段
2. ✅ 在测试用例详情对话框中显示这两个字段

### 建议调整（P1）
3. 在测试用例列表中添加这两个字段的列
4. 在测试报告中显示数据类型和预期行为的统计

### 可选增强（P2）
5. 添加按数据类型和预期行为筛选的功能
6. 显示动态断言的详细信息和说明

---

## 🔧 具体实施步骤

### 步骤1: 更新 TestCases.jsx（最小改动）

在测试用例详情对话框中添加字段显示：

```jsx
// 在 TestCases.jsx 的详情对话框中，priority 和 module 之后添加：

<div className="grid grid-cols-2 gap-4">
  <div>
    <label className="block text-sm font-medium text-gray-700 mb-1">数据类型</label>
    <div className="p-3 bg-gray-50 rounded border">
      {(() => {
        const dataTypeMap = {
          valid: { cls: 'bg-green-100 text-green-700', label: '正常数据' },
          boundary: { cls: 'bg-yellow-100 text-yellow-700', label: '边界数据' },
          invalid: { cls: 'bg-red-100 text-red-700', label: '异常数据' }
        }
        const dt = dataTypeMap[selectedTestCase.data_type] || { cls: 'bg-gray-100 text-gray-700', label: selectedTestCase.data_type || '未知' }
        return <span className={`px-2 py-1 rounded text-sm ${dt.cls}`}>{dt.label}</span>
      })()}
    </div>
  </div>
  <div>
    <label className="block text-sm font-medium text-gray-700 mb-1">预期行为</label>
    <div className="p-3 bg-gray-50 rounded border">
      {(() => {
        const behaviorMap = {
          success: { cls: 'bg-green-100 text-green-700', label: '成功响应' },
          client_error: { cls: 'bg-orange-100 text-orange-700', label: '客户端错误' },
          server_error: { cls: 'bg-red-100 text-red-700', label: '服务器错误' }
        }
        const bh = behaviorMap[selectedTestCase.expected_behavior] || { cls: 'bg-gray-100 text-gray-700', label: selectedTestCase.expected_behavior || '未知' }
        return <span className={`px-2 py-1 rounded text-sm ${bh.cls}`}>{bh.label}</span>
      })()}
    </div>
  </div>
</div>
```

### 步骤2: 验证后端API

确保后端API返回这些字段：

```bash
# 测试API返回
curl http://localhost:5000/api/testcases | jq '.data[0] | {id, title, data_type, expected_behavior}'
```

预期输出：
```json
{
  "id": "TC_001",
  "title": "获取用户列表 - 正常流程",
  "data_type": "valid",
  "expected_behavior": "success"
}
```

### 步骤3: 测试前端显示

1. 启动前端：`cd ai-test-platform/frontend && npm run dev`
2. 打开测试用例页面
3. 点击"查看详情"按钮
4. 确认能看到"数据类型"和"预期行为"字段

---

## 📝 完整代码示例

### TestCases.jsx 完整修改（详情对话框部分）

```jsx
{/* 测试用例详情对话框 - 在现有代码中找到这部分并添加 */}
{showDetailDialog && selectedTestCase && (
  <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
    <div className="bg-white rounded-lg shadow-xl p-6 w-[700px] max-h-[80vh] overflow-y-auto">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-bold">测试用例详情</h2>
        <button
          onClick={() => setShowDetailDialog(false)}
          className="text-gray-400 hover:text-gray-600"
        >
          ✕
        </button>
      </div>
      
      <div className="space-y-4">
        {/* 用例标题 */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">用例标题</label>
          <div className="p-3 bg-gray-50 rounded border">
            {selectedTestCase.title?.replace(/^(测试用例标题|测试点|用例标题|标题)[:：]\s*/, '') || selectedTestCase.title}
          </div>
        </div>
        
        {/* 模块和优先级 */}
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">模块</label>
            <div className="p-3 bg-gray-50 rounded border">{selectedTestCase.module || '-'}</div>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">优先级</label>
            <div className="p-3 bg-gray-50 rounded border">{selectedTestCase.priority}</div>
          </div>
        </div>
        
        {/* 🆕 数据类型和预期行为 */}
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">数据类型</label>
            <div className="p-3 bg-gray-50 rounded border">
              {(() => {
                const dataTypeMap = {
                  valid: { cls: 'bg-green-100 text-green-700', label: '正常数据' },
                  boundary: { cls: 'bg-yellow-100 text-yellow-700', label: '边界数据' },
                  invalid: { cls: 'bg-red-100 text-red-700', label: '异常数据' }
                }
                const dt = dataTypeMap[selectedTestCase.data_type] || { cls: 'bg-gray-100 text-gray-700', label: selectedTestCase.data_type || '未知' }
                return <span className={`px-2 py-1 rounded text-sm ${dt.cls}`}>{dt.label}</span>
              })()}
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">预期行为</label>
            <div className="p-3 bg-gray-50 rounded border">
              {(() => {
                const behaviorMap = {
                  success: { cls: 'bg-green-100 text-green-700', label: '成功响应' },
                  client_error: { cls: 'bg-orange-100 text-orange-700', label: '客户端错误' },
                  server_error: { cls: 'bg-red-100 text-red-700', label: '服务器错误' }
                }
                const bh = behaviorMap[selectedTestCase.expected_behavior] || { cls: 'bg-gray-100 text-gray-700', label: selectedTestCase.expected_behavior || '未知' }
                return <span className={`px-2 py-1 rounded text-sm ${bh.cls}`}>{bh.label}</span>
              })()}
            </div>
          </div>
        </div>
        
        {/* 其他字段继续... */}
      </div>
    </div>
  </div>
)}
```

---

## ✅ 验证清单

- [ ] 后端API返回 `data_type` 和 `expected_behavior` 字段
- [ ] 前端详情对话框显示这两个字段
- [ ] 字段显示正确的颜色标签
- [ ] 字段值映射正确（valid→正常数据，success→成功响应等）
- [ ] 旧数据（没有这些字段）不会导致前端报错

---

## 🎯 总结

**最小改动方案**：只需在测试用例详情对话框中添加两个字段的显示，约20行代码。

**完整方案**：包括列表显示、筛选、统计等功能，约100-150行代码。

**建议**：先实施最小改动方案，验证后端数据正确后，再根据需要添加其他功能。
