// TestCases Component
export function TestCases() {
  const testCases = [
    { id: 1, title: '用户登录 - 有效凭据', module: '用户认证', priority: '高', status: 'passed', lastRun: '2小时前' },
    { id: 2, title: '用户登录 - 无效密码', module: '用户认证', priority: '高', status: 'failed', lastRun: '2小时前' },
    { id: 3, title: '商品搜索 - 关键词搜索', module: '商品管理', priority: '中', status: 'passed', lastRun: '1天前' },
    { id: 4, title: '订单创建 - 正常流程', module: '订单管理', priority: '高', status: 'pending', lastRun: '从未运行' }
  ]

  return (
    <div className="p-8">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">测试用例</h1>
          <p className="text-gray-600 mt-1">管理和执行测试用例，跟踪测试结果</p>
        </div>
        <button className="px-4 py-2 bg-gradient-to-r from-blue-600 to-blue-700 text-white rounded-lg hover:from-blue-700 hover:to-blue-800 flex items-center space-x-2">
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
          </svg>
          <span>AI生成用例</span>
        </button>
      </div>

      <div className="bg-white rounded-lg shadow-sm border overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-semibold">测试用例列表</h3>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider">标题</th>
                <th className="px-6 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider">模块</th>
                <th className="px-6 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider">优先级</th>
                <th className="px-6 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider">状态</th>
                <th className="px-6 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider">最后运行</th>
                <th className="px-6 py-3 text-right text-xs font-semibold text-gray-700 uppercase tracking-wider">操作</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {testCases.map((testCase) => (
                <tr key={testCase.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 font-medium text-gray-900">{testCase.title}</td>
                  <td className="px-6 py-4 text-gray-600">{testCase.module}</td>
                  <td className="px-6 py-4">
                    <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                      testCase.priority === '高' ? 'bg-red-100 text-red-800' :
                      testCase.priority === '中' ? 'bg-yellow-100 text-yellow-800' : 'bg-green-100 text-green-800'
                    }`}>
                      {testCase.priority}
                    </span>
                  </td>
                  <td className="px-6 py-4">
                    <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                      testCase.status === 'passed' ? 'bg-green-100 text-green-800' :
                      testCase.status === 'failed' ? 'bg-red-100 text-red-800' : 'bg-gray-100 text-gray-800'
                    }`}>
                      {testCase.status === 'passed' ? '通过' : testCase.status === 'failed' ? '失败' : '待运行'}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-gray-600">{testCase.lastRun}</td>
                  <td className="px-6 py-4 text-right">
                    <div className="flex items-center justify-end space-x-2">
                      <button className="px-3 py-1 text-sm bg-blue-100 text-blue-700 rounded hover:bg-blue-200">运行</button>
                      <button className="px-3 py-1 text-sm bg-gray-100 text-gray-700 rounded hover:bg-gray-200">编辑</button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}

// Automation Component
export function Automation() {
  const scripts = [
    { id: 1, name: 'test_user_authentication.py', description: '用户认证自动化测试脚本', framework: 'pytest', status: 'ready', testCount: 12 },
    { id: 2, name: 'test_product_management.py', description: '商品管理自动化测试脚本', framework: 'pytest', status: 'ready', testCount: 8 },
    { id: 3, name: 'test_order_workflow.py', description: '订单流程自动化测试脚本', framework: 'pytest', status: 'generating', testCount: 15 }
  ]

  return (
    <div className="p-8">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">自动化脚本</h1>
          <p className="text-gray-600 mt-1">生成和管理自动化测试脚本</p>
        </div>
        <button className="px-4 py-2 bg-gradient-to-r from-blue-600 to-blue-700 text-white rounded-lg hover:from-blue-700 hover:to-blue-800 flex items-center space-x-2">
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
          </svg>
          <span>生成脚本</span>
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {scripts.map((script) => (
          <div key={script.id} className="bg-white p-6 rounded-lg shadow-sm border">
            <div className="flex items-start justify-between mb-4">
              <div className="flex items-center space-x-3">
                <div className="p-2 bg-blue-100 rounded-lg">
                  <svg className="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" />
                  </svg>
                </div>
                <div>
                  <h3 className="font-semibold text-gray-900">{script.name}</h3>
                  <p className="text-sm text-gray-600">{script.description}</p>
                </div>
              </div>
            </div>
            
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-500">框架</span>
                <span className="text-sm font-medium text-gray-900">{script.framework}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-500">测试数量</span>
                <span className="text-sm font-medium text-gray-900">{script.testCount}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-500">状态</span>
                <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                  script.status === 'ready' ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'
                }`}>
                  {script.status === 'ready' ? '就绪' : '生成中'}
                </span>
              </div>
            </div>
            
            <div className="mt-6 flex space-x-2">
              <button className="flex-1 px-3 py-2 text-sm bg-blue-100 text-blue-700 rounded hover:bg-blue-200">
                查看代码
              </button>
              <button className="flex-1 px-3 py-2 text-sm bg-green-100 text-green-700 rounded hover:bg-green-200">
                运行脚本
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

// TestRuns Component
export function TestRuns() {
  const testRuns = [
    { id: 1, name: '完整API测试套件', status: 'completed', progress: 100, totalTests: 45, passed: 42, failed: 3, duration: '00:05:23' },
    { id: 2, name: '用户模块测试', status: 'running', progress: 65, totalTests: 20, passed: 13, failed: 0, duration: '00:02:15' },
    { id: 3, name: '支付流程测试', status: 'pending', progress: 0, totalTests: 15, passed: 0, failed: 0, duration: '00:00:00' }
  ]

  return (
    <div className="p-8">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">测试执行</h1>
          <p className="text-gray-600 mt-1">监控测试执行状态和结果</p>
        </div>
        <button className="px-4 py-2 bg-gradient-to-r from-blue-600 to-blue-700 text-white rounded-lg hover:from-blue-700 hover:to-blue-800 flex items-center space-x-2">
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.828 14.828a4 4 0 01-5.656 0M9 10h1m4 0h1m-6 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <span>新建测试运行</span>
        </button>
      </div>

      <div className="space-y-6">
        {testRuns.map((run) => (
          <div key={run.id} className="bg-white p-6 rounded-lg shadow-sm border">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="text-lg font-semibold text-gray-900">{run.name}</h3>
                <p className="text-sm text-gray-600">执行时间: {run.duration}</p>
              </div>
              <span className={`px-3 py-1 text-sm font-medium rounded-full ${
                run.status === 'completed' ? 'bg-green-100 text-green-800' :
                run.status === 'running' ? 'bg-blue-100 text-blue-800' : 'bg-gray-100 text-gray-800'
              }`}>
                {run.status === 'completed' ? '已完成' : run.status === 'running' ? '运行中' : '等待中'}
              </span>
            </div>
            
            <div className="mb-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm text-gray-600">进度</span>
                <span className="text-sm font-medium text-gray-900">{run.progress}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div 
                  className={`h-2 rounded-full ${
                    run.status === 'completed' ? 'bg-green-500' : 'bg-blue-500'
                  }`}
                  style={{ width: `${run.progress}%` }}
                ></div>
              </div>
            </div>
            
            <div className="grid grid-cols-4 gap-4">
              <div className="text-center">
                <p className="text-2xl font-bold text-gray-900">{run.totalTests}</p>
                <p className="text-xs text-gray-500">总测试数</p>
              </div>
              <div className="text-center">
                <p className="text-2xl font-bold text-green-600">{run.passed}</p>
                <p className="text-xs text-gray-500">通过</p>
              </div>
              <div className="text-center">
                <p className="text-2xl font-bold text-red-600">{run.failed}</p>
                <p className="text-xs text-gray-500">失败</p>
              </div>
              <div className="text-center">
                <p className="text-2xl font-bold text-yellow-600">{run.totalTests - run.passed - run.failed}</p>
                <p className="text-xs text-gray-500">待执行</p>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

// Reports Component
export function Reports() {
  const reports = [
    { id: 1, name: 'API测试报告 - 2024年3月', type: '综合报告', date: '2024-03-14', size: '2.3 MB', format: 'HTML' },
    { id: 2, name: '用户模块测试报告', type: '模块报告', date: '2024-03-13', size: '1.8 MB', format: 'PDF' },
    { id: 3, name: '性能测试报告', type: '性能报告', date: '2024-03-12', size: '3.1 MB', format: 'HTML' }
  ]

  return (
    <div className="p-8">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">测试报告</h1>
          <p className="text-gray-600 mt-1">查看和管理测试报告</p>
        </div>
        <button className="px-4 py-2 bg-gradient-to-r from-blue-600 to-blue-700 text-white rounded-lg hover:from-blue-700 hover:to-blue-800 flex items-center space-x-2">
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          <span>生成报告</span>
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {reports.map((report) => (
          <div key={report.id} className="bg-white p-6 rounded-lg shadow-sm border">
            <div className="flex items-start justify-between mb-4">
              <div className="flex items-center space-x-3">
                <div className="p-2 bg-green-100 rounded-lg">
                  <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                </div>
                <div>
                  <h3 className="font-semibold text-gray-900">{report.name}</h3>
                  <p className="text-sm text-gray-600">{report.type}</p>
                </div>
              </div>
            </div>
            
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-500">日期</span>
                <span className="text-sm font-medium text-gray-900">{report.date}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-500">大小</span>
                <span className="text-sm font-medium text-gray-900">{report.size}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-500">格式</span>
                <span className="text-sm font-medium text-gray-900">{report.format}</span>
              </div>
            </div>
            
            <div className="mt-6 flex space-x-2">
              <button className="flex-1 px-3 py-2 text-sm bg-blue-100 text-blue-700 rounded hover:bg-blue-200">
                查看
              </button>
              <button className="flex-1 px-3 py-2 text-sm bg-green-100 text-green-700 rounded hover:bg-green-200">
                下载
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

// AiInsights Component
export function AiInsights() {
  const agents = [
    { id: 'requirement', name: 'Requirement Agent', status: 'ready', description: '分析需求并提取可测试场景' },
    { id: 'testcase', name: 'TestCase Agent', status: 'ready', description: '从需求生成综合测试用例' },
    { id: 'automation', name: 'Automation Agent', status: 'ready', description: '生成自动化测试脚本' },
    { id: 'execution', name: 'Test Runner', status: 'running', description: '执行测试并收集结果' },
    { id: 'analysis', name: 'Failure Analyzer', status: 'ready', description: '分析失败原因并提供修复建议' },
    { id: 'report', name: 'Bug Generator', status: 'ready', description: '生成详细的缺陷报告' }
  ]

  return (
    <div className="p-8">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">AI分析中心</h1>
          <p className="text-gray-600 mt-1">AI代理工作流程和智能分析</p>
        </div>
        <button className="px-4 py-2 bg-gradient-to-r from-blue-600 to-blue-700 text-white rounded-lg hover:from-blue-700 hover:to-blue-800 flex items-center space-x-2">
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
          </svg>
          <span>启动AI分析</span>
        </button>
      </div>

      <div className="mb-8">
        <h2 className="text-xl font-semibold mb-4">AI代理工作流程</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {agents.map((agent, index) => (
            <div key={agent.id} className="relative">
              <div className="bg-white p-6 rounded-lg shadow-sm border">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center space-x-3">
                    <div className={`p-2 rounded-lg ${
                      agent.status === 'running' ? 'bg-blue-100' : 'bg-green-100'
                    }`}>
                      <svg className={`w-6 h-6 ${
                        agent.status === 'running' ? 'text-blue-600' : 'text-green-600'
                      }`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                      </svg>
                    </div>
                    <div>
                      <h3 className="font-semibold text-gray-900">{agent.name}</h3>
                      <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                        agent.status === 'running' ? 'bg-blue-100 text-blue-800' : 'bg-green-100 text-green-800'
                      }`}>
                        {agent.status === 'running' ? '运行中' : '就绪'}
                      </span>
                    </div>
                  </div>
                </div>
                <p className="text-sm text-gray-600">{agent.description}</p>
              </div>
              
              {index < agents.length - 1 && (
                <div className="hidden lg:block absolute top-1/2 -right-3 transform -translate-y-1/2">
                  <svg className="w-6 h-6 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

// Settings Component
export function Settings() {
  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">设置</h1>
        <p className="text-gray-600 mt-1">系统配置和偏好设置</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2 space-y-6">
          <div className="bg-white p-6 rounded-lg shadow-sm border">
            <h3 className="text-lg font-semibold mb-4">基本设置</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">系统名称</label>
                <input type="text" value="AI测试平台" className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">默认环境</label>
                <select className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500">
                  <option>开发环境</option>
                  <option>测试环境</option>
                  <option>生产环境</option>
                </select>
              </div>
            </div>
          </div>

          <div className="bg-white p-6 rounded-lg shadow-sm border">
            <h3 className="text-lg font-semibold mb-4">AI配置</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">AI模型</label>
                <select className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500">
                  <option>GPT-4</option>
                  <option>GPT-3.5</option>
                  <option>Claude</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">API密钥</label>
                <input type="password" placeholder="输入API密钥" className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
              </div>
            </div>
          </div>
        </div>

        <div className="space-y-6">
          <div className="bg-white p-6 rounded-lg shadow-sm border">
            <h3 className="text-lg font-semibold mb-4">系统状态</h3>
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">数据库连接</span>
                <span className="px-2 py-1 text-xs font-medium bg-green-100 text-green-800 rounded-full">正常</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">AI服务</span>
                <span className="px-2 py-1 text-xs font-medium bg-green-100 text-green-800 rounded-full">正常</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">测试引擎</span>
                <span className="px-2 py-1 text-xs font-medium bg-green-100 text-green-800 rounded-full">正常</span>
              </div>
            </div>
          </div>

          <div className="bg-white p-6 rounded-lg shadow-sm border">
            <h3 className="text-lg font-semibold mb-4">快速操作</h3>
            <div className="space-y-2">
              <button className="w-full px-4 py-2 text-sm bg-blue-100 text-blue-700 rounded hover:bg-blue-200">
                清理缓存
              </button>
              <button className="w-full px-4 py-2 text-sm bg-green-100 text-green-700 rounded hover:bg-green-200">
                导出配置
              </button>
              <button className="w-full px-4 py-2 text-sm bg-yellow-100 text-yellow-700 rounded hover:bg-yellow-200">
                重启服务
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}