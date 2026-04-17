import { useState, useEffect } from 'react'
import { 
  TrendingUp, TrendingDown, Activity, CheckCircle2, 
  XCircle, Target, Clock, Play, RotateCcw, FileText
} from 'lucide-react'
import { dashboardAPI } from '../services/api'

// 模拟真实数据
const mockData = {
  stats: {
    totalTests: 1247,
    passed: 1089,
    failed: 158,
    coverage: 78.5,
    trends: {
      totalTests: 5.2,
      passed: 3.8,
      failed: -12.5,
      coverage: 2.1
    }
  },
  trendData: [
    { date: '05-14', rate: 85.2 },
    { date: '05-15', rate: 87.1 },
    { date: '05-16', rate: 84.8 },
    { date: '05-17', rate: 88.3 },
    { date: '05-18', rate: 86.9 },
    { date: '05-19', rate: 89.5 },
    { date: '05-20', rate: 87.3 }
  ],
  recentExecutions: [
    {
      id: 1,
      apiName: '用户登录接口',
      method: 'POST',
      path: '/api/v1/auth/login',
      executor: '张三',
      duration: 245,
      executeTime: '2024-05-20 18:22:01',
      status: 'success'
    },
    {
      id: 2,
      apiName: '获取用户信息',
      method: 'GET',
      path: '/api/v1/user/profile',
      executor: '李四',
      duration: 128,
      executeTime: '2024-05-20 18:21:45',
      status: 'success'
    },
    {
      id: 3,
      apiName: '创建订单',
      method: 'POST',
      path: '/api/v1/order/create',
      executor: '王五',
      duration: 1523,
      executeTime: '2024-05-20 18:21:30',
      status: 'failed'
    },
    {
      id: 4,
      apiName: '查询订单列表',
      method: 'GET',
      path: '/api/v1/order/list',
      executor: '赵六',
      duration: 342,
      executeTime: '2024-05-20 18:21:15',
      status: 'success'
    },
    {
      id: 5,
      apiName: '更新商品库存',
      method: 'PUT',
      path: '/api/v1/product/stock',
      executor: '张三',
      duration: 567,
      executeTime: '2024-05-20 18:20:58',
      status: 'success'
    },
    {
      id: 6,
      apiName: '删除购物车项',
      method: 'DELETE',
      path: '/api/v1/cart/item/{id}',
      executor: '李四',
      duration: 89,
      executeTime: '2024-05-20 18:20:42',
      status: 'failed'
    },
    {
      id: 7,
      apiName: '支付回调接口',
      method: 'POST',
      path: '/api/v1/payment/callback',
      executor: '王五',
      duration: 2134,
      executeTime: '2024-05-20 18:20:25',
      status: 'success'
    },
    {
      id: 8,
      apiName: '获取商品详情',
      method: 'GET',
      path: '/api/v1/product/{id}',
      executor: '赵六',
      duration: 156,
      executeTime: '2024-05-20 18:20:10',
      status: 'success'
    }
  ]
}

