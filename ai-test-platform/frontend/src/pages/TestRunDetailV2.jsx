import { useState, useEffect, useMemo } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import api from '../services/api'
import PageHeader from '../components/PageHeader'

const STATUS_LABEL = {passed:'通过',failed:'失败',no_assertion:'无断言',error:'错误',running:'运行中',created:'已创建',pending:'待执行',skipped:'跳过'}
const STATUS_COLOR = {
  passed:'bg-green-100 text-green-800', failed:'bg-red-100 text-red-800',
  no_assertion:'bg-yellow-100 text-yellow-800', error:'bg-red-100 text-red-800',
  running:'bg-purple-100 text-purple-800', pending:'bg-gray-100 text-gray-800',
  created:'bg-gray-100 text-gray-800', skipped:'bg-gray-100 text-gray-800',
}

/* ── SVG 环形图组件 ── */
function DonutChart({ segments, size = 140, strokeWidth = 18, centerLabel, centerSub }) {
  const r = (size - strokeWidth) / 2
  const cx = size / 2, cy = size / 2
  const circumference = 2 * Math.PI * r
  let offset = 0
  return (
    <svg width={size} height={size} className="block mx-auto">
      <circle cx={cx} cy={cy} r={r} fill="none" stroke="#f1f5f9" strokeWidth={strokeWidth} />
      {segments.map((seg, i) => {
        const dash = circumference * (seg.pct / 100)
        const gap = circumference - dash
        const cur = offset
        offset += dash
        return <circle key={i} cx={cx} cy={cy} r={r} fill="none" stroke={seg.color}
          strokeWidth={strokeWidth} strokeDasharray={`${dash} ${gap}`}
          strokeDashoffset={-cur} strokeLinecap="butt"
          transform={`rotate(-90 ${cx} ${cy})`} />
      })}
      <text x={cx} y={cy - 6} textAnchor="middle" className="fill-gray-900 text-2xl font-bold" style={{fontSize:'1.5rem',fontWeight:700}}>{centerLabel}</text>
      <text x={cx} y={cy + 14} textAnchor="middle" className="fill-gray-400" style={{fontSize:'0.7rem'}}>{centerSub}</text>
    </svg>
  )
}

/* ── 根因分析辅助 ── */
function classifyError(c) {
  const err = (c.error_message || '').toLowerCase()
  const code = c.response_status_code
  if (err.includes('timeout') || err.includes('timed out')) return { type: 'timeout', label: '超时', color: 'bg-orange-100 text-orange-800' }
  if (err.includes('connect') || err.includes('unreachable') || err.includes('refused')) return { type: 'network', label: '网络错误', color: 'bg-red-100 text-red-800' }
  if (code === 401 || code === 402 || code === 403 || code === 405 || err.includes('token') || err.includes('unauthorized') || err.includes('认证')) return { type: 'auth', label: '认证失败', color: 'bg-purple-100 text-purple-800' }
  if (code >= 500) return { type: 'server', label: '服务端错误', color: 'bg-red-100 text-red-800' }
  if (code >= 400 && code < 500) return { type: 'client', label: '请求错误', color: 'bg-yellow-100 text-yellow-800' }
  if (err.includes('业务响应码') || err.includes('code=')) return { type: 'business', label: '业务码异常', color: 'bg-amber-100 text-amber-800' }
  if (err.includes('断言') || err.includes('assert')) return { type: 'assertion', label: '断言失败', color: 'bg-pink-100 text-pink-800' }
  if (err.includes('变量') || err.includes('variable')) return { type: 'variable', label: '变量缺失', color: 'bg-indigo-100 text-indigo-800' }
  if (c.status === 'failed') return { type: 'assertion', label: '断言失败', color: 'bg-pink-100 text-pink-800' }
  if (c.status === 'error') return { type: 'unknown', label: '未知错误', color: 'bg-gray-100 text-gray-800' }
  return null
}

function extractModule(c) {
  const url = c.request_url || c.url || ''
  const match = url.match(/\/(basic|order|wms|tms|srm|crm|finance|quality|system|userCenter|bound|bom|applet|wechat)\b/)
  if (match) return match[1]
  const pathParts = url.replace(/https?:\/\/[^/]+/, '').split('/').filter(Boolean)
  if (pathParts.length >= 2) return '/' + pathParts.slice(0, 2).join('/')
  return '未分类'
}

