import { useEffect, useMemo, useRef, useState } from 'react'
import { visualAPI, VISUAL_DANGER } from '../services/api'
import DangerConfirmDialog from '../components/common/DangerConfirmDialog'

const VISUAL_BASE = '/visual'   // 静态文件挂载点（backend/app.py:70）

function StatCard({ title, value, sub, color = 'slate' }) {
  const colors = {
    slate: 'bg-slate-50 text-slate-700',
    green: 'bg-green-50 text-green-700',
    red: 'bg-red-50 text-red-700',
    amber: 'bg-amber-50 text-amber-700',
    blue: 'bg-blue-50 text-blue-700',
    violet: 'bg-violet-50 text-violet-700',
  }
  return (
    <div className={`rounded-xl p-4 ${colors[color] || colors.slate}`}>
      <div className="text-2xl font-bold">{value ?? '-'}</div>
      <div className="text-xs mt-1 opacity-75">{title}</div>
      {sub && <div className="text-xs mt-0.5 opacity-60">{sub}</div>}
    </div>
  )
}

function Toast({ msg, type = 'info', onClose }) {
  if (!msg) return null
  const c = type === 'error' ? 'bg-red-600' : type === 'success' ? 'bg-green-600' : 'bg-slate-700'
  return (
    <div className={`fixed top-4 right-4 z-50 ${c} text-white px-4 py-2 rounded-md shadow-lg max-w-md`}>
      <div className="flex items-center justify-between gap-3">
        <span className="text-sm">{msg}</span>
        <button onClick={onClose} className="text-white/80 hover:text-white">✕</button>
      </div>
    </div>
  )
}

function fmtBytes(n) {
  if (!n) return '-'
  if (n < 1024) return `${n}B`
  if (n < 1024 * 1024) return `${(n / 1024).toFixed(1)}KB`
  return `${(n / 1024 / 1024).toFixed(2)}MB`
}

// ─────────────────────── Phase 8: mask 画框组件 ───────────────────────
//
// 设计：用 SVG 叠在基线图上。
//   - 自动同步图像 naturalSize（截图原始像素）↔ displaySize（DOM 渲染尺寸）
//   - rect mask 用半透明红色矩形显示
//   - selector mask 若已有 bbox 用半透明紫色（只读）
//   - editable=true 时支持拖拽画新矩形 + 点击删除已有 rect
//   - 拖拽出的矩形坐标会换算回原始像素坐标后传出
function MaskCanvas({ src, masks, editable, onAddRect, onRemove }) {
  const containerRef = useRef(null)
  const imgRef = useRef(null)
  const [imgSize, setImgSize] = useState({ natural: null, display: null })
  const [drag, setDrag] = useState(null)   // {x0,y0,x1,y1} display 坐标

  const measure = () => {
    const img = imgRef.current
    if (!img || !img.naturalWidth) return
    setImgSize({
      natural: { w: img.naturalWidth, h: img.naturalHeight },
      display: { w: img.clientWidth, h: img.clientHeight },
    })
  }
  useEffect(() => {
    const onResize = () => measure()
    window.addEventListener('resize', onResize)
    return () => window.removeEventListener('resize', onResize)
  }, [])

  // 比例：display → natural
  const scaleX = imgSize.natural && imgSize.display
    ? imgSize.natural.w / imgSize.display.w : 1
  const scaleY = imgSize.natural && imgSize.display
    ? imgSize.natural.h / imgSize.display.h : 1

  // 把鼠标事件转成相对图片左上角的 display 坐标
  const toDisplay = (e) => {
    const r = imgRef.current.getBoundingClientRect()
    const x = Math.max(0, Math.min(e.clientX - r.left, r.width))
    const y = Math.max(0, Math.min(e.clientY - r.top, r.height))
    return { x, y }
  }

  const onMouseDown = (e) => {
    if (!editable) return
    e.preventDefault()
    const p = toDisplay(e)
    setDrag({ x0: p.x, y0: p.y, x1: p.x, y1: p.y })
  }
  const onMouseMove = (e) => {
    if (!drag) return
    const p = toDisplay(e)
    setDrag({ ...drag, x1: p.x, y1: p.y })
  }
  const onMouseUp = () => {
    if (!drag) return
    const x = Math.min(drag.x0, drag.x1)
    const y = Math.min(drag.y0, drag.y1)
    const w = Math.abs(drag.x1 - drag.x0)
    const h = Math.abs(drag.y1 - drag.y0)
    setDrag(null)
    if (w < 4 || h < 4) return   // 太小忽略
    // 换算回原始像素坐标
    onAddRect?.({
      x: Math.round(x * scaleX),
      y: Math.round(y * scaleY),
      w: Math.round(w * scaleX),
      h: Math.round(h * scaleY),
    })
  }

  // 已有 mask 在 SVG 上的显示坐标
  const renderMaskRect = (m, idx) => {
    const mtype = (m.type || 'rect').toLowerCase()
    let bx, by, bw, bh
    if (mtype === 'rect') {
      bx = m.x; by = m.y; bw = m.w; bh = m.h
    } else if (mtype === 'selector' && m.bbox) {
      bx = m.bbox.x; by = m.bbox.y; bw = m.bbox.w; bh = m.bbox.h
    } else {
      return null
    }
    const x = bx / scaleX
    const y = by / scaleY
    const w = bw / scaleX
    const h = bh / scaleY
    const isRect = mtype === 'rect'
    return (
      <g key={idx}>
        <rect x={x} y={y} width={w} height={h}
          fill={isRect ? 'rgba(220,38,38,0.18)' : 'rgba(124,58,237,0.18)'}
          stroke={isRect ? '#dc2626' : '#7c3aed'} strokeWidth="1.5"
          strokeDasharray={isRect ? null : '4,3'}
          style={{ cursor: editable && isRect ? 'pointer' : 'default' }}
          onClick={(e) => { e.stopPropagation(); if (editable && isRect) onRemove?.(idx) }}>
          <title>
            #{idx + 1} {mtype}
            {isRect ? ` ${bw}×${bh}` : ` selector="${m.selector}"`}
            {editable && isRect ? ' · 点击删除' : ''}
          </title>
        </rect>
        <text x={x + 4} y={y + 14} fontSize="11"
          fill={isRect ? '#dc2626' : '#7c3aed'} fontFamily="monospace">
          #{idx + 1}{isRect ? '' : ' 🔗'}
        </text>
      </g>
    )
  }

  const dragRect = drag && (() => {
    const x = Math.min(drag.x0, drag.x1)
    const y = Math.min(drag.y0, drag.y1)
    const w = Math.abs(drag.x1 - drag.x0)
    const h = Math.abs(drag.y1 - drag.y0)
    return { x, y, w, h }
  })()

  return (
    <div ref={containerRef} className="relative inline-block max-w-full select-none">
      <img ref={imgRef} src={src} alt="baseline" onLoad={measure}
        className="block max-w-full border rounded shadow-sm"
        style={{ cursor: editable ? 'crosshair' : 'zoom-in' }}
        draggable={false} />
      {imgSize.display && (
        <svg className="absolute inset-0 w-full h-full"
          viewBox={`0 0 ${imgSize.display.w} ${imgSize.display.h}`}
          preserveAspectRatio="none"
          onMouseDown={onMouseDown} onMouseMove={onMouseMove}
          onMouseUp={onMouseUp} onMouseLeave={onMouseUp}>
          {(masks || []).map(renderMaskRect)}
          {dragRect && (
            <rect x={dragRect.x} y={dragRect.y} width={dragRect.w} height={dragRect.h}
              fill="rgba(59,130,246,0.25)" stroke="#2563eb" strokeWidth="1.5" strokeDasharray="6,3" />
          )}
        </svg>
      )}
      {/* 不可编辑时图片可点击放大；editable 时禁用链接以免影响拖拽 */}
      {!editable && (
        <a href={src} target="_blank" rel="noreferrer"
          className="absolute inset-0" style={{ pointerEvents: 'none' }} />
      )}
      {imgSize.natural && (
        <div className="text-[10px] text-slate-400 mt-1 font-mono">
          原始尺寸 {imgSize.natural.w}×{imgSize.natural.h} · 显示比例 {(1 / scaleX).toFixed(2)}x
        </div>
      )}
    </div>
  )
}


