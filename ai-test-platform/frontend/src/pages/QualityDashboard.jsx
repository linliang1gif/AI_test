import { useEffect, useState } from 'react'

const API = '/api/v2/analytics'

function Card({ title, value, sub, color = 'slate' }) {
  const colors = {
    slate: 'bg-slate-50 text-slate-700',
    green: 'bg-green-50 text-green-700',
    red: 'bg-red-50 text-red-700',
    amber: 'bg-amber-50 text-amber-700',
    blue: 'bg-blue-50 text-blue-700',
    violet: 'bg-violet-50 text-violet-700',
  }
  return (
    <div className={`rounded-xl p-4 ${colors[color] || colors.slate}`}>
      <div className="text-2xl font-bold">{value ?? '-'}</div>
      <div className="text-xs mt-1 opacity-75">{title}</div>
      {sub && <div className="text-xs mt-0.5 opacity-60">{sub}</div>}
    </div>
  )
}

function RiskBadge({ level, reasons }) {
  const cfg = {
    high:   { bg: 'bg-red-100 border-red-300', text: 'text-red-800', label: '高风险' },
    medium: { bg: 'bg-amber-100 border-amber-300', text: 'text-amber-800', label: '中风险' },
    low:    { bg: 'bg-green-100 border-green-300', text: 'text-green-800', label: '低风险' },
  }
  const c = cfg[level] || cfg.low
  return (
    <div className={`rounded-xl border p-4 ${c.bg}`}>
      <div className={`text-lg font-bold ${c.text}`}>{c.label}</div>
      {reasons && reasons.length > 0 && (
        <ul className="mt-2 text-xs space-y-1">
          {reasons.map((r, i) => <li key={i} className={c.text}>• {r}</li>)}
        </ul>
      )}
      {(!reasons || reasons.length === 0) && <div className="text-xs mt-1 opacity-60">无风险因素</div>}
    </div>
  )
}

function MiniBar({ items, labelKey, valueKey, maxKey }) {
  if (!items || items.length === 0) return <div className="text-sm text-gray-400 py-4 text-center">暂无数据</div>
  const max = Math.max(...items.map(i => i[valueKey] || 0), 1)
  return (
    <div className="space-y-2">
      {items.map((item, i) => (
        <div key={i} className="flex items-center gap-2 text-sm">
          <div className="w-28 truncate text-gray-600 text-right">{item[labelKey]}</div>
          <div className="flex-1 bg-gray-100 rounded-full h-5 overflow-hidden">
            <div className="bg-red-400 h-5 rounded-full" style={{ width: `${Math.max((item[valueKey] / max) * 100, 4)}%` }} />
          </div>
          <div className="w-10 text-right font-semibold text-gray-700">{item[valueKey]}</div>
        </div>
      ))}
    </div>
  )
}

function TrendChart({ data, passKey, failKey, dateKey = 'date' }) {
  if (!data || data.length === 0) return <div className="text-sm text-gray-400 py-4 text-center">暂无趋势数据</div>
  const maxVal = Math.max(...data.map(d => (d[passKey] || 0) + (d[failKey] || 0)), 1)
  return (
    <div className="flex items-end gap-1 h-32">
      {data.map((d, i) => {
        const total = (d[passKey] || 0) + (d[failKey] || 0)
        const pct = total / maxVal
        const passH = total > 0 ? ((d[passKey] || 0) / total) * pct * 100 : 0
        const failH = total > 0 ? ((d[failKey] || 0) / total) * pct * 100 : 0
        return (
          <div key={i} className="flex-1 flex flex-col items-center gap-0.5" title={`${d[dateKey]}: ${d[passKey]}/${total}`}>
            <div className="w-full flex flex-col justify-end" style={{ height: '100px' }}>
              <div className="bg-red-400 rounded-t" style={{ height: `${failH}%`, minHeight: failH > 0 ? '2px' : 0 }} />
              <div className="bg-green-400 rounded-b" style={{ height: `${passH}%`, minHeight: passH > 0 ? '2px' : 0 }} />
            </div>
            <div className="text-[9px] text-gray-400 rotate-[-45deg] origin-top-left w-12 mt-1">{d[dateKey]?.slice(5)}</div>
          </div>
        )
      })}
    </div>
  )
}

