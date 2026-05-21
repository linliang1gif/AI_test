import { useState, useEffect, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import api from '../services/api'

const STATUS_LABELS = { planning: '规划中', in_progress: '进行中', testing: '测试中', completed: '已完成', archived: '已归档' }
const STATUS_COLORS = { planning: 'bg-slate-100 text-slate-700', in_progress: 'bg-blue-100 text-blue-700', testing: 'bg-yellow-100 text-yellow-800', completed: 'bg-green-100 text-green-700', archived: 'bg-gray-100 text-gray-500' }
const TABS = ['概览', '需求', 'AI解析', '测试点', '测试用例', '执行集', '测试报告']

export default function IterationDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [tab, setTab] = useState(0)
  const [iter, setIter] = useState(null)
  const [loading, setLoading] = useState(true)
  const [msg, setMsg] = useState({ text: '', type: '' })

  // Data per tab
  const [requirements, setRequirements] = useState([])
  const [analysis, setAnalysis] = useState(null)
  const [testPoints, setTestPoints] = useState([])
  const [testCases, setTestCases] = useState([])
  const [execSets, setExecSets] = useState([])
  const [report, setReport] = useState(null)

  // Forms
  const [reqForm, setReqForm] = useState({ title: '', content: '', risk_level: 'P1' })
  const [actionLoading, setActionLoading] = useState(false)
  const templatePoints = testPoints.filter(tp => String(tp.test_type || '').startsWith('template_'))

  const flash = (text, type = 'info') => { setMsg({ text, type }); setTimeout(() => setMsg({ text: '', type: '' }), 4000) }

  const loadIter = useCallback(() => {
    api.v2.iterations.get(id).then(r => { setIter(r); setLoading(false) }).catch(() => { flash('加载迭代失败', 'error'); setLoading(false) })
  }, [id])

  useEffect(() => { loadIter() }, [loadIter])

  useEffect(() => {
    if (!id) return
    if (tab === 1) api.v2.iterations.listRequirements(id).then(r => setRequirements(r.requirements || [])).catch(() => {})
    if (tab === 3) api.v2.iterations.listTestPoints(id).then(r => setTestPoints(r.test_points || [])).catch(() => {})
    if (tab === 4) api.v2.iterations.listTestCases(id).then(r => setTestCases(r.test_cases || [])).catch(() => {})
    if (tab === 5) api.v2.iterations.listExecutionSets(id).then(r => setExecSets(r.execution_sets || [])).catch(() => {})
    if (tab === 6) api.v2.iterations.getReport(id).then(r => setReport(r)).catch(() => setReport(null))
  }, [id, tab])

  if (loading) return <div className="p-12 text-center text-slate-500">加载中...</div>
  if (!iter) return <div className="p-12 text-center text-slate-500">迭代不存在</div>

  // ── Actions ──
  const addRequirement = async () => {
    if (!reqForm.title.trim()) { flash('请输入需求标题', 'error'); return }
    setActionLoading(true)
    try {
      await api.v2.iterations.createRequirement(id, reqForm)
      setReqForm({ title: '', content: '', risk_level: 'P1' })
      const r = await api.v2.iterations.listRequirements(id)
      setRequirements(r.requirements || [])
      flash('需求已录入')
    } catch (e) { flash(e.message || '录入失败', 'error') }
    setActionLoading(false)
  }

  const runAiAnalysis = async () => {
    setActionLoading(true)
    try {
      const r = await api.v2.iterations.analyzeRequirements(id)
      setAnalysis(r.analysis || r)
      flash(`AI解析完成 (${r.source || 'unknown'})`)
    } catch (e) { flash(e.message || 'AI解析失败', 'error') }
    setActionLoading(false)
  }

  const genTestPoints = async () => {
    setActionLoading(true)
    try {
      const r = await api.v2.iterations.generateTestPoints(id)
      flash(`生成 ${r.generated} 个测试点 (${r.source || 'fallback'})`)
      const tp = await api.v2.iterations.listTestPoints(id)
      setTestPoints(tp.test_points || [])
    } catch (e) { flash(e.message || '生成失败', 'error') }
    setActionLoading(false)
  }

  const confirmTP = async (tpId, confirmed) => {
    try {
      await api.v2.iterations.confirmTestPoint(tpId, confirmed)
      setTestPoints(prev => prev.map(tp => tp.id === tpId ? { ...tp, confirmed } : tp))
    } catch (e) { flash(e.message || '操作失败', 'error') }
  }

  const genTestCases = async () => {
    setActionLoading(true)
    try {
      const r = await api.v2.iterations.generateTestCases(id)
      flash(`生成 ${r.generated} 个测试用例`)
      const tc = await api.v2.iterations.listTestCases(id)
      setTestCases(tc.test_cases || [])
    } catch (e) { flash(e.message || '生成失败', 'error') }
    setActionLoading(false)
  }

  const createExecSet = async (type) => {
    setActionLoading(true)
    try {
      await api.v2.iterations.createExecutionSet(id, { type })
      flash(`${type} 执行集已创建`)
      const es = await api.v2.iterations.listExecutionSets(id)
      setExecSets(es.execution_sets || [])
    } catch (e) { flash(e.message || '创建失败', 'error') }
    setActionLoading(false)
  }

  const runIteration = async (executionSetId = null) => {
    setActionLoading(true)
    try {
      const safeExecutionSetId = typeof executionSetId === 'number' || typeof executionSetId === 'string' ? executionSetId : null
      const payload = safeExecutionSetId ? { execution_set_id: safeExecutionSetId } : {}
      const r = await api.v2.iterations.run(id, payload)
      flash(`执行完成: ${r.run_id} | 通过 ${r.passed}/${r.total_cases} | 通过率 ${r.pass_rate}%`)
      loadIter()
      const es = await api.v2.iterations.listExecutionSets(id)
      setExecSets(es.execution_sets || [])
    } catch (e) { flash(e.message || '执行失败', 'error') }
    setActionLoading(false)
  }

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex items-center gap-3 mb-1">
        <button onClick={() => navigate('/iterations')} className="text-blue-600 hover:text-blue-800 text-sm">&larr; 迭代列表</button>
      </div>
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <h1 className="text-2xl font-bold text-slate-900">{iter.name}</h1>
          {iter.version && <span className="text-xs bg-slate-100 px-2 py-0.5 rounded">v{iter.version}</span>}
          <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${STATUS_COLORS[iter.status] || ''}`}>{STATUS_LABELS[iter.status] || iter.status}</span>
        </div>
        <button onClick={() => runIteration()} disabled={actionLoading} className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 text-sm font-medium disabled:opacity-50">
          执行迭代测试
        </button>
      </div>

      {/* Message bar */}
      {msg.text && (
        <div className={`mb-4 p-3 rounded-lg text-sm ${msg.type === 'error' ? 'bg-red-50 text-red-700' : 'bg-blue-50 text-blue-700'}`}>{msg.text}</div>
      )}

      {/* Tab bar */}
      <div className="flex border-b border-slate-200 mb-6">
        {TABS.map((t, i) => (
          <button key={t} onClick={() => setTab(i)}
            className={`px-4 py-2.5 text-sm font-medium border-b-2 transition-colors ${tab === i ? 'border-blue-600 text-blue-700' : 'border-transparent text-slate-500 hover:text-slate-700'}`}>
            {t}
          </button>
        ))}
      </div>

      {/* Tab content */}
      <div className="min-h-[400px]">

        {/* ═══ 0: 概览 ═══ */}
        {tab === 0 && (
          <div className="space-y-6">
            <div className="bg-blue-50 border border-blue-100 rounded-lg p-4">
              <h3 className="font-semibold text-blue-900 mb-2">新迭代标准流程</h3>
              <p className="text-sm text-blue-800">
                创建迭代 → 选择迭代模板 → 确认模板测试点 → 录入需求 → AI解析 → 生成测试点 → 确认测试点 → 生成用例 → 创建执行集 → 执行测试 → 生成报告 → 缺陷进入 /defects。
              </p>
              <p className="text-xs text-blue-700 mt-2">迭代模板只能在 /iterations 新建迭代时选择；已创建迭代可继续在“测试点”页确认模板初始检查项。</p>
            </div>
          <div className="grid grid-cols-2 gap-6">
            <div className="bg-white border rounded-lg p-5">
              <h3 className="font-semibold text-slate-800 mb-3">基本信息</h3>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between"><span className="text-slate-500">负责人</span><span>{iter.owner || '-'}</span></div>
                <div className="flex justify-between"><span className="text-slate-500">测试负责人</span><span>{iter.test_owner || '-'}</span></div>
                <div className="flex justify-between"><span className="text-slate-500">计划开始</span><span>{iter.planned_start_time || iter.start_date || '-'}</span></div>
                <div className="flex justify-between"><span className="text-slate-500">计划发布</span><span>{iter.planned_release_time || iter.end_date || '-'}</span></div>
                {iter.description && <div className="pt-2 border-t mt-2"><span className="text-slate-500">描述: </span>{iter.description}</div>}
              </div>
            </div>
            <div className="bg-white border rounded-lg p-5">
              <h3 className="font-semibold text-slate-800 mb-3">统计</h3>
              <div className="grid grid-cols-2 gap-4 text-center">
                <div className="bg-slate-50 rounded-lg p-3"><div className="text-2xl font-bold">{iter.requirement_count ?? 0}</div><div className="text-xs text-slate-500">需求</div></div>
                <div className="bg-slate-50 rounded-lg p-3"><div className="text-2xl font-bold">{iter.test_point_confirmed ?? 0}/{iter.test_point_total ?? 0}</div><div className="text-xs text-slate-500">测试点(已确认/总)</div></div>
                <div className="bg-slate-50 rounded-lg p-3"><div className="text-2xl font-bold">{iter.total_cases ?? 0}</div><div className="text-xs text-slate-500">用例</div></div>
                <div className="bg-blue-50 rounded-lg p-3"><div className="text-2xl font-bold text-blue-600">{iter.pass_rate ?? 0}%</div><div className="text-xs text-slate-500">通过率</div></div>
              </div>
            </div>
          </div>
          </div>
        )}

        {/* ═══ 1: 需求 ═══ */}
        {tab === 1 && (
          <div>
            <div className="bg-white border rounded-lg p-4 mb-4">
              <h3 className="font-semibold text-sm mb-3">录入需求</h3>
              <div className="flex gap-3 items-end">
                <div className="flex-1">
                  <input value={reqForm.title} onChange={e => setReqForm({...reqForm, title: e.target.value})}
                    placeholder="需求标题" className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm" />
                </div>
                <select value={reqForm.risk_level} onChange={e => setReqForm({...reqForm, risk_level: e.target.value})}
                  className="px-3 py-2 border border-slate-300 rounded-lg text-sm">
                  <option value="P0">P0</option><option value="P1">P1</option><option value="P2">P2</option>
                </select>
                <button onClick={addRequirement} disabled={actionLoading} className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700 disabled:opacity-50 whitespace-nowrap">
                  添加
                </button>
              </div>
              <textarea value={reqForm.content} onChange={e => setReqForm({...reqForm, content: e.target.value})}
                placeholder="需求详细内容（可选）" className="w-full mt-2 px-3 py-2 border border-slate-300 rounded-lg text-sm" rows={2} />
            </div>
            {requirements.length === 0 ? (
              <div className="text-center py-8 text-slate-400">暂无需求</div>
            ) : (
              <div className="space-y-2">
                {requirements.map(r => (
                  <div key={r.id} className="bg-white border rounded-lg p-4">
                    <div className="flex items-center gap-2">
                      <span className={`text-xs px-1.5 py-0.5 rounded font-medium ${r.risk_level === 'P0' ? 'bg-red-100 text-red-700' : r.risk_level === 'P1' ? 'bg-yellow-100 text-yellow-700' : 'bg-slate-100 text-slate-600'}`}>{r.risk_level}</span>
                      <span className="font-medium text-sm">{r.title}</span>
                    </div>
                    {r.content && <p className="text-xs text-slate-500 mt-1">{r.content}</p>}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* ═══ 2: AI解析 ═══ */}
        {tab === 2 && (
          <div>
            <button onClick={runAiAnalysis} disabled={actionLoading}
              className="mb-4 px-4 py-2 bg-purple-600 text-white rounded-lg text-sm hover:bg-purple-700 disabled:opacity-50">
              {actionLoading ? '解析中...' : 'AI 解析需求'}
            </button>
            {analysis ? (
              <div className="grid grid-cols-2 gap-4">
                {[
                  ['功能点', 'functional_points', 'bg-blue-50'],
                  ['业务规则', 'business_rules', 'bg-green-50'],
                  ['影响范围', 'impact_scope', 'bg-yellow-50'],
                  ['风险点', 'risk_points', 'bg-red-50'],
                  ['待确认问题', 'confirm_questions', 'bg-purple-50'],
                ].map(([label, key, bg]) => (
                  <div key={key} className={`${bg} rounded-lg p-4`}>
                    <h4 className="font-semibold text-sm mb-2">{label}</h4>
                    <ul className="text-xs space-y-1">
                      {(analysis[key] || []).map((item, i) => (
                        <li key={i} className="text-slate-700">• {typeof item === 'string' ? item : item.test_point || JSON.stringify(item)}</li>
                      ))}
                      {(analysis[key] || []).length === 0 && <li className="text-slate-400">暂无</li>}
                    </ul>
                  </div>
                ))}
                <div className="bg-indigo-50 rounded-lg p-4">
                  <h4 className="font-semibold text-sm mb-2">测试点建议 ({(analysis.test_points || []).length})</h4>
                  <ul className="text-xs space-y-1">
                    {(analysis.test_points || []).map((tp, i) => (
                      <li key={i} className="text-slate-700">• {typeof tp === 'string' ? tp : tp.test_point || JSON.stringify(tp)}</li>
                    ))}
                  </ul>
                </div>
              </div>
            ) : (
              <div className="text-center py-8 text-slate-400">点击上方按钮开始 AI 解析</div>
            )}
          </div>
        )}

        {/* ═══ 3: 测试点 ═══ */}
        {tab === 3 && (
          <div>
            <div className="flex gap-3 mb-4">
              <button onClick={genTestPoints} disabled={actionLoading} className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700 disabled:opacity-50">
                {actionLoading ? '生成中...' : '生成测试点'}
              </button>
              <span className="text-sm text-slate-500 self-center">
                共 {testPoints.length} 个 | 已确认 {testPoints.filter(t => t.confirmed).length} 个
              </span>
            </div>
            {templatePoints.length > 0 && (
              <div className="mb-4 bg-amber-50 border border-amber-100 rounded-lg p-3 text-sm text-amber-800">
                已根据迭代模板生成 {templatePoints.length} 个初始检查项。请先确认适用的模板测试点，再继续生成测试用例；这些检查项不会替代 AI 解析需求。
              </div>
            )}
            {testPoints.length === 0 ? (
              <div className="text-center py-8 text-slate-400">暂无测试点</div>
            ) : (
              <div className="space-y-2">
                {testPoints.map(tp => (
                  <div key={tp.id} className="bg-white border rounded-lg p-4 flex items-center justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        {String(tp.test_type || '').startsWith('template_') && <span className="text-xs bg-amber-100 text-amber-700 px-1.5 py-0.5 rounded">模板</span>}
                        {tp.ai_generated && <span className="text-xs bg-purple-100 text-purple-700 px-1.5 py-0.5 rounded">AI</span>}
                        <span className={`text-xs px-1.5 py-0.5 rounded ${tp.priority === 'high' ? 'bg-red-100 text-red-700' : tp.priority === 'medium' ? 'bg-yellow-100 text-yellow-700' : 'bg-slate-100 text-slate-600'}`}>{tp.priority}</span>
                        <span className="text-sm font-medium">{tp.test_point}</span>
                      </div>
                      <div className="text-xs text-slate-500 mt-1">{tp.test_type} | {tp.risk_level}</div>
                    </div>
                    <button onClick={() => confirmTP(tp.id, !tp.confirmed)}
                      className={`ml-4 px-3 py-1.5 rounded-lg text-xs font-medium ${tp.confirmed ? 'bg-green-100 text-green-700 hover:bg-green-200' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'}`}>
                      {tp.confirmed ? '✓ 已确认' : '确认'}
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* ═══ 4: 测试用例 ═══ */}
        {tab === 4 && (
          <div>
            <button onClick={genTestCases} disabled={actionLoading} className="mb-4 px-4 py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700 disabled:opacity-50">
              {actionLoading ? '生成中...' : '根据测试点生成用例'}
            </button>
            {testCases.length === 0 ? (
              <div className="text-center py-8 text-slate-400">暂无用例，请先确认测试点后生成</div>
            ) : (
              <table className="w-full text-sm">
                <thead className="bg-slate-50"><tr>
                  <th className="text-left p-3 font-medium text-slate-600">ID</th>
                  <th className="text-left p-3 font-medium text-slate-600">名称</th>
                  <th className="text-left p-3 font-medium text-slate-600">优先级</th>
                  <th className="text-left p-3 font-medium text-slate-600">类型</th>
                  <th className="text-left p-3 font-medium text-slate-600">状态</th>
                </tr></thead>
                <tbody>
                  {testCases.map(c => (
                    <tr key={c.id} className="border-t border-slate-100 hover:bg-slate-50">
                      <td className="p-3 font-mono text-xs text-slate-500">{c.id}</td>
                      <td className="p-3">{c.name}</td>
                      <td className="p-3"><span className={`text-xs px-1.5 py-0.5 rounded ${c.priority === 'high' ? 'bg-red-100 text-red-700' : 'bg-slate-100'}`}>{c.priority}</span></td>
                      <td className="p-3 text-xs text-slate-500">{c.case_type}</td>
                      <td className="p-3"><span className={`text-xs px-1.5 py-0.5 rounded ${c.last_run_status === 'passed' ? 'bg-green-100 text-green-700' : c.last_run_status === 'failed' ? 'bg-red-100 text-red-700' : 'bg-slate-100 text-slate-500'}`}>{c.last_run_status}</span></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        )}

        {/* ═══ 5: 执行集 ═══ */}
        {tab === 5 && (
          <div>
            <div className="flex gap-3 mb-4">
              {['smoke', 'iteration', 'regression'].map(t => (
                <button key={t} onClick={() => createExecSet(t)} disabled={actionLoading}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700 disabled:opacity-50">
                  创建{t === 'smoke' ? '冒烟' : t === 'iteration' ? '迭代' : '回归'}执行集
                </button>
              ))}
            </div>
            {execSets.length === 0 ? (
              <div className="text-center py-8 text-slate-400">暂无执行集</div>
            ) : (
              <div className="space-y-2">
                {execSets.map(es => {
                  const sc = { created: 'bg-slate-100 text-slate-700', running: 'bg-blue-100 text-blue-700', passed: 'bg-green-100 text-green-700', failed: 'bg-red-100 text-red-700', partial: 'bg-yellow-100 text-yellow-800', error: 'bg-red-100 text-red-700' }
                  return (
                    <div key={es.id} className="bg-white border rounded-lg p-4 flex items-center justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <span className="font-medium text-sm">{es.name}</span>
                          <span className={`text-xs px-1.5 py-0.5 rounded-full font-medium ${sc[es.status] || 'bg-slate-100'}`}>{es.status}</span>
                        </div>
                        <div className="text-xs text-slate-500 mt-1">
                          类型: {es.type} | 用例数: {es.case_count}
                          {es.run_id && <span> | Run: <span className="font-mono text-blue-600">{es.run_id}</span></span>}
                        </div>
                      </div>
                      <button onClick={() => runIteration(es.id)} disabled={actionLoading}
                        className="ml-4 px-3 py-1.5 bg-green-600 text-white rounded-lg text-xs font-medium hover:bg-green-700 disabled:opacity-50">
                        {actionLoading ? '执行中...' : '执行'}
                      </button>
                    </div>
                  )
                })}
              </div>
            )}
          </div>
        )}

        {/* ═══ 6: 测试报告 ═══ */}
        {tab === 6 && (
          <div>
            <button onClick={() => api.v2.iterations.getReport(id).then(r => setReport(r)).catch(() => flash('加载报告失败', 'error'))}
              className="mb-4 px-4 py-2 bg-slate-600 text-white rounded-lg text-sm hover:bg-slate-700">
              刷新报告
            </button>
            {report ? (
              <div className="space-y-4">
                <div className="bg-white border rounded-lg p-4">
                  <div className="grid grid-cols-4 gap-4 text-sm">
                    <div>
                      <div className="text-xs text-slate-500">数据来源</div>
                      <div className="font-mono text-slate-800">{report.data_source || '-'}</div>
                    </div>
                    <div>
                      <div className="text-xs text-slate-500">Latest Run</div>
                      <div className="font-mono text-slate-800 break-all">{report.latest_run_id || '-'}</div>
                    </div>
                    <div>
                      <div className="text-xs text-slate-500">Latest Execution Set</div>
                      <div className="font-mono text-slate-800">{report.latest_execution_set_id || '-'}</div>
                    </div>
                    <div>
                      <div className="text-xs text-slate-500">生成时间</div>
                      <div className="text-slate-800">{report.generated_at ? report.generated_at.slice(0, 19).replace('T', ' ') : '-'}</div>
                    </div>
                  </div>
                </div>

                {(report.empty === true || report.has_real_result === false) && (
                  <div className="bg-slate-50 border border-slate-200 rounded-lg p-4 text-sm text-slate-600">
                    {report.message || '暂无真实执行结果，请先创建执行集并执行测试。'}
                  </div>
                )}

                {(report.error_cases || report.stats?.error_cases || 0) > 0 && (
                  <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 text-sm text-amber-800">
                    执行失败：请先配置测试环境或检查用例请求参数。
                  </div>
                )}

                {/* Release Recommendation */}
                {report.release_recommendation && (
                  <div className={`rounded-lg p-4 border ${
                    report.release_recommendation === 'pass' ? 'bg-green-50 border-green-200' :
                    report.release_recommendation === 'conditional_pass' ? 'bg-yellow-50 border-yellow-200' :
                    'bg-red-50 border-red-200'
                  }`}>
                    <div className="flex items-center gap-3">
                      <span className={`text-lg font-bold ${
                        report.release_recommendation === 'pass' ? 'text-green-700' :
                        report.release_recommendation === 'conditional_pass' ? 'text-yellow-700' :
                        'text-red-700'
                      }`}>
                        {report.release_recommendation === 'pass' ? '✅ 可发布' :
                         report.release_recommendation === 'conditional_pass' ? '⚠️ 有条件发布' :
                         '🚫 阻塞发布'}
                      </span>
                      <span className="text-sm text-slate-600">{report.release_reason}</span>
                    </div>
                    {report.latest_run_id && <div className="text-xs text-slate-500 mt-1">最新 Run: <span className="font-mono">{report.latest_run_id}</span></div>}
                  </div>
                )}

                {/* Stats */}
                <div className="bg-white border rounded-lg p-5">
                  <h3 className="font-semibold mb-3">统计概览</h3>
                  <div className="grid grid-cols-6 gap-4 text-center">
                    <div className="bg-slate-50 rounded p-3"><div className="text-xl font-bold">{report.stats?.total_cases ?? 0}</div><div className="text-xs text-slate-500">总用例</div></div>
                    <div className="bg-blue-50 rounded p-3"><div className="text-xl font-bold text-blue-600">{report.stats?.executed_cases ?? 0}</div><div className="text-xs text-slate-500">已执行</div></div>
                    <div className="bg-green-50 rounded p-3"><div className="text-xl font-bold text-green-600">{report.stats?.passed_cases ?? 0}</div><div className="text-xs text-slate-500">通过</div></div>
                    <div className="bg-red-50 rounded p-3"><div className="text-xl font-bold text-red-600">{report.stats?.failed_cases ?? 0}</div><div className="text-xs text-slate-500">失败</div></div>
                    <div className="bg-amber-50 rounded p-3"><div className="text-xl font-bold text-amber-600">{report.stats?.error_cases ?? 0}</div><div className="text-xs text-slate-500">错误</div></div>
                    <div className="bg-indigo-50 rounded p-3"><div className="text-xl font-bold text-indigo-600">{report.stats?.pass_rate ?? report.pass_rate ?? 0}%</div><div className="text-xs text-slate-500">通过率</div></div>
                  </div>
                </div>

                {/* Failure Categories + Risk Summary */}
                <div className="grid grid-cols-2 gap-4">
                  {report.failure_categories && Object.keys(report.failure_categories).length > 0 && (
                    <div className="bg-white border rounded-lg p-5">
                      <h3 className="font-semibold mb-3">失败分类</h3>
                      <div className="space-y-2">
                        {Object.entries(report.failure_categories).map(([cat, count]) => (
                          <div key={cat} className="flex justify-between text-sm">
                            <span className="text-slate-600">{cat}</span>
                            <span className="font-medium text-red-600">{count}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                  {report.risk_summary && (
                    <div className="bg-white border rounded-lg p-5">
                      <h3 className="font-semibold mb-3">风险摘要</h3>
                      <div className="space-y-2 text-sm">
                        <div className="flex justify-between"><span className="text-slate-600">P0 失败</span><span className={`font-medium ${report.risk_summary.p0_failed > 0 ? 'text-red-600' : 'text-green-600'}`}>{report.risk_summary.p0_failed}</span></div>
                        <div className="flex justify-between"><span className="text-slate-600">P1 失败</span><span className={`font-medium ${report.risk_summary.p1_failed > 0 ? 'text-yellow-600' : 'text-green-600'}`}>{report.risk_summary.p1_failed}</span></div>
                        <div className="flex justify-between"><span className="text-slate-600">总失败</span><span className="font-medium">{report.risk_summary.total_failed}</span></div>
                      </div>
                    </div>
                  )}
                </div>

                {/* Runs */}
                {report.runs && report.runs.length > 0 && (
                  <div className="bg-white border rounded-lg p-5">
                    <h3 className="font-semibold mb-3">执行记录</h3>
                    <table className="w-full text-sm">
                      <thead className="bg-slate-50"><tr>
                        <th className="text-left p-2">Run ID</th><th className="text-left p-2">状态</th>
                        <th className="text-left p-2">通过</th><th className="text-left p-2">失败</th>
                        <th className="text-left p-2">错误</th><th className="text-left p-2">耗时</th><th className="text-left p-2">时间</th>
                      </tr></thead>
                      <tbody>
                        {report.runs.map(r => (
                          <tr key={r.run_id} className="border-t border-slate-100">
                            <td className="p-2 font-mono text-xs">{r.run_id}</td>
                            <td className="p-2"><span className={`text-xs px-1.5 py-0.5 rounded ${r.status === 'passed' ? 'bg-green-100 text-green-700' : r.status === 'failed' ? 'bg-red-100 text-red-700' : 'bg-slate-100 text-slate-600'}`}>{r.status}</span></td>
                            <td className="p-2 text-xs text-green-600">{r.passed ?? 0}</td>
                            <td className="p-2 text-xs text-red-600">{r.failed ?? 0}</td>
                            <td className="p-2 text-xs text-amber-600">{r.error ?? 0}</td>
                            <td className="p-2 text-xs text-slate-500">{r.duration ? `${r.duration}s` : '-'}</td>
                            <td className="p-2 text-xs text-slate-500">{r.created_at?.slice(0, 16)}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            ) : (
              <div className="text-center py-8 text-slate-400">暂无报告数据，请先执行测试</div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
