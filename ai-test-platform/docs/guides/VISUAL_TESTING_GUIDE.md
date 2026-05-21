# 视觉测试模块 · 工程级使用指南

最后更新：2026-05-08（企业级升级 Phase 1-8 完成）

## 1. 总览

视觉测试用于在 Web UI 自动化用例中**对页面截图做像素级回归**，发现意料之外的 UI 变化（布局漂移、字号变更、颜色错位等）。

```
配置 assertion(screenshot_match) → 执行 → 截图 → 对比基线 → 通过 / 失败 / 自动建基线
                                                ↓
                          失败 → 视觉测试中心审核 → 批准更新基线 / 调阈值 / 加 mask
```

## 2. 模块组成

| 层 | 文件 | 职责 |
|---|---|---|
| 引擎 | `services/visual_diff.py` | 像素 diff、SSIM、mask 屏蔽、sidecar metadata |
| 服务 | `services/visual_baseline_service.py` | 基线 CRUD + 批准 + 待审核扫描 |
| 路由 | `routes/visual_routes.py` | REST API（7 个端点） |
| Playwright 集成 | `services/playwright_engine.py` | `_execute_screenshot_match()` |
| 失败归因 | `services/failure_analysis.py` | 视觉失败 → category=`visual_diff` |
| 报告聚合 | `routes/report_routes.py` | `visual_summary` |
| 趋势 | `services/analytics_service.py:get_visual_trend` | 14 天趋势 |
| 前端主页 | `frontend/src/pages/VisualTesting.jsx` | 基线管理 + 待审核 |
| 用例配置 | `frontend/src/components/testcases/WebUICaseForm.jsx` | assertion 类型「📸 视觉对比」 |
| 用例结果 | `frontend/src/pages/TestCases.jsx` | 三图对比 + 批准按钮 |

## 3. 工作流

### 3.1 在用例中启用视觉对比

`Web UI 用例` 表单 → assertion → 类型选 `📸 视觉对比` → 填：
- **基准图名称**：例如 `login_page`、`order_list`，每个用例下唯一
- **阈值**：默认 `0.05`（5% 像素差异内通过），范围 `[0, 1]`

执行后：
- 首次：状态 `baseline_created`，**不算失败**
- 之后：与基线对比，diff_ratio ≤ 阈值 → `passed`，否则 `failed`

### 3.2 文件存放

```
data/artifacts/visual/
├── baselines/{baseline_id}.png            基线图
├── current/{baseline_id}_{run_id}.png     每次执行截图（不覆盖）
├── diff/{baseline_id}_{run_id}_diff.png   差异图（红色=变化区域）
└── meta/{baseline_id}.meta.json           sidecar 元数据
```

`baseline_id = {case_id}_{safe_name}`，例如 `tc_42_login_page`。

### 3.3 sidecar metadata 结构

```json
{
  "baseline_id": "tc_42_login_page",
  "case_id": "tc_42",
  "name": "login_page",
  "threshold": 0.05,
  "algorithm": "pixel",
  "masks": [{"x": 300, "y": 10, "w": 80, "h": 40}],
  "created_at": "2026-05-08T14:30:00",
  "updated_at": "2026-05-08T15:12:00",
  "updated_by": "alice",
  "last_run_id": "run-2026-05-08-001",
  "approve_count": 3,
  "history": [
    {"event": "created",  "run_id": "...", "by": "system", "at": "...", "note": "首次自动创建"},
    {"event": "approved", "run_id": "...", "by": "alice",  "at": "...", "note": "确认 UI 改版"},
    {"event": "config_updated", "by": "alice", "changed": ["threshold", "masks(1)"]}
  ]
}
```

## 4. UI 改版后审核流（关键工作流）

### 路径 A：从用例结果页一键批准
1. 跑完用例后，「视觉回归对比」区显示 ❌ 红色块
2. 点 **✓ 批准并更新基线**
3. 弹窗确认 → 用本次截图覆盖基线 → 写入 history
4. 下次执行就以新基线为准

### 路径 B：到视觉测试中心批量审核
1. 侧边栏 → **视觉测试**
2. **待审核** Tab → 看到所有近 N 天失败的视觉用例（已去重，按 baseline_id 取最近一次）
3. 三图并排（基线 / 当前 / 差异），逐个审核
4. 点 **✓ 批准并更新基线** 或 **查看大图**

