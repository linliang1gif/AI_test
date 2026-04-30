import { useState } from 'react'
import api from '../services/api'

export default function SVNInput({ onSuccess, onCancel }) {
  const [svnUrl, setSvnUrl] = useState('')
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [isGenerating, setIsGenerating] = useState(false)
  const [progress, setProgress] = useState(0)
  const [step, setStep] = useState('')
  const [showPassword, setShowPassword] = useState(false)

  const handleGenerate = async () => {
    if (!svnUrl.trim()) {
      alert('请输入 SVN 地址')
      return
    }

    setIsGenerating(true)
    setProgress(0)
    setStep('📥 连接 SVN 服务器...')

    try {
      // 模拟进度更新
      const progressInterval = setInterval(() => {
        setProgress(prev => {
          if (prev >= 90) return prev
          return prev + 3
        })
      }, 800)

      // 更新步骤提示
      setTimeout(() => setStep('📄 下载需求文档...'), 1000)
      setTimeout(() => setStep('📖 解析文档内容...'), 3000)
      setTimeout(() => setStep('🔍 分析需求模块...'), 6000)
      setTimeout(() => setStep('🎯 生成测试用例...'), 10000)

      const result = await api.testCases.generateFromSVN({
        svn_url: svnUrl,
        svn_username: username || undefined,
        svn_password: password || undefined,
      })

      clearInterval(progressInterval)
      setProgress(100)
      setStep('✅ 生成完成!')

      if (result.success) {
        setTimeout(() => {
          alert(`成功从 SVN 生成 ${result.count} 个测试用例!`)
          if (onSuccess) {
            onSuccess(result)
          }
        }, 500)
      } else {
        alert('生成失败: ' + (result.error || result.detail || '未知错误'))
        setProgress(0)
        setStep('')
      }
    } catch (error) {
      alert('生成失败: ' + error.message)
      setProgress(0)
      setStep('')
    } finally {
      setIsGenerating(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-2xl mx-4">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900">从 SVN 生成测试用例</h3>
          <p className="text-sm text-gray-500 mt-1">
            支持 .docx, .txt, .md, .pdf 格式的需求文档
          </p>
        </div>

        <div className="px-6 py-4 space-y-4">
          {/* SVN URL */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              SVN 地址 <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              value={svnUrl}
              onChange={(e) => setSvnUrl(e.target.value)}
              placeholder="svn://server/project/docs/requirement.docx"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              disabled={isGenerating}
            />
            <p className="text-xs text-gray-500 mt-1">
              示例: svn://192.168.1.100/project/docs/v1.2.2需求.docx
            </p>
          </div>

          {/* Username */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              用户名 (可选)
            </label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="SVN 用户名"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              disabled={isGenerating}
            />
          </div>

          {/* Password */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              密码 (可选)
            </label>
            <div className="relative">
              <input
                type={showPassword ? 'text' : 'password'}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="SVN 密码"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                disabled={isGenerating}
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-700"
                disabled={isGenerating}
              >
                {showPassword ? '🙈' : '👁️'}
              </button>
            </div>
          </div>

          {/* Progress */}
          {isGenerating && (
            <div className="space-y-2">
              <div className="flex items-center justify-between text-sm">
                <span className="text-gray-600">{step}</span>
                <span className="text-blue-600 font-medium">{progress}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${progress}%` }}
                />
              </div>
            </div>
          )}

          {/* Tips */}
          <div className="bg-blue-50 border border-blue-200 rounded-md p-3">
            <p className="text-sm text-blue-800">
              💡 提示:
            </p>
            <ul className="text-xs text-blue-700 mt-1 space-y-1 ml-4 list-disc">
              <li>如果 SVN 不需要认证，可以不填用户名和密码</li>
              <li>支持 svn://, http://, https:// 协议</li>
              <li>文件大小限制: 50 MB</li>
              <li>系统会根据文档复杂度自动生成 50-150 个测试用例</li>
            </ul>
          </div>
        </div>

        <div className="px-6 py-4 border-t border-gray-200 flex justify-end space-x-3">
          <button
            onClick={onCancel}
            disabled={isGenerating}
            className="px-4 py-2 text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            取消
          </button>
          <button
            onClick={handleGenerate}
            disabled={isGenerating || !svnUrl.trim()}
            className="px-4 py-2 text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isGenerating ? '生成中...' : '开始生成'}
          </button>
        </div>
      </div>
    </div>
  )
}
