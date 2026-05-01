import { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../services/api'

export default function ProjectsV2() {
  const navigate = useNavigate()
  const [projects, setProjects] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [showCreateDialog, setShowCreateDialog] = useState(false)
  const [showCreateMenu, setShowCreateMenu] = useState(false)
  const [searchKeyword, setSearchKeyword] = useState('')
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    team: ''
  })
  const menuRef = useRef(null)

  useEffect(() => {
    loadProjects()
  }, [])

  // 点击外部关闭下拉菜单
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (menuRef.current && !menuRef.current.contains(event.target)) {
        setShowCreateMenu(false)
      }
    }

    if (showCreateMenu) {
      document.addEventListener('mousedown', handleClickOutside)
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside)
    }
  }, [showCreateMenu])

  const loadProjects = async () => {
    try {
      setLoading(true)
      setError(null)
      const response = await api.v2.projects.getAll()
      setProjects(response.projects || response || [])
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleCreate = async (e) => {
    e.preventDefault()
    try {
      await api.v2.projects.create(formData)
      setShowCreateDialog(false)
      setFormData({ name: '', description: '', team: '' })
      loadProjects()
    } catch (err) {
      alert(`创建失败: ${err.message}`)
    }
  }

  const handleDelete = async (id) => {
    if (!confirm('确定要删除这个项目吗?')) return
    
    try {
      await api.v2.projects.delete(id)
      setProjects(prev => prev.filter(project => project.id !== id))
      loadProjects()
    } catch (err) {
      alert(`删除失败: ${err.message}`)
    }
  }

  const filteredProjects = projects.filter(p =>
    !searchKeyword || 
    p.name.toLowerCase().includes(searchKeyword.toLowerCase()) ||
    (p.description && p.description.toLowerCase().includes(searchKeyword.toLowerCase()))
  )

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-slate-600">加载中...</div>
      </div>
    )
  }

  return (
    <div className="p-6">
      {/* 头部 */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">项目管理</h1>
          <p className="text-sm text-slate-600 mt-1">管理测试项目、环境和配置</p>
        </div>
        
        {/* 新建项目按钮组 */}
        <div className="relative" ref={menuRef}>
          <button
            onClick={() => setShowCreateMenu(!showCreateMenu)}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors flex items-center gap-2"
          >
            + 新建项目
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </button>
          
          {/* 下拉菜单 */}
          {showCreateMenu && (
            <div className="absolute right-0 top-full mt-2 w-64 bg-white border border-slate-200 rounded-md shadow-lg z-50">
              <button
                onClick={() => {
                  setShowCreateMenu(false)
                  setShowCreateDialog(true)
                }}
                className="w-full px-4 py-3 text-left hover:bg-slate-50 transition-colors border-b border-slate-100"
              >
                <div className="font-medium text-slate-900">手动创建项目</div>
                <div className="text-xs text-slate-600 mt-1">从零开始创建新项目</div>
              </button>
              
              <button
                onClick={() => {
                  setShowCreateMenu(false)
                  navigate('/real-project-onboarding')
                }}
                className="w-full px-4 py-3 text-left hover:bg-slate-50 transition-colors"
              >
                <div className="font-medium text-slate-900 flex items-center gap-2">
                  真实项目快速接入
                  <span className="text-xs bg-blue-100 text-blue-700 px-2 py-0.5 rounded">推荐</span>
                </div>
                <div className="text-xs text-slate-600 mt-1">快速接入已有真实项目</div>
              </button>
            </div>
          )}
        </div>
      </div>

      {/* 搜索栏 */}
      <div className="mb-6">
        <input
          type="text"
          placeholder="搜索项目名称或描述..."
          value={searchKeyword}
          onChange={(e) => setSearchKeyword(e.target.value)}
          className="w-full px-4 py-2 border border-slate-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>

      {/* 错误提示 */}
      {error && (
        <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-md text-red-700">
          {error}
        </div>
      )}

      {/* 项目列表 */}
      {filteredProjects.length === 0 ? (
        <div className="text-center py-12">
          <div className="text-slate-400 text-lg mb-4">暂无项目</div>
          <div className="flex flex-col items-center gap-3">
            <button
              onClick={() => setShowCreateDialog(true)}
              className="px-6 py-3 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
            >
              手动创建项目
            </button>
            <button
              onClick={() => navigate('/real-project-onboarding')}
              className="px-6 py-3 bg-green-600 text-white rounded-md hover:bg-green-700 transition-colors flex items-center gap-2"
            >
              真实项目快速接入
              <span className="text-xs bg-white text-green-700 px-2 py-0.5 rounded">推荐</span>
            </button>
          </div>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredProjects.map(project => (
            <div
              key={project.id}
              className="bg-white border border-slate-200 rounded-lg p-6 hover:shadow-lg transition-shadow cursor-pointer"
              onClick={() => navigate(`/projects-v2/${project.id}`)}
            >
              <div className="flex items-start justify-between mb-4">
                <div className="flex-1">
                  <h3 className="text-lg font-semibold text-slate-900 mb-1">
                    {project.name}
                  </h3>
                  <p className="text-sm text-slate-600 line-clamp-2">
                    {project.description || '暂无描述'}
                  </p>
                </div>
                <button
                  onClick={(e) => {
                    e.stopPropagation()
                    handleDelete(project.id)
                  }}
                  className="text-slate-400 hover:text-red-600 transition-colors ml-2"
                  title="删除项目"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                  </svg>
                </button>
              </div>

              <div className="flex items-center gap-4 text-sm text-slate-600">
                <div className="flex items-center gap-1">
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
                  </svg>
                  <span>{project.team || '未分配团队'}</span>
                </div>
                <div className="flex items-center gap-1">
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <span>{new Date(project.created_at).toLocaleDateString()}</span>
                </div>
              </div>

              {project.is_active !== undefined && (
                <div className="mt-4 pt-4 border-t border-slate-200">
                  <span className={`inline-flex items-center px-2 py-1 rounded text-xs font-medium ${
                    project.is_active 
                      ? 'bg-green-100 text-green-800' 
                      : 'bg-slate-100 text-slate-600'
                  }`}>
                    {project.is_active ? '活跃' : '已归档'}
                  </span>
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* 创建项目对话框 */}
      {showCreateDialog && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h2 className="text-xl font-bold text-slate-900 mb-4">新建项目</h2>
            
            <form onSubmit={handleCreate}>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">
                    项目名称 <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    required
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    className="w-full px-3 py-2 border border-slate-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="输入项目名称"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">
                    项目描述
                  </label>
                  <textarea
                    value={formData.description}
                    onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                    className="w-full px-3 py-2 border border-slate-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="输入项目描述"
                    rows={3}
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">
                    所属团队
                  </label>
                  <input
                    type="text"
                    value={formData.team}
                    onChange={(e) => setFormData({ ...formData, team: e.target.value })}
                    className="w-full px-3 py-2 border border-slate-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="输入团队名称"
                  />
                </div>
              </div>

              <div className="flex gap-3 mt-6">
                <button
                  type="button"
                  onClick={() => {
                    setShowCreateDialog(false)
                    setFormData({ name: '', description: '', team: '' })
                  }}
                  className="flex-1 px-4 py-2 border border-slate-300 text-slate-700 rounded-md hover:bg-slate-50 transition-colors"
                >
                  取消
                </button>
                <button
                  type="submit"
                  className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
                >
                  创建
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
