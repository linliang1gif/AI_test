import { useState, useEffect, useCallback } from 'react'

const API = '/api/v2/defects'
const SEVERITY_COLORS = { blocker: 'bg-red-600 text-white', critical: 'bg-red-100 text-red-700', major: 'bg-amber-100 text-amber-700', minor: 'bg-blue-100 text-blue-700', trivial: 'bg-slate-100 text-slate-600' }
const STATUS_COLORS = { open: 'bg-red-100 text-red-700', confirmed: 'bg-amber-100 text-amber-700', fixed: 'bg-blue-100 text-blue-700', verified: 'bg-green-100 text-green-700', closed: 'bg-slate-200 text-slate-500', rejected: 'bg-slate-100 text-slate-400', reopened: 'bg-red-100 text-red-600' }
const TRANSITIONS = { open: ['confirmed', 'rejected'], confirmed: ['fixed'], fixed: ['verified'], verified: ['closed'], closed: ['reopened'], rejected: [], reopened: ['confirmed', 'rejected'] }
const SEVERITIES = ['blocker', 'critical', 'major', 'minor', 'trivial']
const PRIORITIES = ['P0', 'P1', 'P2', 'P3']
const SOURCES = ['manual', 'product_review', 'code_compare', 'long_flow', 'run_failure', 'failure_analysis', 'quality_gate', 'visual_diff', 'performance_regression', 'data_issue']
const SOURCE_LABELS = { manual: '人工', product_review: '产品走查', code_compare: '代码对比', long_flow: '长流程', run_failure: '执行失败', failure_analysis: '失败归因', quality_gate: '质量门禁', visual_diff: '视觉差异', performance_regression: '性能退化', data_issue: '数据问题' }
const ISSUE_TYPES = ['前端', '后端', '联调', '接口契约', '数据同步', '产品体验', '需求不清', '环境配置']
const DEFAULT_FORM = {
  title: '',
  description: '',
  module: '',
  severity: 'major',
  priority: 'P2',
  source: 'manual',
  failure_category: '',
  assigned_to: '',
  iteration: 'v1.2.5',
  requirement_source: '',
  issue_type: '联调',
  repro_steps: '',
  actual_result: '',
  expected_result: '',
  evidence_text: '',
  code_refs: '',
  api_refs: '',
  suggested_fix: '',
}

