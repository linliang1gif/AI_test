/**
 * P2-9A.1: 按 case_type Tab 动态展示指标卡片
 */
export default function CaseMetricsPanel({ sourceFilter, tabMetrics, testCases, coverage, onRefreshCoverage }) {
  return (
    <>
      {/* 全部 Tab 指标 */}
      {sourceFilter === 'all' && testCases.length > 0 && (
        <div className="grid grid-cols-5 gap-3">
          <div className="p-3 bg-gray-50 rounded-lg border text-center">
            <div className="text-xl font-bold text-gray-800">{tabMetrics.all.total}</div>
            <div className="text-xs text-gray-500">总用例</div>
          </div>
          <div className="p-3 bg-blue-50 rounded-lg border text-center">
            <div className="text-xl font-bold text-blue-600">{tabMetrics.all.apiCount}</div>
            <div className="text-xs text-gray-500">接口用例</div>
          </div>
          <div className="p-3 bg-green-50 rounded-lg border text-center">
            <div className="text-xl font-bold text-green-600">{tabMetrics.all.funcCount}</div>
            <div className="text-xs text-gray-500">功能用例</div>
          </div>
          <div className="p-3 bg-violet-50 rounded-lg border text-center">
            <div className="text-xl font-bold text-violet-600">{tabMetrics.all.webUiCount}</div>
            <div className="text-xs text-gray-500">Web UI</div>
          </div>
          <div className="p-3 bg-red-50 rounded-lg border text-center">
            <div className="text-xl font-bold text-red-600">{tabMetrics.all.recentFailed}</div>
            <div className="text-xs text-gray-500">最近失败</div>
          </div>
        </div>
      )}

      {/* Web UI Tab 指标 */}
      {sourceFilter === 'web_ui' && (
        <div className="grid grid-cols-5 gap-3">
          <div className="p-3 bg-violet-50 rounded-lg border text-center">
            <div className="text-xl font-bold text-violet-700">{tabMetrics.web_ui.total}</div>
            <div className="text-xs text-gray-500">Web UI 用例</div>
          </div>
          <div className="p-3 bg-blue-50 rounded-lg border text-center">
            <div className="text-xl font-bold text-blue-600">{tabMetrics.web_ui.executed}</div>
            <div className="text-xs text-gray-500">已执行</div>
          </div>
          <div className="p-3 bg-green-50 rounded-lg border text-center">
            <div className="text-xl font-bold text-green-600">{tabMetrics.web_ui.passRate}%</div>
            <div className="text-xs text-gray-500">通过率</div>
          </div>
          <div className="p-3 bg-amber-50 rounded-lg border text-center">
            <div className="text-xl font-bold text-amber-600">{tabMetrics.web_ui.traceCount}</div>
            <div className="text-xs text-gray-500">Trace 数</div>
          </div>
          <div className="p-3 bg-purple-50 rounded-lg border text-center">
            <div className="text-xl font-bold text-purple-600">{tabMetrics.web_ui.visualCount}</div>
            <div className="text-xs text-gray-500">视觉断言</div>
          </div>
        </div>
      )}

      {/* 功能测试 Tab 指标 */}
      {sourceFilter === 'functional' && tabMetrics.functional.total > 0 && (
        <div className="grid grid-cols-4 gap-3">
          <div className="p-3 bg-green-50 rounded-lg border text-center">
            <div className="text-xl font-bold text-green-700">{tabMetrics.functional.total}</div>
            <div className="text-xs text-gray-500">功能用例</div>
          </div>
          <div className="p-3 bg-blue-50 rounded-lg border text-center">
            <div className="text-xl font-bold text-blue-600">{tabMetrics.functional.reviewed}</div>
            <div className="text-xs text-gray-500">已评审</div>
          </div>
          <div className="p-3 bg-red-50 rounded-lg border text-center">
            <div className="text-xl font-bold text-red-600">{tabMetrics.functional.highRisk}</div>
            <div className="text-xs text-gray-500">高风险 (P0)</div>
          </div>
          <div className="p-3 bg-amber-50 rounded-lg border text-center">
            <div className="text-xl font-bold text-amber-600">{tabMetrics.functional.needImprove}</div>
            <div className="text-xs text-gray-500">待完善</div>
          </div>
        </div>
      )}

      {/* API 覆盖率摘要 */}
      {coverage && coverage.total_apis > 0 && sourceFilter !== 'functional' && (
        <div className="flex items-center gap-4 px-4 py-3 bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg border border-blue-100">
          <div className="flex items-center gap-2">
            <div className="relative w-12 h-12">
              <svg viewBox="0 0 36 36" className="w-12 h-12 -rotate-90">
                <circle cx="18" cy="18" r="15.9" fill="none" stroke="#e5e7eb" strokeWidth="3" />
                <circle cx="18" cy="18" r="15.9" fill="none"
                  stroke={coverage.coverage_rate >= 80 ? '#22c55e' : coverage.coverage_rate >= 50 ? '#f59e0b' : '#ef4444'}
                  strokeWidth="3" strokeDasharray={`${coverage.coverage_rate} ${100 - coverage.coverage_rate}`} strokeLinecap="round" />
              </svg>
              <span className="absolute inset-0 flex items-center justify-center text-xs font-bold">{coverage.coverage_rate}%</span>
            </div>
          </div>
          <div className="flex-1 grid grid-cols-4 gap-3 text-center">
            <div>
              <div className="text-lg font-bold text-gray-800">{coverage.total_apis}</div>
              <div className="text-xs text-gray-500">API 总数</div>
            </div>
            <div>
              <div className="text-lg font-bold text-green-600">{coverage.covered_apis}</div>
              <div className="text-xs text-gray-500">已覆盖</div>
            </div>
            <div>
              <div className="text-lg font-bold text-blue-600">{coverage.l1_case_count || 0}</div>
              <div className="text-xs text-gray-500">L1 正向</div>
            </div>
            <div>
              <div className="text-lg font-bold text-orange-600">{coverage.l2_case_count || 0}</div>
              <div className="text-xs text-gray-500">L2 变异</div>
            </div>
          </div>
          {coverage.total_apis - coverage.covered_apis > 0 && (
            <div className="text-xs text-red-500 whitespace-nowrap">
              {coverage.total_apis - coverage.covered_apis} 个未覆盖
            </div>
          )}
          <button onClick={onRefreshCoverage} className="text-xs text-blue-500 hover:underline whitespace-nowrap">刷新</button>
        </div>
      )}
    </>
  )
}
