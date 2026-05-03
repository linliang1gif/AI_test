import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { reportsAPI } from '../services/api'

export default function ReportDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [loading, setLoading] = useState(true)
  const [report, setReport] = useState(null)

  useEffect(() => { loadReport() }, [id])

  const loadReport = async () => {
    setLoading(true)
    try {
      const data = await reportsAPI.get(id)
      setReport(data)
    } catch (error) {
      console.error(error)
      setReport(null)
    } finally {
      setLoading(false)
    }
  }

  if (loading) return <div className="min-h-screen bg-slate-50 flex items-center justify-center text-slate-600">加载中...</div>

  if (!report) {
    return (
      <div className="min-h-screen bg-slate-50 flex flex-col items-center justify-center gap-4">
        <p className="text-lg text-slate-500">报告不存在或尚未生成。</p>
        <button onClick={() => navigate('/reports')} className="px-4 py-2 bg-slate-700 text-white rounded-lg text-sm">返回列表</button>
      </div>
    )
  }

  const run = report.run
  const getColor = (rate) => rate >= 90 ? 'text-green-600' : rate >= 75 ? 'text-yellow-600' : 'text-red-600'

  return (
    <div className="p-6 max-w-5xl mx-auto space-y-6">
      <div className="flex items-center gap-4">
        <button onClick={() => navigate('/reports')} className="text-sm text-blue-600 hover:underline">&larr; 返回列表</button>
        <h1 className="text-xl font-bold text-slate-900">{report.title}</h1>
        {report.app_mode === 'real' && <span className="px-2 py-0.5 text-xs rounded-full bg-red-100 text-red-700 font-medium">真实模式</span>}
      </div>

      {/* Risk warnings */}
      {report.risk_warnings && report.risk_warnings.length > 0 && (
        <div className="bg-orange-50 border border-orange-200 rounded-xl p-4">
          <h3 className="font-semibold text-orange-800 mb-1">风险提示</h3>
          {report.risk_warnings.map((w, i) => <p key={i} className="text-sm text-orange-700">{w}</p>)}
        </div>
      )}

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        {[
          { label: '总用例', value: report.total_tests || 0, color: 'text-slate-900' },
          { label: '通过', value: report.passed || 0, color: 'text-green-600' },
          { label: '失败', value: report.failed || 0, color: 'text-red-600' },
          { label: '跳过', value: report.skipped || 0, color: 'text-slate-500' },
          { label: '通过率', value: `${report.pass_rate || 0}%`, color: getColor(report.pass_rate || 0) },
        ].map(s => (
          <div key={s.label} className="bg-white rounded-xl shadow-sm border border-slate-200 p-4 text-center">
            <div className={`text-2xl font-bold ${s.color}`}>{s.value}</div>
            <div className="text-sm text-slate-500">{s.label}</div>
          </div>
        ))}
      </div>

      {/* Execution info */}
      <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-4">
        <h2 className="font-semibold text-slate-900 mb-3">执行信息</h2>
        <div className="grid grid-cols-2 gap-3 text-sm">
          <div><span className="text-slate-500">报告 ID:</span> <span className="font-mono">{report.report_id}</span></div>
          <div><span className="text-slate-500">Run ID:</span> <span className="font-mono">{report.run_id}</span></div>
          <div><span className="text-slate-500">项目:</span> {report.project_name || '-'}</div>
          <div><span className="text-slate-500">环境:</span> {report.environment_name || '-'}</div>
          <div><span className="text-slate-500">执行模式:</span> {report.app_mode || 'mock'}</div>
          <div><span className="text-slate-500">允许写操作:</span> {report.allow_unsafe_methods ? '是' : '否'}</div>
          {run && <>
            <div><span className="text-slate-500">执行状态:</span> {run.status}</div>
            <div><span className="text-slate-500">触发类型:</span> {run.trigger_type || '-'}</div>
            <div><span className="text-slate-500">耗时:</span> {run.duration ? `${run.duration.toFixed(2)}s` : '-'}</div>
            <div><span className="text-slate-500">开始:</span> {run.start_time || '-'}</div>
          </>}
        </div>
      </div>

      {/* P2-6B: Performance Summary */}
      {run?.trigger_type === 'performance' && (() => {
        let ps = null
        try { ps = JSON.parse(run.summary || '{}')?.performance_summary } catch {}
        if (!ps) return null
        return (
          <div className="bg-white rounded-xl shadow-sm border border-orange-200 p-4">
            <h2 className="font-semibold text-orange-700 mb-3">性能测试摘要</h2>
            <div className="grid grid-cols-3 gap-3 mb-3">
              <div className="bg-blue-50 rounded-lg p-3 text-center">
                <div className="text-xl font-bold text-blue-700">{ps.total_requests}</div>
                <div className="text-xs text-blue-600">总请求</div>
              </div>
              <div className="bg-green-50 rounded-lg p-3 text-center">
                <div className="text-xl font-bold text-green-700">{ps.qps}</div>
                <div className="text-xs text-green-600">QPS</div>
              </div>
              <div className="bg-orange-50 rounded-lg p-3 text-center">
                <div className="text-xl font-bold text-orange-700">{(ps.error_rate * 100).toFixed(1)}%</div>
                <div className="text-xs text-orange-600">错误率</div>
              </div>
            </div>
            <div className="grid grid-cols-3 gap-2 text-sm">
              <div className="flex justify-between"><span className="text-slate-500">Avg</span><span>{ps.avg_response_time_ms}ms</span></div>
              <div className="flex justify-between"><span className="text-slate-500">P95</span><span>{ps.p95_ms}ms</span></div>
              <div className="flex justify-between"><span className="text-slate-500">P99</span><span>{ps.p99_ms}ms</span></div>
            </div>
          </div>
        )
      })()}

      {/* P2-7: Web UI Evidence Summary */}
      {run?.trigger_type === 'web_ui_batch' && (() => {
        let ws = null
        try { ws = JSON.parse(run.summary || '{}') } catch {}
        if (!ws || ws.case_type !== 'web_ui') return null
        return (
          <div className="bg-white rounded-xl shadow-sm border border-violet-200 p-4">
            <h2 className="font-semibold text-violet-700 mb-3">Web UI 执行证据</h2>
            <div className="grid grid-cols-4 gap-3">
              <div className="bg-violet-50 rounded-lg p-3 text-center">
                <div className="text-xl font-bold text-violet-700">{ws.total_cases || 0}</div>
                <div className="text-xs text-violet-600">总用例</div>
              </div>
              <div className="bg-violet-50 rounded-lg p-3 text-center">
                <div className="text-xl font-bold text-violet-700">{ws.trace_count || 0}</div>
                <div className="text-xs text-violet-600">Trace 文件</div>
              </div>
              <div className="bg-yellow-50 rounded-lg p-3 text-center">
                <div className="text-xl font-bold text-yellow-700">{ws.console_error_count || 0}</div>
                <div className="text-xs text-yellow-600">Console 错误</div>
              </div>
              <div className="bg-red-50 rounded-lg p-3 text-center">
                <div className="text-xl font-bold text-red-700">{ws.network_error_count || 0}</div>
                <div className="text-xs text-red-600">Network 错误</div>
              </div>
            </div>
            <div className="grid grid-cols-2 gap-2 mt-3 text-sm">
              <div><span className="text-slate-500">通过:</span> <span className="text-green-600 font-bold">{ws.passed_cases || 0}</span></div>
              <div><span className="text-slate-500">失败:</span> <span className="text-red-600 font-bold">{ws.failed_cases || 0}</span></div>
            </div>

            {/* P2-9B: 稳定性摘要 */}
            {(ws.retry_enabled || ws.flaky_candidate_count > 0 || ws.selector_low_score_count > 0 || ws.wait_strategy_warnings > 0) && (
              <div className="mt-3 pt-3 border-t border-violet-100">
                <h3 className="text-sm font-semibold text-violet-700 mb-2">稳定性摘要</h3>
                <div className="grid grid-cols-5 gap-2">
                  {ws.retry_enabled && (
                    <div className="bg-blue-50 rounded-lg p-2 text-center">
                      <div className="text-lg font-bold text-blue-700">{ws.retried_cases || 0}</div>
                      <div className="text-xs text-blue-600">重试次数</div>
                    </div>
                  )}
                  {ws.retry_enabled && (
                    <div className="bg-green-50 rounded-lg p-2 text-center">
                      <div className="text-lg font-bold text-green-700">{ws.recovered_cases || 0}</div>
                      <div className="text-xs text-green-600">重试恢复</div>
                    </div>
                  )}
                  <div className="bg-orange-50 rounded-lg p-2 text-center">
                    <div className="text-lg font-bold text-orange-700">{ws.flaky_candidate_count || 0}</div>
                    <div className="text-xs text-orange-600">Flaky 候选</div>
                  </div>
                  <div className="bg-amber-50 rounded-lg p-2 text-center">
                    <div className="text-lg font-bold text-amber-700">{ws.selector_low_score_count || 0}</div>
                    <div className="text-xs text-amber-600">低稳定 Selector</div>
                  </div>
                  <div className="bg-yellow-50 rounded-lg p-2 text-center">
                    <div className="text-lg font-bold text-yellow-700">{ws.wait_strategy_warnings || 0}</div>
                    <div className="text-xs text-yellow-600">等待策略警告</div>
                  </div>
                </div>
              </div>
            )}
          </div>
        )
      })()}

      {/* P2-8: UI Failure Analysis Summary */}
      {run && (() => {
        let ws = null
        try { ws = JSON.parse(run.summary || '{}') } catch {}
        const fa = ws?.failure_analysis_summary
        const faList = ws?.failure_analysis || []
        if (!fa || !fa.total_analyzed) return null
        return (
          <div className="bg-white rounded-xl shadow-sm border border-amber-200 p-4">
            <h2 className="font-semibold text-amber-700 mb-3">UI 失败归因摘要</h2>
            <div className="grid grid-cols-6 gap-3 mb-3">
              <div className="bg-gray-50 rounded-lg p-3 text-center">
                <div className="text-xl font-bold">{fa.total_analyzed}</div>
                <div className="text-xs text-gray-500">分析总数</div>
              </div>
              <div className="bg-amber-50 rounded-lg p-3 text-center">
                <div className="text-xl font-bold text-amber-600">{fa.high_confidence_count}</div>
                <div className="text-xs text-amber-600">高置信度</div>
              </div>
              <div className="bg-red-50 rounded-lg p-3 text-center">
                <div className="text-xl font-bold text-red-600">{fa.should_create_bug_count}</div>
                <div className="text-xs text-red-600">建议提 Bug</div>
              </div>
              <div className="bg-blue-50 rounded-lg p-3 text-center">
                <div className="text-xl font-bold text-blue-600">{fa.should_retry_count}</div>
                <div className="text-xs text-blue-600">建议重试</div>
              </div>
              <div className="bg-violet-50 rounded-lg p-3 text-center">
                <div className="text-xl font-bold text-violet-600">{fa.should_update_selector_count}</div>
                <div className="text-xs text-violet-600">更新 Selector</div>
              </div>
              <div className="bg-teal-50 rounded-lg p-3 text-center">
                <div className="text-xl font-bold text-teal-600">{fa.should_update_baseline_count}</div>
                <div className="text-xs text-teal-600">更新 Baseline</div>
              </div>
            </div>
            {fa.category_distribution && (
              <div className="flex flex-wrap gap-2 mb-3">
                {Object.entries(fa.category_distribution).map(([cat, cnt]) => (
                  <span key={cat} className="px-3 py-1 bg-gray-100 rounded-full text-xs font-medium">{cat}: {cnt}</span>
                ))}
              </div>
            )}
            {faList.length > 0 && (
              <div className="space-y-2">
                {faList.map((a, i) => (
                  <div key={i} className="p-2 bg-amber-50 rounded-lg text-sm flex items-start gap-2">
                    <span className="px-2 py-0.5 bg-amber-200 text-amber-800 rounded text-xs font-bold whitespace-nowrap">{a.failure_category}</span>
                    <span className="flex-1 text-gray-700">{a.root_cause_summary}</span>
                    <span className="text-xs text-gray-400 font-mono whitespace-nowrap">{(a.case_id || '').slice(0, 12)}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        )
      })()}

      {/* Failure summary */}
      <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-4">
        <h2 className="font-semibold text-slate-900 mb-3">失败摘要</h2>
        {(!report.failure_summary || report.failure_summary.length === 0) ? (
          <p className="text-sm text-green-600">无失败用例</p>
        ) : (
          <div className="space-y-2">
            {report.failure_summary.map((f, i) => (
              <div key={i} className="flex justify-between text-sm p-2 bg-red-50 rounded-lg">
                <span className="text-red-800 font-medium">{f.category}</span>
                <span className="text-red-600">{f.count} 个</span>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Download */}
      {report.download_url && (
        <div className="flex gap-3">
          <a href={report.download_url} target="_blank" rel="noopener noreferrer"
            className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700">
            下载 HTML 报告
          </a>
        </div>
      )}
    </div>
  )
}
