import { useState } from 'react'

const API = '/api/v2/test-selection'

const recColors = {
  must_run: 'bg-red-100 text-red-800',
  should_run: 'bg-amber-100 text-amber-800',
  optional: 'bg-blue-100 text-blue-800',
  skip_candidate: 'bg-gray-100 text-gray-600',
}
const recLabels = {
  must_run: '必须执行', should_run: '建议执行',
  optional: '可选执行', skip_candidate: '可暂缓',
}
const riskColors = {
  high: 'bg-red-50 text-red-700', medium: 'bg-amber-50 text-amber-700', low: 'bg-green-50 text-green-700',
}
const riskLabels = { high: '高风险', medium: '中风险', low: '低风险' }

function Badge({ level, map, labels }) {
  return <span className={`px-2 py-0.5 rounded text-xs font-bold ${(map || recColors)[level] || ''}`}>{(labels || recLabels)[level] || level}</span>
}

function Section({ title, tip, children, count }) {
  return (
    <div className="bg-white rounded-xl shadow-sm border p-4">
      <div className="flex items-center gap-2 mb-3">
        <h3 className="text-sm font-semibold text-slate-700">{title}</h3>
        {count !== undefined && <span className="text-xs bg-indigo-50 text-indigo-600 px-1.5 py-0.5 rounded">{count}</span>}
        {tip && <span className="text-[10px] text-gray-400 bg-gray-50 px-1.5 py-0.5 rounded">{tip}</span>}
      </div>
      {children}
    </div>
  )
}

function Empty({ text = '暂无数据' }) {
  return <div className="text-sm text-gray-400 py-4 text-center">{text}</div>
}

