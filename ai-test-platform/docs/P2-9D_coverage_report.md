# P2-9D 接口覆盖率统计 报告

> 日期: 2026-05-02 | 状态: ✅ 完成

---

## 一、修改文件

| 文件 | 变更 |
|---|---|
| `routes/swagger_routes.py` | 新增 `GET /api/v2/swagger/coverage` 接口 |
| `frontend/src/services/api.js` | 新增 `api.v2.swagger.coverage()` 方法 |
| `frontend/src/pages/TestCases.jsx` | 新增覆盖率状态 + 环形进度条摘要卡片 |

---

## 二、后端接口

### `GET /api/v2/swagger/coverage?project_id=N`

**返回字段：**

| 字段 | 说明 |
|---|---|
| `total_apis` | Swagger 规范中 API 总数 (METHOD + PATH) |
| `covered_apis` | 有对应测试用例的 API 数量 |
| `coverage_rate` | 覆盖率百分比 (0-100) |
| `l1_case_count` | L1 正向用例数 |
| `l2_case_count` | L2 变异用例数 |
| `total_swagger_cases` | Swagger 来源用例总数 |
| `uncovered` | 未覆盖 API 列表 (最多 50 条) |
| `specs` | 各 API 规范详情 |

**计算逻辑：**
1. 遍历所有 `api_specs` 的 `raw_spec_path`，解析 Swagger JSON 提取全部 `(METHOD, PATH)` 组合
2. 查询所有 `source='swagger'` 的 `test_cases`，从 `execution_config.method + execution_config.url` 提取覆盖的 API
3. 交叉比对得出覆盖率

---

## 三、前端 UI

- 环形进度条显示覆盖率百分比
  - ≥80%: 绿色
  - ≥50%: 橙色
  - <50%: 红色
- 4 列统计：API 总数 / 已覆盖 / L1 正向 / L2 变异
- 未覆盖数量红色提示
- 手动刷新按钮
- 仅在「全部」和「接口测试」tab 下显示，「功能测试」tab 隐藏

---

## 四、验证结果

| 测试 | 结果 |
|---|---|
| smoke_p0_7_local | 100% ✅ |
| check_api_contract | ✅ 通过 |
| 前端构建 | ✅ built |
