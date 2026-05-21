# P3-2 测试数据管理 MVP 报告

## 回归结果

| 指标 | 值 |
|---|---|
| 总计 | 19 |
| ✅ PASS | 16 |
| ❌ FAIL | 0 |
| ⚠️ XFAIL | 1 (Phase 18 external_api) |
| ⏭️ SKIP | 2 (AI_PROVIDER=none) |
| 核心通过率 | 16/16 = **100.0%** |
| P3-2 专项 | 61/61 PASS |
| 前端 build | ✅ 通过 |

## 修改/新增文件

### 新增文件
| 文件 | 说明 |
|---|---|
| `database/models.py` (追加) | TestDataset / TestDatasetItem / TestDataBinding 三个模型 |
| `routes/test_data_routes.py` | 12 个 API 端点 |
| `services/test_data_service.py` | 变量替换引擎 + 敏感数据脱敏 |
| `frontend/src/pages/TestDataManagement.jsx` | 前端测试数据管理页面 |
| `scripts/test_p3_2_test_data_management.py` | P3-2 专项测试 61 项 |
| `docs/P3-2_test_data_management_mvp_report.md` | 本报告 |

### 修改文件
| 文件 | 修改内容 |
|---|---|
| `backend/startup.py` | 追加 P3-2 自动建表迁移 |
| `backend/router_registry.py` | 注册测试数据管理路由 |
| `routes/test_suite_routes.py` | 注入变量替换 + data_summary |
| `services/quality_gate_service.py` | Rule 9: data_missing 警告 |
| `frontend/src/App.jsx` | 添加导航 + 路由 |
| `scripts/run_regression_all.py` | 注册 P3-2 测试 |

## 检查项

| # | 检查项 | 状态 |
|---|---|---|
| 1 | 新增 test_datasets 表 | ✅ |
| 2 | 新增 test_dataset_items 表 | ✅ |
| 3 | 新增 test_data_bindings 表 | ✅ |
| 4 | 新增 test_data_routes.py | ✅ |
| 5 | 支持 6 种 dataset_type | ✅ account / api_payload / ui_form / performance_pool / common_fixture / cleanup_rule |
| 6 | 数据集 CRUD | ✅ 创建 / 列表 / 详情 / 更新 / 软删除 |
| 7 | 数据项 CRUD | ✅ 添加 / 更新 / 删除 |
| 8 | 绑定数据集到用例 | ✅ 绑定 / 查询 / 解绑 / 幂等 |
| 9 | API 用例变量替换 | ✅ headers / params / body 中 ${key} 替换 |
| 10 | Web UI 用例变量替换 | ✅ steps.value 中 ${key} 替换 |
| 11 | 测试集支持数据集 | ✅ 执行时自动解析绑定 + 替换变量 |
| 12 | suite_summary.data_summary | ✅ datasets_used / missing_variables / data_binding_errors |
| 13 | CI 门禁识别数据问题 | ✅ Rule 9: data_missing 警告 |
| 14 | 敏感数据脱敏 | ✅ password/token/cookie/authorization 自动掩码 |
| 15 | P3-2 专项测试通过率 | 61/61 = 100% |
| 16 | run_regression_all 结果 | 16 PASS / 0 FAIL / 1 XFAIL / 2 SKIP |
| 17 | 前端 build 通过 | ✅ |
| 18 | 主链路不受影响 | ✅ API / WebUI / Visual / Performance / Suite / Gate 全 PASS |

## API 端点

| Method | Path | 说明 |
|---|---|---|
| POST | /api/v2/test-data/datasets | 创建数据集 |
| GET | /api/v2/test-data/datasets | 查询列表 (project_id/dataset_type/keyword) |
| GET | /api/v2/test-data/datasets/{id} | 详情 (含 items + bindings) |
| PUT | /api/v2/test-data/datasets/{id} | 更新 |
| DELETE | /api/v2/test-data/datasets/{id} | 软删除 |
| POST | /api/v2/test-data/datasets/{id}/items | 添加数据项 |
| PUT | /api/v2/test-data/items/{id} | 更新数据项 |
| DELETE | /api/v2/test-data/items/{id} | 删除数据项 |
| POST | /api/v2/test-data/bindings | 绑定数据集到用例 |
| DELETE | /api/v2/test-data/bindings/{id} | 解绑 |
| GET | /api/v2/test-data/cases/{case_id}/datasets | 查询用例绑定的数据集 |
| POST | /api/v2/test-data/substitute-preview | 变量替换预览 |

## 变量替换示例

```json
// 数据项: username=testuser01, password=MySecret123!
// 用例 execution_config:
{
  "url": "/api/login",
  "body": {"user": "${username}", "pass": "${password}"}
}
// 替换后:
{
  "url": "/api/login",
  "body": {"user": "testuser01", "pass": "MySecret123!"}
}
// 展示时 password 值显示为: My****3!
```

## 安全要求达成

- ✅ password / token / cookie / authorization 默认脱敏展示
- ✅ 数据集详情中敏感字段只显示掩码 (前2后2 + ****)
- ✅ 后端日志不打印完整敏感数据
- ✅ API 响应中敏感值已脱敏
- ✅ 敏感 key 自动识别 (is_sensitive auto-detect)

## 结论

**P3-2 测试数据管理 MVP 已完成，可以进入 P3-3。**
