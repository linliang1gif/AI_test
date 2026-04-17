import { useState, useEffect } from 'react'
import { 
  TrendingUp, 
  Activity, 
  CheckCircle, 
  XCircle, 
  Target, 
  Zap, 
  Brain, 
  Shield, 
  Clock, 
  Users, 
  BarChart3, 
  ArrowUpRight, 
  ArrowDownRight,
  Sparkles,
  Play,
  Pause,
  RefreshCw,
  AlertTriangle,
  Eye,
  ChevronRight
} from 'lucide-react'

export default function Dashboard() {
  const [realTimeData, setRealTimeData] = useState({
    totalTests: 156,
    passedTests: 142,
    failedTests: 14,
    coverage: 85
  })

  // 模拟实时数据更新
  useEffect(() => {
    const interval = setInterval(() => {
      setRealTimeData(prev => ({
        totalTests: prev.totalTests + Math.floor(Math.random() * 3),
        passedTests: prev.passedTests + Math.floor(Math.random() * 2),
        failedTests: prev.failedTests + Math.floor(Math.random() * 1),
        coverage: Math.min(100, prev.coverage + Math.random() * 0.5)
      }))
    }, 5000)
    return () => clearInterval(interval)
  }, [])

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 p-8 relative overflow-hidden">
      {/* Animated background elements */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-20 left-10 w-2 h-2 bg-blue-400 rounded-full animate-pulse opacity-60"></div>
        <div className="absolute top-40 right-20 w-1 h-1 bg-purple-400 rounded-full animate-bounce opacity-40"></div>
        <div className="absolute bottom-20 left-1/3 w-3 h-3 bg-cyan-400 rounded-full animate-ping opacity-30"></div>
        <div className="absolute top-1/2 right-10 w-1.5 h-1.5 bg-pink-400 rounded-full animate-pulse opacity-50"></div>
      </div>

      {/* Header Section */}
      <div className="relative z-10 mb-12">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-4xl font-bold bg-gradient-to-r from-white via-blue-100 to-purple-200 bg-clip-text text-transparent mb-3">
              AI测试控制中心
            </h1>
            <p className="text-slate-400 text-lg flex items-center">
              <Activity className="w-5 h-5 mr-2 text-emerald-400" />
              实时监控 • 智能分析 • 自动化测试
            </p>
          </div>
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2 px-4 py-2 bg-emerald-500/20 rounded-xl border border-emerald-500/30 backdrop-blur-sm">
              <div className="w-3 h-3 bg-emerald-400 rounded-full animate-pulse"></div>
              <span className="text-emerald-300 font-bold">系统运行正常</span>
            </div>
            <button className="p-3 bg-slate-800/50 hover:bg-slate-700/50 rounded-xl border border-slate-600/50 transition-all duration-300 group">
              <RefreshCw className="w-5 h-5 text-slate-400 group-hover:text-blue-400 group-hover:rotate-180 transition-all duration-500" />
            </button>
          </div>
        </div>
      </div>
      
      {/* 实时统计卡片 */}
      <div className="relative z-10 grid grid-cols-1 md:grid-cols-4 gap-8 mb-12">
        {/* 今日测试总数 */}
        <div className="group relative">
          <div className="absolute inset-0 bg-gradient-to-r from-blue-500/20 to-cyan-500/20 rounded-3xl blur-xl opacity-0 group-hover:opacity-100 transition-all duration-500"></div>
          <div className="relative bg-slate-800/50 backdrop-blur-xl p-8 rounded-3xl border border-slate-700/50 hover:border-blue-500/50 transition-all duration-300 shadow-2xl">
            <div className="flex items-center justify-between mb-6">
              <div className="p-4 bg-gradient-to-br from-blue-500 to-cyan-500 rounded-2xl shadow-lg shadow-blue-500/25">
                <BarChart3 className="w-8 h-8 text-white" />
              </div>
              <div className="flex items-center space-x-2 text-emerald-400">
                <ArrowUpRight className="w-4 h-4" />
                <span className="text-sm font-bold">+12%</span>
              </div>
            </div>
            <div>
              <p className="text-slate-400 text-sm font-medium mb-2">今日测试总数</p>
              <p className="text-4xl font-bold text-white mb-2">{realTimeData.totalTests}</p>
              <p className="text-xs text-slate-500 flex items-center">
                <TrendingUp className="w-3 h-3 mr-1" />
                比昨天增长 12%
              </p>
            </div>
            <div className="absolute top-4 right-4 w-2 h-2 bg-blue-400 rounded-full animate-pulse"></div>
          </div>
        </div>
        
        {/* 通过测试 */}
        <div className="group relative">
          <div className="absolute inset-0 bg-gradient-to-r from-emerald-500/20 to-green-500/20 rounded-3xl blur-xl opacity-0 group-hover:opacity-100 transition-all duration-500"></div>
          <div className="relative bg-slate-800/50 backdrop-blur-xl p-8 rounded-3xl border border-slate-700/50 hover:border-emerald-500/50 transition-all duration-300 shadow-2xl">
            <div className="flex items-center justify-between mb-6">
              <div className="p-4 bg-gradient-to-br from-emerald-500 to-green-500 rounded-2xl shadow-lg shadow-emerald-500/25">
                <CheckCircle className="w-8 h-8 text-white" />
              </div>
              <div className="flex items-center space-x-2 text-emerald-400">
                <span className="text-sm font-bold">91.0%</span>
              </div>
            </div>
            <div>
              <p className="text-slate-400 text-sm font-medium mb-2">通过测试</p>
              <p className="text-4xl font-bold text-white mb-2">{realTimeData.passedTests}</p>
              <p className="text-xs text-slate-500 flex items-center">
                <CheckCircle className="w-3 h-3 mr-1" />
                成功率持续提升
              </p>
            </div>
            <div className="absolute top-4 right-4 w-2 h-2 bg-emerald-400 rounded-full animate-pulse"></div>
          </div>
        </div>
        
        {/* 失败测试 */}
        <div className="group relative">
          <div className="absolute inset-0 bg-gradient-to-r from-red-500/20 to-pink-500/20 rounded-3xl blur-xl opacity-0 group-hover:opacity-100 transition-all duration-500"></div>
          <div className="relative bg-slate-800/50 backdrop-blur-xl p-8 rounded-3xl border border-slate-700/50 hover:border-red-500/50 transition-all duration-300 shadow-2xl">
            <div className="flex items-center justify-between mb-6">
              <div className="p-4 bg-gradient-to-br from-red-500 to-pink-500 rounded-2xl shadow-lg shadow-red-500/25">
                <XCircle className="w-8 h-8 text-white" />
              </div>
              <div className="flex items-center space-x-2 text-red-400">
                <AlertTriangle className="w-4 h-4" />
                <span className="text-sm font-bold">需关注</span>
              </div>
            </div>
            <div>
              <p className="text-slate-400 text-sm font-medium mb-2">失败测试</p>
              <p className="text-4xl font-bold text-white mb-2">{realTimeData.failedTests}</p>
              <p className="text-xs text-slate-500 flex items-center">
                <ArrowDownRight className="w-3 h-3 mr-1" />
                AI正在自动修复
              </p>
            </div>
            <div className="absolute top-4 right-4 w-2 h-2 bg-red-400 rounded-full animate-pulse"></div>
          </div>
        </div>
        
        {/* 测试覆盖率 */}
        <div className="group relative">
          <div className="absolute inset-0 bg-gradient-to-r from-purple-500/20 to-pink-500/20 rounded-3xl blur-xl opacity-0 group-hover:opacity-100 transition-all duration-500"></div>
          <div className="relative bg-slate-800/50 backdrop-blur-xl p-8 rounded-3xl border border-slate-700/50 hover:border-purple-500/50 transition-all duration-300 shadow-2xl">
            <div className="flex items-center justify-between mb-6">
              <div className="p-4 bg-gradient-to-br from-purple-500 to-pink-500 rounded-2xl shadow-lg shadow-purple-500/25">
                <Target className="w-8 h-8 text-white" />
              </div>
              <div className="flex items-center space-x-2 text-purple-400">
                <ArrowUpRight className="w-4 h-4" />
                <span className="text-sm font-bold">+5%</span>
              </div>
            </div>
            <div>
              <p className="text-slate-400 text-sm font-medium mb-2">测试覆盖率</p>
              <p className="text-4xl font-bold text-white mb-2">{realTimeData.coverage.toFixed(1)}%</p>
              <div className="w-full bg-slate-700/50 rounded-full h-2 mb-2">
                <div 
                  className="bg-gradient-to-r from-purple-500 to-pink-500 h-2 rounded-full transition-all duration-1000 shadow-sm shadow-purple-500/50"
                  style={{ width: `${realTimeData.coverage}%` }}
                ></div>
              </div>
              <p className="text-xs text-slate-500">本周提升 5%</p>
            </div>
            <div className="absolute top-4 right-4 w-2 h-2 bg-purple-400 rounded-full animate-pulse"></div>
          </div>
        </div>
      </div>
      
      {/* 主要内容区域 */}
      <div className="relative z-10 grid grid-cols-1 lg:grid-cols-3 gap-8 mb-12">
        {/* AI智能分析面板 */}
        <div className="lg:col-span-2 group relative">
          <div className="absolute inset-0 bg-gradient-to-r from-blue-500/10 via-purple-500/10 to-pink-500/10 rounded-3xl blur-2xl opacity-0 group-hover:opacity-100 transition-all duration-700"></div>
          <div className="relative bg-slate-800/50 backdrop-blur-xl p-8 rounded-3xl border border-slate-700/50 hover:border-blue-500/30 transition-all duration-500 shadow-2xl">
            <div className="flex items-center justify-between mb-8">
              <h3 className="text-2xl font-bold text-white flex items-center">
                <div className="p-3 bg-gradient-to-br from-blue-500 to-purple-600 rounded-2xl mr-4 shadow-lg shadow-blue-500/25">
                  <Brain className="w-6 h-6 text-white" />
                </div>
                AI智能分析中心
              </h3>
              <div className="flex items-center space-x-3">
                <button className="p-2 bg-slate-700/50 hover:bg-slate-600/50 rounded-xl transition-all duration-300">
                  <Play className="w-4 h-4 text-emerald-400" />
                </button>
                <button className="p-2 bg-slate-700/50 hover:bg-slate-600/50 rounded-xl transition-all duration-300">
                  <Pause className="w-4 h-4 text-slate-400" />
                </button>
              </div>
            </div>
            
            {/* 实时图表区域 */}
            <div className="h-80 relative overflow-hidden rounded-2xl bg-gradient-to-br from-slate-900/50 to-slate-800/50 border border-slate-700/30 mb-6">
              <div className="absolute inset-0 flex items-center justify-center">
                <div className="text-center">
                  <div className="relative mb-6">
                    <div className="w-24 h-24 bg-gradient-to-br from-blue-500 via-purple-600 to-pink-600 rounded-3xl flex items-center justify-center mx-auto shadow-2xl shadow-blue-500/25 animate-pulse">
                      <BarChart3 className="w-12 h-12 text-white" />
                    </div>
                    <div className="absolute -top-2 -right-2 w-6 h-6 bg-gradient-to-r from-emerald-400 to-green-500 rounded-full flex items-center justify-center">
                      <Sparkles className="w-3 h-3 text-white" />
                    </div>
                  </div>
                  <p className="text-xl font-bold text-white mb-2">实时测试趋势分析</p>
                  <p className="text-slate-400 mb-4">AI正在分析测试数据模式和趋势</p>
                  <div className="flex items-center justify-center space-x-4 text-sm">
                    <div className="flex items-center space-x-2 px-4 py-2 bg-blue-500/20 rounded-xl border border-blue-500/30">
                      <div className="w-2 h-2 bg-blue-400 rounded-full animate-pulse"></div>
                      <span className="text-blue-300 font-medium">实时数据流</span>
                    </div>
                    <div className="flex items-center space-x-2 px-4 py-2 bg-purple-500/20 rounded-xl border border-purple-500/30">
                      <Brain className="w-3 h-3 text-purple-400" />
                      <span className="text-purple-300 font-medium">AI分析中</span>
                    </div>
                  </div>
                </div>
              </div>
              
              {/* 浮动数据点 */}
              <div className="absolute top-4 left-4 w-3 h-3 bg-blue-400 rounded-full animate-bounce opacity-60"></div>
              <div className="absolute top-8 right-8 w-2 h-2 bg-purple-400 rounded-full animate-pulse opacity-40"></div>
              <div className="absolute bottom-6 left-8 w-4 h-4 bg-cyan-400 rounded-full animate-ping opacity-30"></div>
            </div>
            
            {/* AI洞察 */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="p-4 bg-gradient-to-br from-emerald-500/10 to-green-500/10 rounded-2xl border border-emerald-500/20">
                <div className="flex items-center space-x-3 mb-2">
                  <TrendingUp className="w-5 h-5 text-emerald-400" />
                  <span className="text-sm font-bold text-emerald-300">性能提升</span>
                </div>
                <p className="text-2xl font-bold text-white">+23%</p>
                <p className="text-xs text-slate-400">相比上周</p>
              </div>
              <div className="p-4 bg-gradient-to-br from-blue-500/10 to-cyan-500/10 rounded-2xl border border-blue-500/20">
                <div className="flex items-center space-x-3 mb-2">
                  <Shield className="w-5 h-5 text-blue-400" />
                  <span className="text-sm font-bold text-blue-300">稳定性</span>
                </div>
                <p className="text-2xl font-bold text-white">99.2%</p>
                <p className="text-xs text-slate-400">系统可用性</p>
              </div>
              <div className="p-4 bg-gradient-to-br from-purple-500/10 to-pink-500/10 rounded-2xl border border-purple-500/20">
                <div className="flex items-center space-x-3 mb-2">
                  <Zap className="w-5 h-5 text-purple-400" />
                  <span className="text-sm font-bold text-purple-300">自动修复</span>
                </div>
                <p className="text-2xl font-bold text-white">87%</p>
                <p className="text-xs text-slate-400">成功率</p>
              </div>
            </div>
          </div>
        </div>
        
        {/* 最近测试执行 */}
        <div className="group relative">
          <div className="absolute inset-0 bg-gradient-to-r from-emerald-500/10 to-green-500/10 rounded-3xl blur-2xl opacity-0 group-hover:opacity-100 transition-all duration-700"></div>
          <div className="relative bg-slate-800/50 backdrop-blur-xl p-8 rounded-3xl border border-slate-700/50 hover:border-emerald-500/30 transition-all duration-500 shadow-2xl h-full">
            <h3 className="text-xl font-bold text-white mb-6 flex items-center">
              <div className="p-3 bg-gradient-to-br from-emerald-500 to-green-600 rounded-2xl mr-4 shadow-lg shadow-emerald-500/25">
                <Activity className="w-5 h-5 text-white" />
              </div>
              实时测试流
            </h3>
            
            <div className="space-y-4">
              {[
                { name: '用户登录接口', status: 'success', time: '2分钟前', duration: '1.2s' },
                { name: '支付网关验证', status: 'failed', time: '5分钟前', duration: '3.8s' },
                { name: '商品搜索API', status: 'success', time: '8分钟前', duration: '0.9s' },
                { name: '订单创建流程', status: 'success', time: '12分钟前', duration: '2.1s' },
                { name: '库存更新接口', status: 'running', time: '进行中', duration: '...' }
              ].map((test, index) => (
                <div key={index} className="group/item flex items-center justify-between p-4 bg-slate-700/30 hover:bg-slate-700/50 rounded-2xl transition-all duration-300 border border-slate-600/30 hover:border-slate-500/50">
                  <div className="flex items-center space-x-4">
                    <div className={`p-2 rounded-xl ${
                      test.status === 'success' ? 'bg-emerald-500/20 border border-emerald-500/30' :
                      test.status === 'failed' ? 'bg-red-500/20 border border-red-500/30' :
                      'bg-blue-500/20 border border-blue-500/30'
                    }`}>
                      {test.status === 'success' && <CheckCircle className="w-4 h-4 text-emerald-400" />}
                      {test.status === 'failed' && <XCircle className="w-4 h-4 text-red-400" />}
                      {test.status === 'running' && <RefreshCw className="w-4 h-4 text-blue-400 animate-spin" />}
                    </div>
                    <div>
                      <p className="font-bold text-white group-hover/item:text-blue-300 transition-colors">{test.name}</p>
                      <p className="text-xs text-slate-400 flex items-center">
                        <Clock className="w-3 h-3 mr-1" />
                        {test.time} • {test.duration}
                      </p>
                    </div>
                  </div>
                  <button className="opacity-0 group-hover/item:opacity-100 p-2 hover:bg-slate-600/50 rounded-xl transition-all duration-300">
                    <Eye className="w-4 h-4 text-slate-400 hover:text-blue-400" />
                  </button>
                </div>
              ))}
            </div>
            
            <button className="w-full mt-6 p-4 bg-gradient-to-r from-slate-700/50 to-slate-600/50 hover:from-slate-600/50 hover:to-slate-500/50 rounded-2xl border border-slate-600/50 hover:border-slate-500/50 transition-all duration-300 group/btn">
              <span className="text-slate-300 group-hover/btn:text-white font-medium flex items-center justify-center">
                查看全部测试
                <ChevronRight className="w-4 h-4 ml-2 group-hover/btn:translate-x-1 transition-transform" />
              </span>
            </button>
          </div>
        </div>
      </div>
      
      {/* 系统状态和AI代理 */}
      <div className="relative z-10 grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* 系统状态监控 */}
        <div className="group relative">
          <div className="absolute inset-0 bg-gradient-to-r from-emerald-500/10 to-green-500/10 rounded-3xl blur-2xl opacity-0 group-hover:opacity-100 transition-all duration-700"></div>
          <div className="relative bg-slate-800/50 backdrop-blur-xl p-8 rounded-3xl border border-slate-700/50 hover:border-emerald-500/30 transition-all duration-500 shadow-2xl">
            <h3 className="text-xl font-bold text-white mb-8 flex items-center">
              <div className="p-3 bg-gradient-to-br from-emerald-500 to-green-600 rounded-2xl mr-4 shadow-lg shadow-emerald-500/25">
                <Shield className="w-5 h-5 text-white" />
              </div>
              系统健康状态
            </h3>
            
            <div className="space-y-6">
              <div className="flex items-center justify-between p-6 bg-gradient-to-r from-emerald-500/10 to-green-500/10 rounded-2xl border border-emerald-500/20 group/item hover:border-emerald-500/40 transition-all duration-300">
                <div className="flex items-center space-x-4">
                  <div className="relative">
                    <div className="w-4 h-4 bg-emerald-400 rounded-full animate-pulse"></div>
                    <div className="absolute inset-0 w-4 h-4 bg-emerald-400 rounded-full animate-ping opacity-75"></div>
                  </div>
                  <div>
                    <p className="font-bold text-white group-hover/item:text-emerald-300 transition-colors">AI代理系统</p>
                    <p className="text-sm text-slate-400 group-hover/item:text-slate-300 transition-colors">所有智能代理正常运行</p>
                  </div>
                </div>
                <div className="flex items-center space-x-3">
                  <span className="text-emerald-400 font-bold">99.9%</span>
                  <div className="w-16 bg-slate-700/50 rounded-full h-2">
                    <div className="bg-gradient-to-r from-emerald-400 to-green-500 h-2 rounded-full w-full shadow-sm shadow-emerald-500/50"></div>
                  </div>
                </div>
              </div>
              
              <div className="flex items-center justify-between p-6 bg-gradient-to-r from-blue-500/10 to-cyan-500/10 rounded-2xl border border-blue-500/20 group/item hover:border-blue-500/40 transition-all duration-300">
                <div className="flex items-center space-x-4">
                  <div className="relative">
                    <div className="w-4 h-4 bg-blue-400 rounded-full animate-pulse"></div>
                    <div className="absolute inset-0 w-4 h-4 bg-blue-400 rounded-full animate-ping opacity-75"></div>
                  </div>
                  <div>
                    <p className="font-bold text-white group-hover/item:text-blue-300 transition-colors">测试流水线</p>
                    <p className="text-sm text-slate-400 group-hover/item:text-slate-300 transition-colors">自动化流水线运行顺畅</p>
                  </div>
                </div>
                <div className="flex items-center space-x-3">
                  <span className="text-blue-400 font-bold">98.7%</span>
                  <div className="w-16 bg-slate-700/50 rounded-full h-2">
                    <div className="bg-gradient-to-r from-blue-400 to-cyan-500 h-2 rounded-full w-[98%] shadow-sm shadow-blue-500/50"></div>
                  </div>
                </div>
              </div>
              
              <div className="flex items-center justify-between p-6 bg-gradient-to-r from-yellow-500/10 to-orange-500/10 rounded-2xl border border-yellow-500/20 group/item hover:border-yellow-500/40 transition-all duration-300">
                <div className="flex items-center space-x-4">
                  <div className="relative">
                    <div className="w-4 h-4 bg-yellow-400 rounded-full animate-pulse"></div>
                    <div className="absolute inset-0 w-4 h-4 bg-yellow-400 rounded-full animate-ping opacity-75"></div>
                  </div>
                  <div>
                    <p className="font-bold text-white group-hover/item:text-yellow-300 transition-colors">自愈引擎</p>
                    <p className="text-sm text-slate-400 group-hover/item:text-slate-300 transition-colors">2个修复任务正在进行</p>
                  </div>
                </div>
                <div className="flex items-center space-x-3">
                  <span className="text-yellow-400 font-bold">87.3%</span>
                  <div className="w-16 bg-slate-700/50 rounded-full h-2">
                    <div className="bg-gradient-to-r from-yellow-400 to-orange-500 h-2 rounded-full w-[87%] shadow-sm shadow-yellow-500/50"></div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
        
        {/* AI助手和快速操作 */}
        <div className="group relative">
          <div className="absolute inset-0 bg-gradient-to-r from-purple-500/10 via-pink-500/10 to-blue-500/10 rounded-3xl blur-2xl opacity-0 group-hover:opacity-100 transition-all duration-700"></div>
          <div className="relative bg-slate-800/50 backdrop-blur-xl p-8 rounded-3xl border border-slate-700/50 hover:border-purple-500/30 transition-all duration-500 shadow-2xl">
            <h3 className="text-xl font-bold text-white mb-8 flex items-center">
              <div className="p-3 bg-gradient-to-br from-purple-500 to-pink-600 rounded-2xl mr-4 shadow-lg shadow-purple-500/25">
                <Sparkles className="w-5 h-5 text-white" />
              </div>
              AI智能助手
            </h3>
            
            {/* AI助手对话框 */}
            <div className="bg-gradient-to-br from-slate-900/50 to-slate-800/50 rounded-2xl p-6 border border-slate-700/30 mb-6">
              <div className="flex items-start space-x-4 mb-4">
                <div className="w-10 h-10 bg-gradient-to-br from-purple-500 to-pink-600 rounded-2xl flex items-center justify-center shadow-lg">
                  <Brain className="w-5 h-5 text-white" />
                </div>
                <div className="flex-1">
                  <p className="text-white font-medium mb-2">AI助手建议</p>
                  <p className="text-slate-300 text-sm leading-relaxed">
                    检测到支付网关测试失败率上升，建议检查网络连接和API响应时间。我已经为您准备了详细的诊断报告。
                  </p>
                </div>
              </div>
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2 text-xs text-slate-400">
                  <Clock className="w-3 h-3" />
                  <span>2分钟前</span>
                </div>
                <button className="px-4 py-2 bg-gradient-to-r from-purple-500/20 to-pink-500/20 hover:from-purple-500/30 hover:to-pink-500/30 rounded-xl border border-purple-500/30 text-purple-300 text-sm font-medium transition-all duration-300">
                  查看报告
                </button>
              </div>
            </div>
            
            {/* 快速操作 */}
            <div className="grid grid-cols-2 gap-4">
              <button className="p-4 bg-gradient-to-br from-blue-500/10 to-cyan-500/10 hover:from-blue-500/20 hover:to-cyan-500/20 rounded-2xl border border-blue-500/20 hover:border-blue-500/40 transition-all duration-300 group/btn">
                <div className="flex items-center space-x-3 mb-2">
                  <Play className="w-5 h-5 text-blue-400 group-hover/btn:scale-110 transition-transform" />
                  <span className="text-white font-medium">运行测试</span>
                </div>
                <p className="text-xs text-slate-400 text-left">启动新的测试任务</p>
              </button>
              
              <button className="p-4 bg-gradient-to-br from-emerald-500/10 to-green-500/10 hover:from-emerald-500/20 hover:to-green-500/20 rounded-2xl border border-emerald-500/20 hover:border-emerald-500/40 transition-all duration-300 group/btn">
                <div className="flex items-center space-x-3 mb-2">
                  <Brain className="w-5 h-5 text-emerald-400 group-hover/btn:scale-110 transition-transform" />
                  <span className="text-white font-medium">AI分析</span>
                </div>
                <p className="text-xs text-slate-400 text-left">智能问题诊断</p>
              </button>
              
              <button className="p-4 bg-gradient-to-br from-purple-500/10 to-pink-500/10 hover:from-purple-500/20 hover:to-pink-500/20 rounded-2xl border border-purple-500/20 hover:border-purple-500/40 transition-all duration-300 group/btn">
                <div className="flex items-center space-x-3 mb-2">
                  <Zap className="w-5 h-5 text-purple-400 group-hover/btn:scale-110 transition-transform" />
                  <span className="text-white font-medium">自动修复</span>
                </div>
                <p className="text-xs text-slate-400 text-left">启动自愈引擎</p>
              </button>
              
              <button className="p-4 bg-gradient-to-br from-orange-500/10 to-red-500/10 hover:from-orange-500/20 hover:to-red-500/20 rounded-2xl border border-orange-500/20 hover:border-orange-500/40 transition-all duration-300 group/btn">
                <div className="flex items-center space-x-3 mb-2">
                  <BarChart3 className="w-5 h-5 text-orange-400 group-hover/btn:scale-110 transition-transform" />
                  <span className="text-white font-medium">生成报告</span>
                </div>
                <p className="text-xs text-slate-400 text-left">导出测试报告</p>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}