---
description: AI HOT 资讯查询 - 用自然语言获取每日 AI 动态和日报，无需 API Key
---

# AI HOT Skill

让 Agent 用最自然的中文查询拿到 aihot.virxact.com 上每天的 AI HOT 日报和全部 AI 动态，不需要打开浏览器。

线上：https://aihot.virxact.com（公开匿名可访，无需 token）

## 先决条件：必须带 User-Agent（仅 API 端点）

`/api/public/*` 走 nginx UA 黑名单挡商业爬虫，默认 `curl/X.Y` UA 会被 403 Forbidden。**调 API 时所有请求都必须带浏览器 UA**：

```bash
UA="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
```

后面所有 curl 例子默认你已经设了 `$UA`——实际调用必须加 `-H "User-Agent: $UA"`。

## 什么时候用

> **路由优先级（第一原则）**：**默认走精选** `items?mode=selected`——它是 AI HOT 每天精挑细选的"主菜单"。
>
> - **仅当用户明确说出"日报"** 二字才走 `daily`
> - **仅当用户明确说"全部 / 完整 / 所有 / 全量"** 才走 `mode=all`
> - **"今天 AI 圈"、"过去 24 小时大新闻"** 等宽问题 = **默认精选 + 时间窗（since）**

| 用户在说 | 应该走的接口 |
|---|---|
| **默认（宽问题）** | `GET /api/public/items?mode=selected&since=<语义时间窗>` |
| **明确说"日报"** | `GET /api/public/daily` |
| **明确说"全部 / 完整"** | `GET /api/public/items?mode=all` |
| "昨天/前天 AI 日报" | `GET /api/public/daily/{YYYY-MM-DD}` |
| "最近几天日报有哪些" | `GET /api/public/dailies?take=N` |
| "看下精选条目" | `GET /api/public/items?mode=selected` |
| "最近的模型发布" | `GET /api/public/items?mode=selected&category=ai-models&since=<7d>` |
| "最近一周的 AI 动态" | `GET /api/public/items?mode=selected&since=ISO-8601` |
| "OpenAI 最近发的" | `GET /api/public/items?q=OpenAI` |
| "Sora 相关 / RAG 论文" | `GET /api/public/items?q=<关键词>` |

## 端点速览

| 端点 | 用途 | 主要参数 |
|---|---|---|
| `/api/public/daily` | 最新日报 | 无 |
| `/api/public/daily/{YYYY-MM-DD}` | 指定日期日报 | path: `date` |
| `/api/public/dailies` | 日报归档列表 | `take` (1-180, default 30) |
| `/api/public/items` | 全部 AI 动态 | `mode` / `category` / `since` / `take` / `cursor` / `q` |

约定：
- Base URL: `https://aihot.virxact.com`
- 鉴权：无（匿名）
- 限流：600 req/min/IP（请串行调用）
- items 端点 `since` 限最近 7 天
- `take` 上限 100；想要更多走 cursor 翻页

## 工作流

### 默认路径：拉精选 + 时间窗（宽问题首选）

```bash
# 拉最近 24 小时精选
since=$(date -u -v-24H +%Y-%m-%dT%H:%M:%SZ 2>/dev/null || date -u -d '24 hours ago' +%Y-%m-%dT%H:%M:%SZ)
curl -sH "User-Agent: $UA" "https://aihot.virxact.com/api/public/items?mode=selected&since=$since&take=50"

# 拉最近 50 条精选（不带明确时间窗）
curl -sH "User-Agent: $UA" "https://aihot.virxact.com/api/public/items?mode=selected&take=50"
```

### 拉日报（用户明确说"日报"时）

```bash
curl -sH "User-Agent: $UA" "https://aihot.virxact.com/api/public/daily"
```

### 拉指定日期日报

```bash
curl -sH "User-Agent: $UA" "https://aihot.virxact.com/api/public/daily/2026-05-07"
```

### 列日报归档

```bash
curl -sH "User-Agent: $UA" "https://aihot.virxact.com/api/public/dailies?take=14"
```

### 拉全部（用户明确说"全部"时）

```bash
since=$(date -u -v-24H +%Y-%m-%dT%H:%M:%SZ 2>/dev/null || date -u -d '24 hours ago' +%Y-%m-%dT%H:%M:%SZ)
curl -sH "User-Agent: $UA" "https://aihot.virxact.com/api/public/items?mode=all&since=$since&take=100"
```

### 按分类拉条目

5 个 category：

| `items?category=` | `daily.sections[].label` |
|---|---|
| `ai-models` | 模型发布/更新 |
| `ai-products` | 产品发布/更新 |
| `industry` | 行业动态 |
| `paper` | 论文研究 |
| `tip` | 技巧与观点 |

