import { FileQuestion } from 'lucide-react'

/**
 * 空状态占位组件
 * 用于列表、表格等无数据时的展示
 */
export default function EmptyState({ 
  icon: Icon = FileQuestion,
  title = '暂无数据',
  description = '',
  action = null
}) {
  return (
    <div className="flex flex-col items-center justify-center py-12 px-4">
      <div className="w-16 h-16 rounded-full bg-slate-100 flex items-center justify-center mb-4">
        <Icon className="w-8 h-8 text-slate-400" />
      </div>
      <h3 className="text-base font-medium text-slate-900 mb-1">{title}</h3>
      {description && (
        <p className="text-sm text-slate-500 mb-4 text-center max-w-sm">{description}</p>
      )}
      {action && (
        <div className="mt-2">{action}</div>
      )}
    </div>
  )
}
