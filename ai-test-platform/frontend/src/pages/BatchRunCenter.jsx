import { useState, useEffect, useRef, useCallback } from 'react'

const API = '/api/v2/batch-runs'

// ── 失败类型中文映射 ────────────────────
const FAILURE_LABELS = {
  auth_failed: '认证失败',
  network_error: '网络异常',
  assertion_failed: '断言失败',
  business_failed: '业务失败',
  system_error: '系统异常',
}
const FAILURE_COLORS = {
  auth_failed: 'bg-red-100 text-red-700',
  network_error: 'bg-orange-100 text-orange-700',
  assertion_failed: 'bg-yellow-100 text-yellow-700',
  business_failed: 'bg-purple-100 text-purple-700',
  system_error: 'bg-gray-100 text-gray-700',
}
const STATUS_BADGE = {
  created: 'bg-blue-100 text-blue-700',
  running: 'bg-cyan-100 text-cyan-700',
  passed: 'bg-green-100 text-green-700',
  failed: 'bg-red-100 text-red-700',
  aborted: 'bg-gray-100 text-gray-600',
}

export default function BatchRunCenter() {
  const [tab, setTab] = useState('create') // create | list | detail
  const [runs, setRuns] = useState([])
  const [selectedBatch, setSelectedBatch] = useState(null)
  const [progress, setProgress] = useState(null)
  const [report, setReport] = useState(null)
  const [loading, setLoading] = useState(false)
  const [detailCases, setDetailCases] = useState(null)
  const [failureFilter, setFailureFilter] = useState('')
  const pollRef = useRef(null)

  // 项目和环境列表
  const [projects, setProjects] = useState([])
  const [environments, setEnvironments] = useState([])
  const [appMode, setAppMode] = useState('mock')

  // 创建表单
  const [form, setForm] = useState({
    project_id: '',
    environment_id: '',
    batch_size: 50,
    concurrency: 5,
    api_pattern: '',
    module_prefix: '',
    title_keyword: '',
    status_filter: '',
  })

  // ── 加载项目列表 ────────────────────────
  useEffect(() => {
    fetch('/health').then(r => r.ok ? r.json() : {}).then(d => setAppMode(d.app_mode || 'mock')).catch(() => {})
    fetch('/api/v2/projects').then(r => r.ok ? r.json() : []).then(data => {
      const list = Array.isArray(data) ? data : (data.items || data.projects || [])
      setProjects(list)
      if (list.length > 0 && !form.project_id) {
        setForm(f => ({ ...f, project_id: list[0].id }))
        // 加载该项目的环境
        loadEnvs(list[0].id)
      }
    }).catch(() => {})
  }, [])

  const loadEnvs = async (projectId) => {
    try {
      const r = await fetch(`/api/v2/projects/${projectId}/environments`)
      if (r.ok) {
        const envs = await r.json()
        const list = Array.isArray(envs) ? envs : (envs.items || [])
        setEnvironments(list)
        if (list.length > 0) setForm(f => ({ ...f, environment_id: list[0].id }))
      }
    } catch (e) { console.error(e) }
  }

  const handleProjectChange = (pid) => {
    setForm(f => ({ ...f, project_id: +pid, environment_id: '' }))
    loadEnvs(pid)
  }

  // ── 加载列表 ────────────────────────────
  const loadRuns = useCallback(async () => {
    try {
      const r = await fetch(`${API}?limit=50`)
      if (r.ok) setRuns(await r.json())
    } catch (e) { console.error(e) }
  }, [])

  useEffect(() => {
    loadRuns()
  }, [loadRuns])

  // ── 创建批量任务 ────────────────────────
  const handleCreate = async () => {
    if (appMode === 'real') {
      if (!window.confirm(
        '当前为真实项目模式，批量执行可能包含写操作用例，\n可能修改真实测试环境数据。\n\n是否确认创建批量执行任务？'
      )) return
    }
    setLoading(true)
    try {
      const filters = {}
      if (form.api_pattern) filters.api_pattern = form.api_pattern
      if (form.module_prefix) filters.module_prefix = form.module_prefix
      if (form.title_keyword) filters.title_keyword = form.title_keyword
      if (form.status_filter) filters.status = form.status_filter

      const body = {
        project_id: form.project_id,
        environment_id: form.environment_id,
        batch_size: form.batch_size,
        concurrency: form.concurrency,
        filters: Object.keys(filters).length > 0 ? filters : null,
      }
      const r = await fetch(API, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      })
      const data = await r.json()
      if (r.ok && data.batch_id) {
        setSelectedBatch(data.batch_id)
        setTab('detail')
        startPolling(data.batch_id)
        loadRuns()
      } else {
        alert(data.detail || '创建失败')
      }
    } catch (e) {
      alert('请求失败: ' + e.message)
    } finally {
      setLoading(false)
    }
  }

  // ── 轮询进度 ────────────────────────────
  const startPolling = useCallback((batchId) => {
    if (pollRef.current) clearInterval(pollRef.current)
    const poll = async () => {
      try {
        const r = await fetch(`${API}/${batchId}/progress`)
        if (r.ok) {
          const data = await r.json()
          setProgress(data)
          if (data.status && data.status !== 'running' && data.progress_pct >= 100) {
            clearInterval(pollRef.current)
            pollRef.current = null
            loadRuns()
            loadReport(batchId)
          }
        }
      } catch (e) { console.error(e) }
    }
    poll()
    pollRef.current = setInterval(poll, 2000)
  }, [loadRuns])

  useEffect(() => {
    return () => { if (pollRef.current) clearInterval(pollRef.current) }
  }, [])

  // ── 加载报告 ────────────────────────────
  const loadReport = async (batchId) => {
    try {
      const r = await fetch(`${API}/${batchId}/report`)
      if (r.ok) setReport(await r.json())
    } catch (e) { console.error(e) }
  }

  // ── 加载用例详情 ────────────────────────
  const loadDetailCases = async (batchId) => {
    try {
      const r = await fetch(`${API}/${batchId}?include_cases=true`)
      if (r.ok) {
        const data = await r.json()
        setDetailCases(data.run_cases || [])
      }
    } catch (e) { console.error(e) }
  }

  // ── 停止任务 ────────────────────────────
  const handleStop = async (batchId) => {
    try {
      await fetch(`${API}/${batchId}/stop`, { method: 'POST' })
    } catch (e) { console.error(e) }
  }

  // ── 查看详情 ────────────────────────────
  const viewBatch = (batchId, status) => {
    setSelectedBatch(batchId)
    setProgress(null)
    setReport(null)
    setDetailCases(null)
    setFailureFilter('')
    setTab('detail')
    if (status === 'running') {
      startPolling(batchId)
    } else {
      // 已完成：直接加载
      fetch(`${API}/${batchId}/progress`).then(r => r.json()).then(setProgress).catch(() => {})
      loadReport(batchId)
    }
  }

  // ── 导出报告 ────────────────────────────
  const exportReport = () => {
    if (!report) return
    const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `batch_report_${selectedBatch}.json`
    a.click()
    URL.revokeObjectURL(url)
  }

  // ── 失败用例列表（带筛选）────────────────
  const filteredFailedCases = detailCases
    ? detailCases.filter(c => {
        if (c.status === 'passed') return false
        if (failureFilter && c.error_type !== failureFilter) return false
        return true
      })
    : []

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-slate-900">批量执行中心</h1>
        <div className="flex gap-2">
          {['create', 'list'].map(t => (
            <button
              key={t}
              onClick={() => setTab(t)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                tab === t ? 'bg-blue-600 text-white' : 'bg-white border border-slate-300 text-slate-700 hover:bg-slate-50'
              }`}
            >
              {t === 'create' ? '创建任务' : '历史记录'}
            </button>
          ))}
        </div>
      </div>

      {/* ── 创建任务 TAB ── */}
      {tab === 'create' && (
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
          <h2 className="text-lg font-semibold mb-4">新建批量执行</h2>
          <div className="grid grid-cols-2 gap-4 mb-6">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">选择项目</label>
              <select value={form.project_id} onChange={e => handleProjectChange(e.target.value)}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm">
                <option value="">请选择项目</option>
                {projects.map(p => (
                  <option key={p.id} value={p.id}>{p.name || p.title || `项目 ${p.id}`}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">选择环境</label>
              <select value={form.environment_id} onChange={e => setForm({...form, environment_id: +e.target.value})}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm">
                <option value="">请选择环境</option>
                {environments.map(env => (
                  <option key={env.id} value={env.id}>{env.name} - {env.base_url || ''}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">每批大小</label>
              <input type="number" value={form.batch_size} onChange={e => setForm({...form, batch_size: +e.target.value})}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm" />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">并发数</label>
              <input type="number" value={form.concurrency} onChange={e => setForm({...form, concurrency: +e.target.value})}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm" />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">接口类型</label>
              <select value={form.api_pattern} onChange={e => setForm({...form, api_pattern: e.target.value})}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm">
                <option value="">全部</option>
                <option value="page">分页查询 (page)</option>
                <option value="list">列表查询 (list)</option>
                <option value="detail">详情 (detail)</option>
                <option value="save">新增 (save)</option>
                <option value="update">修改 (update)</option>
                <option value="delete">删除 (delete)</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">模块路径</label>
              <input type="text" value={form.module_prefix} onChange={e => setForm({...form, module_prefix: e.target.value})}
                placeholder="如 /basic 或 /wms" className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm" />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">标题关键词</label>
              <input type="text" value={form.title_keyword} onChange={e => setForm({...form, title_keyword: e.target.value})}
                placeholder="搜索用例标题" className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm" />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">用例状态</label>
              <select value={form.status_filter} onChange={e => setForm({...form, status_filter: e.target.value})}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm">
                <option value="">全部</option>
                <option value="pending">待执行</option>
                <option value="passed">已通过</option>
                <option value="failed">已失败</option>
              </select>
            </div>
          </div>
          <button
            onClick={handleCreate}
            disabled={loading}
            className="px-6 py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 disabled:opacity-50 transition-colors"
          >
            {loading ? '创建中...' : '开始批量执行'}
          </button>
        </div>
      )}

      {/* ── 历史记录 TAB ── */}
      {tab === 'list' && (
        <div className="bg-white rounded-xl shadow-sm border border-slate-200">
          <div className="p-4 border-b border-slate-200 flex items-center justify-between">
            <span className="text-sm text-slate-600">共 {runs.length} 条执行记录</span>
            <button onClick={loadRuns} className="text-sm text-blue-600 hover:text-blue-700">刷新</button>
          </div>
          <div className="divide-y divide-slate-100">
            {runs.map(run => (
              <div key={run.batch_id} className="p-4 hover:bg-slate-50 cursor-pointer flex items-center justify-between"
                onClick={() => viewBatch(run.batch_id, run.status)}>
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-1">
                    <span className="font-mono text-sm text-slate-800">{run.batch_id}</span>
                    <span className={`px-2 py-0.5 rounded text-xs font-medium ${STATUS_BADGE[run.status] || 'bg-gray-100'}`}>
                      {run.status}
                    </span>
                  </div>
                  <div className="flex items-center gap-4 text-xs text-slate-500">
                    <span>总计 {run.total_cases}</span>
                    <span className="text-green-600">通过 {run.passed_cases}</span>
                    <span className="text-red-600">失败 {run.failed_cases}</span>
                    <span>通过率 {run.pass_rate}%</span>
                    <span>耗时 {run.duration_seconds}s</span>
                  </div>
                </div>
                <span className="text-xs text-slate-400">{run.created_at?.slice(0, 19)}</span>
              </div>
            ))}
            {runs.length === 0 && (
              <div className="p-12 text-center text-slate-500">暂无执行记录</div>
            )}
          </div>
        </div>
      )}

      {/* ── 详情 TAB ── */}
      {tab === 'detail' && selectedBatch && (
        <div className="space-y-6">
          {/* 顶部操作 */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <button onClick={() => setTab('list')} className="text-sm text-blue-600 hover:text-blue-700">← 返回列表</button>
              <span className="font-mono text-lg font-semibold text-slate-900">{selectedBatch}</span>
              {progress && (
                <span className={`px-2 py-0.5 rounded text-xs font-medium ${STATUS_BADGE[progress.status] || STATUS_BADGE.running}`}>
                  {progress.status || 'running'}
                </span>
              )}
            </div>
            <div className="flex gap-2">
              {progress && progress.status === 'running' && (
                <button onClick={() => handleStop(selectedBatch)}
                  className="px-4 py-2 text-sm bg-red-600 text-white rounded-lg hover:bg-red-700">
                  停止执行
                </button>
              )}
              {report && (
                <button onClick={exportReport}
                  className="px-4 py-2 text-sm bg-green-600 text-white rounded-lg hover:bg-green-700">
                  导出报告
                </button>
              )}
            </div>
          </div>

          {/* 进度条 */}
          {progress && (
            <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
              <div className="flex items-center justify-between mb-3">
                <span className="text-sm font-medium text-slate-700">执行进度</span>
                <span className="text-sm text-slate-500">{progress.executed} / {progress.total} ({progress.progress_pct}%)</span>
              </div>
              <div className="w-full bg-slate-200 rounded-full h-4 overflow-hidden mb-4">
                <div className="h-full rounded-full transition-all duration-500 flex">
                  {progress.total > 0 && (
                    <>
                      <div className="bg-green-500 h-full" style={{ width: `${progress.passed / progress.total * 100}%` }} />
                      <div className="bg-red-500 h-full" style={{ width: `${progress.failed / progress.total * 100}%` }} />
                      <div className="bg-slate-400 h-full" style={{ width: `${progress.skipped / progress.total * 100}%` }} />
                      {progress.running > 0 && (
                        <div className="bg-cyan-400 h-full animate-pulse" style={{ width: `${progress.running / progress.total * 100}%` }} />
                      )}
                    </>
                  )}
                </div>
              </div>
              <div className="grid grid-cols-5 gap-4">
                <StatCard label="通过" value={progress.passed} color="text-green-600" />
                <StatCard label="失败" value={progress.failed} color="text-red-600" />
                <StatCard label="跳过" value={progress.skipped} color="text-slate-500" />
                <StatCard label="运行中" value={progress.running} color="text-cyan-600" />
                <StatCard label="耗时" value={`${progress.elapsed_seconds}s`} color="text-slate-700" />
              </div>
            </div>
          )}

          {/* 失败分类 */}
          {progress && progress.failure_categories && Object.values(progress.failure_categories).some(v => v > 0) && (
            <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
              <h3 className="text-sm font-semibold text-slate-700 mb-3">失败归因</h3>
              <div className="flex flex-wrap gap-3">
                {Object.entries(progress.failure_categories).map(([cat, count]) => count > 0 && (
                  <div key={cat} className={`px-4 py-2 rounded-lg text-sm font-medium ${FAILURE_COLORS[cat] || 'bg-gray-100'}`}>
                    {FAILURE_LABELS[cat] || cat}: {count}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* 报告 */}
          {report && (
            <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
              <h3 className="text-sm font-semibold text-slate-700 mb-4">执行报告</h3>
              <div className="grid grid-cols-4 gap-4 mb-6">
                <ReportCard label="总用例" value={report.total_cases} />
                <ReportCard label="通过率" value={`${report.pass_rate}%`} color={report.pass_rate > 80 ? 'text-green-600' : 'text-red-600'} />
                <ReportCard label="总耗时" value={`${report.duration_seconds}s`} />
                <ReportCard label="平均耗时" value={report.duration_stats?.avg_ms ? `${report.duration_stats.avg_ms}ms` : '-'} />
              </div>

              {/* 模块统计 */}
              {report.module_stats && Object.keys(report.module_stats).length > 0 && (
                <div className="mb-6">
                  <h4 className="text-xs font-semibold text-slate-500 mb-2 uppercase">模块分布</h4>
                  <div className="space-y-2 max-h-64 overflow-y-auto">
                    {Object.entries(report.module_stats)
                      .sort((a, b) => b[1].total - a[1].total)
                      .slice(0, 30)
                      .map(([mod, st]) => (
                        <div key={mod} className="flex items-center gap-3 text-sm">
                          <span className="w-64 font-mono text-xs text-slate-600 truncate" title={mod}>{mod || '(root)'}</span>
                          <div className="flex-1 bg-slate-100 rounded-full h-3 overflow-hidden">
                            <div className="bg-green-500 h-full" style={{ width: `${st.passed / Math.max(st.total, 1) * 100}%` }} />
                          </div>
                          <span className="text-xs text-slate-500 w-24 text-right">{st.passed}/{st.total}</span>
                        </div>
                      ))}
                  </div>
                </div>
              )}

              {/* 失败列表 */}
              {report.failed_case_details && report.failed_case_details.length > 0 && (
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <h4 className="text-xs font-semibold text-slate-500 uppercase">失败用例 ({report.failed_case_details.length})</h4>
                    <button onClick={() => loadDetailCases(selectedBatch)} className="text-xs text-blue-600 hover:underline">
                      加载完整列表
                    </button>
                  </div>
                  <div className="space-y-1 max-h-64 overflow-y-auto">
                    {report.failed_case_details.slice(0, 20).map((c, i) => (
                      <div key={i} className="flex items-center gap-3 text-xs py-1.5 border-b border-slate-50">
                        <span className="font-mono text-slate-600 w-20">{c.test_case_id}</span>
                        <span className={`px-2 py-0.5 rounded ${FAILURE_COLORS[c.error_type] || 'bg-gray-100'}`}>
                          {FAILURE_LABELS[c.error_type] || c.error_type}
                        </span>
                        <span className="flex-1 text-slate-500 truncate">{c.error_message}</span>
                        <span className="text-slate-400">{c.duration_ms}ms</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* 可筛选的用例列表 */}
          {detailCases && (
            <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-sm font-semibold text-slate-700">用例执行详情</h3>
                <div className="flex items-center gap-2">
                  <select value={failureFilter} onChange={e => setFailureFilter(e.target.value)}
                    className="text-xs px-2 py-1 border border-slate-300 rounded">
                    <option value="">全部失败类型</option>
                    {Object.entries(FAILURE_LABELS).map(([k, v]) => (
                      <option key={k} value={k}>{v}</option>
                    ))}
                  </select>
                  <span className="text-xs text-slate-500">{filteredFailedCases.length} 条</span>
                </div>
              </div>
              <div className="space-y-1 max-h-96 overflow-y-auto">
                {filteredFailedCases.map((c, i) => (
                  <div key={i} className="flex items-center gap-3 text-xs py-2 border-b border-slate-50 hover:bg-slate-50">
                    <span className="font-mono text-slate-600 w-20">{c.test_case_id}</span>
                    <span className={`px-2 py-0.5 rounded ${STATUS_BADGE[c.status] || 'bg-gray-100'}`}>{c.status}</span>
                    <span className={`px-2 py-0.5 rounded ${FAILURE_COLORS[c.error_type] || ''}`}>
                      {FAILURE_LABELS[c.error_type] || c.error_type || '-'}
                    </span>
                    <span className="flex-1 text-slate-500 truncate">{c.error_message}</span>
                    <span className="text-slate-400">{c.duration_ms}ms</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

function StatCard({ label, value, color = 'text-slate-900' }) {
  return (
    <div className="text-center">
      <div className={`text-xl font-bold ${color}`}>{value}</div>
      <div className="text-xs text-slate-500">{label}</div>
    </div>
  )
}

function ReportCard({ label, value, color = 'text-slate-900' }) {
  return (
    <div className="bg-slate-50 rounded-lg p-3 text-center">
      <div className={`text-lg font-bold ${color}`}>{value}</div>
      <div className="text-xs text-slate-500">{label}</div>
    </div>
  )
}
