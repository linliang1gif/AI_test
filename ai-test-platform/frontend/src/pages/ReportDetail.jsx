import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { Download } from 'lucide-react'
import PageHeader from '../components/PageHeader'
import DetailCard from '../components/DetailCard'
import EmptyState from '../components/EmptyState'
import StatusBadge from '../components/StatusBadge'
import { reportsAPI } from '../services/api'

export default function ReportDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [loading, setLoading] = useState(true)
  const [report, setReport] = useState(null)

  useEffect(() => {
    loadReport()
  }, [id])

  const loadReport = async () => {
    setLoading(true)
    try {
      const data = await reportsAPI.get(id)
      setReport(data.report)
    } catch (error) {
      console.error(error)
      setReport(null)
    } finally {
      setLoading(false)
    }
  }

  const handleDownload = () => {
    const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `report-${id}.json`
    a.click()
    URL.revokeObjectURL(url)
  }

  if (loading) {
    return <div className="min-h-screen bg-slate-50 flex items-center justify-center text-slate-600">加载中...</div>
  }

  if (!report) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <EmptyState title="报告不存在" description="该报告可能尚未生成或已被删除。" action={<button onClick={() => navigate('/reports')} className="px-4 py-2 bg-slate-700 text-white rounded-md text-sm">返回列表</button>} />
      </div>
    )
  }

  const run = report.run
  const summary = report.summary || {}
  const failures = report.failure_overview?.failures || []

  return (
    <div className="min-h-screen bg-slate-50">
      <PageHeader
        showBack={true}
        breadcrumbs={[
          { label: '测试报告', href: '/reports' },
          { label: report.name },
        ]}
        title={report.name}
        description={`Trace ID: ${report.trace_id || '-'}`}
        meta={<div className="mt-2"><StatusBadge status={`${summary.pass_rate || 0}% 通过率`} type={(summary.pass_rate || 0) >= 80 ? 'success' : 'warning'} /></div>}
        actions={[{ label: '下载 JSON', icon: <Download className="w-4 h-4" />, variant: 'primary', onClick: handleDownload }]}
      />

      <div className="max-w-[1400px] mx-auto px-4 sm:px-6 py-6 space-y-6">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <DetailCard><div className="text-center"><div className="text-3xl font-bold text-slate-900">{summary.total || 0}</div><div className="text-sm text-slate-600">总用例</div></div></DetailCard>
          <DetailCard><div className="text-center"><div className="text-3xl font-bold text-green-600">{summary.passed || 0}</div><div className="text-sm text-slate-600">通过</div></div></DetailCard>
          <DetailCard><div className="text-center"><div className="text-3xl font-bold text-red-600">{summary.failed || 0}</div><div className="text-sm text-slate-600">失败</div></div></DetailCard>
          <DetailCard><div className="text-center"><div className="text-3xl font-bold text-blue-600">{summary.pass_rate || 0}%</div><div className="text-sm text-slate-600">通过率</div></div></DetailCard>
        </div>

        {run && (
          <DetailCard title="关联执行">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
              <div>执行 ID: {run.id}</div>
              <div>状态: {run.status}</div>
              <div>项目: {run.project_name || '-'}</div>
              <div>环境: {run.environment_name || run.environment || '-'}</div>
              <div>开始时间: {run.startTime || '-'}</div>
              <div>结束时间: {run.endTime || '-'}</div>
              <div>Trace ID: <span className="font-mono">{run.trace_id || '-'}</span></div>
              <div>Request ID: <span className="font-mono">{run.request_id || '-'}</span></div>
            </div>
          </DetailCard>
        )}

        <DetailCard title="失败概览">
          {failures.length === 0 ? (
            <div className="text-sm text-slate-500">本次报告没有失败步骤。</div>
          ) : (
            <div className="space-y-4">
              {failures.map((failure, index) => (
                <div key={`${failure.step_name}-${index}`} className="p-4 border border-red-200 rounded-md bg-red-50">
                  <div className="font-medium text-red-900">{failure.step_name}</div>
                  <div className="text-sm text-red-700 mt-2">{failure.error_message}</div>
                  <div className="text-xs text-red-600 mt-2">trace: {failure.trace_id || '-'} · request: {failure.request_id || '-'}</div>
                  {failure.output && <pre className="mt-3 p-3 bg-white rounded-md overflow-x-auto text-xs">{JSON.stringify(failure.output, null, 2)}</pre>}
                </div>
              ))}
            </div>
          )}
        </DetailCard>

        <DetailCard title="完整报告 JSON">
          <pre className="p-4 bg-slate-900 text-slate-100 rounded-md overflow-x-auto text-xs">{JSON.stringify(report, null, 2)}</pre>
        </DetailCard>
      </div>
    </div>
  )
}
