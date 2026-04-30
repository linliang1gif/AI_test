import { useState, useEffect } from 'react'
import { apisAPI } from '../services/api'
import TestDataGenerator from '../components/TestDataGenerator'
import ApiExecutor from '../components/ApiExecutor'

function ApiExplorer() {
  const [swaggerUrl, setSwaggerUrl] = useState('')
  const [apis, setApis] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [uploadMode, setUploadMode] = useState('url') // 'url' or 'file'
  const [showDataGenerator, setShowDataGenerator] = useState(false)
  const [showApiExecutor, setShowApiExecutor] = useState(false)
  const [selectedApi, setSelectedApi] = useState(null)
  const [testData, setTestData] = useState({})
  const [kbQuery, setKbQuery] = useState('')
  const [kbMethods, setKbMethods] = useState('GET')
  const [kbTags, setKbTags] = useState('')
  const [kbRunning, setKbRunning] = useState(false)
  const [kbResult, setKbResult] = useState(null)

  useEffect(() => {
    loadApis()
  }, [])

  const loadApis = () => {
    setLoading(true)
    apisAPI.getAll()
      .then(data => setApis(data.apis || []))
      .catch(err => setError(err.message))
      .finally(() => setLoading(false))
  }

  const handleParseSwagger = () => {
    if (!swaggerUrl.trim()) {
      alert('请输入Swagger URL')
      return
    }
    
    setLoading(true)
    apisAPI.parseSwagger(swaggerUrl)
      .then(() => {
        alert('Swagger解析成功')
        loadApis()
      })
      .catch(err => alert('解析失败: ' + err.message))
      .finally(() => setLoading(false))
  }

  const handleFileUpload = (e) => {
    const file = e.target.files[0]
    if (!file) return

    // 检查文件类型
    const validTypes = ['application/json', 'text/yaml', 'application/x-yaml', 'text/x-yaml']
    const validExtensions = ['.json', '.yaml', '.yml']
    const fileExtension = file.name.toLowerCase().slice(file.name.lastIndexOf('.'))
    
    if (!validTypes.includes(file.type) && !validExtensions.includes(fileExtension)) {
      alert('请上传JSON或YAML格式的Swagger文件')
      return
    }

    setLoading(true)
    api.swagger.upload(file)
      .then(data => {
        if (data.success) {
          alert(`成功解析 ${data.count || 0} 个API接口`)
          loadApis()
        } else {
          throw new Error(data.message || '解析失败')
        }
      })
      .catch(err => alert('上传失败: ' + err.message))
      .finally(() => {
        setLoading(false)
        e.target.value = '' // 清空文件选择
      })
  }

  const getMethodBadge = (method) => {
    const methodConfig = {
      GET: { bg: 'bg-blue-100', text: 'text-blue-700' },
      POST: { bg: 'bg-green-100', text: 'text-green-700' },
      PUT: { bg: 'bg-yellow-100', text: 'text-yellow-700' },
      DELETE: { bg: 'bg-red-100', text: 'text-red-700' },
      PATCH: { bg: 'bg-purple-100', text: 'text-purple-700' }
    }
    const config = methodConfig[method] || methodConfig.GET
    return (
      <span className={`px-2 py-1 text-xs font-semibold rounded ${config.bg} ${config.text}`}>
        {method}
      </span>
    )
  }

  // 打开测试数据生成器
  const handleGenerateTestData = (api) => {
    setSelectedApi(api)
    setShowDataGenerator(true)
  }

  // 打开API执行器
  const handleExecuteApi = (api) => {
    setSelectedApi(api)
    setShowApiExecutor(true)
  }

  // 保存执行结果为测试用例
  const handleSaveAsTestCase = async (executionResult, requestData) => {
    try {
      const result = await api.apis.saveAsTestCase({
        api_info: selectedApi,
        execution_result: executionResult,
        request_data: requestData
      })
      
      if (result.success) {
        alert(`✅ 测试用例保存成功！\n用例ID: ${result.test_case_id}\n\n可以在"测试用例"页面查看`)
        setShowApiExecutor(false)
      } else {
        alert(`❌ 保存失败: ${result.error}`)
      }
    } catch (error) {
      alert(`❌ 保存失败: ${error.message}`)
    }
  }

  // 使用生成的数据
  const handleDataGenerated = (data) => {
    setTestData(prev => ({
      ...prev,
      [selectedApi.id]: data
    }))
    alert('测试数据已生成!可以在API测试中使用')
  }

  const handleRunKbSmoke = async () => {
    if (!kbQuery.trim()) {
      alert('请输入知识库关键词')
      return
    }

    setKbRunning(true)
    setKbResult(null)
    try {
      const methods = kbMethods
        .split(',')
        .map(m => m.trim().toUpperCase())
        .filter(Boolean)
      const include_tags = kbTags
        .split(',')
        .map(t => t.trim())
        .filter(Boolean)

      const data = await apisAPI.smokeRunFromKb({
        query: kbQuery,
        top_k: 30,
        limit: 20,
        methods,
        include_tags,
        allow_unsafe: false,
        verify_ssl: false
      })
      setKbResult(data)
    } catch (err) {
      alert('知识库冒烟执行失败: ' + err.message)
    } finally {
      setKbRunning(false)
    }
  }

  if (loading && apis.length === 0) {
    return (
      <div className="p-6">
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-gray-200 rounded w-1/4"></div>
          <div className="h-32 bg-gray-200 rounded"></div>
        </div>
      </div>
    )
  }

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">🌐 API管理</h1>
        <p className="text-gray-600 mt-2">管理和测试API接口</p>
      </div>

      {error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
          {error}
        </div>
      )}

      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold mb-4">知识库关键词冒烟（SIT）</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mb-3">
          <input
            type="text"
            value={kbQuery}
            onChange={(e) => setKbQuery(e.target.value)}
            placeholder="关键词（例如：币别、支付、订单）"
            className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <input
            type="text"
            value={kbMethods}
            onChange={(e) => setKbMethods(e.target.value)}
            placeholder="方法（逗号分隔，如 GET,POST）"
            className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <input
            type="text"
            value={kbTags}
            onChange={(e) => setKbTags(e.target.value)}
            placeholder="标签（逗号分隔，可选）"
            className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
        <div className="flex items-center justify-between">
          <div className="text-xs text-gray-500">默认：top_k=30，limit=20，仅安全模式（不执行写操作）</div>
          <button
            onClick={handleRunKbSmoke}
            disabled={kbRunning}
            className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50"
          >
            {kbRunning ? '执行中...' : '执行知识库冒烟'}
          </button>
        </div>

        {kbResult && (
          <div className="mt-4 p-4 bg-gray-50 rounded-lg border border-gray-200">
            <div className="text-sm font-medium mb-2">执行结果</div>
            <div className="grid grid-cols-2 md:grid-cols-5 gap-2 text-sm">
              <div>命中: <b>{kbResult.kb?.matched || 0}</b></div>
              <div>已选: <b>{kbResult.kb?.selected || 0}</b></div>
              <div>通过: <b className="text-green-700">{kbResult.summary?.passed || 0}</b></div>
              <div>失败: <b className="text-red-700">{kbResult.summary?.failed || 0}</b></div>
              <div>跳过: <b className="text-yellow-700">{kbResult.summary?.skipped || 0}</b></div>
            </div>
          </div>
        )}
      </div>

      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold mb-4">导入Swagger文档</h2>
        
        {/* 切换按钮 */}
        <div className="flex space-x-2 mb-4">
          <button
            onClick={() => setUploadMode('url')}
            className={`px-4 py-2 rounded-lg transition-colors ${
              uploadMode === 'url' 
                ? 'bg-blue-600 text-white' 
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
             URL导入
          </button>
          <button
            onClick={() => setUploadMode('file')}
            className={`px-4 py-2 rounded-lg transition-colors ${
              uploadMode === 'file' 
                ? 'bg-blue-600 text-white' 
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
             文件上传
          </button>
        </div>

        {/* URL导入 */}
        {uploadMode === 'url' && (
          <div className="flex space-x-4">
            <input
              type="text"
              value={swaggerUrl}
              onChange={(e) => setSwaggerUrl(e.target.value)}
              placeholder="输入Swagger URL (如: https://api.example.com/swagger.json)"
              className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <button
              onClick={handleParseSwagger}
              disabled={loading}
              className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
            >
              {loading ? '解析中...' : '解析'}
            </button>
          </div>
        )}

        {/* 文件上传 */}
        {uploadMode === 'file' && (
          <div className="space-y-3">
            <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center hover:border-blue-500 transition-colors">
              <input
                type="file"
                id="swagger-file"
                accept=".json,.yaml,.yml"
                onChange={handleFileUpload}
                className="hidden"
                disabled={loading}
              />
              <label htmlFor="swagger-file" className="cursor-pointer">
                <div className="text-4xl mb-2"></div>
                <p className="text-gray-700 font-medium mb-1">
                  点击选择或拖拽文件到此处
                </p>
                <p className="text-sm text-gray-500">
                  支持 JSON、YAML 格式的 Swagger/OpenAPI 文档
                </p>
              </label>
            </div>
            <div className="text-xs text-gray-500">
               提示: 支持 Swagger 2.0 和 OpenAPI 3.0 规范
            </div>
          </div>
        )}
      </div>

      <div className="bg-white rounded-lg shadow">
        <div className="p-6 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-semibold">API列表</h2>
            <div className="text-sm text-gray-600">
              共 {apis.length} 个接口
            </div>
          </div>
        </div>

        <div className="divide-y divide-gray-200">
          {apis.length === 0 ? (
            <div className="p-8 text-center text-gray-500">
              <div className="text-4xl mb-2"></div>
              <p>暂无API接口</p>
              <p className="text-sm mt-1">请导入Swagger文档</p>
            </div>
          ) : (
            apis.map((api, index) => (
              <div key={index} className="p-6 hover:bg-gray-50 transition-colors">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center space-x-3 mb-2">
                      {getMethodBadge(api.method)}
                      <span className="font-mono text-sm text-gray-700">{api.path}</span>
                    </div>
                    <p className="text-gray-900 font-medium mb-1">{api.summary || api.name}</p>
                    {api.description && (
                      <p className="text-sm text-gray-600">{api.description}</p>
                    )}
                    {api.tags && api.tags.length > 0 && (
                      <div className="flex items-center space-x-2 mt-2">
                        {api.tags.map((tag, i) => (
                          <span key={i} className="px-2 py-1 text-xs bg-gray-100 text-gray-600 rounded">
                            {tag}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                  <div className="flex items-center space-x-2 ml-4">
                    <button 
                      onClick={() => handleGenerateTestData(api)}
                      className="px-3 py-1.5 text-sm bg-purple-50 text-purple-700 hover:bg-purple-100 rounded-lg transition-colors flex items-center space-x-1"
                      title="生成测试数据"
                    >
                      <span></span>
                      <span>测试数据</span>
                    </button>
                    <button 
                      onClick={() => handleExecuteApi(api)}
                      className="p-2 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded"
                      title="执行API测试"
                    >
                      
                    </button>
                    <button 
                      onClick={() => {
                        const apiText = `${api.method} ${api.path}\n${api.summary || api.name}`;
                        navigator.clipboard.writeText(apiText).then(() => alert('已复制到剪贴板'));
                      }}
                      className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-50 rounded"
                      title="复制API信息"
                    >
                      
                    </button>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {/* 测试数据生成器对话框 */}
      {showDataGenerator && selectedApi && (
        <TestDataGenerator
          apiInfo={selectedApi}
          onDataGenerated={handleDataGenerated}
          onClose={() => setShowDataGenerator(false)}
        />
      )}

      {/* API执行器对话框 */}
      {showApiExecutor && selectedApi && (
        <ApiExecutor
          apiInfo={selectedApi}
          onClose={() => setShowApiExecutor(false)}
          onSaveAsTestCase={handleSaveAsTestCase}
        />
      )}
    </div>
  )
}

export default ApiExplorer