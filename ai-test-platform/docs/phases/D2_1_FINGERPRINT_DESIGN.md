# D2-1 Finding 内容指纹去重设计文档

> **版本**：D2-1（工程风险收敛阶段）
> **目标**：在不改数据库 schema、不改前端的前提下，通过内容指纹（content fingerprint）+ 项目作用域（project scope）双因子，避免同一缺陷被重复转 TAPD bug。
> **范围**：仅触达 `services/tapd_service.py` / `routes/code_compare_routes.py` 与新增 `scripts/test_finding_fingerprint.py`。

---

## 1. 背景与目标

### 1.1 当前重复保护盲区

平台现有的"重复推送 TAPD"保护**仅靠** `finding.tapd_bug_id` 字段是否非空判断（`@G:\AI项目\ai测试\ai-test-platform\routes\code_compare_routes.py:1437` 单条；`@G:\AI项目\ai测试\ai-test-platform\routes\code_compare_routes.py:1732` 批量）。在以下场景会**漏掉**：

1. **同项目重新跑 analyze** → 新 `report_id` + 新 `finding_id`，同一缺陷被当成新 bug 推送。
2. **同一份报告里两条相似 finding**（如同模块 `missing` + `risk` 覆盖同一字段）→ 两条都推。
3. **单条 push 后用批量 push（`skip_already_pushed=False`）** → 重推。

### 1.2 目标

| 目标 | 验收标准 |
|---|---|
| 同一项目内、内容等价的 finding，第二次推送被识别为去重命中 | `requests.post` 不被调用，目标 finding 写入 `dedup_by_fingerprint=true` |
| 误报 finding 即使含 `tapd_bug_id` 也**不**作为 dedup source | source 池中不含 `manual_status==false_positive` |
| 不同项目的同 fingerprint 不互相 dedup | 索引 key = `(project_scope, fingerprint)` 元组隔离 |
| 老数据（无 fingerprint 字段）零迁移可用 | 启动期懒计算到内存，下次 `_save_report` 时自然落盘 |
| 算法稳定可审计 | 写入 `content_fingerprint_version=1` + `content_fingerprint_algorithm="sha256_32_v1"` |

---

## 2. 为什么选择 sha256_32_v1

### 2.1 决策

| 维度 | 选择 | 否决项 |
|---|---|---|
| 哈希算法 | **`hashlib.sha256`** | sha1（碰撞强度不足 + 行业普遍弃用方向）、md5（同上） |
| 输出长度 | **32 hex 字符**（128 bit 等价） | 16 hex（碰撞概率虽低但在跨项目长期累积时不够保险） |
| 算法标签 | **`sha256_32_v1`** | 匿名截断（无法追溯算法升级路径） |

### 2.2 理由

- **碰撞代价 vs 性能**：32 hex 字符（128 bit 等价）的生日攻击难度 ≈ 2^64 量级，在我们预期的累积 finding 规模（< 10^7）下碰撞概率可忽略；同时 sha256 在 Python `hashlib` 内是 C 实现，单条耗时 < 10μs，**不构成性能瓶颈**。
- **算法升级可追溯**：`content_fingerprint_algorithm = "sha256_32_v1"` 显式写入 finding，未来若引入 `sha256_32_v2`（如调整输入字段集合），可按算法标签做兼容性分支。
- **`content_fingerprint_version = 1`**：同时存数字版本号，便于 SQL 过滤 / 索引重建。
- **`32 hex` 也便于人工肉眼对比**：截屏时一行不会过长。

---

## 3. 为什么不改 DB schema

### 3.1 现状

`code_compare_findings` 表（`@G:\AI项目\ai测试\ai-test-platform\database\models.py:542`）**已经**没有 `tapd_bug_id` 等 7 个 TAPD 字段，平台一直运行在以下模式：

> JSON 文件（`data/code_compare/reports/*.json`）= 真值源
> DB = 部分镜像（仅核心列）
> 内存 `_reports` = 启动加载、推送/状态变更后增量回写 JSON

代码自身亦显式说明（`@G:\AI项目\ai测试\ai-test-platform\routes\code_compare_routes.py:847`）：

```text
# DB schema 缺 tapd_* 列，从 _reports 内存（持久化 JSON 来源）补齐
```

### 3.2 决策

