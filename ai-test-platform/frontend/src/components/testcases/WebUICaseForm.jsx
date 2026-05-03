/**
 * P2-9A.2: Web UI 用例表单
 * 包含: 登录会话、页面扫描器(实验功能/默认折叠)、快捷模板、步骤/断言编辑
 */
export default function WebUICaseForm({
  // login session
  loginSession,
  useSession,
  webUiNeedLogin,
  webUiLoginMerchant,
  webUiLoginUser,
  webUiLoginPass,
  sessionSaving,
  // scanner
  scannerExpanded,
  scanUrl,
  scanLoading,
  scanResult,
  aiAvailable,
  // steps & assertions
  webUiSteps,
  webUiAssertions,
  webUiBaseUrl,
  // env context
  selectedProjectId,
  selectedEnvironmentId,
  environments,
  // callbacks
  onSetUseSession,
  onSetWebUiNeedLogin,
  onSetWebUiLoginMerchant,
  onSetWebUiLoginUser,
  onSetWebUiLoginPass,
  onSaveLoginSession,
  onDeleteLoginSession,
  onSetScannerExpanded,
  onSetScanUrl,
  onScanPage,
  onAiGenerate,
  onAddScanElement,
  onSetWebUiSteps,
  onSetWebUiAssertions,
  onSetWebUiBaseUrl,
  onSetManualTitle,
  onSetManualModule,
  onSetImportError,
  onSetImportSuccess,
  // quick templates
  onApplyTemplate,
  onQuickPageTest,
}) {
  return (<>
    {/* P2-7.3: Section 2 - 执行配置 */}
    <div className="text-xs font-semibold text-gray-500 uppercase tracking-wider mt-2 mb-1 flex items-center gap-2">
      <div className="h-px flex-1 bg-gray-200" /><span>执行配置</span><div className="h-px flex-1 bg-gray-200" />
    </div>
    {/* 登录 & 会话管理 */}
    <div className={`p-3 rounded-lg border ${webUiNeedLogin || useSession ? 'bg-amber-50 border-amber-200' : 'bg-gray-50 border-gray-200'}`}>
      <div className="flex items-center gap-4 flex-wrap">
        {loginSession?.has_session ? (
          <label className="flex items-center gap-2 cursor-pointer">
            <input type="checkbox" checked={useSession} onChange={e=>{onSetUseSession(e.target.checked);if(e.target.checked)onSetWebUiNeedLogin(false)}}
              className="w-4 h-4 accent-green-500" />
            <span className="text-sm font-medium text-green-700">使用已保存的登录</span>
            <span className="text-xs text-gray-400">({loginSession.page_title || '已登录'}, {new Date(loginSession.saved_at).toLocaleString()})</span>
            <button onClick={onDeleteLoginSession} className="text-xs text-red-400 hover:underline ml-1">清除</button>
          </label>
        ) : (
          <label className="flex items-center gap-2 cursor-pointer">
            <input type="checkbox" checked={webUiNeedLogin} onChange={e=>{onSetWebUiNeedLogin(e.target.checked);if(e.target.checked)onSetUseSession(false)}}
              className="w-4 h-4 accent-amber-500" />
            <span className="text-sm font-medium text-gray-700">需要先登录</span>
            <span className="text-xs text-gray-400">勾选后自动在测试前登录</span>
          </label>
        )}
      </div>
      {webUiNeedLogin && (
        <div className="mt-2">
          <div className="grid grid-cols-3 gap-2">
            <input type="text" value={webUiLoginMerchant} onChange={e=>onSetWebUiLoginMerchant(e.target.value)}
              placeholder="商户号" className="px-2 py-1.5 border rounded text-sm" />
            <input type="text" value={webUiLoginUser} onChange={e=>onSetWebUiLoginUser(e.target.value)}
              placeholder="账号" className="px-2 py-1.5 border rounded text-sm" />
            <input type="password" value={webUiLoginPass} onChange={e=>onSetWebUiLoginPass(e.target.value)}
              placeholder="密码" className="px-2 py-1.5 border rounded text-sm" />
          </div>
          {selectedProjectId && webUiLoginMerchant && webUiLoginUser && webUiLoginPass && (
            <button disabled={sessionSaving} onClick={onSaveLoginSession}
              className="mt-2 px-3 py-1.5 bg-amber-500 text-white rounded text-xs hover:bg-amber-600 disabled:opacity-50">
              {sessionSaving ? '正在登录...' : '保存登录会话(后续测试免登录)'}
            </button>
          )}
        </div>
      )}
    </div>

    {/* P2-7.3: Section 4 - 高级能力 */}
    <div className="text-xs font-semibold text-gray-500 uppercase tracking-wider mt-2 mb-1 flex items-center gap-2">
      <div className="h-px flex-1 bg-gray-200" /><span>高级能力</span><div className="h-px flex-1 bg-gray-200" />
    </div>
    {/* P2-7.3: 页面扫描器 — 折叠 + 实验标记 */}
    <details open={scannerExpanded} onToggle={e => onSetScannerExpanded(e.currentTarget.open)}
      className="rounded-lg border border-blue-200 bg-blue-50 overflow-hidden">
      <summary className="px-3 py-2.5 cursor-pointer select-none text-sm font-medium text-blue-700 flex items-center gap-2 hover:bg-blue-100 transition-colors">
        <span className="text-xs text-blue-400">{scannerExpanded ? '▼' : '▶'}</span>
        页面扫描器
        <span className="px-1.5 py-0.5 bg-yellow-100 text-yellow-700 rounded text-xs font-normal">实验功能</span>
        <span className="text-xs font-normal text-blue-400 ml-1">— 扫描页面找到所有可操作元素，点击添加为步骤</span>
      </summary>
    <div className="p-3 border-t border-blue-200">
      <div className="flex gap-2 items-center">
        <input type="text" value={scanUrl} onChange={e=>onSetScanUrl(e.target.value)}
          placeholder="输入完整URL，如: https://dev-recycle.szhibu.com/index"
          className="flex-1 px-3 py-2 border border-blue-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
        <button disabled={scanLoading} onClick={onScanPage}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700 disabled:opacity-50 whitespace-nowrap">
          {scanLoading ? '扫描中...' : '扫描页面'}
        </button>
      </div>
      {scanResult && (
        <div className="mt-3">
          {scanResult.screenshot_url && (
            <div className="mb-2">
              <img src={scanResult.screenshot_url} alt="页面截图" className="w-full rounded border max-h-48 object-cover object-top" />
              <p className="text-xs text-gray-500 mt-1">{scanResult.page_title} - {scanResult.page_url}</p>
            </div>
          )}
          <div className="flex items-center gap-2 mb-2 flex-wrap">
            <span className="text-xs text-gray-600">找到 {scanResult.element_count || 0} 个可交互元素</span>
            <button disabled={scanLoading || !aiAvailable} title={!aiAvailable ? 'AI 服务不可用 (AI_PROVIDER=none)' : ''} onClick={onAiGenerate}
              className={`px-3 py-1 rounded text-xs disabled:opacity-50 ${aiAvailable ? 'bg-gradient-to-r from-purple-600 to-blue-600 text-white hover:from-purple-700 hover:to-blue-700' : 'bg-gray-300 text-gray-500 cursor-not-allowed'}`}>
              {scanLoading ? 'AI 生成中...' : !aiAvailable ? '🧪 AI 智能生成用例 (不可用)' : '🧪 AI 智能生成用例'}
            </button>
            <span className="text-xs text-gray-400">或点击下方元素手动添加</span>
          </div>
          <div className="max-h-52 overflow-y-auto space-y-1">
            {(scanResult.elements||[]).map((el,i)=>(
              <div key={i} onClick={()=>onAddScanElement(el)}
                className="flex items-center gap-2 p-1.5 bg-white rounded border hover:bg-blue-50 cursor-pointer text-xs">
                <span className={`px-1.5 py-0.5 rounded text-white text-xs ${
                  el.type==='button'?'bg-green-500':el.type==='input'?'bg-orange-500':el.type==='link'?'bg-blue-500':el.type==='select'?'bg-purple-500':'bg-gray-500'
                }`}>{el.type==='button'?'按钮':el.type==='input'?'输入':el.type==='link'?'链接':el.type==='select'?'下拉':el.type==='checkbox'?'勾选':el.type}</span>
                <span className="flex-1 truncate">{el.label || '(无文字)'}</span>
                <code className="text-gray-400 truncate max-w-[200px]">{el.selector}</code>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
    </details>

    {/* 快速页面测试 */}
    <div className="p-3 bg-violet-50 border border-violet-200 rounded-lg">
      <label className="block text-sm font-medium text-violet-700 mb-2">快速测试 <span className="text-xs font-normal text-violet-500">— 填路径即可生成用例{webUiNeedLogin ? '(含自动登录)' : ''}</span></label>
      <div className="flex gap-2 items-center">
        <span className="text-xs text-gray-500 whitespace-nowrap">{(()=>{
          const env = environments.find(e=>String(e.id)===String(selectedEnvironmentId))
          return env?.base_url ? new URL(env.base_url).origin : 'https://...'
        })()}</span>
        <input id="quickPath" type="text" placeholder="页面路径，如: /index  /order/list  /user/profile"
          className="flex-1 px-3 py-2 border border-violet-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-violet-500" />
        <button onClick={onQuickPageTest}
          className="px-4 py-2 bg-violet-600 text-white rounded-lg text-sm hover:bg-violet-700 whitespace-nowrap">
          生成用例
        </button>
      </div>
    </div>

    {/* 快捷模板 */}
    <div>
      <label className="block text-sm font-medium text-gray-700 mb-1">快捷模板 <span className="text-xs text-gray-400 font-normal">点击自动填充步骤</span></label>
      <div className="flex flex-wrap gap-2">
        {[
          {l:'页面访问',m:'UI测试',steps:[{action:'goto',target:'/',value:'',description:'打开首页'},{action:'wait_for',target:'2000',value:'',description:'等待加载'},{action:'screenshot',target:'',value:'',description:'截图'}],asserts:[{type:'element_visible',target:'body',value:'',description:'页面正常'}]},
          {l:'菜单导航',m:'UI测试',steps:[{action:'goto',target:'/',value:'',description:'进入首页'},{action:'wait_for',target:'2000',value:'',description:'等待加载'},{action:'click',target:'.menu-item, .nav-link, .sidebar a',value:'',description:'点击菜单项(改成实际选择器)'},{action:'wait_for',target:'2000',value:'',description:'等待页面'},{action:'screenshot',target:'',value:'',description:'截图'}],asserts:[{type:'element_visible',target:'body',value:'',description:'页面正常'}]},
          {l:'列表搜索',m:'业务测试',steps:[{action:'goto',target:'/list',value:'',description:'打开列表页(改路径)'},{action:'wait_for',target:'2000',value:'',description:'等待加载'},{action:'fill',target:'input[placeholder*=搜索], input[placeholder*=查询], .search-input',value:'测试',description:'输入搜索词'},{action:'click',target:'button.search, .btn-search, button[type=submit]',value:'',description:'点击搜索'},{action:'wait_for',target:'2000',value:'',description:'等待结果'},{action:'screenshot',target:'',value:'',description:'截图'}],asserts:[{type:'element_visible',target:'table, .list, .el-table',value:'',description:'列表可见'}]},
          {l:'新增表单',m:'业务测试',steps:[{action:'goto',target:'/add',value:'',description:'打开新增页(改路径)'},{action:'wait_for',target:'2000',value:'',description:'等待加载'},{action:'fill',target:'input[name=name], .el-input__inner',value:'测试数据',description:'填写字段(改选择器)'},{action:'screenshot',target:'',value:'',description:'填写后截图'},{action:'click',target:'button[type=submit], .btn-save, .el-button--primary',value:'',description:'点击保存'},{action:'wait_for',target:'2000',value:'',description:'等待响应'},{action:'screenshot',target:'',value:'',description:'结果截图'}],asserts:[{type:'text_visible',target:'',value:'成功',description:'提交成功'}]},
          {l:'详情查看',m:'业务测试',steps:[{action:'goto',target:'/list',value:'',description:'打开列表页(改路径)'},{action:'wait_for',target:'2000',value:'',description:'等待加载'},{action:'click',target:'table tr:first-child a, .list-item:first-child',value:'',description:'点击第一条(改选择器)'},{action:'wait_for',target:'2000',value:'',description:'等待详情'},{action:'screenshot',target:'',value:'',description:'截图'}],asserts:[{type:'element_visible',target:'body',value:'',description:'详情可见'}]},
          {l:'删除确认',m:'业务测试',steps:[{action:'goto',target:'/list',value:'',description:'打开列表页(改路径)'},{action:'wait_for',target:'2000',value:'',description:'等待加载'},{action:'click',target:'.btn-delete, .delete-btn',value:'',description:'点击删除(改选择器)'},{action:'wait_for',target:'1000',value:'',description:'等待弹窗'},{action:'screenshot',target:'',value:'',description:'弹窗截图'},{action:'click',target:'.el-button--primary, button.confirm, .btn-ok',value:'',description:'确认删除'},{action:'wait_for',target:'2000',value:'',description:'等待响应'},{action:'screenshot',target:'',value:'',description:'结果截图'}],asserts:[{type:'text_visible',target:'',value:'成功',description:'删除成功'}]},
        ].map((tpl,i)=>(
          <button key={i} onClick={()=>onApplyTemplate(tpl)}
            className="px-3 py-1.5 text-xs bg-violet-50 text-violet-600 rounded-lg hover:bg-violet-100 border border-violet-200">{tpl.l}</button>
        ))}
      </div>
    </div>

    {/* 基础 URL */}
    <div>
      <label className="block text-sm font-medium text-gray-700 mb-1">
        页面基础 URL
        {selectedEnvironmentId && !webUiBaseUrl && (
          <button onClick={()=>{
            const env = environments.find(e=>String(e.id)===String(selectedEnvironmentId))
            if(env?.base_url) { try { onSetWebUiBaseUrl(new URL(env.base_url).origin) } catch { onSetWebUiBaseUrl(env.base_url.replace(/\/+$/,'')) } }
          }} className="ml-2 text-xs text-violet-500 hover:underline font-normal">从环境自动填入</button>
        )}
      </label>
      <input type="text" value={webUiBaseUrl} onChange={e=>onSetWebUiBaseUrl(e.target.value)}
        placeholder={(() => { const env = environments.find(e=>String(e.id)===String(selectedEnvironmentId)); return env?.base_url || 'https://your-site.com' })()}
        className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
    </div>

    {/* P2-7.3: Section 3 - 步骤与断言 */}
    <div className="text-xs font-semibold text-gray-500 uppercase tracking-wider mt-2 mb-1 flex items-center gap-2">
      <div className="h-px flex-1 bg-gray-200" /><span>步骤与断言</span><div className="h-px flex-1 bg-gray-200" />
    </div>
    {/* 步骤编辑 */}
    <div>
      <label className="block text-sm font-medium text-gray-700 mb-1">
        操作步骤
        {webUiNeedLogin && <span className="text-xs text-amber-500 font-normal ml-2">登录步骤会自动添加到前面</span>}
      </label>
      {webUiSteps.map((step,idx)=>(
        <div key={idx} className="flex items-center gap-1 mb-1.5 p-1.5 bg-gray-50 rounded">
          <span className="text-xs text-gray-400 w-5 text-center">{idx+1}</span>
          <select value={step.action} onChange={e=>{const s=[...webUiSteps];s[idx]={...s[idx],action:e.target.value};onSetWebUiSteps(s)}}
            className="w-24 px-1.5 py-1.5 border rounded text-xs bg-white">
            {[{v:'goto',l:'打开页面'},{v:'click',l:'点击'},{v:'fill',l:'输入'},{v:'wait_for',l:'等待'},{v:'screenshot',l:'截图'},{v:'hover',l:'悬停'},{v:'select',l:'选择'},{v:'upload',l:'上传'},{v:'press',l:'按键'},{v:'double_click',l:'双击'},{v:'clear',l:'清空'},{v:'scroll',l:'滚动'},{v:'switch_frame',l:'切换iframe'},{v:'switch_main',l:'回到主页'},{v:'eval_js',l:'执行JS'},{v:'save_cookies',l:'保存Cookie'}].map(a=><option key={a.v} value={a.v}>{a.l}</option>)}
          </select>
          {step.action !== 'screenshot' && (
            <input value={step.target} onChange={e=>{const s=[...webUiSteps];s[idx]={...s[idx],target:e.target.value};onSetWebUiSteps(s)}}
              placeholder={step.action==='goto'?'页面路径 如 /index':step.action==='wait_for'?'毫秒数 如 2000 或 CSS选择器':'CSS选择器 如 button.login'}
              className="flex-1 px-2 py-1.5 border rounded text-xs" />
          )}
          {step.action === 'fill' && (
            <input value={step.value} onChange={e=>{const s=[...webUiSteps];s[idx]={...s[idx],value:e.target.value};onSetWebUiSteps(s)}}
              placeholder="要输入的值" className="w-28 px-2 py-1.5 border rounded text-xs" />
          )}
          {step.action === 'screenshot' && <span className="flex-1 text-xs text-gray-400 px-2">自动截取当前页面</span>}
          <input value={step.description} onChange={e=>{const s=[...webUiSteps];s[idx]={...s[idx],description:e.target.value};onSetWebUiSteps(s)}}
            placeholder="说明(可选)" className="w-24 px-2 py-1.5 border rounded text-xs" />
          {webUiSteps.length>1&&<button onClick={()=>onSetWebUiSteps(webUiSteps.filter((_,i)=>i!==idx))} className="text-red-400 hover:text-red-600 text-sm px-1">x</button>}
        </div>
      ))}
      <div className="flex gap-2 mt-1">
        <button onClick={()=>onSetWebUiSteps([...webUiSteps,{action:'click',target:'',value:'',description:''}])}
          className="text-xs text-blue-500 hover:underline">+ 添加步骤</button>
        <button onClick={()=>onSetWebUiSteps([...webUiSteps,{action:'screenshot',target:'',value:'',description:'截图'}])}
          className="text-xs text-violet-500 hover:underline">+ 添加截图</button>
      </div>
    </div>
    {/* 断言编辑 */}
    <div>
      <label className="block text-sm font-medium text-gray-700 mb-1">断言 <span className="text-xs text-gray-400 font-normal">(可选)</span></label>
      {webUiAssertions.map((a,idx)=>(
        <div key={idx} className="flex items-center gap-1 mb-1.5 p-1.5 bg-gray-50 rounded">
          <span className="text-xs text-gray-400 w-5 text-center">{idx+1}</span>
          <select value={a.type} onChange={e=>{const arr=[...webUiAssertions];arr[idx]={...arr[idx],type:e.target.value};onSetWebUiAssertions(arr)}}
            className="w-32 px-1.5 py-1.5 border rounded text-xs bg-white">
            {[{v:'url_contains',l:'URL 包含'},{v:'url_not_contains',l:'URL 不包含'},{v:'text_visible',l:'文字可见'},{v:'element_visible',l:'元素可见'},{v:'element_count',l:'元素数量'},{v:'screenshot_match',l:'📸 视觉对比'}].map(t=><option key={t.v} value={t.v}>{t.l}</option>)}
          </select>
          {a.type==='screenshot_match' ? (<>
            <input value={a.name||''} onChange={e=>{const arr=[...webUiAssertions];arr[idx]={...arr[idx],name:e.target.value};onSetWebUiAssertions(arr)}}
              placeholder="基准图名称 如 login_page" className="flex-1 px-2 py-1.5 border rounded text-xs" />
            <input type="number" step="0.01" min="0" max="1" value={a.threshold??0.05} onChange={e=>{const arr=[...webUiAssertions];arr[idx]={...arr[idx],threshold:parseFloat(e.target.value)||0.05};onSetWebUiAssertions(arr)}}
              className="w-16 px-2 py-1.5 border rounded text-xs" title="阈值(0~1)" />
          </>) : (
          <input value={a.value || a.target} onChange={e=>{
            const arr=[...webUiAssertions]
            if(a.type==='element_visible') arr[idx]={...arr[idx],target:e.target.value,value:''}
            else arr[idx]={...arr[idx],value:e.target.value,target:''}
            onSetWebUiAssertions(arr)
          }}
            placeholder={a.type==='url_contains'?'URL 关键词 如 /index':a.type==='text_visible'?'页面上要看到的文字':'CSS 选择器 如 #app'}
            className="flex-1 px-2 py-1.5 border rounded text-xs" />
          )}
          <input value={a.description} onChange={e=>{const arr=[...webUiAssertions];arr[idx]={...arr[idx],description:e.target.value};onSetWebUiAssertions(arr)}}
            placeholder="说明(可选)" className="w-24 px-2 py-1.5 border rounded text-xs" />
          {webUiAssertions.length>1&&<button onClick={()=>onSetWebUiAssertions(webUiAssertions.filter((_,i)=>i!==idx))} className="text-red-400 hover:text-red-600 text-sm px-1">x</button>}
        </div>
      ))}
      <button onClick={()=>onSetWebUiAssertions([...webUiAssertions,{type:'text_visible',target:'',value:'',description:''}])}
        className="text-xs text-blue-500 hover:underline mt-1">+ 添加断言</button>
    </div>
  </>)
}
