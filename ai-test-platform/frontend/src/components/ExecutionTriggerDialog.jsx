import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../services/api'

export default function ExecutionTriggerDialog({ isOpen, onClose, testCaseIds = [], onSuccess }) {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [projectId, setProjectId] = useState('1')
  const [environmentId, setEnvironmentId] = useState('1')

  if (!isOpen) return null

  const handleTrigger = async () => {
    try {
      setLoading(true)
      setError(null)

      // 调用简化触发API
      const response = await fetch(
        `/api/v2/execution/trigger-simple?project_id=${projectId}&environment_id=${environmentId}&test_case_ids=${testCaseIds.join('&test_case_ids=')}`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
        }
      )

      if (!response.ok) {
        const errorText = await response.text()
        throw new Error(`执行失败: ${response.status} ${errorText}`)
      }

      const result = await response.json()

      if (result.success) {
        // 成功后跳转到执行详情页
        onClose()
        if (onSuccess) onSuccess(result)
        navigate(`/test-runs-v2/${result.run_id}`)
      } else {
        setError(result.message || '执行失败')
      }
    } catch (err) {
      console.error('触发执行失败:', err)
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-md w-full p-6">
        <h3 className="text-lg font-semibold mb-4">触发测试执行</h3>

        {error && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded text-red-700 text-sm">
            {error}
          </div>
        )}

        <div className="space-y-4 mb-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              项目ID
            </label>
            <input
              type="number"
              value={projectId}
              onChange={(e) => setProjectId(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              disabled={loading}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              环境ID
            </label>
            <input
              type="number"
              value={environmentId}
              onChange={(e) => setEnvironmentId(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              disabled={loading}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              测试用例
            </label>
            <div className="text-sm text-gray-600">
              {testCaseIds.length > 0 ? (
                <div>
                  已选择 {testCaseIds.length} 个用例
                  <div className="mt-2 max-h-32 overflow-y-auto bg-gray-50 rounded p-2">
                    {testCaseIds.map((id) => (
                      <div key={id} className="text-xs text-gray-500">
                        {id}
                      </div>
                    ))}
                  </div>
                </div>
              ) : (
                <div className="text-gray-400">未选择用例</div>
              )}
            </div>
          </div>
        </div>

        <div className="flex gap-3">
          <button
            onClick={onClose}
            disabled={loading}
            className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 disabled:opacity-50"
          >
            取消
          </button>
          <button
            onClick={handleTrigger}
            disabled={loading || testCaseIds.length === 0}
            className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
          >
            {loading ? '执行中...' : '开始执行'}
          </button>
        </div>

        <div className="mt-4 text-xs text-gray-500">
          <p>提示: 当前使用httpbin.org进行测试</p>
          <p>项目ID和环境ID可以是任意数字</p>
        </div>
      </div>
    </div>
  )
}
