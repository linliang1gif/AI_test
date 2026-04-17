import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { projectsAPI } from '../services/api'

// 模拟数据 - 增加最近执行历史
const mockProjects = [
  {
    id: 1,
    name: '用户管理系统',
    description: '用户注册、登录、权限管理等核心功能',
    environment: 'production',
    baseUrl: 'https://api.user.example.com',
    testsCount: 156,
    coverage: 92.5,
    lastRun: '2024-05-20 18:30:15',
    status: 'active',
    createdAt: '2024-01-15',
    team: '后端团队',
    owner: '张三',
    recentRuns: ['success', 'success', 'success', 'failed', 'success'], // 最近5次
    failedCount: 3,
    avgDuration: 245
  },
  {
    id: 2,
    name: '订单处理服务',
    description: '订单创建、支付、退款、物流跟踪',
    environment: 'staging',
    baseUrl: 'https://staging-order.example.com',
    testsCount: 203,
    coverage: 78.3,
    lastRun: '2024-05-20 17:45:22',
    status: 'active',
    createdAt: '2024-02-10',
    team: '业务团队',
    owner: '李四',
    recentRuns: ['success', 'failed', 'failed', 'success', 'success'],
    failedCount: 12,
    avgDuration: 567
  },
  {
    id: 3,
    name: '商品管理平台',
    description: '商品上架、库存管理、价格调整',
    environment: 'development',
    baseUrl: 'http://localhost:8080',
    testsCount: 89,
    coverage: 45.2,
    lastRun: '2024-05-20 16:20:10',
    status: 'inactive',
    createdAt: '2024-03-05',
    team: '前端团队',
    owner: '王五',
    recentRuns: ['failed', 'failed', 'success', 'failed', 'success'],
    failedCount: 28,
    avgDuration: 189
  },
  {
    id: 4,
    name: '支付网关接口',
    description: '支付宝、微信支付、银联支付集成',
    environment: 'production',
    baseUrl: 'https://pay.example.com',
    testsCount: 124,
    coverage: 95.8,
    lastRun: '2024-05-20 18:15:33',
    status: 'active',
    createdAt: '2024-01-20',
    team: '支付团队',
    owner: '赵六',
    recentRuns: ['success', 'success', 'success', 'success', 'success'],
    failedCount: 1,
    avgDuration: 423
  },
  {
    id: 5,
    name: '消息推送系统',
    description: 'APP推送、短信、邮件通知',
    environment: 'staging',
    baseUrl: 'https://staging-msg.example.com',
    testsCount: 67,
    coverage: 58.9,
    lastRun: '2024-05-20 15:50:45',
    status: 'active',
    createdAt: '2024-04-01',
    team: '运营团队',
    owner: '孙七',
    recentRuns: ['success', 'failed', 'success', 'success', 'failed'],
    failedCount: 15,
    avgDuration: 312
  }
]

