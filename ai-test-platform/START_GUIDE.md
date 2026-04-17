# 启动指南 - AI测试控制台

## 🚀 一键启动（推荐）

### Windows用户
```bash
# 方式1: 使用现有的启动脚本
一键启动.bat

# 方式2: 手动启动
# Terminal 1 - 后端
python backend_api_server.py

# Terminal 2 - 前端
cd frontend
npm run dev
```

### 验证启动
```bash
python check_system.py
```

---

## ✅ 启动检查清单

### 第1步: 检查Python环境
```bash
python --version  # 应该是 3.10+
```

### 第2步: 检查Node环境
```bash
node --version    # 应该是 16+
npm --version
```

### 第3步: 检查依赖
```bash
# Python依赖
pip list | grep fastapi

# Node依赖
cd frontend
npm list react
```

### 第4步: 启动后端
```bash
python backend_api_server.py
```

**预期输出**:
```
INFO:     Started server process
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### 第5步: 启动前端
```bash
cd frontend
npm run dev
```

**预期输出**:
```
VITE ready in XXX ms
Local: http://localhost:5173/
```

### 第6步: 验证系统
```bash
python check_system.py
```

**预期输出**:
```
后端服务:  🟢 运行中
前端服务:  🟢 运行中
Ollama:   🟢 运行中
✅ 系统正常！可以使用
```

---

## 🔧 故障排查

### 问题1: 后端启动失败

**错误**: `Address already in use`

**解决**:
```bash
# 查找占用8000端口的进程
netstat -ano | findstr :8000

# 结束进程
taskkill /PID <进程ID> /F
```

### 问题2: 前端启动失败

**错误**: `EADDRINUSE: address already in use`

**解决**:
```bash
# 查找占用5173端口的进程
netstat -ano | findstr :5173

# 结束进程
taskkill /PID <进程ID> /F
```

### 问题3: 依赖缺失

**错误**: `ModuleNotFoundError` 或 `Cannot find module`

**解决**:
```bash
# Python依赖
pip install -r requirements.txt

# Node依赖
cd frontend
npm install
```

### 问题4: Ollama未启动

**错误**: AI功能无法使用

**解决**:
```bash
# 启动Ollama
ollama serve

# 验证
ollama list
```

---

## 🎯 启动后操作

### 1. 打开控制台
```
浏览器访问: http://localhost:5173/ai-test-console
```

### 2. 快速测试
```bash
python quick_test.py
```

### 3. 查看API文档
```
浏览器访问: http://localhost:8000/docs
```

### 4. 运行演示
```bash
python demo_ai_console.py
```

---

## 📊 服务端口

| 服务 | 端口 | 地址 |
|------|------|------|
| 后端API | 8000 | http://localhost:8000 |
| 前端Web | 5173 | http://localhost:5173 |
| Ollama | 11434 | http://localhost:11434 |

---

## 🔄 重启服务

### 重启后端
```bash
# 停止: Ctrl+C
# 启动: python backend_api_server.py
```

### 重启前端
```bash
# 停止: Ctrl+C
# 启动: cd frontend && npm run dev
```

### 重启Ollama
```bash
# 停止: Ctrl+C
# 启动: ollama serve
```

---

## 💡 启动建议

### 开发环境
- 使用两个Terminal分别启动后端和前端
- 保持Terminal窗口打开查看日志
- 使用 `check_system.py` 定期检查状态

### 生产环境
- 使用进程管理工具（如PM2、Supervisor）
- 配置自动重启
- 设置日志轮转
- 配置反向代理（Nginx）

---

## 🆘 需要帮助？

### 启动问题
1. 运行 `python check_system.py`
2. 查看Terminal输出日志
3. 检查端口占用情况

### 功能问题
1. 运行 `python quick_test.py`
2. 查看API文档: http://localhost:8000/docs
3. 阅读 `快速入门_AI控制台.md`

---

**快速启动**: `一键启动.bat` 或手动启动两个服务  
**快速验证**: `python check_system.py`  
**快速使用**: http://localhost:5173/ai-test-console
