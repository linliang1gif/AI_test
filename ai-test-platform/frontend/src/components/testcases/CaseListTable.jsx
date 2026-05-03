/**
 * P2-9A.1: 用例列表表格 + 分页
 */

const PAGE_SIZE = 20

const SOURCE_LABEL_MAP = {
  ai_generated: 'AI生成',
  smart_generated: 'AI生成',
  swagger: 'Swagger导入',
  demo_swagger: 'Demo',
  demo_seed: 'Demo',
  manual: '人工',
  knowledge_base: '知识库',
}

const PRIORITY_MAP = {
  high: { cls: 'bg-red-100 text-red-700', label: '高' },
  medium: { cls: 'bg-yellow-100 text-yellow-700', label: '中' },
  low: { cls: 'bg-green-100 text-green-700', label: '低' },
}

const STATUS_MAP = {
  passed: { cls: 'bg-green-100 text-green-700', label: '通过' },
  failed: { cls: 'bg-red-100 text-red-700', label: '失败' },
  error: { cls: 'bg-red-100 text-red-700', label: '错误' },
  no_assertion: { cls: 'bg-yellow-100 text-yellow-700', label: '无断言' },
  pending: { cls: 'bg-gray-100 text-gray-700', label: '待运行' },
}

export default function CaseListTable({
  loading,
  sourceFilter,
  govFilteredCases,
  pagedCases,
  selectedIds,
  selectedTestCase,
  isExecuting,
  searchQuery,
  hasGovFilter,
  safePage,
  totalPages,
  onSelectAll,
  onSelectOne,
  onViewDetail,
  onExecuteTest,
  onGenerateScript,
  onManualTest,
  onSetCurrentPage,
}) {
  const sourceLabel = (src) => SOURCE_LABEL_MAP[src] || src || '-'

  return (
    <div className="p-6 overflow-x-auto">
      {loading ? (
        <div className="flex items-center justify-center py-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          <span className="ml-2 text-gray-500">加载中...</span>
        </div>
      ) : (
        <table className="w-full table-fixed min-w-[900px]">
          <thead>
            <tr className="border-b">
              <th className="py-3 px-4 text-gray-600 font-medium w-10">
                <input
                  type="checkbox"
                  checked={govFilteredCases.length > 0 && selectedIds.length === govFilteredCases.length}
                  onChange={onSelectAll}
                  className="w-4 h-4 text-blue-600 rounded focus:ring-2 focus:ring-blue-500"
                />
              </th>
              <th className="text-left py-3 px-4 text-gray-600 font-medium w-[30%]">用例名称</th>
              <th className="text-left py-3 px-4 text-gray-600 font-medium w-[14%]">模块</th>
              <th className="text-left py-3 px-4 text-gray-600 font-medium w-[8%]">风险</th>
              <th className="text-left py-3 px-4 text-gray-600 font-medium w-[8%]">{sourceFilter === 'api' ? '接口类型' : sourceFilter === 'functional' ? '优先级' : '类型'}</th>
              <th className="text-left py-3 px-4 text-gray-600 font-medium w-[8%]">来源</th>
              <th className="text-left py-3 px-4 text-gray-600 font-medium w-[10%]">状态</th>
              <th className="text-left py-3 px-4 text-gray-600 font-medium w-[18%]">操作</th>
            </tr>
          </thead>
          <tbody>
            {govFilteredCases.length === 0 ? (
              <tr>
                <td colSpan={10} className="py-8 text-center text-gray-500">
                  {searchQuery || hasGovFilter ? '未找到匹配的测试用例' : '暂无测试用例，请导入需求文档生成'}
                </td>
              </tr>
            ) : pagedCases.map((tc, index) => {
              const p = PRIORITY_MAP[tc.priority] || { cls: 'bg-gray-100 text-gray-700', label: tc.priority || '-' }
              const s = STATUS_MAP[tc.status] || { cls: 'bg-gray-100 text-gray-700', label: tc.status || '-' }
              const uniqueKey = `${tc.id}-${index}`

              return (
                <tr key={uniqueKey} className="border-b hover:bg-gray-50 transition-colors">
                  <td className="py-4 px-4">
                    <input
                      type="checkbox"
                      checked={selectedIds.includes(tc.id)}
                      onChange={() => onSelectOne(tc.id)}
                      className="w-4 h-4 text-blue-600 rounded focus:ring-2 focus:ring-blue-500"
                    />
                  </td>
                  <td className="py-4 px-4 font-medium truncate" title={tc.title}>
                    {tc.title?.replace(/^(测试用例标题|测试点|用例标题|标题)[:：]\s*/, '') || tc.title}
                  </td>
                  <td className="py-4 px-4 text-gray-600">{tc.module_name || tc.module || '-'}</td>
                  <td className="py-4 px-4">
                    {tc.risk_level ? (
                      <span className={`px-2 py-1 rounded text-xs font-medium ${
                        tc.risk_level === 'P0' ? 'bg-red-100 text-red-700' :
                        tc.risk_level === 'P1' ? 'bg-orange-100 text-orange-700' :
                        'bg-gray-100 text-gray-600'
                      }`}>{tc.risk_level}</span>
                    ) : <span className="text-gray-300 text-xs">-</span>}
                    {tc.destructive && <span className="ml-1 px-1 bg-red-50 text-red-600 text-xs rounded border border-red-200" title="破坏性接口">破坏</span>}
                  </td>
                  <td className="py-4 px-4">
                    {sourceFilter === 'functional' || (!['swagger','demo_swagger','demo_seed'].includes(tc.source) && sourceFilter === 'all') ? (
                      <span className={`px-2 py-1 rounded text-xs font-medium ${p.cls}`}>{p.label}</span>
                    ) : (
                      <span className="px-2 py-1 bg-gray-100 text-gray-600 rounded text-xs">{tc.api_pattern || '-'}</span>
                    )}
                  </td>
                  <td className="py-4 px-4">
                    <span className="px-2 py-1 bg-blue-100 text-blue-700 rounded text-xs">
                      {sourceLabel(tc.source)}
                    </span>
                    {tc.case_type === 'web_ui' && (
                      <span className="ml-1 px-1.5 py-0.5 bg-violet-100 text-violet-700 rounded text-xs font-medium">Web UI</span>
                    )}
                  </td>
                  <td className="py-4 px-4">
                    <span className={`px-2 py-1 rounded text-sm ${s.cls}`}>{s.label}</span>
                    {tc.failure_category && <div className="text-xs text-red-400 mt-0.5">{tc.failure_category}</div>}
                  </td>
                  <td className="py-4 px-4">
                    <div className="flex space-x-2">
                      <button
                        onClick={() => onViewDetail(tc)}
                        className="px-3 py-1 bg-blue-50 text-blue-600 rounded hover:bg-blue-100 text-sm"
                      >
                        查看详情
                      </button>
                      {tc.case_type === 'web_ui' ? (
                        <button
                          onClick={() => onExecuteTest(tc)}
                          disabled={isExecuting}
                          className="px-3 py-1 bg-violet-50 text-violet-600 rounded hover:bg-violet-100 text-sm flex items-center space-x-1 disabled:opacity-50"
                          title="Playwright 执行 Web UI 用例"
                        >
                          <span>🌐</span>
                          <span>{isExecuting && selectedTestCase?.id === tc.id ? '执行中...' : '执行'}</span>
                        </button>
                      ) : ['swagger', 'demo_swagger', 'demo_seed'].includes(tc.source) ? (
                        <>
                          <button
                            onClick={() => onGenerateScript(tc)}
                            className="px-3 py-1 bg-purple-50 text-purple-600 rounded hover:bg-purple-100 text-sm flex items-center space-x-1"
                            title="导出可运行的 pytest 脚本，支持环境变量配置"
                          >
                            <span></span>
                            <span>导出脚本</span>
                          </button>
                          <button
                            onClick={() => onExecuteTest(tc)}
                            className="px-3 py-1 bg-green-50 text-green-600 rounded hover:bg-green-100 text-sm flex items-center space-x-1"
                            title="自动化执行"
                          >
                            <span></span>
                            <span>自动执行</span>
                          </button>
                        </>
                      ) : (
                        <button
                          onClick={() => onManualTest(tc)}
                          className="px-3 py-1 bg-indigo-50 text-indigo-600 rounded hover:bg-indigo-100 text-sm flex items-center space-x-1"
                          title="手动功能测试"
                        >
                          <span></span>
                          <span>手动测试</span>
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      )}
      {/* 分页 */}
      {govFilteredCases.length > PAGE_SIZE && (
        <div className="flex items-center justify-between px-4 py-3 border-t">
          <span className="text-sm text-gray-500">共 {govFilteredCases.length} 条，第 {safePage}/{totalPages} 页</span>
          <div className="flex items-center gap-1">
            <button onClick={() => onSetCurrentPage(1)} disabled={safePage <= 1}
              className="px-2 py-1 text-xs border rounded hover:bg-gray-50 disabled:opacity-40">首页</button>
            <button onClick={() => onSetCurrentPage(Math.max(1, safePage - 1))} disabled={safePage <= 1}
              className="px-2 py-1 text-xs border rounded hover:bg-gray-50 disabled:opacity-40">上一页</button>
            {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
              let page
              if (totalPages <= 5) { page = i + 1 }
              else if (safePage <= 3) { page = i + 1 }
              else if (safePage >= totalPages - 2) { page = totalPages - 4 + i }
              else { page = safePage - 2 + i }
              return (
                <button key={page} onClick={() => onSetCurrentPage(page)}
                  className={`px-2.5 py-1 text-xs border rounded ${page === safePage ? 'bg-blue-600 text-white border-blue-600' : 'hover:bg-gray-50'}`}>{page}</button>
              )
            })}
            <button onClick={() => onSetCurrentPage(Math.min(totalPages, safePage + 1))} disabled={safePage >= totalPages}
              className="px-2 py-1 text-xs border rounded hover:bg-gray-50 disabled:opacity-40">下一页</button>
            <button onClick={() => onSetCurrentPage(totalPages)} disabled={safePage >= totalPages}
              className="px-2 py-1 text-xs border rounded hover:bg-gray-50 disabled:opacity-40">末页</button>
          </div>
        </div>
      )}
    </div>
  )
}