export default function TestSelection() {
  const [days, setDays] = useState(14)
  const [target, setTarget] = useState('')
  const [suiteType, setSuiteType] = useState('')
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const generate = async () => {
    setLoading(true)
    setError(null)
    try {
      const body = { days, include_case_recommendations: true, include_skip_candidates: true }
      if (target) body.target = target
      if (suiteType) body.suite_type = suiteType
      const r = await fetch(`${API}/recommend`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body),
      })
      if (!r.ok) throw new Error(`HTTP ${r.status}`)
      setData(await r.json())
    } catch (e) { setError(e.message) } finally { setLoading(false) }
  }

  const sm = data?.summary
  const suiteRecs = data?.suite_recommendations || []
  const caseRecs = data?.case_recommendations || []
  const modRecs = data?.module_recommendations || []
  const skipCands = data?.skip_candidates || []

  return (
    <div className="max-w-7xl mx-auto p-6 space-y-6">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <h1 className="text-2xl font-bold text-slate-900">智能选测</h1>
        <div className="flex items-center gap-2 flex-wrap">
          {[7, 14, 30].map(d => (
            <button key={d} onClick={() => setDays(d)}
              className={`px-3 py-1.5 rounded-lg text-sm font-medium transition ${days === d ? 'bg-indigo-600 text-white' : 'bg-white border text-gray-600 hover:bg-gray-50'}`}>最近 {d} 天</button>
          ))}
          <select value={target} onChange={e => setTarget(e.target.value)} className="px-2 py-1.5 rounded-lg text-sm border bg-white text-gray-600">
            <option value="">所有目标</option>
            <option value="smoke">冒烟</option>
            <option value="regression">回归</option>
            <option value="release">发布</option>
          </select>
          <select value={suiteType} onChange={e => setSuiteType(e.target.value)} className="px-2 py-1.5 rounded-lg text-sm border bg-white text-gray-600">
            <option value="">所有套件类型</option>
            <option value="smoke">smoke</option>
            <option value="regression">regression</option>
            <option value="release">release</option>
            <option value="api">api</option>
            <option value="web_ui">web_ui</option>
            <option value="performance">performance</option>
            <option value="visual">visual</option>
          </select>
          <button onClick={generate} disabled={loading}
            className="px-4 py-1.5 bg-indigo-600 text-white rounded-lg text-sm font-medium hover:bg-indigo-700 disabled:opacity-50">
            {loading ? '生成中...' : '生成推荐'}
          </button>
        </div>
      </div>

      {error && <div className="bg-red-50 border border-red-200 rounded-lg p-3 text-sm text-red-700">生成失败: {error}</div>}

      {!data && !loading && (
        <div className="bg-slate-50 border rounded-xl p-12 text-center">
          <div className="text-4xl mb-3">🎯</div>
          <div className="text-lg font-semibold text-slate-700">智能选测推荐</div>
          <p className="text-sm text-gray-500 mt-2 max-w-md mx-auto">根据历史失败、模块风险、缺陷、Flaky、性能/视觉退化等数据，推荐本次测试范围。选择时间范围后点击"生成推荐"。</p>
        </div>
      )}

      {sm && (
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-3">
          <div className="rounded-xl p-4 bg-slate-50 text-slate-700"><div className="text-2xl font-bold">{sm.total_candidates}</div><div className="text-xs mt-1 opacity-75">候选用例</div></div>
          <div className="rounded-xl p-4 bg-red-50 text-red-700"><div className="text-2xl font-bold">{sm.must_run_count}</div><div className="text-xs mt-1 opacity-75">必须执行</div></div>
          <div className="rounded-xl p-4 bg-amber-50 text-amber-700"><div className="text-2xl font-bold">{sm.should_run_count}</div><div className="text-xs mt-1 opacity-75">建议执行</div></div>
          <div className="rounded-xl p-4 bg-blue-50 text-blue-700"><div className="text-2xl font-bold">{sm.optional_count}</div><div className="text-xs mt-1 opacity-75">可选执行</div></div>
          <div className="rounded-xl p-4 bg-gray-50 text-gray-600"><div className="text-2xl font-bold">{sm.skip_candidate_count}</div><div className="text-xs mt-1 opacity-75">可暂缓</div></div>
          <div className="rounded-xl p-4 bg-violet-50 text-violet-700"><div className="text-2xl font-bold">{sm.suite_count}</div><div className="text-xs mt-1 opacity-75">推荐测试集</div></div>
        </div>
      )}

      {sm && sm.high_risk_modules && sm.high_risk_modules.length > 0 && (
        <div className="bg-red-50 border border-red-200 rounded-xl p-3 text-sm text-red-700">
          高风险模块: {sm.high_risk_modules.join(' / ')}
        </div>
      )}

      {/* Suite Recommendations */}
      {suiteRecs.length > 0 && (
        <Section title="测试集推荐" count={suiteRecs.length} tip="按风险分降序">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead><tr className="text-left text-xs text-gray-500 border-b">
                <th className="pb-2">测试集</th><th className="pb-2">类型</th><th className="pb-2">推荐</th>
                <th className="pb-2">风险分</th><th className="pb-2">用例数</th><th className="pb-2">必执行</th>
                <th className="pb-2">上次状态</th><th className="pb-2">原因</th>
              </tr></thead>
              <tbody>{suiteRecs.map((s, i) => (
                <tr key={i} className="border-b last:border-0">
                  <td className="py-2 font-medium text-gray-700">{s.suite_name}</td>
                  <td className="py-2 text-gray-500">{s.suite_type}</td>
                  <td className="py-2"><Badge level={s.recommendation_level} /></td>
                  <td className="py-2 font-bold">{s.risk_score.toFixed(2)}</td>
                  <td className="py-2">{s.case_count}</td>
                  <td className="py-2">{s.must_run_cases}</td>
                  <td className="py-2"><span className={s.last_run_status === 'failed' ? 'text-red-600' : 'text-green-600'}>{s.last_run_status}</span></td>
                  <td className="py-2 text-xs text-gray-500 max-w-xs">{s.reasons.join('; ') || '-'}</td>
                </tr>
              ))}</tbody>
            </table>
          </div>
        </Section>
      )}

      {/* Module Recommendations */}
      {modRecs.length > 0 && (
        <Section title="高风险模块" count={modRecs.length}>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead><tr className="text-left text-xs text-gray-500 border-b">
                <th className="pb-2">模块</th><th className="pb-2">风险分</th><th className="pb-2">等级</th>
                <th className="pb-2">用例数</th><th className="pb-2">失败率</th><th className="pb-2">缺陷</th>
                <th className="pb-2">Flaky</th><th className="pb-2">原因</th>
              </tr></thead>
              <tbody>{modRecs.slice(0, 10).map((m, i) => (
                <tr key={i} className="border-b last:border-0">
                  <td className="py-2 font-medium text-gray-700">{m.module}</td>
                  <td className="py-2 font-bold">{m.risk_score.toFixed(2)}</td>
                  <td className="py-2"><Badge level={m.risk_level} map={riskColors} labels={riskLabels} /></td>
                  <td className="py-2">{m.case_count}</td>
                  <td className="py-2">{(m.failure_rate * 100).toFixed(0)}%</td>
                  <td className="py-2">{m.open_defects}</td>
                  <td className="py-2">{m.flaky_candidates}</td>
                  <td className="py-2 text-xs text-gray-500 max-w-xs">{m.reasons.join('; ') || '-'}</td>
                </tr>
              ))}</tbody>
            </table>
          </div>
        </Section>
      )}

      {/* Case Recommendations */}
      {caseRecs.length > 0 && (
        <Section title="用例推荐" count={caseRecs.length} tip="风险分 >= 0.75 必须执行">
          <div className="overflow-x-auto max-h-96 overflow-y-auto">
            <table className="w-full text-sm">
              <thead className="sticky top-0 bg-white"><tr className="text-left text-xs text-gray-500 border-b">
                <th className="pb-2">用例</th><th className="pb-2">类型</th><th className="pb-2">模块</th>
                <th className="pb-2">优先级</th><th className="pb-2">推荐</th><th className="pb-2">风险分</th>
                <th className="pb-2">上次</th><th className="pb-2">原因</th>
              </tr></thead>
              <tbody>{caseRecs.slice(0, 50).map((c, i) => (
                <tr key={i} className="border-b last:border-0">
                  <td className="py-1.5 font-medium text-gray-700 max-w-[200px] truncate" title={c.title}>{c.title}</td>
                  <td className="py-1.5 text-gray-500">{c.case_type}</td>
                  <td className="py-1.5 text-gray-500">{c.module}</td>
                  <td className="py-1.5">{c.priority}</td>
                  <td className="py-1.5"><Badge level={c.recommendation_level} /></td>
                  <td className="py-1.5 font-bold">{c.risk_score.toFixed(2)}</td>
                  <td className="py-1.5"><span className={c.last_status === 'failed' ? 'text-red-600' : 'text-green-600'}>{c.last_status}</span></td>
                  <td className="py-1.5 text-xs text-gray-500 max-w-[200px] truncate" title={c.reasons.join('; ')}>{c.reasons.join('; ') || '-'}</td>
                </tr>
              ))}</tbody>
            </table>
          </div>
          {caseRecs.length > 50 && <div className="text-xs text-gray-400 mt-2 text-center">显示前 50 条，共 {caseRecs.length} 条</div>}
        </Section>
      )}

      {/* Skip Candidates */}
      {skipCands.length > 0 && (
        <Section title="可暂缓执行候选" count={skipCands.length} tip="仅建议，不自动跳过">
          <div className="overflow-x-auto max-h-64 overflow-y-auto">
            <table className="w-full text-sm">
              <thead className="sticky top-0 bg-white"><tr className="text-left text-xs text-gray-500 border-b">
                <th className="pb-2">用例</th><th className="pb-2">类型</th><th className="pb-2">模块</th>
                <th className="pb-2">连续通过</th><th className="pb-2">风险分</th><th className="pb-2">原因</th>
              </tr></thead>
              <tbody>{skipCands.slice(0, 30).map((c, i) => (
                <tr key={i} className="border-b last:border-0">
                  <td className="py-1.5 font-medium text-gray-700 max-w-[200px] truncate" title={c.title}>{c.title}</td>
                  <td className="py-1.5 text-gray-500">{c.case_type}</td>
                  <td className="py-1.5 text-gray-500">{c.module}</td>
                  <td className="py-1.5 text-green-600 font-medium">{c.pass_streak} 次</td>
                  <td className="py-1.5">{c.risk_score.toFixed(2)}</td>
                  <td className="py-1.5 text-xs text-gray-500 max-w-[200px] truncate" title={c.reasons.join('; ')}>{c.reasons.join('; ') || '低风险、连续通过'}</td>
                </tr>
              ))}</tbody>
            </table>
          </div>
          <div className="mt-2 text-[10px] text-amber-600 bg-amber-50 rounded p-2">
            以上用例仅为暂缓建议，不会自动跳过。最终是否执行由测试负责人决定。
          </div>
        </Section>
      )}

      {data && caseRecs.length === 0 && skipCands.length === 0 && suiteRecs.length === 0 && (
        <div className="bg-slate-50 border rounded-xl p-8 text-center text-sm text-gray-500">
          暂无推荐数据。可能原因：无历史执行记录、或所有用例风险较低。
        </div>
      )}
    </div>
  )
}
