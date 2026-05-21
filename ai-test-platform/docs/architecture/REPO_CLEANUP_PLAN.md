# 仓库清理计划

## 背景

当前仓库同时包含 AI 测试平台源码、被测系统源码副本、历史阶段报告、旧启动入口和临时脚本。它们会污染搜索结果、降低 IDE 索引效率、增加构建和排查成本，也会让新接手者不知道应该从哪个入口启动。

本计划只定义清理顺序和确认点，不直接删除用户文件。

## P0：统一启动口径

状态：已开始。

目标：

- 主入口统一为 `backend.app:create_app`。
- 本地后端默认端口统一为 `8001`。
- 前端默认端口统一为 `5173`。
- `start-dev.ps1` 作为推荐启动脚本。
- `start_all.ps1` 仅保留为兼容入口，并转发到 `start-dev.ps1`。
- README 不再引导 `backend_api_server.py` 作为主启动方式。

验收：

- `powershell -ExecutionPolicy Bypass -File .\start-dev.ps1 -StatusOnly` 可正确显示前后端状态。
- `http://127.0.0.1:8001/health` 可访问。
- `http://127.0.0.1:5173/dashboard` 可访问。

## P1：隔离被测系统源码副本

状态：待人工确认后执行。

候选目录：

- `recycle-applet-feature-*/`
- `recycle-front-feature-*/`
- `recycle-server-feature-*/`
- `recycle-pound-feature-*/`
- `蓝点/`
- `ai测试/ai-test-platform/`

建议处理：

1. 确认这些目录是否只是分析样本或被测系统副本。
2. 若仍需要本地保留，移到仓库外部，例如 `G:\AI项目\被测系统源码\`。
3. 若已经提交到 Git 历史，需要单独评估是否清理历史。
4. `.gitignore` 已先加入规则，避免后续继续新增同类目录。

验收：

- `git status` 不再出现新增的被测系统源码副本。
- IDE 全局搜索默认不再扫到这些业务源码。
- 平台构建和测试路径不再误包含被测项目。

## P2：文档归档

状态：待执行。

候选根目录文件：

- `SYSTEM_STATUS.md`
- `SYSTEM_STATUS.2026-03.md`
- `Phase11_前端验收与业务断言修正报告.md`
- `Phase1-10_联调验收报告.md`
- `P0.5_冒烟测试报告.md`
- `P1_*`
- `磅称系统_v1.2.5_*.md`
- 其他阶段性验收或专项报告

建议处理：

- 根目录只保留 `README.md`、`.env.example`、启动脚本、Docker/依赖文件。
- 阶段报告归档到 `docs/archive/`。
- 专项分析归档到 `docs/reports/` 或对应业务目录。

验收：

- 新成员打开根目录时只看到启动和开发必需文件。
- 历史资料仍可在 `docs/` 下按主题查到。

## P3：拆分前端 API 服务

状态：待执行。

问题：

- `frontend/src/services/api.js` 体量过大，混合项目、环境、执行、缺陷、AI Studio 等多个领域。
- 旧接口和 V2 接口并存，修改风险高。

建议拆分：

- `frontend/src/services/httpClient.js`
- `frontend/src/services/projects.js`
- `frontend/src/services/environments.js`
- `frontend/src/services/testCases.js`
- `frontend/src/services/testRuns.js`
- `frontend/src/services/defects.js`
- `frontend/src/services/aiStudio.js`
- `frontend/src/services/uiSessions.js`

验收：

- 页面调用保持兼容。
- trace id、错误码、token 处理集中在 `httpClient.js`。
- 单个 service 文件不再承担所有领域。

## P4：迁移运行时数据库变更

状态：待设计。

问题：

- `backend/startup.py` 内存在多段运行时 `ALTER TABLE` / `CREATE TABLE` 逻辑。
- 没有版本号表，无法追溯、回滚或审计。

建议：

- 引入 Alembic。
- 将现有启动迁移固化为历史 revisions。
- 后续新增字段通过 `alembic revision` 管理。
- 运行时启动只做连接检查和必要的兼容性检查。

验收：

- 数据库结构变更有版本号。
- 启动日志不再重复跑大量 inspect/alter。
- 可在测试库完整重建结构。

## P5：鉴权配置加密

状态：待设计。

问题：

- `AuthProfile.auth_config` 可能保存 token、cookie、authorization。
- 当前模型注释中仍标记为后续加密。

建议：

- 使用 `cryptography.fernet` 或企业 KMS。
- `.env` 增加 `AUTH_CONFIG_KEY`。
- 写入前加密，读取后在服务层解密。
- API 响应继续脱敏，不返回完整敏感值。

验收：

- 数据库中不再明文保存鉴权配置。
- 旧数据有一次性迁移策略。
- 前端展示仍只显示掩码。