const BUG_TEMPLATES = [
  {
    key: 'unload_video_sync',
    name: '卸货录像展示/ERP不一致',
    data: {
      title: '【磅称管理】当前过磅页卸货录像展示与ERP附件同步不一致',
      module: '磅称管理-卸货录像',
      severity: 'critical',
      priority: 'P0',
      source: 'product_review',
      failure_category: '数据同步/页面展示不一致',
      issue_type: '联调',
      repro_steps: '1. 进入磅称页面并选择入库/出库单\n2. 点击“卸货录像”并等待录像完成\n3. 再次点击“卸货录像”并等待完成\n4. 查看当前过磅页照片/视频区域\n5. 查看过磅记录和ERP对应单据附件',
      actual_result: '当前过磅页只展示一个卸货视频；ERP对应单据附件可能显示多个视频，页面展示与同步结果不一致。',
      expected_result: '每次成功录制的视频都应在当前过磅页、过磅记录、ERP附件中保持一致；若产品只允许保留一个视频，也应同步覆盖并给出明确规则。',
      evidence_text: '用户实测：磅秤点击两次卸货录像，磅秤页面只会显示一个视频，同步到ERP显示多个。',
      code_refs: '前端：recycle-pound-feature-1.2.5/src/views/poundHome/index.vue\n后端：recycle-server-feature-1.2.5 中录像保存/ERP同步逻辑',
      api_refs: '详情接口返回需确认 contractAttachments / attachmentFiles / boundInfoDetailsList[].contractAttachments 的一致性。',
      suggested_fix: '统一录像附件的追加/覆盖规则；前端轮询详情接口时兼容后端实际返回字段；后端本地附件与ERP同步使用同一份附件集合。',
    },
  },
  {
    key: 'current_page_video_missing',
    name: '当前页拿不到卸货视频',
    data: {
      title: '【磅称管理】卸货录像完成后当前过磅页未展示视频',
      module: '磅称管理-当前过磅页',
      severity: 'critical',
      priority: 'P0',
      source: 'product_review',
      failure_category: '接口字段兼容/页面展示缺失',
      issue_type: '前端',
      repro_steps: '1. 进入磅称页面并选择入库/出库单\n2. 点击“卸货录像”\n3. 等待录像完成及前端轮询\n4. 查看当前过磅页照片/视频区域\n5. 再进入过磅记录查看同一单据影像',
      actual_result: '过磅记录可以看到卸货视频，但当前过磅页未展示视频。',
      expected_result: '录像生成后，当前过磅页应在轮询到详情接口附件数据后展示卸货视频。',
      evidence_text: '详情接口需确认主表 contractAttachments、attachmentFiles、明细 boundInfoDetailsList[].contractAttachments 的返回情况。',
      code_refs: '前端轮询展示逻辑：recycle-pound-feature-1.2.5/src/views/poundHome/index.vue',
      api_refs: 'GET details 接口：检查是否返回 attachmentFiles 或 contractAttachments。',
      suggested_fix: '当前过磅页展示逻辑兼容后端实际附件字段；后端详情接口与列表/记录接口返回结构保持一致。',
    },
  },
  {
    key: 'clear_state_residue',
    name: '清理/切单后残留影像',
    data: {
      title: '【磅称管理】清理或切换单据后旧卸货影像状态未清空',
      module: '磅称管理-页面状态',
      severity: 'major',
      priority: 'P1',
      source: 'long_flow',
      failure_category: '页面状态残留',
      issue_type: '前端',
      repro_steps: '1. 选择单据并完成一次卸货录像\n2. 当前页面出现影像或进入轮询状态\n3. 点击“清理”或切换入库/出库类型\n4. 查看照片/视频区域和轮询状态\n5. 选择下一单继续操作',
      actual_result: '旧单据的视频、轮询状态或当前记录标识可能残留到新流程。',
      expected_result: '清理或切单后应清空当前影像、当前记录标识，并停止录像轮询。',
      evidence_text: '重点观察 mainAttachment、currentRecordUuid、轮询 timer 是否被清理。',
      code_refs: '前端 handleClear / handlePoundTypeChange / stopRecordCheckTimer',
      api_refs: '',
      suggested_fix: '清理入口统一重置附件状态和轮询状态；切单时停止旧轮询并清空旧影像。',
    },
  },
  {
    key: 'recording_double_click',
    name: '录像按钮重复点击',
    data: {
      title: '【磅称管理】卸货录像过程中重复点击按钮可触发多次录制',
      module: '磅称管理-卸货录像',
      severity: 'major',
      priority: 'P1',
      source: 'long_flow',
      failure_category: '重复提交/并发控制',
      issue_type: '前后端',
      repro_steps: '1. 进入磅称页面并选择单据\n2. 连续快速点击“卸货录像”两次或多次\n3. 观察前端按钮状态、接口请求次数、后端录像任务数量\n4. 查看当前页、过磅记录和ERP附件',
      actual_result: '可能重复触发录像任务，造成页面展示、记录附件、ERP附件数量不一致。',
      expected_result: '录像进行中按钮应禁用或显示录制中；后端应对同一单据/摄像头/时间段做并发保护。',
      evidence_text: '抓包确认 /record 请求次数；后端日志确认异步录像任务数量。',
      code_refs: '前端卸货录像按钮状态；后端录像 Redis lock / async task',
      api_refs: 'POST /recycle/basic/basicDevice/record',
      suggested_fix: '前端增加 recording/loading 状态；后端锁应在任务提交前生效，并返回明确的重复录制提示。',
    },
  },
  {
    key: 'erp_attachment_sync',
    name: 'ERP附件同步异常',
    data: {
      title: '【ERP同步】过磅影像同步到ERP附件结果与本地记录不一致',
      module: '磅称管理-ERP附件同步',
      severity: 'critical',
      priority: 'P0',
      source: 'product_review',
      failure_category: 'ERP同步',
      issue_type: '后端',
      repro_steps: '1. 完成过磅拍照或卸货录像\n2. 保存/继续过磅触发同步\n3. 查看本地过磅记录附件\n4. 查看ERP对应入库/物流附件\n5. 对比附件数量、类型和顺序',
      actual_result: 'ERP附件与本地附件可能出现缺失、重复、覆盖或字段写错。',
      expected_result: '本地过磅记录与ERP对应单据附件应一致，且入库/出库字段写入规则明确。',
      evidence_text: '提供本地接口返回、ERP截图、同步日志。',
      code_refs: '后端 ERP sync：入库/出库 saveStockProductDetail / saveOutProductDetail / modifyFile 等逻辑',
      api_refs: '本地详情接口、ERP附件查询接口',
      suggested_fix: '统一附件集合来源；同步前合并去重；入库/出库分别确认目标字段，不混用 attachment/field1。',
    },
  },
  {
    key: 'monitor_double_click',
    name: '监控双击放大缺失',
    data: {
      title: '【磅称管理】监控画面不支持双击放大预览',
      module: '磅称管理-监控',
      severity: 'major',
      priority: 'P1',
      source: 'product_review',
      failure_category: '需求未实现',
      issue_type: '前端',
      repro_steps: '1. 进入磅称页面\n2. 点击“监控”打开监控区域\n3. 双击任一摄像头画面\n4. 观察是否放大预览并可恢复',
      actual_result: '双击画面无放大预览效果或交互不完整。',
      expected_result: '支持双击放大预览指定摄像头画面，再次操作可退出放大。',
      evidence_text: '对照需求：支持“双击”放大预览对应摄像头监控画面。',
      code_refs: '前端 MonitorPanel.vue / 监控弹窗相关组件',
      api_refs: '',
      suggested_fix: '恢复并完善 dblclick 事件、放大状态、布局尺寸和退出交互。',
    },
  },
  {
    key: 'monitor_idle_close',
    name: '监控5分钟关闭逻辑',
    data: {
      title: '【磅称管理】监控持续播放5分钟关闭提醒逻辑不符合需求',
      module: '磅称管理-监控',
      severity: 'major',
      priority: 'P1',
      source: 'product_review',
      failure_category: '交互逻辑不一致',
      issue_type: '前端',
      repro_steps: '1. 进入磅称页面并打开监控\n2. 保持无人操作超过5分钟\n3. 或切换离开磅称页面后保持监控播放\n4. 观察关闭提醒、倒计时和用户操作后的重置行为',
      actual_result: '可能只按打开时间计时，未准确识别页面停留、用户空闲和操作重置。',
      expected_result: '未停留在磅称界面，或停留但无人操作且监控播放达5分钟时，弹出即将关闭监控提示，并按原型处理倒计时。',
      evidence_text: '对照需求 1.2：页面停留状态、无人操作、播放时长均参与判断。',
      code_refs: '前端监控打开/关闭定时器、visibilitychange、用户操作监听',
      api_refs: '',
      suggested_fix: '引入用户 idle 监听和页面可见性判断；用户操作后重置计时；弹窗倒计时可取消/确认。',
    },
  },
  {
    key: 'duration_validation',
    name: '录像时长校验',
    data: {
      title: '【磅称管理】卸货拍摄时长校验未完整限制5-600秒',
      module: '磅称管理-设置',
      severity: 'major',
      priority: 'P1',
      source: 'product_review',
      failure_category: '表单校验',
      issue_type: '前后端',
      repro_steps: '1. 打开磅称设置\n2. 将卸货拍摄时长分别输入空值、0、4、5、600、601、小数、非数字\n3. 保存设置\n4. 点击卸货录像观察实际拍摄时长',
      actual_result: '表单或后端可能未严格按5-600秒限制，异常值仍可保存或生效。',
      expected_result: '仅允许正整数5-600秒；非法值保存失败或自动修正，并有明确提示。',
      evidence_text: '记录每个输入值的保存结果、接口入参和后端返回。',
      code_refs: '前端 SettingDialog.vue rules；后端 record 请求 recordingTime 校验',
      api_refs: '设置保存接口、录像接口',
      suggested_fix: '前端 form rule 与字段名保持一致；后端补充5-600范围校验，避免绕过前端。',
    },
  },
  {
    key: 'api_contract_mismatch',
    name: '接口字段契约不一致',
    data: {
      title: '【接口契约】前后端附件字段定义不一致导致页面展示异常',
      module: '接口契约-附件字段',
      severity: 'critical',
      priority: 'P0',
      source: 'code_compare',
      failure_category: '接口契约',
      issue_type: '接口契约',
      repro_steps: '1. 调用详情/列表/记录相关接口\n2. 对比 contractAttachments、attachmentFiles、明细附件字段\n3. 打开当前过磅页和过磅记录页\n4. 对比页面展示结果',
      actual_result: '不同接口返回字段结构不一致，前端页面读取字段不统一，导致部分页面不展示影像。',
      expected_result: '同一业务附件在详情、列表、记录接口中应有稳定字段契约；前端读取逻辑和接口文档一致。',
      evidence_text: '贴出接口响应样例和前端读取字段。',
      code_refs: '前端附件展示逻辑；后端 DTO/VO 转换逻辑',
      api_refs: 'GET detail / list / record page',
      suggested_fix: '后端统一输出 attachmentFiles 或明确主表/明细字段；前端兼容历史字段并逐步收敛。',
    },
  },
  {
    key: 'environment_proxy',
    name: '本地环境代理异常',
    data: {
      title: '【测试平台】前端代理端口与后端启动端口不一致导致API 500',
      module: 'AI测试平台-本地环境',
      severity: 'major',
      priority: 'P1',
      source: 'manual',
      failure_category: '环境配置',
      issue_type: '环境配置',
      repro_steps: '1. 启动前端 dev server\n2. 后端未启动或启动端口与 vite proxy 不一致\n3. 打开任意页面\n4. 观察 /health 或 /api/v2/* 请求',
      actual_result: '前端页面显示 API调用失败: 500 或 后端状态连接异常。',
      expected_result: '启动脚本应统一端口并在后端健康检查失败时明确提示。',
      evidence_text: '浏览器控制台出现 /health 500；netstat 无 8001 LISTENING。',
      code_refs: 'frontend/vite.config.js；start_all.ps1',
      api_refs: 'GET /health',
      suggested_fix: '启动脚本只认 LISTENING 端口，并增加 /health 检查；前端代理、.env、README端口统一。',
    },
  },
]