export default function QualityDashboard() {
  const [days, setDays] = useState(7)
  const [overview, setOverview] = useState(null)
  const [suiteTrend, setSuiteTrend] = useState([])
  const [gateTrend, setGateTrend] = useState([])
  const [failModules, setFailModules] = useState([])
  const [failCategories, setFailCategories] = useState([])
  const [defectSummary, setDefectSummary] = useState(null)
  const [dataIssues, setDataIssues] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const load = async (d) => {
    setLoading(true)
    setError(null)
    try {
      const qs = `days=${d}`
      const [ov, st, gt, fm, fc, ds, di] = await Promise.all([
        fetch(`${API}/overview?${qs}`).then(r => r.json()),
        fetch(`${API}/test-suite-trend?${qs}`).then(r => r.json()),
        fetch(`${API}/gate-trend?${qs}`).then(r => r.json()),
        fetch(`${API}/failure-modules?${qs}`).then(r => r.json()),
        fetch(`${API}/failure-categories?${qs}`).then(r => r.json()),
        fetch(`${API}/defect-summary?days=${d}`).then(r => r.json()),
        fetch(`${API}/data-issues?${qs}`).then(r => r.json()),
      ])
      setOverview(ov)
      setSuiteTrend(st)
      setGateTrend(gt)
      setFailModules(fm)
      setFailCategories(fc)
      setDefectSummary(ds)
      setDataIssues(di)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load(days) }, [days])

  return (
    <div className="max-w-7xl mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-slate-900">质量驾驶舱</h1>
        <div className="flex items-center gap-2">
          {[7, 14, 30].map(d => (
            <button key={d} onClick={() => setDays(d)}
              className={`px-3 py-1.5 rounded-lg text-sm font-medium transition ${
                days === d ? 'bg-indigo-600 text-white' : 'bg-white border text-gray-600 hover:bg-gray-50'
              }`}>最近 {d} 天</button>
          ))}
          <button onClick={() => load(days)} disabled={loading}
            className="px-3 py-1.5 bg-slate-100 rounded-lg text-sm hover:bg-slate-200 disabled:opacity-50">
            {loading ? '加载中...' : '刷新'}
          </button>
        </div>
      </div>

      {error && <div className="bg-red-50 border border-red-200 rounded-lg p-3 text-sm text-red-700">加载失败: {error}</div>}

      {/* Overview cards */}
      {overview && (
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-3">
          <Card title="执行通过率" value={`${(overview.run_pass_rate * 100).toFixed(0)}%`} sub={`${overview.passed_runs}/${overview.total_runs}`} color={overview.run_pass_rate >= 0.9 ? 'green' : 'red'} />
          <Card title="用例通过率" value={`${(overview.case_pass_rate * 100).toFixed(0)}%`} sub={`共 ${overview.total_cases_executed} 例`} color={overview.case_pass_rate >= 0.9 ? 'green' : 'red'} />
          <Card title="门禁通过率" value={overview.gate_evaluated > 0 ? `${(overview.gate_pass_rate * 100).toFixed(0)}%` : 'N/A'} sub={`${overview.gate_evaluated} 次评估`} color={overview.gate_pass_rate >= 0.8 ? 'green' : 'amber'} />
          <Card title="未关闭缺陷" value={overview.open_defects} color={overview.open_defects > 10 ? 'red' : 'slate'} />
          <Card title="Blocker" value={overview.blocker_defects} color={overview.blocker_defects > 0 ? 'red' : 'green'} />
          <Card title="数据问题" value={overview.data_issue_count} color={overview.data_issue_count > 5 ? 'amber' : 'slate'} />
          <Card title="Flaky 候选" value={overview.flaky_candidate_count} color={overview.flaky_candidate_count > 3 ? 'amber' : 'slate'} />
        </div>
      )}

      {/* Risk */}
      {overview && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <RiskBadge level={overview.risk_level} reasons={overview.risk_reasons} />
          <div className="md:col-span-2 bg-white rounded-xl shadow-sm border p-4">
            <h3 className="text-sm font-semibold text-slate-700 mb-3">测试集通过率趋势</h3>
            <TrendChart data={suiteTrend} passKey="passed_suite_runs" failKey="failed_suite_runs" />
          </div>
        </div>
      )}

      {/* Gate trend + failure modules */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="bg-white rounded-xl shadow-sm border p-4">
          <h3 className="text-sm font-semibold text-slate-700 mb-3">质量门禁趋势</h3>
          <TrendChart data={gateTrend} passKey="gate_passed" failKey="gate_failed" />
        </div>
        <div className="bg-white rounded-xl shadow-sm border p-4">
          <h3 className="text-sm font-semibold text-slate-700 mb-3">失败模块 Top 5</h3>
          <MiniBar items={failModules} labelKey="module" valueKey="failed_count" />
        </div>
      </div>

      {/* Failure categories + Defect summary */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="bg-white rounded-xl shadow-sm border p-4">
          <h3 className="text-sm font-semibold text-slate-700 mb-3">失败类型分布</h3>
          {failCategories.length > 0 ? (
            <div className="space-y-2">
              {failCategories.map((c, i) => (
                <div key={i} className="flex items-center justify-between text-sm">
                  <span className="text-gray-600">{c.category}</span>
                  <span className="font-semibold">{c.count} <span className="text-gray-400 text-xs">({(c.percentage * 100).toFixed(0)}%)</span></span>
                </div>
              ))}
            </div>
          ) : <div className="text-sm text-gray-400 py-4 text-center">暂无失败数据</div>}
        </div>
        <div className="bg-white rounded-xl shadow-sm border p-4">
          <h3 className="text-sm font-semibold text-slate-700 mb-3">缺陷摘要</h3>
          {defectSummary ? (
            <div className="space-y-3">
              <div className="grid grid-cols-4 gap-2 text-center text-sm">
                <div className="bg-red-50 rounded-lg p-2"><div className="font-bold text-red-600">{defectSummary.open_defects}</div><div className="text-[10px] text-red-500">Open</div></div>
                <div className="bg-amber-50 rounded-lg p-2"><div className="font-bold text-amber-600">{defectSummary.confirmed_defects}</div><div className="text-[10px] text-amber-500">Confirmed</div></div>
                <div className="bg-blue-50 rounded-lg p-2"><div className="font-bold text-blue-600">{defectSummary.fixed_defects}</div><div className="text-[10px] text-blue-500">Fixed</div></div>
                <div className="bg-green-50 rounded-lg p-2"><div className="font-bold text-green-600">{defectSummary.closed_defects}</div><div className="text-[10px] text-green-500">Closed</div></div>
              </div>
              <div className="grid grid-cols-3 gap-2 text-center text-sm">
                <div className="bg-red-100 rounded-lg p-2"><div className="font-bold text-red-700">{defectSummary.blocker_defects}</div><div className="text-[10px]">Blocker</div></div>
                <div className="bg-orange-50 rounded-lg p-2"><div className="font-bold text-orange-600">{defectSummary.critical_defects}</div><div className="text-[10px]">Critical</div></div>
                <div className="bg-slate-50 rounded-lg p-2"><div className="font-bold">{defectSummary.major_defects + defectSummary.minor_defects + defectSummary.trivial_defects}</div><div className="text-[10px]">Other</div></div>
              </div>
            </div>
          ) : <div className="text-sm text-gray-400 py-4 text-center">暂无缺陷数据</div>}
        </div>
      </div>

      {/* Data issues */}
      {dataIssues && (
        <div className="bg-white rounded-xl shadow-sm border p-4">
          <h3 className="text-sm font-semibold text-slate-700 mb-3">测试数据问题摘要</h3>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-3 text-center text-sm">
            <Card title="校验错误" value={dataIssues.data_validation_errors} color={dataIssues.data_validation_errors > 0 ? 'red' : 'green'} />
            <Card title="缺失变量" value={dataIssues.missing_variables} color={dataIssues.missing_variables > 0 ? 'amber' : 'green'} />
            <Card title="清理失败" value={dataIssues.cleanup_failed} color={dataIssues.cleanup_failed > 0 ? 'amber' : 'green'} />
            <Card title="使用数据集" value={dataIssues.datasets_used} color="blue" />
            <Card title="问题 Run" value={dataIssues.data_issue_runs} sub={`/ ${dataIssues.total_runs_analyzed} 总 Run`} color={dataIssues.data_issue_runs > 0 ? 'amber' : 'green'} />
          </div>
        </div>
      )}
    </div>
  )
}
