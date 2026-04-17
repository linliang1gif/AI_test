# 测试数据工厂前端集成指南

## 📋 需要完成的集成步骤

### 1. 添加API接口到后端 (backend_api_server.py)

在 `backend_api_server.py` 文件中添加以下内容:

#### 1.1 在文件顶部添加导入
```python
# 导入测试数据工厂
sys.path.insert(0, 'test_data')
from data_factory import factory
```

#### 1.2 添加数据模型 (在其他BaseModel定义之后)
```python
class DataGenerationRequest(BaseModel):
    data_type: str
    count: int = 1
    context: Optional[Dict[str, Any]] = None
    overrides: Optional[Dict[str, Any]] = None

class SmartGenerationRequest(BaseModel):
    field_name: str
    context: Optional[Dict[str, Any]] = None

class SmartObjectRequest(BaseModel):
    schema: Dict[str, str]
    context: Optional[Dict[str, Any]] = None

class QualityEvaluationRequest(BaseModel):
    data: Dict[str, Any]
    schema: Optional[Dict[str, Any]] = None

class BatchEvaluationRequest(BaseModel):
    data_list: List[Dict[str, Any]]
```

#### 1.3 添加API路由 (在现有路由之后)

参考 `add_test_data_apis.py` 文件中的完整API代码,添加以下路由:

- `POST /api/test-data/generate` - 生成测试数据
- `POST /api/test-data/smart-generate` - AI智能生成字段
- `POST /api/test-data/smart-object` - AI智能生成对象
- `POST /api/test-data/analyze-field` - 分析字段
- `POST /api/test-data/analyze-schema` - 分析Schema
- `GET /api/test-data/scenarios/{entity_type}` - 获取测试场景
- `POST /api/test-data/evaluate` - 评估数据质量
- `POST /api/test-data/batch-evaluate` - 批量评估
- `GET /api/test-data/templates` - 列出模板
- `POST /api/test-data/from-template` - 从模板生成
- `GET /api/test-data/stats` - 获取统计
- `GET /api/test-data/boundary-values/{data_type}` - 获取边界值
- `GET /api/test-data/invalid-values/{data_type}` - 获取非法值

### 2. 添加前端页面

#### 2.1 页面文件已创建
✅ `frontend/src/pages/TestDataFactory.jsx` - 测试数据工厂页面

#### 2.2 更新路由配置

在 `frontend/src/App.jsx` 中:

1. 添加导入:
```javascript
import TestDataFactory from './pages/TestDataFactory'
```

2. 在导航菜单中添加链接:
```javascript
<NavLink to="/test-data-factory" className={({ isActive }) => isActive ? 'active' : ''}>
  <span>🏭</span> 测试数据工厂
</NavLink>
```

3. 在Routes中添加路由:
```javascript
<Route path="/test-data-factory" element={<TestDataFactory />} />
```

### 3. 更新导航菜单

在 `frontend/src/App.jsx` 的导航部分添加:

```javascript
<nav className="sidebar">
  {/* 现有导航项 */}
  <NavLink to="/dashboard">📊 仪表板</NavLink>
  <NavLink to="/projects">📁 项目</NavLink>
  <NavLink to="/api-explorer">🔍 API探索</NavLink>
  <NavLink to="/test-cases">📝 测试用例</NavLink>
  <NavLink to="/automation">🤖 自动化</NavLink>
  <NavLink to="/test-runs">▶️ 测试执行</NavLink>
  <NavLink to="/reports">📈 报告</NavLink>
  <NavLink to="/ai-insights">🧠 AI洞察</NavLink>
  
  {/* 新增 */}
  <NavLink to="/test-data-factory">🏭 测试数据工厂</NavLink>
</nav>
```

### 4. 功能特性

前端页面包含以下功能:

#### 4.1 基础生成
- 选择数据类型(用户/订单/产品/地址/支付/库存)
- 设置生成数量
- 一键生成数据
- 数据质量评估

#### 4.2 AI智能生成
- 基于上下文的智能生成
- 自动识别字段类型
- 智能推荐数据值

#### 4.3 测试场景
- 查看推荐的测试场景
- 按实体类型分类
- 显示场景类型和优先级

#### 4.4 统计信息
- 生成次数统计
- 字段使用频率
- 实时数据展示

#### 4.5 模板管理
- 查看可用模板
- 从模板生成数据
- 模板列表展示

### 5. 测试步骤

#### 5.1 启动后端
```bash
cd ai测试/ai-test-platform
python backend_api_server.py
```

#### 5.2 启动前端
```bash
cd frontend
npm install  # 如果还没安装依赖
npm run dev
```

#### 5.3 访问页面
打开浏览器访问: `http://localhost:5173/test-data-factory`

#### 5.4 测试功能
1. 测试基础生成功能
2. 测试AI智能生成
3. 测试质量评估
4. 测试场景推荐
5. 查看统计信息

### 6. API测试

可以使用以下curl命令测试API:

```bash
# 生成用户数据
curl -X POST http://localhost:8000/api/test-data/generate \
  -H "Content-Type: application/json" \
  -d '{"data_type": "user", "count": 1}'

# AI智能生成
curl -X POST http://localhost:8000/api/test-data/smart-object \
  -H "Content-Type: application/json" \
  -d '{"schema": {"user_id": "string", "email": "string"}, "context": {"country": "CN"}}'

# 获取测试场景
curl http://localhost:8000/api/test-data/scenarios/user

# 获取统计信息
curl http://localhost:8000/api/test-data/stats
```

### 7. 样式优化 (可选)

如果需要自定义样式,可以在 `frontend/src/index.css` 中添加:

```css
/* 测试数据工厂页面样式 */
.test-data-factory {
  padding: 24px;
}

.test-data-factory .ant-card {
  margin-bottom: 16px;
}

.test-data-factory .quality-score {
  font-size: 24px;
  font-weight: bold;
}
```

### 8. 依赖检查

确保前端已安装必要的依赖:

```bash
cd frontend
npm install antd @ant-design/icons react-router-dom
```

### 9. 完成检查清单

- [ ] 后端API接口已添加
- [ ] 前端页面文件已创建
- [ ] 路由配置已更新
- [ ] 导航菜单已添加
- [ ] 后端服务已启动
- [ ] 前端服务已启动
- [ ] 功能测试通过
- [ ] API测试通过

### 10. 常见问题

#### Q: API调用失败,显示CORS错误
A: 确保backend_api_server.py中已配置CORS:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

#### Q: 前端页面空白
A: 检查浏览器控制台错误,确保所有依赖已安装

#### Q: 数据生成失败
A: 检查后端日志,确保test_data模块路径正确

### 11. 下一步

完成集成后,可以:
1. 添加更多数据类型
2. 自定义生成规则
3. 集成到测试用例生成流程
4. 添加数据导出功能
5. 实现数据持久化

---

**集成完成后,系统将具备完整的测试数据生成和管理能力!** 🎉
