# Phase D — 安全与工程治理 路线图

> **创建时间**: 2026-05-05
> **作者**: Cascade（AI 协作助手）
> **基线 commit**: `449cf25` (Phase C2 安全收口完成)
> **基线分支**: `feature/phase-c2-security-hardening`
> **状态**: 未启动 / 待 Approve

---

## 0. 当前位置（Phase C2 完成后基线）

### ✅ 已完成

| 阶段 | 内容 | 关键产出 |
|---|---|---|
| Phase A | V2 架构主线收口 | `backend/app.py` create_app + `router_registry.py` 集中注册 39+ 模块 |
| Phase B1 / B1.5 | TestCases 活跃 V1 接口迁移到 V2 | `routes/test_case_extra_routes.py`，前端 `api.testCases.*` 全部走 V2 |
| Phase C1 | code_compare DB 持久化 | 5 张新表 + `services/code_compare_storage_service.py` |
| Phase C2 | CORS 收紧 + Git clone SSRF + 验收脚本编码兼容 | `_validate_repo_url`、`CORS_ALLOW_ORIGINS` env、4 个脚本 UTF-8 reconfigure |

### ⚠️ 当前仍存在的安全/工程风险（Phase C2 报告识别）

| # | 风险 | 严重度 | 说明 |
|---|---|---|---|
| R1 | **缺少统一 API 鉴权** | **High** | V2 路由除回归测试 `TESTING_KEY` 外无统一身份认证；任何能访问 `:8000` 的客户端都能调用全部业务接口 |
| R2 | 文件上传缺乏 MIME 严格校验 | Medium | `code_compare/upload-snapshot` 仅校验扩展名，未强制校验文件头/MIME |
| R3 | 缺少 API Rate Limit | Medium | 无 IP/账户限流，可能被滥用（尤其 AI 调用、git clone、文件上传） |
| R4 | 日志脱敏分散 | Medium | `_sanitize_git_url_for_log`、`_sanitize_content` 各自独立；token / cookie / authorization 没有统一 logger filter |
| R5 | `_raw_token` 直接读 env | Medium | 应支持密钥管理服务（Vault / Secret Manager） |
| R6 | WebSocket / SSE 通道 origin 校验 | Medium | 跨域保护仅依赖 CORS middleware，长连接通道未单独校验 |
| R7 | legacy `backend_api_server.py` 仍可运行 | Low | 已标记但未删除，38 处 `test_cases_db` 引用 |
| R8 | code_compare 前端来源标签缺失 | Low | DB / legacy_json fallback 未在前端展示来源 |

---

## 1. Phase D1 — V2 API 统一鉴权（**最高优先级**）

### 目标
为 V2 路由添加统一的身份认证中间件，消除「任何人都能调用业务 API」的风险。

### 非目标（明确不做）
- ❌ 不做完整 RBAC / 多租户
- ❌ 不做 OAuth2 第三方登录
- ❌ 不重构现有页面登录逻辑
- ❌ 不删除 `TESTING_KEY` 回归测试旁路

### 范围

| 文件 | 操作 |
|---|---|
| `backend/auth_middleware.py` | **新增** — JWT 或 API Key 校验中间件 |
| `backend/config.py` | +`API_AUTH_ENABLED` / `API_KEYS` / `JWT_SECRET` 配置 |
| `backend/app.py` | 注册中间件，**白名单**: `/health`, `/readiness`, `/docs`, `/openapi.json`, `/screenshots/*`, `/visual/*` |
| `backend/auth_middleware.py` | 保留 `TESTING_KEY` header 旁路（与现有回归脚本兼容） |
| `routes/auth_routes.py` | **新增** — `POST /api/v2/auth/login` 简单签发 JWT（admin user） |
| `frontend/src/services/api.js` | 请求拦截器自动注入 `Authorization: Bearer <token>` |
| `frontend/src/pages/Login.jsx` | 现有登录页接 `/api/v2/auth/login` |
| `scripts/test_api_auth.py` | **新增** — 验收脚本（无 token 401、有 token 200、TESTING_KEY 旁路、白名单可访问） |

### 验收标准

