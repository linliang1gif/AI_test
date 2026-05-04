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

function MiniBar({ items, labelKey, valueKey }) {
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

function Section({ title, tip, children }) {
  return (
    <div className="bg-white rounded-xl shadow-sm border p-4">
      <div className="flex items-center gap-2 mb-3">
        <h3 className="text-sm font-semibold text-slate-700">{title}</h3>
        {tip && <span className="text-[10px] text-gray-400 bg-gray-50 px-1.5 py-0.5 rounded">{tip}</span>}
      </div>
      {children}
    </div>
  )
}

function Empty({ text = '暂无数据' }) {
  return <div className="text-sm text-gray-400 py-4 text-center">{text}</div>
}

const riskColors = { high: 'text-red-600 bg-red-50', medium: 'text-amber-600 bg-amber-50', low: 'text-green-600 bg-green-50' }

export default function QualityDashboard() {
  const [days, setDays] = useState(7)
  const [overview, setOverview] = useState(null)
  const [suiteTrend, setSuiteTrend] = useState([])
  const [gateTrend, setGateTrend] = useState([])
  const [failModules, setFailModules] = useState([])
  const [failCategories, setFailCategories] = useState([])
  const [defectSummary, setDefectSummary] = useState(null)
  const [dataIssues, setDataIssues] = useState(null)
  const [moduleRisk, setModuleRisk] = useState([])
  const [regression, setRegression] = useState([])
  const [defectTrend, setDefectTrend] = useState([])
  const [flakyTrend, setFlakyTrend] = useState([])
  const [perfTrend, setPerfTrend] = useState([])
  const [visualTrend, setVisualTrend] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const load = async (d) => {
    setLoading(true)
    setError(null)
    try {
      const qs = `days=${d}`
      const [ov, st, gt, fm, fc, ds, di, mr, qr, dt, ft, pt, vt] = await Promise.all([
        fetch(`${API}/overview?${qs}`).then(r => r.json()),
        fetch(`${API}/test-suite-trend?${qs}`).then(r => r.json()),
        fetch(`${API}/gate-trend?${qs}`).then(r => r.json()),
        fetch(`${API}/failure-modules?${qs}`).then(r => r.json()),
        fetch(`${API}/failure-categories?${qs}`).then(r => r.json()),
        fetch(`${API}/defect-summary?days=${d}`).then(r => r.json()),
        fetch(`${API}/data-issues?${qs}`).then(r => r.json()),
        fetch(`${API}/module-risk?${qs}`).then(r => r.json()),
        fetch(`${API}/quality-regression?${qs}`).then(r => r.json()),
        fetch(`${API}/defect-trend?${qs}`).then(r => r.json()),
        fetch(`${API}/flaky-trend?${qs}`).then(r => r.json()),
        fetch(`${API}/performance-trend?${qs}`).then(r => r.json()),
        fetch(`${API}/visual-trend?${qs}`).then(r => r.json()),
      ])
      setOverview(ov); setSuiteTrend(st); setGateTrend(gt)
      setFailModules(fm); setFailCategories(fc); setDefectSummary(ds); setDataIssues(di)
      setModuleRisk(mr); setRegression(qr); setDefectTrend(dt)
      setFlakyTrend(ft); setPerfTrend(pt); setVisualTrend(vt)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load(days) }, [days])

  const degraded = regression.filter(r => r.degraded)

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

      {/* Quality Regression Alert (P3-4B) */}
      {degraded.length > 0 && (
        <div className="bg-red-50 border border-red-200 rounded-xl p-4">
          <h3 className="text-sm font-bold text-red-800 mb-2">质量退化提醒 — 以下指标比上周期变差</h3>
          <div className="space-y-2">
            {degraded.map((r, i) => (
              <div key={i} className="flex items-center gap-3 text-sm">
                <span className={`px-2 py-0.5 rounded text-xs font-bold ${
                  r.severity === 'high' ? 'bg-red-200 text-red-800' : r.severity === 'medium' ? 'bg-amber-200 text-amber-800' : 'bg-yellow-100 text-yellow-800'
                }`}>{r.severity === 'high' ? '严重' : r.severity === 'medium' ? '中等' : '轻微'}</span>
                <span className="font-medium text-gray-700">{r.label}</span>
                <span className="text-gray-500">{r.previous_value?.toFixed?.(2) ?? r.previous_value} → {r.current_value?.toFixed?.(2) ?? r.current_value}</span>
                <span className="text-red-600 font-semibold">({r.delta > 0 ? '+' : ''}{typeof r.delta === 'number' ? r.delta.toFixed(4) : r.delta})</span>
              </div>
            ))}
          </div>
          <p className="text-[10px] text-red-500 mt-2">对比最近 {days} 天 vs 前 {days} 天。通过率下降 &gt;2% / 计数增长 &gt;10% 为退化。</p>
        </div>
      )}
      {degraded.length === 0 && regression.length > 0 && (
        <div className="bg-green-50 border border-green-200 rounded-xl p-3 text-sm text-green-700">质量退化检测: 所有指标稳定，无退化趋势。</div>
      )}

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

      {/* Risk + Suite trend */}
      {overview && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <RiskBadge level={overview.risk_level} reasons={overview.risk_reasons} />
          <div className="md:col-span-2 bg-white rounded-xl shadow-sm border p-4">
            <h3 className="text-sm font-semibold text-slate-700 mb-3">测试集通过率趋势</h3>
            <TrendChart data={suiteTrend} passKey="passed_suite_runs" failKey="failed_suite_runs" />
          </div>
        </div>
      )}

      {/* Module Risk Top 5 (P3-4B) */}
      <Section title="模块风险 Top 5" tip="risk_score = failure_rate×0.30 + recent×0.20 + defect×0.20 + blocker×0.15 + data×0.10 + flaky×0.05">
        {moduleRisk.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead><tr className="text-left text-xs text-gray-500 border-b">
                <th className="pb-2">模块</th><th className="pb-2">风险分</th><th className="pb-2">等级</th>
                <th className="pb-2">失败率</th><th className="pb-2">缺陷</th><th className="pb-2">Blocker</th>
                <th className="pb-2">Flaky</th><th className="pb-2">原因</th>
              </tr></thead>
              <tbody>
                {moduleRisk.slice(0, 5).map((m, i) => (
                  <tr key={i} className="border-b last:border-0">
                    <td className="py-2 font-medium text-gray-700">{m.module}</td>
                    <td className="py-2 font-bold">{m.risk_score.toFixed(2)}</td>
                    <td className="py-2"><span className={`px-2 py-0.5 rounded text-xs font-bold ${riskColors[m.risk_level] || ''}`}>{m.risk_level}</span></td>
                    <td className="py-2">{(m.failure_rate * 100).toFixed(0)}%</td>
                    <td className="py-2">{m.open_defects}</td>
                    <td className="py-2">{m.blocker_defects}</td>
                    <td className="py-2">{m.flaky_candidates}</td>
                    <td className="py-2 text-xs text-gray-500">{m.risk_reasons.join('; ') || '-'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : <Empty text="暂无模块风险数据 — 需要有执行记录才能计算" />}
      </Section>

      {/* Gate trend + failure modules */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Section title="质量门禁趋势">
          <TrendChart data={gateTrend} passKey="gate_passed" failKey="gate_failed" />
        </Section>
        <Section title="失败模块 Top 5">
          <MiniBar items={failModules} labelKey="module" valueKey="failed_count" />
        </Section>
      </div>

      {/* Defect trend (P3-4B) + Defect summary */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Section title="缺陷趋势" tip="新增 / 关闭 / 未关闭">
          {defectTrend.length > 0 ? (
            <div className="space-y-1 max-h-48 overflow-y-auto">
              <div className="flex text-[10px] text-gray-400 border-b pb-1">
                <span className="w-20">日期</span><span className="w-12 text-center">新增</span>
                <span className="w-12 text-center">关闭</span><span className="w-12 text-center">Reopen</span>
                <span className="w-12 text-center">未关闭</span>
              </div>
              {defectTrend.map((d, i) => (
                <div key={i} className="flex text-xs items-center">
                  <span className="w-20 text-gray-500">{d.date?.slice(5)}</span>
                  <span className="w-12 text-center text-red-600 font-medium">{d.new_defects || '-'}</span>
                  <span className="w-12 text-center text-green-600 font-medium">{d.closed_defects || '-'}</span>
                  <span className="w-12 text-center text-amber-600 font-medium">{d.reopened_defects || '-'}</span>
                  <span className="w-12 text-center font-bold">{d.open_defects}</span>
                </div>
              ))}
            </div>
          ) : <Empty />}
        </Section>
        <Section title="缺陷摘要">
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
          ) : <Empty text="暂无缺陷数据" />}
        </Section>
      </div>

      {/* Failure categories + Flaky trend (P3-4B) */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Section title="失败类型分布">
          {failCategories.length > 0 ? (
            <div className="space-y-2">
              {failCategories.map((c, i) => (
                <div key={i} className="flex items-center justify-between text-sm">
                  <span className="text-gray-600">{c.category}</span>
                  <span className="font-semibold">{c.count} <span className="text-gray-400 text-xs">({(c.percentage * 100).toFixed(0)}%)</span></span>
                </div>
              ))}
            </div>
          ) : <Empty text="暂无失败数据" />}
        </Section>
        <Section title="Flaky 趋势" tip="同一用例在同周期内既通过又失败即为 Flaky 候选">
          {flakyTrend.length > 0 ? (
            <div className="space-y-1 max-h-48 overflow-y-auto">
              <div className="flex text-[10px] text-gray-400 border-b pb-1">
                <span className="w-20">日期</span><span className="w-16 text-center">Flaky</span>
                <span className="w-16 text-center">重试</span><span className="w-16 text-center">重试恢复</span>
              </div>
              {flakyTrend.map((d, i) => (
                <div key={i} className="flex text-xs items-center">
                  <span className="w-20 text-gray-500">{d.date?.slice(5)}</span>
                  <span className="w-16 text-center text-amber-600 font-medium">{d.flaky_candidate_count}</span>
                  <span className="w-16 text-center text-blue-600 font-medium">{d.retried_cases}</span>
                  <span className="w-16 text-center text-green-600 font-medium">{d.recovered_by_retry_count}</span>
                </div>
              ))}
            </div>
          ) : <Empty text="暂无 Flaky 数据" />}
        </Section>
      </div>

      {/* Performance + Visual trend (P3-4B) */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Section title="性能趋势摘要" tip="从 performance 类型用例和 summary.performance_summary 聚合">
          {perfTrend.length > 0 ? (
            <div className="space-y-1 max-h-48 overflow-y-auto">
              <div className="flex text-[10px] text-gray-400 border-b pb-1">
                <span className="w-20">日期</span><span className="w-14 text-center">P95</span>
                <span className="w-16 text-center">错误率</span><span className="w-14 text-center">阈值失败</span>
              </div>
              {perfTrend.map((d, i) => (
                <div key={i} className="flex text-xs items-center">
                  <span className="w-20 text-gray-500">{d.date?.slice(5)}</span>
                  <span className="w-14 text-center font-medium">{d.p95_ms}ms</span>
                  <span className={`w-16 text-center font-medium ${d.error_rate > 0.05 ? 'text-red-600' : 'text-gray-600'}`}>{(d.error_rate * 100).toFixed(1)}%</span>
                  <span className={`w-14 text-center font-medium ${d.threshold_failed_count > 0 ? 'text-red-600' : 'text-gray-600'}`}>{d.threshold_failed_count}</span>
                </div>
              ))}
            </div>
          ) : <Empty text="暂无性能数据 — 需要运行 performance 类型测试" />}
        </Section>
        <Section title="视觉趋势摘要" tip="从 visual 类型用例和 summary.visual_summary 聚合">
          {visualTrend.length > 0 ? (
            <div className="space-y-1 max-h-48 overflow-y-auto">
              <div className="flex text-[10px] text-gray-400 border-b pb-1">
                <span className="w-20">日期</span><span className="w-16 text-center">视觉失败</span>
                <span className="w-20 text-center">最大 Diff</span>
              </div>
              {visualTrend.map((d, i) => (
                <div key={i} className="flex text-xs items-center">
                  <span className="w-20 text-gray-500">{d.date?.slice(5)}</span>
                  <span className={`w-16 text-center font-medium ${d.visual_failed_count > 0 ? 'text-red-600' : 'text-gray-600'}`}>{d.visual_failed_count}</span>
                  <span className="w-20 text-center font-medium">{(d.max_diff_ratio * 100).toFixed(1)}%</span>
                </div>
              ))}
            </div>
          ) : <Empty text="暂无视觉数据 — 需要运行 visual 类型测试" />}
        </Section>
      </div>

      {/* Data issues */}
      {dataIssues && (
        <Section title="测试数据问题摘要">
          <div className="grid grid-cols-2 md:grid-cols-5 gap-3 text-center text-sm">
            <Card title="校验错误" value={dataIssues.data_validation_errors} color={dataIssues.data_validation_errors > 0 ? 'red' : 'green'} />
            <Card title="缺失变量" value={dataIssues.missing_variables} color={dataIssues.missing_variables > 0 ? 'amber' : 'green'} />
            <Card title="清理失败" value={dataIssues.cleanup_failed} color={dataIssues.cleanup_failed > 0 ? 'amber' : 'green'} />
            <Card title="使用数据集" value={dataIssues.datasets_used} color="blue" />
            <Card title="问题 Run" value={dataIssues.data_issue_runs} sub={`/ ${dataIssues.total_runs_analyzed} 总 Run`} color={dataIssues.data_issue_runs > 0 ? 'amber' : 'green'} />
          </div>
        </Section>
      )}
    </div>
  )
}
