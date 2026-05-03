import { useState, useEffect, useMemo } from 'react'
import { CaseActionToolbar, CaseMetricsPanel, CaseTypeTabs, CaseListTable, CaseDetailDialog, PerfConfigDialog, PerfResultDialog, CaseImportDialog, AiReviewDialog } from '../components/testcases'
import { useNavigate } from 'react-router-dom'
import api from '../services/api'
import SVNInput from '../components/SVNInput'

const EXECUTION_ENV_STORAGE_KEY = 'ai_test_selected_execution_environment_id'

export default function TestCases() {
  const navigate = useNavigate()
  const [showUploadDialog, setShowUploadDialog] = useState(false)
  const [showSVNDialog, setShowSVNDialog] = useState(false)
  // P1-9A: 统一导入弹窗
  const [showImportDialog, setShowImportDialog] = useState(false)
  const [importTab, setImportTab] = useState('requirement')
  const [importLoading, setImportLoading] = useState(false)
  const [importError, setImportError] = useState(null)
  const [importSuccess, setImportSuccess] = useState(null)
  // Swagger 文件 Tab
  const [swaggerFile, setSwaggerFile] = useState(null)
  // Swagger URL Tab
  const [swaggerUrl, setSwaggerUrl] = useState('')
  const [swaggerAuthType, setSwaggerAuthType] = useState('none')
  const [swaggerToken, setSwaggerToken] = useState('')
  // YApi Tab
  const [yapiBase, setYapiBase] = useState('')
  const [yapiProjectId, setYapiProjectId] = useState('')
  const [yapiEmail, setYapiEmail] = useState('')
  const [yapiPassword, setYapiPassword] = useState('')
  // 手动创建 Tab
  const [manualTitle, setManualTitle] = useState('')
  const [manualModule, setManualModule] = useState('')
  const [manualPriority, setManualPriority] = useState('medium')
  const [manualSteps, setManualSteps] = useState([''])
  const [manualExpected, setManualExpected] = useState('')
  const [manualCaseType, setManualCaseType] = useState('functional')
  // Web UI 用例字段
  const [webUiSteps, setWebUiSteps] = useState([{ action: 'goto', target: '', value: '', description: '' }])
  const [webUiAssertions, setWebUiAssertions] = useState([{ type: 'text_visible', target: '', value: '', description: '' }])
  const [webUiBrowser, setWebUiBrowser] = useState('chromium')
  const [webUiBaseUrl, setWebUiBaseUrl] = useState('')
  const [webUiHeadless, setWebUiHeadless] = useState(true)
  const [showHiddenPetStore, setShowHiddenPetStore] = useState(false)
  const [scannerExpanded, setScannerExpanded] = useState(false)
  const [webUiNeedLogin, setWebUiNeedLogin] = useState(false)
  const [webUiLoginMerchant, setWebUiLoginMerchant] = useState('')
  const [webUiLoginUser, setWebUiLoginUser] = useState('')
  const [webUiLoginPass, setWebUiLoginPass] = useState('')
  // Page scanner
  const [scanResult, setScanResult] = useState(null)
  const [scanLoading, setScanLoading] = useState(false)
  const [scanUrl, setScanUrl] = useState('')
  // Login session
  const [loginSession, setLoginSession] = useState(null) // { has_session, saved_at, ... }
  const [sessionSaving, setSessionSaving] = useState(false)
  const [useSession, setUseSession] = useState(false)
  // P2-4.1: AI provider availability
  const [aiAvailable, setAiAvailable] = useState(false)
  const [uploadFile, setUploadFile] = useState(null)
  const [isGenerating, setIsGenerating] = useState(false)
  const [testCases, setTestCases] = useState([])
  const [loading, setLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState('')
  const [sourceFilter, setSourceFilter] = useState('all')
  const [currentPage, setCurrentPage] = useState(1)
  const PAGE_SIZE = 20
  const [projects, setProjects] = useState([])
  const [selectedProjectId, setSelectedProjectId] = useState('')
  const [selectedTestCase, setSelectedTestCase] = useState(null)
  const [showDetailDialog, setShowDetailDialog] = useState(false)
  // P1-9B: 用例编辑
  const [isEditing, setIsEditing] = useState(false)
  const [editForm, setEditForm] = useState({})
  const [editSaving, setEditSaving] = useState(false)
  // P2-9D: 覆盖率
  const [coverage, setCoverage] = useState(null)
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
  // P2-6B: Performance Testing
  const [showPerfDialog, setShowPerfDialog] = useState(false)
  const [perfConfig, setPerfConfig] = useState({ concurrency: 5, duration_seconds: 10, ramp_up_seconds: 0, think_time_ms: 0 })
  const [perfLoading, setPerfLoading] = useState(false)
  const [perfResult, setPerfResult] = useState(null)
  const [showPerfResult, setShowPerfResult] = useState(false)
  // P2-10: 加入测试集
  const [showSuitePickerDialog, setShowSuitePickerDialog] = useState(false)
  const [suitePickerList, setSuitePickerList] = useState([])
  const [selectedSuiteId, setSelectedSuiteId] = useState('')
  // AI 自愈（P1-8A-Guard 两步确认）
  const [healingCases, setHealingCases] = useState({}) // { case_id: 'loading'|'preview'|'applying'|'done'|'error' }
  const [healPreviews, setHealPreviews] = useState({}) // { case_id: { before, after, changes, ... } }
  const [showHealDialog, setShowHealDialog] = useState(false)
  const [healDialogCase, setHealDialogCase] = useState(null) // 当前预览的 case result

  useEffect(() => {
    loadProjects()
    loadTestCases()
    loadDatasets()
    loadEnvironments()
    loadCoverage()
    api.v2.getAppMode().then(setAppMode)
    // P2-4.1: check AI provider availability
    fetch('/health').then(r=>r.json()).then(h=>{ setAiAvailable(h.ai_provider && h.ai_provider !== 'none') }).catch(()=>{})
  }, [])

  const loadCoverage = async (projectId) => {
    try {
      const pid = projectId !== undefined ? projectId : selectedProjectId
      const data = await api.v2.swagger.coverage(pid || undefined)
      setCoverage(data)
    } catch { setCoverage(null) }
  }

  const loadTestCases = async (projectId) => {
    setLoading(true)
    try {
      const params = { limit: 5000 }
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
    // auto-select this project's first environment
    if (pid) {
      const projEnvs = environments.filter(e => String(e.project_id) === String(pid))
      if (projEnvs.length > 0) {
        setSelectedEnvironmentId(String(projEnvs[0].id))
        localStorage.setItem(EXECUTION_ENV_STORAGE_KEY, String(projEnvs[0].id))
      }
      // check login session
      api.v2.ui.getLoginSession(pid).then(s => { setLoginSession(s); if (s?.has_session) setUseSession(true) }).catch(() => setLoginSession(null))
    } else {
      setLoginSession(null); setUseSession(false)
    }
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
        projects.map(project => api.v2.projects.getEnvironments(project.id).then(
          envs => (envs || []).map(e => ({ ...e, project_id: project.id, project_name: project.name }))
        ).catch(() => []))
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

  // ── P1-9A: 统一导入处理函数 ──
  const resetImportState = () => {
    setImportLoading(false); setImportError(null); setImportSuccess(null)
    setSwaggerFile(null); setSwaggerUrl(''); setSwaggerAuthType('none'); setSwaggerToken('')
    setYapiBase(''); setYapiProjectId(''); setYapiEmail(''); setYapiPassword('')
    setUploadFile(null); setIsGenerating(false); setGenerationProgress(0); setGenerationStep('')
  }

  const closeImportDialog = () => {
    if (importLoading || isGenerating) {
      if (!window.confirm('正在处理中，确定要取消吗？')) return
    }
    setShowImportDialog(false)
    resetImportState()
  }

  const handleManualCreate = async () => {
    if (!manualTitle.trim()) { setImportError('请填写用例标题'); return }
    setImportLoading(true); setImportError(null)
    try {
      const payload = {
        title: manualTitle.trim(),
        module: manualModule.trim(),
        priority: manualPriority,
        case_type: manualCaseType,
        expected: manualExpected.trim(),
      }
      if (selectedProjectId) payload.project_id = Number(selectedProjectId)
      if (manualCaseType === 'web_ui') {
        let finalSteps = webUiSteps.filter(s => s.action && (s.target || s.value || s.description))
        // auto-prepend login steps
        if (webUiNeedLogin) {
          const loginSteps = [
            {action:'goto',target:'/index',value:'',description:'打开系统(跳转登录)'},
            {action:'wait_for',target:'#merchantId',value:'',description:'等待登录表单'},
            {action:'fill',target:'#merchantId',value:webUiLoginMerchant,description:'输入商户号'},
            {action:'fill',target:'#username',value:webUiLoginUser,description:'输入账号'},
            {action:'fill',target:'#password',value:webUiLoginPass,description:'输入密码'},
            {action:'click',target:'#agreementCheckbox',value:'',description:'勾选协议'},
            {action:'click',target:'button[type=submit]',value:'',description:'点击登录'},
            {action:'wait_for',target:'3000',value:'',description:'等待登录完成'},
          ]
          finalSteps = [...loginSteps, ...finalSteps]
        }
        payload.steps = finalSteps
        payload.assertions = webUiAssertions.filter(a => a.type && (a.value || a.target || a.description))
        payload.execution_config = {
          engine: 'playwright',
          browser: webUiBrowser,
          base_url: webUiBaseUrl.trim(),
          viewport: { width: 1366, height: 768 },
          headless: webUiHeadless,
          ...(useSession && selectedProjectId ? { session_project_id: selectedProjectId } : {}),
        }
      } else {
        payload.steps = manualSteps.filter(s => s.trim())
      }
      const result = await api.v2.testCases.create(payload)
      if (result.success) {
        setImportSuccess({ count: 1, message: `用例 ${result.test_case_id} 创建成功` })
        loadTestCases()
        setManualTitle(''); setManualModule(''); setManualPriority('medium')
        setManualSteps(['']); setManualExpected(''); setManualCaseType('functional')
        setWebUiSteps([{ action: 'goto', target: '', value: '', description: '' }])
        setWebUiAssertions([{ type: 'text_visible', target: '', value: '', description: '' }])
        setWebUiBaseUrl(''); setWebUiBrowser('chromium'); setWebUiHeadless(true)
        setWebUiNeedLogin(false); setWebUiLoginMerchant(''); setWebUiLoginUser(''); setWebUiLoginPass('')
      } else {
        setImportError(result.message || '创建失败')
      }
    } catch (e) {
      setImportError(e.message || '创建失败')
    } finally {
      setImportLoading(false)
    }
  }

  const handleImportRequirement = async () => {
    if (!uploadFile) { setImportError('请选择需求文档'); return }
    setImportLoading(true); setImportError(null); setIsGenerating(true)
    setGenerationProgress(0); setGenerationStep('准备上传文档...')
    try {
      const progressInterval = setInterval(() => {
        setGenerationProgress(prev => prev >= 90 ? prev : prev + 2)
      }, 1000)
      setTimeout(() => setGenerationStep('📚 加载项目知识库...'), 500)
      setTimeout(() => setGenerationStep(' 解析需求文档...'), 2000)
      setTimeout(() => setGenerationStep('🔍 拆分功能模块...'), 5000)
      setTimeout(() => setGenerationStep('🎯 生成测试场景...'), 12000)
      setTimeout(() => setGenerationStep('✨ 生成测试用例...'), 22000)

      const result = await api.testCases.generate(uploadFile)
      clearInterval(progressInterval)
      setGenerationProgress(100); setGenerationStep('✅ 生成完成!')
      if (result.success) {
        setImportSuccess({ type: 'requirement', count: result.count })
        loadTestCases()
      } else {
        setImportError('AI 生成失败: ' + (result.error || '未知错误'))
      }
    } catch (e) {
      setImportError('需求文档导入失败: ' + e.message)
    } finally {
      setImportLoading(false); setIsGenerating(false)
    }
  }

  const handleImportSwaggerFile = async () => {
    if (!swaggerFile) { setImportError('请选择 Swagger/OpenAPI 文件'); return }
    const pid = selectedProjectId || projects[0]?.id
    if (!pid) { setImportError('请先选择目标项目'); return }
    setImportLoading(true); setImportError(null)
    try {
      const res = await api.v2.swagger.importFromFile(pid, swaggerFile, true)
      setImportSuccess({
        type: 'swagger_file',
        count: res.test_cases_generated || 0,
        apiCount: res.api_count || 0,
        apiSpecId: res.api_spec_id,
      })
      loadTestCases()
    } catch (e) {
      const msg = e.message || ''
      if (msg.includes('409') || msg.includes('SWAGGER_ALREADY_IMPORTED')) {
        setImportError('该 Swagger 文档已导入过此项目，如需更新请先删除旧的 API 规范。')
      } else {
        setImportError('Swagger 文件导入失败: ' + msg)
      }
    } finally { setImportLoading(false) }
  }

  const handleImportSwaggerUrl = async () => {
    if (!swaggerUrl.trim()) { setImportError('请输入 Swagger URL'); return }
    const pid = selectedProjectId || projects[0]?.id
    if (!pid) { setImportError('请先选择目标项目'); return }
    setImportLoading(true); setImportError(null)
    try {
      const payload = {
        project_id: Number(pid),
        url: swaggerUrl.trim(),
        generate_cases: true,
      }
      if (swaggerAuthType !== 'none' && swaggerToken) {
        payload.auth_type = swaggerAuthType
        payload.token = swaggerToken
      }
      const res = await api.v2.swagger.importFromUrl(payload)
      setImportSuccess({
        type: 'swagger_url',
        count: res.test_cases_generated || 0,
        apiCount: res.api_count || 0,
        apiSpecId: res.api_spec_id,
      })
      loadTestCases()
    } catch (e) {
      const msg = e.message || ''
      if (msg.includes('409') || msg.includes('SWAGGER_ALREADY_IMPORTED')) {
        setImportError('该 Swagger URL 已导入过此项目，请勿重复导入。')
      } else if (msg.includes('401') || msg.includes('403')) {
        setImportError('鉴权失败: 请检查 Token 是否正确。')
      } else {
        setImportError('Swagger URL 导入失败: ' + msg)
      }
    } finally { setImportLoading(false) }
  }

  const handleImportYapi = async () => {
    if (!yapiBase.trim()) { setImportError('请输入 YApi 服务地址'); return }
    if (!yapiProjectId) { setImportError('请输入 YApi 项目 ID'); return }
    if (!yapiEmail.trim()) { setImportError('请输入 YApi 登录邮箱'); return }
    if (!yapiPassword) { setImportError('请输入 YApi 登录密码'); return }
    const pid = selectedProjectId || projects[0]?.id
    if (!pid) { setImportError('请先选择目标项目'); return }
    setImportLoading(true); setImportError(null)
    try {
      const res = await fetch('/api/v2/swagger/import-yapi', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          project_id: Number(pid),
          yapi_base: yapiBase.trim(),
          yapi_project_id: Number(yapiProjectId),
          yapi_email: yapiEmail.trim(),
          yapi_password: yapiPassword,
          generate_cases: true,
        }),
      })
      if (!res.ok) {
        const err = await res.json().catch(() => ({}))
        const detail = typeof err.detail === 'string' ? err.detail : err.detail?.message || res.statusText
        if (res.status === 401) throw new Error('YApi 登录失败: 邮箱或密码错误')
        if (res.status === 409) throw new Error('该 YApi 项目已导入过，请勿重复导入。')
        throw new Error(detail || '导入失败')
      }
      const data = await res.json()
      setImportSuccess({
        type: 'yapi',
        count: data.test_cases_generated || 0,
        apiCount: data.api_count || 0,
        apiSpecId: data.api_spec_id,
      })
      loadTestCases()
    } catch (e) {
      setImportError('YApi 导入失败: ' + e.message)
    } finally { setImportLoading(false) }
  }

  const handleViewDetail = (testCase) => {
    setSelectedTestCase(testCase)
    setShowDetailDialog(true)
    setIsEditing(false)
  }

  const enterEditMode = () => {
    const tc = selectedTestCase
    setEditForm({
      title: tc.title || '',
      module: tc.module || '',
      priority: tc.priority || 'medium',
      steps: Array.isArray(tc.steps) && tc.steps.length > 0 ? [...tc.steps] : [''],
      expected: tc.expected || '',
      body: tc.body ? (typeof tc.body === 'string' ? tc.body : JSON.stringify(tc.body, null, 2)) : '',
      assertions: tc.assertions ? (typeof tc.assertions === 'string' ? tc.assertions : JSON.stringify(tc.assertions, null, 2)) : '',
    })
    setIsEditing(true)
  }

  const handleEditSave = async () => {
    if (!selectedTestCase?.id) return
    setEditSaving(true)
    try {
      const payload = {}
      if (editForm.title.trim()) payload.title = editForm.title.trim()
      if (editForm.module !== undefined) payload.module = editForm.module.trim()
      payload.priority = editForm.priority
      payload.expected = editForm.expected.trim()
      const steps = editForm.steps
        .map(s => typeof s === 'string' ? s.trim() : s)
        .filter(s => typeof s === 'string' ? s : (s && s.action))
      if (steps.length > 0) payload.steps = steps

      if (editForm.assertions.trim()) {
        try { payload.assertions = JSON.parse(editForm.assertions) } catch {}
      }

      const res = await api.v2.testCases.update(selectedTestCase.id, payload)
      if (res.success) {
        setIsEditing(false)
        setSelectedTestCase(prev => ({ ...prev, ...payload }))
        loadTestCases()
      } else {
        alert('保存失败: ' + (res.message || ''))
      }
    } catch (e) {
      alert('保存失败: ' + e.message)
    } finally { setEditSaving(false) }
  }

  const handleEditStepChange = (idx, val) => {
    setEditForm(prev => {
      const steps = [...prev.steps]
      steps[idx] = val
      return { ...prev, steps }
    })
  }

  const handleAddStep = () => {
    setEditForm(prev => {
      const isObj = prev.steps.length > 0 && typeof prev.steps[0] !== 'string'
      const newStep = isObj ? { action: 'click', target: '', value: '', description: '' } : ''
      return { ...prev, steps: [...prev.steps, newStep] }
    })
  }

  const handleRemoveStep = (idx) => {
    setEditForm(prev => {
      const wasObj = prev.steps.length > 0 && typeof prev.steps[0] !== 'string'
      const steps = prev.steps.filter((_, i) => i !== idx)
      const fallback = wasObj ? [{ action: 'click', target: '', value: '', description: '' }] : ['']
      return { ...prev, steps: steps.length === 0 ? fallback : steps }
    })
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
    if (!hasSelection && filteredTestCases.length > 200) {
      if (!window.confirm(`当前匹配 ${filteredTestCases.length} 条用例，未勾选时仅评审当前页 ${pagedCases.length} 条。是否继续？`)) return
    }
    setReviewLoading(true)
    try {
      const payload = {}
      if (hasSelection) {
        payload.case_ids = selectedIds
      } else if (filteredTestCases.length > 200) {
        payload.case_ids = pagedCases.map(tc => tc.id)
      } else {
        payload.case_ids = filteredTestCases.map(tc => tc.id)
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

  // AI 自愈 Step 1: dry_run=true 预览
  const handleHealPreview = async (caseItem) => {
    setHealingCases(prev => ({ ...prev, [caseItem.case_id]: 'loading' }))
    try {
      const data = await api.ai.healCases({
        dry_run: true,
        cases: [{
          case_id: caseItem.case_id,
          issues: caseItem.issues || [],
          fix_suggestion: caseItem.fix_suggestion || '',
        }]
      })
      const result = data.results?.[0]
      if (result && result.changes?.length > 0) {
        setHealPreviews(prev => ({ ...prev, [caseItem.case_id]: result }))
        setHealingCases(prev => ({ ...prev, [caseItem.case_id]: 'preview' }))
        setHealDialogCase(result)
        setShowHealDialog(true)
      } else {
        setHealingCases(prev => ({ ...prev, [caseItem.case_id]: 'error' }))
        alert(result?.error || '无修复建议')
      }
    } catch (e) {
      setHealingCases(prev => ({ ...prev, [caseItem.case_id]: 'error' }))
      alert('生成修复预览失败: ' + e.message)
    }
  }

  // AI 自愈 Step 2: dry_run=false 确认应用
  const handleHealApply = async (caseId) => {
    const preview = healPreviews[caseId]
    if (!preview) return
    setHealingCases(prev => ({ ...prev, [caseId]: 'applying' }))
    try {
      const data = await api.ai.healCases({
        dry_run: false,
        cases: [{
          case_id: caseId,
          issues: preview.changes?.map(c => c.reason) || [],
          fix_suggestion: preview.change_summary || '',
        }]
      })
      const result = data.results?.[0]
      if (result?.applied) {
        setHealingCases(prev => ({ ...prev, [caseId]: 'done' }))
        setShowHealDialog(false)
        loadTestCases()
      } else {
        setHealingCases(prev => ({ ...prev, [caseId]: 'error' }))
        alert(result?.error || '应用修复失败')
      }
    } catch (e) {
      setHealingCases(prev => ({ ...prev, [caseId]: 'error' }))
      alert('应用修复失败: ' + e.message)
    }
  }

  // 重新生成建议
  const handleHealRetry = (caseItem) => {
    setHealingCases(prev => ({ ...prev, [caseItem.case_id]: undefined }))
    setHealPreviews(prev => { const n = { ...prev }; delete n[caseItem.case_id]; return n })
    handleHealPreview(caseItem)
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
    if (selectedEnvironmentId && !isPetStoreEnvironment && isPetStoreSampleCase(tc) && !showHiddenPetStore) return false
    // 来源筛选
    const isApiSource = ['swagger', 'demo_swagger', 'demo_seed'].includes(tc.source) || tc.case_type === 'api'
    const isWebUi = tc.case_type === 'web_ui'
    if (sourceFilter === 'functional' && (isApiSource || isWebUi)) return false
    if (sourceFilter === 'api' && !isApiSource) return false
    if (sourceFilter === 'web_ui' && !isWebUi) return false
    // 搜索筛选
    if (searchQuery) {
      const q = searchQuery.toLowerCase()
      const matchTitle = (tc.title || '').toLowerCase().includes(q)
      const matchId = (tc.id || '').toLowerCase().includes(q)
      if (!matchTitle && !matchId) return false
    }
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

  // P2-7: Web UI 批量执行
  const handleWebUiBatchExecute = async () => {
    const selectedCases = filteredTestCases.filter(tc => selectedIds.includes(tc.id))
    const webUiCases = selectedCases.filter(tc => tc.case_type === 'web_ui')
    const nonWebUi = selectedCases.filter(tc => tc.case_type !== 'web_ui')
    if (webUiCases.length === 0) {
      alert('所选用例中没有 Web UI 用例。请选择 case_type=web_ui 的用例。')
      return
    }
    if (nonWebUi.length > 0) {
      if (!window.confirm(`所选 ${selectedCases.length} 条用例中有 ${nonWebUi.length} 条非 Web UI 用例将被跳过，仅执行 ${webUiCases.length} 条 Web UI 用例。继续？`)) return
    } else {
      const traceWarn = appMode === 'real' ? '\n\n⚠️ 当前为真实模式，Trace 可能包含页面敏感数据。' : ''
    if (!window.confirm(`确定批量执行 ${webUiCases.length} 条 Web UI 用例？（Playwright 浏览器执行）${traceWarn}`)) return
    }
    setIsExecuting(true)
    try {
      const result = await api.v2.webUiBatch.run({
        case_ids: webUiCases.map(tc => tc.id),
        execution_config: { browser: 'chromium', headless: true, enable_trace: true, capture_console: true, capture_network: true },
      })
      setExecutionResult({ ...result, is_batch: true, is_web_ui_batch: true })
      setShowResultDialog(true)
      setSelectedIds([])
      const statusById = {}
      ;(result.case_results || []).forEach(r => { statusById[r.case_id] = r.status })
      setTestCases(prev => prev.map(tc =>
        statusById[tc.id] ? { ...tc, status: statusById[tc.id], lastRun: new Date().toLocaleString() } : tc
      ))
    } catch (error) {
      let msg = error.message || 'Web UI 批量执行失败'
      try { const p = JSON.parse(msg.replace(/^API调用失败: \d+ /, '')); if (p.detail) msg = p.detail } catch {}
      alert('Web UI 批量执行失败: ' + msg)
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

  // P2-6B: Performance test handler
  const handlePerfTest = async () => {
    if (!selectedEnvironmentId) { alert('请先选择执行环境'); return }
    const apiCaseIds = selectedIds.length > 0
      ? filteredTestCases.filter(tc => selectedIds.includes(tc.id) && tc.case_type !== 'web_ui').map(tc => tc.id)
      : filteredTestCases.filter(tc => tc.case_type !== 'web_ui' && tc.execution_config).map(tc => tc.id)
    if (apiCaseIds.length === 0) { alert('无可用 API 用例'); return }
    setPerfLoading(true)
    try {
      const result = await api.v2.performance.run({
        project_id: Number(selectedProjectId) || 1,
        case_ids: apiCaseIds,
        environment_id: Number(selectedEnvironmentId),
        concurrency: perfConfig.concurrency,
        duration_seconds: perfConfig.duration_seconds,
        ramp_up_seconds: perfConfig.ramp_up_seconds,
        think_time_ms: perfConfig.think_time_ms,
        allow_unsafe_methods: false,
      })
      setPerfResult(result)
      setShowPerfDialog(false)
      setShowPerfResult(true)
    } catch (e) {
      alert('性能测试失败: ' + (e.message || e))
    } finally {
      setPerfLoading(false)
    }
  }

  // P2-10: 加入测试集
  const handleAddToSuite = async () => {
    if (selectedIds.length === 0) { alert('请先选择用例'); return }
    try {
      const r = await fetch('/api/v2/test-suites?limit=100')
      const d = await r.json()
      setSuitePickerList(d.data || [])
      setSelectedSuiteId('')
      setShowSuitePickerDialog(true)
    } catch (e) { alert('获取测试集列表失败: ' + e.message) }
  }
  const handleConfirmAddToSuite = async () => {
    if (!selectedSuiteId) { alert('请选择测试集'); return }
    try {
      const r = await fetch(`/api/v2/test-suites/${selectedSuiteId}/cases`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ case_ids: selectedIds })
      })
      const d = await r.json()
      alert(`已添加 ${d.added?.length || 0} 条, 跳过 ${d.skipped?.length || 0} 条`)
      setShowSuitePickerDialog(false)
    } catch (e) { alert('添加失败: ' + e.message) }
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
  }).sort((a, b) => {
    const ta = a.created_at || a.id || ''
    const tb = b.created_at || b.id || ''
    return tb > ta ? 1 : tb < ta ? -1 : 0
  })
  const hasGovFilter = Object.values(govFilter).some(v => v !== '')
  const totalPages = Math.max(1, Math.ceil(govFilteredCases.length / PAGE_SIZE))
  const safePage = Math.min(currentPage, totalPages)
  const pagedCases = govFilteredCases.slice((safePage - 1) * PAGE_SIZE, safePage * PAGE_SIZE)

  // P2-7.3: Selected case type analysis for dynamic toolbar
  const selectedCaseAnalysis = useMemo(() => {
    if (selectedIds.length === 0) return { count: 0, isMixed: false, hasApi: false, hasWebUi: false, hasFunctional: false }
    const selected = filteredTestCases.filter(tc => selectedIds.includes(tc.id))
    const types = new Set(selected.map(tc => {
      if (tc.case_type === 'web_ui') return 'web_ui'
      if (['swagger', 'demo_swagger', 'demo_seed'].includes(tc.source) || tc.case_type === 'api') return 'api'
      return 'functional'
    }))
    return { count: selected.length, isMixed: types.size > 1, hasApi: types.has('api'), hasWebUi: types.has('web_ui'), hasFunctional: types.has('functional') }
  }, [selectedIds, filteredTestCases])

  // P2-7.3: Tab-specific metrics
  const tabMetrics = useMemo(() => {
    const apiCases = testCases.filter(tc => ['swagger','demo_swagger','demo_seed'].includes(tc.source) || tc.case_type === 'api')
    const webUiCases = testCases.filter(tc => tc.case_type === 'web_ui')
    const funcCases = testCases.filter(tc => !['swagger','demo_swagger','demo_seed'].includes(tc.source) && tc.case_type !== 'web_ui' && tc.case_type !== 'api')
    return {
      all: { total: testCases.length, apiCount: apiCases.length, funcCount: funcCases.length, webUiCount: webUiCases.length, recentFailed: testCases.filter(tc => tc.status === 'failed').length },
      api: { total: apiCases.length, covered: coverage?.covered_apis || 0, l1: coverage?.l1_case_count || 0, l2: coverage?.l2_case_count || 0, coverageRate: coverage?.coverage_rate || 0 },
      web_ui: {
        total: webUiCases.length,
        executed: webUiCases.filter(tc => tc.status && tc.status !== 'pending').length,
        passRate: webUiCases.length > 0 ? Math.round(webUiCases.filter(tc => tc.status === 'passed').length / webUiCases.length * 100) : 0,
        traceCount: webUiCases.filter(tc => tc.status === 'passed' || tc.status === 'failed').length,
        visualCount: webUiCases.filter(tc => tc.assertions?.some?.(a => a.type === 'screenshot_match')).length,
      },
      functional: {
        total: funcCases.length,
        reviewed: funcCases.filter(tc => tc.status && tc.status !== 'pending').length,
        highRisk: funcCases.filter(tc => tc.risk_level === 'P0').length,
        needImprove: funcCases.filter(tc => !tc.expected || !tc.steps?.length).length,
      },
    }
  }, [testCases, coverage])

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">测试用例</h1>
          <p className="text-gray-600 mt-1">测试用例资产中心 — 统一管理功能、API、Web UI 用例</p>
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
              const envId = e.target.value
              setSelectedEnvironmentId(envId)
              localStorage.setItem(EXECUTION_ENV_STORAGE_KEY, envId)
              // auto-select the project this environment belongs to
              if (envId) {
                const env = environments.find(en => String(en.id) === envId)
                if (env?.project_id && String(env.project_id) !== selectedProjectId) {
                  setSelectedProjectId(String(env.project_id))
                  loadTestCases(String(env.project_id))
                }
              }
            }}
            className="px-3 py-2 border border-gray-300 rounded-lg bg-white text-sm"
          >
            <option value="">选择执行环境</option>
            {(selectedProjectId
              ? environments.filter(e => String(e.project_id) === selectedProjectId)
              : environments
            ).map(env => (
              <option key={env.id} value={env.id}>
                {env.project_name ? `[${env.project_name}] ` : ''}{env.name} - {env.base_url}
              </option>
            ))}
          </select>
          {/* P2-7.3: Primary action - always visible */}
          <button
            onClick={() => { setShowImportDialog(true); setImportError(null); setImportSuccess(null) }}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center space-x-2 transition-colors"
          >
            <span>➕</span>
            <span>导入 / 生成用例</span>
          </button>
        </div>
      </div>
      
      <div className="bg-white rounded-lg shadow">
        <div className="p-6 border-b space-y-3">
          <CaseTypeTabs
            sourceFilter={sourceFilter}
            testCases={testCases}
            onChangeFilter={(key) => { setSourceFilter(key); setCurrentPage(1) }}
          />

          <CaseActionToolbar
            selectedCaseAnalysis={selectedCaseAnalysis}
            isExecuting={isExecuting}
            perfLoading={perfLoading}
            reviewLoading={reviewLoading}
            isDeleting={isDeleting}
            onBatchExecute={handleBatchExecute}
            onWebUiBatchExecute={handleWebUiBatchExecute}
            onShowPerfDialog={() => setShowPerfDialog(true)}
            onAiReview={handleAiReview}
            onExportExcel={handleExportExcel}
            onBatchDelete={handleBatchDelete}
            onAddToSuite={handleAddToSuite}
            onClearSelection={() => setSelectedIds([])}
          />

          <CaseMetricsPanel
            sourceFilter={sourceFilter}
            tabMetrics={tabMetrics}
            testCases={testCases}
            coverage={coverage}
            onRefreshCoverage={() => loadCoverage()}
          />

          {/* P2-7.3: PetStore example hint with project/env context and clickable reveal */}
          {hiddenPetStoreSampleCount > 0 && (
            <div className="px-3 py-2 bg-amber-50 border border-amber-200 rounded-lg text-sm text-amber-700 flex items-center justify-between">
              <span>
                当前环境 <strong>{selectedEnvironment?.name || ''}</strong> 非 PetStore Demo，已隐藏 {hiddenPetStoreSampleCount} 条示例用例，避免误执行。
              </span>
              <button onClick={() => setShowHiddenPetStore(prev => !prev)}
                className="text-xs text-amber-600 hover:text-amber-800 underline ml-2 whitespace-nowrap">
                {showHiddenPetStore ? '恢复隐藏' : '查看隐藏用例'}
              </button>
            </div>
          )}

          <input
            type="text"
            value={searchQuery}
            onChange={(e) => { setSearchQuery(e.target.value); setCurrentPage(1) }}
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
        
        <CaseListTable
          loading={loading}
          sourceFilter={sourceFilter}
          govFilteredCases={govFilteredCases}
          pagedCases={pagedCases}
          selectedIds={selectedIds}
          selectedTestCase={selectedTestCase}
          isExecuting={isExecuting}
          searchQuery={searchQuery}
          hasGovFilter={hasGovFilter}
          safePage={safePage}
          totalPages={totalPages}
          onSelectAll={handleSelectAll}
          onSelectOne={handleSelectOne}
          onViewDetail={handleViewDetail}
          onExecuteTest={handleExecuteTest}
          onGenerateScript={handleGenerateScript}
          onManualTest={handleManualTest}
          onSetCurrentPage={setCurrentPage}
        />
      </div>

      <CaseImportDialog
        show={showImportDialog}
        importTab={importTab}
        importError={importError}
        importSuccess={importSuccess}
        importLoading={importLoading}
        isGenerating={isGenerating}
        generationStep={generationStep}
        generationProgress={generationProgress}
        uploadFile={uploadFile}
        swaggerFile={swaggerFile}
        swaggerUrl={swaggerUrl}
        swaggerAuthType={swaggerAuthType}
        swaggerToken={swaggerToken}
        yapiBase={yapiBase}
        yapiProjectId={yapiProjectId}
        yapiEmail={yapiEmail}
        yapiPassword={yapiPassword}
        selectedProjectId={selectedProjectId}
        projects={projects}
        manualFormProps={{
          manualCaseType, manualTitle, manualModule, manualPriority, manualSteps, manualExpected, importLoading,
          webUiProps: {
            loginSession, useSession, webUiNeedLogin, webUiLoginMerchant, webUiLoginUser, webUiLoginPass, sessionSaving,
            scannerExpanded, scanUrl, scanLoading, scanResult, aiAvailable,
            webUiSteps, webUiAssertions, webUiBaseUrl,
            selectedProjectId, selectedEnvironmentId, environments,
            onSetUseSession: setUseSession, onSetWebUiNeedLogin: setWebUiNeedLogin,
            onSetWebUiLoginMerchant: setWebUiLoginMerchant, onSetWebUiLoginUser: setWebUiLoginUser,
            onSetWebUiLoginPass: setWebUiLoginPass,
            onSaveLoginSession: async () => {
              setSessionSaving(true)
              try {
                const env = environments.find(e=>String(e.project_id)===selectedProjectId)
                const base = env?.base_url ? new URL(env.base_url).origin : webUiBaseUrl
                const res = await api.v2.ui.saveLoginSession({
                  base_url: base, project_id: selectedProjectId,
                  login_steps: [
                    {action:'goto',target:'/index',value:''},
                    {action:'wait_for',target:'#merchantId',value:''},
                    {action:'fill',target:'#merchantId',value:webUiLoginMerchant},
                    {action:'fill',target:'#username',value:webUiLoginUser},
                    {action:'fill',target:'#password',value:webUiLoginPass},
                    {action:'click',target:'#agreementCheckbox',value:''},
                    {action:'click',target:'button[type=submit]',value:''},
                    {action:'wait_for',target:'5000',value:''},
                  ]
                })
                if(res.success){
                  setLoginSession({has_session:true,saved_at:new Date().toISOString(),page_title:res.page_title,cookie_count:res.cookie_count})
                  setUseSession(true); setWebUiNeedLogin(false)
                  setImportSuccess({count:0,message:'登录会话已保存! 后续测试自动携带登录态'})
                }
              } catch(e) { setImportError('登录保存失败: '+e.message) }
              finally { setSessionSaving(false) }
            },
            onDeleteLoginSession: async () => {
              await api.v2.ui.deleteLoginSession(selectedProjectId)
              setLoginSession(null); setUseSession(false)
            },
            onSetScannerExpanded: setScannerExpanded, onSetScanUrl: setScanUrl,
            onScanPage: async () => {
              let url = scanUrl.trim()
              if(!url){setImportError('请输入要扫描的URL');return}
              if(!url.startsWith('http')) url = 'https://'+url
              setScanLoading(true); setScanResult(null)
              try {
                const res = await api.v2.ui.scanPage({url, project_id: selectedProjectId||undefined})
                setScanResult(res)
                if(!webUiBaseUrl && url) { try { setWebUiBaseUrl(new URL(url).origin) } catch{} }
              } catch(e) { setImportError('扫描失败: '+e.message) }
              finally { setScanLoading(false) }
            },
            onAiGenerate: async () => {
              if(!aiAvailable){setImportError('AI 服务不可用，请配置 AI_PROVIDER 环境变量');return}
              setScanLoading(true)
              try {
                const res = await api.v2.ui.aiGenerate({
                  page_title: scanResult.page_title,
                  page_url: scanResult.page_url,
                  elements: (scanResult.elements||[]).slice(0, 30),
                })
                if(res.steps) {
                  setWebUiSteps(res.steps)
                  setWebUiAssertions(res.assertions || [{type:'element_visible',target:'body',value:'',description:'页面正常'}])
                  if(res.title) setManualTitle(res.title)
                  if(res.module) setManualModule(res.module)
                  if(!webUiBaseUrl && scanResult.page_url) { try { setWebUiBaseUrl(new URL(scanResult.page_url).origin) } catch{} }
                  setImportSuccess({count:0,message:'AI 已生成测试用例，请检查步骤并补充输入值'})
                }
              } catch(e) { setImportError('AI生成失败: '+e.message) }
              finally { setScanLoading(false) }
            },
            onAddScanElement: (el) => {
              setWebUiSteps(prev=>[...prev, { action: el.action_hint || 'click', target: el.selector, value: '', description: el.label || el.selector }])
            },
            onSetWebUiSteps: setWebUiSteps, onSetWebUiAssertions: setWebUiAssertions, onSetWebUiBaseUrl: setWebUiBaseUrl,
            onSetManualTitle: setManualTitle, onSetManualModule: setManualModule,
            onSetImportError: setImportError, onSetImportSuccess: setImportSuccess,
            onApplyTemplate: (tpl) => {
              setWebUiSteps(tpl.steps); setWebUiAssertions(tpl.asserts)
              if(!manualTitle) setManualTitle(tpl.l+'测试')
              if(!manualModule) setManualModule(tpl.m||'UI测试')
              const env = environments.find(e=>String(e.id)===String(selectedEnvironmentId))
              if(env?.base_url && !webUiBaseUrl) {
                try { setWebUiBaseUrl(new URL(env.base_url).origin) } catch { setWebUiBaseUrl(env.base_url.replace(/\/+$/,'')) }
              }
            },
            onQuickPageTest: () => {
              const path = document.getElementById('quickPath')?.value?.trim()
              if(!path){setImportError('请输入页面路径');return}
              const env = environments.find(e=>String(e.id)===String(selectedEnvironmentId))
              const base = env?.base_url || ''
              if(!base){setImportError('请先选择一个环境');return}
              try { setWebUiBaseUrl(new URL(base).origin) } catch { setWebUiBaseUrl(base.replace(/\/+$/,'')) }
              setWebUiSteps([
                {action:'goto',target:path,value:'',description:'打开页面'},
                {action:'wait_for',target:'2000',value:'',description:'等待加载'},
                {action:'screenshot',target:'',value:'',description:'截取页面'},
              ])
              setWebUiAssertions([
                {type:'url_contains',target:'',value:path.split('?')[0],description:'URL 正确'},
                {type:'element_visible',target:'body',value:'',description:'页面有内容'},
              ])
              if(!manualTitle) setManualTitle('页面测试 - ' + path)
              if(!manualModule) setManualModule('UI测试')
            },
          },
          onSetManualCaseType: setManualCaseType, onSetManualTitle: setManualTitle,
          onSetManualModule: setManualModule, onSetManualPriority: setManualPriority,
          onSetManualSteps: setManualSteps, onSetManualExpected: setManualExpected,
          onManualCreate: handleManualCreate,
        }}
        onTabChange={(key) => { setImportTab(key); setImportError(null); setImportSuccess(null) }}
        onClearError={() => setImportError(null)}
        onClearSuccess={() => setImportSuccess(null)}
        onClose={closeImportDialog}
        onNavigate={navigate}
        onSetUploadFile={setUploadFile}
        onSetSwaggerFile={setSwaggerFile}
        onSetSwaggerUrl={setSwaggerUrl}
        onSetSwaggerAuthType={setSwaggerAuthType}
        onSetSwaggerToken={setSwaggerToken}
        onSetYapiBase={setYapiBase}
        onSetYapiProjectId={setYapiProjectId}
        onSetYapiEmail={setYapiEmail}
        onSetYapiPassword={setYapiPassword}
        onSetSelectedProjectId={setSelectedProjectId}
        onImportRequirement={handleImportRequirement}
        onImportSwaggerFile={handleImportSwaggerFile}
        onImportSwaggerUrl={handleImportSwaggerUrl}
        onImportYapi={handleImportYapi}
      />

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

      <CaseDetailDialog
        show={showDetailDialog}
        selectedTestCase={selectedTestCase}
        isEditing={isEditing}
        editForm={editForm}
        editSaving={editSaving}
        onClose={() => { setShowDetailDialog(false); setIsEditing(false) }}
        onEnterEdit={enterEditMode}
        onCancelEdit={() => setIsEditing(false)}
        onSave={handleEditSave}
        onEditFormChange={(patch) => setEditForm(p => ({ ...p, ...patch }))}
        onEditStepChange={handleEditStepChange}
        onAddStep={handleAddStep}
        onRemoveStep={handleRemoveStep}
      />

      {/* 脚本生成对话框 */}
      {showScriptDialog && selectedTestCase && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl p-6 w-[800px] max-h-[80vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-bold">pytest 脚本</h2>
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
                <span className="ml-3 text-gray-600">正在生成 pytest 脚本...</span>
              </div>
            ) : (
              <div>
                <div className="mb-4">
                  <label className="block text-sm font-medium text-gray-700 mb-2">pytest 脚本 (可直接 pytest 运行，支持 API_BASE_URL / API_TOKEN 环境变量)</label>
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
                {executionResult.status === 'passed' ? '✅' : executionResult.status === 'no_assertion' ? '⚠️' : '❌'} {executionResult.is_web_ui_batch ? 'Web UI 批量执行结果' : executionResult.is_batch ? '批量执行结果' : executionResult.request_snapshot?.engine === 'playwright' ? 'Web UI 测试结果' : '接口测试结果'}
              </h2>
              <button onClick={() => setShowResultDialog(false)} className="text-gray-400 hover:text-gray-600 text-xl">✕</button>
            </div>
            
            <div className="mb-4 p-3 bg-blue-50 rounded border border-blue-200">
              <p className="text-sm text-blue-800">
                <span className="font-medium">{executionResult.is_batch ? '批量执行:' : '用例:'}</span> {executionResult.is_web_ui_batch ? `${executionResult.total_cases || 0} 个 Web UI 用例` : executionResult.is_batch ? `${executionResult.total_cases || 0} 个接口用例` : selectedTestCase?.title}
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
                {/* P2-7: Web UI 证据摘要 */}
                {executionResult.is_web_ui_batch && executionResult.trace_count > 0 && (
                  <div className="p-2.5 bg-amber-50 border border-amber-200 rounded text-xs text-amber-800 mb-2">
                    ⚠️ Trace 文件可能包含页面截图和调试信息，请勿外传。
                  </div>
                )}
                {executionResult.is_web_ui_batch && (
                  <div className="grid grid-cols-3 gap-2 mt-3 mb-2">
                    <div className="p-2 bg-violet-50 rounded border border-violet-200 text-center">
                      <div className="text-xs text-gray-500">Trace 文件</div>
                      <div className="text-base font-bold text-violet-600">{executionResult.trace_count || 0}</div>
                    </div>
                    <div className="p-2 bg-yellow-50 rounded border border-yellow-200 text-center">
                      <div className="text-xs text-gray-500">Console 错误</div>
                      <div className="text-base font-bold text-yellow-600">{executionResult.console_error_count || 0}</div>
                    </div>
                    <div className="p-2 bg-red-50 rounded border border-red-200 text-center">
                      <div className="text-xs text-gray-500">Network 错误</div>
                      <div className="text-base font-bold text-red-600">{executionResult.network_error_count || 0}</div>
                    </div>
                  </div>
                )}
                {/* P2-7: Web UI 用例明细 */}
                {executionResult.is_web_ui_batch && executionResult.case_results && (
                  <div className="mt-3">
                    <h3 className="text-sm font-semibold mb-2">Web UI 用例执行明细</h3>
                    <div className="border rounded overflow-hidden max-h-60 overflow-y-auto">
                      <table className="w-full text-sm">
                        <thead className="bg-gray-100 sticky top-0">
                          <tr>
                            <th className="px-3 py-2 text-left">用例ID</th>
                            <th className="px-3 py-2 text-left">标题</th>
                            <th className="px-3 py-2 text-center">状态</th>
                            <th className="px-3 py-2 text-center">耗时</th>
                            <th className="px-3 py-2 text-center">Trace</th>
                            <th className="px-3 py-2 text-center">Console</th>
                            <th className="px-3 py-2 text-center">Network</th>
                          </tr>
                        </thead>
                        <tbody>
                          {executionResult.case_results.map((cr, i) => (
                            <tr key={i} className={i % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                              <td className="px-3 py-1.5 text-xs font-mono">{(cr.case_id || '').slice(0, 12)}</td>
                              <td className="px-3 py-1.5 truncate max-w-[200px]">{cr.title || '-'}</td>
                              <td className="px-3 py-1.5 text-center">
                                <span className={`px-1.5 py-0.5 rounded text-xs ${cr.status === 'passed' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
                                  {cr.status === 'passed' ? 'PASS' : 'FAIL'}
                                </span>
                              </td>
                              <td className="px-3 py-1.5 text-center text-xs">{(cr.duration_ms || 0).toFixed(0)}ms</td>
                              <td className="px-3 py-1.5 text-center">{cr.trace_path ? <a href={`/api/v2/web-ui/traces/${cr.trace_path.replace(/\\/g, '/').split('/').pop()}`} target="_blank" rel="noreferrer" className="text-violet-600 underline text-xs">下载</a> : '-'}</td>
                              <td className="px-3 py-1.5 text-center text-xs">{cr.console_error_count || 0}</td>
                              <td className="px-3 py-1.5 text-center text-xs">{cr.network_error_count || 0}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
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

            {/* P2-4: Web UI Step 结果 */}
            {executionResult.response_snapshot?.step_results && executionResult.response_snapshot.step_results.length > 0 && (
              <div className="mb-4">
                <h3 className="text-sm font-semibold mb-2">Web UI 执行步骤</h3>
                <div className="space-y-1">
                  {executionResult.response_snapshot.step_results.map((sr, i) => (
                    <div key={i} className={`p-2 rounded border text-xs ${
                      sr.status === 'passed' ? 'bg-green-50 border-green-200' :
                      sr.status === 'skipped' ? 'bg-yellow-50 border-yellow-200' :
                      sr.status === 'failed' ? 'bg-red-50 border-red-200' : 'bg-gray-50 border-gray-200'
                    }`}>
                      <div className="flex items-center gap-2">
                        <span className="text-gray-400 w-5 text-center">{(sr.index ?? i) + 1}</span>
                        <span className={`px-1.5 py-0.5 rounded text-white text-xs ${
                          sr.status === 'passed' ? 'bg-green-500' : sr.status === 'skipped' ? 'bg-yellow-500' : 'bg-red-500'
                        }`}>
                          {sr.status === 'passed' ? '通过' : sr.status === 'skipped' ? '跳过' : '失败'}
                        </span>
                        <span className="px-1.5 py-0.5 bg-violet-100 text-violet-700 rounded font-mono">{sr.action}</span>
                        <span className="font-mono text-gray-600 truncate flex-1" title={sr.target}>{sr.target || '-'}</span>
                        {sr.description && <span className="text-gray-400">{sr.description}</span>}
                        <span className="text-gray-400 whitespace-nowrap">{sr.duration_ms ? Math.round(sr.duration_ms) + 'ms' : ''}</span>
                      </div>
                      {sr.error && <div className="mt-1 ml-7 text-red-600">{sr.error}</div>}
                      {sr.error_message && <div className="mt-1 ml-7 text-yellow-700">{sr.error_message}</div>}
                      {sr.current_url && sr.action === 'goto' && <div className="mt-1 ml-7 text-gray-400">URL: {sr.current_url}</div>}
                      {sr.screenshot && (
                        <div className="mt-2 ml-7">
                          <img src={`/screenshots/${sr.screenshot.split(/[/\\]/).pop()}`} alt={`步骤${i+1}截图`}
                            className="rounded border max-h-40 cursor-pointer hover:opacity-80"
                            onClick={()=>window.open(`/screenshots/${sr.screenshot.split(/[/\\]/).pop()}`,'_blank')} />
                        </div>
                      )}
                    </div>
                  ))}
                </div>
                {executionResult.response_snapshot.failure_screenshot && (
                  <div className="mt-2">
                    <p className="text-xs text-red-600 font-medium mb-1">失败时截图:</p>
                    <img src={`/screenshots/${executionResult.response_snapshot.failure_screenshot.split(/[/\\]/).pop()}`}
                      alt="失败截图" className="rounded border max-h-48 cursor-pointer hover:opacity-80"
                      onClick={()=>window.open(`/screenshots/${executionResult.response_snapshot.failure_screenshot.split(/[/\\]/).pop()}`,'_blank')} />
                  </div>
                )}
              </div>
            )}

            {/* P2-5: 视觉回归结果 */}
            {executionResult.response_snapshot?.visual_results?.length > 0 && (
              <div className="mb-4">
                <h3 className="text-sm font-semibold mb-2">视觉回归对比</h3>
                <div className="space-y-2">
                  {executionResult.response_snapshot.visual_results.map((vr, i) => (
                    <div key={i} className={`p-3 rounded border text-xs ${
                      vr.status === 'passed' ? 'bg-green-50 border-green-200' :
                      vr.status === 'baseline_created' ? 'bg-blue-50 border-blue-200' :
                      'bg-red-50 border-red-200'
                    }`}>
                      <div className="flex items-center gap-2 mb-1">
                        <span>{vr.status === 'passed' ? '✅' : vr.status === 'baseline_created' ? '📸' : '❌'}</span>
                        <span className="font-medium">{vr.name}</span>
                        {vr.baseline_created ? (
                          <span className="text-blue-600">首次运行已创建视觉基准图，请后续再次运行进行对比。</span>
                        ) : vr.status === 'passed' ? (
                          <span className="text-green-600">diff_ratio={vr.diff_ratio} (阈值: {vr.threshold})</span>
                        ) : (
                          <span className="text-red-600">视觉差异超过阈值 diff_ratio={vr.diff_ratio} &gt; {vr.threshold}</span>
                        )}
                      </div>
                      {!vr.baseline_created && (
                        <div className="flex gap-2 mt-2 flex-wrap">
                          {vr.baseline_path && (
                            <div className="text-center">
                              <div className="text-gray-500 mb-0.5">基准图</div>
                              <img src={`/visual/baselines/${vr.baseline_path.split(/[/\\]/).pop()}`} alt="baseline"
                                className="rounded border max-h-28 cursor-pointer hover:opacity-80"
                                onClick={()=>window.open(`/visual/baselines/${vr.baseline_path.split(/[/\\]/).pop()}`,'_blank')} />
                            </div>
                          )}
                          {vr.current_path && (
                            <div className="text-center">
                              <div className="text-gray-500 mb-0.5">当前截图</div>
                              <img src={`/visual/current/${vr.current_path.split(/[/\\]/).pop()}`} alt="current"
                                className="rounded border max-h-28 cursor-pointer hover:opacity-80"
                                onClick={()=>window.open(`/visual/current/${vr.current_path.split(/[/\\]/).pop()}`,'_blank')} />
                            </div>
                          )}
                          {vr.diff_path && (
                            <div className="text-center">
                              <div className="text-gray-500 mb-0.5">差异图</div>
                              <img src={`/visual/diff/${vr.diff_path.split(/[/\\]/).pop()}`} alt="diff"
                                className="rounded border max-h-28 cursor-pointer hover:opacity-80"
                                onClick={()=>window.open(`/visual/diff/${vr.diff_path.split(/[/\\]/).pop()}`,'_blank')} />
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
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


      <AiReviewDialog
        show={showReviewDialog}
        reviewResult={reviewResult}
        healingCases={healingCases}
        healPreviews={healPreviews}
        onClose={() => setShowReviewDialog(false)}
        onHealPreview={handleHealPreview}
        onHealRetry={handleHealRetry}
        onShowHealDialog={(preview) => { setHealDialogCase(preview); setShowHealDialog(true) }}
        onLocateCase={(caseId) => { setShowReviewDialog(false); setSearchQuery(caseId) }}
      />


      {/* AI 自愈预览确认对话框 */}
      {showHealDialog && healDialogCase && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-[60]">
          <div className="bg-white rounded-lg shadow-xl p-6 w-[700px] max-h-[85vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-bold">AI 自愈预览 — {healDialogCase.case_id}</h2>
              <button onClick={() => setShowHealDialog(false)} className="text-gray-400 hover:text-gray-600 text-xl">✕</button>
            </div>

            {healDialogCase.source && (
              <div className="mb-3 text-xs">
                <span className={`px-2 py-0.5 rounded ${healDialogCase.source === 'ai' ? 'bg-purple-100 text-purple-700' : 'bg-gray-100 text-gray-600'}`}>
                  来源: {healDialogCase.source === 'ai' ? 'AI 生成' : '规则降级'}
                </span>
              </div>
            )}

            <div className="mb-3 p-2 bg-yellow-50 border border-yellow-200 rounded text-xs text-yellow-800">
              ⚠️ AI 生成内容需人工确认后再应用，请仔细检查修改内容。
            </div>

            {healDialogCase.risk_warnings?.length > 0 && (
              <div className="mb-3 p-2 bg-red-50 border border-red-200 rounded">
                {healDialogCase.risk_warnings.map((w, i) => (
                  <div key={i} className="text-xs text-red-700">⛔ {w}</div>
                ))}
              </div>
            )}

            {healDialogCase.changes?.map((ch, i) => (
              <div key={i} className="mb-3 border border-gray-200 rounded overflow-hidden">
                <div className="bg-gray-100 px-3 py-1.5 text-xs font-bold text-gray-700 flex items-center justify-between">
                  <span>字段: {ch.field}</span>
                  <span className="text-gray-500">{ch.reason}</span>
                </div>
                <div className="grid grid-cols-2 gap-0 text-xs">
                  <div className="p-2 bg-red-50 border-r border-gray-200">
                    <div className="font-bold text-red-600 mb-1">修改前</div>
                    <pre className="whitespace-pre-wrap text-gray-700 max-h-32 overflow-y-auto">
                      {typeof ch.before === 'string' ? ch.before : JSON.stringify(ch.before, null, 2)}
                    </pre>
                  </div>
                  <div className="p-2 bg-green-50">
                    <div className="font-bold text-green-600 mb-1">修改后</div>
                    <pre className="whitespace-pre-wrap text-gray-700 max-h-32 overflow-y-auto">
                      {typeof ch.after === 'string' ? ch.after : JSON.stringify(ch.after, null, 2)}
                    </pre>
                  </div>
                </div>
              </div>
            ))}

            <div className="mt-4 flex justify-between">
              <button
                onClick={() => setShowHealDialog(false)}
                className="px-4 py-2 bg-gray-200 text-gray-700 rounded hover:bg-gray-300 text-sm"
              >取消</button>
              <div className="flex gap-2">
                <button
                  onClick={() => {
                    setShowHealDialog(false)
                    const ci = reviewResult?.ai_case_issues?.find(c => c.case_id === healDialogCase.case_id)
                    if (ci) handleHealRetry(ci)
                  }}
                  className="px-4 py-2 bg-blue-100 text-blue-700 rounded hover:bg-blue-200 text-sm"
                >重新生成</button>
                <button
                  onClick={() => handleHealApply(healDialogCase.case_id)}
                  disabled={healingCases[healDialogCase.case_id] === 'applying'}
                  className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 text-sm disabled:opacity-50"
                >
                  {healingCases[healDialogCase.case_id] === 'applying' ? '应用中...' : '确认应用修复'}
                </button>
              </div>
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
      <PerfConfigDialog
        show={showPerfDialog}
        perfConfig={perfConfig}
        perfLoading={perfLoading}
        selectedCount={selectedIds.length}
        onConfigChange={(patch) => setPerfConfig(p => ({ ...p, ...patch }))}
        onStart={handlePerfTest}
        onClose={() => setShowPerfDialog(false)}
      />

      <PerfResultDialog
        show={showPerfResult}
        perfResult={perfResult}
        onClose={() => setShowPerfResult(false)}
      />

      {/* P2-10: Suite Picker Dialog */}
      {showSuitePickerDialog && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl p-6 w-[420px] shadow-2xl">
            <h2 className="text-lg font-bold mb-4">选择测试集</h2>
            <p className="text-sm text-slate-500 mb-3">将选中的 {selectedIds.length} 条用例添加到测试集</p>
            {suitePickerList.length === 0 ? (
              <p className="text-sm text-slate-400 py-4 text-center">暂无测试集，请先在"测试集管理"页面创建</p>
            ) : (
              <select value={selectedSuiteId} onChange={e => setSelectedSuiteId(e.target.value)}
                className="w-full border rounded-lg px-3 py-2 text-sm mb-4">
                <option value="">-- 请选择 --</option>
                {suitePickerList.map(s => (
                  <option key={s.id} value={s.id}>{s.name} ({s.suite_type}, {s.case_count} 条用例)</option>
                ))}
              </select>
            )}
            <div className="flex justify-end gap-2">
              <button onClick={() => setShowSuitePickerDialog(false)} className="px-4 py-2 border rounded-lg text-sm">取消</button>
              <button onClick={handleConfirmAddToSuite} disabled={!selectedSuiteId}
                className="px-4 py-2 bg-indigo-600 text-white rounded-lg text-sm hover:bg-indigo-700 disabled:opacity-50">添加</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