```bash
# 拉最近 50 条 AI 论文
curl -sH "User-Agent: $UA" "https://aihot.virxact.com/api/public/items?mode=selected&category=paper&take=50"
```

### 按时间窗口拉条目

用户问"最近 X"时，显式带 `since` 参数收窄到用户实际意图。

```bash
# 最近 7 天精选模型发布
since=$(date -u -v-7d +%Y-%m-%dT%H:%M:%SZ 2>/dev/null || date -u -d '7 days ago' +%Y-%m-%dT%H:%M:%SZ)
curl -sH "User-Agent: $UA" "https://aihot.virxact.com/api/public/items?mode=selected&category=ai-models&since=$since&take=100"
```

### 翻页（cursor）

响应里有 `nextCursor`，下次请求塞进 `cursor` 参数即可。`hasNext = false` 时停止。

### 关键词搜索

```bash
# 找 OpenAI 最近发的
curl -sH "User-Agent: $UA" "https://aihot.virxact.com/api/public/items?q=OpenAI&take=30"

# 找 RAG 论文
curl -sH "User-Agent: $UA" "https://aihot.virxact.com/api/public/items?category=paper&q=RAG&take=30"

# Anthropic 最近 3 天的精选
SINCE=$(date -u -v-3d +%Y-%m-%dT%H:%M:%SZ 2>/dev/null || date -u -d '3 days ago' +%Y-%m-%dT%H:%M:%SZ)
curl -sH "User-Agent: $UA" "https://aihot.virxact.com/api/public/items?mode=selected&q=Anthropic&since=$SINCE"
```

`q` 约束：至少 2 个字符，最长 200 字，跟其它参数正交叠加。

## 返回数据形态

### `/api/public/daily` 返回
```json
{
  "date": "2026-05-07",
  "generatedAt": "2026-05-07T00:01:23.456Z",
  "lead": { "title": "...", "leadParagraph": "..." },
  "sections": [
    { "label": "模型发布/更新", "items": [{ "title": "...", "summary": "...", "sourceUrl": "...", "sourceName": "..." }] }
  ],
  "flashes": [{ "title": "...", "sourceName": "...", "sourceUrl": "...", "publishedAt": "..." }]
}
```

### `/api/public/items` 返回
```json
{
  "count": 50,
  "hasNext": true,
  "nextCursor": "...",
  "items": [
    {
      "id": "cm9abc456def789ghi012jkl3",
      "title": "中文标题",
      "title_en": "原英文标题（仅当与 title 不同时存在）",
      "url": "https://...",
      "source": "OpenAI Blog",
      "publishedAt": "2026-05-07T15:30:00.000Z",
      "summary": "中文摘要",
      "category": "ai-models"
    }
  ]
}
```

## 给用户的输出格式

> **核心原则**：直接展示给用户的最终内容必须 markdown 格式 + 排版好 + **普通人能看得懂的人话**。所有端点路径、raw 参数、限流、cursor 等基础设施细节**不能出现**在用户看到的输出里。

### 日报式输出

```markdown
**AI HOT 日报 · 2026-05-07**

## 模型发布/更新
1. **<title>** — <source>
   <summary 简化版 50 字内>
   <url>

## 产品发布/更新
2. ...
```

编号贯穿全文（1, 2, 3 ... N），不在每个 ## 内重新计数。

### 列表式输出

默认按 category 分组 + 全局编号。只有 1 个 category 时用扁平编号列表。

### 时间转人话

`publishedAt` 是 ISO 8601 UTC，展示时必须转成北京时间 + 用户能扫读的相对/绝对时间。

### title vs title_en

默认输出 `title`（中文）。`title_en` 只在用户明确要求英文时才用。

## 常见错误处理

- 404 `No daily report available yet`：当天日报还没生成（北京时间 08:00 之前）。建议拉昨天日报。
- 400 `Invalid date format`：date 必须是 `YYYY-MM-DD`
- 429：限流。串行调用 + 翻页加 200ms 间隔

## 不要做

- 不要把宽问题路由到 daily（默认走精选 + since）
- 不要在用户没说"全部"时走 mode=all
- 不要试图猜测/编造内容
- 不要做高频轮询
- 不要并发猛拉翻页
- 不要尝试解析 cursor
- 公司/关键词查询用 server-side `?q=<词>`，不要走"拉一批 + 客户端 grep"
- 用户问"最近 N 天 X"时显式带 `since`
- 不要在用户输出里暴露基础设施细节
- 不要丢掉每条的 sourceUrl
- 引用源写 `<source>`（OpenAI 官网 等），不是端点路径
