import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { 
  Play, 
  Edit, 
  Trash2, 
  MoreVertical, 
  Clock, 
  User, 
  Calendar,
  Tag,
  FileText,
  AlertCircle
} from 'lucide-react'
import PageHeader from '../components/PageHeader'
import DetailCard from '../components/DetailCard'
import StatusBadge from '../components/StatusBadge'
import MetaInfo from '../components/MetaInfo'
import EmptyState from '../components/EmptyState'
import ConfirmDialog from '../components/ui/ConfirmDialog'
import { useToast } from '../components/ui/Toast'
import { SkeletonDetailPage } from '../components/ui/Skeleton'
import api from '../services/api'

export default function TestCaseDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const toast = useToast()
  const [loading, setLoading] = useState(true)
  const [testCase, setTestCase] = useState(null)
  const [activeTab, setActiveTab] = useState('detail')
  const [showMoreMenu, setShowMoreMenu] = useState(false)
  const [executing, setExecuting] = useState(false)
  const [showDeleteDialog, setShowDeleteDialog] = useState(false)
  const [deleting, setDeleting] = useState(false)

  useEffect(() => {
    loadTestCase()
  }, [id])

  const loadTestCase = async () => {
    setLoading(true)
    try {
      const data = await api.testCases.getAll()
      
      const cases = data.test_cases || data.data || []
      if (data.success && cases) {
        // 查找匹配的测试用例
        const foundCase = cases.find(tc => tc.id === id || tc.id === parseInt(id))
        
        if (foundCase) {
          // 转换后端数据格式为前端需要的格式
          setTestCase({
            id: foundCase.id,
            title: foundCase.title || '未命名测试用例',
            module: foundCase.module || '未分类',
            priority: foundCase.priority || 'medium',
            status: foundCase.status || 'pending',
            description: foundCase.description || '暂无描述',
            steps: foundCase.steps || foundCase.test_steps || [],
            expected: foundCase.expected_result || foundCase.expected || '暂无预期结果',
            preconditions: foundCase.preconditions || foundCase.pre_conditions || '无',
            testData: foundCase.test_data || foundCase.testData || {},
            creator: foundCase.creator || '未知',
            createdAt: foundCase.created_at || foundCase.createdAt || '-',
            updatedBy: foundCase.updated_by || foundCase.updatedBy || '-',
            updatedAt: foundCase.updated_at || foundCase.updatedAt || '-',
            version: foundCase.version || 'v1.0',
            project: foundCase.project || '默认项目',
            tags: foundCase.tags || [],
            executionHistory: foundCase.execution_history || foundCase.executionHistory || []
          })
        } else {
          console.warn('未找到测试用例:', id)
          setTestCase(null)
        }
      } else {
        console.error('API 返回数据格式错误:', data)
        setTestCase(null)
      }
      setLoading(false)
    } catch (error) {
      console.error('加载失败:', error)
      toast.error('加载测试用例失败: ' + error.message)
      setTestCase(null)
      setLoading(false)
    }
  }

  const handleExecute = async () => {
    setExecuting(true)
    try {
      const result = await api.testCases.execute(id)
      if (result.success) {
        toast.success('测试用例执行完成')
        navigate('/test-runs')
      } else {
        toast.error('执行失败: ' + (result.message || result.error || '未知错误'))
      }
    } catch (error) {
      toast.error('执行失败: ' + error.message)
    } finally {
      setExecuting(false)
    }
  }

  const handleEdit = () => {
    navigate(`/test-cases/${id}/edit`)
  }

  const handleDelete = async () => {
    setDeleting(true)
    try {
      // 调用后端删除 API
      const data = await api.testCases.batchDelete([id])
      
      if (data.success) {
        toast.success('删除成功')
        setTimeout(() => navigate('/test-cases'), 500)
      } else {
        toast.error('删除失败: ' + (data.message || '未知错误'))
        setDeleting(false)
      }
    } catch (error) {
      toast.error('删除失败: ' + error.message)
      setDeleting(false)
    }
  }

  const getStatusType = (status) => {
    const map = {
      passed: 'success',
      failed: 'error',
      pending: 'default'
    }
    return map[status] || 'default'
  }

  const getStatusLabel = (status) => {
    const map = {
      passed: '通过',
      failed: '失败',
      pending: '待执行'
    }
    return map[status] || status
  }

  const getPriorityType = (priority) => {
    const map = {
      high: 'error',
      medium: 'warning',
      low: 'info'
    }
    return map[priority] || 'default'
  }

  const getPriorityLabel = (priority) => {
    const map = {
      high: '高',
      medium: '中',
      low: '低'
    }
    return map[priority] || priority
  }

  if (loading) {
    return <SkeletonDetailPage />
  }

  if (!testCase) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <EmptyState
          title="测试用例不存在"
          description="该测试用例可能已被删除或您没有访问权限"
          action={
            <button
              onClick={() => navigate('/test-cases')}
              className="px-4 py-2 bg-slate-700 text-white rounded-md text-sm hover:bg-slate-800"
            >
              返回列表
            </button>
          }
        />
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-slate-50">
      {/* 页面头部 */}
      <PageHeader
        showBack={true}
        breadcrumbs={[
          { label: '测试管理', href: '/test-cases' },
          { label: '测试用例', href: '/test-cases' },
          { label: testCase.title }
        ]}
        title={testCase.title}
        description={`${testCase.module} · ${testCase.project}`}
        meta={
          <div className="flex items-center space-x-3 mt-2">
            <StatusBadge 
              status={getStatusLabel(testCase.status)} 
              type={getStatusType(testCase.status)} 
            />
            <StatusBadge 
              status={getPriorityLabel(testCase.priority)} 
              type={getPriorityType(testCase.priority)} 
            />
            {testCase.tags.map((tag, index) => (
              <span key={index} className="inline-flex items-center px-2 py-1 rounded-md text-xs bg-slate-100 text-slate-700 border border-slate-200">
                <Tag className="w-3 h-3 mr-1" />
                {tag}
              </span>
            ))}
          </div>
        }
        actions={[
          {
            label: executing ? '执行中...' : '执行测试',
            icon: <Play className="w-4 h-4" />,
            variant: 'primary',
            onClick: handleExecute,
            disabled: executing
          },
          {
            label: '编辑',
            icon: <Edit className="w-4 h-4" />,
            onClick: handleEdit
          },
          {
            label: '更多',
            icon: <MoreVertical className="w-4 h-4" />,
            onClick: () => setShowMoreMenu(!showMoreMenu)
          }
        ]}
      />

      {/* 更多操作下拉菜单 */}
      {showMoreMenu && (
        <div className="fixed inset-0 z-40" onClick={() => setShowMoreMenu(false)}>
          <div 
            className="absolute right-6 top-32 w-48 bg-white rounded-md shadow-lg border border-slate-200 py-1"
            onClick={(e) => e.stopPropagation()}
          >
            <button
              onClick={() => {
                setShowMoreMenu(false)
                setShowDeleteDialog(true)
              }}
              className="w-full px-4 py-2 text-left text-sm text-red-600 hover:bg-red-50 flex items-center"
            >
              <Trash2 className="w-4 h-4 mr-2" />
              删除用例
            </button>
          </div>
        </div>
      )}

      {/* 主内容区 */}
      <div className="max-w-[1400px] mx-auto px-4 sm:px-6 py-6 space-y-6">
        {/* 基本信息卡片 */}
        <DetailCard title="基本信息">
          <MetaInfo
            items={[
              { label: '创建人', value: testCase.creator },
              { label: '创建时间', value: testCase.createdAt },
              { label: '最后修改人', value: testCase.updatedBy },
              { label: '最后修改时间', value: testCase.updatedAt },
              { label: '版本号', value: testCase.version },
              { label: '所属项目', value: testCase.project },
              { label: '所属模块', value: testCase.module },
              { label: '用例ID', value: `TC-${testCase.id}` }
            ]}
          />
        </DetailCard>

        {/* Tab标签页 */}
        <div className="bg-white rounded-md border border-slate-200">
          {/* Tab导航 */}
          <div className="border-b border-slate-200 overflow-x-auto">
            <nav className="flex space-x-4 sm:space-x-8 px-4 sm:px-6 min-w-max">
              {[
                { key: 'detail', label: '用例详情', icon: FileText },
                { key: 'history', label: '执行历史', icon: Clock }
              ].map(tab => (
                <button
                  key={tab.key}
                  onClick={() => setActiveTab(tab.key)}
                  className={`flex items-center space-x-2 py-4 border-b-2 transition-colors ${
                    activeTab === tab.key
                      ? 'border-slate-700 text-slate-900'
                      : 'border-transparent text-slate-600 hover:text-slate-900'
                  }`}
                >
                  <tab.icon className="w-4 h-4" />
                  <span className="text-sm font-medium">{tab.label}</span>
                </button>
              ))}
            </nav>
          </div>

          {/* Tab内容 */}
          <div className="p-4 sm:p-6">
            {activeTab === 'detail' && (
              <div className="space-y-6">
                {/* 用例描述 */}
                <div>
                  <h4 className="text-sm font-semibold text-slate-900 mb-2">用例描述</h4>
                  <p className="text-sm text-slate-700 leading-relaxed">{testCase.description}</p>
                </div>

                {/* 前置条件 */}
                <div>
                  <h4 className="text-sm font-semibold text-slate-900 mb-2">前置条件</h4>
                  <p className="text-sm text-slate-700">{testCase.preconditions}</p>
                </div>

                {/* 测试步骤 */}
                <div>
                  <h4 className="text-sm font-semibold text-slate-900 mb-3">测试步骤</h4>
                  <div className="space-y-2">
                    {testCase.steps.map((step, index) => (
                      <div key={index} className="flex items-start space-x-3 p-3 bg-slate-50 rounded-md border border-slate-200">
                        <div className="flex-shrink-0 w-6 h-6 rounded-full bg-slate-200 text-slate-700 flex items-center justify-center text-xs font-medium">
                          {index + 1}
                        </div>
                        <p className="text-sm text-slate-700 flex-1">{step}</p>
                      </div>
                    ))}
                  </div>
                </div>

                {/* 预期结果 */}
                <div>
                  <h4 className="text-sm font-semibold text-slate-900 mb-2">预期结果</h4>
                  <div className="p-3 bg-green-50 border border-green-200 rounded-md">
                    <p className="text-sm text-green-900">{testCase.expected}</p>
                  </div>
                </div>

                {/* 测试数据 */}
                <div>
                  <h4 className="text-sm font-semibold text-slate-900 mb-2">测试数据</h4>
                  <div className="bg-slate-50 rounded-md border border-slate-200 p-4">
                    <pre className="text-xs text-slate-700 font-mono">
                      {JSON.stringify(testCase.testData, null, 2)}
                    </pre>
                  </div>
                </div>
              </div>
            )}

            {activeTab === 'history' && (
              <div>
                {testCase.executionHistory.length === 0 ? (
                  <EmptyState
                    icon={Clock}
                    title="暂无执行记录"
                    description="该测试用例还未被执行过"
                  />
                ) : (
                  <div className="space-y-3">
                    {testCase.executionHistory.map((record) => (
                      <div key={record.id} className="p-3 sm:p-4 border border-slate-200 rounded-md hover:bg-slate-50 transition-colors">
                        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-3">
                          <div className="flex flex-wrap items-center gap-2 sm:gap-3">
                            <StatusBadge 
                              status={getStatusLabel(record.status)} 
                              type={getStatusType(record.status)} 
                            />
                            <span className="text-sm text-slate-600">
                              <User className="w-4 h-4 inline mr-1" />
                              {record.executor}
                            </span>
                            <span className="text-sm text-slate-600">
                              <Calendar className="w-4 h-4 inline mr-1" />
                              {record.executeTime}
                            </span>
                          </div>
                          <div className="flex items-center flex-wrap gap-2 sm:gap-4 text-sm text-slate-600">
                            <span>
                              <Clock className="w-4 h-4 inline mr-1" />
                              {record.duration}ms
                            </span>
                            <span className="px-2 py-1 bg-slate-100 rounded text-xs">
                              {record.environment}
                            </span>
                          </div>
                        </div>
                        {record.failReason && (
                          <div className="mt-2 p-2 bg-red-50 border border-red-200 rounded text-sm text-red-700">
                            <AlertCircle className="w-4 h-4 inline mr-1" />
                            {record.failReason}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* 删除确认对话框 */}
      <ConfirmDialog
        isOpen={showDeleteDialog}
        onClose={() => setShowDeleteDialog(false)}
        onConfirm={handleDelete}
        title="删除测试用例"
        message="确定要删除此测试用例吗？此操作不可恢复，所有相关的执行记录也将被删除。"
        confirmText="删除"
        cancelText="取消"
        type="danger"
        loading={deleting}
      />
    </div>
  )
}
