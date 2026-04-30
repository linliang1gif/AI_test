import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import api from '../services/api'
import EnvironmentManager from '../components/EnvironmentManager'

export default function ProjectDetailV2() {
  const { projectId, id: routeId } = useParams()
  const id = projectId || routeId
  const navigate = useNavigate()
  const [project, setProject] = useState(null)
  const [environments, setEnvironments] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [activeTab, setActiveTab] = useState('info')
  const [isEditing, setIsEditing] = useState(false)
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    team: ''
  })

  // 验证 ID 是否有效
  useEffect(() => {
    if (!id || id === 'undefined' || isNaN(id)) {
      console.error('无效的项目ID:', id)
      setError('无效的项目ID')
      setLoading(false)
      return
    }
    loadProject()
    loadEnvironments()
  }, [id])

  const loadProject = async () => {
    if (!id || id === 'undefined' || isNaN(id)) {
      setError('无效的项目ID')
      setLoading(false)
      return
    }
    
    try {
      setLoading(true)
      setError(null)
      const data = await api.v2.projects.get(id)
      setProject(data.project || data)
      setFormData({
        name: data.project?.name || data.name || '',
        description: data.project?.description || data.description || '',
        team: data.project?.team || data.team || ''
      })
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const loadEnvironments = async () => {
    if (!id || id === 'undefined' || isNaN(id)) {
      return
    }
    
    try {
      const data = await api.v2.projects.getEnvironments(id)
      // 后端直接返回数组，不是 { environments: [...] } 格式
      setEnvironments(Array.isArray(data) ? data : (data.environments || []))
    } catch (err) {
      console.error('加载环境列表失败:', err)
    }
  }

  const handleUpdate = async (e) => {
    e.preventDefault()
    try {
      await api.v2.projects.update(id, formData)
      setIsEditing(false)
      loadProject()
    } catch (err) {
      alert(`更新失败: ${err.message}`)
    }
  }

  const handleDelete = async () => {
    if (!confirm('确定要删除这个项目吗? 此操作不可恢复!')) return
    
    try {
      await api.v2.projects.delete(id)
      navigate('/projects-v2')
    } catch (err) {
      alert(`删除失败: ${err.message}`)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-slate-600">加载中...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="p-6">
        <div className="bg-red-50 border border-red-200 rounded-md p-4 text-red-700">
          {error}
        </div>
        <button
          onClick={() => navigate('/projects-v2')}
          className="mt-4 text-blue-600 hover:text-blue-700"
        >
          ← 返回项目列表
        </button>
      </div>
    )
  }

  if (!project) {
    return (
      <div className="p-6">
        <div className="text-slate-600">项目不存在</div>
        <button
          onClick={() => navigate('/projects-v2')}
          className="mt-4 text-blue-600 hover:text-blue-700"
        >
          ← 返回项目列表
        </button>
      </div>
    )
  }

  return (
    <div className="p-6">
      {/* 头部 */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-4">
          <button
            onClick={() => navigate('/projects-v2')}
            className="text-slate-600 hover:text-slate-900"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
          </button>
          <div>
            <h1 className="text-2xl font-bold text-slate-900">{project.name}</h1>
            <p className="text-sm text-slate-600 mt-1">{project.description || '暂无描述'}</p>
          </div>
        </div>
        <div className="flex gap-2">
          {!isEditing && (
            <>
              <button
                onClick={() => setIsEditing(true)}
                className="px-4 py-2 border border-slate-300 text-slate-700 rounded-md hover:bg-slate-50 transition-colors"
              >
                编辑
              </button>
              <button
                onClick={handleDelete}
                className="px-4 py-2 border border-red-300 text-red-600 rounded-md hover:bg-red-50 transition-colors"
              >
                删除
              </button>
            </>
          )}
        </div>
      </div>

      {/* Tab 导航 */}
      <div className="border-b border-slate-200 mb-6">
        <div className="flex gap-6">
          <button
            onClick={() => setActiveTab('info')}
            className={`pb-3 px-1 border-b-2 transition-colors ${
              activeTab === 'info'
                ? 'border-blue-600 text-blue-600 font-medium'
                : 'border-transparent text-slate-600 hover:text-slate-900'
            }`}
          >
            基本信息
          </button>
          <button
            onClick={() => setActiveTab('environments')}
            className={`pb-3 px-1 border-b-2 transition-colors ${
              activeTab === 'environments'
                ? 'border-blue-600 text-blue-600 font-medium'
                : 'border-transparent text-slate-600 hover:text-slate-900'
            }`}
          >
            环境配置 ({environments.length})
          </button>
          <button
            onClick={() => setActiveTab('stats')}
            className={`pb-3 px-1 border-b-2 transition-colors ${
              activeTab === 'stats'
                ? 'border-blue-600 text-blue-600 font-medium'
                : 'border-transparent text-slate-600 hover:text-slate-900'
            }`}
          >
            统计数据
          </button>
        </div>
      </div>

      {/* Tab 内容 */}
      {activeTab === 'info' && (
        <div className="bg-white border border-slate-200 rounded-lg p-6">
          {isEditing ? (
            <form onSubmit={handleUpdate}>
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
                  />
                </div>
              </div>

              <div className="flex gap-3 mt-6">
                <button
                  type="button"
                  onClick={() => {
                    setIsEditing(false)
                    setFormData({
                      name: project.name,
                      description: project.description || '',
                      team: project.team || ''
                    })
                  }}
                  className="px-4 py-2 border border-slate-300 text-slate-700 rounded-md hover:bg-slate-50 transition-colors"
                >
                  取消
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
                >
                  保存
                </button>
              </div>
            </form>
          ) : (
            <div className="space-y-4">
              <div>
                <div className="text-sm font-medium text-slate-700 mb-1">项目名称</div>
                <div className="text-slate-900">{project.name}</div>
              </div>

              <div>
                <div className="text-sm font-medium text-slate-700 mb-1">项目描述</div>
                <div className="text-slate-900">{project.description || '暂无描述'}</div>
              </div>

              <div>
                <div className="text-sm font-medium text-slate-700 mb-1">所属团队</div>
                <div className="text-slate-900">{project.team || '未分配团队'}</div>
              </div>

              <div>
                <div className="text-sm font-medium text-slate-700 mb-1">创建时间</div>
                <div className="text-slate-900">
                  {new Date(project.created_at).toLocaleString()}
                </div>
              </div>

              {project.updated_at && (
                <div>
                  <div className="text-sm font-medium text-slate-700 mb-1">更新时间</div>
                  <div className="text-slate-900">
                    {new Date(project.updated_at).toLocaleString()}
                  </div>
                </div>
              )}

              <div>
                <div className="text-sm font-medium text-slate-700 mb-1">状态</div>
                <span className={`inline-flex items-center px-2 py-1 rounded text-xs font-medium ${
                  project.is_active 
                    ? 'bg-green-100 text-green-800' 
                    : 'bg-slate-100 text-slate-600'
                }`}>
                  {project.is_active ? '活跃' : '已归档'}
                </span>
              </div>
            </div>
          )}
        </div>
      )}

      {activeTab === 'environments' && (
        <EnvironmentManager
          projectId={id}
          environments={environments}
          onUpdate={loadEnvironments}
        />
      )}

      {activeTab === 'stats' && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-white border border-slate-200 rounded-lg p-6">
            <div className="text-sm text-slate-600 mb-1">环境数量</div>
            <div className="text-3xl font-bold text-slate-900">{environments.length}</div>
          </div>

          <div className="bg-white border border-slate-200 rounded-lg p-6">
            <div className="text-sm text-slate-600 mb-1">测试用例</div>
            <div className="text-3xl font-bold text-slate-900">-</div>
            <div className="text-xs text-slate-500 mt-1">待实现</div>
          </div>

          <div className="bg-white border border-slate-200 rounded-lg p-6">
            <div className="text-sm text-slate-600 mb-1">执行次数</div>
            <div className="text-3xl font-bold text-slate-900">-</div>
            <div className="text-xs text-slate-500 mt-1">待实现</div>
          </div>
        </div>
      )}
    </div>
  )
}
