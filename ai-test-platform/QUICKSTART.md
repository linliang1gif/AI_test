# AI Test Platform - 快速开始指南 🚀

## 📋 前置要求

在开始之前，请确保你的系统已安装以下软件：

- **Python 3.11+** - [下载地址](https://www.python.org/downloads/)
- **Node.js 18+** - [下载地址](https://nodejs.org/)
- **Git** - [下载地址](https://git-scm.com/)
- **Ollama** (可选，用于本地AI模型) - [下载地址](https://ollama.ai/)

## 🚀 快速启动 (5分钟)

### 1. 克隆项目

```bash
git clone <repository-url>
cd ai-test-platform
```

### 2. 安装Python依赖

```bash
# 创建虚拟环境 (推荐)
python -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 3. 安装前端依赖

```bash
cd frontend
npm install
cd ..
```

### 4. 配置环境变量

```bash
# 复制环境配置示例
cp .env.example .env

# 编辑 .env 文件，配置你的AI API密钥
# 如果使用Ollama本地模型，可以跳过API密钥配置
```

### 5. 启动Ollama (可选)

如果使用本地AI模型：

```bash
# 启动Ollama服务
ollama serve

# 拉取模型 (新终端)
ollama pull qwen2.5:1.5b
```

### 6. 一键启动平台

```bash
# 使用统一启动脚本
python start_platform.py
```

启动成功后，访问：
- **前端界面**: http://localhost:3000
- **后端API**: http://127.0.0.1:8081
- **API文档**: http://127.0.0.1:8081/docs

## 📖 基础使用流程

### 1. 上传需求文档

1. 访问前端界面 http://localhost:3000
2. 进入 "测试用例" 页面
3. 点击 "上传需求文档" 按钮
4. 选择你的需求文档 (支持 .txt, .md, .docx, .pdf)
5. 等待AI自动生成测试用例

### 2. 查看生成的测试用例

- 在测试用例列表中查看AI生成的用例
- 可以编辑、删除或导出测试用例
- 支持导出为Excel格式

### 3. 执行测试

1. 选择要执行的测试用例
2. 点击 "执行测试" 按钮
3. 查看实时执行进度
4. 查看测试结果和报告

### 4. 生成自动化脚本

1. 进入 "自动化" 页面
2. 选择测试用例
3. 点击 "生成脚本" 按钮
4. 下载生成的pytest脚本

## 🔧 高级配置

### AI提供商配置

平台支持多种AI提供商：

#### 1. Ollama (本地模型，推荐)

```bash
# .env 配置
DEFAULT_AI_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODELS=qwen2.5:1.5b,deepseek-coder
```

优点：
- 完全本地运行，无需API密钥
- 数据隐私安全
- 无使用成本

#### 2. DeepSeek (云端API)

```bash
# .env 配置
DEFAULT_AI_PROVIDER=deepseek
DEEPSEEK_API_KEY=your_api_key_here
DEEPSEEK_BASE_URL=https://api.deepseek.com
```

优点：
- 响应速度快
- 模型能力强
- 成本较低

#### 3. OpenAI (云端API)

```bash
# .env 配置
DEFAULT_AI_PROVIDER=openai
OPENAI_API_KEY=your_api_key_here
OPENAI_BASE_URL=https://api.openai.com/v1
```

### 测试环境配置

编辑 `.env` 文件配置测试目标：

```bash
# 测试环境基础URL
BASE_TEST_URL=http://your-test-server:8080

# 测试超时时间
TEST_TIMEOUT=30

# 并行测试线程数
PARALLEL_WORKERS=4
```

## 🐛 常见问题

### 1. 前端无法连接后端

**问题**: 前端显示网络错误

**解决方案**:
- 检查后端是否正常启动 (http://127.0.0.1:8081)
- 检查防火墙设置
- 查看浏览器控制台错误信息

### 2. AI生成失败

**问题**: 测试用例生成失败

**解决方案**:
- 检查AI服务是否正常运行
  - Ollama: `ollama list` 查看已安装模型
  - DeepSeek/OpenAI: 检查API密钥是否正确
- 查看后端日志获取详细错误信息
- 尝试切换其他AI提供商

### 3. Ollama模型下载慢

**问题**: 模型下载速度慢或失败

**解决方案**:
```bash
# 使用国内镜像 (如果可用)
export OLLAMA_HOST=http://your-mirror-host

# 或使用较小的模型
ollama pull qwen2.5:1.5b  # 1.5B参数，较小
```

### 4. 端口被占用

**问题**: 启动失败，提示端口被占用

**解决方案**:
```bash
# Windows查看端口占用
netstat -ano | findstr :8081
netstat -ano | findstr :3000

# 杀死占用进程
taskkill /PID <进程ID> /F

# 或修改 .env 配置使用其他端口
BACKEND_PORT=8082
FRONTEND_PORT=3001
```

## 📚 更多文档

- [完整使用指南](项目使用指南.md)
- [API文档](http://127.0.0.1:8081/docs) (启动后访问)
- [架构设计](docs/enterprise-refactoring-plan.md)
- [开发指南](CONTRIBUTING.md)

## 💡 使用技巧

### 1. 提高测试用例质量

- 上传详细的需求文档
- 使用结构化的文档格式
- 包含具体的功能描述和业务规则

### 2. 优化AI生成速度

- 使用本地Ollama模型 (最快)
- 调整 `AI_MAX_TOKENS` 参数
- 使用较小的模型 (如 qwen2.5:1.5b)

### 3. 批量处理

- 一次上传多个需求文档
- 使用API批量生成测试用例
- 导出Excel后批量编辑

## 🆘 获取帮助

如果遇到问题：

1. 查看 [常见问题](#-常见问题)
2. 查看后端日志: `logs/platform.log`
3. 查看浏览器控制台错误
4. 提交Issue到项目仓库

## 🎉 下一步

现在你已经成功启动平台，可以：

1. 尝试上传一个简单的需求文档
2. 查看AI生成的测试用例
3. 执行测试并查看报告
4. 探索更多高级功能

祝你使用愉快！🚀
