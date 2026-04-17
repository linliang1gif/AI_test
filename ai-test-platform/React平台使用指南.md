# AI Test Engineer Platform - React版使用指南

## 🎯 项目概述

AI Test Engineer Platform 是一个现代化的企业级AI测试工程师工作台，采用 React + FastAPI 架构，提供完整的AI驱动测试解决方案。

### 🏗️ 技术架构

**前端 (Frontend)**
- React 18 + Vite
- TailwindCSS + shadcn/ui
- React Router
- Axios (API调用)
- Lucide React (图标)

**后端 (Backend)**
- FastAPI
- Python 3.8+
- Pydantic (数据验证)
- Uvicorn (ASGI服务器)

## 🚀 快速启动

### 1. 环境要求

```bash
# Node.js (推荐 LTS 版本)
node --version  # >= 16.0.0
npm --version   # >= 8.0.0

# Python
python --version  # >= 3.8.0
```

### 2. 安装依赖

```bash
# 安装前端依赖
cd frontend
npm install

# 安装后端依赖 (如果需要)
pip install fastapi uvicorn python-multipart
```

### 3. 启动服务

**方式一：使用启动器 (推荐)**
```bash
python start_react_platform.py
```

**方式二：手动启动**
```bash
# 终端1: 启动后端API
python backend_api_server.py

# 终端2: 启动前端开发服务器
cd frontend
npm run dev
```

### 4. 访问地址

- 🌐 **前端界面**: http://localhost:3000
- 🔗 **后端API**: http://127.0.0.1:8080
- 📖 **API文档**: http://127.0.0.1:8080/docs

## 📱 功能模块

### 1. Dashboard (仪表板)
- 📊 实时测试统计
- 📈 测试趋势图表
- 🚨 失败测试警报
- ⚡ 系统状态监控

### 2. Projects (项目管理)
- 📁 创建和管理测试项目
- 🌍 多环境支持 (dev/staging/prod)
- 🔧 项目配置管理
- 📊 项目统计信息

### 3. API Explorer (接口管理)
- 📄 Swagger/OpenAPI 自动解析
- 🔍 接口发现和管理
- 🧪 接口测试执行
- 📝 接口文档查看

### 4. Test Cases (测试用例库)
- 📋 测试用例管理
- 🔍 智能搜索和筛选
- 🤖 AI自动生成测试用例
- 📊 测试覆盖率分析

### 5. Automation (自动化脚本)
- 🤖 AI生成pytest脚本
- 📝 代码预览和编辑
- ⬇️ 脚本下载
- 🔄 脚本重新生成

### 6. Test Runs (测试执行)
- ▶️ 测试执行管理
- 📊 实时进度监控
- 📋 实时日志查看
- ⏸️ 测试暂停/停止

### 7. Reports (测试报告)
- 📊 多种报告类型
- 📈 测试趋势分析
- 📄 报告导出 (HTML/PDF/Excel)
- 📧 报告分享

### 8. AI Insights (AI分析中心)
- 🧠 AI Agent工作流可视化
- 🔄 端到端AI流程
- 📊 AI性能统计
- 🤖 智能分析建议

## 🎨 界面设计特色

### 现代企业级SaaS风格
- 🎨 **设计语言**: 现代简约，专业企业级
- 🎯 **用户体验**: 直观易用，工程师友好
- 📱 **响应式设计**: 完美适配桌面和移动设备
- 🌈 **视觉层次**: 清晰的信息架构和视觉引导

### 组件系统
- 🧩 **shadcn/ui**: 高质量UI组件库
- 🎨 **TailwindCSS**: 原子化CSS框架
- 🔧 **可定制**: 支持主题和样式定制
- ♿ **无障碍**: 遵循WCAG无障碍标准

## 🔧 开发指南

