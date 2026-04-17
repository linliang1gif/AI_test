@echo off
echo 正在重启后端...

REM 停止占用8000端口的进程
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000 ^| findstr LISTENING') do (
    taskkill /F /PID %%a >nul 2>&1
)

timeout /t 2 /nobreak >nul

REM 启动后端
cd ai-test-platform
start "AI测试平台后端" py backend_api_server.py

echo 后端已在新窗口中启动
timeout /t 5 /nobreak >nul

echo 完成！