export default function TestRunDetailV2() {
  const { runId } = useParams()
  const navigate = useNavigate()
  const [run, setRun] = useState(null)
  const [cases, setCases] = useState([])
  const [selectedCase, setSelectedCase] = useState(null)
  const [caseDetail, setCaseDetail] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [reportLoading, setReportLoading] = useState(false)
  const [reportId, setReportId] = useState(null)
  const [statusFilter, setStatusFilter] = useState('all')
  const [viewMode, setViewMode] = useState('list')
  const [activeTab, setActiveTab] = useState('overview')
  const [faLoading, setFaLoading] = useState(false)
  const [faResults, setFaResults] = useState([])
  const [faSummary, setFaSummary] = useState(null)

  useEffect(() => { loadRunDetail(); checkReport() }, [runId])

  const checkReport = async () => {
    try {
      const data = await api.reports.getByRunId(runId)
      const items = data?.items || []
      if (items.length > 0) setReportId(items[0].report_id)
    } catch {}
  }

  const loadRunDetail = async () => {
    try {
      setLoading(true); setError(null)
      const res = await api.v2.observability.getRunDetail(runId)
      setRun(res.data)
      setCases(res.data?.run_cases || [])
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const loadCaseDetail = async (c) => {
    setSelectedCase(c.test_case_id)
    try {
      const res = await api.v2.observability.getRunCaseDetail(runId, c.test_case_id)
      setCaseDetail(res.data)
    } catch {
      setCaseDetail(c)
    }
  }

  const loadFailureAnalysis = async () => {
    try {
      const res = await fetch(`/api/v2/web-ui/runs/${runId}/failure-analysis`)
      const data = await res.json()
      if (data.analyses?.length) { setFaResults(data.analyses); setFaSummary(data.summary) }
    } catch {}
  }
  useEffect(() => { loadFailureAnalysis() }, [runId])

  const handleRunFailureAnalysis = async () => {
    try {
      setFaLoading(true)
      const res = await fetch(`/api/v2/web-ui/runs/${runId}/failure-analysis`, { method: 'POST' })
      const data = await res.json()
      setFaResults(data.analyses || [])
      setFaSummary(data.summary || null)
      if (data.analyses?.length) setActiveTab('ai-analysis')
    } catch (err) {
      alert('归因分析失败: ' + err.message)
    } finally {
      setFaLoading(false)
    }
  }

  const handleGenerateReport = async () => {
    try {
      setReportLoading(true)
      await api.v2.observability.generateReport(runId, 'html')
      await checkReport()
    } catch (err) {
      alert('报告生成失败: ' + err.message)
    } finally {
      setReportLoading(false)
    }
  }

  const handleDownloadReport = () => {
    window.open(api.v2.observability.downloadReport(runId, 'html'), '_blank')
  }

  const fmt = (s) => s ? new Date(s).toLocaleString('zh-CN') : 'N/A'
  const fmtMs = (ms) => ms ? `${Number(ms).toFixed(0)}ms` : 'N/A'
  const fmtSec = (s) => s ? `${Number(s).toFixed(2)}s` : 'N/A'
  const sc = (status) => STATUS_COLOR[status] || 'bg-gray-100 text-gray-800'
  const sl = (status) => STATUS_LABEL[status] || status

  const copyText = (text) => {
    navigator.clipboard.writeText(text).then(() => alert('已复制'))
  }

  // 计算统计
  const stats = useMemo(() => {
    const total = cases.length
    const passed = cases.filter(c => c.status === 'passed').length
    const failed = cases.filter(c => c.status === 'failed').length
    const noAssertion = cases.filter(c => c.status === 'no_assertion').length
    const errored = cases.filter(c => c.status === 'error').length
    return { total, passed, failed, noAssertion, errored }
  }, [cases])

  // 环形图数据
  const donutSegments = useMemo(() => {
    if (!stats.total) return []
    const segs = []
    if (stats.passed) segs.push({ pct: (stats.passed / stats.total) * 100, color: '#22c55e' })
    if (stats.failed) segs.push({ pct: (stats.failed / stats.total) * 100, color: '#ef4444' })
    if (stats.noAssertion) segs.push({ pct: (stats.noAssertion / stats.total) * 100, color: '#eab308' })
    if (stats.errored) segs.push({ pct: (stats.errored / stats.total) * 100, color: '#f97316' })
    return segs
  }, [stats])

  // 根因分析
  const failureAnalysis = useMemo(() => {
    const failedCases = cases.filter(c => c.status === 'failed' || c.status === 'error')
    const groups = {}
    failedCases.forEach(c => {
      const cls = classifyError(c)
      if (!cls) return
      if (!groups[cls.type]) groups[cls.type] = { ...cls, cases: [] }
      groups[cls.type].cases.push(c)
    })
    return Object.values(groups).sort((a, b) => b.cases.length - a.cases.length)
  }, [cases])

  // 按模块分组
  const moduleGroups = useMemo(() => {
    const groups = {}
    cases.forEach(c => {
      const mod = extractModule(c)
      if (!groups[mod]) groups[mod] = { module: mod, cases: [], passed: 0, failed: 0, error: 0 }
      groups[mod].cases.push(c)
      if (c.status === 'passed') groups[mod].passed++
      else if (c.status === 'failed') groups[mod].failed++
      else if (c.status === 'error') groups[mod].error++
    })
    return Object.values(groups).sort((a, b) => b.cases.length - a.cases.length)
  }, [cases])

  // 过滤用例
  const filteredCases = useMemo(() => {
    if (statusFilter === 'all') return cases
    return cases.filter(c => c.status === statusFilter)
  }, [cases, statusFilter])

  if (loading) return <div className="min-h-screen bg-gray-50 p-6 flex justify-center items-center"><div className="text-gray-500">加载中...</div></div>
  if (error || !run) return <div className="min-h-screen bg-gray-50 p-6"><div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">加载失败: {error || '未找到执行记录'}</div></div>

  const passRate = run.total_cases ? ((run.passed_cases / run.total_cases) * 100).toFixed(1) : 0
  const cd = caseDetail

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <PageHeader
        title="执行详情"
        subtitle={run.id}
        action={
          <div className="flex gap-2">
            <button onClick={handleGenerateReport} disabled={reportLoading}
              className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 text-sm">
              {reportLoading ? '生成中...' : reportId ? '重新生成报告' : '生成报告'}
            </button>
            {reportId && (
              <button onClick={() => navigate(`/reports/${reportId}`)}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm">
                查看报告
              </button>
            )}
            <button onClick={handleRunFailureAnalysis} disabled={faLoading}
              className="px-4 py-2 bg-amber-600 text-white rounded-lg hover:bg-amber-700 disabled:opacity-50 text-sm">
              {faLoading ? '分析中...' : faResults.length ? '重新归因分析' : '失败归因分析'}
            </button>
            <button onClick={handleDownloadReport}
              className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 text-sm">
              下载HTML
            </button>
            <button onClick={() => navigate('/test-runs-v2')}
              className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 text-sm">
              返回列表
            </button>
          </div>
        }
      />

      {/* ═══ 执行概览 ═══ */}
      <div className="bg-white rounded-xl shadow-sm p-6 mb-6">
        <div className="flex items-center gap-8">
          {/* 环形图 */}
          <div className="flex-shrink-0">
            <DonutChart
              segments={donutSegments}
              centerLabel={`${passRate}%`}
              centerSub="通过率"
            />
          </div>
          {/* 统计卡片 */}
          <div className="flex-1 grid grid-cols-5 gap-3">
            <div className="rounded-lg bg-gray-50 p-4 text-center">
              <div className="text-xs text-gray-500 mb-1">总用例</div>
              <div className="text-2xl font-bold text-gray-900">{stats.total}</div>
            </div>
            <div className="rounded-lg bg-green-50 p-4 text-center">
              <div className="text-xs text-green-600 mb-1">通过</div>
              <div className="text-2xl font-bold text-green-600">{stats.passed}</div>
            </div>
            <div className="rounded-lg bg-red-50 p-4 text-center">
              <div className="text-xs text-red-600 mb-1">失败</div>
              <div className="text-2xl font-bold text-red-600">{stats.failed}</div>
            </div>
            <div className="rounded-lg bg-yellow-50 p-4 text-center">
              <div className="text-xs text-yellow-600 mb-1">无断言</div>
              <div className="text-2xl font-bold text-yellow-600">{stats.noAssertion}</div>
            </div>
            <div className="rounded-lg bg-orange-50 p-4 text-center">
              <div className="text-xs text-orange-600 mb-1">错误</div>
              <div className="text-2xl font-bold text-orange-600">{stats.errored}</div>
            </div>
          </div>
        </div>
        {/* 进度条 */}
        {stats.total > 0 && (
          <div className="mt-4 h-2.5 bg-gray-100 rounded-full overflow-hidden flex">
            {stats.passed > 0 && <div className="bg-green-500 h-full" style={{width: `${(stats.passed/stats.total)*100}%`}} />}
            {stats.failed > 0 && <div className="bg-red-500 h-full" style={{width: `${(stats.failed/stats.total)*100}%`}} />}
            {stats.noAssertion > 0 && <div className="bg-yellow-400 h-full" style={{width: `${(stats.noAssertion/stats.total)*100}%`}} />}
            {stats.errored > 0 && <div className="bg-orange-400 h-full" style={{width: `${(stats.errored/stats.total)*100}%`}} />}
          </div>
        )}
        <div className="mt-3 pt-3 border-t text-xs text-gray-500 flex gap-6">
          <span>创建: {fmt(run.created_at)}</span>
          <span>耗时: {fmtSec(run.duration)}</span>
          <span>触发: {run.trigger_type || 'manual'}</span>
          {run.trigger_type === 'suite' && (() => { try { const s = JSON.parse(run.summary || '{}')?.suite_summary; return s ? <span className="text-blue-600">测试集: {s.suite_name} ({s.suite_type})</span> : null } catch { return null } })()}
          {run.trace_id && <span>Trace: <code className="font-mono">{run.trace_id}</code></span>}
        </div>
      </div>

      {/* ═══ Tab 导航 ═══ */}
      <div className="bg-white rounded-t-xl shadow-sm border-b mb-0">
        <div className="flex">
          {[
            { key: 'overview', label: '用例详情' },
            { key: 'modules', label: '模块分组' },
            { key: 'failures', label: `根因分析${failureAnalysis.length ? ` (${cases.filter(c=>c.status==='failed'||c.status==='error').length})` : ''}` },
            ...(faResults.length ? [{ key: 'ai-analysis', label: `归因结果 (${faResults.length})` }] : []),
          ].map(tab => (
            <button key={tab.key} onClick={() => setActiveTab(tab.key)}
              className={`px-6 py-3 text-sm font-medium border-b-2 transition ${
                activeTab === tab.key
                  ? 'border-blue-600 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}>
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* ═══ Tab: 用例详情 ═══ */}
      {activeTab === 'overview' && (
        <div className="grid grid-cols-12 gap-6 mt-6">
          {/* 左侧: 用例列表 */}
          <div className="col-span-4">
            <div className="bg-white rounded-lg shadow-sm">
              {/* 状态过滤 */}
              <div className="p-3 border-b flex flex-wrap gap-1.5">
                {[
                  { key: 'all', label: '全部', count: cases.length },
                  { key: 'passed', label: '通过', count: stats.passed },
                  { key: 'failed', label: '失败', count: stats.failed },
                  { key: 'error', label: '错误', count: stats.errored },
                  { key: 'no_assertion', label: '无断言', count: stats.noAssertion },
                ].filter(f => f.key === 'all' || f.count > 0).map(f => (
                  <button key={f.key} onClick={() => setStatusFilter(f.key)}
                    className={`px-2.5 py-1 rounded-full text-xs font-medium transition ${
                      statusFilter === f.key
                        ? 'bg-blue-600 text-white'
                        : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                    }`}>
                    {f.label} ({f.count})
                  </button>
                ))}
              </div>
              <div className="p-3 space-y-2 max-h-[600px] overflow-y-auto">
                {filteredCases.length === 0 && (
                  <div className="text-center text-gray-400 py-8 text-sm">无匹配用例</div>
                )}
                {filteredCases.map((c) => (
                  <div key={c.id}
                    className={`p-3 rounded-lg border cursor-pointer hover:bg-gray-50 transition ${selectedCase === c.test_case_id ? 'border-blue-500 bg-blue-50 shadow-sm' : 'border-gray-200'}`}
                    onClick={() => loadCaseDetail(c)}>
                    <div className="flex items-center justify-between mb-1">
                      <span className="font-medium text-sm truncate flex-1 mr-2">{c.test_case_id}</span>
                      <span className={`px-2 py-0.5 rounded text-xs whitespace-nowrap ${sc(c.status)}`}>{sl(c.status)}</span>
                    </div>
                    <div className="flex items-center gap-3 text-xs text-gray-500">
                      {c.method && <span className="font-mono font-bold">{c.method}</span>}
                      {c.response_status_code > 0 && <span>HTTP {c.response_status_code}</span>}
                      <span>{fmtMs(c.response_time_ms)}</span>
                      {(c.assertions_passed > 0 || c.assertions_failed > 0) && (
                        <span>断言 <span className="text-green-600">{c.assertions_passed}</span>/<span className="text-red-600">{c.assertions_failed}</span></span>
                      )}
                    </div>
                    {c.error_message && <div className="text-xs text-red-600 mt-1 truncate">{c.error_message}</div>}
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* 右侧: 用例详情 */}
          <div className="col-span-8">
            {!cd ? (
              <div className="bg-white rounded-lg shadow-sm p-12 text-center text-gray-400">
                <div className="text-4xl mb-3">&#8592;</div>
                <p className="text-base">请选择一个用例查看详情</p>
              </div>
            ) : (
              <div className="space-y-4">
                {/* 用例概览 */}
                <div className="bg-white rounded-lg shadow-sm p-4">
                  <div className="flex items-center justify-between mb-3">
                    <h3 className="text-base font-semibold truncate flex-1 mr-3">{cd.test_case_id}</h3>
                    <span className={`px-3 py-1 rounded-full text-sm font-bold ${sc(cd.status)}`}>{sl(cd.status)}</span>
                  </div>
                  <div className="grid grid-cols-4 gap-3 text-sm">
                    <div><span className="text-gray-500">方法:</span> <span className="font-mono font-bold">{cd.method || '-'}</span></div>
                    <div><span className="text-gray-500">HTTP:</span> {cd.response_status_code || '-'}</div>
                    <div><span className="text-gray-500">耗时:</span> {fmtMs(cd.response_time_ms)}</div>
                    <div><span className="text-gray-500">断言:</span> <span className="text-green-600">{cd.assertions_passed}</span>/<span className="text-red-600">{cd.assertions_failed}</span></div>
                  </div>
                </div>

                {cd.error_message && (
                  <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                    <h4 className="text-sm font-semibold text-red-800 mb-1">错误信息</h4>
                    <div className="text-sm text-red-700">{cd.error_message}</div>
                  </div>
                )}

                {cd.status === 'no_assertion' && (
                  <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3">
                    <div className="text-sm text-yellow-800">该用例无自定义断言，建议添加断言规则以确保测试有效性</div>
                  </div>
                )}

                {cd.assertion_details && cd.assertion_details.length > 0 && (
                  <div className="bg-white rounded-lg shadow-sm p-4">
                    <h4 className="text-sm font-semibold mb-3">断言详情</h4>
                    <div className="border rounded overflow-hidden">
                      <table className="w-full text-sm">
                        <thead className="bg-gray-50">
                          <tr>
                            <th className="py-2 px-3 text-left text-xs">类型</th>
                            <th className="py-2 px-3 text-left text-xs">路径</th>
                            <th className="py-2 px-3 text-left text-xs">期望值</th>
                            <th className="py-2 px-3 text-left text-xs">实际值</th>
                            <th className="py-2 px-3 text-center text-xs">结果</th>
                            <th className="py-2 px-3 text-left text-xs">说明</th>
                          </tr>
                        </thead>
                        <tbody>
                          {cd.assertion_details.map((a, i) => (
                            <tr key={i} className={`border-t ${a.passed ? '' : 'bg-red-50'}`}>
                              <td className="py-2 px-3 font-mono text-xs">{a.type}</td>
                              <td className="py-2 px-3 font-mono text-xs">{a.path || '-'}</td>
                              <td className="py-2 px-3 text-xs max-w-[120px] truncate">{JSON.stringify(a.expected)}</td>
                              <td className="py-2 px-3 text-xs max-w-[120px] truncate">{JSON.stringify(a.actual)}</td>
                              <td className="py-2 px-3 text-center">{a.passed ? <span className="text-green-600 font-bold">&#10003;</span> : <span className="text-red-600 font-bold">&#10007;</span>}</td>
                              <td className="py-2 px-3 text-xs text-gray-500">{a.message || ''}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}

                {cd.request_snapshot && (
                  <div className="bg-white rounded-lg shadow-sm p-4">
                    <div className="flex items-center justify-between mb-3">
                      <h4 className="text-sm font-semibold">请求详情</h4>
                      <button onClick={() => copyText(JSON.stringify(cd.request_snapshot, null, 2))} className="text-xs text-blue-600 hover:underline">复制</button>
                    </div>
                    <div className="space-y-2 text-xs">
                      <div className="flex gap-2">
                        <span className="font-mono font-bold bg-blue-100 text-blue-800 px-2 py-0.5 rounded">{cd.request_snapshot.method}</span>
                        <span className="font-mono break-all">{cd.request_snapshot.url}</span>
                      </div>
                      {cd.request_snapshot.headers && Object.keys(cd.request_snapshot.headers).length > 0 && (
                        <details>
                          <summary className="cursor-pointer text-gray-600 font-medium">Headers</summary>
                          <pre className="mt-1 bg-gray-900 text-green-400 p-3 rounded text-xs overflow-auto max-h-40">{JSON.stringify(cd.request_snapshot.headers, null, 2)}</pre>
                        </details>
                      )}
                      {cd.request_snapshot.body && (
                        <details open>
                          <summary className="cursor-pointer text-gray-600 font-medium">Body</summary>
                          <pre className="mt-1 bg-gray-900 text-green-400 p-3 rounded text-xs overflow-auto max-h-48">{typeof cd.request_snapshot.body === 'string' ? cd.request_snapshot.body : JSON.stringify(cd.request_snapshot.body, null, 2)}</pre>
                        </details>
                      )}
                    </div>
                  </div>
                )}

                {cd.response_snapshot && (
                  <div className="bg-white rounded-lg shadow-sm p-4">
                    <div className="flex items-center justify-between mb-3">
                      <h4 className="text-sm font-semibold">响应详情</h4>
                      <button onClick={() => copyText(JSON.stringify(cd.response_snapshot, null, 2))} className="text-xs text-blue-600 hover:underline">复制</button>
                    </div>
                    <div className="space-y-2 text-xs">
                      <div className="flex gap-4">
                        <span>状态码: <span className={`font-bold ${cd.response_snapshot.status_code < 400 ? 'text-green-600' : 'text-red-600'}`}>{cd.response_snapshot.status_code}</span></span>
                        <span>耗时: {fmtMs(cd.response_snapshot.elapsed_ms)}</span>
                      </div>
                      {cd.response_snapshot.headers && Object.keys(cd.response_snapshot.headers).length > 0 && (
                        <details>
                          <summary className="cursor-pointer text-gray-600 font-medium">Headers</summary>
                          <pre className="mt-1 bg-gray-900 text-blue-400 p-3 rounded text-xs overflow-auto max-h-40">{JSON.stringify(cd.response_snapshot.headers, null, 2)}</pre>
                        </details>
                      )}
                      {cd.response_snapshot.body && (
                        <details open>
                          <summary className="cursor-pointer text-gray-600 font-medium">Body</summary>
                          <pre className="mt-1 bg-gray-900 text-blue-400 p-3 rounded text-xs overflow-auto max-h-64">{typeof cd.response_snapshot.body === 'string' ? cd.response_snapshot.body : JSON.stringify(cd.response_snapshot.body, null, 2)}</pre>
                        </details>
                      )}
                    </div>
                  </div>
                )}

                {/* P2-7: Trace / Console / Network 证据块 */}
                {cd.response_snapshot?.trace_path && (
                  <div className="bg-white rounded-lg shadow-sm p-4">
                    <h4 className="text-sm font-semibold mb-2">Playwright Trace</h4>
                    <a href={`/api/v2/web-ui/traces/${cd.response_snapshot.trace_path.replace(/\\/g, '/').split('/').pop()}`} target="_blank" rel="noreferrer"
                       className="inline-flex items-center gap-1 px-3 py-1.5 bg-violet-50 text-violet-700 rounded border border-violet-200 text-xs hover:bg-violet-100">
                      下载 trace.zip
                    </a>
                    <p className="mt-2 text-xs text-amber-600">⚠️ Trace 可能包含页面截图和调试信息，请勿外传。</p>
                  </div>
                )}

                {cd.response_snapshot?.console_logs && cd.response_snapshot.console_logs.length > 0 && (
                  <div className="bg-white rounded-lg shadow-sm p-4">
                    <h4 className="text-sm font-semibold mb-2">Console 日志 ({cd.response_snapshot.console_error_count || cd.response_snapshot.console_logs.length})</h4>
                    <div className="space-y-1 max-h-40 overflow-y-auto">
                      {cd.response_snapshot.console_logs.map((log, i) => (
                        <div key={i} className={`text-xs p-1.5 rounded ${log.type === 'error' ? 'bg-red-50 text-red-700' : 'bg-yellow-50 text-yellow-700'}`}>
                          <span className="font-mono font-bold">[{log.type}]</span> {log.text?.slice(0, 200)}
                          {log.location && <span className="text-gray-400 ml-1">@ {log.location}</span>}
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {cd.response_snapshot?.network_errors && cd.response_snapshot.network_errors.length > 0 && (
                  <div className="bg-white rounded-lg shadow-sm p-4">
                    <h4 className="text-sm font-semibold mb-2">Network 错误 ({cd.response_snapshot.network_error_count || cd.response_snapshot.network_errors.length})</h4>
                    <div className="space-y-1 max-h-40 overflow-y-auto">
                      {cd.response_snapshot.network_errors.map((ne, i) => (
                        <div key={i} className="text-xs p-1.5 rounded bg-red-50 text-red-700 flex gap-2">
                          <span className="font-mono">{ne.method}</span>
                          <span className="truncate flex-1">{ne.url}</span>
                          {ne.status && <span className="font-bold">{ne.status}</span>}
                          {ne.failure_text && <span className="text-gray-500">{ne.failure_text}</span>}
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* P2-9B: Web UI 稳定性信息 */}
                {cd.response_snapshot?.retry_attempt > 0 && (
                  <div className="bg-white rounded-lg shadow-sm p-4">
                    <h4 className="text-sm font-semibold mb-2">重试信息</h4>
                    <div className="flex gap-3 text-xs">
                      <span className="px-2 py-1 bg-yellow-100 text-yellow-700 rounded">重试 {cd.response_snapshot.retry_attempt} 次</span>
                      {cd.response_snapshot.flaky_candidate && <span className="px-2 py-1 bg-orange-100 text-orange-700 rounded">⚠ flaky_candidate</span>}
                      {cd.response_snapshot.recovered_by_retry && <span className="px-2 py-1 bg-green-100 text-green-700 rounded">✓ 重试后恢复</span>}
                      {cd.response_snapshot.first_failure_category && <span className="px-2 py-1 bg-gray-100 text-gray-600 rounded">首次: {cd.response_snapshot.first_failure_category}</span>}
                    </div>
                  </div>
                )}

                {cd.response_snapshot?.selector_score != null && (
                  <div className="bg-white rounded-lg shadow-sm p-4">
                    <h4 className="text-sm font-semibold mb-2">Selector 稳定性</h4>
                    <div className="flex items-center gap-3">
                      <span className={`text-lg font-bold ${cd.response_snapshot.selector_score >= 80 ? 'text-green-600' : cd.response_snapshot.selector_score >= 50 ? 'text-yellow-600' : 'text-red-600'}`}>
                        {cd.response_snapshot.selector_score}分
                      </span>
                      {cd.response_snapshot.unstable_selectors?.length > 0 && (
                        <span className="text-xs text-orange-600">{cd.response_snapshot.unstable_selectors.length} 个低稳定 selector</span>
                      )}
                    </div>
                    {cd.response_snapshot.unstable_selectors?.length > 0 && (
                      <div className="mt-2 space-y-1">
                        {cd.response_snapshot.unstable_selectors.map((s, i) => (
                          <div key={i} className="text-xs p-1.5 bg-orange-50 rounded flex gap-2">
                            <span className="text-gray-500">步骤 {s.step_index + 1}</span>
                            <code className="font-mono text-orange-700">{s.target}</code>
                            <span className="text-gray-500">{s.reason}</span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}

                {cd.response_snapshot?.wait_warnings?.length > 0 && (
                  <div className="bg-white rounded-lg shadow-sm p-4">
                    <h4 className="text-sm font-semibold mb-2">等待策略警告</h4>
                    <div className="space-y-1">
                      {cd.response_snapshot.wait_warnings.map((w, i) => (
                        <div key={i} className="text-xs p-1.5 bg-yellow-50 rounded flex gap-2">
                          <span className="text-gray-500">步骤 {w.step_index + 1}</span>
                          <span className="text-yellow-700">{w.reason}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      )}
      {/* ═══ Tab: 模块分组 ═══ */}
      {activeTab === 'modules' && (
        <div className="mt-6 space-y-4">
          {moduleGroups.length === 0 ? (
            <div className="bg-white rounded-lg shadow-sm p-8 text-center text-gray-400">无用例数据</div>
          ) : moduleGroups.map(g => {
            const total = g.cases.length
            const pRate = total ? ((g.passed / total) * 100).toFixed(0) : 0
            return (
              <div key={g.module} className="bg-white rounded-lg shadow-sm p-5">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-3">
                    <span className="font-mono text-sm font-bold bg-slate-100 px-3 py-1 rounded">{g.module}</span>
                    <span className="text-sm text-gray-500">{total} 个用例</span>
                  </div>
                  <div className="flex items-center gap-4 text-sm">
                    <span className="text-green-600 font-medium">{g.passed} 通过</span>
                    <span className="text-red-600 font-medium">{g.failed} 失败</span>
                    <span className="text-orange-600 font-medium">{g.error} 错误</span>
                    <span className={`font-bold ${Number(pRate) >= 80 ? 'text-green-600' : Number(pRate) >= 50 ? 'text-yellow-600' : 'text-red-600'}`}>
                      {pRate}%
                    </span>
                  </div>
                </div>
                {/* 模块内进度条 */}
                <div className="h-2 bg-gray-100 rounded-full overflow-hidden flex">
                  {g.passed > 0 && <div className="bg-green-500 h-full" style={{width: `${(g.passed/total)*100}%`}} />}
                  {g.failed > 0 && <div className="bg-red-500 h-full" style={{width: `${(g.failed/total)*100}%`}} />}
                  {g.error > 0 && <div className="bg-orange-400 h-full" style={{width: `${(g.error/total)*100}%`}} />}
                  {(total - g.passed - g.failed - g.error) > 0 && <div className="bg-yellow-300 h-full" style={{width: `${((total - g.passed - g.failed - g.error)/total)*100}%`}} />}
                </div>
                {/* 模块内失败用例展示 */}
                {g.cases.filter(c => c.status === 'failed' || c.status === 'error').length > 0 && (
                  <div className="mt-3 pt-3 border-t">
                    <div className="text-xs text-gray-500 mb-2">失败/错误用例:</div>
                    <div className="space-y-1.5">
                      {g.cases.filter(c => c.status === 'failed' || c.status === 'error').map(c => (
                        <div key={c.id} className="flex items-center gap-2 text-xs">
                          <span className={`px-1.5 py-0.5 rounded text-xs ${sc(c.status)}`}>{sl(c.status)}</span>
                          <span className="font-mono text-gray-700 truncate flex-1">{c.test_case_id}</span>
                          {c.error_message && <span className="text-red-500 truncate max-w-[300px]">{c.error_message}</span>}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )
          })}
        </div>
      )}

      {/* ═══ Tab: 根因分析 ═══ */}
      {activeTab === 'failures' && (
        <div className="mt-6 space-y-4">
          {failureAnalysis.length === 0 ? (
            <div className="bg-white rounded-lg shadow-sm p-12 text-center">
              <div className="text-4xl mb-3 text-green-400">&#10003;</div>
              <p className="text-gray-500">所有用例均通过，无失败用例</p>
            </div>
          ) : (
            <>
              {/* 根因分布汇总 */}
              <div className="bg-white rounded-lg shadow-sm p-5">
                <h3 className="text-sm font-semibold mb-4">失败根因分布</h3>
                <div className="flex flex-wrap gap-3">
                  {failureAnalysis.map(g => (
                    <div key={g.type} className={`px-4 py-3 rounded-lg ${g.color} flex items-center gap-2`}>
                      <span className="text-2xl font-bold">{g.cases.length}</span>
                      <span className="text-sm">{g.label}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* 各根因类别详情 */}
              {failureAnalysis.map(g => (
                <div key={g.type} className="bg-white rounded-lg shadow-sm p-5">
                  <div className="flex items-center gap-3 mb-3">
                    <span className={`px-3 py-1 rounded-full text-sm font-bold ${g.color}`}>{g.label}</span>
                    <span className="text-sm text-gray-500">{g.cases.length} 个用例</span>
                  </div>
                  <div className="space-y-2">
                    {g.cases.map(c => (
                      <div key={c.id}
                        className="p-3 rounded border border-gray-200 hover:bg-gray-50 cursor-pointer transition"
                        onClick={() => { setActiveTab('overview'); setStatusFilter('all'); loadCaseDetail(c); }}>
                        <div className="flex items-center justify-between mb-1">
                          <span className="font-medium text-sm truncate flex-1 mr-2 font-mono">{c.test_case_id}</span>
                          {c.method && <span className="font-mono text-xs font-bold text-blue-700 bg-blue-50 px-2 py-0.5 rounded mr-2">{c.method}</span>}
                          <span className="text-xs text-gray-500">{fmtMs(c.response_time_ms)}</span>
                        </div>
                        {c.error_message && (
                          <div className="text-xs text-red-600 mt-1 bg-red-50 p-2 rounded">{c.error_message}</div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </>
          )}
        </div>
      )}
      {/* ═══ Tab: AI/规则归因结果 (P2-8) ═══ */}
      {activeTab === 'ai-analysis' && (
        <div className="mt-6 space-y-4">
          {/* 归因汇总 */}
          {faSummary && (
            <div className="bg-white rounded-lg shadow-sm p-5">
              <h3 className="text-sm font-semibold mb-4">归因分析汇总</h3>
              <div className="grid grid-cols-6 gap-3">
                <div className="rounded-lg bg-gray-50 p-3 text-center">
                  <div className="text-xs text-gray-500 mb-1">分析总数</div>
                  <div className="text-xl font-bold">{faSummary.total_analyzed}</div>
                </div>
                <div className="rounded-lg bg-amber-50 p-3 text-center">
                  <div className="text-xs text-amber-600 mb-1">高置信度</div>
                  <div className="text-xl font-bold text-amber-600">{faSummary.high_confidence_count}</div>
                </div>
                <div className="rounded-lg bg-red-50 p-3 text-center">
                  <div className="text-xs text-red-600 mb-1">建议提 Bug</div>
                  <div className="text-xl font-bold text-red-600">{faSummary.should_create_bug_count}</div>
                </div>
                <div className="rounded-lg bg-blue-50 p-3 text-center">
                  <div className="text-xs text-blue-600 mb-1">建议重试</div>
                  <div className="text-xl font-bold text-blue-600">{faSummary.should_retry_count}</div>
                </div>
                <div className="rounded-lg bg-violet-50 p-3 text-center">
                  <div className="text-xs text-violet-600 mb-1">更新 Selector</div>
                  <div className="text-xl font-bold text-violet-600">{faSummary.should_update_selector_count}</div>
                </div>
                <div className="rounded-lg bg-teal-50 p-3 text-center">
                  <div className="text-xs text-teal-600 mb-1">更新 Baseline</div>
                  <div className="text-xl font-bold text-teal-600">{faSummary.should_update_baseline_count}</div>
                </div>
              </div>
              {/* 分类分布 */}
              {faSummary.category_distribution && (
                <div className="mt-4 flex flex-wrap gap-2">
                  {Object.entries(faSummary.category_distribution).map(([cat, cnt]) => (
                    <span key={cat} className="px-3 py-1 bg-gray-100 rounded-full text-xs font-medium">{cat}: {cnt}</span>
                  ))}
                </div>
              )}
            </div>
          )}
          {/* 归因卡片 */}
          {faResults.map((a, i) => (
            <div key={i} className="bg-white rounded-lg shadow-sm p-5 border-l-4" style={{borderLeftColor: a.confidence >= 0.8 ? '#f59e0b' : '#9ca3af'}}>
              <div className="flex items-center gap-3 mb-3">
                <span className="px-3 py-1 bg-amber-100 text-amber-800 rounded-full text-xs font-bold">{a.failure_category}</span>
                <span className="text-xs text-gray-500">置信度: <strong>{(a.confidence * 100).toFixed(0)}%</strong></span>
                <span className={`text-xs px-2 py-0.5 rounded ${a.analysis_mode === 'ai' ? 'bg-purple-100 text-purple-700' : 'bg-gray-100 text-gray-600'}`}>{a.analysis_mode === 'ai' ? 'AI' : '规则'}</span>
                <span className="text-xs text-gray-400 font-mono">{(a.case_id || '').slice(0, 16)}</span>
              </div>
              <p className="text-sm text-gray-800 mb-2">{a.root_cause_summary}</p>
              {a.evidence?.length > 0 && (
                <div className="bg-gray-50 rounded p-3 mb-2">
                  <div className="text-xs font-semibold text-gray-500 mb-1">证据</div>
                  {a.evidence.map((e, j) => <div key={j} className="text-xs text-gray-600 font-mono truncate">{e}</div>)}
                </div>
              )}
              <p className="text-sm text-blue-700 mb-2">{a.suggested_action}</p>
              <div className="flex gap-3 text-xs">
                {a.should_retry && <span className="px-2 py-1 bg-blue-50 text-blue-700 rounded">建议重试</span>}
                {a.should_create_bug && <span className="px-2 py-1 bg-red-50 text-red-700 rounded">建议提 Bug</span>}
                {a.should_update_selector && <span className="px-2 py-1 bg-violet-50 text-violet-700 rounded">更新 Selector</span>}
                {a.should_update_baseline && <span className="px-2 py-1 bg-teal-50 text-teal-700 rounded">更新 Baseline</span>}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