`content_fingerprint` / `content_fingerprint_version` / `content_fingerprint_algorithm` / `dedup_by_fingerprint` / `dedup_source_finding_id` / `dedup_source_report_id` / `dedup_at` 沿用同一模式：**只写 JSON，不写 DB schema**。

### 3.3 收益

| 收益 | 说明 |
|---|---|
| 零 migration | 不需要 alembic、不需要重启时停服 |
| 零并发风险 | 单进程 + JSON 落盘，没有 DB 行锁 / 索引锁 |
| 与现有 TAPD 字段处理风格完全一致 | 维护者认知负担低 |
| 回滚成本 = 删字段 | 业务代码删去新增分支，JSON 字段自动 idle 不影响读 |

### 3.4 已知代价

- 老 finding 在被首次访问 / 推送 / 标记前，fingerprint 字段不会落盘 → **可接受**，因为索引在内存里已经有了，不影响行为。
- DB 镜像与 JSON 不一致 → 现状本就如此，本期不引入新差异。

---

## 4. 为什么引入 project_scope

### 4.1 风险场景

不同项目可能产生**字面上相同**的 finding：

- 项目 A `recycle-applet` 的「订单列表」模块 vs 项目 B `wms-applet` 的「订单列表」模块，二者代码不同、需求不同，但若仅以 `finding_type + module + field + code_item` 作为指纹输入，**会撞**。
- 此时若 A 已推送，B 会被错误地"复用"A 的 TAPD bug → **漏推**。

### 4.2 解决方案：以 project_scope 作为索引第一维

**索引 key = `(project_scope, content_fingerprint)`**，scope 不同自动不命中。

### 4.3 project_scope 取值优先级（取首个非空、非 None、strip 后非空者）

```
1. report.project_id          (字符串化)
2. report.project_name
3. report.repo_name
4. _clean_snapshot_name_for_scope(report.code_snapshot_name)
5. "global_unknown"
```

### 4.4 为什么**不**直接用 `code_snapshot_name`

`code_snapshot_name` 在历史报告中常包含**不稳定信息**：

