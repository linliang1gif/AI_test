import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../services/api'
import PageHeader from '../components/PageHeader'
import StatusBadge from '../components/StatusBadge'
import EmptyState from '../components/EmptyState'

export default function TestRunsV2() {
  const navigate = useNavigate()
  const [runs, setRuns] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [filter, setFilter] = useState({
    project_id: '',
    status: '',
  })

  useEffect(() => {
    loadRuns()
  }, [filter])

  const loadRuns = async () => {
    try {
      setLoading(true)
      setError(null)
      const params = {}
      if (filter.project_id) params.project_id = filter.project_id
      if (filter.status) params.status = filter.status
      
      const response = await api.v2.observability.getRuns(params)
      const sortedRuns = [...(response.data || [])].sort((a, b) => {
        const timeA = new Date(a.created_at || a.start_time || 0).getTime()
        const timeB = new Date(b.created_at || b.start_time || 0).getTime()
        if (timeA !== timeB) return timeB - timeA
        return String(b.id || '').localeCompare(String(a.id || ''))
      })
      setRuns(sortedRuns)
    } catch (err) {
      console.error('加载执行记录失败:', err)
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const formatDuration = (seconds) => {
    if (!seconds) return 'N/A'
    if (seconds < 60) return `${seconds.toFixed(1)}秒`
    const minutes = Math.floor(seconds / 60)
    const secs = Math.floor(seconds % 60)
    return `${minutes}分${secs}秒`
  }

  const formatDateTime = (isoString) => {
    if (!isoString) return 'N/A'
    const date = new Date(isoString)
    return date.toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    })
  }

  const getStatusColor = (status) => {
    const colors = {
      created: 'bg-gray-100 text-gray-800',
      queued: 'bg-blue-100 text-blue-800',
      preparing: 'bg-yellow-100 text-yellow-800',
      running: 'bg-purple-100 text-purple-800',
      healing: 'bg-orange-100 text-orange-800',
      passed: 'bg-green-100 text-green-800',
      failed: 'bg-red-100 text-red-800',
      no_assertion: 'bg-yellow-100 text-yellow-800',
      error: 'bg-red-100 text-red-800',
      aborted: 'bg-gray-100 text-gray-800',
    }
    return colors[status] || 'bg-gray-100 text-gray-800'
  }

  const getPassRate = (run) => {
    if (!run.total_cases) return 0
    return ((run.passed_cases / run.total_cases) * 100).toFixed(1)
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 p-6">
        <PageHeader title="测试执行记录" subtitle="查看测试执行历史和详情" />
        <div className="flex justify-center items-center h-64">
          <div className="text-gray-500">加载中...</div>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 p-6">
        <PageHeader title="测试执行记录" subtitle="查看测试执行历史和详情" />
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">
          加载失败: {error}
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <PageHeader 
        title="测试执行记录" 
        subtitle="查看测试执行历史和详情"
        action={
          <button
            onClick={loadRuns}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            刷新
          </button>
        }
      />

      {/* 过滤器 */}
      <div className="bg-white rounded-lg shadow-sm p-4 mb-6">
        <div className="flex gap-4">
          <select
            value={filter.status}
            onChange={(e) => setFilter({ ...filter, status: e.target.value })}
            className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
          >
            <option value="">全部状态</option>
            <option value="passed">通过</option>
            <option value="failed">失败</option>
            <option value="no_assertion">无断言</option>
            <option value="error">错误</option>
            <option value="running">运行中</option>
          </select>
        </div>
      </div>

      {/* 执行记录列表 */}
      {runs.length === 0 ? (
        <EmptyState 
          title="暂无执行记录"
          description="还没有测试执行记录"
        />
      ) : (
        <div className="space-y-4">
          {runs.map((run) => (
            <div
              key={run.id}
              className="bg-white rounded-lg shadow-sm p-6 hover:shadow-md transition-shadow cursor-pointer"
              onClick={() => navigate(`/test-runs-v2/${run.id}`)}
            >
              <div className="flex items-start justify-between mb-4">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <h3 className="text-lg font-semibold text-gray-900">{run.id}</h3>
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(run.status)}`}>
                      {{passed:'通过',failed:'失败',no_assertion:'无断言',error:'错误',running:'运行中',created:'已创建'}[run.status] || run.status}
                    </span>
                    {run.trigger_type && (
                      <span className="px-2 py-1 bg-gray-100 text-gray-600 rounded text-xs">
                        {run.trigger_type}
                      </span>
                    )}
                  </div>
                  <div className="text-sm text-gray-500 space-y-1">
                    <div>Trace ID: <span className="font-mono text-xs">{run.trace_id}</span></div>
                    <div>创建时间: {formatDateTime(run.created_at)}</div>
                    {run.created_by && <div>创建人: {run.created_by}</div>}
                  </div>
                </div>

                <div className="text-right">
                  <div className="text-2xl font-bold text-gray-900 mb-1">
                    {getPassRate(run)}%
                  </div>
                  <div className="text-sm text-gray-500">通过率</div>
                </div>
              </div>

              <div className="grid grid-cols-4 gap-4 pt-4 border-t border-gray-100">
                <div>
                  <div className="text-sm text-gray-500 mb-1">总用例</div>
                  <div className="text-lg font-semibold text-gray-900">{run.total_cases || 0}</div>
                </div>
                <div>
                  <div className="text-sm text-gray-500 mb-1">通过</div>
                  <div className="text-lg font-semibold text-green-600">{run.passed_cases || 0}</div>
                </div>
                <div>
                  <div className="text-sm text-gray-500 mb-1">失败</div>
                  <div className="text-lg font-semibold text-red-600">{run.failed_cases || 0}</div>
                </div>
                <div>
                  <div className="text-sm text-gray-500 mb-1">耗时</div>
                  <div className="text-lg font-semibold text-gray-900">{formatDuration(run.duration)}</div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
