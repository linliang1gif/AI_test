# P0-6: 补齐平台验收必需模块

## 当前结论修正

- ✅ 已完成 V2 执行闭环
- ✅ 可进行阶段性 MVP 验收
- ❌ 尚不具备完整平台验收条件

## 原因分析

当前前端只暴露了:
- 数据集管理
- 测试数据工厂
- 执行记录(V2)
- 快速执行测试

这些模块只能覆盖"数据准备 + 执行触发 + 结果观测",无法覆盖完整平台能力。

## 必需补齐的 4 个模块

### 1. 项目管理(V2)
**功能**:
- 项目列表(查询/搜索/分页)
- 创建项目(名称/描述/团队)
- 查看项目详情(基本信息/环境列表/统计数据)
- 编辑项目
- 删除项目

**后端 API 状态**: ✅ 已实现
- GET `/api/v2/projects`
- POST `/api/v2/projects`
- GET `/api/v2/projects/{id}`
- PUT `/api/v2/projects/{id}`
- DELETE `/api/v2/projects/{id}`
- GET `/api/v2/projects/{id}/environments`

**前端页面**: ❌ 需新建
- `pages/ProjectsV2.jsx` - 项目列表页
- `pages/ProjectDetailV2.jsx` - 项目详情页
- `components/ProjectForm.jsx` - 项目表单组件

### 2. 环境管理 + 鉴权配置
**功能**:
- 环境列表(按项目)
- 创建环境(名称/base_url/timeout/retry)
- 编辑环境
- 删除环境
- 配置鉴权(类型选择/参数配置)
- 鉴权类型: None/API Key/Bearer Token/Basic Auth/OAuth2

**后端 API 状态**: ✅ 已实现
- POST `/api/v2/environments`
- GET `/api/v2/environments/{id}`
- PUT `/api/v2/environments/{id}`
- DELETE `/api/v2/environments/{id}`
- POST `/api/v2/auth-profiles`
- GET `/api/v2/auth-profiles/{id}`
- PUT `/api/v2/auth-profiles/{id}`
- DELETE `/api/v2/auth-profiles/{id}`

**前端页面**: ❌ 需新建
- `pages/EnvironmentsV2.jsx` - 环境管理页(集成在项目详情中)
- `components/EnvironmentForm.jsx` - 环境表单组件
- `components/AuthConfigForm.jsx` - 鉴权配置组件

### 3. Swagger / API 管理
**功能**:
- 导入 Swagger/OpenAPI(文件上传/URL导入)
- API 规范列表
- 查看 API 规范详情
- 与项目/环境绑定
- 解析并展示 API 列表

**后端 API 状态**: ❌ 需实现
- POST `/api/v2/api-specs/import-file` - 文件上传导入
- POST `/api/v2/api-specs/import-url` - URL 导入
- GET `/api/v2/api-specs` - 获取规范列表
- GET `/api/v2/api-specs/{id}` - 获取规范详情
- GET `/api/v2/api-specs/{id}/apis` - 获取 API 列表
- DELETE `/api/v2/api-specs/{id}` - 删除规范

**前端页面**: ❌ 需新建
- `pages/ApiSpecsV2.jsx` - API 规范列表页
- `pages/ApiSpecDetailV2.jsx` - API 规范详情页
- `components/SwaggerImport.jsx` - Swagger 导入组件

**后端需新增**:
- `database/models.py` - ApiSpec 表模型
- `services/api_spec_service.py` - API 规范服务
- `routes/api_spec_routes.py` - API 规范路由
- 集成 `modules.swagger.SwaggerTestCaseGenerator`

### 4. 测试用例管理
**功能**:
- 测试用例列表(按项目/API)
- 从 Swagger 生成用例
- 手动创建用例
- 编辑用例
- 删除用例
- 从用例页触发执行

**后端 API 状态**: ❌ 需实现
- POST `/api/v2/test-cases/generate-from-swagger` - 从 Swagger 生成
- POST `/api/v2/test-cases` - 创建用例
- GET `/api/v2/test-cases` - 获取用例列表
- GET `/api/v2/test-cases/{id}` - 获取用例详情
- PUT `/api/v2/test-cases/{id}` - 更新用例
- DELETE `/api/v2/test-cases/{id}` - 删除用例
- POST `/api/v2/test-cases/{id}/execute` - 执行单个用例

