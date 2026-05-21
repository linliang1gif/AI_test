# Phase 11 前端验收与业务断言修正报告

**时间**: 2026-04-28 17:00
**范围**: 前端展示验收 + 业务断言修正 + 接口风险分级 + 生产环境保护

---

## 一、前端展示验收 (PASS)

构造 passed/failed/error 三类用例 (run_id: p11-verify):

| 用例 | status | HTTP | 耗时 | 断言 | Auth脱敏 |
|------|--------|------|------|------|----------|
| 币别列表-正常 | passed | 200 | 36ms | 3/3 pass | Bearer e*** |
| 币别列表-断言失败 | failed | 200 | 11ms | 0/3 pass | Bearer e*** |
| 不可达地址 | error | 0 | 21049ms | N/A | Bearer e*** |

前端展示项验证:

| # | 检查项 | 结果 |
|---|--------|------|
| 1 | 请求方法 | PASS (POST/GET 正确显示) |
| 2 | 请求 URL | PASS (base_url + path 完整) |
| 3 | 请求 Header | PASS (JsonBlock 展示) |
| 4 | Token 脱敏 | PASS (type=password 输入框 + Bearer e***) |
| 5 | 请求 Body | PASS (JsonBlock 展示) |
| 6 | 响应 HTTP 状态码 | PASS (绿色200/红色4xx 颜色区分) |
| 7 | 响应 Body | PASS (JsonBlock 展示) |
| 8 | 执行耗时 | PASS (duration_ms 精确到小数) |
| 9 | 断言结果列表 | PASS (AssertionRow 组件) |
| 10 | 断言 type/expected/actual/passed/message | PASS (每条断言完整展示) |
| 11 | 失败原因 | PASS (error_message 红色卡片) |
| 12 | AI 智能断言 | PASS (7条AI断言已生成, 不修改执行结果) |

Phase 1-10 报告第 8 项已更新为全部勾选完成。

---

## 二、蓝点接口响应规范分析

详见 `docs/蓝点接口响应规范分析.md`

关键发现:

| 问题 | 结论 |
|------|------|
| HTTP 200 代表什么 | 仅代表网关成功, 不代表业务成功 |
| 业务成功码 | body.code == 200 |
| 认证失败码 | body.code == 401 |
| 参数校验失败码 | body.code == 10000 |
| 业务错误码 | body.code == 400 |
| 消息字段 | 固定使用 message (非 msg) |
| data 字段 | 成功时有值, 失败时为 null |
| 分页结构 | data.list / data.total / data.pageSize / data.pageNum |
| 列表结构 | data 直接为 array |

---

## 三、默认断言策略升级

从 "只判 HTTP 200" 升级为 L1-L5 分层:

| 层级 | 断言内容 | 适用范围 |
|------|---------|---------|
| L1 | status_code == 200, response_time < 10s | 全部接口 |
| L2 | $.code 存在, $.message 存在 | 全部业务接口 |
| L3 | $.code == 200 (业务成功) | page/list 接口 |
| L4 | $.data.list 存在, $.data.total 存在 | page 接口 |
| L4 | $.data 存在 | list 接口 |
| L5 | AI 智能补充 (不修改执行状态) | 可选 |

验证结果:
- page 接口: 8 条断言 (L1+L2+L3+L4)
- list 接口: 6 条断言 (L1+L2+L3+L4)
- detail 接口: 4 条断言 (L1+L2, 假ID可能code=400)
- save/update/delete: 2 条断言 (response_time + code存在)

**关键验证: HTTP 200 + code=10000 => status=failed** (确认通过)

---

## 四、接口风险分级

扫描 814 个 Swagger API 结果:

| 风险等级 | 数量 | 占比 |
|---------|------|------|
| Low (查询/列表/详情) | 295 | 36.2% |
| Medium (导出/计算/校验) | 188 | 23.1% |
| High (新增/修改/删除/审批) | 331 | 40.7% |
| **Total** | **814** | 100% |

### 建议优先回归的 20 个低风险接口

