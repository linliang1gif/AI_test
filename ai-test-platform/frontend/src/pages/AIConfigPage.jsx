import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/Card';
import { useToast } from '../components/ui/Toast';

const AIConfigPage = () => {
  const [providers, setProviders] = useState([]);
  const [config, setConfig] = useState(null);
  const [moduleConfigs, setModuleConfigs] = useState({});
  const [loading, setLoading] = useState(true);
  const toast = useToast();

  // TAPD 配置
  const [tapdConfig, setTapdConfig] = useState({
    workspace_id: '', api_user: '', api_password: '',
    default_reporter: '', default_assignee: '', default_bug_type: 'codeerr',
  });
  const [tapdSaving, setTapdSaving] = useState(false);
  const [tapdTesting, setTapdTesting] = useState(false);

  useEffect(() => {
    loadConfig();
  }, []);

  const loadConfig = async () => {
    try {
      setLoading(true);
      
      // 加载提供商列表
      const providersRes = await fetch('/api/ai/providers');
      const providersData = await providersRes.json();
      setProviders(providersData.providers || []);
      
      // 加载配置
      const configRes = await fetch('/api/ai/config');
      const configData = await configRes.json();
      setConfig(configData);
      
      // 初始化模块配置，确保每个模块都有配置对象
      const initialModuleConfigs = {};
      configData.available_modules?.forEach(module => {
        initialModuleConfigs[module.id] = configData.module_configs?.[module.id] || {
          provider: configData.default_provider,
          model: configData.default_model
        };
      });
      setModuleConfigs(initialModuleConfigs);
      
      // 加载 TAPD 配置
      try {
        const tapdRes = await fetch('/api/v2/code-compare/tapd/config');
        const tapdData = await tapdRes.json();
        if (tapdData.success && tapdData.config) {
          setTapdConfig(prev => ({ ...prev, ...tapdData.config }));
        }
      } catch {}

    } catch (error) {
      toast.error('加载配置失败: ' + error.message);
      console.error('加载配置错误:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSaveTapd = async () => {
    if (!tapdConfig.workspace_id || !tapdConfig.api_user || !tapdConfig.api_password) {
      toast.error('请填写 Workspace ID、API 账号和密码');
      return;
    }
    setTapdSaving(true);
    try {
      const res = await fetch('/api/v2/code-compare/tapd/config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(tapdConfig),
      });
      const data = await res.json();
      if (data.success) toast.success('TAPD 配置已保存');
      else toast.error(data.detail || '保存失败');
    } catch (e) {
      toast.error('保存失败: ' + e.message);
    } finally {
      setTapdSaving(false);
    }
  };

  const handleTestTapd = async () => {
    setTapdTesting(true);
    try {
      const res = await fetch('/api/v2/code-compare/tapd/test', { method: 'POST' });
      const data = await res.json();
      if (data.success) toast.success(data.message || '连接成功');
      else toast.error(data.message || '连接失败');
    } catch (e) {
      toast.error('测试失败: ' + e.message);
    } finally {
      setTapdTesting(false);
    }
  };

  const handleModuleConfigChange = (moduleId, field, value) => {
    console.log('配置变更:', moduleId, field, value);
    setModuleConfigs(prev => ({
      ...prev,
      [moduleId]: {
        ...prev[moduleId],
        [field]: value
      }
    }));
  };

  const handleSave = async () => {
    try {
      console.log('保存配置:', moduleConfigs);
      
      const updates = {};
      
      // 构建更新数据
      Object.entries(moduleConfigs).forEach(([moduleId, moduleConfig]) => {
        const moduleKey = moduleId.toUpperCase();
        updates[`${moduleKey}_AI_PROVIDER`] = moduleConfig.provider;
        updates[`${moduleKey}_AI_MODEL`] = moduleConfig.model;
      });
      
      console.log('更新数据:', updates);
      
      const response = await fetch('/api/ai/config/update', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ updates })
      });
      
      const result = await response.json();
      
      if (result.success) {
        toast.success('配置已保存并立即生效', 3000);
        // 重新加载配置以显示最新状态
        await loadConfig();
      } else {
        toast.error('保存失败: ' + (result.message || '未知错误'));
      }
    } catch (error) {
      toast.error('保存配置失败: ' + error.message);
      console.error('保存配置错误:', error);
    }
  };

  const getProviderModels = (providerId) => {
    const provider = providers.find(p => p.id === providerId);
    return provider?.models || [];
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">加载中...</div>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6 space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold">AI 模型配置</h1>
        <button
          onClick={handleSave}
          className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
        >
          保存配置
        </button>
      </div>

      {/* 提供商状态卡片 */}
      <Card>
        <CardHeader>
          <CardTitle>AI 提供商状态</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {providers.map(provider => (
              <div
                key={provider.id}
                className={`p-4 border rounded-lg ${
                  provider.status === 'available'
                    ? 'border-green-300 bg-green-50'
                    : 'border-gray-300 bg-gray-50'
                }`}
              >
                <div className="flex items-center justify-between mb-2">
                  <span className="font-semibold">{provider.name}</span>
                  <span
                    className={`px-2 py-1 text-xs rounded ${
                      provider.status === 'available'
                        ? 'bg-green-200 text-green-800'
                        : 'bg-gray-200 text-gray-600'
                    }`}
                  >
                    {provider.status === 'available' ? '可用' : '不可用'}
                  </span>
                </div>
                <div className="text-sm text-gray-600">
                  {provider.models?.length || 0} 个模型
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* 默认配置 */}
      <Card>
        <CardHeader>
          <CardTitle>默认配置</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                默认提供商
              </label>
              <div className="px-3 py-2 bg-gray-100 rounded">
                {providers.find(p => p.id === config?.default_provider)?.name || config?.default_provider}
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                默认模型
              </label>
              <div className="px-3 py-2 bg-gray-100 rounded">
                {config?.default_model}
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* 模块配置 */}
      <Card>
        <CardHeader>
          <CardTitle>模块级别配置</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-6">
            {config?.available_modules?.map(module => {
              const moduleConfig = moduleConfigs[module.id] || {};
              const selectedProvider = moduleConfig.provider || config.default_provider;
              const availableModels = getProviderModels(selectedProvider);

              return (
                <div key={module.id} className="border rounded-lg p-4">
                  <div className="mb-4">
                    <h3 className="font-semibold text-lg">{module.name}</h3>
                    <p className="text-sm text-gray-600">{module.description}</p>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        AI 提供商
                      </label>
                      <select
                        value={selectedProvider}
                        onChange={(e) => handleModuleConfigChange(module.id, 'provider', e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      >
                        {providers
                          .filter(p => p.status === 'available')
                          .map(provider => (
                            <option key={provider.id} value={provider.id}>
                              {provider.name}
                            </option>
                          ))}
                      </select>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        模型
                      </label>
                      <select
                        value={moduleConfig.model || config.default_model}
                        onChange={(e) => handleModuleConfigChange(module.id, 'model', e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      >
                        {availableModels.map(model => (
                          <option key={model} value={model}>
                            {model}
                          </option>
                        ))}
                      </select>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>

      {/* TAPD 对接配置 */}
      <Card>
        <CardHeader>
          <CardTitle>TAPD 缺陷推送配置</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-gray-500 mb-4">
            配置 TAPD Open API 账号后，可在需求-代码对比的 Finding 中一键推送缺陷到 TAPD。
          </p>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Workspace ID *</label>
              <input
                type="text"
                className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="在 TAPD 项目 URL 中获取，如 20000001"
                value={tapdConfig.workspace_id}
                onChange={e => setTapdConfig(prev => ({ ...prev, workspace_id: e.target.value }))}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">默认缺陷类型</label>
              <select
                className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                value={tapdConfig.default_bug_type}
                onChange={e => setTapdConfig(prev => ({ ...prev, default_bug_type: e.target.value }))}
              >
                <option value="codeerr">代码错误</option>
                <option value="interface">接口问题</option>
                <option value="function">功能缺陷</option>
                <option value="performance">性能问题</option>
                <option value="others">其他</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">API 账号 *</label>
              <input
                type="text"
                className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="TAPD Open API 账号"
                value={tapdConfig.api_user}
                onChange={e => setTapdConfig(prev => ({ ...prev, api_user: e.target.value }))}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">API 密码 *</label>
              <input
                type="password"
                className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="TAPD Open API 密码"
                value={tapdConfig.api_password}
                onChange={e => setTapdConfig(prev => ({ ...prev, api_password: e.target.value }))}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">默认报告人</label>
              <input
                type="text"
                className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                placeholder="TAPD 用户名（可选）"
                value={tapdConfig.default_reporter}
                onChange={e => setTapdConfig(prev => ({ ...prev, default_reporter: e.target.value }))}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">默认处理人</label>
              <input
                type="text"
                className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                placeholder="TAPD 用户名（可选）"
                value={tapdConfig.default_assignee}
                onChange={e => setTapdConfig(prev => ({ ...prev, default_assignee: e.target.value }))}
              />
            </div>
          </div>
          <div className="flex gap-3 mt-4">
            <button
              onClick={handleSaveTapd}
              disabled={tapdSaving}
              className="px-4 py-2 bg-blue-600 text-white text-sm rounded-md hover:bg-blue-700 disabled:opacity-50"
            >
              {tapdSaving ? '保存中...' : '保存配置'}
            </button>
            <button
              onClick={handleTestTapd}
              disabled={tapdTesting}
              className="px-4 py-2 bg-gray-100 text-gray-700 text-sm rounded-md border hover:bg-gray-200 disabled:opacity-50"
            >
              {tapdTesting ? '测试中...' : '测试连接'}
            </button>
          </div>
          <p className="text-xs text-gray-400 mt-3">
            获取方式: TAPD → 公司管理 → API 账号 → 创建应用。Workspace ID 在项目 URL 中 (如 tapd.cn/<b>20000001</b>/...)。
          </p>
        </CardContent>
      </Card>

      {/* 配置说明 */}
      <Card>
        <CardHeader>
          <CardTitle>配置说明</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2 text-sm text-gray-600">
            <p>• 每个模块可以独立配置使用的 AI 提供商和模型</p>
            <p>• 如果模块未配置，将使用默认配置</p>
            <p>• 配置保存后立即生效，无需重启服务</p>
            <p>• 建议根据模块特点选择合适的模型：</p>
            <ul className="ml-6 space-y-1">
              <li>- 测试用例生成：推荐 deepseek-v4-flash（快速）或 deepseek-v4-pro（复杂需求）</li>
              <li>- 测试脚本生成：推荐 deepseek-v4-pro 或 deepseek-reasoner（带推理）</li>
              <li>- Swagger 分析：推荐 deepseek-v4-flash 或 deepseek-chat</li>
              <li>- 测试优化：使用本地模型节省成本（如 ollama）</li>
              <li>- AI 用例评审：推荐 deepseek-chat 或 deepseek-v4-flash（快速评审大量用例）</li>
            </ul>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default AIConfigPage;
