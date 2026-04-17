import { useState } from 'react'

function AiTestConsole() {
  const [requirement, setRequirement] = useState('')
  const [gitDiff, setGitDiff] = useState('')
  const [priority, setPriority] = useState('P1')
  const [executionMode, setExecutionMode] = useState('full') // 新增: 执行模式
  const [isRunning, setIsRunning] = useState(false)
  const [result, setResult] = useState(null)
  const [currentStage, setCurrentStage] = useState(null)

  // 运行AI测试
  const runAiTest = async () => {
    if (!requirement.trim()) {
      alert('请输入需求描述')
      return
    }

    setIsRunning(true)
    setResult(null)
    setCurrentStage('agent')

    try {
      // 根据执行模式选择不同的API
      if (executionMode === 'decision-only') {
        // 仅决策模式: 只调用Agent API
        const response = await fetch('/api/agent/analyze', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            requirement: requirement,
            git_diff: gitDiff
          })
        })

        const decision = await response.json()
        
        // 构造简化的结果格式
        setResult({
          decision: decision,
          mode: 'decision-only',
          trace_id: `decision-${Date.now()}`
        })
      } else {
        // 完整流程模式: 调用Pipeline API
        const response = await fetch('/api/pipeline/run', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            requirement: requirement,
            git_diff: gitDiff,
            context: { priority: priority }
          })
        })

        const data = await response.json()
        setResult(data)
      }
      
      setCurrentStage(null)
    } catch (error) {
      console.error('执行失败:', error)
      alert('执行失败: ' + error.message)
    } finally {
      setIsRunning(false)
    }
  }

  // 清空表单
  const clearForm = () => {
    setRequirement('')
    setGitDiff('')
    setPriority('P1')
    setExecutionMode('full')
    setResult(null)
    setCurrentStage(null)
  }

  return (
    <div className="p-8 space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="space-y-1">
          <h1 className="text-3xl font-bold text-gray-900">🚀 AI测试控制台</h1>
          <p className="text-gray-600">
            {executionMode === 'decision-only' 
              ? '快速决策分析 - 仅判断是否需要测试' 
              : '一键执行五阶段自动化测试流程,从决策到报告全自动'}
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* 左侧：输入区域 */}
        <div className="space-y-6">
          {/* 输入卡片 */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-200">
            <div className="p-6 border-b border-gray-200">
              <h2 className="text-lg font-semibold text-gray-900">📝 输入信息</h2>
            </div>
            <div className="p-6 space-y-4">
            
            {/* 执行模式 */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                执行模式
              </label>
              <select
                value={executionMode}
                onChange={(e) => setExecutionMode(e.target.value)}
                disabled={isRunning}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="full">完整流程 (5阶段) - 决策→策略→执行→修复→报告</option>
                <option value="decision-only">仅决策分析 (快速) - 只判断是否需要测试</option>
              </select>
              <p className="text-xs text-gray-500 mt-1">
                {executionMode === 'decision-only' 
                  ? '⚡ 快速模式: 2-5秒完成,适合代码提交前快速检查' 
                  : '🔄 完整模式: 10-20秒完成,包含测试执行和自动修复'}
              </p>
            </div>
            
            {/* 需求描述 */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                需求描述 <span className="text-red-500">*</span>
              </label>
              <textarea
                value={requirement}
                onChange={(e) => setRequirement(e.target.value)}
                placeholder="例如：支付模块需要支持微信支付和支付宝支付"
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
                rows="4"
                disabled={isRunning}
              />
            </div>

            {/* Git Diff */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Git Diff（可选）
              </label>
              <textarea
                value={gitDiff}
                onChange={(e) => setGitDiff(e.target.value)}
                placeholder="+def wechat_pay():\n+    return process_payment('wechat')"
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono text-sm resize-none"
                rows="6"
                disabled={isRunning}
              />
            </div>

            {/* 优先级 - 仅完整流程模式显示 */}
            {executionMode === 'full' && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  优先级
                </label>
                <div className="flex space-x-3">
                  {['P0', 'P1', 'P2'].map(p => (
                    <button
                      key={p}
                      onClick={() => setPriority(p)}
                      disabled={isRunning}
                      className={`flex-1 py-2 px-4 rounded-lg font-medium transition-colors ${
                        priority === p
                          ? 'bg-blue-500 text-white'
                          : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                      } ${isRunning ? 'opacity-50 cursor-not-allowed' : ''}`}
                    >
                      {p}
                    </button>
                  ))}
                </div>
                <p className="text-xs text-gray-500 mt-2">
                  P0: 核心功能 | P1: 重要功能 | P2: 一般功能
                </p>
              </div>
            )}

            {/* 执行按钮 */}
            <div className="flex space-x-3">
              <button
                onClick={runAiTest}
                disabled={isRunning || !requirement.trim()}
                className="flex-1 py-3 px-6 bg-gradient-to-r from-blue-500 to-blue-600 text-white rounded-lg font-semibold hover:from-blue-600 hover:to-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 flex items-center justify-center space-x-2"
              >
                {isRunning ? (
                  <>
                    <span className="animate-spin">⚙️</span>
                    <span>执行中...</span>
                  </>
                ) : (
                  <>
                    <span>{executionMode === 'decision-only' ? '⚡' : '🚀'}</span>
                    <span>{executionMode === 'decision-only' ? '快速决策' : 'Run AI Test'}</span>
                  </>
                )}
              </button>
              
              <button
                onClick={clearForm}
                disabled={isRunning}
                className="py-3 px-6 border border-gray-200 text-gray-700 rounded-lg font-semibold hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                清空
              </button>
            </div>
            </div>
          </div>
        </div>

        {/* 右侧：结果展示 */}
        <div className="space-y-6">
          {/* 执行进度 */}
          {isRunning && (
            <div className="bg-white rounded-xl border border-gray-200 shadow-sm">
              <div className="p-6 border-b border-gray-200">
                <div className="flex items-center justify-between">
                  <h2 className="text-lg font-semibold text-gray-900">⚡ 执行进度</h2>
                  <span className="text-sm font-medium text-blue-600">
                    {(() => {
                      const stages = executionMode === 'decision-only' 
                        ? ['agent'] 
                        : ['agent', 'strategy', 'orchestrator', 'healing', 'report'];
                      const currentIndex = stages.indexOf(currentStage);
                      const progress = currentIndex >= 0 
                        ? Math.round(((currentIndex + 1) / stages.length) * 100)
                        : 0;
                      return `${progress}%`;
                    })()}
                  </span>
                </div>
              </div>
              <div className="p-6">
              {/* 进度条 */}
              <div className="mb-6">
                <div className="w-full bg-gray-200 rounded-full h-3 overflow-hidden">
                  <div 
                    className="h-3 bg-gradient-to-r from-blue-500 to-blue-600 rounded-full transition-all duration-500 ease-out"
                    style={{ 
                      width: `${(() => {
                        const stages = executionMode === 'decision-only' 
                          ? ['agent'] 
                          : ['agent', 'strategy', 'orchestrator', 'healing', 'report'];
                        const currentIndex = stages.indexOf(currentStage);
                        return currentIndex >= 0 
                          ? ((currentIndex + 1) / stages.length) * 100
                          : 0;
                      })()}%` 
                    }}
                  >
                    <div className="h-full w-full bg-gradient-to-r from-transparent via-white to-transparent opacity-30 animate-pulse"></div>
                  </div>
                </div>
              </div>

              {/* 阶段列表 */}
              <div className="space-y-3">
                {(executionMode === 'decision-only' 
                  ? ['agent'] 
                  : ['agent', 'strategy', 'orchestrator', 'healing', 'report']
                ).map((stage, index) => {
                  const stages = executionMode === 'decision-only' 
                    ? ['agent'] 
                    : ['agent', 'strategy', 'orchestrator', 'healing', 'report'];
                  const currentIndex = stages.indexOf(currentStage);
                  const isCompleted = index < currentIndex;
                  const isCurrent = currentStage === stage;
                  
                  return (
                    <div key={stage} className="flex items-center space-x-3">
                      <div className={`w-8 h-8 rounded-full flex items-center justify-center transition-all duration-300 ${
                        isCompleted
                          ? 'bg-green-500 text-white'
                          : isCurrent
                          ? 'bg-blue-500 text-white animate-pulse'
                          : 'bg-gray-200 text-gray-500'
                      }`}>
                        {isCompleted ? '✓' : index + 1}
                      </div>
                      <div className="flex-1">
                        <div className={`text-sm font-medium transition-colors ${
                          isCompleted || isCurrent ? 'text-gray-900' : 'text-gray-500'
                        }`}>
                          {stage === 'agent' && '🤖 AI决策分析'}
                          {stage === 'strategy' && '📋 生成测试策略'}
                          {stage === 'orchestrator' && '⚡ 执行测试'}
                          {stage === 'healing' && '🔧 自动修复'}
                          {stage === 'report' && '📊 生成报告'}
                        </div>
                      </div>
                      {isCompleted && (
                        <span className="text-green-500 text-sm">✓ 完成</span>
                      )}
                      {isCurrent && (
                        <span className="text-blue-500 text-sm animate-pulse">● 运行中</span>
                      )}
                    </div>
                  );
                })}
              </div>
              </div>
            </div>
          )}

          {/* 结果展示 */}
          {result && (
            <div className="space-y-6">
              {/* AI决策 */}
              <div className="bg-white rounded-xl border border-gray-200 shadow-sm">
                <div className="p-6 border-b border-gray-200">
                  <h3 className="text-lg font-semibold text-gray-900">🤖 AI决策</h3>
                </div>
                <div className="p-6">
                <div className="space-y-3">
                  <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                    <span className="text-sm text-gray-600">是否执行</span>
                    <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                      result.decision.need_test
                        ? 'bg-green-100 text-green-700'
                        : 'bg-gray-100 text-gray-700'
                    }`}>
                      {result.decision.need_test ? '✅ 需要测试' : '⏭️ 跳过'}
                    </span>
                  </div>
                  
                  <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                    <span className="text-sm text-gray-600">优先级</span>
                    <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                      result.decision.priority === 'P0' ? 'bg-red-100 text-red-700' :
                      result.decision.priority === 'P1' ? 'bg-yellow-100 text-yellow-700' :
                      'bg-blue-100 text-blue-700'
                    }`}>
                      {result.decision.priority}
                    </span>
                  </div>
                  
                  <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                    <span className="text-sm text-gray-600">风险等级</span>
                    <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                      result.decision.risk_level === '高' ? 'bg-red-100 text-red-700' :
                      result.decision.risk_level === '中' ? 'bg-yellow-100 text-yellow-700' :
                      'bg-green-100 text-green-700'
                    }`}>
                      {result.decision.risk_level}
                    </span>
                  </div>

                  <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                    <span className="text-sm text-gray-600">置信度</span>
                    <span className="text-sm font-medium text-gray-900">
                      {(result.decision.confidence * 100).toFixed(0)}%
                    </span>
                  </div>
                </div>
                </div>
              </div>

              {/* 仅决策模式提示 */}
              {result.mode === 'decision-only' && (
                <div className="bg-yellow-50 rounded-xl border border-yellow-200 p-4">
                  <div className="flex items-start space-x-2">
                    <span className="text-xl">⚡</span>
                    <div className="flex-1">
                      <div className="text-sm font-medium text-yellow-900 mb-1">快速决策模式</div>
                      <div className="text-sm text-yellow-800">
                        仅完成AI决策分析。如需执行完整测试流程,请切换到"完整流程"模式。
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* 测试策略 */}
              {result.strategy && (
                <div className="bg-white rounded-xl border border-gray-200 shadow-sm">
                  <div className="p-6 border-b border-gray-200">
                    <h3 className="text-lg font-semibold text-gray-900">📋 测试策略</h3>
                  </div>
                  <div className="p-6">
                  <div className="space-y-3">
                    {result.strategy.strategy?.map((module, index) => (
                      <div key={index} className="p-4 bg-gray-50 rounded-lg">
                        <div className="flex items-center justify-between mb-2">
                          <span className="font-medium text-gray-900">
                            {module.module?.name || module.module}
                          </span>
                          <span className="text-xs text-gray-500">
                            顺序: {module.execution_order}
                          </span>
                        </div>
                        <div className="flex flex-wrap gap-2">
                          {module.test_types?.map((type, i) => (
                            <span key={i} className="px-2 py-1 bg-blue-100 text-blue-700 text-xs rounded">
                              {type}
                            </span>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                  </div>
                </div>
              )}

              {/* 执行结果 */}
              {result.execution && (
                <div className="bg-white rounded-xl border border-gray-200 shadow-sm">
                  <div className="p-6 border-b border-gray-200">
                    <h3 className="text-lg font-semibold text-gray-900">⚡ 执行过程</h3>
                  </div>
                  <div className="p-6">
                  
                  {/* 统计 */}
                  <div className="grid grid-cols-3 gap-4 mb-4">
                    <div className="p-3 bg-gray-50 rounded-lg text-center">
                      <div className="text-2xl font-bold text-gray-900">
                        {result.execution.summary.total}
                      </div>
                      <div className="text-xs text-gray-600">总数</div>
                    </div>
                    <div className="p-3 bg-green-50 rounded-lg text-center">
                      <div className="text-2xl font-bold text-green-700">
                        {result.execution.summary.passed}
                      </div>
                      <div className="text-xs text-green-600">通过</div>
                    </div>
                    <div className="p-3 bg-red-50 rounded-lg text-center">
                      <div className="text-2xl font-bold text-red-700">
                        {result.execution.summary.failed}
                      </div>
                      <div className="text-xs text-red-600">失败</div>
                    </div>
                  </div>

                  {/* 详细结果 */}
                  <div className="space-y-2">
                    {result.execution.results?.map((item, index) => {
                      // 适配后端 Task 数据格式
                      const caseName = item.case?.name || item.case?.module || '未知测试';
                      const isSuccess = item.status === 'success';
                      const displayStatus = isSuccess ? 'passed' : 'failed';
                      
                      return (
                        <div key={index} className={`p-3 rounded-lg border ${
                          isSuccess
                            ? 'bg-green-50 border-green-200'
                            : 'bg-red-50 border-red-200'
                        }`}>
                          <div className="flex items-center justify-between">
                            <span className="text-sm font-medium text-gray-900">
                              {caseName}
                            </span>
                            <div className="flex items-center space-x-2">
                              <span className="text-xs text-gray-500">
                                {item.duration?.toFixed(2) || 0}s
                              </span>
                              <span className={`px-2 py-1 rounded text-xs font-medium ${
                                isSuccess
                                  ? 'bg-green-100 text-green-700'
                                  : 'bg-red-100 text-red-700'
                              }`}>
                                {isSuccess ? '✅ 通过' : '❌ 失败'}
                              </span>
                            </div>
                          </div>
                          {item.error && (
                            <div className="mt-2 text-xs text-red-600">
                              {item.error}
                            </div>
                          )}
                          {item.result && (
                            <div className="mt-2 text-xs text-gray-600">
                              {JSON.stringify(item.result)}
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>
                  </div>
                </div>
              )}

              {/* 自愈过程 */}
              {result.healing && (
                <div className="bg-white rounded-xl border border-gray-200 shadow-sm">
                  <div className="p-6 border-b border-gray-200">
                    <h3 className="text-lg font-semibold text-gray-900">🔧 自愈过程</h3>
                  </div>
                  <div className="p-6">
                  
                  {/* 统计 */}
                  <div className="grid grid-cols-2 gap-4 mb-4">
                    <div className="p-3 bg-blue-50 rounded-lg text-center">
                      <div className="text-2xl font-bold text-blue-700">
                        {result.healing.summary?.total || 0}
                      </div>
                      <div className="text-xs text-blue-600">修复次数</div>
                    </div>
                    <div className="p-3 bg-green-50 rounded-lg text-center">
                      <div className="text-2xl font-bold text-green-700">
                        {result.healing.summary?.healed || 0}
                      </div>
                      <div className="text-xs text-green-600">成功修复</div>
                    </div>
                  </div>

                  {/* 修复记录 */}
                  <div className="space-y-2">
                    {/* 修复成功的任务 */}
                    {result.healing.healed?.map((task, index) => {
                      const caseName = task.case?.name || task.case?.module || '未知测试';
                      return (
                        <div key={`healed-${index}`} className="p-3 rounded-lg border bg-green-50 border-green-200">
                          <div className="flex items-center justify-between mb-1">
                            <span className="text-sm font-medium text-gray-900">
                              {caseName}
                            </span>
                            <span className="px-2 py-1 rounded text-xs font-medium bg-green-100 text-green-700">
                              ✅ 已修复
                            </span>
                          </div>
                          {task.error && (
                            <div className="text-xs text-gray-600">
                              原因: {task.error}
                            </div>
                          )}
                          <div className="text-xs text-gray-500 mt-1">
                            重试次数: {task.retry_count || 0}
                          </div>
                        </div>
                      );
                    })}
                    
                    {/* 修复失败的任务 */}
                    {result.healing.failed?.map((task, index) => {
                      const caseName = task.case?.name || task.case?.module || '未知测试';
                      return (
                        <div key={`failed-${index}`} className="p-3 rounded-lg border bg-yellow-50 border-yellow-200">
                          <div className="flex items-center justify-between mb-1">
                            <span className="text-sm font-medium text-gray-900">
                              {caseName}
                            </span>
                            <span className="px-2 py-1 rounded text-xs font-medium bg-yellow-100 text-yellow-700">
                              ⚠️ 未修复
                            </span>
                          </div>
                          {task.error && (
                            <div className="text-xs text-red-600">
                              错误: {task.error}
                            </div>
                          )}
                          <div className="text-xs text-gray-500 mt-1">
                            重试次数: {task.retry_count || 0}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                  </div>
                </div>
              )}

              {/* 最终报告 */}
              {result.report && (
                <div className="bg-white rounded-xl border border-gray-200 shadow-sm">
                  <div className="p-6 border-b border-gray-200">
                    <h3 className="text-lg font-semibold text-gray-900">📊 最终报告</h3>
                  </div>
                  <div className="p-6">
                  
                  {/* 状态 */}
                  <div className={`p-4 rounded-lg mb-4 ${
                    result.report.summary.status === 'passed' ? 'bg-green-50 border border-green-200' :
                    result.report.summary.status === 'failed' ? 'bg-red-50 border border-red-200' :
                    result.report.summary.status === 'skipped' ? 'bg-gray-50 border border-gray-200' :
                    'bg-yellow-50 border border-yellow-200'
                  }`}>
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-lg font-bold">
                        {result.report.summary.status === 'passed' && '✅ 测试通过'}
                        {result.report.summary.status === 'failed' && '❌ 测试失败'}
                        {result.report.summary.status === 'skipped' && '⏭️ 已跳过'}
                        {result.report.summary.status === 'partial' && '⚠️ 部分通过'}
                      </span>
                      <span className="text-sm text-gray-600">
                        {result.report.summary.passed}/{result.report.summary.total}
                      </span>
                    </div>
                    
                    {result.report.summary.pass_rate !== undefined && (
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div 
                          className={`h-2 rounded-full ${
                            result.report.summary.pass_rate === 100 ? 'bg-green-500' :
                            result.report.summary.pass_rate >= 80 ? 'bg-yellow-500' :
                            'bg-red-500'
                          }`}
                          style={{ width: `${result.report.summary.pass_rate}%` }}
                        ></div>
                      </div>
                    )}
                  </div>

                  {/* AI分析 */}
                  <div className="p-4 bg-blue-50 rounded-lg border border-blue-200">
                    <div className="flex items-start space-x-2">
                      <span className="text-xl">🤖</span>
                      <div className="flex-1">
                        <div className="text-sm font-medium text-blue-900 mb-1">AI分析</div>
                        <div className="text-sm text-gray-700">
                          {result.report.ai_analysis}
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Timeline */}
                  <div className="mt-4">
                    <div className="text-sm font-medium text-gray-700 mb-2">执行时间线</div>
                    <div className="space-y-2">
                      {result.timeline?.map((step, index) => (
                        <div key={index} className="flex items-center justify-between text-sm">
                          <span className="text-gray-600">
                            {step.stage === 'agent' && '🤖 Agent'}
                            {step.stage === 'strategy' && '📋 Strategy'}
                            {step.stage === 'orchestrator' && '⚡ Orchestrator'}
                            {step.stage === 'healing' && '🔧 Healing'}
                            {step.stage === 'report' && '📊 Report'}
                          </span>
                          <span className="text-gray-900 font-medium">{step.duration}s</span>
                        </div>
                      ))}
                      <div className="flex items-center justify-between text-sm pt-2 border-t border-gray-200">
                        <span className="text-gray-900 font-semibold">总耗时</span>
                        <span className="text-blue-600 font-bold">
                          {result.timeline?.reduce((sum, step) => sum + (step.duration || 0), 0).toFixed(2) || 0}s
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Trace ID */}
                  <div className="mt-4 p-3 bg-gray-50 rounded-lg">
                    <div className="text-xs text-gray-500 mb-1">Trace ID</div>
                    <div className="text-sm font-mono text-gray-900">{result.trace_id}</div>
                  </div>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* 空状态 */}
          {!isRunning && !result && (
            <div className="bg-white rounded-xl border border-gray-200 shadow-sm">
              <div className="p-12 text-center">
                <div className="text-6xl mb-4">🚀</div>
                <h3 className="text-lg font-semibold text-gray-900 mb-2">准备就绪</h3>
                <p className="text-gray-600 text-sm">
                  输入需求描述，点击按钮开始执行
                </p>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* 底部说明 */}
      <div className="bg-blue-50 rounded-xl border border-blue-200">
        <div className="p-6">
          <h3 className="text-sm font-semibold text-blue-900 mb-3">💡 使用说明</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <div className="flex items-start space-x-2">
              <span className="text-blue-600 mt-0.5">•</span>
              <span className="text-sm text-blue-800">选择执行模式：快速决策(2-5秒)或完整流程(10-20秒)</span>
            </div>
            <div className="flex items-start space-x-2">
              <span className="text-blue-600 mt-0.5">•</span>
              <span className="text-sm text-blue-800">输入需求描述(必填),系统自动分析是否需要测试</span>
            </div>
            <div className="flex items-start space-x-2">
              <span className="text-blue-600 mt-0.5">•</span>
              <span className="text-sm text-blue-800">可选输入Git Diff,帮助AI更准确判断影响范围</span>
            </div>
            <div className="flex items-start space-x-2">
              <span className="text-blue-600 mt-0.5">•</span>
              <span className="text-sm text-blue-800">完整流程包含:决策→策略→执行→修复→报告</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default AiTestConsole
