# 项目列表 API 错误修复

## 问题描述

用户访问项目列表页面时出现错误：
```
API调用失败: 422 
{"detail":[{
  "type":"int_parsing",
  "loc":["path","project_id"],
  "msg":"Input should be a valid integer, unable to parse string as an integer",
  "input":"undefined"
}]}
```

## 问题原因

### 1. 根本原因

前端在调用 API 时，将 `null` 或 `undefined` 作为 `project_id` 参数传递到 URL 中：
```javascript
// 错误的调用
const query = projectId ? `?project_id=${projectId}` : ''
// 当 projectId = null 时，会生成: ?project_id=null
// 后端收到字符串 "null" 而不是 null 值
```

### 2. 触发场景

在 `ApiSpecList.jsx` 页面：
```javascript
const [selectedProject, setSelectedProject] = useState(null)

useEffect(() => {
  loadApiSpecs()  // 此时 selectedProject = null
}, [selectedProject])

const loadApiSpecs = async () => {
  const data = await api.v2.swagger.getApiSpecs(selectedProject)  // 传递 null
}
```

### 3. 后端期望

后端定义：
```python
@router.get("/swagger/api-specs")
async def get_api_specs(
    project_id: int = Query(None, description="项目ID"),  # 期望 int 或 None
    db: Session = Depends(get_db)
):
```

但收到的是 URL: `/api/v2/swagger/api-specs?project_id=null`
- FastAPI 尝试将字符串 `"null"` 解析为 int
- 解析失败，返回 422 错误

## 修复方案

### 1. 修复 getApiSpecs

**修改前：**
```javascript
getApiSpecs: (projectId) => {
  const query = projectId ? `?project_id=${projectId}` : ''
  return request(`${API_BASE_URL}/v2/swagger/api-specs${query}`)
},
```

**修改后：**
```javascript
getApiSpecs: (projectId) => {
  // 只有当 projectId 是有效数字时才添加查询参数
  const query = (projectId && !isNaN(projectId)) ? `?project_id=${projectId}` : ''
  return request(`${API_BASE_URL}/v2/swagger/api-specs${query}`)
},
```

### 2. 修复 importFromFile

**修改前：**
```javascript
importFromFile: (projectId, file, generateCases = true) => {
  const formData = new FormData()
  formData.append('file', file)
  return fetch(`${API_BASE_URL}/v2/swagger/import-file?project_id=${projectId}&generate_cases=${generateCases}`, {
    method: 'POST',
    body: formData,
  })
}
```

**修改后：**
```javascript
importFromFile: (projectId, file, generateCases = true) => {
  // 确保 projectId 是有效数字
  if (!projectId || isNaN(projectId)) {
    return Promise.reject(new Error('项目ID无效'))
  }
  const formData = new FormData()
  formData.append('file', file)
  return fetch(`${API_BASE_URL}/v2/swagger/import-file?project_id=${projectId}&generate_cases=${generateCases}`, {
    method: 'POST',
    body: formData,
  })
}
```

## 修复效果

### 1. 正确处理 null/undefined

- ✅ 当 `projectId` 为 `null` 时，不添加查询参数
- ✅ 当 `projectId` 为 `undefined` 时，不添加查询参数
- ✅ 当 `projectId` 为有效数字时，正常添加查询参数

### 2. URL 对比

**修复前：**
```
/api/v2/swagger/api-specs?project_id=null      ❌ 错误
/api/v2/swagger/api-specs?project_id=undefined ❌ 错误
```

**修复后：**
```
/api/v2/swagger/api-specs                      ✅ 正确（不传参数）
/api/v2/swagger/api-specs?project_id=8         ✅ 正确（传有效ID）
```

### 3. 错误提示

对于 `importFromFile`，如果 `projectId` 无效，会提前返回错误：
```javascript
return Promise.reject(new Error('项目ID无效'))
```

## 其他潜在问题

检查了其他类似的 API 调用，发现这些也可能有问题（但目前未使用）：

### Pilot API（已废弃，不修复）
```javascript
apis: {
  getAll: (projectId) => request(`${PILOT_API_BASE_URL}/apis${projectId ? `?project_id=${projectId}` : ''}`),
},
testCases: {
  getAll: (projectId) => request(`${PILOT_API_BASE_URL}/test-cases${projectId ? `?project_id=${projectId}` : ''}`),
},
testRuns: {
  getAll: (projectId) => request(`${PILOT_API_BASE_URL}/test-runs${projectId ? `?project_id=${projectId}` : ''}`),
},
```

这些 API 使用的是 Pilot API（已废弃），不需要修复。

## 最佳实践

### 1. 参数验证

在构建 URL 前验证参数：
```javascript
// 方法1：检查是否为有效数字
if (projectId && !isNaN(projectId)) {
  query += `?project_id=${projectId}`
}

// 方法2：使用 Number() 转换
const pid = Number(projectId)
if (!isNaN(pid)) {
  query += `?project_id=${pid}`
}

// 方法3：提前返回错误
if (!projectId || isNaN(projectId)) {
  return Promise.reject(new Error('参数无效'))
}
```

### 2. 使用 URLSearchParams

更安全的方式是使用 `URLSearchParams`：
```javascript
const params = new URLSearchParams()
if (projectId && !isNaN(projectId)) {
  params.append('project_id', projectId)
}
const query = params.toString()
const url = `${API_BASE_URL}/api${query ? '?' + query : ''}`
```

### 3. TypeScript 类型检查

如果使用 TypeScript，可以在类型层面避免这个问题：
```typescript
getApiSpecs: (projectId?: number) => {
  const query = projectId ? `?project_id=${projectId}` : ''
  return request(`${API_BASE_URL}/v2/swagger/api-specs${query}`)
}
```

## 测试验证

### 1. 手动测试

- [ ] 访问 `/projects-v2` 页面，确认无错误
- [ ] 访问 `/api-specs` 页面，确认无错误
- [ ] 在 API 规范页面选择项目，确认正常加载
- [ ] 在 API 规范页面不选择项目，确认显示所有规范

### 2. 控制台检查

打开浏览器控制台，确认：
- ✅ 无 422 错误
- ✅ 无 `unable to parse string as an integer` 错误
- ✅ API 调用成功

### 3. 网络请求检查

在浏览器开发者工具的 Network 标签中，检查：
- ✅ `/api/v2/swagger/api-specs` 请求成功（200）
- ✅ URL 中没有 `project_id=null` 或 `project_id=undefined`

## 总结

这是一个常见的前端参数传递问题：
- ❌ 问题：将 `null`/`undefined` 直接拼接到 URL 中
- ✅ 解决：在拼接前验证参数是否为有效值
- 📝 教训：所有 URL 参数都应该在使用前验证

修复后，项目列表和 API 规范列表页面应该可以正常访问了。
