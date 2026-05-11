import { BrowserRouter as Router, Routes, Route, NavLink, Navigate } from 'react-router-dom'
import { useState, useEffect } from 'react'
import { ToastProvider } from './components/ui/Toast'

// 导入页面组件（仅导入实际使用的）
import Reports from './pages/Reports'
import ReportDetail from './pages/ReportDetail'
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
import Dashboard from './pages/Dashboard'
import RealProjectOnboarding from './pages/RealProjectOnboarding'
import TestSuites from './pages/TestSuites'
import QualityGate from './pages/QualityGate'
import TestDataManagement from './pages/TestDataManagement'
import DefectManagement from './pages/DefectManagement'
import QualityDashboard from './pages/QualityDashboard'
import TestSelection from './pages/TestSelection'
import RequirementUpload from './pages/RequirementUpload'
import CodeCompare from './pages/CodeCompare'
import VisualTesting from './pages/VisualTesting'
import ProductStudio from './pages/ProductStudio'
import ProductStudioDetail from './pages/ProductStudioDetail'
import DevStudio from './pages/DevStudio'
import DevStudioDetail from './pages/DevStudioDetail'

// 健康检查轮询间隔（毫秒）
const HEALTH_CHECK_INTERVAL = 30000

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
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)
  const [healthStatus, setHealthStatus] = useState({ ok: null, latency: null }) // null=未检测
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

  // 真实 /health 健康检查
  useEffect(() => {
    const checkHealth = async () => {
      try {
        const start = performance.now()
        const res = await fetch('/health', { signal: AbortSignal.timeout(5000) })
        const latency = Math.round(performance.now() - start)
        setHealthStatus({ ok: res.ok, latency })
      } catch {
        setHealthStatus({ ok: false, latency: null })
      }
    }
    checkHealth()
    const interval = setInterval(checkHealth, HEALTH_CHECK_INTERVAL)
    return () => clearInterval(interval)
  }, [])

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
                { to: '/dashboard', icon: '■', label: '仪表盘' },
                { to: '/projects-v2', icon: '■', label: '项目列表' },
                { to: '/test-cases', icon: '■', label: '测试用例' },
                { to: '/requirement-upload', icon: '■', label: '需求生成用例' },
                { to: '/code-compare', icon: '■', label: '需求-代码对比' },
                { to: '/test-suites', icon: '■', label: '测试集管理' },
                { to: '/test-data', icon: '■', label: '测试数据' },
                { to: '/defects', icon: '■', label: '缺陷管理' },
                { to: '/quality-dashboard', icon: '■', label: '质量驾驶舱' },
                { to: '/visual-testing', icon: '■', label: '视觉测试' },
                { to: '/test-selection', icon: '■', label: '智能选测' },
                { to: '/product-studio', icon: '■', label: 'AI 产品工坊' },
                { to: '/dev-studio', icon: '■', label: 'AI 研发工坊' },
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
                { to: '/quality-gate', icon: '■', label: '质量门禁' },
                { to: '/reports', icon: '■', label: '测试报告' },
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
              <div className={`p-3 rounded-md border ${
                healthStatus.ok === null
                  ? 'bg-slate-50 border-slate-200'
                  : healthStatus.ok
                    ? 'bg-green-50 border-green-200'
                    : 'bg-red-50 border-red-200'
              }`}>
                <div className="flex items-center justify-between">
                  <span className={`text-sm font-semibold ${
                    healthStatus.ok === null ? 'text-slate-600' : healthStatus.ok ? 'text-green-700' : 'text-red-700'
                  }`}>后端状态</span>
                  <div className={`w-2 h-2 rounded-full ${
                    healthStatus.ok === null ? 'bg-slate-400' : healthStatus.ok ? 'bg-green-500 animate-pulse' : 'bg-red-500 animate-pulse'
                  }`}></div>
                </div>
                <div className="mt-2 text-xs text-slate-600">
                  {healthStatus.ok === null ? '检测中...' : healthStatus.ok
                    ? `服务正常${healthStatus.latency !== null ? ` · ${healthStatus.latency}ms` : ''}`
                    : '连接异常'}
                </div>
              </div>
            ) : (
              <div className="flex justify-center">
                <div className={`w-2 h-2 rounded-full ${
                  healthStatus.ok === null ? 'bg-slate-400' : healthStatus.ok ? 'bg-green-500 animate-pulse' : 'bg-red-500 animate-pulse'
                }`}></div>
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
              <div className="flex items-center gap-3">
                <h2 className="text-base font-semibold text-slate-800">AI 测试平台</h2>
              </div>
              
              <div className="flex items-center gap-3">
                {/* 真实健康状态 */}
                <div className={`flex items-center gap-2 px-3 py-1.5 rounded-md border ${
                  healthStatus.ok === null
                    ? 'bg-slate-50 border-slate-200'
                    : healthStatus.ok
                      ? 'bg-green-50 border-green-200'
                      : 'bg-red-50 border-red-200'
                }`}>
                  <div className={`w-2 h-2 rounded-full ${
                    healthStatus.ok === null
                      ? 'bg-slate-400'
                      : healthStatus.ok
                        ? 'bg-green-500 animate-pulse'
                        : 'bg-red-500 animate-pulse'
                  }`}></div>
                  <span className={`text-sm font-medium ${
                    healthStatus.ok === null
                      ? 'text-slate-500'
                      : healthStatus.ok
                        ? 'text-green-700'
                        : 'text-red-700'
                  }`}>
                    {healthStatus.ok === null ? '检测中...' : healthStatus.ok ? '系统就绪' : '连接异常'}
                  </span>
                  {healthStatus.ok && healthStatus.latency !== null && (
                    <span className="text-xs text-slate-500 font-mono">{healthStatus.latency}ms</span>
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
              <Route path="/" element={<Navigate to="/dashboard" replace />} />
              <Route path="/dashboard" element={<Dashboard />} />
              
              {/* V2 可用页面 */}
              <Route path="/projects-v2" element={<ProjectsV2 />} />
              <Route path="/projects-v2/:projectId" element={<ProjectDetailV2 />} />
              <Route path="/test-cases" element={<TestCases />} />
              <Route path="/requirement-upload" element={<RequirementUpload />} />
              <Route path="/code-compare" element={<CodeCompare />} />
              <Route path="/api-specs" element={<ApiSpecList />} />
              <Route path="/api-specs/:id" element={<ApiSpecDetail />} />
              <Route path="/swagger-workbench" element={<SwaggerWorkbench />} />
              <Route path="/test-runs-v2" element={<TestRunsV2 />} />
              <Route path="/test-runs-v2/:runId" element={<TestRunDetailV2 />} />
              <Route path="/quick-execution-test" element={<QuickExecutionTest />} />
              <Route path="/reports" element={<Reports />} />
              <Route path="/reports/:id" element={<ReportDetail />} />
              <Route path="/dataset-management" element={<div className="p-12 text-center"><p className="text-lg text-slate-500">数据集管理功能暂未启用，后续版本开放。</p></div>} />
              <Route path="/test-data-factory" element={<div className="p-12 text-center"><p className="text-lg text-slate-500">测试数据工厂功能暂未启用，后续版本开放。</p></div>} />
              <Route path="/ai-config" element={<AIConfigPage />} />
              <Route path="/executor-v2" element={<ExecutorV2 />} />
              <Route path="/batch-run" element={<BatchRunCenter />} />
              <Route path="/test-suites" element={<TestSuites />} />
              <Route path="/quality-gate" element={<QualityGate />} />
              <Route path="/test-data" element={<TestDataManagement />} />
              <Route path="/defects" element={<DefectManagement />} />
              <Route path="/quality-dashboard" element={<QualityDashboard />} />
              <Route path="/visual-testing" element={<VisualTesting />} />
              <Route path="/test-selection" element={<TestSelection />} />
              <Route path="/product-studio" element={<ProductStudio />} />
              <Route path="/product-studio/:ideaId" element={<ProductStudioDetail />} />
              <Route path="/dev-studio" element={<DevStudio />} />
              <Route path="/dev-studio/:devTaskId" element={<DevStudioDetail />} />
              <Route path="/real-project-onboarding" element={<RealProjectOnboarding />} />
              
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
              <Route path="/ai-insights" element={<Navigate to="/dashboard" replace />} />
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