// 统计卡片组件 - 增强版（带渐变背景和浮现感）
function StatCard({ title, value, trend, icon: Icon, color, lowThreshold, highThreshold }) {
  const isLow = lowThreshold && value < lowThreshold
  const isHigh = highThreshold && value > highThreshold
  const trendUp = trend > 0
  
  const colorClasses = {
    blue: 'bg-gradient-to-br from-blue-50 to-blue-100 text-blue-600 border-blue-200',
    green: 'bg-gradient-to-br from-green-50 to-green-100 text-green-600 border-green-200',
    red: 'bg-gradient-to-br from-red-50 to-red-100 text-red-600 border-red-200',
    purple: 'bg-gradient-to-br from-purple-50 to-purple-100 text-purple-600 border-purple-200',
    orange: 'bg-gradient-to-br from-orange-50 to-orange-100 text-orange-600 border-orange-200'
  }
  
  const bgColor = isLow ? 'bg-gradient-to-br from-orange-50 to-orange-100' : isHigh ? 'bg-gradient-to-br from-red-50 to-red-100' : 'bg-gradient-to-br from-white to-slate-50'
  const valueColor = isLow ? 'text-orange-600' : isHigh ? 'text-red-600' : `text-${color}-600`
  const borderColor = isLow ? 'border-orange-200' : isHigh ? 'border-red-200' : 'border-slate-200'
  
  return (
    <div className={`${bgColor} rounded-lg border-2 ${borderColor} p-5 transition-all hover:shadow-lg hover:scale-105 hover:-translate-y-1`}>
      <div className="flex items-center justify-between mb-3">
        <span className="text-sm font-medium text-slate-700">{title}</span>
        <div className={`p-2 rounded-lg ${colorClasses[color]}`}>
          <Icon className="w-4 h-4" />
        </div>
      </div>
      <div className="flex items-end justify-between">
        <div>
          <div className={`text-3xl font-bold ${valueColor}`}>
            {typeof value === 'number' && value % 1 !== 0 ? value.toFixed(1) : value}
            {title.includes('覆盖率') && '%'}
          </div>
          {trend !== undefined && (
            <div className={`flex items-center mt-2 text-xs ${trendUp ? 'text-green-600' : 'text-red-600'}`}>
              {trendUp ? <TrendingUp className="w-3 h-3 mr-1" /> : <TrendingDown className="w-3 h-3 mr-1" />}
              <span>较昨日 {trendUp ? '+' : ''}{trend}%</span>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

// HTTP 方法标签组件
function MethodBadge({ method }) {
  const colors = {
    GET: 'bg-green-100 text-green-700 border-green-200',
    POST: 'bg-blue-100 text-blue-700 border-blue-200',
    PUT: 'bg-orange-100 text-orange-700 border-orange-200',
    DELETE: 'bg-red-100 text-red-700 border-red-200',
    PATCH: 'bg-purple-100 text-purple-700 border-purple-200'
  }
  
  return (
    <span className={`px-2 py-0.5 rounded border text-xs font-semibold ${colors[method] || 'bg-slate-100 text-slate-700'}`}>
      {method}
    </span>
  )
}

// 状态标签组件
function StatusBadge({ status }) {
  if (status === 'success') {
    return (
      <div className="flex items-center text-green-600">
        <CheckCircle2 className="w-4 h-4 mr-1" />
        <span className="text-sm font-medium">成功</span>
      </div>
    )
  }
  return (
    <div className="flex items-center text-red-600">
      <XCircle className="w-4 h-4 mr-1" />
      <span className="text-sm font-medium">失败</span>
    </div>
  )
}

// 趋势图组件(简化版 Area Chart)
function TrendChart({ data }) {
  const maxRate = Math.max(...data.map(d => d.rate))
  const minRate = Math.min(...data.map(d => d.rate))
  const range = maxRate - minRate
  
  return (
    <div className="bg-white rounded-lg border border-slate-200 p-5">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-base font-semibold text-slate-900">近七日测试成功率趋势</h3>
        <div className="flex items-center text-sm text-slate-600">
          <Activity className="w-4 h-4 mr-1" />
          <span>平均成功率: {(data.reduce((sum, d) => sum + d.rate, 0) / data.length).toFixed(1)}%</span>
        </div>
      </div>
      
      <div className="relative h-48">
        {/* Y轴标签 */}
        <div className="absolute left-0 top-0 bottom-0 w-12 flex flex-col justify-between text-xs text-slate-500">
          <span>{maxRate.toFixed(0)}%</span>
          <span>{((maxRate + minRate) / 2).toFixed(0)}%</span>
          <span>{minRate.toFixed(0)}%</span>
        </div>
        
        {/* 图表区域 */}
        <div className="ml-12 h-full flex items-end justify-between gap-2">
          {data.map((item, index) => {
            const height = range > 0 ? ((item.rate - minRate) / range) * 100 : 50
            return (
              <div key={index} className="flex-1 flex flex-col items-center group">
                <div className="w-full relative" style={{ height: '160px' }}>
                  <div 
                    className="absolute bottom-0 w-full bg-gradient-to-t from-blue-500 to-blue-300 rounded-t transition-all group-hover:from-blue-600 group-hover:to-blue-400"
                    style={{ height: `${height}%` }}
                  >
                    <div className="absolute -top-6 left-1/2 transform -translate-x-1/2 opacity-0 group-hover:opacity-100 transition-opacity bg-slate-900 text-white text-xs px-2 py-1 rounded whitespace-nowrap">
                      {item.rate}%
                    </div>
                  </div>
                </div>
                <span className="text-xs text-slate-500 mt-2">{item.date}</span>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}

export default function DashboardPro() {
  const [data, setData] = useState(mockData)
  const [searchTerm, setSearchTerm] = useState('')
  const [sortBy, setSortBy] = useState('time') // time, duration, status
  const [sortOrder, setSortOrder] = useState('desc')

  useEffect(() => {
    // 尝试从后端获取真实数据
    dashboardAPI.getStats()
      .then(apiData => {
        // 合并真实数据和模拟数据
        setData(prev => ({
          ...prev,
          stats: {
            ...prev.stats,
            ...apiData
          }
        }))
      })
      .catch(err => {
        console.warn('使用模拟数据:', err.message)
      })
  }, [])

  const handleViewLog = (execution) => {
    console.log('查看日志:', execution)
    alert(`查看 ${execution.apiName} 的执行日志`)
  }

  const handleRerun = (execution) => {
    console.log('重新运行:', execution)
    alert(`重新运行 ${execution.apiName}`)
  }

  const handleSort = (field) => {
    if (sortBy === field) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')
    } else {
      setSortBy(field)
      setSortOrder('desc')
    }
  }

  const handleResetSearch = () => {
    setSearchTerm('')
  }

  // 过滤和排序数据
  const filteredAndSortedExecutions = data.recentExecutions
    .filter(exec => 
      exec.apiName.toLowerCase().includes(searchTerm.toLowerCase()) ||
      exec.path.toLowerCase().includes(searchTerm.toLowerCase()) ||
      exec.executor.toLowerCase().includes(searchTerm.toLowerCase())
    )
    .sort((a, b) => {
      let comparison = 0
      if (sortBy === 'time') {
        comparison = new Date(a.executeTime) - new Date(b.executeTime)
      } else if (sortBy === 'duration') {
        comparison = a.duration - b.duration
      } else if (sortBy === 'status') {
        comparison = a.status.localeCompare(b.status)
      }
      return sortOrder === 'asc' ? comparison : -comparison
    })

  return (
    <div className="p-6 bg-slate-50 min-h-screen">
      {/* 页面标题 */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-slate-900">测试概览</h1>
        <p className="text-sm text-slate-600 mt-1">实时监控接口测试执行情况</p>
      </div>

      {/* 统计卡片 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <StatCard
          title="今日测试总数"
          value={data.stats.totalTests}
          trend={data.stats.trends.totalTests}
          icon={Activity}
          color="blue"
        />
        <StatCard
          title="通过测试"
          value={data.stats.passed}
          trend={data.stats.trends.passed}
          icon={CheckCircle2}
          color="green"
        />
        <StatCard
          title="失败测试"
          value={data.stats.failed}
          trend={data.stats.trends.failed}
          icon={XCircle}
          color="red"
          highThreshold={0}
        />
        <StatCard
          title="测试覆盖率"
          value={data.stats.coverage}
          trend={data.stats.trends.coverage}
          icon={Target}
          color="purple"
          lowThreshold={30}
        />
      </div>

      {/* 趋势图 */}
      <div className="mb-6">
        <TrendChart data={data.trendData} />
      </div>

      {/* 测试执行列表 */}
      <div className="bg-white rounded-lg border border-slate-200 shadow-sm">
        <div className="px-6 py-4 border-b border-slate-200">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-lg font-semibold text-slate-900">最近测试执行</h2>
              <p className="text-sm text-slate-600 mt-0.5">实时更新的接口测试执行记录</p>
            </div>
            <button 
              onClick={() => window.location.reload()}
              className="flex items-center px-3 py-1.5 text-sm text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
            >
              <RotateCcw className="w-4 h-4 mr-1" />
              刷新
            </button>
          </div>
          
          {/* 本页过滤搜索框 */}
          <div className="flex items-center gap-2">
            <div className="flex-1 relative">
              <input
                type="text"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder="本页过滤：搜索接口名称、路径、执行人..."
                className="w-full px-4 py-2 pl-10 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
              <Activity className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 transform -translate-y-1/2" />
            </div>
            {searchTerm && (
              <button
                onClick={handleResetSearch}
                className="px-4 py-2 text-sm text-slate-600 hover:text-slate-900 hover:bg-slate-100 rounded-lg transition-colors border border-slate-300"
              >
                重置
              </button>
            )}
            <div className="text-sm text-slate-600 px-3 py-2 bg-slate-50 rounded-lg border border-slate-200">
              共 {filteredAndSortedExecutions.length} 条
            </div>
          </div>
        </div>

        {/* 表格 */}
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-slate-50 border-b border-slate-200">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-semibold text-slate-600 uppercase tracking-wider">
                  接口名称
                </th>
                <th className="px-6 py-3 text-left text-xs font-semibold text-slate-600 uppercase tracking-wider">
                  方法
                </th>
                <th className="px-6 py-3 text-left text-xs font-semibold text-slate-600 uppercase tracking-wider">
                  请求路径
                </th>
                <th className="px-6 py-3 text-left text-xs font-semibold text-slate-600 uppercase tracking-wider">
                  执行人
                </th>
                <th 
                  className="px-6 py-3 text-left text-xs font-semibold text-slate-600 uppercase tracking-wider cursor-pointer hover:text-blue-600 transition-colors"
                  onClick={() => handleSort('duration')}
                >
                  <div className="flex items-center gap-1">
                    耗时
                    {sortBy === 'duration' && (
                      <span className="text-blue-600">
                        {sortOrder === 'asc' ? '↑' : '↓'}
                      </span>
                    )}
                  </div>
                </th>
                <th 
                  className="px-6 py-3 text-left text-xs font-semibold text-slate-600 uppercase tracking-wider cursor-pointer hover:text-blue-600 transition-colors"
                  onClick={() => handleSort('time')}
                >
                  <div className="flex items-center gap-1">
                    执行时间
                    {sortBy === 'time' && (
                      <span className="text-blue-600">
                        {sortOrder === 'asc' ? '↑' : '↓'}
                      </span>
                    )}
                  </div>
                </th>
                <th 
                  className="px-6 py-3 text-left text-xs font-semibold text-slate-600 uppercase tracking-wider cursor-pointer hover:text-blue-600 transition-colors"
                  onClick={() => handleSort('status')}
                >
                  <div className="flex items-center gap-1">
                    状态
                    {sortBy === 'status' && (
                      <span className="text-blue-600">
                        {sortOrder === 'asc' ? '↑' : '↓'}
                      </span>
                    )}
                  </div>
                </th>
                <th className="px-6 py-3 text-right text-xs font-semibold text-slate-600 uppercase tracking-wider">
                  操作
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200">
              {filteredAndSortedExecutions.map((execution) => (
                <tr 
                  key={execution.id} 
                  className="hover:bg-blue-50/50 transition-colors cursor-pointer"
                >
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm font-medium text-slate-900">{execution.apiName}</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <MethodBadge method={execution.method} />
                  </td>
                  <td className="px-6 py-4">
                    <div className="text-sm text-slate-600 font-mono">{execution.path}</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-slate-900">{execution.executor}</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center text-sm text-slate-600">
                      <Clock className="w-3 h-3 mr-1" />
                      {execution.duration}ms
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-slate-600">{execution.executeTime}</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <StatusBadge status={execution.status} />
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right">
                    <div className="flex items-center justify-end gap-2">
                      <button
                        onClick={() => handleViewLog(execution)}
                        className="p-1.5 text-slate-600 hover:text-blue-600 hover:bg-blue-50 rounded transition-colors"
                        title="查看日志"
                      >
                        <FileText className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => handleRerun(execution)}
                        className="p-1.5 text-slate-600 hover:text-green-600 hover:bg-green-50 rounded transition-colors"
                        title="重新运行"
                      >
                        <Play className="w-4 h-4" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* 分页 */}
        <div className="px-6 py-4 border-t border-slate-200 flex items-center justify-between bg-slate-50">
          <div className="text-sm text-slate-600">
            显示 {filteredAndSortedExecutions.length > 0 ? '1' : '0'}-{Math.min(8, filteredAndSortedExecutions.length)} 条，共 {filteredAndSortedExecutions.length} 条记录
            {searchTerm && <span className="ml-2 text-blue-600">（已过滤）</span>}
          </div>
          <div className="flex gap-2">
            <button className="px-3 py-1.5 text-sm border border-slate-300 rounded-lg hover:bg-white transition-colors disabled:opacity-50 disabled:cursor-not-allowed" disabled>
              上一页
            </button>
            <div className="flex items-center gap-1">
              <button className="px-3 py-1.5 text-sm bg-blue-600 text-white rounded-lg">1</button>
              <button className="px-3 py-1.5 text-sm border border-slate-300 rounded-lg hover:bg-white transition-colors">2</button>
              <button className="px-3 py-1.5 text-sm border border-slate-300 rounded-lg hover:bg-white transition-colors">3</button>
            </div>
            <button className="px-3 py-1.5 text-sm border border-slate-300 rounded-lg hover:bg-white transition-colors">
              下一页
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