| # | 方法 | 路径 | 说明 |
|---|------|------|------|
| 1 | POST | /basic/basicCurrency/page | 币别分页 |
| 2 | POST | /basic/basicExchangeRate/page | 汇率分页 |
| 3 | POST | /basic/basicWarehouseInfo/page | 仓库分页 |
| 4 | POST | /basic/basicLocationInfo/page | 库位分页 |
| 5 | POST | /davinci/crm/customer/page | 客户分页 |
| 6 | POST | /davinci/crm/appletAccount/page | 小程序账号分页 |
| 7 | POST | /basic/productCategory/page | 品类分页 |
| 8 | POST | /wms/materialWarehouseStock/page | 库存分页 |
| 9 | POST | /wms/inoutRecord/page | 出入库记录分页 |
| 10 | POST | /wms/materialWarehouseStockDetail/page | 库存明细分页 |
| 11 | POST | /purchaseOrder/page | 采购订单分页 |
| 12 | POST | /purchaseInForm/page | 采购入库分页 |
| 13 | POST | /basic/productInfo/page | 品名分页 |
| 14 | POST | /system/sysFormCodeRule/page | 编码规则分页 |
| 15 | POST | /salesOrder/detail/page | 销售订单分录分页 |
| 16 | POST | /salesOrder/page | 销售订单分页 |
| 17 | POST | /shopProduct/page | 商城产品分页 |
| 18 | POST | /shopProductPriceRecord/page | 价格记录分页 |
| 19 | POST | /davinci/shopOrderManage/page | 商城订单分页 |
| 20 | POST | /wms/wmsStockOutForm/page | 出库单分页 |

完整结果: `output/risk_classification.json`

---

## 五、生产环境保护

### 保护规则

| 环境 | High | Medium | Low |
|------|------|--------|-----|
| 开发/测试 | 允许 | 允许 | 允许 |
| 生产 (prod/production/生产) | 阻断 | 需二次确认 | 允许+审计 |

### 验证结果 (9/9 通过)

| 场景 | 期望 | 实际 |
|------|------|------|
| Dev + save | 允许 | 允许 PASS |
| Dev + delete | 允许 | 允许 PASS |
| Prod + save | 阻断 | 阻断 PASS |
| Prod + delete | 阻断 | 阻断 PASS |
| Prod + cancel | 阻断 | 阻断 PASS |
| Prod + export (无确认) | 阻断 | 阻断 PASS |
| Prod + export (force=true) | 允许 | 允许 PASS |
| Prod + page | 允许 | 允许 PASS |
| Prod + list | 允许 | 允许 PASS |

阻断提示文案: "当前为生产环境, 为防止数据污染, 已禁止执行高风险接口。"

### 实现位置

| 模块 | 文件 | 作用 |
|------|------|------|
| 风险分级 | app/executor_v2/risk_classifier.py | 根据关键词分级 |
| 环境守卫 | app/executor_v2/env_guard.py | 判断环境+拦截 |
| 引擎集成 | app/executor_v2/execution_engine.py | execute_case 前置检查 |
| API路由 | routes/executor_v2_routes.py | /risk/scan + /risk/check |

---

## 六、验收标准完成情况

| # | 标准 | 状态 |
|---|------|------|
| 1 | 前端第8项展示验收全部勾选完成 | PASS |
| 2 | passed/failed/error 三类结果正确展示 | PASS |
| 3 | Token 已脱敏 | PASS (type=password + Bearer e***) |
| 4 | 默认断言包含业务 code 校验 | PASS (L3: code==200) |
| 5 | HTTP 200 但 code 失败时 status=failed | PASS (code=10000 => failed) |
| 6 | 814 个 API 完成风险分级 | PASS (295/188/331) |
| 7 | 输出 20 个低风险回归接口 | PASS (全部为 /page 接口) |
| 8 | 生产环境 high 风险接口被阻断 | PASS (9/9 测试通过) |
| 9 | AI 分析不覆盖真实断言状态 | PASS (AI 只生成断言, 不修改 status) |

**Phase 11 全部验收标准通过。**

---

## 七、新增/修改文件清单

| 文件 | 操作 | 说明 |
|------|------|------|
| app/executor_v2/swagger_to_cases.py | 修改 | L1-L4 分层断言 |
| app/executor_v2/risk_classifier.py | 新增 | API 风险分级器 |
| app/executor_v2/env_guard.py | 新增 | 生产环境保护守卫 |
| app/executor_v2/execution_engine.py | 修改 | 集成 EnvGuard |
| routes/executor_v2_routes.py | 修改 | +risk/scan +risk/check |
| docs/蓝点接口响应规范分析.md | 新增 | 响应规范文档 |
| output/risk_classification.json | 新增 | 814 API 分级结果 |
| Phase1-10_联调验收报告.md | 修改 | 第8项补充完成 |
