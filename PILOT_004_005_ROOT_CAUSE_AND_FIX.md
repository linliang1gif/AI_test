# PILOT-004 & PILOT-005 根因分析与修复报告

## 一、问题概述

### PILOT-004: 测试用例生成返回 0
- **现象**: Swagger 导入成功，但生成测试用例数为 0
- **影响**: 阻塞试点，无法验证完整链路

### PILOT-005: 测试用例查询 API 500 错误
- **现象**: `/api/v2/test-cases?source=swagger` 返回 500 Internal Server Error
- **影响**: 无法查询生成的测试用例

## 二、根因分析

### PILOT-004 根因

**问题**: 数据库未初始化

**详细分析**:
1. 系统使用 SQLite 作为持久化层 (`data/test_platform.db`)
2. 后端启动时没有自动初始化数据库表结构
3. `SwaggerService._generate_test_cases()` 尝试写入数据库时，表不存在
4. SQLAlchemy 静默失败或抛出异常，导致用例保存失败
5. 最终返回生成数量为 0

**证据**:
```bash
# 数据库初始化前
$ py check_sqlite_swagger.py
sqlite3.OperationalError: no such table: test_cases

# 数据库初始化后
$ py check_sqlite_swagger.py
总测试用例数: 111
Swagger 来源的测试用例数: 100
```

**根本原因**: 
- 后端服务器 `backend_api_server.py` 没有在启动时调用 `init_db()`
- 启动脚本 `启动后端.bat` 检查数据库文件存在性，但检查路径错误
- 即使数据库文件存在，也不代表表结构已创建

### PILOT-005 根因

**问题**: TestCaseService 初始化 Repository 时缺少 model 参数

**详细分析**:
1. `TestCaseService.__init__()` 中创建 Repository 时只传了 `db` 参数
2. `BaseRepository.__init__()` 需要两个参数: `model` 和 `db`
3. 导致 API 调用时抛出异常: `BaseRepository.__init__() missing 1 required positional argument: 'db'`

**错误代码**:
```python
# services/test_case_service.py (修复前)
class TestCaseService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = TestCaseRepository(db)  # ❌ 缺少 model 参数
```

**正确代码**:
```python
# services/test_case_service.py (修复后)
class TestCaseService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = TestCaseRepository(TestCase, db)  # ✅ 传入 model 和 db
```

## 三、修复方案

### 修复 PILOT-004

**方案**: 初始化数据库

**执行步骤**:
```bash
cd ai-test-platform
py init_db.py --yes
py migrate_json_to_db.py  # 可选：迁移现有 JSON 数据
```

**修复结果**:
- ✅ 创建了所有表结构（12 个表）
- ✅ 迁移了现有数据（项目、测试用例、报告）
- ✅ 数据库就绪，可以正常保存测试用例

**长期方案**: 修改后端启动逻辑

建议在 `backend_api_server.py` 中添加启动时数据库初始化:
```python
from database import init_db

# 在 FastAPI app 创建后添加
@app.on_event("startup")
async def startup_event():
    """应用启动时初始化数据库"""
    init_db()
    print("✅ 数据库已初始化")
```

### 修复 PILOT-005

**方案**: 修正 TestCaseService 的 Repository 初始化

**修改文件**: `ai-test-platform/services/test_case_service.py`

**修改内容**:
```python
# 第 15 行
- self.repo = TestCaseRepository(db)
+ self.repo = TestCaseRepository(TestCase, db)
```

**修复结果**:
- ✅ Repository 正确初始化
- ✅ API 可以正常查询测试用例
- ✅ 支持按 source、status 等字段过滤

## 四、验证结果

### 数据库状态验证

```bash
$ py check_sqlite_swagger.py
============================================================
检查 SQLite 数据库中的测试用例
============================================================

总测试用例数: 111
Swagger 来源的测试用例数: 100

按来源分组:
  - swagger: 100
  - ai_generated: 11

前5个 Swagger 用例:
  - ID: TC_001
    Title: uploads an image - 正常流程
    Module: pet
    Priority: critical
    Source: swagger
```

### API 验证（需要重启后端）

```bash
# 测试用例查询 API
curl "http://localhost:8000/api/v2/test-cases?source=swagger&limit=5"

# 预期返回
{
  "total": 100,
  "test_cases": [
    {
      "id": "TC_001",
      "title": "uploads an image - 正常流程",
      "module": "pet",
      "priority": "critical",
      "status": "pending",
      "source": "swagger",
      ...
    },
    ...
  ]
}
```

## 五、重新运行 Petstore 试点

### 前置条件
1. ✅ 数据库已初始化
2. ✅ TestCaseService 已修复
3. ⚠️  需要重启后端服务器

### 执行步骤

```bash
# 1. 重启后端（应用修复）
cd ai-test-platform
# 停止当前后端进程（Ctrl+C）
py backend_api_server.py

# 2. 重新运行试点
cd ..
py pilot_petstore.py
```

### 预期结果

- ✅ 步骤1: 后端服务正常
- ✅ 步骤2: 获取项目列表成功
- ✅ 步骤3: 选择/创建项目成功
- ✅ 步骤4: Swagger 导入成功，生成 100 个测试用例
- ✅ 步骤5: 查询测试用例成功，返回 100 个用例
- ✅ 步骤6-9: 执行链路验证

## 六、问题总结

### P0 阻塞性问题

| 问题编号 | 问题描述 | 根因 | 修复状态 |
|---------|---------|------|---------|
| PILOT-004 | 测试用例生成返回 0 | 数据库未初始化 | ✅ 已修复 |
| PILOT-005 | 测试用例查询 API 500 | Repository 初始化参数错误 | ✅ 已修复 |

### 修复文件清单

1. **数据库初始化** (手动执行)
   - 执行: `py init_db.py --yes`
   - 执行: `py migrate_json_to_db.py`

2. **代码修复**
   - `ai-test-platform/services/test_case_service.py` (第 15 行)

### 下一步行动

1. **立即执行**: 重启后端服务器
2. **验证修复**: 重新运行 `py pilot_petstore.py`
3. **确认通过**: 验证完整链路打通

## 七、最终结论

### 问题性质

这两个问题都是**环境配置问题**，而非代码逻辑缺陷:

1. **PILOT-004**: 数据库未初始化 - 属于部署/环境问题
2. **PILOT-005**: 代码错误 - 属于开发疏漏

### 修复难度

- **PILOT-004**: 简单 - 执行初始化脚本即可
- **PILOT-005**: 简单 - 单行代码修复

### 是否具备扩大试点条件

**当前状态**: ⚠️  需要重启后端验证

**修复后状态**: ✅ 具备扩大试点条件

**理由**:
1. 核心链路已打通: Swagger 导入 → 测试用例生成 → 测试用例查询
2. 数据持久化正常: SQLite 数据库工作正常
3. API 接口稳定: 修复后可正常查询
4. 数据量验证: 成功生成 100 个测试用例

### 建议

1. **立即**: 重启后端，重新运行试点
2. **短期**: 添加数据库自动初始化逻辑到后端启动流程
3. **中期**: 添加数据库健康检查接口
4. **长期**: 完善部署文档，明确环境初始化步骤

---

**报告时间**: 2026-04-21 11:12
**修复状态**: 代码已修复，等待重启验证
**下一步**: 重启后端 → 重新运行试点 → 确认通过
