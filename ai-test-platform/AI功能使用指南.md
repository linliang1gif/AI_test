# AI功能使用指南

## 🚀 快速开始

### 1. 启动服务

```bash
# 1. 启动后端API服务器
cd ai测试/ai-test-platform
py simple_api_server.py

# 2. 启动前端开发服务器（新终端）
cd frontend
npm run dev
```

### 2. 验证功能

访问以下页面验证功能：

#### 主要功能页面
- **AI洞察页面**: http://localhost:3000/ai-insights
- **AI对话测试**: http://localhost:3000/test_ai_chat.html
- **切换功能修复**: http://localhost:3000/fix_switch_issue.html

#### 调试工具页面
- **API测试**: http://localhost:3000/test_frontend_api.html
- **切换调试**: http://localhost:3000/debug_switch.html

## 🔄 AI提供商切换

### 方法1: 使用React界面
1. 访问 http://localhost:3000/ai-insights
2. 找到"AI提供商管理"区域
3. 选择提供商并点击"切换提供商"

### 方法2: 使用修复页面（推荐）
1. 访问 http://localhost:3000/fix_switch_issue.html
2. 点击"切换到Ollama"按钮
3. 查看切换结果

### 方法3: 直接API调用
```bash
# 使用Python测试
py test_switch_api.py

# 或使用PowerShell
Invoke-WebRequest -Uri "http://localhost:8000/api/ai/providers/switch" -Method POST -ContentType "application/json" -Body '{"provider":"ollama","model":"qwen2.5:1.5b"}'
```

## 🤖 AI对话测试

### 使用AI对话页面
1. 访问 http://localhost:3000/test_ai_chat.html
2. 查看当前AI配置
3. 输入问题并发送
4. 查看AI回复和配置信息

### 验证全局配置
- AI回复会显示使用的提供商和模型
- 确认使用的是全局配置
- 切换提供商后重新测试

## 📊 状态监控

### 查看当前配置
```javascript
// 获取当前AI配置
fetch('http://localhost:8000/api/ai/current')
  .then(res => res.json())
  .then(data => console.log(data));
```

### 测试提供商连接
```javascript
// 测试Ollama连接
fetch('http://localhost:8000/api/ai/providers/Ollama/test', {
  method: 'POST'
}).then(res => res.json()).then(data => console.log(data));
```

## 🔧 故障排除

### 常见问题

#### 1. 后端API无法访问
- 确认后端服务器正在运行
- 检查端口8000是否被占用
- 访问 http://localhost:8000/api/ai/current 测试

#### 2. 前端切换失败
- 使用修复页面进行切换
- 检查浏览器开发者工具的网络请求
- 尝试刷新页面

#### 3. Ollama连接失败
- 确认Ollama服务正在运行
- 检查 http://localhost:11434 是否可访问
- 确认模型已下载

### 调试工具

#### 后端测试
```bash
# 完整功能测试
py complete_test.py

# 切换功能测试
py test_switch_api.py
```

#### 前端测试
- 使用浏览器开发者工具查看网络请求
- 访问调试页面查看详细日志
- 检查控制台错误信息

## 📋 功能清单

### ✅ 已完成功能
- [x] AI提供商列表获取
- [x] 提供商连接测试
- [x] 提供商切换功能
- [x] 全局配置管理
- [x] AI文本生成
- [x] 当前状态查询
- [x] 实时配置显示

### 🔄 全局配置机制
- [x] 后端状态存储
- [x] 配置持久化
- [x] 自动应用到AI生成
- [x] 支持配置覆盖
- [x] 实时状态查询

## 🎯 使用建议

1. **首次使用**: 先访问修复页面确认功能正常
2. **日常使用**: 使用React界面进行操作
3. **问题排查**: 使用调试页面和测试脚本
4. **功能验证**: 使用AI对话页面测试生成功能

## 📞 技术支持

如果遇到问题，请：
1. 检查服务器是否正常运行
2. 使用测试脚本验证后端功能
3. 查看浏览器开发者工具
4. 使用调试页面获取详细信息

AI功能已完全集成，可以正常使用！