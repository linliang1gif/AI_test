/**
 * P2-9A.1: 性能测试配置弹窗 + 结果弹窗
 */
export function PerfConfigDialog({
  show,
  perfConfig,
  perfLoading,
  selectedCount,
  onConfigChange,
  onStart,
  onClose,
}) {
  if (!show) return null

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center">
      <div className="bg-white rounded-xl shadow-2xl p-6 w-full max-w-md">
        <h2 className="text-lg font-bold text-slate-900 mb-4">API 性能测试配置</h2>
        <div className="space-y-3">
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">并发数 (1-50)</label>
            <input type="number" min={1} max={50} value={perfConfig.concurrency}
              onChange={e => onConfigChange({ concurrency: Number(e.target.value) })}
              className="w-full px-3 py-2 border rounded-lg text-sm" />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">持续时间 (秒, 1-300)</label>
            <input type="number" min={1} max={300} value={perfConfig.duration_seconds}
              onChange={e => onConfigChange({ duration_seconds: Number(e.target.value) })}
              className="w-full px-3 py-2 border rounded-lg text-sm" />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Ramp-up (秒)</label>
            <input type="number" min={0} value={perfConfig.ramp_up_seconds}
              onChange={e => onConfigChange({ ramp_up_seconds: Number(e.target.value) })}
              className="w-full px-3 py-2 border rounded-lg text-sm" />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">请求间隔 (ms)</label>
            <input type="number" min={0} value={perfConfig.think_time_ms}
              onChange={e => onConfigChange({ think_time_ms: Number(e.target.value) })}
              className="w-full px-3 py-2 border rounded-lg text-sm" />
          </div>
          <p className="text-xs text-slate-500">将对 {selectedCount > 0 ? selectedCount : '所有'} 个 API 用例执行性能测试</p>
        </div>
        <div className="mt-5 flex justify-end space-x-3">
          <button onClick={onClose} className="px-4 py-2 border border-gray-300 rounded-lg text-sm hover:bg-gray-50">取消</button>
          <button onClick={onStart} disabled={perfLoading}
            className="px-4 py-2 bg-orange-500 text-white rounded-lg hover:bg-orange-600 text-sm disabled:opacity-50">
            {perfLoading ? '执行中...' : '开始性能测试'}
          </button>
        </div>
      </div>
    </div>
  )
}

export function PerfResultDialog({ show, perfResult, onClose }) {
  if (!show || !perfResult) return null
  const ps = perfResult.performance_summary
  if (!ps) return null

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center">
      <div className="bg-white rounded-xl shadow-2xl p-6 w-full max-w-2xl max-h-[80vh] overflow-y-auto">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-lg font-bold text-slate-900">性能测试结果</h2>
          <span className={`px-3 py-1 rounded-full text-xs font-medium ${
            ps.threshold_passed ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
          }`}>{ps.threshold_passed ? 'PASSED' : 'FAILED'}</span>
        </div>
        <div className="space-y-4">
          <div className="grid grid-cols-3 gap-3">
            <div className="bg-blue-50 rounded-lg p-3 text-center">
              <div className="text-2xl font-bold text-blue-700">{ps.total_requests}</div>
              <div className="text-xs text-blue-600">总请求数</div>
            </div>
            <div className="bg-green-50 rounded-lg p-3 text-center">
              <div className="text-2xl font-bold text-green-700">{ps.qps}</div>
              <div className="text-xs text-green-600">QPS</div>
            </div>
            <div className="bg-orange-50 rounded-lg p-3 text-center">
              <div className="text-2xl font-bold text-orange-700">{(ps.error_rate * 100).toFixed(1)}%</div>
              <div className="text-xs text-orange-600">错误率</div>
            </div>
          </div>
          <div className="bg-slate-50 rounded-lg p-4">
            <h3 className="text-sm font-semibold text-slate-700 mb-2">响应时间</h3>
            <div className="grid grid-cols-2 gap-2 text-sm">
              <div className="flex justify-between"><span className="text-slate-500">平均</span><span className="font-medium">{ps.avg_response_time_ms} ms</span></div>
              <div className="flex justify-between"><span className="text-slate-500">最小</span><span className="font-medium">{ps.min_response_time_ms} ms</span></div>
              <div className="flex justify-between"><span className="text-slate-500">P50</span><span className="font-medium">{ps.p50_ms} ms</span></div>
              <div className="flex justify-between"><span className="text-slate-500">P95</span><span className="font-medium">{ps.p95_ms} ms</span></div>
              <div className="flex justify-between"><span className="text-slate-500">P99</span><span className="font-medium">{ps.p99_ms} ms</span></div>
              <div className="flex justify-between"><span className="text-slate-500">最大</span><span className="font-medium">{ps.max_response_time_ms} ms</span></div>
            </div>
          </div>
          <div className="grid grid-cols-2 gap-3 text-sm">
            <div className="flex justify-between"><span className="text-slate-500">成功</span><span className="text-green-600 font-medium">{ps.success_requests}</span></div>
            <div className="flex justify-between"><span className="text-slate-500">失败</span><span className="text-red-600 font-medium">{ps.failed_requests}</span></div>
            <div className="flex justify-between"><span className="text-slate-500">并发</span><span className="font-medium">{ps.concurrency}</span></div>
            <div className="flex justify-between"><span className="text-slate-500">持续</span><span className="font-medium">{ps.duration_seconds}s</span></div>
          </div>
          {ps.threshold_failures?.length > 0 && (
            <div className="bg-red-50 rounded-lg p-3">
              <h3 className="text-sm font-semibold text-red-700 mb-1">阈值未通过</h3>
              {ps.threshold_failures.map((f, i) => (
                <div key={i} className="text-xs text-red-600">{f.metric}: 实际 {f.actual} &gt; 期望 {f.expected}</div>
              ))}
            </div>
          )}
          {ps.failure_samples?.length > 0 && (
            <div className="bg-amber-50 rounded-lg p-3">
              <h3 className="text-sm font-semibold text-amber-700 mb-1">失败样本 (前{ps.failure_samples.length}个)</h3>
              {ps.failure_samples.slice(0, 5).map((s, i) => (
                <div key={i} className="text-xs text-amber-600">{s.method} {s.url} → {s.error} ({s.duration_ms}ms)</div>
              ))}
            </div>
          )}
        </div>
        <div className="mt-5 flex justify-end">
          <button onClick={onClose} className="px-4 py-2 bg-slate-600 text-white rounded-lg hover:bg-slate-700 text-sm">关闭</button>
        </div>
      </div>
    </div>
  )
}
