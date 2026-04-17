import { NavLink } from 'react-router-dom'
import { cn } from '@/lib/utils'
import {
  LayoutDashboard,
  FolderOpen,
  Globe,
  FileText,
  Bot,
  Play,
  BarChart3,
  Brain,
  Settings,
  Zap,
  ChevronRight,
  Sparkles
} from 'lucide-react'

const navigation = [
  { 
    name: '仪表板', 
    href: '/', 
    icon: LayoutDashboard, 
    description: '总览和统计',
    gradient: 'from-blue-500 to-cyan-500'
  },
  { 
    name: '项目管理', 
    href: '/projects', 
    icon: FolderOpen, 
    description: '管理测试项目',
    gradient: 'from-purple-500 to-pink-500'
  },
  { 
    name: '接口管理', 
    href: '/api-explorer', 
    icon: Globe, 
    description: '探索和测试API',
    gradient: 'from-green-500 to-emerald-500'
  },
  { 
    name: '测试用例', 
    href: '/test-cases', 
    icon: FileText, 
    description: '管理测试用例',
    gradient: 'from-orange-500 to-red-500'
  },
  { 
    name: '自动化脚本', 
    href: '/automation', 
    icon: Bot, 
    description: '生成自动化脚本',
    gradient: 'from-indigo-500 to-purple-500'
  },
  { 
    name: '测试执行', 
    href: '/test-runs', 
    icon: Play, 
    description: '执行和监控测试',
    gradient: 'from-teal-500 to-cyan-500'
  },
  { 
    name: '测试报告', 
    href: '/reports', 
    icon: BarChart3, 
    description: '查看测试报告',
    gradient: 'from-rose-500 to-pink-500'
  },
  { 
    name: 'AI分析中心', 
    href: '/ai-insights', 
    icon: Brain, 
    description: 'AI智能分析',
    gradient: 'from-violet-500 to-purple-500'
  },
]

export function Sidebar() {
  return (
    <div className="flex h-full w-72 flex-col bg-white/80 backdrop-blur-xl border-r border-gray-200/60 shadow-sm">
      {/* Logo */}
      <div className="flex h-20 items-center px-6 border-b border-gray-200/60">
        <div className="flex items-center space-x-3">
          <div className="relative">
            <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-blue-600 rounded-xl flex items-center justify-center shadow-md shadow-blue-500/20">
              <Zap className="w-5 h-5 text-white" />
            </div>
          </div>
          <div>
            <h1 className="text-lg font-bold text-gray-900">
              AI测试平台
            </h1>
            <p className="text-xs text-gray-500">智能测试工程师</p>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-4 py-6 space-y-1 overflow-y-auto">
        {navigation.map((item) => (
          <NavLink
            key={item.name}
            to={item.href}
            className={({ isActive }) =>
              cn(
                'group relative flex items-center px-3 py-2.5 text-sm font-medium rounded-lg transition-all duration-200',
                isActive
                  ? 'bg-blue-50 text-blue-700'
                  : 'text-gray-700 hover:bg-gray-50 hover:text-gray-900'
              )
            }
          >
            {({ isActive }) => (
              <>
                <div className={cn(
                  "p-1.5 rounded-md transition-colors mr-3",
                  isActive 
                    ? "text-blue-600" 
                    : "text-gray-500 group-hover:text-gray-700"
                )}>
                  <item.icon className="w-5 h-5" />
                </div>
                <span>{item.name}</span>
                
                {/* Active indicator */}
                {isActive && (
                  <div className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-8 bg-blue-600 rounded-r-full"></div>
                )}
              </>
            )}
          </NavLink>
        ))}
      </nav>

      {/* Bottom Section */}
      <div className="px-4 py-4 border-t border-gray-200/60 space-y-3">
        <NavLink
          to="/settings"
          className="group flex items-center px-3 py-2.5 text-sm font-medium text-gray-700 rounded-lg hover:bg-gray-50 transition-all duration-200"
        >
          <div className="p-1.5 rounded-md mr-3 text-gray-500 group-hover:text-gray-700">
            <Settings className="w-5 h-5" />
          </div>
          <span>设置</span>
        </NavLink>
        
        {/* Status Indicator */}
        <div className="p-3 bg-green-50 rounded-lg border border-green-100">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center space-x-2">
              <div className="w-2 h-2 bg-green-500 rounded-full"></div>
              <span className="text-sm font-medium text-green-700">系统正常</span>
            </div>
          </div>
          
          <div className="space-y-1.5 text-xs">
            <div className="flex justify-between text-gray-600">
              <span>活跃测试</span>
              <span className="font-semibold text-gray-900">156</span>
            </div>
            <div className="flex justify-between text-gray-600">
              <span>成功率</span>
              <span className="font-semibold text-green-600">94.2%</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-1 mt-2">
              <div className="bg-green-500 h-1 rounded-full" style={{width: '94%'}}></div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}