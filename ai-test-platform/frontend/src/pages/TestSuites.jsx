import { useState, useEffect, useCallback } from 'react'
import DangerConfirmDialog from '../components/common/DangerConfirmDialog'

const API = '/api/v2/test-suites'
// Phase 10B: 后端 check_confirm 要求的 confirm_text（与 backend/routes/test_suite_routes.py 对齐）
const DELETE_TEST_SUITE = 'DELETE_TEST_SUITE'
const SUITE_TYPES = ['smoke', 'regression', 'release', 'api', 'web_ui', 'visual', 'performance', 'mixed']
const PRIORITIES = ['critical', 'high', 'medium', 'low']
const TYPE_LABELS = { smoke: '冒烟', regression: '回归', release: '发布前', api: 'API', web_ui: 'Web UI', visual: '视觉', performance: '性能', mixed: '混合' }
const PRIORITY_COLORS = { critical: 'bg-red-100 text-red-700', high: 'bg-orange-100 text-orange-700', medium: 'bg-blue-100 text-blue-700', low: 'bg-gray-100 text-gray-600' }

export default function TestSuites() {
  const [suites, setSuites] = useState([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(false)
  const [filterType, setFilterType] = useState('')
  const [keyword, setKeyword] = useState('')

  // dialogs
  const [showCreate, setShowCreate] = useState(false)
  const [showDetail, setShowDetail] = useState(null)
  const [showAddCases, setShowAddCases] = useState(null)
  const [editSuite, setEditSuite] = useState(null)
  const [deleteTarget, setDeleteTarget] = useState(null)  // Phase 10B: 危险操作确认

  // form
  const [form, setForm] = useState({ name: '', description: '', suite_type: 'mixed', priority: 'medium' })

  // add cases
  const [availableCases, setAvailableCases] = useState([])
  const [selectedCases, setSelectedCases] = useState([])

  // running
  const [runResult, setRunResult] = useState(null)

  const fetchSuites = useCallback(async () => {
    setLoading(true)
    try {
      const params = new URLSearchParams()
      if (filterType) params.set('suite_type', filterType)
      if (keyword) params.set('keyword', keyword)
      const r = await fetch(`${API}?${params}`)
      const d = await r.json()
      setSuites(d.data || [])
      setTotal(d.total || 0)
    } catch (e) { console.error(e) }
    setLoading(false)
  }, [filterType, keyword])

  useEffect(() => { fetchSuites() }, [fetchSuites])

  const handleCreate = async () => {
    const r = await fetch(API, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(form) })
    if (r.ok) { setShowCreate(false); setForm({ name: '', description: '', suite_type: 'mixed', priority: 'medium' }); fetchSuites() }
  }

  const handleUpdate = async () => {
    if (!editSuite) return
    const r = await fetch(`${API}/${editSuite.id}`, { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(form) })
    if (r.ok) { setEditSuite(null); fetchSuites() }
  }

  // Phase 10B: 删除改为通过 DangerConfirmDialog 携带 confirm_text
  const handleDelete = (suite) => {
    setDeleteTarget(suite)
  }

  const doDelete = async () => {
    if (!deleteTarget) return
    const r = await fetch(`${API}/${deleteTarget.id}`, {
      method: 'DELETE',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ confirm: true, confirm_text: DELETE_TEST_SUITE }),
    })
    if (!r.ok) {
      const err = await r.text().catch(() => '')
      throw new Error(err || `删除失败 (${r.status})`)
    }
    setDeleteTarget(null)
    fetchSuites()
  }

  const openDetail = async (id) => {
    const r = await fetch(`${API}/${id}`)
    const d = await r.json()
    setShowDetail(d.data)
  }

  const openAddCases = async (suite) => {
    setShowAddCases(suite)
    const r = await fetch('/api/v2/test-cases?limit=200')
    const d = await r.json()
    setAvailableCases(d.data || d.test_cases || d || [])
    setSelectedCases([])
  }

  const handleAddCases = async () => {
    if (!showAddCases || selectedCases.length === 0) return
    await fetch(`${API}/${showAddCases.id}/cases`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ case_ids: selectedCases })
    })
    setShowAddCases(null)
    fetchSuites()
  }

  const handleRemoveCase = async (suiteId, caseId) => {
    await fetch(`${API}/${suiteId}/cases/${caseId}`, { method: 'DELETE' })
    openDetail(suiteId)
  }

  const handleRun = async (id) => {
    setRunResult(null)
    const r = await fetch(`${API}/${id}/run`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({}) })
    const d = await r.json()
    setRunResult(d)
  }

  const openEdit = (s) => {
    setEditSuite(s)
    setForm({ name: s.name, description: s.description, suite_type: s.suite_type, priority: s.priority })
  }

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">测试集管理</h1>
          <p className="text-sm text-slate-500 mt-1">创建、管理和执行测试集 · 共 {total} 个测试集</p>
        </div>
        <button onClick={() => setShowCreate(true)} className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm font-medium">
          + 新建测试集
        </button>
      </div>

      {/* Filters */}
      <div className="flex gap-3 mb-4">
        <select value={filterType} onChange={e => setFilterType(e.target.value)} className="border rounded-lg px-3 py-2 text-sm">
          <option value="">全部类型</option>
          {SUITE_TYPES.map(t => <option key={t} value={t}>{TYPE_LABELS[t] || t}</option>)}
        </select>
        <input value={keyword} onChange={e => setKeyword(e.target.value)} placeholder="搜索测试集名称..." className="border rounded-lg px-3 py-2 text-sm flex-1 max-w-xs" />
      </div>

      {/* Table */}
      <div className="bg-white rounded-xl border shadow-sm overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-slate-50 border-b">
            <tr>
              <th className="text-left px-4 py-3 font-medium text-slate-600">名称</th>
              <th className="text-left px-4 py-3 font-medium text-slate-600">类型</th>
              <th className="text-left px-4 py-3 font-medium text-slate-600">优先级</th>
              <th className="text-center px-4 py-3 font-medium text-slate-600">用例数</th>
              <th className="text-left px-4 py-3 font-medium text-slate-600">创建时间</th>
              <th className="text-center px-4 py-3 font-medium text-slate-600">操作</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan={6} className="text-center py-8 text-slate-400">加载中...</td></tr>
            ) : suites.length === 0 ? (
              <tr><td colSpan={6} className="text-center py-8 text-slate-400">暂无测试集</td></tr>
            ) : suites.map(s => (
              <tr key={s.id} className="border-b hover:bg-slate-50">
                <td className="px-4 py-3">
                  <button onClick={() => openDetail(s.id)} className="text-blue-600 hover:underline font-medium">{s.name}</button>
                  {s.description && <p className="text-xs text-slate-400 mt-0.5 truncate max-w-xs">{s.description}</p>}
                </td>
                <td className="px-4 py-3"><span className="px-2 py-0.5 rounded text-xs bg-slate-100 text-slate-700">{TYPE_LABELS[s.suite_type] || s.suite_type}</span></td>
                <td className="px-4 py-3"><span className={`px-2 py-0.5 rounded text-xs ${PRIORITY_COLORS[s.priority] || ''}`}>{s.priority}</span></td>
                <td className="px-4 py-3 text-center font-mono">{s.case_count}</td>
                <td className="px-4 py-3 text-slate-500 text-xs">{s.created_at?.slice(0, 16).replace('T', ' ')}</td>
                <td className="px-4 py-3 text-center">
                  <div className="flex justify-center gap-1">
                    <button onClick={() => openAddCases(s)} className="px-2 py-1 text-xs bg-green-50 text-green-700 rounded hover:bg-green-100">添加用例</button>
                    <button onClick={() => handleRun(s.id)} className="px-2 py-1 text-xs bg-blue-50 text-blue-700 rounded hover:bg-blue-100">执行</button>
                    <button onClick={() => openEdit(s)} className="px-2 py-1 text-xs bg-slate-50 text-slate-600 rounded hover:bg-slate-100">编辑</button>
                    <button onClick={() => handleDelete(s)} className="px-2 py-1 text-xs bg-red-50 text-red-600 rounded hover:bg-red-100">删除</button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Run Result Banner */}
      {runResult && (
        <div className={`mt-4 p-4 rounded-lg border ${runResult.suite_summary?.failed_cases > 0 ? 'bg-red-50 border-red-200' : 'bg-green-50 border-green-200'}`}>
          <div className="flex justify-between items-center">
            <div>
              <span className="font-semibold">{runResult.suite_summary?.suite_name}</span>
              <span className="ml-3 text-sm">Run: <code className="bg-white px-1 rounded">{runResult.run_id}</code></span>
            </div>
            <button onClick={() => setRunResult(null)} className="text-slate-400 hover:text-slate-600">x</button>
          </div>
          <div className="flex gap-4 mt-2 text-sm">
            <span className="text-green-700">Passed: {runResult.suite_summary?.passed_cases}</span>
            <span className="text-red-700">Failed: {runResult.suite_summary?.failed_cases}</span>
            <span className="text-slate-500">Skipped: {runResult.suite_summary?.skipped_cases}</span>
            <span className="text-slate-500">{runResult.suite_summary?.duration_ms}ms</span>
          </div>
        </div>
      )}

      {/* Create / Edit Dialog */}
      {(showCreate || editSuite) && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl p-6 w-[480px] shadow-2xl">
            <h2 className="text-lg font-bold mb-4">{editSuite ? '编辑测试集' : '新建测试集'}</h2>
            <div className="space-y-3">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">名称 *</label>
                <input value={form.name} onChange={e => setForm({...form, name: e.target.value})} className="w-full border rounded-lg px-3 py-2 text-sm" placeholder="例如: 发布前冒烟测试集" />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">描述</label>
                <textarea value={form.description} onChange={e => setForm({...form, description: e.target.value})} className="w-full border rounded-lg px-3 py-2 text-sm" rows={2} />
              </div>
              <div className="flex gap-3">
                <div className="flex-1">
                  <label className="block text-sm font-medium text-slate-700 mb-1">类型</label>
                  <select value={form.suite_type} onChange={e => setForm({...form, suite_type: e.target.value})} className="w-full border rounded-lg px-3 py-2 text-sm">
                    {SUITE_TYPES.map(t => <option key={t} value={t}>{TYPE_LABELS[t] || t}</option>)}
                  </select>
                </div>
                <div className="flex-1">
                  <label className="block text-sm font-medium text-slate-700 mb-1">优先级</label>
                  <select value={form.priority} onChange={e => setForm({...form, priority: e.target.value})} className="w-full border rounded-lg px-3 py-2 text-sm">
                    {PRIORITIES.map(p => <option key={p} value={p}>{p}</option>)}
                  </select>
                </div>
              </div>
            </div>
            <div className="flex justify-end gap-2 mt-5">
              <button onClick={() => { setShowCreate(false); setEditSuite(null) }} className="px-4 py-2 border rounded-lg text-sm">取消</button>
              <button onClick={editSuite ? handleUpdate : handleCreate} className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700">
                {editSuite ? '保存' : '创建'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Detail Dialog */}
      {showDetail && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl p-6 w-[640px] max-h-[80vh] overflow-y-auto shadow-2xl">
            <div className="flex justify-between items-start mb-4">
              <div>
                <h2 className="text-lg font-bold">{showDetail.name}</h2>
                <div className="flex gap-2 mt-1">
                  <span className="px-2 py-0.5 rounded text-xs bg-slate-100">{TYPE_LABELS[showDetail.suite_type] || showDetail.suite_type}</span>
                  <span className={`px-2 py-0.5 rounded text-xs ${PRIORITY_COLORS[showDetail.priority] || ''}`}>{showDetail.priority}</span>
                </div>
                {showDetail.description && <p className="text-sm text-slate-500 mt-2">{showDetail.description}</p>}
              </div>
              <button onClick={() => setShowDetail(null)} className="text-slate-400 hover:text-slate-600 text-xl">x</button>
            </div>
            <h3 className="font-semibold text-sm text-slate-700 mb-2">用例列表 ({showDetail.cases?.length || 0})</h3>
            {showDetail.cases?.length > 0 ? (
              <table className="w-full text-sm border rounded-lg overflow-hidden">
                <thead className="bg-slate-50">
                  <tr>
                    <th className="text-left px-3 py-2">ID</th>
                    <th className="text-left px-3 py-2">标题</th>
                    <th className="text-left px-3 py-2">类型</th>
                    <th className="text-center px-3 py-2">操作</th>
                  </tr>
                </thead>
                <tbody>
                  {showDetail.cases.map(c => (
                    <tr key={c.id} className="border-t">
                      <td className="px-3 py-2 font-mono text-xs">{c.case_id}</td>
                      <td className="px-3 py-2">{c.title || '-'}</td>
                      <td className="px-3 py-2"><span className="px-2 py-0.5 rounded text-xs bg-slate-100">{c.case_type}</span></td>
                      <td className="px-3 py-2 text-center">
                        <button onClick={() => handleRemoveCase(showDetail.id, c.case_id)} className="text-xs text-red-500 hover:underline">移除</button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : (
              <p className="text-sm text-slate-400 py-4 text-center">暂无用例</p>
            )}
          </div>
        </div>
      )}

      {/* Add Cases Dialog */}
      {showAddCases && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl p-6 w-[640px] max-h-[80vh] overflow-y-auto shadow-2xl">
            <h2 className="text-lg font-bold mb-4">添加用例到 "{showAddCases.name}"</h2>
            <div className="max-h-[50vh] overflow-y-auto border rounded-lg">
              {availableCases.length === 0 ? (
                <p className="text-sm text-slate-400 py-8 text-center">无可用用例</p>
              ) : availableCases.map(c => (
                <label key={c.id} className="flex items-center px-3 py-2 hover:bg-slate-50 border-b cursor-pointer">
                  <input
                    type="checkbox"
                    checked={selectedCases.includes(c.id)}
                    onChange={e => {
                      if (e.target.checked) setSelectedCases([...selectedCases, c.id])
                      else setSelectedCases(selectedCases.filter(x => x !== c.id))
                    }}
                    className="mr-3"
                  />
                  <div className="flex-1">
                    <span className="text-sm font-medium">{c.title}</span>
                    <span className="ml-2 text-xs text-slate-400">{c.id}</span>
                    <span className="ml-2 px-1.5 py-0.5 rounded text-xs bg-slate-100">{c.case_type || 'api'}</span>
                  </div>
                </label>
              ))}
            </div>
            <div className="flex justify-between items-center mt-4">
              <span className="text-sm text-slate-500">已选 {selectedCases.length} 条</span>
              <div className="flex gap-2">
                <button onClick={() => setShowAddCases(null)} className="px-4 py-2 border rounded-lg text-sm">取消</button>
                <button onClick={handleAddCases} disabled={selectedCases.length === 0} className="px-4 py-2 bg-green-600 text-white rounded-lg text-sm hover:bg-green-700 disabled:opacity-50">添加</button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Phase 10B: 删除确认弹窗（要求输入 DELETE_TEST_SUITE） */}
      <DangerConfirmDialog
        open={!!deleteTarget}
        title="删除测试集"
        description={deleteTarget
          ? `将永久删除测试集「${deleteTarget.name}」(ID: ${deleteTarget.id})，包含的用例关联会一并移除，此操作不可恢复。`
          : ''}
        confirmText={DELETE_TEST_SUITE}
        confirmLabel="删除"
        onConfirm={doDelete}
        onClose={() => setDeleteTarget(null)}
      />
    </div>
  )
}
