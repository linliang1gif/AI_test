import { useState, useEffect } from 'react'
import { dashboardAPI } from '../services/api'

export default function Dashboard() {
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    dashboardAPI.getStats()
      .then(data => setStats(data))
      .catch(err => setError(err.message))
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <div className="p-6 text-gray-500">加载中...</div>
  if (error) return <div className="p-6 text-red-500">加载失败: {error}</div>

  const recentTests = stats?.recentTests || []

  return (
    <div className="p-6">
      <h1 className="text-3xl font-bold text-gray-900 mb-4">仪表板</h1>
      <div className="grid grid-cols-4 gap-6">
        <div className="bg-white p-6 rounded-lg shadow">
          <p className="text-gray-600 text-sm">今日测试总数</p>
          <p className="text-3xl font-bold text-blue-600 mt-2">{stats?.totalTests ?? '-'}</p>
        </div>
        <div className="bg-white p-6 rounded-lg shadow">
          <p className="text-gray-600 text-sm">通过测试</p>
          <p className="text-3xl font-bold text-green-600 mt-2">{stats?.passed ?? '-'}</p>
        </div>
        <div className="bg-white p-6 rounded-lg shadow">
          <p className="text-gray-600 text-sm">失败测试</p>
          <p className="text-3xl font-bold text-red-600 mt-2">{stats?.failed ?? '-'}</p>
        </div>
        <div className="bg-white p-6 rounded-lg shadow">
          <p className="text-gray-600 text-sm">测试覆盖率</p>
          <p className="text-3xl font-bold text-purple-600 mt-2">{stats?.coverage != null ? `${stats.coverage}%` : '-'}</p>
        </div>
      </div>

      <div className="mt-8 bg-white p-6 rounded-lg shadow">
        <h2 className="text-xl font-bold text-gray-900 mb-4">最近测试执行</h2>
        <div className="space-y-3">
          {recentTests.length === 0 ? (
            <p className="text-gray-500 text-sm">暂无数据</p>
          ) : recentTests.map((test, i) => (
            <div key={i} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
              <div>
                <p className="font-medium text-gray-900">{test.name}</p>
                <p className="text-sm text-gray-500">{test.time}</p>
              </div>
              <span className={`px-3 py-1 rounded-full text-sm ${
                test.status === 'passed' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
              }`}>
                {test.status === 'passed' ? '通过' : '失败'}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
