/**
 * 骨架屏组件 - 用于加载状态
 */

export function Skeleton({ className = '', variant = 'default' }) {
  const variants = {
    default: 'h-4 bg-slate-200',
    text: 'h-4 bg-slate-200',
    title: 'h-6 bg-slate-200',
    avatar: 'h-12 w-12 rounded-full bg-slate-200',
    button: 'h-10 w-24 bg-slate-200 rounded-md',
    card: 'h-32 bg-slate-200 rounded-md'
  }

  return (
    <div className={`animate-pulse ${variants[variant]} ${className}`} />
  )
}

export function SkeletonText({ lines = 3, className = '' }) {
  return (
    <div className={`space-y-3 ${className}`}>
      {Array.from({ length: lines }).map((_, i) => (
        <Skeleton 
          key={i} 
          className={i === lines - 1 ? 'w-3/4' : 'w-full'} 
        />
      ))}
    </div>
  )
}

export function SkeletonCard({ className = '' }) {
  return (
    <div className={`bg-white rounded-md border border-slate-200 p-6 ${className}`}>
      <Skeleton variant="title" className="w-1/3 mb-4" />
      <SkeletonText lines={3} />
    </div>
  )
}

export function SkeletonTable({ rows = 5, columns = 4 }) {
  return (
    <div className="bg-white rounded-md border border-slate-200">
      {/* 表头 */}
      <div className="border-b border-slate-200 p-4">
        <div className="grid gap-4" style={{ gridTemplateColumns: `repeat(${columns}, 1fr)` }}>
          {Array.from({ length: columns }).map((_, i) => (
            <Skeleton key={i} className="h-4 w-20" />
          ))}
        </div>
      </div>
      
      {/* 表格行 */}
      {Array.from({ length: rows }).map((_, rowIndex) => (
        <div key={rowIndex} className="border-b border-slate-200 p-4 last:border-b-0">
          <div className="grid gap-4" style={{ gridTemplateColumns: `repeat(${columns}, 1fr)` }}>
            {Array.from({ length: columns }).map((_, colIndex) => (
              <Skeleton key={colIndex} />
            ))}
          </div>
        </div>
      ))}
    </div>
  )
}

export function SkeletonDetailPage() {
  return (
    <div className="min-h-screen bg-slate-50">
      {/* 页面头部骨架 */}
      <div className="bg-white border-b border-slate-200">
        <div className="max-w-[1400px] mx-auto px-6 py-4">
          <Skeleton className="w-48 h-4 mb-3" />
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <Skeleton variant="title" className="w-64 mb-2" />
              <Skeleton className="w-96" />
            </div>
            <div className="flex space-x-3">
              <Skeleton variant="button" />
              <Skeleton variant="button" />
            </div>
          </div>
        </div>
      </div>

      {/* 内容区骨架 */}
      <div className="max-w-[1400px] mx-auto px-6 py-6 space-y-6">
        <SkeletonCard />
        <SkeletonCard />
        <div className="bg-white rounded-md border border-slate-200 p-6">
          <SkeletonText lines={8} />
        </div>
      </div>
    </div>
  )
}
