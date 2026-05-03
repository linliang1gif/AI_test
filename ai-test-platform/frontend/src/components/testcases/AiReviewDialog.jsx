/**
 * P2-9A.2: AI 评审结果弹窗
 */
export default function AiReviewDialog({
  show,
  reviewResult,
  healingCases,
  healPreviews,
  onClose,
  onHealPreview,
  onHealRetry,
  onShowHealDialog,
  onLocateCase,
}) {
  if (!show || !reviewResult) return null

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl p-6 w-[800px] max-h-[85vh] overflow-y-auto">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-bold">AI 用例评审报告</h2>
          <div className="flex items-center gap-2">
            <span className={`text-xs px-2 py-1 rounded ${reviewResult.ai_enhanced ? 'bg-purple-100 text-purple-700' : 'bg-gray-100 text-gray-600'}`}>
              {reviewResult.ai_enhanced ? '规则+AI' : '规则评审'}
            </span>
            <button onClick={onClose} className="text-gray-400 hover:text-gray-600 text-xl">✕</button>
          </div>
        </div>

        {/* 评分概览 */}
        <div className="flex items-center gap-6 mb-5 p-4 bg-gradient-to-r from-indigo-50 to-purple-50 rounded-lg">
          <div className="text-center">
            <div className={`text-4xl font-bold ${reviewResult.quality_score >= 80 ? 'text-green-600' : reviewResult.quality_score >= 50 ? 'text-yellow-600' : 'text-red-600'}`}>
              {reviewResult.quality_score}
            </div>
            <div className="text-xs text-gray-500 mt-1">质量评分</div>
          </div>
          <div className="flex-1 grid grid-cols-4 gap-3 text-center text-sm">
            <div><div className="text-lg font-bold">{reviewResult.total_cases}</div><div className="text-xs text-gray-500">总用例</div></div>
            <div><div className="text-lg font-bold text-green-600">{reviewResult.automatable_cases}</div><div className="text-xs text-gray-500">可自动化</div></div>
            <div><div className="text-lg font-bold text-red-600">{reviewResult.missing_assertion_count}</div><div className="text-xs text-gray-500">缺少断言</div></div>
            <div><div className="text-lg font-bold text-orange-600">{reviewResult.high_risk_count}</div><div className="text-xs text-gray-500">高风险接口</div></div>
          </div>
        </div>

        {reviewResult.risk_summary && (
          <div className="mb-4 flex gap-3">
            <span className="px-3 py-1 bg-red-100 text-red-700 rounded text-sm font-medium">高风险 {reviewResult.risk_summary.high}</span>
            <span className="px-3 py-1 bg-yellow-100 text-yellow-700 rounded text-sm font-medium">中风险 {reviewResult.risk_summary.medium}</span>
            <span className="px-3 py-1 bg-green-100 text-green-700 rounded text-sm font-medium">低风险 {reviewResult.risk_summary.low}</span>
          </div>
        )}

        <div className="grid grid-cols-3 gap-3 mb-4 text-sm">
          <div className="p-3 bg-gray-50 rounded"><span className="text-gray-500">缺少预期:</span> <span className="font-bold">{reviewResult.missing_expected_count}</span></div>
          <div className="p-3 bg-gray-50 rounded"><span className="text-gray-500">缺少步骤:</span> <span className="font-bold">{reviewResult.missing_steps_count}</span></div>
          <div className="p-3 bg-gray-50 rounded"><span className="text-gray-500">重复用例:</span> <span className="font-bold">{reviewResult.duplicate_count}</span></div>
        </div>

        {/* 改进建议 */}
        {reviewResult.improvement_suggestions?.length > 0 && (
          <div className="mb-4">
            <h3 className="text-sm font-semibold mb-2">改进建议</h3>
            <ul className="space-y-1">
              {reviewResult.improvement_suggestions.map((s, i) => (
                <li key={i} className="text-sm text-gray-700 bg-yellow-50 p-2 rounded">
                  {typeof s === 'string' ? s : (
                    <>
                      <span>{s.suggestion}</span>
                      {s.affected_cases?.length > 0 && <span className="ml-2 text-gray-500">[{s.affected_cases.join(', ')}]</span>}
                      {s.impact && <span className={`ml-2 px-1 rounded text-xs ${s.impact === 'high' ? 'bg-red-100 text-red-600' : 'bg-gray-100 text-gray-600'}`}>{s.impact}</span>}
                    </>
                  )}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* AI 补充建议 */}
        {reviewResult.ai_suggestions?.length > 0 && (
          <div className="mb-4">
            <h3 className="text-sm font-semibold mb-2 text-purple-700">AI 补充建议</h3>
            <ul className="space-y-1">
              {reviewResult.ai_suggestions.map((s, i) => (
                <li key={i} className="text-sm text-purple-700 bg-purple-50 p-2 rounded">
                  {typeof s === 'string' ? s : (
                    <>
                      <span>{s.suggestion}</span>
                      {s.affected_cases?.length > 0 && <span className="ml-2 text-gray-500">[{s.affected_cases.join(', ')}]</span>}
                      {s.impact && <span className={`ml-2 px-1 rounded text-xs ${s.impact === 'high' ? 'bg-red-100 text-red-600' : 'bg-gray-100 text-gray-600'}`}>{s.impact}</span>}
                    </>
                  )}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* 优先处理用例 */}
        {reviewResult.priority_recommendations?.length > 0 && (
          <div className="mb-4">
            <h3 className="text-sm font-semibold mb-2">优先处理用例</h3>
            <div className="space-y-1 max-h-40 overflow-y-auto">
              {reviewResult.priority_recommendations.map((r, i) => (
                <div key={i} className="text-xs p-2 bg-red-50 rounded flex gap-2">
                  {typeof r === 'string' ? <span>{r}</span> : (
                    <>
                      <span className="font-mono font-bold text-red-700">{r.case_id}</span>
                      <span className="text-gray-600">{r.reason}</span>
                      {r.current_priority && r.suggested_priority && <span className="text-orange-600 text-xs">{r.current_priority} → {r.suggested_priority}</span>}
                    </>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* 疑似重复 */}
        {reviewResult.duplicate_groups?.length > 0 && (
          <div className="mb-4">
            <h3 className="text-sm font-semibold mb-2">疑似重复用例</h3>
            <div className="space-y-1 max-h-32 overflow-y-auto">
              {reviewResult.duplicate_groups.map((g, i) => (
                <div key={i} className="text-xs p-2 bg-orange-50 rounded">
                  <span className="font-mono">{g.signature}</span> x{g.count}: {g.case_ids.join(', ')}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* AI 总评 */}
        {reviewResult.overall_assessment && (
          <div className="mb-4 p-3 bg-blue-50 border border-blue-200 rounded">
            <h3 className="text-sm font-semibold mb-1 text-blue-800">AI 总评</h3>
            <p className="text-sm text-blue-700">{reviewResult.overall_assessment}</p>
          </div>
        )}

        {/* AI 逐条问题 + 自愈 */}
        {reviewResult.ai_case_issues?.length > 0 && (
          <div className="mb-4">
            <h3 className="text-sm font-semibold mb-2 text-red-700">问题用例（AI 诊断）</h3>
            <div className="space-y-2 max-h-60 overflow-y-auto">
              {reviewResult.ai_case_issues.map((c, i) => (
                <div key={i} className={`text-xs p-2 rounded border ${healingCases[c.case_id] === 'done' ? 'bg-green-50 border-green-200' : 'bg-red-50 border-red-100'}`}>
                  <div className="flex items-center justify-between">
                    <span className="font-mono font-bold text-red-700">{c.case_id}</span>
                    <div className="flex items-center gap-2">
                      {healingCases[c.case_id] === 'done' ? (
                        <span className="text-green-600 font-medium">✓ 已修复</span>
                      ) : healingCases[c.case_id] === 'loading' ? (
                        <span className="text-blue-600 animate-pulse">生成中...</span>
                      ) : healingCases[c.case_id] === 'preview' ? (
                        <button
                          onClick={() => onShowHealDialog(healPreviews[c.case_id])}
                          className="px-2 py-0.5 bg-blue-600 text-white rounded hover:bg-blue-700 text-xs"
                        >查看建议</button>
                      ) : healingCases[c.case_id] === 'error' ? (
                        <button onClick={() => onHealRetry(c)} className="text-orange-600 hover:underline text-xs">重试</button>
                      ) : (
                        <button
                          onClick={() => onHealPreview(c)}
                          className="px-2 py-0.5 bg-green-600 text-white rounded hover:bg-green-700 text-xs"
                        >AI 自愈</button>
                      )}
                      <button
                        onClick={() => onLocateCase(c.case_id)}
                        className="text-blue-600 hover:underline text-xs"
                      >定位</button>
                    </div>
                  </div>
                  {c.issues?.map((issue, j) => <div key={j} className="text-gray-600 mt-1">- {typeof issue === 'string' ? issue : JSON.stringify(issue)}</div>)}
                  {c.fix_suggestion && <div className="mt-1 text-green-700 font-medium">修复: {typeof c.fix_suggestion === 'string' ? c.fix_suggestion : JSON.stringify(c.fix_suggestion)}</div>}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* 覆盖缺口 */}
        {reviewResult.coverage_gaps?.length > 0 && (
          <div className="mb-4">
            <h3 className="text-sm font-semibold mb-2">覆盖缺口</h3>
            <ul className="space-y-1">
              {reviewResult.coverage_gaps.map((g, i) => (
                <li key={i} className="text-sm text-gray-700 bg-amber-50 p-2 rounded">{g}</li>
              ))}
            </ul>
          </div>
        )}

        {/* 漏测场景 */}
        {reviewResult.missing_scenarios?.length > 0 && (
          <div className="mb-4">
            <h3 className="text-sm font-semibold mb-2 text-purple-700">建议补充场景</h3>
            <div className="space-y-1 max-h-40 overflow-y-auto">
              {reviewResult.missing_scenarios.map((s, i) => (
                <div key={i} className="text-xs p-2 bg-purple-50 rounded">
                  {typeof s === 'string' ? s : (
                    <>
                      <span className="font-medium">{s.scenario}</span>
                      {s.api && <span className="ml-2 text-gray-500">[{s.api}]</span>}
                      {s.priority && <span className={`ml-2 px-1 rounded ${s.priority === 'high' ? 'bg-red-100 text-red-600' : 'bg-gray-100 text-gray-600'}`}>{s.priority}</span>}
                      {s.reason && <div className="text-gray-500 mt-0.5">{s.reason}</div>}
                    </>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* 规则问题用例明细 */}
        {reviewResult.case_details?.some(c => c.issues?.length > 0) && (
          <details className="mb-4">
            <summary className="text-sm font-semibold cursor-pointer text-gray-700">
              规则检出问题用例 ({reviewResult.case_details.filter(c => c.issues?.length > 0).length} 条)
            </summary>
            <div className="mt-2 space-y-1 max-h-48 overflow-y-auto">
              {reviewResult.case_details.filter(c => c.issues?.length > 0).map((c, i) => (
                <div key={i} className="text-xs p-2 bg-gray-50 rounded flex items-start gap-2">
                  <span className={`px-1.5 py-0.5 rounded font-bold ${c.risk_level === 'high' ? 'bg-red-100 text-red-700' : c.risk_level === 'medium' ? 'bg-yellow-100 text-yellow-700' : 'bg-green-100 text-green-700'}`}>{c.score}</span>
                  <div className="flex-1">
                    <div className="flex items-center justify-between">
                      <span className="font-mono text-gray-500">{c.case_id}</span>
                      <button onClick={() => onLocateCase(c.case_id)} className="text-blue-600 hover:underline text-xs">定位</button>
                    </div>
                    <div className="text-gray-600">{c.issues.join(' | ')}</div>
                  </div>
                </div>
              ))}
            </div>
          </details>
        )}

        <div className="mt-4 flex justify-end">
          <button onClick={onClose} className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 text-sm">关闭</button>
        </div>
      </div>
    </div>
  )
}
