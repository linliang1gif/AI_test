# AI Test Platform Web可视化平台使用说明

## 🚀 快速启动

### Windows系统
1. **双击运行**: `启动Web平台.bat`
2. **或者命令行**:
   ```cmd
   cd ai测试/ai-test-platform
   python app/web/web_server.py
   ```

### Linux/Mac系统
1. **运行脚本**:
   ```bash
   chmod +x 启动Web平台.sh
   ./启动Web平台.sh
   ```
2. **或者命令行**:
   ```bash
   cd ai测试/ai-test-platform
   python3 app/web/web_server.py
   ```

## 🌐 访问Web界面

启动成功后，在浏览器中访问：
**http://localhost:8080**

## 📱 Web界面功能

### 1. 主页面
- 🎯 **项目概述**: AI Test Platform介绍
- 📊 **功能展示**: 完整测试流程展示
- 🚀 **快速开始**: 操作指引

### 2. 文档上传区域

#### 📄 需求文档上传
- **支持格式**: `.txt`, `.md`, `.docx`
- **操作方式**: 点击或拖拽上传
- **功能**: 自动解析需求内容

#### 🔗 Swagger文档上传
- **支持格式**: `.json`, `.yaml`, `.yml`
- **操作方式**: 点击或拖拽上传
- **功能**: 自动解析API接口

### 3. 测试生成功能

#### 🤖 一键生成测试
- **前置条件**: 至少上传需求文档
- **可选项**: Swagger文档（用于API测试）
- **功能**: 
  - AI需求解析
  - 模块拆分
  - 测试点生成
  - 测试用例生成
  - API测试脚本生成
  - 自动化执行
  - 覆盖率分析

#### 📊 实时进度监控
- **进度条**: 显示当前执行进度
- **状态更新**: 实时显示执行状态
- **错误提示**: 失败时显示详细错误信息

### 4. 测试报告查看

#### 📋 报告列表
- **报告类型**: HTML测试报告
- **排序方式**: 按创建时间倒序
- **信息显示**: 文件名、大小、创建时间

#### 🔍 在线查看
- **点击查看**: 在新窗口打开报告
- **报告内容**: 
  - 测试执行摘要
  - 覆盖率分析
  - Bug分析结果
  - Self Healing日志

## 🔧 配置要求

### 环境依赖
```bash
# Python 3.11+
python --version

# 必要依赖包
pip install -r requirements.txt
```

### 主要依赖
- `fastapi` - Web框架
- `uvicorn` - ASGI服务器
- `jinja2` - 模板引擎
- `aiofiles` - 异步文件处理
- `python-multipart` - 文件上传支持

### AI配置
需要在 `.env` 文件中配置AI API Key：
```env
# DeepSeek API (推荐)
DEEPSEEK_API_KEY=sk-your-deepseek-api-key

# 或者 OpenAI API
OPENAI_API_KEY=sk-your-openai-api-key
```

## 📁 文件结构

### 上传目录
- `uploads/` - 用户上传的文件存储

### 输出目录
- `output/` - 生成的测试文件
  - `test_strategy.md` - 测试策略
  - `test_points.json` - 测试点
  - `test_cases.xlsx` - 测试用例
  - `api_tests/` - API测试脚本
  - `reports/` - 测试报告

## 🎯 使用流程

### 标准流程
1. **启动平台**: 运行启动脚本
2. **访问界面**: 浏览器打开 http://localhost:8080
3. **上传需求**: 拖拽或点击上传需求文档
4. **上传接口** (可选): 上传Swagger文档
5. **生成测试**: 点击"开始生成测试"按钮
6. **监控进度**: 观察实时进度和状态
7. **查看报告**: 在报告列表中查看生成的报告

### 高级功能
- **Self Healing**: 测试失败时自动修复
- **覆盖率分析**: 全面的测试覆盖率评估
- **AI Agent**: 多Agent协同工作
- **流水线**: 端到端自动化流程

## 🚨 常见问题

### Q1: 启动失败
**A**: 检查Python环境和依赖包安装
```bash
python --version  # 确认Python 3.11+
pip install -r requirements.txt  # 安装依赖
```

### Q2: 无法访问Web界面
**A**: 确认服务器启动成功，检查端口占用
```bash
netstat -an | findstr 8080  # Windows
netstat -an | grep 8080     # Linux/Mac
```

### Q3: 文件上传失败
**A**: 检查文件格式和大小限制
- 需求文档: `.txt`, `.md`, `.docx`
- Swagger文档: `.json`, `.yaml`, `.yml`
- 文件大小: < 10MB

### Q4: AI API调用失败
**A**: 检查API Key配置
```bash
# 检查.env文件
cat .env

# 确认API Key有效性
```

### Q5: 测试生成失败
**A**: 查看错误日志，常见原因：
- AI API Key未配置或无效
- 需求文档格式不支持
- 网络连接问题

## 📞 技术支持

### 日志查看
- **Web服务器日志**: 控制台输出
- **任务执行日志**: `output/logs/`
- **Self Healing日志**: `output/self_healing_log.json`

### 调试模式
启动时添加调试参数：
```bash
python app/web/web_server.py --debug
```

### 联系支持
- **项目文档**: `README.md`
- **配置示例**: `.env.example`
- **演示脚本**: `demo_enterprise_platform.py`

---

🎉 **享受AI Test Platform带来的智能化测试体验！**