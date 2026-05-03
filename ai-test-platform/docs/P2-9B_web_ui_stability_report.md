# P2-9B Web UI 稳定性增强报告

## 概述

P2-9B 阶段聚焦 Web UI 自动化测试的执行稳定性，实现了 retry 重试机制、flaky 标记、selector 稳定性评分、等待策略增强、执行前环境检查、artifact 清理脚本，以及前端稳定性摘要展示。

## 新增 / 修改文件

| 文件 | 变更类型 | 说明 |
|------|---------|------|
| `services/web_ui_stability.py` | **新增** | 核心稳定性服务：selector 评分、等待策略分析、preflight 检查、retry/flaky 辅助 |
| `services/playwright_engine.py` | 修改 | `wait_for` action 增强：支持 `url_contains`、`text_visible`、`visible/attached/detached/hidden`、`network_idle` |
| `routes/case_execute_routes.py` | 修改 | 单用例执行集成 preflight、selector scoring、retry、flaky、stability 信息 |
| `routes/web_ui_batch_routes.py` | 修改 | 批量执行集成 preflight、selector scoring、retry、flaky、stability summary |
| `scripts/cleanup_artifacts.py` | **新增** | Artifact 清理脚本，支持 dry-run/delete、baselines 保护 |
| `scripts/test_p2_9b_web_ui_stability.py` | **新增** | P2-9B 专项测试脚本，34 个测试点 |
| `scripts/run_regression_all.py` | 修改 | 注册 P2-9B 测试到回归套件 |
| `frontend/src/pages/TestRunDetailV2.jsx` | 修改 | 新增重试信息、Selector 稳定性、等待策略警告展示面板 |
| `frontend/src/pages/ReportDetail.jsx` | 修改 | Web UI 证据摘要新增稳定性指标行 |

## 功能详情

### 1. Retry 重试机制

- **配置方式**：`execution_config` 中设置 `retry_enabled: true`，`retry_count: N`（上限 3），`retry_on: [类别列表]`
- **可重试类别**：`page_timeout`、`network_error`、`selector_not_found`、`browser_crash`、`navigation_error`
- **安全约束**：最多重试 3 次，`unknown` 类别不自动重试
- **flaky_candidate 标记**：首次失败 → 重试成功 → 自动标记为 flaky_candidate

### 2. Selector 稳定性评分

| 稳定性等级 | 分数范围 | 典型选择器 |
|-----------|---------|-----------|
| 高 (high) | 90-100 | `[data-testid="..."]`、`[role="..."]`、`[aria-label="..."]` |
| 中 (medium) | 65-80 | `#id`、`[name="..."]`、`[placeholder="..."]` |
| 低 (low) | 20-35 | `:nth-child(...)`、XPath `//div/...`、深层嵌套 CSS |

- 每个步骤的 target 自动评分
- 低分 selector 列入 `unstable_selectors` 列表并在前端高亮显示
- 整体 `selector_score` 为所有步骤的平均分

### 3. 等待策略增强

`wait_for` action 的 `value` 字段新增以下策略：

| value | 说明 |
|-------|------|
| `url_contains` | 等待 URL 包含 target 字符串 |
| `text_visible` | 等待页面文本可见 |
| `visible` / `attached` / `detached` / `hidden` | 等待 selector 达到指定状态 |
| `network_idle` | 等待网络空闲 |
| *(空)* | 默认 `wait_for_selector` |

固定等待 ≥3000ms 会产生警告，建议替换为语义化等待。

### 4. 执行前环境检查 (Preflight)

检查项：
- 用例类型是否为 `web_ui`
- 步骤列表不为空
- 断言是否配置（无断言只 warning）
- 相对路径 goto 是否有 base_url
- base_url 可达性（超时只 warning）
- Playwright 是否安装
- trace / screenshot 目录可写

### 5. Artifact 清理脚本

```bash
# 干运行（只列出，不删除）
python scripts/cleanup_artifacts.py --dry-run --older-than-days 7

# 真正删除
python scripts/cleanup_artifacts.py --delete --older-than-days 7 --type screenshots

# 清理 baselines（需二次确认）
python scripts/cleanup_artifacts.py --delete --type visual-baselines --confirm-baselines
```

安全措施：
- 默认 dry-run
- 不删除 `.env`、`.db`、`.py` 等受保护文件
- baselines 默认受保护，需 `--confirm-baselines` 确认
- 支持 `--type` 按类别清理

### 6. 前端展示

**TestRunDetailV2** 用例详情新增：
- 重试信息面板：重试次数、flaky_candidate 标记、首次失败类别
- Selector 稳定性面板：分数显示、低稳定 selector 列表
- 等待策略警告面板

**ReportDetail** 批量运行摘要新增：
- 稳定性摘要行：重试次数、重试恢复、Flaky 候选数、低稳定 Selector 数、等待策略警告数

## 禁止操作确认

| 禁止项 | 状态 |
|--------|------|
| 录制/回放 | ✅ 未涉及 |
| 自动元素自愈 | ✅ 未涉及 |
| Selector 自动修改 | ✅ 未涉及（仅评分报告） |
| 视觉基线自动更新 | ✅ 未涉及 |
| 多浏览器矩阵 | ✅ 未涉及 |
| App / 小程序 | ✅ 未涉及 |
| 数据库 Schema 变更 | ✅ 无 |

## 测试结果

### P2-9B 专项测试 (34/34 PASS)

| 测试组 | 测试数 | 结果 |
|--------|--------|------|
| Selector 稳定性评分 | 5 | ✅ 全通过 |
| 等待策略分析 | 3 | ✅ 全通过 |
| 执行前环境检查 | 4 | ✅ 全通过 |
| Retry 机制 | 6 | ✅ 全通过 |
| API retry_enabled=false | 1 | ✅ 全通过 |
| API selector_score | 3 | ✅ 全通过 |
| Artifact 清理脚本 | 3 | ✅ 全通过 |
| base_url 不可达 | 1 | ✅ 全通过 |
| 主链路不受影响 | 4 | ✅ 全通过 |
| Batch stability summary | 4 | ✅ 全通过 |

### 回归测试

| 测试 | 结果 |
|------|------|
| P0-7 Smoke 冒烟 | ✅ 8/8 PASS |
| API Contract 契约 | ✅ 23/23 PASS |
| Frontend Build (Vite) | ✅ 成功 |

## 下一阶段

P2-10: 测试套件 / 冒烟 / 回归管理
