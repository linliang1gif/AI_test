import { useState, useEffect } from 'react'
import { projectsAPI } from '../services/api'

export default function Projects() {
  const [projects, setProjects] = useState([])
  const [searchTerm, setSearchTerm] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [newProject, setNewProject] = useState({
    name: '',
    description: '',
    environment: 'development',
    baseUrl: 'http://localhost:8080'
  })

  const loadProjects = () => {
    setLoading(true)
    projectsAPI.getAll()
      .then(data => setProjects(data.projects || []))
      .catch(err => setError(err.message))
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    loadProjects()
  }, [])

  const handleDelete = (id) => {
    if (!window.confirm('确认删除该项目？')) return
    projectsAPI.delete(id)
      .then(() => setProjects(prev => prev.filter(p => p.id !== id)))
      .catch(err => alert('删除失败: ' + err.message))
  }

  const handleCreate = () => {
    setShowCreateModal(true)
  }

  const handleSubmitCreate = (e) => {
    e.preventDefault()
    if (!newProject.name.trim()) {
      alert('请输入项目名称')
      return
    }
    
    projectsAPI.create(newProject)
      .then(() => {
        loadProjects()
        setShowCreateModal(false)
        setNewProject({
          name: '',
          description: '',
          environment: 'development',
          baseUrl: 'http://localhost:8080'
        })
      })
      .catch(err => alert('创建失败: ' + err.message))
  }

  const handleCancelCreate = () => {
    setShowCreateModal(false)
    setNewProject({
      name: '',
      description: '',
      environment: 'development',
      baseUrl: 'http://localhost:8080'
    })
  }

  const handleRunProject = async (id) => {
    try {
      const data = await api.testRuns.start({ project_id: id, environment: 'staging' })
      alert(data.message || '测试已启动')
    } catch (err) {
      alert('启动失败: ' + err.message)
    }
  }

  const getStatusBadge = (status) => {
    const statusConfig = {
      active: { bg: 'bg-green-100', text: 'text-green-700', label: '活跃' },
      inactive: { bg: 'bg-gray-100', text: 'text-gray-700', label: '暂停' }
    }
    const config = statusConfig[status] || statusConfig.inactive
    return (
      <span className={`px-2 py-1 text-xs font-medium rounded-full ${config.bg} ${config.text}`}>
        {config.label}
      </span>
    )
  }

  const getEnvironmentBadge = (env) => {
    const envConfig = {
      production: { bg: 'bg-red-100', text: 'text-red-700', label: '生产环境' },
      staging: { bg: 'bg-yellow-100', text: 'text-yellow-700', label: '测试环境' },
      development: { bg: 'bg-blue-100', text: 'text-blue-700', label: '开发环境' }
    }
    const config = envConfig[env] || envConfig.development
    return (
      <span className={`px-2 py-1 text-xs font-medium rounded-full ${config.bg} ${config.text}`}>
        {config.label}
      </span>
    )
  }

  const filteredProjects = projects.filter(project =>
    (project.name || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
    (project.description || '').toLowerCase().includes(searchTerm.toLowerCase())
  )

  return (
    <div className="p-8 space-y-8">
      {/* Create Project Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl shadow-2xl w-full max-w-md p-6 space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-xl font-bold text-gray-900">创建新项目</h2>
              <button onClick={handleCancelCreate} className="text-gray-400 hover:text-gray-600">✕</button>
            </div>
            
            <form onSubmit={handleSubmitCreate} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">项目名称 *</label>
                <input
                  type="text"
                  value={newProject.name}
                  onChange={(e) => setNewProject({...newProject, name: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="例如: 用户管理系统"
                  required
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">项目描述</label>
                <textarea
                  value={newProject.description}
                  onChange={(e) => setNewProject({...newProject, description: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="简要描述项目功能..."
                  rows="3"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">环境 *</label>
                <select
                  value={newProject.environment}
                  onChange={(e) => setNewProject({...newProject, environment: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="development">开发环境</option>
                  <option value="staging">测试环境</option>
                  <option value="production">生产环境</option>
                </select>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">基础URL *</label>
                <input
                  type="text"
                  value={newProject.baseUrl}
                  onChange={(e) => setNewProject({...newProject, baseUrl: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="http://localhost:8080"
                  required
                />
              </div>
              
              <div className="flex items-center space-x-3 pt-4">
                <button
                  type="submit"
                  className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                >
                  创建项目
                </button>
                <button
                  type="button"
                  onClick={handleCancelCreate}
                  className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
                >
                  取消
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="space-y-1">
          <h1 className="text-3xl font-bold text-gray-900">📁 项目管理</h1>
          <p className="text-gray-600">管理和监控您的测试项目，跟踪测试覆盖率和执行状态</p>
        </div>
        <button onClick={handleCreate} className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors flex items-center space-x-2">
          <span>➕</span>
          <span>创建项目</span>
        </button>
      </div>

      {loading && <p className="text-gray-500 text-sm">加载中...</p>}
      {error && <div className="p-3 bg-red-50 text-red-600 rounded-md text-sm">加载失败: {error}</div>}

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">总项目数</p>
              <p className="text-2xl font-bold text-gray-900">{projects.length}</p>
            </div>
            <div className="w-12 h-12 bg-blue-100 rounded-xl flex items-center justify-center">
              <span className="text-2xl">🌐</span>
            </div>
          </div>
        </div>
        
        <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">活跃项目</p>
              <p className="text-2xl font-bold text-green-600">
                {projects.filter(p => p.status === 'active').length}
              </p>
            </div>
            <div className="w-12 h-12 bg-green-100 rounded-xl flex items-center justify-center">
              <span className="text-2xl">▶️</span>
            </div>
          </div>
        </div>
        
        <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">总测试数</p>
              <p className="text-2xl font-bold text-purple-600">
                {projects.reduce((sum, p) => sum + p.testsCount, 0)}
              </p>
            </div>
            <div className="w-12 h-12 bg-purple-100 rounded-xl flex items-center justify-center">
              <span className="text-2xl">🧪</span>
            </div>
          </div>
        </div>
        
        <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">平均覆盖率</p>
              <p className="text-2xl font-bold text-orange-600">
                {projects.length ? Math.round(projects.reduce((sum, p) => sum + (p.coverage || 0), 0) / projects.length) : 0}%
              </p>
            </div>
            <div className="w-12 h-12 bg-orange-100 rounded-xl flex items-center justify-center">
              <span className="text-2xl">📊</span>
            </div>
          </div>
        </div>
      </div>

      {/* Search */}
      <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm">
        <div className="flex items-center space-x-4">
          <div className="flex-1 relative">
            <span className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400">🔍</span>
            <input
              type="text"
              placeholder="搜索项目名称或描述..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2.5 bg-gray-50 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
            />
          </div>
          <button onClick={() => alert('筛选功能暂未实现')} className="px-4 py-2 border border-gray-200 rounded-lg hover:bg-gray-50 flex items-center space-x-2">
            <span>🔽</span>
            <span>筛选</span>
          </button>
        </div>
      </div>

      {/* Projects Table */}
      <div className="bg-white rounded-xl border border-gray-200 shadow-sm">
        <div className="p-6 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">项目列表</h2>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">项目信息</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">环境</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">测试统计</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">覆盖率</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">最后运行</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">状态</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">操作</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {filteredProjects.map((project) => (
                <tr key={project.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4">
                    <div className="space-y-1">
                      <div className="font-semibold text-gray-900">{project.name}</div>
                      <div className="text-sm text-gray-500 max-w-md">
                        {project.description}
                      </div>
                      <div className="flex items-center space-x-4 text-xs text-gray-400">
                        <span>📅 创建于 {project.createdAt}</span>
                        <span>👥 {project.team}</span>
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <div className="space-y-2">
                      {getEnvironmentBadge(project.environment)}
                      <div className="text-xs text-gray-500 font-mono">
                        {project.baseUrl}
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <div className="space-y-1">
                      <div className="font-semibold text-gray-900">{project.testsCount}</div>
                      <div className="text-xs text-gray-500">个测试用例</div>
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <div className="space-y-2">
                      <div className="flex items-center space-x-2">
                        <div className="font-semibold text-gray-900">{project.coverage}%</div>
                        <div className={`w-2 h-2 rounded-full ${
                          project.coverage >= 90 ? 'bg-green-500' :
                          project.coverage >= 70 ? 'bg-yellow-500' : 'bg-red-500'
                        }`}></div>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-1.5">
                        <div 
                          className={`h-1.5 rounded-full ${
                            project.coverage >= 90 ? 'bg-green-500' :
                            project.coverage >= 70 ? 'bg-yellow-500' : 'bg-red-500'
                          }`}
                          style={{ width: `${project.coverage}%` }}
                        ></div>
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex items-center space-x-1 text-sm text-gray-600">
                      <span>🕐</span>
                      <span>{project.lastRun}</span>
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    {getStatusBadge(project.status)}
                  </td>
                  <td className="px-6 py-4 text-right">
                    <div className="flex items-center justify-end space-x-2">
                      <button onClick={() => handleRunProject(project.id)} className="p-2 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded-lg">
                        ▶️
                      </button>
                      <button onClick={() => alert('编辑功能暂未实现')} className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-50 rounded-lg">
                        ✏️
                      </button>
                      <button onClick={() => alert('设置功能暂未实现')} className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-50 rounded-lg">
                        ⚙️
                      </button>
                      <button onClick={() => handleDelete(project.id)} className="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg">
                        🗑️
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}