**前端页面**: ❌ 需新建
- `pages/TestCasesV2.jsx` - 测试用例列表页
- `pages/TestCaseDetailV2.jsx` - 测试用例详情页
- `components/TestCaseForm.jsx` - 测试用例表单组件
- `components/TestCaseGenerator.jsx` - 用例生成组件

**后端需新增**:
- `database/models.py` - TestCase 表模型
- `services/test_case_service.py` - 测试用例服务
- `routes/test_case_routes.py` - 测试用例路由
- 集成 `modules.swagger.SwaggerTestCaseGenerator`

## 优先级排序

### P0-6.1: 项目管理(V2) - 最高优先级
**原因**: 后端 API 已完整,只需前端页面,最快完成

**工作量**: 2-3 小时
- 创建 ProjectsV2.jsx (1h)
- 创建 ProjectDetailV2.jsx (1h)
- 创建 ProjectForm.jsx (30min)
- 集成到 App.jsx 路由 (15min)
- 测试验证 (15min)

### P0-6.2: 环境管理 + 鉴权配置 - 高优先级
**原因**: 后端 API 已完整,只需前端页面,依赖项目管理

**工作量**: 2-3 小时
- 创建 EnvironmentForm.jsx (1h)
- 创建 AuthConfigForm.jsx (1h)
- 集成到 ProjectDetailV2.jsx (30min)
- 测试验证 (30min)

### P0-6.3: Swagger / API 管理 - 中优先级
**原因**: 需要后端 API + 前端页面,工作量较大

**工作量**: 4-5 小时
- 后端: ApiSpec 模型 + Service + Routes (2h)
- 前端: ApiSpecsV2.jsx + SwaggerImport.jsx (2h)
- 集成 SwaggerTestCaseGenerator (30min)
- 测试验证 (30min)

### P0-6.4: 测试用例管理 - 中优先级
**原因**: 需要后端 API + 前端页面,依赖 Swagger 管理

**工作量**: 4-5 小时
- 后端: TestCase 模型 + Service + Routes (2h)
- 前端: TestCasesV2.jsx + TestCaseForm.jsx (2h)
- 集成用例生成和执行 (30min)
- 测试验证 (30min)

## 总工作量估算

- P0-6.1: 2-3 小时
- P0-6.2: 2-3 小时
- P0-6.3: 4-5 小时
- P0-6.4: 4-5 小时

**总计**: 12-16 小时

## 后端缺失接口清单

### Swagger / API 管理
```python
# routes/api_spec_routes.py

POST /api/v2/api-specs/import-file
  - 参数: file (UploadFile), project_id, environment_id
  - 返回: ApiSpec 对象

POST /api/v2/api-specs/import-url
  - 参数: url, project_id, environment_id
  - 返回: ApiSpec 对象

GET /api/v2/api-specs
  - 参数: project_id (可选), skip, limit
  - 返回: List[ApiSpec]

GET /api/v2/api-specs/{id}
  - 返回: ApiSpec 详情

GET /api/v2/api-specs/{id}/apis
  - 返回: 解析后的 API 列表

DELETE /api/v2/api-specs/{id}
  - 返回: 成功/失败
```

### 测试用例管理
```python
# routes/test_case_routes.py

POST /api/v2/test-cases/generate-from-swagger
  - 参数: api_spec_id, generation_strategy
  - 返回: List[TestCase]

POST /api/v2/test-cases
  - 参数: TestCaseCreate
  - 返回: TestCase 对象

GET /api/v2/test-cases
  - 参数: project_id, api_spec_id, skip, limit
  - 返回: List[TestCase]

GET /api/v2/test-cases/{id}
  - 返回: TestCase 详情

PUT /api/v2/test-cases/{id}
  - 参数: TestCaseUpdate
  - 返回: TestCase 对象

DELETE /api/v2/test-cases/{id}
  - 返回: 成功/失败

POST /api/v2/test-cases/{id}/execute
  - 参数: environment_id
  - 返回: TestRun 对象
```

