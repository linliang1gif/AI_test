import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../services/api'
import { useToast } from '../components/ui/Toast'

function ApiSpecList() {
  const navigate = useNavigate()
  const toast = useToast()
  const [apiSpecs, setApiSpecs] = useState([])
  const [loading, setLoading] = useState(true)
  const [selectedProject, setSelectedProject] = useState(null)
  const [projects, setProjects] = useState([])

  useEffect(() => {
    loadProjects()
  }, [])

  useEffect(() => {
    loadApiSpecs()
  }, [selectedProject])

  const loadProjects = async () => {
    try {
      const data = await api.v2.projects.getAll()
      setProjects(data.projects || [])
    } catch (error) {
      console.error('加载项目失败:', error)
    }
  }

  const loadApiSpecs = async () => {
    setLoading(true)
    try {
      const data = await api.v2.swagger.getApiSpecs(selectedProject)
      setApiSpecs(data || [])
    } catch (error) {
      console.error('加载API规范失败:', error)
      toast.error('加载失败: ' + error.message)
    } finally {
      setLoading(false)
    }
  }

  const handleDelete = async (apiSpecId) => {
    if (!confirm('确定要删除此API规范吗？')) return
    
    try {
      await api.v2.swagger.deleteApiSpec(apiSpecId)
      toast.success('删除成功')
      loadApiSpecs()
    } catch (error) {
      toast.error('删除失败: ' + error.message)
    }
  }

  const handleGenerateTestCases = async (apiSpecId) => {
    try {
      const result = await api.v2.swagger.generateTestCases(apiSpecId)
      toast.success(`成功生成 ${result.test_cases_generated} 个测试用例`)
      loadApiSpecs()
    } catch (error) {
      toast.error('生成失败: ' + error.message)
    }
  }

  const handleViewDetail = (apiSpec) => {
    // 跳转到API规范详情页面（需要创建）
    navigate(`/api-specs/${apiSpec.id}`)
  }

  if (loading && apiSpecs.length === 0) {
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
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">📋 API规范管理</h1>
          <p className="text-gray-600 mt-2">查看和管理已导入的API规范</p>
        </div>
        <button
          onClick={() => navigate('/swagger-workbench')}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
        >
          + 导入新规范
        </button>
      </div>

      {/* 项目筛选 */}
      <div className="bg-white rounded-lg shadow p-4">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          筛选项目
        </label>
        <select
          value={selectedProject || ''}
          onChange={(e) => setSelectedProject(e.target.value ? parseInt(e.target.value) : null)}
          className="w-full md:w-64 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="">全部项目</option>
          {projects.map(project => (
            <option key={project.id} value={project.id}>
              {project.name}
            </option>
          ))}
        </select>
      </div>

      {/* API规范列表 */}
      <div className="bg-white rounded-lg shadow">
        <div className="p-6 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-semibold">API规范列表</h2>
            <div className="text-sm text-gray-600">
              共 {apiSpecs.length} 个规范
            </div>
          </div>
        </div>

        <div className="divide-y divide-gray-200">
          {apiSpecs.length === 0 ? (
            <div className="p-8 text-center text-gray-500">
              <div className="text-4xl mb-2">📭</div>
              <p>暂无API规范</p>
              <p className="text-sm mt-1">请导入Swagger/OpenAPI文档</p>
              <button
                onClick={() => navigate('/swagger-workbench')}
                className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
              >
                立即导入
              </button>
            </div>
          ) : (
            apiSpecs.map((spec) => (
              <div key={spec.id} className="p-6 hover:bg-gray-50 transition-colors">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center space-x-3 mb-2">
                      <h3 className="text-lg font-semibold text-gray-900">
                        API规范 #{spec.id}
                      </h3>
                      {spec.version && (
                        <span className="px-2 py-1 text-xs bg-blue-100 text-blue-700 rounded">
                          {spec.version}
                        </span>
                      )}
                      <span className="px-2 py-1 text-xs bg-gray-100 text-gray-600 rounded">
                        {spec.source_type}
                      </span>
                    </div>
                    
                    <div className="space-y-1 text-sm text-gray-600">
                      <p>
                        <span className="font-medium">API数量:</span>{' '}
                        <span className="text-blue-600 font-semibold">{spec.api_count}</span> 个
                      </p>
                      {spec.source_url && (
                        <p>
                          <span className="font-medium">来源:</span>{' '}
                          <span className="font-mono text-xs">{spec.source_url}</span>
                        </p>
                      )}
                      <p>
                        <span className="font-medium">导入时间:</span>{' '}
                        {new Date(spec.imported_at).toLocaleString('zh-CN')}
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center space-x-2 ml-4">
                    <button
                      onClick={() => handleViewDetail(spec)}
                      className="px-3 py-1.5 text-sm bg-blue-50 text-blue-700 hover:bg-blue-100 rounded-lg transition-colors"
                      title="查看详情"
                    >
                      查看API
                    </button>
                    <button
                      onClick={() => handleGenerateTestCases(spec.id)}
                      className="px-3 py-1.5 text-sm bg-green-50 text-green-700 hover:bg-green-100 rounded-lg transition-colors"
                      title="生成测试用例"
                    >
                      生成用例
                    </button>
                    <button
                      onClick={() => handleDelete(spec.id)}
                      className="px-3 py-1.5 text-sm bg-red-50 text-red-700 hover:bg-red-100 rounded-lg transition-colors"
                      title="删除"
                    >
                      删除
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

export default ApiSpecList
