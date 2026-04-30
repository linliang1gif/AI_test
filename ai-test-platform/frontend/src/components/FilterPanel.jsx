import { useState } from 'react'
import { Filter, X, ChevronDown } from 'lucide-react'

export default function FilterPanel({ filters, onFilterChange, onReset }) {
  const [isExpanded, setIsExpanded] = useState(false)

  const handleChange = (key, value) => {
    onFilterChange({ ...filters, [key]: value })
  }

  const activeFilterCount = Object.values(filters).filter(v => v && v !== 'all').length

  return (
    <div className="bg-white rounded-md border border-slate-200">
      {/* 筛选头部 */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full px-4 sm:px-6 py-4 flex items-center justify-between hover:bg-slate-50 transition-colors"
      >
        <div className="flex items-center space-x-3">
          <Filter className="w-5 h-5 text-slate-600" />
          <span className="font-medium text-slate-900">高级筛选</span>
          {activeFilterCount > 0 && (
            <span className="px-2 py-0.5 bg-blue-100 text-blue-700 rounded-full text-xs font-medium">
              {activeFilterCount} 个筛选条件
            </span>
          )}
        </div>
        <ChevronDown 
          className={`w-5 h-5 text-slate-400 transition-transform ${isExpanded ? 'rotate-180' : ''}`}
        />
      </button>

      {/* 筛选内容 */}
      {isExpanded && (
        <div className="px-4 sm:px-6 py-4 border-t border-slate-200">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* 状态筛选 */}
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2">
                状态
              </label>
              <select
                value={filters.status || 'all'}
                onChange={(e) => handleChange('status', e.target.value)}
                className="w-full px-3 py-2 border border-slate-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="all">全部</option>
                <option value="passed">通过</option>
                <option value="failed">失败</option>
                <option value="pending">待执行</option>
              </select>
            </div>

            {/* 优先级筛选 */}
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2">
                优先级
              </label>
              <select
                value={filters.priority || 'all'}
                onChange={(e) => handleChange('priority', e.target.value)}
                className="w-full px-3 py-2 border border-slate-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="all">全部</option>
                <option value="high">高</option>
                <option value="medium">中</option>
                <option value="low">低</option>
              </select>
            </div>

            {/* 来源筛选 */}
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2">
                来源
              </label>
              <select
                value={filters.source || 'all'}
                onChange={(e) => handleChange('source', e.target.value)}
                className="w-full px-3 py-2 border border-slate-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="all">全部</option>
                <option value="ai_generated">AI生成</option>
                <option value="manual">人工</option>
                <option value="knowledge_base">知识库</option>
              </select>
            </div>

            {/* 模块筛选 */}
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2">
                模块
              </label>
              <input
                type="text"
                value={filters.module || ''}
                onChange={(e) => handleChange('module', e.target.value)}
                placeholder="输入模块名称"
                className="w-full px-3 py-2 border border-slate-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>

          {/* 操作按钮 */}
          <div className="flex items-center justify-end space-x-3 mt-4 pt-4 border-t border-slate-200">
            <button
              onClick={onReset}
              className="px-4 py-2 text-sm text-slate-600 hover:text-slate-900 flex items-center space-x-2"
            >
              <X className="w-4 h-4" />
              <span>重置筛选</span>
            </button>
            <button
              onClick={() => setIsExpanded(false)}
              className="px-4 py-2 bg-blue-600 text-white rounded-md text-sm hover:bg-blue-700"
            >
              应用筛选
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
