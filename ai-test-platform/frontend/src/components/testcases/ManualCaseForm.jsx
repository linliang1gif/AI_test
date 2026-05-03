/**
 * P2-9A.2: 手动创建用例表单（功能 / API / Web UI）
 * Web UI 表单含页面扫描器、快捷模板、步骤断言编辑
 */
import WebUICaseForm from './WebUICaseForm'

export default function ManualCaseForm({
  manualCaseType,
  manualTitle,
  manualModule,
  manualPriority,
  manualSteps,
  manualExpected,
  importLoading,
  // Web UI props pass-through
  webUiProps,
  // callbacks
  onSetManualCaseType,
  onSetManualTitle,
  onSetManualModule,
  onSetManualPriority,
  onSetManualSteps,
  onSetManualExpected,
  onManualCreate,
}) {
  return (
    <div className="space-y-3" style={{maxHeight:'60vh',overflowY:'auto'}}>
      {/* 用例类型选择 */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">用例类型</label>
        <div className="flex gap-2">
          {[{k:'functional',l:'功能用例'},{k:'api',l:'API用例'},{k:'web_ui',l:'Web UI用例'}].map(t=>(
            <button key={t.k} onClick={()=>onSetManualCaseType(t.k)}
              className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${manualCaseType===t.k?'bg-blue-600 text-white':'bg-gray-100 text-gray-600 hover:bg-gray-200'}`}>{t.l}</button>
          ))}
        </div>
      </div>
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">用例标题 <span className="text-red-500">*</span></label>
        <input type="text" value={manualTitle} onChange={e => onSetManualTitle(e.target.value)}
          placeholder={manualCaseType==='web_ui'?"例: 用户登录流程 - 正常登录":"例: 用户登录 - 正确的用户名密码"}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
      </div>
      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">模块</label>
          <input type="text" value={manualModule} onChange={e => onSetManualModule(e.target.value)}
            placeholder="例: 用户管理"
            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">优先级</label>
          <select value={manualPriority} onChange={e => onSetManualPriority(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500">
            <option value="critical">Critical</option>
            <option value="high">High</option>
            <option value="medium">Medium</option>
            <option value="low">Low</option>
          </select>
        </div>
      </div>

      {/* Web UI 专用表单 */}
      {manualCaseType === 'web_ui' && (
        <WebUICaseForm {...webUiProps} />
      )}

      {/* 功能/API 用例步骤 */}
      {manualCaseType !== 'web_ui' && (
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">测试步骤</label>
          {manualSteps.map((step, idx) => (
            <div key={idx} className="flex items-center gap-2 mb-1">
              <span className="text-xs text-gray-400 w-5">{idx + 1}.</span>
              <input type="text" value={step}
                onChange={e => { const s = [...manualSteps]; s[idx] = e.target.value; onSetManualSteps(s) }}
                placeholder={`步骤 ${idx + 1}`}
                className="flex-1 px-3 py-1.5 border border-gray-300 rounded text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
              {manualSteps.length > 1 && (
                <button onClick={() => onSetManualSteps(manualSteps.filter((_, i) => i !== idx))}
                  className="text-red-400 hover:text-red-600 text-xs">✕</button>
              )}
            </div>
          ))}
          <button onClick={() => onSetManualSteps([...manualSteps, ''])}
            className="text-xs text-blue-500 hover:underline mt-1">+ 添加步骤</button>
        </div>
      )}

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">预期结果</label>
        <textarea value={manualExpected} onChange={e => onSetManualExpected(e.target.value)}
          rows={2} placeholder="例: 登录成功，跳转到首页"
          className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
      </div>
      <button onClick={onManualCreate} disabled={importLoading || !manualTitle.trim()}
        className="w-full py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors">
        {importLoading ? '创建中...' : '创建用例'}
      </button>
    </div>
  )
}
