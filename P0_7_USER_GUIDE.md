# P0-7 Swagger 接入工作台使用指南

**版本**: 1.0  
**更新日期**: 2024-03-24

---

## 🚀 快速开始

### 1. 启动服务

#### 启动后端
```bash
cd ai-test-platform
py backend_api_server.py
```
后端地址: `http://localhost:8000`

#### 启动前端
```bash
cd ai-test-platform/frontend
npm run dev
```
前端地址: `http://localhost:5173`

### 2. 访问工作台

打开浏览器访问: `http://localhost:5173/swagger-workbench`

---

## 📖 使用流程

### 步骤 1: 选择项目

从下拉列表中选择要导入 Swagger 的项目。

如果没有项目，请先访问"项目列表"页面创建项目。

### 步骤 2: 导入 Swagger

#### 方式 A: 从 URL 导入

1. 选择"从 URL 导入"
2. 输入 Swagger URL，例如：
   ```
   https://petstore.swagger.io/v2/swagger.json
   ```
3. 点击"开始导入"

#### 方式 B: 从文件导入

1. 选择"从文件导入"
2. 点击选择文件，上传本地 Swagger 文件（支持 .json 和 .yaml）
3. 点击"开始导入"

### 步骤 3: 查看导入结果

导入成功后，页面会显示：
- API 规范 ID
- API 数量
- 生成的测试用例数量
- API 版本
- 生成的测试用例 ID 列表

### 步骤 4: 查看测试用例

系统会自动加载生成的测试用例，显示：
- 用例 ID
- 标题
- 模块
- 优先级
- 数据类型

### 步骤 5: 执行测试

1. 点击"开始执行测试"按钮
2. 系统会执行前 10 个测试用例
3. 执行开始后，自动跳转到执行详情页
4. 在执行详情页可以查看实时执行状态和结果

---

## 💡 使用技巧

### 推荐的 Swagger 示例

#### 公开 API 示例
- Petstore: `https://petstore.swagger.io/v2/swagger.json`
- JSONPlaceholder: `https://jsonplaceholder.typicode.com/swagger.json`（如果有）

#### 本地文件示例
项目中提供了示例文件：
- `examples/sample_swagger.json`
- `examples/new_swagger.json`

### 测试用例生成规则

系统会为每个 API 接口生成多个测试用例：
- 正常场景（valid data）
- 边界场景（boundary data）
- 异常场景（invalid data）

### 执行限制

为了避免执行时间过长，当前版本限制：
- 单次执行最多 10 个测试用例
- 如需执行更多，可以在"执行记录"页面创建新的执行任务

---

## ❓ 常见问题

### Q1: 导入失败怎么办？

检查以下几点：
1. URL 是否可访问（可以在浏览器中直接打开测试）
2. Swagger 文件格式是否正确（JSON 或 YAML）
3. 网络连接是否正常
4. 后端服务是否正常运行

### Q2: 没有生成测试用例？

可能原因：
1. Swagger 文件中没有定义 API 接口
2. 导入时未勾选"自动生成测试用例"（默认勾选）
3. 后端 AI 服务未配置或不可用

解决方法：
- 检查 Swagger 文件内容
- 查看后端日志确认错误信息
- 可以手动触发生成：使用"重新生成测试用例"功能

### Q3: 执行测试没有反应？

检查：
1. 是否有生成的测试用例
2. 后端执行引擎是否正常
3. 查看浏览器控制台是否有错误信息

### Q4: 如何查看历史执行记录？

点击侧边栏的"执行记录(V2)"，可以查看所有历史执行记录。

---

## 🔧 高级功能

### 重新生成测试用例

如果对生成的测试用例不满意，可以：
1. 调用 API: `POST /api/v2/swagger/generate-test-cases`
2. 传入 `api_spec_id` 重新生成

### 查看 API 规范详情

调用 API: `GET /api/v2/swagger/api-specs/{api_spec_id}`

### 删除 API 规范

调用 API: `DELETE /api/v2/swagger/api-specs/{api_spec_id}`

---

## 📞 技术支持

### 查看日志

#### 后端日志
后端运行时会在控制台输出详细日志，包括：
- API 请求信息
- Swagger 解析过程
- 测试用例生成过程
- 执行状态

#### 前端日志
打开浏览器开发者工具（F12），查看 Console 标签页。

### 验证系统状态

运行验证脚本：
```bash
cd ai测试
py verify_p0_7_status.py
```

### 测试后端 API

运行测试脚本：
```bash
cd ai-test-platform
py test_p0_6_swagger_import.py
```

---

## 📚 相关文档

- `P0_7_SWAGGER_WORKBENCH_COMPLETE.md` - 完成报告
- `SWAGGER_UPLOAD_GUIDE.md` - Swagger 上传指南
- `ai-test-platform/routes/swagger_routes.py` - API 路由定义
- `ai-test-platform/services/swagger_service.py` - 服务实现

---

## 🎯 下一步

完成 Swagger 接入后，你可以：

1. 在"执行记录"页面查看执行历史
2. 在"测试数据工厂"配置测试数据
3. 在"数据集管理"管理测试数据集
4. 使用"快速执行测试"进行临时测试

---

**祝使用愉快！** 🎉
