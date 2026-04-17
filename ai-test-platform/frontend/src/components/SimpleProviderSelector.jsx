import { useState, useEffect } from 'react'
import api from '../services/api'

const SimpleProviderSelector = () => {
  const [providers, setProviders] = useState([])
  const [currentProvider, setCurrentProvider] = useState(null)
  const [currentModel, setCurrentModel] = useState(null) // 新增：当前模型
  const [selectedProvider, setSelectedProvider] = useState('') // 新增：下拉选择的提供商
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [debugInfo, setDebugInfo] = useState([])
  const [testingProvider, setTestingProvider] = useState(null) // 新增：正在测试的提供商

  const addDebugInfo = (message) => {
    const timestamp = new Date().toLocaleTimeString()
    setDebugInfo(prev => [...prev, `[${timestamp}] ${message}`])
  }

  const fetchProviders = async () => {
    addDebugInfo('开始获取AI提供商列表...')
    setLoading(true)
    setError(null)

    try {
      addDebugInfo('使用API服务获取提供商列表')
      const data = await api.ai.getProviders()
      addDebugInfo(`获取到数据: ${JSON.stringify(data)}`)
      
      setProviders(data.providers || [])
      setCurrentProvider(data.current)
      setCurrentModel(data.current_model) // 设置当前模型
      addDebugInfo(`成功加载 ${data.providers?.length || 0} 个提供商`)
      
      // 检查每个提供商的状态
      if (data.providers && data.providers.length > 0) {
        for (const provider of data.providers) {
          try {
            addDebugInfo(`检查 ${provider.name} 状态...`)
            const statusData = await api.ai.getProviderStatus(provider.id)
            addDebugInfo(`${provider.name} 状态: ${JSON.stringify(statusData)}`)
          } catch (statusErr) {
            addDebugInfo(`❌ ${provider.name} 状态检查失败: ${statusErr.message}`)
          }
        }
      }
      
    } catch (err) {
      const errorMsg = `获取提供商失败: ${err.message}`
      setError(errorMsg)
      addDebugInfo(errorMsg)
    } finally {
      setLoading(false)
    }
  }

  // 新增：测试提供商连接
  const testProvider = async (providerId) => {
    addDebugInfo(`测试提供商连接: ${providerId}`)
    setTestingProvider(providerId)

    try {
      const data = await api.ai.testProvider(providerId)
      addDebugInfo(`测试响应: ${JSON.stringify(data)}`)

      if (data.success) {
        addDebugInfo(`✅ ${data.message}`)
        // 重新获取提供商列表以更新状态
        setTimeout(() => {
          fetchProviders()
        }, 1000)
      } else {
        throw new Error(data.message || '测试失败')
      }

    } catch (err) {
      const errorMsg = `测试连接失败: ${err.message}`
      setError(errorMsg)
      addDebugInfo(errorMsg)
    } finally {
      setTestingProvider(null)
    }
  }

  const selectProvider = async (providerId) => {
    addDebugInfo(`选择提供商: ${providerId}`)
    setLoading(true)

    try {
      const data = await api.ai.selectProvider(providerId)
      addDebugInfo(`选择响应: ${JSON.stringify(data)}`)

      if (data.success) {
        setCurrentProvider(providerId)
        addDebugInfo(`✅ ${data.message}`)
        // 重新获取提供商列表以更新状态
        setTimeout(() => {
          fetchProviders()
        }, 1000)
      } else {
        throw new Error(data.error || '选择失败')
      }

    } catch (err) {
      const errorMsg = `选择提供商失败: ${err.message}`
      setError(errorMsg)
      addDebugInfo(errorMsg)
    } finally {
      setLoading(false)
    }
  }

  // 新增：处理下拉选择切换
  const handleProviderSwitch = async () => {
    if (!selectedProvider) {
      setError('请先选择一个提供商')
      return
    }
    
    addDebugInfo(`切换提供商: ${selectedProvider}`)
    setLoading(true)
    setError(null)

    try {
      // 使用switchProvider API
      const data = await api.ai.switchProvider(selectedProvider, 'qwen2.5:1.5b')
      addDebugInfo(`切换响应: ${JSON.stringify(data)}`)

      if (data.success) {
        setCurrentProvider(selectedProvider)
        setCurrentModel(data.current_model || 'qwen2.5:1.5b') // 更新当前模型
        addDebugInfo(`✅ ${data.message}`)
        // 重新获取提供商列表以更新状态
        setTimeout(() => {
          fetchProviders()
        }, 1000)
      } else {
        throw new Error(data.error || '切换失败')
      }

    } catch (err) {
      const errorMsg = `切换提供商失败: ${err.message}`
      setError(errorMsg)
      addDebugInfo(errorMsg)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchProviders()
  }, [])

  return (
    <div style={{ padding: '20px', border: '1px solid #ddd', borderRadius: '8px', margin: '20px 0' }}>
      <h3>🤖 AI提供商管理</h3>
      
      {/* 提供商状态部分 */}
      <div style={{ marginBottom: '20px' }}>
        <h4>提供商状态</h4>
        {providers.length > 0 ? (
          <div>
            {providers.map(provider => (
              <div 
                key={provider.id}
                style={{
                  padding: '10px',
                  margin: '5px 0',
                  border: '1px solid #ddd',
                  borderRadius: '4px',
                  backgroundColor: '#f8f9fa',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center'
                }}
              >
                <div>
                  <div style={{ fontWeight: 'bold', display: 'flex', alignItems: 'center' }}>
                    <span style={{ 
                      width: '10px', 
                      height: '10px', 
                      borderRadius: '50%', 
                      backgroundColor: provider.status === 'available' ? 'green' : 'red',
                      marginRight: '8px'
                    }}></span>
                    {provider.name}
                  </div>
                  <div style={{ fontSize: '12px', color: '#666' }}>
                    成功率: % | 响应时间: s
                  </div>
                </div>
                <div style={{ display: 'flex', gap: '10px' }}>
                  <button
                    onClick={() => testProvider(provider.id)}
                    disabled={testingProvider === provider.id}
                    style={{
                      padding: '4px 12px',
                      backgroundColor: testingProvider === provider.id ? '#6c757d' : '#007bff',
                      color: 'white',
                      border: 'none',
                      borderRadius: '4px',
                      cursor: testingProvider === provider.id ? 'not-allowed' : 'pointer',
                      fontSize: '12px'
                    }}
                  >
                    {testingProvider === provider.id ? '测试中...' : '测试连接'}
                  </button>
                  <button
                    onClick={() => selectProvider(provider.id)}
                    disabled={loading || currentProvider === provider.id}
                    style={{
                      padding: '4px 12px',
                      backgroundColor: currentProvider === provider.id ? '#28a745' : 
                                     provider.status === 'available' ? '#17a2b8' : '#dc3545',
                      color: 'white',
                      border: 'none',
                      borderRadius: '4px',
                      cursor: loading || currentProvider === provider.id ? 'not-allowed' : 'pointer',
                      fontSize: '12px'
                    }}
                  >
                    {currentProvider === provider.id ? '当前使用' : 
                     provider.status === 'available' ? '选择使用' : '不可用'}
                  </button>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div style={{ padding: '20px', textAlign: 'center', color: '#666' }}>
            {loading ? '正在加载提供商...' : '暂无可用提供商'}
          </div>
        )}
      </div>

      {/* 切换提供商部分 */}
      <div style={{ marginBottom: '20px' }}>
        <h4>切换提供商</h4>
        <div style={{ marginBottom: '10px' }}>
          <label style={{ display: 'block', marginBottom: '5px', fontSize: '14px' }}>
            选择提供商
          </label>
          <select
            value={selectedProvider}
            onChange={(e) => setSelectedProvider(e.target.value)}
            style={{
              width: '100%',
              padding: '8px',
              border: '1px solid #ddd',
              borderRadius: '4px',
              fontSize: '14px'
            }}
          >
            <option value="">请选择提供商</option>
            {providers.map(provider => (
              <option key={provider.id} value={provider.id}>
                {provider.name}
              </option>
            ))}
          </select>
        </div>
        
        <div style={{ display: 'flex', gap: '10px' }}>
          <button
            onClick={handleProviderSwitch}
            disabled={loading || !selectedProvider}
            style={{
              padding: '8px 16px',
              backgroundColor: '#28a745',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: loading || !selectedProvider ? 'not-allowed' : 'pointer',
              opacity: loading || !selectedProvider ? 0.6 : 1
            }}
          >
            {loading ? '切换中...' : '切换提供商'}
          </button>
          
          <button
            onClick={fetchProviders}
            disabled={loading}
            style={{
              padding: '8px 16px',
              backgroundColor: '#6c757d',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: loading ? 'not-allowed' : 'pointer'
            }}
          >
            刷新状态
          </button>
        </div>
      </div>

      {error && (
        <div style={{ 
          padding: '10px', 
          backgroundColor: '#f8d7da', 
          color: '#721c24', 
          border: '1px solid #f5c6cb',
          borderRadius: '4px',
          marginBottom: '20px'
        }}>
          ❌ {error}
        </div>
      )}

      <div style={{ marginBottom: '20px' }}>
        <h4>当前提供商: {providers.find(p => p.id === currentProvider)?.name || '未选择'}</h4>
        {currentModel && (
          <div style={{ 
            padding: '10px', 
            backgroundColor: '#e7f3ff', 
            border: '1px solid #007bff',
            borderRadius: '4px',
            marginTop: '10px'
          }}>
            <strong>🤖 当前AI模型:</strong> {currentModel}
            <br />
            <strong>📡 提供商:</strong> {currentProvider?.toUpperCase()}
            <br />
            <strong>🔄 状态:</strong> <span style={{ color: 'green' }}>已激活，全局生效</span>
          </div>
        )}
      </div>

      <div style={{ 
        backgroundColor: '#f8f9fa', 
        border: '1px solid #dee2e6',
        borderRadius: '4px',
        padding: '10px',
        maxHeight: '200px',
        overflowY: 'auto'
      }}>
        <h4>调试日志:</h4>
        {debugInfo.length > 0 ? (
          <div style={{ fontFamily: 'monospace', fontSize: '12px' }}>
            {debugInfo.map((info, index) => (
              <div key={index}>{info}</div>
            ))}
          </div>
        ) : (
          <div style={{ color: '#666', fontStyle: 'italic' }}>暂无日志</div>
        )}
      </div>
    </div>
  )
}

export default SimpleProviderSelector