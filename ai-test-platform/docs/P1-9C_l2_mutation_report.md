# P1-9C 接口用例规则增强 (L2) 报告

> 日期: 2026-05-02 | 状态: ✅ 完成

---

## 一、修改文件

| 文件 | 变更 |
|---|---|
| `app/executor_v2/swagger_to_cases.py` | 新增 `_build_mutation_cases()` 函数 (约 200 行)；`generate_cases_from_swagger_data` 新增 `generate_l2` 参数 |
| `services/swagger_service.py` | `_generate_test_cases` 新增 L2 变异用例生成逻辑，持久化到数据库 |
| `routes/swagger_routes.py` | 预览接口 (preview-file/preview-url/preview-yapi) 设置 `generate_l2=False` |
| `frontend/src/services/api.js` | 新增 `api.v2.testCases.update()` (P1-9B) |
| `frontend/src/pages/TestCases.jsx` | 详情弹窗支持编辑模式 (P1-9B) |

---

## 二、L2 变异类型

| # | 变异类型 | data_type 标签 | 适用方法 | 说明 |
|---|---|---|---|---|
| 1 | 必填字段缺失 | `required_missing` | POST/PUT/PATCH | 每个 required 字段单独移除 |
| 2 | 空值 | `empty_value` | POST/PUT/PATCH | 前 3 个 required 字段设空串 |
| 3 | 类型错误 | `type_error` | POST/PUT/PATCH | integer → "not_a_number", boolean → "not_bool" |
| 4 | 超长字符串 | `overflow` | POST/PUT/PATCH | string 字段设为 10000 个 A |
| 5 | 非法枚举 | `invalid_enum` | POST/PUT/PATCH | enum 字段设为 `__INVALID_ENUM__` |
| 6 | 边界值 | `boundary` | POST/PUT/PATCH | -1, 0, MAX_INT |
| 7 | 鉴权缺失 | `auth_missing` | 全部 | 清空 headers |
| 8 | 不存在 ID | `nonexistent_id` | detail/update/delete | uuid/id 设为不存在值 |

---

## 三、验证结果

### 单元测试
```
1 个 POST /api/user/save (required: name, age)
  → L1: 1 条正向用例
  → L2: 11 条变异用例
  → 总计: 12 条
```

### 回归测试

| 测试脚本 | 结果 |
|---|---|
| smoke_p0_7_local | 8/8 (100%) ✅ |
| check_api_contract | 23/23 (100%) ✅ |
| test_p1_7a_import_pipeline | 24/24 (100%) ✅ |
| 前端构建 | ✅ built |

---

## 四、设计说明

- **预览接口** (`preview-file`, `preview-url`, `preview-yapi`) 默认 `generate_l2=False`，避免预览过多用例
- **导入接口** (`import-file`, `import-url`, `import-yapi`) 通过 `SwaggerService._generate_test_cases` 生成 L2 用例，默认开启
- L2 用例 `expected_behavior` 统一为 `client_error`
- L2 用例使用 `status_code_in` 断言类型，已在 `assertion_engine.py` 中支持
- L2 生成失败不影响 L1 用例（try-catch 隔离）

---

## 五、禁止项确认

| 禁止项 | 遵守 |
|---|---|
| 不做 L3 AI 增强 | ✅ |
| 不做业务语义场景 | ✅ |
| 不做并发测试 | ✅ |
| 不修改数据库 schema | ✅ |
| 不影响现有 L1 用例 | ✅ |
