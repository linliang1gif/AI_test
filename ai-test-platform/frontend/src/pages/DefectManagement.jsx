import { useState, useEffect, useCallback } from 'react'

const API = '/api/v2/defects'
const SEVERITY_COLORS = { blocker: 'bg-red-600 text-white', critical: 'bg-red-100 text-red-700', major: 'bg-amber-100 text-amber-700', minor: 'bg-blue-100 text-blue-700', trivial: 'bg-slate-100 text-slate-600' }
const STATUS_COLORS = { open: 'bg-red-100 text-red-700', confirmed: 'bg-amber-100 text-amber-700', fixed: 'bg-blue-100 text-blue-700', verified: 'bg-green-100 text-green-700', closed: 'bg-slate-200 text-slate-500', rejected: 'bg-slate-100 text-slate-400', reopened: 'bg-red-100 text-red-600' }
const TRANSITIONS = { open: ['confirmed', 'rejected'], confirmed: ['fixed'], fixed: ['verified'], verified: ['closed'], closed: ['reopened'], rejected: [], reopened: ['confirmed', 'rejected'] }
const SEVERITIES = ['blocker', 'critical', 'major', 'minor', 'trivial']
const PRIORITIES = ['P0', 'P1', 'P2', 'P3']
const SOURCES = ['manual', 'run_failure', 'failure_analysis', 'quality_gate', 'visual_diff', 'performance_regression', 'data_issue']
const SOURCE_LABELS = { manual: '人工', run_failure: '执行失败', failure_analysis: '失败归因', quality_gate: '质量门禁', visual_diff: '视觉差异', performance_regression: '性能退化', data_issue: '数据问题' }

