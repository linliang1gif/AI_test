import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Play, Edit, Trash2, Copy, Code, FileText, AlertCircle } from 'lucide-react'
import PageHeader from '../components/PageHeader'
import DetailCard from '../components/DetailCard'
import StatusBadge from '../components/StatusBadge'
import MetaInfo from '../components/MetaInfo'
import EmptyState from '../components/EmptyState'
import ConfirmDialog from '../components/ui/ConfirmDialog'
import { useToast } from '../components/ui/Toast'
import { SkeletonDetailPage } from '../components/ui/Skeleton'

export default function ApiDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const toast = useToast()
  const [loading, setLoading] = useState(true)
  const [api, setApi] = useState(null)
  const [activeTab, setActiveTab] = useState('params')
  const [showDeleteDialog, setShowDeleteDialog] = useState(false)
  const [deleting, setDeleting] = useState(false)
  const [executing, setExecuting] = useState(false)

  useEffect(() => {
    loadApi()
  }, [id])

  const loadApi = async () => {
    setLoading(true)
    try {
      setTimeout(() => {
        setApi({
          id: id,
          name: '用户登录接口',
          path: '/api/v1/auth/login',
          method: 'POST',
          description: '用户登录认证接口，支持用户名密码登录',
          module: '用户认证',
          status: 'active',
          version: 'v1.0',
          params: [
            { name: 'username', type: 'string', required: true, description: '用户名或邮箱' },
            { name: 'password', type: 'string', required: true, description: '登录密码' },
            { name: 'remember', type: 'boolean', required: false, description: '记住登录状态' }
          ],
          headers: [
            { name: 'Content-Type', value: 'application/json', required: true },
            { name: 'X-Client-Version', value: '1.0.0', required: false }
          ],
          responseExample: {
            success: true,
            data: {
              token: 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...',
              user: {
                id: 1001,
                username: 'test@example.com',
                nickname: '测试用户'
              }
            }
          },
          errorCodes: [
            { code: 400, message: '参数错误' },
            { code: 401, message: '用户名或密码错误' },
            { code: 429, message: '请求过于频繁' }
          ]
        })
        setLoading(false)
      }, 500)
    } catch (error) {
      console.error('加载失败:', error)
      setLoading(false)
    }
  }

  const handleExecute = async () => {
    setExecuting(true)
    try {
      await new Promise(resolve => setTimeout(resolve, 1500))
      toast.success('API测试执行成功')
    } catch (error) {
      toast.error('执行失败: ' + error.message)
    } finally {
      setExecuting(false)
    }
  }

  const handleCopyPath = () => {
    navigator.clipboard.writeText(api.path)
    toast.success('API路径已复制')
  }

  const handleDelete = async () => {
    setDeleting(true)
    try {
      await new Promise(resolve => setTimeout(resolve, 500))
      toast.success('删除成功')
      setTimeout(() => navigate('/api-explorer'), 500)
    } catch (error) {
      toast.error('删除失败: ' + error.message)
      setDeleting(false)
    }
  }

  if (loading) {
    return <SkeletonDetailPage />
  }

  if (!api) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <EmptyState
          title="API不存在"
          description="该API可能已被删除或您没有访问权限"
          action={
            <button
              onClick={() => navigate('/api-explorer')}
              className="px-4 py-2 bg-slate-700 text-white rounded-md text-sm hover:bg-slate-800"
            >
              返回列表
            </button>
          }
        />
      </div>
    )
  }

  const methodColors = {
    GET: 'bg-green-100 text-green-700 border-green-300',
    POST: 'bg-blue-100 text-blue-700 border-blue-300',
    PUT: 'bg-yellow-100 text-yellow-700 border-yellow-300',
    DELETE: 'bg-red-100 text-red-700 border-red-300'
  }

  return (
    <div className="min-h-screen bg-slate-50">
      <PageHeader
        showBack={true}
        breadcrumbs={[
          { label: 'API管理', href: '/api-explorer' },
          { label: api.name }
        ]}
        title={api.name}
        description={api.description}
        meta={
          <div className="flex items-center space-x-3 mt-2">
            <span className={`px-3 py-1 rounded-md text-sm font-medium border ${methodColors[api.method]}`}>
              {api.method}
            </span>
            <StatusBadge status={api.status === 'active' ? '启用' : '禁用'} type={api.status === 'active' ? 'success' : 'default'} />
            <span className="text-sm text-slate-600">版本: {api.version}</span>
          </div>
        }
        actions={[
          {
            label: executing ? '测试中...' : '测试接口',
            icon: <Play className="w-4 h-4" />,
            variant: 'primary',
            onClick: handleExecute,
            disabled: executing
          },
          {
            label: '复制路径',
            icon: <Copy className="w-4 h-4" />,
            onClick: handleCopyPath
          },
          {
            label: '编辑',
            icon: <Edit className="w-4 h-4" />,
            onClick: () => navigate(`/api-explorer/${id}/edit`)
          }
        ]}
      />

      <div className="max-w-[1400px] mx-auto px-6 py-6 space-y-6">
        {/* 基本信息 */}
        <DetailCard title="基本信息">
          <div className="space-y-4">
            <div className="flex items-center space-x-3 p-3 bg-slate-50 rounded-md border border-slate-200 font-mono text-sm">
              <span className={`px-2 py-1 rounded text-xs font-bold ${methodColors[api.method]}`}>
                {api.method}
              </span>
              <span className="text-slate-700">{api.path}</span>
              <button onClick={handleCopyPath} className="ml-auto text-slate-500 hover:text-slate-700">
                <Copy className="w-4 h-4" />
              </button>
            </div>
            <MetaInfo
              items={[
                { label: '所属模块', value: api.module },
                { label: '版本', value: api.version },
                { label: '状态', value: api.status === 'active' ? '启用' : '禁用' }
              ]}
            />
          </div>
        </DetailCard>

        {/* Tab标签页 */}
        <div className="bg-white rounded-md border border-slate-200">
          <div className="border-b border-slate-200">
            <nav className="flex space-x-8 px-6">
              {[
                { key: 'params', label: '请求参数' },
                { key: 'response', label: '响应示例' },
                { key: 'errors', label: '错误码' }
              ].map(tab => (
                <button
                  key={tab.key}
                  onClick={() => setActiveTab(tab.key)}
                  className={`py-4 border-b-2 transition-colors text-sm font-medium ${
                    activeTab === tab.key
                      ? 'border-slate-700 text-slate-900'
                      : 'border-transparent text-slate-600 hover:text-slate-900'
                  }`}
                >
                  {tab.label}
                </button>
              ))}
            </nav>
          </div>

          <div className="p-6">
            {activeTab === 'params' && (
              <div className="space-y-6">
                {/* Headers */}
                <div>
                  <h4 className="text-sm font-semibold text-slate-900 mb-3">请求头</h4>
                  <div className="border border-slate-200 rounded-md overflow-hidden">
                    <table className="w-full text-sm">
                      <thead className="bg-slate-50">
                        <tr>
                          <th className="px-4 py-2 text-left font-medium text-slate-700">参数名</th>
                          <th className="px-4 py-2 text-left font-medium text-slate-700">值</th>
                          <th className="px-4 py-2 text-left font-medium text-slate-700">必填</th>
                        </tr>
                      </thead>
                      <tbody>
                        {api.headers.map((header, index) => (
                          <tr key={index} className="border-t border-slate-200">
                            <td className="px-4 py-2 font-mono text-slate-700">{header.name}</td>
                            <td className="px-4 py-2 text-slate-600">{header.value}</td>
                            <td className="px-4 py-2">
                              {header.required ? (
                                <span className="text-red-600">是</span>
                              ) : (
                                <span className="text-slate-400">否</span>
                              )}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>

                {/* Body参数 */}
                <div>
                  <h4 className="text-sm font-semibold text-slate-900 mb-3">Body参数</h4>
                  <div className="border border-slate-200 rounded-md overflow-hidden">
                    <table className="w-full text-sm">
                      <thead className="bg-slate-50">
                        <tr>
                          <th className="px-4 py-2 text-left font-medium text-slate-700">参数名</th>
                          <th className="px-4 py-2 text-left font-medium text-slate-700">类型</th>
                          <th className="px-4 py-2 text-left font-medium text-slate-700">必填</th>
                          <th className="px-4 py-2 text-left font-medium text-slate-700">说明</th>
                        </tr>
                      </thead>
                      <tbody>
                        {api.params.map((param, index) => (
                          <tr key={index} className="border-t border-slate-200">
                            <td className="px-4 py-2 font-mono text-slate-700">{param.name}</td>
                            <td className="px-4 py-2">
                              <span className="px-2 py-1 bg-blue-50 text-blue-700 rounded text-xs">
                                {param.type}
                              </span>
                            </td>
                            <td className="px-4 py-2">
                              {param.required ? (
                                <span className="text-red-600">是</span>
                              ) : (
                                <span className="text-slate-400">否</span>
                              )}
                            </td>
                            <td className="px-4 py-2 text-slate-600">{param.description}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>
            )}

            {activeTab === 'response' && (
              <div>
                <h4 className="text-sm font-semibold text-slate-900 mb-3">成功响应示例</h4>
                <div className="bg-slate-900 rounded-md p-4 overflow-x-auto">
                  <pre className="text-sm text-green-400 font-mono">
                    {JSON.stringify(api.responseExample, null, 2)}
                  </pre>
                </div>
              </div>
            )}

            {activeTab === 'errors' && (
              <div>
                <h4 className="text-sm font-semibold text-slate-900 mb-3">错误码说明</h4>
                <div className="space-y-2">
                  {api.errorCodes.map((error, index) => (
                    <div key={index} className="flex items-center space-x-4 p-3 border border-slate-200 rounded-md">
                      <span className="px-3 py-1 bg-red-50 text-red-700 rounded font-mono text-sm font-medium">
                        {error.code}
                      </span>
                      <span className="text-sm text-slate-700">{error.message}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* 危险操作 */}
        <DetailCard title="危险操作">
          <button
            onClick={() => setShowDeleteDialog(true)}
            className="flex items-center space-x-2 px-4 py-2 text-red-600 border border-red-300 rounded-md hover:bg-red-50 transition-colors"
          >
            <Trash2 className="w-4 h-4" />
            <span className="text-sm font-medium">删除此API</span>
          </button>
        </DetailCard>
      </div>

      <ConfirmDialog
        isOpen={showDeleteDialog}
        onClose={() => setShowDeleteDialog(false)}
        onConfirm={handleDelete}
        title="删除API"
        message="确定要删除此API吗？此操作不可恢复，所有相关的测试用例也将受到影响。"
        confirmText="删除"
        cancelText="取消"
        type="danger"
        loading={deleting}
      />
    </div>
  )
}
