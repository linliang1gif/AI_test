# P1-9E 脚本导出升级 报告

> 日期: 2026-05-02 | 状态: ✅ 完成

---

## 一、修改文件

| 文件 | 变更 |
|---|---|
| `backend_api_server.py` | 重写 `_generate_pytest_script()`，生成真实可运行 pytest 脚本 |
| `frontend/src/pages/TestCases.jsx` | 按钮 "生成脚本" → "导出脚本"；对话框标题和说明更新 |

---

## 二、脚本升级前后对比

| 对比项 | 升级前 (空壳) | 升级后 (P1-9E) |
|---|---|---|
| HTTP 请求 | 无 (`assert True`) | `requests.Session.request()` 真实发请求 |
| 请求参数 | 无 | 从 `execution_config.body` / `query_params` 填充 |
| 状态码断言 | 无 | `assert resp.status_code == 200` |
| 响应时间断言 | 无 | `assert resp.elapsed < 10s` |
| 字段存在断言 | 无 | `assert data["code"] is not None` |
| 字段值断言 | 无 | `assert data["code"] == 200` |
| status_code_in | 无 | `assert resp.status_code in [400, 422, 500]` (L2 变异) |
| 环境变量 | 硬编码 localhost | `API_BASE_URL` + `API_TOKEN` 环境变量 |
| 鉴权 | 无 | `Authorization: Bearer $TOKEN` (有 TOKEN 时) |
| CI 运行 | 不可 | `pytest test_xxx.py -v` 直接运行 |

---

## 三、生成示例

接口用例 (POST /api/order/page) 生成脚本包含：
- `os.getenv("API_BASE_URL")` / `os.getenv("API_TOKEN")`
- `self.session.request(method="POST", url=..., json={"pageNum":1,"pageSize":10}, timeout=30)`
- `assert resp.status_code == 200`
- `assert data["code"] is not None`
- `assert data["code"] == 200`

功能测试用例 (无 execution_config) 仍生成步骤模板 + TODO 提示。

---

## 四、前端变更

- 按钮文字: "生成脚本" → "导出脚本"
- tooltip: "导出可运行的 pytest 脚本，支持环境变量配置"
- 对话框标题: "pytest 脚本"
- 标签说明: "可直接 pytest 运行，支持 API_BASE_URL / API_TOKEN 环境变量"

---

## 五、验证结果

| 测试 | 结果 |
|---|---|
| smoke_p0_7_local | 100% ✅ |
| 前端构建 | ✅ built |
| 脚本语法验证 | 断言缩进正确，无嵌套引号问题 ✅ |

---

## 六、P1-9 全部完成

| 阶段 | 内容 | 状态 |
|---|---|---|
| P1-9A | 统一导入入口 | ✅ |
| P1-9B | 用例编辑能力 | ✅ |
| P1-9C | 接口用例规则增强 (L2) | ✅ |
| P2-9D | 接口覆盖率统计 | ✅ |
| P1-9E | 脚本导出升级 | ✅ |
