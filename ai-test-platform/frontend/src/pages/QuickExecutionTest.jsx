import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import PageHeader from '../components/PageHeader'
import ExecutionTriggerDialog from '../components/ExecutionTriggerDialog'

export default function QuickExecutionTest() {
  const navigate = useNavigate()
  const [showDialog, setShowDialog] = useState(false)
  const [selectedCases, setSelectedCases] = useState([])

  // 预定义的测试用例
  const testCases = [
    { id: 'TC_QUICK_001', title: 'GET请求测试', description: '测试httpbin GET接口' },
    { id: 'TC_QUICK_002', title: 'POST请求测试', description: '测试httpbin POST接口' },
    { id: 'TC_QUICK_003', title: '404错误测试', description: '测试404状态码' },
  ]

  const handleSelectCase = (caseId) => {
    if (selectedCases.includes(caseId)) {
      setSelectedCases(selectedCases.filter(id => id !== caseId))
    } else {
      setSelectedCases([...selectedCases, caseId])
    }
  }

  const handleSelectAll = () => {
    if (selectedCases.length === testCases.length) {
      setSelectedCases([])
    } else {
      setSelectedCases(testCases.map(tc => tc.id))
    }
  }

  const handleTriggerExecution = () => {
    if (selectedCases.length === 0) {
      alert('请至少选择一个测试用例')
      return
    }
    setShowDialog(true)
  }

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <PageHeader
        title="快速执行测试"
        subtitle="选择测试用例并触发执行"
        action={
          <button
            onClick={() => navigate('/test-runs-v2')}
            className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700"
          >
            查看执行记录
          </button>
        }
      />

      <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold">测试用例列表</h3>
          <div className="flex gap-3">
            <button
              onClick={handleSelectAll}
              className="px-3 py-1.5 text-sm border border-gray-300 rounded-lg hover:bg-gray-50"
            >
              {selectedCases.length === testCases.length ? '取消全选' : '全选'}
            </button>
            <button
              onClick={handleTriggerExecution}
              disabled={selectedCases.length === 0}
              className="px-4 py-1.5 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              执行选中用例 ({selectedCases.length})
            </button>
          </div>
        </div>

        <div className="space-y-3">
          {testCases.map((tc) => (
            <div
              key={tc.id}
              className={`p-4 border rounded-lg cursor-pointer transition-colors ${
                selectedCases.includes(tc.id)
                  ? 'border-blue-500 bg-blue-50'
                  : 'border-gray-200 hover:border-gray-300'
              }`}
              onClick={() => handleSelectCase(tc.id)}
            >
              <div className="flex items-start gap-3">
                <input
                  type="checkbox"
                  checked={selectedCases.includes(tc.id)}
                  onChange={() => handleSelectCase(tc.id)}
                  className="mt-1"
                  onClick={(e) => e.stopPropagation()}
                />
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="font-medium text-gray-900">{tc.title}</span>
                    <span className="text-xs text-gray-500 font-mono">{tc.id}</span>
                  </div>
                  <p className="text-sm text-gray-600">{tc.description}</p>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h4 className="font-medium text-blue-900 mb-2">使用说明</h4>
        <ul className="text-sm text-blue-800 space-y-1">
          <li>1. 选择要执行的测试用例</li>
          <li>2. 点击"执行选中用例"按钮</li>
          <li>3. 在弹窗中配置项目ID和环境ID(可以使用默认值)</li>
          <li>4. 点击"开始执行"触发测试</li>
          <li>5. 自动跳转到执行详情页查看结果</li>
        </ul>
      </div>

      <ExecutionTriggerDialog
        isOpen={showDialog}
        onClose={() => setShowDialog(false)}
        testCaseIds={selectedCases}
        onSuccess={(result) => {
          console.log('执行成功:', result)
        }}
      />
    </div>
  )
}