### 路径 C：基线详情精细化配置
1. 视觉测试中心 → **基线管理** Tab → 找到基线 → 点 **详情**
2. 抽屉打开：
   - 元数据卡片（updated_by、approve_count、last_run_id）
   - **对比配置**：阈值 / 算法（pixel/ssim）/ mask 区域增删
   - 基线图大图预览
   - 最近 9 张 diff 缩略图（每张可单独「✓ 用此 run 批准」）
   - 完整变更历史
   - 危险操作：删除基线

## 5. mask 区域屏蔽（解决误报最重要的工具）

### 用途
忽略页面里**频繁变动但与功能无关**的区域：
- 时间戳 / 倒计时
- 用户头像 / 登录用户名
- 广告位 / 推广 banner
- 随机 token / nonce

### 配置方式
进基线详情 → 编辑 → 添加 mask：

| 字段 | 含义 |
|---|---|
| `x` | 左上角 x（像素，相对截图原点） |
| `y` | 左上角 y |
| `w` | 宽 |
| `h` | 高 |

mask 一旦保存，下次执行会**双向屏蔽**（基线 + 当前图都把该矩形涂黑），让该区域永远不参与 diff。

### 效果验证（已通过自动化测试）
```
P4  mask 区域屏蔽
  [mask 屏蔽动态区域 → 由失败变 passed] PASS
```
（见 `scripts/test_visual_full_engineering.py`）

## 6. 算法选择

| 算法 | 说明 | 何时用 |
|---|---|---|
| **pixel** (默认) | `ImageChops` 取差，统计 r+g+b > 30 的像素占比 | 大部分场景，快 |
| **ssim** | 结构相似度（需 `pip install scikit-image`） | 抗锯齿/字体渲染微差，对感知差异更敏感 |

切换：基线详情 → 对比配置 → 算法下拉。失败时自动回退 pixel。

## 7. REST API

挂载点：`/api/v2/visual`

| Method | Path | 用途 |
|---|---|---|
| GET | `/baselines?case_id=&name=&limit=` | 列表 |
| GET | `/baselines/{baseline_id}` | 详情（meta + 最近 currents/diffs） |
| POST | `/baselines/{baseline_id}/approve` | 批准更新（body: `{source, run_id, by, note}`） |
| POST | `/baselines/{baseline_id}/config` | 更新阈值/算法/masks |
| DELETE | `/baselines/{baseline_id}` | 删除（body: `{delete_currents, delete_diffs}`） |
| GET | `/pending-reviews?days=&limit=` | 待审核扫描 |
| GET | `/stats` | 汇总统计 |

### 示例：批准基线

```bash
curl -X POST http://localhost:8000/api/v2/visual/baselines/tc_42_login_page/approve \
  -H "Content-Type: application/json" \
  -d '{"source":"specific_run","run_id":"run-001","by":"alice","note":"确认 UI 改版"}'
```

### 示例：配置 mask + 阈值

```bash
curl -X POST http://localhost:8000/api/v2/visual/baselines/tc_42_login_page/config \
  -H "Content-Type: application/json" \
  -d '{
    "threshold": 0.08,
    "algorithm": "pixel",
    "masks": [{"x":300,"y":10,"w":80,"h":40}],
    "by": "alice",
    "note": "屏蔽时钟"
  }'
```

## 8. 安全

- **路径穿越防御**：所有 baseline_id 必须匹配 `^[A-Za-z0-9_.\-\u4e00-\u9fff]+$` 且不含 `..`，所有路径经 `_safe_baseline_path()` 二次校验（abs_path 必须在 root 下）
- **静态文件**：`/visual/{baselines,current,diff}` 由 FastAPI StaticFiles 挂载，只读
- **基线删除**：备份为 `*.prev`（最近一份），可手动恢复

## 9. 数据清理

CLI 工具：

```bash
# 列出 7 天前的过期 current/diff（dry-run）
python scripts/cleanup_artifacts.py --type visual --older-than-days 7 --dry-run

# 真删除
python scripts/cleanup_artifacts.py --type visual --older-than-days 7 --delete

# 删 baseline（极危险，需双重确认）
python scripts/cleanup_artifacts.py --type visual-baselines --confirm-baselines --delete
```

`baselines/` 默认**永不被自动清理**（除非显式 `--type visual-baselines`）。

## 10. 测试与验证

```bash
# 工程级完整测试（15 个用例）
python scripts/test_visual_full_engineering.py

# 原 P2-5 MVP 测试（25 个用例，向后兼容）
python scripts/test_p2_5_visual_regression_mvp.py
```