export default function DefectManagement() {
  const [defects, setDefects] = useState([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(false)
  const [filterStatus, setFilterStatus] = useState('')
  const [filterSeverity, setFilterSeverity] = useState('')
  const [keyword, setKeyword] = useState('')

  const [showCreate, setShowCreate] = useState(false)
  const [showDetail, setShowDetail] = useState(null)
  const [showTransition, setShowTransition] = useState(null)
  const [transitionComment, setTransitionComment] = useState('')

  const [form, setForm] = useState({ title: '', description: '', module: '', severity: 'major', priority: 'P2', source: 'manual', failure_category: '', assigned_to: '' })

  const fetchDefects = useCallback(async () => {
    setLoading(true)
    try {
      const params = new URLSearchParams()
      if (filterStatus) params.set('status', filterStatus)
      if (filterSeverity) params.set('severity', filterSeverity)
      if (keyword) params.set('keyword', keyword)
      params.set('limit', '50')
      const r = await fetch(`${API}?${params}`)
      const d = await r.json()
      setDefects(d.defects || [])
      setTotal(d.total || 0)
    } catch (e) { console.error(e) }
    setLoading(false)
  }, [filterStatus, filterSeverity, keyword])

  useEffect(() => { fetchDefects() }, [fetchDefects])

  const handleCreate = async () => {
    const r = await fetch(API, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(form) })
    if (r.ok) { setShowCreate(false); setForm({ title: '', description: '', module: '', severity: 'major', priority: 'P2', source: 'manual', failure_category: '', assigned_to: '' }); fetchDefects() }
  }

  const openDetail = async (id) => {
    const r = await fetch(`${API}/${id}`)
    const d = await r.json()
    setShowDetail(d)
  }

  const handleTransition = async (defectId, toStatus) => {
    const r = await fetch(`${API}/${defectId}/transition`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ to_status: toStatus, comment: transitionComment }) })
    if (r.ok) { setShowTransition(null); setTransitionComment(''); openDetail(defectId); fetchDefects() }
  }

  const handleUpdate = async (defectId, data) => {
    await fetch(`${API}/${defectId}`, { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data) })
    openDetail(defectId)
    fetchDefects()
  }

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">缺陷管理</h1>
          <p className="text-sm text-slate-500 mt-1">缺陷闭环跟踪 · 共 {total} 个缺陷</p>
        </div>
        <button onClick={() => setShowCreate(true)} className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 text-sm font-medium">+ 新建缺陷</button>
      </div>

      {/* Filters */}
      <div className="flex gap-3 mb-4 flex-wrap">
        <select value={filterStatus} onChange={e => setFilterStatus(e.target.value)} className="border rounded-lg px-3 py-1.5 text-sm">
          <option value="">全部状态</option>
          {Object.keys(STATUS_COLORS).map(s => <option key={s} value={s}>{s}</option>)}
        </select>
        <select value={filterSeverity} onChange={e => setFilterSeverity(e.target.value)} className="border rounded-lg px-3 py-1.5 text-sm">
          <option value="">全部严重级别</option>
          {SEVERITIES.map(s => <option key={s} value={s}>{s}</option>)}
        </select>
        <input value={keyword} onChange={e => setKeyword(e.target.value)} placeholder="关键词搜索..." className="border rounded-lg px-3 py-1.5 text-sm w-48" />
      </div>

      {/* Table */}
      <div className="bg-white rounded-xl shadow-sm border overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-slate-50 border-b">
            <tr>
              <th className="text-left px-4 py-3 font-medium text-slate-600">ID</th>
              <th className="text-left px-4 py-3 font-medium text-slate-600">标题</th>
              <th className="text-center px-4 py-3 font-medium text-slate-600">严重级别</th>
              <th className="text-center px-4 py-3 font-medium text-slate-600">优先级</th>
              <th className="text-center px-4 py-3 font-medium text-slate-600">状态</th>
              <th className="text-center px-4 py-3 font-medium text-slate-600">来源</th>
              <th className="text-left px-4 py-3 font-medium text-slate-600">模块</th>
              <th className="text-left px-4 py-3 font-medium text-slate-600">更新时间</th>
              <th className="text-center px-4 py-3 font-medium text-slate-600">操作</th>
            </tr>
          </thead>
          <tbody className="divide-y">
            {defects.map(d => (
              <tr key={d.id} className="hover:bg-slate-50 cursor-pointer" onClick={() => openDetail(d.id)}>
                <td className="px-4 py-3 font-mono text-xs text-slate-500">#{d.id}</td>
                <td className="px-4 py-3 font-medium text-slate-800 max-w-xs truncate">{d.title}</td>
                <td className="px-4 py-3 text-center"><span className={`px-2 py-0.5 rounded text-xs ${SEVERITY_COLORS[d.severity] || ''}`}>{d.severity}</span></td>
                <td className="px-4 py-3 text-center font-mono text-xs">{d.priority}</td>
                <td className="px-4 py-3 text-center"><span className={`px-2 py-0.5 rounded text-xs ${STATUS_COLORS[d.status] || ''}`}>{d.status}</span></td>
                <td className="px-4 py-3 text-center text-xs text-slate-500">{SOURCE_LABELS[d.source] || d.source}</td>
                <td className="px-4 py-3 text-xs text-slate-500">{d.module}</td>
                <td className="px-4 py-3 text-xs text-slate-400">{d.updated_at?.slice(0, 16).replace('T', ' ')}</td>
                <td className="px-4 py-3 text-center" onClick={e => e.stopPropagation()}>
                  <div className="flex justify-center gap-1">
                    {(TRANSITIONS[d.status] || []).map(t => (
                      <button key={t} onClick={() => { setShowTransition({ id: d.id, from: d.status, to: t }); setTransitionComment('') }} className="px-2 py-0.5 text-xs bg-indigo-50 text-indigo-700 rounded hover:bg-indigo-100">{t}</button>
                    ))}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {loading && <p className="text-center py-4 text-slate-400">加载中...</p>}
        {!loading && defects.length === 0 && <p className="text-center py-8 text-slate-400">暂无缺陷</p>}
      </div>

      {/* Create Dialog */}
      {showCreate && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl p-6 w-[600px] max-h-[80vh] overflow-y-auto shadow-2xl">
            <h2 className="text-lg font-bold mb-4">新建缺陷</h2>
            <div className="space-y-3">
              <input value={form.title} onChange={e => setForm({ ...form, title: e.target.value })} placeholder="缺陷标题 *" className="w-full border rounded-lg px-3 py-2 text-sm" />
              <textarea value={form.description} onChange={e => setForm({ ...form, description: e.target.value })} placeholder="描述" rows={3} className="w-full border rounded-lg px-3 py-2 text-sm" />
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-xs text-slate-500">严重级别</label>
                  <select value={form.severity} onChange={e => setForm({ ...form, severity: e.target.value })} className="w-full border rounded-lg px-3 py-2 text-sm">
                    {SEVERITIES.map(s => <option key={s} value={s}>{s}</option>)}
                  </select>
                </div>
                <div>
                  <label className="text-xs text-slate-500">优先级</label>
                  <select value={form.priority} onChange={e => setForm({ ...form, priority: e.target.value })} className="w-full border rounded-lg px-3 py-2 text-sm">
                    {PRIORITIES.map(p => <option key={p} value={p}>{p}</option>)}
                  </select>
                </div>
                <div>
                  <label className="text-xs text-slate-500">来源</label>
                  <select value={form.source} onChange={e => setForm({ ...form, source: e.target.value })} className="w-full border rounded-lg px-3 py-2 text-sm">
                    {SOURCES.map(s => <option key={s} value={s}>{SOURCE_LABELS[s]}</option>)}
                  </select>
                </div>
                <div>
                  <label className="text-xs text-slate-500">模块</label>
                  <input value={form.module} onChange={e => setForm({ ...form, module: e.target.value })} placeholder="模块" className="w-full border rounded-lg px-3 py-2 text-sm" />
                </div>
              </div>
              <input value={form.failure_category} onChange={e => setForm({ ...form, failure_category: e.target.value })} placeholder="失败分类" className="w-full border rounded-lg px-3 py-2 text-sm" />
              <input value={form.assigned_to} onChange={e => setForm({ ...form, assigned_to: e.target.value })} placeholder="分配给" className="w-full border rounded-lg px-3 py-2 text-sm" />
            </div>
            <div className="flex justify-end gap-2 mt-5">
              <button onClick={() => setShowCreate(false)} className="px-4 py-2 border rounded-lg text-sm">取消</button>
              <button onClick={handleCreate} disabled={!form.title} className="px-4 py-2 bg-red-600 text-white rounded-lg text-sm hover:bg-red-700 disabled:opacity-50">创建</button>
            </div>
          </div>
        </div>
      )}

      {/* Detail Dialog */}
      {showDetail && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl p-6 w-[700px] max-h-[85vh] overflow-y-auto shadow-2xl">
            <div className="flex justify-between items-start mb-4">
              <div>
                <h2 className="text-lg font-bold">#{showDetail.id} {showDetail.title}</h2>
                <div className="flex gap-2 mt-2">
                  <span className={`px-2 py-0.5 rounded text-xs ${SEVERITY_COLORS[showDetail.severity]}`}>{showDetail.severity}</span>
                  <span className={`px-2 py-0.5 rounded text-xs ${STATUS_COLORS[showDetail.status]}`}>{showDetail.status}</span>
                  <span className="px-2 py-0.5 rounded text-xs bg-slate-100">{showDetail.priority}</span>
                  <span className="px-2 py-0.5 rounded text-xs bg-indigo-50 text-indigo-700">{SOURCE_LABELS[showDetail.source] || showDetail.source}</span>
                </div>
              </div>
              <button onClick={() => setShowDetail(null)} className="text-slate-400 hover:text-slate-600 text-xl">&times;</button>
            </div>

            {showDetail.description && <p className="text-sm text-slate-600 mb-4 whitespace-pre-wrap">{showDetail.description}</p>}

            <div className="grid grid-cols-2 gap-2 text-xs mb-4">
              {showDetail.module && <div><span className="text-slate-400">模块:</span> {showDetail.module}</div>}
              {showDetail.case_id && <div><span className="text-slate-400">用例ID:</span> {showDetail.case_id}</div>}
              {showDetail.run_id && <div><span className="text-slate-400">执行ID:</span> {showDetail.run_id}</div>}
              {showDetail.assigned_to && <div><span className="text-slate-400">分配给:</span> {showDetail.assigned_to}</div>}
              {showDetail.failure_category && <div><span className="text-slate-400">失败分类:</span> {showDetail.failure_category}</div>}
              {showDetail.created_by && <div><span className="text-slate-400">创建人:</span> {showDetail.created_by}</div>}
              {showDetail.created_at && <div><span className="text-slate-400">创建时间:</span> {showDetail.created_at.slice(0, 16).replace('T', ' ')}</div>}
              {showDetail.updated_at && <div><span className="text-slate-400">更新时间:</span> {showDetail.updated_at.slice(0, 16).replace('T', ' ')}</div>}
            </div>

            {/* Evidence */}
            {showDetail.evidence_json && Object.keys(showDetail.evidence_json).length > 0 && (
              <div className="mb-4">
                <h3 className="text-sm font-semibold mb-1">证据</h3>
                <div className="bg-slate-50 rounded-lg p-3 text-xs font-mono max-h-40 overflow-y-auto">
                  {Object.entries(showDetail.evidence_json).map(([k, v]) => (
                    <div key={k} className="mb-1"><span className="text-slate-500">{k}:</span> {typeof v === 'string' ? v : JSON.stringify(v)}</div>
                  ))}
                </div>
              </div>
            )}

            {/* Transitions */}
            <div className="flex gap-2 mb-4">
              {(TRANSITIONS[showDetail.status] || []).map(t => (
                <button key={t} onClick={() => { setShowTransition({ id: showDetail.id, from: showDetail.status, to: t }); setTransitionComment('') }} className="px-3 py-1.5 text-xs bg-indigo-50 text-indigo-700 rounded hover:bg-indigo-100">→ {t}</button>
              ))}
            </div>

            {/* Events */}
            {showDetail.events?.length > 0 && (
              <div>
                <h3 className="text-sm font-semibold mb-2">事件历史 ({showDetail.events.length})</h3>
                <div className="space-y-2 max-h-60 overflow-y-auto">
                  {showDetail.events.map(ev => (
                    <div key={ev.id} className="bg-slate-50 rounded-lg p-2 text-xs">
                      <div className="flex justify-between">
                        <span className="font-medium">{ev.event_type}{ev.from_status ? ` ${ev.from_status} → ${ev.to_status}` : ev.to_status ? ` → ${ev.to_status}` : ''}</span>
                        <span className="text-slate-400">{ev.created_at?.slice(0, 16).replace('T', ' ')}</span>
                      </div>
                      {ev.comment && <p className="text-slate-500 mt-1">{ev.comment}</p>}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Transition Dialog */}
      {showTransition && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl p-6 w-[400px] shadow-2xl">
            <h2 className="text-lg font-bold mb-3">状态流转</h2>
            <p className="text-sm mb-3">{showTransition.from} → <span className="font-bold text-indigo-700">{showTransition.to}</span></p>
            <textarea value={transitionComment} onChange={e => setTransitionComment(e.target.value)} placeholder="备注（可选）" rows={2} className="w-full border rounded-lg px-3 py-2 text-sm mb-4" />
            <div className="flex justify-end gap-2">
              <button onClick={() => setShowTransition(null)} className="px-4 py-2 border rounded-lg text-sm">取消</button>
              <button onClick={() => handleTransition(showTransition.id, showTransition.to)} className="px-4 py-2 bg-indigo-600 text-white rounded-lg text-sm hover:bg-indigo-700">确认</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
