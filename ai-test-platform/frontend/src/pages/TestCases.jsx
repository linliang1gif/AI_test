import { useState, useEffect } from 'react'
import api from '../services/api'

export default function TestCases() {
  const [showUploadDialog, setShowUploadDialog] = useState(false)
  const [uploadFile, setUploadFile] = useState(null)
  const [isGenerating, setIsGenerating] = useState(false)
  const [testCases, setTestCases] = useState([])
  const [loading, setLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedTestCase, setSelectedTestCase] = useState(null)
  const [showDetailDialog, setShowDetailDialog] = useState(false)
  const [showDatasetDialog, setShowDatasetDialog] = useState(false)
  const [datasets, setDatasets] = useState([])
  const [selectedDataset, setSelectedDataset] = useState(null)
  const [generationProgress, setGenerationProgress] = useState(0)
  const [generationStep, setGenerationStep] = useState('')
  const [selectedIds, setSelectedIds] = useState([])
  const [isDeleting, setIsDeleting] = useState(false)
  const [showScriptDialog, setShowScriptDialog] = useState(false)
  const [generatedScript, setGeneratedScript] = useState('')
  const [isGeneratingScript, setIsGeneratingScript] = useState(false)
  const [isExecuting, setIsExecuting] = useState(false)
  const [executionResult, setExecutionResult] = useState(null)
  const [showResultDialog, setShowResultDialog] = useState(false)
  const [showManualTestDialog, setShowManualTestDialog] = useState(false)
  const [manualTestSteps, setManualTestSteps] = useState([])
  const [currentStepIndex, setCurrentStepIndex] = useState(0)
  const [manualTestNotes, setManualTestNotes] = useState('')

  useEffect(() => {
    loadTestCases()
    loadDatasets()
  }, [])

  const loadTestCases = async () => {
    try {
      const result = await api.testCases.getAll()
      setTestCases(result.data || [])
    } catch (error) {
      console.error('加载测试用例失败:', error)
    } finally {
      setLoading(false)
    }
  }

  const loadDatasets = async () => {
    try {
      const response = await fetch('/api/test-data/datasets')
      const result = await response.json()
      setDatasets(result.datasets || [])
    } catch (error) {
      console.error('加载数据集失败:', error)
    }
  }

  const handleFileUpload = async () => {
    if (!uploadFile) return
    
    setIsGenerating(true)
    setGenerationProgress(0)
    setGenerationStep('准备上传文档...')
    
    const formData = new FormData()
    formData.append('file', uploadFile)

    try {
      // 模拟进度更新
      const progressInterval = setInterval(() => {
        setGenerationProgress(prev => {
          if (prev >= 90) return prev
          return prev + 2
        })
      }, 1000)

      // 更新步骤提示
      setTimeout(() => setGenerationStep('📄 解析需求文档...'), 500)
      setTimeout(() => setGenerationStep('🔍 拆分功能模块...'), 3000)
      setTimeout(() => setGenerationStep('📝 生成测试点...'), 8000)
      setTimeout(() => setGenerationStep('🎯 生成测试场景...'), 15000)
      setTimeout(() => setGenerationStep('✨ 生成测试用例...'), 25000)
      
      const response = await fetch('/api/testcases/generate', {
        method: 'POST',
        body: formData
      })
      
      clearInterval(progressInterval)
      setGenerationProgress(100)
      setGenerationStep('✅ 生成完成!')
      
      const result = await response.json()
      
      if (result.success) {
        setTimeout(() => {
          alert(`成功生成 ${result.count} 个测试用例!`)
          setShowUploadDialog(false)
          setUploadFile(null)
          setGenerationProgress(0)
          setGenerationStep('')
          
          const newTestCases = result.testCases.map(tc => ({
            id: tc.id,
            title: tc.title,
            priority: tc.priority.toLowerCase(),
            status: tc.status,
            lastRun: tc.lastRun,
            source: 'ai_generated',
            steps: tc.steps,
            expected: tc.expected,
            module: tc.module
          }))
          setTestCases(prev => [...newTestCases, ...prev])
        }, 500)
      } else {
        alert('生成失败: ' + result.error)
        setGenerationProgress(0)
        setGenerationStep('')
      }
    } catch (error) {
      alert('上传失败: ' + error.message)
      setGenerationProgress(0)
      setGenerationStep('')
    } finally {
      setIsGenerating(false)
    }
  }

  const handleViewDetail = (testCase) => {
    setSelectedTestCase(testCase)
    setShowDetailDialog(true)
  }

  const handleSelectDataset = (testCase) => {
    setSelectedTestCase(testCase)
    setShowDatasetDialog(true)
  }

  const handleBindDataset = async () => {
    if (!selectedDataset || !selectedTestCase) return

    try {
      const response = await fetch(`/api/test-cases/${selectedTestCase.id}/bind-dataset`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ dataset_id: selectedDataset })
      })

      if (response.ok) {
        alert('数据集绑定成功!')
        setShowDatasetDialog(false)
        setSelectedDataset(null)

        setTestCases(prev => prev.map(tc =>
          tc.id === selectedTestCase.id
            ? { ...tc, dataset_id: selectedDataset }
            : tc
        ))
      } else {
        alert('绑定失败')
      }
    } catch (error) {
      alert('绑定失败: ' + error.message)
    }
  }

  const handleExportExcel = async () => {
    try {
      const response = await fetch('/api/test-cases/export')
      if (response.ok) {
        const blob = await response.blob()
        const url = window.URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `测试用例_${new Date().toISOString().slice(0,10)}.xlsx`
        document.body.appendChild(a)
        a.click()
        document.body.removeChild(a)
        window.URL.revokeObjectURL(url)
      } else {
        alert('导出失败')
      }
    } catch (error) {
      alert('导出失败: ' + error.message)
    }
  }

  const sourceLabel = (src) => {
    const map = { 
      ai_generated: 'AI生成', 
      manual: '人工', 
      knowledge_base: '知识库' 
    }
    return map[src] || src || '-'
  }

  const filteredTestCases = searchQuery
    ? testCases.filter(tc =>
        (tc.title || '').toLowerCase().includes(searchQuery.toLowerCase())
      )
    : testCases

  const handleSelectAll = (e) => {
    if (e.target.checked) {
      setSelectedIds(filteredTestCases.map(tc => tc.id))
    } else {
      setSelectedIds([])
    }
  }

  const handleSelectOne = (id) => {
    setSelectedIds(prev => 
      prev.includes(id) 
        ? prev.filter(i => i !== id)
        : [...prev, id]
    )
  }

  const handleBatchDelete = async () => {
    if (selectedIds.length === 0) {
      alert('请先选择要删除的测试用例')
      return
    }

    if (!window.confirm(`确定要删除选中的 ${selectedIds.length} 个测试用例吗?`)) {
      return
    }

    setIsDeleting(true)
    try {
      const response = await fetch('/api/testcases/batch-delete', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ids: selectedIds })
      })

      const result = await response.json()
      
      if (result.success) {
        alert(`成功删除 ${result.deleted_count} 个测试用例`)
        setTestCases(prev => prev.filter(tc => !selectedIds.includes(tc.id)))
        setSelectedIds([])
      } else {
        alert('删除失败: ' + result.error)
      }
    } catch (error) {
      alert('删除失败: ' + error.message)
    } finally {
      setIsDeleting(false)
    }
  }

  const handleGenerateScript = async (testCase) => {
    setSelectedTestCase(testCase)
    setIsGeneratingScript(true)
    setShowScriptDialog(true)
    
    try {
      const response = await fetch(`/api/testcases/${testCase.id}/generate-script`, {
        method: 'POST'
      })
      const result = await response.json()
      
      if (result.success) {
        setGeneratedScript(result.script)
      } else {
        alert('脚本生成失败: ' + result.error)
        setShowScriptDialog(false)
      }
    } catch (error) {
      alert('脚本生成失败: ' + error.message)
      setShowScriptDialog(false)
    } finally {
      setIsGeneratingScript(false)
    }
  }

  const handleExecuteTest = async (testCase) => {
    if (!window.confirm(`确定要执行测试用例: ${testCase.title}?`)) {
      return
    }

    setIsExecuting(true)
    try {
      const response = await fetch(`/api/testcases/${testCase.id}/execute`, {
        method: 'POST'
      })
      const result = await response.json()
      
      if (result.success) {
        setExecutionResult(result)
        setSelectedTestCase(testCase)
        setShowResultDialog(true)
        
        // 更新测试用例状态
        setTestCases(prev => prev.map(tc => 
          tc.id === testCase.id 
            ? { ...tc, status: result.status, lastRun: new Date().toLocaleString() }
            : tc
        ))
      } else {
        alert('测试执行失败: ' + result.error)
      }
    } catch (error) {
      alert('测试执行失败: ' + error.message)
    } finally {
      setIsExecuting(false)
    }
  }

  const handleDownloadScript = () => {
    const blob = new Blob([generatedScript], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `test_${selectedTestCase.id}_${Date.now()}.py`
    a.click()
    URL.revokeObjectURL(url)
  }

  const handleManualTest = (testCase) => {
    setSelectedTestCase(testCase)
    const steps = testCase.steps || []
    setManualTestSteps(steps.map((step, index) => ({
      index: index + 1,
      description: step,
      status: 'pending', // pending, passed, failed
      note: ''
    })))
    setCurrentStepIndex(0)
    setManualTestNotes('')
    setShowManualTestDialog(true)
  }

  const handleStepResult = (index, status) => {
    setManualTestSteps(prev => prev.map((step, i) => 
      i === index ? { ...step, status } : step
    ))
    // 自动跳到下一步
    if (index < manualTestSteps.length - 1) {
      setCurrentStepIndex(index + 1)
    }
  }

  const handleStepNote = (index, note) => {
    setManualTestSteps(prev => prev.map((step, i) => 
      i === index ? { ...step, note } : step
    ))
  }

  const handleSubmitManualTest = async () => {
    // 检查是否所有步骤都已执行
    const pendingSteps = manualTestSteps.filter(s => s.status === 'pending')
    if (pendingSteps.length > 0) {
      if (!window.confirm(`还有 ${pendingSteps.length} 个步骤未执行，确定要提交吗？`)) {
        return
      }
    }

    // 计算最终状态
    const failedSteps = manualTestSteps.filter(s => s.status === 'failed')
    const finalStatus = failedSteps.length > 0 ? 'failed' : 'passed'

    try {
      const response = await fetch(`/api/testcases/${selectedTestCase.id}/manual-execute`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          steps: manualTestSteps,
          notes: manualTestNotes,
          status: finalStatus
        })
      })

      const result = await response.json()
      
      if (result.success) {
        alert(`手动测试已提交！\n状态: ${finalStatus === 'passed' ? '通过' : '失败'}`)
        
        // 更新测试用例状态
        setTestCases(prev => prev.map(tc => 
          tc.id === selectedTestCase.id 
            ? { ...tc, status: finalStatus, lastRun: new Date().toLocaleString() }
            : tc
        ))
        
        setShowManualTestDialog(false)
      } else {
        alert('提交失败: ' + result.error)
      }
    } catch (error) {
      alert('提交失败: ' + error.message)
    }
  }

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">📝 测试用例</h1>
          <p className="text-gray-600 mt-1">管理和生成测试用例</p>
        </div>
        <div className="flex space-x-3">
          {selectedIds.length > 0 && (
            <button
              onClick={handleBatchDelete}
              disabled={isDeleting}
              className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 flex items-center space-x-2 transition-colors disabled:opacity-50"
            >
              <span>🗑️</span>
              <span>{isDeleting ? '删除中...' : `删除 (${selectedIds.length})`}</span>
            </button>
          )}
          <button
            onClick={handleExportExcel}
            className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 flex items-center space-x-2 transition-colors"
          >
            <span>📥</span>
            <span>导出Excel</span>
          </button>
          <button
            onClick={() => setShowUploadDialog(true)}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center space-x-2 transition-colors"
          >
            <span>📄</span>
            <span>导入需求文档</span>
          </button>
        </div>
      </div>
      
      <div className="bg-white rounded-lg shadow">
        <div className="p-6 border-b">
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="搜索测试用例..."
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
        
        <div className="p-6">
          {loading ? (
            <div className="flex items-center justify-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
              <span className="ml-2 text-gray-500">加载中...</span>
            </div>
          ) : (
            <table className="w-full">
              <thead>
                <tr className="border-b">
                  <th className="py-3 px-4 text-gray-600 font-medium w-12">
                    <input
                      type="checkbox"
                      checked={filteredTestCases.length > 0 && selectedIds.length === filteredTestCases.length}
                      onChange={handleSelectAll}
                      className="w-4 h-4 text-blue-600 rounded focus:ring-2 focus:ring-blue-500"
                    />
                  </th>
                  <th className="text-left py-3 px-4 text-gray-600 font-medium">用例名称</th>
                  <th className="text-left py-3 px-4 text-gray-600 font-medium">模块</th>
                  <th className="text-left py-3 px-4 text-gray-600 font-medium">优先级</th>
                  <th className="text-left py-3 px-4 text-gray-600 font-medium">来源</th>
                  <th className="text-left py-3 px-4 text-gray-600 font-medium">状态</th>
                  <th className="text-left py-3 px-4 text-gray-600 font-medium">最后运行</th>
                  <th className="text-left py-3 px-4 text-gray-600 font-medium">操作</th>
                </tr>
              </thead>
              <tbody>
                {filteredTestCases.length === 0 ? (
                  <tr>
                    <td colSpan={8} className="py-8 text-center text-gray-500">
                      {searchQuery ? '未找到匹配的测试用例' : '暂无测试用例，请导入需求文档生成'}
                    </td>
                  </tr>
                ) : filteredTestCases.map((tc, index) => {
                  const priorityMap = { 
                    high: { cls: 'bg-red-100 text-red-700', label: '高' }, 
                    medium: { cls: 'bg-yellow-100 text-yellow-700', label: '中' }, 
                    low: { cls: 'bg-green-100 text-green-700', label: '低' } 
                  }
                  const statusMap = { 
                    passed: { cls: 'bg-green-100 text-green-700', label: '通过' }, 
                    failed: { cls: 'bg-red-100 text-red-700', label: '失败' }, 
                    pending: { cls: 'bg-gray-100 text-gray-700', label: '待运行' } 
                  }
                  const p = priorityMap[tc.priority] || { cls: 'bg-gray-100 text-gray-700', label: tc.priority || '-' }
                  const s = statusMap[tc.status] || { cls: 'bg-gray-100 text-gray-700', label: tc.status || '-' }
                  
                  // 使用组合key避免重复
                  const uniqueKey = `${tc.id}-${index}`;
                  
                  return (
                    <tr key={uniqueKey} className="border-b hover:bg-gray-50 transition-colors">
                      <td className="py-4 px-4">
                        <input
                          type="checkbox"
                          checked={selectedIds.includes(tc.id)}
                          onChange={() => handleSelectOne(tc.id)}
                          className="w-4 h-4 text-blue-600 rounded focus:ring-2 focus:ring-blue-500"
                        />
                      </td>
                      <td className="py-4 px-4 font-medium">
                        {tc.title?.replace(/^(测试用例标题|测试点|用例标题|标题)[:：]\s*/, '') || tc.title}
                      </td>
                      <td className="py-4 px-4 text-gray-600">{tc.module || '-'}</td>
                      <td className="py-4 px-4">
                        <span className={`px-2 py-1 rounded text-sm ${p.cls}`}>{p.label}</span>
                      </td>
                      <td className="py-4 px-4">
                        <span className="px-2 py-1 bg-blue-100 text-blue-700 rounded text-xs">
                          {sourceLabel(tc.source)}
                        </span>
                      </td>
                      <td className="py-4 px-4">
                        <span className={`px-2 py-1 rounded text-sm ${s.cls}`}>{s.label}</span>
                      </td>
                      <td className="py-4 px-4 text-gray-600">{tc.lastRun}</td>
                      <td className="py-4 px-4">
                        <div className="flex space-x-2">
                          <button
                            onClick={() => handleViewDetail(tc)}
                            className="px-3 py-1 bg-blue-50 text-blue-600 rounded hover:bg-blue-100 text-sm"
                          >
                            查看详情
                          </button>
                          <button
                            onClick={() => handleGenerateScript(tc)}
                            className="px-3 py-1 bg-purple-50 text-purple-600 rounded hover:bg-purple-100 text-sm flex items-center space-x-1"
                            title="生成自动化脚本"
                          >
                            <span>📝</span>
                            <span>生成脚本</span>
                          </button>
                          <button
                            onClick={() => handleExecuteTest(tc)}
                            className="px-3 py-1 bg-green-50 text-green-600 rounded hover:bg-green-100 text-sm flex items-center space-x-1"
                            title="自动化执行"
                          >
                            <span>▶️</span>
                            <span>自动执行</span>
                          </button>
                          <button
                            onClick={() => handleManualTest(tc)}
                            className="px-3 py-1 bg-indigo-50 text-indigo-600 rounded hover:bg-indigo-100 text-sm flex items-center space-x-1"
                            title="手动功能测试"
                          >
                            <span>👤</span>
                            <span>手动测试</span>
                          </button>
                          <button
                            onClick={() => handleSelectDataset(tc)}
                            className="px-3 py-1 bg-orange-50 text-orange-600 rounded hover:bg-orange-100 text-sm flex items-center space-x-1"
                            title={tc.dataset_id ? '已绑定数据集' : '绑定数据集'}
                          >
                            <span>🏭</span>
                            <span>{tc.dataset_id ? '已绑定' : '数据集'}</span>
                          </button>
                        </div>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          )}
        </div>
      </div>

      {/* 上传对话框 */}
      {showUploadDialog && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl p-6 w-[500px]">
            <h2 className="text-xl font-bold mb-4">🤖 AI生成测试用例</h2>
            
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                选择需求文档
              </label>
              <input
                type="file"
                accept=".docx,.xlsx,.pdf,.doc,.xls,.txt"
                onChange={(e) => setUploadFile(e.target.files[0])}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              {uploadFile && (
                <p className="mt-2 text-sm text-green-600 flex items-center">
                  <span className="mr-1">✓</span>
                  已选择: {uploadFile.name}
                </p>
              )}
            </div>

            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
              <div className="flex items-start space-x-2">
                <span className="text-blue-600 mt-0.5">🧠</span>
                <div className="text-sm text-blue-800">
                  <p className="font-medium mb-1">AI将自动执行以下步骤:</p>
                  <ul className="list-disc list-inside space-y-1 text-xs">
                    <li>解析需求文档内容</li>
                    <li>拆分功能模块</li>
                    <li>生成测试点和场景</li>
                    <li>生成完整测试用例</li>
                    <li>自动去重和质量评估</li>
                  </ul>
                  <p className="mt-2 text-xs text-blue-600">⏱️ 预计需要 1-2 分钟</p>
                </div>
              </div>
            </div>

            {isGenerating && (
              <div className="mb-4">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-gray-700">{generationStep}</span>
                  <span className="text-sm text-gray-500">{generationProgress}%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2.5">
                  <div 
                    className="bg-blue-600 h-2.5 rounded-full transition-all duration-500"
                    style={{ width: `${generationProgress}%` }}
                  ></div>
                </div>
                <div className="mt-2 flex items-center space-x-2 text-xs text-gray-500">
                  <div className="animate-spin rounded-full h-3 w-3 border-b-2 border-blue-600"></div>
                  <span>AI正在处理中,请稍候...</span>
                </div>
              </div>
            )}

            <div className="flex justify-end space-x-3">
              <button
                onClick={() => {
                  if (isGenerating) {
                    // 如果正在生成,提示用户
                    if (window.confirm('AI正在生成中,确定要取消吗?')) {
                      setShowUploadDialog(false)
                      setUploadFile(null)
                      setIsGenerating(false)
                      setGenerationProgress(0)
                      setGenerationStep('')
                    }
                  } else {
                    setShowUploadDialog(false)
                    setUploadFile(null)
                  }
                }}
                className={`px-4 py-2 border border-gray-300 rounded-lg transition-colors ${
                  isGenerating 
                    ? 'bg-red-50 border-red-300 text-red-700 hover:bg-red-100' 
                    : 'hover:bg-gray-50'
                }`}
              >
                {isGenerating ? '强制取消' : '取消'}
              </button>
              <button
                onClick={handleFileUpload}
                disabled={!uploadFile || isGenerating}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center space-x-2"
              >
                {isGenerating ? (
                  <>
                    <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                    <span>AI生成中...</span>
                  </>
                ) : (
                  <>
                    <span>🚀</span>
                    <span>开始生成</span>
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 数据集选择对话框 */}
      {showDatasetDialog && selectedTestCase && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl p-6 w-[600px] max-h-[80vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-bold">🏭 选择测试数据集</h2>
              <button
                onClick={() => {
                  setShowDatasetDialog(false)
                  setSelectedDataset(null)
                }}
                className="text-gray-400 hover:text-gray-600"
              >
                ✕
              </button>
            </div>
            
            <div className="mb-4 p-3 bg-blue-50 rounded border border-blue-200">
              <p className="text-sm text-blue-800">
                <span className="font-medium">测试用例:</span> {selectedTestCase.title?.replace(/^(测试用例标题|测试点|用例标题|标题)[:：]\s*/, '') || selectedTestCase.title}
              </p>
            </div>

            <div className="space-y-3 mb-6">
              {datasets.length === 0 ? (
                <div className="text-center py-8 text-gray-500">
                  <p>暂无可用数据集</p>
                  <p className="text-sm mt-2">请先在API管理中生成并保存数据集</p>
                </div>
              ) : (
                datasets.map((dataset) => (
                  <div
                    key={dataset.id}
                    onClick={() => setSelectedDataset(dataset.id)}
                    className={`p-4 border rounded-lg cursor-pointer transition-all ${
                      selectedDataset === dataset.id
                        ? 'border-blue-500 bg-blue-50'
                        : 'border-gray-200 hover:border-blue-300'
                    }`}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <h3 className="font-medium text-gray-900">{dataset.name}</h3>
                        <p className="text-sm text-gray-600 mt-1">{dataset.description || '无描述'}</p>
                        <div className="flex items-center space-x-4 mt-2 text-xs text-gray-500">
                          <span>创建时间: {new Date(dataset.created_at).toLocaleString()}</span>
                          <span>使用次数: {dataset.usage_count || 0}</span>
                        </div>
                      </div>
                      {selectedDataset === dataset.id && (
                        <div className="ml-3">
                          <span className="inline-block w-5 h-5 bg-blue-500 text-white rounded-full flex items-center justify-center text-xs">
                            ✓
                          </span>
                        </div>
                      )}
                    </div>
                  </div>
                ))
              )}
            </div>

            <div className="flex justify-end space-x-3">
              <button
                onClick={() => {
                  setShowDatasetDialog(false)
                  setSelectedDataset(null)
                }}
                className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
              >
                取消
              </button>
              <button
                onClick={handleBindDataset}
                disabled={!selectedDataset}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                绑定数据集
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 测试用例详情对话框 */}
      {showDetailDialog && selectedTestCase && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl p-6 w-[700px] max-h-[80vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-bold">测试用例详情</h2>
              <button
                onClick={() => setShowDetailDialog(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                ✕
              </button>
            </div>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">用例标题</label>
                <div className="p-3 bg-gray-50 rounded border">
                  {selectedTestCase.title?.replace(/^(测试用例标题|测试点|用例标题|标题)[:：]\s*/, '') || selectedTestCase.title}
                </div>
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">模块</label>
                  <div className="p-3 bg-gray-50 rounded border">{selectedTestCase.module || '-'}</div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">优先级</label>
                  <div className="p-3 bg-gray-50 rounded border">{selectedTestCase.priority}</div>
                </div>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">测试步骤</label>
                <div className="p-3 bg-gray-50 rounded border">
                  {selectedTestCase.steps && selectedTestCase.steps.length > 0 ? (
                    <ol className="list-decimal list-inside space-y-1">
                      {selectedTestCase.steps.map((step, index) => (
                        <li key={index} className="text-gray-700">{step}</li>
                      ))}
                    </ol>
                  ) : (
                    <p className="text-gray-500">暂无测试步骤</p>
                  )}
                </div>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">预期结果</label>
                <div className="p-3 bg-gray-50 rounded border">{selectedTestCase.expected || '-'}</div>
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">状态</label>
                  <div className="p-3 bg-gray-50 rounded border">{selectedTestCase.status}</div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">最后运行</label>
                  <div className="p-3 bg-gray-50 rounded border">{selectedTestCase.lastRun}</div>
                </div>
              </div>
            </div>
            
            <div className="mt-6 flex justify-end">
              <button
                onClick={() => setShowDetailDialog(false)}
                className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300"
              >
                关闭
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 脚本生成对话框 */}
      {showScriptDialog && selectedTestCase && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl p-6 w-[800px] max-h-[80vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-bold">📝 自动化脚本</h2>
              <button
                onClick={() => setShowScriptDialog(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                ✕
              </button>
            </div>
            
            <div className="mb-4 p-3 bg-blue-50 rounded border border-blue-200">
              <p className="text-sm text-blue-800">
                <span className="font-medium">测试用例:</span> {selectedTestCase.title?.replace(/^(测试用例标题|测试点|用例标题|标题)[:：]\s*/, '') || selectedTestCase.title}
              </p>
            </div>

            {isGeneratingScript ? (
              <div className="flex items-center justify-center py-12">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                <span className="ml-3 text-gray-600">AI正在生成脚本...</span>
              </div>
            ) : (
              <div>
                <div className="mb-4">
                  <label className="block text-sm font-medium text-gray-700 mb-2">生成的测试脚本</label>
                  <pre className="bg-gray-900 text-green-400 p-4 rounded-lg overflow-x-auto text-sm font-mono max-h-96">
                    {generatedScript || '# 脚本生成中...'}
                  </pre>
                </div>

                <div className="flex justify-end space-x-3">
                  <button
                    onClick={() => setShowScriptDialog(false)}
                    className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
                  >
                    关闭
                  </button>
                  <button
                    onClick={handleDownloadScript}
                    disabled={!generatedScript}
                    className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 flex items-center space-x-2"
                  >
                    <span>📥</span>
                    <span>下载脚本</span>
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* 测试执行结果对话框 */}
      {showResultDialog && executionResult && selectedTestCase && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl p-6 w-[700px] max-h-[80vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-bold">
                {executionResult.status === 'passed' ? '✅' : '❌'} 测试执行结果
              </h2>
              <button
                onClick={() => setShowResultDialog(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                ✕
              </button>
            </div>
            
            <div className="mb-4 p-3 bg-blue-50 rounded border border-blue-200">
              <p className="text-sm text-blue-800">
                <span className="font-medium">测试用例:</span> {selectedTestCase.title?.replace(/^(测试用例标题|测试点|用例标题|标题)[:：]\s*/, '') || selectedTestCase.title}
              </p>
            </div>

            <div className="space-y-4">
              <div className="grid grid-cols-3 gap-4">
                <div className="p-4 bg-gray-50 rounded border">
                  <div className="text-sm text-gray-600 mb-1">执行状态</div>
                  <div className={`text-lg font-bold ${executionResult.status === 'passed' ? 'text-green-600' : 'text-red-600'}`}>
                    {executionResult.status === 'passed' ? '通过' : '失败'}
                  </div>
                </div>
                <div className="p-4 bg-gray-50 rounded border">
                  <div className="text-sm text-gray-600 mb-1">执行时间</div>
                  <div className="text-lg font-bold text-gray-900">
                    {executionResult.duration?.toFixed(2)}s
                  </div>
                </div>
                <div className="p-4 bg-gray-50 rounded border">
                  <div className="text-sm text-gray-600 mb-1">断言结果</div>
                  <div className="text-lg font-bold text-gray-900">
                    {executionResult.assertions?.passed || 0}/{executionResult.assertions?.total || 0}
                  </div>
                </div>
              </div>

              {executionResult.logs && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">执行日志</label>
                  <pre className="bg-gray-900 text-gray-300 p-4 rounded-lg overflow-x-auto text-xs font-mono max-h-64">
                    {executionResult.logs}
                  </pre>
                </div>
              )}

              {executionResult.error && (
                <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
                  <div className="text-sm font-medium text-red-800 mb-1">错误信息</div>
                  <div className="text-sm text-red-700">{executionResult.error}</div>
                </div>
              )}
            </div>

            <div className="mt-6 flex justify-end">
              <button
                onClick={() => setShowResultDialog(false)}
                className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300"
              >
                关闭
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