测试覆盖：
- ✓ baseline_id 安全规则 + 路径穿越拦截（含 `..` / `/` / `\` / 控制字符）
- ✓ 中文 baseline_id 允许
- ✓ 首次执行 → 自动创建基线 + sidecar
- ✓ 相同截图 → passed
- ✓ 显著变化 → failed
- ✓ mask 屏蔽动态区域：由失败变 passed
- ✓ SSIM 算法切换 + 自动 fallback
- ✓ list/detail/approve/update_config/delete 服务函数
- ✓ FastAPI TestClient 全链路（含恶意 URL `..%2Fpasswd` 拦截）

## 11. 与失败归因/质量门禁联动

- 失败归因（`services/failure_analysis.py:163-171`）：检测到 `visual_failed` finding → category=`visual_diff` → 自动建议 `should_update_baseline`
- 质量门禁（`services/quality_gate_service.py`）：视觉失败可作为门禁因子
- 趋势看板（`/api/v2/analytics/visual-trend`）：14 天日级 visual_failed_count / max_diff_ratio

## 12. 企业级能力（Phase 1-4 升级）

### 12.1 命名空间隔离（Phase 1）

`baseline_id` 升级支持三个命名空间维度：**env / viewport / branch**。同一个 `case_id + name` 在不同维度下会产生**独立基线**，相互不踩踏。

#### 命名规则

```
baseline_id = {case_id}_{name}[@env][@viewport][@branch]
```

> 命名空间维度按需附加；缺省值是 `default`（不出现在 id 中，向后兼容旧基线）。

| 维度 | 默认 | 典型值 | 示例 baseline_id |
|---|---|---|---|
| env | `default` | `dev` / `sit` / `prod` | `tc_42_login@prod` |
| viewport | `default` | `1920x1080` / `375x667` | `tc_42_login@default@1920x1080` |
| branch | `default` | `main` / `feature_x` | `tc_42_login@default@default@feature_x` |

#### 引擎自动注入

`PlaywrightEngine` 在 `_execute_screenshot_match()` 时自动从执行上下文采集：

| 字段 | 来源 |
|---|---|
| `env` | 用例所属 environment.name 或 `EXECUTOR_ENV` 环境变量 |
| `viewport` | playwright `page.viewport_size` → `{w}x{h}` |
| `branch` | `GIT_BRANCH` 环境变量（可在 CI 注入） |

> 用户**无需在 assertion 里手填**这三个字段，自动隔离。

#### REST API 升级（向后兼容）

```
GET /api/v2/visual/baselines?env=prod&viewport=1920x1080&branch=main
GET /api/v2/visual/namespaces        # 返回当前所有出现过的 env/vp/branch
```

#### 批量操作 API

| Endpoint | 用途 | 上限 |
|---|---|---|
| `POST /api/v2/visual/bulk/approve` | 批量批准 | 200 个/次 |
| `POST /api/v2/visual/bulk/delete`  | 批量删除 | 200 个/次 |
| `POST /api/v2/visual/bulk/config`  | 批量改阈值/算法/mask | 200 个/次 |

部分失败不会终止其余项，返回 `{success_count, fail_count, results: [...]}`。

#### 前端

「基线管理」Tab 新增：
- 三个命名空间下拉筛选（env / viewport / branch）
- 表格行 checkbox 多选 + 全选
- 选中后显示批量操作栏：批量批准 / 批量改阈值 / 批量删除

### 12.2 元素级 selector mask（Phase 2）

旧 mask 只支持**手填矩形坐标**——但页面布局一变，坐标就漂了。新增 **selector mask**：直接绑定 CSS / Playwright selector，**bbox 由引擎在每次执行时实时解析**。

#### Mask 类型

```jsonc
// 矩形（旧）
{"type": "rect", "x": 300, "y": 10, "w": 80, "h": 40}