1. ✅ 不带 `Authorization` 调用 `/api/v2/test-cases` 返回 401
2. ✅ 带正确 JWT 调用 `/api/v2/test-cases` 返回 200
3. ✅ 带 `TESTING_KEY` 头调用回归仍可通过（保留）
4. ✅ 白名单 `/health` `/docs` 不需要鉴权
5. ✅ smoke 回归通过
6. ✅ 前端登录后可正常访问页面（手动验证）
7. ✅ 前端 build 通过

### 配置示例

```bash
# .env
API_AUTH_ENABLED=true
JWT_SECRET=<64位随机串>
API_KEYS=key1,key2     # 可选：服务间调用
```

---

## 2. Phase D2 — 文件上传 MIME 严格校验

### 目标
防止上传伪装扩展名的恶意文件（zip 中藏 exe、图片中藏脚本等）。

### 范围

| 文件 | 操作 |
|---|---|
| `utils/file_validation.py` | **新增** — 基于 `python-magic` 或文件头 magic bytes 校验真实 MIME |
| `routes/code_compare_routes.py` | `upload_snapshot` 调用 MIME 校验，拒绝声明 zip 但实际不是的文件 |
| `routes/upload_routes.py` (如有) | 同样接入 |
| `requirements.txt` | +`python-magic-bin` (Windows) 或 `python-magic` |
| `scripts/test_file_upload_security.py` | **新增** — 上传伪装文件返回 400 |

### 验收标准

1. ✅ 上传 `.zip` 但内容是 `.exe` → 400 拒绝
2. ✅ 正常 zip 上传成功
3. ✅ 上传超过大小限制 → 413
4. ✅ 上传请求保持现有 zip slip / 敏感文件过滤生效

---

## 3. Phase D3 — API Rate Limit

### 目标
防止接口滥用，尤其是耗资源的 AI 调用、git clone、文件上传。

### 范围

| 文件 | 操作 |
|---|---|
| `requirements.txt` | +`slowapi` |
| `backend/rate_limit.py` | **新增** — slowapi limiter 实例 + 策略配置 |
| `backend/app.py` | 注册 limiter |
| `routes/code_compare_routes.py` | `clone_repo` / `upload_snapshot` / `analyze_*` 加 `@limiter.limit("5/minute")` |
| `routes/ai_*.py` | AI 接口加 `@limiter.limit("20/minute")` |
| `scripts/test_rate_limit.py` | **新增** — 触发限流返回 429 |

### 验收标准

1. ✅ 5 秒内连续 6 次 clone-repo → 第 6 次 429
2. ✅ 普通业务接口（CRUD）不受限流影响
3. ✅ smoke 回归通过

---

## 4. Phase D4 — 集中化日志脱敏

### 目标
统一处理日志中可能出现的 token / cookie / authorization / password / api_key，消除散落的脱敏函数。

### 范围

| 文件 | 操作 |
|---|---|
| `backend/logging_config.py` | +`SensitiveDataFilter`（python logging.Filter）拦截所有 LogRecord |
| `routes/code_compare_routes.py` | 移除 `_sanitize_git_url_for_log`，改由 logger filter 自动脱敏 |
| `services/*` | 凡是 `logger.info(token)` / `logger.warning(url)` 都受统一 filter 保护 |
| `scripts/test_log_sanitization.py` | **新增** — 写入含 token 的日志，校验输出中已脱敏 |

### 验收标准

1. ✅ `logger.info("token=abc123def456ghi")` 日志输出 `token=***REDACTED***`
2. ✅ `logger.warning("https://abc123@gitlab.com/repo.git")` 输出 `https://***@gitlab.com/repo.git`
3. ✅ 现有功能日志正常输出

---

## 5. Phase E（小步收尾，非必须）

### E1 — code_compare 前端来源标签
- 列表/详情页显示 `数据来源: DB | legacy_json`
- 仅前端改动，不影响后端

### E2 — legacy backend_api_server.py 缩减
- 删除已迁移到 V2 的路由（前提：Phase D1 鉴权完成、再无生产环境依赖）
- 谨慎：保留 38 处 `test_cases_db` 中确实只在 legacy 文件中使用的部分

---

## 6. 推荐执行顺序

