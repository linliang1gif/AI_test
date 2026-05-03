# P2-6 Playwright 能力增强 报告

## 概述
P2-6 对 Playwright 执行引擎进行全面增强，新增 8 种操作和 1 种断言，支持 iframe 操作、键盘事件、Cookie 持久化等高级场景。

## 新增操作

| 操作 | 前端标签 | target | value | 说明 |
|------|---------|--------|-------|------|
| `press` | 按键 | CSS选择器(可选) | 按键名(Enter/Tab/Escape) | 模拟键盘按键 |
| `double_click` | 双击 | CSS选择器 | — | 双击元素 |
| `clear` | 清空 | CSS选择器 | — | 清空输入框 |
| `scroll` | 滚动 | CSS选择器(可选) | 像素数(正=下,负=上) | 滚动页面或元素 |
| `switch_frame` | 切换iframe | iframe选择器 | — | 进入 iframe 操作 |
| `switch_main` | 回到主页 | — | — | 从 iframe 返回主页面 |
| `eval_js` | 执行JS | JavaScript代码 | — | 执行自定义 JS |
| `save_cookies` | 保存Cookie | project_id | — | 保存当前会话 cookie |

## 新增断言

| 断言类型 | 前端标签 | target | value | 说明 |
|---------|---------|--------|-------|------|
| `element_count` | 元素数量 | CSS选择器 | 期望值(3, >0, >=5, <10) | 检查匹配元素数量 |

## 架构改动

### engine_ctx 上下文
引入 `engine_ctx` 字典在步骤间传递可变状态：
- `page`: Playwright Page 对象
- `context`: Browser Context (用于 cookie 操作)
- `active_frame`: 当前活跃帧 (page 或 iframe)

iframe 操作通过修改 `active_frame` 实现，`fill`、`click`、`wait_for` 等操作均通过 `frame` 而非直接 `page` 执行，确保 iframe 内元素可操作。

### 前端适配
创建表单和编辑表单的操作下拉框均已同步更新为中文标签，支持全部 16 种操作。

## 测试结果

```
P2-6 Playwright Enhanced: PASS=22 FAIL=0 TOTAL=22 (100%)
```

### 测试覆盖
- ✅ press 按键操作
- ✅ double_click 双击操作
- ✅ clear 清空操作
- ✅ scroll 滚动操作
- ✅ switch_frame/switch_main iframe 切换
- ✅ eval_js JavaScript 执行
- ✅ element_count 断言
- ✅ save_cookies Cookie 持久化
- ✅ P2-4 回归 28/28
- ✅ P2-5 回归 29/29

## 操作总览 (P2-6 后)

| 类别 | 操作 |
|------|------|
| 导航 | goto |
| 表单 | fill, clear, select, upload |
| 交互 | click, double_click, hover, press |
| 等待 | wait_for |
| 视图 | screenshot, scroll |
| 框架 | switch_frame, switch_main |
| 高级 | eval_js, save_cookies |

**断言**: text_visible, url_contains, url_not_contains, element_visible, element_count, screenshot_match

## 日期
2026-05-03
