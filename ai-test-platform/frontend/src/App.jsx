import { BrowserRouter as Router, Routes, Route, NavLink, Navigate } from 'react-router-dom'
import { useState, useEffect } from 'react'
import { ToastProvider } from './components/ui/Toast'

// 导入页面组件（仅导入实际使用的）
import TestDataFactory from './pages/TestDataFactory'
import DatasetManagement from './pages/DatasetManagement'
// V2 页面
import ProjectsV2 from './pages/ProjectsV2'
import ProjectDetailV2 from './pages/ProjectDetailV2'
import TestCases from './pages/TestCases'
import TestRunsV2 from './pages/TestRunsV2'
import TestRunDetailV2 from './pages/TestRunDetailV2'
import QuickExecutionTest from './pages/QuickExecutionTest'
import ExecutorV2 from './pages/ExecutorV2'
import SwaggerWorkbench from './pages/SwaggerWorkbench'
import ApiSpecList from './pages/ApiSpecList'
import ApiSpecDetail from './pages/ApiSpecDetail'
import AIConfigPage from './pages/AIConfigPage'
import BatchRunCenter from './pages/BatchRunCenter'

const GLOBAL_ENV_STORAGE_KEY = 'ai_test_global_environment'

// AI对话组件 - 改为技术支持
function TechSupportWidget() {
  const [isOpen, setIsOpen] = useState(false)
  const [messages, setMessages] = useState([
    { id: 1, content: '你好！有什么可以帮助您的吗？', isUser: false }
  ])
  const [inputMessage, setInputMessage] = useState('')
  const [isLoading, setIsLoading] = useState(false)

  // 发送消息
  const sendMessage = async () => {
    if (!inputMessage.trim()) return

    // 添加用户消息
    const userMessage = { id: Date.now(), content: inputMessage, isUser: true }
    setMessages(prev => [...prev, userMessage])
    setInputMessage('')
    setIsLoading(true)

    try {
      const response = await fetch('/api/ai/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt: inputMessage })
      })

      const result = await response.json()

      if (result.success) {
        const aiMessage = { id: Date.now() + 1, content: result.response, isUser: false }
        setMessages(prev => [...prev, aiMessage])
      } else {
        const errorMessage = { id: Date.now() + 1, content: `错误: ${result.error}`, isUser: false }
        setMessages(prev => [...prev, errorMessage])
      }
    } catch (error) {
      const errorMessage = { id: Date.now() + 1, content: '网络错误，请检查服务器连接', isUser: false }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }

  if (!isOpen) {
    return (
      <div className="fixed bottom-6 right-6 z-50">
        <button
          onClick={() => setIsOpen(true)}
          className="w-12 h-12 bg-slate-700 hover:bg-slate-800 text-white rounded-md shadow-lg flex items-center justify-center transition-all duration-300 hover:scale-105"
          title="技术支持"
        >
          <span className="text-lg">?</span>
        </button>
      </div>
    )
  }

  return (
    <div className="fixed bottom-6 right-6 z-50 w-96 h-[500px] bg-white rounded-md shadow-2xl border border-gray-200 flex flex-col">
      {/* 头部 */}
      <div className="flex items-center justify-between p-4 border-b border-gray-200 bg-slate-700 text-white rounded-t-md">
        <div>
          <h3 className="font-semibold">技术支持</h3>
          <p className="text-xs opacity-90">在线帮助</p>
        </div>
        <button
          onClick={() => setIsOpen(false)}
          className="text-white hover:bg-white hover:bg-opacity-20 rounded-full w-8 h-8 flex items-center justify-center"
        >
          ✕
        </button>
      </div>

      {/* 消息列表 */}
      <div className="flex-1 p-4 overflow-y-auto space-y-3">
        {messages.map(msg => (
          <div key={msg.id} className={`flex ${msg.isUser ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-[80%] p-3 rounded-md text-sm ${
              msg.isUser 
                ? 'bg-blue-600 text-white' 
                : 'bg-gray-100 text-gray-800'
            }`}>
              {msg.content}
            </div>
          </div>
        ))}
        
        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-gray-100 text-gray-800 p-3 rounded-md text-sm">
              正在处理中...
            </div>
          </div>
        )}
      </div>

      {/* 输入区域 */}
      <div className="p-4 border-t border-gray-200">
        <div className="flex space-x-2">
          <input
            type="text"
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && sendMessage()}
            placeholder="输入您的问题..."
            className="flex-1 px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <button
            onClick={sendMessage}
            disabled={isLoading || !inputMessage.trim()}
            className="px-4 py-2 bg-blue-600 text-white rounded-md text-sm hover:bg-blue-700 disabled:opacity-50"
          >
            发送
          </button>
        </div>
      </div>
    </div>
  )
}

