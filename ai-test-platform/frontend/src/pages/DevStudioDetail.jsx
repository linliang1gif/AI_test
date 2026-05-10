import { useState, useEffect } from 'react';
import { useParams, useNavigate, useSearchParams } from 'react-router-dom';

const TYPE_LABELS = {
  dev_plan: '开发计划',
  api_design: 'API 设计',
  db_design: '数据库设计',
  file_impact: '影响文件分析',
  file_impact_v2: '增强影响分析',
  test_plan: '测试计划',
  patch_draft: '补丁草稿',
  patch_review: '补丁评审',
};

const SOURCE_LABELS = {
  product_artifact: '产品产物',
  test_case: '测试用例',
  manual: '手动创建',
};

const STATUS_LABELS = {
  succeeded: '成功',
  failed: '失败',
  running: '运行中',
  draft: '草稿',
  confirmed: '已确认',
  archived: '已归档',
  created: '已创建',
};

const GENERATE_ENDPOINTS = {
  dev_plan: 'generate-dev-plan',
  api_design: 'generate-api-design',
  db_design: 'generate-db-design',
  file_impact: 'generate-file-impact',
  test_plan: 'generate-test-plan',
};

const GENERATE_COLORS = {
  dev_plan: 'bg-blue-600 hover:bg-blue-700',
  api_design: 'bg-purple-600 hover:bg-purple-700',
  db_design: 'bg-teal-600 hover:bg-teal-700',
  file_impact: 'bg-amber-600 hover:bg-amber-700',
  test_plan: 'bg-green-600 hover:bg-green-700',
};

