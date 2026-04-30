import { useEffect, useMemo, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { Download, RefreshCw } from 'lucide-react'
import PageHeader from '../components/PageHeader'
import DetailCard from '../components/DetailCard'
import StatusBadge from '../components/StatusBadge'
import EmptyState from '../components/EmptyState'
import { testRunsAPI } from '../services/api'
import { useToast } from '../components/ui/Toast'

function statusType(status) {
  if (status === 'passed') return 'success'
  if (status === 'failed' || status === 'aborted') return 'error'
  if (status === 'running' || status === 'healing' || status === 'preparing' || status === 'queued') return 'warning'
  return 'default'
}

export default function ExecutionDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const toast = useToast()
  const [loading, setLoading] = useState(true)
  const [execution, setExecution] = useState(null)

  const steps = execution?.steps || []
  const healingRecords = execution?.healing_records || []

  const summary = useMemo(() => ({
    total: execution?.totalTests || 0,
    passed: execution?.passed || 0,
    failed: execution?.failed || 0,
    pending: execution?.pending || 0,
  }), [execution])

  useEffect(() => {
    loadExecution()
    const timer = setInterval(() => {
      if (execution?.status === 'created' || execution?.status === 'queued' || execution?.status === 'preparing' || execution?.status === 'running' || execution?.status === 'healing') {
        loadExecution(true)
      }
    }, 2000)
    return () => clearInterval(timer)
  }, [id, execution?.status])

  const loadExecution = async (silent = false) => {
    if (!silent) setLoading(true)
    try {
      const data = await testRunsAPI.get(id)
      setExecution(data.testRun)
    } catch (error) {
      console.error(error)
      if (!silent) toast.error('加载执行详情失败')
      setExecution(null)
    } finally {
      if (!silent) setLoading(false)
    }
  }

  const handleDownload = () => {
    const content = JSON.stringify(execution, null, 2)
    const blob = new Blob([content], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `test-run-${id}.json`
    a.click()
    URL.revokeObjectURL(url)
  }

  if (loading) {
    return <div className="min-h-screen bg-slate-50 flex items-center justify-center text-slate-600">加载中...</div>
  }

  if (!execution) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <EmptyState title="执行记录不存在" description="该执行记录可能已删除或尚未生成。" action={<button onClick={() => navigate('/test-runs')} className="px-4 py-2 bg-slate-700 text-white rounded-md text-sm">返回列表</button>} />
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-slate-50">
      <PageHeader
        showBack={true}
        breadcrumbs={[
          { label: '测试执行', href: '/test-runs' },
          { label: execution.name },
        ]}
        title={execution.name}
        description={`${execution.project_name || ''} · ${execution.environment_name || execution.environment || ''}`}
        meta={<div className="mt-2"><StatusBadge status={execution.status} type={statusType(execution.status)} /></div>}
        actions={[
          { label: '刷新', icon: <RefreshCw className="w-4 h-4" />, onClick: () => loadExecution() },
          { label: '下载 JSON', icon: <Download className="w-4 h-4" />, variant: 'primary', onClick: handleDownload },
        ]}
      />

      <div className="max-w-[1400px] mx-auto px-4 sm:px-6 py-6 space-y-6">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <DetailCard><div className="text-center"><div className="text-3xl font-bold text-slate-900">{summary.total}</div><div className="text-sm text-slate-600">总用例</div></div></DetailCard>
          <DetailCard><div className="text-center"><div className="text-3xl font-bold text-green-600">{summary.passed}</div><div className="text-sm text-slate-600">通过</div></div></DetailCard>
          <DetailCard><div className="text-center"><div className="text-3xl font-bold text-red-600">{summary.failed}</div><div className="text-sm text-slate-600">失败</div></div></DetailCard>
          <DetailCard><div className="text-center"><div className="text-3xl font-bold text-orange-600">{execution.progress || 0}%</div><div className="text-sm text-slate-600">进度</div></div></DetailCard>
        </div>

        <DetailCard title="执行链路">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
            <div>Trace ID: <span className="font-mono">{execution.trace_id || '-'}</span></div>
            <div>Request ID: <span className="font-mono">{execution.request_id || '-'}</span></div>
            <div>开始时间: {execution.startTime || '-'}</div>
            <div>结束时间: {execution.endTime || '-'}</div>
            <div>报告 ID: {execution.report_id || '-'}</div>
            <div>最后错误: {execution.last_error || '-'}</div>
          </div>
        </DetailCard>

        <DetailCard title="状态流转审计">
          <div className="space-y-3">
            {(execution.status_history || []).map((item, index) => (
              <div key={`${item.status}-${index}`} className="p-3 border border-slate-200 rounded-md bg-slate-50">
                <div className="text-sm font-medium text-slate-900">{item.status}</div>
                <div className="text-xs text-slate-500 mt-1">{item.time}</div>
                <div className="text-sm text-slate-700 mt-2">{item.message}</div>
              </div>
            ))}
          </div>
        </DetailCard>

        <DetailCard title="执行步骤">
          <div className="space-y-4">
            {steps.map((step) => (
              <div key={step.id} className="border border-slate-200 rounded-md overflow-hidden">
                <div className="px-4 py-3 bg-slate-50 border-b border-slate-200 flex items-center justify-between">
                  <div>
                    <div className="font-medium text-slate-900">{step.step_name}</div>
                    <div className="text-xs text-slate-500 mt-1">trace: {step.trace_id || '-'} · request: {step.request_id || '-'}</div>
                  </div>
                  <StatusBadge status={step.status} type={statusType(step.status)} />
                </div>
                <div className="p-4 grid grid-cols-1 lg:grid-cols-2 gap-4 text-sm">
                  <div>
                    <div className="font-medium text-slate-700 mb-2">输入快照</div>
                    <pre className="p-3 bg-slate-900 text-slate-100 rounded-md overflow-x-auto text-xs">{JSON.stringify(step.input_snapshot || {}, null, 2)}</pre>
                  </div>
                  <div>
                    <div className="font-medium text-slate-700 mb-2">输出快照</div>
                    <pre className="p-3 bg-slate-900 text-slate-100 rounded-md overflow-x-auto text-xs">{JSON.stringify(step.output_snapshot || {}, null, 2)}</pre>
                  </div>
                </div>
                {(step.error_message || step.stack_trace) && (
                  <div className="px-4 pb-4 text-sm text-red-700">
                    <div className="font-medium mb-1">错误信息</div>
                    <div className="mb-2">{step.error_message}</div>
                    {step.stack_trace && <pre className="p-3 bg-red-50 rounded-md overflow-x-auto text-xs whitespace-pre-wrap">{step.stack_trace}</pre>}
                  </div>
                )}
              </div>
            ))}
          </div>
        </DetailCard>

        <DetailCard title="Self-Healing 审计">
          {healingRecords.length === 0 ? (
            <div className="text-sm text-slate-500">本次执行未触发自愈。</div>
          ) : (
            <div className="space-y-4">
              {healingRecords.map((record) => (
                <div key={record.id} className="p-4 border border-slate-200 rounded-md bg-slate-50">
                  <div className="flex items-center justify-between">
                    <div className="font-medium text-slate-900">{record.action_type}</div>
                    <span className="text-xs px-2 py-1 rounded-md bg-amber-100 text-amber-700">{record.risk_level}</span>
                  </div>
                  <div className="text-sm text-slate-700 mt-2">{record.reason}</div>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-3">
                    <pre className="p-3 bg-slate-900 text-slate-100 rounded-md overflow-x-auto text-xs">{JSON.stringify(record.before_snapshot || {}, null, 2)}</pre>
                    <pre className="p-3 bg-slate-900 text-slate-100 rounded-md overflow-x-auto text-xs">{JSON.stringify(record.after_snapshot || {}, null, 2)}</pre>
                  </div>
                </div>
              ))}
            </div>
          )}
        </DetailCard>
      </div>
    </div>
  )
}
