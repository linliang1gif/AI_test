import { useState, useEffect } from 'react'
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
  const [reportReady, setReportReady] = useState(false)

  useEffect(() => { loadRunDetail() }, [runId])

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

  const handleGenerateReport = async () => {
    try {
      setReportLoading(true)
      await api.v2.observability.generateReport(runId, 'html')
      setReportReady(true)
      alert('报告生成成功！')
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

  if (loading) return <div className="min-h-screen bg-gray-50 p-6 flex justify-center items-center"><div className="text-gray-500">加载中...</div></div>
  if (error || !run) return <div className="min-h-screen bg-gray-50 p-6"><div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">加载失败: {error || '未找到执行记录'}</div></div>

  const passRate = run.total_cases ? ((run.passed_cases / run.total_cases) * 100).toFixed(1) : 0
  const noAssertionCount = cases.filter(c => c.status === 'no_assertion').length
  const errorCount = cases.filter(c => c.status === 'error').length
  const cd = caseDetail

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <PageHeader
        title={`执行详情`}
        subtitle={run.id}
        action={
          <div className="flex gap-2">
            <button onClick={handleGenerateReport} disabled={reportLoading}
              className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 text-sm">
              {reportLoading ? '生成中...' : '📊 生成报告'}
            </button>
            <button onClick={handleDownloadReport}
              className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 text-sm">
              📥 下载报告
            </button>
            <button onClick={() => navigate('/test-runs-v2')}
              className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 text-sm">
              返回列表
            </button>
          </div>
        }
      />

      {/* 执行概览 */}
      <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
        <div className="grid grid-cols-6 gap-4">
          <div className="text-center">
            <div className="text-xs text-gray-500 mb-1">状态</div>
            <span className={`inline-block px-3 py-1 rounded-full text-sm font-bold ${sc(run.status)}`}>{sl(run.status)}</span>
          </div>
          <div className="text-center">
            <div className="text-xs text-gray-500 mb-1">通过率</div>
            <div className="text-2xl font-bold text-gray-900">{passRate}%</div>
          </div>
          <div className="text-center">
            <div className="text-xs text-gray-500 mb-1">通过</div>
            <div className="text-2xl font-bold text-green-600">{run.passed_cases || 0}</div>
          </div>
          <div className="text-center">
            <div className="text-xs text-gray-500 mb-1">失败</div>
            <div className="text-2xl font-bold text-red-600">{run.failed_cases || 0}</div>
          </div>
          <div className="text-center">
            <div className="text-xs text-gray-500 mb-1">无断言</div>
            <div className="text-2xl font-bold text-yellow-600">{noAssertionCount}</div>
          </div>
          <div className="text-center">
            <div className="text-xs text-gray-500 mb-1">耗时</div>
            <div className="text-2xl font-bold text-gray-900">{fmtSec(run.duration)}</div>
          </div>
        </div>
        <div className="mt-3 pt-3 border-t text-xs text-gray-500 flex gap-6">
          <span>创建: {fmt(run.created_at)}</span>
          <span>触发: {run.trigger_type || 'manual'}</span>
          {run.trace_id && <span>Trace: <code className="font-mono">{run.trace_id}</code></span>}
        </div>
      </div>

      <div className="grid grid-cols-12 gap-6">
        {/* 左侧: 用例列表 */}
        <div className="col-span-4">
          <div className="bg-white rounded-lg shadow-sm p-4">
            <h3 className="text-base font-semibold mb-3">用例列表 ({cases.length})</h3>
            <div className="space-y-2 max-h-[650px] overflow-y-auto">
              {cases.map((c) => (
                <div key={c.id}
                  className={`p-3 rounded border cursor-pointer hover:bg-gray-50 transition ${selectedCase === c.test_case_id ? 'border-blue-500 bg-blue-50' : 'border-gray-200'}`}
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
            <div className="bg-white rounded-lg shadow-sm p-8 text-center text-gray-500">
              <p className="text-lg">← 请选择一个用例查看详情</p>
            </div>
          ) : (
            <div className="space-y-4">
              {/* 用例概览 */}
              <div className="bg-white rounded-lg shadow-sm p-4">
                <div className="flex items-center justify-between mb-3">
                  <h3 className="text-base font-semibold">{cd.test_case_id}</h3>
                  <span className={`px-3 py-1 rounded-full text-sm font-bold ${sc(cd.status)}`}>{sl(cd.status)}</span>
                </div>
                <div className="grid grid-cols-4 gap-3 text-sm">
                  <div><span className="text-gray-500">方法:</span> <span className="font-mono font-bold">{cd.method || '-'}</span></div>
                  <div><span className="text-gray-500">HTTP:</span> {cd.response_status_code || '-'}</div>
                  <div><span className="text-gray-500">耗时:</span> {fmtMs(cd.response_time_ms)}</div>
                  <div><span className="text-gray-500">断言:</span> <span className="text-green-600">{cd.assertions_passed}</span>/<span className="text-red-600">{cd.assertions_failed}</span></div>
                </div>
              </div>

              {/* 错误信息 */}
              {cd.error_message && (
                <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                  <h4 className="text-sm font-semibold text-red-800 mb-1">❌ 错误信息</h4>
                  <div className="text-sm text-red-700">{cd.error_message}</div>
                </div>
              )}

              {/* no_assertion 警告 */}
              {cd.status === 'no_assertion' && (
                <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3">
                  <div className="text-sm text-yellow-800">⚠️ 该用例无自定义断言，建议添加断言规则以确保测试有效性</div>
                </div>
              )}

              {/* 断言详情 */}
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
                            <td className="py-2 px-3 text-center">{a.passed ? <span className="text-green-600 font-bold">✓</span> : <span className="text-red-600 font-bold">✗</span>}</td>
                            <td className="py-2 px-3 text-xs text-gray-500">{a.message || ''}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {/* 请求详情 */}
              {cd.request_snapshot && (
                <div className="bg-white rounded-lg shadow-sm p-4">
                  <div className="flex items-center justify-between mb-3">
                    <h4 className="text-sm font-semibold">📤 请求详情</h4>
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

              {/* 响应详情 */}
              {cd.response_snapshot && (
                <div className="bg-white rounded-lg shadow-sm p-4">
                  <div className="flex items-center justify-between mb-3">
                    <h4 className="text-sm font-semibold">📥 响应详情</h4>
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
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
