import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Upload, Download, Search, Grid, List, FileUp, Link as LinkIcon } from 'lucide-react'
import api from '../services/api'
import { projectsAPI } from '../services/api'
import { useToast } from '../components/ui/Toast'
import { SkeletonCard } from '../components/ui/Skeleton'
import FilterPanel from '../components/FilterPanel'
import ApiCard from '../components/ApiCard'
import EmptyState from '../components/EmptyState'
import TestDataGenerator from '../components/TestDataGenerator'
import ApiExecutor from '../components/ApiExecutor'

export default function ApiExplorerPro() {
  const navigate = useNavigate()
  const toast = useToast()
  
  // 状态管理
  const [apis, setApis] = useState([])
  const [loading, setLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState('')
  const [viewMode, setViewMode] = useState('grid')
  const [selectedIds, setSelectedIds] = useState([])
  const [projects, setProjects] = useState([])
  const [selectedProjectId, setSelectedProjectId] = useState('')
  const [selectedEnvironmentId, setSelectedEnvironmentId] = useState('')
  
  // 筛选状态
  const [filters, setFilters] = useState({
    method: 'all',
    tag: '',
    path: ''
  })
  
  // 对话框状态
  const [showUploadDialog, setShowUploadDialog] = useState(false)
  const [uploadMode, setUploadMode] = useState('url') // 'url' or 'file'
  const [swaggerUrl, setSwaggerUrl] = useState('')
  const [uploading, setUploading] = useState(false)
  
  // API操作对话框
  const [showDataGenerator, setShowDataGenerator] = useState(false)
  const [showApiExecutor, setShowApiExecutor] = useState(false)
  const [selectedApi, setSelectedApi] = useState(null)

  useEffect(() => {
    loadProjects()
  }, [])

  useEffect(() => {
    if (selectedProjectId) {
      loadApis(selectedProjectId)
    }
  }, [selectedProjectId])

  const loadProjects = async () => {
    try {
      const data = await projectsAPI.getAll()
      const items = data.projects || []
      setProjects(items)
      if (items.length > 0) {
        const firstProject = items[0]
        setSelectedProjectId(String(firstProject.id))
        setSelectedEnvironmentId(String(firstProject.default_environment_id || ''))
      }
      if (items.length === 0) setLoading(false)
    } catch (error) {
      console.error(error)
      toast.error('加载项目失败')
      setLoading(false)
    }
  }

  const loadApis = async (projectId = selectedProjectId) => {
    setLoading(true)
    try {
      const data = await api.apis.getAll(projectId)
      setApis(data.apis || [])
    } catch (error) {
      console.error('加载失败:', error)
      toast.error('加载API列表失败')
    } finally {
      setLoading(false)
    }
  }

  // 筛选和搜索
  const filteredApis = apis.filter(api => {
    // 搜索过滤
    if (searchQuery) {
      const query = searchQuery.toLowerCase()
      const matchName = api.name?.toLowerCase().includes(query)
      const matchSummary = api.summary?.toLowerCase().includes(query)
      const matchPath = api.path?.toLowerCase().includes(query)
      if (!matchName && !matchSummary && !matchPath) return false
    }
    
    // 方法过滤
    if (filters.method !== 'all' && api.method !== filters.method) {
      return false
    }
    
    // 标签过滤
    if (filters.tag && !api.tags?.some(t => t.toLowerCase().includes(filters.tag.toLowerCase()))) {
      return false
    }
    
    // 路径过滤
    if (filters.path && !api.path?.toLowerCase().includes(filters.path.toLowerCase())) {
      return false
    }
    
    return true
  })

  // 选择操作
  const handleSelectAll = () => {
    if (selectedIds.length === filteredApis.length) {
      setSelectedIds([])
    } else {
      setSelectedIds(filteredApis.map(api => api.id))
    }
  }

  const handleSelectOne = (id) => {
    setSelectedIds(prev =>
      prev.includes(id) ? prev.filter(i => i !== id) : [...prev, id]
    )
  }

  // URL导入
  const handleParseSwagger = async () => {
    if (!selectedProjectId || !selectedEnvironmentId) {
      toast.warning('请先选择项目和环境')
      return
    }
    if (!swaggerUrl.trim()) {
      toast.warning('请输入Swagger URL')
      return
    }
    
    setUploading(true)
    try {
      await api.apis.importFromUrl({
        project_id: Number(selectedProjectId),
        environment_id: Number(selectedEnvironmentId),
        url: swaggerUrl,
      })
      await api.apis.generateCases({ project_id: Number(selectedProjectId) })
      toast.success('Swagger 导入并生成基础测试用例成功')
      setShowUploadDialog(false)
      setSwaggerUrl('')
      loadApis(selectedProjectId)
    } catch (error) {
      toast.error('解析失败: ' + error.message)
    } finally {
      setUploading(false)
    }
  }

  // 文件上传
  const handleFileUpload = async (e) => {
    const file = e.target.files[0]
    if (!file) return
    if (!selectedProjectId || !selectedEnvironmentId) {
      toast.warning('请先选择项目和环境')
      return
    }

    const validExtensions = ['.json', '.yaml', '.yml']
    const fileExtension = file.name.toLowerCase().slice(file.name.lastIndexOf('.'))
    
    if (!validExtensions.includes(fileExtension)) {
      toast.error('请上传JSON或YAML格式的Swagger文件')
      return
    }

    setUploading(true)

    try {
      const data = await api.apis.importFromFile({
        projectId: Number(selectedProjectId),
        environmentId: Number(selectedEnvironmentId),
        file,
      })
      
      if (data.success) {
        await api.apis.generateCases({ project_id: Number(selectedProjectId) })
        toast.success(`成功解析 ${data.count || 0} 个API接口`)
        setShowUploadDialog(false)
        loadApis(selectedProjectId)
      } else {
        throw new Error(data.message || '解析失败')
      }
    } catch (error) {
      toast.error('上传失败: ' + error.message)
    } finally {
      setUploading(false)
      e.target.value = ''
    }
  }

  // 导出
  const handleExport = () => {
    const dataStr = JSON.stringify(apis, null, 2)
    const blob = new Blob([dataStr], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `apis_${new Date().toISOString().slice(0,10)}.json`
    a.click()
    URL.revokeObjectURL(url)
    toast.success('导出成功')
  }

  // API操作
  const handleViewApi = (api) => {
    navigate(`/api-explorer/${api.id}`)
  }

  const handleExecuteApi = (api) => {
    setSelectedApi(api)
    setShowApiExecutor(true)
  }

  const handleGenerateData = (api) => {
    setSelectedApi(api)
    setShowDataGenerator(true)
  }

  const handleCopyApi = (api) => {
    const apiText = `${api.method} ${api.path}\n${api.summary || api.name}`
    navigator.clipboard.writeText(apiText)
    toast.success('已复制到剪贴板')
  }

  const handleDataGenerated = (data) => {
    toast.success('测试数据已生成')
    setShowDataGenerator(false)
  }

  const handleSaveAsTestCase = async (executionResult, requestData) => {
    try {
      const result = await api.apis.saveAsTestCase({
        api_info: selectedApi,
        execution_result: executionResult,
        request_data: requestData
      })
      
      if (result.success) {
        toast.success(`测试用例保存成功！ID: ${result.test_case_id}`)
        setShowApiExecutor(false)
      } else {
        toast.error('保存失败: ' + result.error)
      }
    } catch (error) {
      toast.error('保存失败: ' + error.message)
    }
  }

  // 重置筛选
  const handleResetFilters = () => {
    setFilters({
      method: 'all',
      tag: '',
      path: ''
    })
  }

  // 自定义筛选面板
  const ApiFilterPanel = () => (
    <div className="bg-white rounded-md border border-slate-200 p-4 sm:p-6">
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-2">
            请求方法
          </label>
          <select
            value={filters.method}
            onChange={(e) => setFilters(prev => ({ ...prev, method: e.target.value }))}
            className="w-full px-3 py-2 border border-slate-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="all">全部</option>
            <option value="GET">GET</option>
            <option value="POST">POST</option>
            <option value="PUT">PUT</option>
            <option value="DELETE">DELETE</option>
            <option value="PATCH">PATCH</option>
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-slate-700 mb-2">
            标签
          </label>
          <input
            type="text"
            value={filters.tag}
            onChange={(e) => setFilters(prev => ({ ...prev, tag: e.target.value }))}
            placeholder="输入标签名称"
            className="w-full px-3 py-2 border border-slate-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-slate-700 mb-2">
            路径
          </label>
          <input
            type="text"
            value={filters.path}
            onChange={(e) => setFilters(prev => ({ ...prev, path: e.target.value }))}
            placeholder="输入路径关键词"
            className="w-full px-3 py-2 border border-slate-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
      </div>

      {(filters.method !== 'all' || filters.tag || filters.path) && (
        <div className="mt-4 pt-4 border-t border-slate-200 flex justify-end">
          <button
            onClick={handleResetFilters}
            className="px-4 py-2 text-sm text-slate-600 hover:text-slate-900"
          >
            重置筛选
          </button>
        </div>
      )}
    </div>
  )

  return (
    <div className="min-h-screen bg-slate-50">
      {/* 页面头部 */}
      <div className="bg-white border-b border-slate-200">
        <div className="max-w-[1400px] mx-auto px-4 sm:px-6 py-6">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            <div>
              <h1 className="text-2xl sm:text-3xl font-bold text-slate-900">API管理</h1>
              <p className="text-slate-600 mt-1">管理和测试API接口</p>
            </div>
            
            <div className="flex flex-wrap items-center gap-3">
              <button
                onClick={handleExport}
                className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 flex items-center space-x-2 transition-colors"
              >
                <Download className="w-4 h-4" />
                <span className="hidden sm:inline">导出</span>
              </button>
              <button
                onClick={() => setShowUploadDialog(true)}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 flex items-center space-x-2 transition-colors"
              >
                <Upload className="w-4 h-4" />
                <span className="hidden sm:inline">导入Swagger</span>
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* 主内容区 */}
      <div className="max-w-[1400px] mx-auto px-4 sm:px-6 py-6 space-y-6">
        {/* 搜索和视图切换 */}
        <div className="flex flex-col sm:flex-row gap-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <select
              value={selectedProjectId}
              onChange={(e) => {
                const project = projects.find(item => String(item.id) === e.target.value)
                setSelectedProjectId(e.target.value)
                setSelectedEnvironmentId(String(project?.default_environment_id || ''))
              }}
              className="px-3 py-2 border border-slate-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">选择项目</option>
              {projects.map(project => (
                <option key={project.id} value={project.id}>{project.name}</option>
              ))}
            </select>
            <select
              value={selectedEnvironmentId}
              onChange={(e) => setSelectedEnvironmentId(e.target.value)}
              className="px-3 py-2 border border-slate-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">选择环境</option>
              {(projects.find(item => String(item.id) === selectedProjectId)?.environments || []).map(environment => (
                <option key={environment.id} value={environment.id}>
                  {environment.name} ({environment.environment_type})
                </option>
              ))}
            </select>
          </div>
        </div>

        <div className="flex flex-col sm:flex-row gap-4">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-slate-400" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="搜索API（名称、路径、描述）..."
              className="w-full pl-10 pr-4 py-2 border border-slate-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          
          <div className="flex items-center space-x-2">
            <div className="flex border border-slate-300 rounded-md overflow-hidden">
              <button
                onClick={() => setViewMode('grid')}
                className={`px-3 py-2 ${viewMode === 'grid' ? 'bg-blue-50 text-blue-600' : 'bg-white text-slate-600 hover:bg-slate-50'}`}
              >
                <Grid className="w-5 h-5" />
              </button>
              <button
                onClick={() => setViewMode('list')}
                className={`px-3 py-2 border-l border-slate-300 ${viewMode === 'list' ? 'bg-blue-50 text-blue-600' : 'bg-white text-slate-600 hover:bg-slate-50'}`}
              >
                <List className="w-5 h-5" />
              </button>
            </div>
          </div>
        </div>

        {/* 筛选面板 */}
        <ApiFilterPanel />

        {/* API列表 */}
        {loading ? (
          <div className={`grid gap-4 ${viewMode === 'grid' ? 'grid-cols-1 md:grid-cols-2 lg:grid-cols-3' : 'grid-cols-1'}`}>
            {[1, 2, 3, 4, 5, 6].map(i => (
              <SkeletonCard key={i} />
            ))}
          </div>
        ) : filteredApis.length === 0 ? (
          <EmptyState
            title={searchQuery || Object.values(filters).some(v => v && v !== 'all') ? '未找到匹配的API' : '暂无API接口'}
            description={searchQuery || Object.values(filters).some(v => v && v !== 'all') ? '尝试调整搜索条件或筛选器' : '点击"导入Swagger"开始导入API'}
            action={
              !searchQuery && !Object.values(filters).some(v => v && v !== 'all') && (
                <button
                  onClick={() => setShowUploadDialog(true)}
                  className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
                >
                  导入Swagger文档
                </button>
              )
            }
          />
        ) : (
          <div className={`grid gap-4 ${viewMode === 'grid' ? 'grid-cols-1 md:grid-cols-2 lg:grid-cols-3' : 'grid-cols-1'}`}>
            {filteredApis.map(api => (
              <ApiCard
                key={api.id || api.path}
                api={api}
                isSelected={selectedIds.includes(api.id)}
                onSelect={handleSelectOne}
                onView={handleViewApi}
                onExecute={handleExecuteApi}
                onGenerateData={handleGenerateData}
                onCopy={handleCopyApi}
              />
            ))}
          </div>
        )}

        {/* 结果统计 */}
        {!loading && filteredApis.length > 0 && (
          <div className="text-center text-sm text-slate-600">
            显示 {filteredApis.length} / {apis.length} 个API接口
          </div>
        )}
      </div>

      {/* 上传对话框 */}
      {showUploadDialog && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl p-6 w-full max-w-2xl">
            <h2 className="text-xl font-bold mb-4">导入Swagger文档</h2>
            
            {/* 切换按钮 */}
            <div className="flex space-x-2 mb-4">
              <button
                onClick={() => setUploadMode('url')}
                className={`flex-1 px-4 py-2 rounded-md transition-colors flex items-center justify-center space-x-2 ${
                  uploadMode === 'url' 
                    ? 'bg-blue-600 text-white' 
                    : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
                }`}
              >
                <LinkIcon className="w-4 h-4" />
                <span>URL导入</span>
              </button>
              <button
                onClick={() => setUploadMode('file')}
                className={`flex-1 px-4 py-2 rounded-md transition-colors flex items-center justify-center space-x-2 ${
                  uploadMode === 'file' 
                    ? 'bg-blue-600 text-white' 
                    : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
                }`}
              >
                <FileUp className="w-4 h-4" />
                <span>文件上传</span>
              </button>
            </div>

            {/* URL导入 */}
            {uploadMode === 'url' && (
              <div className="space-y-4">
                <input
                  type="text"
                  value={swaggerUrl}
                  onChange={(e) => setSwaggerUrl(e.target.value)}
                  placeholder="输入Swagger URL (如: https://api.example.com/swagger.json)"
                  className="w-full px-4 py-2 border border-slate-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            )}

            {/* 文件上传 */}
            {uploadMode === 'file' && (
              <div className="border-2 border-dashed border-slate-300 rounded-lg p-8 text-center hover:border-blue-500 transition-colors">
                <input
                  type="file"
                  id="swagger-file"
                  accept=".json,.yaml,.yml"
                  onChange={handleFileUpload}
                  className="hidden"
                  disabled={uploading}
                />
                <label htmlFor="swagger-file" className="cursor-pointer">
                  <FileUp className="w-12 h-12 mx-auto mb-4 text-slate-400" />
                  <p className="text-slate-700 font-medium mb-1">
                    点击选择或拖拽文件到此处
                  </p>
                  <p className="text-sm text-slate-500">
                    支持 JSON、YAML 格式的 Swagger/OpenAPI 文档
                  </p>
                </label>
              </div>
            )}

            <div className="flex justify-end space-x-3 mt-6">
              <button
                onClick={() => {
                  setShowUploadDialog(false)
                  setSwaggerUrl('')
                }}
                disabled={uploading}
                className="px-4 py-2 border border-slate-300 rounded-md hover:bg-slate-50 disabled:opacity-50"
              >
                取消
              </button>
              {uploadMode === 'url' && (
                <button
                  onClick={handleParseSwagger}
                  disabled={!swaggerUrl.trim() || uploading}
                  className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
                >
                  {uploading ? '解析中...' : '开始解析'}
                </button>
              )}
            </div>
          </div>
        </div>
      )}

      {/* 测试数据生成器 */}
      {showDataGenerator && selectedApi && (
        <TestDataGenerator
          apiInfo={selectedApi}
          onDataGenerated={handleDataGenerated}
          onClose={() => setShowDataGenerator(false)}
        />
      )}

      {/* API执行器 */}
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