## 数据库表设计

### ApiSpec 表
```python
class ApiSpec(Base):
    __tablename__ = "api_specs"
    
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id"))
    name = Column(String(200))
    description = Column(Text)
    spec_type = Column(String(50))  # swagger_2, openapi_3
    spec_content = Column(Text)  # JSON 格式
    source_type = Column(String(50))  # file, url
    source_value = Column(String(500))
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
```

### TestCase 表
```python
class TestCase(Base):
    __tablename__ = "test_cases"
    
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id"))
    api_spec_id = Column(Integer, ForeignKey("api_specs.id"))
    name = Column(String(200))
    description = Column(Text)
    method = Column(String(10))  # GET, POST, PUT, DELETE
    path = Column(String(500))
    headers = Column(Text)  # JSON
    query_params = Column(Text)  # JSON
    body = Column(Text)  # JSON
    expected_status = Column(Integer)
    expected_response = Column(Text)  # JSON
    assertions = Column(Text)  # JSON
    priority = Column(String(20))  # high, medium, low
    tags = Column(String(500))
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
```

## 前端路由规划

```jsx
// App.jsx 新增路由

// 项目管理
<Route path="/projects-v2" element={<ProjectsV2 />} />
<Route path="/projects-v2/:id" element={<ProjectDetailV2 />} />

// API 规范管理
<Route path="/api-specs-v2" element={<ApiSpecsV2 />} />
<Route path="/api-specs-v2/:id" element={<ApiSpecDetailV2 />} />

// 测试用例管理
<Route path="/test-cases-v2" element={<TestCasesV2 />} />
<Route path="/test-cases-v2/:id" element={<TestCaseDetailV2 />} />
```

## 前端菜单规划

```jsx
// App.jsx 菜单更新

{/* 项目管理分组 */}
<div>
  <button>项目管理</button>
  {expandedSections.projects && [
    { to: '/projects-v2', label: '项目列表' },
    { to: '/api-specs-v2', label: 'API规范' },
    { to: '/test-cases-v2', label: '测试用例' },
  ].map(item => ...)}
</div>

{/* 执行管理分组 */}
<div>
  <button>执行管理</button>
  {expandedSections.execution && [
    { to: '/test-runs-v2', label: '执行记录' },
    { to: '/quick-execution-test', label: '快速执行' },
  ].map(item => ...)}
</div>

{/* 数据管理分组 */}
<div>
  <button>数据管理</button>
  {expandedSections.data && [
    { to: '/dataset-management', label: '数据集管理' },
    { to: '/test-data-factory', label: '测试数据工厂' },
  ].map(item => ...)}
</div>
```

## P0-6.1 实施计划: 项目管理(V2)

### 步骤 1: 创建 ProjectsV2.jsx (1h)
**功能**:
- 项目列表展示(卡片或表格)
- 搜索/过滤
- 创建项目按钮
- 查看详情链接
- 删除项目

**API 调用**:
- `api.v2.projects.getAll()`
- `api.v2.projects.create()`
- `api.v2.projects.delete()`

### 步骤 2: 创建 ProjectDetailV2.jsx (1h)
**功能**:
- 项目基本信息展示
- 编辑项目
- 环境列表(Tab 页)
- 统计数据(用例数/执行数)

**API 调用**:
- `api.v2.projects.get(id)`
- `api.v2.projects.update(id, data)`
- `api.v2.projects.getEnvironments(id)`

### 步骤 3: 创建 ProjectForm.jsx (30min)
**功能**:
- 项目名称输入
- 项目描述输入
- 团队选择
- 表单验证

### 步骤 4: 集成到 App.jsx (15min)
- 添加路由
- 添加菜单项
- 导入组件

### 步骤 5: 测试验证 (15min)
- 创建项目
- 查看项目列表
- 查看项目详情
- 编辑项目
- 删除项目

## 开始执行

现在开始执行 P0-6.1: 项目管理(V2)
