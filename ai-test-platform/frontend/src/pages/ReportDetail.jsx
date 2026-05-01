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
