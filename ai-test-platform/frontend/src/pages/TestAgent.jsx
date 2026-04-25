import { useState } from 'react'

export default function TestAgent() {
  const [requirement, setRequirement] = useState('')
  const [gitDiff, setGitDiff] = useState('')
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [result, setResult] = useState(null)
  const [history, setHistory] = useState([])
  const [showHistory, setShowHistory] = useState(false)

  const handleAnalyze = async () => {
    if (!requirement.trim()) {
      alert('请输入需求描述')
      return
    }

    setIsAnalyzing(true)
    setResult(null)

    try {
      const response = await fetch('/api/agent/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          requirement: requirement,
          git_diff: gitDiff
        })
      })

      const data = await response.json()
      setResult(data)
      
      // 刷新历史记录
      loadHistory()
    } catch (error) {
      alert('分析失败: ' + error.message)
    } finally {
      setIsAnalyzing(false)
    }
  }

  const loadHistory = async () => {
    try {
      const response = await fetch('/api/agent/history?limit=10')
      const data = await response.json()
      setHistory(data.data || [])
    } catch (error) {
      console.error('加载历史失败:', error)
    }
  }

  const handleClear = () => {
    setRequirement('')
    setGitDiff('')
    setResult(null)
  }

  const loadExample = (exampleNum) => {
    const examples = {
      1: {
        requirement: '新增订单支付功能，支持微信支付和支付宝支付。用户下单后可以选择支付方式，完成支付后订单状态更新为已支付。',
        gitDiff: `diff --git a/order/service.py b/order/service.py
+++ b/order/service.py
@@ -10,6 +10,15 @@ class OrderService:
+    def process_payment(self, order_id, payment_method):
+        order = self.get_order(order_id)
+        if payment_method == 'wechat':
+            result = wechat_pay(order)
+        elif payment_method == 'alipay':
+            result = alipay_pay(order)
+        order.status = 'paid'
+        order.save()`
      },
      2: {
        requirement: '修复用户登录时密码验证失败的bug',
        gitDiff: `diff --git a/auth/service.py b/auth/service.py
+++ b/auth/service.py
@@ -5,7 +5,7 @@ def login(username, password):
-    if user.password == password:
+    if check_password_hash(user.password, password):`
      },
      3: {
        requirement: '更新README文档，添加安装说明和使用示例',
        gitDiff: `diff --git a/README.md b/README.md
+++ b/README.md
@@ -1,3 +1,10 @@
+## 安装
+pip install -r requirements.txt
+
+## 使用
+python main.py`
      }
    }

    const example = examples[exampleNum]
    if (example) {
      setRequirement(example.requirement)
      setGitDiff(example.gitDiff)
    }
  }

  const priorityColor = {
    'P0': 'bg-red-100 text-red-700 border-red-300',
    'P1': 'bg-yellow-100 text-yellow-700 border-yellow-300',
    'P2': 'bg-green-100 text-green-700 border-green-300'
  }

  const riskColor = {
    '高': 'text-red-600',
    '中': 'text-yellow-600',
    '低': 'text-green-600'
  }

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">🤖 Test Agent</h1>
          <p className="text-gray-600 mt-1">AI测试决策中心 - 智能分析测试需求</p>
        </div>
        <button
          onClick={() => { setShowHistory(true); loadHistory(); }}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center space-x-2"
        >
          <span>📜</span>
          <span>决策历史</span>
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* 左侧：输入区域 */}
        <div className="space-y-4">
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-bold mb-4">📝 输入信息</h2>
            
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                需求描述 <span className="text-red-500">*</span>
              </label>
              <textarea
                value={requirement}
                onChange={(e) => setRequirement(e.target.value)}
                placeholder="请输入需求描述或变更说明..."
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 h-32"
              />
            </div>

            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Git Diff（可选）
              </label>
              <textarea
                value={gitDiff}
                onChange={(e) => setGitDiff(e.target.value)}
                placeholder="粘贴git diff内容..."
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono text-sm h-40"
              />
            </div>

            <div className="flex space-x-2 mb-4">
              <button
                onClick={() => loadExample(1)}
                className="px-3 py-1 bg-gray-100 text-gray-700 rounded hover:bg-gray-200 text-sm"
              >
                示例1: 支付功能
              </button>
              <button
                onClick={() => loadExample(2)}
                className="px-3 py-1 bg-gray-100 text-gray-700 rounded hover:bg-gray-200 text-sm"
              >
                示例2: Bug修复
              </button>
              <button
                onClick={() => loadExample(3)}
                className="px-3 py-1 bg-gray-100 text-gray-700 rounded hover:bg-gray-200 text-sm"
              >
                示例3: 文档更新
              </button>
            </div>

            <div className="flex space-x-3">
              <button
                onClick={handleAnalyze}
                disabled={isAnalyzing || !requirement.trim()}
                className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center space-x-2"
              >
                {isAnalyzing ? (
                  <>
                    <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                    <span>AI分析中...</span>
                  </>
                ) : (
                  <>
                    <span>🚀</span>
                    <span>开始分析</span>
                  </>
                )}
              </button>
              <button
                onClick={handleClear}
                className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
              >
                清空
              </button>
            </div>
          </div>

          {/* 使用说明 */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <h3 className="font-medium text-blue-900 mb-2">💡 使用说明</h3>
            <ul className="text-sm text-blue-800 space-y-1">
              <li>• 输入需求描述或变更说明</li>
              <li>• 可选：粘贴git diff内容</li>
              <li>• AI将分析是否需要测试</li>
              <li>• 给出影响模块和优先级</li>
              <li>• 预估测试工作量</li>
            </ul>
          </div>
        </div>

        {/* 右侧：结果区域 */}
        <div>
          {result ? (
            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-bold">📊 分析结果</h2>
                <span className={`px-3 py-1 rounded-full text-sm font-medium border ${
                  result.need_test 
                    ? 'bg-green-100 text-green-700 border-green-300' 
                    : 'bg-gray-100 text-gray-700 border-gray-300'
                }`}>
                  {result.need_test ? '✅ 需要测试' : '❌ 无需测试'}
                </span>
              </div>

              <div className="space-y-4">
                {/* 优先级和风险 */}
                <div className="grid grid-cols-2 gap-4">
                  <div className="p-4 bg-gray-50 rounded-lg border">
                    <div className="text-sm text-gray-600 mb-1">测试优先级</div>
                    <div className={`text-2xl font-bold px-3 py-1 rounded border inline-block ${priorityColor[result.priority] || 'bg-gray-100 text-gray-700'}`}>
                      {result.priority}
                    </div>
                  </div>
                  <div className="p-4 bg-gray-50 rounded-lg border">
                    <div className="text-sm text-gray-600 mb-1">风险等级</div>
                    <div className={`text-2xl font-bold ${riskColor[result.risk_level] || 'text-gray-700'}`}>
                      {result.risk_level}
                    </div>
                  </div>
                </div>

                {/* 影响模块 */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">影响模块</label>
                  <div className="flex flex-wrap gap-2">
                    {result.modules.map((module, index) => (
                      <span key={index} className="px-3 py-1 bg-purple-100 text-purple-700 rounded-full text-sm">
                        {module}
                      </span>
                    ))}
                  </div>
                </div>

                {/* 测试类型 */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">测试类型</label>
                  <div className="flex flex-wrap gap-2">
                    {result.test_types.map((type, index) => (
                      <span key={index} className="px-3 py-1 bg-blue-100 text-blue-700 rounded-full text-sm">
                        {type}
                      </span>
                    ))}
                  </div>
                </div>

                {/* 预估工作量 */}
                <div className="p-4 bg-orange-50 rounded-lg border border-orange-200">
                  <div className="text-sm text-orange-800 mb-1">预估测试工作量</div>
                  <div className="text-lg font-bold text-orange-900">{result.estimated_effort}</div>
                </div>

                {/* 决策理由 */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">决策理由</label>
                  <div className="p-3 bg-gray-50 rounded-lg border text-sm text-gray-700">
                    {result.reason}
                  </div>
                </div>

                {/* 元数据 */}
                <div className="pt-4 border-t">
                  <div className="grid grid-cols-2 gap-4 text-xs text-gray-500">
                    <div>
                      <span className="font-medium">分析时间:</span> {new Date(result.analyzed_at).toLocaleString()}
                    </div>
                    <div>
                      <span className="font-medium">耗时:</span> {result.duration}
                    </div>
                    <div>
                      <span className="font-medium">AI模型:</span> {result.provider} - {result.model}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex flex-col items-center justify-center py-12 text-gray-400">
                <div className="text-6xl mb-4">🤖</div>
                <p className="text-lg">等待分析...</p>
                <p className="text-sm mt-2">请在左侧输入需求描述</p>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* 决策历史对话框 */}
      {showHistory && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl p-6 w-[900px] max-h-[80vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-bold">📜 决策历史</h2>
              <button
                onClick={() => setShowHistory(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                ✕
              </button>
            </div>

            {history.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                暂无决策历史
              </div>
            ) : (
              <div className="space-y-4">
                {history.map((item, index) => (
                  <div key={index} className="border rounded-lg p-4 hover:bg-gray-50">
                    <div className="flex items-start justify-between mb-2">
                      <div className="flex-1">
                        <p className="font-medium text-gray-900">{item.requirement}</p>
                        <p className="text-xs text-gray-500 mt-1">
                          {new Date(item.timestamp).toLocaleString()}
                        </p>
                      </div>
                      <span className={`px-2 py-1 rounded text-xs font-medium ${
                        item.decision.need_test 
                          ? 'bg-green-100 text-green-700' 
                          : 'bg-gray-100 text-gray-700'
                      }`}>
                        {item.decision.need_test ? '需要测试' : '无需测试'}
                      </span>
                    </div>
                    
                    <div className="flex items-center space-x-4 text-sm">
                      <span className={`px-2 py-1 rounded border ${priorityColor[item.decision.priority]}`}>
                        {item.decision.priority}
                      </span>
                      <span className="text-gray-600">
                        模块: {item.decision.modules.join(', ')}
                      </span>
                      <span className="text-gray-600">
                        工作量: {item.decision.estimated_effort}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}

            <div className="mt-6 flex justify-end">
              <button
                onClick={() => setShowHistory(false)}
                className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300"
              >
                关闭
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 功能说明 */}
      <div className="mt-6 bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg p-6 border border-blue-200">
        <h3 className="text-lg font-bold text-gray-900 mb-3">🎯 Test Agent 能做什么？</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="flex items-start space-x-3">
            <span className="text-2xl">🧠</span>
            <div>
              <h4 className="font-medium text-gray-900">智能决策</h4>
              <p className="text-sm text-gray-600">AI分析需求和代码变更，自动判断是否需要测试</p>
            </div>
          </div>
          <div className="flex items-start space-x-3">
            <span className="text-2xl">🎯</span>
            <div>
              <h4 className="font-medium text-gray-900">影响分析</h4>
              <p className="text-sm text-gray-600">识别受影响的功能模块和测试范围</p>
            </div>
          </div>
          <div className="flex items-start space-x-3">
            <span className="text-2xl">⚡</span>
            <div>
              <h4 className="font-medium text-gray-900">优先级评估</h4>
              <p className="text-sm text-gray-600">评估测试优先级（P0/P1/P2）和风险等级</p>
            </div>
          </div>
          <div className="flex items-start space-x-3">
            <span className="text-2xl">📊</span>
            <div>
              <h4 className="font-medium text-gray-900">工作量预估</h4>
              <p className="text-sm text-gray-600">预估测试所需时间和资源</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
