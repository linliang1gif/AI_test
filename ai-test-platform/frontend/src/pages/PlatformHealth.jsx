import { useState, useEffect, useCallback } from 'react'
import { api } from '../services/api'

const STATUS_COLORS = {
  ok: 'bg-green-100 text-green-800 border-green-300',
  configured: 'bg-green-100 text-green-800 border-green-300',
  found: 'bg-green-100 text-green-800 border-green-300',
  degraded: 'bg-yellow-100 text-yellow-800 border-yellow-300',
  partial: 'bg-yellow-100 text-yellow-800 border-yellow-300',
  not_configured: 'bg-slate-100 text-slate-600 border-slate-300',
  no_runs: 'bg-slate-100 text-slate-600 border-slate-300',
  error: 'bg-red-100 text-red-800 border-red-300',
  unknown: 'bg-slate-100 text-slate-500 border-slate-300',
}

const STATUS_LABELS = {
  ok: '正常',
  configured: '已配置',
  found: '有记录',
  degraded: '降级',
  partial: '部分配置',
  not_configured: '未配置',
  no_runs: '无执行记录',
  error: '异常',
  unknown: '未知',
}

function StatusBadge({ status }) {
  const cls = STATUS_COLORS[status] || STATUS_COLORS.unknown
  const label = STATUS_LABELS[status] || status
  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${cls}`}>
      {label}
    </span>
  )
}

export default function PlatformHealth() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [lastRefresh, setLastRefresh] = useState(null)

  const refresh = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await api.health.full()
      setData(res)
      setLastRefresh(new Date())
    } catch (e) {
      setError(e.message || '请求失败')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { refresh() }, [refresh])

  // 整体健康评分
  const overallStatus = data
    ? [data.backend_status, data.database_status, data.environment_status].every(s => s === 'ok')
      ? 'healthy'
      : [data.backend_status, data.database_status, data.environment_status].some(s => s === 'error')
        ? 'unhealthy'
        : 'degraded'
    : 'unknown'

  return (
    <div className="p-6 max-w-5xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">平台健康检查</h1>
          <p className="text-sm text-slate-500 mt-1">D2-2 全量健康状态面板</p>
        </div>
        <div className="flex items-center gap-3">
          {lastRefresh && (
            <span className="text-xs text-slate-400">
              最近刷新: {lastRefresh.toLocaleTimeString()}
            </span>
          )}
          <button
            onClick={refresh}
            disabled={loading}
            className="px-4 py-2 bg-indigo-600 text-white text-sm rounded-lg hover:bg-indigo-700 disabled:opacity-50"
          >
            {loading ? '检查中...' : '刷新'}
          </button>
        </div>
      </div>

      {error && (
        <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-red-800 font-medium">连接后端失败</p>
          <p className="text-red-600 text-sm mt-1">{error}</p>
          <p className="text-red-500 text-xs mt-2">请确认后端服务已启动并可访问。</p>
        </div>
      )}

      {data && (
        <>
          {/* 总览卡片 */}
          <div className={`mb-6 p-5 rounded-xl border-2 ${
            overallStatus === 'healthy' ? 'bg-green-50 border-green-300' :
            overallStatus === 'unhealthy' ? 'bg-red-50 border-red-300' :
            'bg-yellow-50 border-yellow-300'
          }`}>
            <div className="flex items-center justify-between">
              <div>
                <span className="text-3xl mr-3">
                  {overallStatus === 'healthy' ? '✅' : overallStatus === 'unhealthy' ? '❌' : '⚠️'}
                </span>
                <span className="text-xl font-bold">
                  {overallStatus === 'healthy' ? '平台运行正常' : overallStatus === 'unhealthy' ? '平台存在异常' : '平台部分降级'}
                </span>
              </div>
              {data.trace_id && (
                <span className="text-xs text-slate-400 font-mono">trace: {data.trace_id}</span>
              )}
            </div>
          </div>

          {/* 详细状态卡片 */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            {/* 后端服务 */}
            <div className="bg-white border border-slate-200 rounded-xl p-5">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-base font-semibold text-slate-800">后端服务</h3>
                <StatusBadge status={data.backend_status} />
              </div>
              <div className="text-sm text-slate-600 space-y-1">
                <p>响应时间: {data.timestamp ? '正常' : '未知'}</p>
                <p>已加载模块: {data.modules ? Object.values(data.modules).filter(Boolean).length : 0} / {data.modules ? Object.keys(data.modules).length : 0}</p>
              </div>
            </div>

            {/* 数据库 */}
            <div className="bg-white border border-slate-200 rounded-xl p-5">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-base font-semibold text-slate-800">数据库状态</h3>
                <StatusBadge status={data.database_status} />
              </div>
              <div className="text-sm text-slate-600 space-y-1">
                {data.database_counts && (
                  <>
                    <p>项目数: {data.database_counts.projects}</p>
                    <p>测试用例数: {data.database_counts.test_cases}</p>
                    <p>执行记录数: {data.database_counts.test_runs}</p>
                  </>
                )}
                {data.database_missing_tables && (
                  <p className="text-yellow-700">缺少表: {data.database_missing_tables.join(', ')}</p>
                )}
                {data.database_error && (
                  <p className="text-red-600">错误: {data.database_error}</p>
                )}
              </div>
            </div>

            {/* AI 配置 */}
            <div className="bg-white border border-slate-200 rounded-xl p-5">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-base font-semibold text-slate-800">AI 配置状态</h3>
                <StatusBadge status={data.ai_config_status} />
              </div>
              <div className="text-sm text-slate-600 space-y-1">
                {data.ai_provider && <p>Provider: {data.ai_provider}</p>}
                {data.ai_config_hint && <p className="text-yellow-700">{data.ai_config_hint}</p>}
                {data.ai_config_status === 'configured' && <p className="text-green-700">AI 服务已就绪</p>}
              </div>
            </div>

            {/* 运行环境 */}
            <div className="bg-white border border-slate-200 rounded-xl p-5">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-base font-semibold text-slate-800">运行环境</h3>
                <StatusBadge status={data.environment_status} />
              </div>
              <div className="text-sm text-slate-600 space-y-1">
                {data.environment && (
                  <>
                    <p>运行模式: {data.environment.app_mode}</p>
                    <p>Python: {data.environment.python_version}</p>
                    <p>后端端口: {data.environment.backend_port}</p>
                  </>
                )}
              </div>
            </div>

            {/* 最近执行 */}
            <div className="bg-white border border-slate-200 rounded-xl p-5 md:col-span-2">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-base font-semibold text-slate-800">最近一次测试执行</h3>
                <StatusBadge status={data.latest_run_status} />
              </div>
              <div className="text-sm text-slate-600 space-y-1">
                {data.latest_run ? (
                  <>
                    <p>Run ID: <span className="font-mono">{data.latest_run.run_id}</span></p>
                    <p>状态: {data.latest_run.status}</p>
                    <p>开始时间: {data.latest_run.started_at || '-'}</p>
                    <p>结束时间: {data.latest_run.finished_at || '-'}</p>
                  </>
                ) : data.latest_run_status === 'no_runs' ? (
                  <p>暂无测试执行记录。请先通过"测试执行"创建运行。</p>
                ) : (
                  <p>无法获取最近执行信息。</p>
                )}
              </div>
            </div>
          </div>

          {/* 时间戳 */}
          <div className="mt-6 text-center text-xs text-slate-400">
            检查时间: {data.timestamp} · Trace ID: {data.trace_id}
          </div>
        </>
      )}
    </div>
  )
}