function buildBugMarkdown(defect) {
  const ev = defect.evidence_json || {}
  const lines = [
    `【标题】${defect.title || ''}`,
    `【优先级】${defect.priority || ''}`,
    `【严重级别】${defect.severity || ''}`,
    `【模块】${defect.module || ''}`,
    `【问题类型】${ev.issue_type || defect.failure_category || ''}`,
    `【所属迭代】${ev.iteration || ''}`,
    `【需求来源】${ev.requirement_source || ''}`,
    '',
    '【复现步骤】',
    ev.repro_steps || '',
    '',
    '【实际结果】',
    ev.actual_result || defect.description || '',
    '',
    '【期望结果】',
    ev.expected_result || '',
    '',
    '【证据】',
    ev.evidence_text || '',
    '',
    '【代码/接口线索】',
    [ev.code_refs, ev.api_refs].filter(Boolean).join('\n'),
    '',
    '【建议修复方向】',
    ev.suggested_fix || '',
  ]
  return lines.join('\n').trim()
}

export default function DefectManagement() {
  const [defects, setDefects] = useState([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(false)
  const [filterStatus, setFilterStatus] = useState('')
  const [filterSeverity, setFilterSeverity] = useState('')
  const [keyword, setKeyword] = useState('')

  const [showCreate, setShowCreate] = useState(false)
  const [showDetail, setShowDetail] = useState(null)
  const [showTransition, setShowTransition] = useState(null)
  const [transitionComment, setTransitionComment] = useState('')

  const [form, setForm] = useState(DEFAULT_FORM)

  const fetchDefects = useCallback(async () => {
    setLoading(true)
    try {
      const params = new URLSearchParams()
      if (filterStatus) params.set('status', filterStatus)
      if (filterSeverity) params.set('severity', filterSeverity)
      if (keyword) params.set('keyword', keyword)
      params.set('limit', '50')
      const r = await fetch(`${API}?${params}`)
      const d = await r.json()
      setDefects(d.defects || [])
      setTotal(d.total || 0)
    } catch (e) { console.error(e) }
    setLoading(false)
  }, [filterStatus, filterSeverity, keyword])

  useEffect(() => { fetchDefects() }, [fetchDefects])

  const handleCreate = async () => {
    const {
      iteration, requirement_source, issue_type, repro_steps, actual_result,
      expected_result, evidence_text, code_refs, api_refs, suggested_fix,
      ...base
    } = form
    const description = base.description || actual_result || expected_result
    const payload = {
      ...base,
      description,
      evidence_json: {
        iteration,
        requirement_source,
        issue_type,
        repro_steps,
        actual_result,
        expected_result,
        evidence_text,
        code_refs,
        api_refs,
        suggested_fix,
      },
    }
    if (payload.run_case_id !== undefined && payload.run_case_id !== null && payload.run_case_id !== '') {
      payload.run_case_id = String(payload.run_case_id)
    }
    const r = await fetch(API, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) })
    if (r.ok) { setShowCreate(false); setForm(DEFAULT_FORM); fetchDefects() }
    else {
      const d = await r.json().catch(() => ({}))
      alert(d.message || d.detail || '创建缺陷失败')
    }
  }

  const applyBugTemplate = (key) => {
    const template = BUG_TEMPLATES.find(t => t.key === key)
    if (!template) return
    setForm({ ...DEFAULT_FORM, ...template.data })
  }

  const copyBugMarkdown = async (defect) => {
    const text = buildBugMarkdown(defect)
    try {
      await navigator.clipboard.writeText(text)
      alert('已复制 bug 单模板')
    } catch (e) {
      window.prompt('复制下面的 bug 单内容', text)
    }
  }

  const openDetail = async (id) => {
    const r = await fetch(`${API}/${id}`)
    const d = await r.json()
    setShowDetail(d)
  }

  const handleTransition = async (defectId, toStatus) => {
    const r = await fetch(`${API}/${defectId}/transition`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ to_status: toStatus, comment: transitionComment }) })
    if (r.ok) { setShowTransition(null); setTransitionComment(''); openDetail(defectId); fetchDefects() }
  }

  const handleUpdate = async (defectId, data) => {
    await fetch(`${API}/${defectId}`, { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data) })
    openDetail(defectId)
    fetchDefects()
  }

  const handlePushToTapd = async (defectId) => {
    const r = await fetch(`${API}/${defectId}/push-to-tapd`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({}) })
    const d = await r.json()
    if (!r.ok || !d.success) {
      alert(d.detail || d.message || '推送 TAPD 失败')
      return
    }
    alert(d.already_pushed ? '该缺陷已推送过 TAPD' : `推送 TAPD 成功：${d.bug_id}`)
    openDetail(defectId)
    fetchDefects()
  }

  const handleSyncTapd = async (defectId) => {
    const r = await fetch(`${API}/${defectId}/sync-tapd-status`, { method: 'POST', headers: { 'Content-Type': 'application/json' } })
    const d = await r.json()
    if (!r.ok || !d.success) {
      alert(d.detail || d.message || 'TAPD 状态同步失败')
      return
    }
    const steps = d.advanced_steps || []
    const stepsTxt = steps.length ? steps.map(s => `${s.from}→${s.to}`).join(', ') : '无变化'
    alert(`TAPD: ${d.tapd_status_name}\n本地: ${d.local_status}\n推进: ${stepsTxt}${d.skipped_reason ? `\n${d.skipped_reason}` : ''}`)
    if (showDetail?.id === defectId) openDetail(defectId)
    fetchDefects()
  }

  const handleBatchSyncTapd = async () => {
    if (!confirm('对所有已推送 TAPD 的缺陷进行状态同步？\n（会从 TAPD 拉取最新状态并自动推动本地状态机）')) return
    const r = await fetch(`${API}/sync-tapd-status-batch`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ force_advance: true }) })
    const d = await r.json()
    if (!r.ok || !d.success) {
      alert(d.detail || d.message || '批量同步失败')
      return
    }
    alert(`批量同步完成\n  扫描已推送: ${d.total}\n  状态推进: ${d.advanced}\n  失败: ${d.failed}\n  未推送跳过: ${d.no_tapd_link}`)
    fetchDefects()
  }

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">缺陷管理</h1>
          <p className="text-sm text-slate-500 mt-1">缺陷闭环跟踪 · 共 {total} 个缺陷</p>
        </div>
        <div className="flex gap-2">
          <button onClick={handleBatchSyncTapd} title="从 TAPD 拉取所有已推送缺陷的最新状态并推动本地状态机" className="px-3 py-2 border border-cyan-500 text-cyan-700 rounded-lg hover:bg-cyan-50 text-sm font-medium">⥂ 同步 TAPD</button>
          <button onClick={() => { setForm(DEFAULT_FORM); setShowCreate(true) }} className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 text-sm font-medium">+ 新建缺陷</button>
        </div>
      </div>

      {/* Filters */}
      <div className="flex gap-3 mb-4 flex-wrap">
        <select value={filterStatus} onChange={e => setFilterStatus(e.target.value)} className="border rounded-lg px-3 py-1.5 text-sm">
          <option value="">全部状态</option>
          {Object.keys(STATUS_COLORS).map(s => <option key={s} value={s}>{s}</option>)}
        </select>
        <select value={filterSeverity} onChange={e => setFilterSeverity(e.target.value)} className="border rounded-lg px-3 py-1.5 text-sm">
          <option value="">全部严重级别</option>
          {SEVERITIES.map(s => <option key={s} value={s}>{s}</option>)}
        </select>
        <input value={keyword} onChange={e => setKeyword(e.target.value)} placeholder="关键词搜索..." className="border rounded-lg px-3 py-1.5 text-sm w-48" />
      </div>

      {/* Table */}
      <div className="bg-white rounded-xl shadow-sm border overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-slate-50 border-b">
            <tr>
              <th className="text-left px-4 py-3 font-medium text-slate-600">ID</th>
              <th className="text-left px-4 py-3 font-medium text-slate-600">标题</th>
              <th className="text-center px-4 py-3 font-medium text-slate-600">严重级别</th>
              <th className="text-center px-4 py-3 font-medium text-slate-600">优先级</th>
              <th className="text-center px-4 py-3 font-medium text-slate-600">状态</th>
              <th className="text-center px-4 py-3 font-medium text-slate-600">来源</th>
              <th className="text-left px-4 py-3 font-medium text-slate-600">模块</th>
              <th className="text-left px-4 py-3 font-medium text-slate-600">更新时间</th>
              <th className="text-center px-4 py-3 font-medium text-slate-600">操作</th>
            </tr>
          </thead>
          <tbody className="divide-y">
            {defects.map(d => (
              <tr key={d.id} className="hover:bg-slate-50 cursor-pointer" onClick={() => openDetail(d.id)}>
                <td className="px-4 py-3 font-mono text-xs text-slate-500">#{d.id}</td>
                <td className="px-4 py-3 font-medium text-slate-800 max-w-xs truncate">{d.title}</td>
                <td className="px-4 py-3 text-center"><span className={`px-2 py-0.5 rounded text-xs ${SEVERITY_COLORS[d.severity] || ''}`}>{d.severity}</span></td>
                <td className="px-4 py-3 text-center font-mono text-xs">{d.priority}</td>
                <td className="px-4 py-3 text-center"><span className={`px-2 py-0.5 rounded text-xs ${STATUS_COLORS[d.status] || ''}`}>{d.status}</span></td>
                <td className="px-4 py-3 text-center text-xs text-slate-500">{SOURCE_LABELS[d.source] || d.source}</td>
                <td className="px-4 py-3 text-xs text-slate-500">{d.module}</td>
                <td className="px-4 py-3 text-xs text-slate-400">{d.updated_at?.slice(0, 16).replace('T', ' ')}</td>
                <td className="px-4 py-3 text-center" onClick={e => e.stopPropagation()}>
                  <div className="flex justify-center gap-1 flex-wrap">
                    {d.evidence_json?.tapd_bug_id ? (
                      <>
                        <a
                          href={d.evidence_json.tapd_url}
                          target="_blank"
                          rel="noreferrer"
                          title={`已推送 TAPD #${d.evidence_json.tapd_bug_id}${d.evidence_json.tapd_status_name ? ` · ${d.evidence_json.tapd_status_name}` : ''}`}
                          className="px-2 py-0.5 text-xs bg-green-50 text-green-700 rounded hover:bg-green-100"
                        >
                          TAPD #{d.evidence_json.tapd_bug_id}
                          {d.evidence_json.tapd_status_name ? ` (${d.evidence_json.tapd_status_name})` : ''}
                        </a>
                        <button
                          onClick={() => handleSyncTapd(d.id)}
                          title="从 TAPD 拉取最新状态并联动本地状态机"
                          className="px-1.5 py-0.5 text-xs bg-cyan-50 text-cyan-700 rounded hover:bg-cyan-100"
                        >⥂</button>
                      </>
                    ) : (
                      <button
                        onClick={() => handlePushToTapd(d.id)}
                        title="推送到 TAPD 创建缺陷"
                        className="px-2 py-0.5 text-xs bg-blue-50 text-blue-700 rounded hover:bg-blue-100"
                      >
                        推 TAPD
                      </button>
                    )}
                    {(TRANSITIONS[d.status] || []).map(t => (
                      <button key={t} onClick={() => { setShowTransition({ id: d.id, from: d.status, to: t }); setTransitionComment('') }} className="px-2 py-0.5 text-xs bg-indigo-50 text-indigo-700 rounded hover:bg-indigo-100">{t}</button>
                    ))}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {loading && <p className="text-center py-4 text-slate-400">加载中...</p>}
        {!loading && defects.length === 0 && <p className="text-center py-8 text-slate-400">暂无缺陷</p>}
      </div>

      {/* Create Dialog */}
      {showCreate && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl p-6 w-[600px] max-h-[80vh] overflow-y-auto shadow-2xl">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-lg font-bold">新建缺陷</h2>
              <select onChange={e => applyBugTemplate(e.target.value)} defaultValue="" className="border rounded-lg px-3 py-1.5 text-xs text-amber-700 bg-amber-50">
                <option value="">选择 bug 模板</option>
                {BUG_TEMPLATES.map(t => <option key={t.key} value={t.key}>{t.name}</option>)}
              </select>
            </div>
            <div className="space-y-3">
              <input value={form.title} onChange={e => setForm({ ...form, title: e.target.value })} placeholder="缺陷标题 *" className="w-full border rounded-lg px-3 py-2 text-sm" />
              <textarea value={form.description} onChange={e => setForm({ ...form, description: e.target.value })} placeholder="摘要描述" rows={2} className="w-full border rounded-lg px-3 py-2 text-sm" />
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-xs text-slate-500">严重级别</label>
                  <select value={form.severity} onChange={e => setForm({ ...form, severity: e.target.value })} className="w-full border rounded-lg px-3 py-2 text-sm">
                    {SEVERITIES.map(s => <option key={s} value={s}>{s}</option>)}
                  </select>
                </div>
                <div>
                  <label className="text-xs text-slate-500">优先级</label>
                  <select value={form.priority} onChange={e => setForm({ ...form, priority: e.target.value })} className="w-full border rounded-lg px-3 py-2 text-sm">
                    {PRIORITIES.map(p => <option key={p} value={p}>{p}</option>)}
                  </select>
                </div>
                <div>
                  <label className="text-xs text-slate-500">来源</label>
                  <select value={form.source} onChange={e => setForm({ ...form, source: e.target.value })} className="w-full border rounded-lg px-3 py-2 text-sm">
                    {SOURCES.map(s => <option key={s} value={s}>{SOURCE_LABELS[s]}</option>)}
                  </select>
                </div>
                <div>
                  <label className="text-xs text-slate-500">模块</label>
                  <input value={form.module} onChange={e => setForm({ ...form, module: e.target.value })} placeholder="模块" className="w-full border rounded-lg px-3 py-2 text-sm" />
                </div>
                <div>
                  <label className="text-xs text-slate-500">所属迭代</label>
                  <input value={form.iteration} onChange={e => setForm({ ...form, iteration: e.target.value })} placeholder="如 v1.2.5" className="w-full border rounded-lg px-3 py-2 text-sm" />
                </div>
                <div>
                  <label className="text-xs text-slate-500">问题类型</label>
                  <select value={form.issue_type} onChange={e => setForm({ ...form, issue_type: e.target.value })} className="w-full border rounded-lg px-3 py-2 text-sm">
                    {ISSUE_TYPES.map(s => <option key={s} value={s}>{s}</option>)}
                  </select>
                </div>
              </div>
              <input value={form.failure_category} onChange={e => setForm({ ...form, failure_category: e.target.value })} placeholder="失败分类" className="w-full border rounded-lg px-3 py-2 text-sm" />
              <input value={form.assigned_to} onChange={e => setForm({ ...form, assigned_to: e.target.value })} placeholder="分配给" className="w-full border rounded-lg px-3 py-2 text-sm" />
              <input value={form.requirement_source} onChange={e => setForm({ ...form, requirement_source: e.target.value })} placeholder="需求来源 / TAPD 链接" className="w-full border rounded-lg px-3 py-2 text-sm" />
              <textarea value={form.repro_steps} onChange={e => setForm({ ...form, repro_steps: e.target.value })} placeholder="复现步骤" rows={4} className="w-full border rounded-lg px-3 py-2 text-sm" />
              <textarea value={form.actual_result} onChange={e => setForm({ ...form, actual_result: e.target.value })} placeholder="实际结果" rows={3} className="w-full border rounded-lg px-3 py-2 text-sm" />
              <textarea value={form.expected_result} onChange={e => setForm({ ...form, expected_result: e.target.value })} placeholder="期望结果" rows={3} className="w-full border rounded-lg px-3 py-2 text-sm" />
              <textarea value={form.evidence_text} onChange={e => setForm({ ...form, evidence_text: e.target.value })} placeholder="证据：接口响应、截图说明、日志等" rows={3} className="w-full border rounded-lg px-3 py-2 text-sm" />
              <textarea value={form.code_refs} onChange={e => setForm({ ...form, code_refs: e.target.value })} placeholder="代码线索：文件路径 / 方法名" rows={2} className="w-full border rounded-lg px-3 py-2 text-sm" />
              <textarea value={form.api_refs} onChange={e => setForm({ ...form, api_refs: e.target.value })} placeholder="接口线索：URL / 字段 / 返回样例" rows={2} className="w-full border rounded-lg px-3 py-2 text-sm" />
              <textarea value={form.suggested_fix} onChange={e => setForm({ ...form, suggested_fix: e.target.value })} placeholder="建议修复方向" rows={2} className="w-full border rounded-lg px-3 py-2 text-sm" />
            </div>
            <div className="flex justify-end gap-2 mt-5">
              <button onClick={() => setShowCreate(false)} className="px-4 py-2 border rounded-lg text-sm">取消</button>
              <button onClick={handleCreate} disabled={!form.title} className="px-4 py-2 bg-red-600 text-white rounded-lg text-sm hover:bg-red-700 disabled:opacity-50">创建</button>
            </div>
          </div>
        </div>
      )}

      {/* Detail Dialog */}
      {showDetail && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl p-6 w-[700px] max-h-[85vh] overflow-y-auto shadow-2xl">
            <div className="flex justify-between items-start mb-4">
              <div>
                <h2 className="text-lg font-bold">#{showDetail.id} {showDetail.title}</h2>
                <div className="flex gap-2 mt-2">
                  <span className={`px-2 py-0.5 rounded text-xs ${SEVERITY_COLORS[showDetail.severity]}`}>{showDetail.severity}</span>
                  <span className={`px-2 py-0.5 rounded text-xs ${STATUS_COLORS[showDetail.status]}`}>{showDetail.status}</span>
                  <span className="px-2 py-0.5 rounded text-xs bg-slate-100">{showDetail.priority}</span>
                  <span className="px-2 py-0.5 rounded text-xs bg-indigo-50 text-indigo-700">{SOURCE_LABELS[showDetail.source] || showDetail.source}</span>
                </div>
              </div>
              <button onClick={() => setShowDetail(null)} className="text-slate-400 hover:text-slate-600 text-xl">&times;</button>
            </div>

            {showDetail.description && <p className="text-sm text-slate-600 mb-4 whitespace-pre-wrap">{showDetail.description}</p>}
            {showDetail.evidence_json && (
              <div className="mb-4 grid gap-3 text-sm">
                {showDetail.evidence_json.repro_steps && <section><h3 className="font-semibold text-slate-800 mb-1">复现步骤</h3><p className="whitespace-pre-wrap text-slate-600">{showDetail.evidence_json.repro_steps}</p></section>}
                {showDetail.evidence_json.actual_result && <section><h3 className="font-semibold text-slate-800 mb-1">实际结果</h3><p className="whitespace-pre-wrap text-slate-600">{showDetail.evidence_json.actual_result}</p></section>}
                {showDetail.evidence_json.expected_result && <section><h3 className="font-semibold text-slate-800 mb-1">期望结果</h3><p className="whitespace-pre-wrap text-slate-600">{showDetail.evidence_json.expected_result}</p></section>}
                {showDetail.evidence_json.suggested_fix && <section><h3 className="font-semibold text-slate-800 mb-1">建议修复方向</h3><p className="whitespace-pre-wrap text-slate-600">{showDetail.evidence_json.suggested_fix}</p></section>}
              </div>
            )}

            <div className="grid grid-cols-2 gap-2 text-xs mb-4">
              {showDetail.module && <div><span className="text-slate-400">模块:</span> {showDetail.module}</div>}
              {showDetail.case_id && <div><span className="text-slate-400">用例ID:</span> {showDetail.case_id}</div>}
              {showDetail.run_id && <div><span className="text-slate-400">执行ID:</span> {showDetail.run_id}</div>}
              {showDetail.assigned_to && <div><span className="text-slate-400">分配给:</span> {showDetail.assigned_to}</div>}
              {showDetail.failure_category && <div><span className="text-slate-400">失败分类:</span> {showDetail.failure_category}</div>}
              {showDetail.evidence_json?.iteration && <div><span className="text-slate-400">所属迭代:</span> {showDetail.evidence_json.iteration}</div>}
              {showDetail.evidence_json?.issue_type && <div><span className="text-slate-400">问题类型:</span> {showDetail.evidence_json.issue_type}</div>}
              {showDetail.evidence_json?.requirement_source && <div className="col-span-2"><span className="text-slate-400">需求来源:</span> {showDetail.evidence_json.requirement_source}</div>}
              {showDetail.created_by && <div><span className="text-slate-400">创建人:</span> {showDetail.created_by}</div>}
              {showDetail.created_at && <div><span className="text-slate-400">创建时间:</span> {showDetail.created_at.slice(0, 16).replace('T', ' ')}</div>}
              {showDetail.updated_at && <div><span className="text-slate-400">更新时间:</span> {showDetail.updated_at.slice(0, 16).replace('T', ' ')}</div>}
            </div>

            {/* Evidence */}
            {showDetail.evidence_json && Object.keys(showDetail.evidence_json).length > 0 && (
              <div className="mb-4">
                <h3 className="text-sm font-semibold mb-1">证据</h3>
                <div className="bg-slate-50 rounded-lg p-3 text-xs font-mono max-h-40 overflow-y-auto">
                  {Object.entries(showDetail.evidence_json).map(([k, v]) => (
                    <div key={k} className="mb-1"><span className="text-slate-500">{k}:</span> {typeof v === 'string' ? v : JSON.stringify(v)}</div>
                  ))}
                </div>
              </div>
            )}

            {/* Transitions */}
            <div className="flex gap-2 mb-4 flex-wrap">
              <button onClick={() => copyBugMarkdown(showDetail)} className="px-3 py-1.5 text-xs bg-slate-100 text-slate-700 rounded hover:bg-slate-200">复制 bug 单</button>
              {showDetail.evidence_json?.tapd_bug_id ? (
                <>
                  <a href={showDetail.evidence_json.tapd_url} target="_blank" rel="noreferrer" className="px-3 py-1.5 text-xs bg-green-50 text-green-700 rounded hover:bg-green-100">
                    TAPD #{showDetail.evidence_json.tapd_bug_id}
                    {showDetail.evidence_json.tapd_status_name ? ` (${showDetail.evidence_json.tapd_status_name})` : ''}
                  </a>
                  <button onClick={() => handleSyncTapd(showDetail.id)} title="同步 TAPD 状态" className="px-3 py-1.5 text-xs bg-cyan-50 text-cyan-700 rounded hover:bg-cyan-100">⥂ 同步</button>
                </>
              ) : (
                <button onClick={() => handlePushToTapd(showDetail.id)} className="px-3 py-1.5 text-xs bg-blue-50 text-blue-700 rounded hover:bg-blue-100">推送 TAPD</button>
              )}
              {(TRANSITIONS[showDetail.status] || []).map(t => (
                <button key={t} onClick={() => { setShowTransition({ id: showDetail.id, from: showDetail.status, to: t }); setTransitionComment('') }} className="px-3 py-1.5 text-xs bg-indigo-50 text-indigo-700 rounded hover:bg-indigo-100">→ {t}</button>
              ))}
            </div>

            {/* Events */}
            {showDetail.events?.length > 0 && (
              <div>
                <h3 className="text-sm font-semibold mb-2">事件历史 ({showDetail.events.length})</h3>
                <div className="space-y-2 max-h-60 overflow-y-auto">
                  {showDetail.events.map(ev => (
                    <div key={ev.id} className="bg-slate-50 rounded-lg p-2 text-xs">
                      <div className="flex justify-between">
                        <span className="font-medium">{ev.event_type}{ev.from_status ? ` ${ev.from_status} → ${ev.to_status}` : ev.to_status ? ` → ${ev.to_status}` : ''}</span>
                        <span className="text-slate-400">{ev.created_at?.slice(0, 16).replace('T', ' ')}</span>
                      </div>
                      {ev.comment && <p className="text-slate-500 mt-1">{ev.comment}</p>}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Transition Dialog */}
      {showTransition && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl p-6 w-[400px] shadow-2xl">
            <h2 className="text-lg font-bold mb-3">状态流转</h2>
            <p className="text-sm mb-3">{showTransition.from} → <span className="font-bold text-indigo-700">{showTransition.to}</span></p>
            <textarea value={transitionComment} onChange={e => setTransitionComment(e.target.value)} placeholder="备注（可选）" rows={2} className="w-full border rounded-lg px-3 py-2 text-sm mb-4" />
            <div className="flex justify-end gap-2">
              <button onClick={() => setShowTransition(null)} className="px-4 py-2 border rounded-lg text-sm">取消</button>
              <button onClick={() => handleTransition(showTransition.id, showTransition.to)} className="px-4 py-2 bg-indigo-600 text-white rounded-lg text-sm hover:bg-indigo-700">确认</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
