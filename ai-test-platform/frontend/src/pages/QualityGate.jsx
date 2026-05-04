import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'

export default function QualityGate() {
  const navigate = useNavigate()
  const [suites, setSuites] = useState([])
  const [selectedSuite, setSelectedSuite] = useState('')
  const [gateConfig, setGateConfig] = useState(null)
  const [running, setRunning] = useState(false)
  const [result, setResult] = useState(null)
  const [history, setHistory] = useState([])

  useEffect(() => {
    loadSuites()
    loadDefaultConfig()
  }, [])

  const loadSuites = async () => {
    try {
      const r = await fetch('/api/v2/test-suites?limit=100')
      const d = await r.json()
      setSuites(d.data || [])
    } catch {}
  }

  const loadDefaultConfig = async () => {
    try {
      const r = await fetch('/api/v2/quality-gates/default-config')
      setGateConfig(await r.json())
    } catch {}
  }

  const runGate = async () => {
    if (!selectedSuite) return
    setRunning(true)
    setResult(null)
    try {
      // 1. Execute suite
      const runRes = await fetch(`/api/v2/test-suites/${selectedSuite}/run`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({})
      })
      const runData = await runRes.json()
      if (!runData.run_id) { setResult({ gate_status: 'error', gate_failures: [{ rule: 'run_failed', message: '测试集执行失败', severity: 'blocker' }] }); return }

      // 2. Evaluate gate
      const gateRes = await fetch('/api/v2/quality-gates/evaluate', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ run_id: runData.run_id, gate_config: gateConfig })
      })
      const gateData = await gateRes.json()
      const fullResult = { ...gateData, run_id: runData.run_id, suite_summary: runData.suite_summary, timestamp: new Date().toLocaleString() }
      setResult(fullResult)
      setHistory(prev => [fullResult, ...prev].slice(0, 10))
    } catch (err) {
      setResult({ gate_status: 'error', gate_failures: [{ rule: 'error', message: err.message, severity: 'blocker' }] })
    } finally { setRunning(false) }
  }

  const selectedSuiteObj = suites.find(s => String(s.id) === String(selectedSuite))

  return (
    <div className="p-6 max-w-5xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">质量门禁</h1>
          <p className="text-sm text-gray-500 mt-1">选择测试集，执行质量门禁评估，决定是否可发布</p>
        </div>
      </div>

      {/* Config + Execute */}
      <div className="bg-white rounded-xl shadow-sm border p-6">
        <h2 className="text-sm font-semibold text-gray-700 mb-4">执行门禁</h2>
        <div className="grid grid-cols-2 gap-6">
          {/* Left: suite select */}
          <div className="space-y-4">
            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1">测试集</label>
              <select value={selectedSuite} onChange={e => setSelectedSuite(e.target.value)}
                className="w-full border rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500">
                <option value="">选择测试集...</option>
                {suites.filter(s => s.status === 'active').map(s => (
                  <option key={s.id} value={s.id}>{s.name} ({s.suite_type}) — {s.case_count || 0} 用例</option>
                ))}
              </select>
            </div>
            {selectedSuiteObj && (
              <div className="bg-gray-50 rounded-lg p-3 text-xs text-gray-600 space-y-1">
                <div><span className="font-medium">类型:</span> {selectedSuiteObj.suite_type}</div>
                <div><span className="font-medium">用例数:</span> {selectedSuiteObj.case_count || 0}</div>
                <div><span className="font-medium">优先级:</span> {selectedSuiteObj.priority}</div>
              </div>
            )}
            <button onClick={runGate} disabled={!selectedSuite || running}
              className="w-full px-4 py-2.5 bg-indigo-600 text-white rounded-lg text-sm font-medium hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition">
              {running ? (
                <span className="flex items-center justify-center gap-2">
                  <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" opacity="0.25" /><path fill="currentColor" d="M4 12a8 8 0 018-8V0C5.4 0 0 5.4 0 12h4z" opacity="0.75" /></svg>
                  执行中...
                </span>
              ) : '执行质量门禁'}
            </button>
          </div>

          {/* Right: gate config */}
          <div>
            <label className="block text-xs font-medium text-gray-500 mb-1">门禁规则</label>
            {gateConfig && (
              <div className="bg-gray-50 rounded-lg p-3 space-y-2">
                {[
                  { key: 'fail_on_any_failed', label: '任何失败即阻断', type: 'bool' },
                  { key: 'fail_on_p0_failed', label: 'P0/critical 失败即阻断', type: 'bool' },
                  { key: 'max_api_failures', label: 'API 最大失败数', type: 'num' },
                  { key: 'max_web_ui_failures', label: 'Web UI 最大失败数', type: 'num' },
                  { key: 'max_visual_failures', label: 'Visual 最大失败数', type: 'num' },
                  { key: 'performance_must_pass', label: '性能必须通过', type: 'bool' },
                  { key: 'skip_policy', label: 'Skip 策略', type: 'select', opts: ['warn', 'fail'] },
                  { key: 'xfail_policy', label: 'XFail 策略', type: 'select', opts: ['warn', 'fail'] },
                ].map(rule => (
                  <div key={rule.key} className="flex items-center justify-between text-xs">
                    <span className="text-gray-600">{rule.label}</span>
                    {rule.type === 'bool' && (
                      <button onClick={() => setGateConfig(c => ({ ...c, [rule.key]: !c[rule.key] }))}
                        className={`w-9 h-5 rounded-full transition ${gateConfig[rule.key] ? 'bg-indigo-500' : 'bg-gray-300'}`}>
                        <span className={`block w-3.5 h-3.5 rounded-full bg-white shadow transform transition ${gateConfig[rule.key] ? 'translate-x-4' : 'translate-x-0.5'}`} />
                      </button>
                    )}
                    {rule.type === 'num' && (
                      <input type="number" min="0" value={gateConfig[rule.key]} onChange={e => setGateConfig(c => ({ ...c, [rule.key]: parseInt(e.target.value) || 0 }))}
                        className="w-16 border rounded px-2 py-0.5 text-right" />
                    )}
                    {rule.type === 'select' && (
                      <select value={gateConfig[rule.key]} onChange={e => setGateConfig(c => ({ ...c, [rule.key]: e.target.value }))}
                        className="border rounded px-2 py-0.5">
                        {rule.opts.map(o => <option key={o} value={o}>{o}</option>)}
                      </select>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Result */}
      {result && (
        <div className={`rounded-xl shadow-sm border-2 p-6 ${
          result.gate_status === 'passed' ? 'bg-green-50 border-green-300' :
          result.gate_status === 'failed' ? 'bg-red-50 border-red-300' :
          'bg-yellow-50 border-yellow-300'
        }`}>
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <span className={`text-3xl`}>
                {result.gate_status === 'passed' ? '✅' : result.gate_status === 'failed' ? '❌' : '⚠️'}
              </span>
              <div>
                <h3 className={`text-xl font-bold ${
                  result.gate_status === 'passed' ? 'text-green-800' : 'text-red-800'
                }`}>
                  {result.gate_status === 'passed' ? 'Gate Passed — 可以发布' :
                   result.gate_status === 'failed' ? 'Gate Failed — 不可发布' : '评估异常'}
                </h3>
                {result.run_id && <p className="text-xs text-gray-500 mt-0.5">Run: {result.run_id}</p>}
              </div>
            </div>
            {result.run_id && (
              <button onClick={() => navigate(`/test-runs-v2/${result.run_id}`)}
                className="text-xs text-indigo-600 hover:underline">查看执行详情 →</button>
            )}
          </div>

          {/* Stats */}
          {result.suite_summary && (
            <div className="grid grid-cols-5 gap-3 mb-4">
              {[
                { label: '总用例', value: result.suite_summary.total_cases, color: 'text-gray-800' },
                { label: '通过', value: result.suite_summary.passed_cases, color: 'text-green-700' },
                { label: '失败', value: result.suite_summary.failed_cases, color: 'text-red-700' },
                { label: '跳过', value: result.suite_summary.skipped_cases, color: 'text-gray-500' },
                { label: '耗时', value: `${result.suite_summary.duration_ms}ms`, color: 'text-blue-600' },
              ].map(s => (
                <div key={s.label} className="bg-white/60 rounded-lg p-3 text-center">
                  <div className={`text-lg font-bold ${s.color}`}>{s.value}</div>
                  <div className="text-xs text-gray-500">{s.label}</div>
                </div>
              ))}
            </div>
          )}

          {/* Failures */}
          {result.gate_failures?.length > 0 && (
            <div className="space-y-2">
              <h4 className="text-sm font-semibold text-red-700">阻断规则</h4>
              {result.gate_failures.map((f, i) => (
                <div key={i} className="bg-white/80 rounded-lg px-4 py-2 flex items-start gap-2">
                  <span className="text-red-500 mt-0.5">⛔</span>
                  <div>
                    <span className="text-xs font-mono text-red-600">{f.rule}</span>
                    <p className="text-sm text-gray-700">{f.message}</p>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Warnings */}
          {result.gate_warnings?.length > 0 && (
            <div className="space-y-2 mt-3">
              <h4 className="text-sm font-semibold text-yellow-700">警告</h4>
              {result.gate_warnings.map((w, i) => (
                <div key={i} className="bg-white/80 rounded-lg px-4 py-2 flex items-start gap-2">
                  <span className="text-yellow-500 mt-0.5">⚠️</span>
                  <div>
                    <span className="text-xs font-mono text-yellow-600">{w.rule}</span>
                    <p className="text-sm text-gray-700">{w.message}</p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* History */}
      {history.length > 0 && (
        <div className="bg-white rounded-xl shadow-sm border p-5">
          <h2 className="text-sm font-semibold text-gray-700 mb-3">本次会话评估历史</h2>
          <div className="space-y-2">
            {history.map((h, i) => (
              <div key={i} className="flex items-center gap-3 text-sm border-b pb-2 last:border-0">
                <span>{h.gate_status === 'passed' ? '✅' : '❌'}</span>
                <span className="font-mono text-xs text-gray-500">{h.run_id}</span>
                <span className="text-gray-400">{h.timestamp}</span>
                <span className={`ml-auto font-semibold ${h.gate_status === 'passed' ? 'text-green-600' : 'text-red-600'}`}>
                  {h.gate_status?.toUpperCase()}
                </span>
                {h.run_id && (
                  <button onClick={() => navigate(`/test-runs-v2/${h.run_id}`)}
                    className="text-xs text-indigo-500 hover:underline">详情</button>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
