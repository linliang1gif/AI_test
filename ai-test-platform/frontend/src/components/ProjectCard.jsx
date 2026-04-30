import { Play, Settings, BarChart3, Users, Calendar, TrendingUp, AlertCircle } from 'lucide-react'
import { useState } from 'react'

export default function ProjectCard({ project, isSelected, onSelect, onView, onRun, onSettings }) {
  const [showMenu, setShowMenu] = useState(false)

  const envColors = {
    production: 'bg-red-100 text-red-700 border-red-300',
    staging: 'bg-purple-100 text-purple-700 border-purple-300',
    development: 'bg-blue-100 text-blue-700 border-blue-300'
  }

  const statusColors = {
    active: 'bg-green-100 text-green-700 border-green-300',
    inactive: 'bg-gray-100 text-gray-700 border-gray-300'
  }

  const envColor = envColors[project.environment] || envColors.development
  const statusColor = statusColors[project.status] || statusColors.inactive

  const getCoverageColor = (coverage) => {
    if (coverage >= 90) return 'text-green-600'
    if (coverage >= 70) return 'text-yellow-600'
    return 'text-red-600'
  }

  const getCoverageBarColor = (coverage) => {
    if (coverage >= 90) return 'bg-green-500'
    if (coverage >= 70) return 'bg-yellow-500'
    return 'bg-red-500'
  }

  const renderRecentRuns = (runs) => {
    if (!runs || runs.length === 0) return null
    return (
      <div className="flex items-center gap-1">
        {runs.map((status, idx) => (
          <div
            key={idx}
            className={`w-2 h-6 rounded-sm ${
              status === 'success' ? 'bg-green-500' : 'bg-red-500'
            }`}
            title={status === 'success' ? '成功' : '失败'}
          />
        ))}
      </div>
    )
  }

  return (
    <div className={`bg-white rounded-md border transition-all hover:shadow-md ${
      isSelected ? 'border-blue-500 ring-2 ring-blue-100' : 'border-slate-200'
    }`}>
      <div className="p-4 sm:p-6">
        {/* 头部 */}
        <div className="flex items-start justify-between mb-4">
          <div className="flex items-start space-x-3 flex-1 min-w-0">
            {onSelect && (
              <input
                type="checkbox"
                checked={isSelected}
                onChange={(e) => {
                  e.stopPropagation()
                  onSelect(project.id)
                }}
                className="mt-1 w-4 h-4 text-blue-600 rounded focus:ring-2 focus:ring-blue-500"
              />
            )}
            <div className="flex-1 min-w-0">
              <div className="flex items-center space-x-2 mb-2">
                <span className={`px-2 py-1 rounded text-xs font-medium border ${envColor}`}>
                  {project.environment === 'production' ? '生产' : 
                   project.environment === 'staging' ? '测试' : '开发'}
                </span>
                <span className={`px-2 py-1 rounded text-xs font-medium border ${statusColor}`}>
                  {project.status === 'active' ? '活跃' : '暂停'}
                </span>
              </div>
              <h3 
                onClick={() => onView(project)}
                className="text-lg font-semibold text-slate-900 mb-1 hover:text-blue-600 cursor-pointer line-clamp-1"
              >
                {project.name}
              </h3>
              {project.description && (
                <p className="text-sm text-slate-600 line-clamp-2 mb-2">{project.description}</p>
              )}
              <div className="flex flex-wrap gap-2 text-xs text-slate-500">
                {project.owner && (
                  <div className="flex items-center space-x-1">
                    <Users className="w-3 h-3" />
                    <span>{project.owner}</span>
                  </div>
                )}
                {project.createdAt && (
                  <div className="flex items-center space-x-1">
                    <Calendar className="w-3 h-3" />
                    <span>{project.createdAt}</span>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* 统计信息 */}
        <div className="grid grid-cols-2 gap-3 mb-4">
          <div className="bg-slate-50 rounded-md p-3">
            <div className="flex items-center justify-between mb-1">
              <span className="text-xs text-slate-600">测试用例</span>
              <BarChart3 className="w-4 h-4 text-slate-400" />
            </div>
            <div className="text-xl font-bold text-slate-900">{project.testsCount || 0}</div>
          </div>
          
          <div className="bg-slate-50 rounded-md p-3">
            <div className="flex items-center justify-between mb-1">
              <span className="text-xs text-slate-600">覆盖率</span>
              <TrendingUp className="w-4 h-4 text-slate-400" />
            </div>
            <div className={`text-xl font-bold ${getCoverageColor(project.coverage || 0)}`}>
              {(project.coverage || 0).toFixed(1)}%
            </div>
          </div>
        </div>

        {/* 覆盖率进度条 */}
        <div className="mb-4">
          <div className="flex items-center justify-between text-xs text-slate-600 mb-1">
            <span>测试覆盖率</span>
            <span>{(project.coverage || 0).toFixed(1)}%</span>
          </div>
          <div className="w-full bg-slate-200 rounded-full h-2">
            <div 
              className={`h-2 rounded-full transition-all ${getCoverageBarColor(project.coverage || 0)}`}
              style={{ width: `${project.coverage || 0}%` }}
            />
          </div>
        </div>

        {/* 最近执行记录 */}
        {project.recentRuns && project.recentRuns.length > 0 && (
          <div className="mb-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs text-slate-600">最近5次执行</span>
              {project.failedCount > 0 && (
                <div className="flex items-center space-x-1 text-xs text-red-600">
                  <AlertCircle className="w-3 h-3" />
                  <span>{project.failedCount} 次失败</span>
                </div>
              )}
            </div>
            {renderRecentRuns(project.recentRuns)}
          </div>
        )}

        {/* 最后运行时间 */}
        {project.lastRun && (
          <div className="text-xs text-slate-500 mb-4">
            最后运行: {project.lastRun}
          </div>
        )}

        {/* 操作按钮 */}
        <div className="flex flex-wrap gap-2">
          <button
            onClick={() => onView(project)}
            className="flex-1 px-3 py-2 bg-blue-50 text-blue-600 rounded-md hover:bg-blue-100 text-sm flex items-center justify-center space-x-1 transition-colors"
          >
            <BarChart3 className="w-4 h-4" />
            <span>查看详情</span>
          </button>
          <button
            onClick={() => onRun(project)}
            className="px-3 py-2 bg-green-50 text-green-600 rounded-md hover:bg-green-100 text-sm flex items-center space-x-1 transition-colors"
          >
            <Play className="w-4 h-4" />
            <span>运行</span>
          </button>
          <button
            onClick={() => onSettings(project)}
            className="px-3 py-2 bg-slate-50 text-slate-600 rounded-md hover:bg-slate-100 text-sm flex items-center space-x-1 transition-colors"
          >
            <Settings className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  )
}
