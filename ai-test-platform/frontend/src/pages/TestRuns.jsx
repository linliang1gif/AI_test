import React, { useState, useEffect } from 'react'
import { testRunsAPI } from '../services/api'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { 
  Play, 
  Pause, 
  Square, 
  Clock, 
  CheckCircle,
  XCircle,
  AlertTriangle,
  BarChart3,
  Eye
} from 'lucide-react'

export default function TestRuns() {
  const [testRuns, setTestRuns] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [selectedRun, setSelectedRun] = useState(null)
  const [realTimeLogs, setRealTimeLogs] = useState([])
  const [pollingInterval, setPollingInterval] = useState(null)

  useEffect(() => {
    loadTestRuns()
  }, [])
  
  // 轮询正在运行的测试
  useEffect(() => {
    // 过滤掉undefined和null,只保留有效的运行中测试
    const runningRuns = testRuns.filter(r => r && r.status === 'running')
    
    if (runningRuns.length > 0) {
      // 开始轮询
      const interval = setInterval(() => {
        runningRuns.forEach(run => {
          if (run && run.id) {
            testRunsAPI.getStatus(run.id)
              .then(data => {
                const updatedRun = data.testRun
                if (updatedRun) {
                  setTestRuns(prev => prev.map(r => (r && r.id === updatedRun.id) ? updatedRun : r))
                  
                  // 更新选中的运行
                  if (selectedRun && selectedRun.id === updatedRun.id) {
                    setSelectedRun(updatedRun)
                    setRealTimeLogs(updatedRun.logs || [])
                  }
                }
              })
              .catch(err => console.error('轮询状态失败:', err))
          }
        })
      }, 2000) // 每2秒轮询一次
      
      setPollingInterval(interval)
      
      return () => clearInterval(interval)
    } else {
      // 没有运行中的测试,清除轮询
      if (pollingInterval) {
        clearInterval(pollingInterval)
        setPollingInterval(null)
      }
    }
  }, [testRuns, selectedRun])
  
  const loadTestRuns = () => {
    testRunsAPI.getAll()
      .then(data => {
        const runs = data.testRuns || []
        setTestRuns(runs)
        if (runs.length > 0 && !selectedRun) setSelectedRun(runs[0])
      })
      .catch(err => setError(err.message))
      .finally(() => setLoading(false))
  }

  const handleRunNew = () => {
    testRunsAPI.start({ environment: 'staging' })
      .then(data => {
        const newRun = data.testRun || data
        setTestRuns(prev => [newRun, ...prev])
        setSelectedRun(newRun)
        // 立即开始轮询
        loadTestRuns()
      })
      .catch(err => alert('启动失败: ' + err.message))
  }

  const handleRestart = (run) => {
    testRunsAPI.start({ 
      environment: run.environment || 'staging',
      project_id: run.project_id,
      test_case_ids: run.test_case_ids
    })
      .then(data => {
        const newRun = data.testRun || data
        setTestRuns(prev => [newRun, ...prev])
        setSelectedRun(newRun)
        loadTestRuns()
      })
      .catch(err => alert('重启失败: ' + err.message))
  }

  const handleViewDetails = (run) => {
    testRunsAPI.getStatus(run.id)
      .then(data => {
        const details = JSON.stringify(data.testRun, null, 2)
        alert(details)
      })
      .catch(err => alert('获取详情失败: ' + err.message))
  }

  const getStatusIcon = (status) => {
    switch (status) {
      case 'running': return <Clock className="w-4 h-4 text-orange-500 animate-spin" />
      case 'completed': return <CheckCircle className="w-4 h-4 text-green-500" />
      case 'failed': return <XCircle className="w-4 h-4 text-red-500" />
      case 'paused': return <Pause className="w-4 h-4 text-yellow-500" />
      default: return <Clock className="w-4 h-4 text-gray-500" />
    }
  }

  const getStatusColor = (status) => {
    switch (status) {
      case 'running': return 'bg-orange-100 text-orange-800'
      case 'completed': return 'bg-green-100 text-green-800'
      case 'failed': return 'bg-red-100 text-red-800'
      case 'paused': return 'bg-yellow-100 text-yellow-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  const getEnvironmentColor = (env) => {
    switch (env) {
      case 'production': return 'bg-red-100 text-red-800'
      case 'staging': return 'bg-yellow-100 text-yellow-800'
      case 'development': return 'bg-green-100 text-green-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  const getLogLevelColor = (level) => {
    switch (level) {
      case 'PASS': return 'text-green-600'
      case 'FAIL': return 'text-red-600'
      case 'INFO': return 'text-blue-600'
      case 'WARN': return 'text-yellow-600'
      default: return 'text-gray-600'
    }
  }

  const TestRunCard = ({ run }) => (
    <Card 
      className={`cursor-pointer transition-all hover:shadow-md ${
        selectedRun?.id === run.id ? 'ring-2 ring-blue-500' : ''
      }`}
      onClick={() => setSelectedRun(run)}
    >
      <CardContent className="p-4">
        <div className="flex items-start justify-between mb-3">
          <div>
            <h3 className="font-medium text-gray-900">{run.name}</h3>
            <div className="flex items-center space-x-2 mt-1">
              {getStatusIcon(run.status)}
              <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(run.status)}`}>
                {run.status}
              </span>
              <span className={`px-2 py-1 rounded-full text-xs font-medium ${getEnvironmentColor(run.environment)}`}>
                {run.environment}
              </span>
            </div>
          </div>
          <div className="text-right text-sm text-gray-600">
            <p>{run.duration}</p>
            <p>{run.startTime}</p>
          </div>
        </div>
        
        {/* Progress Bar */}
        <div className="mb-3">
          <div className="flex items-center justify-between text-sm mb-1">
            <span>进度</span>
            <span>{run.progress}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div 
              className="bg-blue-600 h-2 rounded-full transition-all duration-300"
              style={{ width: `${run.progress}%` }}
            ></div>
          </div>
        </div>
        
        {/* Test Results */}
        <div className="grid grid-cols-4 gap-2 text-center text-sm">
          <div>
            <p className="font-medium text-gray-900">{run.totalTests}</p>
            <p className="text-gray-500">总计</p>
          </div>
          <div>
            <p className="font-medium text-green-600">{run.passed}</p>
            <p className="text-gray-500">通过</p>
          </div>
          <div>
            <p className="font-medium text-red-600">{run.failed}</p>
            <p className="text-gray-500">失败</p>
          </div>
          <div>
            <p className="font-medium text-yellow-600">{run.pending}</p>
            <p className="text-gray-500">待运行</p>
          </div>
        </div>
        
        {/* V3 新增: 并发任务状态展示 */}
        {run.tasks && run.tasks.length > 0 && (
          <div className="mt-3 pt-3 border-t border-gray-200">
            <div className="text-xs text-gray-600 mb-2">并发任务状态:</div>
            <div className="space-y-1">
              {run.tasks.slice(-3).map((task) => (
                <div key={task.task_id} className="flex items-center justify-between text-xs">
                  <div className="flex items-center space-x-2 flex-1 min-w-0">
                    {task.status === 'running' && <Clock className="w-3 h-3 text-orange-500 animate-spin flex-shrink-0" />}
                    {task.status === 'success' && <CheckCircle className="w-3 h-3 text-green-500 flex-shrink-0" />}
                    {task.status === 'failed' && <XCircle className="w-3 h-3 text-red-500 flex-shrink-0" />}
                    <span className="truncate">{task.name}</span>
                  </div>
                  <span className="text-gray-500 ml-2 flex-shrink-0">
                    {task.duration > 0 ? `${task.duration}s` : '...'}
                  </span>
                </div>
              ))}
              {run.tasks.length > 3 && (
                <div className="text-center text-gray-400">
                  +{run.tasks.length - 3} 更多任务
                </div>
              )}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">测试运行</h1>
          <p className="text-gray-600">监控和管理测试执行</p>
        </div>
        <div className="flex space-x-2">
          <Button variant="outline" onClick={() => window.location.href = '/reports'}>
            <BarChart3 className="w-4 h-4 mr-2" />
            查看报告
          </Button>
          <Button className="bg-green-600 hover:bg-green-700" onClick={handleRunNew}>
            <Play className="w-4 h-4 mr-2" />
            运行新测试
          </Button>
        </div>
      </div>

      {loading && <p className="text-gray-500 text-sm">加载中...</p>}
      {error && <div className="p-3 bg-red-50 text-red-600 rounded-md text-sm">加载失败: {error}</div>}
      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4 text-center">
            <p className="text-2xl font-bold text-blue-600">{testRuns.filter(r => r).length}</p>
            <p className="text-sm text-gray-600">活跃运行</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <p className="text-2xl font-bold text-orange-600">
              {testRuns.filter(r => r && r.status === 'running').length}
            </p>
            <p className="text-sm text-gray-600">运行中</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <p className="text-2xl font-bold text-green-600">
              {testRuns.filter(r => r && r.status === 'completed').length}
            </p>
            <p className="text-sm text-gray-600">已完成</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <p className="text-2xl font-bold text-red-600">
              {testRuns.filter(r => r && r.status === 'failed').length}
            </p>
            <p className="text-sm text-gray-600">失败</p>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Test Runs List */}
        <div className="lg:col-span-2 space-y-4">
          <h2 className="text-xl font-semibold">最近的测试运行</h2>
          <div className="space-y-4">
            {testRuns.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                暂无测试运行记录,点击右上角"运行新测试"开始
              </div>
            ) : (
              testRuns.filter(run => run).map((run) => (
                <TestRunCard key={run.id} run={run} />
              ))
            )}
          </div>
        </div>

        {/* Real-time Details */}
        <div className="space-y-4">
          {/* Run Controls */}
          <Card>
            <CardHeader>
              <CardTitle>运行控制</CardTitle>
            </CardHeader>
            <CardContent>
              {selectedRun && (
                <div className="space-y-4">
                  <div>
                    <h3 className="font-medium mb-2">{selectedRun.name}</h3>
                    <div className="flex items-center space-x-2">
                      {getStatusIcon(selectedRun.status)}
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(selectedRun.status)}`}>
                        {selectedRun.status}
                      </span>
                    </div>
                  </div>
                  
                  <div className="space-y-2">
                    {selectedRun.status === 'running' ? (
                      <>
                        <Button variant="outline" className="w-full" onClick={() => alert('暂停功能暂未实现')}>
                          <Pause className="w-4 h-4 mr-2" />
                          暂停
                        </Button>
                        <Button variant="outline" className="w-full text-red-600" onClick={() => alert('停止功能暂未实现')}>
                          <Square className="w-4 h-4 mr-2" />
                          停止
                        </Button>
                      </>
                    ) : (
                      <Button className="w-full" onClick={() => handleRestart(selectedRun)}>
                        <Play className="w-4 h-4 mr-2" />
                        重新运行
                      </Button>
                    )}
                    <Button variant="outline" className="w-full" onClick={() => handleViewDetails(selectedRun)}>
                      <Eye className="w-4 h-4 mr-2" />
                      查看详情
                    </Button>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Real-time Logs */}
          <Card>
            <CardHeader>
              <CardTitle>实时日志</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="bg-gray-900 rounded-lg p-4 h-64 overflow-y-auto">
                {realTimeLogs.length > 0 ? (
                  <div className="space-y-1 font-mono text-sm">
                    {realTimeLogs.map((log, index) => (
                      <div key={index} className="flex space-x-2">
                        <span className="text-gray-400">{log.time}</span>
                        <span className={`font-medium ${getLogLevelColor(log.level)}`}>
                          [{log.level}]
                        </span>
                        <span className="text-gray-300">{log.message}</span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-gray-500 text-center py-8">
                    {selectedRun && selectedRun.status === 'running' ? '等待日志...' : '暂无日志'}
                  </div>
                )}
              </div>
            </CardContent>
          </Card>

          {/* Test Progress */}
          {selectedRun && (
            <Card>
              <CardHeader>
                <CardTitle>测试进度</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div>
                    <div className="flex items-center justify-between text-sm mb-2">
                      <span>总体进度</span>
                      <span>{selectedRun.progress}%</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-3">
                      <div 
                        className="bg-blue-600 h-3 rounded-full transition-all duration-300"
                        style={{ width: `${selectedRun.progress}%` }}
                      ></div>
                    </div>
                  </div>
                  
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div className="text-center p-2 bg-green-50 rounded">
                      <p className="font-medium text-green-800">{selectedRun.passed}</p>
                      <p className="text-green-600">通过</p>
                    </div>
                    <div className="text-center p-2 bg-red-50 rounded">
                      <p className="font-medium text-red-800">{selectedRun.failed}</p>
                      <p className="text-red-600">失败</p>
                    </div>
                  </div>
                  
                  <div className="text-center">
                    <p className="text-sm text-gray-600">
                      持续时间: {selectedRun.duration}
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}
          
          {/* V3 新增: 并发任务详细列表 */}
          {selectedRun && selectedRun.tasks && selectedRun.tasks.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>并发任务列表</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2 max-h-64 overflow-y-auto">
                  {selectedRun.tasks.map((task) => (
                    <div 
                      key={task.task_id} 
                      className="flex items-center justify-between p-2 bg-gray-50 rounded hover:bg-gray-100 transition-colors"
                    >
                      <div className="flex items-center space-x-2 flex-1 min-w-0">
                        {task.status === 'running' && (
                          <Clock className="w-4 h-4 text-orange-500 animate-spin flex-shrink-0" />
                        )}
                        {task.status === 'success' && (
                          <CheckCircle className="w-4 h-4 text-green-500 flex-shrink-0" />
                        )}
                        {task.status === 'failed' && (
                          <XCircle className="w-4 h-4 text-red-500 flex-shrink-0" />
                        )}
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium truncate">{task.name}</p>
                          <p className="text-xs text-gray-500">{task.task_id}</p>
                        </div>
                      </div>
                      <div className="text-right ml-2 flex-shrink-0">
                        <span className={`px-2 py-1 rounded text-xs font-medium ${
                          task.status === 'running' ? 'bg-orange-100 text-orange-800' :
                          task.status === 'success' ? 'bg-green-100 text-green-800' :
                          'bg-red-100 text-red-800'
                        }`}>
                          {task.status === 'running' ? 'Running' :
                           task.status === 'success' ? 'Success' :
                           'Failed'}
                        </span>
                        {task.duration > 0 && (
                          <p className="text-xs text-gray-500 mt-1">{task.duration}s</p>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  )
}