// 选择器（新）—— bbox 在运行时填充
{
  "type": "selector",
  "selector": ".timestamp",        // 任意 CSS / Playwright selector
  "padding": 4                      // 可选：bbox 外扩像素，默认 0
}
```

#### 工作流

1. 在视觉测试中心 → 基线详情 → **编辑** → **+ 选择器**
2. 填 selector（例如 `[data-testid="clock"]`）和可选 padding
3. 保存。下次执行时引擎会：
   - 在截图前调用 `page.locator(sel).first.bounding_box()` 解析 bbox
   - 把 bbox（含 padding 外扩）一起填回 mask 配置
   - 用解析后的 bbox 屏蔽截图里的对应矩形
4. UI 详情页会显示「✓ bbox: x,y w×h」标签，方便排查

#### 不可见元素自动跳过

如果 selector 在当次执行时不可见（display:none / 不存在），该 mask 会被静默跳过，不影响其他 mask 生效，不报错。

#### 兼容性

旧 sidecar 中无 `type` 字段的 mask 会自动按 `rect` 处理，无须迁移。

### 12.3 写并发文件锁（Phase 3）

sidecar JSON 是 read-modify-write 模式，原本在并发批准/配置更新时存在丢写风险（A 读出，B 读出，A 写，B 写覆盖了 A 的修改）。

#### 实现

`services/visual_diff.py` 提供两套原语：

```python
from services.visual_diff import meta_lock, update_meta_atomic

# 显式锁
with meta_lock(bid, timeout=10):
    meta = read_meta(bid)
    meta["xxx"] = ...
    write_meta(bid, meta)

# 推荐：函数式原子更新
update_meta_atomic(bid, lambda meta: {**meta, "xxx": ...})
```

特性：
- **跨平台**：`os.O_CREAT | os.O_EXCL` 抢占式创建 `.lock` 文件，Windows + POSIX 同语义，零依赖
- **跨进程**：`gunicorn -w N` 多 worker 也安全
- **超时**：默认 10s 拿不到锁抛 `TimeoutError`
- **stale lock 自愈**：超过 60s 未释放的锁会被下一位获取者自动清理（防止崩溃残留）
- **原子写**：`write_meta` 用 `临时文件 + os.replace`，永远不会读到半截 JSON

#### 已被锁保护的写路径

| 函数 | 保护原因 |
|---|---|
| `compare_screenshot` 首跑创建基线 | 双进程同时首跑会双复制 |
| `compare_screenshot` 更新 last_run_id | 防丢失 last 标记 |
| `approve_baseline` | 备份 + 覆盖 + history append 串行化 |
| `update_baseline_config` | read-modify-write 原子化 |

#### 验证

`scripts/test_visual_enterprise_phase3.py` 实跑了 8 线程并发 approve、8 线程并发 update_config、6 线程并发首跑、4 进程并发 approve，全部通过：history 长度严格等于 N，`approve_count == N`，无丢写。

### 12.4 Webhook 通知（Phase 4）

视觉对比失败/基线变更后，可以**主动推送事件**到外部系统（飞书机器人、Slack、自建监控、CI 触发器等）。

#### 配置（环境变量）

| 变量 | 必填 | 说明 |
|---|---|---|
| `VISUAL_WEBHOOK_URL` | ✓ | 收件方 URL；不设则完全静默 |
| `VISUAL_WEBHOOK_SECRET` |  | 设了会带 `X-Visual-Signature: sha256=...` 头（HMAC-SHA256） |
| `VISUAL_WEBHOOK_TIMEOUT` |  | 单次发送超时秒数，默认 5 |
| `VISUAL_WEBHOOK_EVENTS` |  | 逗号分隔的事件白名单；不设则订阅除 `visual.diff.passed` 外所有事件 |

#### 事件清单

| 事件名 | 触发时机 |
|---|---|
| `visual.baseline.created` | 首次执行自动创建基线 |
| `visual.diff.failed` | 对比失败（diff_ratio > threshold） |
| `visual.diff.passed` | 对比通过（默认不订阅，需显式加白名单） |
| `visual.baseline.approved` | 调用 approve_baseline 成功 |
| `visual.baseline.config_updated` | 阈值/算法/mask 变更 |
| `visual.baseline.deleted` | 基线被删除 |

#### 请求体格式

```json
POST {VISUAL_WEBHOOK_URL}
Content-Type: application/json
X-Visual-Event: visual.diff.failed
X-Visual-Signature: sha256=<hmac>     // 仅当配了 secret

