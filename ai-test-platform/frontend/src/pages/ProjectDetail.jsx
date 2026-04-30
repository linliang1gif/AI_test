import { useEffect, useMemo, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { Globe, Lock, Plus, Save, Shield } from 'lucide-react'
import PageHeader from '../components/PageHeader'
import DetailCard from '../components/DetailCard'
import EmptyState from '../components/EmptyState'
import { environmentsAPI, projectsAPI } from '../services/api'
import { useToast } from '../components/ui/Toast'

const emptyEnvironment = (projectId) => ({
  project_id: projectId,
  name: '新环境',
  environment_type: 'test',
  base_url: '',
  auth_type: 'none',
  auth_config: {},
  default_headers: {},
  openapi_source: {},
  timeout_seconds: 30,
  retry_policy: { max_retries: 1, retry_backoff_seconds: 1 },
  env_var_mapping: {},
  data_isolation_key: '',
  allow_write_operations: false,
  allow_self_healing: true,
  allow_auto_test_data: true,
  is_default: false,
})

function stringifyJson(value) {
  return JSON.stringify(value || {}, null, 2)
}

function safeParseJson(text, fallback = {}) {
  if (!text?.trim()) return fallback
  return JSON.parse(text)
}

export default function ProjectDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const toast = useToast()
  const [loading, setLoading] = useState(true)
  const [savingProject, setSavingProject] = useState(false)
  const [savingEnvironment, setSavingEnvironment] = useState(false)
  const [project, setProject] = useState(null)
  const [projectForm, setProjectForm] = useState({
    name: '',
    description: '',
    owner: '',
    team: '',
    status: 'active',
  })
  const [selectedEnvironmentId, setSelectedEnvironmentId] = useState(null)
  const [environmentDraft, setEnvironmentDraft] = useState(null)
  const [environmentMode, setEnvironmentMode] = useState('existing')
  const [headersText, setHeadersText] = useState('{}')
  const [envVarText, setEnvVarText] = useState('{}')
  const [retryText, setRetryText] = useState('{"max_retries":1,"retry_backoff_seconds":1}')
  const [authText, setAuthText] = useState('{}')

  useEffect(() => {
    loadProject()
  }, [id])

  useEffect(() => {
    if (!project?.environments?.length) return
    const env = project.environments.find(item => item.id === selectedEnvironmentId) || project.environments[0]
    setSelectedEnvironmentId(env.id)
    hydrateEnvironmentDraft(env, 'existing')
  }, [project])

  const stats = useMemo(() => ({
    totalApis: project?.totalApis || 0,
    testsCount: project?.testsCount || 0,
    coverage: project?.coverage || 0,
    totalRuns: project?.totalRuns || 0,
  }), [project])

  const hydrateEnvironmentDraft = (environment, mode = 'existing') => {
    setEnvironmentMode(mode)
    setEnvironmentDraft(environment)
    setHeadersText(stringifyJson(environment.default_headers))
    setEnvVarText(stringifyJson(environment.env_var_mapping))
    setRetryText(stringifyJson(environment.retry_policy || { max_retries: 1, retry_backoff_seconds: 1 }))
    setAuthText(stringifyJson(environment.auth_config))
  }

  const loadProject = async () => {
    setLoading(true)
    try {
      const data = await projectsAPI.get(id)
      const projectData = data.project
      setProject(projectData)
      setProjectForm({
        name: projectData.name || '',
        description: projectData.description || '',
        owner: projectData.owner || '',
        team: projectData.team || '',
        status: projectData.status || 'active',
      })
    } catch (error) {
      console.error(error)
      toast.error('加载项目详情失败')
      setProject(null)
    } finally {
      setLoading(false)
    }
  }

  const handleSaveProject = async () => {
    setSavingProject(true)
    try {
      await projectsAPI.update(id, projectForm)
      toast.success('项目基本信息已保存')
      await loadProject()
    } catch (error) {
      toast.error('保存项目失败: ' + error.message)
    } finally {
      setSavingProject(false)
    }
  }

  const handleCreateEnvironmentDraft = () => {
    const draft = emptyEnvironment(Number(id))
    hydrateEnvironmentDraft(draft, 'create')
    setSelectedEnvironmentId(null)
  }

  const handleSaveEnvironment = async () => {
    if (!environmentDraft) return
    setSavingEnvironment(true)
    try {
      const payload = {
        ...environmentDraft,
        default_headers: safeParseJson(headersText, {}),
        env_var_mapping: safeParseJson(envVarText, {}),
        retry_policy: safeParseJson(retryText, { max_retries: 1, retry_backoff_seconds: 1 }),
        auth_config: safeParseJson(authText, {}),
      }

      if (environmentMode === 'create') {
        await environmentsAPI.create(payload)
        toast.success('环境已创建')
      } else {
        await environmentsAPI.update(environmentDraft.id, payload)
        toast.success('环境配置已保存')
      }
      await loadProject()
    } catch (error) {
      toast.error('保存环境失败: ' + error.message)
    } finally {
      setSavingEnvironment(false)
    }
  }

  if (loading) {
    return <div className="min-h-screen bg-slate-50 flex items-center justify-center text-slate-600">加载中...</div>
  }

  if (!project) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <EmptyState
          title="项目不存在"
          description="该项目可能已删除，或当前接口尚未返回数据。"
          action={
            <button onClick={() => navigate('/projects')} className="px-4 py-2 bg-slate-700 text-white rounded-md text-sm">
              返回项目列表
            </button>
          }
        />
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-slate-50">
      <PageHeader
        showBack={true}
        breadcrumbs={[
          { label: '项目管理', href: '/projects' },
          { label: project.name },
        ]}
        title={project.name}
        description="真实项目接入配置、环境约束与安全边界"
        meta={
          <div className="flex items-center gap-3 mt-2 text-sm text-slate-600">
            <span className="inline-flex items-center gap-1"><Globe className="w-4 h-4" /> 默认环境: {project.default_environment_name || '未配置'}</span>
            <span className="inline-flex items-center gap-1"><Shield className="w-4 h-4" /> 默认角色: {project.default_role}</span>
          </div>
        }
      />

      <div className="max-w-[1400px] mx-auto px-4 sm:px-6 py-6 space-y-6">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <DetailCard><div className="text-center"><div className="text-3xl font-bold text-slate-900">{stats.totalApis}</div><div className="text-sm text-slate-600">已纳管 API</div></div></DetailCard>
          <DetailCard><div className="text-center"><div className="text-3xl font-bold text-slate-900">{stats.testsCount}</div><div className="text-sm text-slate-600">测试用例</div></div></DetailCard>
          <DetailCard><div className="text-center"><div className="text-3xl font-bold text-green-600">{stats.coverage}%</div><div className="text-sm text-slate-600">覆盖率</div></div></DetailCard>
          <DetailCard><div className="text-center"><div className="text-3xl font-bold text-blue-600">{stats.totalRuns}</div><div className="text-sm text-slate-600">执行次数</div></div></DetailCard>
        </div>

        <DetailCard
          title="项目基本信息"
          extra={
            <button
              onClick={handleSaveProject}
              disabled={savingProject}
              className="px-4 py-2 bg-blue-600 text-white rounded-md text-sm hover:bg-blue-700 disabled:opacity-50 inline-flex items-center gap-2"
            >
              <Save className="w-4 h-4" />
              保存项目
            </button>
          }
        >
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <label className="text-sm text-slate-700">
              项目名称
              <input className="mt-1 w-full px-3 py-2 border border-slate-300 rounded-md" value={projectForm.name} onChange={(e) => setProjectForm(prev => ({ ...prev, name: e.target.value }))} />
            </label>
            <label className="text-sm text-slate-700">
              状态
              <select className="mt-1 w-full px-3 py-2 border border-slate-300 rounded-md" value={projectForm.status} onChange={(e) => setProjectForm(prev => ({ ...prev, status: e.target.value }))}>
                <option value="active">active</option>
                <option value="inactive">inactive</option>
                <option value="archived">archived</option>
              </select>
            </label>
            <label className="text-sm text-slate-700">
              负责人
              <input className="mt-1 w-full px-3 py-2 border border-slate-300 rounded-md" value={projectForm.owner} onChange={(e) => setProjectForm(prev => ({ ...prev, owner: e.target.value }))} />
            </label>
            <label className="text-sm text-slate-700">
              团队
              <input className="mt-1 w-full px-3 py-2 border border-slate-300 rounded-md" value={projectForm.team} onChange={(e) => setProjectForm(prev => ({ ...prev, team: e.target.value }))} />
            </label>
            <label className="text-sm text-slate-700 md:col-span-2">
              项目说明
              <textarea className="mt-1 w-full px-3 py-2 border border-slate-300 rounded-md min-h-24" value={projectForm.description} onChange={(e) => setProjectForm(prev => ({ ...prev, description: e.target.value }))} />
            </label>
          </div>
        </DetailCard>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <DetailCard
            title="环境列表"
            extra={
              <button onClick={handleCreateEnvironmentDraft} className="px-3 py-2 bg-slate-700 text-white rounded-md text-sm inline-flex items-center gap-2">
                <Plus className="w-4 h-4" />
                新建环境
              </button>
            }
          >
            <div className="space-y-3">
              {(project.environments || []).map((environment) => (
                <button
                  key={environment.id}
                  onClick={() => {
                    setSelectedEnvironmentId(environment.id)
                    hydrateEnvironmentDraft(environment, 'existing')
                  }}
                  className={`w-full text-left p-4 rounded-md border transition-colors ${
                    selectedEnvironmentId === environment.id && environmentMode === 'existing'
                      ? 'border-blue-500 bg-blue-50'
                      : 'border-slate-200 bg-white hover:bg-slate-50'
                  }`}
                >
                  <div className="flex items-center justify-between mb-2">
                    <div className="font-medium text-slate-900">{environment.name}</div>
                    {environment.is_default && <span className="text-xs px-2 py-1 bg-green-100 text-green-700 rounded-md">默认</span>}
                  </div>
                  <div className="text-xs text-slate-600 space-y-1">
                    <div>{environment.environment_type}</div>
                    <div className="truncate">{environment.base_url || '未配置 Base URL'}</div>
                  </div>
                </button>
              ))}
            </div>
          </DetailCard>

          <div className="lg:col-span-2">
            {environmentDraft ? (
              <DetailCard
                title={environmentMode === 'create' ? '新建环境' : '环境接入配置'}
                extra={
                  <button
                    onClick={handleSaveEnvironment}
                    disabled={savingEnvironment}
                    className="px-4 py-2 bg-blue-600 text-white rounded-md text-sm hover:bg-blue-700 disabled:opacity-50 inline-flex items-center gap-2"
                  >
                    <Save className="w-4 h-4" />
                    保存环境
                  </button>
                }
              >
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <label className="text-sm text-slate-700">
                    环境名称
                    <input className="mt-1 w-full px-3 py-2 border border-slate-300 rounded-md" value={environmentDraft.name} onChange={(e) => setEnvironmentDraft(prev => ({ ...prev, name: e.target.value }))} />
                  </label>
                  <label className="text-sm text-slate-700">
                    环境类型
                    <select className="mt-1 w-full px-3 py-2 border border-slate-300 rounded-md" value={environmentDraft.environment_type} onChange={(e) => setEnvironmentDraft(prev => ({ ...prev, environment_type: e.target.value }))}>
                      <option value="dev">dev</option>
                      <option value="test">test</option>
                      <option value="staging">staging</option>
                      <option value="prod">prod</option>
                    </select>
                  </label>
                  <label className="text-sm text-slate-700 md:col-span-2">
                    Base URL
                    <input className="mt-1 w-full px-3 py-2 border border-slate-300 rounded-md font-mono" value={environmentDraft.base_url} onChange={(e) => setEnvironmentDraft(prev => ({ ...prev, base_url: e.target.value }))} />
                  </label>
                  <label className="text-sm text-slate-700">
                    鉴权方式
                    <select className="mt-1 w-full px-3 py-2 border border-slate-300 rounded-md" value={environmentDraft.auth_type} onChange={(e) => setEnvironmentDraft(prev => ({ ...prev, auth_type: e.target.value }))}>
                      <option value="none">none</option>
                      <option value="bearer_token">bearer token</option>
                      <option value="api_key">api key</option>
                      <option value="cookie">cookie</option>
                      <option value="custom_header">custom header</option>
                    </select>
                  </label>
                  <label className="text-sm text-slate-700">
                    数据隔离标识
                    <input className="mt-1 w-full px-3 py-2 border border-slate-300 rounded-md" value={environmentDraft.data_isolation_key || ''} onChange={(e) => setEnvironmentDraft(prev => ({ ...prev, data_isolation_key: e.target.value }))} />
                  </label>
                  <label className="text-sm text-slate-700">
                    超时秒数
                    <input type="number" className="mt-1 w-full px-3 py-2 border border-slate-300 rounded-md" value={environmentDraft.timeout_seconds} onChange={(e) => setEnvironmentDraft(prev => ({ ...prev, timeout_seconds: Number(e.target.value) }))} />
                  </label>
                  <label className="text-sm text-slate-700">
                    默认环境
                    <select className="mt-1 w-full px-3 py-2 border border-slate-300 rounded-md" value={String(environmentDraft.is_default)} onChange={(e) => setEnvironmentDraft(prev => ({ ...prev, is_default: e.target.value === 'true' }))}>
                      <option value="false">否</option>
                      <option value="true">是</option>
                    </select>
                  </label>
                  <label className="text-sm text-slate-700 md:col-span-2">
                    鉴权配置 JSON
                    <textarea className="mt-1 w-full px-3 py-2 border border-slate-300 rounded-md min-h-24 font-mono text-xs" value={authText} onChange={(e) => setAuthText(e.target.value)} />
                    <div className="mt-1 text-xs text-slate-500 inline-flex items-center gap-1"><Lock className="w-3 h-3" /> 返回页面默认脱敏，留空不会覆盖已有 secret。</div>
                  </label>
                  <label className="text-sm text-slate-700 md:col-span-2">
                    默认请求头 JSON
                    <textarea className="mt-1 w-full px-3 py-2 border border-slate-300 rounded-md min-h-24 font-mono text-xs" value={headersText} onChange={(e) => setHeadersText(e.target.value)} />
                  </label>
                  <label className="text-sm text-slate-700 md:col-span-2">
                    重试策略 JSON
                    <textarea className="mt-1 w-full px-3 py-2 border border-slate-300 rounded-md min-h-20 font-mono text-xs" value={retryText} onChange={(e) => setRetryText(e.target.value)} />
                  </label>
                  <label className="text-sm text-slate-700 md:col-span-2">
                    环境变量映射 JSON
                    <textarea className="mt-1 w-full px-3 py-2 border border-slate-300 rounded-md min-h-20 font-mono text-xs" value={envVarText} onChange={(e) => setEnvVarText(e.target.value)} />
                  </label>
                </div>

                <div className="mt-6 grid grid-cols-1 md:grid-cols-3 gap-3">
                  <label className="flex items-center gap-2 text-sm text-slate-700 p-3 bg-slate-50 rounded-md border border-slate-200">
                    <input type="checkbox" checked={environmentDraft.allow_write_operations} onChange={(e) => setEnvironmentDraft(prev => ({ ...prev, allow_write_operations: e.target.checked }))} />
                    允许写操作测试
                  </label>
                  <label className="flex items-center gap-2 text-sm text-slate-700 p-3 bg-slate-50 rounded-md border border-slate-200">
                    <input type="checkbox" checked={environmentDraft.allow_self_healing} onChange={(e) => setEnvironmentDraft(prev => ({ ...prev, allow_self_healing: e.target.checked }))} />
                    允许低风险自愈
                  </label>
                  <label className="flex items-center gap-2 text-sm text-slate-700 p-3 bg-slate-50 rounded-md border border-slate-200">
                    <input type="checkbox" checked={environmentDraft.allow_auto_test_data} onChange={(e) => setEnvironmentDraft(prev => ({ ...prev, allow_auto_test_data: e.target.checked }))} />
                    允许自动生成测试数据
                  </label>
                </div>

                {environmentDraft.openapi_source?.location && (
                  <div className="mt-6 p-4 bg-emerald-50 border border-emerald-200 rounded-md text-sm text-emerald-800">
                    已绑定 OpenAPI 来源：{environmentDraft.openapi_source.location}
                  </div>
                )}
              </DetailCard>
            ) : (
              <EmptyState title="请选择一个环境" description="选择左侧环境后即可编辑接入配置。" />
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
