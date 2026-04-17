import React from 'react'

function SimpleTestApp() {
  return (
    <div style={{ padding: '20px', fontFamily: 'Arial, sans-serif' }}>
      <h1>🚀 AI测试平台</h1>
      <p>React应用正常运行！</p>
      <p>当前时间: {new Date().toLocaleString()}</p>
      
      <div style={{ marginTop: '20px', padding: '15px', border: '1px solid #ddd', borderRadius: '5px' }}>
        <h3>✅ 服务状态</h3>
        <p>前端服务器: 运行中 (端口3000)</p>
        <p>后端API: 运行中 (端口8000)</p>
        <p>AI功能: Ollama已连接</p>
      </div>
      
      <div style={{ marginTop: '20px' }}>
        <h3>🔗 可用页面</h3>
        <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
          <a href="/test.html" style={{ padding: '8px 16px', background: '#007bff', color: 'white', textDecoration: 'none', borderRadius: '4px' }}>
            静态测试页面
          </a>
        </div>
      </div>
    </div>
  )
}

export default SimpleTestApp