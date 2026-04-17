# AI模型切换功能使用说明

## 功能概述

AI测试平台现在支持在前端界面动态切换AI模型,切换后全局生效,所有AI功能都会使用新的配置。

## 支持的AI提供商

### 1. DeepSeek (推荐)
- **模型**: deepseek-chat, deepseek-coder
- **特点**: 性价比高,中文支持好
- **配置**: 需要在.env文件中配置`DEEPSEEK_API_KEY`
- **获取API Key**: https://platform.deepseek.com/

### 2. OpenAI
- **模型**: gpt-3.5-turbo, gpt-4, gpt-4-turbo
- **特点**: 功能强大,质量高
- **配置**: 需要在.env文件中配置`OPENAI_API_KEY`
- **获取API Key**: https://platform.openai.com/

### 3. Ollama (本地)
- **模型**: 自定义本地模型
- **特点**: 完全本地运行,无需API Key,数据隐私
- **配置**: 需要本地安装Ollama服务
- **安装**: https://ollama.ai/

### 4. Mock (测试)
- **模型**: mock-model
- **特点**: 用于测试,返回模拟数据
- **配置**: 无需配置

## 使用方法

### 前端界面切换

1. 在顶部导航栏找到AI模型选择器(显示当前模型)
2. 点击打开设置面板
3. 选择想要使用的提供商和模型
4. 系统会自动切换并更新配置
5. 切换后立即生效,无需重启

### API切换

也可以通过API进行切换:

```bash
# 获取当前配置
curl http://localhost:8000/api/ai/current

# 切换模型
curl -X POST http://localhost:8000/api/ai/providers/switch \
  -H "Content-Type: application/json" \
  -d '{"provider": "deepseek", "model": "deepseek-chat"}'
```

## 配置文件

AI配置存储在`.env`文件中:

```env
# AI提供商配置
DEFAULT_AI_PROVIDER=deepseek
DEFAULT_AI_MODEL=deepseek-chat

# API Keys
DEEPSEEK_API_KEY=sk-your-key-here
OPENAI_API_KEY=

# Base URLs
DEEPSEEK_BASE_URL=https://api.deepseek.com
OPENAI_BASE_URL=https://api.openai.com/v1
OLLAMA_BASE_URL=http://localhost:11434

# Ollama模型列表
OLLAMA_MODELS=qwen2.5:1.5b,deepseek-coder,llama3
```

## 全局生效范围

切换AI模型后,以下功能都会使用新的配置:

1. ✅ 测试用例生成
2. ✅ 功能模块拆分
3. ✅ 测试点生成
4. ✅ 场景矩阵生成
5. ✅ 断言生成
6. ✅ 测试数据智能生成
7. ✅ AI对话助手
8. ✅ 所有其他AI功能

## 注意事项

1. **API Key配置**: DeepSeek和OpenAI需要先配置API Key才能使用
2. **Ollama服务**: 使用Ollama需要确保本地服务正在运行
3. **配置持久化**: 切换后的配置会保存到.env文件,重启后依然有效
4. **实时生效**: 切换后立即生效,正在进行的AI任务会使用新配置
5. **成本考虑**: 不同提供商的API调用成本不同,请根据需求选择

## 故障排查

### 切换失败
- 检查后端服务是否正常运行
- 查看浏览器控制台是否有错误信息
- 确认.env文件有写入权限

### API Key未配置
- 在.env文件中添加对应的API Key
- 重启后端服务使配置生效

### Ollama连接失败
- 确认Ollama服务正在运行: `ollama serve`
- 检查端口是否正确(默认11434)
- 确认模型已下载: `ollama list`

## 测试脚本

运行测试脚本验证功能:

```bash
cd ai-test-platform
python test_ai_switch.py
```

## 技术实现

### 后端API

- `GET /api/ai/current` - 获取当前AI配置
- `POST /api/ai/providers/switch` - 切换AI提供商和模型

### 前端组件

- `AIModelSelector.jsx` - AI模型选择器组件
- 集成在顶部导航栏`Topbar.jsx`中

### 配置管理

- 配置存储在`.env`文件
- 使用`config.py`管理配置
- 支持热重载,无需重启

## 更新日志

### v1.2.0 (2024-03-23)
- ✅ 添加前端AI模型切换界面
- ✅ 实现全局配置更新机制
- ✅ 支持DeepSeek、OpenAI、Ollama、Mock四种提供商
- ✅ 配置持久化到.env文件
- ✅ 实时生效,无需重启
