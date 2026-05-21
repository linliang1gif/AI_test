# Ollama本地模型安装和使用指南

## 🎯 什么是Ollama？

Ollama是一个轻量级、可扩展的框架，用于在本地运行大型语言模型。它支持多种开源模型，包括：
- **deepseek-coder**: 专门用于代码生成和理解
- **qwen2.5**: 阿里巴巴的通用大语言模型
- **llama3**: Meta的开源大语言模型

## 📦 安装Ollama

### Windows安装
1. 访问 [Ollama官网](https://ollama.ai)
2. 下载Windows安装包
3. 运行安装程序
4. 安装完成后，Ollama会自动启动服务

### macOS安装
```bash
# 使用Homebrew安装
brew install ollama

# 或者下载官方安装包
# 访问 https://ollama.ai 下载.dmg文件
```

### Linux安装
```bash
# 使用官方安装脚本
curl -fsSL https://ollama.ai/install.sh | sh

# 或者使用包管理器
# Ubuntu/Debian
sudo apt install ollama

# CentOS/RHEL
sudo yum install ollama
```

## 🚀 启动Ollama服务

```bash
# 启动Ollama服务
ollama serve

# 服务将在 http://localhost:11434 运行
```

## 📥 下载和运行模型

### 1. DeepSeek Coder (推荐用于代码生成)
```bash
# 下载模型
ollama pull deepseek-coder

# 运行模型
ollama run deepseek-coder
```

### 2. Qwen2.5 (通用模型)
```bash
# 下载模型
ollama pull qwen2.5

# 运行模型
ollama run qwen2.5
```

### 3. Llama3 (Meta开源模型)
```bash
# 下载模型
ollama pull llama3

# 运行模型
ollama run llama3
```

## ⚙️ 配置AI测试平台

### 1. 环境变量配置
在 `.env` 文件中添加：
```env
# Ollama配置
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODELS=deepseek-coder,qwen2.5,llama3
DEFAULT_AI_PROVIDER=ollama
DEFAULT_AI_MODEL=deepseek-coder
```

### 2. 验证配置
启动AI测试平台后：
1. 进入"AI分析"页面
2. 点击"管理提供商"
3. 查看Ollama状态是否为"可用"
4. 点击"测试"按钮验证连接

## 🔧 模型管理

### 查看已安装的模型
```bash
ollama list
```

### 删除模型
```bash
ollama rm deepseek-coder
```

### 更新模型
```bash
ollama pull deepseek-coder:latest
```

## 💡 使用建议

### 1. 模型选择
- **代码生成和测试用例**: 使用 `deepseek-coder`
- **需求分析和文档理解**: 使用 `qwen2.5`
- **通用对话和分析**: 使用 `llama3`

### 2. 性能优化
- **内存要求**: 至少8GB RAM，推荐16GB+
- **存储空间**: 每个模型约4-7GB
- **CPU**: 支持AVX2指令集的现代CPU

### 3. 网络配置
如果需要在不同机器上运行：
```bash
# 绑定到所有网络接口
OLLAMA_HOST=0.0.0.0 ollama serve

# 在AI测试平台中配置
OLLAMA_BASE_URL=http://your-server-ip:11434
```

## 🚨 故障排除

### 1. 服务无法启动
```bash
# 检查端口是否被占用
netstat -an | grep 11434

# 杀死占用进程
pkill ollama

# 重新启动
ollama serve
```

### 2. 模型下载失败
```bash
# 检查网络连接
curl -I https://ollama.ai

# 使用代理下载
HTTP_PROXY=http://proxy:port ollama pull deepseek-coder
```

### 3. 内存不足
```bash
# 使用较小的模型
ollama pull deepseek-coder:1.3b

# 或者调整模型参数
ollama run deepseek-coder --memory 4GB
```

## 📊 性能对比

| 提供商 | 成本 | 隐私性 | 响应速度 | 模型质量 |
|--------|------|--------|----------|----------|
| DeepSeek API | 低 | 中 | 快 | 高 |
| OpenAI API | 高 | 低 | 快 | 高 |
| Ollama本地 | 免费 | 高 | 中 | 中-高 |

## 🎉 开始使用

1. 安装Ollama
2. 下载推荐模型：`ollama pull deepseek-coder`
3. 启动服务：`ollama serve`
4. 在AI测试平台中切换到Ollama提供商
5. 开始生成测试用例！

## 📚 更多资源

- [Ollama官方文档](https://github.com/ollama/ollama)
- [支持的模型列表](https://ollama.ai/library)
- [API文档](https://github.com/ollama/ollama/blob/main/docs/api.md)