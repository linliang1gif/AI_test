# AI Test Platform - 功能路线图

## 当前版本 (P1)

已完成功能：
- Swagger/OpenAPI 导入 (P1-7A)
- 测试用例管理 (P1-7B)
- 顶部栏真实数据 (P1-7C)
- 真实项目安全执行保护 (P1-7D)
- 报告 reports 表闭环 (P1-7E)
- 不可用功能入口隐藏 (P1-7F)

## 暂缓功能 (P2 阶段)

以下功能在当前版本中隐藏入口，避免误用：

1. **数据集管理** — 依赖 `dataset_manager` 模块，P2 阶段实现
2. **测试数据工厂** — 依赖 `test_data.data_factory` 模块，P2 阶段实现

直接访问路由 `/dataset-management` 或 `/test-data-factory` 会显示友好提示。
后端 `/api/test-data/*` 接口返回 503，不影响其他功能。
