# AI 配置页面修复完成

## 问题描述

用户反馈 AI 配置页面不能编辑，并且保存时报错：
```
showToast is not a function
```

## 问题原因

1. **Toast 使用错误**
   - 错误用法：`const { showToast } = useToast()`
   - 正确用法：`const toast = useToast()`
   - Toast 方法：`toast.success()`, `toast.error()`, `toast.warning()`, `toast.info()`

2. **API 路径错误**（已在之前修复）
   - 前端调用：`/api/v1/ai/*`
   - 后端注册：`/api/ai/*`

## 修复内容

### 1. 修复 Toast 使用方式

**修改前：**
```javascript
const { showToast } = useToast();
showToast('消息', 'error');
```

**修改后：**
```javascript
const toast = useToast();
toast.error('消息');
toast.success('消息', 5000); // 可选：指定显示时长
```

### 2. 修复 API 路径

**修改前：**
```javascript
fetch('/api/v1/ai/providers')
fetch('/api/v1/ai/config')
fetch('/api/v1/ai/config/update')
```

**修改后：**
```javascript
fetch('/api/ai/providers')
fetch('/api/ai/config')
fetch('/api/ai/config/update')
```

### 3. 改进初始化逻辑

确保每个模块都有初始配置对象：
```javascript
const initialModuleConfigs = {};
configData.available_modules?.forEach(module => {
  initialModuleConfigs[module.id] = configData.module_configs?.[module.id] || {
    provider: configData.default_provider,
    model: configData.default_model
  };
});
setModuleConfigs(initialModuleConfigs);
```

### 4. 添加调试日志

```javascript
console.log('配置变更:', moduleId, field, value);
console.log('保存配置:', moduleConfigs);
console.log('更新数据:', updates);
```

## 测试结果

### 后端 API 测试 ✅

```
=== 测试获取提供商列表 ===
状态码: 200
提供商数量: 4
默认提供商: deepseek
  - DeepSeek: available (2 个模型)
  - 智谱 BigModel: available (3 个模型)
  - Ollama (本地): available (3 个模型)
  - Mock (测试): available (1 个模型)

=== 测试获取配置 ===
状态码: 200
默认提供商: deepseek
默认模型: deepseek-chat
模块配置:
  - testcase_generation: deepseek / deepseek-chat
  - script_generation: deepseek / deepseek-coder
  - swagger_analysis: openai / glm-4-flash
  - test_optimization: ollama / qwen2.5-coder:latest

=== 测试更新配置 ===
状态码: 200
结果: {
  "success": true,
  "message": "配置已更新，请重启后端服务使配置生效"
}
```

### 前端功能测试

- ✅ 页面正常加载
- ✅ 提供商状态正确显示
- ✅ 模块配置正确显示
- ✅ 下拉框可以正常选择
- ✅ 配置变更正常保存
- ✅ Toast 消息正常显示

## 使用说明

### 1. 访问页面

访问 `/ai-config` 或通过侧边栏：配置管理 → AI 模型配置

### 2. 修改配置

1. 在"模块级别配置"区域找到要配置的模块
2. 选择 AI 提供商（DeepSeek、智谱 BigModel、Ollama）
3. 选择模型（根据提供商自动更新可用模型列表）
4. 点击"保存配置"按钮

### 3. 使配置生效

配置保存后，需要重启后端服务：

```bash
# 停止当前后端（Ctrl+C）
# 重新启动
cd ai-test-platform
py backend_api_server.py
```

### 4. 验证配置

重启后端后，可以：
1. 刷新前端页面，查看配置是否保存
2. 查看 `.env` 文件，确认配置已写入
3. 使用相应模块时，会自动使用配置的模型

## 配置示例

### 当前默认配置

```env
DEFAULT_AI_PROVIDER=deepseek
DEFAULT_AI_MODEL=deepseek-chat
```

### 模块配置示例

```env
# 测试用例生成 - 使用 DeepSeek Chat
TESTCASE_GENERATION_AI_PROVIDER=deepseek
TESTCASE_GENERATION_AI_MODEL=deepseek-chat

# 测试脚本生成 - 使用 DeepSeek Coder
SCRIPT_GENERATION_AI_PROVIDER=deepseek
SCRIPT_GENERATION_AI_MODEL=deepseek-coder

# Swagger 分析 - 使用智谱快速模型
SWAGGER_ANALYSIS_AI_PROVIDER=openai
SWAGGER_ANALYSIS_AI_MODEL=glm-4-flash

# 测试优化 - 使用本地 Ollama
TEST_OPTIMIZATION_AI_PROVIDER=ollama
TEST_OPTIMIZATION_AI_MODEL=qwen2.5-coder:latest
```

## 文件清单

### 修改的文件
- ✅ `frontend/src/pages/AIConfigPage.jsx` - 修复 Toast 使用和 API 路径

### 测试文件
- ✅ `test_ai_config_api.py` - 后端 API 测试脚本

## 注意事项

1. **Toast 使用规范**
   - 使用 `const toast = useToast()` 获取 toast 对象
   - 调用方法：`toast.success()`, `toast.error()`, `toast.warning()`, `toast.info()`
   - 可选参数：显示时长（毫秒），默认 3000ms

2. **配置生效**
   - 修改配置后必须重启后端
   - 前端会显示提示信息
   - 配置写入 `.env` 文件

3. **API 路径规范**
   - AI 相关 API：`/api/ai/*`
   - V2 API：`/api/v2/*`
   - 不要使用：`/api/v1/*`（除非明确存在）

## 总结

AI 配置页面现在完全可用：
- ✅ 可以查看所有提供商状态
- ✅ 可以查看当前配置
- ✅ 可以编辑模块配置
- ✅ 可以保存配置
- ✅ Toast 消息正常显示
- ✅ 后端 API 完全正常

用户现在可以根据不同模块的需求，灵活配置最合适的 AI 模型。
