import { useState, useEffect } from 'react'

export default function DatasetSelector({ onSelect, selectedDatasetId }) {
  const [datasets, setDatasets] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadDatasets()
  }, [])

  const loadDatasets = async () => {
    try {
      const response = await fetch('/api/test-data/datasets')
      const result = await response.json()
      setDatasets(result.datasets || [])
    } catch (error) {
      console.error('加载数据集失败:', error)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return <div className="text-sm text-gray-500">加载数据集...</div>
  }

  return (
    <div>
      <label className="block text-sm font-medium text-gray-700 mb-2">
        选择测试数据集 (可选)
      </label>
      <select
        value={selectedDatasetId || ''}
        onChange={(e) => onSelect(e.target.value)}
        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
      >
        <option value="">不使用数据集</option>
        {datasets.map((dataset) => (
          <option key={dataset.id} value={dataset.id}>
            {dataset.name} - {dataset.description || '无描述'}
          </option>
        ))}
      </select>
      {selectedDatasetId && (
        <p className="mt-2 text-sm text-green-600">
          ✓ 已选择数据集,脚本将自动包含数据生成代码
        </p>
      )}
    </div>
  )
}
