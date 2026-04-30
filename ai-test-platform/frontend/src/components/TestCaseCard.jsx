import { Play, Edit, Trash2, MoreVertical, Eye, Code, Database, FileText } from 'lucide-react'
import { useState } from 'react'
import StatusBadge from './StatusBadge'

export default function TestCaseCard({ testCase, onView, onExecute, onGenerateScript, onManualTest, onBindDataset, onDelete, isSelected, onSelect }) {
  const [showMenu, setShowMenu] = useState(false)

  const priorityMap = {
    high: { type: 'error', label: '高' },
    medium: { type: 'warning', label: '中' },
    low: { type: 'info', label: '低' }
  }

  const statusMap = {
    passed: { type: 'success', label: '通过' },
    failed: { type: 'error', label: '失败' },
    pending: { type: 'default', label: '待执行' }
  }

  const sourceMap = {
    ai_generated: 'AI生成',
    manual: '人工',
    knowledge_base: '知识库'
  }

  const priority = priorityMap[testCase.priority] || { type: 'default', label: testCase.priority }
  const status = statusMap[testCase.status] || { type: 'default', label: testCase.status }

  return (
    <div className={`bg-white rounded-md border transition-all hover:shadow-md ${
      isSelected ? 'border-blue-500 ring-2 ring-blue-100' : 'border-slate-200'
    }`}>
      <div className="p-4 sm:p-6">
        {/* 头部 */}
        <div className="flex items-start justify-between mb-3">
          <div className="flex items-start space-x-3 flex-1 min-w-0">
            <input
              type="checkbox"
              checked={isSelected}
              onChange={(e) => {
                e.stopPropagation()
                onSelect(testCase.id)
              }}
              className="mt-1 w-4 h-4 text-blue-600 rounded focus:ring-2 focus:ring-blue-500"
            />
            <div className="flex-1 min-w-0">
              <h3 className="text-base font-semibold text-slate-900 mb-2 line-clamp-2">
                {testCase.title?.replace(/^(测试用例标题|测试点|用例标题|标题)[:：]\s*/, '') || testCase.title}
              </h3>
              <div className="flex flex-wrap items-center gap-2">
                <StatusBadge status={status.label} type={status.type} />
                <StatusBadge status={priority.label} type={priority.type} />
                {testCase.source && (
                  <span className="px-2 py-1 bg-blue-50 text-blue-700 rounded text-xs">
                    {sourceMap[testCase.source] || testCase.source}
                  </span>
                )}
              </div>
            </div>
          </div>

          {/* 更多菜单 */}
          <div className="relative ml-2">
            <button
              onClick={(e) => {
                e.stopPropagation()
                setShowMenu(!showMenu)
              }}
              className="p-1 text-slate-400 hover:text-slate-600 rounded hover:bg-slate-100"
            >
              <MoreVertical className="w-5 h-5" />
            </button>

            {showMenu && (
              <>
                <div 
                  className="fixed inset-0 z-10" 
                  onClick={() => setShowMenu(false)}
                />
                <div className="absolute right-0 top-8 w-48 bg-white rounded-md shadow-lg border border-slate-200 py-1 z-20">
                  <button
                    onClick={() => {
                      setShowMenu(false)
                      onDelete(testCase)
                    }}
                    className="w-full px-4 py-2 text-left text-sm text-red-600 hover:bg-red-50 flex items-center space-x-2"
                  >
                    <Trash2 className="w-4 h-4" />
                    <span>删除</span>
                  </button>
                </div>
              </>
            )}
          </div>
        </div>

        {/* 元信息 */}
        <div className="flex flex-wrap items-center gap-x-4 gap-y-2 text-sm text-slate-600 mb-4">
          {testCase.module && (
            <span className="flex items-center">
              <FileText className="w-4 h-4 mr-1" />
              {testCase.module}
            </span>
          )}
          {testCase.lastRun && (
            <span>最后运行: {testCase.lastRun}</span>
          )}
          {testCase.dataset_id && (
            <span className="flex items-center text-green-600">
              <Database className="w-4 h-4 mr-1" />
              已绑定数据集
            </span>
          )}
        </div>

        {/* 操作按钮 */}
        <div className="flex flex-wrap gap-2">
          <button
            onClick={() => onView(testCase)}
            className="px-3 py-1.5 bg-blue-50 text-blue-600 rounded-md hover:bg-blue-100 text-sm flex items-center space-x-1 transition-colors"
          >
            <Eye className="w-4 h-4" />
            <span>查看</span>
          </button>
          <button
            onClick={() => onExecute(testCase)}
            className="px-3 py-1.5 bg-green-50 text-green-600 rounded-md hover:bg-green-100 text-sm flex items-center space-x-1 transition-colors"
          >
            <Play className="w-4 h-4" />
            <span>执行</span>
          </button>
          <button
            onClick={() => onGenerateScript(testCase)}
            className="px-3 py-1.5 bg-purple-50 text-purple-600 rounded-md hover:bg-purple-100 text-sm flex items-center space-x-1 transition-colors"
          >
            <Code className="w-4 h-4" />
            <span>脚本</span>
          </button>
          <button
            onClick={() => onBindDataset(testCase)}
            className="px-3 py-1.5 bg-orange-50 text-orange-600 rounded-md hover:bg-orange-100 text-sm flex items-center space-x-1 transition-colors"
          >
            <Database className="w-4 h-4" />
            <span>数据</span>
          </button>
        </div>
      </div>
    </div>
  )
}