| 不稳定模式 | 例 |
|---|---|
| 文件路径 | `D:\360Downloads\蓝点\recycle-applet-feature-1.2.3.zip` |
| 压缩后缀 | `.zip` / `.tar` / `.tar.gz` |
| 时间戳 | `_20260507161200` |
| 短 hash | `_a3f912` |
| 临时批次 | `_snapshot` / `_uploaded` |
| 反斜杠 | `\` 与 `/` 混用 |

若直接拼入 fingerprint 或索引 key，会让"同一项目两次上传"的 scope 不一致 → dedup 失效。

### 4.5 `_clean_snapshot_name_for_scope` 清洗规则

按顺序依次：

1. 取**最后一段**路径（去掉 `D:\xxx\` 部分）
2. 去掉 `.zip` `.tar` `.tar.gz` `.tgz` 后缀
3. 去掉 `_snapshot` / `_snapshots` / `_uploaded` 后缀
4. 去掉时间戳：`_\d{8,14}` / `\d{4}-\d{2}-\d{2}T?\d*`
5. 去掉短 hash：`_[0-9a-f]{6,}`（≥ 6 hex 字符的下划线段）
6. `\` → `/`
7. 多空格 → 单空格、`strip()`、`lower()`
8. 截断到 100 字符

---

## 5. 为什么不使用 line / finding_id / report_id / 敏感字段

### 5.1 不使用 `line number`

- **线号易变**：同一份代码经过格式化 / import 调整 / 注释插入，行号会跳。
- 若入指纹，会让"语义未变但格式变了"的 finding 被当成新 bug → 误推率上升。

### 5.2 不使用 `finding_id` / `report_id`

- `finding_id` / `report_id` 是**生成值**（`uuid4()` 派生），每次 analyze 都新生成。
- 若入指纹，"同项目重新分析"产生的 finding 永远 fingerprint 不同 → **dedup 永远失效**，即"伪稳定"。
- 这正是当前 dedup 盲区的根源。

### 5.3 不使用 `tapd_bug_id` / `tapd_url` / `tapd_status`

- 这些是**结果值**（推送 TAPD 后才有）：把它们入指纹会让"未推 vs 已推"被当成两个不同的 finding，**逻辑环**。
- 推送前查 fingerprint，推送后写回去 — 时序明确。

### 5.4 不使用 `token / password / api_key`（TAPD 配置）

- 任何形式的安全凭据**不入指纹输入**：避免日志意外打印 fingerprint 输入串后泄漏。
- 避免凭据轮换后旧 finding 全部失效。
- 单测会主动 assert：fingerprint 输入串中不含 `password` / `token` / `api_key` 关键字（用例 #14）。

---

## 6. fingerprint 输入字段定义

### 6.1 七维输入

| # | 维度 | 取值 |
|---|---|---|
| 1 | `project_scope` | §4.3 优先级链 |
| 2 | `finding_type` | `finding["type"].strip().lower()` |
| 3 | `requirement_key` | `finding["req_id"].strip()` 优先；空则 `finding["requirement"]` 取首个有意义短语，最长 80 字符 |
| 4 | `field_name` | 复用 `_extract_field_from_requirement(requirement_clean)` |
| 5 | `code_file` | `code_evidence.get("file") or ""` 经 `\→/` + lower + 仅取最后两段 |
| 6 | `code_item` | `code_evidence.get("code_item") or ""` strip + lower |
| 7 | `req_digest` | `requirement_clean` 全文经 `\s+ → ' '` 后**前 200 字符** |

### 6.2 拼接

```
raw = "|".join([
    "v=" + FP_VERSION,
    "alg=" + FP_ALGORITHM,
    "scope=" + project_scope,
    "type=" + finding_type,
    "rk=" + requirement_key,
    "fld=" + field_name,
    "cf=" + code_file,
    "ci=" + code_item,
    "rd=" + req_digest[:200],
])
content_fingerprint = sha256(raw.encode("utf-8")).hexdigest()[:32]
```

> 显式带 `v=` / `alg=` 前缀，便于将来引入 v2 时独立命名空间，不与 v1 撞。

### 6.3 空值兜底

- 任意维度为 `None` / 空字符串 → 替换为 `""`，**不**抛异常。
- 即使所有维度都空（极端老 finding），也能算出稳定的 32 hex（输入串为 `v=1|alg=sha256_32_v1|scope=|type=|rk=|fld=|cf=|ci=|rd=`），但这种 finding 不会有 `tapd_bug_id`，**不会成为 dedup source**，对系统无害。

---

## 7. 命中去重后的字段语义

### 7.1 命中条件（同时满足）

```
A. (target.project_scope, target.content_fingerprint)
   == (source.project_scope, source.content_fingerprint)
B. source.tapd_bug_id 非空
C. source.manual_status != "false_positive"
D. target != source（同一 finding 不与自己 dedup）
```

### 7.2 命中后写入 target finding 的字段

| 字段 | 取值 | 说明 |
|---|---|---|
| `content_fingerprint` | 已有则保留，否则补 | 懒计算结果 |
| `content_fingerprint_version` | `1` | 算法版本号 |
| `content_fingerprint_algorithm` | `"sha256_32_v1"` | 算法标签 |
| `tapd_bug_id` | `source.tapd_bug_id` | **复用**对方已建 bug |
| `tapd_url` | `source.tapd_url` | 复用 |
| `tapd_status` | `source.tapd_status`（若 source 有） | 复用，未取到则不写 |
| `tapd_status_name` | `source.tapd_status_name`（若 source 有） | 复用，未取到则不写 |
| `tapd_pushed_at` | `source.tapd_pushed_at`（若 source 有） | **复用 source 的时间，不伪造当前时间** |
| `dedup_by_fingerprint` | `True` | **必填**审计标记 |
| `dedup_source_finding_id` | `source.finding_id` | 审计追溯 |
| `dedup_source_report_id` | `source.report_id`（若可解析） | 审计追溯 |
| `dedup_at` | `datetime.now().isoformat()` | **必填**dedup 发生时间 |

### 7.3 关键语义：审计可分辨

| 字段 | 真实推送 | 去重复用 |
|---|---|---|
| `tapd_bug_id` | ✅ | ✅（与 source 相同） |
| `tapd_pushed_at` | 真实推送时间 | source 的推送时间 |
| `dedup_by_fingerprint` | 缺失 | **`True`** |
| `dedup_at` | 缺失 | **当前时间** |
| `dedup_source_finding_id` | 缺失 | source.finding_id |

> **任何后续审计**（统计真实 TAPD 推送次数、定位重复项）只需 `dedup_by_fingerprint == True` 即可识别去重项，**不**会把 dedup 当成真实推送。

### 7.4 API 返回结构

#### 7.4.1 单条 push

```json
{
  "success": true,
  "already_pushed": true,
  "dedup_by_fingerprint": true,
  "dedup_source_finding_id": "f_xxxxxxxx",
  "bug_id": "1055833",
  "url": "https://www.tapd.cn/...",
  "message": "已通过内容指纹去重，复用源 finding 的 TAPD Bug"
}
```

#### 7.4.2 批量 push

```json
{
  "success": true,
  "data": {
    "total": 5,
    "pushed": 2,
    "skipped": 3,
    "dedup_by_fingerprint": 1,
    "results": [
      {"finding_id": "f_a", "status": "pushed", "bug_id": "..."},
      {"finding_id": "f_b", "status": "dedup_by_fingerprint",
       "bug_id": "...", "url": "...",
       "dedup_source_finding_id": "f_a"}
    ]
  }
}
```

---

## 8. 索引数据结构

### 8.1 内存结构

```python
_fingerprint_index: Dict[Tuple[str, str], dict] = {}
# key   = (project_scope, content_fingerprint)
# value = {
#   "finding_id": str,
#   "report_id":  Optional[str],
#   "tapd_bug_id": str,
#   "tapd_url":    str,
#   "tapd_status": Optional[str],
#   "tapd_status_name": Optional[str],
#   "tapd_pushed_at":  Optional[str],
#   "manual_status":   Optional[str],
# }

