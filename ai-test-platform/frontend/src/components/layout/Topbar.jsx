import { useState } from 'react'
import { Search, Bell, ChevronDown, Settings, User, LogOut, Sparkles } from 'lucide-react'
import { Button } from '@/components/ui/button'
import AIModelSelector from '@/components/AIModelSelector'

export function Topbar() {
  const [showUserMenu, setShowUserMenu] = useState(false)

  return (
    <header className="bg-white/80 backdrop-blur-xl border-b border-gray-200/60 px-6 py-4 shadow-sm sticky top-0 z-40">
      <div className="flex items-center justify-between">
        {/* Left Section - Project Info */}
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-3 px-4 py-2 bg-gray-50 rounded-lg border border-gray-200/60">
            <div className="w-2 h-2 bg-green-500 rounded-full"></div>
            <div>
              <span className="text-sm font-semibold text-gray-900">电商平台接口</span>
              <span className="text-xs text-gray-500 ml-2">生产环境</span>
            </div>
          </div>
        </div>

        {/* Center Section - Search */}
        <div className="flex-1 max-w-2xl mx-8">
          <div className="relative">
            <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
            <input
              type="text"
              placeholder="搜索测试用例、接口、项目..."
              className="w-full pl-12 pr-4 py-2.5 bg-gray-50 border border-gray-200/60 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500/40 transition-all text-sm placeholder-gray-400 text-gray-900"
            />
          </div>
        </div>

        {/* Right Section - Actions & User */}
        <div className="flex items-center space-x-3">
          {/* AI Model Selector */}
          <AIModelSelector />

          {/* AI Assistant Button */}
          <Button variant="ghost" size="sm" className="relative hover:bg-gray-50 p-2.5 rounded-lg">
            <Sparkles className="w-5 h-5 text-purple-600" />
          </Button>

          {/* Notifications */}
          <div className="relative">
            <Button variant="ghost" size="sm" className="relative hover:bg-gray-50 p-2.5 rounded-lg">
              <Bell className="w-5 h-5 text-gray-600" />
              <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center font-semibold">
                3
              </span>
            </Button>
          </div>

          {/* User Menu */}
          <div className="relative">
            <Button
              variant="ghost"
              className="flex items-center space-x-3 px-3 py-2 hover:bg-gray-50 rounded-lg"
              onClick={() => setShowUserMenu(!showUserMenu)}
            >
              <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-blue-600 rounded-lg flex items-center justify-center">
                <User className="w-4 h-4 text-white" />
              </div>
              <div className="text-left">
                <div className="text-sm font-semibold text-gray-900">张测试</div>
                <div className="text-xs text-gray-500">测试工程师</div>
              </div>
              <ChevronDown className="w-4 h-4 text-gray-400" />
            </Button>

            {showUserMenu && (
              <div className="absolute top-full right-0 mt-2 w-64 bg-white border border-gray-200/60 rounded-lg shadow-lg z-50 overflow-hidden">
                <div className="p-4 border-b border-gray-100">
                  <div className="flex items-center space-x-3">
                    <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-blue-600 rounded-lg flex items-center justify-center">
                      <User className="w-5 h-5 text-white" />
                    </div>
                    <div>
                      <div className="font-semibold text-gray-900">张测试</div>
                      <div className="text-sm text-gray-500">zhang.test@company.com</div>
                    </div>
                  </div>
                </div>
                <div className="p-2">
                  <Button variant="ghost" className="w-full justify-start text-sm hover:bg-gray-50 rounded-md">
                    <User className="w-4 h-4 mr-3" />
                    个人资料
                  </Button>
                  <Button variant="ghost" className="w-full justify-start text-sm hover:bg-gray-50 rounded-md">
                    <Settings className="w-4 h-4 mr-3" />
                    偏好设置
                  </Button>
                </div>
                <div className="border-t border-gray-100 p-2">
                  <Button variant="ghost" className="w-full justify-start text-sm text-red-600 hover:bg-red-50 rounded-md">
                    <LogOut className="w-4 h-4 mr-3" />
                    退出登录
                  </Button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </header>
  )
}