function renderMarkdown(md) {
  if (!md) return '<p class="text-slate-400">（空内容）</p>';
  let html = md
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/```(\w*)\n([\s\S]*?)```/g, '<pre class="bg-slate-100 p-3 rounded text-xs overflow-x-auto my-2"><code>$2</code></pre>')
    .replace(/^\|(.+)\|$/gm, (match) => {
      const cells = match.split('|').filter(c => c.trim() !== '');
      const isHeader = cells.every(c => /^[\s-:]+$/.test(c));
      if (isHeader) return '<!-- sep -->';
      const tag = 'td';
      return '<tr>' + cells.map(c => `<${tag} class="border border-slate-200 px-2 py-1 text-xs">${c.trim()}</${tag}>`).join('') + '</tr>';
    })
    .replace(/^### (.+)$/gm, '<h3 class="text-base font-semibold text-slate-800 mt-4 mb-1">$1</h3>')
    .replace(/^## (.+)$/gm, '<h2 class="text-lg font-bold text-slate-900 mt-5 mb-2 border-b pb-1">$1</h2>')
    .replace(/^# (.+)$/gm, '<h1 class="text-xl font-bold text-slate-900 mt-4 mb-3">$1</h1>')
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/^- (.+)$/gm, '<li class="ml-4 list-disc text-sm text-slate-700">$1</li>')
    .replace(/<!-- sep -->/g, '')
    .replace(/(<tr>.*<\/tr>)/gs, '<table class="w-full border-collapse my-2">$1</table>')
    .replace(/^(?!<[ht1-6lr]|<pre|<li|<table|<strong)(\S.+)$/gm, '<p class="text-sm text-slate-700 my-1">$1</p>');
  html = html.replace(/<\/table>\s*<table[^>]*>/g, '');
  return html;
}

const EMPTY_FORM = {
  source_type: 'manual', source_id: '', idea_id: '', title: '', description: '',
};

export default function DevStudioDetail() {
  const { devTaskId } = useParams();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const isNew = !devTaskId || devTaskId === 'new';

  const [form, setForm] = useState(() => {
    if (isNew) {
      return {
        source_type: searchParams.get('source_type') || 'manual',
        source_id: searchParams.get('source_id') || '',
        idea_id: searchParams.get('idea_id') || '',
        title: searchParams.get('title') || '',
        description: searchParams.get('description') || '',
      };
    }
    return EMPTY_FORM;
  });
  const [task, setTask] = useState(null);
  const [artifacts, setArtifacts] = useState([]);
  const [runs, setRuns] = useState([]);
  const [loading, setLoading] = useState(false);
  const [generating, setGenerating] = useState({});
  const [selectedArtifact, setSelectedArtifact] = useState(null);
  const [editMode, setEditMode] = useState(false);
  const [editContent, setEditContent] = useState('');
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [tab, setTab] = useState('artifacts');
  const [batchGenerating, setBatchGenerating] = useState(false);
  const [batchResult, setBatchResult] = useState(null);
  const [packages, setPackages] = useState([]);
  const [selectedPackage, setSelectedPackage] = useState(null);
  const [packageDetail, setPackageDetail] = useState(null);
  const [codeMapSnapshot, setCodeMapSnapshot] = useState(null);
  const [codeMapFiles, setCodeMapFiles] = useState([]);
  const [scanning, setScanning] = useState(false);
  const [generatingV2, setGeneratingV2] = useState(false);
  const [fileImpactV2Result, setFileImpactV2Result] = useState(null);
  const [generatingPatch, setGeneratingPatch] = useState(false);
  const [reviewing, setReviewing] = useState(false);

  // ── 加载详情 ─────────────────────────────────────────────
  const fetchDetail = async (taskId) => {
    setLoading(true);
    try {
      const res = await fetch(`/api/v2/dev-studio/tasks/${taskId}`);
      if (!res.ok) throw new Error('加载失败');
      const data = await res.json();
      setTask(data);
      setArtifacts(data.artifacts || []);
      setRuns(data.runs || []);
      if (data.artifacts?.length > 0 && !selectedArtifact) {
        loadArtifact(data.artifacts[0].dev_artifact_id);
      }
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!isNew) {
      fetchDetail(devTaskId);
      fetchPackages(devTaskId);
      fetchLatestSnapshot();
    }
  }, [devTaskId]);

  // ── 创建任务 ─────────────────────────────────────────────
  const handleCreate = async (e) => {
    e.preventDefault();
    if (!form.title.trim()) { setError('请输入任务标题'); return; }
    setLoading(true);
    try {
      const res = await fetch('/api/v2/dev-studio/tasks', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(form),
      });
      if (!res.ok) { const d = await res.json(); throw new Error(d.detail || '创建失败'); }
      const data = await res.json();
      navigate(`/dev-studio/${data.dev_task_id}`, { replace: true });
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  // ── 加载 Artifact ─────────────────────────────────────────
  const loadArtifact = async (artId) => {
    try {
      const res = await fetch(`/api/v2/dev-studio/artifacts/${artId}`);
      if (!res.ok) return;
      const data = await res.json();
      setSelectedArtifact(data);
      setEditMode(false);
    } catch (e) {
      console.error(e);
    }
  };

  // ── 生成 ─────────────────────────────────────────────────
  const handleGenerate = async (runType) => {
    setGenerating(prev => ({ ...prev, [runType]: true }));
    try {
      const endpoint = GENERATE_ENDPOINTS[runType];
      const res = await fetch(`/api/v2/dev-studio/tasks/${devTaskId}/${endpoint}`, { method: 'POST' });
      if (!res.ok) { const d = await res.json().catch(() => ({})); throw new Error(d.detail || '生成失败'); }
      const data = await res.json();
      if (data.dev_artifact_id) {
        await fetchDetail(devTaskId);
        loadArtifact(data.dev_artifact_id);
      } else if (data.status === 'failed') {
        setError(`生成失败: ${data.error_message || 'LLM 调用失败'}`);
        await fetchDetail(devTaskId);
      }
    } catch (e) {
      setError(e.message);
    } finally {
      setGenerating(prev => ({ ...prev, [runType]: false }));
    }
  };

  // ── 批量生成 ──────────────────────────────────────────────
  const handleBatchGenerate = async () => {
    const ok = window.confirm(
      '将依次生成开发计划、API 设计、数据库设计、影响文件分析、测试计划。\n每类都会生成新的产物记录，是否继续？'
    );
    if (!ok) return;
    setBatchGenerating(true);
    setBatchResult(null);
    try {
      const res = await fetch(`/api/v2/dev-studio/tasks/${devTaskId}/generate-all`, { method: 'POST' });
      if (!res.ok) { const d = await res.json().catch(() => ({})); throw new Error(d.detail || '批量生成失败'); }
      const data = await res.json();
      setBatchResult(data);
      await fetchDetail(devTaskId);
      await fetchPackages(devTaskId);
      if (data.results) {
        const first = data.results.find(r => r.status === 'succeeded' && r.dev_artifact_id);
        if (first) loadArtifact(first.dev_artifact_id);
      }
    } catch (e) {
      setError(e.message);
    } finally {
      setBatchGenerating(false);
    }
  };

  // ── CodeMap 扫描 ────────────────────────────────────────────
  const handleScanProject = async () => {
    setScanning(true);
    try {
      const res = await fetch('/api/v2/dev-studio/code-map/scan', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ dev_task_id: devTaskId }),
      });
      if (!res.ok) throw new Error('扫描失败');
      const data = await res.json();
      setCodeMapSnapshot(data);
      // 加载文件列表
      const fRes = await fetch(`/api/v2/dev-studio/code-map/snapshots/${data.snapshot_id}/files`);
      if (fRes.ok) setCodeMapFiles((await fRes.json()).files || []);
    } catch (e) { setError(e.message); }
    finally { setScanning(false); }
  };

  const handleGenerateFileImpactV2 = async () => {
    if (!codeMapSnapshot?.snapshot_id) { setError('请先扫描代码结构'); return; }
    setGeneratingV2(true);
    setFileImpactV2Result(null);
    try {
      const res = await fetch(`/api/v2/dev-studio/code-map/tasks/${devTaskId}/file-impact-v2`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ snapshot_id: codeMapSnapshot.snapshot_id }),
      });
      if (!res.ok) { const d = await res.json().catch(() => ({})); throw new Error(d.detail || '生成失败'); }
      const data = await res.json();
      setFileImpactV2Result(data);
      if (data.dev_artifact_id) {
        await fetchDetail(devTaskId);
        loadArtifact(data.dev_artifact_id);
      }
    } catch (e) { setError(e.message); }
    finally { setGeneratingV2(false); }
  };

  const handleGeneratePatchDraft = async () => {
    setGeneratingPatch(true);
    try {
      const body = {};
      if (codeMapSnapshot?.snapshot_id) body.snapshot_id = codeMapSnapshot.snapshot_id;
      const res = await fetch(`/api/v2/dev-studio/tasks/${devTaskId}/generate-patch-draft`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body),
      });
      if (!res.ok) { const d = await res.json().catch(() => ({})); throw new Error(d.detail || '生成失败'); }
      const data = await res.json();
      if (data.dev_artifact_id) { await fetchDetail(devTaskId); loadArtifact(data.dev_artifact_id); }
      else if (data.status === 'failed') setError(`补丁草稿生成失败: ${data.error_message || 'LLM 错误'}`);
    } catch (e) { setError(e.message); }
    finally { setGeneratingPatch(false); }
  };

  const handleReviewPatchDraft = async (artifactId) => {
    setReviewing(true);
    try {
      const res = await fetch(`/api/v2/dev-studio/artifacts/${artifactId}/review-patch-draft`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({}),
      });
      if (!res.ok) { const d = await res.json().catch(() => ({})); throw new Error(d.detail || '评审失败'); }
      const data = await res.json();
      if (data.dev_artifact_id) { await fetchDetail(devTaskId); loadArtifact(data.dev_artifact_id); }
      else if (data.status === 'failed') setError(`补丁评审失败: ${data.error_message || 'LLM 错误'}`);
    } catch (e) { setError(e.message); }
    finally { setReviewing(false); }
  };

  const fetchLatestSnapshot = async () => {
    try {
      const res = await fetch(`/api/v2/dev-studio/code-map/snapshots?dev_task_id=${devTaskId}`);
      if (res.ok) {
        const snaps = (await res.json()).snapshots || [];
        if (snaps.length > 0) {
          setCodeMapSnapshot(snaps[0]);
          const fRes = await fetch(`/api/v2/dev-studio/code-map/snapshots/${snaps[0].snapshot_id}/files`);
          if (fRes.ok) setCodeMapFiles((await fRes.json()).files || []);
        }
      }
    } catch (e) { console.error(e); }
  };

  // ── 开发包查询 ──────────────────────────────────────────────
  const fetchPackages = async (taskId) => {
    try {
      const res = await fetch(`/api/v2/dev-studio/tasks/${taskId}/packages`);
      if (res.ok) setPackages((await res.json()).packages || []);
    } catch (e) { console.error(e); }
  };

  const loadPackageDetail = async (batchId) => {
    setSelectedPackage(batchId);
    try {
      const res = await fetch(`/api/v2/dev-studio/tasks/${devTaskId}/packages/${batchId}`);
      if (res.ok) setPackageDetail(await res.json());
    } catch (e) { console.error(e); }
  };

  // ── 保存编辑 ────────────────────────────────────────────────
  const handleSave = async () => {
    if (!selectedArtifact) return;
    setSaving(true);
    try {
      const res = await fetch(`/api/v2/dev-studio/artifacts/${selectedArtifact.dev_artifact_id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content_markdown: editContent }),
      });
      if (!res.ok) throw new Error('保存失败');
      const data = await res.json();
      setSelectedArtifact(data);
      setEditMode(false);
    } catch (e) {
      setError(e.message);
    } finally {
      setSaving(false);
    }
  };

  // ── 导出 ──────────────────────────────────────────────────
  const handleExport = async () => {
    if (!selectedArtifact) return;
    try {
      const res = await fetch(`/api/v2/dev-studio/artifacts/${selectedArtifact.dev_artifact_id}/export`, { method: 'POST' });
      if (!res.ok) throw new Error('导出失败');
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${selectedArtifact.artifact_type}_${selectedArtifact.dev_artifact_id}.md`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (e) {
      setError(e.message);
    }
  };

  // ── 新建表单 ──────────────────────────────────────────────
  if (isNew) {
    return (
      <div className="p-6 max-w-3xl mx-auto">
        <h1 className="text-2xl font-bold text-slate-900 mb-6">新建开发任务</h1>
        {error && <div className="mb-4 p-3 bg-red-50 text-red-700 rounded-lg text-sm">{error}</div>}
        <form onSubmit={handleCreate} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">任务标题 *</label>
            <input type="text" value={form.title} onChange={e => setForm({ ...form, title: e.target.value })}
              className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm" placeholder="例如：用户管理模块开发计划" />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">来源类型</label>
            <select value={form.source_type} onChange={e => setForm({ ...form, source_type: e.target.value })}
              className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm">
              <option value="manual">手动创建</option>
              <option value="product_artifact">产品产物</option>
              <option value="test_case">测试用例</option>
            </select>
          </div>
          {form.source_type !== 'manual' && (
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">来源 ID</label>
              <input type="text" value={form.source_id} onChange={e => setForm({ ...form, source_id: e.target.value })}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm" placeholder="artifact_id 或 test_case id" />
            </div>
          )}
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">需求描述</label>
            <textarea value={form.description} onChange={e => setForm({ ...form, description: e.target.value })}
              className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm h-32" placeholder="描述需求背景、目标、约束..." />
          </div>
          <button type="submit" disabled={loading}
            className="px-6 py-2 bg-indigo-600 text-white rounded-lg text-sm hover:bg-indigo-700 disabled:opacity-50">
            {loading ? '创建中...' : '创建开发任务'}
          </button>
        </form>
      </div>
    );
  }

  // ── 详情页 ────────────────────────────────────────────────
  if (loading && !task) return <div className="p-12 text-center text-slate-400">加载中...</div>;
  if (!task) return <div className="p-12 text-center text-slate-400">任务不存在</div>;

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {error && <div className="mb-4 p-3 bg-red-50 text-red-700 rounded-lg text-sm cursor-pointer" onClick={() => setError('')}>{error} ✕</div>}

      {/* 标题区 */}
      <div className="mb-6">
        <div className="flex items-center gap-3 mb-2">
          <button onClick={() => navigate('/dev-studio')} className="text-slate-400 hover:text-slate-600">← 返回</button>
          <h1 className="text-xl font-bold text-slate-900">{task.title}</h1>
          <span className="text-xs px-2 py-0.5 rounded bg-slate-100 text-slate-600">{SOURCE_LABELS[task.source_type] || task.source_type}</span>
          <span className="text-xs px-2 py-0.5 rounded bg-blue-100 text-blue-700">{task.status}</span>
        </div>
        {task.description && <p className="text-sm text-slate-500 mb-2">{task.description}</p>}
        {task.source_summary && (
          <details className="text-xs text-slate-400 mt-1">
            <summary className="cursor-pointer hover:text-slate-600">来源摘要</summary>
            <pre className="mt-1 p-2 bg-slate-50 rounded text-xs whitespace-pre-wrap max-h-40 overflow-auto">{task.source_summary}</pre>
          </details>
        )}
      </div>

      {/* 生成按钮组 */}
      <div className="flex flex-wrap gap-2 mb-4">
        {Object.entries(GENERATE_ENDPOINTS).map(([runType, endpoint]) => (
          <button
            key={runType}
            onClick={() => handleGenerate(runType)}
            disabled={generating[runType] || batchGenerating}
            className={`px-4 py-2 text-white rounded-lg text-sm disabled:opacity-50 ${GENERATE_COLORS[runType]}`}
          >
            {generating[runType] ? '生成中...' : `生成${TYPE_LABELS[runType]}`}
          </button>
        ))}
        <button
          onClick={handleBatchGenerate}
          disabled={batchGenerating || Object.values(generating).some(Boolean)}
          className="px-4 py-2 text-white rounded-lg text-sm disabled:opacity-50 bg-indigo-600 hover:bg-indigo-700 border-2 border-indigo-400"
        >
          {batchGenerating ? '批量生成中...' : '✨ 批量生成全部'}
        </button>
        <span className="border-l border-slate-300 mx-1"></span>
        <button onClick={handleScanProject} disabled={scanning}
          className="px-4 py-2 text-white rounded-lg text-sm disabled:opacity-50 bg-teal-600 hover:bg-teal-700">
          {scanning ? '扫描中...' : '📂 扫描代码结构'}
        </button>
        <button onClick={handleGenerateFileImpactV2} disabled={generatingV2 || !codeMapSnapshot}
          className="px-4 py-2 text-white rounded-lg text-sm disabled:opacity-50 bg-amber-600 hover:bg-amber-700"
          title={codeMapSnapshot ? `基于 ${codeMapSnapshot.total_files} 个文件的代码结构` : '请先扫描代码结构'}>
          {generatingV2 ? '分析中...' : '🔍 增强影响分析'}
        </button>
        <button onClick={handleGeneratePatchDraft} disabled={generatingPatch}
          className="px-4 py-2 text-white rounded-lg text-sm disabled:opacity-50 bg-rose-600 hover:bg-rose-700"
          title="基于影响文件分析生成补丁草稿（不会自动修改代码）">
          {generatingPatch ? '生成中...' : '📝 补丁草稿'}
        </button>
      </div>

      {/* 批量生成结果 */}
      {batchResult && (
        <div className="mb-6 p-4 rounded-lg border border-indigo-200 bg-indigo-50">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-semibold text-indigo-900">
              批量生成结果：成功 {batchResult.succeeded_count}/{batchResult.total}
              {batchResult.failed_count > 0 && <span className="text-red-600 ml-2">失败 {batchResult.failed_count}</span>}
            </h3>
            <button onClick={() => setBatchResult(null)} className="text-xs text-slate-400 hover:text-slate-600">✕</button>
          </div>
          <div className="grid grid-cols-5 gap-2">
            {batchResult.results?.map(r => (
              <div key={r.artifact_type}
                className={`p-2 rounded text-xs text-center ${r.status === 'succeeded' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
                <div className="font-medium">{TYPE_LABELS[r.artifact_type] || r.artifact_type}</div>
                <div>{r.status === 'succeeded' ? '✅ 成功' : '❌ 失败'}</div>
                {r.error_message && <div className="mt-1 text-[10px] text-red-600 truncate" title={r.error_message}>{r.error_message}</div>}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Tab 切换 */}
      <div className="flex gap-4 mb-4 border-b border-slate-200">
        <button onClick={() => setTab('artifacts')}
          className={`pb-2 text-sm font-medium ${tab === 'artifacts' ? 'text-blue-600 border-b-2 border-blue-600' : 'text-slate-500'}`}>
          产物 ({artifacts.length})
        </button>
        <button onClick={() => setTab('packages')}
          className={`pb-2 text-sm font-medium ${tab === 'packages' ? 'text-indigo-600 border-b-2 border-indigo-600' : 'text-slate-500'}`}>
          开发包 ({packages.length})
        </button>
        <button onClick={() => setTab('runs')}
          className={`pb-2 text-sm font-medium ${tab === 'runs' ? 'text-blue-600 border-b-2 border-blue-600' : 'text-slate-500'}`}>
          执行记录 ({runs.length})
        </button>
        <button onClick={() => setTab('codemap')}
          className={`pb-2 text-sm font-medium ${tab === 'codemap' ? 'text-teal-600 border-b-2 border-teal-600' : 'text-slate-500'}`}>
          代码结构 {codeMapSnapshot ? `(${codeMapSnapshot.total_files})` : ''}
        </button>
      </div>

      <div className="grid grid-cols-12 gap-6">
        {/* 左侧列表 */}
        <div className="col-span-4">
          {tab === 'artifacts' ? (
            <div className="space-y-2">
              {artifacts.length === 0 ? (
                <p className="text-sm text-slate-400 py-4 text-center">暂无产物，请点击上方按钮生成</p>
              ) : artifacts.map(a => (
                <div
                  key={a.dev_artifact_id}
                  onClick={() => loadArtifact(a.dev_artifact_id)}
                  className={`p-3 rounded-lg border cursor-pointer transition-colors ${
                    selectedArtifact?.dev_artifact_id === a.dev_artifact_id
                      ? 'border-blue-500 bg-blue-50'
                      : 'border-slate-200 hover:bg-slate-50'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium text-slate-800">{TYPE_LABELS[a.artifact_type] || a.artifact_type}</span>
                    <span className="text-xs text-slate-400">{STATUS_LABELS[a.status] || a.status}</span>
                  </div>
                  <p className="text-xs text-slate-500 mt-1 truncate">{a.title}</p>
                  <div className="flex items-center gap-2 mt-0.5">
                    <span className="text-xs text-slate-400">{a.created_at?.slice(0, 16).replace('T', ' ')}</span>
                    {a.batch_id && <span className="text-[10px] px-1.5 py-0.5 rounded bg-indigo-50 text-indigo-600 font-mono">{a.batch_id.slice(0, 16)}</span>}
                  </div>
                </div>
              ))}
            </div>
          ) : tab === 'packages' ? (
            <div className="space-y-2">
              <p className="text-[10px] text-amber-600 bg-amber-50 p-2 rounded mb-2">开发包为 AI 生成的研发设计产物，需人工确认</p>
              {packages.length === 0 ? (
                <p className="text-sm text-slate-400 py-4 text-center">暂无开发包，请使用“批量生成全部”创建</p>
              ) : packages.map(pkg => (
                <div key={pkg.batch_id}
                  onClick={() => loadPackageDetail(pkg.batch_id)}
                  className={`p-3 rounded-lg border cursor-pointer transition-colors ${
                    selectedPackage === pkg.batch_id ? 'border-indigo-500 bg-indigo-50' : 'border-slate-200 hover:bg-slate-50'
                  }`}>
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-xs font-mono text-indigo-700">{pkg.batch_id}</span>
                    <span className="text-xs text-slate-400">{pkg.artifact_count} 产物</span>
                  </div>
                  <div className="flex gap-1 flex-wrap mb-1">
                    {pkg.artifact_types?.map(t => (
                      <span key={t} className="text-[10px] px-1.5 py-0.5 rounded bg-slate-100 text-slate-600">{TYPE_LABELS[t] || t}</span>
                    ))}
                  </div>
                  <div className="flex items-center gap-2 text-xs">
                    <span className="text-green-600">✅ {pkg.succeeded_count}</span>
                    {pkg.failed_count > 0 && <span className="text-red-600">❌ {pkg.failed_count}</span>}
                    <span className="text-slate-400 ml-auto">{pkg.created_at?.slice(0, 16).replace('T', ' ')}</span>
                  </div>
                </div>
              ))}
            </div>
          ) : tab === 'codemap' ? (
            <div className="space-y-2">
              {!codeMapSnapshot ? (
                <div className="text-center py-6">
                  <p className="text-sm text-slate-400 mb-3">未扫描代码结构</p>
                  <button onClick={handleScanProject} disabled={scanning}
                    className="px-4 py-2 bg-teal-600 text-white rounded text-sm hover:bg-teal-700 disabled:opacity-50">
                    {scanning ? '扫描中...' : '📂 开始扫描'}
                  </button>
                </div>
              ) : (
                <>
                  <div className="p-3 rounded-lg border border-teal-200 bg-teal-50 text-xs">
                    <div className="flex justify-between mb-1">
                      <span className="font-medium text-teal-800">扫描结果</span>
                      <span className="text-teal-600">{codeMapSnapshot.scan_duration_ms}ms</span>
                    </div>
                    <p className="text-teal-700">总文件: {codeMapSnapshot.total_files} | 目录: {codeMapSnapshot.total_dirs || '-'}</p>
                    <p className="text-teal-700">后端: {codeMapSnapshot.backend_files} | 前端: {codeMapSnapshot.frontend_files}</p>
                    <p className="text-teal-600 text-[10px] mt-1 font-mono">{codeMapSnapshot.snapshot_id}</p>
                  </div>
                  {(() => {
                    const cats = {};
                    codeMapFiles.forEach(f => { cats[f.category] = (cats[f.category] || 0) + 1; });
                    return Object.entries(cats).sort((a,b) => b[1]-a[1]).map(([cat, cnt]) => (
                      <div key={cat} className="p-2 rounded border border-slate-200 text-xs flex justify-between items-center">
                        <span className="font-medium text-slate-700">{cat}</span>
                        <span className="text-slate-400">{cnt} 文件</span>
                      </div>
                    ));
                  })()}
                  <button onClick={handleScanProject} disabled={scanning}
                    className="w-full py-1.5 text-xs text-teal-600 border border-teal-200 rounded hover:bg-teal-50 disabled:opacity-50">
                    {scanning ? '重新扫描中...' : '🔄 重新扫描'}
                  </button>
                </>
              )}
            </div>
          ) : (
            <div className="space-y-2">
              {runs.length === 0 ? (
                <p className="text-sm text-slate-400 py-4 text-center">暂无执行记录</p>
              ) : runs.map(r => (
                <div key={r.run_id} className="p-3 rounded-lg border border-slate-200 text-xs">
                  <div className="flex items-center justify-between mb-1">
                    <span className="font-medium text-slate-700">{TYPE_LABELS[r.run_type] || r.run_type}</span>
                    <span className={`px-1.5 py-0.5 rounded ${r.status === 'succeeded' ? 'bg-green-100 text-green-700' : r.status === 'failed' ? 'bg-red-100 text-red-700' : 'bg-amber-100 text-amber-700'}`}>
                      {STATUS_LABELS[r.status] || r.status}
                    </span>
                  </div>
                  <p className="text-slate-500">运行: {r.run_id}</p>
                  <p className="text-slate-500">追踪: {r.trace_id}</p>
                  <p className="text-slate-500">模型: {r.model_name || '-'}</p>
                  {r.error_message && <p className="text-red-500 mt-1">{r.error_message}</p>}
                  <p className="text-slate-400 mt-1">{r.created_at?.slice(0, 19).replace('T', ' ')}</p>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* 右侧内容 */}
        <div className="col-span-8">
          {tab === 'packages' && packageDetail ? (
            <div className="bg-white border border-indigo-200 rounded-lg p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-base font-semibold text-indigo-900">开发包: <span className="font-mono text-sm">{packageDetail.batch_id}</span></h2>
                <button onClick={() => { setPackageDetail(null); setSelectedPackage(null); }}
                  className="text-xs text-slate-400 hover:text-slate-600">✕</button>
              </div>
              <p className="text-[10px] text-amber-600 bg-amber-50 p-2 rounded mb-3">开发包为 AI 生成的研发设计产物，需人工确认</p>
              <div className="space-y-2">
                {packageDetail.artifacts?.map(a => (
                  <div key={a.dev_artifact_id}
                    onClick={() => { loadArtifact(a.dev_artifact_id); setTab('artifacts'); }}
                    className="p-3 rounded border border-slate-200 hover:bg-blue-50 cursor-pointer flex items-center justify-between">
                    <div>
                      <span className="text-sm font-medium text-slate-800">{TYPE_LABELS[a.artifact_type] || a.artifact_type}</span>
                      <span className="text-xs text-slate-400 ml-2">#{a.batch_index}</span>
                      <p className="text-xs text-slate-500 mt-0.5 truncate">{a.title}</p>
                      {a.reference_artifact_ids && (
                        <p className="text-[10px] text-indigo-500 mt-0.5">引用: {a.reference_artifact_ids.length} 个产物</p>
                      )}
                    </div>
                    <span className="text-xs text-slate-400">{STATUS_LABELS[a.status] || a.status}</span>
                  </div>
                ))}
              </div>
              {packageDetail.runs?.length > 0 && (
                <details className="mt-4">
                  <summary className="text-xs text-slate-500 cursor-pointer">执行记录 ({packageDetail.runs.length})</summary>
                  <div className="mt-2 space-y-1">
                    {packageDetail.runs.map(r => (
                      <div key={r.run_id} className="text-xs p-2 bg-slate-50 rounded flex justify-between">
                        <span>{TYPE_LABELS[r.run_type] || r.run_type}</span>
                        <span className={r.status === 'succeeded' ? 'text-green-600' : 'text-red-600'}>{STATUS_LABELS[r.status] || r.status}</span>
                      </div>
                    ))}
                  </div>
                </details>
              )}
            </div>
          ) : selectedArtifact ? (
            <div className="bg-white border border-slate-200 rounded-lg p-6">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h2 className="text-lg font-semibold text-slate-800">{selectedArtifact.title || TYPE_LABELS[selectedArtifact.artifact_type]}</h2>
                  {selectedArtifact.batch_id && (
                    <span className="text-[10px] px-1.5 py-0.5 rounded bg-indigo-50 text-indigo-600 font-mono">开发包: {selectedArtifact.batch_id.slice(0, 16)}</span>
                  )}
                </div>
                <div className="flex gap-2">
                  {editMode ? (
                    <>
                      <button onClick={handleSave} disabled={saving}
                        className="px-3 py-1 bg-green-600 text-white rounded text-xs hover:bg-green-700 disabled:opacity-50">
                        {saving ? '保存中...' : '保存'}
                      </button>
                      <button onClick={() => setEditMode(false)}
                        className="px-3 py-1 bg-slate-200 text-slate-700 rounded text-xs hover:bg-slate-300">取消</button>
                    </>
                  ) : (
                    <>
                      <button onClick={() => { setEditContent(selectedArtifact.content_markdown || ''); setEditMode(true); }}
                        className="px-3 py-1 bg-slate-200 text-slate-700 rounded text-xs hover:bg-slate-300">编辑</button>
                      <button onClick={handleExport}
                        className="px-3 py-1 bg-slate-200 text-slate-700 rounded text-xs hover:bg-slate-300">导出</button>
                      {selectedArtifact.artifact_type === 'patch_draft' && (
                        <button onClick={() => handleReviewPatchDraft(selectedArtifact.dev_artifact_id)} disabled={reviewing}
                          className="px-3 py-1 bg-violet-600 text-white rounded text-xs hover:bg-violet-700 disabled:opacity-50"
                          title="AI 评审补丁草稿（不会自动应用）">
                          {reviewing ? '评审中...' : '🔍 评审补丁'}
                        </button>
                      )}
                    </>
                  )}
                </div>
              </div>
              {editMode ? (
                <textarea value={editContent} onChange={e => setEditContent(e.target.value)}
                  className="w-full h-[60vh] p-4 border border-slate-200 rounded text-sm font-mono" />
              ) : (
                <div className="prose max-w-none"
                  dangerouslySetInnerHTML={{ __html: renderMarkdown(selectedArtifact.content_markdown) }} />
              )}
            </div>
          ) : (
            <div className="flex items-center justify-center h-64 text-slate-400">
              <p>选择左侧产物查看内容，或点击按钮生成新产物</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