```
Phase D1 (鉴权)  → 价值最高，先做
   ↓
Phase D3 (限流)  → 与 D1 协同，限流粒度按 user/api_key
   ↓
Phase D2 (MIME) → 独立，可与 D3 并行
   ↓
Phase D4 (日志) → 收尾治理
   ↓
Phase E1 + E2  → 可选，根据时间安排
```

**单阶段预估工作量**:
- D1: 1 天（含前端联调）
- D2: 0.5 天
- D3: 0.5 天
- D4: 0.5 天
- E1 + E2: 0.5 天

---

## 7. 每阶段共同约束（适用所有 Phase D/E）

### 必须遵守
1. ✅ 每个阶段独立 feature 分支：`feature/phase-d1-api-auth` 等
2. ✅ 每个阶段独立验收脚本，FAIL=0 才能合并
3. ✅ smoke 回归 + 前端 build 必须通过
4. ✅ 不得引入新 `allow_origins=["*"]` 等已知安全反模式
5. ✅ 验收脚本必须通过 `scripts/test_security_hardening.py`（防止 C2 收口被回退）
6. ✅ commit message 遵循 `<type>: <subject>` 形式（`feat: / fix: / chore: / docs:`）

### 不得做
1. ❌ 不删 legacy JSON 数据文件
2. ❌ 不删 `backend_api_server.py`（除非 Phase E2 明确批准）
3. ❌ 不重构现有 React 页面（除登录页接鉴权外）
4. ❌ 不引入新数据库（继续 SQLite）
5. ❌ 不绕过 TESTING_KEY 回归旁路

---

## 8. 依赖与风险

| 依赖项 | 风险 | 备注 |
|---|---|---|
| Python `python-magic-bin` (D2) | Windows 安装可能需要 vcredist | 备选: 自实现 magic bytes 校验 |
| Python `slowapi` (D3) | 0.1.x 与 FastAPI 中间件兼容性 | 锁版本到 `0.1.9` |
| JWT 密钥泄漏 (D1) | 如 `.env` 误提交风险 | 保持 `.env` 在 `.gitignore`，密钥强度 ≥ 64 字节 |
| 前端登录回归 (D1) | 现有 `Login.jsx` 是否完整 | 先在测试环境验证 |
| Logger Filter 性能 (D4) | 每条日志都过 regex | 仅在 INFO 及以下级别启用，正则提前编译 |

---

## 9. 验收脚本汇总（D 阶段累积）

| 脚本 | 阶段 | 检查项数 |
|---|---|---|
| `scripts/test_api_auth.py` | D1 | 8+ |
| `scripts/test_file_upload_security.py` | D2 | 6+ |
| `scripts/test_rate_limit.py` | D3 | 5+ |
| `scripts/test_log_sanitization.py` | D4 | 6+ |
| `scripts/test_security_hardening.py` | C2（已存在）| 16 |

**累积安全验收**: ≥ 41 项

---

## 10. 明天开工 Checklist

- [ ] 拉取最新代码：`git fetch origin && git checkout feature/phase-c2-security-hardening`
- [ ] 阅读本文档，确认 Phase D1 范围
- [ ] 新建分支：`git checkout -b feature/phase-d1-api-auth`
- [ ] 先写验收脚本 `scripts/test_api_auth.py`（TDD）
- [ ] 实现 `backend/auth_middleware.py` + `routes/auth_routes.py`
- [ ] 前端 `api.js` 拦截器 + `Login.jsx` 联调
- [ ] 跑全量回归（`run_regression_all.py --profile core`），确认 FAIL=0
- [ ] 跑 `test_security_hardening.py`，确认 C2 收口未被破坏
- [ ] 前端 build
- [ ] commit + push + 输出 PhaseD1 实施报告 `docs/PhaseD1_api_auth_report.md`

---

## 附录 A — 已知不在 Phase D 范围内的事项

如果想做以下事项，需要重新立项：
- 多租户 / 工作空间隔离
- 完整审计日志系统（结构化日志、ELK 接入）
- 容器化部署 (Docker Compose 升级)
- AI Provider 切换（已在 P4 路线图）
- 性能压测（locust / k6）
- 国际化 i18n

---

> **维护说明**: 本文档每完成一个阶段后追加一节「Phase Dx 实际完成情况」，并在表格中标记 ✅。