function App() {
  const [currentRole, setCurrentRole] = useState(() => localStorage.getItem('pilot_role') || 'admin')
  const [globalEnvironment, setGlobalEnvironment] = useState(() => localStorage.getItem(GLOBAL_ENV_STORAGE_KEY) || 'test')
  const [ping, setPing] = useState({ backend: 24, database: 12 })
  const [failedTasks] = useState([
    { id: 1, name: '订单处理服务 - 支付接口', time: '18:30', error: 'Timeout' },
    { id: 2, name: '商品管理平台 - 库存更新', time: '17:45', error: '500 Error' },
    { id: 3, name: '用户管理系统 - 登录验证', time: '16:20', error: 'Assert Failed' }
  ])
  const [showFailedTasks, setShowFailedTasks] = useState(false)
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)
  const [expandedSections, setExpandedSections] = useState({
    overview: false,  // 默认折叠,避免加载Dashboard
    projects: true,   // 项目管理分组
    development: true,
    scheduling: true,
    config: true
  })

  // 切换分组展开/折叠
  const toggleSection = (section) => {
    setExpandedSections(prev => ({
      ...prev,
      [section]: !prev[section]
    }))
  }

  // 模拟实时 Ping 跳动
  useEffect(() => {
    const interval = setInterval(() => {
      setPing({
        backend: Math.floor(Math.random() * 50) + 10, // 10-60ms
        database: Math.floor(Math.random() * 30) + 5   // 5-35ms
      })
    }, 2000)
    return () => clearInterval(interval)
  }, [])

  const handleRoleChange = (value) => {
    setCurrentRole(value)
    localStorage.setItem('pilot_role', value)
  }

  return (
    <ToastProvider>
      <Router>
      <div className="flex h-screen bg-gray-50">
        {/* 侧边栏 */}
        <div className={`${sidebarCollapsed ? 'w-16' : 'w-64'} bg-white border-r border-gray-200 flex flex-col transition-all duration-300`}>
          <div className="p-6 border-b border-gray-200 flex items-center justify-between">
            <div className={`flex items-center space-x-3 ${sidebarCollapsed ? 'hidden' : ''}`}>
              <div className="w-10 h-10 bg-blue-600 rounded-md flex items-center justify-center text-white font-bold text-lg">
                T
              </div>
              <div>
                <h1 className="text-lg font-bold text-gray-900">测试平台</h1>
                <p className="text-xs text-gray-500">企业级测试管理</p>
              </div>
            </div>
            {sidebarCollapsed && (
              <div className="w-10 h-10 bg-blue-600 rounded-md flex items-center justify-center text-white font-bold text-lg mx-auto">
                T
              </div>
            )}
          </div>
          
          <nav className="flex-1 p-4 space-y-6 overflow-y-auto">
            {/* 项目管理 */}
            <div>
              {!sidebarCollapsed && (
                <button
                  onClick={() => toggleSection('projects')}
                  className="w-full flex items-center justify-between px-3 mb-2 text-sm font-semibold text-slate-600 hover:text-slate-900 transition-colors"
                >
                  <span>项目管理</span>
                  <span>{expandedSections.projects ? '▼' : '▶'}</span>
                </button>
              )}
              {expandedSections.projects && [
                { to: '/projects-v2', icon: '■', label: '项目列表' },
                { to: '/test-cases', icon: '■', label: '测试用例' },
              ].map(item => (
                <NavLink 
                  key={item.to}
                  to={item.to} 
                  className={({ isActive }) => `flex items-center ${sidebarCollapsed ? 'justify-center' : 'space-x-3'} px-3 py-2.5 rounded-md transition-colors ${
                    isActive 
                      ? 'bg-blue-50 text-blue-700 font-medium border-l-3 border-blue-600' 
                      : 'text-slate-700 hover:bg-slate-50'
                  }`}
                  title={sidebarCollapsed ? item.label : ''}
                >
                  {!sidebarCollapsed && <span className="text-sm">{item.label}</span>}
                </NavLink>
              ))}
            </div>

            {/* 测试开发 */}
            <div>
              {!sidebarCollapsed && (
                <button
                  onClick={() => toggleSection('development')}
                  className="w-full flex items-center justify-between px-3 mb-2 text-sm font-semibold text-slate-600 hover:text-slate-900 transition-colors"
                >
                  <span>测试开发</span>
                  <span>{expandedSections.development ? '▼' : '▶'}</span>
                </button>
              )}
              {expandedSections.development && [
                { to: '/swagger-workbench', icon: '■', label: 'Swagger接入' },
                { to: '/api-specs', icon: '■', label: 'API规范' },
                { to: '/dataset-management', icon: '■', label: '数据集管理' },
                { to: '/test-data-factory', icon: '■', label: '测试数据工厂' },
              ].map(item => (
                <NavLink 
                  key={item.to}
                  to={item.to} 
                  className={({ isActive }) => `flex items-center ${sidebarCollapsed ? 'justify-center' : 'space-x-3'} px-3 py-2.5 rounded-md transition-colors ${
                    isActive 
                      ? 'bg-blue-50 text-blue-700 font-medium border-l-3 border-blue-600' 
                      : 'text-slate-700 hover:bg-slate-50'
                  }`}
                  title={sidebarCollapsed ? item.label : ''}
                >
                  {!sidebarCollapsed && <span className="text-sm">{item.label}</span>}
                </NavLink>
              ))}
            </div>

            {/* 执行管理 */}
            <div>
              {!sidebarCollapsed && (
                <button
                  onClick={() => toggleSection('scheduling')}
                  className="w-full flex items-center justify-between px-3 mb-2 text-sm font-semibold text-slate-600 hover:text-slate-900 transition-colors"
                >
                  <span>执行管理</span>
                  <span>{expandedSections.scheduling ? '▼' : '▶'}</span>
                </button>
              )}
              {expandedSections.scheduling && [
                { to: '/test-runs-v2', icon: '■', label: '执行记录' },
                { to: '/executor-v2', icon: '■', label: 'API测试执行' },
                { to: '/batch-run', icon: '■', label: '批量执行中心' },
              ].map(item => (
                <NavLink 
                  key={item.to}
                  to={item.to} 
                  className={({ isActive }) => `flex items-center ${sidebarCollapsed ? 'justify-center' : 'space-x-3'} px-3 py-2.5 rounded-md transition-colors ${
                    isActive 
                      ? 'bg-blue-50 text-blue-700 font-medium border-l-3 border-blue-600' 
                      : 'text-slate-700 hover:bg-slate-50'
                  }`}
                  title={sidebarCollapsed ? item.label : ''}
                >
                  {!sidebarCollapsed && <span className="text-sm">{item.label}</span>}
                </NavLink>
              ))}
            </div>

            {/* 配置管理 */}
            <div>
              {!sidebarCollapsed && (
                <button
                  onClick={() => toggleSection('config')}
                  className="w-full flex items-center justify-between px-3 mb-2 text-sm font-semibold text-slate-600 hover:text-slate-900 transition-colors"
                >
                  <span>配置管理</span>
                  <span>{expandedSections.config ? '▼' : '▶'}</span>
                </button>
              )}
              {expandedSections.config && [
                { to: '/ai-config', icon: '■', label: 'AI 模型配置' },
              ].map(item => (
                <NavLink 
                  key={item.to}
                  to={item.to} 
                  className={({ isActive }) => `flex items-center ${sidebarCollapsed ? 'justify-center' : 'space-x-3'} px-3 py-2.5 rounded-md transition-colors ${
                    isActive 
                      ? 'bg-blue-50 text-blue-700 font-medium border-l-3 border-blue-600' 
                      : 'text-slate-700 hover:bg-slate-50'
                  }`}
                  title={sidebarCollapsed ? item.label : ''}
                >
                  {!sidebarCollapsed && <span className="text-sm">{item.label}</span>}
                </NavLink>
              ))}
            </div>
          </nav>

          {/* 底部状态 */}
          <div className="p-4 border-t border-slate-200">
            {!sidebarCollapsed ? (
              <div className="bg-green-50 p-3 rounded-md border border-green-200">
                <div className="flex items-center justify-between mb-3">
                  <span className="text-sm font-semibold text-green-700">系统监控</span>
                  <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                </div>
                <div className="space-y-2">
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-slate-600">后端服务</span>
                    <div className="flex items-center gap-2">
                      <span className="font-semibold text-green-600">运行中</span>
                      <span className={`font-mono transition-colors ${
                        ping.backend > 100 ? 'text-red-600 animate-pulse' : 'text-slate-500'
                      }`}>
                        {ping.backend}ms
                      </span>
                    </div>
                  </div>
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-slate-600">数据库</span>
                    <div className="flex items-center gap-2">
                      <span className="font-semibold text-green-600">已连接</span>
                      <span className={`font-mono transition-colors ${
                        ping.database > 100 ? 'text-red-600 animate-pulse' : 'text-slate-500'
                      }`}>
                        {ping.database}ms
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            ) : (
              <div className="flex justify-center">
                <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
              </div>
            )}
            
            {/* 折叠/展开按钮 */}
            <button
              onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
              className="w-full mt-3 py-2 text-slate-600 hover:text-slate-900 hover:bg-slate-100 rounded-md transition-colors flex items-center justify-center"
              title={sidebarCollapsed ? '展开侧边栏' : '折叠侧边栏'}
            >
              <span className="text-lg">{sidebarCollapsed ? '→' : '←'}</span>
            </button>
          </div>
        </div>

        {/* 主内容区 */}
        <div className="flex-1 flex flex-col overflow-hidden">
          {/* 顶部栏 */}
          <div className="bg-white border-b border-slate-200 px-6 py-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                {/* 环境选择器 */}
                <select
                  value={globalEnvironment}
                  onChange={(e) => {
                    setGlobalEnvironment(e.target.value)
                    localStorage.setItem(GLOBAL_ENV_STORAGE_KEY, e.target.value)
                  }}
                  className="px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white"
                >
                  <option value="production">生产环境</option>
                  <option value="staging">预发布环境</option>
                  <option value="test">测试环境</option>
                </select>
                
                {/* 全局搜索框 - 标注为全局搜索 */}
                <div className="relative">
                  <input 
                    type="text" 
                    placeholder="全局搜索：测试用例、接口、项目..." 
                    className="w-96 px-4 py-2 pl-10 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                  <svg className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                  </svg>
                </div>
              </div>
              
              <div className="flex items-center gap-3">
                <select
                  value={currentRole}
                  onChange={(e) => handleRoleChange(e.target.value)}
                  className="px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white"
                >
                  <option value="admin">admin</option>
                  <option value="operator">operator</option>
                  <option value="viewer">viewer</option>
                </select>

                {/* 新建测试任务按钮 */}
                <button className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-md text-sm font-medium transition-colors">
                  <span className="text-lg">+</span>
                  新建测试任务
                </button>
                
                <div className="flex items-center gap-2 px-3 py-1.5 bg-green-50 border border-green-200 rounded-md">
                  <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                  <span className="text-sm text-green-700 font-medium">系统就绪</span>
                </div>
                
                {/* 通知铃铛 - 增强版 */}
                <div className="relative">
                  <button 
                    onClick={() => setShowFailedTasks(!showFailedTasks)}
                    className="relative p-2 text-slate-600 hover:text-slate-900 hover:bg-slate-100 rounded-md transition-colors"
                  >
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
                    </svg>
                    {failedTasks.length > 0 && (
                      <span className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full animate-pulse"></span>
                    )}
                  </button>
                  
                  {/* 最近失败任务下拉列表 */}
                  {showFailedTasks && (
                    <div className="absolute right-0 top-full mt-2 w-80 bg-white border border-slate-200 rounded-md shadow-lg z-50">
                      <div className="p-3 border-b border-slate-200 bg-red-50">
                        <div className="flex items-center justify-between">
                          <span className="text-sm font-semibold text-red-900">最近失败任务</span>
                          <span className="text-xs text-red-600">{failedTasks.length} 个</span>
                        </div>
                      </div>
                      <div className="max-h-64 overflow-y-auto">
                        {failedTasks.map(task => (
                          <div 
                            key={task.id}
                            className="p-3 border-b border-slate-100 hover:bg-slate-50 cursor-pointer"
                            onClick={() => alert(`查看错误日志:\n${task.name}\n错误: ${task.error}`)}
                          >
                            <div className="flex items-start justify-between">
                              <div className="flex-1">
                                <div className="text-sm font-medium text-slate-900">{task.name}</div>
                                <div className="text-xs text-red-600 mt-1">错误: {task.error}</div>
                              </div>
                              <span className="text-xs text-slate-500">{task.time}</span>
                            </div>
                          </div>
                        ))}
                      </div>
                      <div className="p-2 border-t border-slate-200 bg-slate-50">
                        <button 
                          onClick={() => setShowFailedTasks(false)}
                          className="w-full text-xs text-blue-600 hover:text-blue-800"
                        >
                          查看全部
                        </button>
                      </div>
                    </div>
                  )}
                </div>
                
                <div className="flex items-center gap-3 pl-3 border-l border-slate-200">
                  <div className="w-8 h-8 bg-blue-600 rounded-md flex items-center justify-center text-white text-sm font-medium">
                    AI
                  </div>
                  <div>
                    <p className="text-sm font-medium text-slate-900">AI测试平台</p>
                    <p className="text-xs text-slate-500">测试工程师</p>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* 页面内容 */}
          <div className="flex-1 overflow-auto">
            <Routes>
              <Route path="/" element={<Navigate to="/projects-v2" replace />} />
              
              {/* V2 可用页面 */}
              <Route path="/projects-v2" element={<ProjectsV2 />} />
              <Route path="/projects-v2/:projectId" element={<ProjectDetailV2 />} />
              <Route path="/test-cases" element={<TestCases />} />
              <Route path="/api-specs" element={<ApiSpecList />} />
              <Route path="/api-specs/:id" element={<ApiSpecDetail />} />
              <Route path="/swagger-workbench" element={<SwaggerWorkbench />} />
              <Route path="/test-runs-v2" element={<TestRunsV2 />} />
              <Route path="/test-runs-v2/:runId" element={<TestRunDetailV2 />} />
              <Route path="/quick-execution-test" element={<QuickExecutionTest />} />
              <Route path="/dataset-management" element={<DatasetManagement />} />
              <Route path="/test-data-factory" element={<TestDataFactory />} />
              <Route path="/ai-config" element={<AIConfigPage />} />
              <Route path="/executor-v2" element={<ExecutorV2 />} />
              <Route path="/batch-run" element={<BatchRunCenter />} />
              
              {/* 旧版页面 - 重定向到V2或占位页 */}
              <Route path="/projects" element={<Navigate to="/projects-v2" replace />} />
              <Route path="/projects-old" element={<Navigate to="/projects-v2" replace />} />
              <Route path="/projects/:id" element={<Navigate to="/projects-v2" replace />} />
              <Route path="/api-explorer-old" element={<Navigate to="/api-explorer" replace />} />
              <Route path="/test-cases-old" element={<Navigate to="/test-cases" replace />} />
              <Route path="/test-cases/:id" element={<Navigate to="/test-cases" replace />} />
              <Route path="/automation" element={<Navigate to="/quick-execution-test" replace />} />
              <Route path="/test-runs" element={<Navigate to="/test-runs-v2" replace />} />
              <Route path="/test-runs-old" element={<Navigate to="/test-runs-v2" replace />} />
              <Route path="/test-runs/:id" element={<Navigate to="/test-runs-v2" replace />} />
              <Route path="/reports" element={<Navigate to="/test-runs-v2" replace />} />
              <Route path="/reports/:id" element={<Navigate to="/test-runs-v2" replace />} />
              <Route path="/ai-insights" element={<Navigate to="/test-data-factory" replace />} />
              <Route path="/ai-test-console" element={<Navigate to="/quick-execution-test" replace />} />
            </Routes>
          </div>
        </div>
      </div>

      {/* 技术支持小部件 */}
      <TechSupportWidget />
    </Router>
    </ToastProvider>
  )
}

export default App
