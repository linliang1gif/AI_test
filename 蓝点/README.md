# 蓝点项目平台接入 - 完整指南

## 📋 目录

1. [项目概述](#项目概述)
2. [快速开始](#快速开始)
3. [详细文档](#详细文档)
4. [执行流程](#执行流程)
5. [验证方法](#验证方法)
6. [常见问题](#常见问题)
7. [文件清单](#文件清单)

## 项目概述

### 背景
蓝点新生废品回收B2B平台，包含 817 个 API 接口。本项目旨在将蓝点项目正式接入 AI 测试平台，实现从 OpenAPI 导入到平台内执行的完整流程。

### 目标
- ✓ 导入 bluedot_openapi.json（817个接口）
- ✓ 创建蓝点项目和测试环境
- ✓ 配置 Bearer Token 鉴权
- ✓ 生成币别管理测试用例（约8个）
- ✓ 在平台内触发执行
- ✓ 查看执行详情（RunCase/RunStep/快照/状态历史）

### 当前状态
- ✅ YApi → OpenAPI 转换完成（817个接口）
- ✅ 脚本验证通过（100%成功率）
- ✅ 平台接入脚本已更新（API端点修正）
- ✅ 完整文档已输出
- ⏳ 等待执行

## 快速开始

### 三步执行

#### 第一步：启动平台
```bash
# 终端1: 启动后端
cd ai测试/ai-test-platform
python backend_api_server.py

# 终端2: 启动前端
cd ai测试/ai-test-platform/frontend
npm start
```

#### 第二步：获取 Token
1. 登录 https://dev-recycle.szhibu.com/index
   - 商户号: `1014`
   - 账号: `ldsit`
   - 密码: `654321`
2. F12 → Network → 复制 Bearer Token
3. 更新 `ai测试/bluedot_platform_integration.py` 第18行

#### 第三步：执行接入
```bash
cd ai测试
python bluedot_platform_integration.py
```

### 验证结果
```bash
cd ai测试
python verify_bluedot_integration.py
```

## 详细文档

### 核心文档
| 文档 | 说明 | 用途 |
|------|------|------|
| [快速执行卡片.md](快速执行卡片.md) | 三步执行指南 | 快速参考 |
| [执行前检查清单.md](执行前检查清单.md) | 执行前必查项 | 执行准备 |
| [BLUEDOT_PLATFORM_INTEGRATION_GUIDE.md](BLUEDOT_PLATFORM_INTEGRATION_GUIDE.md) | 完整执行指南 | 详细步骤 |
| [BLUEDOT_PLATFORM_INTEGRATION_SUMMARY.md](BLUEDOT_PLATFORM_INTEGRATION_SUMMARY.md) | 工作完成总结 | 技术细节 |
| [本轮工作完成清单.md](本轮工作完成清单.md) | 工作量统计 | 交付物清单 |
| [验证报告模板.md](验证报告模板.md) | 验证报告模板 | 结果记录 |

### 历史文档
| 文档 | 说明 |
|------|------|
| [BLUEDOT_PROJECT_PROFILE.md](BLUEDOT_PROJECT_PROFILE.md) | 项目技术档案 |
| [PILOT_EXECUTION_GUIDE.md](PILOT_EXECUTION_GUIDE.md) | 试点执行指南 |
| [PILOT_READY_REPORT.md](PILOT_READY_REPORT.md) | 试点准备报告 |
| [BLUEDOT_PILOT_EXECUTION_RESULT.md](BLUEDOT_PILOT_EXECUTION_RESULT.md) | 试点执行结果 |

## 执行流程

### 完整流程图
```
1. 创建蓝点项目
   ↓
2. 创建测试环境
   ↓
3. 配置 Bearer Token 鉴权
   ↓
4. 导入 bluedot_openapi.json
   ↓
5. 生成测试用例（自动）
   ↓
6. 筛选币别管理用例
   ↓
7. 触发平台内执行
   ↓
8. 查看执行结果
```

### 关键步骤说明

#### 步骤 1-3: 项目配置
- 创建项目、环境、鉴权配置
- 使用平台 API: `/api/v2/projects`, `/api/v2/environments`, `/api/v2/auth-profiles`

#### 步骤 4: OpenAPI 导入
- 上传 `bluedot_openapi.json`
- 使用平台 API: `/api/v2/swagger/import-file`
- 解析 817 个接口

#### 步骤 5-6: 测试用例生成
- 自动从 OpenAPI 生成测试用例
- 使用平台 API: `/api/v2/swagger/generate-test-cases`
- 筛选币别管理相关用例（约8个）

#### 步骤 7-8: 执行和验证
- 在平台内触发执行
- 使用平台 API: `/api/v2/execution/trigger`
- 查看 TestRun、RunCase、状态历史

## 验证方法

### 自动验证
运行验证脚本:
```bash
cd ai测试
python verify_bluedot_integration.py
```

验证项包括:
- ✓ 后端健康状态
- ✓ 蓝点项目存在
- ✓ OpenAPI 已导入
- ✓ 测试用例已生成
- ✓ 测试执行记录存在
- ✓ RunCase 记录存在
- ✓ 状态历史存在

### 手工验证

#### 前端验证
访问 http://localhost:3000
- 项目列表中看到"蓝点回收系统"
- 测试用例列表中看到币别管理相关用例
- TestRun 列表中看到执行记录
- 可查看 RunCase 详情和快照

#### API 验证
```bash
# 查询项目
curl http://localhost:5000/api/v2/projects

# 查询测试用例
curl "http://localhost:5000/api/v2/test-cases?source=swagger"

# 查询 TestRun
curl http://localhost:5000/api/v2/test-runs
```

#### 数据库验证
```bash
cd ai测试/ai-test-platform
sqlite3 test_platform.db

# 查询蓝点项目
SELECT * FROM projects WHERE name LIKE '%蓝点%';

# 查询测试用例
SELECT COUNT(*) FROM test_cases WHERE source = 'swagger';

# 查询 TestRun
SELECT * FROM test_runs ORDER BY created_at DESC LIMIT 1;
```

## 常见问题

### Q1: Token 过期怎么办？
**A**: 重新登录蓝点系统，获取新的 Bearer Token，更新脚本后重新执行。

### Q2: 数据库未初始化怎么办？
**A**: 运行 `cd ai测试/ai-test-platform && python init_db.py`

### Q3: 网络连接失败怎么办？
**A**: 确认 VPN 已连接，测试 `ping dev-recycle.szhibu.com`

### Q4: 测试用例生成失败怎么办？
**A**: 检查 OpenAPI 文件格式，查看后端日志中的错误信息。

### Q5: 执行触发失败怎么办？
**A**: 确认测试用例已成功生成，检查 execution_config 是否完整。

更多问题请参考 [BLUEDOT_PLATFORM_INTEGRATION_GUIDE.md](BLUEDOT_PLATFORM_INTEGRATION_GUIDE.md) 的"常见问题"章节。

## 文件清单

### 核心文件
```
蓝点/
├── README.md                                    # 本文件
├── bluedot_openapi.json                         # OpenAPI规范（817个接口）
├── 快速执行卡片.md                              # 快速参考
├── 执行前检查清单.md                            # 执行准备
├── BLUEDOT_PLATFORM_INTEGRATION_GUIDE.md        # 详细指南
├── BLUEDOT_PLATFORM_INTEGRATION_SUMMARY.md      # 完成总结
├── 本轮工作完成清单.md                          # 工作量统计
└── 验证报告模板.md                              # 报告模板

ai测试/
├── bluedot_platform_integration.py              # 平台接入脚本
├── verify_bluedot_integration.py                # 验证脚本
├── pilot_bluedot_with_token.py                  # 脚本验证（已通过）
└── bluedot_pilot_result.json                    # 试点结果
```

### 历史文件
```
蓝点/
├── BLUEDOT_PROJECT_PROFILE.md                   # 项目档案
├── PILOT_EXECUTION_GUIDE.md                     # 试点指南
├── PILOT_READY_REPORT.md                        # 准备报告
└── BLUEDOT_PILOT_EXECUTION_RESULT.md            # 试点结果

ai测试/
├── convert_yapi_to_openapi.py                   # YApi转换工具
├── pilot_bluedot_secure.py                      # OAuth2试点（已废弃）
├── pilot_bluedot_web_login.py                   # Web登录试点（已废弃）
└── diagnose_oauth2.py                           # OAuth2诊断（已废弃）
```

## 技术架构

### 数据流转
```
YApi (819接口)
    ↓ convert_yapi_to_openapi.py
OpenAPI (817接口)
    ↓ SwaggerService.import_from_file()
ApiSpec (数据库记录)
    ↓ SwaggerTestCaseGenerator
TestCase (817个用例)
    ↓ 筛选币别管理
TestCase (8个用例)
    ↓ ExecutionOrchestrator
TestRun + RunCase + RunStep
    ↓ 前端展示
完整的执行详情和快照
```

### 关键组件
- **SwaggerService**: OpenAPI 导入和解析
- **SwaggerTestCaseGenerator**: 测试用例自动生成
- **TestCaseService**: 测试用例管理
- **ExecutionOrchestrator**: 执行编排
- **ExecutionEngine**: 测试执行引擎
- **RunStateMachine**: 状态流转管理

### 数据库表
- `projects` - 项目信息
- `environments` - 测试环境
- `auth_profiles` - 鉴权配置
- `api_specs` - API 规范
- `test_cases` - 测试用例
- `test_runs` - 测试执行
- `run_cases` - 用例执行详情
- `run_steps` - 步骤执行详情
- `run_status_history` - 状态变更历史

## 成功标准

### 本轮目标
- ✓ 蓝点项目在平台中可见
- ✓ OpenAPI 导入成功（817个接口）
- ✓ 币别管理测试用例生成（约8个）
- ✓ 平台内触发执行成功
- ✓ 可查看执行详情（RunCase/RunStep/快照/状态历史）
- ✓ 输出平台接入验证报告

### 验收标准
1. **功能完整性**: 所有7个步骤成功
2. **数据准确性**: 项目、环境、用例、执行记录正确
3. **可观测性**: 前端可查看所有执行详情
4. **可追溯性**: 状态历史完整
5. **文档完整性**: 执行指南、验证报告齐全

## 下一步计划

### 短期（1-2天）
1. 完成平台接入执行
2. 验证所有功能
3. 输出验证报告
4. 修复发现的问题

### 中期（1周）
1. 接入第二条业务链（供应商管理/订单管理）
2. 扩展到更多接口（50-100个）
3. 验证自愈能力
4. 生成测试报告

### 长期（1月）
1. 全量接口接入（817个）
2. 性能优化
3. 稳定性提升
4. 生产环境部署

## 联系与支持

### 文档索引
- 快速开始: [快速执行卡片.md](快速执行卡片.md)
- 执行准备: [执行前检查清单.md](执行前检查清单.md)
- 详细指南: [BLUEDOT_PLATFORM_INTEGRATION_GUIDE.md](BLUEDOT_PLATFORM_INTEGRATION_GUIDE.md)
- 技术细节: [BLUEDOT_PLATFORM_INTEGRATION_SUMMARY.md](BLUEDOT_PLATFORM_INTEGRATION_SUMMARY.md)

### 问题排查
1. 查看脚本输出的错误信息
2. 查看后端日志
3. 查看前端控制台
4. 查阅"常见问题"章节
5. 检查数据库状态

---

**准备就绪，开始执行！**

最后更新: 2026-04-21
