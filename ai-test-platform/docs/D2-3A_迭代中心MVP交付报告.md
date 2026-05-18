# D2-3A 迭代中心 MVP 交付报告

## 一、概述

D2-3A 迭代中心 MVP 实现了迭代测试的核心闭环流程：
**创建迭代 → 录入需求 → AI解析 → 生成测试点 → 手动确认 → 生成测试用例 → 创建执行集 → 执行测试 → 查看报告**

## 二、数据库变更

### 2.1 iterations 表扩展（4 个新列）
| 列名 | 类型 | 说明 |
|---|---|---|
| `version` | VARCHAR(50) | 迭代版本号 |
| `test_owner` | VARCHAR(100) | 测试负责人 |
| `planned_start_time` | VARCHAR(30) | 计划开始时间 |
| `planned_release_time` | VARCHAR(30) | 计划发布时间 |

### 2.2 新建表（3 张）
| 表名 | 说明 |
|---|---|
| `iteration_requirements` | 迭代需求（title, content, source_type, risk_level, ai_summary, confirm_questions） |
| `iteration_test_points` | 迭代测试点（test_point, priority, test_type, risk_level, ai_generated, confirmed） |
| `iteration_execution_sets` | 迭代执行集（name, type, status, case_count, run_id） |

### 2.3 迁移脚本
- `scripts/migrate_d2_3a_iteration_center.py` — 幂等，重复执行安全

## 三、后端 API（16 个端点）

| # | Method | Path | 说明 |
|---|---|---|---|
| 1 | POST | `/api/v2/iterations` | 创建迭代 |
| 2 | GET | `/api/v2/projects/{pid}/iterations` | 项目迭代列表（已有） |
| 3 | GET | `/api/v2/iterations/{iid}` | 迭代详情（已有，含新字段） |
| 4 | PATCH | `/api/v2/iterations/{iid}` | 更新迭代 |
| 5 | POST | `/api/v2/iterations/{iid}/requirements` | 录入需求 |
| 6 | GET | `/api/v2/iterations/{iid}/requirements` | 查询需求 |
| 7 | POST | `/api/v2/iterations/{iid}/ai/analyze-requirements` | AI 解析需求 |
| 8 | POST | `/api/v2/iterations/{iid}/test-points/generate` | 生成测试点 |
| 9 | GET | `/api/v2/iterations/{iid}/test-points` | 查询测试点 |
| 10 | PATCH | `/api/v2/iteration-test-points/{tpid}/confirm` | 确认/取消确认测试点 |
| 11 | POST | `/api/v2/iterations/{iid}/test-cases/generate` | 生成测试用例 |
| 12 | GET | `/api/v2/iterations/{iid}/test-cases` | 查询迭代用例 |
| 13 | POST | `/api/v2/iterations/{iid}/execution-sets` | 创建执行集 |
| 14 | GET | `/api/v2/iterations/{iid}/execution-sets` | 查询执行集 |
| 15 | POST | `/api/v2/iterations/{iid}/run` | 执行迭代测试 |
| 16 | GET | `/api/v2/iterations/{iid}/report` | 迭代测试报告 |

所有端点均返回 `X-Trace-Id` 响应头，错误响应包含 `{code, message, trace_id, details}` 统一结构。

## 四、AI 解析服务

文件：`services/iteration_ai_service.py`

### 4.1 两层策略
1. **LLM 优先**：调用已有 `AIClient`，解析需求为结构化 JSON
2. **规则型 fallback**：LLM 不可用时，基于关键词提取功能点/业务规则/影响范围/风险点/测试点/待确认问题

### 4.2 输出结构（始终稳定）
```json
{
  "functional_points": [],
  "business_rules": [],
  "impact_scope": [],
  "risk_points": [],
  "test_points": [{"test_point": "", "priority": "", "test_type": "", "risk_level": ""}],
  "confirm_questions": [],
  "_source": "llm|fallback"
}
```

