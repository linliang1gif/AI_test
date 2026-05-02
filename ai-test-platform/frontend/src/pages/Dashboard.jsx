import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../services/api'

const REC_LABELS = { pass: '✅ 可发布', caution: '⚠️ 谨慎发布', block: '🚫 不建议发布' }
const REC_COLORS = { pass: 'text-green-600', caution: 'text-yellow-600', block: 'text-red-600' }
const REC_BG = { pass: 'bg-green-50 border-green-200', caution: 'bg-yellow-50 border-yellow-200', block: 'bg-red-50 border-red-200' }

const FC_LABELS = {
  auth_error: '认证错误', env_error: '环境错误', request_error: '请求错误',
  response_error: '响应错误', assertion_error: '断言错误', dependency_error: '依赖错误',
  timeout_error: '超时错误', unknown_error: '未知错误',
}

function ScoreColor(score) {
  if (score >= 85) return 'text-green-600'
  if (score >= 60) return 'text-yellow-600'
  return 'text-red-600'
}

function ScoreLabel(score) {
  if (score >= 85) return '健康'
  if (score >= 60) return '一般'
  return '风险较高'
}

export default function Dashboard() {
  const navigate = useNavigate()
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [actionLoading, setActionLoading] = useState('')
  const [actionMsg, setActionMsg] = useState('')

  const loadDashboard = async () => {
    setLoading(true)
    try {
      const res = await api.v2.dashboard.getSummary()
      setData(res.data || res)
    } catch (e) {
      setData(null)
    }
    setLoading(false)
  }

  useEffect(() => { loadDashboard() }, [])

  const handleDemoInit = async () => {
    setActionLoading('init')
    setActionMsg('')
    try {
      await fetch('/api/v2/demo/init', { method: 'POST' })
      setActionMsg('✅ Demo 项目初始化成功')
      await loadDashboard()
    } catch (e) { setActionMsg('❌ 初始化失败: ' + e.message) }
    setActionLoading('')
  }

  const handleDemoReset = async () => {
    if (!window.confirm('确定要重置 Demo 项目？所有 Demo 数据将被清空重建。')) return
    setActionLoading('reset')
    setActionMsg('')
    try {
      await fetch('/api/v2/demo/reset', { method: 'POST' })
      setActionMsg('✅ Demo 项目已重置')
      await loadDashboard()
    } catch (e) { setActionMsg('❌ 重置失败: ' + e.message) }
    setActionLoading('')
  }

  const handleGenAiAnalysis = async () => {
    if (!data?.latest_run?.run_id) return
    setActionLoading('ai')
    setActionMsg('')
    try {
      await api.v2.observability.generateAiAnalysis(data.latest_run.run_id, true)
      setActionMsg('✅ AI 分析已生成')
      await loadDashboard()
    } catch (e) { setActionMsg('❌ AI 分析失败: ' + e.message) }
    setActionLoading('')
  }

  if (loading) return (
    <div className="flex items-center justify-center h-full">
      <div className="text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
        <p className="text-gray-500">加载 Dashboard...</p>
      </div>
    </div>
  )

  const d = data || {}
  const lr = d.latest_run
  const ai = d.latest_ai_analysis
  const fc = d.failure_categories || {}
  const risk = d.risk_distribution || {}
  const status = d.status_distribution || {}
  const destruct = d.destructive_summary || {}
  const runs = d.recent_runs || []

  const noData = !d.project_count && !d.test_case_count

  return (
    <div className="p-6 max-w-[1400px] mx-auto">
      {/* 标题 */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">AI Test Platform Dashboard</h1>
          <p className="text-sm text-gray-500 mt-1">Phase 20 · 平台概览与演示仪表盘</p>
        </div>
        <button onClick={loadDashboard} className="px-3 py-1.5 text-sm bg-gray-100 hover:bg-gray-200 rounded-lg">🔄 刷新</button>
      </div>

      {/* 无数据提示 */}
      {noData && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-6 mb-6 text-center">
          <p className="text-blue-800 text-lg mb-3">暂无执行数据，请先导入需求文档或 Swagger 生成测试用例。</p>
          <button onClick={() => navigate('/test-cases')}
            className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
            前往测试用例页
          </button>
        </div>
      )}

      {/* 快捷操作区 */}
      <div className="bg-white rounded-lg shadow-sm border p-4 mb-6">
        <div className="flex items-center justify-between flex-wrap gap-2">
          <span className="text-sm font-semibold text-gray-700">快捷操作</span>
          <div className="flex gap-2 flex-wrap">
            <button onClick={() => navigate('/test-cases')}
              className="px-3 py-1.5 text-xs bg-blue-600 text-white rounded hover:bg-blue-700">
              前往测试用例页
            </button>
            {lr && !ai && (
              <button onClick={handleGenAiAnalysis} disabled={!!actionLoading}
                className="px-3 py-1.5 text-xs bg-purple-600 text-white rounded hover:bg-purple-700 disabled:opacity-50">
                {actionLoading === 'ai' ? '生成中...' : '生成最近一次 AI 分析'}
              </button>
            )}
            {lr && ai && (
              <button onClick={handleGenAiAnalysis} disabled={!!actionLoading}
                className="px-3 py-1.5 text-xs bg-indigo-600 text-white rounded hover:bg-indigo-700 disabled:opacity-50">
                {actionLoading === 'ai' ? '分析中...' : '🔄 重新 AI 分析'}
              </button>
            )}
          </div>
        </div>
        {actionMsg && <p className="text-sm mt-2">{actionMsg}</p>}
      </div>

      {/* 核心指标卡片 */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4 mb-6">
        <StatCard label="项目数" value={d.project_count} color="blue" />
        <StatCard label="测试用例" value={d.test_case_count} color="indigo" />
        <StatCard label="执行次数" value={d.test_run_count} color="purple" />
        <StatCard label="最近通过率" value={lr ? `${lr.pass_rate}%` : '-'} color={lr && lr.pass_rate >= 80 ? 'green' : 'red'} />
        <StatCard label="AI 健康评分" value={ai ? ai.health_score : '-'}
          color={ai ? (ai.health_score >= 85 ? 'green' : ai.health_score >= 60 ? 'yellow' : 'red') : 'gray'}
          sub={ai ? ScoreLabel(ai.health_score) : ''} />
        <div className={`rounded-lg border p-4 ${ai ? REC_BG[ai.release_recommendation] || 'bg-gray-50' : 'bg-gray-50 border-gray-200'}`}>
          <p className="text-xs text-gray-500 mb-1">发布建议</p>
          <p className={`text-lg font-bold ${ai ? REC_COLORS[ai.release_recommendation] || '' : 'text-gray-400'}`}>
            {ai ? REC_LABELS[ai.release_recommendation] || ai.release_recommendation : '-'}
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        {/* 最近一次执行概览 */}
        <div className="bg-white rounded-lg shadow-sm border p-5">
          <h2 className="text-base font-bold text-gray-800 mb-3">最近一次执行</h2>
          {lr ? (
            <div className="space-y-2 text-sm">
              <Row label="项目" value={lr.project_name} />
              <Row label="环境" value={lr.environment_name} />
              <Row label="Preset" value={lr.preset || '-'} />
              <Row label="执行时间" value={lr.created_at} />
              <div className="grid grid-cols-4 gap-2 mt-3">
                <MiniStat label="总数" value={lr.total} />
                <MiniStat label="通过" value={lr.passed} cls="text-green-600" />
                <MiniStat label="失败" value={lr.failed} cls="text-red-600" />
                <MiniStat label="跳过" value={lr.skipped} cls="text-gray-500" />
              </div>
              <div className="mt-2">
                <div className="flex items-center justify-between text-xs mb-1">
                  <span>通过率</span><span className="font-bold">{lr.pass_rate}%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2.5">
                  <div className={`h-2.5 rounded-full ${lr.pass_rate >= 80 ? 'bg-green-500' : lr.pass_rate >= 50 ? 'bg-yellow-500' : 'bg-red-500'}`}
                    style={{ width: `${Math.min(lr.pass_rate, 100)}%` }}></div>
                </div>
              </div>
            </div>
          ) : <p className="text-sm text-gray-400">暂无执行记录</p>}
        </div>

        {/* AI 分析摘要 */}
        <div className="bg-white rounded-lg shadow-sm border p-5">
          <h2 className="text-base font-bold text-gray-800 mb-3">AI 分析摘要</h2>
          {ai ? (
            <div className="space-y-3">
              <div className="flex items-center gap-4">
                <div className="text-center">
                  <div className={`text-3xl font-bold ${ScoreColor(ai.health_score)}`}>{ai.health_score}</div>
                  <div className="text-xs text-gray-500">{ScoreLabel(ai.health_score)}</div>
                </div>
                <div className={`px-3 py-1.5 rounded-lg border text-sm font-bold ${REC_BG[ai.release_recommendation]} ${REC_COLORS[ai.release_recommendation]}`}>
                  {REC_LABELS[ai.release_recommendation] || ai.release_recommendation}
                </div>
                <span className="text-xs px-2 py-0.5 bg-gray-100 rounded">{ai.provider === 'rule_based' ? '规则分析' : 'AI 大模型'}</span>
              </div>
              <p className="text-sm text-gray-700">{ai.summary}</p>
            </div>
          ) : (
            <div className="text-center py-4">
              <p className="text-sm text-gray-400 mb-2">暂无 AI 分析</p>
              {lr && (
                <button onClick={handleGenAiAnalysis} disabled={!!actionLoading}
                  className="px-4 py-1.5 text-sm bg-purple-600 text-white rounded hover:bg-purple-700 disabled:opacity-50">
                  生成最近一次 AI 分析
                </button>
              )}
            </div>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
        {/* 失败分类统计 */}
        <div className="bg-white rounded-lg shadow-sm border p-5">
          <h2 className="text-base font-bold text-gray-800 mb-3">失败分类统计</h2>
          {Object.keys(fc).length > 0 ? (
            <div className="space-y-2">
              {Object.entries(fc).sort((a, b) => b[1] - a[1]).map(([k, v]) => (
                <div key={k} className="flex items-center justify-between">
                  <span className="text-xs text-gray-600">{FC_LABELS[k] || k}</span>
                  <span className="text-sm font-bold text-red-600">{v}</span>
                </div>
              ))}
            </div>
          ) : <p className="text-sm text-gray-400">无失败用例</p>}
        </div>

        {/* 风险分布 */}
        <div className="bg-white rounded-lg shadow-sm border p-5">
          <h2 className="text-base font-bold text-gray-800 mb-3">风险分布</h2>
          <div className="space-y-3">
            {['P0', 'P1', 'P2'].map(level => {
              const count = risk[level] || 0
              const total = (risk.P0 || 0) + (risk.P1 || 0) + (risk.P2 || 0)
              const pct = total > 0 ? Math.round(count / total * 100) : 0
              const color = level === 'P0' ? 'bg-red-500' : level === 'P1' ? 'bg-yellow-500' : 'bg-blue-500'
              return (
                <div key={level}>
                  <div className="flex items-center justify-between text-xs mb-1">
                    <span className="font-medium">{level}</span>
                    <span>{count} ({pct}%)</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div className={`h-2 rounded-full ${color}`} style={{ width: `${pct}%` }}></div>
                  </div>
                </div>
              )
            })}
          </div>
          <div className="mt-3 pt-3 border-t text-xs text-gray-500">
            破坏性用例: {destruct.total || 0} 条 · 最近跳过: {destruct.skipped_latest || 0} 条
          </div>
        </div>

        {/* 用例状态分布 */}
        <div className="bg-white rounded-lg shadow-sm border p-5">
          <h2 className="text-base font-bold text-gray-800 mb-3">用例状态分布</h2>
          <div className="space-y-3">
            {[
              { key: 'passed', label: '通过', color: 'bg-green-500' },
              { key: 'failed', label: '失败', color: 'bg-red-500' },
              { key: 'pending', label: '待执行', color: 'bg-gray-400' },
              { key: 'skipped', label: '跳过', color: 'bg-yellow-500' },
            ].map(({ key, label, color }) => {
              const count = status[key] || 0
              const total = Object.values(status).reduce((a, b) => a + b, 0) || 1
              const pct = Math.round(count / total * 100)
              return (
                <div key={key}>
                  <div className="flex items-center justify-between text-xs mb-1">
                    <span className="font-medium">{label}</span>
                    <span>{count} ({pct}%)</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div className={`h-2 rounded-full ${color}`} style={{ width: `${pct}%` }}></div>
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      </div>

      {/* 最近 5 次执行记录 */}
      <div className="bg-white rounded-lg shadow-sm border p-5">
        <h2 className="text-base font-bold text-gray-800 mb-3">最近执行记录</h2>
        {runs.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-gray-50 text-xs text-gray-500">
                  <th className="text-left p-2">Run ID</th>
                  <th className="text-left p-2">Preset</th>
                  <th className="text-center p-2">总数</th>
                  <th className="text-center p-2">通过</th>
                  <th className="text-center p-2">失败</th>
                  <th className="text-center p-2">跳过</th>
                  <th className="text-center p-2">通过率</th>
                  <th className="text-left p-2">执行时间</th>
                </tr>
              </thead>
              <tbody>
                {runs.map((r, i) => (
                  <tr key={i} className="border-t hover:bg-gray-50 cursor-pointer" onClick={() => navigate('/test-runs-v2')}>
                    <td className="p-2 font-mono text-xs text-blue-600">{r.run_id?.slice(0, 30)}...</td>
                    <td className="p-2">{r.preset || '-'}</td>
                    <td className="p-2 text-center">{r.total}</td>
                    <td className="p-2 text-center text-green-600 font-medium">{r.passed}</td>
                    <td className="p-2 text-center text-red-600 font-medium">{r.failed}</td>
                    <td className="p-2 text-center text-gray-500">{r.skipped}</td>
                    <td className="p-2 text-center">
                      <span className={`font-bold ${r.pass_rate >= 80 ? 'text-green-600' : r.pass_rate >= 50 ? 'text-yellow-600' : 'text-red-600'}`}>
                        {r.pass_rate}%
                      </span>
                    </td>
                    <td className="p-2 text-xs text-gray-500">{r.created_at}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : <p className="text-sm text-gray-400">暂无执行记录</p>}
      </div>
    </div>
  )
}

function StatCard({ label, value, color = 'blue', sub }) {
  const colors = {
    blue: 'text-blue-600', indigo: 'text-indigo-600', purple: 'text-purple-600',
    green: 'text-green-600', red: 'text-red-600', yellow: 'text-yellow-600', gray: 'text-gray-400',
  }
  return (
    <div className="bg-white rounded-lg border p-4 shadow-sm">
      <p className="text-xs text-gray-500 mb-1">{label}</p>
      <p className={`text-2xl font-bold ${colors[color] || 'text-gray-800'}`}>{value ?? 0}</p>
      {sub && <p className="text-xs text-gray-400 mt-0.5">{sub}</p>}
    </div>
  )
}

function Row({ label, value }) {
  return (
    <div className="flex items-center justify-between">
      <span className="text-xs text-gray-500">{label}</span>
      <span className="text-sm font-medium text-gray-800">{value || '-'}</span>
    </div>
  )
}

function MiniStat({ label, value, cls = '' }) {
  return (
    <div className="text-center bg-gray-50 rounded p-2">
      <div className={`text-lg font-bold ${cls}`}>{value}</div>
      <div className="text-xs text-gray-500">{label}</div>
    </div>
  )
}
