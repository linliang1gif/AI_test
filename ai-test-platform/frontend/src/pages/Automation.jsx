import React, { useState, useEffect } from 'react'
import { automationAPI } from '../services/api'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import DatasetSelector from '../components/DatasetSelector'
import { 
  Code, 
  Download, 
  Play, 
  RefreshCw, 
  FileText,
  CheckCircle,
  Clock,
  AlertCircle
} from 'lucide-react'

export default function Automation() {
  const [scripts, setScripts] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [selectedScript, setSelectedScript] = useState(null)
  const [executionStatus, setExecutionStatus] = useState(null)
  const [taskId, setTaskId] = useState(null)
  const [selectedDatasetId, setSelectedDatasetId] = useState(null)

  useEffect(() => {
    automationAPI.getScripts()
      .then(data => setScripts(data.scripts || []))
      .catch(err => setError(err.message))
      .finally(() => setLoading(false))
  }, [])

  const handleRunScript = (script) => {
    console.log('运行脚本:', script)
    const url = `/api/automation/scripts/${script.id}/execute`
    
    // 设置初始状态
    setExecutionStatus({
      status: 'starting',
      message: '正在启动脚本执行...',
      scriptName: script.name,
      progress: 0
    })
    
    fetch(url, { 
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      }
    })
      .then(r => {
        console.log('响应状态:', r.status)
        if (!r.ok) {
          throw new Error(`HTTP ${r.status}`)
        }
        return r.json()
      })
      .then(data => {
        console.log('执行响应:', data)
        if (data.success) {
          setTaskId(data.taskId)
          setExecutionStatus({
            status: 'running',
            message: data.message,
            scriptName: script.name,
            taskId: data.taskId,
            progress: 0
          })
          
          // 开始轮询任务状态
          pollTaskStatus(data.taskId)
          
          // 刷新脚本列表
          automationAPI.getScripts()
            .then(d => setScripts(d.scripts || []))
            .catch(() => {})
        } else {
          setExecutionStatus({
            status: 'failed',
            message: data.error || '执行失败',
            scriptName: script.name
          })
        }
      })
      .catch(err => {
        console.error('执行错误:', err)
        setExecutionStatus({
          status: 'failed',
          message: err.message,
          scriptName: script.name
        })
      })
  }
  
  // 新增: 轮询任务状态
  const pollTaskStatus = (taskId) => {
    const checkStatus = () => {
      fetch(`/api/tasks/${taskId}/status`)
        .then(r => r.json())
        .then(data => {
          console.log('任务状态:', data)
          
          setExecutionStatus(prev => ({
            ...prev,
            status: data.status,
            progress: data.progress || 0,
            currentStep: data.current_step,
            result: data.result
          }))
          
          // 如果任务还在运行,继续轮询
          if (data.status === 'running') {
            setTimeout(checkStatus, 2000) // 每2秒查询一次
          } else if (data.status === 'completed') {
            // 任务完成,刷新脚本列表
            setTimeout(() => {
              automationAPI.getScripts()
                .then(d => setScripts(d.scripts || []))
                .catch(() => {})
            }, 1000)
          }
        })
        .catch(err => {
          console.error('查询状态失败:', err)
        })
    }
    
    checkStatus()
  }

  const handleDownloadScript = (script) => {
    console.log('下载脚本:', script)
    const url = `/api/automation/scripts/${script.id}/download`
    window.open(url, '_blank')
  }

  const handleGenerateScript = () => {
    const framework = document.getElementById('gen-framework')?.value || 'pytest'
    const language = document.getElementById('gen-language')?.value || 'Python'
    const testType = document.getElementById('gen-type')?.value || 'API Tests'
    
    console.log('生成脚本参数:', { framework, language, testType, datasetId: selectedDatasetId })
    
    fetch('/api/ai/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ 
        type: 'automation_script', 
        framework, 
        language, 
        test_type: testType,
        dataset_id: selectedDatasetId  // 包含数据集ID
      })
    })
      .then(r => {
        console.log('生成响应状态:', r.status)
        if (!r.ok) {
          throw new Error(`HTTP ${r.status}`)
        }
        return r.json()
      })
      .then(data => {
        console.log('生成响应:', data)
        if (data.success) {
          const message = selectedDatasetId 
            ? `✅ ${data.message}\n任务ID: ${data.taskId}\n\n脚本已包含测试数据生成代码\n请稍等3-5秒后刷新查看新脚本`
            : `✅ ${data.message}\n任务ID: ${data.taskId}\n\n请稍等3-5秒后刷新查看新脚本`
          alert(message)
          // 延迟刷新,等待脚本生成完成
          setTimeout(() => {
            automationAPI.getScripts()
              .then(d => {
                setScripts(d.scripts || [])
                console.log('脚本列表已刷新')
              })
              .catch(() => {})
          }, 5000)
        } else {
          alert(`❌ 生成失败: ${data.error || '未知错误'}`)
        }
      })
      .catch(err => {
        console.error('生成错误:', err)
        alert(`❌ 生成失败: ${err.message}`)
      })
  }

  const getStatusIcon = (status) => {
    switch (status) {
      case 'ready': return <CheckCircle className="w-4 h-4 text-green-500" />
      case 'running': return <Clock className="w-4 h-4 text-orange-500 animate-spin" />
      case 'failed': return <AlertCircle className="w-4 h-4 text-red-500" />
      default: return <Clock className="w-4 h-4 text-gray-500" />
    }
  }

  const getStatusColor = (status) => {
    switch (status) {
      case 'ready': return 'bg-green-100 text-green-800'
      case 'running': return 'bg-orange-100 text-orange-800'
      case 'failed': return 'bg-red-100 text-red-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  const sampleCode = `import pytest
import requests
from datetime import datetime

class TestUserAuthentication:
    """AI-generated test suite for user authentication"""
    
    def setup_method(self):
        self.base_url = "https://api.example.com"
        self.headers = {"Content-Type": "application/json"}
    
    def test_valid_login(self):
        """Test successful user login with valid credentials"""
        payload = {
            "username": "testuser@example.com",
            "password": "validpassword123"
        }
        
        response = requests.post(
            f"{self.base_url}/auth/login",
            json=payload,
            headers=self.headers
        )
        
        assert response.status_code == 200
        assert "access_token" in response.json()
        assert response.json()["user"]["email"] == payload["username"]
    
    def test_invalid_password(self):
        """Test login failure with invalid password"""
        payload = {
            "username": "testuser@example.com", 
            "password": "wrongpassword"
        }
        
        response = requests.post(
            f"{self.base_url}/auth/login",
            json=payload,
            headers=self.headers
        )
        
        assert response.status_code == 401
        assert "error" in response.json()
        assert "Invalid credentials" in response.json()["error"]`

  const ScriptCard = ({ script }) => (
    <Card 
      className={`cursor-pointer transition-all hover:shadow-md ${
        selectedScript?.id === script.id ? 'ring-2 ring-blue-500' : ''
      }`}
      onClick={() => setSelectedScript(script)}
    >
      <CardContent className="p-4">
        <div className="flex items-start justify-between mb-3">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-blue-100 rounded-lg">
              <Code className="w-5 h-5 text-blue-600" />
            </div>
            <div>
              <h3 className="font-medium text-gray-900">{script.name}</h3>
              <p className="text-sm text-gray-600">{script.description}</p>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            {getStatusIcon(script.status)}
            <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(script.status)}`}>
              {script.status}
            </span>
          </div>
        </div>
        
        <div className="grid grid-cols-3 gap-4 text-center text-sm">
          <div>
            <p className="font-medium text-gray-900">{script.testCount}</p>
            <p className="text-gray-500">测试数</p>
          </div>
          <div>
            <p className="font-medium text-gray-900">{script.framework}</p>
            <p className="text-gray-500">框架</p>
          </div>
          <div>
            <p className="font-medium text-gray-900">{script.language}</p>
            <p className="text-gray-500">语言</p>
          </div>
        </div>
        
        <div className="flex items-center justify-between mt-4 pt-3 border-t">
          <span className="text-xs text-gray-500">生成时间: {script.lastGenerated}</span>
          <div className="flex space-x-1">
            <Button size="sm" variant="outline" onClick={(e) => { e.stopPropagation(); handleRunScript(script) }}>
              <Play className="w-3 h-3" />
            </Button>
            <Button size="sm" variant="outline" onClick={(e) => { e.stopPropagation(); handleDownloadScript(script) }}>
              <Download className="w-3 h-3" />
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  )

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">自动化脚本</h1>
          <p className="text-gray-600">AI生成的测试自动化脚本</p>
        </div>
        <Button className="bg-blue-600 hover:bg-blue-700" onClick={() => {
          automationAPI.getScripts().then(d => setScripts(d.scripts || [])).catch(() => {})
        }}>
          <RefreshCw className="w-4 h-4 mr-2" />
          重新生成脚本
        </Button>
      </div>

      {loading && <p className="text-gray-500 text-sm">加载中...</p>}
      {error && <div className="p-3 bg-red-50 text-red-600 rounded-md text-sm">加载失败: {error}</div>}

      {/* Execution Status Panel */}
      {executionStatus && (
        <Card className="border-2 border-blue-500">
          <CardHeader className="bg-blue-50">
            <CardTitle className="flex items-center justify-between">
              <span>执行状态</span>
              <button 
                onClick={() => setExecutionStatus(null)}
                className="text-gray-500 hover:text-gray-700"
              >
                ✕
              </button>
            </CardTitle>
          </CardHeader>
          <CardContent className="p-4">
            <div className="space-y-4">
              {/* 脚本名称 */}
              <div>
                <p className="text-sm text-gray-600">脚本名称</p>
                <p className="font-medium">{executionStatus.scriptName}</p>
              </div>

              {/* 状态 */}
              <div>
                <p className="text-sm text-gray-600">状态</p>
                <div className="flex items-center space-x-2 mt-1">
                  {executionStatus.status === 'running' && (
                    <Clock className="w-5 h-5 text-orange-500 animate-spin" />
                  )}
                  {executionStatus.status === 'completed' && (
                    <CheckCircle className="w-5 h-5 text-green-500" />
                  )}
                  {executionStatus.status === 'failed' && (
                    <AlertCircle className="w-5 h-5 text-red-500" />
                  )}
                  <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                    executionStatus.status === 'running' ? 'bg-orange-100 text-orange-800' :
                    executionStatus.status === 'completed' ? 'bg-green-100 text-green-800' :
                    executionStatus.status === 'failed' ? 'bg-red-100 text-red-800' :
                    'bg-gray-100 text-gray-800'
                  }`}>
                    {executionStatus.status === 'running' ? '运行中' :
                     executionStatus.status === 'completed' ? '已完成' :
                     executionStatus.status === 'failed' ? '失败' :
                     executionStatus.status}
                  </span>
                </div>
              </div>

              {/* 进度条 */}
              {executionStatus.progress !== undefined && (
                <div>
                  <div className="flex justify-between text-sm text-gray-600 mb-1">
                    <span>进度</span>
                    <span>{executionStatus.progress}%</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div 
                      className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                      style={{ width: `${executionStatus.progress}%` }}
                    ></div>
                  </div>
                </div>
              )}

              {/* 当前步骤 */}
              {executionStatus.currentStep && (
                <div>
                  <p className="text-sm text-gray-600">当前步骤</p>
                  <p className="font-medium">{executionStatus.currentStep}</p>
                </div>
              )}

              {/* 消息 */}
              {executionStatus.message && (
                <div>
                  <p className="text-sm text-gray-600">消息</p>
                  <p className="text-sm">{executionStatus.message}</p>
                </div>
              )}

              {/* 执行结果 */}
              {executionStatus.result && (
                <div className="mt-4 p-4 bg-gray-50 rounded-lg">
                  <p className="text-sm font-medium text-gray-700 mb-2">执行结果</p>
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <p className="text-gray-600">总测试数</p>
                      <p className="text-lg font-bold">{executionStatus.result.total_tests}</p>
                    </div>
                    <div>
                      <p className="text-gray-600">通过</p>
                      <p className="text-lg font-bold text-green-600">{executionStatus.result.passed}</p>
                    </div>
                    <div>
                      <p className="text-gray-600">失败</p>
                      <p className="text-lg font-bold text-red-600">{executionStatus.result.failed}</p>
                    </div>
                    <div>
                      <p className="text-gray-600">耗时</p>
                      <p className="text-lg font-bold">{executionStatus.result.duration}</p>
                    </div>
                  </div>
                </div>
              )}

              {/* 任务ID */}
              {executionStatus.taskId && (
                <div className="text-xs text-gray-500">
                  任务ID: {executionStatus.taskId}
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4 text-center">
            <p className="text-2xl font-bold text-blue-600">{scripts.length}</p>
            <p className="text-sm text-gray-600">脚本总数</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <p className="text-2xl font-bold text-green-600">
              {scripts.filter(s => s.status === 'ready').length}
            </p>
            <p className="text-sm text-gray-600">就绪</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <p className="text-2xl font-bold text-orange-600">
              {scripts.filter(s => s.status === 'running').length}
            </p>
            <p className="text-sm text-gray-600">运行中</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <p className="text-2xl font-bold text-purple-600">
              {scripts.reduce((sum, s) => sum + s.testCount, 0)}
            </p>
            <p className="text-sm text-gray-600">测试总数</p>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Scripts List */}
        <div className="lg:col-span-2 space-y-4">
          <h2 className="text-xl font-semibold">生成的脚本</h2>
          <div className="space-y-4">
            {scripts.map((script) => (
              <ScriptCard key={script.id} script={script} />
            ))}
          </div>
        </div>

        {/* Script Details */}
        <div className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>脚本预览</CardTitle>
            </CardHeader>
            <CardContent>
              {selectedScript ? (
                <div className="space-y-4">
                  <div>
                    <h3 className="font-medium mb-2">{selectedScript.name}</h3>
                    <p className="text-sm text-gray-600 mb-4">{selectedScript.description}</p>
                    
                    <div className="bg-gray-900 rounded-lg p-4 overflow-x-auto">
                      <pre className="text-sm text-gray-300">
                        <code>{sampleCode}</code>
                      </pre>
                    </div>
                  </div>
                  
                  <div className="space-y-2">
                    <Button className="w-full" onClick={() => handleRunScript(selectedScript)}>
                      <Play className="w-4 h-4 mr-2" />
                      运行脚本
                    </Button>
                    <Button variant="outline" className="w-full" onClick={() => handleDownloadScript(selectedScript)}>
                      <Download className="w-4 h-4 mr-2" />
                      下载
                    </Button>
                    <Button variant="outline" className="w-full" onClick={() => alert('代码编辑功能暂未实现')}>
                      <Code className="w-4 h-4 mr-2" />
                      编辑代码
                    </Button>
                  </div>
                </div>
              ) : (
                <div className="text-center py-8">
                  <Code className="w-12 h-12 text-gray-400 mx-auto mb-3" />
                  <p className="text-gray-500">选择一个脚本查看代码</p>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Generation Settings */}
          <Card>
            <CardHeader>
              <CardTitle>生成设置</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  测试框架
                </label>
                <select id="gen-framework" className="w-full px-3 py-2 border border-gray-300 rounded-md">
                  <option>pytest</option>
                  <option>unittest</option>
                  <option>selenium</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  编程语言
                </label>
                <select id="gen-language" className="w-full px-3 py-2 border border-gray-300 rounded-md">
                  <option>Python</option>
                  <option>JavaScript</option>
                  <option>Java</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  测试类型
                </label>
                <select id="gen-type" className="w-full px-3 py-2 border border-gray-300 rounded-md">
                  <option>API Tests</option>
                  <option>UI Tests</option>
                  <option>Integration Tests</option>
                </select>
              </div>
              
              {/* 数据集选择器 */}
              <div className="pt-3 border-t">
                <DatasetSelector 
                  selectedDatasetId={selectedDatasetId}
                  onSelect={setSelectedDatasetId}
                />
              </div>
              
              <Button className="w-full" onClick={handleGenerateScript}>
                <RefreshCw className="w-4 h-4 mr-2" />
                生成新脚本
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}