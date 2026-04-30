# Pipeline V2 智能执行系统 - 文档索引

## 📚 快速导航

### 🚀 快速开始
- **[快速启动指南](./QUICK_START_INTELLIGENT_PIPELINE.md)** - 5分钟快速上手
- **[测试脚本](./test_intelligent_pipeline.py)** - 一键测试工具

### 📖 核心文档
- **[API完整文档](./INTELLIGENT_PIPELINE_API.md)** - 详细的API说明
- **[完成报告](./INTELLIGENT_PIPELINE_COMPLETE.md)** - 实现细节和流程
- **[总结报告](./PIPELINE_V2_SUMMARY.md)** - 项目总结和成果

### 🔧 实现文件
- **[后端API](./ai-test-platform/backend_api_server.py)** - 后端实现代码
- **[前端API](./ai-test-platform/frontend/src/services/api.js)** - 前端集成代码

### 📊 相关模块文档
- **[Intelligence Agent](./INTELLIGENCE_ARCHITECTURE_SUMMARY.md)** - 智能决策引擎
- **[Execution Engine](./EXECUTION_ENGINE_COMPLETE.md)** - 执行引擎
- **[Healing Engine](./RESILIENCE_ENGINE_COMPLETE.md)** - 自动修复引擎
- **[Report Generator](./PROJECT_COMPLETE_SUMMARY.md)** - 报告生成器

## 🎯 按角色查看

### 开发者
1. [快速启动指南](./QUICK_START_INTELLIGENT_PIPELINE.md) - 了解如何使用
2. [API完整文档](./INTELLIGENT_PIPELINE_API.md) - 查看API接口
3. [后端实现](./ai-test-platform/backend_api_server.py) - 查看代码实现

### 测试人员
1. [快速启动指南](./QUICK_START_INTELLIGENT_PIPELINE.md) - 学习如何测试
2. [测试脚本](./test_intelligent_pipeline.py) - 使用测试工具
3. [API文档](./INTELLIGENT_PIPELINE_API.md) - 了解功能

### 架构师
1. [总结报告](./PIPELINE_V2_SUMMARY.md) - 了解整体架构
2. [完成报告](./INTELLIGENT_PIPELINE_COMPLETE.md) - 查看实现细节
3. [相关模块文档](#-相关模块文档) - 深入各个模块

### 产品经理
1. [总结报告](./PIPELINE_V2_SUMMARY.md) - 了解功能和价值
2. [快速启动指南](./QUICK_START_INTELLIGENT_PIPELINE.md) - 体验功能
3. [API文档](./INTELLIGENT_PIPELINE_API.md) - 了解能力

## 📋 按主题查看

### 功能说明
- [API完整文档](./INTELLIGENT_PIPELINE_API.md) - 完整功能说明
- [总结报告](./PIPELINE_V2_SUMMARY.md) - 核心功能总结

### 使用指南
- [快速启动指南](./QUICK_START_INTELLIGENT_PIPELINE.md) - 快速上手
- [API文档 - 测试方法](./INTELLIGENT_PIPELINE_API.md#-测试方法) - 详细使用方法

### 技术实现
- [完成报告](./INTELLIGENT_PIPELINE_COMPLETE.md) - 实现细节
- [后端代码](./ai-test-platform/backend_api_server.py) - 源代码
- [前端代码](./ai-test-platform/frontend/src/services/api.js) - 前端集成

### 测试验证
- [测试脚本](./test_intelligent_pipeline.py) - 自动化测试
- [完成报告 - 测试验证](./INTELLIGENT_PIPELINE_COMPLETE.md#-测试验证) - 测试场景

## 🔍 常见问题

### Q1: 如何快速开始?
**A**: 查看 [快速启动指南](./QUICK_START_INTELLIGENT_PIPELINE.md)

### Q2: API接口是什么?
**A**: `POST /api/v2/test/run-intelligent`，详见 [API文档](./INTELLIGENT_PIPELINE_API.md)

### Q3: 如何测试?
**A**: 运行 `py test_intelligent_pipeline.py`，详见 [测试脚本](./test_intelligent_pipeline.py)

### Q4: 支持哪些功能?
**A**: 智能决策、真实执行、自动修复、报告生成，详见 [总结报告](./PIPELINE_V2_SUMMARY.md)

### Q5: 如何集成到前端?
**A**: 使用 `api.pipeline.runIntelligent()`，详见 [API文档 - 前端集成](./INTELLIGENT_PIPELINE_API.md#-前端集成示例)

## 📊 文档结构

```
Pipeline V2 文档
├── PIPELINE_V2_INDEX.md (本文档)
│   └── 文档索引和导航
│
├── QUICK_START_INTELLIGENT_PIPELINE.md
│   └── 5分钟快速启动指南
│
├── INTELLIGENT_PIPELINE_API.md
│   ├── API接口说明
│   ├── 请求/响应格式
│   ├── 数据结构
│   ├── 测试方法
│   └── 前端集成示例
│
├── INTELLIGENT_PIPELINE_COMPLETE.md
│   ├── 实现内容
│   ├── 执行流程
│   ├── 数据流转
│   └── 测试验证
│
├── PIPELINE_V2_SUMMARY.md
│   ├── 完成清单
│   ├── 架构图
│   ├── 核心功能
│   ├── 技术亮点
│   └── 未来规划
│
└── test_intelligent_pipeline.py
    └── 自动化测试脚本
```

## 🎯 学习路径

### 初级 (1小时)
1. 阅读 [快速启动指南](./QUICK_START_INTELLIGENT_PIPELINE.md)
2. 运行 [测试脚本](./test_intelligent_pipeline.py)
3. 查看测试结果

### 中级 (3小时)
1. 阅读 [API完整文档](./INTELLIGENT_PIPELINE_API.md)
2. 理解请求/响应格式
3. 尝试curl测试
4. 查看前端集成示例

### 高级 (1天)
1. 阅读 [完成报告](./INTELLIGENT_PIPELINE_COMPLETE.md)
2. 理解执行流程和数据流转
3. 查看 [后端代码](./ai-test-platform/backend_api_server.py)
4. 阅读各模块文档
5. 尝试修改和扩展

## 🔗 相关链接

### 内部文档
- [项目总结](./PROJECT_COMPLETE_SUMMARY.md)
- [架构说明](./AI测试项目完整架构说明.md)
- [前端优化报告](./ai-test-platform/frontend/FRONTEND_OPTIMIZATION_FINAL_REPORT.md)
- [API迁移报告](./ai-test-platform/frontend/API_MIGRATION_COMPLETE.md)

### 外部资源
- [FastAPI文档](https://fastapi.tiangolo.com/)
- [React文档](https://react.dev/)
- [Python文档](https://docs.python.org/3/)

## 📞 支持

### 遇到问题?
1. 查看 [常见问题](#-常见问题)
2. 查看后端日志
3. 运行测试脚本诊断
4. 查看 [API文档 - 错误处理](./INTELLIGENT_PIPELINE_API.md#-错误处理)

### 需要帮助?
- 查看完整文档
- 运行测试脚本
- 查看示例代码

## 🎉 开始使用

**推荐路径**:
1. 📖 阅读 [快速启动指南](./QUICK_START_INTELLIGENT_PIPELINE.md)
2. 🧪 运行 [测试脚本](./test_intelligent_pipeline.py)
3. 📚 查看 [API文档](./INTELLIGENT_PIPELINE_API.md)
4. 🚀 开始集成到项目

---

**版本**: v2.0
**更新时间**: 2026-04-18
**状态**: ✅ 完整
