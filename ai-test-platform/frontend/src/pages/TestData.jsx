import React, { useState, useEffect } from 'react'
import { testDataAPI } from '../services/api'

export default function TestData() {
  const [datasets, setDatasets] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadDatasets()
  }, [])

  const loadDatasets = async () => {
    try {
      const response = await testDataAPI.getDatasets()
      setDatasets(response.datasets || [])
    } catch (error) {
      console.error('加载数据集失败:', error)
    } finally {
      setLoading(false)
    }
  }

  const generateTestData = async (dataType) => {
    try {
      const response = await testDataAPI.generate({
        data_type: dataType,
        count: 1
      })
      alert(`生成成功:\n${JSON.stringify(response.data, null, 2)}`)
    } catch (error) {
      alert(`生成失败: ${error.message}`)
    }
  }

  if (loading) {
    return <div className="p-6">加载中...</div>
  }

  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold mb-2">测试数据管理</h1>
        <p className="text-gray-600">生成和管理测试数据</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <button
          onClick={() => generateTestData('user')}
          className="p-4 bg-blue-500 text-white rounded hover:bg-blue-600"
        >
          生成用户数据
        </button>
        <button
          onClick={() => generateTestData('order')}
          className="p-4 bg-green-500 text-white rounded hover:bg-green-600"
        >
          生成订单数据
        </button>
        <button
          onClick={() => generateTestData('product')}
          className="p-4 bg-purple-500 text-white rounded hover:bg-purple-600"
        >
          生成商品数据
        </button>
      </div>

      <div className="bg-white rounded-lg shadow">
        <div className="p-4 border-b">
          <h2 className="text-lg font-semibold">数据集列表</h2>
        </div>
        <div className="p-4">
          {datasets.length === 0 ? (
            <p className="text-gray-500 text-center py-8">暂无数据集</p>
          ) : (
            <div className="space-y-2">
              {datasets.map((dataset) => (
                <div key={dataset.id} className="p-3 border rounded hover:bg-gray-50">
                  <div className="font-medium">{dataset.name}</div>
                  <div className="text-sm text-gray-600">{dataset.description}</div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
