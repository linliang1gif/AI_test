import { useState, useEffect } from 'react'

export default function AiInsights() {
  const [agents, setAgents] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setTimeout(() => {
      setAgents([
        { id: 1, name: 'Bug分析代理', status: 'active', tasksCompleted: 45, accuracy: 92 },
        { id: 2, name: '测试生成代理', status: 'active', tasksCompleted: 128, accuracy: 88 },
        { id: 3, name: '自愈代理', status: 'idle', tasksCompleted: 23, accuracy: 85 }
      ])
      setLoading(false)
    }, 500)
  }, [])

  if (loading) {
    return <div className="p-6 text-gray-500">加载中...</div>
  }

  return (
    <div className="p-6">
      <h1 className="text-3xl font-bold text-gray-900 mb-6">AI分析中心</h1>
      
      <div className="grid grid-cols-3 gap-6 mb-8">
        <div className="bg-white p-6 rounded-lg shadow">
          <p className="text-gray-600 text-sm">活跃代理</p>
          <p className="text-3xl font-bold text-blue-600 mt-2">
            {agents.filter(a => a.status === 'active').length}
          </p>
        </div>
        <div className="bg-white p-6 rounded-lg shadow">
          <p className="text-gray-600 text-sm">总任务数</p>
          <p className="text-3xl font-bold text-green-600 mt-2">
            {agents.reduce((sum, a) => sum + a.tasksCompleted, 0)}
          </p>
        </div>
        <div className="bg-white p-6 rounded-lg shadow">
          <p className="text-gray-600 text-sm">平均准确率</p>
          <p className="text-3xl font-bold text-purple-600 mt-2">
            {agents.length > 0 ? Math.round(agents.reduce((sum, a) => sum + a.accuracy, 0) / agents.length) : 0}%
          </p>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow">
        <div className="p-6 border-b border-gray-200">
          <h2 className="text-xl font-bold text-gray-900">AI代理状态</h2>
        </div>
        <div className="p-6">
          <div className="space-y-4">
            {agents.map(agent => {
              const statusColor = agent.status === 'active' ? 'bg-green-500' : 'bg-gray-400'
              const statusText = agent.status === 'active' ? '运行中' : '空闲'
              
              return (
                <div key={agent.id} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                  <div className="flex items-center space-x-4">
                    <div className={`w-3 h-3 rounded-full ${statusColor}`}></div>
                    <div>
                      <p className="font-medium text-gray-900">{agent.name}</p>
                      <p className="text-sm text-gray-500">{statusText}</p>
                    </div>
                  </div>
                  <div className="flex items-center space-x-8">
                    <div className="text-right">
                      <p className="text-sm text-gray-500">完成任务</p>
                      <p className="font-semibold text-gray-900">{agent.tasksCompleted}</p>
                    </div>
                    <div className="text-right">
                      <p className="text-sm text-gray-500">准确率</p>
                      <p className="font-semibold text-gray-900">{agent.accuracy}%</p>
                    </div>
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      </div>

      <div className="mt-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
        <p className="text-blue-800">AI代理正在后台自动分析测试结果、生成测试用例和修复建议</p>
      </div>
    </div>
  )
}
