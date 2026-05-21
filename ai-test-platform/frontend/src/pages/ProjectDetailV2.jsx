import { useState, useEffect, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import api, { DANGER } from '../services/api'
import EnvironmentManager from '../components/EnvironmentManager'
import DangerConfirmDialog from '../components/common/DangerConfirmDialog'

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
  const [deleteOpen, setDeleteOpen] = useState(false)  // Phase 10B

  // Iteration states
  const [iterations, setIterations] = useState([])
  const [iterLoading, setIterLoading] = useState(false)
  const [iterModalOpen, setIterModalOpen] = useState(false)
  const [iterEditing, setIterEditing] = useState(null)
  const [iterForm, setIterForm] = useState({ name: '', code: '', description: '', start_date: '', end_date: '', status: 'planning', owner: '' })
  const [iterDeleteTarget, setIterDeleteTarget] = useState(null)

  const loadIterations = useCallback(async () => {
    if (!id || id === 'undefined' || isNaN(id)) return
    try {
      setIterLoading(true)
      const data = await api.v2.iterations.list(id)
      setIterations(data.iterations || [])
    } catch (err) {
      console.error('加载迭代列表失败:', err)
    } finally {
      setIterLoading(false)
    }
  }, [id])

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
    loadIterations()
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

  // Phase 10B: 删除改为 DangerConfirmDialog
  const handleDelete = () => {
    setDeleteOpen(true)
  }

  const doDelete = async () => {
    await api.v2.projects.delete(id, {
      confirm: true,
      confirm_text: DANGER.DELETE_PROJECT,
    })
    setDeleteOpen(false)
    navigate('/projects-v2')
  }

  // ── Iteration handlers ──
  const ITER_STATUS_MAP = {
    planning: { label: '规划中', color: 'bg-slate-100 text-slate-700' },
    in_progress: { label: '进行中', color: 'bg-blue-100 text-blue-700' },
    completed: { label: '已完成', color: 'bg-green-100 text-green-700' },
    archived: { label: '已归档', color: 'bg-gray-100 text-gray-500' },
  }

  const openIterCreate = () => {
    setIterEditing(null)
    setIterForm({ name: '', code: '', description: '', start_date: '', end_date: '', status: 'planning', owner: '' })
    setIterModalOpen(true)
  }

  const openIterEdit = (it) => {
    setIterEditing(it)
    setIterForm({ name: it.name, code: it.code || '', description: it.description || '', start_date: it.start_date || '', end_date: it.end_date || '', status: it.status, owner: it.owner || '' })
    setIterModalOpen(true)
  }

  const handleIterSave = async (e) => {
    e.preventDefault()
    try {
      if (iterEditing) {
        await api.v2.iterations.update(iterEditing.id, iterForm)
      } else {
        await api.v2.iterations.create(id, iterForm)
      }
      setIterModalOpen(false)
      loadIterations()
    } catch (err) {
      alert(`保存失败: ${err.message}`)
    }
  }

  const doIterDelete = async () => {
    if (!iterDeleteTarget) return
    await api.v2.iterations.delete(iterDeleteTarget.id, {
      confirm: true,
      confirm_text: DANGER.DELETE_ITERATION,
    })
    setIterDeleteTarget(null)
    loadIterations()
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
            onClick={() => setActiveTab('iterations')}
            className={`pb-3 px-1 border-b-2 transition-colors ${
              activeTab === 'iterations'
                ? 'border-blue-600 text-blue-600 font-medium'
                : 'border-transparent text-slate-600 hover:text-slate-900'
            }`}
          >
            迭代管理 ({iterations.length})
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

      {/* 迭代管理 Tab */}
      {activeTab === 'iterations' && (
        <div>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-slate-900">迭代列表</h2>
            <button
              onClick={openIterCreate}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors text-sm"
            >
              + 新建迭代
            </button>
          </div>

          {iterLoading ? (
            <div className="text-center py-8 text-slate-500">加载中...</div>
          ) : iterations.length === 0 ? (
            <div className="text-center py-12 bg-white border border-slate-200 rounded-lg">
              <div className="text-slate-400 text-4xl mb-3">&#128197;</div>
              <div className="text-slate-500">暂无迭代，点击上方按钮创建第一个迭代</div>
            </div>
          ) : (
            <div className="space-y-3">
              {iterations.map(it => {
                const st = ITER_STATUS_MAP[it.status] || ITER_STATUS_MAP.planning
                return (
                  <div key={it.id} className="bg-white border border-slate-200 rounded-lg p-4 hover:shadow-sm transition-shadow">
                    <div className="flex items-start justify-between">
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                          <span className="font-medium text-slate-900 truncate">{it.name}</span>
                          {it.code && <span className="text-xs bg-slate-100 text-slate-600 px-2 py-0.5 rounded">{it.code}</span>}
                          <span className={`text-xs px-2 py-0.5 rounded ${st.color}`}>{st.label}</span>
                        </div>
                        {it.description && <p className="text-sm text-slate-500 mb-2 line-clamp-2">{it.description}</p>}
                        <div className="flex flex-wrap gap-4 text-xs text-slate-500">
                          {it.owner && <span>负责人: {it.owner}</span>}
                          {it.start_date && <span>开始: {it.start_date}</span>}
                          {it.end_date && <span>结束: {it.end_date}</span>}
                          <span>用例: {it.total_cases || 0}</span>
                          <span>通过率: {it.pass_rate ?? 0}%</span>
                          <span>执行: {it.total_runs || 0} 次</span>
                        </div>
                      </div>
                      <div className="flex gap-2 ml-4 flex-shrink-0">
                        <button onClick={() => openIterEdit(it)} className="px-3 py-1 text-xs border border-slate-300 text-slate-600 rounded hover:bg-slate-50">编辑</button>
                        <button onClick={() => setIterDeleteTarget(it)} className="px-3 py-1 text-xs border border-red-300 text-red-600 rounded hover:bg-red-50">删除</button>
                      </div>
                    </div>
                  </div>
                )
              })}
            </div>
          )}

          {/* 迭代新建/编辑弹窗 */}
          {iterModalOpen && (
            <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
              <div className="bg-white rounded-lg shadow-xl w-full max-w-lg mx-4">
                <div className="px-6 py-4 border-b border-slate-200">
                  <h3 className="text-lg font-semibold">{iterEditing ? '编辑迭代' : '新建迭代'}</h3>
                </div>
                <form onSubmit={handleIterSave} className="px-6 py-4 space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-1">迭代名称 <span className="text-red-500">*</span></label>
                    <input type="text" required value={iterForm.name} onChange={e => setIterForm({...iterForm, name: e.target.value})} className="w-full px-3 py-2 border border-slate-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500" placeholder="例：v1.2.3 / Sprint 2026-S1" />
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-slate-700 mb-1">迭代编号</label>
                      <input type="text" value={iterForm.code} onChange={e => setIterForm({...iterForm, code: e.target.value})} className="w-full px-3 py-2 border border-slate-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500" placeholder="ITER-001" />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-slate-700 mb-1">状态</label>
                      <select value={iterForm.status} onChange={e => setIterForm({...iterForm, status: e.target.value})} className="w-full px-3 py-2 border border-slate-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500">
                        <option value="planning">规划中</option>
                        <option value="in_progress">进行中</option>
                        <option value="completed">已完成</option>
                        <option value="archived">已归档</option>
                      </select>
                    </div>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-1">描述</label>
                    <textarea value={iterForm.description} onChange={e => setIterForm({...iterForm, description: e.target.value})} className="w-full px-3 py-2 border border-slate-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500" rows={2} />
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-slate-700 mb-1">开始日期</label>
                      <input type="date" value={iterForm.start_date} onChange={e => setIterForm({...iterForm, start_date: e.target.value})} className="w-full px-3 py-2 border border-slate-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500" />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-slate-700 mb-1">结束日期</label>
                      <input type="date" value={iterForm.end_date} onChange={e => setIterForm({...iterForm, end_date: e.target.value})} className="w-full px-3 py-2 border border-slate-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500" />
                    </div>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-1">负责人</label>
                    <input type="text" value={iterForm.owner} onChange={e => setIterForm({...iterForm, owner: e.target.value})} className="w-full px-3 py-2 border border-slate-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500" />
                  </div>
                  <div className="flex justify-end gap-3 pt-2">
                    <button type="button" onClick={() => setIterModalOpen(false)} className="px-4 py-2 border border-slate-300 text-slate-700 rounded-md hover:bg-slate-50">取消</button>
                    <button type="submit" className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700">保存</button>
                  </div>
                </form>
              </div>
            </div>
          )}
        </div>
      )}

      {/* 迭代删除确认弹窗 */}
      <DangerConfirmDialog
        open={!!iterDeleteTarget}
        title="删除迭代"
        description={iterDeleteTarget
          ? `将永久删除迭代「${iterDeleteTarget.name}」(ID: ${iterDeleteTarget.id})。已分配到此迭代的用例将被解除关联，此操作不可恢复。`
          : ''}
        confirmText={DANGER.DELETE_ITERATION}
        confirmLabel="删除"
        onConfirm={doIterDelete}
        onClose={() => setIterDeleteTarget(null)}
      />

      {/* Phase 10B: 删除确认弹窗 */}
      <DangerConfirmDialog
        open={deleteOpen}
        title="删除项目"
        description={project
          ? `将永久删除项目「${project.name}」(ID: ${id})。相关环境、鉴权配置及关联用例将被连带删除，此操作不可恢复。`
          : ''}
        confirmText={DANGER.DELETE_PROJECT}
        confirmLabel="删除"
        onConfirm={doDelete}
        onClose={() => setDeleteOpen(false)}
      />
    </div>
  )
}