_fingerprint_index_built: bool = False
```

### 8.2 操作

| 操作 | 时机 | 行为 |
|---|---|---|
| `_build_fingerprint_index()` | 第一次 push 时（懒触发） | 扫 `_reports`，对每条**符合 source 条件**的 finding 注册到索引 |
| `_register_fingerprint(finding, report)` | push 成功后 / mark 状态后 | 增量加索引；若 finding 不符合 source 条件则忽略 |
| `_unregister_fingerprint(finding, report)` | `manual_status` 变 `false_positive` 时 | 增量移除 |
| `_lookup_dedup_source(scope, fp, exclude_finding_id)` | push 前查询 | 返回索引值或 None |

### 8.3 懒触发位置

仅在 `push_finding_to_tapd` 与 `batch_push_findings_to_tapd` 入口处执行 `_ensure_fingerprint_index()`：第一次执行时全量扫描，之后增量维护。

> 不在 `routes/code_compare_routes.py` 模块导入时构建，避免影响启动延迟与单元测试 import 行为。

---

## 9. 老数据兼容

### 9.1 finding 缺字段

| 缺什么 | 处理 |
|---|---|
| 缺 `content_fingerprint` | 懒计算（`_get_or_compute_fingerprint`），只写内存 |
| 缺 `content_fingerprint_version` / `_algorithm` | 同上 |
| 缺 `tapd_*`（未推送） | 不会成为 dedup source，无影响 |

### 9.2 落盘时机

- **不**在启动时主动 `_save_report` 全量落盘（避免大量 IO）。
- 任何已有的 `_save_report` 触发点（push、sync、mark、convert 等）会自然把懒补的字段一起落盘。

### 9.3 算法版本不匹配

- finding 中存的 `content_fingerprint_version != FP_VERSION` 时，重算新的并覆盖（D2-1 阶段不存在此情况，预留升级口）。

---

## 10. manual_status 变化的同步

### 10.1 触发点

`mark_finding_false_positive`（`@G:\AI项目\ai测试\ai-test-platform\routes\code_compare_routes.py:1141`）在 `_save_report` 之前调 `_unregister_fingerprint(finding, report)`。

### 10.2 反向（false_positive → 其他状态）

如果 finding 从 `false_positive` 改回其他状态：

- 现有 `confirm_finding_status` 端点（`@G:\AI项目\ai测试\ai-test-platform\routes\code_compare_routes.py:891` 起）允许任意 valid_statuses 互转。
- D2-1 **不**在此处主动 register（保守策略）：因为 dedup source 必须有 `tapd_bug_id`，而 `mark_false_positive` 不影响 `tapd_bug_id` 字段，只在状态再变化后**下次 push 触发懒重建**或**该 finding 自身再被推送**时通过 `_register_fingerprint` 回到索引。
- 这一保守策略可能导致**短暂期内**：原 false_positive finding 已被人工改回有效但仍未在索引中 → 不会成为 dedup source → 多推一次 bug 的概率上升。**已接受**，因为这是边缘场景（先改回有效后再次重新分析产生相同 finding）。

### 10.3 索引可手动重建（暗门）

`_build_fingerprint_index()` 设计为**幂等**：可在调试时反复调用，每次清空再重建，作为兜底机制。

---

## 11. 已知限制

| 限制 | 影响 | 缓解 |
|---|---|---|
| **字段提取不稳定**：`_extract_field_from_requirement` 依赖中文标点切句，少数 finding 可能抽到空 | 这部分 finding 的 fingerprint 区分度下降 → 命中率下降，但不会错配（其他维度兜底） | 已有 §6.1 第 7 维 `req_digest[:200]` 作为强区分兜底 |
| **跨 report 同 fingerprint 但不同 source** | 索引只记录第一个 source；后入的 source 不覆盖 | 这是预期行为：取最先入索引的有效 source 即可 |
| **manual_status 反向变更**（§10.2） | 短暂索引不一致 | 已记录，暗门 `_build_fingerprint_index()` 可重建 |
| **进程重启** | 索引清空，第一次 push 会重新全量扫描 | 167 条/报告级别，扫描耗时 < 100ms，不构成问题 |
| **TAPD 侧 bug 已被关闭/删除** | 仍会被 dedup，target finding 拿到失效 bug_id | 不在 D2-1 范围；属 D2-3 同步失败日志持久化 |
| **多进程部署** | 各进程内存索引独立，可能冲突 | 当前是单进程 FastAPI，**不构成问题**；多进程改造在 D3+ 范围 |
| **fingerprint 抗碰撞 32 hex** | 理论碰撞概率极低，但**非零** | 命中时返回 `dedup_source_finding_id`，人工可追溯审计 |

---

## 12. 测试用例清单（共 14 项）

> 详细实现见 `scripts/test_finding_fingerprint.py`。
> 全部测试**不联网、不写 DB、不真实推 TAPD**。

| # | 用例 | 期望 |
|---|---|---|
| 1 | 同一 finding 调用两次 `compute_finding_fingerprint` | fingerprint 完全相同 |
| 2 | sha256_32_v1 输出 | `len() == 32`，全部 hex 字符 |
| 3 | 改 `code_evidence.line` 不改其他 | fingerprint 不变 |
| 4 | 改 `finding_id` / `report_id` 不改其他 | fingerprint 不变 |
| 5 | 改 `finding_type` 从 missing → risk | fingerprint **变** |
| 6 | 改 `code_evidence.file` | fingerprint **变** |
| 7 | 同 fingerprint 但不同 project_scope | 不互相 dedup（lookup 返回 None） |
| 8 | 同 scope + 同 fp + source 有 tapd_bug_id | lookup 命中，返回 source 信息 |
| 9 | source.manual_status == false_positive | lookup **不**命中 |
| 10 | source 没有 tapd_bug_id | lookup **不**命中（即使 fp 相同） |
| 11 | 命中 dedup 时（mock `requests.post`）模拟单条 push | `requests.post` **未被调用**，target 写入 11 个字段 |
| 12 | 批量 push 中 dedup 与 真推混合 | results 列表中 dedup 项 `status == "dedup_by_fingerprint"`，统计字段正确 |
| 13 | 老 finding（无 fingerprint 字段） | `_get_or_compute_fingerprint` 能算出，懒补到内存 |
| 14 | fingerprint 输入串中**不含**敏感字段 | 不含 `password` / `token` / `api_key` / `tapd_bug_id` / `tapd_url` / `tapd_status` / `finding_id` / `report_id` / `line` 关键字 |

---

## 13. 测试结果

> 本节由 D2-1 开发会话首次运行结果回填（2026-05-07）。

### 13.1 `python scripts/test_finding_fingerprint.py`

```
================================================================
D2-1 Finding Fingerprint 单元测试
FP_VERSION=1  FP_ALGORITHM=sha256_32_v1
================================================================
  PASS: 01_fingerprint_stable
  PASS: 02_output_length_32_hex
  PASS: 03_line_does_not_affect
  PASS: 04_finding_id_report_id_not_affect
  PASS: 05_type_affects
  PASS: 06_code_file_affects
  PASS: 07_different_scope_no_cross_dedup
  PASS: 08_same_scope_fp_with_tapd_bug_id_hit
  PASS: 09_false_positive_source_not_hit
  PASS: 10_no_tapd_bug_id_source_not_hit
  PASS: 11_single_push_dedup_no_http
  PASS: 12_batch_push_dedup_mixed
  PASS: 13_legacy_finding_lazy_compute
  PASS: 14_no_sensitive_in_input
