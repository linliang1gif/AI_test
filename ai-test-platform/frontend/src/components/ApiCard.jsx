import { Play, Copy, Database, MoreVertical, Eye, Code } from 'lucide-react'
import { useState } from 'react'

export default function ApiCard({ api, onView, onExecute, onGenerateData, onCopy, isSelected, onSelect }) {
  const [showMenu, setShowMenu] = useState(false)

  const methodColors = {
    GET: 'bg-green-100 text-green-700 border-green-300',
    POST: 'bg-blue-100 text-blue-700 border-blue-300',
    PUT: 'bg-yellow-100 text-yellow-700 border-yellow-300',
    DELETE: 'bg-red-100 text-red-700 border-red-300',
    PATCH: 'bg-purple-100 text-purple-700 border-purple-300'
  }

  const methodColor = methodColors[api.method] || methodColors.GET

  return (
    <div className={`bg-white rounded-md border transition-all hover:shadow-md ${
      isSelected ? 'border-blue-500 ring-2 ring-blue-100' : 'border-slate-200'
    }`}>
      <div className="p-4 sm:p-6">
        {/* 头部 */}
        <div className="flex items-start justify-between mb-3">
          <div className="flex items-start space-x-3 flex-1 min-w-0">
            {onSelect && (
              <input
                type="checkbox"
                checked={isSelected}
                onChange={(e) => {
                  e.stopPropagation()
                  onSelect(api.id)
                }}
                className="mt-1 w-4 h-4 text-blue-600 rounded focus:ring-2 focus:ring-blue-500"
              />
            )}
            <div className="flex-1 min-w-0">
              <div className="flex items-center space-x-2 mb-2">
                <span className={`px-3 py-1 rounded-md text-sm font-medium border ${methodColor}`}>
                  {api.method}
                </span>
                <code className="text-sm text-slate-700 font-mono truncate">
                  {api.path}
                </code>
              </div>
              <h3 className="text-base font-semibold text-slate-900 mb-1 line-clamp-2">
                {api.summary || api.name}
              </h3>
              {api.description && (
                <p className="text-sm text-slate-600 line-clamp-2">{api.description}</p>
              )}
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
                      onCopy(api)
                    }}
                    className="w-full px-4 py-2 text-left text-sm text-slate-700 hover:bg-slate-50 flex items-center space-x-2"
                  >
                    <Copy className="w-4 h-4" />
                    <span>复制信息</span>
                  </button>
                </div>
              </>
            )}
          </div>
        </div>

        {/* 标签 */}
        {api.tags && api.tags.length > 0 && (
          <div className="flex flex-wrap gap-2 mb-4">
            {api.tags.map((tag, i) => (
              <span key={i} className="px-2 py-1 bg-slate-100 text-slate-600 rounded text-xs">
                {tag}
              </span>
            ))}
          </div>
        )}

        {/* 操作按钮 */}
        <div className="flex flex-wrap gap-2">
          <button
            onClick={() => onView(api)}
            className="px-3 py-1.5 bg-blue-50 text-blue-600 rounded-md hover:bg-blue-100 text-sm flex items-center space-x-1 transition-colors"
          >
            <Eye className="w-4 h-4" />
            <span>查看</span>
          </button>
          <button
            onClick={() => onExecute(api)}
            className="px-3 py-1.5 bg-green-50 text-green-600 rounded-md hover:bg-green-100 text-sm flex items-center space-x-1 transition-colors"
          >
            <Play className="w-4 h-4" />
            <span>测试</span>
          </button>
          <button
            onClick={() => onGenerateData(api)}
            className="px-3 py-1.5 bg-purple-50 text-purple-600 rounded-md hover:bg-purple-100 text-sm flex items-center space-x-1 transition-colors"
          >
            <Database className="w-4 h-4" />
            <span>数据</span>
          </button>
        </div>
      </div>
    </div>
  )
}
