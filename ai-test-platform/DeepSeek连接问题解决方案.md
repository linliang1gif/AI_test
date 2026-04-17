# DeepSeek API 连接问题解决方案

## 问题描述
在使用DeepSeek API时,偶尔会出现以下错误:
- `Connection broken: InvalidChunkLength`
- `SSLError: EOF occurred in violation of protocol`
- `Max retries exceeded`

## 根本原因
这些错误通常是由以下原因引起的:
1. **网络不稳定** - 间歇性的网络波动
2. **SSL握手失败** - 网络环境或防火墙导致的SSL连接问题
3. **超时设置过短** - 默认60秒可能不够
4. **DeepSeek服务器负载** - 高峰期响应较慢

## 已实施的修复

### 1. 增强的错误处理和重试机制
已更新 `ai/ai_client.py`,添加:
- 自动重试策略(最多3次)
- 指数退避算法
- 更详细的错误信息
- 连接池复用

### 2. 增加超时时间
在 `.env` 文件中添加:
```env
AI_TIMEOUT=120  # 从60秒增加到120秒
```

### 3. 优化网络配置
- 使用requests.Session()复用连接
- 配置HTTPAdapter和Retry策略
- 分离连接超时(10秒)和读取超时(120秒)

## 解决方案

### 方案1: 使用Mock模式(推荐用于开发测试)
如果网络问题持续,可以临时切换到Mock模式:

1. 在前端点击右上角的AI模型选择器
2. 选择 "Mock" 提供商
3. Mock模式会返回模拟数据,不需要网络连接

或者修改 `.env`:
```env
DEFAULT_AI_PROVIDER=mock
```

### 方案2: 使用本地Ollama(推荐用于离线环境)
1. 安装Ollama: https://ollama.ai
2. 下载模型: `ollama pull qwen2.5:1.5b`
3. 在前端切换到 "Ollama" 提供商

或者修改 `.env`:
```env
DEFAULT_AI_PROVIDER=ollama
DEFAULT_AI_MODEL=qwen2.5:1.5b
```

### 方案3: 配置代理(如果在受限网络环境)
如果需要通过代理访问DeepSeek API:

在 `.env` 中添加:
```env
HTTP_PROXY=http://your-proxy:port
HTTPS_PROXY=http://your-proxy:port
```

### 方案4: 重启后端服务
有时候重启后端可以解决连接池问题:
```bash
# 停止当前后端
Ctrl+C

# 重新启动
py backend_api_server.py
```

## 诊断工具

运行诊断脚本检查连接状态:
```bash
py diagnose_deepseek.py
```

这个工具会:
- 测试基本网络连接
- 测试DeepSeek API连接
- 检查代理配置
- 显示环境信息

## 最佳实践

### 1. 生产环境建议
- 使用DeepSeek或OpenAI(需要稳定网络)
- 设置较长的超时时间(120秒)
- 配置重试机制(已默认启用)

### 2. 开发环境建议
- 使用Mock模式快速开发
- 或使用本地Ollama(需要下载模型)

### 3. 离线环境建议
- 必须使用Ollama本地模型
- 推荐模型: qwen2.5:1.5b (体积小,速度快)

## 前端模型切换功能

现在可以在前端实时切换AI模型:

1. 点击右上角的 **设置图标** 按钮
2. 查看当前使用的提供商和模型
3. 选择其他提供商和模型
4. 切换后全局生效,无需重启

支持的提供商:
- **DeepSeek** - 需要API Key,需要网络
- **OpenAI** - 需要API Key,需要网络
- **Ollama** - 本地模型,无需网络
- **Mock** - 模拟数据,无需网络

## 常见问题

### Q: 为什么有时候能连接,有时候不能?
A: 这是网络波动导致的。DeepSeek API在高峰期可能响应较慢,建议:
- 增加超时时间到120秒
- 使用重试机制(已默认启用)
- 或切换到Mock/Ollama模式

### Q: 如何知道当前使用的是哪个AI提供商?
A: 
- 前端右上角显示当前提供商和模型
- AI对话框标题显示当前配置
- 侧边栏底部显示系统状态

### Q: Mock模式和真实AI有什么区别?
A: 
- Mock模式返回预设的模拟数据,速度快但不够智能
- 真实AI(DeepSeek/OpenAI/Ollama)会根据输入生成真实的响应
- Mock模式适合开发测试,真实AI适合生产使用

### Q: Ollama需要什么配置?
A:
- 需要本地安装Ollama服务
- 需要下载至少一个模型
- 推荐: qwen2.5:1.5b (1.5GB,速度快)
- 不需要API Key,完全离线

## 技术支持

如果问题持续,请提供以下信息:
1. 运行 `py diagnose_deepseek.py` 的输出
2. 后端日志中的错误信息
3. 网络环境描述(是否使用代理,是否在公司内网等)