// ─────────────────────── 基线详情抽屉 ───────────────────────
function BaselineDetail({ baselineId, onClose, onChanged, showToast }) {
  const [detail, setDetail] = useState(null)
  const [loading, setLoading] = useState(false)
  const [err, setErr] = useState('')
  const [editingMasks, setEditingMasks] = useState(false)
  const [maskDraft, setMaskDraft] = useState([])
  const [thresholdDraft, setThresholdDraft] = useState(0.05)
  const [algoDraft, setAlgoDraft] = useState('pixel')
  const [busy, setBusy] = useState(false)
  const [versions, setVersions] = useState([])

  const load = async () => {
    if (!baselineId) return
    setLoading(true); setErr('')
    try {
      const [r, vr] = await Promise.all([
        visualAPI.getBaseline(baselineId),
        visualAPI.listVersions(baselineId).catch(() => ({ versions: [] })),
      ])
      setDetail(r.baseline)
      const m = r.baseline?.metadata || {}
      setMaskDraft(m.masks || [])
      setThresholdDraft(m.threshold ?? 0.05)
      setAlgoDraft(m.algorithm || 'pixel')
      setVersions(vr.versions || [])
    } catch (e) {
      setErr(e.message || '加载失败')
    } finally {
      setLoading(false)
    }
  }
  useEffect(() => { load() }, [baselineId])

  // Phase 10B: 危险操作弹窗状态（rollback / delete）
  const [rollbackTarget, setRollbackTarget] = useState(null)  // 待回滚版本对象
  const [deleteOpen, setDeleteOpen] = useState(false)

  const doRollback = async (v) => {
    setBusy(true)
    try {
      await visualAPI.rollback(baselineId, {
        version_id: v.id, by: 'user', note: `回滚到 ${v.id}`,
        confirm: true, confirm_text: VISUAL_DANGER.ROLLBACK_BASELINE,
      })
      showToast('已回滚', 'success')
      setRollbackTarget(null)
      load(); onChanged?.()
    } catch (e) {
      showToast(`回滚失败: ${e.message}`, 'error')
    } finally { setBusy(false) }
  }

  const handleApprove = async (run_id) => {
    if (!confirm(`确认用 ${run_id ? `run ${run_id}` : '最近一次'} 的截图覆盖当前基线？`)) return
    setBusy(true)
    try {
      await visualAPI.approveBaseline(baselineId, run_id ? { source: 'specific_run', run_id } : { source: 'latest_current' })
      showToast('基线已更新', 'success')
      onChanged?.(); load()
    } catch (e) {
      showToast(`批准失败: ${e.message}`, 'error')
    } finally { setBusy(false) }
  }

  const handleSaveConfig = async () => {
    setBusy(true)
    try {
      const masksPayload = maskDraft
        .map(m => {
          const t = (m.type || 'rect').toLowerCase()
          if (t === 'selector') {
            const sel = (m.selector || '').trim()
            if (!sel) return null
            return { type: 'selector', selector: sel, padding: +(m.padding || 0) }
          }
          return { type: 'rect', x: +m.x || 0, y: +m.y || 0, w: +m.w || 0, h: +m.h || 0 }
        })
        .filter(Boolean)
      await visualAPI.updateConfig(baselineId, {
        threshold: parseFloat(thresholdDraft),
        algorithm: algoDraft,
        masks: masksPayload,
        note: '配置更新（UI）',
      })
      showToast('配置已保存', 'success')
      setEditingMasks(false)
      load(); onChanged?.()
    } catch (e) {
      showToast(`保存失败: ${e.message}`, 'error')
    } finally { setBusy(false) }
  }

  const doDelete = async () => {
    setBusy(true)
    try {
      await visualAPI.deleteBaseline(baselineId, {
        delete_currents: false, delete_diffs: false,
        confirm: true, confirm_text: VISUAL_DANGER.DELETE_BASELINE,
      })
      showToast('基线已删除', 'success')
      setDeleteOpen(false)
      onChanged?.(); onClose()
    } catch (e) {
      showToast(`删除失败: ${e.message}`, 'error')
    } finally { setBusy(false) }
  }

  if (!baselineId) return null
  return (
    <div className="fixed inset-0 z-40 bg-black/40 flex justify-end" onClick={onClose}>
      <div className="bg-white w-[1100px] max-w-[95vw] h-full overflow-auto shadow-2xl" onClick={e => e.stopPropagation()}>
        <div className="sticky top-0 bg-white border-b px-5 py-3 flex items-center justify-between z-10">
          <div>
            <div className="text-lg font-bold">基线详情</div>
            <div className="text-xs text-slate-500 font-mono">{baselineId}</div>
          </div>
          <button onClick={onClose} className="text-slate-500 hover:text-slate-800 text-xl">✕</button>
        </div>

        {loading && <div className="p-8 text-center text-slate-500">加载中…</div>}
        {err && <div className="p-4 m-4 bg-red-50 text-red-700 rounded">{err}</div>}

        {detail && (
          <div className="p-5 space-y-5">
            {/* 元数据 */}
            <div className="bg-slate-50 border rounded-lg p-4">
              <div className="text-sm font-semibold mb-2">元数据</div>
              <div className="grid grid-cols-2 gap-2 text-xs">
                <div><span className="text-slate-500">case_id：</span><span className="font-mono">{detail.metadata?.case_id || '-'}</span></div>
                <div><span className="text-slate-500">name：</span>{detail.metadata?.name || '-'}</div>
                <div><span className="text-slate-500">阈值：</span>{detail.metadata?.threshold ?? 0.05}</div>
                <div><span className="text-slate-500">算法：</span>{detail.metadata?.algorithm || 'pixel'}</div>
                <div><span className="text-slate-500">大小：</span>{fmtBytes(detail.size)}</div>
                <div><span className="text-slate-500">最后更新：</span>{detail.metadata?.updated_at || detail.mtime || '-'}</div>
                <div><span className="text-slate-500">更新人：</span>{detail.metadata?.updated_by || '-'}</div>
                <div><span className="text-slate-500">已批准次数：</span>{detail.metadata?.approve_count || 0}</div>
                <div><span className="text-slate-500">最后 run_id：</span><span className="font-mono">{detail.metadata?.last_run_id || '-'}</span></div>
                <div><span className="text-slate-500">屏蔽区域：</span>{(detail.metadata?.masks || []).length} 个</div>
              </div>
            </div>

            {/* 配置编辑 */}
            <div className="border rounded-lg p-4">
              <div className="flex items-center justify-between mb-3">
                <div className="text-sm font-semibold">对比配置</div>
                <div className="flex gap-2">
                  {!editingMasks && <button onClick={() => setEditingMasks(true)} className="px-3 py-1 text-xs bg-blue-50 text-blue-700 rounded hover:bg-blue-100">编辑</button>}
                  {editingMasks && (
                    <>
                      <button onClick={() => { setEditingMasks(false); load() }} className="px-3 py-1 text-xs bg-slate-100 text-slate-700 rounded hover:bg-slate-200">取消</button>
                      <button onClick={handleSaveConfig} disabled={busy} className="px-3 py-1 text-xs bg-green-600 text-white rounded hover:bg-green-700 disabled:opacity-50">保存</button>
                    </>
                  )}
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4 mb-3">
                <div>
                  <label className="text-xs text-slate-500">阈值（0-1，超过则失败）</label>
                  <input type="number" step="0.01" min="0" max="1" value={thresholdDraft}
                    disabled={!editingMasks}
                    onChange={e => setThresholdDraft(e.target.value)}
                    className="mt-1 w-full px-2 py-1.5 border rounded text-sm disabled:bg-slate-50" />
                </div>
                <div>
                  <label className="text-xs text-slate-500">对比算法</label>
                  <select value={algoDraft} disabled={!editingMasks}
                    onChange={e => setAlgoDraft(e.target.value)}
                    className="mt-1 w-full px-2 py-1.5 border rounded text-sm disabled:bg-slate-50">
                    <option value="pixel">pixel（像素差，默认）</option>
                    <option value="ssim">ssim（结构相似度，需 scikit-image）</option>
                  </select>
                </div>
              </div>

              <div>
                <div className="flex items-center justify-between mb-2">
                  <label className="text-xs text-slate-500">屏蔽区域 mask（rect 矩形 / selector 元素选择器）</label>
                  {editingMasks && (
                    <div className="flex gap-2">
                      <button onClick={() => setMaskDraft([...maskDraft, { type: 'rect', x: 0, y: 0, w: 100, h: 30 }])}
                        className="text-xs text-blue-600 hover:underline">+ 矩形</button>
                      <button onClick={() => setMaskDraft([...maskDraft, { type: 'selector', selector: '', padding: 4 }])}
                        className="text-xs text-violet-600 hover:underline">+ 选择器</button>
                    </div>
                  )}
                </div>
                {maskDraft.length === 0 && <div className="text-xs text-slate-400 py-2">暂无屏蔽区域</div>}
                {maskDraft.map((m, idx) => {
                  const mtype = (m.type || 'rect').toLowerCase()
                  const setField = (k, v) => {
                    const arr = [...maskDraft]; arr[idx] = { ...arr[idx], [k]: v }; setMaskDraft(arr)
                  }
                  const removeRow = () => setMaskDraft(maskDraft.filter((_, i) => i !== idx))
                  return (
                    <div key={idx} className="flex items-center gap-2 mb-1.5 text-xs">
                      <span className="w-6 text-slate-400">#{idx + 1}</span>
                      <select value={mtype} disabled={!editingMasks}
                        onChange={e => setField('type', e.target.value)}
                        className="px-1.5 py-0.5 border rounded text-xs disabled:bg-slate-50">
                        <option value="rect">rect</option>
                        <option value="selector">selector</option>
                      </select>
                      {mtype === 'rect' ? (
                        <>
                          {['x', 'y', 'w', 'h'].map(k => (
                            <div key={k} className="flex items-center gap-1">
                              <span className="text-slate-500">{k}:</span>
                              <input type="number" value={m[k] ?? 0} disabled={!editingMasks}
                                onChange={e => setField(k, +e.target.value)}
                                className="w-16 px-1.5 py-0.5 border rounded disabled:bg-slate-50" />
                            </div>
                          ))}
                          {m.bbox && (
                            <span className="text-[10px] text-slate-400 ml-1" title="最近一次执行解析到的 bbox">
                              bbox: {m.bbox.x},{m.bbox.y} {m.bbox.w}×{m.bbox.h}
                            </span>
                          )}
                        </>
                      ) : (
                        <>
                          <input type="text" value={m.selector ?? ''} disabled={!editingMasks}
                            placeholder=".banner, [data-testid='clock']"
                            onChange={e => setField('selector', e.target.value)}
                            className="flex-1 px-2 py-0.5 border rounded font-mono text-xs disabled:bg-slate-50" />
                          <div className="flex items-center gap-1">
                            <span className="text-slate-500">padding:</span>
                            <input type="number" min="0" max="200"
                              value={m.padding ?? 0} disabled={!editingMasks}
                              onChange={e => setField('padding', +e.target.value)}
                              className="w-14 px-1.5 py-0.5 border rounded disabled:bg-slate-50" />
                          </div>
                          {m.bbox && (
                            <span className="text-[10px] text-violet-500 ml-1"
                              title="最近一次执行时解析到的 bbox（每次执行刷新）">
                              ✓ bbox: {m.bbox.x},{m.bbox.y} {m.bbox.w}×{m.bbox.h}
                            </span>
                          )}
                        </>
                      )}
                      {editingMasks && (
                        <button onClick={removeRow}
                          className="text-red-500 hover:text-red-700 ml-auto">删除</button>
                      )}
                    </div>
                  )
                })}
              </div>
            </div>

            {/* 基线图预览 + 拖拽画 mask（Phase 8） */}
            <div className="border rounded-lg p-4">
              <div className="flex items-center justify-between mb-2">
                <div className="text-sm font-semibold">基线图</div>
                <div className="text-xs text-slate-500">
                  {editingMasks ? '🖱️ 在图上拖拽画矩形 → 自动加入 mask 列表 · 点击已有 mask 删除' : '点击「编辑」启用画框'}
                </div>
              </div>
              <MaskCanvas
                src={`${VISUAL_BASE}/baselines/${baselineId}.png?t=${Date.now()}`}
                masks={maskDraft}
                editable={editingMasks}
                onAddRect={(rect) => setMaskDraft([...maskDraft, { type: 'rect', ...rect }])}
                onRemove={(idx) => setMaskDraft(maskDraft.filter((_, i) => i !== idx))}
              />
            </div>

            {/* 最近 diff 历史 */}
            {detail.recent_diffs?.length > 0 && (
              <div className="border rounded-lg p-4">
                <div className="text-sm font-semibold mb-2">最近 diff（点击批准用对应 current 覆盖基线）</div>
                <div className="grid grid-cols-3 gap-3">
                  {detail.recent_diffs.slice(0, 9).map((d, i) => (
                    <div key={i} className="border rounded overflow-hidden text-xs">
                      <a href={`${VISUAL_BASE}/diff/${d.filename}`} target="_blank" rel="noreferrer">
                        <img src={`${VISUAL_BASE}/diff/${d.filename}`} className="w-full h-32 object-cover" alt="diff" />
                      </a>
                      <div className="p-2 bg-slate-50">
                        <div className="font-mono truncate" title={d.run_id}>run: {d.run_id}</div>
                        <div className="text-slate-500">{d.mtime}</div>
                        <button onClick={() => handleApprove(d.run_id)} disabled={busy}
                          className="mt-1 w-full px-2 py-1 bg-green-600 text-white rounded hover:bg-green-700 disabled:opacity-50">
                          ✓ 用此 run 批准
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* 历史日志 */}
            {detail.metadata?.history?.length > 0 && (
              <div className="border rounded-lg p-4">
                <div className="text-sm font-semibold mb-2">变更历史</div>
                <div className="space-y-1.5 text-xs max-h-60 overflow-auto">
                  {[...(detail.metadata.history)].reverse().map((h, i) => (
                    <div key={i} className="flex items-start gap-2 py-1 border-b border-slate-100 last:border-b-0">
                      <span className={`px-1.5 py-0.5 rounded text-white text-[10px] ${h.event === 'approved' ? 'bg-green-600' : h.event === 'created' ? 'bg-blue-600' : 'bg-slate-500'}`}>
                        {h.event}
                      </span>
                      <div className="flex-1">
                        <div><span className="text-slate-500">{h.at}</span> by <b>{h.by}</b></div>
                        {h.run_id && <div className="font-mono text-slate-500">run: {h.run_id}</div>}
                        {h.note && <div className="text-slate-700">{h.note}</div>}
                        {h.changed && <div className="text-slate-500">变更: {h.changed.join(', ')}</div>}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* 版本历史 / 回滚 */}
            <div className="border rounded-lg p-4">
              <div className="flex items-center justify-between mb-2">
                <div>
                  <div className="text-sm font-semibold">版本历史</div>
                  <div className="text-xs text-slate-500">每次创建/批准/回滚都会归档为一个版本，默认保留最近 5 个（可由 VISUAL_KEEP_VERSIONS 调整）</div>
                </div>
                <span className="text-xs text-slate-500">共 {versions.length}</span>
              </div>
              {versions.length === 0 && (
                <div className="text-xs text-slate-400 py-2">暂无版本（新创建的基线会在下次执行时自动归档首版）</div>
              )}
              {versions.length > 0 && (
                <div className="grid grid-cols-3 gap-3">
                  {[...versions].reverse().map((v, i) => {
                    const colors = {
                      created: 'bg-blue-100 text-blue-700',
                      approved: 'bg-green-100 text-green-700',
                      rollback: 'bg-violet-100 text-violet-700',
                      pre_rollback: 'bg-amber-100 text-amber-700',
                    }
                    const isCurrent = i === 0
                    return (
                      <div key={v.id} className={`border rounded overflow-hidden text-xs ${isCurrent ? 'ring-2 ring-blue-500' : ''}`}>
                        {v.preview_url ? (
                          <a href={v.preview_url} target="_blank" rel="noreferrer">
                            <img src={v.preview_url}
                              className="w-full h-28 object-cover bg-slate-50 hover:opacity-80" alt="version" />
                          </a>
                        ) : (
                          <div className="w-full h-28 bg-slate-100 flex items-center justify-center text-slate-400">无预览</div>
                        )}
                        <div className="p-2 bg-slate-50 space-y-1">
                          <div className="flex items-center gap-1.5 flex-wrap">
                            <span className={`text-[10px] px-1.5 py-0.5 rounded ${colors[v.source] || 'bg-slate-100 text-slate-700'}`}>
                              {v.source}
                            </span>
                            {isCurrent && <span className="text-[10px] px-1.5 py-0.5 rounded bg-blue-600 text-white">当前</span>}
                            {!v.exists && <span className="text-[10px] px-1.5 py-0.5 rounded bg-red-100 text-red-700">文件丢失</span>}
                          </div>
                          <div className="font-mono text-[10px] text-slate-500 truncate" title={v.id}>{v.id}</div>
                          <div className="text-slate-500 text-[10px]">{v.at} · {v.by}</div>
                          {v.note && <div className="text-slate-700 text-[10px] truncate" title={v.note}>📝 {v.note}</div>}
                          {!isCurrent && v.exists && (
                            <button onClick={() => setRollbackTarget(v)} disabled={busy}
                              className="w-full mt-1 px-2 py-1 bg-violet-600 text-white rounded hover:bg-violet-700 disabled:opacity-50">
                              ⟲ 回滚到此版本
                            </button>
                          )}
                        </div>
                      </div>
                    )
                  })}
                </div>
              )}
            </div>

            {/* 危险操作 */}
            <div className="border-2 border-red-200 rounded-lg p-4 bg-red-50/30">
              <div className="text-sm font-semibold text-red-700 mb-2">危险操作</div>
              <button onClick={() => setDeleteOpen(true)} disabled={busy}
                className="px-4 py-1.5 bg-red-600 text-white rounded hover:bg-red-700 disabled:opacity-50 text-sm">
                删除此基线
              </button>
              <p className="text-xs text-red-600 mt-1.5">删除后下次执行将自动重新生成基线（baseline_created 状态）</p>
            </div>
          </div>
        )}
      </div>

      {/* Phase 10B: 危险操作确认弹窗 */}
      <DangerConfirmDialog
        open={!!rollbackTarget}
        title="回滚基线"
        description={
          rollbackTarget
            ? `将把基线 ${baselineId} 回滚到版本：\n\nid: ${rollbackTarget.id}\n来源: ${rollbackTarget.source}\n时间: ${rollbackTarget.at}\n操作人: ${rollbackTarget.by}\n\n当前生效基线会先自动留存为 pre_rollback 版本。`
            : ''
        }
        confirmText={VISUAL_DANGER.ROLLBACK_BASELINE}
        confirmLabel="回滚"
        loading={busy}
        onConfirm={() => doRollback(rollbackTarget)}
        onClose={() => setRollbackTarget(null)}
      />
      <DangerConfirmDialog
        open={deleteOpen}
        title="删除基线"
        description={`将永久删除基线 ${baselineId}（关联 current/diff 历史不会自动删除，请到「数据清理」处理）。`}
        confirmText={VISUAL_DANGER.DELETE_BASELINE}
        confirmLabel="删除"
        loading={busy}
        onConfirm={doDelete}
        onClose={() => setDeleteOpen(false)}
      />
    </div>
  )
}

// ─────────────────────── 待审核 Tab ───────────────────────
function PendingTab({ showToast, onChanged }) {
  const [days, setDays] = useState(7)
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(false)
  const [busyId, setBusyId] = useState('')

  const load = async () => {
    setLoading(true)
    try {
      const r = await visualAPI.pendingReviews({ days, limit: 100 })
      setItems(r.items || [])
    } catch (e) {
      showToast(`加载失败: ${e.message}`, 'error')
    } finally { setLoading(false) }
  }
  useEffect(() => { load() }, [days])

  const handleApprove = async (item) => {
    if (!confirm(`批准并用 run ${item.run_id} 的截图更新基线 ${item.baseline_id}？`)) return
    setBusyId(item.baseline_id)
    try {
      await visualAPI.approveBaseline(item.baseline_id, { source: 'specific_run', run_id: item.run_id, note: '从待审核批准' })
      showToast('基线已更新', 'success')
      load(); onChanged?.()
    } catch (e) {
      showToast(`批准失败: ${e.message}`, 'error')
    } finally { setBusyId('') }
  }

  return (
    <div>
      <div className="flex items-center gap-3 mb-4">
        <label className="text-sm text-slate-600">最近</label>
        <select value={days} onChange={e => setDays(+e.target.value)} className="px-2 py-1 border rounded text-sm">
          <option value={1}>1 天</option>
          <option value={3}>3 天</option>
          <option value={7}>7 天</option>
          <option value={14}>14 天</option>
          <option value={30}>30 天</option>
        </select>
        <span className="text-sm text-slate-500">的失败用例</span>
        <div className="flex-1" />
        <button onClick={load} className="px-3 py-1 text-sm bg-slate-100 hover:bg-slate-200 rounded">刷新</button>
      </div>

      {loading && <div className="text-center text-slate-500 py-8">加载中…</div>}
      {!loading && items.length === 0 && (
        <div className="text-center text-slate-400 py-12">
          <div className="text-4xl mb-2">✓</div>
          <div>近 {days} 天没有待审核的视觉失败</div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {items.map((it, i) => (
          <div key={i} className="border rounded-lg overflow-hidden bg-white">
            <div className="px-3 py-2 bg-slate-50 border-b text-xs">
              <div className="font-mono text-slate-700">{it.baseline_id}</div>
              <div className="flex items-center gap-3 mt-1 text-slate-500">
                <span>用例: {it.test_case_id}</span>
                <span>run: <span className="font-mono">{it.run_id}</span></span>
                <span className="text-red-600 font-semibold">diff: {(it.diff_ratio * 100).toFixed(2)}%</span>
                <span>阈值: {(it.threshold * 100).toFixed(1)}%</span>
              </div>
            </div>
            <div className="grid grid-cols-3 gap-2 p-3">
              <div>
                <div className="text-[10px] text-slate-500 mb-1">基线</div>
                <a href={`${VISUAL_BASE}/baselines/${it.baseline_id}.png`} target="_blank" rel="noreferrer">
                  <img src={`${VISUAL_BASE}/baselines/${it.baseline_id}.png`}
                    className="w-full h-24 object-cover border rounded hover:opacity-80" alt="baseline" />
                </a>
              </div>
              <div>
                <div className="text-[10px] text-slate-500 mb-1">当前</div>
                {it.current_path && (
                  <a href={`${VISUAL_BASE}/current/${it.current_path}`} target="_blank" rel="noreferrer">
                    <img src={`${VISUAL_BASE}/current/${it.current_path}`}
                      className="w-full h-24 object-cover border rounded hover:opacity-80" alt="current" />
                  </a>
                )}
              </div>
              <div>
                <div className="text-[10px] text-slate-500 mb-1">差异</div>
                {it.diff_path && (
                  <a href={`${VISUAL_BASE}/diff/${it.diff_path}`} target="_blank" rel="noreferrer">
                    <img src={`${VISUAL_BASE}/diff/${it.diff_path}`}
                      className="w-full h-24 object-cover border rounded hover:opacity-80" alt="diff" />
                  </a>
                )}
              </div>
            </div>
            <div className="px-3 pb-3 flex items-center gap-2">
              <button onClick={() => handleApprove(it)} disabled={busyId === it.baseline_id}
                className="flex-1 px-3 py-1.5 bg-green-600 text-white rounded text-sm hover:bg-green-700 disabled:opacity-50">
                ✓ 批准并更新基线
              </button>
              <a href={`${VISUAL_BASE}/diff/${it.diff_path}`} target="_blank" rel="noreferrer"
                className="px-3 py-1.5 bg-slate-100 text-slate-700 rounded text-sm hover:bg-slate-200">
                查看大图
              </a>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

// ─────────────────────── 基线管理 Tab ───────────────────────
function BaselinesTab({ onSelect, refreshKey, showToast }) {
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(false)
  const [search, setSearch] = useState('')
  const [filterCase, setFilterCase] = useState('')
  const [filterEnv, setFilterEnv] = useState('')
  const [filterViewport, setFilterViewport] = useState('')
  const [filterBranch, setFilterBranch] = useState('')
  const [namespaces, setNamespaces] = useState({ envs: [], viewports: [], branches: [] })
  const [selected, setSelected] = useState(new Set())
  const [busy, setBusy] = useState(false)
  // Phase 10B: 批量删除危险确认弹窗
  const [bulkDeleteOpen, setBulkDeleteOpen] = useState(false)

  const load = async () => {
    setLoading(true)
    try {
      const r = await visualAPI.listBaselines({
        name: search || undefined,
        case_id: filterCase || undefined,
        env: filterEnv || undefined,
        viewport: filterViewport || undefined,
        branch: filterBranch || undefined,
        limit: 500,
      })
      setItems(r.items || [])
      setSelected(new Set())
    } catch (e) {
      showToast(`加载失败: ${e.message}`, 'error')
    } finally { setLoading(false) }
  }
  const loadNamespaces = async () => {
    try {
      const r = await visualAPI.listNamespaces()
      setNamespaces(r.namespaces || { envs: [], viewports: [], branches: [] })
    } catch { /* ignore */ }
  }
  useEffect(() => { load() }, [refreshKey, filterEnv, filterViewport, filterBranch])
  useEffect(() => { loadNamespaces() }, [refreshKey])

  const toggleAll = () => {
    if (selected.size === items.length) setSelected(new Set())
    else setSelected(new Set(items.map(it => it.baseline_id)))
  }
  const toggleOne = (bid) => {
    const s = new Set(selected)
    if (s.has(bid)) s.delete(bid); else s.add(bid)
    setSelected(s)
  }

  const bulkApprove = async () => {
    if (selected.size === 0) return
    if (!confirm(`批量批准 ${selected.size} 个基线？\n（用每个基线最近一次的 current 截图覆盖）`)) return
    setBusy(true)
    try {
      const r = await visualAPI.bulkApprove({
        baseline_ids: [...selected],
        source: 'latest_current',
        note: '批量批准（UI）',
      })
      showToast(`成功 ${r.success_count} / 失败 ${r.fail_count}`, r.fail_count ? 'error' : 'success')
      load()
    } catch (e) {
      showToast(`批量批准失败: ${e.message}`, 'error')
    } finally { setBusy(false) }
  }
  const doBulkDelete = async () => {
    setBusy(true)
    try {
      const r = await visualAPI.bulkDelete({
        baseline_ids: [...selected],
        delete_currents: false,
        delete_diffs: false,
        confirm: true,
        confirm_text: VISUAL_DANGER.BULK_DELETE_BASELINES,
      })
      showToast(`成功 ${r.success_count} / 失败 ${r.fail_count}`, r.fail_count ? 'error' : 'success')
      setBulkDeleteOpen(false)
      load()
    } catch (e) {
      showToast(`批量删除失败: ${e.message}`, 'error')
    } finally { setBusy(false) }
  }
  const bulkUpdateThreshold = async () => {
    if (selected.size === 0) return
    const v = prompt(`批量设置阈值（0~1，越小越严）`, '0.05')
    if (!v) return
    const t = parseFloat(v)
    if (Number.isNaN(t) || t < 0 || t > 1) { showToast('阈值必须在 0~1 之间', 'error'); return }
    setBusy(true)
    try {
      const r = await visualAPI.bulkConfig({
        baseline_ids: [...selected],
        threshold: t,
        note: '批量调整阈值（UI）',
      })
      showToast(`成功 ${r.success_count} / 失败 ${r.fail_count}`, r.fail_count ? 'error' : 'success')
      load()
    } catch (e) {
      showToast(`批量配置失败: ${e.message}`, 'error')
    } finally { setBusy(false) }
  }

  const allChecked = items.length > 0 && selected.size === items.length
  const someChecked = selected.size > 0 && !allChecked

  return (
    <div>
      <div className="flex flex-wrap items-center gap-2 mb-3">
        <input value={search} onChange={e => setSearch(e.target.value)} placeholder="按名称模糊搜索"
          className="px-3 py-1.5 border rounded text-sm w-52" />
        <input value={filterCase} onChange={e => setFilterCase(e.target.value)} placeholder="case_id"
          className="px-3 py-1.5 border rounded text-sm w-36" />
        <select value={filterEnv} onChange={e => setFilterEnv(e.target.value)}
          className="px-2 py-1.5 border rounded text-sm">
          <option value="">所有环境</option>
          {namespaces.envs.map(v => <option key={v} value={v}>env: {v}</option>)}
        </select>
        <select value={filterViewport} onChange={e => setFilterViewport(e.target.value)}
          className="px-2 py-1.5 border rounded text-sm">
          <option value="">所有视口</option>
          {namespaces.viewports.map(v => <option key={v} value={v}>vp: {v}</option>)}
        </select>
        <select value={filterBranch} onChange={e => setFilterBranch(e.target.value)}
          className="px-2 py-1.5 border rounded text-sm">
          <option value="">所有分支</option>
          {namespaces.branches.map(v => <option key={v} value={v}>br: {v}</option>)}
        </select>
        <button onClick={load} className="px-3 py-1.5 bg-blue-600 text-white rounded text-sm hover:bg-blue-700">搜索</button>
        <div className="flex-1" />
        <span className="text-xs text-slate-500">共 {items.length} 个基线 · 已选 {selected.size}</span>
      </div>

      {/* 批量操作栏 */}
      {selected.size > 0 && (
        <div className="mb-3 px-3 py-2 bg-blue-50 border border-blue-200 rounded-lg flex items-center gap-2 text-sm">
          <span className="text-blue-700 font-semibold">已选 {selected.size} 项</span>
          <span className="flex-1" />
          <button onClick={bulkApprove} disabled={busy}
            className="px-3 py-1 bg-green-600 text-white rounded text-xs hover:bg-green-700 disabled:opacity-50">
            ✓ 批量批准
          </button>
          <button onClick={bulkUpdateThreshold} disabled={busy}
            className="px-3 py-1 bg-amber-600 text-white rounded text-xs hover:bg-amber-700 disabled:opacity-50">
            ⚙ 批量改阈值
          </button>
          <button onClick={() => selected.size > 0 && setBulkDeleteOpen(true)} disabled={busy}
            className="px-3 py-1 bg-red-600 text-white rounded text-xs hover:bg-red-700 disabled:opacity-50">
            🗑 批量删除
          </button>
          <button onClick={() => setSelected(new Set())}
            className="px-3 py-1 bg-slate-200 text-slate-700 rounded text-xs hover:bg-slate-300">
            取消选择
          </button>
        </div>
      )}

      {loading && <div className="text-center text-slate-500 py-8">加载中…</div>}
      {!loading && items.length === 0 && (
        <div className="text-center text-slate-400 py-12">
          <div className="text-4xl mb-2">📷</div>
          <div>暂无基线</div>
          <div className="text-xs mt-1">在 Web UI 用例的 assertion 中选「📸 视觉对比」并执行后会自动创建</div>
        </div>
      )}

      {items.length > 0 && (
        <div className="overflow-auto border rounded-lg">
          <table className="w-full text-sm">
            <thead className="bg-slate-50 text-slate-700 text-xs">
              <tr>
                <th className="px-3 py-2 w-8">
                  <input type="checkbox" checked={allChecked}
                    ref={el => el && (el.indeterminate = someChecked)}
                    onChange={toggleAll} />
                </th>
                <th className="px-3 py-2 text-left">预览</th>
                <th className="px-3 py-2 text-left">baseline_id</th>
                <th className="px-3 py-2 text-left">env / vp / br</th>
                <th className="px-3 py-2 text-left">name</th>
                <th className="px-3 py-2 text-right">阈值</th>
                <th className="px-3 py-2 text-center">算法</th>
                <th className="px-3 py-2 text-center">mask</th>
                <th className="px-3 py-2 text-center">已批准</th>
                <th className="px-3 py-2 text-left">最后更新</th>
                <th className="px-3 py-2"></th>
              </tr>
            </thead>
            <tbody>
              {items.map(it => (
                <tr key={it.baseline_id} className={`border-t hover:bg-slate-50 ${selected.has(it.baseline_id) ? 'bg-blue-50/50' : ''}`}>
                  <td className="px-3 py-2">
                    <input type="checkbox" checked={selected.has(it.baseline_id)}
                      onChange={() => toggleOne(it.baseline_id)} />
                  </td>
                  <td className="px-3 py-2">
                    <img src={`${VISUAL_BASE}/baselines/${it.filename}`}
                      className="w-16 h-10 object-cover border rounded" alt="" />
                  </td>
                  <td className="px-3 py-2 font-mono text-xs break-all">{it.baseline_id}</td>
                  <td className="px-3 py-2 text-xs">
                    <div className="flex flex-wrap gap-1">
                      {it.env && it.env !== 'default' && (
                        <span className="px-1.5 py-0.5 bg-blue-100 text-blue-700 rounded text-[10px]">{it.env}</span>
                      )}
                      {it.viewport && it.viewport !== 'default' && (
                        <span className="px-1.5 py-0.5 bg-violet-100 text-violet-700 rounded text-[10px]">{it.viewport}</span>
                      )}
                      {it.branch && it.branch !== 'default' && (
                        <span className="px-1.5 py-0.5 bg-amber-100 text-amber-700 rounded text-[10px]">{it.branch}</span>
                      )}
                    </div>
                  </td>
                  <td className="px-3 py-2">{it.name || <span className="text-slate-300">-</span>}</td>
                  <td className="px-3 py-2 text-right">{(it.threshold * 100).toFixed(1)}%</td>
                  <td className="px-3 py-2 text-center">
                    <span className={`text-[10px] px-1.5 py-0.5 rounded ${it.algorithm === 'ssim' ? 'bg-violet-100 text-violet-700' : 'bg-slate-100 text-slate-700'}`}>
                      {it.algorithm}
                    </span>
                  </td>
                  <td className="px-3 py-2 text-center">{it.masks_count || '-'}</td>
                  <td className="px-3 py-2 text-center">{it.approve_count || '-'}</td>
                  <td className="px-3 py-2 text-xs text-slate-500">{it.updated_at}</td>
                  <td className="px-3 py-2 text-right">
                    <button onClick={() => onSelect(it.baseline_id)}
                      className="px-2 py-1 text-xs bg-blue-50 text-blue-700 rounded hover:bg-blue-100">
                      详情
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Phase 10B: 批量删除危险确认弹窗 */}
      <DangerConfirmDialog
        open={bulkDeleteOpen}
        title="批量删除基线"
        description={`将永久删除选中的 ${selected.size} 个基线（含 sidecar/.prev 备份）。`}
        confirmText={VISUAL_DANGER.BULK_DELETE_BASELINES}
        confirmLabel="批量删除"
        loading={busy}
        onConfirm={doBulkDelete}
        onClose={() => setBulkDeleteOpen(false)}
      />
    </div>
  )
}

// ─────────────────────── Webhook 配置 Tab ───────────────────────
function WebhookTab({ showToast }) {
  const [cfg, setCfg] = useState(null)
  const [loading, setLoading] = useState(false)
  const [eventType, setEventType] = useState('visual.diff.failed')
  const [payloadText, setPayloadText] = useState('')
  const [busy, setBusy] = useState(false)
  const [dlq, setDlq] = useState({ items: [], stats: null })
  const [dlqIncludeResolved, setDlqIncludeResolved] = useState(false)
  const [dlqBusyId, setDlqBusyId] = useState(0)
  // Phase 10B: 危险操作确认弹窗
  const [dlqDeleteTarget, setDlqDeleteTarget] = useState(null)
  const [testWebhookOpen, setTestWebhookOpen] = useState(false)

  const load = async () => {
    setLoading(true)
    try {
      const r = await visualAPI.getWebhookConfig()
      setCfg(r.config)
    } catch (e) {
      showToast(`加载失败: ${e.message}`, 'error')
    } finally { setLoading(false) }
  }
  const loadDlq = async () => {
    try {
      const r = await visualAPI.listDeadLetters({ limit: 50, include_resolved: dlqIncludeResolved })
      setDlq({ items: r.items || [], stats: r.stats || null })
    } catch (e) {
      showToast(`死信加载失败: ${e.message}`, 'error')
    }
  }
  useEffect(() => { load() }, [])
  useEffect(() => { loadDlq() }, [dlqIncludeResolved])

  const handleDlqRetry = async (item) => {
    setDlqBusyId(item.id)
    try {
      const r = await visualAPI.retryDeadLetter(item.id)
      if (r.success) {
        showToast(`#${item.id} 重发成功 ✓`, 'success')
      } else {
        showToast(`#${item.id} 仍然失败：${r.error || ''}`, 'error')
      }
      loadDlq()
    } catch (e) {
      showToast(`重发请求失败: ${e.message}`, 'error')
    } finally { setDlqBusyId(0) }
  }
  const doDlqDelete = async () => {
    const item = dlqDeleteTarget
    if (!item) return
    setDlqBusyId(item.id)
    try {
      await visualAPI.deleteDeadLetter(item.id, {
        confirm: true, confirm_text: VISUAL_DANGER.DELETE_DEAD_LETTER,
      })
      showToast('已删除', 'success')
      setDlqDeleteTarget(null)
      loadDlq()
    } catch (e) {
      showToast(`删除失败: ${e.message}`, 'error')
    } finally { setDlqBusyId(0) }
  }

  const doSendTest = async () => {
    setBusy(true)
    try {
      let payload
      if (payloadText.trim()) {
        try { payload = JSON.parse(payloadText) }
        catch { showToast('payload 必须是合法 JSON', 'error'); setBusy(false); return }
      }
      const r = await visualAPI.testWebhook({
        event: eventType, payload,
        confirm: true, confirm_text: VISUAL_DANGER.TEST_WEBHOOK,
      })
      showToast(r.dry_run
        ? '测试事件已构造（未配置 URL，dry_run）'
        : '测试事件已分发到 webhook', r.dry_run ? 'info' : 'success')
      setTestWebhookOpen(false)
    } catch (e) {
      showToast(`发送失败: ${e.message}`, 'error')
    } finally { setBusy(false) }
  }

  return (
    <div className="max-w-3xl">
      <div className="border rounded-lg p-5 mb-4 bg-white">
        <div className="flex items-center justify-between mb-3">
          <div>
            <div className="text-sm font-semibold">当前 Webhook 配置</div>
            <div className="text-xs text-slate-500 mt-0.5">环境变量 VISUAL_WEBHOOK_URL / SECRET / TIMEOUT / EVENTS（修改后需重启服务）</div>
          </div>
          <button onClick={load} className="px-3 py-1 text-xs bg-slate-100 hover:bg-slate-200 rounded">刷新</button>
        </div>

        {loading && <div className="text-slate-500 text-sm">加载中…</div>}
        {cfg && (
          <div className="space-y-2 text-sm">
            <div className="flex items-center gap-2">
              <span className="w-32 text-slate-500">URL</span>
              <span className={`px-2 py-0.5 rounded text-xs ${cfg.url_configured ? 'bg-green-100 text-green-700' : 'bg-red-50 text-red-600'}`}>
                {cfg.url_configured ? '✓ 已配置' : '✗ 未配置'}
              </span>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-32 text-slate-500">HMAC Secret</span>
              <span className={`px-2 py-0.5 rounded text-xs ${cfg.secret_configured ? 'bg-green-100 text-green-700' : 'bg-slate-100 text-slate-500'}`}>
                {cfg.secret_configured ? '✓ 已配置（请求会带 X-Visual-Signature）' : '未配置（不签名）'}
              </span>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-32 text-slate-500">超时</span>
              <span className="text-slate-700">{cfg.timeout_seconds}s</span>
            </div>
            <div className="flex items-start gap-2">
              <span className="w-32 text-slate-500">订阅事件</span>
              <span className="text-slate-700 text-xs flex-1">
                {Array.isArray(cfg.subscriptions)
                  ? cfg.subscriptions.map(e => <span key={e} className="inline-block px-1.5 py-0.5 mr-1 mb-1 bg-blue-50 text-blue-700 rounded">{e}</span>)
                  : <span className="font-mono text-slate-500">{cfg.subscriptions}</span>}
              </span>
            </div>
          </div>
        )}
      </div>

      <div className="border rounded-lg p-5 bg-white">
        <div className="text-sm font-semibold mb-3">发送测试事件</div>
        <div className="space-y-3">
          <div>
            <label className="text-xs text-slate-500">事件类型</label>
            <select value={eventType} onChange={e => setEventType(e.target.value)}
              className="mt-1 w-full px-3 py-1.5 border rounded text-sm">
              <option value="visual.diff.failed">visual.diff.failed</option>
              <option value="visual.diff.passed">visual.diff.passed</option>
              <option value="visual.baseline.created">visual.baseline.created</option>
              <option value="visual.baseline.approved">visual.baseline.approved</option>
              <option value="visual.baseline.config_updated">visual.baseline.config_updated</option>
              <option value="visual.baseline.deleted">visual.baseline.deleted</option>
            </select>
          </div>
          <div>
            <label className="text-xs text-slate-500">payload（JSON，可选；为空时使用 demo 数据）</label>
            <textarea value={payloadText} onChange={e => setPayloadText(e.target.value)}
              rows={6} placeholder='{"case_id":"demo","name":"home","diff_ratio":0.123}'
              className="mt-1 w-full px-3 py-2 border rounded text-xs font-mono" />
          </div>
          <button onClick={() => setTestWebhookOpen(true)} disabled={busy}
            className="px-4 py-2 bg-blue-600 text-white rounded text-sm hover:bg-blue-700 disabled:opacity-50">
            {busy ? '发送中…' : '🚀 发送测试事件'}
          </button>
          {cfg && !cfg.url_configured && (
            <div className="text-xs text-amber-600 bg-amber-50 border border-amber-200 rounded px-3 py-2">
              ⚠️ 当前未配置 VISUAL_WEBHOOK_URL，事件会被构造但不会真正发出（dry_run 模式）。
            </div>
          )}
        </div>
      </div>

      {/* 死信队列 */}
      <div className="border rounded-lg p-5 bg-white mt-4">
        <div className="flex items-center justify-between mb-3">
          <div>
            <div className="text-sm font-semibold">
              死信队列（重试 {3 + 1} 次仍失败的事件）
              {dlq.stats && dlq.stats.unresolved > 0 && (
                <span className="ml-2 text-xs px-2 py-0.5 bg-red-100 text-red-700 rounded">
                  {dlq.stats.unresolved} 待处理
                </span>
              )}
            </div>
            <div className="text-xs text-slate-500 mt-0.5">
              环境变量 VISUAL_WEBHOOK_MAX_RETRIES / VISUAL_WEBHOOK_BACKOFF_BASE 控制策略；存储在 data/visual_webhook_dlq.sqlite
            </div>
          </div>
          <div className="flex items-center gap-2">
            <label className="text-xs text-slate-600 flex items-center gap-1">
              <input type="checkbox" checked={dlqIncludeResolved}
                onChange={e => setDlqIncludeResolved(e.target.checked)} />
              含已解决
            </label>
            <button onClick={loadDlq} className="px-3 py-1 text-xs bg-slate-100 hover:bg-slate-200 rounded">刷新</button>
          </div>
        </div>

        {dlq.stats && (
          <div className="flex items-center gap-3 text-xs text-slate-600 mb-3">
            <span>总计: <b>{dlq.stats.total}</b></span>
            <span>未解决: <b className={dlq.stats.unresolved ? 'text-red-600' : 'text-green-600'}>{dlq.stats.unresolved}</b></span>
            {dlq.stats.by_event_type && Object.entries(dlq.stats.by_event_type).map(([k, v]) => (
              <span key={k} className="px-1.5 py-0.5 bg-slate-100 rounded font-mono text-[10px]">{k}: {v}</span>
            ))}
          </div>
        )}

        {dlq.items.length === 0 && (
          <div className="text-center text-slate-400 py-8 text-sm">
            <div className="text-2xl mb-1">✓</div>
            <div>{dlqIncludeResolved ? '没有任何死信记录' : '没有未解决的死信'}</div>
          </div>
        )}

        {dlq.items.length > 0 && (
          <div className="space-y-2 max-h-96 overflow-auto">
            {dlq.items.map(item => (
              <div key={item.id} className={`border rounded p-3 text-xs ${item.resolved ? 'bg-green-50/40' : 'bg-red-50/30'}`}>
                <div className="flex items-start gap-2">
                  <span className="px-1.5 py-0.5 bg-slate-700 text-white rounded font-mono">#{item.id}</span>
                  <span className="px-1.5 py-0.5 bg-blue-100 text-blue-700 rounded">{item.event_type}</span>
                  {item.resolved
                    ? <span className="px-1.5 py-0.5 bg-green-100 text-green-700 rounded">resolved</span>
                    : <span className="px-1.5 py-0.5 bg-red-100 text-red-700 rounded">attempts: {item.attempts}</span>}
                  <span className="text-slate-500 ml-auto">{item.created_at}</span>
                </div>
                {item.last_error && (
                  <div className="mt-1.5 font-mono text-[10px] text-red-700 bg-red-50 px-2 py-1 rounded truncate" title={item.last_error}>
                    {item.last_error}
                  </div>
                )}
                <details className="mt-1.5">
                  <summary className="cursor-pointer text-slate-600 select-none">payload</summary>
                  <pre className="text-[10px] bg-slate-50 p-2 rounded mt-1 overflow-auto">{JSON.stringify(item.payload, null, 2)}</pre>
                </details>
                <div className="mt-2 flex items-center gap-2">
                  {!item.resolved && (
                    <button onClick={() => handleDlqRetry(item)} disabled={dlqBusyId === item.id}
                      className="px-3 py-1 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50">
                      🔄 重发
                    </button>
                  )}
                  <button onClick={() => setDlqDeleteTarget(item)} disabled={dlqBusyId === item.id}
                    className="px-3 py-1 bg-slate-200 text-slate-700 rounded hover:bg-slate-300 disabled:opacity-50">
                    删除
                  </button>
                  {item.resolved_at && <span className="text-slate-500 ml-auto">resolved at {item.resolved_at}</span>}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Phase 10B: 危险操作确认弹窗 */}
      <DangerConfirmDialog
        open={testWebhookOpen}
        title="发送 Webhook 测试事件"
        description={`将向已配置的 Webhook 端点发送一条 ${eventType} 测试事件。如未配置 URL 则为 dry_run。`}
        confirmText={VISUAL_DANGER.TEST_WEBHOOK}
        confirmLabel="发送"
        loading={busy}
        onConfirm={doSendTest}
        onClose={() => setTestWebhookOpen(false)}
      />
      <DangerConfirmDialog
        open={!!dlqDeleteTarget}
        title="删除死信"
        description={
          dlqDeleteTarget
            ? `将永久删除死信 #${dlqDeleteTarget.id}（${dlqDeleteTarget.event_type}）。`
            : ''
        }
        confirmText={VISUAL_DANGER.DELETE_DEAD_LETTER}
        confirmLabel="删除"
        loading={dlqBusyId === dlqDeleteTarget?.id}
        onConfirm={doDlqDelete}
        onClose={() => setDlqDeleteTarget(null)}
      />
    </div>
  )
}

// ─────────────────────── 主页面 ───────────────────────
export default function VisualTesting() {
  const [tab, setTab] = useState('baselines')
  const [stats, setStats] = useState(null)
  const [selected, setSelected] = useState('')
  const [refreshKey, setRefreshKey] = useState(0)
  const [toast, setToast] = useState({ msg: '', type: 'info' })

  const showToast = (msg, type = 'info') => {
    setToast({ msg, type })
    setTimeout(() => setToast({ msg: '', type: 'info' }), 3500)
  }

  const loadStats = async () => {
    try {
      const r = await visualAPI.getStats()
      setStats(r.stats)
    } catch { /* ignore */ }
  }
  useEffect(() => { loadStats() }, [refreshKey])

  return (
    <div className="p-6 max-w-[1400px] mx-auto">
      <Toast msg={toast.msg} type={toast.type} onClose={() => setToast({ msg: '', type: 'info' })} />

      <div className="mb-5">
        <h1 className="text-2xl font-bold text-slate-800">视觉测试中心</h1>
        <p className="text-sm text-slate-500 mt-1">管理视觉基线 · 审核视觉差异 · 配置屏蔽区域 / 阈值 / 算法</p>
      </div>

      {/* 统计卡片 */}
      {stats && (
        <div className="grid grid-cols-5 gap-3 mb-5">
          <StatCard title="基线总数" value={stats.total_baselines} color="blue" />
          <StatCard title="待审核" value={stats.pending_review_count} sub="近 7 天失败" color={stats.pending_review_count > 0 ? 'red' : 'green'} />
          <StatCard title="带 mask" value={stats.with_masks} sub="配置了屏蔽区域" color="violet" />
          <StatCard title="使用 SSIM" value={stats.ssim_count} sub="结构相似度" color="amber" />
          <StatCard title="历史批准" value={stats.approved_count} sub="至少批准过 1 次" color="slate" />
        </div>
      )}

      {/* Tabs */}
      <div className="flex border-b mb-4">
        {[
          { key: 'baselines', label: '基线管理', count: stats?.total_baselines },
          { key: 'pending', label: '待审核', count: stats?.pending_review_count, hot: stats?.pending_review_count > 0 },
          { key: 'webhook', label: 'Webhook 通知' },
        ].map(t => (
          <button key={t.key} onClick={() => setTab(t.key)}
            className={`px-4 py-2 text-sm border-b-2 transition ${tab === t.key
                ? 'border-blue-600 text-blue-700 font-semibold'
                : 'border-transparent text-slate-600 hover:text-slate-900'}`}>
            {t.label}
            {t.count !== undefined && (
              <span className={`ml-2 text-xs px-1.5 py-0.5 rounded ${t.hot ? 'bg-red-100 text-red-700' : 'bg-slate-100 text-slate-600'}`}>
                {t.count}
              </span>
            )}
          </button>
        ))}
      </div>

      <div>
        {tab === 'baselines' && (
          <BaselinesTab
            onSelect={setSelected}
            refreshKey={refreshKey}
            showToast={showToast}
          />
        )}
        {tab === 'pending' && (
          <PendingTab
            showToast={showToast}
            onChanged={() => setRefreshKey(k => k + 1)}
          />
        )}
        {tab === 'webhook' && (
          <WebhookTab showToast={showToast} />
        )}
      </div>

      {selected && (
        <BaselineDetail
          baselineId={selected}
          onClose={() => setSelected('')}
          onChanged={() => setRefreshKey(k => k + 1)}
          showToast={showToast}
        />
      )}
    </div>
  )
}
