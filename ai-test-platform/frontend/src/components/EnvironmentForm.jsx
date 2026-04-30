import { useState, useEffect } from 'react'
import api from '../services/api'
import { useToast } from './ui/Toast'

export default function EnvironmentForm({ projectId, environment, onClose, onSaved }) {
  const toast = useToast()
  const [loading, setLoading] = useState(false)
  const [formData, setFormData] = useState({
    project_id: projectId,
    name: '',
    base_url: '',
    description: '',
    is_protected: false,
    allow_write: true,
    timeout_seconds: 30,
    retry_count: 0
  })

  useEffect(() => {
    if (environment) {
      setFormData({
        project_id: projectId,
        name: environment.name || '',
        base_url: environment.base_url || '',
        description: environment.description || '',
        is_protected: environment.is_protected || false,
        allow_write: environment.allow_write !== false,
        timeout_seconds: environment.timeout_seconds || 30,
        retry_count: environment.retry_count || 0
      })
    }
  }, [environment, projectId])

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)

    try {
      if (environment) {
        await api.v2.environments.update(environment.id, formData)
        toast.success('环境更新成功')
      } else {
        await api.v2.environments.create(formData)
        toast.success('环境创建成功')
      }
      onSaved()
    } catch (error) {
      toast.error(`操作失败: ${error.message}`)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-2xl max-h-[90vh] overflow-y-auto">
        <div className="p-6 border-b border-slate-200">
          <h2 className="text-xl font-semibold text-slate-900">
            {environment ? '编辑环境' : '新建环境'}
          </h2>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">
              环境类型 <span className="text-red-500">*</span>
            </label>
            <select
              required
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              className="w-full px-3 py-2 border border-slate-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">请选择环境类型</option>
              <option value="dev">开发环境 (dev)</option>
              <option value="test">测试环境 (test)</option>
              <option value="staging">预发布环境 (staging)</option>
              <option value="prod">生产环境 (prod)</option>
            </select>
            <p className="text-xs text-slate-500 mt-1">
              环境类型必须是 dev, test, staging, prod 之一
            </p>
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">
              Base URL <span className="text-red-500">*</span>
            </label>
            <input
              type="url"
              required
              value={formData.base_url}
              onChange={(e) => setFormData({ ...formData, base_url: e.target.value })}
              placeholder="https://api.example.com"
              className="w-full px-3 py-2 border border-slate-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <p className="text-xs text-slate-500 mt-1">
              API的基础URL，例如：https://api.example.com
            </p>
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">
              描述
            </label>
            <textarea
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              placeholder="环境描述信息"
              className="w-full px-3 py-2 border border-slate-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              rows={2}
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">
                超时时间（秒）
              </label>
              <input
                type="number"
                min="1"
                max="300"
                value={formData.timeout_seconds}
                onChange={(e) => setFormData({ ...formData, timeout_seconds: parseInt(e.target.value) })}
                className="w-full px-3 py-2 border border-slate-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">
                重试次数
              </label>
              <input
                type="number"
                min="0"
                max="5"
                value={formData.retry_count}
                onChange={(e) => setFormData({ ...formData, retry_count: parseInt(e.target.value) })}
                className="w-full px-3 py-2 border border-slate-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>

          <div className="space-y-3">
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={formData.is_protected}
                onChange={(e) => setFormData({ ...formData, is_protected: e.target.checked })}
                className="w-4 h-4 text-blue-600 border-slate-300 rounded focus:ring-blue-500"
              />
              <span className="text-sm text-slate-700">
                保护环境（需要额外确认才能执行测试）
              </span>
            </label>

            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={formData.allow_write}
                onChange={(e) => setFormData({ ...formData, allow_write: e.target.checked })}
                className="w-4 h-4 text-blue-600 border-slate-300 rounded focus:ring-blue-500"
              />
              <span className="text-sm text-slate-700">
                允许写操作测试（POST/PUT/DELETE等）
              </span>
            </label>
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
              {loading ? '保存中...' : (environment ? '更新' : '创建')}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