### 项目结构
```
frontend/
├── src/
│   ├── components/          # 组件
│   │   ├── ui/             # 基础UI组件
│   │   └── layout/         # 布局组件
│   ├── pages/              # 页面组件
│   ├── lib/                # 工具函数
│   ├── App.jsx             # 主应用
│   └── main.jsx            # 入口文件
├── public/                 # 静态资源
├── package.json            # 依赖配置
├── vite.config.js          # Vite配置
└── tailwind.config.js      # Tailwind配置
```

### 添加新页面
1. 在 `src/pages/` 创建新页面组件
2. 在 `App.jsx` 中添加路由
3. 在 `Sidebar.jsx` 中添加导航链接

### 添加新API
1. 在 `backend_api_server.py` 中添加新端点
2. 在前端页面中使用 `axios` 调用API
3. 处理加载状态和错误处理

## 🔌 API接口文档

### 核心API端点

**Dashboard**
- `GET /api/dashboard/stats` - 获取仪表板统计

**Projects**
- `GET /api/projects` - 获取项目列表
- `POST /api/projects` - 创建新项目
- `DELETE /api/projects/{id}` - 删除项目

**API Explorer**
- `GET /api/apis` - 获取API列表
- `POST /api/swagger/parse` - 解析Swagger文档

**Test Cases**
- `GET /api/test-cases` - 获取测试用例
- `POST /api/test-cases` - 创建测试用例

**Test Runs**
- `GET /api/test-runs` - 获取测试执行记录
- `POST /api/test-runs` - 启动测试执行

**Reports**
- `GET /api/reports` - 获取报告列表
- `GET /api/reports/{id}` - 获取报告详情

**AI Insights**
- `GET /api/ai/agents` - 获取AI代理状态
- `POST /api/ai/generate` - 启动AI生成

## 🛠️ 自定义配置

### 主题定制
编辑 `src/index.css` 中的CSS变量:
```css
:root {
  --primary: 221.2 83.2% 53.3%;
  --secondary: 210 40% 96%;
  /* 更多颜色变量... */
}
```

### API地址配置
编辑 `vite.config.js` 中的代理配置:
```javascript
server: {
  proxy: {
    '/api': {
      target: 'http://127.0.0.1:8080',
      changeOrigin: true,
    }
  }
}
```

## 🚀 部署指南

### 开发环境
```bash
# 前端开发服务器
npm run dev

# 后端开发服务器
python backend_api_server.py
```

### 生产环境
```bash
# 构建前端
npm run build

# 启动生产服务器
npm run preview

# 后端生产部署
uvicorn backend_api_server:app --host 0.0.0.0 --port 8080
```

## 🔍 故障排除

### 常见问题

**1. 前端无法连接后端**
- 检查后端服务器是否在 http://127.0.0.1:8080 运行
- 检查CORS配置是否正确
- 查看浏览器控制台错误信息

**2. 依赖安装失败**
```bash
# 清除npm缓存
npm cache clean --force

# 删除node_modules重新安装
rm -rf node_modules package-lock.json
npm install
```

**3. 端口冲突**
- 前端默认端口: 3000
- 后端默认端口: 8080
- 可在配置文件中修改端口

### 日志查看
- 前端: 浏览器开发者工具控制台
- 后端: 终端输出日志
- API调用: 网络面板查看请求响应

## 📞 技术支持

### 开发团队
- 🏗️ **架构设计**: AI测试平台架构师
- 💻 **前端开发**: React全栈工程师
- 🔧 **后端开发**: FastAPI工程师
- 🎨 **UI/UX设计**: 企业级界面设计师

### 更新日志
- **v1.0.0** (2024-03-14): 初始版本发布
  - ✅ 完整的React前端界面
  - ✅ FastAPI后端API
  - ✅ 8个核心功能模块
  - ✅ 现代企业级设计

---

🎉 **恭喜！** 您已成功部署AI Test Engineer Platform React版本！

这是一个现代化、专业级的AI测试工程师工作台，具备完整的企业级功能和优雅的用户界面。立即开始您的智能化测试之旅吧！