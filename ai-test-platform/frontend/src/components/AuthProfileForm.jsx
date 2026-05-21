import { useState, useEffect } from 'react'
import api from '../services/api'
import { useToast } from './ui/Toast'

export default function AuthProfileForm({ environment, onClose, onSaved }) {
  const toast = useToast()
  const [loading, setLoading] = useState(false)
  const [loadingProfile, setLoadingProfile] = useState(true)
  const [existingProfile, setExistingProfile] = useState(null)
  const [authType, setAuthType] = useState('none')
  const [authConfig, setAuthConfig] = useState({})
  const [defaultHeaders, setDefaultHeaders] = useState([{ key: '', value: '' }])
  const [oauth2Testing, setOauth2Testing] = useState(false)
  const [oauth2TestResult, setOauth2TestResult] = useState(null)

  useEffect(() => {
    loadAuthProfile()
  }, [environment.id])

  const loadAuthProfile = async () => {
    try {
      setLoadingProfile(true)
      const profile = await api.v2.environments.getAuthProfile(environment.id)
      if (profile) {
        setExistingProfile(profile)
        setAuthType(profile.auth_type || 'none')
        
        let config = {}
        if (profile.auth_config_masked) {
          config = profile.auth_config_masked
        }
        setAuthConfig(config)

        // 解析default_headers
        if (profile.default_headers && Object.keys(profile.default_headers).length > 0) {
          const headers = Object.entries(profile.default_headers).map(([key, value]) => ({ key, value }))
          setDefaultHeaders(headers)
        }
      }
    } catch (error) {
      // 404表示还没有鉴权配置，这是正常的
      if (!error.message.includes('404')) {
        console.error('加载鉴权配置失败:', error)
      }
    } finally {
      setLoadingProfile(false)
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)

    try {
      // 构建headers对象
      const headers = {}
      defaultHeaders.forEach(h => {
        if (h.key && h.value) {
          headers[h.key] = h.value
        }
      })

      const hasMaskedSecret = Object.values(authConfig || {}).some(value =>
        typeof value === 'string' && value.includes('****')
      )

      const data = {
        environment_id: environment.id,
        auth_type: authType,
        default_headers: headers
      }
      if (!existingProfile || !hasMaskedSecret) {
        data.auth_config = authConfig
      }

      if (existingProfile) {
        await api.v2.authProfiles.update(existingProfile.id, data)
        toast.success('鉴权配置更新成功')
      } else {
        await api.v2.authProfiles.create(data)
        toast.success('鉴权配置创建成功')
      }
      onSaved()
    } catch (error) {
      let message = error.message || String(error)
      const jsonStart = message.indexOf('{')
      if (jsonStart >= 0) {
        try {
          const body = JSON.parse(message.slice(jsonStart))
          const detail = body.detail
          message = typeof detail === 'object'
            ? (detail.message || JSON.stringify(detail))
            : (detail || body.message || message)
        } catch {}
      }
      toast.error(`操作失败: ${message}`)
    } finally {
      setLoading(false)
    }
  }

  const addHeader = () => {
    setDefaultHeaders([...defaultHeaders, { key: '', value: '' }])
  }

  const removeHeader = (index) => {
    setDefaultHeaders(defaultHeaders.filter((_, i) => i !== index))
  }

  const updateHeader = (index, field, value) => {
    const newHeaders = [...defaultHeaders]
    newHeaders[index][field] = value
    setDefaultHeaders(newHeaders)
  }

  if (loadingProfile) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg shadow-xl p-6">
          <div className="text-slate-600">加载中...</div>
        </div>
      </div>
    )
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-3xl max-h-[90vh] overflow-y-auto">
        <div className="p-6 border-b border-slate-200">
          <h2 className="text-xl font-semibold text-slate-900">
            配置鉴权 - {environment.name}
          </h2>
          <p className="text-sm text-slate-600 mt-1">
            为环境 {environment.base_url} 配置鉴权方式
          </p>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          {/* 鉴权类型 */}
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-2">
              鉴权类型 <span className="text-red-500">*</span>
            </label>
            <select
              value={authType}
              onChange={(e) => {
                setAuthType(e.target.value)
                setAuthConfig({})
              }}
              className="w-full px-3 py-2 border border-slate-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="none">无鉴权</option>
              <option value="bearer">Bearer Token</option>
              <option value="apikey">API Key</option>
              <option value="basic">Basic Auth</option>
              <option value="oauth2">OAuth 2.0</option>
              <option value="custom">自定义</option>
            </select>
          </div>

          {/* Bearer Token */}
          {authType === 'bearer' && (
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">
                Token <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                required
                value={authConfig.token || ''}
                onChange={(e) => setAuthConfig({ ...authConfig, token: e.target.value })}
                placeholder="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
                className="w-full px-3 py-2 border border-slate-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono text-sm"
              />
              <p className="text-xs text-slate-500 mt-1">
                将在请求头中添加: Authorization: Bearer {'{token}'}
              </p>
            </div>
          )}

          {/* API Key */}
          {authType === 'apikey' && (
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">
                  API Key 名称 <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  required
                  value={authConfig.key_name || ''}
                  onChange={(e) => setAuthConfig({ ...authConfig, key_name: e.target.value })}
                  placeholder="X-API-Key"
                  className="w-full px-3 py-2 border border-slate-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">
                  API Key 值 <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  required
                  value={authConfig.key_value || ''}
                  onChange={(e) => setAuthConfig({ ...authConfig, key_value: e.target.value })}
                  placeholder="your-api-key-here"
                  className="w-full px-3 py-2 border border-slate-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono text-sm"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">
                  位置
                </label>
                <select
                  value={authConfig.in || 'header'}
                  onChange={(e) => setAuthConfig({ ...authConfig, in: e.target.value })}
                  className="w-full px-3 py-2 border border-slate-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="header">Header</option>
                  <option value="query">Query Parameter</option>
                </select>
              </div>
            </div>
          )}

          {/* Basic Auth */}
          {authType === 'basic' && (
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">
                  用户名 <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  required
                  value={authConfig.username || ''}
                  onChange={(e) => setAuthConfig({ ...authConfig, username: e.target.value })}
                  className="w-full px-3 py-2 border border-slate-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">
                  密码 <span className="text-red-500">*</span>
                </label>
                <input
                  type="password"
                  required
                  value={authConfig.password || ''}
                  onChange={(e) => setAuthConfig({ ...authConfig, password: e.target.value })}
                  className="w-full px-3 py-2 border border-slate-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>
          )}

          {/* OAuth 2.0 */}
          {authType === 'oauth2' && (
            <div className="space-y-4">
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 text-sm text-blue-800">
                <strong>自动获取 Token</strong>
                <p className="text-xs mt-1">配置 OAuth2 端点信息后，执行测试时将自动获取并缓存 Token，无需手动粘贴。</p>
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">
                  Token URL <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  required
                  value={authConfig.token_url || ''}
                  onChange={(e) => setAuthConfig({ ...authConfig, token_url: e.target.value })}
                  placeholder="https://sit-sso.szhibu.com/oauth/token"
                  className="w-full px-3 py-2 border border-slate-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono text-sm"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">
                  Client Authorization (Basic)
                </label>
                <input
                  type="text"
                  value={authConfig.client_authorization || ''}
                  onChange={(e) => setAuthConfig({ ...authConfig, client_authorization: e.target.value })}
                  placeholder="c2l0X3VzZXJfY2VudGVyOjEyMzQ1Ng=="
                  className="w-full px-3 py-2 border border-slate-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono text-sm"
                />
                <p className="text-xs text-slate-500 mt-1">Base64 编码的 client_id:client_secret</p>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">
                    用户名 <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    required
                    value={authConfig.username || ''}
                    onChange={(e) => setAuthConfig({ ...authConfig, username: e.target.value })}
                    placeholder="blueRecycle"
                    className="w-full px-3 py-2 border border-slate-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">
                    密码 <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="password"
                    required
                    value={authConfig.password || ''}
                    onChange={(e) => setAuthConfig({ ...authConfig, password: e.target.value })}
                    placeholder=""
                    className="w-full px-3 py-2 border border-slate-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Grant Type</label>
                  <select
                    value={authConfig.grant_type || 'password'}
                    onChange={(e) => setAuthConfig({ ...authConfig, grant_type: e.target.value })}
                    className="w-full px-3 py-2 border border-slate-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="password">password</option>
                    <option value="client_credentials">client_credentials</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Scope</label>
                  <input
                    type="text"
                    value={authConfig.scope || 'all'}
                    onChange={(e) => setAuthConfig({ ...authConfig, scope: e.target.value })}
                    className="w-full px-3 py-2 border border-slate-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </div>
              <div>
                <button
                  type="button"
                  disabled={oauth2Testing || !authConfig.token_url}
                  onClick={async () => {
                    setOauth2Testing(true)
                    setOauth2TestResult(null)
                    try {
                      const res = await fetch('/api/v2/execute/auth/oauth2/test', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(authConfig),
                      })
                      const data = await res.json()
                      setOauth2TestResult(data)
                      if (data.success) {
                        toast.success('OAuth2 连通性测试成功!')
                      } else {
                        toast.error(data.message || '测试失败')
                      }
                    } catch (err) {
                      setOauth2TestResult({ success: false, message: err.message })
                      toast.error('测试请求失败: ' + err.message)
                    } finally {
                      setOauth2Testing(false)
                    }
                  }}
                  className="w-full px-4 py-2 bg-emerald-600 text-white rounded-md hover:bg-emerald-700 disabled:opacity-50 transition-colors text-sm font-medium"
                >
                  {oauth2Testing ? '测试中...' : '测试连通性'}
                </button>
                {oauth2TestResult && (
                  <div className={`mt-2 p-2 rounded text-sm ${
                    oauth2TestResult.success
                      ? 'bg-green-50 text-green-700 border border-green-200'
                      : 'bg-red-50 text-red-700 border border-red-200'
                  }`}>
                    {oauth2TestResult.success
                      ? `Token 获取成功 (${oauth2TestResult.token_type}): ${oauth2TestResult.token_preview}`
                      : `失败: ${oauth2TestResult.message}`
                    }
                  </div>
                )}
              </div>
            </div>
          )}

          {/* 默认请求头 */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <label className="block text-sm font-medium text-slate-700">
                默认请求头
              </label>
              <button
                type="button"
                onClick={addHeader}
                className="text-sm text-blue-600 hover:text-blue-700"
              >
                + 添加
              </button>
            </div>
            <div className="space-y-2">
              {defaultHeaders.map((header, index) => (
                <div key={index} className="flex gap-2">
                  <input
                    type="text"
                    value={header.key}
                    onChange={(e) => updateHeader(index, 'key', e.target.value)}
                    placeholder="Header名称"
                    className="flex-1 px-3 py-2 border border-slate-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
                  />
                  <input
                    type="text"
                    value={header.value}
                    onChange={(e) => updateHeader(index, 'value', e.target.value)}
                    placeholder="Header值"
                    className="flex-1 px-3 py-2 border border-slate-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
                  />
                  <button
                    type="button"
                    onClick={() => removeHeader(index)}
                    className="px-3 py-2 text-red-600 hover:bg-red-50 rounded-md transition-colors"
                  >
                    删除
                  </button>
                </div>
              ))}
            </div>
            <p className="text-xs text-slate-500 mt-2">
              这些请求头将自动添加到所有API请求中
            </p>
          </div>

          <div className="flex gap-3 pt-4 border-t border-slate-200">
            <button
              type="button"
              onClick={onClose}
              disabled={loading}
              className="flex-1 px-4 py-2 border border-slate-300 text-slate-700 rounded-md hover:bg-slate-50 transition-colors disabled:opacity-50"
            >
              取消
            </button>
            <button
              type="submit"
              disabled={loading}
              className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors disabled:opacity-50"
            >
              {loading ? '保存中...' : (existingProfile ? '更新配置' : '创建配置')}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
