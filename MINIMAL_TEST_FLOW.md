# 最小可用测试执行流程

## 流程概览

```
Swagger解析 → 执行API → 保存为测试用例 → 执行测试用例
```

## 详细步骤

### 步骤1: Swagger解析API
**前端操作：** 上传Swagger文件
**后端接口：** `POST /api/upload/swagger`
**返回数据：** API列表

### 步骤2: 执行API
**前端操作：** 点击"执行"按钮
**后端接口：** `POST /api/execute-api`
**返回数据：** 执行结果（状态码、响应时间、响应数据）

### 步骤3: 保存为测试用例
**前端操作：** 点击"保存为测试用例"按钮
**后端接口：** `POST /api/save-api-as-testcase`
**返回数据：** 测试用例ID

### 步骤4: 执行测试用例
**前端操作：** 点击"执行测试用例"按钮
**后端接口：** `POST /api/testcases/{id}/execute`
**返回数据：** 执行结果

## 前端实现

### ApiExplorer.jsx - API管理页面

```jsx
import React, { useState } from 'react'
import api from '@/services/api'
import ApiExecutor from '@/components/ApiExecutor'

export default function ApiExplorer() {
  const [apis, setApis] = useState([])
  const [selectedApi, setSelectedApi] = useState(null)
  const [showExecutor, setShowExecutor] = useState(false)
  const [executionResult, setExecutionResult] = useState(null)
  const [savedTestCaseId, setSavedTestCaseId] = useState(null)

  // 步骤1: 上传Swagger文件
  const handleSwaggerUpload = async (file) => {
    try {
      const result = await api.swagger.upload(file)
      if (result.success) {
        // 重新加载API列表
        loadApis()
        alert('Swagger上传成功！')
      }
    } catch (error) {
      alert('上传失败: ' + error.message)
    }
  }

  // 加载API列表
  const loadApis = async () => {
    try {
      const result = await api.apis.getAll()
      setApis(result.apis || [])
    } catch (error) {
      console.error('加载API失败:', error)
    }
  }

  // 步骤2: 执行API
  const handleExecuteApi = (apiItem) => {
    setSelectedApi(apiItem)
    setShowExecutor(true)
  }

  // API执行完成回调
  const handleExecutionComplete = (result) => {
    setExecutionResult(result)
    setShowExecutor(false)
  }

  // 步骤3: 保存为测试用例
  const handleSaveAsTestCase = async () => {
    if (!executionResult || !selectedApi) {
      alert('请先执行API')
      return
    }

    try {
      const result = await api.apis.saveAsTestCase({
        api_info: {
          name: selectedApi.name,
          method: selectedApi.method,
          path: selectedApi.path,
          tags: selectedApi.tags || []
        },
        execution_result: executionResult,
        request_data: executionResult.request_data || {}
      })

      if (result.success) {
        setSavedTestCaseId(result.test_case_id)
        alert('保存成功！测试用例ID: ' + result.test_case_id)
      }
    } catch (error) {
      alert('保存失败: ' + error.message)
    }
  }

  // 步骤4: 执行测试用例
  const handleExecuteTestCase = async () => {
    if (!savedTestCaseId) {
      alert('请先保存为测试用例')
      return
    }

    try {
      const result = await api.testCases.execute(savedTestCaseId)
      if (result.success) {
        alert('测试用例执行成功！\n状态: ' + result.result.status)
      }
    } catch (error) {
      alert('执行失败: ' + error.message)
    }
  }

  return (
    <div className="api-explorer">
      {/* Swagger上传 */}
      <div className="upload-section">
        <input 
          type="file" 
          accept=".json,.yaml,.yml"
          onChange={(e) => handleSwaggerUpload(e.target.files[0])}
        />
      </div>

      {/* API列表 */}
      <div className="api-list">
        {apis.map(apiItem => (
          <div key={apiItem.id} className="api-item">
            <span>{apiItem.method} {apiItem.path}</span>
            <button onClick={() => handleExecuteApi(apiItem)}>
              执行API
            </button>
          </div>
        ))}
      </div>

      {/* 执行结果 */}
      {executionResult && (
        <div className="execution-result">
          <h3>执行结果</h3>
          <p>状态码: {executionResult.status_code}</p>
          <p>响应时间: {executionResult.response_time}ms</p>
          
          <button onClick={handleSaveAsTestCase}>
            保存为测试用例
          </button>
        </div>
      )}

      {/* 测试用例操作 */}
      {savedTestCaseId && (
        <div className="testcase-actions">
          <p>测试用例ID: {savedTestCaseId}</p>
          <button onClick={handleExecuteTestCase}>
            执行测试用例
          </button>
        </div>
      )}

      {/* API执行器弹窗 */}
      {showExecutor && (
        <ApiExecutor
          api={selectedApi}
          onClose={() => setShowExecutor(false)}
          onExecutionComplete={handleExecutionComplete}
        />
      )}
    </div>
  )
}
```

### ApiExecutor.jsx - API执行组件

