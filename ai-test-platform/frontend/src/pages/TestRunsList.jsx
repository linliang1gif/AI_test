import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Search, Grid, List, Play, Download, RefreshCw } from 'lucide-react'
import { testRunsAPI } from '../services/api'
import { useToast } from '../components/ui/Toast'
import { SkeletonCard } from '../components/ui/Skeleton'
import ConfirmDialog from '../components/ui/ConfirmDialog'
import ExecutionCard from '../components/ExecutionCard'
import EmptyState from '../components/EmptyState'

export default function TestRunsList() {
  const navigate = useNavigate()
  const toast = useToast()
  
  // 状态管理
  const [executions, setExecutions] = useState([])
  const [loading, setLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState('')
  const [viewMode, setViewMode] = useState('grid')
  const [selectedIds, setSelectedIds] = useState([])
  const [autoRefresh, setAutoRefresh] = useState(false)
  
  // 筛选状态
  const [filters, setFilters] = useState({
    status: 'all',
    environment: 'all',
    dateRange: 'all'
  })
  
  // 对话框状态
  const [showDeleteDialog, setShowDeleteDialog] = useState(false)

  useEffect(() => {
    loadExecutions()
  }, [])

  // 自动刷新
  useEffect(() => {
    if (autoRefresh) {
      const interval = setInterval(() => {
        loadExecutions(true) // 静默刷新
      }, 3000)
      return () => clearInterval(interval)
    }
  }, [autoRefresh])

  const loadExecutions = async (silent = false) => {
    if (!silent) setLoading(true)
    try {
      const data = await testRunsAPI.getAll()
      const runs = (data.testRuns || []).filter(r => r).map(r => ({
        ...r,
        environment: r.environment || 'development',
        totalTests: r.totalTests || 0,
        passed: r.passed || 0,
        failed: r.failed || 0,
        pending: r.pending || 0,
        progress: r.progress || 0
      }))
      setExecutions(runs)
    } catch (error) {
      console.error('加载失败:', error)
      if (!silent) toast.error('加载执行记录失败')
    } finally {
      if (!silent) setLoading(false)
    }
  }

  // 筛选和搜索
  const filteredExecutions = executions.filter(execution => {
    // 搜索过滤
    if (searchQuery) {
      const query = searchQuery.toLowerCase()
      const matchName = execution.name?.toLowerCase().includes(query)
      const matchId = execution.id?.toString().includes(query)
      if (!matchName && !matchId) return false
    }
    
    // 状态过滤
    if (filters.status !== 'all' && execution.status !== filters.status) {
      return false
    }
    
    // 环境过滤
    if (filters.environment !== 'all' && execution.environment !== filters.environment) {
      return false
    }
    
    // 日期范围过滤
    if (filters.dateRange !== 'all') {
      const now = new Date()
      const executionDate = new Date(execution.startTime)
      const diffHours = (now - executionDate) / (1000 * 60 * 60)
      
      if (filters.dateRange === 'today' && diffHours > 24) return false
      if (filters.dateRange === 'week' && diffHours > 168) return false
      if (filters.dateRange === 'month' && diffHours > 720) return false
    }
    
    return true
  })

  // 选择操作
  const handleSelectAll = () => {
    if (selectedIds.length === filteredExecutions.length) {
      setSelectedIds([])
    } else {
      setSelectedIds(filteredExecutions.map(e => e.id))
    }
  }

  const handleSelectOne = (id) => {
    setSelectedIds(prev =>
      prev.includes(id) ? prev.filter(i => i !== id) : [...prev, id]
    )
  }

  // 执行操作
  const handleViewExecution = (execution) => {
    navigate(`/test-runs/${execution.id}`)
  }

  const handleRerunExecution = async (execution) => {
    try {
      await testRunsAPI.start({
        environment: execution.environment,
        project_id: execution.project_id,
        test_case_ids: execution.test_case_ids
      })
      toast.success('测试已重新启动')
      loadExecutions()
    } catch (error) {
      toast.error('重新运行失败: ' + error.message)
    }
  }

  const handleViewReport = (execution) => {
    navigate(`/reports/${execution.report_id || execution.id}`)
  }

  // 批量操作
  const handleBatchRerun = async () => {
    if (selectedIds.length === 0) return
    
    toast.info(`正在重新运行 ${selectedIds.length} 个测试...`)
    
    for (const id of selectedIds) {
      const execution = executions.find(e => e.id === id)
      if (execution) {
        await handleRerunExecution(execution)
      }
    }
    
    setSelectedIds([])
  }

  const handleBatchDelete = () => {
    if (selectedIds.length === 0) return
    setShowDeleteDialog(true)
  }

  const confirmBatchDelete = async () => {
    try {
      // 这里应该调用删除API
      setExecutions(prev => prev.filter(e => !selectedIds.includes(e.id)))
      toast.success(`成功删除 ${selectedIds.length} 条记录`)
      setSelectedIds([])
      setShowDeleteDialog(false)
    } catch (error) {
      toast.error('删除失败: ' + error.message)
    }
  }

  // 新建测试
  const handleRunNew = async () => {
    try {
      await testRunsAPI.start({ environment: 'staging' })
      toast.success('测试已启动')
      loadExecutions()
    } catch (error) {
      toast.error('启动失败: ' + error.message)
    }
  }

  // 导出
  const handleExport = () => {
    const dataStr = JSON.stringify(executions, null, 2)
    const blob = new Blob([dataStr], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `test-runs_${new Date().toISOString().slice(0,10)}.json`
    a.click()
    URL.revokeObjectURL(url)
    toast.success('导出成功')
  }

  // 重置筛选
  const handleResetFilters = () => {
    setFilters({
      status: 'all',
      environment: 'all',
      dateRange: 'all'
    })
  }

  // 统计数据
  const stats = {
    total: executions.length,
    running: executions.filter(e => e.status === 'running').length,
    completed: executions.filter(e => e.status === 'completed' || e.status === 'passed').length,
    failed: executions.filter(e => e.status === 'failed').length
  }

  return (
    <div className="min-h-screen bg-slate-50">
      {/* 页面头部 */}
      <div className="bg-white border-b border-slate-200">
        <div className="max-w-[1400px] mx-auto px-4 sm:px-6 py-6">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            <div>
              <h1 className="text-2xl sm:text-3xl font-bold text-slate-900">测试执行</h1>
              <p className="text-slate-600 mt-1">监控和管理测试执行记录</p>
            </div>
            
            <div className="flex flex-wrap items-center gap-3">
              <label className="flex items-center space-x-2 text-sm text-slate-600">
                <input
                  type="checkbox"
                  checked={autoRefresh}
                  onChange={(e) => setAutoRefresh(e.target.checked)}
                  className="rounded border-slate-300"
                />
                <span>自动刷新</span>
              </label>
              <button
                onClick={() => loadExecutions()}
                className="px-4 py-2 bg-slate-600 text-white rounded-md hover:bg-slate-700 flex items-center space-x-2 transition-colors"
              >
                <RefreshCw className="w-4 h-4" />
                <span className="hidden sm:inline">刷新</span>
              </button>
              <button
                onClick={handleExport}
                className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 flex items-center space-x-2 transition-colors"
              >
                <Download className="w-4 h-4" />
                <span className="hidden sm:inline">导出</span>
              </button>
              <button
                onClick={handleRunNew}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 flex items-center space-x-2 transition-colors"
              >
                <Play className="w-4 h-4" />
                <span className="hidden sm:inline">运行新测试</span>
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* 主内容区 */}
      <div className="max-w-[1400px] mx-auto px-4 sm:px-6 py-6 space-y-6">
        {/* 统计卡片 */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-white rounded-md border border-slate-200 p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-600">总执行数</p>
                <p className="text-2xl font-bold text-slate-900">{stats.total}</p>
              </div>
              <div className="w-10 h-10 bg-slate-100 rounded-md flex items-center justify-center">
                <span className="text-xl">📊</span>
              </div>
            </div>
          </div>
          
          <div className="bg-white rounded-md border border-orange-200 p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-orange-600">执行中</p>
                <p className="text-2xl font-bold text-orange-600">{stats.running}</p>
              </div>
              <div className="w-10 h-10 bg-orange-100 rounded-md flex items-center justify-center">
                <span className="text-xl">⏳</span>
              </div>
            </div>
          </div>
          
          <div className="bg-white rounded-md border border-green-200 p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-green-600">已完成</p>
                <p className="text-2xl font-bold text-green-600">{stats.completed}</p>
              </div>
              <div className="w-10 h-10 bg-green-100 rounded-md flex items-center justify-center">
                <span className="text-xl">✅</span>
              </div>
            </div>
          </div>
          
          <div className="bg-white rounded-md border border-red-200 p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-red-600">失败</p>
                <p className="text-2xl font-bold text-red-600">{stats.failed}</p>
              </div>
              <div className="w-10 h-10 bg-red-100 rounded-md flex items-center justify-center">
                <span className="text-xl">❌</span>
              </div>
            </div>
          </div>
        </div>

        {/* 搜索和视图切换 */}
        <div className="flex flex-col sm:flex-row gap-4">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-slate-400" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="搜索执行记录（名称、ID）..."
              className="w-full pl-10 pr-4 py-2 border border-slate-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          
          <div className="flex items-center space-x-2">
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
        <div className="bg-white rounded-md border border-slate-200 p-4 sm:p-6">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2">
                执行状态
              </label>
              <select
                value={filters.status}
                onChange={(e) => setFilters(prev => ({ ...prev, status: e.target.value }))}
                className="w-full px-3 py-2 border border-slate-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="all">全部</option>
                <option value="running">执行中</option>
                <option value="completed">已完成</option>
                <option value="failed">失败</option>
                <option value="paused">已暂停</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2">
                执行环境
              </label>
              <select
                value={filters.environment}
                onChange={(e) => setFilters(prev => ({ ...prev, environment: e.target.value }))}
                className="w-full px-3 py-2 border border-slate-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="all">全部</option>
                <option value="production">生产环境</option>
                <option value="staging">测试环境</option>
                <option value="development">开发环境</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2">
                时间范围
              </label>
              <select
                value={filters.dateRange}
                onChange={(e) => setFilters(prev => ({ ...prev, dateRange: e.target.value }))}
                className="w-full px-3 py-2 border border-slate-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="all">全部</option>
                <option value="today">今天</option>
                <option value="week">最近7天</option>
                <option value="month">最近30天</option>
              </select>
            </div>
          </div>

          {(filters.status !== 'all' || filters.environment !== 'all' || filters.dateRange !== 'all') && (
            <div className="mt-4 pt-4 border-t border-slate-200 flex justify-end">
              <button
                onClick={handleResetFilters}
                className="px-4 py-2 text-sm text-slate-600 hover:text-slate-900"
              >
                重置筛选
              </button>
            </div>
          )}
        </div>

        {/* 批量操作栏 */}
        {selectedIds.length > 0 && (
          <div className="bg-blue-50 border border-blue-200 rounded-md p-4 flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <input
                type="checkbox"
                checked={selectedIds.length === filteredExecutions.length}
                onChange={handleSelectAll}
                className="w-4 h-4 text-blue-600 rounded"
              />
              <span className="text-sm text-blue-900">
                已选择 <span className="font-bold">{selectedIds.length}</span> 条记录
              </span>
            </div>
            <div className="flex items-center space-x-2">
              <button
                onClick={handleBatchRerun}
                className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 text-sm"
              >
                批量重运行
              </button>
              <button
                onClick={handleBatchDelete}
                className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 text-sm"
              >
                批量删除
              </button>
              <button
                onClick={() => setSelectedIds([])}
                className="px-4 py-2 border border-slate-300 rounded-md hover:bg-white text-sm"
              >
                取消选择
              </button>
            </div>
          </div>
        )}

        {/* 执行记录列表 */}
        {loading ? (
          <div className={`grid gap-4 ${viewMode === 'grid' ? 'grid-cols-1 md:grid-cols-2 lg:grid-cols-3' : 'grid-cols-1'}`}>
            {[1, 2, 3, 4, 5, 6].map(i => (
              <SkeletonCard key={i} />
            ))}
          </div>
        ) : filteredExecutions.length === 0 ? (
          <EmptyState
            title={searchQuery || Object.values(filters).some(v => v !== 'all') ? '未找到匹配的执行记录' : '暂无执行记录'}
            description={searchQuery || Object.values(filters).some(v => v !== 'all') ? '尝试调整搜索条件或筛选器' : '点击"运行新测试"开始执行测试'}
            action={
              !searchQuery && !Object.values(filters).some(v => v !== 'all') && (
                <button
                  onClick={handleRunNew}
                  className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
                >
                  运行新测试
                </button>
              )
            }
          />
        ) : (
          <div className={`grid gap-4 ${viewMode === 'grid' ? 'grid-cols-1 md:grid-cols-2 lg:grid-cols-3' : 'grid-cols-1'}`}>
            {filteredExecutions.map(execution => (
              <ExecutionCard
                key={execution.id}
                execution={execution}
                isSelected={selectedIds.includes(execution.id)}
                onSelect={handleSelectOne}
                onView={handleViewExecution}
                onRerun={handleRerunExecution}
                onViewReport={handleViewReport}
              />
            ))}
          </div>
        )}

        {/* 结果统计 */}
        {!loading && filteredExecutions.length > 0 && (
          <div className="text-center text-sm text-slate-600">
            显示 {filteredExecutions.length} / {executions.length} 条执行记录
          </div>
        )}
      </div>

      {/* 删除确认对话框 */}
      <ConfirmDialog
        isOpen={showDeleteDialog}
        title="确认删除"
        message={`确定要删除选中的 ${selectedIds.length} 条执行记录吗？此操作不可恢复。`}
        confirmText="删除"
        cancelText="取消"
        onConfirm={confirmBatchDelete}
        onCancel={() => setShowDeleteDialog(false)}
        type="danger"
      />
    </div>
  )
}
