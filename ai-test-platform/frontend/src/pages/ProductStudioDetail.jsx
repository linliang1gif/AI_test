import { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';

const TYPE_LABELS = {
  product_solution: '产品方案',
  prd: 'PRD 文档',
  prototype: '原型说明',
  test_strategy: '测试策略',
  acceptance_criteria: '验收标准',
  quality_report: '质量报告',
};

// 简易 Markdown 渲染器（支持标题/表格/代码块/列表/粗体/emoji）
function renderMarkdown(md) {
  if (!md) return '<p class="text-slate-400">（空内容）</p>';
  let html = md
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    // code blocks
    .replace(/```(\w*)\n([\s\S]*?)```/g, '<pre class="bg-slate-100 p-3 rounded text-xs overflow-x-auto my-2"><code>$2</code></pre>')
    // tables
    .replace(/^\|(.+)\|$/gm, (match) => {
      const cells = match.split('|').filter(c => c.trim() !== '');
      const isHeader = cells.every(c => /^[\s-:]+$/.test(c));
      if (isHeader) return '<!-- sep -->';
      const tag = 'td';
      return '<tr>' + cells.map(c => `<${tag} class="border border-slate-200 px-2 py-1 text-xs">${c.trim()}</${tag}>`).join('') + '</tr>';
    })
    // headings
    .replace(/^### (.+)$/gm, '<h3 class="text-base font-semibold text-slate-800 mt-4 mb-1">$1</h3>')
    .replace(/^## (.+)$/gm, '<h2 class="text-lg font-bold text-slate-900 mt-5 mb-2 border-b pb-1">$1</h2>')
    .replace(/^# (.+)$/gm, '<h1 class="text-xl font-bold text-slate-900 mt-4 mb-3">$1</h1>')
    // bold
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    // list items
    .replace(/^- (.+)$/gm, '<li class="ml-4 list-disc text-sm text-slate-700">$1</li>')
    // cleanup separator rows
    .replace(/<!-- sep -->/g, '')
    // wrap table rows
    .replace(/(<tr>.*<\/tr>)/gs, '<table class="w-full border-collapse my-2">$1</table>')
    // paragraphs for remaining lines
    .replace(/^(?!<[ht1-6lr]|<pre|<li|<table|<strong)(\S.+)$/gm, '<p class="text-sm text-slate-700 my-1">$1</p>');
  // merge adjacent tables
  html = html.replace(/<\/table>\s*<table[^>]*>/g, '');
  return html;
}

const GENERATE_ENDPOINTS = {
  product_solution: 'generate-solution',
  prd: 'generate-prd',
  prototype: 'generate-prototype',
  test_strategy: 'generate-test-strategy',
  acceptance_criteria: 'generate-acceptance-criteria',
};

const EMPTY_FORM = {
  title: '', product_direction: '', target_users: '',
  pain_points: '', existing_assets: '', current_blockers: '', constraints: '',
};

export default function ProductStudioDetail() {
  const { ideaId } = useParams();
  const navigate = useNavigate();
  const isNew = !ideaId || ideaId === 'new';

  const [form, setForm] = useState(EMPTY_FORM);
  const [idea, setIdea] = useState(null);
  const [artifacts, setArtifacts] = useState([]);
  const [runs, setRuns] = useState([]);
  const [loading, setLoading] = useState(false);
  const [generating, setGenerating] = useState({});
  const [selectedArtifact, setSelectedArtifact] = useState(null);
  const [editMode, setEditMode] = useState(false);
  const [editContent, setEditContent] = useState('');
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [tab, setTab] = useState('artifacts'); // artifacts | runs
  const [traceLinks, setTraceLinks] = useState(null);
  const [generatingTrace, setGeneratingTrace] = useState({});
  const [qualitySummary, setQualitySummary] = useState(null);
  const [dashboard, setDashboard] = useState(null);
  const [generatingReport, setGeneratingReport] = useState(false);
  const [batchPromoting, setBatchPromoting] = useState(false);

  // ── 加载详情 ──
  const fetchDetail = useCallback(async () => {
    if (isNew) return;
    setLoading(true);
    try {
      const res = await fetch(`/api/v2/product-studio/ideas/${ideaId}`);
      if (!res.ok) throw new Error('加载失败');
      const data = await res.json();
      setIdea(data);
      setArtifacts(data.artifacts || []);
      setRuns(data.runs || []);
      setForm({
        title: data.title || '',
        product_direction: data.product_direction || '',
        target_users: data.target_users || '',
        pain_points: data.pain_points || '',
        existing_assets: data.existing_assets || '',
        current_blockers: data.current_blockers || '',
        constraints: data.constraints || '',
      });
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, [ideaId, isNew]);

  useEffect(() => { fetchDetail(); }, [fetchDetail]);

  // ── 创建想法 ──
  const handleCreate = async () => {
    if (!form.title.trim()) { setError('产品名称不能为空'); return; }
    setLoading(true);
    setError('');
    try {
      const res = await fetch('/api/v2/product-studio/ideas', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(form),
      });
      const data = await res.json();
      if (data.idea_id) navigate(`/product-studio/${data.idea_id}`, { replace: true });
    } catch (e) {
      setError('创建失败');
    } finally {
      setLoading(false);
    }
  };

  // ── 生成 ──
  const handleGenerate = async (runType) => {
    if (generating[runType]) return;
    setGenerating(g => ({ ...g, [runType]: true }));
    setError('');
    try {
      const endpoint = GENERATE_ENDPOINTS[runType];
      const res = await fetch(`/api/v2/product-studio/ideas/${ideaId}/${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({}),
      });
      if (!res.ok) { setError(`生成失败: HTTP ${res.status}`); await fetchDetail(); return; }
      const text = await res.text();
      if (!text) { setError('生成失败: 服务端返回空响应'); await fetchDetail(); return; }
      const data = JSON.parse(text);
      if (data.status === 'failed') {
        setError(`生成失败: ${data.error_message || '未知错误'}`);
      }
      await fetchDetail();
      if (data.artifact_id) {
        const artRes = await fetch(`/api/v2/product-studio/artifacts/${data.artifact_id}`);
        if (artRes.ok) {
          const artText = await artRes.text();
          if (artText) { setSelectedArtifact(JSON.parse(artText)); setEditMode(false); }
        }
      }
    } catch (e) {
      setError(`生成失败: ${e.message}`);
    } finally {
      setGenerating(g => ({ ...g, [runType]: false }));
    }
  };

  // ── 查看 Artifact ──
  const handleSelectArtifact = async (art) => {
    try {
      const res = await fetch(`/api/v2/product-studio/artifacts/${art.artifact_id}`);
      const data = await res.json();
      setSelectedArtifact(data);
      setEditContent(data.content_markdown || '');
      setEditMode(false);
      fetchTraceLinks(art.artifact_id);
      fetchQualitySummary(art.artifact_id);
    } catch (e) {
      setError('加载产物失败');
    }
  };

  // ── 保存编辑 ──
  const handleSave = async () => {
    if (!selectedArtifact) return;
    setSaving(true);
    try {
      await fetch(`/api/v2/product-studio/artifacts/${selectedArtifact.artifact_id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content_markdown: editContent }),
      });
      setSelectedArtifact(a => ({ ...a, content_markdown: editContent }));
      setEditMode(false);
      await fetchDetail();
    } catch (e) {
      setError('保存失败');
    } finally {
      setSaving(false);
    }
  };

  // ── 导出 ──
  const handleExport = async () => {
    if (!selectedArtifact) return;
    try {
      const res = await fetch(`/api/v2/product-studio/artifacts/${selectedArtifact.artifact_id}/export`, { method: 'POST' });
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${selectedArtifact.artifact_type}_${selectedArtifact.artifact_id}.md`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (e) {
      setError('导出失败');
    }
  };

  const isGenerating = Object.values(generating).some(Boolean);

  // ── Phase 2: 追溯 ──
  const fetchTraceLinks = async (artifactId) => {
    try {
      const res = await fetch(`/api/v2/product-studio/artifacts/${artifactId}/trace-links`);
      if (res.ok) {
        const data = await res.json();
        setTraceLinks(data);
      }
    } catch (e) { /* ignore */ }
  };

  const handleGenerateRP = async () => {
    if (!selectedArtifact || generatingTrace.rp) return;
    setGeneratingTrace(g => ({ ...g, rp: true }));
    setError('');
    try {
      const res = await fetch(`/api/v2/product-studio/artifacts/${selectedArtifact.artifact_id}/generate-requirement-points`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' }, body: '{}'
      });
      if (!res.ok) { setError(`需求点生成失败: HTTP ${res.status}`); return; }
      const text = await res.text();
      if (!text) { setError('需求点生成失败: 服务端返回空响应'); return; }
      const data = JSON.parse(text);
      if (data.error_message) setError(`需求点生成失败: ${data.error_message}`);
      await fetchTraceLinks(selectedArtifact.artifact_id);
    } catch (e) {
      setError(`需求点生成失败: ${e.message}`);
    } finally {
      setGeneratingTrace(g => ({ ...g, rp: false }));
    }
  };

  const handleGenerateTC = async () => {
    if (!selectedArtifact || generatingTrace.tc) return;
    setGeneratingTrace(g => ({ ...g, tc: true }));
    setError('');
    try {
      const res = await fetch(`/api/v2/product-studio/artifacts/${selectedArtifact.artifact_id}/generate-test-cases`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' }, body: '{}'
      });
      if (!res.ok) { setError(`测试用例生成失败: HTTP ${res.status}`); return; }
      const text = await res.text();
      if (!text) { setError('测试用例生成失败: 服务端返回空响应'); return; }
      const data = JSON.parse(text);
      if (data.error_message) setError(`测试用例生成失败: ${data.error_message}`);
      await fetchTraceLinks(selectedArtifact.artifact_id);
    } catch (e) {
      setError(`测试用例生成失败: ${e.message}`);
    } finally {
      setGeneratingTrace(g => ({ ...g, tc: false }));
    }
  };

  const fetchQualitySummary = async (artifactId) => {
    try {
      const res = await fetch(`/api/v2/product-studio/artifacts/${artifactId}/quality-summary`);
      if (res.ok) setQualitySummary(await res.json());
    } catch (e) { /* ignore */ }
  };

  const handleConfirmLink = async (linkId) => {
    const reason = prompt('确认原因（可留空）:');
    if (reason === null) return;
    try {
      await fetch(`/api/v2/product-studio/trace-links/${linkId}/confirm`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ review_reason: reason })
      });
      if (selectedArtifact) { await fetchTraceLinks(selectedArtifact.artifact_id); await fetchQualitySummary(selectedArtifact.artifact_id); }
    } catch (e) { setError('确认失败'); }
  };

  const handleRejectLink = async (linkId) => {
    const reason = prompt('驳回原因（可留空）:');
    if (reason === null) return;
    try {
      await fetch(`/api/v2/product-studio/trace-links/${linkId}/reject`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ review_reason: reason })
      });
      if (selectedArtifact) { await fetchTraceLinks(selectedArtifact.artifact_id); await fetchQualitySummary(selectedArtifact.artifact_id); }
    } catch (e) { setError('驳回失败'); }
  };

  const handleConfirmAll = async () => {
    const reason = prompt('批量确认原因（可留空）:');
    if (reason === null) return;
    const draftLinks = traceLinks?.trace_links?.filter(l => l.status === 'draft') || [];
    try {
      for (const l of draftLinks) {
        await fetch(`/api/v2/product-studio/trace-links/${l.link_id}/confirm`, {
          method: 'POST', headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ review_reason: reason })
        });
      }
      if (selectedArtifact) { await fetchTraceLinks(selectedArtifact.artifact_id); await fetchQualitySummary(selectedArtifact.artifact_id); }
    } catch (e) { setError('批量确认失败'); }
  };

  const handleRejectAll = async () => {
    const reason = prompt('批量驳回原因（可留空）:');
    if (reason === null) return;
    const draftLinks = traceLinks?.trace_links?.filter(l => l.status === 'draft') || [];
    try {
      for (const l of draftLinks) {
        await fetch(`/api/v2/product-studio/trace-links/${l.link_id}/reject`, {
          method: 'POST', headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ review_reason: reason })
        });
      }
      if (selectedArtifact) { await fetchTraceLinks(selectedArtifact.artifact_id); await fetchQualitySummary(selectedArtifact.artifact_id); }
    } catch (e) { setError('批量驳回失败'); }
  };

  const handleScoreAll = async () => {
    if (!selectedArtifact) return;
    try {
      await fetch(`/api/v2/product-studio/artifacts/${selectedArtifact.artifact_id}/score-trace-links`, { method: 'POST' });
      await fetchTraceLinks(selectedArtifact.artifact_id);
      await fetchQualitySummary(selectedArtifact.artifact_id);
    } catch (e) { setError('评分失败'); }
  };

  const handlePromoteLink = async (linkId) => {
    try {
      const res = await fetch(`/api/v2/product-studio/trace-links/${linkId}/promote-to-test-case`, { method: 'POST' });
      const data = await res.json();
      if (data.warning) alert(data.warning);
      if (selectedArtifact) { await fetchTraceLinks(selectedArtifact.artifact_id); await fetchQualitySummary(selectedArtifact.artifact_id); }
    } catch (e) { setError('转正式失败'); }
  };

  // ── Phase 5: 质量报告 / Dashboard / 批量 Promote ──
  const fetchDashboard = async () => {
    if (isNew || !ideaId) return;
    try {
      const res = await fetch(`/api/v2/product-studio/ideas/${ideaId}/quality-dashboard`);
      if (res.ok) setDashboard(await res.json());
    } catch (e) { /* ignore */ }
  };

  useEffect(() => { if (!isNew) fetchDashboard(); }, [ideaId, isNew]);

  const handleGenerateReport = async () => {
    if (generatingReport) return;
    setGeneratingReport(true);
    setError('');
    try {
      const res = await fetch(`/api/v2/product-studio/ideas/${ideaId}/generate-quality-report`, { method: 'POST' });
      if (!res.ok) { setError(`报告生成失败: HTTP ${res.status}`); return; }
      const data = await res.json();
      await fetchDetail();
      await fetchDashboard();
      if (data.artifact_id) {
        const artRes = await fetch(`/api/v2/product-studio/artifacts/${data.artifact_id}`);
        if (artRes.ok) { const artData = await artRes.json(); setSelectedArtifact(artData); setEditMode(false); }
      }
    } catch (e) {
      setError(`报告生成失败: ${e.message}`);
    } finally {
      setGeneratingReport(false);
    }
  };

  const handleBatchPromote = async () => {
    if (batchPromoting) return;
    if (!confirm('确定批量转正式？将 promote 已确认且质量分 >= 0.8 的用例')) return;
    setBatchPromoting(true);
    setError('');
    try {
      const res = await fetch(`/api/v2/product-studio/ideas/${ideaId}/batch-promote-test-cases`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ min_quality_score: 0.8, only_confirmed: true, max_count: 20 })
      });
      if (!res.ok) { setError(`批量转正式失败: HTTP ${res.status}`); return; }
      const data = await res.json();
      alert(`批量转正式完成\n✅ promoted: ${data.promoted_count}\n⏩ skipped: ${data.skipped_count}`);
      await fetchDashboard();
      if (selectedArtifact) { await fetchTraceLinks(selectedArtifact.artifact_id); await fetchQualitySummary(selectedArtifact.artifact_id); }
    } catch (e) {
      setError(`批量转正式失败: ${e.message}`);
    } finally {
      setBatchPromoting(false);
    }
  };

  // ══════════ 新建表单 ══════════
  if (isNew) {
    return (
      <div className="p-6 max-w-3xl mx-auto">
        <button onClick={() => navigate('/product-studio')} className="text-sm text-blue-600 hover:underline mb-4">
          ← 返回列表
        </button>
        <h1 className="text-2xl font-bold text-slate-900 mb-6">新建产品想法</h1>
        {error && <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">{error}</div>}
        <div className="space-y-4">
          {[
            { key: 'title', label: '产品名称 *', placeholder: '例如：AI 测试报告分析平台' },
            { key: 'product_direction', label: '产品方向', placeholder: '例如：SaaS / 内部工具 / 开源项目', area: false },
            { key: 'target_users', label: '目标用户', placeholder: '例如：测试工程师、QA Leader', area: false },
            { key: 'pain_points', label: '当前痛点', placeholder: '描述你想解决的问题...', area: true },
            { key: 'existing_assets', label: '已有基础', placeholder: '已有哪些代码/资源/用户...', area: true },
            { key: 'current_blockers', label: '当前卡点', placeholder: '目前遇到什么阻碍...', area: true },
            { key: 'constraints', label: '约束条件', placeholder: '预算/时间/技术栈等限制...', area: true },
          ].map(({ key, label, placeholder, area }) => (
            <div key={key}>
              <label className="block text-sm font-medium text-slate-700 mb-1">{label}</label>
              {area ? (
                <textarea
                  value={form[key]}
                  onChange={e => setForm(f => ({ ...f, [key]: e.target.value }))}
                  placeholder={placeholder}
                  rows={3}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:outline-none"
                />
              ) : (
                <input
                  type="text"
                  value={form[key]}
                  onChange={e => setForm(f => ({ ...f, [key]: e.target.value }))}
                  placeholder={placeholder}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:outline-none"
                />
              )}
            </div>
          ))}
          <div className="flex gap-3 pt-4">
            <button
              onClick={handleCreate}
              disabled={loading}
              className="px-6 py-2.5 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50"
            >
              {loading ? '创建中...' : '保存并进入详情'}
            </button>
          </div>
        </div>
      </div>
    );
  }

  // ══════════ 详情页 ══════════
  if (loading && !idea) {
    return <div className="p-6 text-center text-slate-400">加载中...</div>;
  }

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <button onClick={() => navigate('/product-studio')} className="text-sm text-blue-600 hover:underline mb-4">
        ← 返回列表
      </button>

      {error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700 flex justify-between items-center">
          <span>{error}</span>
          <button onClick={() => setError('')} className="text-red-400 hover:text-red-600">✕</button>
        </div>
      )}

      {/* 想法信息 */}
      <div className="bg-white border border-slate-200 rounded-xl p-6 mb-6">
        <h1 className="text-xl font-bold text-slate-900 mb-3">{idea?.title}</h1>
        <div className="grid grid-cols-2 gap-4 text-sm">
          {[
            ['产品方向', idea?.product_direction],
            ['目标用户', idea?.target_users],
            ['当前痛点', idea?.pain_points],
            ['已有基础', idea?.existing_assets],
            ['当前卡点', idea?.current_blockers],
            ['约束条件', idea?.constraints],
          ].filter(([, v]) => v).map(([label, value]) => (
            <div key={label}>
              <span className="text-slate-500">{label}：</span>
              <span className="text-slate-800">{value}</span>
            </div>
          ))}
        </div>
      </div>

      {/* 生成按钮组 */}
      <div className="flex gap-3 mb-6 flex-wrap">
        {Object.entries(TYPE_LABELS).filter(([t]) => t !== 'quality_report').map(([type, label]) => (
          <button
            key={type}
            onClick={() => handleGenerate(type)}
            disabled={generating[type] || isGenerating}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
              generating[type]
                ? 'bg-blue-100 text-blue-600 animate-pulse'
                : 'bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50'
            }`}
          >
            {generating[type] ? `生成${label}中...` : `生成${label}`}
          </button>
        ))}
        <button
          onClick={handleGenerateReport}
          disabled={generatingReport}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
            generatingReport ? 'bg-amber-100 text-amber-700 animate-pulse' : 'bg-amber-600 text-white hover:bg-amber-700'}`}
        >
          {generatingReport ? '生成质量报告中...' : '📊 生成质量报告'}
        </button>
        <button
          onClick={handleBatchPromote}
          disabled={batchPromoting}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
            batchPromoting ? 'bg-indigo-100 text-indigo-700 animate-pulse' : 'bg-indigo-600 text-white hover:bg-indigo-700'}`}
        >
          {batchPromoting ? '批量转正式中...' : '⬆️ 批量转正式'}
        </button>
      </div>

      {/* Phase 5: 质量 Dashboard */}
      {dashboard && dashboard.summary && (
        <div className="mb-6 bg-white border border-slate-200 rounded-xl p-5">
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-sm font-bold text-slate-900">📊 质量 Dashboard</h2>
            <button onClick={fetchDashboard} className="text-xs text-blue-600 hover:underline">刷新</button>
          </div>
          <div className="grid grid-cols-4 sm:grid-cols-8 gap-3 text-center text-xs mb-3">
            {[
              ['产物', dashboard.summary.artifact_count, 'text-slate-700'],
              ['需求点', dashboard.summary.requirement_point_count, 'text-purple-700'],
              ['TC草稿', dashboard.summary.test_case_draft_count, 'text-teal-700'],
              ['TraceLink', dashboard.summary.trace_link_count, 'text-slate-700'],
              ['已确认', dashboard.summary.confirmed_count, 'text-green-700'],
              ['已驳回', dashboard.summary.rejected_count, 'text-red-600'],
              ['已转正', dashboard.summary.promotion_count, 'text-indigo-700'],
              ['质量分', dashboard.summary.average_quality_score, dashboard.summary.average_quality_score >= 0.7 ? 'text-green-700' : 'text-red-600'],
            ].map(([label, val, cls]) => (
              <div key={label}><span className={`block font-bold text-base ${cls}`}>{val}</span>{label}</div>
            ))}
          </div>
          {dashboard.risk_flags?.length > 0 && (
            <div className="flex flex-wrap gap-1.5 mb-2">
              {dashboard.risk_flags.map(f => (
                <span key={f} className="px-2 py-0.5 bg-red-50 text-red-700 rounded text-xs">⚠️ {f}</span>
              ))}
            </div>
          )}
          {dashboard.recommendations?.length > 0 && (
            <div className="text-xs text-slate-600 space-y-0.5">
              {dashboard.recommendations.map((r, i) => <div key={i}>• {r}</div>)}
            </div>
          )}
        </div>
      )}

      {/* Tabs */}
      <div className="flex gap-1 mb-4 border-b border-slate-200">
        {[
          { key: 'artifacts', label: `产物 (${artifacts.length})` },
          { key: 'runs', label: `执行记录 (${runs.length})` },
        ].map(t => (
          <button
            key={t.key}
            onClick={() => setTab(t.key)}
            className={`px-4 py-2.5 text-sm font-medium border-b-2 transition-colors ${
              tab === t.key
                ? 'border-blue-600 text-blue-600'
                : 'border-transparent text-slate-500 hover:text-slate-700'
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      <div className="flex gap-6">
        {/* 左侧列表 */}
        <div className="w-80 flex-shrink-0">
          {tab === 'artifacts' ? (
            artifacts.length === 0 ? (
              <div className="text-center py-8 text-slate-400 text-sm">暂无产物，点击上方按钮生成</div>
            ) : (
              <div className="space-y-2">
                {artifacts.map(art => (
                  <div
                    key={art.artifact_id}
                    onClick={() => handleSelectArtifact(art)}
                    className={`p-3 rounded-lg border cursor-pointer transition-all text-sm ${
                      selectedArtifact?.artifact_id === art.artifact_id
                        ? 'border-blue-300 bg-blue-50'
                        : 'border-slate-200 bg-white hover:border-slate-300'
                    }`}
                  >
                    <div className="font-medium text-slate-800">{art.title || TYPE_LABELS[art.artifact_type]}</div>
                    <div className="flex items-center gap-2 mt-1">
                      <span className={`px-1.5 py-0.5 rounded text-xs ${
                        art.status === 'confirmed' ? 'bg-green-50 text-green-700' :
                        art.status === 'archived' ? 'bg-slate-100 text-slate-500' :
                        'bg-yellow-50 text-yellow-700'
                      }`}>{art.status}</span>
                      <span className="text-xs text-slate-400">
                        {art.created_at ? new Date(art.created_at).toLocaleString() : ''}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )
          ) : (
            runs.length === 0 ? (
              <div className="text-center py-8 text-slate-400 text-sm">暂无执行记录</div>
            ) : (
              <div className="space-y-2">
                {runs.map(run => (
                  <div key={run.run_id} className="p-3 rounded-lg border border-slate-200 bg-white text-sm">
                    <div className="flex items-center gap-2">
                      <span className={`w-2 h-2 rounded-full ${
                        run.status === 'succeeded' ? 'bg-green-500' :
                        run.status === 'failed' ? 'bg-red-500' :
                        run.status === 'running' ? 'bg-blue-500 animate-pulse' :
                        'bg-slate-400'
                      }`} />
                      <span className="font-medium text-slate-800">{TYPE_LABELS[run.run_type] || run.run_type}</span>
                    </div>
                    <div className="mt-1.5 text-xs text-slate-500 space-y-0.5">
                      <div>run: {run.run_id}</div>
                      <div>模型: {run.model_name || '-'}</div>
                      <div>trace: {run.trace_id}</div>
                      <div>耗时: {run.started_at && run.finished_at
                        ? `${((new Date(run.finished_at) - new Date(run.started_at)) / 1000).toFixed(1)}s`
                        : '-'}</div>
                      {run.error_message && (
                        <div className="text-red-600 mt-1">错误: {run.error_message}</div>
                      )}
                      <div>{run.created_at ? new Date(run.created_at).toLocaleString() : ''}</div>
                    </div>
                  </div>
                ))}
              </div>
            )
          )}
        </div>

        {/* 右侧预览/编辑 */}
        <div className="flex-1 min-w-0">
          {selectedArtifact ? (
            <div className="bg-white border border-slate-200 rounded-xl p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold text-slate-900">{selectedArtifact.title}</h2>
                <div className="flex gap-2">
                  {editMode ? (
                    <>
                      <button
                        onClick={handleSave}
                        disabled={saving}
                        className="px-3 py-1.5 bg-green-600 text-white rounded-md text-sm hover:bg-green-700 disabled:opacity-50"
                      >
                        {saving ? '保存中...' : '保存'}
                      </button>
                      <button
                        onClick={() => { setEditMode(false); setEditContent(selectedArtifact.content_markdown || ''); }}
                        className="px-3 py-1.5 bg-slate-100 text-slate-700 rounded-md text-sm hover:bg-slate-200"
                      >
                        取消
                      </button>
                    </>
                  ) : (
                    <>
                      <button
                        onClick={() => { setEditMode(true); setEditContent(selectedArtifact.content_markdown || ''); }}
                        className="px-3 py-1.5 bg-slate-100 text-slate-700 rounded-md text-sm hover:bg-slate-200"
                      >
                        编辑
                      </button>
                      <button
                        onClick={handleExport}
                        className="px-3 py-1.5 bg-slate-100 text-slate-700 rounded-md text-sm hover:bg-slate-200"
                      >
                        导出 MD
                      </button>
                      <button
                        onClick={() => {
                          const params = new URLSearchParams({
                            source_type: 'product_artifact',
                            source_id: selectedArtifact.artifact_id || '',
                            idea_id: ideaId || '',
                            title: `[${TYPE_LABELS[selectedArtifact.artifact_type] || selectedArtifact.artifact_type}] ${idea?.title || ''}`,
                          });
                          navigate(`/dev-studio/new?${params}`);
                        }}
                        className="px-3 py-1.5 bg-indigo-600 text-white rounded-md text-sm hover:bg-indigo-700"
                      >
                        创建开发任务
                      </button>
                    </>
                  )}
                </div>
              </div>
              {/* run 信息 */}
              {selectedArtifact.run_id && (
                <div className="text-xs text-slate-400 mb-4">
                  run: {selectedArtifact.run_id} | artifact: {selectedArtifact.artifact_id}
                </div>
              )}
              {/* Phase 2: 转测试资产按钮 */}
              {!editMode && (
                <div className="flex gap-2 mb-4">
                  {['prd', 'product_solution'].includes(selectedArtifact.artifact_type) && (
                    <button
                      onClick={handleGenerateRP}
                      disabled={generatingTrace.rp}
                      className="px-3 py-1.5 bg-purple-600 text-white rounded-md text-sm hover:bg-purple-700 disabled:opacity-50"
                    >
                      {generatingTrace.rp ? '生成中...' : '生成需求点'}
                    </button>
                  )}
                  {['prd', 'test_strategy', 'acceptance_criteria'].includes(selectedArtifact.artifact_type) && (
                    <button
                      onClick={handleGenerateTC}
                      disabled={generatingTrace.tc}
                      className="px-3 py-1.5 bg-teal-600 text-white rounded-md text-sm hover:bg-teal-700 disabled:opacity-50"
                    >
                      {generatingTrace.tc ? '生成中...' : '生成测试用例草稿'}
                    </button>
                  )}
                </div>
              )}
              {/* Phase 3: 质量统计面板 */}
              {qualitySummary && qualitySummary.total_links > 0 && (
                <div className="mb-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
                  <div className="flex items-center justify-between mb-1">
                    <h3 className="text-xs font-semibold text-blue-800">📊 质量统计</h3>
                    <button onClick={handleScoreAll} className="px-2 py-0.5 bg-blue-600 text-white rounded text-xs hover:bg-blue-700">批量评分</button>
                  </div>
                  <div className="grid grid-cols-4 gap-2 text-xs text-center">
                    <div><span className="block font-medium text-slate-700">{qualitySummary.total_links}</span>总数</div>
                    <div><span className="block font-medium text-green-700">{qualitySummary.confirmed_count}</span>已确认</div>
                    <div><span className="block font-medium text-red-600">{qualitySummary.rejected_count}</span>已驳回</div>
                    <div><span className="block font-medium text-yellow-700">{qualitySummary.draft_count}</span>草稿</div>
                  </div>
                  <div className="grid grid-cols-3 gap-2 text-xs text-center mt-2">
                    <div><span className={`block font-medium ${qualitySummary.average_quality_score >= 0.8 ? 'text-green-700' : qualitySummary.average_quality_score >= 0.6 ? 'text-yellow-700' : 'text-red-600'}`}>{qualitySummary.average_quality_score}</span>平均质量分</div>
                    <div><span className="block font-medium text-blue-700">{qualitySummary.promotion_count}</span>已转正式</div>
                    <div><span className="block font-medium text-slate-600">{(qualitySummary.acceptance_rate * 100).toFixed(0)}%</span>采纳率</div>
                  </div>
                </div>
              )}
              {/* 追溯链路 */}
              {traceLinks && (traceLinks.requirement_points?.length > 0 || traceLinks.test_cases?.length > 0) && (
                <div className="mb-4 p-4 bg-slate-50 border border-slate-200 rounded-lg">
                  <h3 className="text-sm font-semibold text-slate-700 mb-2">📌 追溯链路</h3>
                  {traceLinks.requirement_points?.length > 0 && (
                    <div className="mb-3">
                      <div className="text-xs font-medium text-purple-700 mb-1">需求点 ({traceLinks.requirement_points.length})</div>
                      <div className="space-y-1">
                        {traceLinks.requirement_points.map((rp) => {
                          const lk = traceLinks.trace_links?.find(l => l.target_id === rp.id);
                          const qs = lk?.quality_score;
                          return (
                            <div key={rp.id} className="flex items-center justify-between text-xs bg-white p-2 rounded border border-slate-100">
                              <span className="flex-1 text-slate-700 truncate mr-2">{rp.title}</span>
                              {qs != null && <span className={`px-1 py-0.5 rounded mr-1 ${qs >= 0.8 ? 'bg-green-50 text-green-700' : qs >= 0.6 ? 'bg-yellow-50 text-yellow-700' : 'bg-red-50 text-red-600'}`}>{qs}</span>}
                              <span className={`px-1.5 py-0.5 rounded ${rp.link_status === 'confirmed' ? 'bg-green-50 text-green-700' : rp.link_status === 'rejected' ? 'bg-red-50 text-red-700' : 'bg-yellow-50 text-yellow-700'}`}>{rp.link_status}</span>
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  )}
                  {traceLinks.test_cases?.length > 0 && (
                    <div>
                      <div className="text-xs font-medium text-teal-700 mb-1">测试用例 ({traceLinks.test_cases.length})</div>
                      <div className="space-y-1">
                        {traceLinks.test_cases.map((tc) => {
                          const lk = traceLinks.trace_links?.find(l => l.target_id === tc.id);
                          const qs = lk?.quality_score;
                          const canPromote = lk && lk.target_type === 'test_case' && ['draft','confirmed'].includes(lk.status) && !lk.promoted_at;
                          return (
                            <div key={tc.id} className="flex items-center justify-between text-xs bg-white p-2 rounded border border-slate-100">
                              <span className="flex-1 text-slate-700 truncate mr-1">{tc.title}</span>
                              <span className="text-slate-400 mr-1">{tc.case_type}</span>
                              {qs != null && <span className={`px-1 py-0.5 rounded mr-1 ${qs >= 0.8 ? 'bg-green-50 text-green-700' : qs >= 0.6 ? 'bg-yellow-50 text-yellow-700' : 'bg-red-50 text-red-600'}`}>{qs}</span>}
                              {qs != null && qs < 0.6 && <span className="text-red-500 mr-1" title="低质量">⚠️</span>}
                              <span className={`px-1.5 py-0.5 rounded mr-1 ${tc.link_status === 'confirmed' ? 'bg-green-50 text-green-700' : tc.link_status === 'rejected' ? 'bg-red-50 text-red-700' : 'bg-yellow-50 text-yellow-700'}`}>{tc.link_status}</span>
                              {canPromote && <button onClick={() => handlePromoteLink(lk.link_id)} className="px-1.5 py-0.5 bg-indigo-600 text-white rounded text-xs hover:bg-indigo-700">转正式</button>}
                              {lk?.promoted_at && <span className="px-1.5 py-0.5 bg-indigo-50 text-indigo-700 rounded">已转正</span>}
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  )}
                  {/* 操作按钮 */}
                  <div className="flex gap-2 mt-3 flex-wrap">
                    {traceLinks.trace_links?.filter(l => l.status === 'draft').length > 0 && (
                      <>
                        <button onClick={handleConfirmAll} className="px-3 py-1 bg-green-600 text-white rounded text-xs hover:bg-green-700">全部确认</button>
                        <button onClick={handleRejectAll} className="px-3 py-1 bg-red-500 text-white rounded text-xs hover:bg-red-600">全部驳回</button>
                      </>
                    )}
                  </div>
                </div>
              )}
              {/* 内容 */}
              {editMode ? (
                <textarea
                  value={editContent}
                  onChange={e => setEditContent(e.target.value)}
                  className="w-full h-[600px] px-4 py-3 border border-slate-300 rounded-lg text-sm font-mono focus:ring-2 focus:ring-blue-500 focus:outline-none resize-y"
                />
              ) : (
                <div
                  className="prose prose-sm prose-slate max-w-none overflow-auto max-h-[700px] bg-slate-50 p-4 rounded-lg border"
                  dangerouslySetInnerHTML={{ __html: renderMarkdown(selectedArtifact.content_markdown) }}
                />
              )}
            </div>
          ) : (
            <div className="text-center py-20 text-slate-400">
              <div className="text-4xl mb-3">📄</div>
              <p>点击左侧产物查看内容，或点击上方按钮生成新产物</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
