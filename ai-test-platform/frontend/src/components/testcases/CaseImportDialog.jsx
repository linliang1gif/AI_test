/**
 * P2-9A.2: 统一导入 / 生成用例弹窗
 * 包含: 需求文档 / Swagger 文件 / Swagger URL / YApi / 手动创建 五个 Tab
 */
import ManualCaseForm from './ManualCaseForm'

export default function CaseImportDialog({
  show,
  importTab,
  importError,
  importSuccess,
  importLoading,
  isGenerating,
  generationStep,
  generationProgress,
  uploadFile,
  swaggerFile,
  swaggerUrl,
  swaggerAuthType,
  swaggerToken,
  yapiBase,
  yapiProjectId,
  yapiEmail,
  yapiPassword,
  folderPath,
  selectedProjectId,
  projects,
  // manual form props
  manualFormProps,
  // callbacks
  onTabChange,
  onSetFolderPath,
  onClearError,
  onClearSuccess,
  onClose,
  onNavigate,
  onSetUploadFile,
  onSetSwaggerFile,
  onSetSwaggerUrl,
  onSetSwaggerAuthType,
  onSetSwaggerToken,
  onSetYapiBase,
  onSetYapiProjectId,
  onSetYapiEmail,
  onSetYapiPassword,
  onSetSelectedProjectId,
  onImportRequirement,
  onImportSwaggerFile,
  onImportSwaggerUrl,
  onImportYapi,
}) {
  if (!show) return null

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-xl shadow-2xl w-[680px] max-h-[85vh] overflow-y-auto">
        {/* 标题栏 */}
        <div className="flex items-center justify-between px-6 py-4 border-b">
          <h2 className="text-lg font-bold text-gray-800">导入 / 生成用例</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 text-xl leading-none">&times;</button>
        </div>

        {/* Tab 切换 */}
        <div className="flex border-b px-6 pt-3 gap-1">
          {[
            { key: 'requirement', label: '需求文档' },
            { key: 'swagger_file', label: 'Swagger 文件' },
            { key: 'swagger_url', label: 'Swagger URL' },
            { key: 'yapi', label: 'YApi' },
            { key: 'manual', label: '手动创建' },
          ].map(t => (
            <button
              key={t.key}
              onClick={() => onTabChange(t.key)}
              className={`px-4 py-2 text-sm font-medium rounded-t-lg transition-colors ${
                importTab === t.key
                  ? 'bg-blue-50 text-blue-700 border border-b-0 border-blue-200'
                  : 'text-gray-500 hover:text-gray-700 hover:bg-gray-50'
              }`}
            >{t.label}</button>
          ))}
        </div>

        {/* 错误提示 */}
        {importError && (
          <div className="mx-6 mt-4 p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700 flex items-start gap-2">
            <span className="mt-0.5">⚠️</span>
            <span>{importError}</span>
            <button onClick={onClearError} className="ml-auto text-red-400 hover:text-red-600">&times;</button>
          </div>
        )}

        {/* 成功提示 */}
        {importSuccess && (
          <div className="mx-6 mt-4 p-4 bg-green-50 border border-green-200 rounded-lg text-sm text-green-800">
            <p className="font-medium mb-2">✅ {importSuccess.message ? '操作成功！' : '导入成功！'}</p>
            {importSuccess.message ? (
              <p>{importSuccess.message}</p>
            ) : (
              <p>已生成 <strong>{importSuccess.count}</strong> 条测试用例
                {importSuccess.apiCount ? `，共 ${importSuccess.apiCount} 个接口` : ''}
              </p>
            )}
            {importSuccess.apiSpecId && (
              <p className="mt-1 text-xs text-green-600">API 规范已写入 (ID: {importSuccess.apiSpecId})</p>
            )}
            <div className="flex gap-2 mt-3">
              <button onClick={onClose} className="px-3 py-1.5 text-xs bg-green-600 text-white rounded hover:bg-green-700">
                查看测试用例
              </button>
              {importSuccess.apiSpecId && (
                <button onClick={() => { onClose(); onNavigate('/api-specs') }}
                  className="px-3 py-1.5 text-xs bg-white border border-green-300 text-green-700 rounded hover:bg-green-50">
                  查看 API 规范
                </button>
              )}
            </div>
          </div>
        )}

        {/* Tab 内容 */}
        <div className="px-6 py-5">

          {/* ── 需求文档 Tab ── */}
          {importTab === 'requirement' && !importSuccess && (
            <div>
              <div className="mb-3">
                <label className="block text-sm font-medium text-gray-700 mb-2">方式一：上传需求文档</label>
                <input type="file" accept=".html,.htm,.docx,.xlsx,.pdf,.doc,.xls,.txt,.md"
                  onChange={(e) => onSetUploadFile(e.target.files?.[0] || null)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500" />
                {uploadFile && <p className="mt-1.5 text-sm text-green-600">✓ 已选择: {uploadFile.name}</p>}
              </div>
              <div className="relative my-3 flex items-center">
                <div className="flex-grow border-t border-gray-200"></div>
                <span className="mx-3 text-xs text-gray-400">或</span>
                <div className="flex-grow border-t border-gray-200"></div>
              </div>
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">方式二：Axure 原型文件夹路径</label>
                <input type="text"
                  placeholder="如: G:\需求\付款单-企业小程序_v1.2.3_files"
                  value={typeof folderPath === 'string' ? folderPath : ''}
                  onChange={(e) => onSetFolderPath?.(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 placeholder-gray-400" />
                <p className="mt-1 text-xs text-gray-400">支持 Axure 导出的 _files 文件夹，自动解析 data.js 中的需求注释</p>
              </div>
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 mb-4 text-xs text-blue-800">
                <p className="font-medium mb-1">AI 将自动 <span className="px-1.5 py-0.5 bg-green-100 text-green-700 rounded text-xs ml-1">→ 功能用例</span>：</p>
                <ul className="list-disc list-inside space-y-0.5">
                  <li>解析需求文档 / Axure 原型注释，拆分功能模块</li>
                  <li>结合项目知识库生成测试场景</li>
                  <li>生成完整测试用例（含业务断言）</li>
                </ul>
                <p className="mt-1.5 text-blue-600">⏱️ 预计 1-2 分钟</p>
              </div>
              {isGenerating && (
                <div className="mb-4">
                  <div className="flex justify-between mb-1 text-sm">
                    <span className="text-gray-700">{generationStep}</span>
                    <span className="text-gray-500">{generationProgress}%</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div className="bg-blue-600 h-2 rounded-full transition-all duration-500" style={{ width: `${generationProgress}%` }} />
                  </div>
                </div>
              )}
              <div className="flex justify-end">
                <button onClick={onImportRequirement} disabled={(!uploadFile && !folderPath) || importLoading}
                  className="px-5 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 text-sm flex items-center gap-2">
                  {importLoading ? <><div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" /> AI 生成中...</> : '开始生成'}
                </button>
              </div>
            </div>
          )}

          {/* ── Swagger 文件 Tab ── */}
          {importTab === 'swagger_file' && !importSuccess && (
            <div>
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">上传 Swagger / OpenAPI 文件</label>
                <label className="flex items-center justify-center px-4 py-4 border-2 border-dashed border-gray-300 rounded-lg cursor-pointer hover:border-blue-400 hover:bg-blue-50 transition-colors">
                  <input type="file" accept=".json,.yaml,.yml" className="hidden"
                    onChange={(e) => onSetSwaggerFile(e.target.files?.[0] || null)} />
                  <span className="text-sm text-gray-600">
                    {swaggerFile ? `📄 ${swaggerFile.name} (${(swaggerFile.size/1024).toFixed(1)} KB)` : '点击选择 JSON / YAML 文件'}
                  </span>
                </label>
                {swaggerFile && <button onClick={() => onSetSwaggerFile(null)} className="mt-1 text-xs text-red-500 hover:underline">清除</button>}
                <p className="text-xs text-gray-400 mt-1">支持 Swagger 2.0 / OpenAPI 3.0 格式，导入后写入 API 规范并自动生成 <span className="px-1 py-0.5 bg-blue-100 text-blue-600 rounded">API 接口用例</span></p>
              </div>
              <div className="mb-4">
                <label className="block text-xs text-gray-500 mb-1">目标项目</label>
                <select value={selectedProjectId || projects[0]?.id || ''}
                  onChange={(e) => onSetSelectedProjectId(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500">
                  <option value="">选择项目</option>
                  {projects.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}
                </select>
              </div>
              <div className="flex justify-end">
                <button onClick={onImportSwaggerFile} disabled={!swaggerFile || importLoading}
                  className="px-5 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 text-sm flex items-center gap-2">
                  {importLoading ? <><div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" /> 导入中...</> : '导入并生成用例'}
                </button>
              </div>
            </div>
          )}

          {/* ── Swagger URL Tab ── */}
          {importTab === 'swagger_url' && !importSuccess && (
            <div>
              <div className="mb-3">
                <label className="block text-sm font-medium text-gray-700 mb-1">Swagger / OpenAPI URL</label>
                <input type="text" value={swaggerUrl} onChange={(e) => onSetSwaggerUrl(e.target.value)}
                  placeholder="https://api.example.com/v2/api-docs"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500" />
              </div>
              <div className="grid grid-cols-2 gap-3 mb-3">
                <div>
                  <label className="block text-xs text-gray-500 mb-1">鉴权方式</label>
                  <select value={swaggerAuthType} onChange={(e) => onSetSwaggerAuthType(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm">
                    <option value="none">无鉴权</option>
                    <option value="bearer">Bearer Token</option>
                    <option value="basic">Basic Auth</option>
                  </select>
                </div>
                {swaggerAuthType !== 'none' && (
                  <div>
                    <label className="block text-xs text-gray-500 mb-1">Token</label>
                    <input type="password" value={swaggerToken} onChange={(e) => onSetSwaggerToken(e.target.value)}
                      placeholder="输入鉴权 Token"
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm" />
                  </div>
                )}
              </div>
              <div className="mb-4">
                <label className="block text-xs text-gray-500 mb-1">目标项目</label>
                <select value={selectedProjectId || projects[0]?.id || ''}
                  onChange={(e) => onSetSelectedProjectId(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500">
                  <option value="">选择项目</option>
                  {projects.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}
                </select>
              </div>
              <p className="text-xs text-gray-400 mb-4">导入后写入 API 规范并自动生成 <span className="px-1 py-0.5 bg-blue-100 text-blue-600 rounded">API 接口用例</span>，重复导入会返回 409</p>
              <div className="flex justify-end">
                <button onClick={onImportSwaggerUrl} disabled={!swaggerUrl.trim() || importLoading}
                  className="px-5 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 text-sm flex items-center gap-2">
                  {importLoading ? <><div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" /> 导入中...</> : '导入并生成用例'}
                </button>
              </div>
            </div>
          )}

          {/* ── YApi Tab ── */}
          {importTab === 'yapi' && !importSuccess && (
            <div>
              <div className="grid grid-cols-2 gap-3 mb-3">
                <div>
                  <label className="block text-xs text-gray-500 mb-1">YApi 服务地址</label>
                  <input type="text" value={yapiBase} onChange={(e) => onSetYapiBase(e.target.value)}
                    placeholder="https://yapi.example.com"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm" />
                </div>
                <div>
                  <label className="block text-xs text-gray-500 mb-1">YApi 项目 ID</label>
                  <input type="number" value={yapiProjectId} onChange={(e) => onSetYapiProjectId(e.target.value)}
                    placeholder="123"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm" />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-3 mb-3">
                <div>
                  <label className="block text-xs text-gray-500 mb-1">登录邮箱</label>
                  <input type="email" value={yapiEmail} onChange={(e) => onSetYapiEmail(e.target.value)}
                    placeholder="user@example.com"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm" />
                </div>
                <div>
                  <label className="block text-xs text-gray-500 mb-1">登录密码</label>
                  <input type="password" value={yapiPassword} onChange={(e) => onSetYapiPassword(e.target.value)}
                    placeholder="密码"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm" />
                </div>
              </div>
              <div className="mb-4">
                <label className="block text-xs text-gray-500 mb-1">目标项目</label>
                <select value={selectedProjectId || projects[0]?.id || ''}
                  onChange={(e) => onSetSelectedProjectId(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500">
                  <option value="">选择项目</option>
                  {projects.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}
                </select>
              </div>
              <p className="text-xs text-gray-400 mb-4">YApi → OpenAPI 转换 → 写入 API 规范 → 自动生成 <span className="px-1 py-0.5 bg-blue-100 text-blue-600 rounded">API 接口用例</span></p>
              <div className="flex justify-end">
                <button onClick={onImportYapi} disabled={importLoading}
                  className="px-5 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 text-sm flex items-center gap-2">
                  {importLoading ? <><div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" /> 导入中...</> : '导入并生成用例'}
                </button>
              </div>
            </div>
          )}

          {/* ── 手动创建 Tab ── */}
          {importTab === 'manual' && !importSuccess && (
            <ManualCaseForm {...manualFormProps} />
          )}
        </div>

        {/* 底部关闭 */}
        {!importSuccess && (
          <div className="px-6 py-3 border-t flex justify-between items-center">
            <p className="text-xs text-gray-400">
              {importTab.startsWith('swagger') || importTab === 'yapi' ? 'API 导入会写入 API 规范模块' : ''}
            </p>
            <button onClick={onClose}
              className="px-4 py-2 text-sm border border-gray-300 rounded-lg hover:bg-gray-50">取消</button>
          </div>
        )}
      </div>
    </div>
  )
}
