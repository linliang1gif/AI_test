/**
 * Phase 10B 通用危险操作确认弹窗
 *
 * 与后端 backend/danger_guard.py 配套：
 *   - 后端：check_confirm(required_text, body.confirm, body.confirm_text)
 *   - 前端：用户必须输入 required_text 才能提交，提交时携带
 *           { confirm: true, confirm_text: required_text } 进入业务请求体
 *
 * Props:
 *   open            : boolean        是否显示
 *   title           : string         弹窗标题，如 "删除基线"
 *   description     : string|node    操作说明（可含变量名等危险细节）
 *   confirmText     : string         必须输入的确认文本，如 "DELETE_BASELINE"
 *   confirmLabel    : string         主按钮文案，默认 "确认"
 *   loading         : boolean        提交中（外部控制）
 *   onConfirm       : () => Promise  确认回调（内部传递 {confirm, confirm_text} 由调用方拼装请求）
 *   onClose         : () => void     关闭弹窗
 *   placeholder     : string         输入框占位（默认显示 confirmText）
 *
 * 用法示例（VisualTesting.jsx）：
 *   <DangerConfirmDialog
 *     open={confirmOpen}
 *     title="删除基线"
 *     description={`将永久删除基线 ${baselineId}。`}
 *     confirmText="DELETE_BASELINE"
 *     onConfirm={async () => {
 *       await visualAPI.deleteBaseline(baselineId, {
 *         delete_currents: false, delete_diffs: false,
 *         confirm: true, confirm_text: 'DELETE_BASELINE',
 *       })
 *     }}
 *     onClose={() => setConfirmOpen(false)}
 *   />
 */
import React, { useState, useEffect, useRef } from 'react'

export default function DangerConfirmDialog({
  open,
  title = '危险操作',
  description = '此操作不可撤销，请谨慎确认。',
  confirmText,
  confirmLabel = '确认执行',
  loading = false,
  onConfirm,
  onClose,
  placeholder,
}) {
  const [input, setInput] = useState('')
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const inputRef = useRef(null)

  // 弹窗每次打开时清空状态
  useEffect(() => {
    if (open) {
      setInput('')
      setError('')
      setSubmitting(false)
      // 自动聚焦输入框
      setTimeout(() => inputRef.current?.focus(), 50)
    }
  }, [open])

  if (!open) return null

  const matched = input.trim() === confirmText
  const busy = loading || submitting

  const handleSubmit = async (e) => {
    e?.preventDefault?.()
    if (!matched || busy) return
    setError('')
    setSubmitting(true)
    try {
      await onConfirm?.({ confirm: true, confirm_text: confirmText })
    } catch (err) {
      // 后端 DANGEROUS_OPERATION_CONFIRM_REQUIRED 兜底提示
      const msg = String(err?.message || err || '')
      if (msg.includes('DANGEROUS_OPERATION_CONFIRM_REQUIRED')) {
        setError('危险操作需要确认，请输入指定确认文本。')
      } else {
        setError(msg || '操作失败')
      }
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm"
      onClick={(e) => {
        // 点击背景关闭（提交中除外）
        if (e.target === e.currentTarget && !busy) onClose?.()
      }}
    >
      <form
        onSubmit={handleSubmit}
        className="bg-white rounded-lg shadow-xl border-2 border-red-200 w-full max-w-md mx-4 overflow-hidden"
      >
        {/* 头部 */}
        <div className="bg-red-50 border-b border-red-200 px-5 py-3 flex items-start gap-3">
          <span className="text-red-600 text-xl leading-none mt-0.5">⚠️</span>
          <div className="flex-1">
            <div className="text-base font-semibold text-red-700">{title}</div>
            <div className="text-xs text-red-600/70 mt-0.5">此操作不可撤销</div>
          </div>
        </div>

        {/* 内容 */}
        <div className="px-5 py-4 space-y-3">
          <div className="text-sm text-slate-700 whitespace-pre-line">
            {description}
          </div>

          <div className="text-xs text-slate-600">
            请输入下方文字以确认操作：
          </div>

          <div className="bg-slate-100 border border-slate-200 rounded px-3 py-2 font-mono text-sm font-semibold text-red-700 select-all">
            {confirmText}
          </div>

          <input
            ref={inputRef}
            type="text"
            value={input}
            onChange={(e) => {
              setInput(e.target.value)
              setError('')
            }}
            placeholder={placeholder || confirmText}
            disabled={busy}
            className={`w-full px-3 py-2 text-sm border rounded outline-none transition ${
              matched
                ? 'border-green-400 focus:border-green-500 focus:ring-1 focus:ring-green-300'
                : 'border-slate-300 focus:border-red-400 focus:ring-1 focus:ring-red-300'
            } disabled:bg-slate-100 disabled:cursor-not-allowed`}
            autoComplete="off"
            spellCheck={false}
          />

          {error && (
            <div className="text-xs text-red-600 bg-red-50 border border-red-200 rounded px-3 py-2">
              {error}
            </div>
          )}
        </div>

        {/* 底部按钮 */}
        <div className="bg-slate-50 border-t border-slate-200 px-5 py-3 flex justify-end gap-2">
          <button
            type="button"
            onClick={() => !busy && onClose?.()}
            disabled={busy}
            className="px-4 py-1.5 text-sm bg-white border border-slate-300 text-slate-700 rounded hover:bg-slate-100 disabled:opacity-50"
          >
            取消
          </button>
          <button
            type="submit"
            disabled={!matched || busy}
            className="px-4 py-1.5 text-sm bg-red-600 text-white rounded hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {busy ? '处理中...' : confirmLabel}
          </button>
        </div>
      </form>
    </div>
  )
}
