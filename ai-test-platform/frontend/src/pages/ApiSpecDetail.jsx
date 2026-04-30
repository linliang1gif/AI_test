import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useToast } from '../components/ui/Toast'

function ApiSpecDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const toast = useToast()
  const [apiSpec, setApiSpec] = useState(null)
  const [apis, setApis] = useState([])
  const [loading, setLoading] = useState(true)
  const [searchTerm, setSearchTerm] = useState('')
  const [filterMethod, setFilterMethod] = useState('all')

  useEffect(() => {
    loadApiSpec()
  }, [id])

  const loadApiSpec = async () => {
    setLoading(true)
    try {
      // 读取API规范的基本信息
      const response = await fetch(`/api/v2/swagger/api-specs/${id}`)
      if (!response.ok) throw new Error('加载失败')
      
      const spec = await response.json()
      setApiSpec(spec)

      // 读取OpenAPI文件内容
      const contentResponse = await fetch(`/api/v2/swagger/api-specs/${id}/content`)
      if (contentResponse.ok) {
        const openApiData = await contentResponse.json()
        parseOpenApiSpec(openApiData)
      } else {
        toast.error('无法加载OpenAPI文件内容')
      }
    } catch (error) {
      console.error('加载API规范失败:', error)
      toast.error('加载失败: ' + error.message)
    } finally {
      setLoading(false)
    }
  }

  const parseOpenApiSpec = (openApiData) => {
    const apiList = []
    
    // 检查数据格式
    if (!openApiData || typeof openApiData !== 'object') {
      console.error('Invalid OpenAPI data:', openApiData)
      toast.error('OpenAPI数据格式错误')
      return
    }

    const paths = openApiData.paths || {}

    Object.keys(paths).forEach(path => {
      const pathItem = paths[path]
      
      if (!pathItem || typeof pathItem !== 'object') {
        console.warn(`Invalid path item for ${path}:`, pathItem)
        return
      }
      
      // 遍历每个HTTP方法
      ['get', 'post', 'put', 'delete', 'patch', 'options', 'head'].forEach(method => {
        if (pathItem[method]) {
          const operation = pathItem[method]
          
          if (!operation || typeof operation !== 'object') {
            console.warn(`Invalid operation for ${method} ${path}:`, operation)
            return
          }
          
          apiList.push({
            path: path,
            method: method.toUpperCase(),
            summary: operation.summary || operation.operationId || path,
            description: operation.description || '',
            tags: Array.isArray(operation.tags) ? operation.tags : [],
            operationId: operation.operationId || '',
            parameters: Array.isArray(operation.parameters) ? operation.parameters : [],
            requestBody: operation.requestBody || null,
            responses: operation.responses || {}
          })
        }
      })
    })

    console.log(`Parsed ${apiList.length} APIs from OpenAPI spec`)
    setApis(apiList)
  }

  const getMethodBadge = (method) => {
    const methodConfig = {
      GET: { bg: 'bg-blue-100', text: 'text-blue-700', border: 'border-blue-300' },
      POST: { bg: 'bg-green-100', text: 'text-green-700', border: 'border-green-300' },
      PUT: { bg: 'bg-yellow-100', text: 'text-yellow-700', border: 'border-yellow-300' },
      DELETE: { bg: 'bg-red-100', text: 'text-red-700', border: 'border-red-300' },
      PATCH: { bg: 'bg-purple-100', text: 'text-purple-700', border: 'border-purple-300' }
    }
    const config = methodConfig[method] || methodConfig.GET
    return (
      <span className={`px-3 py-1 text-xs font-bold rounded border ${config.bg} ${config.text} ${config.border}`}>
        {method}
      </span>
    )
  }

  const filteredApis = apis.filter(api => {
    const matchesSearch = searchTerm === '' || 
      api.path.toLowerCase().includes(searchTerm.toLowerCase()) ||
      api.summary.toLowerCase().includes(searchTerm.toLowerCase()) ||
      api.description.toLowerCase().includes(searchTerm.toLowerCase())
    
    const matchesMethod = filterMethod === 'all' || api.method === filterMethod
    
    return matchesSearch && matchesMethod
  })

  if (loading) {
    return (
      <div className="p-6">
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-gray-200 rounded w-1/4"></div>
          <div className="h-32 bg-gray-200 rounded"></div>
        </div>
      </div>
    )
  }

  if (!apiSpec) {
    return (
      <div className="p-6">
        <div className="text-center text-gray-500">
          <p>API规范不存在</p>
          <button
            onClick={() => navigate('/api-specs')}
            className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            返回列表
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="p-6 space-y-6">
      {/* 头部 */}
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center space-x-3">
            <button
              onClick={() => navigate('/api-specs')}
              className="text-gray-600 hover:text-gray-900"
            >
              ← 返回
            </button>
            <h1 className="text-3xl font-bold text-gray-900">API规范详情</h1>
          </div>
          <div className="mt-2 flex items-center space-x-4 text-sm text-gray-600">
            <span>规范ID: {apiSpec.id}</span>
            {apiSpec.version && <span>版本: {apiSpec.version}</span>}
            <span>API数量: {apis.length}</span>
            <span>导入时间: {new Date(apiSpec.imported_at).toLocaleString('zh-CN')}</span>
          </div>
        </div>
      </div>

      {/* 搜索和筛选 */}
      <div className="bg-white rounded-lg shadow p-4">
        <div className="flex items-center space-x-4">
          <div className="flex-1">
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="搜索API路径、名称或描述..."
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <select
            value={filterMethod}
            onChange={(e) => setFilterMethod(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="all">全部方法</option>
            <option value="GET">GET</option>
            <option value="POST">POST</option>
            <option value="PUT">PUT</option>
            <option value="DELETE">DELETE</option>
            <option value="PATCH">PATCH</option>
          </select>
        </div>
        <div className="mt-2 text-sm text-gray-600">
          显示 {filteredApis.length} / {apis.length} 个API
        </div>
      </div>

      {/* API列表 */}
      <div className="bg-white rounded-lg shadow">
        <div className="p-6 border-b border-gray-200">
          <h2 className="text-xl font-semibold">API列表</h2>
        </div>

        <div className="divide-y divide-gray-200">
          {filteredApis.length === 0 ? (
            <div className="p-8 text-center text-gray-500">
              <div className="text-4xl mb-2">🔍</div>
              <p>没有找到匹配的API</p>
            </div>
          ) : (
            filteredApis.map((api, index) => (
              <div key={index} className="p-6 hover:bg-gray-50 transition-colors">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center space-x-3 mb-2">
                      {getMethodBadge(api.method)}
                      <span className="font-mono text-sm text-gray-700">{api.path}</span>
                    </div>
                    <p className="text-gray-900 font-medium mb-1">{api.summary}</p>
                    {api.description && (
                      <p className="text-sm text-gray-600 mb-2">{api.description}</p>
                    )}
                    {api.tags && api.tags.length > 0 && (
                      <div className="flex items-center space-x-2">
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
                      onClick={() => {
                        const apiText = `${api.method} ${api.path}\n${api.summary}`;
                        navigator.clipboard.writeText(apiText).then(() => toast.success('已复制'));
                      }}
                      className="px-3 py-1.5 text-sm bg-gray-50 text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
                      title="复制API信息"
                    >
                      复制
                    </button>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  )
}

export default ApiSpecDetail
