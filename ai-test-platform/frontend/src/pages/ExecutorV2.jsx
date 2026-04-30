import { useState, useEffect } from 'react'
import { useSearchParams } from 'react-router-dom'
import { Play, Eye, ChevronDown, ChevronRight, CheckCircle, XCircle, AlertCircle, Clock, Send, Zap, FileJson, Shield, ShieldCheck, Sparkles } from 'lucide-react'
import api from '../services/api'

const STATUS_COLORS = {
  passed: 'text-green-600 bg-green-50 border-green-200',
  failed: 'text-red-600 bg-red-50 border-red-200',
  error: 'text-orange-600 bg-orange-50 border-orange-200',
  skipped: 'text-slate-500 bg-slate-50 border-slate-200',
}

const STATUS_ICONS = {
  passed: <CheckCircle className="w-4 h-4 text-green-500" />,
  failed: <XCircle className="w-4 h-4 text-red-500" />,
  error: <AlertCircle className="w-4 h-4 text-orange-500" />,
  skipped: <Clock className="w-4 h-4 text-slate-400" />,
}

function JsonBlock({ data, title, maxHeight = '300px' }) {
  if (!data) return null
  return (
    <div>
      {title && <div className="text-xs font-medium text-slate-500 mb-1">{title}</div>}
      <pre className="p-3 bg-slate-900 text-slate-100 rounded-md overflow-auto text-xs leading-relaxed" style={{ maxHeight }}>
        {typeof data === 'string' ? data : JSON.stringify(data, null, 2)}
      </pre>
    </div>
  )
}

function AssertionRow({ assertion }) {
  const icon = assertion.passed ? STATUS_ICONS.passed : STATUS_ICONS.failed
  return (
    <div className={`flex items-start gap-2 p-2 rounded-md border ${assertion.passed ? 'bg-green-50 border-green-100' : 'bg-red-50 border-red-100'}`}>
      <div className="mt-0.5">{icon}</div>
      <div className="flex-1 min-w-0">
        <div className="text-sm font-medium text-slate-800">
          {assertion.type}
          {assertion.path && <span className="text-slate-500 ml-1 font-mono text-xs">({assertion.path})</span>}
        </div>
        <div className="text-xs text-slate-600 mt-0.5">
          期望: <span className="font-mono">{JSON.stringify(assertion.expected)}</span>
          {' → '}
          实际: <span className="font-mono">{JSON.stringify(assertion.actual)}</span>
        </div>
        {assertion.message && <div className="text-xs text-red-600 mt-0.5">{assertion.message}</div>}
      </div>
    </div>
  )
}

