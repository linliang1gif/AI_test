import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../services/api'
import SVNInput from '../components/SVNInput'

const EXECUTION_ENV_STORAGE_KEY = 'ai_test_selected_execution_environment_id'

export default function TestCases() {
  const navigate = useNavigate()
  const [showUploadDialog, setShowUploadDialog] = useState(false)
  const [showSVNDialog, setShowSVNDialog] = useState(false)
  const [uploadFile, setUploadFile] = useState(null)
  const [isGenerating, setIsGenerating] = useState(false)
  const [testCases, setTestCases] = useState([])
  const [loading, setLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState('')
  const [sourceFilter, setSourceFilter] = useState('all')
  const [projects, setProjects] = useState([])
  const [selectedProjectId, setSelectedProjectId] = useState('')
  const [selectedTestCase, setSelectedTestCase] = useState(null)
  const [showDetailDialog, setShowDetailDialog] = useState(false)
  const [showDatasetDialog, setShowDatasetDialog] = useState(false)
  const [datasets, setDatasets] = useState([])
  const [selectedDataset, setSelectedDataset] = useState(null)
  const [generationProgress, setGenerationProgress] = useState(0)
  const [generationStep, setGenerationStep] = useState('')
  const [selectedIds, setSelectedIds] = useState([])
  const [isDeleting, setIsDeleting] = useState(false)
  const [showScriptDialog, setShowScriptDialog] = useState(false)
  const [generatedScript, setGeneratedScript] = useState('')
  const [isGeneratingScript, setIsGeneratingScript] = useState(false)
  const [isExecuting, setIsExecuting] = useState(false)
  const [executionResult, setExecutionResult] = useState(null)
  const [showResultDialog, setShowResultDialog] = useState(false)
  const [showManualTestDialog, setShowManualTestDialog] = useState(false)
  const [manualTestSteps, setManualTestSteps] = useState([])
  const [currentStepIndex, setCurrentStepIndex] = useState(0)
  const [manualTestNotes, setManualTestNotes] = useState('')
  const [environments, setEnvironments] = useState([])
  const [selectedEnvironmentId, setSelectedEnvironmentId] = useState('')
  // Phase 16: 治理筛选
  const [govFilter, setGovFilter] = useState({ risk_level: '', api_pattern: '', destructive: '', assertion_status: '', failure_category: '', status: '' })
  const [isGoverning, setIsGoverning] = useState(false)
  const [govSummary, setGovSummary] = useState(null)
  const [presetLoading, setPresetLoading] = useState('')
  // Phase 17: Demo
  const [demoLoading, setDemoLoading] = useState(false)
  const [demoStatus, setDemoStatus] = useState(null)
  // Phase 19: AI Analysis
  const [aiAnalysis, setAiAnalysis] = useState(null)
  const [aiAnalysisLoading, setAiAnalysisLoading] = useState(false)
  const [appMode, setAppMode] = useState('mock')
  // P1-8: AI 用例评审
  const [reviewLoading, setReviewLoading] = useState(false)
  const [reviewResult, setReviewResult] = useState(null)
  const [showReviewDialog, setShowReviewDialog] = useState(false)

  useEffect(() => {
    loadProjects()
    loadTestCases()
    loadDatasets()
    loadEnvironments()
    api.v2.getAppMode().then(setAppMode)
  }, [])

  const loadTestCases = async (projectId) => {
    setLoading(true)
    try {
      const params = { limit: 1000 }
      const pid = projectId !== undefined ? projectId : selectedProjectId
      if (pid) params.project_id = pid

      const data = await api.v2.testCases.getAll(params)
      const cases = (data.test_cases || []).map(tc => ({
        ...tc,
        lastRun: tc.last_run_status || '未运行',
        type: tc.source === 'swagger' ? 'API测试' : tc.type || '功能测试'
      }))
      setTestCases(cases)
    } catch (error) {
      console.error('加载测试用例失败:', error)
    } finally {
      setLoading(false)
    }
  }

  const loadProjects = async () => {
    try {
      const result = await api.v2.projects.getAll()
      setProjects(result.projects || [])
    } catch (error) {
      console.error('加载项目列表失败:', error)
    }
  }

  const handleProjectChange = (pid) => {
    setSelectedProjectId(pid)
    loadTestCases(pid)
  }

  const loadDatasets = async () => {
    try {
      const result = await api.datasets.getAll()
      setDatasets(result.datasets || [])
    } catch (error) {
      console.error('加载数据集失败:', error)
    }
  }

  const loadEnvironments = async () => {
    try {
      const result = await api.v2.projects.getAll()
      const projects = result.projects || []
      const envLists = await Promise.all(
        projects.map(project => api.v2.projects.getEnvironments(project.id).catch(() => []))
      )
      const allEnvironments = envLists.flat()
      setEnvironments(allEnvironments)
      if (allEnvironments.length > 0) {
        const savedEnvironmentId = localStorage.getItem(EXECUTION_ENV_STORAGE_KEY)
        const validSavedEnvironment = allEnvironments.find(env => String(env.id) === savedEnvironmentId)
        setSelectedEnvironmentId(validSavedEnvironment ? savedEnvironmentId : String(allEnvironments[0].id))
      }
    } catch (error) {
      console.error('加载环境列表失败:', error)
    }
  }

  const handleFileUpload = async () => {
    if (!uploadFile) return
    
    setIsGenerating(true)
    setGenerationProgress(0)
    setGenerationStep('准备上传文档...')
    
    const formData = new FormData()
    formData.append('file', uploadFile)

    try {
      // 模拟进度更新
      const progressInterval = setInterval(() => {
        setGenerationProgress(prev => {
          if (prev >= 90) return prev
          return prev + 2
        })
      }, 1000)

      // 更新步骤提示
      setTimeout(() => setGenerationStep('📚 加载项目知识库...'), 500)
      setTimeout(() => setGenerationStep(' 解析需求文档...'), 2000)
      setTimeout(() => setGenerationStep('🔍 拆分功能模块...'), 5000)
      setTimeout(() => setGenerationStep('🎯 结合项目上下文生成测试场景...'), 12000)
      setTimeout(() => setGenerationStep('✨ 生成测试用例（含业务断言）...'), 22000)
      
      const result = await api.testCases.generate(uploadFile)
      
      clearInterval(progressInterval)
      setGenerationProgress(100)
      setGenerationStep('✅ 生成完成!')
      
      if (result.success) {
        setTimeout(() => {
          alert(`成功生成 ${result.count} 个测试用例!`)
          setShowUploadDialog(false)
          setUploadFile(null)
          setGenerationProgress(0)
          setGenerationStep('')
          
          const newTestCases = result.testCases.map(tc => ({
            id: tc.id,
            title: tc.title,
            priority: tc.priority.toLowerCase(),
            status: tc.status,
            lastRun: tc.lastRun,
            source: 'ai_generated',
            steps: tc.steps,
            expected: tc.expected,
            module: tc.module
          }))
          setTestCases(prev => [...newTestCases, ...prev])
        }, 500)
      } else {
        alert('生成失败: ' + result.error)
        setGenerationProgress(0)
        setGenerationStep('')
      }
    } catch (error) {
      alert('上传失败: ' + error.message)
      setGenerationProgress(0)
      setGenerationStep('')
    } finally {
      setIsGenerating(false)
    }
  }

  const handleViewDetail = (testCase) => {
    setSelectedTestCase(testCase)
    setShowDetailDialog(true)
  }

  const handleSelectDataset = (testCase) => {
    setSelectedTestCase(testCase)
    setShowDatasetDialog(true)
  }

  const handleBindDataset = async () => {
    if (!selectedDataset || !selectedTestCase) return

    try {
      await api.testCases.bindDataset(selectedTestCase.id, selectedDataset)
      alert('数据集绑定成功!')
      setShowDatasetDialog(false)
      setSelectedDataset(null)

      setTestCases(prev => prev.map(tc =>
        tc.id === selectedTestCase.id
          ? { ...tc, dataset_id: selectedDataset }
          : tc
      ))
    } catch (error) {
      alert('绑定失败: ' + error.message)
    }
  }

  // P1-8: AI 用例评审
  const handleAiReview = async () => {
    const hasSelection = selectedIds.length > 0
    if (!hasSelection && !selectedProjectId && filteredTestCases.length === 0) {
      alert('请先选择项目或勾选用例')
      return
    }
    if (!hasSelection && !selectedProjectId && filteredTestCases.length > 200) {
      if (!window.confirm(`当前有 ${filteredTestCases.length} 条用例，确定评审全部？`)) return
    }
    setReviewLoading(true)
    try {
      const payload = {}
      if (hasSelection) {
        payload.case_ids = selectedIds
      } else if (selectedProjectId) {
        payload.project_id = Number(selectedProjectId)
      }
      const data = await api.ai.reviewCases(payload)
      setReviewResult(data)
      setShowReviewDialog(true)
    } catch (e) {
      alert('AI 评审失败: ' + e.message)
    } finally {
      setReviewLoading(false)
    }
  }

  const handleExportExcel = async () => {
    try {
      const blob = await api.testCases.exportExcel()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `测试用例_${new Date().toISOString().slice(0,10)}.xlsx`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      window.URL.revokeObjectURL(url)
    } catch (error) {
      alert('导出失败: ' + error.message)
    }
  }

  const sourceLabel = (src) => {
    const map = { 
      ai_generated: 'AI生成', 
      smart_generated: 'AI生成',
      swagger: 'Swagger导入',
      demo_swagger: 'Demo',
      demo_seed: 'Demo',
      manual: '人工', 
      knowledge_base: '知识库' 
    }
    return map[src] || src || '-'
  }

  const selectedEnvironment = environments.find(env => String(env.id) === String(selectedEnvironmentId))
  const isPetStoreEnvironment = selectedEnvironment?.base_url?.toLowerCase().includes('petstore')
  const isPetStoreSampleCase = (tc) => {
    const moduleName = String(tc.module || '').toLowerCase()
    const title = String(tc.title || '').toLowerCase()
    return tc.source === 'swagger' && (
      ['pet', 'store', 'user'].includes(moduleName) ||
      title.includes('pet store') ||
      title.includes('add a new pet') ||
      title.includes('uploads an image')
    )
  }

  const filteredTestCases = testCases.filter(tc => {
    if (selectedEnvironmentId && !isPetStoreEnvironment && isPetStoreSampleCase(tc)) return false
    // 来源筛选
    const isApiSource = ['swagger', 'demo_swagger', 'demo_seed'].includes(tc.source)
    if (sourceFilter === 'functional' && isApiSource) return false
    if (sourceFilter === 'api' && !isApiSource) return false
    // 搜索筛选
    if (searchQuery && !(tc.title || '').toLowerCase().includes(searchQuery.toLowerCase())) return false
    return true
  })
  const hiddenPetStoreSampleCount = selectedEnvironmentId && !isPetStoreEnvironment
    ? testCases.filter(isPetStoreSampleCase).length
    : 0

  const handleSelectAll = (e) => {
    if (e.target.checked) {
      setSelectedIds(filteredTestCases.map(tc => tc.id))
    } else {
      setSelectedIds([])
    }
  }

  const handleSelectOne = (id) => {
    setSelectedIds(prev => 
      prev.includes(id) 
        ? prev.filter(i => i !== id)
        : [...prev, id]
    )
  }

  const handleBatchDelete = async () => {
    if (selectedIds.length === 0) {
      alert('请先选择要删除的测试用例')
      return
    }

    if (!window.confirm(`确定要删除选中的 ${selectedIds.length} 个测试用例吗?`)) {
      return
    }

    setIsDeleting(true)
    try {
      const result = await api.testCases.batchDelete(selectedIds)
      
      if (result.success) {
        alert(`成功删除 ${result.deleted_count} 个测试用例`)
        setTestCases(prev => prev.filter(tc => !selectedIds.includes(tc.id)))
        setSelectedIds([])
      } else {
        alert('删除失败: ' + result.error)
      }
    } catch (error) {
      alert('删除失败: ' + error.message)
    } finally {
      setIsDeleting(false)
    }
  }

  const handleGenerateScript = async (testCase) => {
    setSelectedTestCase(testCase)
    setIsGeneratingScript(true)
    setShowScriptDialog(true)
    
    try {
      const result = await api.testCases.generateScript(testCase.id)
      
      if (result.success) {
        setGeneratedScript(result.script)
      } else {
        alert('脚本生成失败: ' + result.error)
        setShowScriptDialog(false)
      }
    } catch (error) {
      alert('脚本生成失败: ' + error.message)
      setShowScriptDialog(false)
    } finally {
      setIsGeneratingScript(false)
    }
  }

  const UNSAFE_METHODS = ['POST', 'PUT', 'PATCH', 'DELETE']

  const handleExecuteTest = async (testCase) => {
    if (!selectedEnvironmentId) {
      alert('请先选择执行环境')
      return
    }

    // 真实项目模式安全确认
    const method = ((testCase.execution_config?.method) || 'GET').toUpperCase()
    let allowUnsafe = false
    if (appMode === 'real' && UNSAFE_METHODS.includes(method)) {
      if (!window.confirm(
        `当前为真实项目模式，该用例使用 ${method} 方法，可能修改真实测试环境数据。\n\n用例: ${testCase.title}\n接口: ${testCase.execution_config?.url || ''}\n\n是否确认执行？`
      )) return
      allowUnsafe = true
    } else {
      if (!window.confirm(`确定要执行接口测试: ${testCase.title}?`)) return
    }

    setIsExecuting(true)
    setSelectedTestCase(testCase)
    try {
      const result = await api.v2.testCases.execute(testCase.id, {
        environment_id: Number(selectedEnvironmentId),
        allow_unsafe_methods: allowUnsafe,
      })
      
      setExecutionResult(result)
      setShowResultDialog(true)
      
      // 更新测试用例状态
      setTestCases(prev => prev.map(tc => 
        tc.id === testCase.id 
          ? { ...tc, status: result.status, lastRun: new Date().toLocaleString() }
          : tc
      ))
    } catch (error) {
      // 解析后端返回的具体错误信息
      let msg = error.message || '执行失败'
      try {
        const parsed = JSON.parse(msg.replace(/^API调用失败: \d+ /, ''))
        const detail = parsed.detail
        if (detail && typeof detail === 'object' && detail.code === 'REAL_MODE_UNSAFE_METHOD_BLOCKED') {
          msg = `真实项目模式已阻止写操作。\n方法: ${detail.method}\n接口: ${detail.url}\n如确认允许写操作，请勾选“允许执行写操作”。`
        } else if (detail && typeof detail === 'string') {
          msg = detail
        }
      } catch {}
      alert('执行失败: ' + msg)
    } finally {
      setIsExecuting(false)
    }
  }

  const handleBatchExecute = async () => {
    if (!selectedEnvironmentId) {
      alert('请先选择执行环境')
      return
    }
    const selectedCases = filteredTestCases.filter(tc => selectedIds.includes(tc.id))
    const apiCases = selectedCases.filter(tc => tc.source === 'swagger' || tc.source === 'demo_swagger' || tc.source === 'demo_seed' || tc.execution_config)
    if (apiCases.length === 0) {
      alert('请选择可执行的接口测试用例进行批量执行')
      return
    }
    // 真实项目模式安全确认
    let allowUnsafe = false
    if (appMode === 'real') {
      const unsafeCases = apiCases.filter(tc => {
        const m = ((tc.execution_config?.method) || 'GET').toUpperCase()
        return UNSAFE_METHODS.includes(m)
      })
      if (unsafeCases.length > 0) {
        const unsafeList = unsafeCases.slice(0, 5).map(tc => `  ${(tc.execution_config?.method || 'GET').toUpperCase()} ${tc.execution_config?.url || ''}`).join('\n')
        if (!window.confirm(
          `当前为真实项目模式，批量中包含 ${unsafeCases.length} 个写操作用例：\n${unsafeList}${unsafeCases.length > 5 ? '\n  ...' : ''}\n\n可能修改真实测试环境数据，是否确认执行？`
        )) return
        allowUnsafe = true
      } else {
        if (!window.confirm(`确定要批量执行 ${apiCases.length} 个接口测试用例吗?`)) return
      }
    } else {
      if (!window.confirm(`确定要批量执行 ${apiCases.length} 个接口测试用例吗?`)) return
    }

    setIsExecuting(true)
    try {
      const result = await api.v2.testCases.batchExecute(apiCases.map(tc => tc.id), {
        environment_id: Number(selectedEnvironmentId),
        allow_unsafe_methods: allowUnsafe,
      })
      setExecutionResult({ ...result, is_batch: true })
      setShowResultDialog(true)
      setSelectedIds([])

      const statusById = {}
      ;(result.results || []).forEach(r => {
        statusById[r.case_id] = r.status
      })
      setTestCases(prev => prev.map(tc =>
        statusById[tc.id]
          ? { ...tc, status: statusById[tc.id], lastRun: new Date().toLocaleString() }
          : tc
      ))
    } catch (error) {
      let msg = error.message || '批量执行失败'
      try {
        const parsed = JSON.parse(msg.replace(/^API调用失败: \d+ /, ''))
        if (parsed.detail) msg = parsed.detail
      } catch {}
      alert('批量执行失败: ' + msg)
    } finally {
      setIsExecuting(false)
    }
  }

  const handleDownloadScript = () => {
    const blob = new Blob([generatedScript], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `test_${selectedTestCase.id}_${Date.now()}.py`
    a.click()
    URL.revokeObjectURL(url)
  }

  const handleManualTest = (testCase) => {
    setSelectedTestCase(testCase)
    const steps = testCase.steps || []
    setManualTestSteps(steps.map((step, index) => ({
      index: index + 1,
      description: step,
      status: 'pending', // pending, passed, failed
      note: ''
    })))
    setCurrentStepIndex(0)
    setManualTestNotes('')
    setShowManualTestDialog(true)
  }

  const handleStepResult = (index, status) => {
    setManualTestSteps(prev => prev.map((step, i) => 
      i === index ? { ...step, status } : step
    ))
    // 自动跳到下一步
    if (index < manualTestSteps.length - 1) {
      setCurrentStepIndex(index + 1)
    }
  }

  const handleStepNote = (index, note) => {
    setManualTestSteps(prev => prev.map((step, i) => 
      i === index ? { ...step, note } : step
    ))
  }

  const handleSubmitManualTest = async () => {
    // 检查是否所有步骤都已执行
    const pendingSteps = manualTestSteps.filter(s => s.status === 'pending')
    if (pendingSteps.length > 0) {
      if (!window.confirm(`还有 ${pendingSteps.length} 个步骤未执行，确定要提交吗？`)) {
        return
      }
    }

    // 计算最终状态
    const failedSteps = manualTestSteps.filter(s => s.status === 'failed')
    const finalStatus = failedSteps.length > 0 ? 'failed' : 'passed'

    try {
      const result = await api.testCases.manualExecute(selectedTestCase.id, {
        steps: manualTestSteps,
        notes: manualTestNotes,
        status: finalStatus
      })
      
      if (result.success) {
        alert(`手动测试已提交！\n状态: ${finalStatus === 'passed' ? '通过' : '失败'}`)
        
        // 更新测试用例状态
        setTestCases(prev => prev.map(tc => 
          tc.id === selectedTestCase.id 
            ? { ...tc, status: finalStatus, lastRun: new Date().toLocaleString() }
            : tc
        ))
        
        setShowManualTestDialog(false)
      } else {
        alert('提交失败: ' + result.error)
      }
    } catch (error) {
      alert('提交失败: ' + error.message)
    }
  }

  const handleSVNSuccess = (result) => {
    setShowSVNDialog(false)
    
    // 添加新生成的测试用例到列表
    const newTestCases = result.testcases.map((tc, index) => ({
      id: `svn_${Date.now()}_${index}`,
      title: tc.title,
      priority: tc.priority?.toLowerCase() || 'medium',
      status: 'not_run',
      lastRun: '-',
      source: 'svn',
      steps: tc.steps,
      expected: tc.expected,
      module: tc.module,
      type: tc.type
    }))
    
    setTestCases(prev => [...newTestCases, ...prev])
  }

  // Phase 16: 治理操作
  const handleGovern = async () => {
    if (!window.confirm('将自动给所有用例打标签（api_pattern / risk_level / destructive 等），确定？')) return
    setIsGoverning(true)
    try {
      const res = await api.v2.testCases.govern(true)
      alert(`治理完成：共 ${res.total} 条，已更新 ${res.updated} 条`)
      loadTestCases()
      loadGovSummary()
    } catch (e) { alert('治理失败: ' + e.message) }
    finally { setIsGoverning(false) }
  }

  const loadGovSummary = async () => {
    try { setGovSummary(await api.v2.testCases.governanceSummary()) } catch {}
  }
  // 首次加载治理概况 + Demo 状态
  useEffect(() => { loadGovSummary(); loadDemoStatus() }, [])

  // Phase 17: Demo 操作
  const loadDemoStatus = async () => {
    try {
      const res = await api.v2.demo.status()
      setDemoStatus(res?.data || null)
    } catch {}
  }

  const handleDemoInit = async () => {
    setDemoLoading(true)
    try {
      const res = await api.v2.demo.init()
      if (res.code === 0) {
        alert(`Demo 项目初始化成功！\n用例: ${res.data.test_case_count} 个\n治理: ${res.data.governed_count} 个`)
        loadTestCases()
        loadEnvironments()
        loadGovSummary()
        loadDemoStatus()
      } else {
        alert('初始化失败: ' + res.message)
      }
    } catch (e) { alert('初始化失败: ' + e.message) }
    finally { setDemoLoading(false) }
  }

  const handleDemoReset = async () => {
    if (!window.confirm('确定重置 Demo 项目？将清除所有 Demo 数据并重新初始化。')) return
    setDemoLoading(true)
    try {
      const res = await api.v2.demo.reset()
      if (res.code === 0) {
        alert(`Demo 项目已重置！\n用例: ${res.data.test_case_count} 个`)
        loadTestCases()
        loadEnvironments()
        loadGovSummary()
        loadDemoStatus()
      } else {
        alert('重置失败: ' + res.message)
      }
    } catch (e) { alert('重置失败: ' + e.message) }
    finally { setDemoLoading(false) }
  }

  const handlePresetExecute = async (preset) => {
    if (!selectedEnvironmentId) { alert('请先选择执行环境'); return }
    if (!window.confirm(`确定批量执行「${preset}」推荐测试集？将自动跳过破坏性用例。`)) return
    setPresetLoading(preset)
    try {
      const result = await api.v2.testCases.batchExecutePreset(preset, { environment_id: Number(selectedEnvironmentId) })
      setExecutionResult({ ...result, is_batch: true, preset })
      setShowResultDialog(true)
      loadTestCases()
    } catch (e) {
      let msg = e.message
      try { const p = JSON.parse(msg.replace(/^API调用失败: \d+ /, '')); if (p.detail) msg = p.detail } catch {}
      alert(`${preset} 执行失败: ` + msg)
    } finally { setPresetLoading('') }
  }

  // Phase 16: 治理字段筛选
  const govFilteredCases = filteredTestCases.filter(tc => {
    if (govFilter.risk_level && tc.risk_level !== govFilter.risk_level) return false
    if (govFilter.api_pattern && tc.api_pattern !== govFilter.api_pattern) return false
    if (govFilter.destructive === 'true' && !tc.destructive) return false
    if (govFilter.destructive === 'false' && tc.destructive) return false
    if (govFilter.assertion_status && tc.assertion_status !== govFilter.assertion_status) return false
    if (govFilter.failure_category && tc.failure_category !== govFilter.failure_category) return false
    if (govFilter.status && tc.status !== govFilter.status) return false
    return true
  })
  const hasGovFilter = Object.values(govFilter).some(v => v !== '')

  return (
    <div className="p-6">
      {/* Phase 18: Demo 项目提示 */}
      {demoStatus?.initialized && (
        <div className="mb-4 p-3 bg-indigo-50 border border-indigo-200 rounded-lg flex items-center justify-between">
          <div className="text-sm text-indigo-800">
            <span className="font-semibold">Demo 模式</span> - 当前为 ERP Demo System，数据来自 Mock API。
            用例 {demoStatus.test_case_count || 0} 个，执行 {demoStatus.run_count || 0} 次。
          </div>
          <button onClick={() => api.v2.demo.status().then(r => setDemoStatus(r?.data || null)).catch(() => {})} className="text-xs text-indigo-600 hover:underline">刷新</button>
        </div>
      )}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900"> 测试用例</h1>
          <p className="text-gray-600 mt-1">管理和生成测试用例</p>
        </div>
        <div className="flex space-x-3">
          <select
            value={selectedProjectId}
            onChange={(e) => handleProjectChange(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-lg bg-white text-sm"
          >
            <option value="">全部项目</option>
            {projects.map(p => (
              <option key={p.id} value={p.id}>{p.name}</option>
            ))}
          </select>
          <select
            value={selectedEnvironmentId}
            onChange={(e) => {
              setSelectedEnvironmentId(e.target.value)
              localStorage.setItem(EXECUTION_ENV_STORAGE_KEY, e.target.value)
            }}
            className="px-3 py-2 border border-gray-300 rounded-lg bg-white text-sm"
          >
            <option value="">选择执行环境</option>
            {environments.map(env => (
              <option key={env.id} value={env.id}>
                {env.name} - {env.base_url}
              </option>
            ))}
          </select>
          {selectedIds.length > 0 && (
            <>
              <button
                onClick={handleBatchExecute}
                disabled={isExecuting}
                className="px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 flex items-center space-x-2 transition-colors disabled:opacity-50"
              >
                <span>{isExecuting ? '执行中...' : `批量执行 (${selectedIds.length})`}</span>
              </button>
              <button
                onClick={handleBatchDelete}
                disabled={isDeleting}
                className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 flex items-center space-x-2 transition-colors disabled:opacity-50"
              >
                <span></span>
                <span>{isDeleting ? '删除中...' : `删除 (${selectedIds.length})`}</span>
              </button>
            </>
          )}
          <button
            onClick={handleExportExcel}
            className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 flex items-center space-x-2 transition-colors"
          >
            <span></span>
            <span>导出Excel</span>
          </button>
          <button
            onClick={() => setShowSVNDialog(true)}
            className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 flex items-center space-x-2 transition-colors"
          >
            <span>📦</span>
            <span>从SVN生成</span>
          </button>
          <button
            onClick={() => setShowUploadDialog(true)}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center space-x-2 transition-colors"
          >
            <span></span>
            <span>导入需求文档</span>
          </button>
          {/* Phase 17: Demo 按钮 */}
          <button
            onClick={handleDemoInit}
            disabled={demoLoading}
            className="px-4 py-2 bg-amber-500 text-white rounded-lg hover:bg-amber-600 flex items-center space-x-2 transition-colors disabled:opacity-50"
          >
            <span>{demoLoading ? '' : ''}</span>
            <span>{demoLoading ? '初始化中...' : '初始化Demo'}</span>
          </button>
          {demoStatus?.initialized && (
            <button
              onClick={handleDemoReset}
              disabled={demoLoading}
              className="px-3 py-2 bg-gray-500 text-white rounded-lg hover:bg-gray-600 text-sm transition-colors disabled:opacity-50"
            >
              重置Demo
            </button>
          )}
          <button
            onClick={handleAiReview}
            disabled={reviewLoading}
            className="px-4 py-2 bg-gradient-to-r from-indigo-600 to-purple-600 text-white rounded-lg hover:from-indigo-700 hover:to-purple-700 flex items-center space-x-2 transition-colors disabled:opacity-50"
          >
            <span>{reviewLoading ? '评审中...' : `AI评审${selectedProjectId ? '(当前项目)' : selectedIds.length > 0 ? `(${selectedIds.length}条)` : '(全部)'}`}</span>
          </button>
        </div>
      </div>
      
      <div className="bg-white rounded-lg shadow">
        <div className="p-6 border-b space-y-3">
          <div className="flex gap-2">
            {[
              { key: 'all', label: '全部', count: testCases.length },
              { key: 'functional', label: '功能测试', count: testCases.filter(tc => !['swagger','demo_swagger','demo_seed'].includes(tc.source)).length },
              { key: 'api', label: '接口测试', count: testCases.filter(tc => ['swagger','demo_swagger','demo_seed'].includes(tc.source)).length },
            ].map(tab => (
              <button
                key={tab.key}
                onClick={() => setSourceFilter(tab.key)}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                  sourceFilter === tab.key
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                {tab.label} ({tab.count})
              </button>
            ))}
          </div>
          {hiddenPetStoreSampleCount > 0 && (
            <div className="px-3 py-2 bg-amber-50 border border-amber-200 rounded-lg text-sm text-amber-700">
              已根据当前执行环境隐藏 {hiddenPetStoreSampleCount} 条 PetStore 示例 Swagger 用例，避免误用蓝点环境执行示例接口。
            </div>
          )}
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="搜索测试用例..."
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />

          {/* Phase 16: 推荐测试集快捷按钮（仅接口测试 tab） */}
          {sourceFilter === 'api' && <div className="flex flex-wrap gap-2 items-center">
            <span className="text-sm text-gray-500 font-medium">推荐集:</span>
            {[
              { key: 'query-safe', label: '查询安全集', color: 'bg-green-100 text-green-700 hover:bg-green-200' },
              { key: 'smoke', label: '冒烟测试集', color: 'bg-blue-100 text-blue-700 hover:bg-blue-200' },
              { key: 'p0', label: 'P0测试集', color: 'bg-red-100 text-red-700 hover:bg-red-200' },
              { key: 'failed-rerun', label: '失败重跑集', color: 'bg-orange-100 text-orange-700 hover:bg-orange-200' },
              { key: 'regression', label: '回归测试集', color: 'bg-purple-100 text-purple-700 hover:bg-purple-200' },
            ].map(p => (
              <button
                key={p.key}
                disabled={!!presetLoading}
                onClick={() => handlePresetExecute(p.key)}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${p.color} disabled:opacity-50`}
              >
                {presetLoading === p.key ? '执行中...' : p.label}
              </button>
            ))}
            <button
              onClick={handleGovern}
              disabled={isGoverning}
              className="px-3 py-1.5 rounded-lg text-xs font-medium bg-gray-200 text-gray-700 hover:bg-gray-300 disabled:opacity-50"
            >
              {isGoverning ? '治理中...' : '一键治理'}
            </button>
            {govSummary && (
              <span className="text-xs text-gray-400">
                已治理 {govSummary.governed}/{govSummary.total} | 破坏性 {govSummary.destructive_count} | 无断言 {govSummary.no_assertion_count} | 失败 {govSummary.failed_count}
              </span>
            )}
          </div>}

          {/* Phase 16: 治理字段筛选（仅接口测试 tab） */}
          {sourceFilter === 'api' && <div className="flex flex-wrap gap-2 items-center">
            <span className="text-sm text-gray-500 font-medium">筛选:</span>
            <select value={govFilter.status} onChange={e => setGovFilter(f => ({...f, status: e.target.value}))} className="px-2 py-1 border rounded text-xs">
              <option value="">状态</option>
              <option value="passed">通过</option>
              <option value="failed">失败</option>
              <option value="error">错误</option>
              <option value="no_assertion">无断言</option>
              <option value="pending">待运行</option>
            </select>
            <select value={govFilter.risk_level} onChange={e => setGovFilter(f => ({...f, risk_level: e.target.value}))} className="px-2 py-1 border rounded text-xs">
              <option value="">风险等级</option>
              <option value="P0">P0</option>
              <option value="P1">P1</option>
              <option value="P2">P2</option>
            </select>
            <select value={govFilter.api_pattern} onChange={e => setGovFilter(f => ({...f, api_pattern: e.target.value}))} className="px-2 py-1 border rounded text-xs">
              <option value="">接口类型</option>
              <option value="list">list</option>
              <option value="page">page</option>
              <option value="detail">detail</option>
              <option value="save">save</option>
              <option value="modify">modify</option>
              <option value="delete">delete</option>
              <option value="unknown">unknown</option>
            </select>
            <select value={govFilter.destructive} onChange={e => setGovFilter(f => ({...f, destructive: e.target.value}))} className="px-2 py-1 border rounded text-xs">
              <option value="">破坏性</option>
              <option value="true">是</option>
              <option value="false">否</option>
            </select>
            <select value={govFilter.assertion_status} onChange={e => setGovFilter(f => ({...f, assertion_status: e.target.value}))} className="px-2 py-1 border rounded text-xs">
              <option value="">断言</option>
              <option value="has_assertion">有断言</option>
              <option value="no_assertion">无断言</option>
            </select>
            <select value={govFilter.failure_category} onChange={e => setGovFilter(f => ({...f, failure_category: e.target.value}))} className="px-2 py-1 border rounded text-xs">
              <option value="">失败分类</option>
              <option value="auth_error">认证失败</option>
              <option value="env_error">环境错误</option>
              <option value="request_error">请求错误</option>
              <option value="response_error">服务端错误</option>
              <option value="assertion_error">断言失败</option>
              <option value="dependency_error">依赖错误</option>
              <option value="timeout_error">超时</option>
              <option value="unknown_error">未知错误</option>
            </select>
            {hasGovFilter && (
              <button onClick={() => setGovFilter({ risk_level: '', api_pattern: '', destructive: '', assertion_status: '', failure_category: '', status: '' })} className="px-2 py-1 text-xs text-red-500 hover:text-red-700">清除筛选</button>
            )}
          </div>}
        </div>
        
        <div className="p-6 overflow-x-auto">
          {loading ? (
            <div className="flex items-center justify-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
              <span className="ml-2 text-gray-500">加载中...</span>
            </div>
          ) : (
            <table className="w-full table-fixed min-w-[900px]">
              <thead>
                <tr className="border-b">
                  <th className="py-3 px-4 text-gray-600 font-medium w-10">
                    <input
                      type="checkbox"
                      checked={govFilteredCases.length > 0 && selectedIds.length === govFilteredCases.length}
                      onChange={handleSelectAll}
                      className="w-4 h-4 text-blue-600 rounded focus:ring-2 focus:ring-blue-500"
                    />
                  </th>
                  <th className="text-left py-3 px-4 text-gray-600 font-medium w-[30%]">用例名称</th>
                  <th className="text-left py-3 px-4 text-gray-600 font-medium w-[14%]">模块</th>
                  <th className="text-left py-3 px-4 text-gray-600 font-medium w-[8%]">风险</th>
                  <th className="text-left py-3 px-4 text-gray-600 font-medium w-[8%]">{sourceFilter === 'api' ? '接口类型' : sourceFilter === 'functional' ? '优先级' : '类型'}</th>
                  <th className="text-left py-3 px-4 text-gray-600 font-medium w-[8%]">来源</th>
                  <th className="text-left py-3 px-4 text-gray-600 font-medium w-[10%]">状态</th>
                  <th className="text-left py-3 px-4 text-gray-600 font-medium w-[18%]">操作</th>
                </tr>
              </thead>
              <tbody>
                {govFilteredCases.length === 0 ? (
                  <tr>
                    <td colSpan={10} className="py-8 text-center text-gray-500">
                      {searchQuery || hasGovFilter ? '未找到匹配的测试用例' : '暂无测试用例，请导入需求文档生成'}
                    </td>
                  </tr>
                ) : govFilteredCases.map((tc, index) => {
                  const priorityMap = { 
                    high: { cls: 'bg-red-100 text-red-700', label: '高' }, 
                    medium: { cls: 'bg-yellow-100 text-yellow-700', label: '中' }, 
                    low: { cls: 'bg-green-100 text-green-700', label: '低' } 
                  }
                  const statusMap = { 
                    passed: { cls: 'bg-green-100 text-green-700', label: '通过' }, 
                    failed: { cls: 'bg-red-100 text-red-700', label: '失败' }, 
                    error: { cls: 'bg-red-100 text-red-700', label: '错误' },
                    no_assertion: { cls: 'bg-yellow-100 text-yellow-700', label: '无断言' },
                    pending: { cls: 'bg-gray-100 text-gray-700', label: '待运行' } 
                  }
                  const p = priorityMap[tc.priority] || { cls: 'bg-gray-100 text-gray-700', label: tc.priority || '-' }
                  const s = statusMap[tc.status] || { cls: 'bg-gray-100 text-gray-700', label: tc.status || '-' }
                  
                  // 使用组合key避免重复
                  const uniqueKey = `${tc.id}-${index}`;
                  
                  return (
                    <tr key={uniqueKey} className="border-b hover:bg-gray-50 transition-colors">
                      <td className="py-4 px-4">
                        <input
                          type="checkbox"
                          checked={selectedIds.includes(tc.id)}
                          onChange={() => handleSelectOne(tc.id)}
                          className="w-4 h-4 text-blue-600 rounded focus:ring-2 focus:ring-blue-500"
                        />
                      </td>
                      <td className="py-4 px-4 font-medium truncate" title={tc.title}>
                        {tc.title?.replace(/^(测试用例标题|测试点|用例标题|标题)[:：]\s*/, '') || tc.title}
                      </td>
                      <td className="py-4 px-4 text-gray-600">{tc.module_name || tc.module || '-'}</td>
                      <td className="py-4 px-4">
                        {tc.risk_level ? (
                          <span className={`px-2 py-1 rounded text-xs font-medium ${
                            tc.risk_level === 'P0' ? 'bg-red-100 text-red-700' :
                            tc.risk_level === 'P1' ? 'bg-orange-100 text-orange-700' :
                            'bg-gray-100 text-gray-600'
                          }`}>{tc.risk_level}</span>
                        ) : <span className="text-gray-300 text-xs">-</span>}
                        {tc.destructive && <span className="ml-1 px-1 bg-red-50 text-red-600 text-xs rounded border border-red-200" title="破坏性接口">破坏</span>}
                      </td>
                      <td className="py-4 px-4">
                        {sourceFilter === 'functional' || (!['swagger','demo_swagger','demo_seed'].includes(tc.source) && sourceFilter === 'all') ? (
                          <span className={`px-2 py-1 rounded text-xs font-medium ${p.cls}`}>{p.label}</span>
                        ) : (
                          <span className="px-2 py-1 bg-gray-100 text-gray-600 rounded text-xs">{tc.api_pattern || '-'}</span>
                        )}
                      </td>
                      <td className="py-4 px-4">
                        <span className="px-2 py-1 bg-blue-100 text-blue-700 rounded text-xs">
                          {sourceLabel(tc.source)}
                        </span>
                      </td>
                      <td className="py-4 px-4">
                        <span className={`px-2 py-1 rounded text-sm ${s.cls}`}>{s.label}</span>
                        {tc.failure_category && <div className="text-xs text-red-400 mt-0.5">{tc.failure_category}</div>}
                      </td>
                      <td className="py-4 px-4">
                        <div className="flex space-x-2">
                          <button
                            onClick={() => handleViewDetail(tc)}
                            className="px-3 py-1 bg-blue-50 text-blue-600 rounded hover:bg-blue-100 text-sm"
                          >
                            查看详情
                          </button>
                          {['swagger', 'demo_swagger', 'demo_seed'].includes(tc.source) ? (
                            <>
                              <button
                                onClick={() => handleGenerateScript(tc)}
                                className="px-3 py-1 bg-purple-50 text-purple-600 rounded hover:bg-purple-100 text-sm flex items-center space-x-1"
                                title="生成自动化脚本"
                              >
                                <span></span>
                                <span>生成脚本</span>
                              </button>
                              <button
                                onClick={() => handleExecuteTest(tc)}
                                className="px-3 py-1 bg-green-50 text-green-600 rounded hover:bg-green-100 text-sm flex items-center space-x-1"
                                title="自动化执行"
                              >
                                <span></span>
                                <span>自动执行</span>
                              </button>
                            </>
                          ) : (
                            <button
                              onClick={() => handleManualTest(tc)}
                              className="px-3 py-1 bg-indigo-50 text-indigo-600 rounded hover:bg-indigo-100 text-sm flex items-center space-x-1"
                              title="手动功能测试"
                            >
                              <span></span>
                              <span>手动测试</span>
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          )}
        </div>
      </div>

      {/* 上传对话框 */}
      {showUploadDialog && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl p-6 w-[500px]">
            <h2 className="text-xl font-bold mb-4"> AI生成测试用例</h2>
            
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                选择需求文档
              </label>
              <input
                type="file"
                accept=".docx,.xlsx,.pdf,.doc,.xls,.txt"
                onChange={(e) => setUploadFile(e.target.files[0])}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              {uploadFile && (
                <p className="mt-2 text-sm text-green-600 flex items-center">
                  <span className="mr-1">✓</span>
                  已选择: {uploadFile.name}
                </p>
              )}
            </div>

            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
              <div className="flex items-start space-x-2">
                <span className="text-blue-600 mt-0.5"></span>
                <div className="text-sm text-blue-800">
                  <p className="font-medium mb-1">AI将自动执行以下步骤:</p>
                  <ul className="list-disc list-inside space-y-1 text-xs">
                    <li>加载项目知识库（接口路由、响应结构、鉴权方式）</li>
                    <li>解析需求文档，拆分功能模块</li>
                    <li>结合项目上下文生成测试点和场景</li>
                    <li>生成完整测试用例（含业务断言 code==200）</li>
                    <li>覆盖功能 / 边界 / 异常 / 安全测试</li>
                  </ul>
                  <p className="mt-2 text-xs text-blue-600">⏱️ 预计需要 1-2 分钟（AI模式），知识库已就绪</p>
                </div>
              </div>
            </div>

            {isGenerating && (
              <div className="mb-4">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-gray-700">{generationStep}</span>
                  <span className="text-sm text-gray-500">{generationProgress}%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2.5">
                  <div 
                    className="bg-blue-600 h-2.5 rounded-full transition-all duration-500"
                    style={{ width: `${generationProgress}%` }}
                  ></div>
                </div>
                <div className="mt-2 flex items-center space-x-2 text-xs text-gray-500">
                  <div className="animate-spin rounded-full h-3 w-3 border-b-2 border-blue-600"></div>
                  <span>AI正在处理中,请稍候...</span>
                </div>
              </div>
            )}

            <div className="flex justify-end space-x-3">
              <button
                onClick={() => {
                  if (isGenerating) {
                    // 如果正在生成,提示用户
                    if (window.confirm('AI正在生成中,确定要取消吗?')) {
                      setShowUploadDialog(false)
                      setUploadFile(null)
                      setIsGenerating(false)
                      setGenerationProgress(0)
                      setGenerationStep('')
                    }
                  } else {
                    setShowUploadDialog(false)
                    setUploadFile(null)
                  }
                }}
                className={`px-4 py-2 border border-gray-300 rounded-lg transition-colors ${
                  isGenerating 
                    ? 'bg-red-50 border-red-300 text-red-700 hover:bg-red-100' 
                    : 'hover:bg-gray-50'
                }`}
              >
                {isGenerating ? '强制取消' : '取消'}
              </button>
              <button
                onClick={handleFileUpload}
                disabled={!uploadFile || isGenerating}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center space-x-2"
              >
                {isGenerating ? (
                  <>
                    <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                    <span>AI生成中...</span>
                  </>
                ) : (
                  <>
                    <span></span>
                    <span>开始生成</span>
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* SVN 生成对话框 */}
      {showSVNDialog && (
        <SVNInput
          onSuccess={handleSVNSuccess}
          onCancel={() => setShowSVNDialog(false)}
        />
      )}

      {/* 数据集选择对话框 */}
      {showDatasetDialog && selectedTestCase && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl p-6 w-[600px] max-h-[80vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-bold"> 选择测试数据集</h2>
              <button
                onClick={() => {
                  setShowDatasetDialog(false)
                  setSelectedDataset(null)
                }}
                className="text-gray-400 hover:text-gray-600"
              >
                ✕
              </button>
            </div>
            
            <div className="mb-4 p-3 bg-blue-50 rounded border border-blue-200">
              <p className="text-sm text-blue-800">
                <span className="font-medium">测试用例:</span> {selectedTestCase.title?.replace(/^(测试用例标题|测试点|用例标题|标题)[:：]\s*/, '') || selectedTestCase.title}
              </p>
            </div>

            <div className="space-y-3 mb-6">
              {datasets.length === 0 ? (
                <div className="text-center py-8 text-gray-500">
                  <p>暂无可用数据集</p>
                  <p className="text-sm mt-2">请先在API管理中生成并保存数据集</p>
                </div>
              ) : (
                datasets.map((dataset) => (
                  <div
                    key={dataset.id}
                    onClick={() => setSelectedDataset(dataset.id)}
                    className={`p-4 border rounded-lg cursor-pointer transition-all ${
                      selectedDataset === dataset.id
                        ? 'border-blue-500 bg-blue-50'
                        : 'border-gray-200 hover:border-blue-300'
                    }`}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <h3 className="font-medium text-gray-900">{dataset.name}</h3>
                        <p className="text-sm text-gray-600 mt-1">{dataset.description || '无描述'}</p>
                        <div className="flex items-center space-x-4 mt-2 text-xs text-gray-500">
                          <span>创建时间: {new Date(dataset.created_at).toLocaleString()}</span>
                          <span>使用次数: {dataset.usage_count || 0}</span>
                        </div>
                      </div>
                      {selectedDataset === dataset.id && (
                        <div className="ml-3">
                          <span className="inline-block w-5 h-5 bg-blue-500 text-white rounded-full flex items-center justify-center text-xs">
                            ✓
                          </span>
                        </div>
                      )}
                    </div>
                  </div>
                ))
              )}
            </div>

            <div className="flex justify-end space-x-3">
              <button
                onClick={() => {
                  setShowDatasetDialog(false)
                  setSelectedDataset(null)
                }}
                className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
              >
                取消
              </button>
              <button
                onClick={handleBindDataset}
                disabled={!selectedDataset}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                绑定数据集
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 测试用例详情对话框 */}
      {showDetailDialog && selectedTestCase && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl p-6 w-[700px] max-h-[80vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-bold">测试用例详情</h2>
              <button
                onClick={() => setShowDetailDialog(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                ✕
              </button>
            </div>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">用例标题</label>
                <div className="p-3 bg-gray-50 rounded border">
                  {selectedTestCase.title?.replace(/^(测试用例标题|测试点|用例标题|标题)[:：]\s*/, '') || selectedTestCase.title}
                </div>
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">模块</label>
                  <div className="p-3 bg-gray-50 rounded border">{selectedTestCase.module || '-'}</div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">优先级</label>
                  <div className="p-3 bg-gray-50 rounded border">{selectedTestCase.priority}</div>
                </div>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">测试步骤</label>
                <div className="p-3 bg-gray-50 rounded border">
                  {selectedTestCase.steps && selectedTestCase.steps.length > 0 ? (
                    <ol className="list-decimal list-inside space-y-1">
                      {selectedTestCase.steps.map((step, index) => (
                        <li key={index} className="text-gray-700">{step}</li>
                      ))}
                    </ol>
                  ) : (
                    <p className="text-gray-500">暂无测试步骤</p>
                  )}
                </div>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">预期结果</label>
                <div className="p-3 bg-gray-50 rounded border">{selectedTestCase.expected || '-'}</div>
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">状态</label>
                  <div className="p-3 bg-gray-50 rounded border">{selectedTestCase.status}</div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">最后运行</label>
                  <div className="p-3 bg-gray-50 rounded border">{selectedTestCase.lastRun}</div>
                </div>
              </div>
            </div>
            
            <div className="mt-6 flex justify-end">
              <button
                onClick={() => setShowDetailDialog(false)}
                className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300"
              >
                关闭
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 脚本生成对话框 */}
      {showScriptDialog && selectedTestCase && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl p-6 w-[800px] max-h-[80vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-bold"> 自动化脚本</h2>
              <button
                onClick={() => setShowScriptDialog(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                ✕
              </button>
            </div>
            
            <div className="mb-4 p-3 bg-blue-50 rounded border border-blue-200">
              <p className="text-sm text-blue-800">
                <span className="font-medium">测试用例:</span> {selectedTestCase.title?.replace(/^(测试用例标题|测试点|用例标题|标题)[:：]\s*/, '') || selectedTestCase.title}
              </p>
            </div>

            {isGeneratingScript ? (
              <div className="flex items-center justify-center py-12">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                <span className="ml-3 text-gray-600">AI正在生成脚本...</span>
              </div>
            ) : (
              <div>
                <div className="mb-4">
                  <label className="block text-sm font-medium text-gray-700 mb-2">生成的测试脚本</label>
                  <pre className="bg-gray-900 text-green-400 p-4 rounded-lg overflow-x-auto text-sm font-mono max-h-96">
                    {generatedScript || '# 脚本生成中...'}
                  </pre>
                </div>

                <div className="flex justify-end space-x-3">
                  <button
                    onClick={() => setShowScriptDialog(false)}
                    className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
                  >
                    关闭
                  </button>
                  <button
                    onClick={handleDownloadScript}
                    disabled={!generatedScript}
                    className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 flex items-center space-x-2"
                  >
                    <span></span>
                    <span>下载脚本</span>
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* 测试执行结果对话框 (Phase 11+13) */}
      {showResultDialog && executionResult && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl p-6 w-[850px] max-h-[85vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-bold">
                {executionResult.status === 'passed' ? '✅' : executionResult.status === 'no_assertion' ? '⚠️' : '❌'} {executionResult.is_batch ? '批量执行结果' : '接口测试结果'}
              </h2>
              <button onClick={() => setShowResultDialog(false)} className="text-gray-400 hover:text-gray-600 text-xl">✕</button>
            </div>
            
            <div className="mb-4 p-3 bg-blue-50 rounded border border-blue-200">
              <p className="text-sm text-blue-800">
                <span className="font-medium">{executionResult.is_batch ? '批量执行:' : '用例:'}</span> {executionResult.is_batch ? `${executionResult.total_cases || 0} 个接口用例` : selectedTestCase?.title}
              </p>
              {executionResult.run_id && <p className="text-xs text-blue-600 mt-1">Run ID: {executionResult.run_id}</p>}
            </div>

            {/* Phase 18: 增强状态概览 */}
            {executionResult.is_batch ? (
              <div className="mb-4">
                <div className="grid grid-cols-6 gap-2 mb-3">
                  <div className="p-2.5 bg-gray-50 rounded border text-center">
                    <div className="text-xs text-gray-500">总用例</div>
                    <div className="text-lg font-bold">{executionResult.total_cases || 0}</div>
                  </div>
                  <div className="p-2.5 bg-green-50 rounded border text-center">
                    <div className="text-xs text-gray-500">通过</div>
                    <div className="text-lg font-bold text-green-600">{executionResult.passed_cases || 0}</div>
                  </div>
                  <div className="p-2.5 bg-red-50 rounded border text-center">
                    <div className="text-xs text-gray-500">失败</div>
                    <div className="text-lg font-bold text-red-600">{executionResult.failed_cases || 0}</div>
                  </div>
                  <div className="p-2.5 bg-gray-50 rounded border text-center">
                    <div className="text-xs text-gray-500">跳过</div>
                    <div className="text-lg font-bold text-gray-500">{executionResult.skipped_cases || 0}</div>
                  </div>
                  <div className="p-2.5 bg-blue-50 rounded border text-center">
                    <div className="text-xs text-gray-500">通过率</div>
                    <div className="text-lg font-bold text-blue-600">{executionResult.pass_rate ?? '-'}%</div>
                  </div>
                  <div className="p-2.5 bg-gray-50 rounded border text-center">
                    <div className="text-xs text-gray-500">耗时</div>
                    <div className="text-lg font-bold">{(executionResult.duration_ms || 0).toFixed(0)}ms</div>
                  </div>
                </div>
                {/* Phase 18: 失败分类统计 */}
                {executionResult.failure_categories && Object.keys(executionResult.failure_categories).length > 0 && (
                  <div className="flex flex-wrap gap-2 mb-2">
                    <span className="text-xs text-gray-500 leading-6">失败分类:</span>
                    {Object.entries(executionResult.failure_categories).map(([k, v]) => (
                      <span key={k} className="px-2 py-0.5 bg-red-50 text-red-700 text-xs rounded border border-red-200">{k}: {v}</span>
                    ))}
                  </div>
                )}
                {/* Phase 18: 跳过原因统计 */}
                {executionResult.skipped_reasons && Object.keys(executionResult.skipped_reasons).length > 0 && (
                  <div className="flex flex-wrap gap-2 mb-2">
                    <span className="text-xs text-gray-500 leading-6">跳过原因:</span>
                    {Object.entries(executionResult.skipped_reasons).map(([k, v]) => (
                      <span key={k} className="px-2 py-0.5 bg-gray-100 text-gray-700 text-xs rounded border border-gray-200">{k}: {v}</span>
                    ))}
                  </div>
                )}
              </div>
            ) : (
              <div className="grid grid-cols-4 gap-3 mb-4">
                <div className="p-3 bg-gray-50 rounded border text-center">
                  <div className="text-xs text-gray-500">状态</div>
                  <div className={`text-base font-bold ${
                    executionResult.status === 'passed' ? 'text-green-600' :
                    executionResult.status === 'no_assertion' ? 'text-yellow-600' : 'text-red-600'
                  }`}>
                    {executionResult.status === 'passed' ? '通过' :
                     executionResult.status === 'no_assertion' ? '无断言' :
                     executionResult.status === 'failed' ? '失败' : '错误'}
                  </div>
                </div>
                <div className="p-3 bg-gray-50 rounded border text-center">
                  <div className="text-xs text-gray-500">耗时</div>
                  <div className="text-base font-bold">{(executionResult.duration_ms || 0).toFixed(0)}ms</div>
                </div>
                <div className="p-3 bg-gray-50 rounded border text-center">
                  <div className="text-xs text-gray-500">断言通过</div>
                  <div className="text-base font-bold text-green-600">{executionResult.assertion_summary?.passed || 0}</div>
                </div>
                <div className="p-3 bg-gray-50 rounded border text-center">
                  <div className="text-xs text-gray-500">断言失败</div>
                  <div className="text-base font-bold text-red-600">{executionResult.assertion_summary?.failed || 0}</div>
                </div>
              </div>
            )}

            {/* 提示信息 */}
            {executionResult.message && (
              <div className={`p-3 rounded border mb-4 text-sm ${
                executionResult.status === 'passed' ? 'bg-green-50 border-green-200 text-green-800' :
                executionResult.status === 'no_assertion' ? 'bg-yellow-50 border-yellow-200 text-yellow-800' :
                'bg-red-50 border-red-200 text-red-800'
              }`}>{executionResult.message}</div>
            )}

            {/* 批量执行明细 */}
            {executionResult.is_batch && executionResult.results && (
              <div className="mb-4">
                <h3 className="text-sm font-semibold mb-2">用例执行明细</h3>
                <div className="border rounded overflow-hidden max-h-72 overflow-y-auto">
                  <table className="w-full text-sm">
                    <thead className="bg-gray-100 sticky top-0">
                      <tr>
                        <th className="py-2 px-3 text-left">用例ID</th>
                        <th className="py-2 px-3 text-left">用例名称</th>
                        <th className="py-2 px-3 text-center">状态</th>
                        <th className="py-2 px-3 text-center">失败分类</th>
                        <th className="py-2 px-3 text-right">耗时</th>
                        <th className="py-2 px-3 text-left">错误信息</th>
                      </tr>
                    </thead>
                    <tbody>
                      {executionResult.results.map((r) => (
                        <tr key={r.case_id} className={`border-t ${
                          r.status === 'failed' || r.status === 'error' ? 'bg-red-50' :
                          r.status === 'skipped' ? 'bg-gray-50' :
                          r.status === 'no_assertion' ? 'bg-yellow-50' : ''
                        }`}>
                          <td className="py-2 px-3 font-mono text-xs">{r.case_id}</td>
                          <td className="py-2 px-3 text-xs max-w-[260px] truncate">{r.case_name}</td>
                          <td className="py-2 px-3 text-center">
                            <span className={`px-2 py-0.5 rounded text-xs ${
                              r.status === 'passed' ? 'bg-green-100 text-green-700' :
                              r.status === 'skipped' ? 'bg-gray-200 text-gray-600' :
                              r.status === 'no_assertion' ? 'bg-yellow-100 text-yellow-700' :
                              'bg-red-100 text-red-700'
                            }`}>
                              {r.status === 'passed' ? '通过' : r.status === 'skipped' ? '跳过' : r.status === 'no_assertion' ? '无断言' : r.status === 'failed' ? '失败' : '错误'}
                            </span>
                          </td>
                          <td className="py-2 px-3 text-center text-xs">
                            {r.failure_category ? <span className="px-1.5 py-0.5 bg-red-50 text-red-600 rounded">{r.failure_category}</span> :
                             r.skipped_reason ? <span className="px-1.5 py-0.5 bg-gray-100 text-gray-600 rounded">{r.skipped_reason}</span> : '-'}
                          </td>
                          <td className="py-2 px-3 text-right text-xs">{(r.duration_ms || 0).toFixed(0)}ms</td>
                          <td className="py-2 px-3 text-xs text-red-600 max-w-[220px] truncate">{r.error_message || r.skipped_message || '-'}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                {(executionResult.no_assertion_cases || 0) > 0 && (
                  <div className="mt-2 text-xs text-yellow-700 bg-yellow-50 border border-yellow-200 rounded p-2">
                    ⚠️ 无断言用例 {executionResult.no_assertion_cases} 个，未计入通过用例。
                  </div>
                )}
              </div>
            )}

            {/* 断言详情 (Phase 13) */}
            {executionResult.assertion_details && executionResult.assertion_details.length > 0 && (
              <div className="mb-4">
                <h3 className="text-sm font-semibold mb-2">断言详情</h3>
                <div className="border rounded overflow-hidden">
                  <table className="w-full text-sm">
                    <thead className="bg-gray-100">
                      <tr>
                        <th className="py-2 px-3 text-left">类型</th>
                        <th className="py-2 px-3 text-left">路径</th>
                        <th className="py-2 px-3 text-left">期望值</th>
                        <th className="py-2 px-3 text-left">实际值</th>
                        <th className="py-2 px-3 text-center">结果</th>
                      </tr>
                    </thead>
                    <tbody>
                      {executionResult.assertion_details.map((a, i) => (
                        <tr key={i} className={`border-t ${a.passed ? '' : 'bg-red-50'}`}>
                          <td className="py-2 px-3 font-mono text-xs">{a.type}</td>
                          <td className="py-2 px-3 font-mono text-xs">{a.path || '-'}</td>
                          <td className="py-2 px-3 text-xs">{JSON.stringify(a.expected)}</td>
                          <td className="py-2 px-3 text-xs">{JSON.stringify(a.actual)}</td>
                          <td className="py-2 px-3 text-center">
                            {a.passed
                              ? <span className="text-green-600 font-bold">✓</span>
                              : <span className="text-red-600 font-bold" title={a.message}>✗</span>}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* 请求快照 */}
            {executionResult.request_snapshot && (
              <details className="mb-3">
                <summary className="text-sm font-semibold cursor-pointer text-gray-700">请求详情</summary>
                <pre className="mt-2 bg-gray-900 text-green-400 p-3 rounded text-xs font-mono max-h-48 overflow-auto">
                  {JSON.stringify(executionResult.request_snapshot, null, 2)}
                </pre>
              </details>
            )}

            {/* 响应快照 */}
            {executionResult.response_snapshot && (
              <details className="mb-3">
                <summary className="text-sm font-semibold cursor-pointer text-gray-700">响应详情</summary>
                <pre className="mt-2 bg-gray-900 text-blue-400 p-3 rounded text-xs font-mono max-h-48 overflow-auto">
                  {JSON.stringify(executionResult.response_snapshot, null, 2)}
                </pre>
              </details>
            )}

            {/* 错误信息 */}
            {executionResult.error_message && (
              <div className="p-3 bg-red-50 border border-red-200 rounded mb-4">
                <div className="text-sm font-medium text-red-800 mb-1">错误信息</div>
                <div className="text-sm text-red-700">{executionResult.error_message}</div>
              </div>
            )}

            {/* Phase 19: AI Analysis Display */}
            {aiAnalysis && (
              <div className="mt-4 p-4 bg-gradient-to-r from-indigo-50 to-purple-50 rounded-lg border border-indigo-200">
                <div className="flex items-center justify-between mb-3">
                  <h3 className="text-lg font-bold text-indigo-800">AI 质量分析</h3>
                  <span className="text-xs px-2 py-1 bg-indigo-100 text-indigo-600 rounded">
                    {aiAnalysis.provider === 'rule_based' ? '规则分析' : 'AI 大模型'}
                  </span>
                </div>
                <div className="grid grid-cols-2 gap-3 mb-3">
                  <div className="text-center p-3 bg-white rounded-lg shadow-sm">
                    <div className={`text-3xl font-bold ${aiAnalysis.health_score >= 85 ? 'text-green-600' : aiAnalysis.health_score >= 60 ? 'text-yellow-600' : 'text-red-600'}`}>
                      {aiAnalysis.health_score}
                    </div>
                    <div className="text-xs text-gray-500">健康评分</div>
                  </div>
                  <div className="text-center p-3 bg-white rounded-lg shadow-sm">
                    <div className={`text-lg font-bold ${aiAnalysis.release_recommendation === 'pass' ? 'text-green-600' : aiAnalysis.release_recommendation === 'caution' ? 'text-yellow-600' : 'text-red-600'}`}>
                      {aiAnalysis.release_recommendation === 'pass' ? '✅ 可发布' : aiAnalysis.release_recommendation === 'caution' ? '⚠️ 谨慎发布' : '🚫 不建议发布'}
                    </div>
                    <div className="text-xs text-gray-500">发布建议</div>
                  </div>
                </div>
                <p className="text-sm text-gray-700 mb-2">{aiAnalysis.summary}</p>
                {aiAnalysis.key_findings && aiAnalysis.key_findings.length > 0 && (
                  <details className="mb-2">
                    <summary className="text-sm font-medium text-indigo-700 cursor-pointer">关键发现 ({aiAnalysis.key_findings.length})</summary>
                    <ul className="text-xs text-gray-600 mt-1 ml-4 list-disc">
                      {aiAnalysis.key_findings.map((f, i) => <li key={i}>{f}</li>)}
                    </ul>
                  </details>
                )}
                {aiAnalysis.risk_points && aiAnalysis.risk_points.length > 0 && (
                  <details className="mb-2">
                    <summary className="text-sm font-medium text-red-700 cursor-pointer">风险点 ({aiAnalysis.risk_points.length})</summary>
                    <ul className="text-xs text-gray-600 mt-1 ml-4 list-disc">
                      {aiAnalysis.risk_points.map((r, i) => <li key={i}><span className={`font-bold ${r.level === 'high' ? 'text-red-600' : r.level === 'medium' ? 'text-yellow-600' : 'text-blue-600'}`}>[{r.level.toUpperCase()}]</span> {r.description}</li>)}
                    </ul>
                  </details>
                )}
                {aiAnalysis.suggestions && aiAnalysis.suggestions.length > 0 && (
                  <details className="mb-2">
                    <summary className="text-sm font-medium text-green-700 cursor-pointer">修复建议 ({aiAnalysis.suggestions.length})</summary>
                    <ul className="text-xs text-gray-600 mt-1 ml-4 list-disc">
                      {aiAnalysis.suggestions.map((s, i) => <li key={i}>{s}</li>)}
                    </ul>
                  </details>
                )}
                {aiAnalysis.next_actions && aiAnalysis.next_actions.length > 0 && (
                  <details>
                    <summary className="text-sm font-medium text-blue-700 cursor-pointer">下一步行动 ({aiAnalysis.next_actions.length})</summary>
                    <ul className="text-xs text-gray-600 mt-1 ml-4 list-disc">
                      {aiAnalysis.next_actions.map((a, i) => <li key={i}><span className={`font-bold ${a.priority === 'high' ? 'text-red-600' : a.priority === 'medium' ? 'text-yellow-600' : 'text-blue-600'}`}>[{a.priority.toUpperCase()}]</span> {a.action}</li>)}
                    </ul>
                  </details>
                )}
              </div>
            )}

            <div className="mt-4 flex justify-between">
              <div className="flex space-x-2">
                {executionResult.run_id && (
                  <button
                    onClick={() => { setShowResultDialog(false); navigate('/test-runs-v2') }}
                    className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm"
                  >
                    查看执行记录
                  </button>
                )}
                {executionResult.run_id && (
                  <button
                    onClick={async () => {
                      try {
                        await api.v2.observability.generateReport(executionResult.run_id)
                        window.open(`/api/v2/test-runs/${executionResult.run_id}/report/download?format=html`, '_blank')
                      } catch (e) { alert('报告生成失败: ' + e.message) }
                    }}
                    className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 text-sm"
                  >
                    生成HTML报告
                  </button>
                )}
                {executionResult.run_id && (
                  <button
                    disabled={aiAnalysisLoading}
                    onClick={async () => {
                      setAiAnalysisLoading(true)
                      try {
                        const force = !!aiAnalysis
                        const res = await api.v2.observability.generateAiAnalysis(executionResult.run_id, force)
                        setAiAnalysis(res.data || res)
                      } catch (e) { alert('AI 分析失败: ' + e.message) }
                      finally { setAiAnalysisLoading(false) }
                    }}
                    className="px-4 py-2 bg-gradient-to-r from-indigo-600 to-purple-600 text-white rounded-lg hover:from-indigo-700 hover:to-purple-700 text-sm disabled:opacity-50"
                  >
                    {aiAnalysisLoading ? '分析中...' : (aiAnalysis ? '🔄 重新分析(LLM)' : '生成AI分析')}
                  </button>
                )}
              </div>
              <button onClick={() => { setShowResultDialog(false); setAiAnalysis(null) }} className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300">关闭</button>
            </div>
          </div>
        </div>
      )}

      {/* P1-8: AI 评审结果弹窗 */}
      {showReviewDialog && reviewResult && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl p-6 w-[800px] max-h-[85vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-bold">AI 用例评审报告</h2>
              <div className="flex items-center gap-2">
                <span className={`text-xs px-2 py-1 rounded ${reviewResult.ai_enhanced ? 'bg-purple-100 text-purple-700' : 'bg-gray-100 text-gray-600'}`}>
                  {reviewResult.ai_enhanced ? '规则+AI' : '规则评审'}
                </span>
                <button onClick={() => setShowReviewDialog(false)} className="text-gray-400 hover:text-gray-600 text-xl">✕</button>
              </div>
            </div>

            <div className="flex items-center gap-6 mb-5 p-4 bg-gradient-to-r from-indigo-50 to-purple-50 rounded-lg">
              <div className="text-center">
                <div className={`text-4xl font-bold ${reviewResult.quality_score >= 80 ? 'text-green-600' : reviewResult.quality_score >= 50 ? 'text-yellow-600' : 'text-red-600'}`}>
                  {reviewResult.quality_score}
                </div>
                <div className="text-xs text-gray-500 mt-1">质量评分</div>
              </div>
              <div className="flex-1 grid grid-cols-4 gap-3 text-center text-sm">
                <div><div className="text-lg font-bold">{reviewResult.total_cases}</div><div className="text-xs text-gray-500">总用例</div></div>
                <div><div className="text-lg font-bold text-green-600">{reviewResult.automatable_cases}</div><div className="text-xs text-gray-500">可自动化</div></div>
                <div><div className="text-lg font-bold text-red-600">{reviewResult.missing_assertion_count}</div><div className="text-xs text-gray-500">缺少断言</div></div>
                <div><div className="text-lg font-bold text-orange-600">{reviewResult.high_risk_count}</div><div className="text-xs text-gray-500">高风险接口</div></div>
              </div>
            </div>

            {reviewResult.risk_summary && (
              <div className="mb-4 flex gap-3">
                <span className="px-3 py-1 bg-red-100 text-red-700 rounded text-sm font-medium">高风险 {reviewResult.risk_summary.high}</span>
                <span className="px-3 py-1 bg-yellow-100 text-yellow-700 rounded text-sm font-medium">中风险 {reviewResult.risk_summary.medium}</span>
                <span className="px-3 py-1 bg-green-100 text-green-700 rounded text-sm font-medium">低风险 {reviewResult.risk_summary.low}</span>
              </div>
            )}

            <div className="grid grid-cols-3 gap-3 mb-4 text-sm">
              <div className="p-3 bg-gray-50 rounded"><span className="text-gray-500">缺少预期:</span> <span className="font-bold">{reviewResult.missing_expected_count}</span></div>
              <div className="p-3 bg-gray-50 rounded"><span className="text-gray-500">缺少步骤:</span> <span className="font-bold">{reviewResult.missing_steps_count}</span></div>
              <div className="p-3 bg-gray-50 rounded"><span className="text-gray-500">重复用例:</span> <span className="font-bold">{reviewResult.duplicate_count}</span></div>
            </div>

            {reviewResult.improvement_suggestions?.length > 0 && (
              <div className="mb-4">
                <h3 className="text-sm font-semibold mb-2">改进建议</h3>
                <ul className="space-y-1">
                  {reviewResult.improvement_suggestions.map((s, i) => (
                    <li key={i} className="text-sm text-gray-700 bg-yellow-50 p-2 rounded">
                      {typeof s === 'string' ? s : (
                        <>
                          <span>{s.suggestion}</span>
                          {s.affected_cases?.length > 0 && <span className="ml-2 text-gray-500">[{s.affected_cases.join(', ')}]</span>}
                          {s.impact && <span className={`ml-2 px-1 rounded text-xs ${s.impact === 'high' ? 'bg-red-100 text-red-600' : 'bg-gray-100 text-gray-600'}`}>{s.impact}</span>}
                        </>
                      )}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {reviewResult.ai_suggestions?.length > 0 && (
              <div className="mb-4">
                <h3 className="text-sm font-semibold mb-2 text-purple-700">AI 补充建议</h3>
                <ul className="space-y-1">
                  {reviewResult.ai_suggestions.map((s, i) => (
                    <li key={i} className="text-sm text-purple-700 bg-purple-50 p-2 rounded">{s}</li>
                  ))}
                </ul>
              </div>
            )}

            {reviewResult.priority_recommendations?.length > 0 && (
              <div className="mb-4">
                <h3 className="text-sm font-semibold mb-2">优先处理用例</h3>
                <div className="space-y-1 max-h-40 overflow-y-auto">
                  {reviewResult.priority_recommendations.map((r, i) => (
                    <div key={i} className="text-xs p-2 bg-red-50 rounded flex gap-2">
                      <span className="font-mono font-bold text-red-700">{r.case_id}</span>
                      <span className="text-gray-600">{r.reason}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {reviewResult.duplicate_groups?.length > 0 && (
              <div className="mb-4">
                <h3 className="text-sm font-semibold mb-2">疑似重复用例</h3>
                <div className="space-y-1 max-h-32 overflow-y-auto">
                  {reviewResult.duplicate_groups.map((g, i) => (
                    <div key={i} className="text-xs p-2 bg-orange-50 rounded">
                      <span className="font-mono">{g.signature}</span> x{g.count}: {g.case_ids.join(', ')}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* AI 总评 */}
            {reviewResult.overall_assessment && (
              <div className="mb-4 p-3 bg-blue-50 border border-blue-200 rounded">
                <h3 className="text-sm font-semibold mb-1 text-blue-800">AI 总评</h3>
                <p className="text-sm text-blue-700">{reviewResult.overall_assessment}</p>
              </div>
            )}

            {/* AI 逐条问题 */}
            {reviewResult.ai_case_issues?.length > 0 && (
              <div className="mb-4">
                <h3 className="text-sm font-semibold mb-2 text-red-700">问题用例（AI 诊断）</h3>
                <div className="space-y-2 max-h-48 overflow-y-auto">
                  {reviewResult.ai_case_issues.map((c, i) => (
                    <div key={i} className="text-xs p-2 bg-red-50 rounded border border-red-100">
                      <div className="flex items-center justify-between">
                        <span className="font-mono font-bold text-red-700">{c.case_id}</span>
                        <button
                          onClick={() => { setShowReviewDialog(false); setSearchQuery(c.case_id) }}
                          className="text-blue-600 hover:underline text-xs"
                        >定位</button>
                      </div>
                      {c.issues?.map((issue, j) => <div key={j} className="text-gray-600 mt-1">- {issue}</div>)}
                      {c.fix_suggestion && <div className="mt-1 text-green-700 font-medium">修复: {c.fix_suggestion}</div>}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* 覆盖缺口 */}
            {reviewResult.coverage_gaps?.length > 0 && (
              <div className="mb-4">
                <h3 className="text-sm font-semibold mb-2">覆盖缺口</h3>
                <ul className="space-y-1">
                  {reviewResult.coverage_gaps.map((g, i) => (
                    <li key={i} className="text-sm text-gray-700 bg-amber-50 p-2 rounded">{g}</li>
                  ))}
                </ul>
              </div>
            )}

            {/* 漏测场景 */}
            {reviewResult.missing_scenarios?.length > 0 && (
              <div className="mb-4">
                <h3 className="text-sm font-semibold mb-2 text-purple-700">建议补充场景</h3>
                <div className="space-y-1 max-h-40 overflow-y-auto">
                  {reviewResult.missing_scenarios.map((s, i) => (
                    <div key={i} className="text-xs p-2 bg-purple-50 rounded">
                      {typeof s === 'string' ? s : (
                        <>
                          <span className="font-medium">{s.scenario}</span>
                          {s.api && <span className="ml-2 text-gray-500">[{s.api}]</span>}
                          {s.priority && <span className={`ml-2 px-1 rounded ${s.priority === 'high' ? 'bg-red-100 text-red-600' : 'bg-gray-100 text-gray-600'}`}>{s.priority}</span>}
                          {s.reason && <div className="text-gray-500 mt-0.5">{s.reason}</div>}
                        </>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* 规则问题用例明细 */}
            {reviewResult.case_details?.some(c => c.issues?.length > 0) && (
              <details className="mb-4">
                <summary className="text-sm font-semibold cursor-pointer text-gray-700">
                  规则检出问题用例 ({reviewResult.case_details.filter(c => c.issues?.length > 0).length} 条)
                </summary>
                <div className="mt-2 space-y-1 max-h-48 overflow-y-auto">
                  {reviewResult.case_details.filter(c => c.issues?.length > 0).map((c, i) => (
                    <div key={i} className="text-xs p-2 bg-gray-50 rounded flex items-start gap-2">
                      <span className={`px-1.5 py-0.5 rounded font-bold ${c.risk_level === 'high' ? 'bg-red-100 text-red-700' : c.risk_level === 'medium' ? 'bg-yellow-100 text-yellow-700' : 'bg-green-100 text-green-700'}`}>{c.score}</span>
                      <div className="flex-1">
                        <div className="flex items-center justify-between">
                          <span className="font-mono text-gray-500">{c.case_id}</span>
                          <button onClick={() => { setShowReviewDialog(false); setSearchQuery(c.case_id) }} className="text-blue-600 hover:underline text-xs">定位</button>
                        </div>
                        <div className="text-gray-600">{c.issues.join(' | ')}</div>
                      </div>
                    </div>
                  ))}
                </div>
              </details>
            )}

            <div className="mt-4 flex justify-end">
              <button onClick={() => setShowReviewDialog(false)} className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 text-sm">关闭</button>
            </div>
          </div>
        </div>
      )}

      {/* 手动测试对话框 */}
      {showManualTestDialog && selectedTestCase && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl p-6 w-[750px] max-h-[85vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-bold">🧪 手动功能测试</h2>
              <button onClick={() => setShowManualTestDialog(false)} className="text-gray-400 hover:text-gray-600 text-xl">✕</button>
            </div>

            <div className="mb-4 p-3 bg-indigo-50 rounded border border-indigo-200">
              <p className="text-sm text-indigo-800"><span className="font-medium">用例:</span> {selectedTestCase.title}</p>
              {selectedTestCase.module && <p className="text-xs text-indigo-600 mt-1">模块: {selectedTestCase.module}</p>}
            </div>

            {manualTestSteps.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                <p className="text-lg mb-2">该用例没有定义测试步骤</p>
                <p className="text-sm">请先在用例详情中添加测试步骤</p>
              </div>
            ) : (
              <div className="space-y-3">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium">测试步骤 ({manualTestSteps.filter(s => s.status !== 'pending').length}/{manualTestSteps.length} 已执行)</span>
                  <div className="flex space-x-2 text-xs">
                    <span className="text-green-600">✓ 通过 {manualTestSteps.filter(s => s.status === 'passed').length}</span>
                    <span className="text-red-600">✗ 失败 {manualTestSteps.filter(s => s.status === 'failed').length}</span>
                  </div>
                </div>

                {manualTestSteps.map((step, i) => (
                  <div key={i} className={`p-3 rounded border ${
                    i === currentStepIndex ? 'border-indigo-400 bg-indigo-50' :
                    step.status === 'passed' ? 'border-green-300 bg-green-50' :
                    step.status === 'failed' ? 'border-red-300 bg-red-50' :
                    'border-gray-200'
                  }`}>
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <span className="text-xs font-bold text-gray-500">步骤 {step.index}</span>
                        <p className="text-sm mt-1">{typeof step.description === 'string' ? step.description : JSON.stringify(step.description)}</p>
                      </div>
                      <div className="flex space-x-2 ml-3">
                        <button
                          onClick={() => handleStepResult(i, 'passed')}
                          className={`px-3 py-1 rounded text-xs font-medium ${
                            step.status === 'passed' ? 'bg-green-600 text-white' : 'bg-green-100 text-green-700 hover:bg-green-200'
                          }`}
                        >✓ 通过</button>
                        <button
                          onClick={() => handleStepResult(i, 'failed')}
                          className={`px-3 py-1 rounded text-xs font-medium ${
                            step.status === 'failed' ? 'bg-red-600 text-white' : 'bg-red-100 text-red-700 hover:bg-red-200'
                          }`}
                        >✗ 失败</button>
                      </div>
                    </div>
                    {step.status === 'failed' && (
                      <input
                        type="text"
                        placeholder="失败原因（可选）"
                        value={step.note}
                        onChange={(e) => handleStepNote(i, e.target.value)}
                        className="mt-2 w-full px-2 py-1 border rounded text-xs"
                      />
                    )}
                  </div>
                ))}

                <div className="mt-4">
                  <label className="block text-sm font-medium text-gray-700 mb-1">备注</label>
                  <textarea
                    value={manualTestNotes}
                    onChange={(e) => setManualTestNotes(e.target.value)}
                    placeholder="整体测试备注..."
                    className="w-full px-3 py-2 border rounded-lg text-sm"
                    rows={2}
                  />
                </div>
              </div>
            )}

            <div className="mt-4 flex justify-end space-x-3">
              <button
                onClick={() => setShowManualTestDialog(false)}
                className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 text-sm"
              >取消</button>
              {manualTestSteps.length > 0 && (
                <button
                  onClick={handleSubmitManualTest}
                  className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 text-sm"
                >提交测试结果</button>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