### 4.3 质量保障
- AI 生成的测试点标记 `ai_generated=true`
- 支持手动确认（`confirmed` 字段），只有已确认的测试点才会生成用例
- 不产生随机测试结果

## 五、前端页面

### 5.1 `/iterations` — 迭代列表
- 项目筛选 + 状态筛选
- 创建迭代弹窗（名称、版本、负责人、测试负责人、计划时间）
- 卡片式列表，展示需求数/测试点数/用例数/通过率

### 5.2 `/iterations/:id` — 迭代详情（7 个 Tab）
| Tab | 功能 |
|---|---|
| 概览 | 基本信息 + 统计面板 |
| 需求 | 录入需求表单 + 需求列表 |
| AI解析 | 一键 AI 解析，展示 6 维分析结果 |
| 测试点 | 生成测试点 + 确认/取消确认 |
| 测试用例 | 根据已确认测试点生成用例 + 用例表格 |
| 执行集 | 创建冒烟/迭代/回归执行集 |
| 测试报告 | 统计面板 + 执行记录表格 |

### 5.3 API 客户端
`frontend/src/services/api.js` iterations 命名空间新增 16 个方法，全部通过 `request()` 统一调用，自动携带 `X-Trace-Id`。

### 5.4 路由 + 菜单
`App.jsx` 新增 `IterationList` / `IterationDetail` 路由，侧边栏"项目管理"分区增加"迭代中心"入口。

## 六、验收测试结果

**56/56 全部通过** ✅

```
scripts/test_d2_3a_iteration_center.py
```

覆盖：
- 创建/查询/详情 (含新字段 version, test_owner)
- 需求录入 + AI 解析 (fallback)
- 测试点生成 + 确认
- 测试用例生成
- 执行集创建 + 查询
- 迭代报告
- trace_id 全链路 (3 端点 header 验证)
- 422 标准错误结构
- 敏感字段不泄露

## 七、对历史数据的影响

- **零影响**：新表独立，iterations 表 4 个新列均有默认值，不影响已有迭代记录
- TestCase 复用已有模型，通过 `iteration_id` 外键关联
- 迁移脚本幂等，可重复执行

## 八、已知风险

| 风险 | 等级 | 缓解 |
|---|---|---|
| LLM 不可用时 fallback 解析质量有限 | 低 | 关键词规则覆盖基础场景，后续可扩展 |
| 测试用例生成为骨架（无真实请求参数） | 中 | 需配合 Swagger 导入或手动补充具体参数 |
| 执行集尚未关联执行引擎调度 | 低 | run 端点已创建 TestRun + RunCase，可接入现有引擎 |

## 九、回滚方案

1. 从 `router_registry.py` 移除 `iteration_center_routes` 行
2. 从 `database/__init__.py` 移除 3 个新 model 导出
3. 新表 (`iteration_requirements`, `iteration_test_points`, `iteration_execution_sets`) 可保留或 DROP
4. iterations 表新列可保留（有默认值，不影响旧逻辑）

## 十、文件清单

| 文件 | 变更类型 |
|---|---|
| `database/models.py` | 修改（扩展 Iteration + 新增 3 model） |
| `database/__init__.py` | 修改（导出新 model） |
| `backend/router_registry.py` | 修改（注册新路由） |
| `services/iteration_ai_service.py` | **新建** |
| `routes/iteration_center_routes.py` | **新建** |
| `scripts/migrate_d2_3a_iteration_center.py` | **新建** |
| `scripts/test_d2_3a_iteration_center.py` | **新建** |
| `frontend/src/services/api.js` | 修改（iterations 命名空间扩展） |
| `frontend/src/pages/IterationList.jsx` | **新建** |
| `frontend/src/pages/IterationDetail.jsx` | **新建** |
| `frontend/src/App.jsx` | 修改（路由 + 菜单） |
| `docs/D2-3A_迭代中心MVP交付报告.md` | **新建** |
