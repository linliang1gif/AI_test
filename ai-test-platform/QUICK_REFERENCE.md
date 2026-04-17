# AI测试控制台 - 快速参考卡

## 🚀 一分钟上手

```bash
# 1. 检查系统
python check_system.py

# 2. 打开控制台
浏览器访问: http://localhost:5173/ai-test-console

# 3. 输入需求 → 选择优先级 → 点击执行 → 查看结果
```

---

## 📍 常用地址

| 服务 | 地址 |
|------|------|
| AI控制台 | http://localhost:5173/ai-test-console |
| 项目管理 | http://localhost:5173/projects |
| API文档 | http://localhost:8000/docs |

---

## 🎯 优先级选择

| 级别 | 说明 | 测试范围 | 耗时 |
|------|------|---------|------|
| P0 | 核心功能 | API+UI+集成 | 15-25秒 |
| P1 | 重要功能 | API+UI | 10-20秒 |
| P2 | 一般功能 | API | 5-15秒 |

---

## 🔍 结果解读

| 状态 | 含义 | 颜色 |
|------|------|------|
| passed | 全部通过 | 🟢 绿色 |
| failed | 有失败 | 🔴 红色 |
| partial | 部分通过 | 🟡 黄色 |
| skipped | 已跳过 | ⚪ 灰色 |

---

## 🧪 快速测试

```bash
python check_system.py     # 检查服务（3秒）
python quick_test.py       # 快速测试（10秒）
python verify_ai_console.py # 完整验收（2分钟）
```

---

## 📖 推荐文档

- **新手**: `快速入门_AI控制台.md`
- **详细**: `AI测试控制台使用说明.md`
- **索引**: `使用手册索引.md`

---

## 🆘 故障排查

| 问题 | 解决方案 |
|------|---------|
| 页面无法访问 | `cd frontend && npm run dev` |
| API调用失败 | `python backend_api_server.py` |
| AI响应慢 | 切换模型 qwen2.5:1.5b |

---

## 💡 使用场景

✅ 代码提交前验证  
✅ 功能变更影响分析  
✅ 回归测试执行  
✅ Bug修复验证

---

**快速访问**: http://localhost:5173/ai-test-console
