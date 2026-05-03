/**
 * P2-9A.1: 上下文感知操作栏
 * 根据选中用例的 case_type 动态展示操作按钮
 */
export default function CaseActionToolbar({
  selectedCaseAnalysis,
  isExecuting,
  perfLoading,
  reviewLoading,
  isDeleting,
  onBatchExecute,
  onWebUiBatchExecute,
  onShowPerfDialog,
  onAiReview,
  onExportExcel,
  onBatchDelete,
  onAddToSuite,
  onClearSelection,
}) {
  if (selectedCaseAnalysis.count === 0) return null

  const { hasApi, hasWebUi, hasFunctional, isMixed, count } = selectedCaseAnalysis

  return (
    <div className="flex items-center gap-2 px-4 py-2.5 bg-blue-50 rounded-lg border border-blue-200">
      <span className="text-sm text-blue-700 font-medium whitespace-nowrap">已选 {count} 条</span>
      <div className="h-4 w-px bg-blue-200" />
      {hasApi && !hasWebUi && !hasFunctional && (
        <button onClick={onBatchExecute} disabled={isExecuting}
          className="px-3 py-1.5 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 text-xs disabled:opacity-50">
          {isExecuting ? '执行中...' : '批量执行'}
        </button>
      )}
      {hasWebUi && !hasApi && !hasFunctional && (
        <button onClick={onWebUiBatchExecute} disabled={isExecuting}
          className="px-3 py-1.5 bg-violet-600 text-white rounded-lg hover:bg-violet-700 text-xs disabled:opacity-50">
          {isExecuting ? '执行中...' : 'Web UI 批量执行'}
        </button>
      )}
      {hasApi && !hasWebUi && !hasFunctional && (
        <button onClick={onShowPerfDialog} disabled={perfLoading}
          className="px-3 py-1.5 bg-orange-500 text-white rounded-lg hover:bg-orange-600 text-xs disabled:opacity-50">
          {perfLoading ? '测试中...' : '性能测试'}
        </button>
      )}
      {isMixed && (
        <span className="text-xs text-amber-600 bg-amber-50 px-2 py-1 rounded border border-amber-200">
          ⚠ 混合类型选择，仅可导出/删除/评审
        </span>
      )}
      <button onClick={onAiReview} disabled={reviewLoading}
        className="px-3 py-1.5 bg-gradient-to-r from-indigo-600 to-purple-600 text-white rounded-lg text-xs disabled:opacity-50">
        {reviewLoading ? '评审中...' : 'AI评审'}
      </button>
      <button onClick={onExportExcel}
        className="px-3 py-1.5 bg-green-600 text-white rounded-lg hover:bg-green-700 text-xs">导出</button>
      {onAddToSuite && (
        <button onClick={onAddToSuite}
          className="px-3 py-1.5 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 text-xs">加入测试集</button>
      )}
      <button onClick={onBatchDelete} disabled={isDeleting}
        className="px-3 py-1.5 bg-red-600 text-white rounded-lg hover:bg-red-700 text-xs disabled:opacity-50">
        {isDeleting ? '删除中...' : '删除'}
      </button>
      <button onClick={onClearSelection} className="ml-auto text-xs text-gray-500 hover:text-gray-700">清除选择</button>
    </div>
  )
}
