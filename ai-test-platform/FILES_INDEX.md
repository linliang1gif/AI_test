# AI测试控制台 - 文件索引

## 📂 核心代码文件

### 前端（3个）
```
frontend/src/pages/AiTestConsole.jsx    # AI测试控制台主页面
frontend/src/App.jsx                    # 路由配置（已更新）
frontend/test_ai_console.html           # 快速测试页
```

### 后端（已存在）
```
pipeline/controller.py                  # Pipeline API控制器
pipeline/pipeline_service.py            # Pipeline服务
agent/test_agent_service.py             # Agent服务
strategy/strategy_service.py            # Strategy服务
orchestrator/orchestrator_service.py    # Orchestrator服务
self_healing/healing_service.py         # Healing服务
backend_api_server.py                   # 统一后端服务器
```

---

## 🧪 测试脚本（5个）

### 快速测试
```
check_system.py                         # 系统状态检查（3秒）
quick_test.py                           # 快速功能测试（10秒）
```

### 完整测试
```
test_ai_console_integration.py          # 基础集成测试（30秒）
verify_ai_console.py                    # 完整验收测试（2分钟）
demo_ai_console.py                      # 三场景演示（交互式）
```

---

## 📖 文档文件（15个）

### 快速入门（3个）
```
快速入门_AI控制台.md                    # ⭐ 5分钟上手指南
AI测试控制台使用说明.md                 # 详细使用说明
AI控制台界面说明.md                     # 界面布局和交互
```

### 系统说明（4个）
```
README.md                               # 项目总览（已更新）
SYSTEM_STATUS.md                        # 系统状态总览
PROJECT_SUMMARY.md                      # 项目总结
使用手册索引.md                         # 文档导航索引
```

### 完成报告（3个）
```
AI测试控制台完成报告.md                 # 功能完成报告
AI控制台交付清单.md                     # 交付清单
AI测试控制台_最终交付.md                # 最终交付文档
```

### 演示指南（1个）
```
使用演示脚本.md                         # 演示话术和技巧
```

### 快速参考（4个）
```
DONE.md                                 # 完成确认
ONE_PAGE_SUMMARY.md                     # 一页纸总结
QUICK_REFERENCE.md                      # 快速参考卡
交付总结.txt                            # 交付总结（纯文本）
```

---

## 🎯 按需查找

### 我想快速上手
👉 `快速入门_AI控制台.md`

### 我想了解详细功能
👉 `AI测试控制台使用说明.md`

### 我想查看界面说明
👉 `AI控制台界面说明.md`

### 我想准备演示
👉 `使用演示脚本.md`

### 我想查看系统状态
👉 `SYSTEM_STATUS.md`

### 我想了解项目全貌
👉 `PROJECT_SUMMARY.md`

### 我想查看交付内容
👉 `AI控制台交付清单.md`

### 我想快速参考
👉 `QUICK_REFERENCE.md`

### 我想确认完成情况
👉 `DONE.md`

---

## 🔗 快速命令

```bash
# 系统检查
python check_system.py

# 快速测试
python quick_test.py

# 完整验收
python verify_ai_console.py

# 场景演示
python demo_ai_console.py
```

---

## 📊 文件统计

- **代码文件**: 3个（前端）
- **测试脚本**: 5个
- **文档文件**: 15个
- **总计**: 23个文件

---

## ⭐ 推荐阅读顺序

1. `ONE_PAGE_SUMMARY.md` - 1分钟了解全貌
2. `快速入门_AI控制台.md` - 5分钟上手
3. `AI测试控制台使用说明.md` - 10分钟详细学习
4. `使用手册索引.md` - 查找更多文档

---

**提示**: 所有文档都在 `ai-test-platform/` 目录下
