import { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Card, Upload, Button, Space, Table, Tag, message, Spin, Alert, Descriptions, Collapse, Select, InputNumber, Input, Progress, Tabs, Empty, Divider } from 'antd';
import { UploadOutlined, FileTextOutlined, FolderOpenOutlined, CheckCircleOutlined, ExperimentOutlined, DownloadOutlined } from '@ant-design/icons';

const { Dragger } = Upload;
const { TextArea } = Input;

const ACCEPT = '.html,.htm,.txt,.md,.docx,.doc,.pdf';

export default function RequirementUpload() {
  const navigate = useNavigate();
  // 状态
  const [step, setStep] = useState('upload'); // upload | preview | generating | result
  const [uploading, setUploading] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [fileInfo, setFileInfo] = useState(null);
  const [preview, setPreview] = useState(null);
  const [testcases, setTestcases] = useState([]);
  const [coverage, setCoverage] = useState(null);
  const [config, setConfig] = useState({ module: '默认模块', count: 100, provider: null, model: null, extra: '' });
  const [uploadedFile, setUploadedFile] = useState(null);
  const [folderPath, setFolderPath] = useState('');
  const [sourceType, setSourceType] = useState(null); // 'file' | 'folder'
  const [genProgress, setGenProgress] = useState(0);
  const [genStep, setGenStep] = useState('');
  const [aiProviders, setAiProviders] = useState([]);
  const [aiConfig, setAiConfig] = useState(null);

  // 加载 AI 提供商和模型列表
  useEffect(() => {
    fetch('/api/ai/providers').then(r => r.json()).then(data => {
      setAiProviders(data.providers || []);
    }).catch(() => {});
    fetch('/api/ai/config').then(r => r.json()).then(data => {
      setAiConfig(data);
      setConfig(prev => ({
        ...prev,
        provider: data.default_provider,
        model: data.default_model,
      }));
    }).catch(() => {});
  }, []);

  // 当提供商变化时，重置模型为该提供商的第一个模型
  const handleProviderChange = (providerId) => {
    const provider = aiProviders.find(p => p.id === providerId);
    const firstModel = provider?.models?.[0] || null;
    setConfig(prev => ({ ...prev, provider: providerId, model: firstModel }));
  };

  const currentModels = aiProviders.find(p => p.id === config.provider)?.models || [];

  // 上传文件并预览
  const handleUpload = async (file) => {
    setUploading(true);
    try {
      const formData = new FormData();
      formData.append('file', file);

      const resp = await fetch('/api/ai/upload-preview', { method: 'POST', body: formData });
      const data = await resp.json();

      if (!resp.ok) {
        message.error(data.detail || '上传失败');
        return false;
      }

      setFileInfo({ name: file.name, size: file.size });
      setPreview(data);
      setUploadedFile(file);
      setSourceType('file');
      setStep('preview');
      message.success(`文档解析成功: ${data.structured.stats.modules || 0} 个模块, ${data.structured.stats.features || 0} 个功能点`);
    } catch (e) {
      message.error('上传失败: ' + e.message);
    } finally {
      setUploading(false);
    }
    return false;
  };

  // 解析 Axure 文件夹并预览
  const handleFolderPreview = async () => {
    if (!folderPath.trim()) {
      message.error('请输入文件夹路径');
      return;
    }
    setUploading(true);
    try {
      const resp = await fetch('/api/ai/folder-preview', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ folder_path: folderPath.trim() }),
      });
      const data = await resp.json();

      if (!resp.ok) {
        message.error(data.detail || '文件夹解析失败');
        return;
      }

      const stats = data.structured.stats;
      setFileInfo({ name: data.filename, size: null });
      setPreview(data);
      setSourceType('folder');
      setStep('preview');
      message.success(`Axure 文件夹解析成功: ${stats.annotations_total || stats.axure_notes || 0} 条注释, ${stats.features || 0} 个功能点`);
    } catch (e) {
      message.error('文件夹解析失败: ' + e.message);
    } finally {
      setUploading(false);
    }
  };

  // 确认生成用例
  const handleGenerate = async () => {
    if (sourceType === 'file' && !uploadedFile) {
      message.error('请先上传文件');
      return;
    }
    if (sourceType === 'folder' && !folderPath.trim()) {
      message.error('请先输入文件夹路径');
      return;
    }
    setGenerating(true);
    setStep('generating');
    setGenProgress(0);
    setGenStep('准备解析文档...');

    // 进度模拟
    const steps = [
      [500, 5, '📚 加载项目知识库...'],
      [2000, 15, sourceType === 'folder' ? '📂 解析 Axure 原型注释...' : '📄 解析需求文档...'],
      [5000, 30, '🔍 拆分功能模块与业务规则...'],
      [12000, 50, '🎯 AI 正在生成测试场景...'],
      [22000, 70, '✨ AI 正在编写测试用例...'],
      [35000, 85, '📝 整理输出结果...'],
    ];
    const timers = steps.map(([delay, pct, txt]) =>
      setTimeout(() => { setGenProgress(pct); setGenStep(txt); }, delay)
    );
    const progressInterval = setInterval(() => {
      setGenProgress(prev => prev >= 90 ? prev : prev + 1);
    }, 2000);

    try {
      let resp;
      if (sourceType === 'folder') {
        resp = await fetch('/api/ai/generate-testcases-from-folder', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            folder_path: folderPath.trim(),
            module: config.module,
            count: config.count,
            provider: config.provider,
            model: config.model || undefined,
            extra_requirements: config.extra || undefined,
          }),
        });
      } else {
        const formData = new FormData();
        formData.append('file', uploadedFile);
        formData.append('module', config.module);
        formData.append('count', String(config.count));
        if (config.provider) formData.append('provider', config.provider);
        if (config.model) formData.append('model', config.model);
        if (config.extra) formData.append('extra_requirements', config.extra);
        resp = await fetch('/api/ai/generate-testcases-from-file', { method: 'POST', body: formData });
      }

      const data = await resp.json();

      if (!resp.ok) {
        message.error(data.detail || '生成失败');
        setStep('preview');
        return;
      }

      if (data.success) {
        setGenProgress(100);
        setGenStep('✅ 生成完成!');
        setTestcases(data.testcases || []);
        setCoverage(data.coverage);
        setTimeout(() => setStep('result'), 500);
        message.success(`生成完成: ${data.count} 个测试用例，已保存到数据库`);
      } else {
        message.error(data.error || '生成失败');
        setStep('preview');
      }
    } catch (e) {
      message.error('生成失败: ' + e.message);
      setStep('preview');
    } finally {
      timers.forEach(clearTimeout);
      clearInterval(progressInterval);
      setGenerating(false);
    }
  };

  // 重新开始
  const handleReset = () => {
    setStep('upload');
    setFileInfo(null);
    setPreview(null);
    setTestcases([]);
    setCoverage(null);
    setUploadedFile(null);
    setFolderPath('');
    setSourceType(null);
  };

  // 导出 JSON
  const handleExport = () => {
    const blob = new Blob([JSON.stringify(testcases, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `testcases_${fileInfo?.name || 'export'}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  // 用例表格列
  const columns = [
    { title: '序号', width: 60, render: (_, __, i) => i + 1 },
    { title: '标题', dataIndex: 'title', width: 250, ellipsis: true },
    { title: '模块', dataIndex: 'module', width: 120, ellipsis: true },
    { title: '测试点', dataIndex: 'test_point', width: 150, ellipsis: true },
    {
      title: '优先级', dataIndex: 'priority', width: 80,
      render: (v) => {
        const colors = { high: 'red', medium: 'orange', low: 'blue' };
        const labels = { high: '高', medium: '中', low: '低' };
        return <Tag color={colors[v] || 'default'}>{labels[v] || v}</Tag>;
      }
    },
    {
      title: '类型', dataIndex: 'type', width: 100,
      render: (v) => <Tag>{v}</Tag>
    },
    { title: '前置条件', dataIndex: 'precondition', width: 150, ellipsis: true },
    {
      title: '步骤数', width: 70,
      render: (_, r) => (r.steps || []).length
    },
    { title: '预期结果', dataIndex: 'expected', width: 200, ellipsis: true },
  ];

  return (
    <div style={{ padding: 24 }}>
      <Card
        title={
          <Space>
            <FileTextOutlined />
            <span>从需求文档生成测试用例</span>
          </Space>
        }
        extra={
          step !== 'upload' && (
            <Button onClick={handleReset}>重新上传</Button>
          )
        }
      >
        {/* ========== Step 1: 上传 ========== */}
        {step === 'upload' && (
          <div style={{ maxWidth: 600, margin: '0 auto' }}>
            <Alert
              message="支持格式"
              description="HTML (.html/.htm)、TXT、Markdown、Word (.docx)、PDF。也支持直接输入 Axure 导出的原型文件夹路径（_files 目录），自动提取 data.js 中的注释和控件标签。"
              type="info"
              showIcon
              style={{ marginBottom: 24 }}
            />
            <Dragger
              accept={ACCEPT}
              maxCount={1}
              showUploadList={false}
              beforeUpload={handleUpload}
              disabled={uploading}
            >
              <p style={{ fontSize: 48, color: '#1890ff' }}>
                {uploading ? <Spin size="large" /> : <UploadOutlined />}
              </p>
              <p style={{ fontSize: 16 }}>点击或拖拽需求文档到此区域</p>
              <p style={{ color: '#999' }}>
                支持 HTML / TXT / Markdown / Word / PDF
              </p>
            </Dragger>

            <Divider plain style={{ margin: '20px 0', color: '#aaa', fontSize: 13 }}>或输入 Axure 文件夹路径</Divider>

            <Space.Compact style={{ width: '100%' }}>
              <Input
                prefix={<FolderOpenOutlined />}
                placeholder="如: G:\需求\付款单-企业小程序_v1.2.3_files"
                value={folderPath}
                onChange={e => setFolderPath(e.target.value)}
                onPressEnter={handleFolderPreview}
                disabled={uploading}
                style={{ flex: 1 }}
              />
              <Button
                type="primary"
                onClick={handleFolderPreview}
                loading={uploading}
                disabled={!folderPath.trim()}
              >
                解析文件夹
              </Button>
            </Space.Compact>
            <p style={{ marginTop: 8, color: '#999', fontSize: 12 }}>
              输入本地 Axure 导出的 _files 文件夹绝对路径，点击解析按钮
            </p>
          </div>
        )}

        {/* ========== Step 2: 预览确认 ========== */}
        {step === 'preview' && preview && (
          <Space direction="vertical" style={{ width: '100%' }} size="large">
            <Alert
              message="文档解析完成，请确认提取结果"
              description="检查下方提取到的模块、功能点、业务规则是否完整，确认后点击生成。"
              type="success"
              showIcon
            />

            {/* 统计 */}
            <Descriptions title={`${sourceType === 'folder' ? '�' : '�'} ${fileInfo?.name}`} bordered size="small" column={4}>
              {fileInfo?.size != null && (
                <Descriptions.Item label="文件大小">{(fileInfo.size / 1024).toFixed(1)} KB</Descriptions.Item>
              )}
              <Descriptions.Item label="内容长度">{preview.raw_text_length} 字符</Descriptions.Item>
              {sourceType === 'folder' ? (
                <Descriptions.Item label="Axure 注释">
                  {(preview.structured.stats.annotations_total ?? preview.structured.stats.axure_notes) || 0} 条
                </Descriptions.Item>
              ) : (
                <Descriptions.Item label="文件类型">{preview.structured.stats.file_type}</Descriptions.Item>
              )}
              <Descriptions.Item label="功能点">{preview.structured.stats.features || 0} 个</Descriptions.Item>
            </Descriptions>

            {/* 分层结果 */}
            <Tabs items={[
              {
                key: 'modules',
                label: `模块 (${preview.structured.modules.length})`,
                children: preview.structured.modules.length > 0 ? (
                  <div>{preview.structured.modules.map((m, i) => (
                    <Tag key={i} color="blue" style={{ margin: 4 }}>
                      {'  '.repeat(m.level - 1)}{m.name}
                    </Tag>
                  ))}</div>
                ) : <Empty description="未识别到模块（可在下方手动补充）" />
              },
              {
                key: 'features',
                label: `功能点 (${preview.structured.features.length})`,
                children: preview.structured.features.length > 0 ? (
                  <div>{preview.structured.features.map((f, i) => (
                    <Tag key={i} style={{ margin: 4 }}>{f.name}</Tag>
                  ))}</div>
                ) : <Empty description="未识别到功能点" />
              },
              {
                key: 'rules',
                label: `业务规则 (${preview.structured.rules.length})`,
                children: preview.structured.rules.length > 0 ? (
                  <ul style={{ paddingLeft: 20 }}>
                    {preview.structured.rules.map((r, i) => <li key={i} style={{ marginBottom: 4 }}>{r}</li>)}
                  </ul>
                ) : <Empty description="未识别到业务规则" />
              },
              {
                key: 'fields',
                label: `表单字段 (${preview.structured.fields.length})`,
                children: preview.structured.fields.length > 0 ? (
                  <div>{preview.structured.fields.map((f, i) => (
                    <Tag key={i} color={f.required ? 'red' : 'default'} style={{ margin: 4 }}>
                      {f.name} ({f.type}){f.required ? ' *' : ''}
                    </Tag>
                  ))}</div>
                ) : <Empty description="未识别到表单字段" />
              },
              ...(preview.structured.axure_notes.length > 0 ? [{
                key: 'axure',
                label: `Axure 注释 (${preview.structured.axure_notes.length})`,
                children: (
                  <ul style={{ paddingLeft: 20 }}>
                    {preview.structured.axure_notes.map((n, i) => <li key={i} style={{ marginBottom: 4 }}>{n}</li>)}
                  </ul>
                )
              }] : []),
              {
                key: 'raw',
                label: '原始文本',
                children: (
                  <pre style={{ maxHeight: 400, overflow: 'auto', background: '#f5f5f5', padding: 12, fontSize: 12, whiteSpace: 'pre-wrap' }}>
                    {preview.raw_text_preview}
                  </pre>
                )
              }
            ]} />

            {/* 生成配置 */}
            <Card title="⚙️ 生成配置" size="small" style={{ border: '1px solid #1890ff', borderRadius: 8 }}
              extra={<Link to="/ai-config" style={{ fontSize: 12 }}>高级配置 →</Link>}
            >
              <Space wrap size="middle">
                <div>
                  <div style={{ fontSize: 12, color: '#666', marginBottom: 4 }}>AI 提供商</div>
                  <Select
                    style={{ width: 180 }}
                    value={config.provider}
                    onChange={handleProviderChange}
                    placeholder="选择提供商"
                    options={aiProviders.filter(p => p.status === 'available').map(p => ({
                      label: `${p.name}${p.id === aiConfig?.default_provider ? ' (默认)' : ''}`,
                      value: p.id,
                    }))}
                  />
                </div>
                <div>
                  <div style={{ fontSize: 12, color: '#666', marginBottom: 4 }}>模型</div>
                  <Select
                    style={{ width: 220 }}
                    value={config.model}
                    onChange={v => setConfig(prev => ({ ...prev, model: v }))}
                    placeholder="选择模型"
                    options={currentModels.map(m => ({ label: m, value: m }))}
                  />
                </div>
                <div>
                  <div style={{ fontSize: 12, color: '#666', marginBottom: 4 }}>模块名称</div>
                  <Input
                    style={{ width: 160 }}
                    value={config.module}
                    onChange={e => setConfig({ ...config, module: e.target.value })}
                  />
                </div>
                <div>
                  <div style={{ fontSize: 12, color: '#666', marginBottom: 4 }}>用例数量</div>
                  <InputNumber
                    min={10} max={500} step={10}
                    value={config.count}
                    onChange={v => setConfig({ ...config, count: v })}
                    style={{ width: 100 }}
                  />
                </div>
              </Space>
              <div style={{ marginTop: 12 }}>
                <div style={{ fontSize: 12, color: '#666', marginBottom: 4 }}>额外测试要求（可选）</div>
                <TextArea
                  rows={2}
                  placeholder="例如: 重点测试权限控制、需要覆盖多语言场景..."
                  value={config.extra}
                  onChange={e => setConfig({ ...config, extra: e.target.value })}
                />
              </div>
              <div style={{ textAlign: 'center', marginTop: 16 }}>
                <Space size="middle">
                  <Button type="primary" size="large" icon={<ExperimentOutlined />} onClick={handleGenerate} style={{ minWidth: 200 }}>
                    🚀 确认生成测试用例
                  </Button>
                  <Button size="large" onClick={async () => {
                    try {
                      const structured = preview?.structured || preview || {};
                      const resp = await fetch('/api/v2/code-compare/cache-requirement', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(structured),
                      });
                      const data = await resp.json();
                      if (data.success && data.requirement_id) {
                        const stats = structured.stats || {};
                        localStorage.setItem(`req_summary_${data.requirement_id}`, JSON.stringify({
                          modules: stats.modules || 0,
                          features: stats.features || 0,
                          rules: stats.rules || 0,
                          fields: stats.fields || 0,
                          axure_notes: stats.axure_notes || 0,
                          parsed_at: new Date().toLocaleString(),
                        }));
                        localStorage.setItem(`req_data_${data.requirement_id}`, JSON.stringify(structured));
                        navigate(`/code-compare?requirement_id=${data.requirement_id}`);
                      } else {
                        navigate('/code-compare');
                      }
                    } catch {
                      navigate('/code-compare');
                    }
                  }}>
                    进入需求-代码对比
                  </Button>
                </Space>
              </div>
            </Card>
          </Space>
        )}

        {/* ========== Step 3: 生成中 ========== */}
        {step === 'generating' && (
          <div style={{ maxWidth: 500, margin: '0 auto', padding: '60px 0' }}>
            <div style={{ textAlign: 'center', marginBottom: 32 }}>
              <Spin size="large" />
            </div>
            <div style={{ marginBottom: 8, display: 'flex', justifyContent: 'space-between', fontSize: 14 }}>
              <span style={{ color: '#333' }}>{genStep}</span>
              <span style={{ color: '#999' }}>{genProgress}%</span>
            </div>
            <Progress percent={genProgress} showInfo={false} strokeColor={{ '0%': '#108ee9', '100%': '#87d068' }} />
            <p style={{ color: '#999', fontSize: 12, marginTop: 16, textAlign: 'center' }}>
              {config.provider || 'DeepSeek'} / {config.model || 'deepseek-chat'} · 目标 {config.count} 条用例 · 预计 1-3 分钟
            </p>
          </div>
        )}

        {/* ========== Step 4: 结果 ========== */}
        {step === 'result' && (
          <Space direction="vertical" style={{ width: '100%' }} size="large">
            <Alert
              message={`生成完成: ${testcases.length} 个测试用例`}
              type="success"
              showIcon
              action={
                <Space>
                  <Button icon={<DownloadOutlined />} onClick={handleExport}>导出 JSON</Button>
                </Space>
              }
            />

            {/* 覆盖率 */}
            {coverage && (
              <Descriptions title="覆盖率统计" bordered size="small" column={4}>
                <Descriptions.Item label="文档模块数">{coverage.total_modules_in_doc}</Descriptions.Item>
                <Descriptions.Item label="文档功能点">{coverage.total_features_in_doc}</Descriptions.Item>
                <Descriptions.Item label="文档业务规则">{coverage.total_rules_in_doc}</Descriptions.Item>
                <Descriptions.Item label="生成用例数">{coverage.testcases_generated}</Descriptions.Item>
              </Descriptions>
            )}

            {/* 用例分布 */}
            <Space>
              {(() => {
                const types = {};
                const priorities = {};
                testcases.forEach(tc => {
                  types[tc.type] = (types[tc.type] || 0) + 1;
                  priorities[tc.priority] = (priorities[tc.priority] || 0) + 1;
                });
                return (
                  <>
                    {Object.entries(types).map(([k, v]) => (
                      <Tag key={k}>{k}: {v}</Tag>
                    ))}
                    <span style={{ margin: '0 8px', color: '#ccc' }}>|</span>
                    {Object.entries(priorities).map(([k, v]) => {
                      const colors = { high: 'red', medium: 'orange', low: 'blue' };
                      const labels = { high: '高', medium: '中', low: '低' };
                      return <Tag key={k} color={colors[k]}>{labels[k] || k}: {v}</Tag>;
                    })}
                  </>
                );
              })()}
            </Space>

            {/* 用例表格 */}
            <Table
              dataSource={testcases}
              columns={columns}
              rowKey={(_, i) => i}
              size="small"
              scroll={{ x: 1200 }}
              pagination={{ pageSize: 20, showTotal: t => `共 ${t} 条` }}
              expandable={{
                expandedRowRender: (record) => (
                  <div style={{ padding: 8 }}>
                    <p><strong>前置条件:</strong> {record.precondition}</p>
                    <p><strong>测试步骤:</strong></p>
                    <ol style={{ paddingLeft: 20 }}>
                      {(record.steps || []).map((s, i) => <li key={i}>{s}</li>)}
                    </ol>
                    <p><strong>预期结果:</strong> {record.expected}</p>
                  </div>
                )
              }}
            />
          </Space>
        )}
      </Card>
    </div>
  );
}
