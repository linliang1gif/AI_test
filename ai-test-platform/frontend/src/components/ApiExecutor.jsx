import { useState } from 'react'

/**
 * API执行器组件
 */
function ApiExecutor({ apiInfo, onClose, onSaveAsTestCase }) {
  const [requestData, setRequestData] = useState('')
  const [executing, setExecuting] = useState(false)
  const [result, setResult] = useState(null)
  const [baseUrl, setBaseUrl] = useState('http://localhost:8000')
  const [mockMode, setMockMode] = useState(false)
  const [authToken, setAuthToken] = useState('')
  const [showAdvanced, setShowAdvanced] = useState(false)

  // 初始化请求数据
  const initializeRequestData = () => {
    const data = {}
    
    // 从requestBody提取参数
    if (apiInfo.requestBody && apiInfo.requestBody.schema) {
      const schema = apiInfo.requestBody.schema
      if (schema.properties) {
        Object.keys(schema.properties).forEach(key => {
          const prop = schema.properties[key]
          // 根据类型设置默认值
          if (prop.type === 'string') data[key] = ''
          else if (prop.type === 'integer' || prop.type === 'number') data[key] = 0
          else if (prop.type === 'boolean') data[key] = false
          else if (prop.type === 'array') data[key] = []
          else data[key] = null
        })
      }
    }
    
    setRequestData(JSON.stringify(data, null, 2))
  }

  // 执行API
  const handleExecute = async () => {
    setExecuting(true)
    setResult(null)
    
    try {
      // Mock模式：模拟响应
      if (mockMode) {
        await new Promise(resolve => setTimeout(resolve, 500)) // 模拟延迟
        
        const mockResult = {
          success: true,
          status_code: 200,
          response_time: Math.floor(Math.random() * 500) + 100,
          response_data: {
            success: true,
            message: "Mock响应 - 这是模拟数据",
            data: {
              id: 1,
              name: "测试数据",
              timestamp: new Date().toISOString()
            }
          }
        }
        
        setResult(mockResult)
        setExecuting(false)
        return
      }
      
      // 真实模式：调用实际API
      let parsedData = {}
      if (requestData.trim()) {
        parsedData = JSON.parse(requestData)
      }
      
      const response = await fetch('/api/execute-api', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          base_url: baseUrl,
          method: apiInfo.method,
          path: apiInfo.path,
          data: parsedData,
          timeout: 30,
          auth_token: authToken || null
        })
      })
      
      const resultData = await response.json()
      setResult(resultData)
    } catch (error) {
      setResult({
        success: false,
        error: error.message,
        status_code: 0,
        response_time: 0
      })
    } finally {
      setExecuting(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl w-[800px] max-h-[90vh] overflow-hidden flex flex-col">
        {/* 标题 */}
        <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
          <h3 className="text-lg font-semibold">🚀 执行API测试</h3>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">✕</button>
        </div>

        {/* 内容 */}
        <div className="flex-1 overflow-y-auto p-6 space-y-4">
          {/* API信息 */}
          <div className="p-4 bg-gray-50 rounded-lg">
            <div className="flex items-center space-x-2 mb-2">
              <span className={`px-2 py-1 text-xs font-semibold rounded ${
                apiInfo.method === 'GET' ? 'bg-blue-100 text-blue-700' :
                apiInfo.method === 'POST' ? 'bg-green-100 text-green-700' :
                apiInfo.method === 'PUT' ? 'bg-yellow-100 text-yellow-700' :
                apiInfo.method === 'DELETE' ? 'bg-red-100 text-red-700' :
                'bg-gray-100 text-gray-700'
              }`}>
                {apiInfo.method}
              </span>
              <span className="font-mono text-sm">{apiInfo.path}</span>
            </div>
            <p className="text-sm text-gray-600">{apiInfo.summary || apiInfo.name}</p>
          </div>

          {/* 基础URL */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              基础URL
            </label>
            <input
              type="text"
              value={baseUrl}
              onChange={(e) => setBaseUrl(e.target.value)}
              disabled={mockMode}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100 disabled:text-gray-500"
              placeholder="http://localhost:8000"
            />
          </div>

          {/* Mock模式开关 */}
          <div className="flex items-center space-x-2 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
            <input
              type="checkbox"
              id="mockMode"
              checked={mockMode}
              onChange={(e) => setMockMode(e.target.checked)}
              className="w-4 h-4 text-blue-600 rounded focus:ring-2 focus:ring-blue-500"
            />
            <label htmlFor="mockMode" className="text-sm text-gray-700 cursor-pointer">
              🎭 Mock模式（模拟响应，不调用真实API）
            </label>
          </div>

          {/* 高级选项 */}
          <div>
            <button
              onClick={() => setShowAdvanced(!showAdvanced)}
              className="text-sm text-blue-600 hover:text-blue-700 flex items-center space-x-1"
            >
              <span>{showAdvanced ? '▼' : '▶'}</span>
              <span>高级选项</span>
            </button>
            
            {showAdvanced && (
              <div className="mt-3 space-y-3 p-3 bg-gray-50 rounded-lg">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    认证Token（可选）
                  </label>
                  <input
                    type="text"
                    value={authToken}
                    onChange={(e) => setAuthToken(e.target.value)}
                    placeholder="Bearer token 或 API Key"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    如果API需要认证，在这里填写Token
                  </p>
                </div>
              </div>
            )}
          </div>

          {/* 请求参数 */}
          {(apiInfo.method === 'POST' || apiInfo.method === 'PUT') && (
            <div>
              <div className="flex items-center justify-between mb-2">
                <label className="block text-sm font-medium text-gray-700">
                  请求参数 (JSON)
                </label>
                <button
                  onClick={initializeRequestData}
                  className="text-xs text-blue-600 hover:text-blue-700"
                >
                  初始化参数
                </button>
              </div>
              <textarea
                value={requestData}
                onChange={(e) => setRequestData(e.target.value)}
                className="w-full h-40 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono text-sm"
                placeholder='{"key": "value"}'
              />
            </div>
          )}

          {/* 执行结果 */}
          {result && (
            <div className="border-t pt-4">
              <h4 className="text-sm font-medium text-gray-700 mb-3">执行结果</h4>
              
              {/* 状态信息 */}
              <div className="grid grid-cols-3 gap-3 mb-3">
                <div className="p-3 bg-gray-50 rounded">
                  <div className="text-xs text-gray-500">状态码</div>
                  <div className={`text-lg font-semibold ${
                    result.status_code >= 200 && result.status_code < 300 ? 'text-green-600' :
                    result.status_code >= 400 ? 'text-red-600' : 'text-gray-600'
                  }`}>
                    {result.status_code || 'N/A'}
                  </div>
                </div>
                <div className="p-3 bg-gray-50 rounded">
                  <div className="text-xs text-gray-500">响应时间</div>
                  <div className="text-lg font-semibold text-blue-600">
                    {result.response_time ? `${result.response_time}ms` : 'N/A'}
                  </div>
                </div>
                <div className="p-3 bg-gray-50 rounded">
                  <div className="text-xs text-gray-500">结果</div>
                  <div className={`text-lg font-semibold ${
                    result.success ? 'text-green-600' : 'text-red-600'
                  }`}>
                    {result.success ? '✅ 成功' : '❌ 失败'}
                  </div>
                </div>
              </div>

              {/* 响应数据 */}
              {result.response_data && (
                <div>
                  <div className="text-xs text-gray-500 mb-1">响应数据:</div>
                  <pre className="p-3 bg-gray-900 text-green-400 rounded-lg text-xs overflow-x-auto max-h-60">
                    {JSON.stringify(result.response_data, null, 2)}
                  </pre>
                </div>
              )}

              {/* 错误信息 */}
              {result.error && (
                <div className="p-3 bg-red-50 border border-red-200 rounded text-sm text-red-700">
                  {result.error}
                </div>
              )}
            </div>
          )}
        </div>

        {/* 底部按钮 */}
        <div className="px-6 py-4 border-t border-gray-200 flex items-center justify-end space-x-3">
          <button
            onClick={onClose}
            className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
          >
            关闭
          </button>
          {result && result.success && onSaveAsTestCase && (
            <button
              onClick={() => onSaveAsTestCase(result, JSON.parse(requestData || '{}'))}
              className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700"
            >
              💾 保存为测试用例
            </button>
          )}
          <button
            onClick={handleExecute}
            disabled={executing}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 flex items-center space-x-2"
          >
            {executing ? (
              <>
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                <span>执行中...</span>
              </>
            ) : (
              <>
                <span>▶️</span>
                <span>执行</span>
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  )
}

export default ApiExecutor
