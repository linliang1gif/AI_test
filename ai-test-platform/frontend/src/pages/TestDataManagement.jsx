import { useState, useEffect, useCallback } from 'react'
import DangerConfirmDialog from '../components/common/DangerConfirmDialog'
import { DANGER } from '../services/api'

const API = '/api/v2/test-data'
const DATASET_TYPES = ['account', 'api_payload', 'ui_form', 'performance_pool', 'common_fixture', 'cleanup_rule']
const TYPE_LABELS = { account: '测试账号', api_payload: 'API请求数据', ui_form: 'Web UI表单', performance_pool: '性能数据池', common_fixture: '公共前置', cleanup_rule: '清理规则' }
const CASE_TYPES = ['api', 'web_ui', 'visual', 'performance']
const SENSITIVE_KEYS = ['password', 'token', 'cookie', 'authorization', 'secret', 'api_key', 'apikey', 'access_token']
const isSensitive = (key) => SENSITIVE_KEYS.some(sk => key.toLowerCase().includes(sk))

export default function TestDataManagement() {
  const [datasets, setDatasets] = useState([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(false)
  const [filterType, setFilterType] = useState('')
  const [keyword, setKeyword] = useState('')

  const [showCreate, setShowCreate] = useState(false)
  const [editDs, setEditDs] = useState(null)
  const [showDetail, setShowDetail] = useState(null)
  const [showAddItem, setShowAddItem] = useState(null)
  const [showBind, setShowBind] = useState(null)
  const [healthResult, setHealthResult] = useState(null)
  const [deleteTarget, setDeleteTarget] = useState(null)  // Phase 10B

  const [form, setForm] = useState({ name: '', description: '', dataset_type: 'common_fixture', case_type: 'api', tags: [] })
  const [itemForm, setItemForm] = useState({ key: '', value_json: '', is_sensitive: false })
  const [bindCaseId, setBindCaseId] = useState('')
  const [availableCases, setAvailableCases] = useState([])

  const fetchDatasets = useCallback(async () => {
    setLoading(true)
    try {
      const params = new URLSearchParams()
      if (filterType) params.set('dataset_type', filterType)
      if (keyword) params.set('keyword', keyword)
      const r = await fetch(`${API}/datasets?${params}`)
      const d = await r.json()
      setDatasets(d.data || [])
      setTotal(d.total || 0)
    } catch (e) { console.error(e) }
    setLoading(false)
  }, [filterType, keyword])

  useEffect(() => { fetchDatasets() }, [fetchDatasets])

  const handleCreate = async () => {
    const r = await fetch(`${API}/datasets`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(form) })
    if (r.ok) { setShowCreate(false); setForm({ name: '', description: '', dataset_type: 'common_fixture', case_type: 'api', tags: [] }); fetchDatasets() }
  }

  const handleUpdate = async () => {
    if (!editDs) return
    const r = await fetch(`${API}/datasets/${editDs.id}`, { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(form) })
    if (r.ok) { setEditDs(null); fetchDatasets() }
  }

  // Phase 10B: 删除改为 DangerConfirmDialog
  const handleDelete = (ds) => {
    setDeleteTarget(ds)
  }

  const doDelete = async () => {
    if (!deleteTarget) return
    const r = await fetch(`${API}/datasets/${deleteTarget.id}`, {
      method: 'DELETE',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ confirm: true, confirm_text: DANGER.DELETE_DATASET }),
    })
    if (!r.ok) {
      const err = await r.text().catch(() => '')
      throw new Error(err || `删除失败 (${r.status})`)
    }
    setDeleteTarget(null)
    fetchDatasets()
  }

  const openDetail = async (id) => {
    const r = await fetch(`${API}/datasets/${id}`)
    const d = await r.json()
    setShowDetail(d.data)
  }

  const openEdit = (ds) => {
    setEditDs(ds)
    setForm({ name: ds.name, description: ds.description, dataset_type: ds.dataset_type, case_type: ds.case_type, tags: ds.tags || [] })
  }

  const handleAddItem = async () => {
    if (!showAddItem) return
    let val = itemForm.value_json
    try { val = JSON.parse(val) } catch { /* keep as string */ }
    await fetch(`${API}/datasets/${showAddItem.id}/items`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ key: itemForm.key, value_json: val, is_sensitive: itemForm.is_sensitive || isSensitive(itemForm.key) })
    })
    setItemForm({ key: '', value_json: '', is_sensitive: false })
    openDetail(showAddItem.id)
  }

  const handleDeleteItem = async (itemId) => {
    await fetch(`${API}/items/${itemId}`, { method: 'DELETE' })
    if (showDetail) openDetail(showDetail.id)
  }

  const openBind = async (ds) => {
    setShowBind(ds)
    setBindCaseId('')
    try {
      const r = await fetch('/api/v2/test-cases?limit=200')
      const d = await r.json()
      setAvailableCases(d.data || d.test_cases || [])
    } catch { setAvailableCases([]) }
  }

  const handleBind = async () => {
    if (!showBind || !bindCaseId) return
    await fetch(`${API}/bindings`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ dataset_id: showBind.id, case_id: bindCaseId })
    })
    setShowBind(null)
    fetchDatasets()
  }

  const handleUnbind = async (bindingId) => {
    await fetch(`${API}/bindings/${bindingId}`, { method: 'DELETE' })
    if (showDetail) openDetail(showDetail.id)
  }

  const handleValidate = async (id) => {
    try {
      const r = await fetch(`${API}/datasets/${id}/validate`, { method: 'POST' })
      const d = await r.json()
      setHealthResult(d)
    } catch (e) { console.error(e) }
  }

  const handleClone = async (id) => {
    const r = await fetch(`${API}/datasets/${id}/clone`, { method: 'POST' })
    if (r.ok) fetchDatasets()
  }

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">测试数据管理</h1>
          <p className="text-sm text-slate-500 mt-1">管理测试数据集、数据项和用例绑定 · 共 {total} 个数据集</p>
        </div>
        <button onClick={() => setShowCreate(true)} className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 text-sm font-medium">+ 新建数据集</button>
      </div>

      {/* Filters */}
      <div className="flex gap-3 mb-4">
        <select value={filterType} onChange={e => setFilterType(e.target.value)} className="border rounded-lg px-3 py-2 text-sm">
          <option value="">全部类型</option>
          {DATASET_TYPES.map(t => <option key={t} value={t}>{TYPE_LABELS[t] || t}</option>)}
        </select>
        <input value={keyword} onChange={e => setKeyword(e.target.value)} placeholder="搜索数据集名称..." className="border rounded-lg px-3 py-2 text-sm flex-1 max-w-xs" />
      </div>

      {/* Table */}
      <div className="bg-white rounded-xl border shadow-sm overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-slate-50 border-b">
            <tr>
              <th className="text-left px-4 py-3 font-medium text-slate-600">名称</th>
              <th className="text-left px-4 py-3 font-medium text-slate-600">类型</th>
              <th className="text-left px-4 py-3 font-medium text-slate-600">用例类型</th>
              <th className="text-center px-4 py-3 font-medium text-slate-600">数据项</th>
              <th className="text-center px-4 py-3 font-medium text-slate-600">绑定用例</th>
              <th className="text-left px-4 py-3 font-medium text-slate-600">更新时间</th>
              <th className="text-center px-4 py-3 font-medium text-slate-600">操作</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan={7} className="text-center py-8 text-slate-400">加载中...</td></tr>
            ) : datasets.length === 0 ? (
              <tr><td colSpan={7} className="text-center py-8 text-slate-400">暂无数据集</td></tr>
            ) : datasets.map(ds => (
              <tr key={ds.id} className="border-b hover:bg-slate-50">
                <td className="px-4 py-3">
                  <button onClick={() => openDetail(ds.id)} className="text-indigo-600 hover:underline font-medium">{ds.name}</button>
                  {ds.description && <p className="text-xs text-slate-400 mt-0.5 truncate max-w-xs">{ds.description}</p>}
                </td>
                <td className="px-4 py-3"><span className="px-2 py-0.5 rounded text-xs bg-indigo-50 text-indigo-700">{TYPE_LABELS[ds.dataset_type] || ds.dataset_type}</span></td>
                <td className="px-4 py-3"><span className="px-2 py-0.5 rounded text-xs bg-slate-100">{ds.case_type}</span></td>
                <td className="px-4 py-3 text-center font-mono">{ds.item_count}</td>
                <td className="px-4 py-3 text-center font-mono">{ds.binding_count}</td>
                <td className="px-4 py-3 text-slate-500 text-xs">{ds.updated_at?.slice(0, 16).replace('T', ' ')}</td>
                <td className="px-4 py-3 text-center">
                  <div className="flex justify-center gap-1">
                    <button onClick={() => { setShowAddItem(ds) }} className="px-2 py-1 text-xs bg-green-50 text-green-700 rounded hover:bg-green-100">添加数据</button>
                    <button onClick={() => openBind(ds)} className="px-2 py-1 text-xs bg-blue-50 text-blue-700 rounded hover:bg-blue-100">绑定用例</button>
                    <button onClick={() => handleValidate(ds.id)} className="px-2 py-1 text-xs bg-amber-50 text-amber-700 rounded hover:bg-amber-100">健康检查</button>
                    <button onClick={() => handleClone(ds.id)} className="px-2 py-1 text-xs bg-purple-50 text-purple-700 rounded hover:bg-purple-100">复制</button>
                    <button onClick={() => openEdit(ds)} className="px-2 py-1 text-xs bg-slate-50 text-slate-600 rounded hover:bg-slate-100">编辑</button>
                    <button onClick={() => handleDelete(ds)} className="px-2 py-1 text-xs bg-red-50 text-red-600 rounded hover:bg-red-100">删除</button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Create/Edit Dialog */}
      {(showCreate || editDs) && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl p-6 w-[500px] shadow-2xl">
            <h2 className="text-lg font-bold mb-4">{editDs ? '编辑数据集' : '新建数据集'}</h2>
            <div className="space-y-3">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">名称 *</label>
                <input value={form.name} onChange={e => setForm({...form, name: e.target.value})} className="w-full border rounded-lg px-3 py-2 text-sm" placeholder="例如: 登录测试账号" />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">描述</label>
                <textarea value={form.description} onChange={e => setForm({...form, description: e.target.value})} className="w-full border rounded-lg px-3 py-2 text-sm" rows={2} />
              </div>
              <div className="flex gap-3">
                <div className="flex-1">
                  <label className="block text-sm font-medium text-slate-700 mb-1">数据集类型</label>
                  <select value={form.dataset_type} onChange={e => setForm({...form, dataset_type: e.target.value})} className="w-full border rounded-lg px-3 py-2 text-sm">
                    {DATASET_TYPES.map(t => <option key={t} value={t}>{TYPE_LABELS[t] || t}</option>)}
                  </select>
                </div>
                <div className="flex-1">
                  <label className="block text-sm font-medium text-slate-700 mb-1">用例类型</label>
                  <select value={form.case_type} onChange={e => setForm({...form, case_type: e.target.value})} className="w-full border rounded-lg px-3 py-2 text-sm">
                    {CASE_TYPES.map(t => <option key={t} value={t}>{t}</option>)}
                  </select>
                </div>
              </div>
            </div>
            <div className="flex justify-end gap-2 mt-5">
              <button onClick={() => { setShowCreate(false); setEditDs(null) }} className="px-4 py-2 border rounded-lg text-sm">取消</button>
              <button onClick={editDs ? handleUpdate : handleCreate} className="px-4 py-2 bg-indigo-600 text-white rounded-lg text-sm hover:bg-indigo-700">{editDs ? '保存' : '创建'}</button>
            </div>
          </div>
        </div>
      )}

      {/* Detail Dialog */}
      {showDetail && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl p-6 w-[700px] max-h-[80vh] overflow-y-auto shadow-2xl">
            <div className="flex justify-between items-start mb-4">
              <div>
                <h2 className="text-lg font-bold">{showDetail.name}</h2>
                <div className="flex gap-2 mt-1">
                  <span className="px-2 py-0.5 rounded text-xs bg-indigo-50 text-indigo-700">{TYPE_LABELS[showDetail.dataset_type] || showDetail.dataset_type}</span>
                  <span className="px-2 py-0.5 rounded text-xs bg-slate-100">{showDetail.case_type}</span>
                </div>
                {showDetail.description && <p className="text-sm text-slate-500 mt-2">{showDetail.description}</p>}
              </div>
              <button onClick={() => setShowDetail(null)} className="text-slate-400 hover:text-slate-600 text-xl">×</button>
            </div>

            {/* Items */}
            <h3 className="font-semibold text-sm text-slate-700 mb-2">数据项 ({showDetail.items?.length || 0})</h3>
            {showDetail.items?.length > 0 ? (
              <table className="w-full text-sm border rounded-lg overflow-hidden mb-4">
                <thead className="bg-slate-50">
                  <tr>
                    <th className="text-left px-3 py-2">Key</th>
                    <th className="text-left px-3 py-2">Value</th>
                    <th className="text-center px-3 py-2">敏感</th>
                    <th className="text-center px-3 py-2">操作</th>
                  </tr>
                </thead>
                <tbody>
                  {showDetail.items.map(item => (
                    <tr key={item.id} className="border-t">
                      <td className="px-3 py-2 font-mono text-xs">${'{' + item.key + '}'}</td>
                      <td className="px-3 py-2 text-xs">{item.is_sensitive ? <span className="text-slate-400">****</span> : <span className="font-mono">{JSON.stringify(item.value_json)}</span>}</td>
                      <td className="px-3 py-2 text-center">{item.is_sensitive ? <span className="text-red-500 text-xs">🔒</span> : ''}</td>
                      <td className="px-3 py-2 text-center">
                        <button onClick={() => handleDeleteItem(item.id)} className="text-xs text-red-500 hover:underline">删除</button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : <p className="text-sm text-slate-400 py-2 text-center mb-4">暂无数据项</p>}

            <div className="flex gap-2 mb-4">
              <button onClick={() => setShowAddItem(showDetail)} className="px-3 py-1.5 text-xs bg-green-50 text-green-700 rounded hover:bg-green-100">+ 添加数据项</button>
              <button onClick={() => handleValidate(showDetail.id)} className="px-3 py-1.5 text-xs bg-amber-50 text-amber-700 rounded hover:bg-amber-100">健康检查</button>
            </div>
            {showDetail.dataset_type === 'cleanup_rule' && (
              <div className="bg-amber-50 border border-amber-200 rounded-lg p-3 mb-4 text-xs text-amber-800">
                <strong>清理规则说明:</strong> 数据项的 value 应为 JSON 格式 {'{"method": "DELETE", "url": "/api/...", "headers": {}, "body": {}}'}
              </div>
            )}

            {/* Bindings */}
            <h3 className="font-semibold text-sm text-slate-700 mb-2">绑定用例 ({showDetail.bindings?.length || 0})</h3>
            {showDetail.bindings?.length > 0 ? (
              <table className="w-full text-sm border rounded-lg overflow-hidden">
                <thead className="bg-slate-50">
                  <tr>
                    <th className="text-left px-3 py-2">用例 ID</th>
                    <th className="text-left px-3 py-2">绑定类型</th>
                    <th className="text-center px-3 py-2">操作</th>
                  </tr>
                </thead>
                <tbody>
                  {showDetail.bindings.map(b => (
                    <tr key={b.id} className="border-t">
                      <td className="px-3 py-2 font-mono text-xs">{b.case_id}</td>
                      <td className="px-3 py-2 text-xs">{b.binding_type}</td>
                      <td className="px-3 py-2 text-center">
                        <button onClick={() => handleUnbind(b.id)} className="text-xs text-red-500 hover:underline">解绑</button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : <p className="text-sm text-slate-400 py-2 text-center">暂无绑定</p>}
          </div>
        </div>
      )}

      {/* Add Item Dialog */}
      {showAddItem && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl p-6 w-[480px] shadow-2xl">
            <h2 className="text-lg font-bold mb-4">添加数据项到 "{showAddItem.name}"</h2>
            <div className="space-y-3">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Key (变量名) *</label>
                <input value={itemForm.key} onChange={e => setItemForm({...itemForm, key: e.target.value})} className="w-full border rounded-lg px-3 py-2 text-sm font-mono" placeholder="例如: username" />
                <p className="text-xs text-slate-400 mt-1">用例中使用 ${'{'}key{'}'} 引用</p>
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Value (值)</label>
                <input value={itemForm.value_json} onChange={e => setItemForm({...itemForm, value_json: e.target.value})} className="w-full border rounded-lg px-3 py-2 text-sm font-mono" placeholder='字符串或 JSON' />
              </div>
              <label className="flex items-center gap-2 text-sm">
                <input type="checkbox" checked={itemForm.is_sensitive || isSensitive(itemForm.key)} onChange={e => setItemForm({...itemForm, is_sensitive: e.target.checked})} />
                <span>标记为敏感数据 (展示时脱敏)</span>
              </label>
            </div>
            <div className="flex justify-end gap-2 mt-5">
              <button onClick={() => setShowAddItem(null)} className="px-4 py-2 border rounded-lg text-sm">取消</button>
              <button onClick={handleAddItem} disabled={!itemForm.key} className="px-4 py-2 bg-green-600 text-white rounded-lg text-sm hover:bg-green-700 disabled:opacity-50">添加</button>
            </div>
          </div>
        </div>
      )}

      {/* Bind Dialog */}
      {/* Health Check Result */}
      {healthResult && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl p-6 w-[500px] max-h-[70vh] overflow-y-auto shadow-2xl">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-lg font-bold">数据集健康检查</h2>
              <span className={`px-3 py-1 rounded-full text-sm font-medium ${healthResult.valid ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
                {healthResult.valid ? '✓ 健康' : '✗ 异常'}
              </span>
            </div>
            {healthResult.errors?.length > 0 && (
              <div className="mb-3">
                <h3 className="text-sm font-semibold text-red-600 mb-1">错误 ({healthResult.errors.length})</h3>
                {healthResult.errors.map((e, i) => <p key={i} className="text-xs text-red-600 bg-red-50 p-2 rounded mb-1">{e}</p>)}
              </div>
            )}
            {healthResult.warnings?.length > 0 && (
              <div className="mb-3">
                <h3 className="text-sm font-semibold text-amber-600 mb-1">警告 ({healthResult.warnings.length})</h3>
                {healthResult.warnings.map((w, i) => <p key={i} className="text-xs text-amber-700 bg-amber-50 p-2 rounded mb-1">{w}</p>)}
              </div>
            )}
            {healthResult.sensitive_fields?.length > 0 && (
              <div className="mb-3">
                <h3 className="text-sm font-semibold text-slate-600 mb-1">敏感字段</h3>
                <div className="flex flex-wrap gap-1">{healthResult.sensitive_fields.map((f, i) => <span key={i} className="px-2 py-0.5 bg-red-50 text-red-600 rounded text-xs">{f}</span>)}</div>
              </div>
            )}
            {healthResult.suggestions?.length > 0 && (
              <div className="mb-3">
                <h3 className="text-sm font-semibold text-blue-600 mb-1">建议</h3>
                {healthResult.suggestions.map((s, i) => <p key={i} className="text-xs text-blue-700 bg-blue-50 p-2 rounded mb-1">{s}</p>)}
              </div>
            )}
            {healthResult.errors?.length === 0 && healthResult.warnings?.length === 0 && (
              <p className="text-sm text-green-600 text-center py-4">所有检查项均通过</p>
            )}
            <div className="flex justify-end mt-4">
              <button onClick={() => setHealthResult(null)} className="px-4 py-2 border rounded-lg text-sm">关闭</button>
            </div>
          </div>
        </div>
      )}

      {showBind && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl p-6 w-[500px] shadow-2xl">
            <h2 className="text-lg font-bold mb-4">绑定用例到 "{showBind.name}"</h2>
            <select value={bindCaseId} onChange={e => setBindCaseId(e.target.value)} className="w-full border rounded-lg px-3 py-2 text-sm mb-4">
              <option value="">选择用例...</option>
              {availableCases.map(c => (
                <option key={c.id} value={c.id}>{c.title} ({c.id})</option>
              ))}
            </select>
            <div className="flex justify-end gap-2">
              <button onClick={() => setShowBind(null)} className="px-4 py-2 border rounded-lg text-sm">取消</button>
              <button onClick={handleBind} disabled={!bindCaseId} className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700 disabled:opacity-50">绑定</button>
            </div>
          </div>
        </div>
      )}

      {/* Phase 10B: 删除数据集确认弹窗 */}
      <DangerConfirmDialog
        open={!!deleteTarget}
        title="删除数据集"
        description={deleteTarget
          ? `将永久删除数据集「${deleteTarget.name}」(ID: ${deleteTarget.id})，包含的数据项与绑定将被连带清除。此操作不可恢复。`
          : ''}
        confirmText={DANGER.DELETE_DATASET}
        confirmLabel="删除"
        onConfirm={doDelete}
        onClose={() => setDeleteTarget(null)}
      />
    </div>
  )
}