{
  "event": "visual.diff.failed",
  "ts": "2026-05-08T16:00:00",
  "source": "visual_testing",
  "data": {
    "baseline_id": "tc_42_login@prod",
    "case_id": "tc_42",
    "name": "login",
    "run_id": "run-001",
    "env": "prod", "viewport": "1920x1080", "branch": "main",
    "diff_ratio": 0.123,
    "threshold": 0.05,
    "algorithm": "pixel",
    "masks_applied": 2,
    "diff_path": "tc_42_login@prod_run-001_diff.png"
  }
}
```

#### 主流程零阻塞

发送在**后台 daemon 线程**进行，HTTP 失败/超时**永远不会拖垮**视觉对比/批准主流程，只会写一条 warning 日志。

#### 在 UI 中联调

视觉测试中心 → **Webhook 通知** Tab：
- 显示当前 URL/Secret/Timeout/订阅状态
- 提供「发送测试事件」按钮：可选事件类型 + 可选自定义 payload，一键打到真实 URL（或 dry_run 模式提示未配 URL）

#### 验证 HMAC 签名（接收方示例 Python）

```python
import hmac, hashlib

def verify(body: bytes, sig_header: str, secret: str) -> bool:
    if not sig_header.startswith("sha256="):
        return False
    expected = "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(sig_header, expected)
```

### 12.5 e2e 集成测试（Phase 5）

为前 4 期所有改造增加了**真 chromium 端到端验证**，不再 mock：

`scripts/test_visual_enterprise_phase5_e2e.py`：
- 起 headless chromium，data URL 加载内嵌 HTML
- 验证：命名空间自动注入 + selector mask 真实 bbox 解析 + 不可见元素容错 + Webhook 全链事件序列 + viewport 兜底

附带修复了关键 bug：原 `compare_screenshot` 在 sidecar 已存 selector mask 但 `engine` 又传入 resolved_masks 时，会**优先使用 sidecar 未解析版本（无 bbox）**导致 selector mask 实际不生效。修复后调用方传入 masks（非 None）一律优先生效。

### 12.6 基线版本历史 + 回滚（Phase 6）

每次创建/批准/回滚都自动归档为一个**独立物理副本**，可双向回滚。

#### 数据结构

- 物理：`data/artifacts/visual/versions/{bid}/{vid}.png`，每基线一个独立子目录
- sidecar：新增 `versions: [...]`，每条含 `{id, at, by, size, source, from_run_id, note, file}`
- `source` 取值：`created` / `approved` / `pre_rollback` / `rollback`

#### 保留策略

环境变量 `VISUAL_KEEP_VERSIONS`（默认 5，范围 [1, 50]）。超过上限时**最旧版本的物理文件 + sidecar 条目同时剪掉**，并发 approve 下也保持一致。

#### REST API

| Method | Path | 用途 |
|---|---|---|
| GET | `/baselines/{bid}/versions` | 列出版本（最新在最后），含 `preview_url` 可直接在浏览器打开 |
| POST | `/baselines/{bid}/rollback` | body `{version_id, by, note}`：回滚到指定版本，自动 snapshot 当前为 `pre_rollback`，写 history `rolled_back` 事件 |

#### UI

视觉测试中心 → 基线详情 → 「版本历史」面板：
- 卡片网格展示每个版本（缩略图 + source 颜色标 + 操作人/时间/备注）
- 当前生效版本带蓝色高亮 + 「当前」标签
- 旧版本可一键「⟲ 回滚到此版本」（前置确认对话框说明会自动留存当前为 pre_rollback）

### 12.7 Webhook 重试 + 死信队列（Phase 7）

#### 重试策略

后台 daemon 线程内**指数退避重试**，默认 1s / 2s / 4s（共 1+3=4 次尝试）：

| 环境变量 | 默认 | 说明 |
|---|---|---|
| `VISUAL_WEBHOOK_MAX_RETRIES` | 3 | 重试次数（总尝试 = 1 + 此值） |
| `VISUAL_WEBHOOK_BACKOFF_BASE` | 1.0 | 退避基数（秒）；第 i 次重试睡 base × 2^(i−1) |

#### 死信队列（DLQ）

所有重试失败的事件自动写入 **独立 sqlite 文件** `data/visual_webhook_dlq.sqlite`（不污染主 DB）。表结构：

```
id | event_type | payload_json | last_error | attempts | created_at | last_attempt_at | resolved | resolved_at
```

#### REST API

| Method | Path | 用途 |
|---|---|---|
| GET | `/webhook/dead-letters?limit=&include_resolved=&event_type=` | 死信列表 + stats |
| POST | `/webhook/dead-letters/{id}/retry` | 手动重发；成功标 resolved，失败 attempts++ 留库 |
| DELETE | `/webhook/dead-letters/{id}` | 删除一条 |

#### UI

视觉测试中心 → Webhook 通知 Tab → 新增「死信队列」面板：
- 头部 stats badge：未解决数（红色高亮）+ 各事件类型分布
- 列表卡片：事件类型/attempts/last_error/payload 折叠
- 「🔄 重发」按钮（resolved 后自动隐藏）+ 「删除」按钮
- 顶部 `含已解决` checkbox 切换可见性

### 12.8 mask 拖拽标注器（Phase 8）

基线详情 → 编辑模式下，基线图变成**可拖拽画框**的画布：

- **零依赖**：纯 SVG 叠加在原图上，无需 react-konva 等
- **自动尺寸映射**：图像 naturalSize（截图原始像素） ↔ displaySize（DOM 渲染尺寸）双向换算
- **画框**：editable 时鼠标光标变 crosshair，按下→拖动→松开 即生成新 rect mask（坐标自动换算回原始像素）
- **可视化已有 mask**：rect 用半透明红色，selector（已解析 bbox）用半透明紫色虚线
- **点击删除**：editable 模式下点击红色 rect mask 直接删除
- **响应窗口缩放**：window resize 时自动重新测量
- **超小框忽略**：< 4×4 像素的拖拽不会创建 mask，防止误触

## 13. 测试矩阵（全 76 用例）

```bash
# 工程级原始测试（向后兼容）
python scripts/test_visual_full_engineering.py                # 15/15

