import { useState, useEffect, useCallback } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import {
  Card, Steps, Button, Upload, Space, Tabs, Tag, message, Spin, Alert,
  Descriptions, Progress, Input, Empty, Tooltip, Badge, Dropdown, Statistic, Row, Col,
  Modal, Select,
} from 'antd';
import {
  UploadOutlined, FileSearchOutlined, CodeOutlined, CheckCircleOutlined,
  CloseCircleOutlined, QuestionCircleOutlined, WarningOutlined,
  ExperimentOutlined, HistoryOutlined, ArrowLeftOutlined,
  InboxOutlined, FileZipOutlined, BugOutlined, FormOutlined, BranchesOutlined, LockOutlined,
} from '@ant-design/icons';
import { codeCompareAPI } from '../services/api';

const { TextArea } = Input;
const { Dragger } = Upload;

// ── finding 类型配置 ──
const FINDING_TYPES = {
  implemented: { label: '已实现', color: '#52c41a', bg: '#f6ffed', border: '#b7eb8f', icon: <CheckCircleOutlined /> },
  missing:     { label: '疑似未实现', color: '#ff4d4f', bg: '#fff2f0', border: '#ffccc7', icon: <CloseCircleOutlined /> },
  extra:       { label: '超范围实现', color: '#722ed1', bg: '#f9f0ff', border: '#d3adf7', icon: <QuestionCircleOutlined /> },
  uncertain:   { label: '不确定', color: '#fa8c16', bg: '#fff7e6', border: '#ffd591', icon: <QuestionCircleOutlined /> },
  risk:        { label: '风险点', color: '#cf1322', bg: '#fff1f0', border: '#ffa39e', icon: <WarningOutlined /> },
};

const CONFIRM_OPTIONS = [
  { key: 'confirmed_implemented', label: '确认已实现' },
  { key: 'confirmed_missing', label: '确认未实现' },
  { key: 'false_positive', label: '误报' },
  { key: 'need_discussion', label: '待产品确认' },
];

// 按 finding 类型显示不同流转按钮
const FLOW_BUTTONS_BY_TYPE = {
  implemented: ['test_case', 'false_positive'],
  missing:     ['defect', 'test_case', 'question', 'false_positive'],
  risk:        ['defect', 'test_case', 'question', 'false_positive'],
  extra:       ['question', 'test_case', 'false_positive'],
  uncertain:   ['question', 'test_case', 'false_positive'],
};

