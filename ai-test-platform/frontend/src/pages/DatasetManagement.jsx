import { useState, useEffect } from 'react'

/**
 * 数据集管理页面
 * 用于管理保存的测试数据集
 */
function DatasetManagement() {
  const [datasets, setDatasets] = useState([])
  const [loading, setLoading] = useState(true)
  const [searchKeyword, setSearchKeyword] = useState('')
  const [selectedDataset, setSelectedDataset] = useState(null)
  const [showDetail, setShowDetail] = useState(false)

  useEffect(() => {
    loadDatasets()
  }, [])

  const loadDatasets = async () => {
    setLoading(true)
    try {
      const response = await fetch('/api/test-data/datasets')
      const result = await response.json()
      
      if (result.success) {
        setDatasets(result.datasets || [])
      }
    } catch (error) {
      console.error('加载数据集失败:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleSearch = async () => {
    if (!searchKeyword.trim()) {
      loadDatasets()
      return
    }

    setLoading(true)
    try {
      const response = await fetch(`/api/test-data/datasets?keyword=${encodeURIComponent(searchKeyword)}`)
      const result = await response.json()
      
      if (result.success) {
        setDatasets(result.datasets || [])
      }
    } catch (error) {
      console.error('搜索失败:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleDelete = async (datasetId) => {
    if (!confirm('确定要删除这个数据集吗?')) return

    try {
      const response = await fetch(`/api/test-data/datasets/${datasetId}`, {
        method: 'DELETE'
      })
      const result = await response.json()
      
      if (result.success) {
        alert('✅ 删除成功')
        loadDatasets()
      } else {
        alert('删除失败: ' + result.message)
      }
    } catch (error) {
      alert('删除失败: ' + error.message)
    }
  }

  const handleViewDetail = (dataset) => {
    setSelectedDataset(dataset)
    setShowDetail(true)
  }

  const handleUseDataset = async (dataset) => {
    try {
      // 增加使用次数
      await fetch(`/api/test-data/datasets/${dataset.id}/use`, {
        method: 'POST'
      })
      
      // 复制数据到剪贴板
      await navigator.clipboard.writeText(JSON.stringify(dataset.data, null, 2))
      alert('✅ 数据已复制到剪贴板!')
      loadDatasets()
    } catch (error) {
      alert('操作失败: ' + error.message)
    }
  }

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleString('zh-CN')
  }

  if (loading && datasets.length === 0) {
    return (
      <div className="p-6">
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-gray-200 rounded w-1/4"></div>
          <div className="h-32 bg-gray-200 rounded"></div>
        </div>
      </div>
    )
  }

  return (
    <div className="p-6 space-y-6">
      {/* 标题 */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">💾 数据集管理</h1>
        <p className="text-gray-600 mt-2">管理和复用测试数据集</p>
      </div>

      {/* 搜索栏 */}
      <div className="bg-white rounded-lg shadow p-4">
        <div className="flex space-x-4">
          <input
            type="text"
            value={searchKeyword}
            onChange={(e) => setSearchKeyword(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
            placeholder="搜索数据集名称或描述..."
            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <button
            onClick={handleSearch}
            className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            🔍 搜索
          </button>
          <button
            onClick={loadDatasets}
            className="px-6 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200"
          >
            🔄 刷新
          </button>
        </div>
      </div>

      {/* 统计信息 */}
      <div className="grid grid-cols-3 gap-4">
        <div className="bg-white rounded-lg shadow p-6">
          <div className="text-sm text-gray-600 mb-1">总数据集</div>
          <div className="text-3xl font-bold text-blue-600">{datasets.length}</div>
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <div className="text-sm text-gray-600 mb-1">总使用次数</div>
          <div className="text-3xl font-bold text-green-600">
            {datasets.reduce((sum, d) => sum + (d.usage_count || 0), 0)}
          </div>
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <div className="text-sm text-gray-600 mb-1">最常用</div>
          <div className="text-sm font-medium text-gray-900 truncate">
            {datasets.length > 0 
              ? datasets.sort((a, b) => (b.usage_count || 0) - (a.usage_count || 0))[0]?.name || '-'
              : '-'
            }
          </div>
        </div>
      </div>

      {/* 数据集列表 */}
      <div className="bg-white rounded-lg shadow">
        <div className="p-6 border-b border-gray-200">
          <h2 className="text-xl font-semibold">数据集列表</h2>
        </div>

        <div className="divide-y divide-gray-200">
          {datasets.length === 0 ? (
            <div className="p-8 text-center text-gray-500">
              <div className="text-4xl mb-2">📭</div>
              <p>暂无数据集</p>
              <p className="text-sm mt-1">在API管理中生成数据后保存即可创建数据集</p>
            </div>
          ) : (
            datasets.map((dataset) => (
              <div key={dataset.id} className="p-6 hover:bg-gray-50 transition-colors">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center space-x-3 mb-2">
                      <h3 className="text-lg font-semibold text-gray-900">{dataset.name}</h3>
                      <span className="px-2 py-1 text-xs bg-blue-100 text-blue-700 rounded">
                        使用 {dataset.usage_count || 0} 次
                      </span>
                    </div>
                    
                    {dataset.description && (
                      <p className="text-sm text-gray-600 mb-2">{dataset.description}</p>
                    )}
                    
                    <div className="flex items-center space-x-4 text-sm text-gray-500">
                      <span>📅 创建: {formatDate(dataset.created_at)}</span>
                      <span>🔄 更新: {formatDate(dataset.updated_at)}</span>
                      <span>📦 版本: {dataset.version}</span>
                    </div>
                    
                    {dataset.tags && dataset.tags.length > 0 && (
                      <div className="flex items-center space-x-2 mt-2">
                        {dataset.tags.map((tag, i) => (
                          <span key={i} className="px-2 py-1 text-xs bg-gray-100 text-gray-600 rounded">
                            {tag}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                  
                  <div className="flex items-center space-x-2 ml-4">
                    <button
                      onClick={() => handleViewDetail(dataset)}
                      className="px-3 py-1.5 text-sm bg-blue-50 text-blue-700 hover:bg-blue-100 rounded-lg"
                      title="查看详情"
                    >
                      👁️ 查看
                    </button>
                    <button
                      onClick={() => handleUseDataset(dataset)}
                      className="px-3 py-1.5 text-sm bg-green-50 text-green-700 hover:bg-green-100 rounded-lg"
                      title="使用数据集"
                    >
                      📋 复制
                    </button>
                    <button
                      onClick={() => handleDelete(dataset.id)}
                      className="px-3 py-1.5 text-sm bg-red-50 text-red-700 hover:bg-red-100 rounded-lg"
                      title="删除"
                    >
                      🗑️ 删除
                    </button>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {/* 详情对话框 */}
      {showDetail && selectedDataset && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[80vh] overflow-hidden">
            <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
              <h3 className="text-lg font-semibold">{selectedDataset.name}</h3>
              <button
                onClick={() => setShowDetail(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                ✕
              </button>
            </div>

            <div className="p-6 overflow-y-auto max-h-[60vh]">
              <div className="space-y-4">
                <div>
                  <h4 className="text-sm font-medium text-gray-700 mb-2">描述</h4>
                  <p className="text-sm text-gray-600">{selectedDataset.description || '无描述'}</p>
                </div>

                <div>
                  <h4 className="text-sm font-medium text-gray-700 mb-2">数据内容</h4>
                  <pre className="p-4 bg-gray-900 text-green-400 rounded-lg text-sm overflow-x-auto">
                    {JSON.stringify(selectedDataset.data, null, 2)}
                  </pre>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <h4 className="text-sm font-medium text-gray-700 mb-1">创建时间</h4>
                    <p className="text-sm text-gray-600">{formatDate(selectedDataset.created_at)}</p>
                  </div>
                  <div>
                    <h4 className="text-sm font-medium text-gray-700 mb-1">更新时间</h4>
                    <p className="text-sm text-gray-600">{formatDate(selectedDataset.updated_at)}</p>
                  </div>
                  <div>
                    <h4 className="text-sm font-medium text-gray-700 mb-1">使用次数</h4>
                    <p className="text-sm text-gray-600">{selectedDataset.usage_count || 0} 次</p>
                  </div>
                  <div>
                    <h4 className="text-sm font-medium text-gray-700 mb-1">版本</h4>
                    <p className="text-sm text-gray-600">{selectedDataset.version}</p>
                  </div>
                </div>
              </div>
            </div>

            <div className="px-6 py-4 border-t border-gray-200 flex items-center justify-end space-x-3">
              <button
                onClick={() => setShowDetail(false)}
                className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-lg"
              >
                关闭
              </button>
              <button
                onClick={() => {
                  handleUseDataset(selectedDataset)
                  setShowDetail(false)
                }}
                className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
              >
                📋 复制数据
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default DatasetManagement
