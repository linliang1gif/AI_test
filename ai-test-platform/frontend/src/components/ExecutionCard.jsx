import { Play, Clock, CheckCircle, XCircle, AlertCircle, BarChart3, Eye, RefreshCw } from 'lucide-react'
import { useState } from 'react'

export default function ExecutionCard({ execution, isSelected, onSelect, onView, onRerun, onViewReport }) {
  const [showMenu, setShowMenu] = useState(false)

  const statusColors = {
    running: 'bg-orange-100 text-orange-700 border-orange-300',
    completed: 'bg-green-100 text-green-700 border-green-300',
    passed: 'bg-green-100 text-green-700 border-green-300',
    failed: 'bg-red-100 text-red-700 border-red-300',
    paused: 'bg-yellow-100 text-yellow-700 border-yellow-300',
    pending: 'bg-gray-100 text-gray-700 border-gray-300'
  }

  const envColors = {
    production: 'bg-red-100 text-red-700 border-red-300',
    staging: 'bg-purple-100 text-purple-700 border-purple-300',
    development: 'bg-blue-100 text-blue-700 border-blue-300'
  }

  const statusColor = statusColors[execution.status] || statusColors.pending
  const envColor = envColors[execution.environment] || envColors.development

  const getStatusIcon = () => {
    switch (execution.status) {
      case 'running':
        return <Clock className="w-5 h-5 text-orange-500 animate-spin" />
      case 'completed':
      case 'passed':
        return <CheckCircle className="w-5 h-5 text-green-500" />
      case 'failed':
        return <XCircle className="w-5 h-5 text-red-500" />
      case 'paused':
        return <AlertCircle className="w-5 h-5 text-yellow-500" />
      default:
        return <Clock className="w-5 h-5 text-gray-500" />
    }
  }

  const getPassRate = () => {
    if (!execution.totalTests || execution.totalTests === 0) return 0
    return ((execution.passed / execution.totalTests) * 100).toFixed(1)
  }

  const getPassRateColor = () => {
    const rate = getPassRate()
    if (rate >= 90) return 'text-green-600'
    if (rate >= 70) return 'text-yellow-600'
    return 'text-red-600'
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
                  onSelect(execution.id)
                }}
                className="mt-1 w-4 h-4 text-blue-600 rounded focus:ring-2 focus:ring-blue-500"
              />
            )}
            <div className="flex-1 min-w-0">
              <div className="flex items-center space-x-2 mb-2">
                {getStatusIcon()}
                <span className={`px-2 py-1 rounded text-xs font-medium border ${statusColor}`}>
                  {execution.status === 'running' ? '执行中' :
                   execution.status === 'completed' || execution.status === 'passed' ? '已完成' :
                   execution.status === 'failed' ? '失败' :
                   execution.status === 'paused' ? '已暂停' : '待执行'}
                </span>
                <span className={`px-2 py-1 rounded text-xs font-medium border ${envColor}`}>
                  {execution.environment === 'production' ? '生产' :
                   execution.environment === 'staging' ? '测试' : '开发'}
                </span>
              </div>
              <h3 
                onClick={() => onView(execution)}
                className="text-lg font-semibold text-slate-900 mb-1 hover:text-blue-600 cursor-pointer line-clamp-1"
              >
                {execution.name}
              </h3>
              <div className="flex flex-wrap gap-2 text-xs text-slate-500">
                <span>ID: {execution.id}</span>
                <span>•</span>
                <span>{execution.startTime}</span>
                {execution.duration && (
                  <>
                    <span>•</span>
                    <span>耗时: {execution.duration}</span>
                  </>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* 进度条 */}
        {execution.status === 'running' && execution.progress !== undefined && (
          <div className="mb-4">
            <div className="flex items-center justify-between text-xs text-slate-600 mb-1">
              <span>执行进度</span>
              <span>{execution.progress}%</span>
            </div>
            <div className="w-full bg-slate-200 rounded-full h-2">
              <div 
                className="bg-blue-600 h-2 rounded-full transition-all"
                style={{ width: `${execution.progress}%` }}
              />
            </div>
          </div>
        )}

        {/* 测试统计 */}
        <div className="grid grid-cols-4 gap-2 mb-4">
          <div className="text-center bg-slate-50 rounded-md p-2">
            <div className="text-lg font-bold text-slate-900">{execution.totalTests || 0}</div>
            <div className="text-xs text-slate-600">总计</div>
          </div>
          <div className="text-center bg-green-50 rounded-md p-2">
            <div className="text-lg font-bold text-green-600">{execution.passed || 0}</div>
            <div className="text-xs text-green-600">通过</div>
          </div>
          <div className="text-center bg-red-50 rounded-md p-2">
            <div className="text-lg font-bold text-red-600">{execution.failed || 0}</div>
            <div className="text-xs text-red-600">失败</div>
          </div>
          <div className="text-center bg-yellow-50 rounded-md p-2">
            <div className="text-lg font-bold text-yellow-600">{execution.pending || 0}</div>
            <div className="text-xs text-yellow-600">待运行</div>
          </div>
        </div>

        {/* 通过率 */}
        {execution.totalTests > 0 && (
          <div className="mb-4">
            <div className="flex items-center justify-between text-xs text-slate-600 mb-1">
              <span>通过率</span>
              <span className={`font-bold ${getPassRateColor()}`}>{getPassRate()}%</span>
            </div>
            <div className="w-full bg-slate-200 rounded-full h-2">
              <div 
                className={`h-2 rounded-full transition-all ${
                  getPassRate() >= 90 ? 'bg-green-500' :
                  getPassRate() >= 70 ? 'bg-yellow-500' : 'bg-red-500'
                }`}
                style={{ width: `${getPassRate()}%` }}
              />
            </div>
          </div>
        )}

        {/* 并发任务状态 */}
        {execution.tasks && execution.tasks.length > 0 && (
          <div className="mb-4 p-3 bg-slate-50 rounded-md">
            <div className="text-xs text-slate-600 mb-2">并发任务 ({execution.tasks.length})</div>
            <div className="flex items-center gap-1">
              {execution.tasks.slice(0, 10).map((task, idx) => (
                <div
                  key={idx}
                  className={`w-2 h-6 rounded-sm ${
                    task.status === 'success' ? 'bg-green-500' :
                    task.status === 'failed' ? 'bg-red-500' :
                    'bg-orange-500'
                  }`}
                  title={`${task.name}: ${task.status}`}
                />
              ))}
              {execution.tasks.length > 10 && (
                <span className="text-xs text-slate-500 ml-1">+{execution.tasks.length - 10}</span>
              )}
            </div>
          </div>
        )}

        {/* 操作按钮 */}
        <div className="flex flex-wrap gap-2">
          <button
            onClick={() => onView(execution)}
            className="flex-1 px-3 py-2 bg-blue-50 text-blue-600 rounded-md hover:bg-blue-100 text-sm flex items-center justify-center space-x-1 transition-colors"
          >
            <Eye className="w-4 h-4" />
            <span>查看详情</span>
          </button>
          {execution.status !== 'running' && (
            <button
              onClick={() => onRerun(execution)}
              className="px-3 py-2 bg-green-50 text-green-600 rounded-md hover:bg-green-100 text-sm flex items-center space-x-1 transition-colors"
            >
              <RefreshCw className="w-4 h-4" />
              <span>重新运行</span>
            </button>
          )}
          {(execution.status === 'completed' || execution.status === 'passed' || execution.status === 'failed') && (
            <button
              onClick={() => onViewReport(execution)}
              className="px-3 py-2 bg-purple-50 text-purple-600 rounded-md hover:bg-purple-100 text-sm flex items-center space-x-1 transition-colors"
            >
              <BarChart3 className="w-4 h-4" />
              <span>报告</span>
            </button>
          )}
        </div>
      </div>
    </div>
  )
}