export default function CodeCompare() {
  const [searchParams] = useSearchParams();
  const [currentStep, setCurrentStep] = useState(0);

  // Step 1 states
  const [requirementSource, setRequirementSource] = useState(null); // 'url' | 'text'
  const [requirementId, setRequirementId] = useState(null);
  const [requirementText, setRequirementText] = useState('');
  const [requirementSummary, setRequirementSummary] = useState(null);

  // Step 2 states
  const [uploading, setUploading] = useState(false);
  const [snapshot, setSnapshot] = useState(null);
  const [codeSource, setCodeSource] = useState('zip'); // 'zip' | 'git'
  const [gitUrl, setGitUrl] = useState('');
  const [gitBranch, setGitBranch] = useState('main');
  const [gitToken, setGitToken] = useState('');
  const [gitSubDir, setGitSubDir] = useState('');
  const [cloning, setCloning] = useState(false);

  // Step 3 states
  const [analyzing, setAnalyzing] = useState(false);
  const [analyzeProgress, setAnalyzeProgress] = useState(0);
  const [analyzeStep, setAnalyzeStep] = useState('');
  const [aiProviders, setAiProviders] = useState([]);
  const [aiProvider, setAiProvider] = useState(null);   // null = 用默认
  const [aiModel, setAiModel] = useState(null);

  // Step 4 states
  const [report, setReport] = useState(null);
  const [activeTab, setActiveTab] = useState('all');
  const [confirmingId, setConfirmingId] = useState(null);

  // History
  const [showHistory, setShowHistory] = useState(false);
  const [historyReports, setHistoryReports] = useState([]);
  const [loadingHistory, setLoadingHistory] = useState(false);

  // Flow modal
  const [flowModal, setFlowModal] = useState({ open: false, type: null, finding: null });
  const [flowLoading, setFlowLoading] = useState(false);
  const [flowForm, setFlowForm] = useState({});

  // ── Step 1: 自动读取 URL 参数 ──
  useEffect(() => {
    const reqId = searchParams.get('requirement_id');
    if (reqId) {
      setRequirementId(reqId);
      setRequirementSource('url');
      // 从 localStorage 读取缓存的需求摘要
      try {
        const cached = localStorage.getItem(`req_summary_${reqId}`);
        if (cached) {
          setRequirementSummary(JSON.parse(cached));
        }
      } catch (e) { /* ignore */ }
    }
  }, [searchParams]);

  // ── 加载 AI 提供商列表 ──
  useEffect(() => {
    fetch('/api/ai/providers').then(r => r.json()).then(data => {
      setAiProviders(data.providers || []);
    }).catch(() => {});
  }, []);

  // ── Step 2: 上传代码 ZIP ──
  const handleUpload = useCallback(async (file) => {
    if (!file.name.endsWith('.zip')) {
      message.error('仅支持 ZIP 格式');
      return false;
    }
    if (file.size > 100 * 1024 * 1024) {
      message.error('文件过大，最大 100MB');
      return false;
    }
    setUploading(true);
    try {
      const formData = new FormData();
      formData.append('file', file);
      const data = await codeCompareAPI.uploadCodeSnapshot(formData);
      if (data.success) {
        setSnapshot(data.snapshot);
        message.success('代码快照上传成功');
      } else {
        message.error(data.detail || '上传失败');
      }
    } catch (e) {
      message.error(`上传失败: ${e.message}`);
    } finally {
      setUploading(false);
    }
    return false; // prevent antd auto upload
  }, []);

  // ── Step 2b: Git 克隆 ──
  const handleCloneRepo = useCallback(async () => {
    if (!gitUrl.trim()) { message.error('请输入 Git 仓库地址'); return; }
    setCloning(true);
    try {
      const data = await codeCompareAPI.cloneRepo({
        repo_url: gitUrl.trim(),
        branch: gitBranch.trim() || 'main',
        token: gitToken.trim() || undefined,
        sub_dir: gitSubDir.trim() || undefined,
      });
      if (data.success) {
        setSnapshot(data.snapshot);
        message.success(`仓库克隆成功: ${data.snapshot.name}`);
      } else {
        message.error(data.detail || '克隆失败');
      }
    } catch (e) {
      message.error(`克隆失败: ${e.message}`);
    } finally {
      setCloning(false);
    }
  }, [gitUrl, gitBranch, gitToken, gitSubDir]);

  // ── Step 3: 开始分析 ──
  const handleAnalyze = useCallback(async () => {
    if (!snapshot) { message.error('请先上传代码包'); return; }
    if (!requirementId && !requirementText.trim()) {
      message.error('请先选择需求来源'); return;
    }

    // 如果有 requirementId 但 localStorage 没有完整数据，提示用户输入文本兜底
    if (requirementId && !requirementText.trim()) {
      const hasLocalData = !!localStorage.getItem(`req_data_${requirementId}`);
      if (!hasLocalData) {
        message.warning('需求缓存已过期，请在下方文本框中重新输入需求内容，或返回需求页面重新解析');
        setRequirementId(null);
        setRequirementSummary(null);
        setRequirementSource('text');
        setCurrentStep(0);
        return;
      }
    }

    setAnalyzing(true);
    setCurrentStep(2);
    setAnalyzeProgress(0);
    setAnalyzeStep('正在提取需求点...');

    const steps = [
      [500,    5,  '正在提取需求点...'],
      [2000,  10,  '正在扫描代码结构...'],
      [5000,  20,  'AI 正在逐条对比需求（第 1 批）...'],
      [15000, 35,  'AI 正在逐条对比需求（第 2 批）...'],
      [30000, 50,  'AI 正在深度分析代码实现...'],
      [60000, 65,  '正在检查边界条件和校验规则...'],
      [90000, 80,  '正在生成 Bug 清单和测试建议...'],
    ];
    const timers = steps.map(([delay, pct, txt]) =>
      setTimeout(() => { setAnalyzeProgress(pct); setAnalyzeStep(txt); }, delay)
    );

    try {
      // 如果有 requirementId，先尝试从 localStorage 重新缓存到后端（防止服务器重启丢失）
      let effectiveReqId = null;
      let fallbackText = requirementText.trim() || null;

      if (requirementId) {
        try {
          const cachedData = localStorage.getItem(`req_data_${requirementId}`);
          if (cachedData) {
            const res = await codeCompareAPI.cacheRequirement(JSON.parse(cachedData));
            if (res.success && res.requirement_id) {
              effectiveReqId = res.requirement_id;
            }
          }
        } catch (_) { /* ignore */ }

        // 如果 localStorage 没有完整数据，尝试直接用原始 id（可能后端磁盘有）
        if (!effectiveReqId) {
          effectiveReqId = requirementId;
        }
      }

      // 同时传 requirement_text 作为双保险：后端 id 找不到时可用 text 兜底
      const data = await codeCompareAPI.analyzeRequirementCodeCompare({
        requirement_id: effectiveReqId || undefined,
        requirement_text: fallbackText || undefined,
        code_snapshot_id: snapshot.snapshot_id,
        use_ai: true,
        provider: aiProvider || undefined,
        model: aiModel || undefined,
      });
      timers.forEach(clearTimeout);
      if (data.success) {
        setReport(data.report);
        setAnalyzeProgress(100);
        setAnalyzeStep('分析完成');
        setTimeout(() => setCurrentStep(3), 600);
        message.success('对比分析完成');
      } else {
        message.error(data.detail || '分析失败');
        setCurrentStep(1);
      }
    } catch (e) {
      timers.forEach(clearTimeout);
      message.error(`分析失败: ${e.message}`);
      setCurrentStep(1);
    } finally {
      setAnalyzing(false);
    }
  }, [snapshot, requirementId, requirementText]);

  // ── 人工确认 ──
  const handleConfirm = useCallback(async (findingId, status) => {
    if (!report) return;
    setConfirmingId(findingId);
    try {
      const data = await codeCompareAPI.confirmCodeCompareFinding(report.report_id, {
        finding_id: findingId,
        manual_status: status,
      });
      if (data.success) {
        _updateFinding(findingId, { manual_status: status, confirmed_at: new Date().toISOString() });
        message.success('确认成功');
      }
    } catch (e) {
      message.error(`确认失败: ${e.message}`);
    } finally {
      setConfirmingId(null);
    }
  }, [report]);

  // ── 更新单个 finding ──
  const _updateFinding = useCallback((findingId, patch) => {
    setReport(prev => ({
      ...prev,
      findings: prev.findings.map(f =>
        f.finding_id === findingId ? { ...f, ...patch } : f
      ),
    }));
  }, []);

  // ── 流转操作 ──
  const handleFlowAction = useCallback(async () => {
    const { type, finding } = flowModal;
    if (!finding) return;
    setFlowLoading(true);
    try {
      let res;
      if (type === 'defect') {
        res = await codeCompareAPI.convertFindingToDefect(finding.finding_id, {
          severity: flowForm.severity || 'major',
          priority: flowForm.priority || 'P2',
          assignee: flowForm.assignee || '',
          review_comment: flowForm.review_comment || '',
        });
        if (res.success) {
          _updateFinding(finding.finding_id, { manual_status: 'converted_to_bug', target_type: 'defect', target_id: String(res.data?.defect_id) });
          message.success(`已转缺陷 #${res.data?.defect_id}`);
        }
      } else if (type === 'test_case') {
        res = await codeCompareAPI.convertFindingToTestCase(finding.finding_id, {
          case_priority: flowForm.case_priority || 'P1',
          case_type: 'whitebox_enhanced',
          module_name: flowForm.module_name || '',
        });
        if (res.success) {
          _updateFinding(finding.finding_id, { manual_status: 'converted_to_case', target_type: 'test_case', target_id: res.data?.case_ids?.join(',') });
          message.success(`已生成 ${res.data?.case_ids?.length} 条测试用例`);
        }
      } else if (type === 'question') {
        if (!flowForm.question?.trim()) { message.warning('请输入待确认问题'); setFlowLoading(false); return; }
        res = await codeCompareAPI.convertFindingToQuestion(finding.finding_id, {
          owner: flowForm.owner || 'product',
          question: flowForm.question,
          review_comment: flowForm.review_comment || '',
        });
        if (res.success) {
          _updateFinding(finding.finding_id, { manual_status: 'need_product_confirm', target_type: 'question', target_id: res.data?.question_id });
          message.success('已转待确认问题');
        }
      } else if (type === 'false_positive') {
        if (!flowForm.reason?.trim()) { message.warning('请输入误报原因'); setFlowLoading(false); return; }
        res = await codeCompareAPI.markFindingFalsePositive(finding.finding_id, {
          reason: flowForm.reason,
        });
        if (res.success) {
          _updateFinding(finding.finding_id, { manual_status: 'false_positive', review_comment: flowForm.reason });
          message.success('已标记误报');
        }
      } else if (type === 'tapd') {
        res = await codeCompareAPI.pushFindingToTapd(finding.finding_id, {
          title: flowForm.title || undefined,
          severity: flowForm.severity || undefined,
          priority: flowForm.priority || undefined,
          iteration: flowForm.iteration || undefined,
          module: flowForm.module || undefined,
          steps: flowForm.steps || undefined,
          expected: flowForm.expected || undefined,
          actual: flowForm.actual || undefined,
          code_location: flowForm.code_location || undefined,
        });
        if (res.success) {
          if (res.already_pushed) {
            message.info(`该 Finding 已推送: TAPD #${res.bug_id}`);
          } else {
            _updateFinding(finding.finding_id, { tapd_bug_id: res.bug_id, tapd_url: res.url });
            message.success(<span>已推送 TAPD <a href={res.url} target="_blank" rel="noreferrer">#{res.bug_id}</a></span>);
          }
        }
      }
      setFlowModal({ open: false, type: null, finding: null });
      setFlowForm({});
    } catch (e) {
      message.error(`操作失败: ${e.message}`);
    } finally {
      setFlowLoading(false);
    }
  }, [flowModal, flowForm, _updateFinding]);

  const openFlowModal = useCallback((type, finding) => {
    setFlowModal({ open: true, type, finding });
    setFlowForm({});
  }, []);

  // ── 历史报告 ──
  const loadHistory = useCallback(async () => {
    setLoadingHistory(true);
    try {
      const data = await codeCompareAPI.getCodeCompareReports();
      setHistoryReports(data.success ? data.reports : []);
    } catch (e) {
      message.error(`加载历史报告失败: ${e.message}`);
    } finally {
      setLoadingHistory(false);
    }
  }, []);

  const loadReportDetail = useCallback(async (reportId) => {
    try {
      const data = await codeCompareAPI.getCodeCompareReportDetail(reportId);
      if (data.success) {
        setReport(data.report);
        setCurrentStep(3);
        setShowHistory(false);
      }
    } catch (e) {
      message.error(`加载报告详情失败: ${e.message}`);
    }
  }, []);

  // ── 需求确认判断 ──
  const isReqReady = requirementId || requirementText.trim().length > 10;

  // ── 过滤 findings ──
  const getFilteredFindings = (type) => {
    if (!report) return [];
    if (type === 'all') return report.findings;
    return report.findings.filter(f => f.type === type);
  };

  return (
    <div style={{ padding: 24, maxWidth: 1200, margin: '0 auto' }}>
      {/* 页头 */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <div>
          <h2 style={{ margin: 0, fontSize: 20, fontWeight: 600 }}>需求-代码对比</h2>
          <p style={{ margin: '4px 0 0', color: '#666', fontSize: 13 }}>
            对比需求文档中的功能点与代码中的实际实现，识别差异并生成白盒测试建议
          </p>
        </div>
        <Space>
          <Button icon={<HistoryOutlined />} onClick={() => { setShowHistory(!showHistory); if (!showHistory) loadHistory(); }}>
            历史报告
          </Button>
          <Link to="/requirement-upload">
            <Button icon={<ArrowLeftOutlined />}>返回需求生成用例</Button>
          </Link>
        </Space>
      </div>

      {/* 历史报告面板 */}
      {showHistory && (
        <Card size="small" title="历史报告" style={{ marginBottom: 16 }}
          extra={<Button size="small" onClick={() => setShowHistory(false)}>关闭</Button>}
        >
          {loadingHistory ? <Spin /> : historyReports.length === 0 ? (
            <Empty description="暂无历史报告" />
          ) : (
            <div style={{ maxHeight: 300, overflow: 'auto' }}>
              {historyReports.map(r => (
                <div key={r.report_id} style={{
                  display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                  padding: '8px 0', borderBottom: '1px solid #f0f0f0',
                }}>
                  <div>
                    <span style={{ fontWeight: 500 }}>{r.code_snapshot_name || r.report_id}</span>
                    <span style={{ color: '#999', marginLeft: 8, fontSize: 12 }}>{r.created_at?.split('T')[0]}</span>
                    <span style={{ marginLeft: 12 }}>
                      <Tag color="green">{r.summary?.implemented || 0} 已实现</Tag>
                      <Tag color="red">{r.summary?.missing || 0} 缺失</Tag>
                      <Tag color="orange">{r.summary?.risk || 0} 风险</Tag>
                    </span>
                  </div>
                  <Button size="small" type="link" onClick={() => loadReportDetail(r.report_id)}>查看详情</Button>
                </div>
              ))}
            </div>
          )}
        </Card>
      )}

      {/* Steps */}
      <Steps current={currentStep} style={{ marginBottom: 32 }} items={[
        { title: '选择需求来源' },
        { title: '上传代码包' },
        { title: '开始对比分析' },
        { title: '查看分析报告' },
      ]} />

      {/* ========== Step 1: 选择需求来源 ========== */}
      {currentStep === 0 && (
        <Card title="选择需求来源">
          {requirementId && requirementSummary ? (
            <Alert type="success" showIcon icon={<CheckCircleOutlined />}
              message="需求来源已确认"
              description={
                <Descriptions size="small" column={3} style={{ marginTop: 8 }}>
                  <Descriptions.Item label="需求ID">{requirementId}</Descriptions.Item>
                  <Descriptions.Item label="模块数">{requirementSummary.modules || 0}</Descriptions.Item>
                  <Descriptions.Item label="功能点">{requirementSummary.features || 0}</Descriptions.Item>
                  <Descriptions.Item label="业务规则">{requirementSummary.rules || 0}</Descriptions.Item>
                  <Descriptions.Item label="字段数">{requirementSummary.fields || 0}</Descriptions.Item>
                  {requirementSummary.axure_notes > 0 && (
                    <Descriptions.Item label="Axure注释">{requirementSummary.axure_notes}</Descriptions.Item>
                  )}
                  <Descriptions.Item label="解析时间">{requirementSummary.parsed_at || '-'}</Descriptions.Item>
                </Descriptions>
              }
            />
          ) : requirementId ? (
            <Alert type="info" showIcon message={`已关联需求 ID: ${requirementId}`}
              description="将使用该需求解析结果进行对比分析" />
          ) : (
            <div>
              <p style={{ marginBottom: 12, color: '#666' }}>
                请粘贴需求文本，或从「需求生成用例」页面解析后跳转过来。
              </p>
              <TextArea
                rows={8}
                placeholder={"请在此输入需求内容，每行一个功能点或业务规则。\n\n例如：\n1. 用户可以新增付款单\n2. 付款单必须填写供应商、金额、付款方式\n3. 审核通过后不允许修改\n4. 支持分账付款，需拆分明细"}
                value={requirementText}
                onChange={e => {
                  setRequirementText(e.target.value);
                  setRequirementSource('text');
                }}
              />
              {requirementText.trim().length > 0 && requirementText.trim().length <= 10 && (
                <p style={{ color: '#fa8c16', fontSize: 12, marginTop: 4 }}>请输入更多需求内容（至少 10 个字符）</p>
              )}
            </div>
          )}
          <div style={{ marginTop: 16, textAlign: 'right' }}>
            <Button type="primary" disabled={!isReqReady} onClick={() => setCurrentStep(1)}>
              下一步：上传代码包
            </Button>
          </div>
        </Card>
      )}

      {/* ========== Step 2: 上传代码包 ========== */}
      {currentStep === 1 && (
        <Card title="获取代码">
          {!snapshot ? (
            <Tabs activeKey={codeSource} onChange={setCodeSource} items={[
              {
                key: 'zip',
                label: <span><FileZipOutlined /> 上传 ZIP 包</span>,
                children: (
                  <Dragger
                    accept=".zip"
                    maxCount={1}
                    showUploadList={false}
                    beforeUpload={handleUpload}
                    disabled={uploading}
                  >
                    <p className="ant-upload-drag-icon">
                      {uploading ? <Spin size="large" /> : <InboxOutlined style={{ fontSize: 48, color: '#1890ff' }} />}
                    </p>
                    <p className="ant-upload-text">{uploading ? '正在上传并解压...' : '点击或拖拽上传代码 ZIP 包'}</p>
                    <p className="ant-upload-hint">支持 .zip 格式，最大 100MB。将自动忽略 node_modules、.git 等目录。</p>
                  </Dragger>
                ),
              },
              {
                key: 'git',
                label: <span><BranchesOutlined /> Git 仓库克隆</span>,
                children: (
                  <div style={{ maxWidth: 600 }}>
                    <div style={{ marginBottom: 16 }}>
                      <label style={{ display: 'block', marginBottom: 4, fontWeight: 500 }}>仓库地址 *</label>
                      <Input
                        placeholder="https://gitlab.example.com/group/repo.git"
                        value={gitUrl}
                        onChange={e => setGitUrl(e.target.value)}
                        disabled={cloning}
                      />
                    </div>
                    <Space style={{ marginBottom: 16, width: '100%' }} size={16}>
                      <div style={{ flex: 1 }}>
                        <label style={{ display: 'block', marginBottom: 4, fontWeight: 500 }}>分支</label>
                        <Input
                          placeholder="main"
                          value={gitBranch}
                          onChange={e => setGitBranch(e.target.value)}
                          disabled={cloning}
                          style={{ width: 160 }}
                        />
                      </div>
                      <div style={{ flex: 1 }}>
                        <label style={{ display: 'block', marginBottom: 4, fontWeight: 500 }}>子目录（可选）</label>
                        <Input
                          placeholder="src"
                          value={gitSubDir}
                          onChange={e => setGitSubDir(e.target.value)}
                          disabled={cloning}
                          style={{ width: 160 }}
                        />
                      </div>
                    </Space>
                    <div style={{ marginBottom: 16 }}>
                      <label style={{ display: 'block', marginBottom: 4, fontWeight: 500 }}>
                        <LockOutlined /> Access Token（私有仓库需填）
                      </label>
                      <Input.Password
                        placeholder="glpat-xxxx 或 ghp_xxxx"
                        value={gitToken}
                        onChange={e => setGitToken(e.target.value)}
                        disabled={cloning}
                      />
                    </div>
                    <Button
                      type="primary"
                      icon={<BranchesOutlined />}
                      loading={cloning}
                      onClick={handleCloneRepo}
                      disabled={!gitUrl.trim()}
                    >
                      {cloning ? '正在克隆...' : '开始克隆'}
                    </Button>
                    <p style={{ color: '#999', fontSize: 12, marginTop: 8 }}>
                      支持 GitLab / GitHub / Gitee 等，使用 --depth 1 浅克隆，自动忽略 node_modules、.git 等目录。
                    </p>
                  </div>
                ),
              },
            ]} />
          ) : (
            <div>
              <Alert type="success" showIcon
                message={snapshot.source === 'git_clone' ? '仓库克隆成功' : '代码快照上传成功'}
                style={{ marginBottom: 16 }}
              />
              <Descriptions bordered size="small" column={2}>
                <Descriptions.Item label="快照名称">{snapshot.name}</Descriptions.Item>
                <Descriptions.Item label="文件总数">{snapshot.total_files}</Descriptions.Item>
                {snapshot.repo_url && (
                  <Descriptions.Item label="仓库地址" span={2}>
                    <Tag color="blue"><BranchesOutlined /> {snapshot.branch}</Tag> {snapshot.repo_url}
                  </Descriptions.Item>
                )}
                <Descriptions.Item label="语言分布" span={2}>
                  {Object.entries(snapshot.language_distribution || {}).map(([lang, count]) => (
                    <Tag key={lang}>{lang}: {count}</Tag>
                  ))}
                </Descriptions.Item>
                <Descriptions.Item label="主要目录" span={2}>
                  {(snapshot.top_dirs || []).slice(0, 8).map(d => (
                    <Tag key={d} color="blue">{d}</Tag>
                  ))}
                </Descriptions.Item>
                <Descriptions.Item label="创建时间">{snapshot.upload_time?.replace('T', ' ').split('.')[0]}</Descriptions.Item>
              </Descriptions>
              <Button style={{ marginTop: 12 }} onClick={() => setSnapshot(null)}>重新获取</Button>
            </div>
          )}
          <div style={{ marginTop: 16, display: 'flex', justifyContent: 'space-between' }}>
            <Button onClick={() => setCurrentStep(0)}>上一步</Button>
            <Button type="primary" disabled={!snapshot} onClick={() => setCurrentStep(2)}>
              下一步：开始分析
            </Button>
          </div>
        </Card>
      )}

      {/* ========== Step 3: 分析中 ========== */}
      {currentStep === 2 && (
        <Card title="需求-代码对比分析">
          {!analyzing && !report ? (
            <div style={{ textAlign: 'center', padding: '40px 0' }}>
              <FileSearchOutlined style={{ fontSize: 48, color: '#1890ff', marginBottom: 16 }} />
              <p style={{ fontSize: 16, marginBottom: 24 }}>准备就绪，点击下方按钮开始对比分析</p>
              <Space direction="vertical" align="center">
                <Descriptions size="small" column={2} style={{ maxWidth: 400, textAlign: 'left' }}>
                  <Descriptions.Item label="需求来源">{requirementId || '手动输入'}</Descriptions.Item>
                  <Descriptions.Item label="代码快照">{snapshot?.name}</Descriptions.Item>
                </Descriptions>
                <div style={{ display: 'flex', gap: 12, justifyContent: 'center', marginTop: 8 }}>
                  <div>
                    <div style={{ fontSize: 12, color: '#999', marginBottom: 4 }}>AI 提供商</div>
                    <Select
                      value={aiProvider}
                      onChange={v => { setAiProvider(v); setAiModel(null); }}
                      style={{ width: 160 }}
                      placeholder="默认"
                      allowClear
                      options={aiProviders.filter(p => p.status === 'available').map(p => ({ value: p.id, label: p.name }))}
                    />
                  </div>
                  <div>
                    <div style={{ fontSize: 12, color: '#999', marginBottom: 4 }}>模型</div>
                    <Select
                      value={aiModel}
                      onChange={setAiModel}
                      style={{ width: 200 }}
                      placeholder="默认"
                      allowClear
                      options={(aiProviders.find(p => p.id === aiProvider)?.models || []).map(m => ({ value: m, label: m }))}
                    />
                  </div>
                </div>
                <Button type="primary" size="large" icon={<ExperimentOutlined />} onClick={handleAnalyze}>
                  开始需求-代码对比
                </Button>
                <Button onClick={() => setCurrentStep(1)}>上一步</Button>
              </Space>
            </div>
          ) : (
            <div style={{ maxWidth: 500, margin: '0 auto', padding: '60px 0' }}>
              <div style={{ textAlign: 'center', marginBottom: 32 }}>
                <Spin size="large" />
              </div>
              <div style={{ marginBottom: 8, display: 'flex', justifyContent: 'space-between', fontSize: 14 }}>
                <span style={{ color: '#333' }}>{analyzeStep}</span>
                <span style={{ color: '#999' }}>{analyzeProgress}%</span>
              </div>
              <Progress percent={analyzeProgress} showInfo={false} strokeColor={{ '0%': '#108ee9', '100%': '#87d068' }} />
              <p style={{ color: '#999', fontSize: 12, marginTop: 16, textAlign: 'center' }}>
                AI 正在逐条深度对比，预计 2-5 分钟，请耐心等待
              </p>
            </div>
          )}
        </Card>
      )}

      {/* ========== Step 4: 报告 ========== */}
      {currentStep === 3 && report && (
        <Space direction="vertical" style={{ width: '100%' }} size="middle">
          {/* 统计卡片 */}
          <Row gutter={12}>
            {[
              { key: 'total_req_points', title: '需求点总数', color: '#1890ff' },
              { key: 'implemented', title: '已实现', color: '#52c41a' },
              { key: 'missing', title: '疑似未实现', color: '#ff4d4f' },
              { key: 'extra', title: '超范围实现', color: '#722ed1' },
              { key: 'uncertain', title: '不确定', color: '#fa8c16' },
              { key: 'risk', title: '风险点', color: '#cf1322' },
            ].map(item => (
              <Col span={4} key={item.key}>
                <Card size="small" style={{ borderTop: `3px solid ${item.color}` }}>
                  <Statistic
                    title={<span style={{ fontSize: 12 }}>{item.title}</span>}
                    value={report.summary?.[item.key] || 0}
                    valueStyle={{ color: item.color, fontSize: 24 }}
                  />
                </Card>
              </Col>
            ))}
          </Row>

          {/* Tabs */}
          <Card>
            <Tabs activeKey={activeTab} onChange={setActiveTab} items={[
              { key: 'all', label: `全部 (${report.findings?.length || 0})` },
              ...Object.entries(FINDING_TYPES).map(([key, cfg]) => ({
                key,
                label: (
                  <span>
                    {cfg.label} ({getFilteredFindings(key).length})
                  </span>
                ),
              })),
            ]} />

            {/* Findings */}
            {getFilteredFindings(activeTab).length === 0 ? (
              <Empty description="暂无数据" />
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                {getFilteredFindings(activeTab).map(finding => (
                  <FindingCard
                    key={finding.finding_id}
                    finding={finding}
                    onConfirm={handleConfirm}
                    confirming={confirmingId === finding.finding_id}
                    reportId={report.report_id}
                    onFlow={openFlowModal}
                  />
                ))}
              </div>
            )}
          </Card>

          {/* AI 降级提示 */}
          {report.ai_mode === 'fallback' && (
            <Alert type="warning" showIcon message="AI 深度分析不可用，已使用规则匹配结果" style={{ marginTop: -4 }} />
          )}

          <div style={{ textAlign: 'center' }}>
            <Button onClick={() => { setCurrentStep(0); setReport(null); }}>新建对比分析</Button>
          </div>
        </Space>
      )}

      {/* ── 流转 Modal ── */}
      <FlowModal
        open={flowModal.open}
        type={flowModal.type}
        finding={flowModal.finding}
        form={flowForm}
        setForm={setFlowForm}
        loading={flowLoading}
        onOk={handleFlowAction}
        onCancel={() => { setFlowModal({ open: false, type: null, finding: null }); setFlowForm({}); }}
      />
    </div>
  );
}


// ── 状态标签映射 ──
const MANUAL_STATUS_LABELS = {
  confirmed_implemented: { text: '已确认实现', color: 'green' },
  confirmed_missing:     { text: '已确认缺失', color: 'red' },
  false_positive:        { text: '误报', color: 'default' },
  need_discussion:       { text: '待讨论', color: 'orange' },
  converted_to_bug:      { text: '已转缺陷', color: 'red' },
  converted_to_case:     { text: '已转用例', color: 'blue' },
  need_product_confirm:  { text: '待产品确认', color: 'orange' },
};

const FLOW_LABELS = {
  defect:         { text: '转缺陷', icon: <BugOutlined /> },
  test_case:      { text: '转测试用例', icon: <FormOutlined /> },
  question:       { text: '待产品确认', icon: <QuestionCircleOutlined /> },
  false_positive: { text: '标记误报', icon: <CloseCircleOutlined /> },
};


// ── Finding 卡片组件 ──

function FindingCard({ finding, onConfirm, confirming, reportId, onFlow }) {
  const typeCfg = FINDING_TYPES[finding.type] || FINDING_TYPES.uncertain;
  const flowButtons = FLOW_BUTTONS_BY_TYPE[finding.type] || ['false_positive'];

  const confirmMenuItems = CONFIRM_OPTIONS.map(opt => ({
    key: opt.key,
    label: opt.label,
    onClick: () => onConfirm(finding.finding_id, opt.key),
  }));

  return (
    <div style={{
      border: `1px solid ${typeCfg.border}`,
      borderLeft: `4px solid ${typeCfg.color}`,
      borderRadius: 6,
      padding: 16,
      background: typeCfg.bg,
    }}>
      {/* 头部 */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 8 }}>
        <div style={{ flex: 1 }}>
          <Space wrap>
            <Tag color={typeCfg.color} icon={typeCfg.icon}>{typeCfg.label}</Tag>
            {finding.confidence != null && (
              <Tooltip title="置信度"><Tag>{Math.round(finding.confidence * 100)}%</Tag></Tooltip>
            )}
            {finding.manual_status && (
              <Tag color={MANUAL_STATUS_LABELS[finding.manual_status]?.color || 'default'}>
                {MANUAL_STATUS_LABELS[finding.manual_status]?.text || finding.manual_status}
              </Tag>
            )}
            {finding.target_type && finding.target_id && (
              <Tag color="geekblue">{finding.target_type}: {finding.target_id}</Tag>
            )}
          </Space>
          <h4 style={{ margin: '8px 0 0', fontSize: 14, fontWeight: 500 }}>{finding.requirement}</h4>
        </div>
        <Dropdown menu={{ items: confirmMenuItems }} trigger={['click']} disabled={confirming}>
          <Button size="small" loading={confirming}>
            {finding.manual_status ? '重新确认' : '人工确认'}
          </Button>
        </Dropdown>
      </div>

      {/* 分析说明 */}
      {finding.analysis && (
        <p style={{ color: '#555', fontSize: 13, margin: '8px 0' }}>{finding.analysis}</p>
      )}

      {/* 代码证据 */}
      {finding.code_evidence && (
        <div style={{
          background: '#fff', border: '1px solid #e8e8e8', borderRadius: 4,
          padding: '8px 12px', marginTop: 8, fontSize: 12,
        }}>
          <div style={{ fontWeight: 500, marginBottom: 4 }}>
            <CodeOutlined style={{ marginRight: 4 }} /> 代码证据
          </div>
          {finding.code_evidence.file && (
            <div><span style={{ color: '#999' }}>文件:</span> {finding.code_evidence.file}</div>
          )}
          {finding.code_evidence.line > 0 && (
            <div><span style={{ color: '#999' }}>行号:</span> {finding.code_evidence.line}</div>
          )}
          {finding.code_evidence.match_reason && (
            <div><span style={{ color: '#999' }}>匹配原因:</span> {finding.code_evidence.match_reason}</div>
          )}
        </div>
      )}

      {/* 建议测试用例 */}
      {finding.test_suggestion && (
        <div style={{
          background: '#fff', border: '1px solid #e8e8e8', borderRadius: 4,
          padding: '8px 12px', marginTop: 8, fontSize: 12,
        }}>
          <div style={{ fontWeight: 500, marginBottom: 4 }}>
            <ExperimentOutlined style={{ marginRight: 4 }} /> 建议测试用例
          </div>
          <div><span style={{ color: '#999' }}>标题:</span> {finding.test_suggestion.title}</div>
          {finding.test_suggestion.precondition && (
            <div><span style={{ color: '#999' }}>前置条件:</span> {finding.test_suggestion.precondition}</div>
          )}
          {finding.test_suggestion.steps && (
            <div>
              <span style={{ color: '#999' }}>操作步骤:</span>
              <ol style={{ paddingLeft: 20, margin: '2px 0' }}>
                {(Array.isArray(finding.test_suggestion.steps) ? finding.test_suggestion.steps : [finding.test_suggestion.steps])
                  .map((s, i) => <li key={i}>{s}</li>)}
              </ol>
            </div>
          )}
          {finding.test_suggestion.expected && (
            <div><span style={{ color: '#999' }}>预期结果:</span> {finding.test_suggestion.expected}</div>
          )}
        </div>
      )}

      {/* 流转按钮 */}
      <div style={{ marginTop: 12, display: 'flex', gap: 8, flexWrap: 'wrap' }}>
        {flowButtons.map(fb => {
          const cfg = FLOW_LABELS[fb];
          return (
            <Button key={fb} size="small" icon={cfg.icon}
              onClick={() => onFlow(fb, finding)}
              disabled={finding.manual_status && ['converted_to_bug', 'converted_to_case'].includes(finding.manual_status)}
            >
              {cfg.text}
            </Button>
          );
        })}
        {finding.type !== 'implemented' && (
          finding.tapd_bug_id ? (
            <Button size="small" type="link" href={finding.tapd_url} target="_blank"
              style={{ color: '#1890ff' }}>
              TAPD #{finding.tapd_bug_id}
            </Button>
          ) : (
            <Button size="small" style={{ borderColor: '#13c2c2', color: '#13c2c2' }}
              onClick={() => onFlow('tapd', finding)}>
              推送 TAPD
            </Button>
          )
        )}
      </div>
    </div>
  );
}


// ── 流转 Modal 组件 ──

function FlowModal({ open, type, finding, form, setForm, loading, onOk, onCancel }) {
  if (!type) return null;

  const titles = {
    defect: '转为缺陷',
    test_case: '转为测试用例',
    question: '转为待确认问题',
    false_positive: '标记误报',
    tapd: '推送到 TAPD',
  };

  return (
    <Modal
      title={titles[type] || '操作'}
      open={open}
      onOk={onOk}
      onCancel={onCancel}
      confirmLoading={loading}
      okText={type === 'tapd' ? '推送到 TAPD' : '确定'}
      destroyOnClose
      width={type === 'tapd' ? 640 : 520}
    >
      {finding && (
        <div style={{ marginBottom: 16, padding: 8, background: '#fafafa', borderRadius: 4, fontSize: 13 }}>
          <strong>需求点: </strong>{finding.requirement}
        </div>
      )}

      {type === 'defect' && (
        <Space direction="vertical" style={{ width: '100%' }}>
          <div>
            <div style={{ marginBottom: 4, fontSize: 13 }}>严重级别</div>
            <Select value={form.severity || 'major'} onChange={v => setForm({ ...form, severity: v })} style={{ width: '100%' }}
              options={[{ value: 'critical', label: '严重' }, { value: 'major', label: '主要' }, { value: 'minor', label: '轻微' }]} />
          </div>
          <div>
            <div style={{ marginBottom: 4, fontSize: 13 }}>优先级</div>
            <Select value={form.priority || 'P2'} onChange={v => setForm({ ...form, priority: v })} style={{ width: '100%' }}
              options={[{ value: 'P0', label: 'P0' }, { value: 'P1', label: 'P1' }, { value: 'P2', label: 'P2' }]} />
          </div>
          <div>
            <div style={{ marginBottom: 4, fontSize: 13 }}>备注</div>
            <Input.TextArea rows={2} value={form.review_comment || ''} onChange={e => setForm({ ...form, review_comment: e.target.value })} />
          </div>
        </Space>
      )}

      {type === 'test_case' && (
        <Space direction="vertical" style={{ width: '100%' }}>
          <div>
            <div style={{ marginBottom: 4, fontSize: 13 }}>用例优先级</div>
            <Select value={form.case_priority || 'P1'} onChange={v => setForm({ ...form, case_priority: v })} style={{ width: '100%' }}
              options={[{ value: 'P0', label: 'P0' }, { value: 'P1', label: 'P1' }, { value: 'P2', label: 'P2' }]} />
          </div>
          <div>
            <div style={{ marginBottom: 4, fontSize: 13 }}>模块名称</div>
            <Input value={form.module_name || ''} onChange={e => setForm({ ...form, module_name: e.target.value })} placeholder="可选" />
          </div>
        </Space>
      )}

      {type === 'question' && (
        <Space direction="vertical" style={{ width: '100%' }}>
          <div>
            <div style={{ marginBottom: 4, fontSize: 13 }}>需要确认的问题 *</div>
            <Input.TextArea rows={3} value={form.question || ''} onChange={e => setForm({ ...form, question: e.target.value })}
              placeholder="请描述需要产品确认的问题" />
          </div>
          <div>
            <div style={{ marginBottom: 4, fontSize: 13 }}>指派给</div>
            <Select value={form.owner || 'product'} onChange={v => setForm({ ...form, owner: v })} style={{ width: '100%' }}
              options={[{ value: 'product', label: '产品' }, { value: 'dev', label: '开发' }, { value: 'test', label: '测试' }]} />
          </div>
          <div>
            <div style={{ marginBottom: 4, fontSize: 13 }}>备注</div>
            <Input.TextArea rows={2} value={form.review_comment || ''} onChange={e => setForm({ ...form, review_comment: e.target.value })} />
          </div>
        </Space>
      )}

      {type === 'false_positive' && (
        <div>
          <div style={{ marginBottom: 4, fontSize: 13 }}>误报原因 *</div>
          <Input.TextArea rows={3} value={form.reason || ''} onChange={e => setForm({ ...form, reason: e.target.value })}
            placeholder="请说明为什么认为这是误报" />
        </div>
      )}

      {type === 'tapd' && (
        <Space direction="vertical" style={{ width: '100%' }} size={12}>
          <div>
            <div style={{ marginBottom: 4, fontSize: 13, fontWeight: 500 }}>Bug 标题 *</div>
            <Input
              value={form.title ?? (finding ? (() => {
                // 从 requirement 提取简洁标题：去掉序号前缀如 "4、"、"1. " 等
                let raw = finding.requirement || '';
                raw = raw.replace(/^\d+[、.．)\]】]\s*/, '');
                // 如果有【模块】前缀就直接用，否则加上 module
                if (/^[【\[]/.test(raw)) return raw;
                const mod = finding.module || '';
                return mod ? `[${mod}] ${raw}` : raw;
              })() : '')}
              onChange={e => setForm({ ...form, title: e.target.value })}
              placeholder="[模块名] 问题描述"
            />
          </div>
          <div style={{ display: 'flex', gap: 12 }}>
            <div style={{ flex: 1 }}>
              <div style={{ marginBottom: 4, fontSize: 13, fontWeight: 500 }}>迭代</div>
              <Input
                value={form.iteration || ''}
                onChange={e => setForm({ ...form, iteration: e.target.value })}
                placeholder="如 1.2.3"
              />
            </div>
            <div style={{ flex: 1 }}>
              <div style={{ marginBottom: 4, fontSize: 13, fontWeight: 500 }}>模块</div>
              <Input
                value={form.module || finding?.module || ''}
                onChange={e => setForm({ ...form, module: e.target.value })}
                placeholder="如 暂估应付单"
              />
            </div>
          </div>
          <div style={{ display: 'flex', gap: 12 }}>
            <div style={{ flex: 1 }}>
              <div style={{ marginBottom: 4, fontSize: 13, fontWeight: 500 }}>严重程度</div>
              <Select value={form.severity || 'minor'} onChange={v => setForm({ ...form, severity: v })} style={{ width: '100%' }}
                options={[{ value: 'critical', label: '致命' }, { value: 'major', label: '严重' }, { value: 'minor', label: '一般' }, { value: 'trivial', label: '提示' }]} />
            </div>
            <div style={{ flex: 1 }}>
              <div style={{ marginBottom: 4, fontSize: 13, fontWeight: 500 }}>优先级</div>
              <Select value={form.priority || 'P2'} onChange={v => setForm({ ...form, priority: v })} style={{ width: '100%' }}
                options={[{ value: 'P0', label: '紧急' }, { value: 'P1', label: '高' }, { value: 'P2', label: '中' }, { value: 'P3', label: '低' }]} />
            </div>
          </div>
          <div>
            <div style={{ marginBottom: 4, fontSize: 13, fontWeight: 500 }}>操作步骤 *</div>
            <Input.TextArea
              rows={3}
              value={form.steps ?? (finding?.test_suggestion ? `1. ${finding.test_suggestion.steps || finding.test_suggestion.scenario || ''}` : '')}
              onChange={e => setForm({ ...form, steps: e.target.value })}
              placeholder={"1. 进入xxx页面\n2. 点击xxx按钮\n3. 检查xxx"}
            />
          </div>
          <div>
            <div style={{ marginBottom: 4, fontSize: 13, fontWeight: 500 }}>预期结果 *</div>
            <Input.TextArea
              rows={2}
              value={form.expected ?? (finding?.test_suggestion?.expected || '')}
              onChange={e => setForm({ ...form, expected: e.target.value })}
              placeholder="应该xxx"
            />
          </div>
          <div>
            <div style={{ marginBottom: 4, fontSize: 13, fontWeight: 500 }}>实际结果 *</div>
            <Input.TextArea
              rows={2}
              value={form.actual ?? (finding?.analysis || '')}
              onChange={e => setForm({ ...form, actual: e.target.value })}
              placeholder="实际xxx"
            />
          </div>
          <div>
            <div style={{ marginBottom: 4, fontSize: 13, fontWeight: 500 }}>代码位置（可选）</div>
            <Input
              value={form.code_location ?? (Array.isArray(finding?.code_evidence) ? finding.code_evidence.map(e => `${e.file_path || e.file || ''}:${e.line || ''}`).join(', ') : '')}
              onChange={e => setForm({ ...form, code_location: e.target.value })}
              placeholder="xxx.vue:343, 345"
            />
          </div>
        </Space>
      )}
    </Modal>
  );
}