```jsx
import React, { useState } from 'react'
import api from '@/services/api'

export default function ApiExecutor({ api: apiInfo, onClose, onExecutionComplete }) {
  const [loading, setLoading] = useState(false)
  const [requestData, setRequestData] = useState({})

  const handleExecute = async () => {
    setLoading(true)
    try {
      const result = await api.apis.execute({
        method: apiInfo.method,
        path: apiInfo.path,
        base_url: 'http://localhost:8000', // 可配置
        data: requestData,
        timeout: 30
      })

      // 保存请求数据到结果中
      result.request_data = requestData

      onExecutionComplete(result)
    } catch (error) {
      alert('执行失败: ' + error.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="api-executor-modal">
      <div className="modal-content">
        <h2>执行API: {apiInfo.method} {apiInfo.path}</h2>
        
        <div className="request-params">
          <label>请求参数（JSON）:</label>
          <textarea
            value={JSON.stringify(requestData, null, 2)}
            onChange={(e) => {
              try {
                setRequestData(JSON.parse(e.target.value))
              } catch {}
            }}
            rows={10}
          />
        </div>

        <div className="actions">
          <button onClick={handleExecute} disabled={loading}>
            {loading ? '执行中...' : '执行'}
          </button>
          <button onClick={onClose}>取消</button>
        </div>
      </div>
    </div>
  )
}
```

## 后端接口调用链

### 1. Swagger上传
```python
@app.post("/api/upload/swagger")
async def upload_swagger(file: UploadFile):
    # 1. 读取文件内容
    content = await file.read()
    
    # 2. 解析Swagger
    swagger_data = json.loads(content)
    
    # 3. 提取API列表
    apis = extract_apis_from_swagger(swagger_data)
    
    # 4. 保存到数据库
    apis_db.extend(apis)
    data_manager.set_data("apis", apis_db, save=True)
    
    return {"success": True, "count": len(apis)}
```

### 2. 执行API
```python
@app.post("/api/execute-api")
async def execute_api(request: Dict[str, Any]):
    # 1. 提取参数
    method = request.get('method')
    url = request.get('base_url') + request.get('path')
    data = request.get('data', {})
    
    # 2. 发送HTTP请求
    import requests
    response = requests.request(method, url, json=data, timeout=30)
    
    # 3. 返回结果
    return {
        "success": response.status_code < 400,
        "status_code": response.status_code,
        "response_time": 123,  # ms
        "response_data": response.json()
    }
```

### 3. 保存为测试用例
```python
@app.post("/api/save-api-as-testcase")
async def save_api_as_testcase(request: Dict[str, Any]):
    # 1. 生成测试用例ID
    import time
    test_case_id = f"TC_{int(time.time())}_{len(test_cases_db)}"
    
    # 2. 构建测试用例
    test_case = {
        "id": test_case_id,
        "title": f"{request['api_info']['name']} - {request['api_info']['method']}",
        "execution_config": {
            "method": request['api_info']['method'],
            "url": request['api_info']['path'],
            "data": request['request_data']
        },
        "status": "passed" if request['execution_result']['success'] else "failed"
    }
    
    # 3. 保存到数据库
    test_cases_db.append(test_case)
    data_manager.set_data("test_cases", test_cases_db, save=True)
    
    return {"success": True, "test_case_id": test_case_id}
```

### 4. 执行测试用例
```python
@app.post("/api/testcases/{testcase_id}/execute")
async def execute_test_case(testcase_id: str):
    # 1. 查找测试用例
    testcase = next((tc for tc in test_cases_db if tc['id'] == testcase_id), None)
    if not testcase:
        raise HTTPException(404, "测试用例不存在")
    
    # 2. 提取执行配置
    config = testcase.get('execution_config', {})
    
    # 3. 执行API请求
    import requests
    response = requests.request(
        config['method'],
        config['url'],
        json=config.get('data', {}),
        timeout=30
    )
    
    # 4. 更新测试用例状态
    testcase['status'] = 'passed' if response.status_code < 400 else 'failed'
    testcase['lastRun'] = time.strftime("%Y-%m-%d %H:%M:%S")
    
    # 5. 保存更新
    data_manager.set_data("test_cases", test_cases_db, save=True)
    
    return {
        "success": True,
        "result": {
            "status": testcase['status'],
            "status_code": response.status_code,
            "response_time": 123
        }
    }
```

## 数据流转

```
1. Swagger文件
   ↓
2. API列表 (apis_db)
   ↓
3. 执行结果 (executionResult)
   ↓
4. 测试用例 (test_cases_db)
   ↓
5. 执行结果 (testRunResult)
```

## 测试验证

```bash
# 1. 准备Swagger文件
# 2. 启动服务
cd G:\AI项目\ai测试
.\restart_all.bat

# 3. 访问前端
# http://localhost:5173

# 4. 执行流程
# - 上传Swagger文件
# - 点击"执行API"
# - 点击"保存为测试用例"
# - 点击"执行测试用例"
```

## 关键点

1. **状态管理**: 使用React useState管理流程状态
2. **错误处理**: 每个步骤都有try-catch
3. **用户反馈**: 使用alert提示操作结果
4. **数据持久化**: 所有数据保存到JSON文件
5. **接口统一**: 使用api.js统一管理API调用