export default function ProjectsPro() {
  const [projects, setProjects] = useState(mockProjects)
  const [selectedIds, setSelectedIds] = useState([])
  const [searchTerm, setSearchTerm] = useState('')
  const [filterEnv, setFilterEnv] = useState('all')
  const [filterOwner, setFilterOwner] = useState('')
  const [sortBy, setSortBy] = useState('coverage')
  const [sortOrder, setSortOrder] = useState('asc')

  useEffect(() => {
    projectsAPI.getAll()
      .then(data => {
        if (data.projects && data.projects.length > 0) {
          // 合并后端数据和模拟数据的字段
          const enrichedProjects = data.projects.map(p => ({
            ...p,
            owner: p.owner || '未分配',
            recentRuns: p.recentRuns || ['success', 'success', 'success', 'success', 'success'],
            failedCount: p.failedCount || 0,
            coverage: p.coverage || 0,
            testsCount: p.testsCount || 0
          }))
          setProjects(enrichedProjects)
        }
      })
      .catch(err => console.warn('使用模拟数据:', err.message))
  }, [])

  const handleSelectAll = (e) => {
    if (e.target.checked) {
      setSelectedIds(filteredProjects.map(p => p.id))
    } else {
      setSelectedIds([])
    }
  }

  const handleSelectOne = (id) => {
    setSelectedIds(prev => 
      prev.includes(id) ? prev.filter(i => i !== id) : [...prev, id]
    )
  }

  const handleBatchRun = () => {
    if (selectedIds.length === 0) return
    if (confirm(`确认批量运行 ${selectedIds.length} 个项目？`)) {
      alert(`正在运行 ${selectedIds.length} 个项目...`)
      setSelectedIds([])
    }
  }

  const handleBatchDelete = () => {
    if (selectedIds.length === 0) return
    if (confirm(`确认批量删除 ${selectedIds.length} 个项目？此操作不可恢复！`)) {
      setProjects(prev => prev.filter(p => !selectedIds.includes(p.id)))
      setSelectedIds([])
    }
  }

  const handleSort = (field) => {
    if (sortBy === field) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')
    } else {
      setSortBy(field)
      setSortOrder('asc')
    }
  }

  const handleResetSearch = () => {
    setSearchTerm('')
    setFilterEnv('all')
    setFilterOwner('')
  }

  const filteredProjects = projects
    .filter(p => {
      // 安全检查：确保所有字段都存在
      const name = p.name || ''
      const description = p.description || ''
      const owner = p.owner || ''
      
      const matchSearch = 
        name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        description.toLowerCase().includes(searchTerm.toLowerCase()) ||
        owner.toLowerCase().includes(searchTerm.toLowerCase())
      const matchEnv = filterEnv === 'all' || p.environment === filterEnv
      const matchOwner = !filterOwner || owner.toLowerCase().includes(filterOwner.toLowerCase())
      return matchSearch && matchEnv && matchOwner
    })
    .sort((a, b) => {
      let comparison = 0
      if (sortBy === 'coverage') {
        comparison = (a.coverage || 0) - (b.coverage || 0)
      } else if (sortBy === 'failedCount') {
        comparison = (a.failedCount || 0) - (b.failedCount || 0)
      } else if (sortBy === 'lastRun') {
        comparison = new Date(a.lastRun || 0) - new Date(b.lastRun || 0)
      }
      return sortOrder === 'asc' ? comparison : -comparison
    })

  const getEnvBadge = (env) => {
    const config = {
      production: { bg: 'bg-red-50', text: 'text-red-700', border: 'border-red-200', label: '生产' },
      staging: { bg: 'bg-purple-50', text: 'text-purple-700', border: 'border-purple-200', label: '测试' },
      development: { bg: 'bg-blue-50', text: 'text-blue-700', border: 'border-blue-200', label: '开发' }
    }
    const c = config[env] || config.development
    return (
      <span className={`px-2 py-0.5 text-xs font-medium rounded border ${c.bg} ${c.text} ${c.border}`}>
        {c.label}
      </span>
    )
  }

  const getCoverageColor = (coverage) => {
    if (coverage >= 90) return 'text-green-600'
    if (coverage >= 60) return 'text-orange-600'
    return 'text-red-600'
  }

  const renderRecentRuns = (runs) => {
    return (
      <div className="flex items-center gap-0.5">
        {runs.map((status, idx) => (
          <div
            key={idx}
            className={`w-3 h-3 rounded-sm ${
              status === 'success' ? 'bg-green-500' : 'bg-red-500'
            }`}
            title={status === 'success' ? '成功' : '失败'}
          />
        ))}
      </div>
    )
  }

  return (
    <div className="p-6 bg-slate-50 min-h-screen">
      <div className="mb-4">
        <h1 className="text-xl font-bold text-slate-900">项目管理</h1>
        <p className="text-xs text-slate-600 mt-0.5">监控项目健康度，快速定位故障</p>
      </div>

      <div className="grid grid-cols-4 gap-3 mb-4">
        <div className="bg-white border border-slate-200 p-3 rounded-md">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs text-slate-600">总项目</p>
              <p className="text-2xl font-bold text-slate-900">{projects.length}</p>
            </div>
            <div className="text-2xl">📁</div>
          </div>
        </div>
        
        <div className="bg-white border border-slate-200 p-3 rounded-md">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs text-slate-600">活跃项目</p>
              <p className="text-2xl font-bold text-green-600">
                {projects.filter(p => p.status === 'active').length}
              </p>
            </div>
            <div className="text-2xl">✓</div>
          </div>
        </div>
        
        <div className="bg-white border border-slate-200 p-3 rounded-md">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs text-slate-600">故障项目</p>
              <p className="text-2xl font-bold text-red-600">
                {projects.filter(p => p.failedCount > 10).length}
              </p>
            </div>
            <div className="text-2xl">⚠️</div>
          </div>
        </div>
        
        <div className="bg-white border border-slate-200 p-3 rounded-md">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs text-slate-600">低覆盖率</p>
              <p className="text-2xl font-bold text-orange-600">
                {projects.filter(p => p.coverage < 60).length}
              </p>
            </div>
            <div className="text-2xl">📉</div>
          </div>
        </div>
      </div>

      <div className="bg-white border border-slate-200 p-3 rounded-md mb-4">
        <div className="flex items-center gap-2">
          <div className="flex-1 relative">
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="按 / 快速搜索：项目名称、描述、负责人..."
              className="w-full px-3 py-1.5 text-sm border border-slate-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
          </div>
          
          <select
            value={filterEnv}
            onChange={(e) => setFilterEnv(e.target.value)}
            className="px-3 py-1.5 text-sm border border-slate-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
          >
            <option value="all">全部环境</option>
            <option value="production">生产</option>
            <option value="staging">测试</option>
            <option value="development">开发</option>
          </select>
          
          <input
            type="text"
            value={filterOwner}
            onChange={(e) => setFilterOwner(e.target.value)}
            placeholder="负责人"
            className="w-32 px-3 py-1.5 text-sm border border-slate-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
          />
          
          {(searchTerm || filterEnv !== 'all' || filterOwner) && (
            <button
              onClick={handleResetSearch}
              className="px-3 py-1.5 text-sm text-slate-600 hover:text-slate-900 border border-slate-300 rounded hover:bg-slate-50"
            >
              重置
            </button>
          )}
          
          <div className="text-xs text-slate-600 px-2 py-1.5 bg-slate-50 border border-slate-200 rounded">
            {filteredProjects.length} 项
          </div>
        </div>
      </div>

      {selectedIds.length > 0 && (
        <div className="bg-blue-50 border border-blue-200 p-3 rounded-md mb-4 flex items-center justify-between">
          <div className="text-sm text-blue-900">
            已选择 <span className="font-bold">{selectedIds.length}</span> 个项目
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={handleBatchRun}
              className="px-3 py-1.5 text-sm bg-blue-600 text-white rounded hover:bg-blue-700"
            >
              批量运行
            </button>
            <button
              onClick={handleBatchDelete}
              className="px-3 py-1.5 text-sm bg-red-600 text-white rounded hover:bg-red-700"
            >
              批量删除
            </button>
            <button
              onClick={() => setSelectedIds([])}
              className="px-3 py-1.5 text-sm text-slate-600 border border-slate-300 rounded hover:bg-white"
            >
              取消
            </button>
          </div>
        </div>
      )}

      <div className="bg-white border border-slate-200 rounded-md">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-slate-50 border-b border-slate-200">
              <tr>
                <th className="px-3 py-2 text-left w-10">
                  <input
                    type="checkbox"
                    checked={selectedIds.length === filteredProjects.length && filteredProjects.length > 0}
                    onChange={handleSelectAll}
                    className="rounded border-slate-300"
                  />
                </th>
                <th className="px-3 py-2 text-left text-xs font-semibold text-slate-600 uppercase">
                  项目名称
                </th>
                <th className="px-3 py-2 text-left text-xs font-semibold text-slate-600 uppercase">
                  环境
                </th>
                <th className="px-3 py-2 text-left text-xs font-semibold text-slate-600 uppercase">
                  负责人
                </th>
                <th className="px-3 py-2 text-left text-xs font-semibold text-slate-600 uppercase">
                  用例数
                </th>
                <th 
                  className="px-3 py-2 text-left text-xs font-semibold text-slate-600 uppercase cursor-pointer hover:text-blue-600"
                  onClick={() => handleSort('coverage')}
                >
                  <div className="flex items-center gap-1">
                    覆盖率
                    {sortBy === 'coverage' && (
                      <span className="text-blue-600">{sortOrder === 'asc' ? '↑' : '↓'}</span>
                    )}
                  </div>
                </th>
                <th 
                  className="px-3 py-2 text-left text-xs font-semibold text-slate-600 uppercase cursor-pointer hover:text-blue-600"
                  onClick={() => handleSort('failedCount')}
                >
                  <div className="flex items-center gap-1">
                    故障数
                    {sortBy === 'failedCount' && (
                      <span className="text-blue-600">{sortOrder === 'asc' ? '↑' : '↓'}</span>
                    )}
                  </div>
                </th>
                <th className="px-3 py-2 text-left text-xs font-semibold text-slate-600 uppercase">
                  最近5次
                </th>
                <th 
                  className="px-3 py-2 text-left text-xs font-semibold text-slate-600 uppercase cursor-pointer hover:text-blue-600"
                  onClick={() => handleSort('lastRun')}
                >
                  <div className="flex items-center gap-1">
                    最后运行
                    {sortBy === 'lastRun' && (
                      <span className="text-blue-600">{sortOrder === 'asc' ? '↑' : '↓'}</span>
                    )}
                  </div>
                </th>
                <th className="px-3 py-2 text-right text-xs font-semibold text-slate-600 uppercase">
                  操作
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200">
              {filteredProjects.map((project) => (
                <tr 
                  key={project.id} 
                  className="hover:bg-slate-50 transition-colors"
                >
                  <td className="px-3 py-2">
                    <input
                      type="checkbox"
                      checked={selectedIds.includes(project.id)}
                      onChange={() => handleSelectOne(project.id)}
                      className="rounded border-slate-300"
                    />
                  </td>
                  <td className="px-3 py-2">
                    <Link 
                      to={`/test-cases?project=${project.id}`}
                      className="text-blue-600 hover:text-blue-800 hover:underline font-medium"
                    >
                      {project.name || '未命名项目'}
                    </Link>
                    <div className="text-xs text-slate-500 mt-0.5 max-w-xs truncate">
                      {project.description || '暂无描述'}
                    </div>
                  </td>
                  <td className="px-3 py-2">
                    {getEnvBadge(project.environment || 'development')}
                  </td>
                  <td className="px-3 py-2 text-slate-700">
                    {project.owner || '未分配'}
                  </td>
                  <td className="px-3 py-2 text-slate-700">
                    {project.testsCount || 0}
                  </td>
                  <td className="px-3 py-2">
                    <Link
                      to={`/reports?project=${project.id}`}
                      className={`font-semibold hover:underline ${getCoverageColor(project.coverage || 0)}`}
                    >
                      {(project.coverage || 0).toFixed(1)}%
                    </Link>
                  </td>
                  <td className="px-3 py-2">
                    <span className={`font-semibold ${
                      (project.failedCount || 0) > 20 ? 'text-red-600' :
                      (project.failedCount || 0) > 10 ? 'text-orange-600' : 'text-slate-700'
                    }`}>
                      {project.failedCount || 0}
                    </span>
                  </td>
                  <td className="px-3 py-2">
                    {renderRecentRuns(project.recentRuns || ['success', 'success', 'success', 'success', 'success'])}
                  </td>
                  <td className="px-3 py-2 text-xs text-slate-600">
                    {project.lastRun || '未运行'}
                  </td>
                  <td className="px-3 py-2 text-right">
                    <div className="flex items-center justify-end gap-1">
                      <button
                        onClick={() => alert(`运行项目: ${project.name}`)}
                        className="p-1 text-slate-600 hover:text-green-600 hover:bg-green-50 rounded"
                        title="运行"
                      >
                        ▶
                      </button>
                      <button
                        onClick={() => alert(`查看日志: ${project.name}`)}
                        className="p-1 text-slate-600 hover:text-blue-600 hover:bg-blue-50 rounded"
                        title="日志"
                      >
                        📄
                      </button>
                      <button
                        onClick={() => alert(`编辑: ${project.name}`)}
                        className="p-1 text-slate-600 hover:text-slate-900 hover:bg-slate-100 rounded"
                        title="编辑"
                      >
                        ✏
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        
        <div className="px-3 py-2 border-t border-slate-200 flex items-center justify-between bg-slate-50">
          <div className="text-xs text-slate-600">
            显示 {filteredProjects.length} 条记录
          </div>
          <div className="flex gap-1">
            <button className="px-2 py-1 text-xs border border-slate-300 rounded hover:bg-white disabled:opacity-50" disabled>
              上一页
            </button>
            <button className="px-2 py-1 text-xs bg-blue-600 text-white rounded">1</button>
            <button className="px-2 py-1 text-xs border border-slate-300 rounded hover:bg-white">2</button>
            <button className="px-2 py-1 text-xs border border-slate-300 rounded hover:bg-white">
              下一页
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
