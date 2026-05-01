# 本地Mock模式运行指南

## 概述

AI Test Platform 支持两种运行模式：
- **Mock模式**：使用httpbin.org等公开API进行本地测试，不依赖真实项目
- **Real模式**：连接真实被测系统进行测试

本文档说明如何在本地使用Mock模式运行平台。

## 快速开始

### 1. 复制配置文件

```bash
cd ai-test-platform
cp .env.example .env
```

### 2. 确认Mock模式配置

打开 `.env` 文件，确认以下配置：

```bash
# 运行模式
APP_MODE=mock
USE_MOCK_DATA=true
MOCK_API_BASE_URL=https://httpbin.org

# AI配置（本地测试不需要AI）
AI_PROVIDER=none
AI_ANALYSIS_MODE=rule

# 超时配置
REQUEST_TIMEOUT=30
AI_ANALYSIS_TIMEOUT=60
```

### 3. 安装依赖

```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 安装后端依赖
pip install -r requirements.txt

# 安装前端依赖
cd frontend
npm install
cd ..
```

### 4. 启动服务

**启动后端**：
```bash
python backend_api_server.py
```

后端将运行在 `http://localhost:8000`

**启动前端**（新终端）：
```bash
cd frontend
npm run dev
```

前端将运行在 `http://localhost:5173` 或 `http://localhost:5174`

### 5. 运行验收测试

```bash
python scripts/smoke_p0_7_local.py
```

预期输出：
```
✅ PASS 健康检查
✅ PASS 项目列表
✅ PASS 环境列表
✅ PASS API规范列表
✅ PASS 测试用例列表
✅ PASS 执行记录列表
✅ PASS Dashboard摘要
✅ PASS 可观测性-执行列表

通过率: 100.0%
🎉 验收通过！平台核心功能正常
```

## 切换到Real模式

### 1. 修改.env配置

```bash
# 运行模式
APP_MODE=real
USE_MOCK_DATA=false

# 真实API配置
TARGET_API_BASE_URL=https://your-real-api.com
TARGET_API_TOKEN=your_real_token_here

# AI配置（可选）
AI_PROVIDER=deepseek  # 或 openai/ollama
AI_ANALYSIS_MODE=ai
```

### 2. 重启服务

重启后端服务以加载新配置。

### 3. 验证连接

```bash
curl -H "Authorization: Bearer $TARGET_API_TOKEN" $TARGET_API_BASE_URL/health
```

## 配置说明

### .env.example 字段说明

| 字段 | 说明 | Mock模式 | Real模式 |
|------|------|---------|---------|
| APP_MODE | 运行模式 | mock | real |
| USE_MOCK_DATA | 是否使用Mock数据 | true | false |
| MOCK_API_BASE_URL | Mock API地址 | https://httpbin.org | - |
| TARGET_API_BASE_URL | 真实API地址 | - | 填写真实地址 |
| TARGET_API_TOKEN | 真实API Token | - | 填写真实Token |
| AI_PROVIDER | AI提供商 | none | deepseek/openai/ollama |
| AI_ANALYSIS_MODE | 分析模式 | rule | ai/hybrid |
| REQUEST_TIMEOUT | 请求超时(秒) | 30 | 30 |
| AI_ANALYSIS_TIMEOUT | AI分析超时(秒) | 60 | 60 |

## 注意事项

### ⚠️ 不要提交.env文件

`.env` 文件包含敏感配置，已在 `.gitignore` 中排除。

**永远不要**：
- 提交 `.env` 文件到Git
- 在 `.env` 中写入真实Token
- 在代码中硬编码真实API地址

### ✅ 安全实践

1. 使用 `.env.example` 作为模板
2. 真实配置仅保存在本地 `.env`
3. 团队成员各自维护自己的 `.env`
4. 生产环境使用环境变量或密钥管理服务

## 故障排查

### 问题1：后端启动失败

**症状**：`pydantic` 版本冲突

**解决**：使用虚拟环境
```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### 问题2：前端路由404

**症状**：访问 `/api-specs` 返回404

**解决**：检查 `frontend/vite.config.js` 中的proxy配置
```javascript
proxy: {
  '/api/': {  // 注意末尾的斜杠
    target: 'http://127.0.0.1:8000',
    // ...
  }
}
```

### 问题3：环境列表405

**症状**：GET `/api/v2/environments` 返回405

**解决**：确保后端已更新到最新版本，包含环境列表接口。

### 问题4：AI分析超时

**症状**：AI分析请求超时

**解决**：Mock模式下使用规则分析
```bash
AI_PROVIDER=none
AI_ANALYSIS_MODE=rule
```

## 本地验收脚本

### 脚本位置
`scripts/smoke_p0_7_local.py`

### 运行方式
```bash
python scripts/smoke_p0_7_local.py
```

### 验收内容
- 8个核心接口
- 不依赖真实项目
- 不破坏数据库
- 输出彩色结果

### 通过标准
- 所有接口返回2xx
- 通过率 ≥ 85%

## 相关文档

- [项目README](../README.md)
- [环境配置示例](../.env.example)
- [P1增强报告](../P1_environment_field_analysis.md)
