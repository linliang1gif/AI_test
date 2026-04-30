/**
 * 商用级状态标签组件
 * 统一的状态展示样式
 */
export default function StatusBadge({ 
  status, 
  type = 'default',
  size = 'md' 
}) {
  const typeStyles = {
    success: 'bg-green-50 text-green-700 border-green-200',
    warning: 'bg-yellow-50 text-yellow-700 border-yellow-200',
    error: 'bg-red-50 text-red-700 border-red-200',
    info: 'bg-blue-50 text-blue-700 border-blue-200',
    default: 'bg-slate-50 text-slate-700 border-slate-200'
  }

  const sizeStyles = {
    sm: 'px-2 py-0.5 text-xs',
    md: 'px-2.5 py-1 text-sm',
    lg: 'px-3 py-1.5 text-base'
  }

  return (
    <span className={`inline-flex items-center rounded-md border font-medium ${typeStyles[type]} ${sizeStyles[size]}`}>
      {status}
    </span>
  )
}
