import React, { useState, useEffect } from 'react';
import { Settings, Check, AlertCircle, RefreshCw } from 'lucide-react';

const AIModelSelector = () => {
  const [config, setConfig] = useState(null);
  const [loading, setLoading] = useState(true);
  const [switching, setSwitching] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  // 加载当前配置
  const loadConfig = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/ai/current');
      const data = await response.json();
      
      if (data.success) {
        setConfig(data);
        setError(null);
      } else {
        setError(data.error || '加载配置失败');
      }
    } catch (err) {
      setError('无法连接到后端服务');
      console.error('加载AI配置失败:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadConfig();
  }, []);

  // 切换AI提供商和模型
  const switchProvider = async (provider, model) => {
    try {
      setSwitching(true);
      setError(null);
      setSuccess(null);

      const response = await fetch('/api/ai/providers/switch', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ provider, model }),
      });

      const data = await response.json();

      if (data.success) {
        setSuccess(data.message);
        // 重新加载配置
        await loadConfig();
        // 3秒后关闭成功提示
        setTimeout(() => setSuccess(null), 3000);
      } else {
        setError(data.error || '切换失败');
      }
    } catch (err) {
      setError('切换失败: ' + err.message);
      console.error('切换AI提供商失败:', err);
    } finally {
      setSwitching(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center gap-2 text-sm text-gray-600">
        <RefreshCw className="w-4 h-4 animate-spin" />
        <span>加载中...</span>
      </div>
    );
  }

  if (!config) {
    return null;
  }

  const currentProvider = config.providers[config.provider];
  const providersList = Object.entries(config.providers);

  return (
    <div className="relative">
      {/* 当前配置显示 */}
      <button
        onClick={() => setShowSettings(!showSettings)}
        className="flex items-center gap-2 px-3 py-2 text-sm bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
      >
        <Settings className="w-4 h-4" />
        <div className="flex flex-col items-start">
          <span className="font-medium">{currentProvider?.name || config.provider}</span>
          <span className="text-xs text-gray-500">{config.model}</span>
        </div>
      </button>

      {/* 设置面板 */}
      {showSettings && (
        <div className="absolute right-0 top-full mt-2 w-96 bg-white border border-gray-200 rounded-lg shadow-lg z-50">
          <div className="p-4 border-b border-gray-200">
            <h3 className="text-lg font-semibold">AI模型配置</h3>
            <p className="text-sm text-gray-600 mt-1">选择AI提供商和模型,全局生效</p>
          </div>

          {/* 错误提示 */}
          {error && (
            <div className="mx-4 mt-4 p-3 bg-red-50 border border-red-200 rounded-lg flex items-start gap-2">
              <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
              <span className="text-sm text-red-700">{error}</span>
            </div>
          )}

          {/* 成功提示 */}
          {success && (
            <div className="mx-4 mt-4 p-3 bg-green-50 border border-green-200 rounded-lg flex items-start gap-2">
              <Check className="w-5 h-5 text-green-500 flex-shrink-0 mt-0.5" />
              <span className="text-sm text-green-700">{success}</span>
            </div>
          )}

          <div className="p-4 max-h-96 overflow-y-auto">
            {providersList.map(([providerId, providerInfo]) => (
              <div key={providerId} className="mb-4 last:mb-0">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <h4 className="font-medium">{providerInfo.name}</h4>
                    {providerId === config.provider && (
                      <span className="px-2 py-0.5 text-xs bg-blue-100 text-blue-700 rounded">
                        当前
                      </span>
                    )}
                  </div>
                  {!providerInfo.api_key_configured && providerId !== 'mock' && providerId !== 'ollama' && (
                    <span className="text-xs text-orange-600">未配置API Key</span>
                  )}
                </div>

                <div className="space-y-1">
                  {providerInfo.models.map((model) => (
                    <button
                      key={model}
                      onClick={() => switchProvider(providerId, model)}
                      disabled={switching || (!providerInfo.api_key_configured && providerId !== 'mock' && providerId !== 'ollama')}
                      className={`w-full text-left px-3 py-2 rounded-lg text-sm transition-colors ${
                        providerId === config.provider && model === config.model
                          ? 'bg-blue-50 text-blue-700 border border-blue-200'
                          : 'hover:bg-gray-50 border border-transparent'
                      } ${
                        switching || (!providerInfo.api_key_configured && providerId !== 'mock' && providerId !== 'ollama')
                          ? 'opacity-50 cursor-not-allowed'
                          : 'cursor-pointer'
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <span>{model}</span>
                        {providerId === config.provider && model === config.model && (
                          <Check className="w-4 h-4 text-blue-600" />
                        )}
                      </div>
                    </button>
                  ))}
                </div>
              </div>
            ))}
          </div>

          <div className="p-4 border-t border-gray-200 bg-gray-50">
            <div className="text-xs text-gray-600 space-y-1">
              <p>💡 提示:</p>
              <ul className="list-disc list-inside space-y-0.5 ml-2">
                <li>切换后全局生效,所有AI功能都会使用新配置</li>
                <li>DeepSeek/OpenAI需要在.env文件中配置API Key</li>
                <li>Ollama需要本地安装并运行服务</li>
              </ul>
            </div>
          </div>

          <div className="p-4 border-t border-gray-200 flex justify-between">
            <button
              onClick={loadConfig}
              disabled={switching}
              className="px-3 py-1.5 text-sm text-gray-700 hover:bg-gray-100 rounded-lg transition-colors disabled:opacity-50"
            >
              <RefreshCw className={`w-4 h-4 inline mr-1 ${switching ? 'animate-spin' : ''}`} />
              刷新
            </button>
            <button
              onClick={() => setShowSettings(false)}
              className="px-4 py-1.5 text-sm bg-gray-200 hover:bg-gray-300 rounded-lg transition-colors"
            >
              关闭
            </button>
          </div>
        </div>
      )}

      {/* 点击外部关闭 */}
      {showSettings && (
        <div
          className="fixed inset-0 z-40"
          onClick={() => setShowSettings(false)}
        />
      )}
    </div>
  );
};

export default AIModelSelector;
