import { useState, useEffect, useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../services/api'

const PATTERN_LABEL = { page: '分页查询', list: '列表', detail: '详情', save: '新增', update: '修改', delete: '删除', export: '导出', import: '导入', other: '其他' }
const PATTERN_COLOR = { page: 'bg-blue-100 text-blue-700', list: 'bg-cyan-100 text-cyan-700', detail: 'bg-green-100 text-green-700', save: 'bg-amber-100 text-amber-700', update: 'bg-orange-100 text-orange-700', delete: 'bg-red-100 text-red-700', other: 'bg-gray-100 text-gray-700' }

export default function SwaggerWorkbench() {
  const navigate = useNavigate()

  const [projects, setProjects] = useState([])
  const [selectedProject, setSelectedProject] = useState(null)
  const [sourceType, setSourceType] = useState('yapi')
  const [swaggerUrl, setSwaggerUrl] = useState('https://dev-recycle.szhibu.com/dev-api/recycle/v2/api-docs')
  const [swaggerFile, setSwaggerFile] = useState(null)
  const [yapiBaseUrl, setYapiBaseUrl] = useState('')
  const [yapiToken, setYapiToken] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  // 预览数据
  const [preview, setPreview] = useState(null)
  const [selectedIds, setSelectedIds] = useState(new Set())
  const [tagFilter, setTagFilter] = useState('all')
  const [patternFilter, setPatternFilter] = useState('all')
  const [searchTerm, setSearchTerm] = useState('')

  // 导入状态
  const [importing, setImporting] = useState(false)
  const [importResult, setImportResult] = useState(null)
  const [customBaseUrl, setCustomBaseUrl] = useState('')

  useEffect(() => { loadProjects() }, [])

  const loadProjects = async () => {
    try {
      const response = await api.v2.projects.getAll()
      const list = response.projects || response || []
      setProjects(list)
      if (list.length > 0) setSelectedProject(list[0].id)
    } catch (err) {
      setError('加载项目列表失败: ' + err.message)
    }
  }

  // 步骤 1: 解析预览
  const handlePreview = async () => {
    if (sourceType === 'url' && !swaggerUrl) { setError('请输入 Swagger URL'); return }
    if (sourceType === 'yapi' && !yapiBaseUrl) { setError('请输入 YApi 服务地址或完整模板 URL'); return }
    if (sourceType === 'yapi' && !yapiToken) { setError('请输入 YApi 项目 token'); return }
    if (sourceType === 'file' && !swaggerFile) { setError('请选择 Swagger/OpenAPI 文件'); return }
    setLoading(true); setError(null); setPreview(null); setImportResult(null)
    try {
      let res
      if (sourceType === 'file') {
        const formData = new FormData()
        formData.append('file', swaggerFile)
        formData.append('project_id', selectedProject || 1)
        res = await fetch('/api/v2/swagger/preview-file', { method: 'POST', body: formData })
      } else {
        const endpoint = sourceType === 'yapi' ? '/api/v2/swagger/preview-yapi' : '/api/v2/swagger/preview-url'
        const payload = sourceType === 'yapi'
          ? { project_id: selectedProject || 1, yapi_base_url: yapiBaseUrl, token: yapiToken }
          : { project_id: selectedProject || 1, url: swaggerUrl, generate_cases: true }
        res = await fetch(endpoint, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        })
      }
      if (!res.ok) { const err = await res.json(); throw new Error(err.detail || res.statusText) }
      const data = await res.json()
      setPreview(data)
      setCustomBaseUrl(data.base_url || '')
      // 默认全选 page/list/detail
      const defaultSelected = new Set()
      ;(data.cases || []).forEach((c, i) => {
        const p = detectPattern(c.path)
        if (['page', 'list', 'detail'].includes(p)) defaultSelected.add(i)
      })
      setSelectedIds(defaultSelected)
    } catch (err) {
      setError('解析失败: ' + err.message)
    } finally {
      setLoading(false)
    }
  }

  function detectPattern(path) {
    if (/\/page$/.test(path)) return 'page'
    if (/\/list$/.test(path)) return 'list'
    if (/\/(detail|get|info|query)$/i.test(path)) return 'detail'
    if (/\/(save|add|create|insert)$/i.test(path)) return 'save'
    if (/\/(update|edit|modify)$/i.test(path)) return 'update'
    if (/\/(delete|remove)$/i.test(path)) return 'delete'
    if (/\/(export|download)/i.test(path)) return 'export'
    if (/\/(import|upload)/i.test(path)) return 'import'
    return 'other'
  }

  // 过滤后的用例列表
  const filteredCases = useMemo(() => {
    if (!preview?.cases) return []
    return preview.cases.map((c, i) => ({ ...c, _idx: i })).filter(c => {
      if (tagFilter !== 'all') {
        const tag = c.title?.match(/^\[([^\]]+)\]/)?.[1] || ''
        if (tag !== tagFilter) return false
      }
      if (patternFilter !== 'all') {
        if (detectPattern(c.path) !== patternFilter) return false
      }
      if (searchTerm) {
        const q = searchTerm.toLowerCase()
        if (!c.title?.toLowerCase().includes(q) && !c.path?.toLowerCase().includes(q)) return false
      }
      return true
    })
  }, [preview, tagFilter, patternFilter, searchTerm])

  // 选择操作
  const toggleSelect = (idx) => {
    const s = new Set(selectedIds)
    s.has(idx) ? s.delete(idx) : s.add(idx)
    setSelectedIds(s)
  }
  const selectAll = () => {
    const s = new Set(selectedIds)
    filteredCases.forEach(c => s.add(c._idx))
    setSelectedIds(s)
  }
  const deselectAll = () => {
    const s = new Set(selectedIds)
    filteredCases.forEach(c => s.delete(c._idx))
    setSelectedIds(s)
  }
  const selectByPattern = (pattern) => {
    const s = new Set(selectedIds)
    ;(preview?.cases || []).forEach((c, i) => {
      if (detectPattern(c.path) === pattern) s.add(i)
    })
    setSelectedIds(s)
  }

  // 步骤 2: 批量导入选中用例
  const handleImport = async () => {
    if (!selectedProject) { setError('请先选择项目'); return }
    if (selectedIds.size === 0) { setError('请至少选择一个用例'); return }
    setImporting(true); setError(null)
    const casesToImport = (preview?.cases || []).filter((_, i) => selectedIds.has(i))
    try {
      const finalBaseUrl = customBaseUrl.trim() || preview?.base_url || ''
      if (!finalBaseUrl) {
        setError('请填写 API 服务地址 (base_url)，否则导入的用例无法执行。示例: https://api.example.com')
        setImporting(false)
        return
      }
      const res = await fetch('/api/v2/swagger/batch-import', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          project_id: selectedProject,
          base_url: finalBaseUrl,
          cases: casesToImport,
        }),
      })
      if (!res.ok) { const err = await res.json(); throw new Error(err.detail || res.statusText) }
      const data = await res.json()
      setImportResult(data)
    } catch (err) {
      setError('导入失败: ' + err.message)
    } finally {
      setImporting(false)
    }
  }

  // 步骤 3: 执行
  const handleExecute = async () => {
    if (!importResult?.case_ids?.length) return
    try {
      const res = await fetch('/api/v2/execution/trigger', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          case_ids: importResult.case_ids,
          project_id: selectedProject,
          trigger_type: 'swagger_import',
        }),
      })
      const data = await res.json()
      if (data.run_id) navigate(`/test-runs-v2/${data.run_id}`)
      else setError('执行失败: ' + JSON.stringify(data))
    } catch (err) {
      setError('执行失败: ' + err.message)
    }
  }

  const stats = preview?.stats || {}

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-gray-900">Swagger 一键导入</h1>
          <p className="text-sm text-gray-500 mt-1">解析 Swagger 文档 → 预览选择接口 → 批量生成可执行测试用例</p>
        </div>

        {error && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700 flex justify-between items-center">
            <span>{error}</span>
            <button onClick={() => setError(null)} className="text-red-400 hover:text-red-600 ml-4">&#x2715;</button>
          </div>
        )}

        {/* ═══ Step 1: URL + 项目 ═══ */}
        <div className="bg-white rounded-xl shadow-sm p-6 mb-6">
          <div className="flex items-center gap-3 mb-4">
            <span className="w-7 h-7 bg-blue-600 text-white rounded-full flex items-center justify-center text-sm font-bold">1</span>
            <h2 className="text-base font-semibold">配置接口文档来源</h2>
          </div>
          <div className="flex gap-3 mb-4">
            <button
              onClick={() => setSourceType('yapi')}
              className={`px-4 py-2 rounded-lg text-sm ${sourceType === 'yapi' ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'}`}
            >
              YApi Token
            </button>
            <button
              onClick={() => setSourceType('url')}
              className={`px-4 py-2 rounded-lg text-sm ${sourceType === 'url' ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'}`}
            >
              Swagger URL
            </button>
            <button
              onClick={() => setSourceType('file')}
              className={`px-4 py-2 rounded-lg text-sm ${sourceType === 'file' ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'}`}
            >
              文件上传
            </button>
          </div>
          <div className="grid grid-cols-12 gap-4">
            <div className="col-span-8">
              {sourceType === 'file' ? (
                <>
                  <label className="block text-xs text-gray-500 mb-1">上传 Swagger / OpenAPI 文件 (JSON / YAML)</label>
                  <div className="flex items-center gap-3">
                    <label className="flex-1 flex items-center justify-center px-4 py-3 border-2 border-dashed border-gray-300 rounded-lg cursor-pointer hover:border-blue-400 hover:bg-blue-50 transition-colors">
                      <input
                        type="file"
                        accept=".json,.yaml,.yml"
                        className="hidden"
                        onChange={(e) => setSwaggerFile(e.target.files?.[0] || null)}
                      />
                      <span className="text-sm text-gray-600">
                        {swaggerFile ? `📄 ${swaggerFile.name} (${(swaggerFile.size / 1024).toFixed(1)} KB)` : '点击选择或拖拽 JSON / YAML 文件'}
                      </span>
                    </label>
                    {swaggerFile && (
                      <button onClick={() => setSwaggerFile(null)} className="text-xs text-red-500 hover:underline">清除</button>
                    )}
                  </div>
                  <p className="text-xs text-gray-400 mt-1">支持 Swagger 2.0 / OpenAPI 3.0 格式</p>
                </>
              ) : sourceType === 'url' ? (
                <>
                  <label className="block text-xs text-gray-500 mb-1">Swagger / OpenAPI URL</label>
                  <input
                    type="text"
                    value={swaggerUrl}
                    onChange={(e) => setSwaggerUrl(e.target.value)}
                    placeholder="https://api.example.com/v2/api-docs"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                  <div className="flex gap-2 mt-1.5">
                    <button onClick={() => setSwaggerUrl('https://dev-recycle.szhibu.com/dev-api/recycle/v2/api-docs')} className="text-xs text-blue-600 hover:underline">蓝点 Dev</button>
                    <button onClick={() => setSwaggerUrl('https://petstore.swagger.io/v2/swagger.json')} className="text-xs text-blue-600 hover:underline">Petstore 示例</button>
                  </div>
                </>
              ) : (
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs text-gray-500 mb-1">YApi 服务地址 / URL模板</label>
                    <input
                      type="text"
                      value={yapiBaseUrl}
                      onChange={(e) => setYapiBaseUrl(e.target.value)}
                      placeholder="https://yapi.example.com 或 https://yapi.example.com/api/open/plugin/export-full?type=json&status=all&token={token}"
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    />
                    <p className="text-xs text-gray-400 mt-1">不含 {'{token}'} 时会自动拼接 YApi OpenAPI 导出路径</p>
                  </div>
                  <div>
                    <label className="block text-xs text-gray-500 mb-1">项目 Token</label>
                    <input
                      type="password"
                      value={yapiToken}
                      onChange={(e) => setYapiToken(e.target.value)}
                      placeholder="粘贴 YApi 项目唯一 token"
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    />
                  </div>
                </div>
              )}
            </div>
            <div className="col-span-4">
              <label className="block text-xs text-gray-500 mb-1">目标项目</label>
              <select
                value={selectedProject || ''}
                onChange={(e) => setSelectedProject(Number(e.target.value))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500"
              >
                <option value="">选择项目</option>
                {projects.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}
              </select>
            </div>
          </div>
          <button
            onClick={handlePreview}
            disabled={loading || (sourceType === 'url' ? !swaggerUrl : sourceType === 'file' ? !swaggerFile : (!yapiBaseUrl || !yapiToken))}
            className="mt-4 px-6 py-2.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 text-sm font-medium"
          >
            {loading ? '解析中...' : '解析预览'}
          </button>
        </div>

        {/* ═══ Step 2: 预览结果 ═══ */}
        {preview && (
          <div className="bg-white rounded-xl shadow-sm mb-6">
            {/* 统计头 */}
            <div className="p-5 border-b">
              <div className="flex items-center gap-3 mb-3">
                <span className="w-7 h-7 bg-green-600 text-white rounded-full flex items-center justify-center text-sm font-bold">2</span>
                <h2 className="text-base font-semibold">选择要导入的接口</h2>
                <span className="text-xs text-gray-400">Swagger {preview.swagger_version} | base: {preview.base_url}</span>
              </div>
              <div className="flex flex-wrap gap-3">
                <div className="bg-blue-50 px-4 py-2 rounded-lg text-center">
                  <div className="text-lg font-bold text-blue-700">{stats.total_apis || 0}</div>
                  <div className="text-xs text-blue-500">总 API</div>
                </div>
                <div className="bg-green-50 px-4 py-2 rounded-lg text-center">
                  <div className="text-lg font-bold text-green-700">{stats.generated || 0}</div>
                  <div className="text-xs text-green-500">已生成</div>
                </div>
                <div className="bg-purple-50 px-4 py-2 rounded-lg text-center">
                  <div className="text-lg font-bold text-purple-700">{selectedIds.size}</div>
                  <div className="text-xs text-purple-500">已选中</div>
                </div>
                {stats.by_pattern && Object.entries(stats.by_pattern).map(([k, v]) => (
                  <button key={k} onClick={() => selectByPattern(k)}
                    className={`px-3 py-2 rounded-lg text-center cursor-pointer hover:opacity-80 ${PATTERN_COLOR[k] || 'bg-gray-100'}`}>
                    <div className="text-sm font-bold">{v}</div>
                    <div className="text-xs">{PATTERN_LABEL[k] || k}</div>
                  </button>
                ))}
              </div>
            </div>

            {/* 过滤栏 */}
            <div className="p-4 border-b bg-gray-50 flex flex-wrap gap-3 items-center">
              <input
                type="text"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder="搜索接口名称或路径..."
                className="px-3 py-1.5 border rounded-lg text-sm w-64 focus:ring-2 focus:ring-blue-500"
              />
              <select value={tagFilter} onChange={e => setTagFilter(e.target.value)} className="px-3 py-1.5 border rounded-lg text-sm">
                <option value="all">全部 Tag</option>
                {(preview.tags || []).map(t => <option key={t} value={t}>{t}</option>)}
              </select>
              <select value={patternFilter} onChange={e => setPatternFilter(e.target.value)} className="px-3 py-1.5 border rounded-lg text-sm">
                <option value="all">全部模式</option>
                {Object.keys(PATTERN_LABEL).map(k => <option key={k} value={k}>{PATTERN_LABEL[k]}</option>)}
              </select>
              <div className="ml-auto flex gap-2">
                <button onClick={selectAll} className="px-3 py-1.5 text-xs bg-blue-100 text-blue-700 rounded-lg hover:bg-blue-200">全选当前</button>
                <button onClick={deselectAll} className="px-3 py-1.5 text-xs bg-gray-100 text-gray-600 rounded-lg hover:bg-gray-200">取消当前</button>
              </div>
            </div>

            {/* 用例列表 */}
            <div className="max-h-[500px] overflow-y-auto">
              <table className="w-full text-sm">
                <thead className="bg-gray-50 sticky top-0">
                  <tr>
                    <th className="py-2 px-3 w-10"></th>
                    <th className="py-2 px-3 text-left text-xs text-gray-500">方法</th>
                    <th className="py-2 px-3 text-left text-xs text-gray-500">路径</th>
                    <th className="py-2 px-3 text-left text-xs text-gray-500">标题</th>
                    <th className="py-2 px-3 text-left text-xs text-gray-500">模式</th>
                    <th className="py-2 px-3 text-left text-xs text-gray-500">断言</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredCases.map(c => {
                    const pattern = detectPattern(c.path)
                    const checked = selectedIds.has(c._idx)
                    return (
                      <tr key={c._idx}
                        className={`border-t cursor-pointer hover:bg-blue-50/50 transition ${checked ? 'bg-blue-50/30' : ''}`}
                        onClick={() => toggleSelect(c._idx)}>
                        <td className="py-2 px-3">
                          <input type="checkbox" checked={checked} onChange={() => {}} className="rounded" />
                        </td>
                        <td className="py-2 px-3">
                          <span className={`font-mono text-xs font-bold px-1.5 py-0.5 rounded ${
                            c.method === 'GET' ? 'bg-green-100 text-green-700' :
                            c.method === 'POST' ? 'bg-blue-100 text-blue-700' :
                            c.method === 'PUT' ? 'bg-amber-100 text-amber-700' :
                            c.method === 'DELETE' ? 'bg-red-100 text-red-700' : 'bg-gray-100'
                          }`}>{c.method}</span>
                        </td>
                        <td className="py-2 px-3 font-mono text-xs text-gray-700 max-w-[300px] truncate">{c.path}</td>
                        <td className="py-2 px-3 text-gray-800 max-w-[250px] truncate">{c.title}</td>
                        <td className="py-2 px-3">
                          <span className={`px-2 py-0.5 rounded text-xs ${PATTERN_COLOR[pattern] || 'bg-gray-100'}`}>
                            {PATTERN_LABEL[pattern] || pattern}
                          </span>
                        </td>
                        <td className="py-2 px-3 text-xs text-gray-500">{c.assertions?.length || 0} 条</td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
              {filteredCases.length === 0 && (
                <div className="py-8 text-center text-gray-400 text-sm">无匹配的接口</div>
              )}
            </div>

            {/* 导入按钮 */}
            <div className="p-4 border-t bg-gray-50">
              <div className="flex items-center gap-3 mb-3">
                <label className="text-xs text-gray-500 whitespace-nowrap">API 服务地址:</label>
                <input
                  type="text"
                  value={customBaseUrl}
                  onChange={(e) => setCustomBaseUrl(e.target.value)}
                  placeholder="https://api.example.com  (必填，用例 URL = 此地址 + 接口路径)"
                  className={`flex-1 px-3 py-1.5 border rounded-lg text-sm focus:ring-2 focus:ring-blue-500 ${
                    !customBaseUrl.trim() ? 'border-orange-400 bg-orange-50' : 'border-gray-300'
                  }`}
                />
              </div>
              {!customBaseUrl.trim() && (
                <p className="text-xs text-orange-600 mb-2">⚠️ 请填写 API 服务地址，否则导入的用例 URL 只有路径没有域名，无法执行</p>
              )}
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-500">
                  已选 <strong className="text-blue-600">{selectedIds.size}</strong> / {preview.cases?.length || 0} 个接口
                </span>
                <button
                  onClick={handleImport}
                  disabled={importing || selectedIds.size === 0 || !selectedProject}
                  className="px-6 py-2.5 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 text-sm font-medium"
                >
                  {importing ? '导入中...' : `导入 ${selectedIds.size} 个用例到项目`}
                </button>
              </div>
            </div>
          </div>
        )}

        {/* ═══ Step 3: 导入结果 ═══ */}
        {importResult && (
          <div className="bg-white rounded-xl shadow-sm p-6 mb-6">
            <div className="flex items-center gap-3 mb-4">
              <span className="w-7 h-7 bg-green-600 text-white rounded-full flex items-center justify-center text-sm font-bold">3</span>
              <h2 className="text-base font-semibold">导入完成</h2>
            </div>
            <div className="flex gap-4 mb-4">
              <div className="bg-green-50 px-5 py-3 rounded-lg">
                <div className="text-2xl font-bold text-green-600">{importResult.imported}</div>
                <div className="text-xs text-green-500">新增用例</div>
              </div>
              {importResult.skipped > 0 && (
                <div className="bg-yellow-50 px-5 py-3 rounded-lg">
                  <div className="text-2xl font-bold text-yellow-600">{importResult.skipped}</div>
                  <div className="text-xs text-yellow-500">跳过(已存在)</div>
                </div>
              )}
            </div>
            <p className="text-sm text-gray-600 mb-4">
              用例已导入到项目，可在「测试用例」页面查看，或直接执行测试。
            </p>
            <div className="flex gap-3">
              <button
                onClick={handleExecute}
                className="px-6 py-2.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm font-medium"
              >
                执行全部导入的用例
              </button>
              <button
                onClick={() => navigate('/test-cases')}
                className="px-6 py-2.5 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 text-sm"
              >
                查看测试用例
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