================================================================
PASS=14  FAIL=0  TOTAL=14
================================================================
```

**结论**：D2-1 14 项用例全部通过，FAIL=0。

### 13.2 `python scripts/test_finding_to_tapd_bug.py`（不退化检查）

```
=== 8/8 passed ===
```

涵盖：
- 纯组件类型【(矩形)】被丢弃 → 只剩模块前缀
- risk + high + 高置信 → major + 模块名
- 星号必填标识被清理
- inconsistencies 优先用作问题描述
- missing 高置信 + risk_level=high → minor (不再一律严重)
- missing 低置信 → trivial
- 历史字段 requirement_point 兼容
- 无 report_context 兜底用「白盒对比」

**结论**：finding → TAPD bug 字段生成逻辑零退化，8/8 通过。

### 13.3 `python scripts/acceptance_rc1.py`（RC-1 验收不退化）

```
======================================================================
RC-1 ACCEPTANCE  backend=http://127.0.0.1:8001  timeout=10.0s
======================================================================
[OK] 01_health - status=healthy, database.connected=true
[OK] 02_modules - 全部 40 个模块 true
[OK] 03_projects - GET /api/v2/projects -> 200
[OK] 04_test_cases - 200 OK total=4729
[OK] 05_test_runs - GET /api/v2/test-runs -> 200
[OK] 06_defects - GET /api/v2/defects -> 200
[OK] 07_dashboard_summary - GET /api/v2/dashboard/summary -> 200
[OK] 08_analytics_overview - GET /api/v2/analytics/overview -> 200
[OK] 09_code_compare_reports - GET /api/v2/code-compare/reports -> 200
[OK] 10_tapd_config - api_password 已脱敏 (value='******')
[WARN] 11_demo_status - Demo 未初始化（按 RC-1 规则不阻塞）
[OK] 12_test_selection - POST recommend -> 200
[OK] 13_quality_gate - GET /api/v2/quality-gates/default-config -> 200
[OK] 14_error_structure - 404 含字段 ['detail']
[OK] 15_sensitive_leak - 未发现疑似明文敏感值（JWT/Bearer/bcrypt/AWS/PEM/PAT/Slack 等）
======================================================================
SUMMARY
======================================================================
TOTAL:     15
PASS:      14
FAIL:      0
WARN:      1
SKIP:      0
EXIT_CODE: 0
```

**结论**：RC-1 既有 14 项工程基线全绿，FAIL=0，EXIT_CODE=0。WARN（demo_status）按 RC-1 规则不阻塞，与本次改动无关。

---

## 14. 触达文件清单

| 文件 | 操作 | 主要内容 |
|---|---|---|
| `services/tapd_service.py` | 新增 | `FP_VERSION` / `FP_ALGORITHM` 常量；`_clean_snapshot_name_for_scope` / `compute_project_scope` / `compute_finding_fingerprint` / `is_dedup_source_eligible` / `build_dedup_payload` / `apply_dedup_to_finding` 6 个纯函数 |
| `routes/code_compare_routes.py` | 修改 | `_fingerprint_index` / `_fingerprint_index_built` 模块级状态；`_get_or_compute_fingerprint` / `_build_fingerprint_index` / `_register_fingerprint` / `_unregister_fingerprint` / `_lookup_dedup_source` / `_ensure_fingerprint_index` 6 个工具函数；单条 push、批量 push、`mark_finding_false_positive` 3 个端点接入 |
| `scripts/test_finding_fingerprint.py` | 新增 | 14 个用例（§12） |
| `docs/D2_1_FINGERPRINT_DESIGN.md` | 新增 | 本文档 |

> **不**触达：`database/models.py`（不改 schema）、`frontend/`（不改前端）、`scripts/test_finding_to_tapd_bug.py`（不改既有测试）、`scripts/acceptance_rc1.py`（不改既有验收）。
