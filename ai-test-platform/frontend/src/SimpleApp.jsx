import React, { useState, useEffect } from 'react'

function SimpleApp() {
  const [aiConfig, setAiConfig] = useState(null)
  const [messages, setMessages] = useState([
    { id: 1, content: '👋 你好！我是AI助手，使用Ollama本地模型为您服务。有什么可以帮助您的吗？', isUser: false }
  ])
  const [inputMessage, setInputMessage] = useState('')
  const [isLoading, setIsLoading] = useState(false)

  // 获取AI配置
  useEffect(() => {
    fetch('http://localhost:8000/api/ai/current')
      .then(res => res.json())
      .then(config => {
        setAiConfig(config)
        console.log('当前AI配置:', config)
      })
      .catch(err => console.error('获取AI配置失败:', err))
  }, [])

  // 发送消息
  const sendMessage = async () => {
    if (!inputMessage.trim()) return

    // 添加用户消息
    const userMessage = { id: Date.now(), content: inputMessage, isUser: true }
    setMessages(prev => [...prev, userMessage])
    setInputMessage('')
    setIsLoading(true)

    try {
      const response = await fetch('http://localhost:8000/api/ai/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt: inputMessage })
      })

      const result = await response.json()

      if (result.success) {
        const aiMessage = { id: Date.now() + 1, content: result.response, isUser: false }
        setMessages(prev => [...prev, aiMessage])
      } else {
        const errorMessage = { id: Date.now() + 1, content: `❌ 错误: ${result.error}`, isUser: false }
        setMessages(prev => [...prev, errorMessage])
      }
    } catch (error) {
      const errorMessage = { id: Date.now() + 1, content: '❌ 网络错误，请检查服务器连接', isUser: false }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div style={{ padding: '20px', fontFamily: 'Arial, sans-serif', maxWidth: '1200px', margin: '0 auto' }}>
      <h1>🚀 AI测试平台 - 默认Ollama模式</h1>
      
      {/* AI配置状态 */}
      <div style={{ margin: '20px 0', padding: '15px', border: '1px solid #ddd', borderRadius: '5px', background: '#f8f9fa' }}>
        <h3>🤖 AI配置状态</h3>
        {aiConfig ? (
          <div style={{ display: 'flex', gap: '20px', alignItems: 'center' }}>
            <span style={{ padding: '5px 10px', background: '#28a745', color: 'white', borderRadius: '15px', fontSize: '14px' }}>
              ✅ {aiConfig.current_provider?.toUpperCase()} ({aiConfig.current_model})
            </span>
            <span style={{ color: '#6c757d', fontSize: '14px' }}>
              默认配置已生效，无需手动切换
            </span>
          </div>
        ) : (
          <span style={{ color: '#dc3545' }}>⚠️ 正在获取AI配置...</span>
        )}
      </div>

      {/* AI对话区域 */}
      <div style={{ margin: '20px 0', border: '1px solid #ddd', borderRadius: '10px', overflow: 'hidden', height: '500px', display: 'flex', flexDirection: 'column' }}>
        <div style={{ padding: '15px', background: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)', color: 'white' }}>
          <h3 style={{ margin: 0 }}>💬 AI智能对话</h3>
          <small>直接使用默认Ollama模型，无需配置</small>
        </div>
        
        {/* 消息列表 */}
        <div style={{ flex: 1, padding: '15px', overflowY: 'auto', background: '#f8f9fa' }}>
          {messages.map(msg => (
            <div key={msg.id} style={{ 
              marginBottom: '15px', 
              display: 'flex', 
              justifyContent: msg.isUser ? 'flex-end' : 'flex-start' 
            }}>
              <div style={{
                maxWidth: '70%',
                padding: '10px 15px',
                borderRadius: '18px',
                background: msg.isUser ? '#007bff' : 'white',
                color: msg.isUser ? 'white' : '#333',
                border: msg.isUser ? 'none' : '1px solid #e9ecef'
              }}>
                {msg.content}
              </div>
            </div>
          ))}
          
          {isLoading && (
            <div style={{ textAlign: 'center', color: '#6c757d', padding: '10px' }}>
              🤖 AI正在思考中...
            </div>
          )}
        </div>
        
        {/* 输入区域 */}
        <div style={{ padding: '15px', background: 'white', borderTop: '1px solid #e9ecef' }}>
          <div style={{ display: 'flex', gap: '10px' }}>
            <input
              type="text"
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
              placeholder="输入您的问题..."
              style={{
                flex: 1,
                padding: '10px 15px',
                border: '2px solid #e9ecef',
                borderRadius: '25px',
                fontSize: '16px',
                outline: 'none'
              }}
            />
            <button
              onClick={sendMessage}
              disabled={isLoading || !inputMessage.trim()}
              style={{
                padding: '10px 20px',
                background: '#007bff',
                color: 'white',
                border: 'none',
                borderRadius: '25px',
                cursor: 'pointer',
                fontSize: '16px'
              }}
            >
              发送
            </button>
          </div>
        </div>
      </div>
      
      {/* 快速链接 */}
      <div style={{ margin: '20px 0', padding: '15px', border: '1px solid #ddd', borderRadius: '5px' }}>
        <h3>🔗 其他功能页面</h3>
        <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
          <a href="/default_ai_chat.html" style={{ padding: '8px 16px', background: '#007bff', color: 'white', textDecoration: 'none', borderRadius: '4px' }}>
            纯HTML AI对话
          </a>
          <a href="/test_ai_chat.html" style={{ padding: '8px 16px', background: '#28a745', color: 'white', textDecoration: 'none', borderRadius: '4px' }}>
            AI对话测试
          </a>
          <a href="/test_frontend_api.html" style={{ padding: '8px 16px', background: '#17a2b8', color: 'white', textDecoration: 'none', borderRadius: '4px' }}>
            API测试
          </a>
        </div>
      </div>
      
      {/* 服务状态 */}
      <div style={{ margin: '20px 0', padding: '15px', border: '1px solid #ddd', borderRadius: '5px' }}>
        <h3>📊 服务状态</h3>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '10px' }}>
          <div style={{ padding: '10px', background: '#d4edda', borderRadius: '4px' }}>
            <strong>前端服务</strong><br />
            <span style={{ color: 'green' }}>✅ 运行中 (端口3000)</span>
          </div>
          <div style={{ padding: '10px', background: '#d4edda', borderRadius: '4px' }}>
            <strong>后端API</strong><br />
            <span style={{ color: 'green' }}>✅ 运行中 (端口8000)</span>
          </div>
          <div style={{ padding: '10px', background: '#d4edda', borderRadius: '4px' }}>
            <strong>默认AI</strong><br />
            <span style={{ color: 'green' }}>✅ Ollama自动配置</span>
          </div>
        </div>
      </div>
    </div>
  )
}

export default SimpleApp