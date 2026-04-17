import React from 'react'

function TestApp() {
  return (
    <div style={{ padding: '20px', fontFamily: 'Arial, sans-serif' }}>
      <h1>🚀 AI测试平台 - 前端测试</h1>
      <div style={{ backgroundColor: '#d4edda', padding: '10px', borderRadius: '5px', margin: '10px 0' }}>
        ✅ React应用正常运行
      </div>
      <div style={{ backgroundColor: '#fff3cd', padding: '10px', borderRadius: '5px', margin: '10px 0' }}>
        📊 正在测试API连接...
      </div>
      <div id="api-test"></div>
    </div>
  )
}

export default TestApp