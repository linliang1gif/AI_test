import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Upload, Download, Trash2, Search, Grid, List } from 'lucide-react'
import api from '../services/api'
import { useToast } from '../components/ui/Toast'
import ConfirmDialog from '../components/ui/ConfirmDialog'
import { SkeletonCard } from '../components/ui/Skeleton'
import FilterPanel from '../components/FilterPanel'
import TestCaseCard from '../components/TestCaseCard'
import EmptyState from '../components/EmptyState'

export default function TestCasesList() {
  const navigate = useNavigate()
  const toast = useToast()
  
  // 状态管理
  const [testCases, setTestCases] = useState([])
  const [loading, setLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState('')
  const [viewMode, setViewMode] = useState('grid') // grid or list
  const [selectedIds, setSelectedIds] = useState([])
  
  // 筛选状态
  const [filters, setFilters] = useState({
    status: 'all',
    priority: 'all',
    source: 'all',
    module: ''
  })
  
  // 对话框状态
  const [showDeleteDialog, setShowDeleteDialog] = useState(false)
  const [deleting, setDeleting] = useState(false)
  const [showUploadDialog, setShowUploadDialog] = useState(false)
  const [uploadFile, setUploadFile] = useState(null)
  const [isGenerating, setIsGenerating] = useState(false)
  const [generationProgress, setGenerationProgress] = useState(0)
  
  // 智能执行状态
  const [isExecuting, setIsExecuting] = useState(false)
  const [executionProgress, setExecutionProgress] = useState(0)
  const [executionStatus, setExecutionStatus] = useState('') // 'preparing' | 'intelligence' | 'executing' | 'healing' | 'reporting' | 'success' | 'error'

  useEffect(() => {
    loadTestCases()
  }, [])

  const loadTestCases = async () => {
    setLoading(true)
    try {
      const result = await api.testCases.getAll()
      setTestCases(result.test_cases || result.data || [])
    } catch (error) {
      console.error('加载失败:', error)
      toast.error('加载测试用例失败')
    } finally {
      setLoading(false)
    }
  }

  // 筛选和搜索
  const filteredTestCases = testCases.filter(tc => {
    // 搜索过滤
    if (searchQuery && !tc.title?.toLowerCase().includes(searchQuery.toLowerCase())) {
      return false
    }
    
    // 状态过滤
    if (filters.status !== 'all' && tc.status !== filters.status) {
      return false
    }
    
    // 优先级过滤
    if (filters.priority !== 'all' && tc.priority !== filters.priority) {
      return false
    }
    
    // 来源过滤
    if (filters.source !== 'all' && tc.source !== filters.source) {
      return false
    }
    
    // 模块过滤
    if (filters.module && !tc.module?.toLowerCase().includes(filters.module.toLowerCase())) {
      return false
    }
    
    return true
  })

  // 选择操作
  const handleSelectAll = () => {
    if (selectedIds.length === filteredTestCases.length) {
      setSelectedIds([])
    } else {
      setSelectedIds(filteredTestCases.map(tc => tc.id))
    }
  }

  const handleSelectOne = (id) => {
    setSelectedIds(prev =>
      prev.includes(id) ? prev.filter(i => i !== id) : [...prev, id]
    )
  }

  // 批量删除
  const handleBatchDelete = async () => {
    setDeleting(true)
    try {
      const result = await api.testCases.batchDelete(selectedIds)
      
      if (result.success) {
        toast.success(`成功删除 ${result.deleted_count} 个测试用例`)
        // 清空选中状态
        setSelectedIds([])
        // 关闭对话框
        setShowDeleteDialog(false)
        // 重新加载数据
        await loadTestCases()
      } else {
        toast.error('删除失败: ' + result.error)
      }
    } catch (error) {
      toast.error('删除失败: ' + error.message)
    } finally {
      setDeleting(false)
    }
  }

  // 导出Excel
  const handleExport = async () => {
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
      toast.success('导出成功')
    } catch (error) {
      toast.error('导出失败: ' + error.message)
    }
  }

  // 文件上传生成
  const handleFileUpload = async () => {
    if (!uploadFile) return
    
    setIsGenerating(true)
    setGenerationProgress(0)
    
    try {
      const progressInterval = setInterval(() => {
        setGenerationProgress(prev => (prev >= 90 ? prev : prev + 2))
      }, 1000)

      const result = await api.testCases.generate(uploadFile)
      
      clearInterval(progressInterval)
      setGenerationProgress(100)
      
      if (result.success) {
        setTimeout(() => {
          toast.success(`成功生成 ${result.count} 个测试用例`)
          setShowUploadDialog(false)
          setUploadFile(null)
          setGenerationProgress(0)
          loadTestCases()
        }, 500)
      } else {
        toast.error('生成失败: ' + result.error)
        setGenerationProgress(0)
      }
    } catch (error) {
      toast.error('上传失败: ' + error.message)
      setGenerationProgress(0)
    } finally {
      setIsGenerating(false)
    }
  }

  // 重置筛选
  const handleResetFilters = () => {
    setFilters({
      status: 'all',
      priority: 'all',
      source: 'all',
      module: ''
    })
  }

  // 智能执行
  const handleIntelligentRun = async () => {
    if (selectedIds.length === 0) {
      toast.error('请先选择要执行的测试用例')
      return
    }

    setIsExecuting(true)
    setExecutionProgress(0)
    setExecutionStatus('preparing')

    try {
      // 模拟进度更新
      const progressSteps = [
        { status: 'preparing', progress: 10, delay: 500 },
        { status: 'intelligence', progress: 30, delay: 1000 },
        { status: 'executing', progress: 60, delay: 2000 },
        { status: 'healing', progress: 80, delay: 1000 },
        { status: 'reporting', progress: 95, delay: 500 }
      ]

      // 启动进度动画
      let currentStep = 0
      const progressInterval = setInterval(() => {
        if (currentStep < progressSteps.length) {
          const step = progressSteps[currentStep]
          setExecutionStatus(step.status)
          setExecutionProgress(step.progress)
          currentStep++
        }
      }, 800)

      // 调用智能执行API
      const result = await api.pipeline.runIntelligent({
        test_case_ids: selectedIds,
        environment: 'test',
        base_url: 'https://jsonplaceholder.typicode.com'
      })

      clearInterval(progressInterval)
      setExecutionProgress(100)
      setExecutionStatus('success')

      // 显示成功信息
      const stats = result.statistics || {}
      toast.success(
        `执行完成! 通过率: ${stats.pass_rate || '0%'}, ` +
        `通过: ${stats.passed_tests || 0}, 失败: ${stats.failed_tests || 0}`
      )

      // 延迟后跳转到测试运行页面
      setTimeout(() => {
        navigate('/test-runs')
      }, 1500)

    } catch (error) {
      setExecutionStatus('error')
      toast.error('执行失败: ' + error.message)
      
      // 3秒后重置状态
      setTimeout(() => {
        setIsExecuting(false)
        setExecutionProgress(0)
        setExecutionStatus('')
      }, 3000)
    }
  }

  // 获取执行状态文本
  const getExecutionStatusText = () => {
    switch (executionStatus) {
      case 'preparing': return '准备执行...'
      case 'intelligence': return '智能分析中...'
      case 'executing': return '执行测试中...'
      case 'healing': return '自动修复中...'
      case 'reporting': return '生成报告中...'
      case 'success': return '执行成功!'
      case 'error': return '执行失败'
      default: return ''
    }
  }

  // 获取执行状态颜色
  const getExecutionStatusColor = () => {
    switch (executionStatus) {
      case 'success': return 'text-green-600'
      case 'error': return 'text-red-600'
      default: return 'text-blue-600'
    }
  }

  return (
    <div className="min-h-screen bg-slate-50">
      {/* 页面头部 */}
      <div className="bg-white border-b border-slate-200">
        <div className="max-w-[1400px] mx-auto px-4 sm:px-6 py-6">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            <div>
              <h1 className="text-2xl sm:text-3xl font-bold text-slate-900">测试用例</h1>
              <p className="text-slate-600 mt-1">管理和生成测试用例</p>
            </div>
            
            <div className="flex flex-wrap items-center gap-3">
              {selectedIds.length > 0 && (
                <>
                  <button
                    onClick={handleIntelligentRun}
                    disabled={isExecuting}
                    className="px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2 transition-colors"
                  >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                    </svg>
                    <span>智能执行 ({selectedIds.length})</span>
                  </button>
                  <button
                    onClick={() => setShowDeleteDialog(true)}
                    className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 flex items-center space-x-2 transition-colors"
                  >
                    <Trash2 className="w-4 h-4" />
                    <span>删除 ({selectedIds.length})</span>
                  </button>
                </>
              )}
              <button
                onClick={handleExport}
                className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 flex items-center space-x-2 transition-colors"
              >
                <Download className="w-4 h-4" />
                <span className="hidden sm:inline">导出</span>
              </button>
              <button
                onClick={() => setShowUploadDialog(true)}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 flex items-center space-x-2 transition-colors"
              >
                <Upload className="w-4 h-4" />
                <span className="hidden sm:inline">导入文档</span>
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* 主内容区 */}
      <div className="max-w-[1400px] mx-auto px-4 sm:px-6 py-6 space-y-6">
        {/* 智能执行进度条 */}
        {isExecuting && (
          <div className="bg-white border border-slate-200 rounded-lg p-6 shadow-sm">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center space-x-3">
                <div className="relative">
                  <div className="w-10 h-10 border-4 border-blue-200 border-t-blue-600 rounded-full animate-spin" />
                </div>
                <div>
                  <h3 className="font-semibold text-slate-900">智能执行中</h3>
                  <p className={`text-sm ${getExecutionStatusColor()}`}>
                    {getExecutionStatusText()}
                  </p>
                </div>
              </div>
              <div className="text-right">
                <div className="text-2xl font-bold text-slate-900">{executionProgress}%</div>
                <div className="text-xs text-slate-500">执行进度</div>
              </div>
            </div>
            
            <div className="relative">
              <div className="w-full bg-slate-200 rounded-full h-3 overflow-hidden">
                <div 
                  className={`h-3 rounded-full transition-all duration-500 ${
                    executionStatus === 'success' ? 'bg-green-500' :
                    executionStatus === 'error' ? 'bg-red-500' :
                    'bg-blue-600'
                  }`}
                  style={{ width: `${executionProgress}%` }}
                />
              </div>
            </div>
            
            {/* 执行阶段指示器 */}
            <div className="mt-4 flex items-center justify-between text-xs">
              <div className={`flex items-center space-x-1 ${executionProgress >= 10 ? 'text-blue-600' : 'text-slate-400'}`}>
                <div className={`w-2 h-2 rounded-full ${executionProgress >= 10 ? 'bg-blue-600' : 'bg-slate-300'}`} />
                <span>准备</span>
              </div>
              <div className={`flex items-center space-x-1 ${executionProgress >= 30 ? 'text-blue-600' : 'text-slate-400'}`}>
                <div className={`w-2 h-2 rounded-full ${executionProgress >= 30 ? 'bg-blue-600' : 'bg-slate-300'}`} />
                <span>智能分析</span>
              </div>
              <div className={`flex items-center space-x-1 ${executionProgress >= 60 ? 'text-blue-600' : 'text-slate-400'}`}>
                <div className={`w-2 h-2 rounded-full ${executionProgress >= 60 ? 'bg-blue-600' : 'bg-slate-300'}`} />
                <span>执行测试</span>
              </div>
              <div className={`flex items-center space-x-1 ${executionProgress >= 80 ? 'text-blue-600' : 'text-slate-400'}`}>
                <div className={`w-2 h-2 rounded-full ${executionProgress >= 80 ? 'bg-blue-600' : 'bg-slate-300'}`} />
                <span>自动修复</span>
              </div>
              <div className={`flex items-center space-x-1 ${executionProgress >= 95 ? 'text-blue-600' : 'text-slate-400'}`}>
                <div className={`w-2 h-2 rounded-full ${executionProgress >= 95 ? 'bg-blue-600' : 'bg-slate-300'}`} />
                <span>生成报告</span>
              </div>
            </div>
          </div>
        )}
        
        {/* 搜索和视图切换 */}
        <div className="flex flex-col sm:flex-row gap-4">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-slate-400" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="搜索测试用例..."
              className="w-full pl-10 pr-4 py-2 border border-slate-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          
          <div className="flex items-center space-x-2">
            {selectedIds.length > 0 && (
              <button
                onClick={handleSelectAll}
                className="px-4 py-2 border border-slate-300 rounded-md hover:bg-slate-50 text-sm"
              >
                {selectedIds.length === filteredTestCases.length ? '取消全选' : '全选'}
              </button>
            )}
            <div className="flex border border-slate-300 rounded-md overflow-hidden">
              <button
                onClick={() => setViewMode('grid')}
                className={`px-3 py-2 ${viewMode === 'grid' ? 'bg-blue-50 text-blue-600' : 'bg-white text-slate-600 hover:bg-slate-50'}`}
              >
                <Grid className="w-5 h-5" />
              </button>
              <button
                onClick={() => setViewMode('list')}
                className={`px-3 py-2 border-l border-slate-300 ${viewMode === 'list' ? 'bg-blue-50 text-blue-600' : 'bg-white text-slate-600 hover:bg-slate-50'}`}
              >
                <List className="w-5 h-5" />
              </button>
            </div>
          </div>
        </div>

        {/* 筛选面板 */}
        <FilterPanel
          filters={filters}
          onFilterChange={setFilters}
          onReset={handleResetFilters}
        />

        {/* 测试用例列表 */}
        {loading ? (
          <div className={`grid gap-4 ${viewMode === 'grid' ? 'grid-cols-1 md:grid-cols-2 lg:grid-cols-3' : 'grid-cols-1'}`}>
            {[1, 2, 3, 4, 5, 6].map(i => (
              <SkeletonCard key={i} />
            ))}
          </div>
        ) : filteredTestCases.length === 0 ? (
          <EmptyState
            title={searchQuery || Object.values(filters).some(v => v && v !== 'all') ? '未找到匹配的测试用例' : '暂无测试用例'}
            description={searchQuery || Object.values(filters).some(v => v && v !== 'all') ? '尝试调整搜索条件或筛选器' : '点击"导入文档"开始生成测试用例'}
            action={
              !searchQuery && !Object.values(filters).some(v => v && v !== 'all') && (
                <button
                  onClick={() => setShowUploadDialog(true)}
                  className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
                >
                  导入需求文档
                </button>
              )
            }
          />
        ) : (
          <div className={`grid gap-4 ${viewMode === 'grid' ? 'grid-cols-1 md:grid-cols-2 lg:grid-cols-3' : 'grid-cols-1'}`}>
            {filteredTestCases.map((tc, index) => (
              <TestCaseCard
                key={`${tc.id}-${index}`}
                testCase={tc}
                isSelected={selectedIds.includes(tc.id)}
                onSelect={handleSelectOne}
                onView={(tc) => navigate(`/test-cases/${tc.id}`)}
                onExecute={(tc) => toast.info('执行测试: ' + tc.title)}
                onGenerateScript={(tc) => toast.info('生成脚本: ' + tc.title)}
                onManualTest={(tc) => toast.info('手动测试: ' + tc.title)}
                onBindDataset={(tc) => toast.info('绑定数据集: ' + tc.title)}
                onDelete={(tc) => {
                  setSelectedIds([tc.id])
                  setShowDeleteDialog(true)
                }}
              />
            ))}
          </div>
        )}

        {/* 结果统计 */}
        {!loading && filteredTestCases.length > 0 && (
          <div className="text-center text-sm text-slate-600">
            显示 {filteredTestCases.length} / {testCases.length} 个测试用例
          </div>
        )}
      </div>

      {/* 删除确认对话框 */}
      <ConfirmDialog
        isOpen={showDeleteDialog}
        onClose={() => setShowDeleteDialog(false)}
        onConfirm={handleBatchDelete}
        title="删除测试用例"
        message={`确定要删除选中的 ${selectedIds.length} 个测试用例吗？此操作不可恢复。`}
        confirmText="删除"
        cancelText="取消"
        type="danger"
        loading={deleting}
      />

      {/* 上传对话框 */}
      {showUploadDialog && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl p-6 w-full max-w-md">
            <h2 className="text-xl font-bold mb-4">AI生成测试用例</h2>
            
            <div className="mb-4">
              <label className="block text-sm font-medium text-slate-700 mb-2">
                选择需求文档
              </label>
              <input
                type="file"
                accept=".docx,.xlsx,.pdf,.doc,.xls,.txt"
                onChange={(e) => setUploadFile(e.target.files[0])}
                className="w-full px-3 py-2 border border-slate-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              {uploadFile && (
                <p className="mt-2 text-sm text-green-600">
                  ✓ 已选择: {uploadFile.name}
                </p>
              )}
            </div>

            {isGenerating && (
              <div className="mb-4">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-slate-700">生成中...</span>
                  <span className="text-sm text-slate-500">{generationProgress}%</span>
                </div>
                <div className="w-full bg-slate-200 rounded-full h-2">
                  <div 
                    className="bg-blue-600 h-2 rounded-full transition-all duration-500"
                    style={{ width: `${generationProgress}%` }}
                  />
                </div>
              </div>
            )}

            <div className="flex justify-end space-x-3">
              <button
                onClick={() => {
                  setShowUploadDialog(false)
                  setUploadFile(null)
                }}
                disabled={isGenerating}
                className="px-4 py-2 border border-slate-300 rounded-md hover:bg-slate-50 disabled:opacity-50"
              >
                取消
              </button>
              <button
                onClick={handleFileUpload}
                disabled={!uploadFile || isGenerating}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
              >
                {isGenerating ? '生成中...' : '开始生成'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
