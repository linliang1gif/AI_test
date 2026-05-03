/**
 * P2-9A.1: 用例详情 / 编辑弹窗
 */
export default function CaseDetailDialog({
  show,
  selectedTestCase,
  isEditing,
  editForm,
  editSaving,
  onClose,
  onEnterEdit,
  onCancelEdit,
  onSave,
  onEditFormChange,
  onEditStepChange,
  onAddStep,
  onRemoveStep,
}) {
  if (!show || !selectedTestCase) return null

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-xl shadow-2xl w-[720px] max-h-[85vh] overflow-y-auto">
        {/* 标题栏 */}
        <div className="flex items-center justify-between px-6 py-4 border-b">
          <h2 className="text-lg font-bold text-gray-800">{isEditing ? '编辑用例' : '用例详情'}</h2>
          <div className="flex items-center gap-2">
            {!isEditing && (
              <button onClick={onEnterEdit}
                className="px-3 py-1.5 text-sm bg-blue-50 text-blue-600 rounded-lg hover:bg-blue-100 transition-colors">
                编辑
              </button>
            )}
            <button onClick={onClose}
              className="text-gray-400 hover:text-gray-600 text-xl leading-none">&times;</button>
          </div>
        </div>

        <div className="px-6 py-5 space-y-4">
          {/* 用例标题 */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">用例标题</label>
            {isEditing ? (
              <input type="text" value={editForm.title} onChange={(e) => onEditFormChange({ title: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500" />
            ) : (
              <div className="p-3 bg-gray-50 rounded-lg border text-sm">
                {selectedTestCase.title?.replace(/^(测试用例标题|测试点|用例标题|标题)[:：]\s*/, '') || selectedTestCase.title}
              </div>
            )}
          </div>

          {/* 模块 + 优先级 */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">模块</label>
              {isEditing ? (
                <input type="text" value={editForm.module} onChange={(e) => onEditFormChange({ module: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500" />
              ) : (
                <div className="p-3 bg-gray-50 rounded-lg border text-sm">{selectedTestCase.module || '-'}</div>
              )}
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">优先级</label>
              {isEditing ? (
                <select value={editForm.priority} onChange={(e) => onEditFormChange({ priority: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500">
                  <option value="high">high</option>
                  <option value="medium">medium</option>
                  <option value="low">low</option>
                </select>
              ) : (
                <div className="p-3 bg-gray-50 rounded-lg border text-sm">{selectedTestCase.priority}</div>
              )}
            </div>
          </div>

          {/* 测试步骤 */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">测试步骤</label>
            {isEditing ? (
              <div className="space-y-2">
                {editForm.steps.map((step, idx) => (
                  <div key={idx} className="flex items-center gap-1">
                    <span className="text-xs text-gray-400 w-5 text-right">{idx + 1}.</span>
                    {typeof step === 'string' ? (
                      <input type="text" value={step} onChange={(e) => onEditStepChange(idx, e.target.value)}
                        className="flex-1 px-3 py-1.5 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500" />
                    ) : (
                      <>
                        <select value={step.action||''} onChange={e=>{const s=[...editForm.steps];s[idx]={...s[idx],action:e.target.value};onEditFormChange({steps:s})}}
                          className="w-20 px-1 py-1.5 border rounded text-xs">
                          {[{v:'goto',l:'打开页面'},{v:'click',l:'点击'},{v:'fill',l:'输入'},{v:'wait_for',l:'等待'},{v:'screenshot',l:'截图'},{v:'hover',l:'悬停'},{v:'select',l:'选择'},{v:'upload',l:'上传'},{v:'press',l:'按键'},{v:'double_click',l:'双击'},{v:'clear',l:'清空'},{v:'scroll',l:'滚动'},{v:'switch_frame',l:'切换iframe'},{v:'switch_main',l:'回到主页'},{v:'eval_js',l:'执行JS'},{v:'save_cookies',l:'保存Cookie'}].map(a=><option key={a.v} value={a.v}>{a.l}</option>)}
                        </select>
                        <input value={step.target||''} onChange={e=>{const s=[...editForm.steps];s[idx]={...s[idx],target:e.target.value};onEditFormChange({steps:s})}}
                          placeholder="选择器" className="flex-1 px-2 py-1.5 border rounded text-xs" />
                        <input value={step.value||''} onChange={e=>{const s=[...editForm.steps];s[idx]={...s[idx],value:e.target.value};onEditFormChange({steps:s})}}
                          placeholder="值" className="w-20 px-2 py-1.5 border rounded text-xs" />
                        <input value={step.description||''} onChange={e=>{const s=[...editForm.steps];s[idx]={...s[idx],description:e.target.value};onEditFormChange({steps:s})}}
                          placeholder="说明" className="w-24 px-2 py-1.5 border rounded text-xs" />
                      </>
                    )}
                    <button onClick={() => onRemoveStep(idx)} className="text-red-400 hover:text-red-600 text-sm px-1">✕</button>
                  </div>
                ))}
                <button onClick={onAddStep} className="text-xs text-blue-600 hover:underline">+ 添加步骤</button>
              </div>
            ) : (
              <div className="p-3 bg-gray-50 rounded-lg border text-sm">
                {selectedTestCase.steps && selectedTestCase.steps.length > 0 ? (
                  <ol className="list-decimal list-inside space-y-1">
                    {selectedTestCase.steps.map((step, index) => (
                      <li key={index} className="text-gray-700">
                        {typeof step === 'string' ? step : (
                          <span>
                            <span className="inline-block px-1.5 py-0.5 bg-violet-100 text-violet-700 rounded text-xs font-mono mr-1">{step.action}</span>
                            {step.target && <code className="text-xs bg-gray-200 px-1 rounded mr-1">{step.target}</code>}
                            {step.value && <span className="text-blue-600 text-xs mr-1">"{step.value}"</span>}
                            {step.description && <span className="text-gray-500 text-xs">— {step.description}</span>}
                          </span>
                        )}
                      </li>
                    ))}
                  </ol>
                ) : (
                  <p className="text-gray-400">暂无测试步骤</p>
                )}
              </div>
            )}
          </div>

          {/* 预期结果 */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">预期结果</label>
            {isEditing ? (
              <textarea value={editForm.expected} onChange={(e) => onEditFormChange({ expected: e.target.value })}
                rows={3} className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500" />
            ) : (
              <div className="p-3 bg-gray-50 rounded-lg border text-sm">{selectedTestCase.expected || '-'}</div>
            )}
          </div>

          {/* 断言 (JSON) */}
          {(isEditing || (selectedTestCase.assertions && selectedTestCase.assertions.length > 0)) && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">断言 (JSON)</label>
              {isEditing ? (
                <textarea value={editForm.assertions}
                  onChange={(e) => onEditFormChange({ assertions: e.target.value })}
                  rows={4} className="w-full px-3 py-2 border border-gray-300 rounded-lg text-xs font-mono focus:ring-2 focus:ring-blue-500"
                  placeholder='[{"type":"status_code","expected":200}]' />
              ) : (
                <pre className="p-3 bg-gray-50 rounded-lg border text-xs font-mono overflow-x-auto max-h-32">
                  {JSON.stringify(selectedTestCase.assertions, null, 2)}
                </pre>
              )}
            </div>
          )}

          {/* 只读信息 */}
          {!isEditing && (
            <div className="grid grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">状态</label>
                <div className="p-3 bg-gray-50 rounded-lg border text-sm">{selectedTestCase.status || '-'}</div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">最后运行</label>
                <div className="p-3 bg-gray-50 rounded-lg border text-sm">{selectedTestCase.lastRun || '-'}</div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">来源</label>
                <div className="p-3 bg-gray-50 rounded-lg border text-sm">{selectedTestCase.source || '-'}</div>
              </div>
            </div>
          )}

          {/* Web UI 专属信息 */}
          {!isEditing && selectedTestCase.case_type === 'web_ui' && (
            <div className="space-y-3">
              <div className="flex items-center gap-2">
                <span className="px-2 py-1 bg-violet-100 text-violet-700 rounded text-xs font-medium">Web UI 用例</span>
                {selectedTestCase.execution_config?.browser && (
                  <span className="px-2 py-1 bg-blue-50 text-blue-600 rounded text-xs">{selectedTestCase.execution_config.browser}</span>
                )}
                {selectedTestCase.execution_config?.base_url && (
                  <span className="px-2 py-1 bg-gray-100 text-gray-600 rounded text-xs font-mono">{selectedTestCase.execution_config.base_url}</span>
                )}
              </div>
              {selectedTestCase.execution_config && (
                <details>
                  <summary className="text-sm font-medium text-gray-700 cursor-pointer">执行配置</summary>
                  <pre className="mt-1 p-3 bg-gray-50 rounded-lg border text-xs font-mono overflow-x-auto">
                    {JSON.stringify(selectedTestCase.execution_config, null, 2)}
                  </pre>
                </details>
              )}
            </div>
          )}
        </div>

        {/* 底部操作 */}
        <div className="px-6 py-4 border-t flex justify-end gap-3">
          {isEditing ? (
            <>
              <button onClick={onCancelEdit} disabled={editSaving}
                className="px-4 py-2 text-sm border border-gray-300 rounded-lg hover:bg-gray-50">取消编辑</button>
              <button onClick={onSave} disabled={editSaving}
                className="px-5 py-2 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 flex items-center gap-2">
                {editSaving ? <><div className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" /> 保存中...</> : '保存'}
              </button>
            </>
          ) : (
            <button onClick={onClose}
              className="px-4 py-2 text-sm border border-gray-300 rounded-lg hover:bg-gray-50">关闭</button>
          )}
        </div>
      </div>
    </div>
  )
}
