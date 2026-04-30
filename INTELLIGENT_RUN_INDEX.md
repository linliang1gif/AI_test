# 智能执行功能 - 文档索引

## 📚 文档导航

### 🚀 快速开始
- **[快速启动指南](./QUICK_START_GUIDE.md)** - 5分钟快速体验智能执行功能

### 📋 完整报告
- **[功能完成报告](./INTELLIGENT_RUN_COMPLETE.md)** - 详细的功能说明和技术实现
- **[上下文转移总结](./CONTEXT_TRANSFER_SUMMARY.md)** - 任务完成状态和关键信息

### 🧪 测试工具
- **[前端功能测试](./test_intelligent_run_frontend.py)** - 自动化测试脚本
- **[Pipeline测试](./test_intelligent_pipeline.py)** - 后端Pipeline测试
- **[真实Pipeline端到端测试](./test_real_pipeline.py)** - 完整流程验证 (Swagger → 执行 → 报告)

### 📖 技术文档
- **[Pipeline V2 总结](./PIPELINE_V2_SUMMARY.md)** - Pipeline架构说明
- **[API文档](./INTELLIGENT_PIPELINE_API.md)** - API接口详细说明
- **[真实Pipeline测试指南](./REAL_PIPELINE_TEST_GUIDE.md)** - 端到端测试说明

## 🗂️ 文件结构

```
ai测试/
├── INTELLIGENT_RUN_INDEX.md          # 📍 当前文件 - 文档索引
├── QUICK_START_GUIDE.md              # 🚀 快速启动指南
├── INTELLIGENT_RUN_COMPLETE.md       # 📋 功能完成报告
├── CONTEXT_TRANSFER_SUMMARY.md       # 📝 上下文转移总结
├── REAL_PIPELINE_TEST_GUIDE.md       # 📖 真实Pipeline测试指南
├── test_intelligent_run_frontend.py  # 🧪 前端功能测试
├── test_intelligent_pipeline.py      # 🧪 Pipeline测试
├── test_real_pipeline.py             # 🧪 真实Pipeline端到端测试
│
└── ai-test-platform/
    ├── backend_api_server.py         # 🔧 后端API服务器
    │   └── POST /api/v2/test/run-intelligent (第3054行)
    │
    └── frontend/
        ├── src/
        │   ├── services/
        │   │   └── api.js            # 🔌 API服务层
        │   │       └── api.pipeline.runIntelligent()
        │   │
        │   └── pages/
        │       └── TestCasesList.jsx # 🎨 测试用例列表页
        │           └── 智能执行按钮 + 进度显示
        │
        └── vite.config.js            # ⚙️ Vite配置
```

## 🎯 按场景查找

### 场景 1: 我想快速体验功能
👉 阅读 [快速启动指南](./QUICK_START_GUIDE.md)

### 场景 2: 我想了解技术实现
👉 阅读 [功能完成报告](./INTELLIGENT_RUN_COMPLETE.md)

### 场景 3: 我想运行完整的端到端测试
👉 运行 `py test_real_pipeline.py`

### 场景 4: 我想运行前端功能测试
👉 运行 `py test_intelligent_run_frontend.py`

### 场景 5: 我想查看API接口
👉 阅读 [API文档](./INTELLIGENT_PIPELINE_API.md)

### 场景 6: 我想了解Pipeline架构
👉 阅读 [Pipeline V2 总结](./PIPELINE_V2_SUMMARY.md)

### 场景 7: 我想查看任务完成状态
👉 阅读 [上下文转移总结](./CONTEXT_TRANSFER_SUMMARY.md)

## 🔍 按文件类型查找

### 📄 Markdown 文档
- `INTELLIGENT_RUN_INDEX.md` - 文档索引
- `QUICK_START_GUIDE.md` - 快速启动
- `INTELLIGENT_RUN_COMPLETE.md` - 完整报告
- `CONTEXT_TRANSFER_SUMMARY.md` - 任务总结
- `REAL_PIPELINE_TEST_GUIDE.md` - 端到端测试指南
- `PIPELINE_V2_SUMMARY.md` - Pipeline架构
- `INTELLIGENT_PIPELINE_API.md` - API文档

### 🐍 Python 脚本
- `test_intelligent_run_frontend.py` - 前端测试
- `test_intelligent_pipeline.py` - Pipeline测试
- `test_real_pipeline.py` - 端到端测试

### 💻 源代码
- `backend_api_server.py` - 后端服务器
- `api.js` - API服务层
- `TestCasesList.jsx` - 测试用例列表页

## 📊 功能模块

### 1. 后端 Pipeline
- **文件**: `backend_api_server.py`
- **接口**: `POST /api/v2/test/run-intelligent`
- **模块**:
  - Intelligence Agent - 智能分析
  - Execution Engine - 测试执行
  - Healing Engine - 自动修复
  - Report Generator - 报告生成

### 2. 前端 API 层
- **文件**: `api.js`
- **方法**: `api.pipeline.runIntelligent()`
- **功能**: 统一API调用接口

### 3. 前端 UI
- **文件**: `TestCasesList.jsx`
- **组件**:
  - 智能执行按钮
  - 实时进度显示
  - 执行结果展示

## 🧪 测试验证

### 运行前端测试
```bash
cd ai测试
py test_intelligent_run_frontend.py
```

### 运行Pipeline测试
```bash
cd ai测试
py test_intelligent_pipeline.py
```

### 运行端到端测试
```bash
cd ai测试
py test_real_pipeline.py
```

## 🚀 启动服务

### 后端服务
```bash
cd ai-test-platform
py backend_api_server.py
```
访问: `http://localhost:8000`

### 前端服务
```bash
cd ai-test-platform/frontend
npm run dev
```
访问: `http://localhost:5173`

## 📝 更新日志

### 2024-03-24
- ✅ 完成智能执行Pipeline API
- ✅ 完成前端智能执行按钮
- ✅ 完成实时进度显示
- ✅ 完成自动页面跳转
- ✅ 创建测试脚本
- ✅ 编写完整文档

## 🎉 快速链接

| 文档 | 用途 | 链接 |
|------|------|------|
| 快速启动 | 5分钟体验 | [QUICK_START_GUIDE.md](./QUICK_START_GUIDE.md) |
| 完整报告 | 详细说明 | [INTELLIGENT_RUN_COMPLETE.md](./INTELLIGENT_RUN_COMPLETE.md) |
| 任务总结 | 完成状态 | [CONTEXT_TRANSFER_SUMMARY.md](./CONTEXT_TRANSFER_SUMMARY.md) |
| 端到端测试 | 完整验证 | [test_real_pipeline.py](./test_real_pipeline.py) |
| 前端测试 | 功能验证 | [test_intelligent_run_frontend.py](./test_intelligent_run_frontend.py) |
| Pipeline测试 | 后端验证 | [test_intelligent_pipeline.py](./test_intelligent_pipeline.py) |

## 💡 提示

- 📖 建议先阅读快速启动指南
- 🧪 运行测试脚本验证功能
- 📋 查看完整报告了解技术细节
- 🔍 使用本索引快速定位文档

## 🆘 需要帮助?

1. 查看 [快速启动指南](./QUICK_START_GUIDE.md) 的常见问题部分
2. 运行测试脚本检查系统状态
3. 查看完整报告了解详细实现

---

**最后更新**: 2024-03-24  
**版本**: 1.0.0  
**状态**: ✅ 已完成
