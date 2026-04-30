/**
 * 商用级详情卡片组件
 * 用于展示详情页的各个信息区块
 */
export default function DetailCard({ 
  title, 
  extra = null, 
  children, 
  className = '' 
}) {
  return (
    <div className={`bg-white rounded-md border border-slate-200 ${className}`}>
      {title && (
        <div className="px-4 sm:px-6 py-4 border-b border-slate-200 flex items-center justify-between">
          <h3 className="text-base font-semibold text-slate-900">{title}</h3>
          {extra && <div>{extra}</div>}
        </div>
      )}
      <div className="p-4 sm:p-6">
        {children}
      </div>
    </div>
  )
}