function ResultCard({ result, index }) {
  const [expanded, setExpanded] = useState(false)
  const status = result.status || 'error'
  const req = result.request
  const resp = result.response
  const assertions = result.assertions || []
  const summary = result.assertion_summary || {}

  return (
    <div className={`border rounded-lg overflow-hidden ${STATUS_COLORS[status] || STATUS_COLORS.error}`}>
      <div className="px-4 py-3 flex items-center gap-3 cursor-pointer hover:bg-opacity-80" onClick={() => setExpanded(!expanded)}>
        {expanded ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            {STATUS_ICONS[status]}
            <span className="font-medium text-sm text-slate-900">{result.case_title || result.case_id}</span>
          </div>
          <div className="text-xs text-slate-500 mt-0.5">
            {req?.method} {req?.url} · {result.duration_ms?.toFixed(0)}ms
            {summary.total > 0 && ` · 断言 ${summary.passed}/${summary.total}`}
          </div>
        </div>
        <div className={`px-2 py-0.5 rounded text-xs font-medium ${status === 'passed' ? 'bg-green-100 text-green-700' : status === 'failed' ? 'bg-red-100 text-red-700' : 'bg-orange-100 text-orange-700'}`}>
          {status.toUpperCase()}
        </div>
      </div>

      {expanded && (
        <div className="border-t bg-white p-4 space-y-4">
          {/* 请求 */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <div className="space-y-2">
              <div className="text-sm font-semibold text-slate-700 flex items-center gap-1">
                <Send className="w-3.5 h-3.5" /> 请求
              </div>
              <div className="text-xs space-y-1">
                <div><span className="text-slate-500">URL:</span> <span className="font-mono">{req?.method} {req?.url}</span></div>
                <div><span className="text-slate-500">超时:</span> {req?.timeout}s</div>
              </div>
              {req?.headers && Object.keys(req.headers).length > 0 && (
                <JsonBlock data={req.headers} title="请求头" maxHeight="150px" />
              )}
              {req?.body && <JsonBlock data={req.body} title="请求体" maxHeight="200px" />}
              {req?.query_params && Object.keys(req.query_params).length > 0 && (
                <JsonBlock data={req.query_params} title="查询参数" maxHeight="100px" />
              )}
            </div>

            {/* 响应 */}
            <div className="space-y-2">
              <div className="text-sm font-semibold text-slate-700">响应</div>
              <div className="text-xs space-y-1">
                <div>
                  <span className="text-slate-500">状态码:</span>{' '}
                  <span className={`font-mono font-bold ${resp?.status_code >= 200 && resp?.status_code < 300 ? 'text-green-600' : resp?.status_code >= 400 ? 'text-red-600' : 'text-orange-600'}`}>
                    {resp?.status_code || 'N/A'}
                  </span>
                </div>
                <div><span className="text-slate-500">耗时:</span> {resp?.elapsed_ms?.toFixed(2)}ms</div>
              </div>
              {resp?.body && <JsonBlock data={resp.body} title="响应体" maxHeight="250px" />}
              {!resp?.body && resp?.body_text && <JsonBlock data={resp.body_text} title="响应文本" maxHeight="250px" />}
            </div>
          </div>

          {/* 断言 */}
          {assertions.length > 0 && (
            <div>
              <div className="text-sm font-semibold text-slate-700 mb-2">
                断言结果 ({summary.passed}/{summary.total} 通过)
              </div>
              <div className="space-y-1.5">
                {assertions.map((a, i) => <AssertionRow key={i} assertion={a} />)}
              </div>
            </div>
          )}

          {/* 错误信息 */}
          {result.error_message && (
            <div className="p-3 bg-red-50 border border-red-200 rounded-md text-sm text-red-700">
              <div className="font-medium">错误</div>
              <div className="mt-1 font-mono text-xs">{result.error_message}</div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default function ExecutorV2() {
  const [searchParams] = useSearchParams()
  const [baseUrl, setBaseUrl] = useState(searchParams.get('base_url') || '')
  const [caseText, setCaseText] = useState(DEFAULT_CASE)
  const [loading, setLoading] = useState(false)
  const [runResult, setRunResult] = useState(null)
  const [error, setError] = useState('')

  // 认证
  const [tokenInput, setTokenInput] = useState('')
  const [authStatus, setAuthStatus] = useState(null)
  const [authLoading, setAuthLoading] = useState(false)

  useEffect(() => { loadAuthStatus() }, [])

  const loadAuthStatus = async () => {
    try {
      const res = await api.v2.executorV2.getAuthStatus()
      setAuthStatus(res.envs || {})
    } catch { setAuthStatus(null) }
  }

  const handleSetToken = async () => {
    if (!tokenInput.trim()) return
    setAuthLoading(true)
    try {
      await api.v2.executorV2.setToken({ token: tokenInput.trim(), auth_type: 'bearer' })
      await loadAuthStatus()
      setTokenInput('')
    } catch (e) {
      setError('设置Token失败: ' + (e.message || e))
    } finally { setAuthLoading(false) }
  }

  const handleClearToken = async () => {
    try {
      await api.v2.executorV2.clearToken()
      await loadAuthStatus()
    } catch (e) { setError('清除Token失败: ' + (e.message || e)) }
  }

  // Swagger 一键生成
  const [swaggerLoading, setSwaggerLoading] = useState(false)
  const [swaggerMeta, setSwaggerMeta] = useState(null)
  const [includePatterns, setIncludePatterns] = useState(['page', 'list', 'detail'])
  const [maxCases, setMaxCases] = useState(20)

  // AI 增强
  const [aiLoading, setAiLoading] = useState(false)
  const [aiEnhanced, setAiEnhanced] = useState(0)

  // 查看历史
  const [runIdInput, setRunIdInput] = useState('')
  const [historyResult, setHistoryResult] = useState(null)
  const [historyLoading, setHistoryLoading] = useState(false)

  const handleExecute = async () => {
    setError('')
    setRunResult(null)

    if (!baseUrl.trim()) {
      setError('请输入目标服务地址 (base_url)')
      return
    }

    let cases
    try {
      cases = JSON.parse(caseText)
      if (!Array.isArray(cases)) cases = [cases]
    } catch (e) {
      setError('用例 JSON 格式错误: ' + e.message)
      return
    }

    setLoading(true)
    try {
      const res = await api.v2.executorV2.executeBatch({
        base_url: baseUrl.trim(),
        cases: cases,
      })
      setRunResult(res)
      if (res.run_id) setRunIdInput(res.run_id)
    } catch (e) {
      setError(e.message || '执行失败')
    } finally {
      setLoading(false)
    }
  }

  const handleGenerateCases = async () => {
    setError('')
    setSwaggerLoading(true)
    setSwaggerMeta(null)
    try {
      const res = await api.v2.executorV2.generateFromSwagger({
        base_url: baseUrl.trim(),
        include_patterns: includePatterns,
        max_cases: maxCases,
      })
      setCaseText(JSON.stringify(res.cases, null, 2))
      if (res.base_url && !baseUrl.trim()) setBaseUrl(res.base_url)
      setSwaggerMeta(res.meta)
    } catch (e) {
      setError('生成用例失败: ' + (e.message || e))
    } finally {
      setSwaggerLoading(false)
    }
  }

  const handleAiEnhance = async () => {
    setError('')
    setAiLoading(true)
    setAiEnhanced(0)
    setSwaggerMeta(null)
    try {
      const res = await api.v2.executorV2.aiEnhanceCases({
        base_url: baseUrl.trim(),
        include_patterns: includePatterns,
        max_cases: maxCases,
      })
      setCaseText(JSON.stringify(res.cases, null, 2))
      if (res.base_url && !baseUrl.trim()) setBaseUrl(res.base_url)
      setSwaggerMeta(res.meta)
      setAiEnhanced(res.ai_enhanced || 0)
    } catch (e) {
      setError('AI增强失败: ' + (e.message || e))
    } finally {
      setAiLoading(false)
    }
  }

  const handleGenerateAndRun = async () => {
    setError('')
    setRunResult(null)
    setSwaggerLoading(true)
    setSwaggerMeta(null)
    try {
      const res = await api.v2.executorV2.generateAndRun({
        base_url: baseUrl.trim(),
        include_patterns: includePatterns,
        max_cases: maxCases,
      })
      setRunResult(res)
      setSwaggerMeta(res.meta)
      if (res.base_url && !baseUrl.trim()) setBaseUrl(res.base_url)
      if (res.run_id) setRunIdInput(res.run_id)
    } catch (e) {
      setError('生成并执行失败: ' + (e.message || e))
    } finally {
      setSwaggerLoading(false)
    }
  }

  const handleAiAndRun = async () => {
    setError('')
    setRunResult(null)
    setAiLoading(true)
    setAiEnhanced(0)
    setSwaggerMeta(null)
    try {
      // 第1步：AI 生成智能断言用例
      const gen = await api.v2.executorV2.aiEnhanceCases({
        base_url: baseUrl.trim(),
        include_patterns: includePatterns,
        max_cases: maxCases,
      })
      const url = gen.base_url || baseUrl.trim()
      if (url && !baseUrl.trim()) setBaseUrl(url)
      setSwaggerMeta(gen.meta)
      setAiEnhanced(gen.ai_enhanced || 0)
      setCaseText(JSON.stringify(gen.cases, null, 2))

      // 第2步：用 AI 断言执行
      const res = await api.v2.executorV2.executeBatch({
        base_url: url,
        cases: gen.cases,
      })
      setRunResult(res)
      if (res.run_id) setRunIdInput(res.run_id)
    } catch (e) {
      setError('AI断言+执行失败: ' + (e.message || e))
    } finally {
      setAiLoading(false)
    }
  }

  const handleLoadHistory = async () => {
    if (!runIdInput.trim()) return
    setHistoryLoading(true)
    setHistoryResult(null)
    try {
      const res = await api.v2.executorV2.getRunResults(runIdInput.trim())
      setHistoryResult(res)
    } catch (e) {
      setError(e.message || '加载历史失败')
    } finally {
      setHistoryLoading(false)
    }
  }

  const displayResults = runResult?.results || historyResult?.results || []
  const displaySummary = runResult?.summary || historyResult?.summary || null
  const displayRunId = runResult?.run_id || historyResult?.run_id || ''

  return (
    <div className="min-h-screen bg-slate-50">
      <div className="max-w-[1400px] mx-auto px-4 sm:px-6 py-6 space-y-6">

        {/* 标题 */}
        <div>
          <h1 className="text-2xl font-bold text-slate-900">真实 API 测试执行</h1>
          <p className="text-sm text-slate-500 mt-1">使用 Executor V2 引擎，发送真实 HTTP 请求，执行真实断言</p>
        </div>

        {/* 认证配置 */}
        <div className="bg-white rounded-lg border border-slate-200 p-4">
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 min-w-0">
              {authStatus && Object.keys(authStatus).length > 0
                ? <ShieldCheck className="w-5 h-5 text-green-500" />
                : <Shield className="w-5 h-5 text-slate-400" />
              }
              <span className="text-sm font-medium text-slate-700">认证</span>
              {authStatus && Object.keys(authStatus).length > 0 ? (
                <span className="text-xs text-green-600 bg-green-50 px-2 py-0.5 rounded">
                  Token 已设置 · {Object.values(authStatus)[0]?.token_preview}
                </span>
              ) : (
                <span className="text-xs text-slate-400">未设置 Token，部分接口可能返回 401</span>
              )}
            </div>
            <div className="flex items-center gap-2 flex-1 ml-auto">
              <input
                type="password"
                className="flex-1 px-3 py-1.5 border border-slate-300 rounded text-xs font-mono focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="粘贴 Bearer Token (JWT)..."
                value={tokenInput}
                onChange={(e) => setTokenInput(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSetToken()}
              />
              <button
                className="px-3 py-1.5 bg-green-600 text-white rounded text-xs font-medium hover:bg-green-700 disabled:opacity-50"
                onClick={handleSetToken}
                disabled={authLoading || !tokenInput.trim()}
              >
                设置
              </button>
              {authStatus && Object.keys(authStatus).length > 0 && (
                <button
                  className="px-3 py-1.5 border border-red-300 text-red-600 rounded text-xs hover:bg-red-50"
                  onClick={handleClearToken}
                >
                  清除
                </button>
              )}
            </div>
          </div>
        </div>

        {/* Swagger 一键生成 */}
        <div className="bg-white rounded-lg border border-blue-200 p-4 space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <FileJson className="w-5 h-5 text-blue-600" />
              <span className="font-semibold text-slate-800">Swagger 自动生成</span>
              <span className="text-xs text-slate-400">从已导入的 Swagger 文件自动生成测试用例</span>
            </div>
          </div>

          <div className="flex items-center gap-3 flex-wrap">
            <div className="flex items-center gap-2">
              <span className="text-xs text-slate-500">接口类型:</span>
              {['page', 'list', 'detail', 'other'].map(p => (
                <label key={p} className="flex items-center gap-1 text-xs">
                  <input
                    type="checkbox"
                    checked={includePatterns.includes(p)}
                    onChange={(e) => {
                      if (e.target.checked) setIncludePatterns([...includePatterns, p])
                      else setIncludePatterns(includePatterns.filter(x => x !== p))
                    }}
                    className="rounded border-slate-300"
                  />
                  {p}
                </label>
              ))}
            </div>
            <div className="flex items-center gap-1">
              <span className="text-xs text-slate-500">最多:</span>
              <input
                type="number"
                className="w-16 px-2 py-1 border border-slate-300 rounded text-xs"
                value={maxCases}
                onChange={(e) => setMaxCases(Number(e.target.value) || 0)}
                min={0}
              />
              <span className="text-xs text-slate-400">条 (0=全部)</span>
            </div>

            <div className="flex items-center gap-2 ml-auto">
              <button
                className="px-3 py-1.5 bg-blue-100 text-blue-700 rounded text-xs font-medium hover:bg-blue-200 disabled:opacity-50 flex items-center gap-1"
                onClick={handleGenerateCases}
                disabled={swaggerLoading || aiLoading}
              >
                <FileJson className="w-3.5 h-3.5" />
                生成用例
              </button>
              <button
                className="px-3 py-1.5 bg-purple-100 text-purple-700 rounded text-xs font-medium hover:bg-purple-200 disabled:opacity-50 flex items-center gap-1"
                onClick={handleAiEnhance}
                disabled={aiLoading || swaggerLoading}
              >
                <Sparkles className="w-3.5 h-3.5" />
                {aiLoading && !runResult ? 'AI分析中...' : 'AI生成断言'}
              </button>
              <button
                className="px-3 py-1.5 bg-blue-500 text-white rounded text-xs font-medium hover:bg-blue-600 disabled:opacity-50 flex items-center gap-1"
                onClick={handleGenerateAndRun}
                disabled={swaggerLoading || aiLoading}
              >
                <Zap className="w-3.5 h-3.5" />
                {swaggerLoading ? '执行中...' : '生成并执行'}
              </button>
              <button
                className="px-3 py-1.5 bg-purple-600 text-white rounded text-xs font-medium hover:bg-purple-700 disabled:opacity-50 flex items-center gap-1"
                onClick={handleAiAndRun}
                disabled={aiLoading || swaggerLoading}
              >
                <Sparkles className="w-3.5 h-3.5" />
                {aiLoading ? 'AI断言+执行中...' : 'AI断言+执行'}
              </button>
            </div>
          </div>

          {swaggerMeta && (
            <div className="text-xs text-slate-500 bg-slate-50 rounded p-2">
              Swagger 共 {swaggerMeta.total_apis} 个 API，已生成 {swaggerMeta.generated} 个用例
              （{Object.entries(swaggerMeta.by_pattern || {}).map(([k,v]) => `${k}: ${v}`).join(', ')}）
              {swaggerMeta.skipped > 0 && `，跳过 ${swaggerMeta.skipped} 个`}
              {aiEnhanced > 0 && <span className="text-purple-600 font-medium ml-1">✨ AI 增强 {aiEnhanced} 个</span>}
            </div>
          )}
        </div>

        {/* 配置区 */}
        <div className="bg-white rounded-lg border border-slate-200 p-4 space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">目标服务地址 (base_url)</label>
            <input
              type="text"
              className="w-full px-3 py-2 border border-slate-300 rounded-md text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              placeholder="例如: http://localhost:8080 或 https://api.example.com"
              value={baseUrl}
              onChange={(e) => setBaseUrl(e.target.value)}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">
              测试用例 (JSON 数组)
              <span className="text-xs text-slate-400 ml-2">支持单个对象或数组</span>
            </label>
            <textarea
              className="w-full px-3 py-2 border border-slate-300 rounded-md text-sm font-mono focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              rows={12}
              value={caseText}
              onChange={(e) => setCaseText(e.target.value)}
            />
          </div>

          {error && (
            <div className="p-3 bg-red-50 border border-red-200 rounded-md text-sm text-red-700">{error}</div>
          )}

          <div className="flex items-center gap-3">
            <button
              className="px-4 py-2 bg-blue-600 text-white rounded-md text-sm font-medium hover:bg-blue-700 disabled:opacity-50 flex items-center gap-2"
              onClick={handleExecute}
              disabled={loading}
            >
              <Play className="w-4 h-4" />
              {loading ? '执行中...' : '执行测试'}
            </button>

            <div className="flex items-center gap-2 ml-auto">
              <input
                type="text"
                className="px-3 py-2 border border-slate-300 rounded-md text-sm w-64"
                placeholder="输入 run_id 查看历史..."
                value={runIdInput}
                onChange={(e) => setRunIdInput(e.target.value)}
              />
              <button
                className="px-3 py-2 border border-slate-300 rounded-md text-sm hover:bg-slate-50 flex items-center gap-1"
                onClick={handleLoadHistory}
                disabled={historyLoading}
              >
                <Eye className="w-4 h-4" />
                查看
              </button>
            </div>
          </div>
        </div>

        {/* 汇总 */}
        {displaySummary && (
          <div className="bg-white rounded-lg border border-slate-200 p-4">
            <div className="flex items-center justify-between mb-3">
              <div className="text-sm font-semibold text-slate-700">
                执行结果
                {displayRunId && <span className="text-xs text-slate-400 ml-2 font-mono">run_id: {displayRunId}</span>}
              </div>
            </div>
            <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
              <div className="text-center p-3 bg-slate-50 rounded-md">
                <div className="text-2xl font-bold text-slate-900">{displaySummary.total}</div>
                <div className="text-xs text-slate-500">总计</div>
              </div>
              <div className="text-center p-3 bg-green-50 rounded-md">
                <div className="text-2xl font-bold text-green-600">{displaySummary.passed}</div>
                <div className="text-xs text-slate-500">通过</div>
              </div>
              <div className="text-center p-3 bg-red-50 rounded-md">
                <div className="text-2xl font-bold text-red-600">{displaySummary.failed}</div>
                <div className="text-xs text-slate-500">失败</div>
              </div>
              <div className="text-center p-3 bg-orange-50 rounded-md">
                <div className="text-2xl font-bold text-orange-600">{displaySummary.error || 0}</div>
                <div className="text-xs text-slate-500">错误</div>
              </div>
              <div className="text-center p-3 bg-blue-50 rounded-md">
                <div className="text-2xl font-bold text-blue-600">{displaySummary.total_duration_ms?.toFixed(0) || 0}</div>
                <div className="text-xs text-slate-500">总耗时(ms)</div>
              </div>
            </div>
          </div>
        )}

        {/* 结果列表 */}
        {displayResults.length > 0 && (
          <div className="space-y-3">
            <div className="text-sm font-semibold text-slate-700">用例详情 ({displayResults.length})</div>
            {displayResults.map((r, i) => <ResultCard key={r.case_id || i} result={r} index={i} />)}
          </div>
        )}
      </div>
    </div>
  )
}

const DEFAULT_CASE = JSON.stringify([
  {
    title: "币别 - 分页查询",
    method: "POST",
    path: "/basic/basicCurrency/page",
    body: { pageNum: 1, pageSize: 10 },
    assertions: [
      { type: "status_code", expected: 200 },
      { type: "response_time", expected: 10000 },
      { type: "field_exists", path: "code" }
    ]
  },
  {
    title: "币别 - 列表(启用)",
    method: "POST",
    path: "/basic/basicCurrency/list",
    body: {},
    assertions: [
      { type: "status_code", expected: 200 },
      { type: "response_time", expected: 5000 }
    ]
  },
  {
    title: "汇率 - 分页查询",
    method: "POST",
    path: "/basic/basicExchangeRate/page",
    body: { pageNum: 1, pageSize: 10 },
    assertions: [
      { type: "status_code", expected: 200 },
      { type: "response_time", expected: 5000 }
    ]
  },
  {
    title: "仓库 - 列表",
    method: "POST",
    path: "/basic/basicWarehouseInfo/list",
    body: {},
    assertions: [
      { type: "status_code", expected: 200 },
      { type: "response_time", expected: 5000 }
    ]
  },
  {
    title: "客户信息 - 分页列表",
    method: "POST",
    path: "/davinci/crm/customer/page",
    body: { pageNum: 1, pageSize: 10 },
    assertions: [
      { type: "status_code", expected: 200 },
      { type: "response_time", expected: 5000 }
    ]
  }
], null, 2)
