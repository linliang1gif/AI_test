import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../services/api'

const STATUS_LABELS = {
  planning: '规划中', in_progress: '进行中', testing: '测试中',
  completed: '已完成', archived: '已归档',
}
const STATUS_COLORS = {
  planning: 'bg-slate-100 text-slate-700',
  in_progress: 'bg-blue-100 text-blue-700',
  testing: 'bg-yellow-100 text-yellow-800',
  completed: 'bg-green-100 text-green-700',
  archived: 'bg-gray-100 text-gray-500',
}

export default function IterationList() {
  const navigate = useNavigate()
  const [projects, setProjects] = useState([])
  const [selectedProject, setSelectedProject] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [iterations, setIterations] = useState([])
  const [templates, setTemplates] = useState([])
  const [loading, setLoading] = useState(false)
  const [showCreate, setShowCreate] = useState(false)
  const [form, setForm] = useState({ name: '', version: '', description: '', owner: '', test_owner: '', planned_start_time: '', planned_release_time: '', template_key: 'general_feature' })
  const [error, setError] = useState('')
  const selectedTemplate = templates.find(t => t.template_key === form.template_key)

  useEffect(() => {
    api.projects.getAll().then(r => {
      const list = r.projects || r.data || []
      setProjects(list)
      if (list.length > 0 && !selectedProject) setSelectedProject(String(list[0].id))
    }).catch(() => {})
    api.v2.iterations.templates().then(r => {
      setTemplates(r.templates || [])
    }).catch(() => setTemplates([]))
  }, [])

  useEffect(() => {
    if (!selectedProject) return
    setLoading(true)
    const params = statusFilter ? { status: statusFilter } : {}
    api.v2.iterations.list(selectedProject, params).then(r => {
      setIterations(r.iterations || [])
    }).catch(() => setIterations([])).finally(() => setLoading(false))
  }, [selectedProject, statusFilter])

  const handleCreate = async () => {
    if (!form.name.trim()) { setError('请输入迭代名称'); return }
    setError('')
    try {
      const res = await api.v2.iterations.create({ ...form, project_id: Number(selectedProject) })
      setShowCreate(false)
      setForm({ name: '', version: '', description: '', owner: '', test_owner: '', planned_start_time: '', planned_release_time: '', template_key: 'general_feature' })
      setIterations(prev => [res, ...prev])
      if (res.template_key) {
        alert(res.message || '已根据模板生成初始测试点，请在测试点页确认后再生成用例。')
      }
      navigate(`/iterations/${res.id}`)
    } catch (e) {
      setError(e.message || e.detail || '创建失败')
    }
  }

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">迭代中心</h1>
          <p className="text-sm text-slate-500 mt-1">管理迭代、需求、测试点、用例和执行</p>
        </div>
        <button onClick={() => setShowCreate(true)} className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium">
          + 创建迭代
        </button>
      </div>

      {/* 筛选栏 */}
      <div className="flex gap-4 mb-6">
        <select value={selectedProject} onChange={e => setSelectedProject(e.target.value)}
          className="px-3 py-2 border border-slate-300 rounded-lg text-sm bg-white min-w-[200px]">
          {projects.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}
        </select>
        <select value={statusFilter} onChange={e => setStatusFilter(e.target.value)}
          className="px-3 py-2 border border-slate-300 rounded-lg text-sm bg-white">
          <option value="">全部状态</option>
          {Object.entries(STATUS_LABELS).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
        </select>
      </div>

      {/* 列表 */}
      {loading ? (
        <div className="text-center py-12 text-slate-500">加载中...</div>
      ) : iterations.length === 0 ? (
        <div className="text-center py-12 text-slate-400">暂无迭代，点击右上角创建</div>
      ) : (
        <div className="grid gap-4">
          {iterations.map(it => (
            <div key={it.id} onClick={() => navigate(`/iterations/${it.id}`)}
              className="bg-white border border-slate-200 rounded-lg p-5 hover:shadow-md hover:border-blue-300 cursor-pointer transition-all">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-3">
                    <h3 className="text-lg font-semibold text-slate-900">{it.name}</h3>
                    {it.version && <span className="text-xs bg-slate-100 text-slate-600 px-2 py-0.5 rounded">v{it.version}</span>}
                    <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${STATUS_COLORS[it.status] || 'bg-slate-100'}`}>
                      {STATUS_LABELS[it.status] || it.status}
                    </span>
                  </div>
                  {it.description && <p className="text-sm text-slate-500 mt-1 line-clamp-1">{it.description}</p>}
                  <div className="flex gap-4 mt-3 text-xs text-slate-500">
                    {it.owner && <span>负责人: {it.owner}</span>}
                    {it.test_owner && <span>测试: {it.test_owner}</span>}
                    {it.created_at && <span>创建: {it.created_at.slice(0, 10)}</span>}
                  </div>
                </div>
                <div className="flex gap-6 text-center ml-6">
                  <div><div className="text-xl font-bold text-slate-800">{it.requirement_count ?? '-'}</div><div className="text-xs text-slate-500">需求</div></div>
                  <div><div className="text-xl font-bold text-slate-800">{it.test_point_total ?? '-'}</div><div className="text-xs text-slate-500">测试点</div></div>
                  <div><div className="text-xl font-bold text-slate-800">{it.total_cases ?? 0}</div><div className="text-xs text-slate-500">用例</div></div>
                  <div><div className="text-xl font-bold text-blue-600">{it.pass_rate ?? 0}%</div><div className="text-xs text-slate-500">通过率</div></div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* 创建弹窗 */}
      {showCreate && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50" onClick={() => setShowCreate(false)}>
          <div className="bg-white rounded-xl p-6 w-full max-w-2xl max-h-[90vh] overflow-y-auto shadow-xl" onClick={e => e.stopPropagation()}>
            <h2 className="text-lg font-bold mb-4">创建迭代</h2>
            {error && <div className="mb-3 p-2 bg-red-50 text-red-700 text-sm rounded">{error}</div>}
            <div className="space-y-3">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">迭代名称 *</label>
                <input value={form.name} onChange={e => setForm({...form, name: e.target.value})} className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm" placeholder="如: Sprint 2026-05" />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">版本号</label>
                  <input value={form.version} onChange={e => setForm({...form, version: e.target.value})} className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm" placeholder="v1.2.3" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">负责人</label>
                  <input value={form.owner} onChange={e => setForm({...form, owner: e.target.value})} className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm" />
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">测试负责人</label>
                <input value={form.test_owner} onChange={e => setForm({...form, test_owner: e.target.value})} className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm" />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">迭代模板</label>
                <select value={form.template_key} onChange={e => setForm({...form, template_key: e.target.value})}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm bg-white">
                  <option value="">不使用模板</option>
                  {templates.map(t => <option key={t.template_key} value={t.template_key}>{t.template_name}</option>)}
                </select>
              </div>
              {selectedTemplate && (
                <div className="border border-blue-100 bg-blue-50 rounded-lg p-3 text-sm">
                  <div className="font-medium text-blue-900 mb-1">{selectedTemplate.template_name}</div>
                  <p className="text-blue-800 mb-2">{selectedTemplate.description}</p>
                  <div className="grid grid-cols-2 gap-3 text-xs text-blue-900">
                    <div>
                      <span className="text-blue-600">默认测试点:</span> {selectedTemplate.default_test_points?.length || 0} 个
                    </div>
                    <div>
                      <span className="text-blue-600">建议执行集:</span> {(selectedTemplate.default_execution_sets || []).join(', ') || '-'}
                    </div>
                  </div>
                  {selectedTemplate.default_risk_points?.length > 0 && (
                    <div className="mt-2">
                      <div className="text-xs text-blue-600 mb-1">默认风险点</div>
                      <div className="flex flex-wrap gap-1">
                        {selectedTemplate.default_risk_points.map(r => (
                          <span key={r} className="px-2 py-0.5 rounded bg-white text-blue-700 border border-blue-100 text-xs">{r}</span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">描述</label>
                <textarea value={form.description} onChange={e => setForm({...form, description: e.target.value})} className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm" rows={2} />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">计划开始</label>
                  <input type="date" value={form.planned_start_time} onChange={e => setForm({...form, planned_start_time: e.target.value})} className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">计划发布</label>
                  <input type="date" value={form.planned_release_time} onChange={e => setForm({...form, planned_release_time: e.target.value})} className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm" />
                </div>
              </div>
            </div>
            <div className="flex justify-end gap-3 mt-5">
              <button onClick={() => setShowCreate(false)} className="px-4 py-2 text-sm text-slate-600 border border-slate-300 rounded-lg hover:bg-slate-50">取消</button>
              <button onClick={handleCreate} className="px-4 py-2 text-sm text-white bg-blue-600 rounded-lg hover:bg-blue-700">创建</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
