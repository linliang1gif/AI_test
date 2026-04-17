# 前端API适配指南 - V3架构升级

## 📋 概述

由于后端架构从单线程升级到并发调度系统(V3),前端需要适配新的API接口和数据格式。

---

## 🔄 API变化对比

### 1. Test Runs API

#### 启动测试执行

**旧版本(V2)**:
```javascript
POST /api/test-runs
{
  "environment": "staging"
}
```

**新版本(V3)**:
```javascript
POST /api/test-runs/start  // ← 路径变化
{
  "environment": "staging"
}
```

**前端修改**:
```javascript
// frontend/src/services/api.js
export const testRunsAPI = {
  start: (config) => request('/test-runs/start', {  // 修改路径
    method: 'POST',
    body: JSON.stringify(config),
  }),
}
```

---

#### 获取测试执行列表

**旧版本(V2)**:
```json
{
  "success": true,
  "data": [...]  // ← 字段名
}
```

**新版本(V3)**:
```json
{
  "success": true,
  "testRuns": [...],  // ← 字段名变化
  "count": 10
}
```

**影响**: 前端需要从 `data.testRuns` 而不是 `data.data` 获取数据

---

#### 获取测试执行状态

**旧版本(V2)**:
```json
{
  "success": true,
  "data": {
    "id": 1,
    "status": "running",
    "progress": 50
  }
}
```

**新版本(V3)** - 新增并发任务信息:
```json
{
  "success": true,
  "testRun": {  // ← 字段名变化
    "id": 1,
    "status": "running",
    "progress": 50,
    "tasks": [  // ← 新增字段
      {
        "task_id": "task-001",
        "name": "测试用例 1",
        "status": "success",
        "duration": 1.2
      }
    ]
  }
}
```

**影响**: 前端可以展示详细的并发任务状态

---

## 📝 前端组件适配清单

### ✅ 已完成适配

#### 1. TestRuns.jsx
**修改内容**:
- ✅ 适配新的API路径 (`/test-runs/start`)
- ✅ 适配新的返回字段 (`testRuns` 而不是 `data`)
- ✅ 新增并发任务状态展示
- ✅ 显示 task_id, status, duration

**新增功能**:
```jsx
{/* 并发任务状态展示 */}
{run.tasks && run.tasks.length > 0 && (
  <div className="mt-3 pt-3 border-t">
    <div className="text-xs text-gray-600 mb-2">并发任务状态:</div>
    {run.tasks.slice(-3).map((task) => (
      <div key={task.task_id}>
        {/* 显示状态图标和执行时长 */}
      </div>
    ))}
  </div>
)}
```

---

#### 2. api.js
**修改内容**:
- ✅ 修改 `testRunsAPI.start()` 路径为 `/test-runs/start`

---

### ⚠️ 可能需要适配的组件

#### 1. TestCases.jsx
**检查点**:
- 是否调用测试执行API?
- 是否需要显示并发任务状态?

**建议**: 如果有"执行测试"功能,需要适配新API

---

#### 2. Automation.jsx
**检查点**:
- 自动化脚本执行是否使用test-runs API?
- 是否需要显示任务执行状态?

**建议**: 如果使用,需要适配新的返回格式

---

#### 3. Reports.jsx
**检查点**:
- 报告生成是否依赖test-runs数据?
- 是否需要展示任务级别的统计?

**建议**: 可以利用新的tasks数据生成更详细的报告

---

## 🎯 适配步骤

### 步骤1: 检查API调用
```bash
# 搜索所有调用test-runs API的地方
grep -r "test-runs" frontend/src/
grep -r "testRunsAPI" frontend/src/
```

### 步骤2: 更新API路径
```javascript
// 旧代码
testRunsAPI.start(config)  // POST /api/test-runs

// 新代码
testRunsAPI.start(config)  // POST /api/test-runs/start
```

### 步骤3: 更新数据访问
```javascript
// 旧代码
const runs = data.data

// 新代码
const runs = data.testRuns
```

### 步骤4: 利用新字段
```javascript
// 新增: 显示并发任务状态
{run.tasks && run.tasks.map(task => (
  <TaskStatus 
    key={task.task_id}
    status={task.status}
    duration={task.duration}
  />
))}
```

---

## 🧪 测试验证

### 1. 启动测试
```bash
# 启动后端
cd ai测试/ai-test-platform
python backend_api_server.py

# 启动前端
cd frontend
npm run dev
```

### 2. 功能测试
1. ✅ 打开"测试运行"页面
2. ✅ 点击"运行新测试"
3. ✅ 观察并发任务状态实时更新
4. ✅ 验证状态显示: Running / Success / Failed
5. ✅ 验证执行时长显示

### 3. API测试
```bash
# 运行API测试
python test_concurrent_execution_status.py
```

---

## 📊 数据流对比

### 旧版本(V2)
```
前端 → POST /api/test-runs → 后端
前端 ← { data: {...} } ← 后端
```

### 新版本(V3)
```
前端 → POST /api/test-runs/start → 后端
前端 ← { testRun: { tasks: [...] } } ← 后端
                      ↑
                  并发任务状态
```

---

## ✅ 兼容性说明

### 向后兼容
- ✅ 旧的 `GET /api/test-runs` 仍然可用
- ✅ 旧的 `GET /api/test-runs/{id}/status` 仍然可用
- ⚠️ `POST /api/test-runs` 改为 `POST /api/test-runs/start`

### 数据格式兼容
- ✅ 所有旧字段仍然存在
- ✅ 新增 `tasks` 字段(可选)
- ✅ 前端可以渐进式升级

---

## 🚀 升级建议

### 立即需要
1. ✅ 修改 `api.js` 中的 `/test-runs/start` 路径
2. ✅ 更新 `TestRuns.jsx` 显示并发任务状态

### 可选升级
1. ⚠️ 其他页面如需要,可以利用 `tasks` 数据
2. ⚠️ 报告页面可以展示任务级别统计
3. ⚠️ Dashboard可以显示并发执行指标

### 不需要修改
1. ✅ Projects页面 - 不涉及测试执行
2. ✅ TestCases页面 - 只管理用例,不执行
3. ✅ Settings页面 - 配置管理

---

## 📚 相关文档

- `Architecture_Upgrade_Complete_Summary.md` - 架构升级总结
- `Frontend_Concurrent_Status_Report.md` - 前端并发状态报告
- `test_concurrent_execution_status.py` - API测试

---

## 💡 总结

**核心变化**:
1. API路径: `/test-runs` → `/test-runs/start`
2. 返回字段: `data` → `testRuns`
3. 新增字段: `tasks` (包含并发任务状态)

**适配范围**:
- ✅ 必须: `api.js`, `TestRuns.jsx`
- ⚠️ 可选: 其他使用test-runs的组件

**升级策略**:
- 渐进式升级,不影响现有功能
- 新功能(并发任务状态)可选启用
- 保持向后兼容

---

**文档更新时间**: 2024年  
**状态**: ✅ 已完成
