import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Search, Grid, List, Plus, Download } from 'lucide-react'
import { projectsAPI, testRunsAPI } from '../services/api'
import { useToast } from '../components/ui/Toast'
import { SkeletonCard } from '../components/ui/Skeleton'
import ConfirmDialog from '../components/ui/ConfirmDialog'
import ProjectCard from '../components/ProjectCard'
import EmptyState from '../components/EmptyState'

export default function ProjectsList() {
  const navigate = useNavigate()
  const toast = useToast()
  
  // 状态管理
  const [projects, setProjects] = useState([])
  const [loading, setLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState('')
  const [viewMode, setViewMode] = useState('grid')
  const [selectedIds, setSelectedIds] = useState([])
  
  // 筛选状态
  const [filters, setFilters] = useState({
    environment: 'all',
    status: 'all',
    owner: ''
  })
  
  // 对话框状态
  const [showDeleteDialog, setShowDeleteDialog] = useState(false)
  const [showCreateDialog, setShowCreateDialog] = useState(false)
  const [newProject, setNewProject] = useState({
    name: '',
    description: '',
    environment: 'development',
    baseUrl: 'http://localhost:8080'
  })

  useEffect(() => {
    loadProjects()
  }, [])

  const loadProjects = async () => {
    setLoading(true)
    try {
      const data = await projectsAPI.getAll()
      // 增强数据
      const enrichedProjects = (data.projects || []).map(p => ({
        ...p,
        owner: p.owner || '未分配',
        recentRuns: p.recentRuns || ['success', 'success', 'success', 'success', 'success'],
        failedCount: p.failedCount || 0,
        coverage: p.coverage || 0,
        testsCount: p.testsCount || 0
      }))
      setProjects(enrichedProjects)
    } catch (error) {
      console.error('加载失败:', error)
      toast.error('加载项目列表失败')
    } finally {
      setLoading(false)
    }
  }

  // 筛选和搜索
  const filteredProjects = projects.filter(project => {
    // 搜索过滤
    if (searchQuery) {
      const query = searchQuery.toLowerCase()
      const matchName = project.name?.toLowerCase().includes(query)
      const matchDescription = project.description?.toLowerCase().includes(query)
      const matchOwner = project.owner?.toLowerCase().includes(query)
      if (!matchName && !matchDescription && !matchOwner) return false
    }
    
    // 环境过滤
    if (filters.environment !== 'all' && project.environment !== filters.environment) {
      return false
    }
    
    // 状态过滤
    if (filters.status !== 'all' && project.status !== filters.status) {
      return false
    }
    
    // 负责人过滤
    if (filters.owner && !project.owner?.toLowerCase().includes(filters.owner.toLowerCase())) {
      return false
    }
    
    return true
  })

  // 选择操作
  const handleSelectAll = () => {
    if (selectedIds.length === filteredProjects.length) {
      setSelectedIds([])
    } else {
      setSelectedIds(filteredProjects.map(p => p.id))
    }
  }

  const handleSelectOne = (id) => {
    setSelectedIds(prev =>
      prev.includes(id) ? prev.filter(i => i !== id) : [...prev, id]
    )
  }

  // 项目操作
  const handleViewProject = (project) => {
    navigate(`/projects/${project.id}`)
  }

  const handleRunProject = async (project) => {
    try {
      const environmentId = project.default_environment_id
      if (!environmentId) {
        toast.warning('请先在项目详情中完成环境配置')
        return
      }

      const data = await testRunsAPI.start({ 
        project_id: project.id, 
        environment_id: environmentId,
        name: `${project.name} - 手动执行`,
      })
      
      if (data.success) {
        toast.success(`项目 "${project.name}" 已开始运行`)
      } else {
        toast.error('启动失败: ' + data.message)
      }
    } catch (error) {
      toast.error('启动失败: ' + error.message)
    }
  }

  const handleSettingsProject = (project) => {
    toast.info('设置功能开发中...')
  }

  // 批量操作
  const handleBatchRun = async () => {
    if (selectedIds.length === 0) return
    
    toast.info(`正在运行 ${selectedIds.length} 个项目...`)
    
    for (const id of selectedIds) {
      const project = projects.find(p => p.id === id)
      if (project) {
        await handleRunProject(project)
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
      for (const id of selectedIds) {
        await projectsAPI.delete(id)
      }
      
      setProjects(prev => prev.filter(p => !selectedIds.includes(p.id)))
      toast.success(`成功删除 ${selectedIds.length} 个项目`)
      setSelectedIds([])
      setShowDeleteDialog(false)
    } catch (error) {
      toast.error('删除失败: ' + error.message)
    }
  }

  // 创建项目
  const handleCreateProject = () => {
    setShowCreateDialog(true)
  }

  const handleSubmitCreate = async (e) => {
    e.preventDefault()
    
    if (!newProject.name.trim()) {
      toast.warning('请输入项目名称')
      return
    }
    
    try {
      await projectsAPI.create(newProject)
      toast.success('项目创建成功')
      setShowCreateDialog(false)
      setNewProject({
        name: '',
        description: '',
        environment: 'development',
        baseUrl: 'http://localhost:8080'
      })
      loadProjects()
    } catch (error) {
      toast.error('创建失败: ' + error.message)
    }
  }

  // 导出
  const handleExport = () => {
    const dataStr = JSON.stringify(projects, null, 2)
    const blob = new Blob([dataStr], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `projects_${new Date().toISOString().slice(0,10)}.json`
    a.click()
    URL.revokeObjectURL(url)
    toast.success('导出成功')
  }

  // 重置筛选
  const handleResetFilters = () => {
    setFilters({
      environment: 'all',
      status: 'all',
      owner: ''
    })
  }

  // 统计数据
  const stats = {
    total: projects.length,
    active: projects.filter(p => p.status === 'active').length,
    failed: projects.filter(p => p.failedCount > 10).length,
    lowCoverage: projects.filter(p => p.coverage < 60).length
  }

  return (
    <div className="min-h-screen bg-slate-50">
      {/* 页面头部 */}
      <div className="bg-white border-b border-slate-200">
        <div className="max-w-[1400px] mx-auto px-4 sm:px-6 py-6">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            <div>
              <h1 className="text-2xl sm:text-3xl font-bold text-slate-900">项目管理</h1>
              <p className="text-slate-600 mt-1">管理和监控测试项目</p>
            </div>
            
            <div className="flex flex-wrap items-center gap-3">
              <button
                onClick={handleExport}
                className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 flex items-center space-x-2 transition-colors"
              >
                <Download className="w-4 h-4" />
                <span className="hidden sm:inline">导出</span>
              </button>
              <button
                onClick={handleCreateProject}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 flex items-center space-x-2 transition-colors"
              >
                <Plus className="w-4 h-4" />
                <span className="hidden sm:inline">创建项目</span>
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
                <p className="text-sm text-slate-600">总项目</p>
                <p className="text-2xl font-bold text-slate-900">{stats.total}</p>
              </div>
              <div className="w-10 h-10 bg-slate-100 rounded-md flex items-center justify-center">
                <span className="text-xl">📁</span>
              </div>
            </div>
          </div>
          
          <div className="bg-white rounded-md border border-slate-200 p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-600">活跃项目</p>
                <p className="text-2xl font-bold text-green-600">{stats.active}</p>
              </div>
              <div className="w-10 h-10 bg-green-100 rounded-md flex items-center justify-center">
                <span className="text-xl">✅</span>
              </div>
            </div>
          </div>
          
          <div className="bg-white rounded-md border border-slate-200 p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-600">故障项目</p>
                <p className="text-2xl font-bold text-red-600">{stats.failed}</p>
              </div>
              <div className="w-10 h-10 bg-red-100 rounded-md flex items-center justify-center">
                <span className="text-xl">⚠️</span>
              </div>
            </div>
          </div>
          
          <div className="bg-white rounded-md border border-slate-200 p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-600">低覆盖率</p>
                <p className="text-2xl font-bold text-orange-600">{stats.lowCoverage}</p>
              </div>
              <div className="w-10 h-10 bg-orange-100 rounded-md flex items-center justify-center">
                <span className="text-xl">📊</span>
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
              placeholder="搜索项目（名称、描述、负责人）..."
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
                环境
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
                状态
              </label>
              <select
                value={filters.status}
                onChange={(e) => setFilters(prev => ({ ...prev, status: e.target.value }))}
                className="w-full px-3 py-2 border border-slate-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="all">全部</option>
                <option value="active">活跃</option>
                <option value="inactive">暂停</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2">
                负责人
              </label>
              <input
                type="text"
                value={filters.owner}
                onChange={(e) => setFilters(prev => ({ ...prev, owner: e.target.value }))}
                placeholder="输入负责人名称"
                className="w-full px-3 py-2 border border-slate-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>

          {(filters.environment !== 'all' || filters.status !== 'all' || filters.owner) && (
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
                checked={selectedIds.length === filteredProjects.length}
                onChange={handleSelectAll}
                className="w-4 h-4 text-blue-600 rounded"
              />
              <span className="text-sm text-blue-900">
                已选择 <span className="font-bold">{selectedIds.length}</span> 个项目
              </span>
            </div>
            <div className="flex items-center space-x-2">
              <button
                onClick={handleBatchRun}
                className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 text-sm"
              >
                批量运行
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

        {/* 项目列表 */}
        {loading ? (
          <div className={`grid gap-4 ${viewMode === 'grid' ? 'grid-cols-1 md:grid-cols-2 lg:grid-cols-3' : 'grid-cols-1'}`}>
            {[1, 2, 3, 4, 5, 6].map(i => (
              <SkeletonCard key={i} />
            ))}
          </div>
        ) : filteredProjects.length === 0 ? (
          <EmptyState
            title={searchQuery || Object.values(filters).some(v => v && v !== 'all') ? '未找到匹配的项目' : '暂无项目'}
            description={searchQuery || Object.values(filters).some(v => v && v !== 'all') ? '尝试调整搜索条件或筛选器' : '点击"创建项目"开始创建第一个项目'}
            action={
              !searchQuery && !Object.values(filters).some(v => v && v !== 'all') && (
                <button
                  onClick={handleCreateProject}
                  className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
                >
                  创建项目
                </button>
              )
            }
          />
        ) : (
          <div className={`grid gap-4 ${viewMode === 'grid' ? 'grid-cols-1 md:grid-cols-2 lg:grid-cols-3' : 'grid-cols-1'}`}>
            {filteredProjects.map(project => (
              <ProjectCard
                key={project.id}
                project={project}
                isSelected={selectedIds.includes(project.id)}
                onSelect={handleSelectOne}
                onView={handleViewProject}
                onRun={handleRunProject}
                onSettings={handleSettingsProject}
              />
            ))}
          </div>
        )}

        {/* 结果统计 */}
        {!loading && filteredProjects.length > 0 && (
          <div className="text-center text-sm text-slate-600">
            显示 {filteredProjects.length} / {projects.length} 个项目
          </div>
        )}
      </div>

      {/* 删除确认对话框 */}
      <ConfirmDialog
        isOpen={showDeleteDialog}
        title="确认删除"
        message={`确定要删除选中的 ${selectedIds.length} 个项目吗？此操作不可恢复。`}
        confirmText="删除"
        cancelText="取消"
        onConfirm={confirmBatchDelete}
        onCancel={() => setShowDeleteDialog(false)}
        type="danger"
      />

      {/* 创建项目对话框 */}
      {showCreateDialog && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl p-6 w-full max-w-md">
            <h2 className="text-xl font-bold mb-4">创建新项目</h2>
            
            <form onSubmit={handleSubmitCreate} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">
                  项目名称 *
                </label>
                <input
                  type="text"
                  value={newProject.name}
                  onChange={(e) => setNewProject({...newProject, name: e.target.value})}
                  className="w-full px-3 py-2 border border-slate-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="例如: 用户管理系统"
                  required
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">
                  项目描述
                </label>
                <textarea
                  value={newProject.description}
                  onChange={(e) => setNewProject({...newProject, description: e.target.value})}
                  className="w-full px-3 py-2 border border-slate-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="简要描述项目功能..."
                  rows="3"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">
                  环境 *
                </label>
                <select
                  value={newProject.environment}
                  onChange={(e) => setNewProject({...newProject, environment: e.target.value})}
                  className="w-full px-3 py-2 border border-slate-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="development">开发环境</option>
                  <option value="staging">测试环境</option>
                  <option value="production">生产环境</option>
                </select>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">
                  基础URL *
                </label>
                <input
                  type="text"
                  value={newProject.baseUrl}
                  onChange={(e) => setNewProject({...newProject, baseUrl: e.target.value})}
                  className="w-full px-3 py-2 border border-slate-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="http://localhost:8080"
                  required
                />
              </div>
              
              <div className="flex items-center space-x-3 pt-4">
                <button
                  type="submit"
                  className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
                >
                  创建项目
                </button>
                <button
                  type="button"
                  onClick={() => setShowCreateDialog(false)}
                  className="flex-1 px-4 py-2 border border-slate-300 text-slate-700 rounded-md hover:bg-slate-50 transition-colors"
                >
                  取消
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
