/**
 * 元数据信息展示组件
 * 用于展示创建人、修改时间等业务字段
 */
export default function MetaInfo({ items = [] }) {
  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
      {items.map((item, index) => (
        <div key={index} className="space-y-1">
          <div className="text-xs text-slate-500 font-medium">{item.label}</div>
          <div className="text-sm text-slate-900">{item.value || '-'}</div>
        </div>
      ))}
    </div>
  )
}