# Phase 1 命名空间 + 批量
python scripts/test_visual_enterprise_phase1.py               # 16/16

# Phase 2 元素级 selector mask
python scripts/test_visual_enterprise_phase2.py               # 11/11

# Phase 3 写并发文件锁（含 4 进程并发）
python scripts/test_visual_enterprise_phase3.py               # 9/9

# Phase 4.1 Webhook 通知
python scripts/test_visual_enterprise_phase4_webhook.py       # 6/6

# Phase 5 e2e 集成（真起 chromium）
python scripts/test_visual_enterprise_phase5_e2e.py           # 5/5

# Phase 6 基线版本历史 + 回滚
python scripts/test_visual_enterprise_phase6_versions.py      # 8/8

# Phase 7 Webhook 重试 + 死信队列
python scripts/test_visual_enterprise_phase7_retry_dlq.py     # 6/6
```

测试覆盖能力清单：
- ✓ baseline_id 路径穿越拦截 + 中文支持
- ✓ env / viewport / branch 三维隔离 + 自动从 page.viewport_size 兜底
- ✓ namespaces 反向枚举、按维度筛选
- ✓ bulk_approve / bulk_delete / bulk_update_config 部分失败容忍
- ✓ rect / selector mask 混合应用，selector 不可见元素自动跳过
- ✓ **mask 优先级 fix**：调用方显式传入的已 resolved masks 不会被 sidecar 未解析版本覆盖
- ✓ 文件锁互斥 / 释放重获 / 超时 / stale 自愈 / 原子写不留 .tmp
- ✓ 8 线程并发 approve / update_config 不丢写；6 线程并发首跑只创建一次；4 进程并发 approve 跨进程互斥
- ✓ Webhook 6 事件全投递、白名单订阅、HMAC 签名、URL 缺失静默
- ✓ Webhook 指数退避重试，中途成功不入 DLQ，最终失败入 DLQ
- ✓ DLQ CRUD（list/get/delete/stats），UI 重发成功标 resolved，失败 attempts++
- ✓ e2e 真 chromium：selector mask 实时屏蔽 .timestamp 区域 → 由失败转通过
- ✓ 基线版本：创建/批准/回滚自动归档；超 keep 上限剪枝（物理 + sidecar 一致）；并发 approve 下数量与文件一致；rollback 双向恢复 + 自动留 pre_rollback

## 14. 已知限制 & 下一步

| 限制 | 影响 | 优先级 |
|---|---|---|
| 仅 chromium 浏览器（`playwright_engine.py`） | 跨浏览器视觉对比做不了 | 中 |
| 没有 SSIM 默认安装 | 用户需自行 `pip install scikit-image` | 低 |
| DLQ 重发是单条手动 | 大批量恢复需循环点击；可后续加 bulk_retry | 低 |
| selector 解析失败仅日志记录 | 频繁失败时人工不易感知；可后续上报 webhook 自身事件 | 低 |
| mask 拖拽暂未支持「在截图上点选元素自动生成 selector」 | 仍需手写 selector 字符串 | 低 |
