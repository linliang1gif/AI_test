import { ChevronRight, ArrowLeft } from 'lucide-react'
import { useNavigate } from 'react-router-dom'

/**
 * 商用级页面头部组件
 * 包含面包屑导航、标题、描述和操作按钮
 */
export default function PageHeader({ 
  breadcrumbs = [], 
  title, 
  description, 
  actions = [],
  meta = null,
  showBack = false,
  onBack = null 
}) {
  const navigate = useNavigate()
  return (
    <div className="bg-white border-b border-slate-200">
      <div className="max-w-[1400px] mx-auto px-4 sm:px-6 py-4">
        {/* 面包屑导航 */}
        <div className="flex items-center space-x-4 mb-3">
          {showBack && (
            <button
              onClick={onBack || (() => navigate(-1))}
              className="flex items-center space-x-1 text-sm text-slate-600 hover:text-slate-900 transition-colors"
            >
              <ArrowLeft className="w-4 h-4" />
              <span className="hidden sm:inline">返回</span>
            </button>
          )}
          {breadcrumbs.length > 0 && (
            <nav className="flex items-center space-x-2 text-sm overflow-x-auto">
              {breadcrumbs.map((crumb, index) => (
                <div key={index} className="flex items-center flex-shrink-0">
                  {index > 0 && <ChevronRight className="w-4 h-4 mx-2 text-slate-400" />}
                  {crumb.href ? (
                    <button 
                      onClick={() => navigate(crumb.href)}
                      className="text-slate-600 hover:text-slate-900 transition-colors"
                    >
                      {crumb.label}
                    </button>
                  ) : (
                    <span className="text-slate-900 font-medium">{crumb.label}</span>
                  )}
                </div>
              ))}
            </nav>
          )}
        </div>

        {/* 标题和操作区 */}
        <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
          <div className="flex-1 min-w-0">
            <h1 className="text-xl sm:text-2xl font-semibold text-slate-900 mb-1 truncate">{title}</h1>
            {description && (
              <p className="text-sm text-slate-600">{description}</p>
            )}
            {meta && (
              <div className="mt-2">{meta}</div>
            )}
          </div>

          {/* 操作按钮组 */}
          {actions.length > 0 && (
            <div className="flex items-center flex-wrap gap-2 sm:gap-3 sm:ml-6">
              {actions.map((action, index) => (
                <button
                  key={index}
                  onClick={action.onClick}
                  disabled={action.disabled}
                  className={`px-3 sm:px-4 py-2 rounded-md text-sm font-medium transition-colors flex items-center ${
                    action.variant === 'primary'
                      ? 'bg-slate-700 text-white hover:bg-slate-800 disabled:opacity-50'
                      : action.variant === 'danger'
                      ? 'bg-red-600 text-white hover:bg-red-700 disabled:opacity-50'
                      : 'bg-white border border-slate-300 text-slate-700 hover:bg-slate-50 disabled:opacity-50'
                  }`}
                >
                  {action.icon && <span className="mr-2">{action.icon}</span>}
                  <span className="hidden sm:inline">{action.label}</span>
                </button>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
