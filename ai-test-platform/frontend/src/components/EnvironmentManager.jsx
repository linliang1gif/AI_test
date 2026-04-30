import { useState } from 'react'
import EnvironmentForm from './EnvironmentForm'
import AuthProfileForm from './AuthProfileForm'
import api from '../services/api'
import { useToast } from './ui/Toast'

export default function EnvironmentManager({ projectId, environments, onUpdate }) {
  const toast = useToast()
  const [showEnvForm, setShowEnvForm] = useState(false)
  const [showAuthForm, setShowAuthForm] = useState(false)
  const [editingEnv, setEditingEnv] = useState(null)
  const [selectedEnvForAuth, setSelectedEnvForAuth] = useState(null)
  const [showTokenDialog, setShowTokenDialog] = useState(false)
  const [tokenEnvId, setTokenEnvId] = useState(null)
  const [tokenInput, setTokenInput] = useState('')
  const [tokenLoading, setTokenLoading] = useState(false)

  const handleQuickToken = (env) => {
    setTokenEnvId(env.id)
    setTokenInput('')
    setShowTokenDialog(true)
  }

  const handleSubmitToken = async () => {
    if (!tokenInput.trim()) { toast.error('请粘贴 Token'); return }
    setTokenLoading(true)
    try {
      const res = await fetch('/api/v2/test-cases/quick-token', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ token: tokenInput.trim(), environment_id: tokenEnvId })
      })
      const data = await res.json()
      if (data.success) {
        toast.success(data.message)
        setShowTokenDialog(false)
        onUpdate()
      } else {
        toast.error(data.detail || 'Token 更新失败')
      }
    } catch (e) {
      toast.error('请求失败: ' + e.message)
    } finally {
      setTokenLoading(false)
    }
  }

  const handleCreateEnv = () => {
    setEditingEnv(null)
    setShowEnvForm(true)
  }

  const handleEditEnv = (env) => {
    setEditingEnv(env)
    setShowEnvForm(true)
  }

  const handleDeleteEnv = async (envId) => {
    if (!confirm('确定要删除此环境吗？相关的鉴权配置也将被删除。')) return

    try {
      await api.v2.environments.delete(envId)
      toast.success('环境删除成功')
      onUpdate()
    } catch (error) {
      toast.error('删除失败: ' + error.message)
    }
  }

  const handleEnvSaved = () => {
    setShowEnvForm(false)
    setEditingEnv(null)
    onUpdate()
  }

  const handleConfigureAuth = (env) => {
    setSelectedEnvForAuth(env)
    setShowAuthForm(true)
  }

  const handleAuthSaved = () => {
    setShowAuthForm(false)
    setSelectedEnvForAuth(null)
    onUpdate()
  }

  const getEnvTypeBadge = (name) => {
    const types = {
      dev: { bg: 'bg-blue-100', text: 'text-blue-700', label: '开发' },
      test: { bg: 'bg-green-100', text: 'text-green-700', label: '测试' },
      staging: { bg: 'bg-yellow-100', text: 'text-yellow-700', label: '预发布' },
      prod: { bg: 'bg-red-100', text: 'text-red-700', label: '生产' }
    }
    const type = types[name] || { bg: 'bg-gray-100', text: 'text-gray-700', label: name }
    return (
      <span className={`px-2 py-1 rounded text-xs font-medium ${type.bg} ${type.text}`}>
        {type.label}
      </span>
    )
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <div className="text-sm text-slate-600">
          共 {environments.length} 个环境
        </div>
        <button
          onClick={handleCreateEnv}
          className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors text-sm"
        >
          + 新建环境
        </button>
      </div>

      {environments.length === 0 ? (
        <div className="bg-white border border-slate-200 rounded-lg p-12 text-center">
          <div className="text-4xl mb-4">🌍</div>
          <div className="text-slate-600 mb-2">暂无环境配置</div>
          <p className="text-sm text-slate-500 mb-4">
            环境用于配置不同的测试目标（开发/测试/生产等）
          </p>
          <button
            onClick={handleCreateEnv}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors text-sm"
          >
            创建第一个环境
          </button>
        </div>
      ) : (
        <div className="space-y-3">
          {environments.map(env => (
            <div
              key={env.id}
              className="bg-white border border-slate-200 rounded-lg p-4 hover:shadow-md transition-shadow"
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    {getEnvTypeBadge(env.name)}
                    <h3 className="font-medium text-slate-900">{env.name}</h3>
                  </div>
                  
                  <div className="space-y-1 text-sm">
                    <div className="flex items-center gap-2">
                      <span className="text-slate-500">Base URL:</span>
                      <span className="font-mono text-slate-700">{env.base_url}</span>
                    </div>
                    
                    {env.description && (
                      <div className="text-slate-600">{env.description}</div>
                    )}

                    <div className="flex items-center gap-4 text-xs text-slate-500 mt-2">
                      <span>超时: {env.timeout_seconds || 30}s</span>
                      <span>重试: {env.retry_count || 0}次</span>
                      {env.is_protected && (
                        <span className="text-orange-600">🔒 保护环境</span>
                      )}
                      {!env.allow_write && (
                        <span className="text-orange-600">⚠️ 只读</span>
                      )}
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-2 ml-4">
                  <button
                    onClick={() => handleQuickToken(env)}
                    className="px-3 py-1.5 text-sm border border-amber-300 text-amber-600 rounded-md hover:bg-amber-50 transition-colors"
                    title="快捷粘贴 Bearer Token"
                  >
                    🔑 Token
                  </button>
                  <button
                    onClick={() => handleConfigureAuth(env)}
                    className="px-3 py-1.5 text-sm border border-purple-300 text-purple-600 rounded-md hover:bg-purple-50 transition-colors"
                    title="配置鉴权"
                  >
                    🔐 鉴权
                  </button>
                  <button
                    onClick={() => handleEditEnv(env)}
                    className="px-3 py-1.5 text-sm border border-slate-300 text-slate-700 rounded-md hover:bg-slate-50 transition-colors"
                  >
                    编辑
                  </button>
                  <button
                    onClick={() => handleDeleteEnv(env.id)}
                    className="px-3 py-1.5 text-sm border border-red-300 text-red-600 rounded-md hover:bg-red-50 transition-colors"
                  >
                    删除
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* 环境表单对话框 */}
      {showEnvForm && (
        <EnvironmentForm
          projectId={projectId}
          environment={editingEnv}
          onClose={() => {
            setShowEnvForm(false)
            setEditingEnv(null)
          }}
          onSaved={handleEnvSaved}
        />
      )}

      {/* 鉴权配置对话框 */}
      {showAuthForm && selectedEnvForAuth && (
        <AuthProfileForm
          environment={selectedEnvForAuth}
          onClose={() => {
            setShowAuthForm(false)
            setSelectedEnvForAuth(null)
          }}
          onSaved={handleAuthSaved}
        />
      )}
      {/* Token 快捷粘贴对话框 */}
      {showTokenDialog && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-lg p-6">
            <h3 className="text-lg font-semibold mb-2">🔑 快捷更新 Token</h3>
            <p className="text-sm text-slate-500 mb-4">
              从浏览器 F12 → Network → 任意请求的 Authorization 头复制 Token（不含 "Bearer " 前缀）
            </p>
            <textarea
              className="w-full h-32 px-3 py-2 border border-slate-300 rounded-lg text-sm font-mono focus:ring-2 focus:ring-blue-500 focus:border-blue-500 resize-none"
              placeholder="粘贴 eyJhbGciOiJSUzI1NiIs... 格式的 JWT Token"
              value={tokenInput}
              onChange={e => setTokenInput(e.target.value)}
            />
            <div className="flex justify-end gap-3 mt-4">
              <button
                onClick={() => setShowTokenDialog(false)}
                className="px-4 py-2 text-sm border border-slate-300 rounded-md hover:bg-slate-50"
              >
                取消
              </button>
              <button
                onClick={handleSubmitToken}
                disabled={tokenLoading}
                className="px-4 py-2 text-sm bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
              >
                {tokenLoading ? '更新中...' : '确认更新'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
